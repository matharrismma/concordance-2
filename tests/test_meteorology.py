"""Unit-pin the meteorology verifier (A2, 2026-10-06). Saturation vapor pressure at 20 C ~ 23.4 hPa
(Magnus/Tetens). Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import meteorology as ME


def test_saturation_vapor_pressure():
    assert ME.verify_saturation_vapor_pressure({"temperature_c_for_es": 20,
                                                "claimed_saturation_vapor_pressure_hpa": 23.4}).status == "CONFIRMED"
    assert ME.verify_saturation_vapor_pressure({"temperature_c_for_es": 20,
                                                "claimed_saturation_vapor_pressure_hpa": 10.0}).status == "MISMATCH"
    assert ME.verify_saturation_vapor_pressure({}).status == "NOT_APPLICABLE"
