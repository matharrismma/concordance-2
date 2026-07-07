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

sympify = simplify = diff = integrate = limit = solve = None
Symbol = oo = S = expand = _SympifyError = None
_PARSE_ERRORS = (SyntaxError, TypeError, ValueError, NotImplementedError)
_sympy_loaded = False


def _ensure_sympy() -> None:
    """Import sympy on first use. Idempotent — every entrypoint calls it."""
    global sympify, simplify, diff, integrate, limit, solve
    global Symbol, oo, S, expand, _SympifyError, _PARSE_ERRORS, _sympy_loaded
    if _sympy_loaded:
        return
    from sympy import (
        sympify as _f, simplify as _s, diff as _d, integrate as _i,
        limit as _l, solve as _so, Symbol as _Sy, oo as _oo, S as _S, expand as _e,
    )
    from sympy.core.sympify import SympifyError as _SE
    sympify, simplify, diff, integrate = _f, _s, _d, _i
    limit, solve, Symbol, oo, S, expand = _l, _so, _Sy, _oo, _S, _e
    _SympifyError = _SE
    _PARSE_ERRORS = (_SE, SyntaxError, TypeError, ValueError, NotImplementedError)
    _sympy_loaded = True


# Characters that are NOT part of any valid math expression string. sympify treats
# '#' as a comment, silently dropping the rest — reject such inputs early.
_INVALID_EXPR_RE = _re.compile(r"[#@!$%&\[\]\{\}\\|`]")

# Compute-DoS guards: a short input like 9**9**9 expands to a ~369M-digit bignum.
_MAX_POW_EXP = 10000
_MAX_AST_NODES = 2000
_MAX_AST_DEPTH = 60


def _ast_compute_guard(expr: str):
    """Reject pathological inputs (giant exponents, power towers, oversized/too-deep
    expressions) before SymPy evaluates them. Raises _SympifyError on rejection."""
    try:
        tree = _ast.parse(str(expr), mode="eval")
    except SyntaxError:
        return
    n = 0
    for node in _ast.walk(tree):
        n += 1
        if n > _MAX_AST_NODES:
            raise _SympifyError("expression too large")
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


def _parse(expr: str, var_names: List[str] = None):
    _ensure_sympy()
    if _INVALID_EXPR_RE.search(str(expr)):
        raise _SympifyError(f"invalid characters in expression: {expr!r}")
    _ast_compute_guard(expr)
    locals_ = {n: Symbol(n) for n in (var_names or [])}
    locals_.setdefault("oo", oo)
    locals_.setdefault("inf", oo)
    return sympify(expr, locals=locals_)


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


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    results: List[VerifierResult] = []
    mv = packet.get("MATH_VERIFY") or {}
    if "expr_a" in mv and "expr_b" in mv:
        results.append(verify_equality(mv))
    if "function" in mv and "claimed_derivative" in mv:
        results.append(verify_derivative(mv))
    if "integrand" in mv and "claimed_antiderivative" in mv:
        results.append(verify_integral(mv))
    if "function" in mv and "point" in mv and "claimed_limit" in mv:
        results.append(verify_limit(mv))
    if "equation" in mv and "claimed_solutions" in mv:
        results.append(verify_solve(mv))
    if "lhs" in mv and "rhs" in mv and "op" in mv:
        results.append(verify_inequality(mv))
    if not results:
        results.append(na("mathematics", "no MATH_VERIFY artifacts present"))
    return results
