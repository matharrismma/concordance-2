"""Mathematics verifier — symbolic checks via sympy.

  * equality   : simplify(a - b) == 0, with a removable-singularity / pole GUARD
                 so x/x == 1 is NOT sealed as an unconditional identity
  * derivative : d/dx f == g symbolically
  * inequality : L op R symbolically, with a sampling fallback
  * integral / limit / solve / series / matrix / ode

sympy (~4s import) loads on first use via _ensure_sympy, so the engine cold start
stays fast. Ported as-is from 1.0 — the derivation moat, the 0-false-positive crown.
"""
from __future__ import annotations

import ast as _ast
import builtins as _builtins
import math as _math
import operator as _operator
import re as _re
import sys as _sys
import types as _types
import unicodedata as _unicodedata
from typing import Any, Dict, List

from .. import cells as _cells
from .base import PowerFloorRefused, VerifierResult, clamp_tol, confirm, error, mismatch, na
from .base import stated_precision, stated_tolerance_abs, stated_window, window_for
from .base import dispatch  # declarative run() driver

simplify = diff = integrate = limit = solve = None
Symbol = oo = S = expand = _SympifyError = None
_PARSE_ERRORS = (SyntaxError, TypeError, ValueError, NotImplementedError)
_sympy_loaded = False
_sympy_ok = None  # None = untried; True/False after first attempt
# The parser's tables, built once from sympy in _ensure_sympy.
_sp = None                  # the sympy module
_SYMPY_VALUES = ()          # what counts as a sympy value: Basic, and MatrixBase, since a mutable Matrix is no Basic
_FUNCTIONS: Dict[str, Any] = {}     # each name on _ALLOWED_FUNCS that sympy binds to a callable
_CONSTANTS: Dict[str, Any] = {}     # the only names that read as a value without the caller supplying them
_NOT_SYMBOLS = frozenset()  # every other name sympy would read as something other than a symbol


def sympy_is_loaded() -> bool:
    """Is sympy in this process? sys.modules can answer yes: sympy is pure Python, so a read of the process's
    mapped files shows nothing of it either way."""
    return "sympy" in _sys.modules


def _ensure_sympy() -> bool:
    """Import sympy on first use. Idempotent. Returns True if sympy is available, False on a
    stdlib-only box (the optional `math` extra is not installed). Callers degrade to a clean
    NOT_APPLICABLE — the symbolic checks genuinely need sympy — rather than crash, so the engine
    keeps running offline. (set_algebra does not need sympy; it uses the pure-stdlib engine.)
    In a process with cells on it raises instead: this is the one way sympy loads, so this is the
    wall that keeps sympy out of the front, by default and with no list of handlers."""
    global simplify, diff, integrate, limit, solve
    global Symbol, oo, S, expand, _SympifyError, _PARSE_ERRORS, _sympy_loaded, _sympy_ok
    global _sp, _SYMPY_VALUES, _FUNCTIONS, _CONSTANTS, _NOT_SYMBOLS
    if _cells.active() is not None:
        raise PowerFloorRefused("sympy does not load in the front; a read that needs it runs in a cell")
    if _sympy_loaded:
        return _sympy_ok
    try:
        import sympy as _sympy
        from sympy import (
            simplify as _s, diff as _d, integrate as _i, limit as _l, solve as _so,
            Symbol as _Sy, oo as _oo, S as _S, expand as _e, SympifyError as _SE,
        )
        simplify, diff, integrate = _s, _d, _i
        limit, solve, Symbol, oo, S, expand = _l, _so, _Sy, _oo, _S, _e
        _SympifyError = _SE
        _PARSE_ERRORS = (_SE, SyntaxError, TypeError, ValueError, NotImplementedError)
        bound = {n: getattr(_sympy, n, None) for n in _sympy.__all__}
        _FUNCTIONS = {n: bound[n] for n in _ALLOWED_FUNCS if callable(bound.get(n))}
        _FUNCTIONS.update(abs=abs, round=round)    # the two builtin spellings on the list
        _CONSTANTS = {n: bound[n] for n in _CONSTANT_NAMES}
        # What sympy's own auto_symbol reads as an object and not a symbol: anything `from sympy import *`
        # binds to a Basic, a class or a callable, Q, and every real builtin function.
        _NOT_SYMBOLS = frozenset(
            {n for n, v in bound.items() if isinstance(v, (_sympy.Basic, type)) or callable(v) or v is _sympy.Q}
            | {n for n, v in vars(_builtins).items() if isinstance(v, _types.BuiltinFunctionType)})
        _SYMPY_VALUES = (_sympy.Basic, _sympy.MatrixBase)
        _sp = _sympy
        _install_power_floor()
        _sympy_ok = True
    except ModuleNotFoundError:
        _sympy_ok = False
    _sympy_loaded = True
    return _sympy_ok


# Characters that are NOT part of any valid math expression string. ast.parse treats '#' as a
# comment and silently drops the rest, so the text after it would never be read — reject such
# inputs early.
#
# `%` WAS ON THIS LIST AND DID NOT BELONG THERE (removed 2026-08-02): SymPy evaluates `16 % 9`
# as Mod natively, and blacklisting it left the fleet unable to check MODULAR ARITHMETIC at all
# — every "n mod m = k" claim returned INCOMPLETE, found when the vortex-math assay tried to
# seal the doubling cycle (16→7, 32→5, 64→1 ... mod 9) and could not. Casting out nines is the
# oldest integrity check in bookkeeping — the ancestor of this project's own hashes — and the
# fleet could not perform it.
_INVALID_EXPR_RE = _re.compile(r"[#@!$&\[\]\{\}\\|`]")

# The word form people actually write: "16 mod 9". Normalized to the operator before parsing so
# every mode (equality, equation, solve, limit) reads it. Word-boundary only, and NEVER before a
# parenthesis: the first draft's IGNORECASE happily rewrote the function form `Mod(16, 9)` into
# `%(16, 9)` — the exact thing its own comment promised it would not touch, caught by the test
# minutes after it was written. The lookahead is the promise, made structural.
_MOD_WORD_RE = _re.compile(r"\bmod\b(?!\s*\()", _re.IGNORECASE)

# Compute-DoS guards: a short input like 9**9**9 expands to a ~369M-digit bignum.
_MAX_POW_EXP = 10000
_MAX_POW_BITS = 2 ** 20     # the size of an integer or rational power, however its base was built
_ROOT_TRIAL_TO = 2 ** 15    # where sympy's own root stops dividing an integer by primes
# What that leaves, sympy's root must prove prime or a perfect power before it goes on. Measured 2026-11-06, that proof
# reaches the verify window near this size, and it is no longer bounded by anything well before _MAX_POW_BITS.
_MAX_ROOT_BITS = 2 ** 14
_MAX_AST_NODES = 2000
_MAX_AST_DEPTH = 60
_MAX_EXPR_CHARS = 4000

# SECURITY (red team 2026-08-06, CRITICAL; replaced 2026-11-04): sympy.sympify() EVALUATES arbitrary
# Python, and an expr that named its way out of it was an unauthenticated RCE reachable from public
# POST /verify. A guard in front of it was tried and is withdrawn: a check on a text that something
# else then evaluates cannot be made sufficient, because the text checked and the text evaluated
# differ. So no text from a request reaches sympify, parse_expr or any sympy entry that parses a
# string. parse_expression reads a text by walking Python's ast itself and builds sympy objects
# directly. What is not on its allowlist cannot run, because nothing runs. A missing function name
# yields INCOMPLETE (an honest gap), never a false verdict — add names here as real math needs them.
# Never add a function that parses a text built from what a request names: nsimplify did, with a
# name the request chose, and came off this list for that.
_ALLOWED_FUNCS = frozenset({
    # trig / inverse / hyperbolic
    "sin", "cos", "tan", "cot", "sec", "csc", "sinc", "asin", "acos", "atan", "acot", "asec",
    "acsc", "atan2", "sinh", "cosh", "tanh", "coth", "sech", "csch", "asinh", "acosh", "atanh",
    "acoth", "deg", "rad",
    # exp / log / roots / powers
    "exp", "log", "ln", "sqrt", "cbrt", "root", "Pow",
    # abs / sign / rounding
    "Abs", "abs", "sign", "floor", "ceiling", "frac", "round",
    # number theory / combinatorics
    "Mod", "gcd", "lcm", "igcd", "ilcm", "factorial", "factorial2", "binomial", "totient",
    "isprime", "factorint", "primerange", "nextprime", "prevprime",
    # special functions
    "gamma", "loggamma", "polygamma", "digamma", "beta", "erf", "erfc", "erfi", "zeta",
    "Ei", "li", "Si", "Ci",
    # min / max / complex
    "Min", "Max", "re", "im", "conjugate", "arg",
    # numbers / symbols
    "Rational", "Integer", "Float", "Number", "Symbol", "symbols", "Dummy",
    # relations / logic
    "Eq", "Ne", "Lt", "Le", "Gt", "Ge", "Equality", "Unequality", "StrictLessThan", "LessThan",
    "StrictGreaterThan", "GreaterThan", "Relational", "And", "Or", "Not", "Xor", "Nand", "Nor",
    "Implies", "Equivalent", "ITE", "Piecewise",
    # calculus
    "diff", "Derivative", "integrate", "Integral", "limit", "Limit", "Sum", "summation",
    "Product", "product", "Subs",
    # algebra / manipulation
    "simplify", "expand", "factor", "cancel", "together", "apart", "collect", "trigsimp",
    "radsimp", "N", "evalf", "Poly", "degree", "solve", "solveset", "roots",
    # matrices
    "Matrix", "ImmutableMatrix", "eye", "zeros", "ones", "diag", "Transpose", "det", "trace",
    "Determinant", "Trace", "Inverse", "transpose",
    # containers sympy constructors sometimes need
    "Tuple", "Interval", "FiniteSet", "S",
})

