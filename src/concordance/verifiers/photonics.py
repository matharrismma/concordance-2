"""Photonics verifier — light engineered as a signal and computing medium.

Guided, resonant, active, and nonlinear light: the physics of integrated and optical
interconnect, distinct from classical ray/wave optics (which lives in `optics`). Every
check is a closed-form, public-domain relation, verified deterministically: given the
inputs, compute the quantity and compare it to the claim.

These calculations instantiate forms the Atlas already carries across many fields — a
waveguide is a `wave`, a resonator is `periodic`, gain/absorption is `decay`, fiber loss
is `logarithmic`, an electro-optic modulator is `linear_flux`, harmonic generation is a
`power_law` — which is why photonics is a connective domain, a bridge between optics,
electrical, quantum, and materials.

Checks:
  * photonics.waveguide_v_number  — V = 2*pi*a*NA/lambda ; single-mode iff V <= 2.405
  * photonics.ring_resonator_fsr  — FSR = c / (n_g * L)
  * photonics.fiber_loss          — P_out(dBm) = P_in(dBm) - alpha * L
  * photonics.electro_optic_vpi   — V_pi = lambda * d / (n^3 * r * L)
  * photonics.second_harmonic     — P_2w is proportional to P_w^2
  * photonics.laser_slope         — P_out = eta * (I - I_th)   (0 below threshold)
  * photonics.grating_angle       — d * sin(theta) = m * lambda
  * photonics.beer_lambert        — I(z) = I0 * exp(-alpha * z)

PHOT_VERIFY shape (any subset; each check fires when its keys are present):
    {
      "core_radius_m": 4e-6, "numerical_aperture": 0.14, "wavelength_m": 1.31e-6,
      "claimed_v_number": 2.68,

      "group_index": 4.2, "ring_length_m": 6.28e-5, "claimed_fsr_hz": 1.136e12,

      "input_power_dbm": 3.0, "attenuation_db_per_km": 0.2, "length_km": 40.0,
      "claimed_output_dbm": -5.0,

      "wavelength_m": 1.55e-6, "gap_m": 1e-5, "index": 2.2,
      "eo_coefficient_m_per_v": 3.1e-11, "length_m": 0.02, "claimed_vpi_v": 5.09,

      "reference_fundamental_w": 1.0, "reference_shg_w": 0.01,
      "test_fundamental_w": 2.0, "claimed_shg_w": 0.04,

      "threshold_current_a": 0.015, "slope_efficiency_w_per_a": 0.9,
      "drive_current_a": 0.05, "claimed_output_w": 0.0315,

      "grating_period_m": 1.5e-6, "order": 1, "claimed_angle_deg": 31.06,

      "input_intensity": 1.0, "coefficient_per_m": 200.0, "length_m2": 0.001,
      "claimed_output_intensity": 0.8187,
    }
"""
from __future__ import annotations
import math
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol
from .base import dispatch  # declarative run() driver

_C = 299792458.0  # speed of light in vacuum, m/s


def _close(a: float, b: float, rel: float = 1e-2, abs_: float = 1e-12) -> bool:
    return abs(a - b) <= max(abs_, rel * max(abs(a), abs(b)))


def _nums(*vals):
    return [float(v) for v in vals]


def verify_waveguide_v_number(spec: Dict[str, Any]) -> VerifierResult:
    name = "photonics.waveguide_v_number"
    a, NA, lam, claimed = (spec.get("core_radius_m"), spec.get("numerical_aperture"),
                           spec.get("wavelength_m"), spec.get("claimed_v_number"))
    if a is None or NA is None or lam is None or claimed is None:
        return na(name)
    try:
        a, NA, lam, c = _nums(a, NA, lam, claimed)
    except (TypeError, ValueError):
        return error(name, "core_radius_m, numerical_aperture, wavelength_m, claimed_v_number must be numeric")
    if lam <= 0:
        return error(name, "wavelength must be > 0")
    V = 2 * math.pi * a * NA / lam
    if _close(V, c, clamp_tol(spec, "tolerance", 1e-2)):
        sm = V <= 2.405
        return confirm(name, f"V = 2*pi*a*NA/lambda = {V:.4g} (single-mode={sm}), matches claim",
                       {"V": V, "single_mode": sm, "claimed": c})
    return mismatch(name, f"V = {V:.4g}, claimed {c:.4g}", {"V": V, "claimed": c})


