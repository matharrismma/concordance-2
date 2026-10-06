"""Condensed-matter verifier — the solid state, on the same going train.

Deterministic checks against canonical solid-state relations (all public-domain):

  * condensed_matter.phonon_dispersion — a 1-D monatomic chain of coupled oscillators
        omega(k) = 2·sqrt(K/m)·|sin(k·a/2)|         [rad/s]
  * condensed_matter.fermi_energy — the free-electron Fermi energy from number density
        E_F = (hbar^2 / 2m_e)·(3·pi^2·n)^(2/3)        [joules]
  * condensed_matter.bragg — constructive diffraction from lattice planes
        n·lambda = 2·d·sin(theta)
  * condensed_matter.quantum_hall — the resistance quantum and Josephson constant, condensed
        matter THROUGH the fine structure constant:
        R_K = h/e^2 = mu_0 c / (2 alpha)   (von Klitzing, ~25812.807 ohm)
        K_J = 2e/h                          (Josephson, ~483597.8 GHz/V)
        R_H = R_K / nu                      (a quantized Hall plateau)

CONDMAT_VERIFY packet (any subset):
    {
      "spring_const": 10.0, "atom_mass": 1e-26, "wavevector": 1e10, "lattice_a": 3e-10, "claimed_omega": 6.3e13,
      "number_density": 8.5e28, "claimed_fermi_J": 1.12e-18,
      "diff_order": 1, "wavelength_m": 1.54e-10, "plane_spacing_m": 3.13e-10, "claimed_theta_deg": 14.3,
      "claimed_von_klitzing_ohm": 25812.807, "claimed_josephson_ghz_per_v": 483597.8,
      "filling_factor": 2, "claimed_hall_resistance_ohm": 12906.4,
    }
"""
from __future__ import annotations
import math
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol
from .base import dispatch
from . import physical_constants as _pc

_HBAR = 1.054571817e-34   # J·s
_ME = 9.1093837015e-31    # kg
# alpha-anchored checks read from the ONE constant source, so h, e, alpha match the rest of the engine
_C = {c["constant"]: c["value"] for c in _pc.list_constants()}


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


def verify_quantum_hall(spec: Dict[str, Any]) -> VerifierResult:
    """The quantum Hall / Josephson constants — condensed matter through the fine structure
    constant. The von Klitzing constant R_K = h/e^2 is the resistance quantum, and it equals
    mu_0 c / (2 alpha) — so a quantized Hall plateau IS a measurement of alpha (the route the
    2019 SI turned into a definition). The Josephson constant is K_J = 2e/h. Verifies whichever
    claim is present."""
    name = "condensed_matter.quantum_hall"
    h = _C["planck_constant"]
    e = _C["elementary_charge"]
    alpha = _C["fine_structure_constant"]
    R_K = h / (e * e)                                                   # von Klitzing, ohm
    K_J = 2.0 * e / h                                                   # Josephson, Hz/V
    R_K_from_alpha = _C["vacuum_permeability"] * _C["speed_of_light"] / (2.0 * alpha)
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-4)
    base = {"von_klitzing_ohm": R_K, "josephson_hz_per_v": K_J,
            "R_K_from_alpha_ohm": R_K_from_alpha, "alpha": alpha,
            "identity": "R_K = h/e^2 = mu_0 c / (2 alpha);  K_J = 2e/h"}

    if "claimed_von_klitzing_ohm" in spec:
        try:
            cl = float(spec["claimed_von_klitzing_ohm"])
        except (TypeError, ValueError):
            return error(name, "claimed_von_klitzing_ohm must be numeric")
        data = {**base, "claimed_ohm": cl}
        if _close(R_K, cl, rel_tol=rel_tol):
            return confirm(name, f"R_K = h/e^2 = {R_K:.6f} ohm (= mu0 c/2alpha = "
                                 f"{R_K_from_alpha:.6f}); matches {cl}", data)
        return mismatch(name, f"R_K = h/e^2 = {R_K:.6f} ohm, claimed {cl}", data)

    if "claimed_josephson_ghz_per_v" in spec:
        try:
            cl = float(spec["claimed_josephson_ghz_per_v"])
        except (TypeError, ValueError):
            return error(name, "claimed_josephson_ghz_per_v must be numeric")
        kj_ghz = K_J / 1e9
        data = {**base, "josephson_ghz_per_v": kj_ghz, "claimed_ghz_per_v": cl}
        if _close(kj_ghz, cl, rel_tol=rel_tol):
            return confirm(name, f"K_J = 2e/h = {kj_ghz:.4f} GHz/V; matches {cl}", data)
        return mismatch(name, f"K_J = 2e/h = {kj_ghz:.4f} GHz/V, claimed {cl}", data)

    if "filling_factor" in spec and "claimed_hall_resistance_ohm" in spec:
        try:
            nu = float(spec["filling_factor"])
            cl = float(spec["claimed_hall_resistance_ohm"])
        except (TypeError, ValueError):
            return error(name, "filling_factor and claimed_hall_resistance_ohm must be numeric")
        if nu <= 0:
            return error(name, f"filling factor must be positive (nu={nu})")
        R_H = R_K / nu
        data = {**base, "filling_factor": nu, "hall_resistance_ohm": R_H, "claimed_ohm": cl}
        if _close(R_H, cl, rel_tol=rel_tol):
            return confirm(name, f"R_H = R_K/{nu:g} = {R_H:.4f} ohm; matches {cl}", data)
        return mismatch(name, f"R_H = R_K/{nu:g} = {R_H:.4f} ohm, claimed {cl}", data)

    return na(name)


