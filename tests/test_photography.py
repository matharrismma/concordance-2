"""Unit-pin the photography verifier (A2, 2026-10-06). Exposure value EV = log2(N^2 / t); f/8 at 1/250 s
-> log2(64*250) ~ 13.97. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import photography as PG


def test_exposure_value():
    assert PG.verify_exposure_value({"f_number": 8, "shutter_seconds": 0.004, "claimed_exposure_value": 13.97}).status == "CONFIRMED"
    assert PG.verify_exposure_value({"f_number": 8, "shutter_seconds": 0.004, "claimed_exposure_value": 10.0}).status == "MISMATCH"
    assert PG.verify_exposure_value({}).status == "NOT_APPLICABLE"