# The names that read as a value without a caller supplying them. Nothing else can: a Name is a
# caller's name, one of these, or a Symbol, so no Name yields a Python object from outside these.
_CONSTANT_NAMES = ("pi", "E", "I", "oo", "zoo", "nan", "EulerGamma", "GoldenRatio", "Catalan",
                   "TribonacciConstant", "true", "false")

# The functions that hand back a plain int or bool, not a sympy value.
_PLAIN_RESULT_FUNCS = frozenset({"igcd", "ilcm", "nextprime", "prevprime", "isprime"})

# The functions sympy's evaluate=False leaves unevaluated; every other call in an unevaluated read
# still evaluates, as it does there.
_UNEVALUATED_FUNCS = frozenset({
    "Abs", "im", "re", "sign", "arg", "conjugate", "acos", "acot", "acsc", "asec", "asin", "atan",
    "acosh", "acoth", "asinh", "atanh", "cos", "cot", "csc", "sec", "sin", "tan", "cosh", "coth",
    "csch", "sech", "sinh", "tanh", "exp", "ln", "log", "sqrt", "cbrt",
})

_ARITHMETIC = {_ast.Add: _operator.add, _ast.Sub: _operator.sub, _ast.Mult: _operator.mul,
               _ast.Div: _operator.truediv}
_TERMS, _FACTORS = (_ast.Add, _ast.Sub), (_ast.Mult, _ast.Div)

_WRITTEN_EXPONENT_RE = _re.compile(r"[eE]([+-]?[0-9_]+)$")


class ExpressionRefused(ValueError):
    """A text parse_expression will not read. A ValueError, so it is a member of _PARSE_ERRORS whether
    or not sympy has loaded yet, and each mode keeps its reading of a refused text."""


class NoMeaningRefused(ExpressionRefused):
    """A value the rule refuses. Its own kind, because a text refused this way is arithmetic with no
    meaning, never prose and never a claim that can be set aside: see _refuse_no_meaning."""


class PowerRefused(ExpressionRefused):
    """A text the power limits refuse. Its own kind, so an unevaluated read can say so: there a refusal
    is a pole that could not be looked for, and it must never read as no pole."""


def _normalise_expression(expr, word_mod: bool) -> str:
    """The one normal form, and the only text anything reads: no surrounding whitespace (ast.parse
    rejects it as an IndentationError), one spelling of a power, and, for mathematics alone, the word
    form of mod. Physics never read that word: there mod is a name a symbol may have, and reading the
    word would turn a claim that never parsed into one that reads."""
    expr = _MOD_WORD_RE.sub("%", str(expr)).strip() if word_mod else str(expr).strip()
    return expr.replace("^", "**")


def _bound_tree(tree) -> None:
    """Today's node and depth limits, on the tree itself. Iterative, so a long chain is refused here
    and cannot overflow the stack; it is what keeps _Reader's recursion shallow."""
    nodes = 0
    todo = [(tree, 1)]
    while todo:
        node, depth = todo.pop()
        nodes += 1
        if nodes > _MAX_AST_NODES:
            raise ExpressionRefused("expression too large")
        if depth > _MAX_AST_DEPTH:
            raise ExpressionRefused("expression too deeply nested")
        todo.extend((child, depth + 1) for child in _ast.iter_child_nodes(node))


