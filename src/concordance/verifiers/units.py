"""Unit-conversion verifier.

Checks a CLAIMED conversion equality — "1 mile is 1.609 kilometers", "500 mg is 0.5 grams",
"100 degrees fahrenheit is 37.78 celsius" — against exact SI / US conversion factors. It VERIFIES,
it never generates: given both sides of the claim it confirms or refutes; it does not answer an open
"convert X to Y" (that is the compute front door). The factor table is the ONE in ``compute._UNITS``
(single source of truth — a unit added there is checkable here for free), and temperature uses the
same affine forms as ``compute`` (a factor cannot express an offset scale).

CONV_VERIFY shape:
    {
      "from_value": 1, "from_unit": "mile",
      "to_value": 1.609, "to_unit": "km",
      "rel_tol": 1e-3,          # optional, default 1e-3 (a claim is usually a rounded figure)
    }

Discipline: only a SAME-DIMENSION claim is ever confirmed or refuted. A cross-dimension pair
("2 cups is 16 ounces" — volume vs the table's mass ounce) is declared NOT_APPLICABLE, never a
MISMATCH: "ounce" and friends are ambiguous (mass vs fluid), so we decline rather than risk telling
someone their true claim is false. An unknown unit is likewise NOT_APPLICABLE.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..compute import _UNITS, _TEMP, _to_celsius, _from_celsius, _fmt
from .base import VerifierResult, na, confirm, mismatch, clamp_tol, dispatch


def _u(s: Any) -> str:
    return str(s or "").strip().lower().rstrip(".")


def verify_conversion(spec: Dict[str, Any]) -> VerifierResult:
    name = "units.conversion"
    fu, tu = _u(spec.get("from_unit")), _u(spec.get("to_unit"))
    fv_raw, tv_raw = spec.get("from_value"), spec.get("to_value")
    if not fu or not tu or fv_raw is None or tv_raw is None:
        return na(name)
    try:
        fv, tv = float(fv_raw), float(tv_raw)
    except (TypeError, ValueError):
        return na(name)
    rel_tol = clamp_tol(spec, "rel_tol", 1e-3)

    if fu in _TEMP or tu in _TEMP:
        if fu not in _TEMP or tu not in _TEMP:          # temperature vs non-temperature — decline
            return na(name, f"cannot convert between {fu} and {tu}")
        actual = _from_celsius(_to_celsius(fv, _TEMP[fu]), _TEMP[tu])
    else:
        a, b = _UNITS.get(fu), _UNITS.get(tu)
        if not a or not b:                              # a unit we don't carry — decline, not a finding
            return na(name, f"unit not in the table: {fu if not a else tu}")
        if a[0] != b[0]:                                # different dimensions — decline (ambiguous units)
            return na(name, f"{fu} and {tu} are different dimensions ({a[0]} vs {b[0]})")
        actual = fv * a[1] / b[1]

    threshold = abs(actual) * rel_tol if actual != 0 else 1e-9
    data = {"from_value": fv, "from_unit": fu, "to_unit": tu,
            "actual_value": actual, "claimed_value": tv, "rel_tol": rel_tol,
            "source": "SI / US customary conversion factors"}
    if abs(actual - tv) <= threshold:
        return confirm(name, f"{_fmt(fv)} {fu} = {_fmt(actual)} {tu} (claim {_fmt(tv)} within {rel_tol:.0e})", data)
    return mismatch(name, f"{_fmt(fv)} {fu} = {_fmt(actual)} {tu}, not {_fmt(tv)} {tu}", data)


_RULES = [
    (lambda cv: (cv.get("from_unit") and cv.get("to_unit")
                 and cv.get("from_value") is not None and cv.get("to_value") is not None),
     verify_conversion),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "CONV_VERIFY", _RULES, domain="unit_conversion",
                    none_reason="no artifact provided")
