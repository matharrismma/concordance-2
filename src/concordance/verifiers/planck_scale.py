"""Planck scale — the quantities the Planck constant h SETS.

Same single-source pattern as alpha_scale / grav_scale / rela_scale / thermal_scale, for h: every
quantity is an exact function of h, computed once from the one constant source (physical_constants).
The domains h governs (physical_constants.governance("planck_constant")) verify THROUGH these.

Not a verifier (no run(), not registered) — a shared library the governed domains call.
"""
from __future__ import annotations

from typing import Any, Dict

from .base import VerifierResult
from . import scale_base as _sb
from . import physical_constants as _pc

_C = {c["constant"]: c["value"] for c in _pc.list_constants()}
_h = _C["planck_constant"]
_c = _C["speed_of_light"]
_e = _C["elementary_charge"]


def photon_energy_J(nu_hz: float) -> float:
    """E = h nu — the energy of a photon of frequency nu (joules)."""
    return _h * nu_hz


def photon_energy_eV_from_freq(nu_hz: float) -> float:
    """E = h nu expressed in eV."""
    return _h * nu_hz / _e


def photon_energy_eV_from_wavelength(lam_m: float) -> float:
    """E = h c / lambda expressed in eV (~2.48 eV at 500 nm)."""
    return _h * _c / lam_m / _e


def de_broglie_wavelength_m(p_kg_m_s: float) -> float:
    """lambda = h / p — the matter wavelength of momentum p."""
    return _h / p_kg_m_s


def compare(name: str, actual: float, claimed: Any, rel_tol: float,
            data: Dict[str, Any]) -> VerifierResult:
    """Compare a computed h-anchored quantity against a claimed value (delegates to scale_base)."""
    return _sb.compare(name, actual, claimed, rel_tol, data, anchor=("h", _h))