def verify_ring_resonator_fsr(spec: Dict[str, Any]) -> VerifierResult:
    name = "photonics.ring_resonator_fsr"
    ng, L, claimed = spec.get("group_index"), spec.get("ring_length_m"), spec.get("claimed_fsr_hz")
    if ng is None or L is None or claimed is None:
        return na(name)
    try:
        ng, L, c = _nums(ng, L, claimed)
    except (TypeError, ValueError):
        return error(name, "group_index, ring_length_m, claimed_fsr_hz must be numeric")
    if ng <= 0 or L <= 0:
        return error(name, "group_index and ring_length_m must be > 0")
    fsr = _C / (ng * L)
    if _close(fsr, c, clamp_tol(spec, "tolerance", 1e-2)):
        return confirm(name, f"FSR = c/(n_g*L) = {fsr:.4g} Hz, matches claim", {"fsr_hz": fsr, "claimed": c})
    return mismatch(name, f"FSR = {fsr:.4g} Hz, claimed {c:.4g} Hz", {"fsr_hz": fsr, "claimed": c})


def verify_fiber_loss(spec: Dict[str, Any]) -> VerifierResult:
    name = "photonics.fiber_loss"
    pin, alpha, Lkm, claimed = (spec.get("input_power_dbm"), spec.get("attenuation_db_per_km"),
                                spec.get("length_km"), spec.get("claimed_output_dbm"))
    if pin is None or alpha is None or Lkm is None or claimed is None:
        return na(name)
    try:
        pin, alpha, Lkm, c = _nums(pin, alpha, Lkm, claimed)
    except (TypeError, ValueError):
        return error(name, "input_power_dbm, attenuation_db_per_km, length_km, claimed_output_dbm must be numeric")
    out = pin - alpha * Lkm
    if _close(out, c, clamp_tol(spec, "tolerance", 1e-2), abs_=1e-3):
        return confirm(name, f"P_out = P_in - alpha*L = {out:.4g} dBm, matches claim", {"output_dbm": out, "claimed": c})
    return mismatch(name, f"P_out = {out:.4g} dBm, claimed {c:.4g} dBm", {"output_dbm": out, "claimed": c})


def verify_electro_optic_vpi(spec: Dict[str, Any]) -> VerifierResult:
    name = "photonics.electro_optic_vpi"
    lam, d, n, r, L, claimed = (spec.get("wavelength_m"), spec.get("gap_m"), spec.get("index"),
                                spec.get("eo_coefficient_m_per_v"), spec.get("length_m"), spec.get("claimed_vpi_v"))
    if lam is None or d is None or n is None or r is None or L is None or claimed is None:
        return na(name)
    try:
        lam, d, n, r, L, c = _nums(lam, d, n, r, L, claimed)
    except (TypeError, ValueError):
        return error(name, "wavelength_m, gap_m, index, eo_coefficient_m_per_v, length_m, claimed_vpi_v must be numeric")
    if n <= 0 or r == 0 or L <= 0:
        return error(name, "index and length must be > 0, eo_coefficient nonzero")
    vpi = lam * d / (n ** 3 * r * L)
    if _close(vpi, c, clamp_tol(spec, "tolerance", 1e-2)):
        return confirm(name, f"V_pi = lambda*d/(n^3*r*L) = {vpi:.4g} V, matches claim", {"vpi_v": vpi, "claimed": c})
    return mismatch(name, f"V_pi = {vpi:.4g} V, claimed {c:.4g} V", {"vpi_v": vpi, "claimed": c})


def verify_second_harmonic(spec: Dict[str, Any]) -> VerifierResult:
    name = "photonics.second_harmonic"
    p_ref, shg_ref, p_test, claimed = (spec.get("reference_fundamental_w"), spec.get("reference_shg_w"),
                                       spec.get("test_fundamental_w"), spec.get("claimed_shg_w"))
    if p_ref is None or shg_ref is None or p_test is None or claimed is None:
        return na(name)
    try:
        p_ref, shg_ref, p_test, c = _nums(p_ref, shg_ref, p_test, claimed)
    except (TypeError, ValueError):
        return error(name, "reference_fundamental_w, reference_shg_w, test_fundamental_w, claimed_shg_w must be numeric")
    if p_ref <= 0:
        return error(name, "reference_fundamental_w must be > 0")
    pred = shg_ref * (p_test / p_ref) ** 2  # P_2w proportional to P_w^2
    if _close(pred, c, clamp_tol(spec, "tolerance", 1e-2)):
        return confirm(name, f"P_2w ~ P_w^2 -> {pred:.4g} W, matches claim", {"shg_w": pred, "claimed": c})
    return mismatch(name, f"P_2w ~ P_w^2 -> {pred:.4g} W, claimed {c:.4g} W", {"shg_w": pred, "claimed": c})


