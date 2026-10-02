"""Planck scale — the quantities the Planck constant h SETS.

Same single-source pattern as alpha_scale / grav_scale / rela_scale / thermal_scale, for h: every
quantity is an exact function of h, computed once from the one constant source (physical_constants).
The domains h governs (physical_constants.governance("planck_constant")) verify THROUGH these.

Not a verifier (no run(), not registered) — a shared library the governed domains call.
"""
from __future__ import annotations

import math as _math
from typing import Any, Dict

from .base import VerifierResult
from . import scale_base as _sb
from . import physical_constants as _pc

_C = {c["constant"]: c["value"] for c in _pc.list_constants()}
_h = _C["planck_constant"]
_c = _C["speed_of_light"]
_e = _C["elementary_charge"]
_G = _C["gravitational_constant"]
_kB = _C["boltzmann_constant"]
_hbar = _h / (2 * _math.pi)


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


# ── THE PLANCK UNITS — where h meets G and c (and k_B), one number each ──────────────────────────
# l_P = sqrt(hbar G / c^3) is the only length the three anchors make together: below it a length has
# no measured meaning (the floor Padgett's fractals point at; Russell's "all is light" reads as
# c = l_P / t_P). Each is an exact function of the constant table — no literal here can drift.

def planck_length_m() -> float:
    """l_P = sqrt(hbar G / c^3) ~ 1.616255e-35 m."""
    return _math.sqrt(_hbar * _G / _c ** 3)


def planck_time_s() -> float:
    """t_P = sqrt(hbar G / c^5) = l_P / c ~ 5.391247e-44 s."""
    return _math.sqrt(_hbar * _G / _c ** 5)


def planck_mass_kg() -> float:
    """m_P = sqrt(hbar c / G) ~ 2.176434e-8 kg."""
    return _math.sqrt(_hbar * _c / _G)


def planck_energy_J() -> float:
    """E_P = m_P c^2 = sqrt(hbar c^5 / G) ~ 1.956081e9 J."""
    return _math.sqrt(_hbar * _c ** 5 / _G)


def planck_energy_GeV() -> float:
    """E_P in GeV ~ 1.220890e19 GeV."""
    return planck_energy_J() / _e / 1e9


def planck_temperature_K() -> float:
    """T_P = E_P / k_B = sqrt(hbar c^5 / (G k_B^2)) ~ 1.416784e32 K."""
    return planck_energy_J() / _kB


def compare(name: str, actual: float, claimed: Any, rel_tol: float,
            data: Dict[str, Any]) -> VerifierResult:
    """Compare a computed h-anchored quantity against a claimed value (delegates to scale_base)."""
    return _sb.compare(name, actual, claimed, rel_tol, data, anchor=("h", _h))
