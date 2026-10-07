"""Unit-pin the rhetoric verifier (A2, 2026-10-06). A complete argument has a premise, a conclusion, and
a warrant linking them (Toulmin). A false completeness claim is caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import rhetoric as RH


def test_argument_structure():
    assert RH.verify_argument_structure({"has_premise": True, "has_conclusion": True, "has_warrant": True,
                                         "claimed_is_complete_argument": True}).status == "CONFIRMED"
    assert RH.verify_argument_structure({"has_premise": True, "has_conclusion": False, "has_warrant": True,
                                         "claimed_is_complete_argument": True}).status == "MISMATCH"
    assert RH.verify_argument_structure({}).status == "NOT_APPLICABLE"
