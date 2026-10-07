"""Unit-pin the ecology verifier (A2, 2026-10-06). Shannon diversity of two equally-common species is
ln(2) ~ 0.693 (nats). Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import ecology as ECO


def test_shannon_diversity():
    assert ECO.verify_shannon_diversity({"species_proportions": [0.5, 0.5], "claimed_shannon_index": 0.693}).status == "CONFIRMED"
    assert ECO.verify_shannon_diversity({"species_proportions": [0.5, 0.5], "claimed_shannon_index": 1.5}).status == "MISMATCH"
    assert ECO.verify_shannon_diversity({}).status == "NOT_APPLICABLE"