def verify_phonon_energy(spec: Dict[str, Any]) -> VerifierResult:
    """E = hbar*omega — a phonon is a QUANTUM of lattice vibration, its energy set by its frequency."""
    name = "condensed_matter.phonon_energy"
    w, claimed = spec.get("phonon_omega"), spec.get("claimed_phonon_energy_J")
    if w is None or claimed is None:
        return na(name)
    try:
        wf, cl = float(w), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if wf < 0:
        return error(name, f"angular frequency must be non-negative (omega={wf})")
    actual = _HBAR * wf
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-4)
    data = {"omega": wf, "E_J": actual, "E_eV": actual / 1.602176634e-19, "claimed_J": cl,
            "formula": "E = hbar*omega"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"E = hbar*omega = {actual:.4g} J ({data['E_eV']:.4g} eV) (matches {cl})", data)
    return mismatch(name, f"E = hbar*omega = {actual:.4g} J, claimed {cl}", data)


def verify_debye_temperature(spec: Dict[str, Any]) -> VerifierResult:
    """theta_D = hbar*omega_D/k_B — the Debye temperature, the cutoff that caps the phonon spectrum."""
    name = "condensed_matter.debye_temperature"
    wd, claimed = spec.get("debye_frequency"), spec.get("claimed_debye_temp_K")
    if wd is None or claimed is None:
        return na(name)
    try:
        wdf, cl = float(wd), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if wdf <= 0:
        return error(name, f"Debye frequency must be positive (omega_D={wdf})")
    actual = _HBAR * wdf / _C["boltzmann_constant"]
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-4)
    data = {"omega_D": wdf, "theta_D_K": actual, "claimed_K": cl, "formula": "theta_D = hbar*omega_D/k_B"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"theta_D = hbar*omega_D/k_B = {actual:.4g} K (matches {cl})", data)
    return mismatch(name, f"theta_D = {actual:.4g} K, claimed {cl}", data)


