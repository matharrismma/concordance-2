"""Unit-pin the soil_science verifier (A2, 2026-10-06). Blueberries suit acidic soil (pH 4.5); a
40/40/20 sand/silt/clay mix classifies as loam. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import soil_science as SS


def test_ph_suitability():
    assert SS.verify_ph_suitability({"crop": "blueberry", "soil_ph": 4.5, "claimed_ph_suitable": True}).status == "CONFIRMED"
    assert SS.verify_ph_suitability({"crop": "blueberry", "soil_ph": 4.5, "claimed_ph_suitable": False}).status == "MISMATCH"
    assert SS.verify_ph_suitability({}).status == "NOT_APPLICABLE"


def test_soil_texture():
    assert SS.verify_soil_texture({"sand_pct": 40, "silt_pct": 40, "clay_pct": 20, "claimed_texture_class": "loam"}).status == "CONFIRMED"
    assert SS.verify_soil_texture({"sand_pct": 40, "silt_pct": 40, "clay_pct": 20, "claimed_texture_class": "clay"}).status == "MISMATCH"
