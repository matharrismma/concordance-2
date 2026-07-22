"""Recall — we recall what is important, not everything.

The discipline under test: durable artifacts (seals, scripture, word studies) become cards;
ordinary conversation does not. The chain still holds every word — nothing is deleted — but
only what is worth recalling is promoted.
"""
import os
import tempfile

os.environ["CONCORDANCE_THREADS_DIR"] = tempfile.mkdtemp(prefix="nh-recall-threads-")
os.environ["CONCORDANCE_STACKS_DIR"] = tempfile.mkdtemp(prefix="nh-recall-stacks-")

from concordance import recall, threads  # noqa: E402


def _thread():
    tid = threads.new_thread()["thread_id"]
    threads.append(tid, "what does chesed mean in H2617",
                   {"kind": "word_study", "message": "covenant loyalty"})
    threads.append(tid, "read John 3:16", {"kind": "scripture", "message": "For God so loved"})
    threads.append(tid, "is 0.1 + 0.2 = 0.3",
                   {"kind": "verify", "message": "BROKEN",
                    "seal": {"cite_url": "https://narrowhighway.com/s/abc123"}})
    threads.append(tid, "ok thanks, that's helpful", {"kind": "found", "message": "found"})
    return tid


def test_the_important_things_become_cards():
    r = recall.remember(_thread())
    assert r["ok"] and r["count"] >= 3
    assert {"seal", "scripture", "word"} <= {c["kind"] for c in r["kept"]}


def test_a_sealed_receipt_is_recalled():
    seals = [c for c in recall.remember(_thread())["kept"] if c["kind"] == "seal"]
    assert seals and "abc123" in seals[0]["text"]


def test_small_talk_is_not_promoted_to_a_card():
    """'ok thanks, that's helpful' leaves no card — we cannot recall everything."""
    r = recall.remember(_thread())
    assert not any("thanks" in c["text"].lower() for c in r["kept"])


def test_the_chain_still_holds_everything():
    """Nothing is discarded: what is not promoted is still in the record, verbatim."""
    tid = _thread()
    recall.remember(tid)
    said = [e["user"] for e in threads.get(tid)["exchanges"]]
    assert "ok thanks, that's helpful" in said


def test_recalling_twice_adds_nothing():
    tid = _thread()
    first = recall.remember(tid)["count"]
    again = recall.remember(tid)["count"]
    assert first > 0 and again == 0


def test_recalled_reads_back_what_was_stored():
    tid = _thread()
    n = recall.remember(tid)["count"]
    back = recall.recalled(tid)
    assert back["ok"] and back["count"] == n


def test_a_card_lives_once_and_is_referenced():
    """The superposition model: the same verse recalled again is not a second card."""
    tid = _thread()
    recall.remember(tid)
    threads.append(tid, "John 3:16 again", {"kind": "scripture", "message": "again"})
    recall.remember(tid)
    refs = [c for c in recall.recalled(tid)["kept"]
            if c["kind"] == "scripture" and "John 3:16" in c["text"]]
    assert len(refs) == 1


def test_unknown_thread_is_handled():
    assert recall.remember("0" * 32)["ok"] is False


def test_an_empty_conversation_recalls_nothing():
    tid = threads.new_thread()["thread_id"]
    r = recall.remember(tid)
    assert r["ok"] and r["count"] == 0
