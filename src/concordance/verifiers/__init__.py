"""Verifiers — the deterministic complications mounted on the going train.

Each domain verifier exposes `run(packet) -> list[VerifierResult]` and is imported
LAZILY on first use (never eager-imported at package load — that was a 1.0 coupling
hotspot). Heavy deps (sympy/scipy/numpy) load only inside the modules that need them,
only when a packet exercises that domain.

VERIFIERS maps every SECULAR domain (canonical name + aliases) to its module. The
witness-surface verifiers (scripture, theology, witness) are NOT here — they register
only when surface == "witness" (the .org overlay, ported later). `governance` is also
deferred: it carries a scriptural anchor (hotspot #5) and needs the strip refactor.
Cross-cutting verifiers are intentionally empty in the secular core.
"""
from __future__ import annotations

import importlib
from types import ModuleType
from typing import Dict, List, Optional

from .base import VerifierResult, VerifierStatus, confirm, error, mismatch, na

_P = "concordance.verifiers."

# Domain name (canonical or alias) -> module path. Lazy import on demand.
VERIFIERS: Dict[str, str] = {
    # formal reasoning
    "mathematics": _P + "mathematics", "math": _P + "mathematics",
    "number_theory": _P + "number_theory",
    "combinatorics": _P + "combinatorics",
    "geometry": _P + "geometry",
    "formal_logic": _P + "formal_logic", "logic": _P + "formal_logic",
    "probability": _P + "probability",
    "statistics": _P + "statistics",
    "linear_algebra": _P + "linear_algebra",
    "information_theory": _P + "information_theory", "info_theory": _P + "information_theory",
    "computer_science": _P + "computer_science", "cs": _P + "computer_science",
    "cryptography": _P + "cryptography", "cryptology": _P + "cryptography",
    "operations_research": _P + "operations_research", "or": _P + "operations_research",
    "optimization": _P + "operations_research",
    "quantum_computing": _P + "quantum_computing", "quantum": _P + "quantum_computing",
    "qc": _P + "quantum_computing",
    # physical sciences
    "physics": _P + "physics",
    "chemistry": _P + "chemistry",
    "atomic": _P + "atomic",
    "molecular_geometry": _P + "molecular_geometry",
    "periodic_table": _P + "periodic_table",
    "physical_constants": _P + "physical_constants",
    "thermodynamics": _P + "thermodynamics", "thermo": _P + "thermodynamics", "heat": _P + "thermodynamics",
    "nuclear_physics": _P + "nuclear_physics", "nuclear": _P + "nuclear_physics",
    "radioactivity": _P + "nuclear_physics",
    "electrical": _P + "electrical", "electrical_engineering": _P + "electrical",
    "energy": _P + "energy", "power": _P + "energy", "off_grid": _P + "energy",
    "acoustics": _P + "acoustics",
    "optics": _P + "optics",
    "materials_science": _P + "materials_science", "materials": _P + "materials_science",
    "metallurgy": _P + "materials_science",
    # earth & space
    "astronomy": _P + "astronomy",
    "ephemeris": _P + "ephemeris",
    "geology": _P + "geology", "earth_science": _P + "geology",
    "geography": _P + "geography",
    "meteorology": _P + "meteorology", "weather": _P + "meteorology",
    "hydrology": _P + "hydrology", "water": _P + "hydrology",
    "oceanography": _P + "oceanography", "ocean": _P + "oceanography", "marine_science": _P + "oceanography",
    "soil_science": _P + "soil_science", "soil": _P + "soil_science", "agronomy": _P + "soil_science",
    # life sciences
    "biology": _P + "biology",
    "genetics": _P + "genetics",
    "medicine": _P + "medicine", "clinical": _P + "medicine", "medical": _P + "medicine",
    "nutrition": _P + "nutrition",
    "exercise_science": _P + "exercise_science", "exercise": _P + "exercise_science",
    "ecology": _P + "ecology", "ecosystem": _P + "ecology", "environmental": _P + "ecology",
    "agriculture": _P + "agriculture",
    # applied / human systems
    "finance": _P + "finance",
    "economics": _P + "economics", "economy": _P + "economics", "macro": _P + "economics",
    "micro": _P + "economics",
    "labor": _P + "labor", "labour": _P + "labor", "employment": _P + "labor", "wages": _P + "labor",
    "real_estate": _P + "real_estate", "property": _P + "real_estate", "mortgage": _P + "real_estate",
    "law": _P + "law", "legal": _P + "law", "contract": _P + "law",
    "governance": _P + "governance", "business": _P + "governance",
    "household": _P + "governance", "education": _P + "governance",
    "manufacturing": _P + "manufacturing",
    "construction": _P + "construction", "building": _P + "construction",
    "architecture": _P + "architecture", "building_design": _P + "architecture",
    "structural": _P + "architecture",
    "networking": _P + "networking", "network": _P + "networking",
    "cybersecurity": _P + "cybersecurity", "cyber": _P + "cybersecurity", "infosec": _P + "cybersecurity",
    "document_validation": _P + "document_validation", "doc_validation": _P + "document_validation",
    "calendar_time": _P + "calendar_time", "calendar": _P + "calendar_time", "time": _P + "calendar_time",
    "history_chronology": _P + "history_chronology", "history": _P + "history_chronology",
    "chronology": _P + "history_chronology",
    "sports_analytics": _P + "sports_analytics", "sports": _P + "sports_analytics",
    "photography": _P + "photography", "photo": _P + "photography",
    # humanities
    "linguistics": _P + "linguistics",
    "music_theory": _P + "music_theory", "music": _P + "music_theory",
    "rhetoric": _P + "rhetoric", "argumentation": _P + "rhetoric", "fallacy": _P + "rhetoric",
    "philosophy": _P + "philosophy", "ethics": _P + "philosophy", "epistemology": _P + "philosophy",
}

