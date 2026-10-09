"""Get fairly close, with a PROVEN bound — the set path's approximation step.

Matt, 2026-10-09: "What we need is a way to get fairly close." -> "build". The barriers (on the P vs NP stick) say an
exact answer cannot always be found by rule. This is the rule for getting CLOSE: do not search from nothing - anchor
on a point known exactly, take ONE step toward the target, and bound the step. The anchor carries the truth; the step
carries the error; "fairly close" is the step and its length is the bound.

Two anchors, one shape:
  * a KNOWN elementary function (sqrt, exp, ln, sin, cos, 1/x): the engine computes f(x0), f'(x0), a true sup of
    |f''| on the interval, and the exact f(x) - the whole bounded estimate is checked end to end.
  * ANY function: the caller supplies the anchor value f(x0), the slope f'(x0) and a bound on the curvature
    (second_bound = sup|f''|), or a Lipschitz bound (lipschitz = sup|f'|) for a zeroth-order estimate; the engine
    computes the interval, and if a true value is given, confirms it lies inside.

The estimate is the anchor plus one step (f0 + f1*(x-x0)); the bound is a THEOREM, not a hope:
  Taylor with Lagrange remainder: |f(x) - (f0 + f1*(x-x0))| <= (sup|f''|) (x-x0)^2 / 2.
  Lipschitz (zeroth order):       |f(x) - f0|                <= (sup|f'|)  |x-x0|.
Nothing is generated: found from the anchor and the variation bound, and a stated closeness claim that the true value
does NOT satisfy is a MISMATCH (0 false positives) - the engine never calls a thing close that is not.

Artifact: APPROX_VERIFY = {
  "anchor": x0, "target": x,
  "func": "sqrt"|"exp"|"ln"|"log"|"sin"|"cos"|"recip",      # OR supply the pieces below
  "anchor_value": f(x0), "slope": f'(x0), "second_bound": sup|f''|,   # general, first order
  "lipschitz": sup|f'|,                                              # general, zeroth order (no slope)
  "true_value": f(x),                                                # optional: confirm the bound holds
  "claimed_value": v, "claimed_error": e,                            # optional: check a closeness claim "within e of v"
}
"""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Tuple

from .base import VerifierResult, confirm, dispatch, error, mismatch, na

_EPS = 1e-12


def _known(name: str) -> Optional[Tuple[Callable, Callable, Callable]]:
    """f, f', and sup|f''| over the closed interval [min(a,b), max(a,b)], for the elementary functions whose
    derivatives are known in closed form. The sup is taken where |f''| is largest on a monotone interval."""
    n = (name or "").strip().lower()
    F: Dict[str, Tuple[Callable, Callable, Callable]] = {
        # |f''| = 1/(4 x^1.5), decreasing -> sup at the smaller x
        "sqrt": (math.sqrt, lambda x: 0.5 / math.sqrt(x), lambda a, b: 0.25 / (min(a, b) ** 1.5)),
        # f'' = e^x, increasing -> sup at the larger x
        "exp": (math.exp, math.exp, lambda a, b: math.exp(max(a, b))),
        # |f''| = 1/x^2, decreasing -> sup at the smaller x
        "ln": (math.log, lambda x: 1.0 / x, lambda a, b: 1.0 / (min(a, b) ** 2)),
        "log": (math.log, lambda x: 1.0 / x, lambda a, b: 1.0 / (min(a, b) ** 2)),
        # |f''| = |sin|, |cos| <= 1
        "sin": (math.sin, math.cos, lambda a, b: 1.0),
        "cos": (math.cos, lambda x: -math.sin(x), lambda a, b: 1.0),
        # |f''| = 2/|x|^3, decreasing in |x| -> sup at the smaller |x|
        "recip": (lambda x: 1.0 / x, lambda x: -1.0 / (x * x), lambda a, b: 2.0 / (min(abs(a), abs(b)) ** 3)),
    }
    return F.get(n)


def _domain_ok(func: str, x0: float, x: float) -> Tuple[bool, str]:
    n = (func or "").strip().lower()
    lo, hi = min(x0, x), max(x0, x)
    if n in ("sqrt", "ln", "log") and lo <= 0:
        return False, f"{n} needs a positive interval; got [{lo}, {hi}]"
    if n == "recip" and lo <= 0 <= hi:
        return False, "1/x: the interval straddles the singularity at 0"
    return True, ""


