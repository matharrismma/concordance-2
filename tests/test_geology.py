"""Unit-pin the geology verifier (A2, 2026-10-06). Mohs: a harder mineral (7) scratches a softer one (5).
A false claim is caught; a missing field is NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import geology as GL


def test_mohs_scratch():
    assert GL.verify_mohs_scratch({"harder_mineral_mohs": 7, "softer_mineral_mohs": 5,
                                   "claimed_can_scratch": True}).status == "CONFIRMED"
    assert GL.verify_mohs_scratch({"harder_mineral_mohs": 5, "softer_mineral_mohs": 7,
                                   "claimed_can_scratch": True}).status == "MISMATCH"
    assert GL.verify_mohs_scratch({}).status == "NOT_APPLICABLE"
