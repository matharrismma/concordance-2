"""Neuroscience verifier — the membrane, on the same going train.

Deterministic checks against the canonical membrane laws (all public-domain):

  * neuroscience.nernst_potential — the equilibrium (reversal) potential of one ion
        E = (RT / zF) · ln(C_out / C_in)      [reported in mV]
  * neuroscience.goldman — the resting potential over several ions (GHK)
        V_m = (RT/F) · ln( (P_K·K_o + P_Na·Na_o + P_Cl·Cl_i)
                           / (P_K·K_i + P_Na·Na_i + P_Cl·Cl_o) )   [mV]
  * neuroscience.weber_fechner — perceived intensity is the log of the stimulus
        S = k · ln(I / I0)

NEURO_VERIFY packet (any subset):
    {
      "ion_z": 1, "c_out_mM": 145, "c_in_mM": 12, "temp_K": 310, "claimed_mV": 66.6,

      "p_k": 1.0, "p_na": 0.04, "p_cl": 0.45,
      "k_out": 4, "k_in": 140, "na_out": 145, "na_in": 12, "cl_out": 110, "cl_in": 10,
      "claimed_vm_mV": -70,

      "stimulus": 100, "reference": 10, "weber_k": 1.0, "claimed_sensation": 2.302,
    }
"""
from __future__ import annotations
import math
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol
from .base import dispatch

_R = 8.314462618   # J/(mol·K)
_F = 96485.33212   # C/mol


def _close(actual: float, claimed: float, rel_tol: float = 1e-2, abs_tol: float = 1e-2) -> bool:
    return abs(actual - claimed) <= max(abs_tol, rel_tol * abs(actual))


def verify_nernst_potential(spec: Dict[str, Any]) -> VerifierResult:
    """E = (RT/zF) ln(C_out/C_in), in mV. Default body temperature 310 K."""
    name = "neuroscience.nernst_potential"
    z, co, ci, claimed = spec.get("ion_z"), spec.get("c_out_mM"), spec.get("c_in_mM"), spec.get("claimed_mV")
    if any(v is None for v in (z, co, ci, claimed)):
        return na(name)
    try:
        zf, cof, cif, cl = float(z), float(co), float(ci), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if zf == 0 or cof <= 0 or cif <= 0:
        return error(name, f"ion charge must be nonzero and concentrations positive (z={zf}, Co={cof}, Ci={cif})")
    T = clamp_tol(spec, "temp_K", 310.0) if spec.get("temp_K") is None else float(spec["temp_K"])
    actual = (_R * T / (zf * _F)) * math.log(cof / cif) * 1000.0
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-2)
    data = {"z": zf, "c_out": cof, "c_in": cif, "T_K": T, "E_mV": actual, "claimed_mV": cl,
            "formula": "E = (RT/zF) ln(C_out/C_in)"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"E = (RT/{zf:g}F) ln({cof}/{cif}) = {actual:.2f} mV (matches {cl})", data)
    return mismatch(name, f"E = {actual:.2f} mV, claimed {cl} (diff {abs(actual-cl):.2f})", data)


def verify_goldman(spec: Dict[str, Any]) -> VerifierResult:
    """GHK resting potential over K, Na, Cl (Cl flipped, being an anion). Default 310 K."""
    name = "neuroscience.goldman"
    keys = ("p_k", "p_na", "p_cl", "k_out", "k_in", "na_out", "na_in", "cl_out", "cl_in", "claimed_vm_mV")
    if any(spec.get(k) is None for k in keys):
        return na(name)
    try:
        pk, pna, pcl = float(spec["p_k"]), float(spec["p_na"]), float(spec["p_cl"])
        ko, ki, nao, nai, clo, cli = (float(spec[k]) for k in ("k_out", "k_in", "na_out", "na_in", "cl_out", "cl_in"))
        cl = float(spec["claimed_vm_mV"])
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    num = pk * ko + pna * nao + pcl * cli
    den = pk * ki + pna * nai + pcl * clo
    if num <= 0 or den <= 0:
        return error(name, "weighted concentrations must be positive")
    T = 310.0 if spec.get("temp_K") is None else float(spec["temp_K"])
    actual = (_R * T / _F) * math.log(num / den) * 1000.0
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-2)
    data = {"num": num, "den": den, "T_K": T, "Vm_mV": actual, "claimed_mV": cl, "formula": "GHK"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"V_m = {actual:.2f} mV (matches {cl})", data)
    return mismatch(name, f"V_m = {actual:.2f} mV, claimed {cl} (diff {abs(actual-cl):.2f})", data)


def verify_weber_fechner(spec: Dict[str, Any]) -> VerifierResult:
    """S = k ln(I / I0) — perceived intensity as the log of the stimulus ratio."""
    name = "neuroscience.weber_fechner"
    I, I0, k, claimed = spec.get("stimulus"), spec.get("reference"), spec.get("weber_k"), spec.get("claimed_sensation")
    if any(v is None for v in (I, I0, k, claimed)):
        return na(name)
    try:
        If, I0f, kf, cl = float(I), float(I0), float(k), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if If <= 0 or I0f <= 0:
        return error(name, f"stimulus and reference must be positive (I={If}, I0={I0f})")
    actual = kf * math.log(If / I0f)
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-3)
    data = {"stimulus": If, "reference": I0f, "k": kf, "S": actual, "claimed": cl, "formula": "S = k ln(I/I0)"}
    if _close(actual, cl, rel_tol=rel_tol, abs_tol=1e-4):
        return confirm(name, f"S = {kf}·ln({If}/{I0f}) = {actual:.4f} (matches {cl})", data)
    return mismatch(name, f"S = {actual:.4f}, claimed {cl}", data)


_RULES = [
    (("ion_z", "c_out_mM", "c_in_mM", "claimed_mV"), verify_nernst_potential),
    (("p_k", "p_na", "p_cl", "k_out", "k_in", "na_out", "na_in", "cl_out", "cl_in", "claimed_vm_mV"), verify_goldman),
    (("stimulus", "reference", "weber_k", "claimed_sensation"), verify_weber_fechner),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "NEURO_VERIFY", _RULES, domain="neuroscience",
                    none_reason="no NEURO_VERIFY artifacts present")