# Witness-surface verifiers — surfaced ONLY when surface == "witness" (the .org overlay).
# The foundation is shared on both surfaces; this governs only what the surface EXPOSES.
# `scripture` (ref resolution) is deferred — it needs the Bible corpus data.
WITNESS_VERIFIERS: Dict[str, str] = {
    "theology_doctrine": _P + "theology_doctrine", "theology": _P + "theology_doctrine",
    "doctrine": _P + "theology_doctrine", "scripture_doctrine": _P + "theology_doctrine",
    "witness": _P + "witness", "testimony": _P + "witness",
}

# Cross-cutting verifiers run on every packet. Empty in the secular core.
CROSS_CUTTING_VERIFIERS: tuple = ()

_LOADED_MODULES: Dict[str, ModuleType] = {}


def _resolve(mod_path: Optional[str]) -> Optional[ModuleType]:
    if mod_path is None:
        return None
    cached = _LOADED_MODULES.get(mod_path)
    if cached is not None:
        return cached
    cached = importlib.import_module(mod_path)
    _LOADED_MODULES[mod_path] = cached
    return cached


def _get_module(domain: str) -> Optional[ModuleType]:
    """Resolve a SECULAR domain to its verifier module (lazy). None if unregistered."""
    return _resolve(VERIFIERS.get(domain))


def _get_witness_module(domain: str) -> Optional[ModuleType]:
    """Resolve a WITNESS-surface domain to its verifier module (lazy). None if unregistered."""
    return _resolve(WITNESS_VERIFIERS.get(domain))


def run_for_domain(domain: str, packet, surface: str = "secular") -> List[VerifierResult]:
    """Run the verifiers for this domain. On the witness surface, the witness-surface
    verifiers (theology/witness) are ALSO surfaced; on the secular reach they are not.
    The foundation is shared; surface governs only what is exposed."""
    results: List[VerifierResult] = []
    d = (domain or "").lower()
    mod = _get_module(d)
    if mod is not None:
        results.extend(mod.run(packet))
    if surface == "witness":
        wmod = _get_witness_module(d)
        if wmod is not None:
            results.extend(wmod.run(packet))
    for cross in CROSS_CUTTING_VERIFIERS:
        results.extend(cross.run(packet))
    return results


__all__ = [
    "VerifierResult", "VerifierStatus", "na", "confirm", "mismatch", "error",
    "run_for_domain", "VERIFIERS", "WITNESS_VERIFIERS", "CROSS_CUTTING_VERIFIERS",
]
