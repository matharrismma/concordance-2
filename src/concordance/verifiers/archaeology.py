"""Archaeology verifier — dating the past by the same decay law the physics uses.

Public-domain checks:

  * archaeology.radiocarbon — age from the surviving fraction of carbon-14
        t = -(T_half / ln 2) · ln(fraction),  fraction = N/N0,  T_half = 5730 yr
  * archaeology.radiometric — the same clock for any isotope (given its half-life)
        t = -(T_half / ln 2) · ln(fraction)
  * archaeology.half_lives_elapsed — how many half-lives a fraction represents
        n = -log2(fraction)

ARCH_VERIFY packet (any subset):
    {
      "fraction_remaining": 0.25, "claimed_age_years": 11460,
      "fraction_remaining_iso": 0.5, "half_life_years": 1250, "claimed_age_years_iso": 1250,
      "fraction_for_halflives": 0.125, "claimed_half_lives": 3,
    }
"""
from __future__ import annotations
import math
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol
from .base import dispatch

_C14_HALFLIFE = 5730.0   # years (Libby/Cambridge convention; 5730 standard)
_LN2 = math.log(2.0)


def _close(actual: float, claimed: float, rel_tol: float = 1e-2, abs_tol: float = 1.0) -> bool:
    return abs(actual - claimed) <= max(abs_tol, rel_tol * abs(actual))


def verify_radiocarbon(spec: Dict[str, Any]) -> VerifierResult:
    """t = -(5730/ln2) ln(fraction) — carbon-14 age from the surviving fraction."""
    name = "archaeology.radiocarbon"
    frac, claimed = spec.get("fraction_remaining"), spec.get("claimed_age_years")
    if frac is None or claimed is None:
        return na(name)
    try:
        f, cl = float(frac), float(claimed)
    except (TypeError, ValueError):
        return error(name, "inputs must be numeric")
    if not 0.0 < f <= 1.0:
        return error(name, f"fraction remaining must be in (0, 1] (got {f})")
    T = _C14_HALFLIFE if spec.get("half_life_years") is None else float(spec["half_life_years"])
    actual = -(T / _LN2) * math.log(f)
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-2)
    data = {"fraction": f, "half_life_yr": T, "age_years": actual, "claimed_years": cl,
            "formula": "t = -(T_half/ln2) ln(f)"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"t = -(5730/ln2)·ln({f}) = {actual:.0f} yr (matches {cl})", data)
    return mismatch(name, f"t = {actual:.0f} yr, claimed {cl} (diff {abs(actual-cl):.0f})", data)


def verify_radiometric(spec: Dict[str, Any]) -> VerifierResult:
    """The same decay clock for any isotope, given its half-life."""
    name = "archaeology.radiometric"
    frac, T, claimed = spec.get("fraction_remaining_iso"), spec.get("half_life_years"), spec.get("claimed_age_years_iso")
    if any(v is None for v in (frac, T, claimed)):
        return na(name)
    try:
        f, Tf, cl = float(frac), float(T), float(claimed)
    except (TypeError, ValueError):
        return error(name, "inputs must be numeric")
    if not 0.0 < f <= 1.0 or Tf <= 0:
        return error(name, f"fraction must be in (0,1] and half-life positive (f={f}, T={Tf})")
    actual = -(Tf / _LN2) * math.log(f)
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-2)
    data = {"fraction": f, "half_life_yr": Tf, "age_years": actual, "claimed_years": cl,
            "formula": "t = -(T_half/ln2) ln(f)"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"t = {actual:.4g} yr (matches {cl})", data)
    return mismatch(name, f"t = {actual:.4g} yr, claimed {cl}", data)


def verify_half_lives_elapsed(spec: Dict[str, Any]) -> VerifierResult:
    """n = -log2(fraction) — how many half-lives a surviving fraction represents."""
    name = "archaeology.half_lives_elapsed"
    frac, claimed = spec.get("fraction_for_halflives"), spec.get("claimed_half_lives")
    if frac is None or claimed is None:
        return na(name)
    try:
        f, cl = float(frac), float(claimed)
    except (TypeError, ValueError):
        return error(name, "inputs must be numeric")
    if not 0.0 < f <= 1.0:
        return error(name, f"fraction must be in (0, 1] (got {f})")
    actual = -math.log2(f)
    data = {"fraction": f, "half_lives": actual, "claimed": cl, "formula": "n = -log2(f)"}
    if _close(actual, cl, rel_tol=1e-3, abs_tol=1e-3):
        return confirm(name, f"n = -log2({f}) = {actual:.4f} half-lives (matches {cl})", data)
    return mismatch(name, f"n = {actual:.4f} half-lives, claimed {cl}", data)


_RULES = [
    (("fraction_remaining", "claimed_age_years"), verify_radiocarbon),
    (("fraction_remaining_iso", "half_life_years", "claimed_age_years_iso"), verify_radiometric),
    (("fraction_for_halflives", "claimed_half_lives"), verify_half_lives_elapsed),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "ARCH_VERIFY", _RULES, domain="archaeology",
                    none_reason="no ARCH_VERIFY artifacts present")