def verify_phonon_occupation(spec: Dict[str, Any]) -> VerifierResult:
    """n(omega,T) = 1/(exp(hbar*omega/k_B T) - 1) — the Bose-Einstein occupation of a phonon mode."""
    name = "condensed_matter.phonon_occupation"
    w, T, claimed = spec.get("phonon_omega"), spec.get("temperature_K"), spec.get("claimed_occupation")
    if w is None or T is None or claimed is None:
        return na(name)
    try:
        wf, Tf, cl = float(w), float(T), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if wf <= 0 or Tf <= 0:
        return error(name, f"frequency and temperature must be positive (omega={wf}, T={Tf})")
    x = _HBAR * wf / (_C["boltzmann_constant"] * Tf)
    actual = 1.0 / math.expm1(x)                                   # expm1 keeps it stable for small and large x
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-3)
    data = {"omega": wf, "T": Tf, "x_hw_over_kT": x, "occupation": actual, "claimed": cl,
            "formula": "n = 1/(exp(hbar*omega/k_B T) - 1)"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"n = 1/(exp({x:.4g})-1) = {actual:.4g} (matches {cl})", data)
    return mismatch(name, f"n = {actual:.4g}, claimed {cl}", data)


def verify_sound_velocity(spec: Dict[str, Any]) -> VerifierResult:
    """v_s = a*sqrt(K/m) — the long-wavelength (k->0) acoustic-branch sound speed of the monatomic chain."""
    name = "condensed_matter.sound_velocity"
    K, m, a, claimed = (spec.get(x) for x in ("spring_const", "atom_mass", "lattice_a", "claimed_sound_velocity"))
    if any(v is None for v in (K, m, a, claimed)):
        return na(name)
    try:
        Kf, mf, af, cl = float(K), float(m), float(a), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if Kf <= 0 or mf <= 0 or af <= 0:
        return error(name, f"spring constant, mass and spacing must be positive (K={Kf}, m={mf}, a={af})")
    actual = af * math.sqrt(Kf / mf)
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-3)
    data = {"K": Kf, "m": mf, "a": af, "v_s": actual, "claimed": cl, "formula": "v_s = a*sqrt(K/m)"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"v_s = a*sqrt(K/m) = {actual:.4g} m/s (matches {cl})", data)
    return mismatch(name, f"v_s = {actual:.4g} m/s, claimed {cl}", data)


def verify_dulong_petit(spec: Dict[str, Any]) -> VerifierResult:
    """The Dulong-Petit law — at high T a crystal's molar heat capacity approaches 3R (each atom carries
    3 vibrational modes, k_B each): C = 3R ~ 24.94 J/(mol*K), the classical ceiling the phonon gas obeys."""
    name = "condensed_matter.dulong_petit"
    claimed = spec.get("claimed_molar_heat_capacity")
    if claimed is None:
        return na(name)
    try:
        cl = float(claimed)
    except (TypeError, ValueError):
        return error(name, "claimed_molar_heat_capacity must be numeric")
    actual = 3.0 * _C["gas_constant"]
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-2)
    data = {"molar_heat_capacity_J_per_mol_K": actual, "claimed": cl, "formula": "C = 3R"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"C = 3R = {actual:.4f} J/(mol*K) (matches {cl})", data)
    return mismatch(name, f"C = 3R = {actual:.4f} J/(mol*K), claimed {cl}", data)


_RULES = [
    (("spring_const", "atom_mass", "wavevector", "lattice_a", "claimed_omega"), verify_phonon_dispersion),
    (("phonon_omega", "claimed_phonon_energy_J"), verify_phonon_energy),
    (("debye_frequency", "claimed_debye_temp_K"), verify_debye_temperature),
    (("phonon_omega", "temperature_K", "claimed_occupation"), verify_phonon_occupation),
    (("spring_const", "atom_mass", "lattice_a", "claimed_sound_velocity"), verify_sound_velocity),
    (("claimed_molar_heat_capacity",), verify_dulong_petit),
    (("number_density", "claimed_fermi_J"), verify_fermi_energy),
    (("diff_order", "wavelength_m", "plane_spacing_m", "claimed_theta_deg"), verify_bragg),
    (lambda cm: ("claimed_von_klitzing_ohm" in cm or "claimed_josephson_ghz_per_v" in cm
                 or ("filling_factor" in cm and "claimed_hall_resistance_ohm" in cm)), verify_quantum_hall),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "CONDMAT_VERIFY", _RULES, domain="condensed_matter",
                    none_reason="no CONDMAT_VERIFY artifacts present")
