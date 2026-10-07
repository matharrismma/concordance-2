"""Unit-pin the agriculture verifier (A2, 2026-10-06). Blueberries suit acidic soil (pH 4.5); a crop
rotation that varies the family is valid. Missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import agriculture as AG


def test_soil_ph():
    assert AG.verify_soil_ph({"crop": "blueberry", "soil_ph": 4.5}).status == "CONFIRMED"
    assert AG.verify_soil_ph({"crop": "blueberry", "soil_ph": 8.0}).status == "MISMATCH"
    assert AG.verify_soil_ph({}).status == "NOT_APPLICABLE"


def test_rotation():
    assert AG.verify_rotation({"crop": "corn", "rotation": ["corn", "soybean", "corn"]}).status == "CONFIRMED"
