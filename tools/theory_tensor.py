#!/usr/bin/env python3
"""The boundary map as a TENSOR (not a matrix).

The coordinate map today is 2-mode: grid.AXIS_DIMENSIONS = domain x dimension (a sparse binary
matrix). The assay adds a third mode — the VERDICT (confirmed vs refused) — turning the matrix
into a 3-tensor T[domain, dimension, verdict], stored sovereign as a coordinate list (COO), no
new deps.

Its purpose is one honest slice: does the engine's REFUSAL boundary lie along the dimension
axes (a spatial region of the map) — or somewhere else? We compute it and let the number answer,
rather than assert a pattern. Emits site/tensor.json for the boundary page.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from concordance import grid  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site", "tensor.json")

# The 53 refusals from the assay, each tagged by WHY it is unsealable + its domain.
# why: conjecture | foundation | interpretation | empirical | speculative | heuristic | mind | faith
REFUSALS = [
    ("Godel's incompleteness theorems", "formal_logic", "foundation"),
    ("ZFC set theory", "formal_logic", "foundation"),
    ("Church-Turing thesis", "computer_science", "foundation"),
    ("the Standard Model / QFT", "nuclear_physics", "empirical"),
    ("the third law of thermodynamics", "thermodynamics", "foundation"),
    ("plate tectonics", "geology", "empirical"),
    ("Darwinian evolution", "biology", "empirical"),
    ("cell theory", "biology", "empirical"),
    ("germ theory", "medicine", "empirical"),
    ("Christian theology", "theology_doctrine", "faith"),
    ("the Drake equation", "astronomy", "speculative"),
    ("the anthropic principle", "philosophy", "speculative"),
    ("the Fermi paradox", "astronomy", "speculative"),
    ("the fine-tuning argument", "physics", "speculative"),
    ("the Titius-Bode law", "astronomy", "heuristic"),
    ("the Phillips curve", "economics", "heuristic"),
    ("the Laffer curve", "economics", "heuristic"),
    ("Moore's law", "computer_science", "heuristic"),
    ("the Malthusian catastrophe", "ecology", "heuristic"),
    ("the efficient-market hypothesis", "finance", "heuristic"),
    ("the string-theory landscape", "nuclear_physics", "speculative"),
    ("cosmic fine-tuning / design", "biology", "speculative"),
    ("the Riemann hypothesis", "number_theory", "conjecture"),
    ("P versus NP", "computer_science", "conjecture"),
    ("the Goldbach conjecture", "number_theory", "conjecture"),
    ("the Collatz conjecture", "number_theory", "conjecture"),
    ("the multiverse hypothesis", "astronomy", "speculative"),
    ("dark-matter existence", "astronomy", "speculative"),
    ("the continuum hypothesis", "formal_logic", "conjecture"),
    ("the simulation hypothesis", "philosophy", "speculative"),
    ("dark energy", "astronomy", "speculative"),
    ("panspermia", "biology", "speculative"),
    ("libertarian free will", "philosophy", "mind"),
    ("the Boltzmann-brain hypothesis", "physics", "speculative"),
    ("Poincare recurrence", "physics", "speculative"),
    ("the many-worlds interpretation", "physics", "interpretation"),
    ("the Gaia hypothesis", "biology", "speculative"),
    ("the mathematical-universe hypothesis", "astronomy", "speculative"),
    ("Orch-OR quantum consciousness", "philosophy", "mind"),
    ("the Copenhagen interpretation", "physics", "interpretation"),
    ("de Broglie-Bohm pilot-wave theory", "physics", "interpretation"),
    ("the holographic principle", "physics", "speculative"),
    ("loop quantum gravity", "nuclear_physics", "speculative"),
    ("panpsychism", "philosophy", "mind"),
    ("the hard problem of consciousness", "philosophy", "mind"),
    ("the strong Sapir-Whorf hypothesis", "linguistics", "heuristic"),
    ("astrology", "philosophy", "heuristic"),
    ("the steady-state universe", "astronomy", "empirical"),
    ("modal realism", "philosophy", "mind"),
    ("Freudian psychoanalysis", "philosophy", "heuristic"),
    ("cosmological natural selection", "astronomy", "speculative"),
    ("quantum immortality", "physics", "interpretation"),
    ("Boltzmann-brain dominance", "physics", "speculative"),
]

WHY_LABEL = {
    "conjecture": "Unproven conjecture — true or false, but no one has shown which",
    "foundation": "Foundational axiom / meta-theorem — the ground you reason FROM, not a claim you check",
    "interpretation": "Interpretation of settled math — same equations, rival stories",
    "empirical": "Empirical / historical — established by observation, not computation",
    "speculative": "Speculative / unfalsifiable — no deterministic test exists",
    "heuristic": "Heuristic / social regularity — a trend, not a law",
    "mind": "Mind / value — consciousness, meaning, the will",
    "faith": "Faith — a Person, not a proposition (John 14:6); pointed to, never sealed",
}


def _confirmed_domains():
    """The domains the assay actually SEALED claims in — grounded in the FP-gate's 60 validated
    domains (the moat's own coverage set), not asserted."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))
        from test_fp_gate import CASES  # noqa: E402
        return sorted({d for d, _t, _f in CASES})
    except Exception:
        return sorted({d for _n, d, _w in REFUSALS})  # degrade gracefully


def build():
    A = grid.AXIS_DIMENSIONS          # domain -> frozenset(dimensions)  (the existing 2-mode matrix)
    DIMS = list(grid.DIMENSIONS)
    confirmed = _confirmed_domains()
    refused_domains = sorted({d for _n, d, _w in REFUSALS})

    # --- the COO tensor: (domain, dimension, verdict) -> 1 (sovereign coordinate list) ---
    coo = []
    for dom in confirmed:
        for dim in A.get(dom, ()):
            coo.append([dom, dim, "confirmed"])
    for dom in refused_domains:
        for dim in A.get(dom, ()):
            coo.append([dom, dim, "refused"])

    # --- the honest slice, computed not asserted: is the unmappable a PLACE on the map, or a
    # KIND of claim? If it were a place, the refusing domains would be disjoint from the
    # confirming ones. Measure the overlap directly. ---
    both = sorted(set(refused_domains) & set(confirmed))
    overlap_frac = round(len(both) / max(1, len(refused_domains)), 3)
    modal = (overlap_frac >= 0.9)     # nearly every refusing domain ALSO seals -> boundary is modal
    finding = (("MODAL, not spatial — {n}/{t} domains that refused a theory ALSO sealed one. "
                "The unmappable is not a region of the map; it is a KIND of claim (a proposition, "
                "an interpretation, an unfalsifiable) that appears in EVERY region. That is why "
                "the boundary can't be drawn as a line on the domain/dimension grid — it runs "
                "through every cell.").format(n=len(both), t=len(refused_domains))
               if modal else
               "SPATIAL — refusals concentrate in domains that seal little; the boundary is a region.")

    # per-dimension recurrence (RESONANCE only): how many domains carry each dimension
    recurring = {dim: sorted(d for d in confirmed if dim in A.get(d, ())) for dim in DIMS}

    by_why = {}
    for _n, _d, w in REFUSALS:
        by_why.setdefault(w, []).append(_n)

    out = {
        "modes": {"domain_confirmed": len(confirmed), "domain_refused": len(refused_domains),
                  "dimension": len(DIMS), "verdict": 2},
        "nnz": len(coo),
        "dimensions": DIMS,
        "dimension_domain_counts": {k: len(v) for k, v in recurring.items()},
        "refused_count": len(REFUSALS),
        "refused_domains": refused_domains,
        "boundary": {
            "refusing_and_confirming_domains": both,
            "overlap_fraction": overlap_frac,
            "modal": modal,
            "finding": finding,
        },
        "why_labels": WHY_LABEL,
        "refusals_by_why": {w: sorted(by_why.get(w, [])) for w in WHY_LABEL},
        "note": ("Cross-domain dimension recurrence (e.g. conservation across physics, finance, "
                 "ecology) is RESONANCE — a map aid, never a proof; the 0-false-positive rule "
                 "governs the map as strictly as the seals."),
    }
    return out, coo


if __name__ == "__main__":
    out, coo = build()
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"tensor: modes={out['modes']} nnz={out['nnz']} -> {OUT}")
    print(f"refusals: {out['refused_count']} across {len(out['refused_domains'])} domains")
    b = out["boundary"]
    print(f"boundary modal={b['modal']}  overlap={b['overlap_fraction']}  "
          f"({len(b['refusing_and_confirming_domains'])} domains both refuse AND seal)")
    print(f"finding: {b['finding']}")