def verify_laser_slope(spec: Dict[str, Any]) -> VerifierResult:
    name = "photonics.laser_slope"
    Ith, eta, I, claimed = (spec.get("threshold_current_a"), spec.get("slope_efficiency_w_per_a"),
                            spec.get("drive_current_a"), spec.get("claimed_output_w"))
    if Ith is None or eta is None or I is None or claimed is None:
        return na(name)
    try:
        Ith, eta, I, c = _nums(Ith, eta, I, claimed)
    except (TypeError, ValueError):
        return error(name, "threshold_current_a, slope_efficiency_w_per_a, drive_current_a, claimed_output_w must be numeric")
    P = max(0.0, eta * (I - Ith))  # linear above threshold, dark below
    if _close(P, c, clamp_tol(spec, "tolerance", 1e-2), abs_=1e-6):
        return confirm(name, f"P_out = eta*(I - I_th) = {P:.4g} W, matches claim", {"output_w": P, "claimed": c})
    return mismatch(name, f"P_out = {P:.4g} W, claimed {c:.4g} W", {"output_w": P, "claimed": c})


def verify_grating_angle(spec: Dict[str, Any]) -> VerifierResult:
    name = "photonics.grating_angle"
    d, m, lam, claimed = (spec.get("grating_period_m"), spec.get("order"),
                          spec.get("wavelength_m"), spec.get("claimed_angle_deg"))
    if d is None or m is None or lam is None or claimed is None:
        return na(name)
    try:
        d, m, lam, c = _nums(d, m, lam, claimed)
    except (TypeError, ValueError):
        return error(name, "grating_period_m, order, wavelength_m, claimed_angle_deg must be numeric")
    if d <= 0:
        return error(name, "grating_period_m must be > 0")
    s = m * lam / d
    if abs(s) > 1:
        return na(name, f"|m*lambda/d| = {abs(s):.3g} > 1: this diffracted order is evanescent (no real angle)")
    theta = math.degrees(math.asin(s))
    if _close(theta, c, clamp_tol(spec, "tolerance", 1e-2), abs_=1e-3):
        return confirm(name, f"d*sin(theta) = m*lambda -> theta = {theta:.4g} deg, matches claim",
                       {"angle_deg": theta, "claimed": c})
    return mismatch(name, f"theta = {theta:.4g} deg, claimed {c:.4g} deg", {"angle_deg": theta, "claimed": c})


def verify_beer_lambert(spec: Dict[str, Any]) -> VerifierResult:
    name = "photonics.beer_lambert"
    I0, alpha, z, claimed = (spec.get("input_intensity"), spec.get("coefficient_per_m"),
                             spec.get("length_m2"), spec.get("claimed_output_intensity"))
    if I0 is None or alpha is None or z is None or claimed is None:
        return na(name)
    try:
        I0, alpha, z, c = _nums(I0, alpha, z, claimed)
    except (TypeError, ValueError):
        return error(name, "input_intensity, coefficient_per_m, length_m2, claimed_output_intensity must be numeric")
    I = I0 * math.exp(-alpha * z)  # absorption (alpha>0) or gain (alpha<0)
    if _close(I, c, clamp_tol(spec, "tolerance", 1e-2)):
        return confirm(name, f"I(z) = I0*exp(-alpha*z) = {I:.4g}, matches claim", {"output_intensity": I, "claimed": c})
    return mismatch(name, f"I(z) = {I:.4g}, claimed {c:.4g}", {"output_intensity": I, "claimed": c})


_RULES = [
    (lambda pv: "core_radius_m" in pv and "claimed_v_number" in pv, verify_waveguide_v_number),
    (lambda pv: "group_index" in pv and "claimed_fsr_hz" in pv, verify_ring_resonator_fsr),
    (lambda pv: "input_power_dbm" in pv and "claimed_output_dbm" in pv, verify_fiber_loss),
    (lambda pv: "eo_coefficient_m_per_v" in pv and "claimed_vpi_v" in pv, verify_electro_optic_vpi),
    (lambda pv: "reference_shg_w" in pv and "claimed_shg_w" in pv, verify_second_harmonic),
    (lambda pv: "slope_efficiency_w_per_a" in pv and "claimed_output_w" in pv, verify_laser_slope),
    (lambda pv: "grating_period_m" in pv and "claimed_angle_deg" in pv, verify_grating_angle),
    (lambda pv: "coefficient_per_m" in pv and "claimed_output_intensity" in pv, verify_beer_lambert),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, 'PHOT_VERIFY', _RULES, domain='photonics',
                    none_reason='no PHOT_VERIFY artifacts present')
