"""Unit-pin the physical_constants verifier (A2, 2026-10-06). The speed of light is 299792458 m/s
(exact, SI). A clearly wrong value is caught; a missing field is NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import physical_constants as PC


def test_physical_constant():
    assert PC.verify_physical_constant({"constant": "speed_of_light", "claimed_value": 299792458,
                                        "claimed_unit": "m/s"}).status == "CONFIRMED"
    assert PC.verify_physical_constant({"constant": "speed_of_light", "claimed_value": 1.0e8,
                                        "claimed_unit": "m/s"}).status == "MISMATCH"
    assert PC.verify_physical_constant({}).status == "NOT_APPLICABLE"
