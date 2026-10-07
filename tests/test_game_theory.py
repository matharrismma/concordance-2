"""Unit-pin the game_theory verifier (A2, 2026-10-06). Row 0 of [[3,2],[1,0]] strictly dominates row 1
(3>1 and 2>0). A false dominance claim is caught; a missing field is NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import game_theory as GT


def test_dominant_strategy():
    assert GT.verify_dominant_strategy({"dom_matrix": [[3, 2], [1, 0]], "dom_row": 0,
                                        "dominated_row": 1, "claimed_dominates": True}).status == "CONFIRMED"
    assert GT.verify_dominant_strategy({"dom_matrix": [[3, 2], [1, 0]], "dom_row": 0,
                                        "dominated_row": 1, "claimed_dominates": False}).status == "MISMATCH"
    assert GT.verify_dominant_strategy({}).status == "NOT_APPLICABLE"
