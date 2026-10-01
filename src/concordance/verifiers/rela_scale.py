"""Relativistic scale — the quantities the speed of light c SETS.

The same single-source pattern as alpha_scale / grav_scale, for c: every quantity is an exact
function of c, computed once from the one constant source (physical_constants). The domains c
governs (physical_constants.governance("speed_of_light")) verify THROUGH these.

Not a verifier (no run(), not registered) — a shared library the governed domains call.
"""
from __future__ import annotations

import math
from typing import Any, Dict

from .base import VerifierResult
from . import scale_base as _sb
from . import physical_constants as _pc

_C = {c["constant"]: c["value"] for c in _pc.list_constants()}
_c = _C["speed_of_light"]
_amu = _C["atomic_mass_unit"]
_e = _C["elementary_charge"]


def rest_energy_J(m_kg: float) -> float:
    """E = m c^2 — the rest energy of mass m (joules)."""
    return m_kg * _c * _c


def rest_energy_MeV_from_amu(m_amu: float) -> float:
    """E = m c^2 for a mass given in atomic mass units, expressed in MeV (~931.494 MeV per amu)."""
    return m_amu * _amu * _c * _c / _e / 1e6


def lorentz_factor(v_m_s: float) -> float:
    """gamma = 1 / sqrt(1 - (v/c)^2) — the time-dilation / length-contraction factor."""
    beta = v_m_s / _c
    return 1.0 / math.sqrt(1.0 - beta * beta)


def light_travel_time_s(d_m: float) -> float:
    """t = d / c — the light-travel time over distance d."""
    return d_m / _c


def light_travel_distance_m(t_s: float) -> float:
    """d = c t — the distance light travels in time t."""
    return _c * t_s


def compare(name: str, actual: float, claimed: Any, rel_tol: float,
            data: Dict[str, Any]) -> VerifierResult:
    """Compare a computed c-anchored quantity against a claimed value (delegates to scale_base)."""
    return _sb.compare(name, actual, claimed, rel_tol, data, anchor=("c", _c))
