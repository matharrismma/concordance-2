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
import re as _re
from typing import Any, Dict, List

from .base import VerifierResult, confirm, error, mismatch, na
from .base import dispatch  # declarative run() driver

sympify = simplify = diff = integrate = limit = solve = None
Symbol = oo = S = expand = _SympifyError = None
_PARSE_ERRORS = (SyntaxError, TypeError, ValueError, NotImplementedError)
_sympy_loaded = False
_sympy_ok = None  # None = untried; True/False after first attempt


def _ensure_sympy() -> bool:
    """Import sympy on first use. Idempotent. Returns True if sympy is available, False on a
    stdlib-only box (the optional `math` extra is not installed). Callers degrade to a clean
    NOT_APPLICABLE — the symbolic checks genuinely need sympy — rather than crash, so the engine
    keeps running offline. (set_algebra does not need sympy; it uses the pure-stdlib engine.)"""
    global sympify, simplify, diff, integrate, limit, solve
    global Symbol, oo, S, expand, _SympifyError, _PARSE_ERRORS, _sympy_loaded, _sympy_ok
    if _sympy_loaded:
        return _sympy_ok
    try:
        from sympy import (
            sympify as _f, simplify as _s, diff as _d, integrate as _i,
            limit as _l, solve as _so, Symbol as _Sy, oo as _oo, S as _S, expand as _e,
        )
        from sympy.core.sympify import SympifyError as _SE
        sympify, simplify, diff, integrate = _f, _s, _d, _i
        limit, solve, Symbol, oo, S, expand = _l, _so, _Sy, _oo, _S, _e
        _SympifyError = _SE
        _PARSE_ERRORS = (_SE, SyntaxError, TypeError, ValueError, NotImplementedError)
        _sympy_ok = True
    except ModuleNotFoundError:
        _sympy_ok = False
    _sympy_loaded = True
    return _sympy_ok


# Characters that are NOT part of any valid math expression string. sympify treats
# '#' as a comment, silently dropping the rest — reject such inputs early.
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
_MAX_AST_NODES = 2000
_MAX_AST_DEPTH = 60

# SECURITY (red team 2026-08-06, CRITICAL): sympy.sympify() EVALUATES arbitrary Python — an
# expr like "__import__('os').system(...)" was an unauthenticated RCE reachable from public
# POST /verify (the flagship math path). The old blacklist missed '.', '_', '(', quotes. The guard
# below is now an ALLOWLIST over the parsed AST: only pure mathematics reaches sympify. An escape
# needs a sink (eval/open/getattr/attribute) or a way to NAME a target (a string/dunder) — all are
# refused here, so the type-graph and import escapes cannot be expressed. A missing function name
# yields INCOMPLETE (an honest gap), never a false verdict — add names here as real math needs them.
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
    "radsimp", "nsimplify", "N", "evalf", "Poly", "degree", "solve", "solveset", "roots",
    # matrices
    "Matrix", "ImmutableMatrix", "eye", "zeros", "ones", "diag", "Transpose", "det", "trace",
    "Determinant", "Trace", "Inverse", "transpose",
    # containers sympy constructors sometimes need
    "Tuple", "Interval", "FiniteSet", "S",
})

_UNSAFE_NODES = (_ast.Attribute, _ast.Lambda, _ast.ListComp, _ast.SetComp, _ast.DictComp,
                 _ast.GeneratorExp, _ast.Await, _ast.Yield, _ast.YieldFrom, _ast.NamedExpr,
                 _ast.Starred, _ast.JoinedStr, _ast.FormattedValue, _ast.Import, _ast.ImportFrom)


def _ast_compute_guard(expr: str):
    """Reject pathological AND dangerous inputs before SymPy evaluates them: giant exponents /
    power towers / oversized trees (DoS), and — critically — anything that is not pure mathematics
    (attribute access, string literals, underscore/dunder names, lambdas/comprehensions, or a call
    to a non-mathematical function), which would be arbitrary code execution via sympify. Raises
    _SympifyError on rejection. An input Python cannot parse is rejected (never passed to eval)."""
    try:
        tree = _ast.parse(str(expr), mode="eval")
    except SyntaxError:
        raise _SympifyError("expression is not parseable as mathematics")
    n = 0
    for node in _ast.walk(tree):
        n += 1
        if n > _MAX_AST_NODES:
            raise _SympifyError("expression too large")
        if isinstance(node, _UNSAFE_NODES):
            raise _SympifyError("expression contains a non-mathematical construct")
        if isinstance(node, _ast.Constant) and isinstance(node.value, (str, bytes)):
            raise _SympifyError("string literals are not allowed in a math expression")
        if isinstance(node, _ast.Name) and node.id.startswith("_"):
            raise _SympifyError("names beginning with underscore are not allowed")
        if isinstance(node, _ast.Call):
            fn = node.func
            if not isinstance(fn, _ast.Name) or fn.id not in _ALLOWED_FUNCS:
                raise _SympifyError("call to a non-mathematical function is not allowed")
        if isinstance(node, _ast.BinOp) and isinstance(node.op, _ast.Pow):
            ex = node.right
            val = None
            if isinstance(ex, _ast.Constant) and isinstance(ex.value, (int, float)):
                val = ex.value
            elif isinstance(ex, _ast.UnaryOp) and isinstance(ex.operand, _ast.Constant) \
                    and isinstance(ex.operand.value, (int, float)):
                val = ex.operand.value
            if val is not None and abs(val) > _MAX_POW_EXP:
                raise _SympifyError("exponent too large")
            for sub in _ast.walk(ex):
                if isinstance(sub, _ast.BinOp) and isinstance(sub.op, _ast.Pow):
                    raise _SympifyError("nested power tower not allowed")

    def _depth(nd):
        return 1 + max((_depth(c) for c in _ast.iter_child_nodes(nd)), default=0)
    if _depth(tree) > _MAX_AST_DEPTH:
        raise _SympifyError("expression too deeply nested")


