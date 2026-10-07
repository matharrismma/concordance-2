"""Unit-pin the molecular_geometry verifier (A2, 2026-10-06). VSEPR: 4 bonding domains, 0 lone pairs
-> tetrahedral, 109.5 deg (e.g. methane)."""
from __future__ import annotations
from concordance.verifiers import molecular_geometry as MG


def test_vsepr():
    assert MG.verify_vsepr({"bonding_domains": 4, "lone_pairs": 0, "claimed_geometry": "tetrahedral",
                            "claimed_bond_angle_deg": 109.5}).status == "CONFIRMED"
    assert MG.verify_vsepr({"bonding_domains": 4, "lone_pairs": 0,
                            "claimed_geometry": "linear"}).status == "MISMATCH"
    assert MG.verify_vsepr({}).status == "NOT_APPLICABLE"
