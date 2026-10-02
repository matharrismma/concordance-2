"""Electrical engineering verifier (engineering / physical-substance grid axis
sibling to chemistry, physics, manufacturing, astronomy).

Deterministic checks against canonical electrical-circuits laws:
Ohm's law, electrical power, Kirchhoff's voltage/current laws, and
RC time constants. All formulas are public-domain.

Checks performed:

  * electrical.ohms_law
      V = I·R. Given any two of (V, I, R), the third must match claim
      within tolerance.
  * electrical.power
      P = V·I = I²·R = V²/R. Three forms cross-checked against claim.
  * electrical.kirchhoff_voltage_loop
      Sum of EMF/voltage drops around any closed loop = 0. Given
      a list of signed voltages, the sum must equal claim within tol.
  * electrical.rc_time_constant
      τ = R·C (seconds). Capacitor voltage v(t) = V·(1 - e^(-t/τ)).
      Given R, C, and t, the claimed fraction-of-final must match.
  * electrical.reflection_coefficient — THE SMITH CHART'S OWN MAP, in its literal domain
      z = Z/Z0 (complex), Γ = (z − 1)/(z + 1), z = (1 + Γ)/(1 − Γ); |Γ| ≤ 1 for a passive load,
      VSWR = (1 + |Γ|)/(1 − |Γ|), return loss = −20·log10|Γ|. Given Z (re, im) and Z0, the claimed
      Γ (re, im), |Γ|, VSWR or return loss must match; the inverse is checked too (Γ → Z). A single
      frequency, lossless reference, no component model — the idealized chart, nothing more.

ELEC_VERIFY packet shape (any subset of fields):
    {
      "voltage_V": 12.0, "current_A": 0.5, "resistance_ohm": 24.0,

      "power_W_claim": 6.0,

      "voltages_in_loop": [9, -4.5, -4.5],
      "claimed_loop_sum_V": 0.0,

      "z_real_ohm": 50, "z_imag_ohm": 50, "z0_ohm": 50,
      "claimed_gamma_real": 0.2, "claimed_gamma_imag": 0.4, "claimed_gamma_mag": 0.4472,
      "claimed_vswr": 2.618, "claimed_return_loss_db": 6.99,

      "resistance_ohm_rc": 1000, "capacitance_F": 1e-6,
      "elapsed_s": 1e-3,
      "supply_V": 5.0,
      "claimed_capacitor_voltage_V": 3.16,
    }
"""
from __future__ import annotations
import math
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol
from .base import dispatch  # declarative run() driver


def _close(actual: float, claimed: float, rel_tol: float = 1e-3, abs_tol: float = 1e-6) -> bool:
    return abs(actual - claimed) <= max(abs_tol, rel_tol * abs(actual))


def verify_ohms_law(spec: Dict[str, Any]) -> VerifierResult:
    """V = I·R. Provide two of three; the verifier checks the third."""
    name = "electrical.ohms_law"
    V = spec.get("voltage_V")
    I = spec.get("current_A")
    R = spec.get("resistance_ohm")
    provided = sum(1 for x in (V, I, R) if x is not None)
    if provided < 3:
        return na(name, "ohms_law needs all three of (voltage_V, current_A, resistance_ohm)")
    try:
        Vf, If, Rf = float(V), float(I), float(R)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if Rf < 0 or If < 0 and Vf > 0:
        # Negative R/I flips sign convention but still computes; only error on R<0.
        if Rf < 0:
            return error(name, f"resistance must be non-negative, got {Rf}")
    actual_V = If * Rf
    diff = abs(actual_V - Vf)
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-3)
    threshold = max(1e-6, rel_tol * abs(actual_V) if actual_V else 1e-6)
    data = {"voltage_V": Vf, "current_A": If, "resistance_ohm": Rf,
            "actual_V_from_IR": actual_V, "diff_V": diff,
            "formula": "V = I · R"}
    if diff <= threshold:
        return confirm(name, f"V = {If}·{Rf} = {actual_V} (matches claim {Vf})", data)
    return mismatch(name,
                    f"V = {If}·{Rf} = {actual_V}, claimed {Vf} (diff {diff})",
                    data)


