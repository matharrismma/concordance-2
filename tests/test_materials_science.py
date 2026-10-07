"""Unit-pin the materials_science verifier (A2: verifier test-depth, 2026-10-06).
Density = mass/volume (1000 kg / 1 m^3 = 1000); hardness comparison (9 > 6). Wrong claim caught; missing
field NOT_APPLICABLE.
"""
from __future__ import annotations

from concordance.verifiers import materials_science as MS


def test_density():
    assert MS.verify_density({"mass_kg": 1000, "volume_m3": 1.0, "claimed_density_kg_per_m3": 1000}).status == "CONFIRMED"
    assert MS.verify_density({"mass_kg": 1000, "volume_m3": 1.0, "claimed_density_kg_per_m3": 500}).status == "MISMATCH"
    assert MS.verify_density({}).status == "NOT_APPLICABLE"


def test_hardness_comparison():
    assert MS.verify_hardness_comparison({"material_a_hardness": 9, "material_b_hardness": 6,
                                          "claimed_a_harder_than_b": True}).status == "CONFIRMED"
    assert MS.verify_hardness_comparison({"material_a_hardness": 9, "material_b_hardness": 6,
                                          "claimed_a_harder_than_b": False}).status == "MISMATCH"
