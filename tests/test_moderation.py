"""The moderation floor — one report is a claim, three hold for a human, blocking is a boundary.

Contract §6 item 4. The floor reuses the house's own witness doctrine (Deut 19:15) instead of
inventing a court: no counter ever judges; it only decides when a human steward must look.

Pinned here:
  * one report hides nothing; the SAME reporter repeating is still one witness;
  * three DISTINCT reporters hold the item for review — quarantined, not deleted, not judged;
  * a steward's restore beats the counter; a steward's remove holds until changed; every
    resolution carries the steward's name — no anonymous judgement;
  * block is viewer-side and sovereign: it filters what YOU see, needs no threshold, and a
    public read with no viewer filters NOTHING (your boundary is not the world's verdict);
  * the review queue shows exactly what waits on a human.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True, scope="module")
def _isolate_data_dir():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


def test_one_report_is_a_claim_and_hides_nothing():
    from concordance import moderation as m
    r = m.report("group_contribution", "c-1", "spam", "alice")
    assert r["ok"] is True and r["reporters"] == 1 and r["held_for_review"] is False
    assert m.held("group_contribution", "c-1") is False


def test_the_same_reporter_repeating_is_one_witness():
    from concordance import moderation as m
    for _ in range(5):
        m.report("group_contribution", "c-2", "spam", "bob")
    st = m.status("group_contribution", "c-2")
    assert st["reporters"] == 1 and st["held_for_review"] is False, \
        "a voice cannot become three witnesses by shouting"


def test_three_distinct_reporters_hold_for_a_human_not_a_verdict():
    from concordance import moderation as m
    for who in ("alice", "bob", "carol"):
        m.report("mesh_message", "msg-9", "harmful", who)
    st = m.status("mesh_message", "msg-9")
    assert st["held_for_review"] is True and st["steward_action"] is None
    assert m.held("mesh_message", "msg-9") is True
    q = m.review_queue()
    assert any(i["target_id"] == "msg-9" for i in q["held"]), "the steward's inbox must show it"


def test_a_steward_restore_beats_the_counter_and_remove_holds():
    from concordance import moderation as m
    for who in ("a", "b", "c"):
        m.report("door_note", "note-1", "other", who)
    assert m.held("door_note", "note-1") is True
    anon = m.resolve("door_note", "note-1", "restore", "")
    assert anon["ok"] is False, "no anonymous judgement"
    m.resolve("door_note", "note-1", "restore", "matt", "reviewed; stands")
    assert m.held("door_note", "note-1") is False, "a human's restore beats the counter"
    m.resolve("door_note", "note-1", "remove", "matt", "on reflection")
    assert m.held("door_note", "note-1") is True, "a human's remove holds until changed"


def test_bad_report_shapes_are_refused():
    from concordance import moderation as m
    assert m.report("nonsense_kind", "x", "spam", "a")["ok"] is False
    assert m.report("mesh_message", "", "spam", "a")["ok"] is False
    assert m.report("mesh_message", "x", "spam", "")["ok"] is False


def test_block_is_a_viewers_own_boundary():
    from concordance import moderation as m
    items = [{"handle": "kind-friend", "text": "hello"},
             {"handle": "loud-stranger", "text": "noise"}]
    m.block("me", "loud-stranger")
    assert [i["handle"] for i in m.filter_for("me", items)] == ["kind-friend"]
    # a public read with NO viewer filters nothing — my boundary is not the world's verdict
    assert len(m.filter_for(None, items)) == 2
    # another viewer sees everything
    assert len(m.filter_for("someone-else", items)) == 2
    m.unblock("me", "loud-stranger")
    assert len(m.filter_for("me", items)) == 2


if __name__ == "__main__":
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the counter never judges; it calls a human.")
