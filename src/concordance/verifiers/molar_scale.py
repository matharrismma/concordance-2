"""Molar scale — the quantities the Avogadro constant N_A SETS.

Same single-source pattern as the other *_scale libraries, for N_A: every quantity is an exact
function of N_A, computed once from the one constant source (physical_constants). The domains N_A
governs (physical_constants.governance("avogadro_constant")) verify THROUGH these — the bridge from
counts of particles to laboratory amounts.

Not a verifier (no run(), not registered) — a shared library the governed domains call.
"""
from __future__ import annotations

from typing import Any, Dict

from .base import VerifierResult
from . import scale_base as _sb
from . import physical_constants as _pc

_C = {c["constant"]: c["value"] for c in _pc.list_constants()}
_NA = _C["avogadro_constant"]
_kB = _C["boltzmann_constant"]
_e = _C["elementary_charge"]


def particles_from_moles(n_mol: float) -> float:
    """N = n * N_A — the number of entities in n moles."""
    return n_mol * _NA


def gas_constant() -> float:
    """R = N_A k_B — the molar gas constant (~8.314462618 J/(mol K))."""
    return _NA * _kB


def faraday_C_per_mol() -> float:
    """F = N_A e — the charge per mole of electrons (~96485.33 C/mol)."""
    return _NA * _e


def compare(name: str, actual: float, claimed: Any, rel_tol: float,
            data: Dict[str, Any]) -> VerifierResult:
    """Compare a computed N_A-anchored quantity against a claimed value (delegates to scale_base)."""
    return _sb.compare(name, actual, claimed, rel_tol, data, anchor=("N_A", _NA))
