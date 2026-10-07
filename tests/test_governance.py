"""Unit-pin the governance verifier (A2, 2026-10-06). The decision-packet SHAPE check: a complete packet
(title, scope, red_items, floor_items, way_path, execution_steps, witnesses, all non-empty, valid scope,
a real way_path) passes; a packet missing a required field is rejected; a non-object errors."""
from __future__ import annotations
from concordance.verifiers import governance as GV

_PKT = {"title": "Shop order 12", "scope": "local", "red_items": ["spindle rpm <= 12000"],
        "floor_items": ["margin >= 18%"],
        "way_path": "classify the work, run the gates, then seal the record",
        "execution_steps": ["classify", "gate", "seal"], "witnesses": ["shop_owner"]}


def test_decision_packet_shape():
    assert GV.verify_decision_packet_shape(_PKT).status == "CONFIRMED"
    bad = {k: v for k, v in _PKT.items() if k != "red_items"}
    assert GV.verify_decision_packet_shape(bad).status == "MISMATCH"
    assert GV.verify_decision_packet_shape("not a packet").status == "ERROR"
