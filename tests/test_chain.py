"""M3 (core) — the Chain executor (conductor/chain.py, 2026-10-06). A synthetic, benign traveler-shaped
chain (NOT the shop's real paper traveler). Proves the Canon's three invariants: a benign chain walks its
PASS edges to a terminal and seals each step; a step with no witness halts the walk (cannot advance
unsigned); movement is only along the edge the verdict selects (cannot skip); edge keys must be verdicts.
"""
from __future__ import annotations

import time

import pytest

from conductor import chain as CH


def _traveler():
    return {
        "po": CH.step("po", "accept a purchase order for 20 aluminum brackets to print",
                      {"PASS": "machine", "QUARANTINE": "mrb"}),
        "machine": CH.step("machine", "mill the brackets to standard tolerances with coolant",
                           {"PASS": "ship", "QUARANTINE": "mrb"}),
        "ship": CH.step("ship", "ship the finished brackets to the customer", {}),          # terminal
        "mrb": CH.step("mrb", "route nonconforming parts to the material review board", {}),  # branch terminal
    }


def test_walk_completes_benign_traveler(tmp_path):
    r = CH.walk(_traveler(), "po", ledger_dir=tmp_path)
    assert r["status"] == "complete"
    assert [p["step"] for p in r["walked"]] == ["po", "machine", "ship"]   # PASS edges; mrb NOT taken
    assert all(p["verdict"] == "PASS" for p in r["walked"])
    assert len(r["sealed_path"]) == 3                                       # every step sealed


def test_cannot_advance_unsigned(tmp_path):
    ch = _traveler()
    ch["machine"] = CH.step("machine", "mill the brackets", {"PASS": "ship"}, witnesses=())
    r = CH.walk(ch, "po", ledger_dir=tmp_path)
    assert r["status"] == "halted_unsigned"
    assert r["walked"][-1]["step"] == "machine"
    assert "UNSIGNED" in r["walked"][-1]["halted"]


def test_cannot_skip_only_matching_edge_is_followed(tmp_path):
    ch = {"po": CH.step("po", "accept the order", {"QUARANTINE": "mrb"}),
          "mrb": CH.step("mrb", "review the nonconforming parts", {})}
    r = CH.walk(ch, "po", ledger_dir=tmp_path)
    assert r["status"] == "complete"
    assert [p["step"] for p in r["walked"]] == ["po"]   # PASS has no edge -> terminal; did not jump to mrb


def test_edge_keys_must_be_verdicts():
    with pytest.raises(ValueError):
        CH.step("x", "do the thing", {"OK": "y"})


def test_fresh_step_quarantines_into_its_branch(tmp_path):
    # a step still inside its deliberate WAIT window quarantines, and the walk follows the QUARANTINE edge
    ch = {"po": CH.step("po", "accept the order", {"PASS": "machine", "QUARANTINE": "mrb"},
                        target={"created_epoch": int(time.time())}),   # fresh -> WAIT gate quarantines
          "machine": CH.step("machine", "mill the brackets", {}),
          "mrb": CH.step("mrb", "review the nonconforming parts", {})}
    r = CH.walk(ch, "po", ledger_dir=tmp_path)
    assert r["walked"][0]["verdict"] == "QUARANTINE"
    assert [p["step"] for p in r["walked"]] == ["po", "mrb"]   # routed down the QUARANTINE edge, not PASS