def verify_get_close(a: Dict[str, Any]) -> VerifierResult:
    name = "approximation.get_close"
    try:
        x0 = float(a["anchor"]); x = float(a["target"])
    except (KeyError, TypeError, ValueError):
        return error(name, "need numeric 'anchor' and 'target'")
    func = a.get("func")
    known = _known(func) if func else None
    true: Optional[float] = None
    M: Optional[float] = None
    L: Optional[float] = None
    try:
        if known:
            ok, why = _domain_ok(func, x0, x)
            if not ok:
                return error(name, why)
            f, fp, f2 = known
            f0 = f(x0); f1 = fp(x0); M = f2(x0, x); true = f(x)
        else:
            if "anchor_value" not in a:
                return na(name, "no known 'func' and no 'anchor_value' — nothing to anchor on")
            f0 = float(a["anchor_value"]); f1 = float(a.get("slope", 0.0))
            if "second_bound" in a:
                M = abs(float(a["second_bound"]))
            elif "lipschitz" in a:
                L = abs(float(a["lipschitz"]))
            else:
                return error(name, "need 'second_bound' (sup|f''|) or 'lipschitz' (sup|f'|)")
            if "true_value" in a:
                true = float(a["true_value"])
    except (TypeError, ValueError, ZeroDivisionError, OverflowError) as e:
        return error(name, f"could not evaluate the anchor/target: {e}")

    h = x - x0
    if M is not None:
        est = f0 + f1 * h
        err = M * h * h / 2.0
        order = 1
        guarantee = "Taylor + Lagrange remainder: |f(x) - (f0 + f1·(x-x0))| <= sup|f''|·(x-x0)^2/2"
    else:
        est = f0
        err = L * abs(h)
        order = 0
        guarantee = "Lipschitz: |f(x) - f0| <= sup|f'|·|x-x0|"
    lo, hi = est - err, est + err
    data: Dict[str, Any] = {"estimate": est, "error_bound": err, "lo": lo, "hi": hi, "order": order,
                            "anchor": x0, "target": x, "step": h, "actual": est}
    if true is not None:
        actual = abs(true - est)
        data["true_value"] = true; data["actual_error"] = actual
        if actual > err + _EPS * (1.0 + abs(err)):
            return mismatch(name, f"the bound does NOT hold: |true - estimate| = {actual:.3e} > {err:.3e} — the "
                                  f"supplied curvature/Lipschitz bound is too small for this interval", data)
    # a stated closeness CLAIM, checked (0 false positives): "f(x) is within claimed_error of claimed_value"
    if "claimed_value" in a and "claimed_error" in a:
        try:
            cv = float(a["claimed_value"]); ce = float(a["claimed_error"])
        except (TypeError, ValueError):
            return error(name, "claimed_value / claimed_error must be numeric")
        if ce < 0:
            return error(name, "claimed_error must be non-negative")
        ref = true if true is not None else est
        what = "true value" if true is not None else "bounded estimate"
        gap = abs(ref - cv)
        if gap > ce + _EPS * (1.0 + abs(ce)):
            return mismatch(name, f"NOT within the claimed bound: |{what} {ref:.10g} − {cv:g}| = {gap:.3e} > "
                                  f"claimed {ce:.3e}", data)
        return confirm(name, f"within bound: {cv:g} ± {ce:g} contains the {what} {ref:.10g} (gap {gap:.3e}); "
                             f"get close gave {est:.10g} ± {err:.3e}, anchored at f({x0:g})", data)
    inside = f"; true f(x) = {true:.12g}, inside by {err - abs(true - est):.3e}" if true is not None else ""
    return confirm(name, f"get close: f({x:g}) ≈ {est:.12g} ± {err:.3e} (order {order}), interval "
                         f"[{lo:.12g}, {hi:.12g}], anchored at f({x0:g}) = {f0:.12g}. {guarantee}{inside}", data)


_RULES = [
    (lambda a: ("anchor" in a and "target" in a), verify_get_close),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "APPROX_VERIFY", _RULES, domain="approximation",
                    none_reason="no APPROX_VERIFY artifacts present")
