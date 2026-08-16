"""Cross-domain BRIDGE verifiers — the guard at the SEAM between two domains.

A single-domain verifier checks a step in its OWN terms; it cannot see the JOIN. But a whole class of
real errors lives exactly at the boundary between domains — a statistical p-value asserted as a
MATHEMATICAL PROOF, a quantum treatment carried past its validity range, a scaling law applied across
regimes with no dimensional analysis. The Floor Assembly joins aligned theories ACROSS domains; this
refuses the UNjustified join. Ported from the master concordance registry v1 §4 (bridge_modules), the
six boundary HALTs, reframed onto today's derivation moat.

It fires only on a `uses` edge whose two steps are in DIFFERENT domains. Deterministic, no I/O:
  - a category error at the seam (a p-value claimed as proof) is a MISMATCH → the derivation BROKEN.
  - a crossing whose boundary justification is simply ABSENT is INCOMPLETE — unproven at the seam,
    never a false HOLDS (our-failure-is-not-their-falsehood). A caller satisfies it by declaring the
    justification on the crossing step: `step["bridge"] = {"dimensional_analysis": true, ...}`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

_ALIAS = {"math": "mathematics", "maths": "mathematics", "cs": "computer_science",
          "comp_sci": "computer_science", "compsci": "computer_science", "stats": "statistics",
          "stat": "statistics", "chem": "chemistry", "bio": "biology", "phys": "physics"}


def _canon(d: str) -> str:
    d = (d or "").strip().lower().replace("-", "_").replace(" ", "_")
    return _ALIAS.get(d, d)


# A step asserting mathematical PROOF while it stands on a statistical step — the p-value-as-proof
# category error. The single most common cross-domain fallacy; it HALTs.
_PROOF_CLAIM = re.compile(
    r"\b(proof|proven|proves|q\.?e\.?d|theorem|mathematically (?:certain|proven|true)|"
    r"proves that|establishes that .* for all|therefore .* is true for all)\b", re.I)
# A step making a SCALING claim — scale_regime spans every domain pair, so it is checked by the claim,
# not by a fixed pair.
_SCALE_CLAIM = re.compile(r"\b(scal\w+|proportional to|goes as|varies as|power[- ]law|"
                          r"order of magnitude|asymptotic\w*)\b", re.I)
_SCALE_REQUIRE = ("dimensional_analysis", "regime")

# The five fixed-pair bridges (registry §4). `forbid_proof` HALTs on a proof claim; `require` HALTs
# (as INCOMPLETE) unless the crossing step DECLARES the listed boundary justifications.
BRIDGES = (
    {"id": "theory_inference", "pair": frozenset({"mathematics", "statistics"}), "mode": "forbid_proof",
     "red": "statistical significance claimed as MATHEMATICAL PROOF — a p-value does not measure the "
            "probability that a claim is true",
     "cite": "ASA statement on p-values (2016): a p-value is evidence about data under a model, not a proof"},
    {"id": "quantum_classical", "pair": frozenset({"physics", "chemistry"}), "mode": "require",
     "require": ("classical_limit", "decoherence_timescale"),
     "red": "a quantum treatment used outside its validity range without the classical limit",
     "cite": "the correspondence principle — quantum results must reduce to classical as h-bar -> 0 / "
             "for large quantum numbers"},
    {"id": "discrete_continuous", "pair": frozenset({"computer_science", "mathematics"}), "mode": "require",
     "require": ("convergence", "error_bound"),
     "red": "a numerical / discrete method used for a continuous claim without demonstrated convergence",
     "cite": "a discretization is not the continuum until convergence and an error bound are shown"},
    {"id": "deterministic_stochastic", "pair": frozenset({"physics", "statistics"}), "mode": "require",
     "require": ("noise_model", "ergodicity"),
     "red": "a stochastic model applied without a specified noise model or stated ergodicity",
     "cite": "noise must be specified, not assumed; a time-average equals an ensemble-average only if "
             "the process is ergodic"},
    {"id": "molecular_cellular", "pair": frozenset({"chemistry", "biology"}), "mode": "require",
     "require": ("concentration_units", "in_vitro_or_in_vivo"),
     "red": "a molecular result carried to the cellular scale without consistent units or an "
            "in-vitro / in-vivo declaration",
     "cite": "concentration and context (in vitro vs in vivo) do not transfer silently across scales"},
)


def _bridge_for(a: str, b: str) -> Optional[Dict[str, Any]]:
    pair = frozenset({_canon(a), _canon(b)})
    for br in BRIDGES:
        if br["pair"] == pair:
            return br
    return None


def _declares(step: Dict[str, Any], key: str) -> bool:
    """A crossing step declares its boundary justification in a `bridge` dict: {key: truthy}."""
    b = step.get("bridge") if isinstance((step or {}).get("bridge"), dict) else {}
    return bool(b.get(key))


def check(crossing_domain: str, crossing_step: Dict[str, Any], dep_domain: str) -> Dict[str, Any]:
    """The seam between a step (`crossing_step`, in `crossing_domain`) and a step it USES (in
    `dep_domain`). Returns a verifier-shaped verdict:
      MISMATCH        — a category error at the boundary (a p-value claimed as proof). HALT.
      INCOMPLETE      — the crossing's boundary justification is absent. Unproven, not false.
      NOT_APPLICABLE  — no registered bridge, or the bridge is satisfied.
    """
    a, b = _canon(crossing_domain), _canon(dep_domain)
    if not a or not b or a == b:
        return {"status": "NOT_APPLICABLE"}
    claim = str((crossing_step or {}).get("claim") or "")

    # scale_regime — spans every pair; fires on a scaling claim that crosses any domain boundary.
    if _SCALE_CLAIM.search(claim):
        missing = [k for k in _SCALE_REQUIRE if not _declares(crossing_step, k)]
        if missing:
            return {"status": "INCOMPLETE", "bridge": "scale_regime", "missing": missing,
                    "red": "a scaling law applied across regimes without dimensional analysis / regime "
                           "boundaries",
                    "cite": "a scaling law holds only within the regime its dimensional analysis defines"}

    br = _bridge_for(a, b)
    if not br:
        return {"status": "NOT_APPLICABLE"}
    if br["mode"] == "forbid_proof":
        if _PROOF_CLAIM.search(claim):
            return {"status": "MISMATCH", "bridge": br["id"], "red": br["red"], "cite": br["cite"]}
        return {"status": "NOT_APPLICABLE", "bridge": br["id"]}
    # require mode
    missing = [k for k in br["require"] if not _declares(crossing_step, k)]
    if missing:
        return {"status": "INCOMPLETE", "bridge": br["id"], "missing": missing,
                "red": br["red"], "cite": br["cite"]}
    return {"status": "NOT_APPLICABLE", "bridge": br["id"]}