def _parse(expr: str, var_names: List[str] = None, rational: bool = False):
    if not _ensure_sympy():
        # stdlib-only box: the symbolic-math checks need sympy. Raise a _PARSE_ERRORS member so
        # every verify_* wrapper degrades to NOT_APPLICABLE with this reason, never a crash.
        raise ValueError("requires the optional math extra (sympy); not installed on this box")
    # Strip surrounding whitespace: ast.parse(..., mode="eval") rejects leading/trailing space as an
    # IndentationError, so a split like "x + y = 3" -> " 3" would otherwise fail to parse.
    expr = _MOD_WORD_RE.sub("%", str(expr)).strip()
    if _INVALID_EXPR_RE.search(str(expr)):
        raise _SympifyError(f"invalid characters in expression: {expr!r}")
    _ast_compute_guard(expr)
    locals_ = {n: Symbol(n) for n in (var_names or [])}
    locals_.setdefault("oo", oo)
    locals_.setdefault("inf", oo)
    # rational=True parses decimals as EXACT rationals (0.1 -> 1/10), so a chain like 520/1.04 = 500
    # or 6*0.1 = 0.60 is TRUE by exact arithmetic rather than tripping on the last IEEE-754 bit. This
    # TIGHTENS exactness (no float wobble); it never loosens it. Default off to leave every symbolic
    # caller (equality/derivative/limit/series) unchanged.
    return sympify(expr, locals=locals_, rational=rational)


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
    the domains match. Re-parses with evaluate=False so x/x is not auto-reduced to 1
    before its pole can be seen."""
    try:
        locals_ = {n: Symbol(n) for n in (var_names or [])}
        locals_.setdefault("oo", oo)
        locals_.setdefault("inf", oo)
        ra = sympify(a_str, locals=locals_, evaluate=False)
        rb = sympify(b_str, locals=locals_, evaluate=False)
    except Exception:
        return None
    pa, pb = _pole_bases(ra), _pole_bases(rb)
    if pa == pb:
        return None
    diff_ = pa.symmetric_difference(pb)
    return ", ".join(sorted(str(p) for p in diff_)) if diff_ else None


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
        return mismatch("mathematics.equality", f"{a} - ({b}) simplifies to {diff_}")
    except _PARSE_ERRORS as e:
        return na("mathematics.equality", f"cannot parse expression: {e}")
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
        return na("mathematics.derivative", f"cannot parse expression: {e}")
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
        return na("mathematics.integral", f"cannot parse expression: {e}")
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
        return na("mathematics.limit", f"cannot parse expression: {e}")
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
        return na("mathematics.solve", f"cannot parse expression: {e}")
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
        return na(name, f"cannot parse set expression: {e}")
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
    try:
        tol = min(abs(float(spec.get("step_rel_tol", 0.0) or 0.0)), 1e-2)
    except (TypeError, ValueError):
        tol = 0.0
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
                try:
                    L = _parse(lhs, var_names, rational=True)
                    R = _parse(rhs, var_names, rational=True)
                except _PARSE_ERRORS:
                    continue  # not a parseable computation -> prose, skip (never a silent confirm)
                if getattr(L, "free_symbols", None) or getattr(R, "free_symbols", None):
                    continue  # contains variables -> not a pure numeric step, skip
                if not (getattr(L, "is_number", False) and getattr(R, "is_number", False)):
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
                return abs(lf - rf) <= tol * max(1.0, abs(lf))
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
    try:
        rel_tol = min(abs(float(spec.get("rel_tol", 1e-6))), 1e-2)
    except (TypeError, ValueError):
        rel_tol = 1e-6
    try:
        val = _parse(str(expr), spec.get("variables") or [])
        fv = float(val.evalf() if hasattr(val, "evalf") else val)
        cv = float(claimed)
    except _PARSE_ERRORS as e:
        return error(name, f"could not evaluate {expr!r}: {type(e).__name__}")
    except (TypeError, ValueError):
        return mismatch(name, f"{expr} is not a pure number (has free symbols?)", {"expr": str(expr)})
    data = {"expr": str(expr), "computed": fv, "claimed": cv, "rel_tol": rel_tol,
            "abs_diff": abs(fv - cv)}
    if abs(fv - cv) <= rel_tol * max(1.0, abs(fv)):
        return confirm(name, f"{expr} = {fv:.10g} (claim {cv}, within {rel_tol:.0e})", data)
    return mismatch(name, f"{expr} = {fv:.10g}, claimed {cv}", data)


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
    return dispatch(packet, 'MATH_VERIFY', _RULES, domain='mathematics', none_reason='no MATH_VERIFY artifacts present')
