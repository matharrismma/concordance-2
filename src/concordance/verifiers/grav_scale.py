"""Gravitational scale — the quantities the Newtonian constant G SETS.

The same single-source pattern as alpha_scale.py, for a different constant: every quantity here is
an exact function of G (and c, where relativity enters), computed once from the one constant source
(physical_constants). The domains G governs (physical_constants.governance("gravitational_constant"))
verify THROUGH these. Demonstrates that the alpha pattern generalizes: each fundamental constant
gets a governance graph and a single-source scale library, and its domains verify through it.

Not a verifier (no run(), not registered) — a shared library the governed domains call.
"""
from __future__ import annotations

import math
from typing import Any, Dict

from .base import VerifierResult
from . import scale_base as _sb
from . import physical_constants as _pc

_C = {c["constant"]: c["value"] for c in _pc.list_constants()}
_G = _C["gravitational_constant"]
_c = _C["speed_of_light"]


def escape_velocity_m_s(M: float, r: float) -> float:
    """v = sqrt(2 G M / r) — the speed to escape mass M from radius r."""
    return math.sqrt(2.0 * _G * M / r)


def schwarzschild_radius_m(M: float) -> float:
    """r_s = 2 G M / c^2 — the event-horizon radius of mass M."""
    return 2.0 * _G * M / (_c * _c)


def orbital_period_s(a: float, M: float) -> float:
    """T = 2 pi sqrt(a^3 / (G M)) — Kepler's third law, gravitational form."""
    return 2.0 * math.pi * math.sqrt(a ** 3 / (_G * M))


def surface_gravity_m_s2(M: float, r: float) -> float:
    """g = G M / r^2 — gravitational acceleration at radius r from mass M."""
    return _G * M / (r * r)


def gravitational_force_N(m1: float, m2: float, r: float) -> float:
    """F = G m1 m2 / r^2 — Newton's law of universal gravitation."""
    return _G * m1 * m2 / (r * r)


def compare(name: str, actual: float, claimed: Any, rel_tol: float,
            data: Dict[str, Any], as_written: Any = None, unit_factor: float = 1.0,
            hedged: bool = False) -> VerifierResult:
    """Compare a computed G-anchored quantity against a claimed value (delegates to scale_base).
    `as_written` / `unit_factor`: the claim as the person stated it, for stated-precision judgement."""
    return _sb.compare(name, actual, claimed, rel_tol, data, anchor=("G", _G),
                       as_written=as_written, unit_factor=unit_factor, hedged=hedged)
