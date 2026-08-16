"""Cross-domain BRIDGE verifiers — the guard at the SEAM (registry §4, LH-3).

A single-domain verifier checks a step in its own terms; it cannot see the JOIN. These hold the six
boundary HALTs: a p-value asserted as mathematical PROOF is a category error (BROKEN); a crossing
whose boundary justification is absent is INCOMPLETE (unproven, never a false HOLDS). Pure.
"""
from concordance.verifiers import bridges


# ── the seam check in isolation ───────────────────────────────────────────────────────────────────
def test_p_value_claimed_as_proof_is_a_category_error():
    step = {"claim": "the p-value is 0.001, therefore the theorem is proven for all n"}
    r = bridges.check("mathematics", step, "statistics")
    assert r["status"] == "MISMATCH" and r["bridge"] == "theory_inference" and r["cite"]


def test_a_statistics_step_that_does_not_claim_proof_passes():
    step = {"claim": "the effect is significant at p < 0.01"}
    assert bridges.check("mathematics", step, "statistics")["status"] == "NOT_APPLICABLE"


def test_a_require_bridge_without_its_justification_is_incomplete_not_broken():
    # quantum->classical carried with no classical limit declared: unproven at the seam, not false
    step = {"claim": "the molecular orbital energies follow from the quantum treatment"}
    r = bridges.check("chemistry", step, "physics")
    assert r["status"] == "INCOMPLETE" and r["bridge"] == "quantum_classical"
    assert set(r["missing"]) == {"classical_limit", "decoherence_timescale"}


def test_declaring_the_justification_satisfies_the_bridge():
    step = {"claim": "...from the quantum treatment",
            "bridge": {"classical_limit": True, "decoherence_timescale": True}}
    assert bridges.check("chemistry", step, "physics")["status"] == "NOT_APPLICABLE"


def test_a_scaling_claim_across_any_boundary_needs_dimensional_analysis():
    step = {"claim": "metabolic rate scales as mass to the 3/4 power"}
    r = bridges.check("biology", step, "physics")
    assert r["status"] == "INCOMPLETE" and r["bridge"] == "scale_regime" and "dimensional_analysis" in r["missing"]


def test_same_domain_edge_is_never_a_bridge():
    assert bridges.check("mathematics", {"claim": "QED, proven"}, "mathematics")["status"] == "NOT_APPLICABLE"


def test_domain_aliases_resolve():
    step = {"claim": "p < 0.05 proves the theorem"}
    assert bridges.check("math", step, "stats")["status"] == "MISMATCH"


# ── end-to-end through the derivation moat ────────────────────────────────────────────────────────
def test_derivation_breaks_at_the_seam_when_a_p_value_is_claimed_as_proof():
    from concordance import derivation as d
    steps = [
        {"id": "s1", "domain": "statistics", "claim": "observed p = 0.001",
         "spec": {"STAT_VERIFY": {}}},
        {"id": "s2", "domain": "mathematics", "claim": "therefore the theorem is proven for all n",
         "uses": ["s1"], "spec": {"mode": "identity", "params": {}}},
    ]
    out = d.verify_derivation(steps)
    assert out["verdict"] == "BROKEN" and out["broken_at"] == "s2"
    s2 = next(e for e in out["trail"] if e["id"] == "s2")
    assert s2.get("bridge", {}).get("bridge") == "theory_inference"
