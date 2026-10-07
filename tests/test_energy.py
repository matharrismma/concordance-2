"""Unit-pin the energy verifier (A2, 2026-10-06). 1 kWh = 1000 Wh. Wrong claim caught; missing field NA."""
from __future__ import annotations
from concordance.verifiers import energy as EN


def test_kwh_wh_consistency():
    assert EN.verify_kwh_wh_consistency({"kwh": 1, "claimed_wh": 1000}).status == "CONFIRMED"
    assert EN.verify_kwh_wh_consistency({"kwh": 1, "claimed_wh": 500}).status == "MISMATCH"
    assert EN.verify_kwh_wh_consistency({}).status == "NOT_APPLICABLE"
