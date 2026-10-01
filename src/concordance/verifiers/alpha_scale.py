"""Alpha-anchored scale — the quantities the fine structure constant SETS.

Computed once, from the one constant source (physical_constants), so every alpha-anchored check
across the engine rests on the same numbers and the same physics, stated in one auditable place.
The domains alpha governs (see physical_constants.alpha_governance) verify THROUGH these.

This is NOT a verifier (no run(), not registered) — a shared library the governed domains call.
Every quantity here is an exact function of alpha or of the constants alpha defines (e, epsilon_0,
R_inf, a_0), so a check built on it is genuinely "through alpha," never a keyword match.
"""
from __future__ import annotations

import math
from typing import Any, Dict

from .base import VerifierResult
from . import scale_base as _sb
from . import physical_constants as _pc

_C = {c["constant"]: c["value"] for c in _pc.list_constants()}

_e = _C["elementary_charge"]
_h = _C["planck_constant"]
_c = _C["speed_of_light"]
_me = _C["electron_mass"]
_eps0 = _C["vacuum_permittivity"]
_Rinf = _C["rydberg_constant"]
_NA = _C["avogadro_constant"]
_kB = _C["boltzmann_constant"]
_ALPHA = _C["fine_structure_constant"]


def alpha() -> float:
    return _ALPHA


# ── alpha-governed derived quantities (each an exact identity in the constant web) ───────────
def rydberg_energy_eV() -> float:
    """Ry = R_inf h c = alpha^2 m_e c^2 / 2 — the atomic energy unit (~13.6057 eV)."""
    return _Rinf * _h * _c / _e


def hartree_eV() -> float:
    """E_h = 2 Ry = alpha^2 m_e c^2 — the Hartree, atomic unit of energy (~27.2114 eV)."""
    return 2.0 * rydberg_energy_eV()


def hydrogen_energy_eV(Z: float, n: int) -> float:
    """E_n = -Z^2 Ry / n^2 — hydrogenic bound-state energy (infinite nuclear mass)."""
    return -(Z * Z) * rydberg_energy_eV() / (n * n)


def rydberg_line_m(Z: float, n_lower: int, n_upper: int) -> float:
    """1/lambda = R_inf Z^2 (1/n_lower^2 - 1/n_upper^2) — a hydrogenic spectral line (inf. mass)."""
    inv = _Rinf * Z * Z * (1.0 / (n_lower * n_lower) - 1.0 / (n_upper * n_upper))
    return 1.0 / inv


def moseley_k_alpha_eV(Z: float) -> float:
    """E(K-alpha) ~ (3/4) Ry (Z-1)^2 — Moseley's law (approximate; single-electron screening)."""
    return 0.75 * rydberg_energy_eV() * (Z - 1.0) ** 2


def classical_electron_radius_m() -> float:
    """r_e = e^2 / (4 pi eps0 m_e c^2) = alpha^2 a_0 (~2.8179e-15 m)."""
    return _e * _e / (4.0 * math.pi * _eps0 * _me * _c * _c)


def thomson_cross_section_m2() -> float:
    """sigma_T = (8 pi / 3) r_e^2 — Thomson scattering cross section (~6.6524e-29 m^2)."""
    r = classical_electron_radius_m()
    return (8.0 * math.pi / 3.0) * r * r


def compton_wavelength_m() -> float:
    """lambda_C = h / (m_e c) = 2 pi alpha a_0 (~2.4263e-12 m)."""
    return _h / (_me * _c)


def von_klitzing_ohm() -> float:
    """R_K = h / e^2 = mu_0 c / (2 alpha) (~25812.807 ohm)."""
    return _h / (_e * _e)


def josephson_hz_per_v() -> float:
    """K_J = 2 e / h (~4.8360e14 Hz/V)."""
    return 2.0 * _e / _h


def faraday_C_per_mol() -> float:
    """F = N_A e (~96485.33 C/mol)."""
    return _NA * _e


def nernst_thermal_V(T: float) -> float:
    """RT/F — the thermal voltage that scales the Nernst equation (~25.69 mV at 298.15 K)."""
    R = _NA * _kB
    return R * T / faraday_C_per_mol()


# ── deeper alpha: the QED / fine-structure layer ─────────────────────────────────────────────
def electron_g2_anomaly() -> float:
    """a_e = (g-2)/2, the electron magnetic-moment anomaly — leading QED term alpha/(2 pi)
    (~0.0011614; the measured 0.00115965 adds higher-order alpha terms, agreeing to ~0.2%)."""
    return _ALPHA / (2.0 * math.pi)


def fine_structure_scale_eV() -> float:
    """alpha^2 Ry — the characteristic fine-structure energy scale (~7.24e-4 eV), the size of
    the spin-orbit splitting relative to the gross atomic structure."""
    return _ALPHA * _ALPHA * rydberg_energy_eV()


def compare(name: str, actual: float, claimed: Any, rel_tol: float,
            data: Dict[str, Any]) -> VerifierResult:
    """Compare a computed alpha-anchored quantity against a claimed value (delegates to scale_base)."""
    return _sb.compare(name, actual, claimed, rel_tol, data, anchor=("alpha", _ALPHA))
