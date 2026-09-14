"""Electrochemistry verifier — cells, potentials, and electrolysis.

Deterministic checks against canonical electrochemistry (all public-domain):

  * electrochemistry.nernst — a cell/electrode potential shifted by concentration
        E = E0 - (RT / nF) · ln(Q)          [volts]
  * electrochemistry.cell_potential — a full cell from two half-cells
        E_cell = E_cathode - E_anode
  * electrochemistry.faraday — mass deposited/consumed by a charge (Faraday's law)
        m = (Q · M) / (n · F)                [grams]

ECHEM_VERIFY packet (any subset):
    {
      "e0_V": 1.10, "n_electrons": 2, "reaction_quotient": 0.01, "temp_K": 298.15, "claimed_E_V": 1.159,
      "e_cathode_V": 0.34, "e_anode_V": -0.76, "claimed_cell_V": 1.10,
      "charge_C": 96485, "molar_mass_g": 63.55, "n_faraday": 2, "claimed_mass_g": 31.77,
    }
"""
from __future__ import annotations
import math
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol
from .base import dispatch

_R = 8.314462618   # J/(mol·K)
_F = 96485.33212   # C/mol


def _close(actual: float, claimed: float, rel_tol: float = 1e-2, abs_tol: float = 1e-3) -> bool:
    return abs(actual - claimed) <= max(abs_tol, rel_tol * abs(actual))


def verify_nernst(spec: Dict[str, Any]) -> VerifierResult:
    """E = E0 - (RT/nF) ln(Q). Default 298.15 K."""
    name = "electrochemistry.nernst"
    e0, n, Q, claimed = spec.get("e0_V"), spec.get("n_electrons"), spec.get("reaction_quotient"), spec.get("claimed_E_V")
    if any(v is None for v in (e0, n, Q, claimed)):
        return na(name)
    try:
        e0f, nf, Qf, cl = float(e0), float(n), float(Q), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if nf <= 0 or Qf <= 0:
        return error(name, f"electron count and reaction quotient must be positive (n={nf}, Q={Qf})")
    T = 298.15 if spec.get("temp_K") is None else float(spec["temp_K"])
    actual = e0f - (_R * T / (nf * _F)) * math.log(Qf)
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-2)
    data = {"E0": e0f, "n": nf, "Q": Qf, "T_K": T, "E_V": actual, "claimed_V": cl,
            "formula": "E = E0 - (RT/nF) ln(Q)"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"E = {e0f} - (RT/{nf:g}F)ln({Qf}) = {actual:.4f} V (matches {cl})", data)
    return mismatch(name, f"E = {actual:.4f} V, claimed {cl} (diff {abs(actual-cl):.4f})", data)


def verify_cell_potential(spec: Dict[str, Any]) -> VerifierResult:
    """E_cell = E_cathode - E_anode."""
    name = "electrochemistry.cell_potential"
    ec, ea, claimed = spec.get("e_cathode_V"), spec.get("e_anode_V"), spec.get("claimed_cell_V")
    if any(v is None for v in (ec, ea, claimed)):
        return na(name)
    try:
        ecf, eaf, cl = float(ec), float(ea), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    actual = ecf - eaf
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-3)
    data = {"E_cathode": ecf, "E_anode": eaf, "E_cell": actual, "claimed_V": cl,
            "formula": "E_cell = E_cathode - E_anode"}
    if _close(actual, cl, rel_tol=rel_tol, abs_tol=1e-3):
        return confirm(name, f"E_cell = {ecf} - ({eaf}) = {actual:.3f} V (matches {cl})", data)
    return mismatch(name, f"E_cell = {actual:.3f} V, claimed {cl}", data)


def verify_faraday(spec: Dict[str, Any]) -> VerifierResult:
    """m = (Q·M)/(n·F) — mass from charge passed (Faraday's law of electrolysis)."""
    name = "electrochemistry.faraday"
    Q, M, n, claimed = spec.get("charge_C"), spec.get("molar_mass_g"), spec.get("n_faraday"), spec.get("claimed_mass_g")
    if any(v is None for v in (Q, M, n, claimed)):
        return na(name)
    try:
        Qf, Mf, nf, cl = float(Q), float(M), float(n), float(claimed)
    except (TypeError, ValueError):
        return error(name, "all inputs must be numeric")
    if nf <= 0 or Mf <= 0:
        return error(name, f"electron count and molar mass must be positive (n={nf}, M={Mf})")
    actual = (Qf * Mf) / (nf * _F)
    rel_tol = clamp_tol(spec, "tolerance_relative", 1e-2)
    data = {"charge_C": Qf, "molar_mass": Mf, "n": nf, "mass_g": actual, "claimed_g": cl,
            "formula": "m = QM/(nF)"}
    if _close(actual, cl, rel_tol=rel_tol):
        return confirm(name, f"m = ({Qf}·{Mf})/({nf}·F) = {actual:.4f} g (matches {cl})", data)
    return mismatch(name, f"m = {actual:.4f} g, claimed {cl} (diff {abs(actual-cl):.4f})", data)


_RULES = [
    (("e0_V", "n_electrons", "reaction_quotient", "claimed_E_V"), verify_nernst),
    (("e_cathode_V", "e_anode_V", "claimed_cell_V"), verify_cell_potential),
    (("charge_C", "molar_mass_g", "n_faraday", "claimed_mass_g"), verify_faraday),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "ECHEM_VERIFY", _RULES, domain="electrochemistry",
                    none_reason="no ECHEM_VERIFY artifacts present")