def verify_power(spec: Dict[str, Any]) -> VerifierResult:
    """P = V·I (or I²R or V²/R) matches claim."""
    name = "electrical.power"
    V = spec.get("voltage_V")
    I = spec.get("current_A")
    R = spec.get("resistance_ohm")
    claimed = spec.get("power_W_claim")
    if claimed is None:
        return na(name)
    # Need at least two of (V, I, R).
    forms = []
    if V is not None and I is not None:
        try:
            forms.append(("V·I", float(V) * float(I)))
        except (TypeError, ValueError):
            return error(name, "V/I must be numeric")
    if I is not None and R is not None:
        try:
            Rf = float(R)
            forms.append(("I²·R", float(I) ** 2 * Rf))
        except (TypeError, ValueError):
            return error(name, "I/R must be numeric")
    if V is not None and R is not None:
        try:
            Rf = float(R)
            if Rf == 0:
                return error(name, "cannot compute V²/R with R=0")
            forms.append(("V²/R", float(V) ** 2 / Rf))
        except (TypeError, ValueError):
            return error(name, "V/R must be numeric")
    if not forms:
        return na(name, "need at least two of (voltage_V, current_A, resistance_ohm)")
    try:
        c = float(claimed)
    except (TypeError, ValueError):
        return error(name, f"power_W_claim must be numeric, got {claimed!r}")
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-3)
    matches = [(label, p, abs(p - c)) for (label, p) in forms]
    all_match = all(_close(p, c, rel_tol=rel_tol) for (_, p, _) in matches)
    data = {"forms": [{"label": label, "value": p, "diff": d} for (label, p, d) in matches],
            "claimed_W": c, "tolerance_relative": rel_tol,
            "formulas": "P = V·I = I²·R = V²/R"}
    if all_match:
        return confirm(name,
                       f"P forms {[f'{label}={p:.4g}' for (label, p, _) in matches]} all match claim {c}",
                       data)
    return mismatch(name,
                    f"power forms {[(label, p) for (label, p, _) in matches]} vs claim {c}",
                    data)


def verify_kirchhoff_voltage_loop(spec: Dict[str, Any]) -> VerifierResult:
    """Sum of signed voltages around a loop equals claim (typically 0)."""
    name = "electrical.kirchhoff_voltage_loop"
    voltages = spec.get("voltages_in_loop")
    claimed = spec.get("claimed_loop_sum_V")
    if voltages is None or claimed is None:
        return na(name)
    if not isinstance(voltages, (list, tuple)) or not voltages:
        return error(name, "voltages_in_loop must be a non-empty list")
    try:
        vs = [float(v) for v in voltages]
        c = float(claimed)
    except (TypeError, ValueError):
        return error(name, "voltages must be numeric")
    actual = sum(vs)
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-3)
    abs_tol = clamp_tol(spec, "tolerance_absolute", 1e-6)
    threshold = max(abs_tol, rel_tol * max(abs(actual), 1.0))
    diff = abs(actual - c)
    data = {"voltages_in_loop": vs, "actual_sum": actual, "claimed_sum": c,
            "diff": diff, "formula": "ΣV = 0 (KVL)"}
    if diff <= threshold:
        return confirm(name,
                       f"ΣV = {actual:.6g} (matches claim {c}, diff {diff:.6g})",
                       data)
    return mismatch(name,
                    f"ΣV = {actual:.6g}, claimed {c} (diff {diff:.6g} > {threshold:.6g})",
                    data)


def verify_rc_time_constant(spec: Dict[str, Any]) -> VerifierResult:
    """RC charging: v(t) = V·(1 - e^(-t/RC))."""
    name = "electrical.rc_time_constant"
    R = spec.get("resistance_ohm_rc")
    C = spec.get("capacitance_F")
    t = spec.get("elapsed_s")
    V = spec.get("supply_V")
    claimed = spec.get("claimed_capacitor_voltage_V")
    if R is None or C is None or t is None or V is None or claimed is None:
        return na(name)
    try:
        Rf, Cf, tf, Vf, cf = float(R), float(C), float(t), float(V), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if Rf <= 0 or Cf <= 0:
        return error(name, f"R and C must be positive, got R={Rf}, C={Cf}")
    if tf < 0:
        return error(name, f"elapsed time cannot be negative, got {tf}")
    tau = Rf * Cf
    actual = Vf * (1.0 - math.exp(-tf / tau))
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-3)
    abs_tol = clamp_tol(spec, "tolerance_absolute", 1e-3)
    threshold = max(abs_tol, rel_tol * abs(actual))
    diff = abs(actual - cf)
    data = {"R": Rf, "C": Cf, "elapsed_s": tf, "supply_V": Vf,
            "tau": tau, "actual_v": actual, "claimed_v": cf,
            "diff": diff, "formula": "v(t) = V(1 − e^(−t/RC))"}
    if diff <= threshold:
        return confirm(name,
                       f"v({tf}) = {Vf}·(1 − e^(−{tf}/{tau:.3g})) = {actual:.4f} V (matches claim {cf})",
                       data)
    return mismatch(name,
                    f"v({tf}) = {actual:.4f} V, claimed {cf} (diff {diff:.4f})",
                    data)



