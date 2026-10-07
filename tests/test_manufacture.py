"""The Conductor's shop-domain CALC door (concordance.manufacture).

Synthetic numbers only — this door is proven on fixtures, never on anyone's confidential design data.
It checks the composition (verify -> seal -> disposition), not the manufacturing math itself (that is
tests for verifiers/manufacturing.py). RSS of [0.1, 0.2, 0.2] = sqrt(0.09) = 0.3.
"""
from __future__ import annotations

from concordance import manufacture as M


def test_holds_calc_is_sealed_and_calculated():
    r = M.manufacture("the RSS tolerance stack closes at 0.3 mm",
                      {"tolerances": [0.1, 0.2, 0.2], "claimed_rss": 0.3})
    assert r["ok"] is True
    assert r["verdict"] == "HOLDS"
    assert r["calc_kind"] == "tolerance_stack_rss"
    assert r["disposition_earned"] == "CALCULATED"
    assert r["seal"]                      # a real content hash was minted
    assert r["ledgered"] is True          # HOLDS => PASS => hash-chained ledger entry


def test_wrong_numbers_are_refused_and_unsealed():
    r = M.manufacture("the RSS tolerance stack closes at 0.5 mm",
                      {"tolerances": [0.1, 0.2, 0.2], "claimed_rss": 0.5})
    assert r["ok"] is True
    assert r["verdict"] == "BROKEN"
    assert r["disposition_earned"] == "REFUSED"
    assert r["seal"] is None              # a miss stays a miss — nothing sealed
    assert r["ledgered"] is False


def test_process_capability_shape_is_detected():
    r = M.manufacture("the process is capable",
                      {"usl": 110.0, "lsl": 90.0, "process_mean": 100.0,
                       "process_sigma": 2.0, "claimed_cp_capable": True})
    assert r["ok"] is True
    assert r["calc_kind"] == "process_capability"
    assert r["verdict"] == "HOLDS"        # Cp = 20/12 = 1.67 >= 1.33, centered => capable


def test_claimed_disposition_is_carried_never_upgraded():
    r = M.manufacture("the RSS tolerance stack closes at 0.3 mm",
                      {"tolerances": [0.1, 0.2, 0.2], "claimed_rss": 0.3},
                      disposition="controlled")
    assert r["disposition_claimed"] == "CONTROLLED"
    assert r["disposition_earned"] == "CALCULATED"   # the engine reports what the calc earned, not the label


def test_bad_inputs_are_refused_cleanly():
    assert M.manufacture("", {"tolerances": [0.1], "claimed_rss": 0.1})["ok"] is False
    assert M.manufacture("claim", {})["ok"] is False
    assert M.manufacture("claim", {"tolerances": [0.1], "claimed_rss": 0.1},
                         disposition="bogus")["ok"] is False


def test_unknown_calc_shape_does_not_crash():
    r = M.manufacture("some claim with no checkable numbers", {"foo": 1})
    assert r["ok"] is True
    assert r["calc_kind"] == "unknown"
    assert r["seal"] is None              # nothing to verify => no seal
