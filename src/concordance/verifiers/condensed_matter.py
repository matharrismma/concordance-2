"""Condensed-matter verifier — the solid state, on the same going train.

Deterministic checks against canonical solid-state relations (all public-domain):

  * condensed_matter.phonon_dispersion — a 1-D monatomic chain of coupled oscillators
        omega(k) = 2·sqrt(K/m)·|sin(k·a/2)|         [rad/s]
  * condensed_matter.fermi_energy — the free-electron Fermi energy from number density
        E_F = (hbar^2 / 2m_e)·(3·pi^2·n)^(2/3)        [joules]
  * condensed_matter.bragg — constructive diffraction from lattice planes
        n·lambda = 2·d·sin(theta)

CONDMAT_VERIFY packet (any subset):
    {
      "spring_const": 10.0, "atom_mass": 1e-26, "wavevector": 1e10, "lattice_a": 3e-10, "claimed_omega": 1.0e13,
      "number_density": 8.5e28, "claimed_fermi_J": 1.12e-18,
      "diff_order": 1, "wavelength_m": 1.54e-10, "plane_spacing_m": 3.13e-10, "claimed_theta_deg": 14.3,
    }
"""
from __future__ import annotations
import math
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol
from .base import dispatch

_HBAR = 1.054571817e-34   # J·s
_ME = 9.1093837015e-31    # kg


def _close(actual: float, claimed: float, rel_tol: float = 1e-2, abs_tol: float = 0.0) -> bool:
    return abs(actual - claimed) <= max(abs_tol, rel_tol * abs(actual))


def verify_phonon_dispersion(spec: Dict[str, Any]) -> VerifierResult:
    """omega(k) = 2 sqrt(K/m) |sin(k a / 2)| — the monatomic-chain phonon branch."""
    name = "condensed_matter.phonon_dispersion"
    K, m, k, a, claimed = (spec.get(x) for x in ("spring_const", "atom_mass", "wavevector", "lattice_a", "claimed_omega"))
    if any(v is None for v in (K, m, k, a, claimed)):
        return na(name)
    try:
        Kf, mf, kf, af, cl = float(K), float(m), float(k), float(a), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if Kf <= 0 or mf <= 0 or af <= 0:
        return error(name, f"spring constant, mass and spacing must be positive (K={Kf}, m={mf}, a={af})")
    actual = 2.0 * math.sqrt(Kf / mf) * abs(math.sin(kf * af / 2.0))
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-2)
    data = {"K": Kf, "m": mf, "k": kf, "a": af, "omega": actual, "claimed": cl,
            "formula": "omega = 2 sqrt(K/m) |sin(ka/2)|"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"omega = {actual:.4g} rad/s (matches {cl})", data)
    return mismatch(name, f"omega = {actual:.4g} rad/s, claimed {cl}", data)


def verify_fermi_energy(spec: Dict[str, Any]) -> VerifierResult:
    """E_F = (hbar^2/2 m_e)(3 pi^2 n)^(2/3) — the free-electron Fermi energy."""
    name = "condensed_matter.fermi_energy"
    n, claimed = spec.get("number_density"), spec.get("claimed_fermi_J")
    if n is None or claimed is None:
        return na(name)
    try:
        nf, cl = float(n), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if nf <= 0:
        return error(name, f"number density must be positive (n={nf})")
    actual = (_HBAR ** 2 / (2.0 * _ME)) * (3.0 * math.pi ** 2 * nf) ** (2.0 / 3.0)
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-2)
    data = {"n": nf, "E_F_J": actual, "E_F_eV": actual / 1.602176634e-19, "claimed_J": cl,
            "formula": "E_F = (hbar^2/2m)(3 pi^2 n)^(2/3)"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"E_F = {actual:.4g} J ({data['E_F_eV']:.3f} eV) (matches {cl})", data)
    return mismatch(name, f"E_F = {actual:.4g} J, claimed {cl}", data)


def verify_bragg(spec: Dict[str, Any]) -> VerifierResult:
    """n lambda = 2 d sin(theta) — verify the diffraction angle in degrees."""
    name = "condensed_matter.bragg"
    n, lam, d, claimed = (spec.get(x) for x in ("diff_order", "wavelength_m", "plane_spacing_m", "claimed_theta_deg"))
    if any(v is None for v in (n, lam, d, claimed)):
        return na(name)
    try:
        nf, lamf, df, cl = float(n), float(lam), float(d), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if df <= 0 or lamf <= 0 or nf <= 0:
        return error(name, "order, wavelength and spacing must be positive")
    s = nf * lamf / (2.0 * df)
    if not -1.0 <= s <= 1.0:
        return error(name, f"no diffraction: n·lambda/(2d) = {s:.3f} is outside [-1, 1]")
    actual = math.degrees(math.asin(s))
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-2)
    data = {"n": nf, "lambda": lamf, "d": df, "theta_deg": actual, "claimed_deg": cl,
            "formula": "n lambda = 2 d sin(theta)"}
    if _close(actual, cl, rel_tol=rel_tol, abs_tol=1e-2):
        return confirm(name, f"theta = arcsin({s:.4f}) = {actual:.3f} deg (matches {cl})", data)
    return mismatch(name, f"theta = {actual:.3f} deg, claimed {cl}", data)


_RULES = [
    (("spring_const", "atom_mass", "wavevector", "lattice_a", "claimed_omega"), verify_phonon_dispersion),
    (("number_density", "claimed_fermi_J"), verify_fermi_energy),
    (("diff_order", "wavelength_m", "plane_spacing_m", "claimed_theta_deg"), verify_bragg),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "CONDMAT_VERIFY", _RULES, domain="condensed_matter",
                    none_reason="no CONDMAT_VERIFY artifacts present")