def _ceiling(value) -> int:
    return -(-value.p // value.q)


def _settled(value):
    """The value of arithmetic an unevaluated read left written out, as 5000*2 for 10000. It rebuilds
    sums, products and powers and nothing else, so a Sum in an exponent is not run by bounding it. What
    will not rebuild, as an exponent holding a matrix, is no number to bound, and never fails a read."""
    if isinstance(value, (_sp.Add, _sp.Mul, _sp.Pow)):
        try:
            return value.func(*[_settled(arg) for arg in value.args])
        except Exception:
            return value
    return value


def _power_bits(base, exponent) -> int:
    """An upper bound on the bits of the integers base**exponent multiplies out, for a Rational
    exponent. It reads what it knows sympy carries a power through: a power's own base and exponent,
    the pieces of a Piecewise and the entries of a matrix. Everything else is default-deny: what
    carries a power cannot be known by name (a constant Poly is an integer, a matrix expression
    multiplies out when done), so a base it does not read counts every Rational inside it. So a root
    of an integer, which shows no integer at all, is bounded by the integer under it. Each step
    rounds up: a fraction never rounds the bound down. It binds a power and only a power: another
    spelling of one, such as exp of a multiple of a log, has only the timeout."""
    if isinstance(base, _sp.MatrixBase):
        # An entry of M**n is at most (rows * largest entry)**n for n >= 0. A negative power goes through
        # the determinant, whose size grows with the rows, so this is no upper bound for one.
        largest = max((_power_bits(entry, exponent) for entry in base), default=0)
        return largest + _ceiling(abs(exponent)) * base.rows.bit_length()
    if not isinstance(base, _sp.Basic):
        raise PowerRefused("a power is on a mathematical value")
    if base.is_Rational:
        return max(int(base.p).bit_length(), int(base.q).bit_length()) * _ceiling(abs(exponent))
    if isinstance(base, _sp.Piecewise):
        return max(_power_bits(piece, exponent) for piece, _condition in base.args)
    if isinstance(base, _sp.Pow):
        root, power = base.as_base_exp()
        power = _settled(power)
        if power.is_Rational:
            return _power_bits(root, abs(power * exponent))
    return sum(_power_bits(arg, exponent) for arg in base.args)


def _bound_power(base, exponent) -> None:
    """The exponent limit, and the cap on the bits of an integer or rational power. Both read the
    values already built, so they hold however the base or the exponent was written: an operator, the
    Pow function, a power nested on the base side. They bind an unevaluated read too. A call in that
    read still multiplies, and a base that collapsed in the evaluated read stands whole there, so this
    can refuse what the evaluated read took; _domain_mismatch fails closed on that."""
    exponent = _settled(exponent)
    if not getattr(exponent, "is_Number", False) or not exponent.is_finite:
        return
    if abs(exponent) > _MAX_POW_EXP:
        raise PowerRefused("exponent too large")
    if exponent.is_Rational and _power_bits(base, exponent) > _MAX_POW_BITS:
        raise PowerRefused("power too large")


def _unfactored_bits(whole: int) -> int:
    """The bits of what trial division leaves of an integer, stopping where sympy's own root stops."""
    for prime in _sp.primerange(2, _ROOT_TRIAL_TO + 1):
        if whole == 1:
            break
        if whole % prime == 0:
            whole //= prime ** _sp.multiplicity(prime, whole)
    return whole.bit_length()


def _left_under_the_root(whole: int, exponent) -> int:
    """The bits Integer._eval_power multiplies out under a root, read as it reads them. Each prime goes in
    with its multiplicity times the numerator, less the whole powers _power_bits has measured, so what
    stays is under the denominator: the numerator alone says nothing of it. All of them are divided by
    their common divisor, so primes that each appear the same number of times leave the integer as it
    was, however long the exponent. A remainder sharing a divisor with the denominator leaves for a
    power of its own, as does a perfect power's one root, and each meets this floor there. A prime is at
    least one bit, so a power past the bound is past it at any prime: clipped there, no float overflows."""
    if _sp.perfect_power(whole):
        return 0
    left = {}
    for factor, times in _sp.Integer(whole).factors(limit=_ROOT_TRIAL_TO).items():
        remainder = times * exponent.p % exponent.q
        if remainder and _math.gcd(remainder, exponent.q) == 1:
            left[factor] = remainder
    common = _math.gcd(*left.values())
    return 1 + int(sum(min(remainder // common, _MAX_POW_BITS + 1) * _math.log2(factor)
                       for factor, remainder in left.items()))


def _root_past_the_floor(integer, exponent) -> bool:
    """A root, before sympy's own root reads it. An exact root multiplies out only the power _power_bits
    measured. Past that, this hands perfect_power and factors no more than _MAX_ROOT_BITS to prove: a
    perfect power of that much is refused with the rest. The primes of an integer of n bits multiply to
    at most n bits and each stays under the denominator, so a root small on both counts has nothing to
    measure, and the two sympy calls are not made twice for it. That is all this bounds: it says nothing
    of how long its own reads of the integer take, or of what sympy's own root does with what passes here.
    Neither is refused here, and a read that stalls on either ends at a cell's window."""
    whole = abs(int(integer.p))
    bits = whole.bit_length()
    if bits <= _MAX_ROOT_BITS and bits * (exponent.q - 1) <= _MAX_POW_BITS:
        return False
    if _sp.integer_nthroot(whole, exponent.q)[1]:
        return False
    return _unfactored_bits(whole) > _MAX_ROOT_BITS or _left_under_the_root(whole, exponent) > _MAX_POW_BITS


def _past_the_floor(base, exponent) -> bool:
    """The result passes _MAX_POW_BITS as _power_bits measures it, or an Integer's root is past what it
    may multiply out or leave to prove. A negative exponent inverts and a Rational splits into an Integer
    for each side, so every root reaches _root_past_the_floor with the exponent sympy really reads."""
    if _power_bits(base, exponent) > _MAX_POW_BITS:
        return True
    return base.is_Integer and exponent.q > 1 and exponent.p > 0 and _root_past_the_floor(base, exponent)


def _floored(power):
    """sympy's own Integer or Rational power, behind the floor: what _past_the_floor reads as past it is
    refused before any arithmetic, and everything else goes straight on. `unfloored` is
    sympy's own power, kept for the differential test's oracle alone: the engine sets it and never reads
    it, nothing under src or tools names it, and no evaluator here reads an attribute, so no text can
    ask for it. tests/test_power_floor.py holds all three."""
    def _eval_power(self, exponent):
        if isinstance(exponent, _sp.Rational) and _past_the_floor(self, exponent):
            raise PowerFloorRefused("a power past the bound is not computed")
        return power(self, exponent)
    _eval_power.unfloored = power
    return _eval_power


def _install_power_floor() -> None:
    """The floor under _bound_power: that bound reads what a request wrote, and this is the same bound
    at the layer that computes, where big-integer work holds Python's global lock and stops every
    thread in the engine. It stands at these two powers only, so it does not bound every long read.
    0, 1 and -1 have powers of their own in sympy, and those never grow."""
    for kind in (_sp.Integer, _sp.Rational):
        if not hasattr(kind._eval_power, "unfloored"):
            kind._eval_power = _floored(kind._eval_power)


def _require_sympy_values(value) -> None:
    """A value a call returned: a sympy value, or a list, tuple or dict of them at every depth. An
    iterator, a str or anything else is refused. This runs after the call, so it is a second line.
    What keeps a request's own text out of a parse is that no str and no callable can reach a call.
    A call can still parse a text sympy builds itself: a decimal in solve reaches sympy's string
    parser with numeric text made from that number, as it did before this parser existed."""
    if isinstance(value, _SYMPY_VALUES):
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _require_sympy_values(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            _require_sympy_values(key)
            _require_sympy_values(item)
    else:
        raise ExpressionRefused(f"a call returned a {type(value).__name__}, not a mathematical value")


def _holds(value, *wanted) -> bool:
    """Whether a built value is or contains any of these, through every container."""
    if isinstance(value, dict):
        return any(_holds(key, *wanted) or _holds(item, *wanted) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_holds(item, *wanted) for item in value)
    return isinstance(value, _SYMPY_VALUES) and bool(value.has(*wanted))


def _refuse_no_meaning(value, written: bool, carried: bool) -> bool:
    """THE RULE: a value with no meaning never leaves the node that built it. sympy answers a division by
    zero and some poles with zoo, nan, AccumBounds or an oo of its own and carries on, and a later node can
    collapse that into an ordinary number: 1/zoo is 0. So each built value is tested here, at its own node,
    before anything can build on it. A value that is or contains zoo, nan or AccumBounds is refused. So is
    one that contains oo or -oo, unless it is itself written (a name that read as one) or was carried in by
    a value it was built from. It tests the value and never a name: a variable called oo is a symbol and
    earns nothing, and a written oo that reduced to a finite number carries nothing further. Returns whether
    the value holds an infinity, for the node that builds on it."""
    if _holds(value, _sp.zoo, _sp.nan, _sp.AccumBounds):
        raise NoMeaningRefused("a value with no meaning is not read")
    infinite = _holds(value, _sp.oo, -_sp.oo)
    if infinite and not (written or carried):
        raise NoMeaningRefused("an infinity nobody wrote is not read")
    return infinite


class _Reader:
    """Builds sympy objects from a bounded tree. A node it does not name is refused."""

    def __init__(self, source: str, names: Dict[str, Any], rational: bool, evaluate: bool):
        self.source, self.names, self.rational, self.evaluate = source, names, rational, evaluate
        self.carried = False    # whether a value the node being built was built from held an infinity

    def read(self, node, in_call: bool = False):
        """Every node passes through here, so each built value meets the rule at its own node. Only a read
        that evaluates is tested: the unevaluated read is how a pole is seen, and a refusal there would
        read as no pole."""
        if not self.evaluate:
            return self._build(node, in_call)
        outer, self.carried = self.carried, False
        value = self._build(node, in_call)
        infinite = _refuse_no_meaning(value, isinstance(node, _ast.Name), self.carried)
        self.carried = outer or infinite
        return value

    def _build(self, node, in_call: bool):
        if isinstance(node, _ast.Constant):
            return self._number(node)
        if isinstance(node, _ast.Name):
            return self._name(node.id)
        if isinstance(node, _ast.BinOp):
            return self._binop(node)
        if isinstance(node, _ast.UnaryOp):
            return self._unary(node)
        if isinstance(node, _ast.Compare):
            return self._compare(node)
        if isinstance(node, _ast.Call):
            return self._call(node)
        if isinstance(node, _ast.Tuple) and in_call:   # so a matrix or a Sum limit can be written
            return tuple(self.read(item, in_call=True) for item in node.elts)
        raise ExpressionRefused(f"a {type(node).__name__} is not read as mathematics")

    def _number(self, node):
        if type(node.value) is int:
            return _sp.Integer(node.value)
        if type(node.value) is float:
            written = _ast.get_source_segment(self.source, node)
            exponent = _WRITTEN_EXPONENT_RE.search(written)    # a written 1eN is the power 10**N,
            if exponent and abs(int(exponent.group(1))) > _MAX_POW_EXP:    # and sympy expands it whole
                raise ExpressionRefused("exponent too large")
            return _sp.Rational(written) if self.rational else _sp.Float(written)
        raise ExpressionRefused(f"a {type(node.value).__name__} literal is not a number here")

    def _name(self, name: str):
        if name.startswith("_"):
            raise ExpressionRefused("names beginning with underscore are not allowed")
        if name in self.names:
            return self.names[name]
        if name in _CONSTANTS:
            return _CONSTANTS[name]
        if name in _ALLOWED_FUNCS or name in _NOT_SYMBOLS:
            raise ExpressionRefused(f"{name} is not a value")
        return Symbol(name)

    def _operand(self, node):
        value = self.read(node)
        if not isinstance(value, _SYMPY_VALUES) or isinstance(value, _sp.Tuple):
            raise ExpressionRefused("arithmetic is on sympy values only, never a tuple or list")
        return value

    def _binop(self, node):
        op = type(node.op)
        if op is _ast.Mod:
            # sympy's evaluate=False leaves % and everything under it evaluated.
            reader = self if self.evaluate else _Reader(self.source, self.names, self.rational, True)
            return reader._operand(node.left) % reader._operand(node.right)
        if op is not _ast.Pow and op not in _ARITHMETIC:
            raise ExpressionRefused(f"the operator {op.__name__} is not read as mathematics")
        if op is _ast.Pow and any(isinstance(n, _ast.BinOp) and isinstance(n.op, _ast.Pow)
                                  for n in _ast.walk(node.right)):
            raise ExpressionRefused("nested power tower not allowed")
        if op is not _ast.Pow and not self.evaluate:
            kind = _sp.Add if op in _TERMS else _sp.Mul
            return kind(*self._unevaluated_args(node), evaluate=False)
        left, right = self._operand(node.left), self._operand(node.right)
        if op is _ast.Pow:
            _bound_power(left, right)
            return left ** right if self.evaluate else _sp.Pow(left, right, evaluate=False)
        return _ARITHMETIC[op](left, right)

    def _unevaluated_args(self, node) -> list:
        """The arguments sympy's evaluate=False gives one Add or Mul. It flattens a sum written in a
        sum and a product written in a product, so x+(y+z) and x+y+z have one pole base. It does that
        to the tree, before anything is built: by the value built, a sum a call returned would be
        flattened too, and a product holding a matrix, which is a matrix by then, would not be."""
        op = type(node.op)
        ops = _TERMS if op in _TERMS else _FACTORS
        left = self._flattened(node.left, ops)
        if op is _ast.Sub:
            return left + [_sp.Mul(-1, self._operand(node.right), evaluate=False)]
        if op is _ast.Div:
            return left + [_sp.Pow(self._operand(node.right), -1, evaluate=False)]
        return left + self._flattened(node.right, ops)

    def _flattened(self, node, ops) -> list:
        if isinstance(node, _ast.BinOp) and type(node.op) in ops:
            return self._unevaluated_args(node)
        return [self._operand(node)]

    def _unary(self, node):
        if isinstance(node.op, _ast.USub):
            return -self._operand(node.operand)
        if isinstance(node.op, _ast.UAdd):
            return +self._operand(node.operand)
        raise ExpressionRefused(f"the operator {type(node.op).__name__} is not read as mathematics")

    def _compare(self, node):
        relation = {_ast.Lt: _sp.Lt, _ast.LtE: _sp.Le, _ast.Gt: _sp.Gt,
                    _ast.GtE: _sp.Ge}.get(type(node.ops[0]))
        if relation is None or len(node.ops) != 1:
            raise ExpressionRefused("one comparison by <, <=, > or >= is all that is read")
        left, right = self._operand(node.left), self._operand(node.comparators[0])
        return relation(left, right) if self.evaluate else relation(left, right, evaluate=False)

    def _call(self, node):
        func = node.func
        if not isinstance(func, _ast.Name) or func.id not in _ALLOWED_FUNCS:
            raise ExpressionRefused("call to a non-mathematical function is not allowed")
        name = func.id
        if name in self.names:
            raise ExpressionRefused(f"{name} is a value here, not a function")
        if name not in _FUNCTIONS:
            raise ExpressionRefused(f"{name} is not bound to a function")
        if node.keywords:
            raise ExpressionRefused("a call takes no keywords")
        args = [self.read(arg, in_call=True) for arg in node.args]
        if name == "Pow" and len(args) >= 2:
            _bound_power(args[0], args[1])
        # sympy's rational read rewrites the name Float as well as the numbers.
        function = _sp.Rational if self.rational and name == "Float" else _FUNCTIONS[name]
        if not self.evaluate and name in _UNEVALUATED_FUNCS:
            value = function(*args, evaluate=False)
        else:
            value = function(*args)
        if name in _PLAIN_RESULT_FUNCS:
            if value is True or value is False:
                return _sp.true if value else _sp.false
            if type(value) is int:
                return _sp.Integer(value)
        _require_sympy_values(value)
        return value


def parse_expression(text, names: Dict[str, Any] = None, rational: bool = False, evaluate: bool = True,
                     word_mod: bool = False):
    """Read an expression text into sympy objects. The one way any text reaches sympy.

    It normalises the text once, and everything after reads exactly that text: the limits apply to
    the tree ast.parse builds from it, and nothing re-reads the input. Nothing is evaluated. The
    tree is walked and each node on the allowlist is built directly; every other node is refused.

    names maps the caller's names to sympy values and wins over the constants. rational=True reads
    decimals as exact rationals, as sympify's rational=True does. evaluate=False builds what sympify's
    evaluate=False builds, for reading pole bases. word_mod=True reads the word form of mod, which
    mathematics has and physics does not. A text the parser will not read, and any failure while
    reading it, raises ExpressionRefused."""
    if not _ensure_sympy():
        # stdlib-only box: the symbolic-math checks need sympy. Raise a _PARSE_ERRORS member so
        # every verify_* wrapper degrades to NOT_APPLICABLE with this reason, never a crash.
        raise ValueError("requires the optional math extra (sympy); not installed on this box")
    try:
        names = names or {}
        source = _normalise_expression(text, word_mod)
        if len(source) > _MAX_EXPR_CHARS:
            raise ExpressionRefused("expression too long")
        if _INVALID_EXPR_RE.search(source):
            raise ExpressionRefused(f"invalid characters in expression: {source!r}")
        # ast normalises identifiers, so a name NFKC would change would become two symbols: one as the
        # caller wrote it, one as the text was read.
        for word in (source, *names):
            if _unicodedata.normalize("NFKC", word) != word:
                raise ExpressionRefused("a text or name Unicode normalisation would change")
        tree = _ast.parse(source, mode="eval")
        _bound_tree(tree)
        return _Reader(source, names, rational, evaluate).read(tree.body)
    except ExpressionRefused:
        raise
    except Exception as e:  # a syntax error, RecursionError, or sympy refusing what it was handed
        raise ExpressionRefused(f"expression is not read as mathematics: {type(e).__name__}") from None


def _parse(expr: str, var_names: List[str] = None, rational: bool = False, evaluate: bool = True):
    if not _ensure_sympy():
        raise ValueError("requires the optional math extra (sympy); not installed on this box")
    locals_ = {n: Symbol(n) for n in (var_names or [])}
    locals_.setdefault("oo", oo)
    locals_.setdefault("inf", oo)
    # rational=True parses decimals as EXACT rationals (0.1 -> 1/10), so a chain like 520/1.04 = 500
    # or 6*0.1 = 0.60 is TRUE by exact arithmetic rather than tripping on the last IEEE-754 bit. This
    # TIGHTENS exactness (no float wobble); it never loosens it. Default off to leave every symbolic
    # caller (equality/derivative/limit/series) unchanged.
    return parse_expression(expr, locals_, rational, evaluate, word_mod=True)


def _pole_bases(expr):
    """Bases of NEGATIVE powers in a RAW (un-cancelled) sympy expression — the
    sub-expressions whose vanishing makes expr undefined. Detects removable
    singularities that simplify() would otherwise silently cancel."""
    from sympy import Pow
    poles = set()
    try:
        for sub in expr.atoms(Pow):
            base, exp_ = sub.as_base_exp()
            if exp_.is_number and exp_.is_negative and getattr(base, "free_symbols", set()):
                poles.add(base)
    except Exception:
        pass
    return poles


def _domain_mismatch(a_str, b_str, var_names):
    """If expr_a and expr_b have DIFFERENT poles, an equality that simplifies to zero
    is true only OFF that singular set — NOT an unconditional identity, and must not be
    sealed as a clean HOLDS. Returns a description of the differing poles, or None when
    the domains match. Re-reads the same normalised text unevaluated, so x/x is not auto-reduced
    to 1 before its pole can be seen. A read the power limits or the rule refuse raises, as a member of
    _PARSE_ERRORS, so verify_equality reads the claim as not checkable: a pole that could not be
    looked for is never no pole. Any other failed read is no mismatch, as it has always been."""
    try:
        ra = _parse(a_str, var_names, evaluate=False)
        rb = _parse(b_str, var_names, evaluate=False)
    except (PowerRefused, NoMeaningRefused):
        raise
    except Exception:
        return None
    pa, pb = _pole_bases(ra), _pole_bases(rb)
    if pa == pb:
        return None
    diff_ = pa.symmetric_difference(pb)
    return ", ".join(sorted(str(p) for p in diff_)) if diff_ else None


_REFUSAL = "cannot parse "


def _refused(name: str, reason, what: str = "expression") -> VerifierResult:
    """A mode's reading of a text it could not read. run() tells this from any other NOT_APPLICABLE."""
    return na(name, f"{_REFUSAL}{what}: {reason}")


def _worked_equality(a, b, ea, eb):
    """Human-readable detail SHOWING the work behind a confirmed equality (the canonical
    form both sides reduce to). Every form is computed by sympy, never fabricated."""
    try:
        ca, cb = expand(ea), expand(eb)
        if ca == cb:
            return f"{a} = {b}; both sides reduce to {ca}"
    except Exception:
        pass
    try:
        sa = simplify(ea)
        return (f"{a} = {b}; the two sides are equal -- each reduces to {sa}, "
                f"so their difference simplifies to 0")
    except Exception:
        return f"{a} = {b}; the difference simplifies to 0"


def verify_equality(spec: Dict[str, Any]) -> VerifierResult:
    _ensure_sympy()
    a = spec.get("expr_a")
    b = spec.get("expr_b")
    var_names = spec.get("variables", [])
    if a is None or b is None:
        return na("mathematics.equality")
    try:
        ea = _parse(a, var_names)
        eb = _parse(b, var_names)
        diff_ = simplify(ea - eb)
        _dm = _domain_mismatch(a, b, var_names)
        if diff_ == 0:
            if _dm:
                return mismatch("mathematics.equality",
                    f"{a} == {b} holds only off the singular set (denominator vanishes at: "
                    f"{_dm}); a removable singularity makes this NOT an unconditional "
                    f"identity (e.g. x/x is undefined at x=0)")
            return confirm("mathematics.equality", _worked_equality(a, b, ea, eb))
        if expand(ea - eb) == 0:
            if _dm:
                return mismatch("mathematics.equality",
                    f"{a} == {b} holds only off the singular set (denominator vanishes at: "
                    f"{_dm}); not an unconditional identity")
            return confirm("mathematics.equality", _worked_equality(a, b, ea, eb))
        # EXACT DECIMALS (2026-10-08, the failure report C3): "0.1 + 0.2 = 0.3" is TRUE, and IEEE-754 left
        # 5.55e-17 behind, which read as a mismatch. When both sides are plain numbers, re-read every decimal
        # as the exact rational it writes (0.1 = 1/10) and compare exactly — the same arithmetic that already
        # made 1/3 + 1/3 + 1/3 = 1 hold. Then, and only then, the claim's own precision: a claimed literal
        # stated to two or more figures earns half a unit in its last place (stated_tolerance_abs); a
        # one-figure literal earns nothing, and a structured call with no literal stays exact.
        if not getattr(ea, "free_symbols", set()) and not getattr(eb, "free_symbols", set()):
            try:
                ra, rb = _parse(a, var_names, rational=True), _parse(b, var_names, rational=True)
                if simplify(ra - rb) == 0:
                    return confirm("mathematics.equality",
                                   f"{a} = {b}; by exact rational arithmetic both sides reduce to {ra}",
                                   {"exact_rational": str(ra)})
            except NoMeaningRefused:
                raise       # undefined by exact arithmetic: the float read's window must not certify it
            except _PARSE_ERRORS:
                pass
            lit = spec.get("claimed_literal")
            tol = stated_window(lit, bool(spec.get("hedged"))) if lit not in (None, "") else None
            if tol is not None:
                try:
                    fa, fb = float(ea.evalf()), float(eb.evalf())
                except Exception:
                    fa = fb = None
                if fa is not None and abs(fa - fb) <= tol:
                    sig = (stated_precision(lit) or (0, 0.0))[0]
                    return confirm("mathematics.equality",
                                   f"{a} = {fa:.10g} agrees with {b} at the stated precision of {sig} significant "
                                   f"figure(s) (half a unit in the last place = ±{tol:g})",
                                   {"actual": fa, "claimed": fb, "stated_sigfigs": sig, "stated_tolerance_abs": tol})
        return mismatch("mathematics.equality", f"{a} - ({b}) simplifies to {diff_}")
    except _PARSE_ERRORS as e:
        return _refused("mathematics.equality", e)
    except Exception as e:
        return error("mathematics.equality", f"computation failure: {e}")


def verify_derivative(spec: Dict[str, Any]) -> VerifierResult:
    _ensure_sympy()
    f = spec.get("function")
    var = spec.get("variable", "x")
    claimed = spec.get("claimed_derivative")
    if f is None or claimed is None:
        return na("mathematics.derivative")
    try:
        x = Symbol(var)
        ef = _parse(f, [var])
        ec = _parse(claimed, [var])
        actual = diff(ef, x)
        if simplify(actual - ec) == 0:
            return confirm("mathematics.derivative", f"d/d{var} of {f} = {actual}, matches {claimed}")
        return mismatch("mathematics.derivative",
                        f"d/d{var} of {f} = {actual}, but claimed {claimed}",
                        {"computed": str(actual), "claimed": str(ec)})
    except _PARSE_ERRORS as e:
        return _refused("mathematics.derivative", e)
    except Exception as e:
        return error("mathematics.derivative", f"computation failure: {e}")


def verify_integral(spec: Dict[str, Any]) -> VerifierResult:
    _ensure_sympy()
    f = spec.get("integrand")
    var = spec.get("variable", "x")
    claimed = spec.get("claimed_antiderivative")
    if f is None or claimed is None:
        return na("mathematics.integral")
    try:
        x = Symbol(var)
        ef = _parse(f, [var])
        ec = _parse(claimed, [var])
        derivative = diff(ec, x)
        if simplify(derivative - ef) == 0:
            return confirm("mathematics.integral", f"d/d{var} of claimed antiderivative {claimed} = {ef}")
        return mismatch("mathematics.integral",
                        f"d/d{var} of {claimed} = {derivative}, expected {ef}",
                        {"derivative_of_claim": str(derivative), "integrand": str(ef)})
    except _PARSE_ERRORS as e:
        return _refused("mathematics.integral", e)
    except Exception as e:
        return error("mathematics.integral", f"computation failure: {e}")


def verify_limit(spec: Dict[str, Any]) -> VerifierResult:
    _ensure_sympy()
    f = spec.get("function")
    var = spec.get("variable", "x")
    point = spec.get("point")
    claimed = spec.get("claimed_limit")
    if f is None or point is None or claimed is None:
        return na("mathematics.limit")
    try:
        x = Symbol(var)
        ef = _parse(f, [var])
        ep = _parse(str(point), [var])
        ec = _parse(str(claimed), [var])
        actual = limit(ef, x, ep)
        if simplify(actual - ec) == 0:
            return confirm("mathematics.limit", f"lim_{{{var}->{point}}} {f} = {actual}, matches {claimed}")
        return mismatch("mathematics.limit",
                        f"lim_{{{var}->{point}}} {f} = {actual}, claimed {claimed}",
                        {"computed": str(actual), "claimed": str(ec)})
    except _PARSE_ERRORS as e:
        return _refused("mathematics.limit", e)
    except Exception as e:
        return error("mathematics.limit", f"computation failure: {e}")


def verify_solve(spec: Dict[str, Any]) -> VerifierResult:
    _ensure_sympy()
    eq = spec.get("equation")
    var = spec.get("variable", "x")
    claimed = spec.get("claimed_solutions")
    if eq is None or claimed is None:
        return na("mathematics.solve")
    try:
        x = Symbol(var)
        if "=" in eq and "==" not in eq:
            lhs, rhs = eq.split("=", 1)
            eq_expr = _parse(lhs, [var]) - _parse(rhs, [var])
        else:
            eq_expr = _parse(eq, [var])
        actual = sorted(solve(eq_expr, x), key=lambda s: str(s))
        claimed_set = sorted([_parse(str(c), [var]) for c in claimed], key=lambda s: str(s))
        if len(actual) != len(claimed_set):
            return mismatch("mathematics.solve",
                            f"solutions count mismatch: actual {actual} vs claimed {claimed_set}")
        for a, c in zip(actual, claimed_set):
            if simplify(a - c) != 0:
                return mismatch("mathematics.solve", f"solution {a} != claimed {c}",
                                {"computed": [str(s) for s in actual],
                                 "claimed": [str(s) for s in claimed_set]})
        return confirm("mathematics.solve", f"solutions {[str(s) for s in actual]} match claim")
    except _PARSE_ERRORS as e:
        return _refused("mathematics.solve", e)
    except Exception as e:
        return error("mathematics.solve", f"computation failure: {e}")


def verify_inequality(spec):
    """Verify a claimed inequality by SYMBOLIC DECISION only.

    Sampling is used solely to DISPROVE — a violation at any point makes a universal claim
    false (sound). It is NEVER used to confirm, because finite sampling can miss a violation
    between points: (x-3)**2 > 0 is false only at x=3; sin(x) <= 0.9999 only near x=pi/2.
    A truth we cannot decide symbolically is returned INCONCLUSIVE (a safe false-negative),
    never sealed as HOLDS — the 0-false-positive guarantee comes before coverage."""
    _ensure_sympy()
    import sympy as sp
    lhs, rhs = spec.get("lhs"), spec.get("rhs")
    op = spec.get("op", "<=")
    var = spec.get("variable", "x")
    if lhs is None or rhs is None:
        return na("mathematics.inequality")
    if op not in ("<", "<=", ">", ">="):
        return error("mathematics.inequality", f"bad op {op!r}")
    try:
        # SAME guards as equality (rejects '#'-truncation, giant exponents, oversized ASTs)
        L, R = _parse(lhs, [var]), _parse(rhs, [var])
    except _PARSE_ERRORS as e:
        return error("mathematics.inequality", f"parse error: {e}")
    x = sp.Symbol(var, real=True)
    L, R = L.subs(sp.Symbol(var), x), R.subs(sp.Symbol(var), x)
    diff_ = sp.simplify(L - R)
    rel = {"<=": diff_ <= 0, ">=": diff_ >= 0, "<": diff_ < 0, ">": diff_ > 0}[op]

    # 1) direct symbolic decision — settles every constant comparison and many universals
    try:
        truth = sp.simplify(rel)
        if truth is sp.true:
            return confirm("mathematics.inequality", f"{lhs} {op} {rhs} holds (symbolic)")
        if truth is sp.false:
            return mismatch("mathematics.inequality", f"{lhs} {op} {rhs} is false (symbolic)")
    except Exception:
        pass

    # 2) solution-set decision for a univariate claim over the stated domain
    dom_name = spec.get("domain", "Reals")
    dom = {"Positive": sp.Interval.open(0, sp.oo),
           "Nonneg": sp.Interval(0, sp.oo)}.get(dom_name, sp.S.Reals)
    if diff_.free_symbols <= {x}:
        try:
            sol = sp.solve_univariate_inequality(rel, x, relational=False, domain=dom)
            if dom.is_subset(sol):
                return confirm("mathematics.inequality",
                               f"{lhs} {op} {rhs} holds on {dom_name} (solved)")
            return mismatch("mathematics.inequality",
                            f"{lhs} {op} {rhs} does not hold on all of {dom_name} (solved)")
        except Exception:
            pass

    # 3) counterexample search — SOUND for disproof only (a violation => genuinely false)
    for s in (-1000, -10, -1, -0.5, 0, 0.5, 1, 10, 1000):
        try:
            if dom is not sp.S.Reals and s not in dom:
                continue
            d = float(diff_.subs(x, s))
        except Exception:
            continue
        if ((op == "<=" and d > 1e-9) or (op == "<" and d >= 0)
                or (op == ">=" and d < -1e-9) or (op == ">" and d <= 0)):
            return mismatch("mathematics.inequality", f"{lhs} {op} {rhs} fails at {var}={s}")

    # 4) genuinely inconclusive — NEVER confirm from finite sampling
    return na("mathematics.inequality",
              f"{lhs} {op} {rhs}: symbolic decision inconclusive — not sealed")


def verify_set_algebra(spec: Dict[str, Any]) -> VerifierResult:
    """Set-algebra identity — the Boole/Stone bridge (the algebra of sets IS a Boolean algebra).

    Under the correspondence union -> |, intersection -> &, complement -> ~, an identity between
    set expressions holds for ALL sets exactly when the matching propositional formula is a
    tautology (Stone's representation theorem: every Boolean algebra embeds in a field of sets).
    De Morgan, distributivity and absorption for sets are decided here by exact truth-table
    enumeration over element membership (pure standard library) — the third face of one Boolean
    algebra (logic / circuits / sets), and runnable on the sovereign stdlib-only box.

    Spec:
      variables: set names, e.g. ["A", "B", "C"] (membership of an arbitrary element)
      set_a, set_b: set expressions (& intersection, | union, ~ complement, ^ symmetric difference)
      claimed_equal: bool — are the two sets equal for every choice of A, B, C?
    """
    name = "mathematics.set_algebra"
    a = spec.get("set_a")
    b = spec.get("set_b")
    claimed = spec.get("claimed_equal")
    if a is None or b is None or claimed is None:
        return na(name)
    var_names = spec.get("variables") or []
    from ._boolean import boolean_equivalent, BooleanParseError
    try:
        # sets equal for all elements iff no membership pattern separates them
        equal = boolean_equivalent(a, b, var_names)
    except BooleanParseError as e:
        return _refused(name, e, "set expression")
    except Exception as e:  # noqa: BLE001
        return error(name, f"computation failure: {e}")
    claimed_b = bool(claimed)
    if equal == claimed_b:
        return confirm(name, f"sets {a!r} and {b!r} equal-for-all={equal}, matches claim",
                       {"set_a": a, "set_b": b, "actual": equal, "claimed": claimed_b})
    return mismatch(name, f"sets {a!r} and {b!r} equal-for-all={equal}, claimed {claimed_b}",
                    {"set_a": a, "set_b": b, "actual": equal, "claimed": claimed_b})


# <<lhs=rhs>> calculator annotations and the final '#### N', for grading GSM8K-style worked solutions.
_CALC_ANNOTATION = _re.compile(r"<<\s*(.+?)\s*=\s*(.+?)\s*>>")
_FINAL_ANSWER = _re.compile(r"####\s*([\-\d.,/]+)")

# Inline arithmetic written in prose, e.g. the final step GSM8K leaves un-bracketed:
# "99 + 5 = $104", "12/20 x 100% = 60%". The LHS must carry >=1 operator so a plain "x = 5"
# variable definition is not mistaken for a computation. Currency, percent, thousands commas and
# an 'x'/'×' multiplication sign are normalized away before parsing.
_INLINE_EQ = _re.compile(
    r"(?<![\w.)])(\$?\d[\d.,]*(?:\s*[-+*/x×]\s*\$?\d[\d.,]*)+)\s*=\s*\$?(\d[\d.,]*)")
_INLINE_X = _re.compile(r"(?<=[\d)])\s*[x×]\s*(?=[\d(])")
_THOUSANDS = _re.compile(r"(?<=\d),(?=\d\d\d(?:\D|$))")
# A matched result followed by '/n' (a fraction) or ' n/n' (a mixed number) means the true value is
# longer than the integer captured — prose arithmetic is ambiguous there, so the step is SKIPPED
# rather than graded on a truncated number. Declining beats guessing.
_FRACTION_TAIL = _re.compile(r"\s*/\s*\d|\s+\d+\s*/\s*\d")
# A matched result immediately followed by an operator is not a result but the next expression in a
# chained equality "A = B = C" (GSM8K: "4 * 60 / 5 = 4 * 12 = <<4*60/5=48>>48", where our regex
# grabs "4 * 60 / 5 = 4"). Skip it — the bracketed step still carries the real check. A result
# followed by prose ("= $300 left") is a genuine final step and stays graded.
_CHAINED_TAIL = _re.compile(r"\s*[-+*/x×]")
# Prose algebra — a coefficient-variable ("2x"), a variable in an operation ("X + 3", "X*4") or a
# parenthesized variable ("(X+80)"). A segment carrying any of these is NOT graded inline: the
# equations are symbolic and the numeric fragments ("4x - 4" -> "4 - 4") would be mis-read. Single
# trailing-letter only, so ordinals/units ("7th", "5km") do not trip it into over-matching symbols.
_ALGEBRA = _re.compile(r"\d[a-zA-Z](?![a-zA-Z])|\b[a-zA-Z]\s*[-+*/=]\s*\d|\b[a-zA-Z]\s*\*|\([a-zA-Z]")


def _norm_inline(tok: str) -> str:
    """Normalize a prose arithmetic token to something _parse accepts: drop $, 'x'->*, drop
    thousands commas. Percent signs are stripped by the caller (both sides, symmetrically)."""
    t = tok.replace("$", "").replace("×", "*")
    t = _INLINE_X.sub("*", t)
    t = _THOUSANDS.sub("", t)
    return t.strip()


def _inline_is_prose(lhs: str, rhs: str, var_names) -> bool:
    """Whether an inline equation is prose to skip, not arithmetic to grade. A refusal by the rule is not
    prose: it is arithmetic with no meaning, and dropping it would let a chain certify over a false step.
    So it is kept, and _ok reads it as unparseable."""
    try:
        L = _parse(lhs, var_names, rational=True)
        R = _parse(rhs, var_names, rational=True)
    except NoMeaningRefused:
        return False
    except _PARSE_ERRORS:
        return True  # not a parseable computation -> prose, skip (never a silent confirm)
    if getattr(L, "free_symbols", None) or getattr(R, "free_symbols", None):
        return True  # contains variables -> not a pure numeric step, skip
    return not (getattr(L, "is_number", False) and getattr(R, "is_number", False))


def _calc_chain_framing(spec: Dict[str, Any]) -> VerifierResult:
    """Kind B: when there is nothing gradeable, do not just decline — EXPLAIN why and ASK for the
    structure needed to calculate, so the caller (a person, or a proposer model) can supply the work
    and we verify it. This NEVER guesses the answer; it asks for the computation. The framing lives in
    data so a surface can render the question; the status stays NOT_APPLICABLE (nothing was verified).
    Deterministic routing by what the input looks like."""
    name = "mathematics.calc_chain"
    text = spec.get("solution_text")
    if isinstance(text, str) and _ALGEBRA.search(text):
        return na(name, "reads as an equation to SOLVE, not a worked chain to CHECK — I verify "
                  "provided work, I do not solve the problem",
                  data={"need": "equation(s), the unknown(s), and a claimed solution",
                        "framing_question": "What is the equation, and the claimed value for each "
                        "unknown? Give me equations + variables + a claimed solution and I will "
                        "verify it by substitution.",
                        "example": {"equations": ["2*x = 10"], "variables": ["x"],
                                    "claimed_solution": {"x": 5}},
                        "route": "mathematics mode=system"})
    if isinstance(text, str) and text.strip():
        return na(name, "the answer is stated in prose, not as checkable arithmetic — I grade written "
                  "steps, I do not infer the computation",
                  data={"need": "the arithmetic written as steps",
                        "framing_question": "Which quantities combine to reach the answer? Write the "
                        "arithmetic as steps (e.g. '16-3-4=9', '9*2=18') and I will check every one.",
                        "example": {"calc_steps": ["16-3-4=9", "9*2=18"], "claimed_answer": 18},
                        "route": "mathematics mode=calc_chain"})
    return na(name, "no worked solution provided to grade",
              data={"need": "calc_steps or a solution_text with the arithmetic written out",
                    "framing_question": "Give me the worked steps and I will verify each one. What "
                    "calculation reaches the answer?",
                    "example": {"calc_steps": ["16-3-4=9", "9*2=18"], "claimed_answer": 18},
                    "route": "mathematics mode=calc_chain"})


def verify_calc_chain(spec: Dict[str, Any]) -> VerifierResult:
    """Grade a worked arithmetic/algebra SOLUTION: a chain of 'lhs = rhs' steps reaching a final
    answer. Each step is checked with the SAME equality engine (simplify(lhs - rhs) == 0), so a
    single wrong step is caught; the final answer, if given, must equal the last step. Accepts
    explicit steps (calc_steps = ['16-3-4=9', '9*2=18'] or [{'lhs':.., 'rhs':..}]) OR a GSM8K-style
    solution_text with <<lhs=rhs>> calculator annotations and a '#### N' final answer. In
    solution_text, inline prose equations ("99 + 5 = $104", "12/20 x 100% = 60%") are graded too —
    not just the bracketed ones — so a solution whose final step is written in prose is still
    certified; a prose fragment that is not a pure numeric computation is skipped, never silently
    confirmed. Decimals are parsed as exact rationals, so 520/1.04 = 500 and 6*0.1 = 0.60 hold by
    exact arithmetic instead of tripping on a float's last bit. Deterministic, no NL understanding —
    it grades a worked chain, it does not solve the word problem. An opt-in step_rel_tol (clamped to
    <= 1e-2) additionally accepts steps rounded to display precision (e.g. 2/3 -> 0.67); the default
    is 0 (exact), preserving the zero-false-positive guarantee."""
    name = "mathematics.calc_chain"
    if not _ensure_sympy():
        return na(name, "requires the optional math extra (sympy)")
    var_names = spec.get("variables") or []
    # Exact by default (preserving the zero-false-positive guarantee); a caller may opt into a display
    # tolerance, but clamp_tol caps it at 1e-2 and lets it only TIGHTEN — never widen the FP window.
    tol = clamp_tol(spec, "step_rel_tol", 1e-2) if spec.get("step_rel_tol") is not None else 0.0
    claimed_answer = spec.get("claimed_answer")
    pairs: List = []
    raw = spec.get("calc_steps")
    text = spec.get("solution_text")
    if raw:
        for s in raw:
            if isinstance(s, dict) and (s.get("lhs") is not None or s.get("expr") is not None):
                pairs.append((str(s.get("lhs", s.get("expr"))), str(s.get("rhs", s.get("result")))))
            elif isinstance(s, str) and "=" in s:
                lhs, rhs = s.split("=", 1)
                pairs.append((lhs, rhs))
    elif isinstance(text, str):
        # Collect <<lhs=rhs>> annotations (authoritative) in text order, then add any inline
        # prose equations that are NOT just an echo of a bracketed step (deduped by value), so the
        # final un-bracketed step GSM8K-style solutions end on is graded too. Each entry carries its
        # text position so the merged chain stays in reading order (the final-answer check compares
        # against the LAST step).
        positioned: List = []
        seen = set()

        def _key(a: str, b: str) -> str:
            return _re.sub(r"\s+", "", a) + "=" + _re.sub(r"\s+", "", b)

        # Bracketed <<lhs=rhs>> steps are authoritative. Record them AND the text segments BETWEEN
        # them: an inline scan runs per segment, never across a bracket, so an echo
        # ("a op b = <<a op b=c>>c") splits at the boundary and matches neither side — no cross-
        # binding of an LHS before a bracket to the result after it.
        segments: List = []
        last = 0
        for m in _CALC_ANNOTATION.finditer(text):
            positioned.append((m.start(), m.group(1), m.group(2)))
            seen.add(_key(m.group(1), m.group(2)))
            segments.append((last, text[last:m.start()]))
            last = m.end()
        segments.append((last, text[last:]))
        for off, seg in segments:
            if _ALGEBRA.search(seg):
                continue  # prose algebra: variables/coefficients get mis-read -> decline the segment
            for m in _INLINE_EQ.finditer(seg):
                if "%" in seg[m.start():m.end() + 1]:
                    continue  # percent is an ambiguous operand/label ("100 * 20%", "= 50%") -> decline
                if _FRACTION_TAIL.match(seg, m.end()):
                    continue  # result is a fraction/mixed number ("= 2/5", "= 3 1/2") -> decline
                if _CHAINED_TAIL.match(seg, m.end()):
                    continue  # "A = B = C": the RHS is the next expression, not a result -> decline
                pre = seg[:m.start()].rstrip()
                if pre and (pre[-1].isdigit() or pre[-1] == ")"):
                    continue  # LHS is a fragment of a mixed number ("1 1/2") or a coefficient ("(1/2) 278")
                lhs, rhs = _norm_inline(m.group(1)), _norm_inline(m.group(2))
                if _key(lhs, rhs) in seen:
                    continue  # already counted as a bracketed step
                if _inline_is_prose(lhs, rhs, var_names):
                    continue
                seen.add(_key(lhs, rhs))
                positioned.append((off + m.start(), lhs, rhs))
        positioned.sort(key=lambda t: t[0])
        pairs = [(a, b) for _p, a, b in positioned]
        if claimed_answer is None:
            fm = _FINAL_ANSWER.search(text)
            if fm:
                claimed_answer = fm.group(1).replace(",", "")
    else:
        return _calc_chain_framing(spec)
    if not pairs:
        return _calc_chain_framing(spec)

    def _ok(lhs: str, rhs: str) -> bool:
        L, R = _parse(lhs, var_names, rational=True), _parse(rhs, var_names, rational=True)
        if simplify(L - R) == 0:
            return True
        if tol > 0:
            try:
                lf, rf = float(L), float(R)
                return _math.isfinite(lf) and _math.isfinite(rf) and abs(lf - rf) <= tol * max(1.0, abs(lf))
            except (TypeError, ValueError):
                return False
        return False

    step_failures: List[str] = []
    for i, (lhs, rhs) in enumerate(pairs):
        try:
            if not _ok(lhs, rhs):
                step_failures.append(f"step {i + 1}: {lhs.strip()} != {rhs.strip()}")
        except _PARSE_ERRORS:
            step_failures.append(f"step {i + 1}: unparseable ({lhs.strip()}={rhs.strip()})")
    final_failure = None
    if claimed_answer is not None:
        try:
            if not _ok(str(claimed_answer), pairs[-1][1]):
                final_failure = f"final answer {claimed_answer} != last step {pairs[-1][1].strip()}"
        except _PARSE_ERRORS:
            final_failure = f"final answer {claimed_answer} not comparable"
    failures = step_failures + ([final_failure] if final_failure else [])
    data = {"steps": len(pairs), "final_answer": claimed_answer, "step_rel_tol": tol,
            "chain": [f"{l.strip()}={r.strip()}" for l, r in pairs][:50]}
    # Kind B: every written step checked out, but the stated answer isn't linked to the last verified
    # value — the final step was left in prose. Don't imply the math is wrong; explain and ask for the
    # missing step so we can finish the check. (Status stays MISMATCH: nothing was certified.)
    if final_failure and not step_failures:
        data["framing_question"] = (
            f"All {len(pairs)} written steps check out, but I can't connect your answer "
            f"{claimed_answer} to the last verified value ({pairs[-1][1].strip()}) — the final step "
            f"isn't written out. Show it as 'a op b = {claimed_answer}' and I'll verify it.")
        data["need"] = "the final computation, written as a step"
    if failures:
        return mismatch(name, "; ".join(failures)[:300], data)
    tail = f"; final answer {claimed_answer}" if claimed_answer is not None else ""
    return confirm(name, f"all {len(pairs)} steps verified{tail}", data)


def verify_numeric(spec: Dict[str, Any]) -> VerifierResult:
    """Evaluate an arithmetic/numeric expression and check a claimed value — the engine as the
    verifier behind any solver (the solver proposes a number, the engine disposes). Exact via sympy,
    compared to the claim within rel_tol (default 1e-6 to accept display rounding, clamped <= 1e-2).
    Spec: {"numeric_expr": "sqrt(2) + 1", "claimed_value": 2.414214, "rel_tol": 1e-6}."""
    name = "mathematics.numeric"
    if not _ensure_sympy():
        return na(name, "requires the optional math extra (sympy)")
    expr = spec.get("numeric_expr")
    claimed = spec.get("claimed_value")
    if expr is None or claimed is None:
        return na(name)
    # clamp_tol: default 1e-6 and a caller may only TIGHTEN below it, never loosen — the earlier
    # min(..., 1e-2) let a caller widen the match window to 1e-2 (the FP-widening hole clamp_tol closes).
    rel_tol = clamp_tol(spec, "rel_tol", 1e-6)
    try:
        val = _parse(str(expr), spec.get("variables") or [])
        fv = float(val.evalf() if hasattr(val, "evalf") else val)
        cv = float(claimed)
    except _PARSE_ERRORS as e:
        return error(name, f"could not evaluate {expr!r}: {type(e).__name__}")
    except (TypeError, ValueError):
        return mismatch(name, f"{expr} is not a pure number (has free symbols?)", {"expr": str(expr)})
    if not _math.isfinite(fv):      # past a float, or infinite: no window around it can mean anything
        if _math.isfinite(cv):      # and no finite claim equals it, which does prove this one false
            return mismatch(name, f"{expr} is not finite as a float, so no finite claim equals it", {"expr": str(expr)})
        return error(name, f"{expr} is not finite as a float, so it cannot be compared with {cv}")
    if not _math.isfinite(cv):      # before any window: at the top of the float range a window's own edge is infinite
        return mismatch(name, f"{expr} is finite, and the claim {cv} is not", {"expr": str(expr)})
    diff = abs(fv - cv)
    threshold = rel_tol * max(1.0, abs(fv))
    strict_threshold = threshold   # the exact-match window, before any stated-precision widening below
    data = {"expr": str(expr), "computed": fv, "claimed": cv, "rel_tol": rel_tol, "abs_diff": diff}
    # STATED PRECISION (2026-10-07), as physical_constants keeps it: the literal as the person wrote it
    # ("1.41421") earns half a unit in its last stated place — two or more significant figures only, so a
    # one-figure "1" never passes as sqrt(2). Only the claim's own literal can widen the window; a structured
    # caller that sends no literal keeps the strict default unchanged (clamp_tol still only tightens).
    stated_used = False
    lit = spec.get("claimed_literal")
    if lit is not None:
        # THE ONE RULE (2026-10-08, H6): the stated window replaces the flat default; a hedge doubles it; a
        # one-figure claim is exact without a hedge (window_for).
        threshold, info = window_for(spec, "claimed_literal", threshold, 1.0, fv)
        data.update(info)
        data["stated_tolerance"] = threshold
        stated_used = True
    if diff <= threshold:
        # EXPLAIN WHY IT IS WHAT IT IS (2026-10-09): a certification must say whether the claim is EXACT or only
        # correct to the precision stated. A bare "holds" on "sqrt(150) is 12" reads as an equality; it is not
        # (sqrt(150) = 12.2474). So when the claim holds only through the stated-precision window, the verdict names
        # it an APPROXIMATION and gives the exact value, so no reader mistakes "to 2 s.f." for "equals".
        exact = diff <= strict_threshold
        data["exact"] = bool(exact)
        if stated_used and not exact:
            sig = data.get("stated_sigfigs")
            data["approximation"] = True
            return confirm(name, f"{expr} = {fv:.10g}, and your '{lit}' is correct to the {sig} significant "
                                 f"figure(s) you wrote — but it is an APPROXIMATION, not exact: the exact value is "
                                 f"{fv:.10g}, not {cv}.", data)
        if stated_used:
            return confirm(name, f"{expr} = {fv:.10g} — the claim {cv} is exact (to the "
                                 f"{data.get('stated_sigfigs')} significant figure(s) stated).", data)
        if not exact:
            data["approximation"] = True
            return confirm(name, f"{expr} = {fv:.10g}, which the claim {cv} matches within {rel_tol:.0e} "
                                 f"(display rounding; the exact value is {fv:.10g}).", data)
        return confirm(name, f"{expr} = {fv:.10g} — the claim {cv} is exact.", data)
    return mismatch(name, f"{expr} = {fv:.10g}, claimed {cv} — off by {diff:.4g}.", data)


def verify_number_theory(spec: Dict[str, Any]) -> VerifierResult:
    """Number-theory claims — gcd, lcm, primality, factorial, binomial, modulo — checked exactly.
    Spec (any one): {"gcd": [12, 18], "claimed_gcd": 6} · {"lcm": [4, 6], "claimed_lcm": 12} ·
    {"is_prime": 17, "claimed_prime": true} · {"factorial": 5, "claimed_factorial": 120} ·
    {"binomial": [5, 2], "claimed_binomial": 10} · {"modulo": [17, 5], "claimed_modulo": 2}."""
    name = "mathematics.number_theory"
    if not _ensure_sympy():
        return na(name, "requires the optional math extra (sympy)")
    from sympy import igcd, ilcm, isprime, factorial as _fact, binomial as _binom
    try:
        if "gcd" in spec and "claimed_gcd" in spec:
            a = [int(x) for x in spec["gcd"]]
            actual, claimed, label = igcd(*a), int(spec["claimed_gcd"]), f"gcd{tuple(a)}"
        elif "lcm" in spec and "claimed_lcm" in spec:
            a = [int(x) for x in spec["lcm"]]
            actual, claimed, label = ilcm(*a), int(spec["claimed_lcm"]), f"lcm{tuple(a)}"
        elif "is_prime" in spec and "claimed_prime" in spec:
            actual, claimed, label = bool(isprime(int(spec["is_prime"]))), bool(spec["claimed_prime"]), f"isprime({spec['is_prime']})"
        elif "factorial" in spec and "claimed_factorial" in spec:
            actual, claimed, label = int(_fact(int(spec["factorial"]))), int(spec["claimed_factorial"]), f"{spec['factorial']}!"
        elif "binomial" in spec and "claimed_binomial" in spec:
            n, k = int(spec["binomial"][0]), int(spec["binomial"][1])
            actual, claimed, label = int(_binom(n, k)), int(spec["claimed_binomial"]), f"C({n},{k})"
        elif "modulo" in spec and "claimed_modulo" in spec:
            a, m = int(spec["modulo"][0]), int(spec["modulo"][1])
            actual, claimed, label = a % m, int(spec["claimed_modulo"]), f"{a} mod {m}"
        else:
            return na(name)
    except (TypeError, ValueError, IndexError) as e:
        return error(name, f"malformed number-theory input: {e}")
    data = {"claim": label, "actual": actual, "claimed": claimed}
    if actual == claimed:
        return confirm(name, f"{label} = {actual}", data)
    return mismatch(name, f"{label} = {actual}, claimed {claimed}", data)


def verify_system(spec: Dict[str, Any]) -> VerifierResult:
    """A claimed solution to a SYSTEM of equations — verified by substitution (each equation must
    hold), so no solver ambiguity and no false positive. Spec: {"equations": ["x + y = 3",
    "x - y = 1"], "variables": ["x", "y"], "claimed_solution": {"x": 2, "y": 1}}."""
    name = "mathematics.system"
    if not _ensure_sympy():
        return na(name, "requires the optional math extra (sympy)")
    eqs = spec.get("equations")
    claimed = spec.get("claimed_solution")
    var_names = spec.get("variables") or (list(claimed.keys()) if isinstance(claimed, dict) else [])
    if not eqs or not isinstance(claimed, dict):
        return na(name)
    try:
        subs = {Symbol(k): _parse(str(v), var_names) for k, v in claimed.items()}
    except _PARSE_ERRORS as e:
        return error(name, f"unparseable claimed value: {type(e).__name__}")
    failures = []
    for eq in eqs:
        if "=" not in str(eq):
            return error(name, f"equation has no '=': {eq!r}")
        lhs, rhs = str(eq).split("=", 1)
        try:
            if simplify((_parse(lhs, var_names) - _parse(rhs, var_names)).subs(subs)) != 0:
                failures.append(str(eq).strip())
        except _PARSE_ERRORS:
            return error(name, f"unparseable equation: {eq!r}")
    data = {"equations": [str(e).strip() for e in eqs], "claimed_solution": claimed}
    if failures:
        return mismatch(name, "solution fails: " + "; ".join(failures)[:200], data)
    return confirm(name, f"claimed solution satisfies all {len(eqs)} equations", data)


_RULES = [
    (lambda mv: ("calc_steps" in mv or "solution_text" in mv), verify_calc_chain),
    (lambda mv: ("numeric_expr" in mv and "claimed_value" in mv), verify_numeric),
    (lambda mv: any(k in mv for k in ("gcd", "lcm", "is_prime", "factorial", "binomial", "modulo")), verify_number_theory),
    (lambda mv: ("equations" in mv and "claimed_solution" in mv), verify_system),
    (lambda mv: ("expr_a" in mv and "expr_b" in mv), verify_equality),
    (lambda mv: ("set_a" in mv and "set_b" in mv and "claimed_equal" in mv), verify_set_algebra),
    (lambda mv: ("function" in mv and "claimed_derivative" in mv), verify_derivative),
    (lambda mv: ("integrand" in mv and "claimed_antiderivative" in mv), verify_integral),
    (lambda mv: ("function" in mv and "point" in mv and "claimed_limit" in mv), verify_limit),
    (lambda mv: ("equation" in mv and "claimed_solutions" in mv), verify_solve),
    (lambda mv: ("lhs" in mv and "rhs" in mv and "op" in mv), verify_inequality),
]


GOLDEN_PACKET_KEY = "MATH_VERIFY"  # dispatch()-routed, so the auto-detector needs this named
GOLDEN_EXAMPLE = {"function": "x**2", "variable": "x", "claimed_derivative": "2*x"}  # d/dx x^2 = 2x


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    results = dispatch(packet, 'MATH_VERIFY', _RULES, domain='mathematics', none_reason='no MATH_VERIFY artifacts present')
    if any(r.status == "NOT_APPLICABLE" and r.detail.startswith(_REFUSAL) for r in results):
        # As in physics: a step's status drops NOT_APPLICABLE, so a passing check beside a refused text would read
        # the whole packet as HOLDS, and it goes. A MISMATCH or an error stands, so a refused text hides no false claim.
        return [r for r in results if r.status != "CONFIRMED"]
    return results
