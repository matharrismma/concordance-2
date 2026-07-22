"""Distill — the thread's memory is an index, not a summary.

Guards the property that keeps this honest: nothing is ever compressed away. The digest
counts; it does not judge. recall() returns the actual exchanges, verbatim. And no code path
generates a single word.
"""
import os
import tempfile

os.environ["CONCORDANCE_THREADS_DIR"] = tempfile.mkdtemp(prefix="nh-distill-")

from concordance import distill, threads  # noqa: E402  (env must be set first)


def _thread():
    rec = threads.new_thread(surface="secular")
    tid = rec["thread_id"]
    threads.append(tid, "what does chesed mean in H2617",
                   {"kind": "word_study", "message": "covenant loyalty", "generated": False})
    threads.append(tid, "is 0.1 + 0.2 = 0.3",
                   {"kind": "verify", "message": "BROKEN",
                    "seal": {"cite_url": "https://narrowhighway.com/s/abc123"}, "generated": False})
    threads.append(tid, "read John 3:16 about love",
                   {"kind": "scripture", "message": "For God so loved", "generated": False})
    threads.append(tid, "tell me more about love and covenant",
                   {"kind": "search", "message": "found", "generated": False})
    return tid


# --- the digest counts, it does not judge ----------------------------------------------------

def test_digest_counts_the_thread():
    d = distill.digest(_thread())
    assert d["ok"] and d["exchanges"] == 4
    assert d["kinds"] == {"scripture": 1, "search": 1, "verify": 1, "word_study": 1}


def test_digest_collects_seals():
    d = distill.digest(_thread())
    assert len(d["sealed"]) == 1
    assert d["sealed"][0]["seal"].endswith("abc123")


def test_digest_finds_scripture_and_strongs():
    d = distill.digest(_thread())
    assert any(r.startswith("John 3:16") for r, _n in d["scripture_refs"])
    assert ("H2617", 1) in d["strongs"]


def test_digest_surfaces_recurring_terms():
    d = distill.digest(_thread())
    terms = dict(d["recurring_terms"])
    assert terms.get("love") == 2          # counted across two exchanges, not summarised


def test_generated_count_is_zero_because_nothing_generates():
    """The honesty metric: this engine authors nothing, so this must stay 0."""
    assert distill.digest(_thread())["generated"] == 0


def test_chain_linkage_is_checked():
    assert distill.digest(_thread())["chain_ok"] is True


def test_digest_is_deterministic():
    tid = _thread()
    first = distill.digest(tid)
    for _ in range(4):
        assert distill.digest(tid) == first


def test_unknown_thread_is_handled():
    assert distill.digest("0" * 32)["ok"] is False
    assert distill.recall("0" * 32, "x")["ok"] is False


# --- recall returns the exchanges themselves -------------------------------------------------

def test_recall_returns_verbatim_exchanges_not_a_summary():
    tid = _thread()
    r = distill.recall(tid, "covenant")
    assert r["ok"] and r["matches"]
    top = r["matches"][0]
    original = threads.get(tid)["exchanges"][top["seq"]]["user"]
    assert top["user"] == original          # verbatim: the note, not a retelling


def test_recall_explains_why_each_matched():
    r = distill.recall(_thread(), "love covenant")
    assert all(m["matched"] for m in r["matches"])


def test_recall_ranks_more_distinct_terms_first():
    r = distill.recall(_thread(), "love covenant")
    assert len(r["matches"][0]["matched"]) >= len(r["matches"][-1]["matched"])


def test_recall_is_deterministic():
    tid = _thread()
    first = distill.recall(tid, "love")
    for _ in range(4):
        assert distill.recall(tid, "love") == first


def test_recall_with_no_searchable_terms():
    r = distill.recall(_thread(), "the and of")
    assert r["ok"] and r["matches"] == []


def test_nothing_is_lost_the_chain_is_still_the_truth():
    """The digest is a finding aid; every exchange remains intact and readable."""
    tid = _thread()
    d = distill.digest(tid)
    rec = threads.get(tid)
    assert d["exchanges"] == len(rec["exchanges"])
    assert d["head_hash"] == rec["head_hash"]
