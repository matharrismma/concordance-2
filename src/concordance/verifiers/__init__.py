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
    # RH by elimination through the divisor sum (Robin 1984) — a number_theory check, named so the engine
    # routes a Robin query and the nightly benchmark runs it on its own golden (2026-10-05)
    "robin": _P + "number_theory", "robins_inequality": _P + "number_theory",
    # RH by elimination through the prime count (Schoenfeld 1976) — the same window from another side, routed and
    # run nightly like the Robin check (2026-10-05)
    "schoenfeld": _P + "number_theory", "schoenfelds_inequality": _P + "number_theory",
    # the zero count N(T) at a great height (Turing's method) — cheap, counts the zeros in the strip, routed and
    # run nightly like the other number_theory marks (2026-10-05)
    "zero_count": _P + "number_theory", "zeta_zero_count": _P + "number_theory",
    # two more RH-equivalent eliminations, same divisor-sum / primorial machinery (2026-10-05)
    "lagarias": _P + "number_theory", "lagarias_inequality": _P + "number_theory",
    "nicolas": _P + "number_theory", "nicolas_criterion": _P + "number_theory",
    # the sight picture: S(T), the signed residual of the zero count, tracked against RH's Selberg envelope
    "count_residual": _P + "number_theory", "s_of_t": _P + "number_theory",
    "combinatorics": _P + "combinatorics",
    "geometry": _P + "geometry",
    "formal_logic": _P + "formal_logic", "logic": _P + "formal_logic",
    "probability": _P + "probability",
    "statistics": _P + "statistics",
    # the cross-domain answer for Riemann: the zeta zeros' spacings follow random-matrix (GUE) statistics
    # (Montgomery-Odlyzko) — a statistics-domain mark on a number-theory question (2026-10-05)
    "gue": _P + "statistics", "zeta_spacing": _P + "statistics",
    # "do these independent measurements agree?" — the concordance check lives in statistics
    "measurement_consistency": _P + "statistics",
    "measurement_agreement": _P + "statistics",
    "measurement_concordance": _P + "statistics",
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
    "unit_conversion": _P + "units",
    "units": _P + "units",
    "conversion": _P + "units",
    "thermodynamics": _P + "thermodynamics", "thermo": _P + "thermodynamics", "heat": _P + "thermodynamics",
    "nuclear_physics": _P + "nuclear_physics", "nuclear": _P + "nuclear_physics",
    "radioactivity": _P + "nuclear_physics",
    "electrical": _P + "electrical", "electrical_engineering": _P + "electrical",
    "energy": _P + "energy", "power": _P + "energy", "off_grid": _P + "energy",
    "acoustics": _P + "acoustics",
    "optics": _P + "optics",
    "photonics": _P + "photonics", "integrated_photonics": _P + "photonics",
    "optical_engineering": _P + "photonics", "silicon_photonics": _P + "photonics",
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
    # the fleet turned inward — the library measuring its own finding, on the same terms it
    # holds everyone else to. Registered as an ordinary domain on purpose: our retrieval gets no
    # gentler a verifier than a stranger's chemistry.
    "retrieval": _P + "retrieval", "search_quality": _P + "retrieval",
    "information_retrieval": _P + "retrieval",
    # domains Atlas mapped before the engine could check them — now built from the map's own formulas
    "neuroscience": _P + "neuroscience", "neuro": _P + "neuroscience", "neurophysiology": _P + "neuroscience",
    "electrochemistry": _P + "electrochemistry", "echem": _P + "electrochemistry",
    "condensed_matter": _P + "condensed_matter", "solid_state": _P + "condensed_matter",
    "game_theory": _P + "game_theory",
    # the Pressure Fighting System's combat grammar, enforced (Matt, 2026-10-06): a closed-set
    # classification of an exchange, MATCH/NO_MATCH, the first link of the chain to optimal
    "pressure_fighting": _P + "pressure_fighting", "combat_grammar": _P + "pressure_fighting", "games": _P + "game_theory", "strategy": _P + "game_theory",
    "archaeology": _P + "archaeology", "radiocarbon": _P + "archaeology", "radiometric_dating": _P + "archaeology",
    # the elliptic-curve L-value door for the Birch and Swinnerton-Dyer stick (tick stick, 2026-10-05)
    "elliptic_curves": _P + "elliptic_curves", "elliptic": _P + "elliptic_curves", "bsd": _P + "elliptic_curves",
}

# Witness-surface verifiers — surfaced ONLY when surface == "witness" (the .org overlay).
# The foundation is shared on both surfaces; this governs only what the surface EXPOSES.
# `scripture` (ref resolution) is deferred — it needs the Bible corpus data.
WITNESS_VERIFIERS: Dict[str, str] = {
    "theology_doctrine": _P + "theology_doctrine", "theology": _P + "theology_doctrine",
    "doctrine": _P + "theology_doctrine", "scripture_doctrine": _P + "theology_doctrine",
    "witness": _P + "witness", "testimony": _P + "witness",
    "scripture": _P + "scripture", "scripture_anchors": _P + "scripture",
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
    # VERIFIERS AS DATA (Gen 3 · 2, 2026-10-04): the admitted specs of this domain, run by the generic
    # evaluator; a result a module already produced shadows the spec's. A domain with no module is
    # served by its specs alone — a new domain without a deploy.
    from . import spec as _spec
    results.extend(_spec.run_for_domain(d, packet, have=(r.name for r in results)))
    return results


__all__ = [
    "VerifierResult", "VerifierStatus", "na", "confirm", "mismatch", "error",
    "run_for_domain", "VERIFIERS", "WITNESS_VERIFIERS", "CROSS_CUTTING_VERIFIERS",
]
