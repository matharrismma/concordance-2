"""Verifiers — the deterministic complications mounted on the going train.

Each domain verifier is a pure function family exposing `run(packet) -> list[VerifierResult]`.
Modules are imported LAZILY on first use (never eager-imported at package load — that
was a 1.0 coupling hotspot). Heavy deps (sympy/scipy/numpy) load only inside the
modules that need them, only when a packet exercises that domain.

The VERIFIERS map lists the SECULAR domains. It grows as modules port (see
PORT_PLAN.md) — the map is the parts manifest. The witness-surface verifiers
(scripture, theology, witness) register only when surface == "witness" (port later).
Cross-cutting verifiers are intentionally empty in the secular core (1.0's eager
`scripture` cross-cutting was hotspot #1).
"""
from __future__ import annotations

import importlib
from types import ModuleType
from typing import Dict, List, Optional

from .base import VerifierResult, VerifierStatus, confirm, error, mismatch, na

# Domain name (canonical or alias) -> module path. Lazy import on demand.
# Grows as verifiers port; only listed domains are active.
VERIFIERS: Dict[str, str] = {
    "combinatorics": "concordance.verifiers.combinatorics",
}

# Cross-cutting verifiers run on every packet. Empty in the secular core.
CROSS_CUTTING_VERIFIERS: tuple = ()

_LOADED_MODULES: Dict[str, ModuleType] = {}


def _get_module(domain: str) -> Optional[ModuleType]:
    """Resolve a domain to its verifier module, importing on first use.
    Returns None for unregistered domains."""
    mod_path = VERIFIERS.get(domain)
    if mod_path is None:
        return None
    cached = _LOADED_MODULES.get(mod_path)
    if cached is not None:
        return cached
    cached = importlib.import_module(mod_path)
    _LOADED_MODULES[mod_path] = cached
    return cached


def run_for_domain(domain: str, packet) -> List[VerifierResult]:
    """Run all verifiers registered for this domain plus any cross-cutting ones."""
    results: List[VerifierResult] = []
    mod = _get_module((domain or "").lower())
    if mod is not None:
        results.extend(mod.run(packet))
    for cross in CROSS_CUTTING_VERIFIERS:
        results.extend(cross.run(packet))
    return results


__all__ = [
    "VerifierResult", "VerifierStatus", "na", "confirm", "mismatch", "error",
    "run_for_domain", "VERIFIERS", "CROSS_CUTTING_VERIFIERS",
]
