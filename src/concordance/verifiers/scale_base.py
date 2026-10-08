"""Shared helper for the constant-anchored scale libraries.

The comparison of a computed constant-anchored quantity against a claimed value is identical across
every scale library (alpha_scale, grav_scale, rela_scale, thermal_scale, planck_scale, molar_scale),
so it lives here ONCE. Each *_scale module exposes a thin compare() that calls this with its own
constant as the `anchor`, so the trail records which constant grounded the check.

Not a verifier (no run(), not registered) — a shared library the scale libraries call.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

from .base import VerifierResult, confirm, mismatch, error, stated_precision, stated_tolerance_abs, stated_window


def compare(name: str, actual: float, claimed: Any, rel_tol: float, data: Dict[str, Any],
            anchor: Optional[Tuple[str, float]] = None, as_written: Optional[str] = None,
            unit_factor: float = 1.0, hedged: bool = False) -> VerifierResult:
    """Confirm/mismatch on a computed quantity vs a claimed value. Fail-closed on bad input.

    `anchor` = (constant_name, constant_value); when given it is recorded in the trail so the seal
    shows which constant grounded the check. `data["formula"]`, if present, labels the value.

    `as_written` (2026-10-07) is the claimed number exactly as the person stated it ("11.2"), in a unit
    `unit_factor` times the computed unit (km/s -> 1000). It lets the check honour STATED PRECISION: a
    claim right to every figure it states is confirmed even when the flat rel_tol would refuse it.
    Only the claim's own literal can widen the window, never a tolerance handed in — and never on a
    single stated figure (verifiers.base.stated_tolerance_abs).
    """
    try:
        cl = float(claimed)
    except (TypeError, ValueError):
        return error(name, "claimed value must be numeric")
    if not math.isfinite(actual) or actual == 0:
        return error(name, "computed value is not usable")
    rel = abs(actual - cl) / abs(actual)
    d = {**data, "computed": actual, "claimed": cl, "rel_tol": rel_tol, "rel_diff": rel}
    if anchor:
        d[anchor[0]] = anchor[1]
    label = data.get("formula", name)
    if as_written:
        # THE ONE RULE (2026-10-08, H6): a stated literal sets the window — doubled by a hedge, exact for a
        # one-figure claim without one — and the flat rel_tol no longer passes a prose claim first.
        tol = stated_window(as_written, hedged, unit_factor)
        sp = stated_precision(as_written)
        d["stated_sigfigs"] = sp[0] if sp else None
        d["hedged"] = bool(hedged)
        d["stated_tolerance"] = tol if tol is not None else 0.0
        if tol is not None and abs(actual - cl) <= tol:
            return confirm(name, f"{label} = {actual:.6g} — matches {as_written} to the {sp[0] if sp else '?'} "
                                 f"significant figure(s) stated{' (hedged)' if hedged else ''} (exact {actual:.6g})", d)
        if tol is None and abs(actual - cl) <= 1e-9 * abs(actual):
            return confirm(name, f"{label} = {actual:.6g} (matches {cl} exactly)", d)
        return mismatch(name, f"{label} = {actual:.6g}, claimed {cl} (stated to {sp[0] if sp else '?'} figure(s)"
                              f"{' with a hedge' if hedged else ''}: window ±{tol if tol is not None else 0:g})", d)
    if rel <= rel_tol:
        return confirm(name, f"{label} = {actual:.6g} (matches {cl}, rel {rel:.1e})", d)
    return mismatch(name, f"{label} = {actual:.6g}, claimed {cl} (rel {rel:.1e} > {rel_tol:.0e})", d)
