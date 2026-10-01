"""Thermal scale — the quantities the Boltzmann constant k_B SETS.

Same single-source pattern as alpha_scale / grav_scale / rela_scale, for k_B: every quantity is an
exact function of k_B, computed once from the one constant source (physical_constants). The domains
k_B governs (physical_constants.governance("boltzmann_constant")) verify THROUGH these.

Not a verifier (no run(), not registered) — a shared library the governed domains call.
"""
from __future__ import annotations

import math
from typing import Any, Dict

from .base import VerifierResult
from . import scale_base as _sb
from . import physical_constants as _pc

_C = {c["constant"]: c["value"] for c in _pc.list_constants()}
_kB = _C["boltzmann_constant"]
_e = _C["elementary_charge"]


def thermal_energy_J(T: float) -> float:
    """k_B T — the thermal energy at temperature T (joules)."""
    return _kB * T


def thermal_energy_eV(T: float) -> float:
    """k_B T expressed in eV (~0.02585 eV at 300 K)."""
    return _kB * T / _e


def boltzmann_factor(E_J: float, T: float) -> float:
    """exp(-E / k_B T) — the relative population of a state at energy E."""
    return math.exp(-E_J / (_kB * T))


def boltzmann_entropy_J_per_K(W: float) -> float:
    """S = k_B ln W — the Boltzmann entropy of W equally likely microstates."""
    return _kB * math.log(W)


def scale_height_m(T: float, m_kg: float, g: float) -> float:
    """H = k_B T / (m g) — the barometric scale height of an isothermal atmosphere."""
    return _kB * T / (m_kg * g)


def compare(name: str, actual: float, claimed: Any, rel_tol: float,
            data: Dict[str, Any]) -> VerifierResult:
    """Compare a computed k_B-anchored quantity against a claimed value (delegates to scale_base)."""
    return _sb.compare(name, actual, claimed, rel_tol, data, anchor=("k_B", _kB))
