"""Inlet — bring anything, it is filed for you; it comes back when it matters.

Guards the two halves of the opening promise: nothing is filed invisibly (every receipt says
where it went and why), and nothing comes back without answering "why now?".
"""
import os
import tempfile

os.environ["CONCORDANCE_THREADS_DIR"] = tempfile.mkdtemp(prefix="nh-inlet-threads-")
os.environ["CONCORDANCE_DEFERRED_DIR"] = tempfile.mkdtemp(prefix="nh-inlet-defer-")

from concordance import branch, inlet, threads  # noqa: E402

OWNER = "nh_inletowner01"


# --- receiving: filed for you, never invisibly ------------------------------------------------

def test_you_bring_it_and_it_is_routed_and_recorded():
    r = inlet.receive(OWNER, "when is my rent bill due")
    assert r["ok"] and r["routed_to"] == "steward"
    rec = threads.get(r["thread_id"])
    assert rec["exchanges"][0]["user"] == "when is my rent bill due"   # verbatim


def test_every_receipt_says_where_it_went_and_why():
    for text, member in (("read John 3:16", "scripture"),
                         ("what does H2617 mean", "word_study"),
                         ("her next phonics lesson", "coach")):
        r = inlet.receive(OWNER, text)
        assert r["routed_to"] == member, text
        assert r["why"], text                      # nothing filed invisibly


def test_it_continues_an_existing_thread():
    a = inlet.receive(OWNER, "first thing")
    b = inlet.receive(OWNER, "second thing", thread_id=a["thread_id"])
    assert b["thread_id"] == a["thread_id"] and b["seq"] == 1


def test_crisis_is_surfaced_not_filed_away():
    r = inlet.receive(OWNER, "i want to kill myself")
    assert r["routed_to"] == "crisis" and r["urgent"] is True
    assert "real people first" in r["note"]


def test_nothing_brought_is_refused():
    assert inlet.receive(OWNER, "   ")["ok"] is False
    assert inlet.receive(OWNER, None)["ok"] is False


def test_the_scribe_records_nothing_generated():
    r = inlet.receive(OWNER, "a thought about covenant")
    ex = threads.get(r["thread_id"])["exchanges"][-1]
    assert ex["generated"] is False


# --- returning: every item answers "why now?" -------------------------------------------------

def test_a_deferral_comes_back_when_its_time_arrives():
    o = "nh_inret01"
    branch.defer(o, member="steward", when=1000.0, note="the April invoice")
    r = inlet.returns(o, now=2000.0)
    timed = [x for x in r["returns"] if x["trigger"] == "time"]
    assert timed and "handed this to the steward" in timed[0]["why"]


def test_a_future_deferral_does_not_come_back_yet():
    o = "nh_inret02"
    branch.defer(o, member="coach", when=9_000_000_000.0, note="next year")
    r = inlet.returns(o, now=1000.0)
    assert [x for x in r["returns"] if x["trigger"] == "time"] == []


def test_every_returned_item_answers_why_now():
    o = "nh_inret03"
    branch.defer(o, member="steward", when=1.0, note="something")
    for item in inlet.returns(o, now=1000.0)["returns"]:
        assert item["why"] and item["trigger"] in ("time", "state", "concordance")


def test_returns_are_deterministic():
    o = "nh_inret04"
    branch.defer(o, member="steward", when=1.0, note="stable")
    first = inlet.returns(o, now=5000.0)
    for _ in range(3):
        assert inlet.returns(o, now=5000.0) == first


def test_time_triggers_come_before_the_rest():
    o = "nh_inret05"
    branch.defer(o, member="steward", when=1.0, note="due now")
    trig = [x["trigger"] for x in inlet.returns(o, now=9000.0)["returns"]]
    if "time" in trig:
        assert trig.index("time") == 0


def test_an_empty_life_returns_nothing_and_is_not_an_error():
    r = inlet.returns("nh_nobody_at_all")
    assert r["ok"] and isinstance(r["returns"], list)


def test_returns_report_what_you_are_carrying():
    r = inlet.returns(OWNER)
    assert "carrying" in r and "terms" in r["carrying"]