def verify_reflection_coefficient(spec: Dict[str, Any]) -> VerifierResult:
    """The Smith chart's own mapping, literal: a load Z = R + jX against a real reference Z0 reflects
    Γ = (Z − Z0)/(Z + Z0) = (z − 1)/(z + 1) with z = Z/Z0; the inverse z = (1 + Γ)/(1 − Γ) is checked
    back; |Γ| ≤ 1 for a passive load (R ≥ 0), VSWR = (1+|Γ|)/(1−|Γ|), return loss = −20 log10|Γ|.
    One frequency, a lossless real Z0, no component model — the idealized chart (the handoff's
    fixture: Z0 = 50 Ω, Z = 50 + j50 Ω → Γ = 0.2 + 0.4j; a series −j50 Ω reaches the centre)."""
    name = "electrical.reflection_coefficient"
    claims = ("claimed_gamma_real", "claimed_gamma_imag", "claimed_gamma_mag", "claimed_vswr", "claimed_return_loss_db")
    if "z0_ohm" not in spec or "z_real_ohm" not in spec or not any(k in spec for k in claims):
        return na(name)
    try:
        R = float(spec["z_real_ohm"]); X = float(spec.get("z_imag_ohm", 0.0)); Z0 = float(spec["z0_ohm"])
    except (TypeError, ValueError):
        return error(name, "z_real_ohm, z_imag_ohm and z0_ohm must be numeric")
    if not all(math.isfinite(v) for v in (R, X, Z0)):
        return error(name, "impedances must be finite")
    if Z0 <= 0:
        return error(name, "the reference impedance Z0 must be a positive real number")
    if R < 0:
        return error(name, "a passive load has nonnegative resistance (R >= 0); an active load lies outside the unit disk")
    z = complex(R, X) / Z0
    if z == -1:
        return error(name, "z = -1 (Z = -Z0): the map has no finite image here")
    gamma = (z - 1) / (z + 1)
    back = (1 + gamma) / (1 - gamma) if gamma != 1 else None       # the inverse, checked
    mag = abs(gamma)
    vswr = (1 + mag) / (1 - mag) if mag < 1 else float("inf")
    rl = (-20.0 * math.log10(mag)) if mag > 0 else float("inf")
    data = {"Z_ohm": [R, X], "Z0_ohm": Z0, "z_normalized": [z.real, z.imag],
            "gamma": [gamma.real, gamma.imag], "gamma_mag": mag, "vswr": vswr, "return_loss_db": rl,
            "inverse_z": [back.real, back.imag] if back is not None else None,
            "inverse_holds": (back is not None and abs(back - z) < 1e-9),
            "to_centre_series_reactance_ohm": -X if abs(R - Z0) < 1e-9 else None,
            "formula": "Γ = (z−1)/(z+1), z = Z/Z0; z = (1+Γ)/(1−Γ); VSWR = (1+|Γ|)/(1−|Γ|); RL = −20·log10|Γ|",
            "model": "single frequency, lossless real Z0, no component/tolerance model — the idealized Smith chart"}
    tol = clamp_tol(spec, "tolerance_relative", 1e-3)
    bad = []
    for key, val in (("claimed_gamma_real", gamma.real), ("claimed_gamma_imag", gamma.imag), ("claimed_gamma_mag", mag),
                     ("claimed_vswr", vswr), ("claimed_return_loss_db", rl)):
        if key in spec:
            try:
                cl = float(spec[key])
            except (TypeError, ValueError):
                return error(name, f"{key} must be numeric")
            if not math.isfinite(val):
                if not (isinstance(cl, float) and math.isinf(cl)):
                    bad.append(f"{key.replace('claimed_', '')} is unbounded (|Γ| = 1), claimed {cl:g}")
                continue
            if abs(val - cl) > max(1e-4, tol * abs(val)):
                bad.append(f"{key.replace('claimed_', '')} = {val:.6g}, claimed {cl:.6g}")
    if not data["inverse_holds"]:
        bad.append("the inverse map did not return the load (numerical failure)")
    if bad:
        return mismatch(name, "; ".join(bad), data)
    return confirm(name, f"z = {z.real:.4g}{z.imag:+.4g}j → Γ = {gamma.real:.4g}{gamma.imag:+.4g}j (|Γ| = {mag:.4g}, "
                         f"VSWR {vswr:.4g}, RL {rl:.4g} dB); inverse returns z (matches claims)", data)


_RULES = [
    (lambda ev: (all(ev.get(k) is not None for k in ("voltage_V", "current_A", "resistance_ohm"))), verify_ohms_law),
    (lambda ev: ("power_W_claim" in ev), verify_power),
    (lambda ev: ("voltages_in_loop" in ev and "claimed_loop_sum_V" in ev), verify_kirchhoff_voltage_loop),
    (lambda ev: (all(k in ev for k in ("resistance_ohm_rc", "capacitance_F", "elapsed_s",
                             "supply_V", "claimed_capacitor_voltage_V"))), verify_rc_time_constant),
    (lambda ev: "z0_ohm" in ev and "z_real_ohm" in ev and any(k in ev for k in ("claimed_gamma_real", "claimed_gamma_imag", "claimed_gamma_mag", "claimed_vswr", "claimed_return_loss_db")), verify_reflection_coefficient),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, 'ELEC_VERIFY', _RULES, domain='electrical', none_reason='no ELEC_VERIFY artifacts present')
