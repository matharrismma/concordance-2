"""Unit-pin the pressure_fighting verifier's boundary behavior (A2, 2026-10-06). This is Matt's combat
grammar (data/pfs_grammar.json); a valid observation needs his position fixtures, so here we pin the
HONEST boundary: card validation is the next link and is NOT half-checked (NA), and a malformed
observation is rejected rather than waved through."""
from __future__ import annotations
from concordance.verifiers import pressure_fighting as PF


def test_card_is_not_half_checked():
    # verify_card is a declared-but-not-yet-enforced link; it must return NA, never a false pass.
    assert PF.verify_card({}).status == "NOT_APPLICABLE"


def test_malformed_observation_is_rejected():
    r = PF.verify_observation({})
    assert r.status in ("MISMATCH", "NOT_APPLICABLE")   # never CONFIRMED on an empty observation
    assert PF.verify_observation("not an object").status == "ERROR"
