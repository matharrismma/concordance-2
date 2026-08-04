"""The ops log — a count may only be claimed with its substance split, and records survive.

G1's fix made testable: every claimed count carries total / substance / stubs / ratio with the
threshold that defined them, and the claim itself is logged with WHERE it reached a reader.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import ops  # noqa: E402


def _tmp_data_dir():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-ops-")
    return prior


def _restore(prior):
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


_FIX = {
    "a": {"id": "a", "body": "x" * 400},                       # substance
    "b": {"id": "b", "body": "a pointer"},                     # stub
    "c": {"id": "c", "body": ""},                              # stub
    "e": {"id": "e", "kind": "connection", "body": ""},        # edge — excluded entirely
}


def test_substance_counts_the_g1_split_and_says_what_it_counted():
    s = ops.substance(_FIX)
    assert s["total"] == 3                     # the connection card is an edge, not a holding
    assert s["substance_cards"] == 1 and s["stub_cards"] == 2
    assert abs(s["stub_ratio"] - 2 / 3) < 1e-3
    assert s["stub_threshold_chars"] == ops.STUB_BODY_CHARS == 120
    for k in ("total", "substance_cards", "stub_cards", "stub_ratio"):
        assert s["means"][k], f"{k} reported with no definition — a number waiting to be misread"


def test_a_count_claim_is_logged_with_both_numbers_and_where_it_went():
    prior = _tmp_data_dir()
    try:
        s = ops.claim_count(_FIX, where="/capabilities")
        assert s["stub_cards"] == 2
        rec = ops.tail(1)[0]
        assert rec["event"] == "count_claimed" and rec["where"] == "/capabilities"
        # the log record itself carries the split — a headline total alone is exactly the
        # single-number claim G1 forbids
        assert rec["total"] == 3 and rec["substance_cards"] == 1 and rec["stub_cards"] == 2
    finally:
        _restore(prior)


def test_records_append_and_tail_reads_them_back_oldest_first():
    prior = _tmp_data_dir()
    try:
        ops.log("deploy", files=2)
        ops.log("gate", verdict="PASS")
        got = ops.tail(10)
        assert [r["event"] for r in got] == ["deploy", "gate"]
        assert got[0]["files"] == 2 and got[1]["verdict"] == "PASS"
        assert ops.tail(1)[0]["event"] == "gate"
    finally:
        _restore(prior)


def test_a_nameless_event_is_refused_and_a_missing_log_is_an_empty_history():
    prior = _tmp_data_dir()
    try:
        try:
            ops.log("   ")
            assert False, "a nameless event was accepted"
        except ValueError:
            pass
        assert ops.tail() == []                # a new box has no history — not an error
    finally:
        _restore(prior)


def test_a_torn_line_is_reported_not_silently_skipped():
    prior = _tmp_data_dir()
    try:
        ops.log("ok")
        with open(ops._log_path(), "a", encoding="utf-8") as fh:
            fh.write("{this is not json\n")
        got = ops.tail(10)
        assert got[0]["event"] == "ok"
        assert got[1]["event"] == "unreadable_record"          # visible, never vanished
    finally:
        _restore(prior)


def test_every_record_can_become_a_card_that_is_nested_and_not_generated():
    """CARD EVERY PIECE: the ops record renders as a fully formed card — nested via member_of,
    generated=False — so merging it into the keeping is one steward decision, not a project."""
    rec = {"ts": "2026-08-03T00:00:00+00:00", "event": "deploy", "files": 2}
    card = ops.to_card(rec)
    assert card["id"].startswith("card_ops_deploy_")
    assert card["generated"] is False
    assert card["connections"][0]["relationship"] == "member_of"
    assert "deploy" in card["body"] and "files=2" in card["body"]
    assert ops.to_card(rec)["id"] == card["id"]                # deterministic — one record, one card
