"""Threads — the Deck: a conversation as a resumable, tamper-evident chain of exchanges.

Proves the deck store: valid ids, the per-thread hash chain, tamper detection, client-held-id
auto-create, path-traversal rejection, list/delete, and that past exchanges are searchable with
the same corpus ranker. Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-threads-")  # isolate the store

from concordance import threads, validate  # noqa: E402


def _resp(kind: str = "found", **extra):
    d = {"kind": kind, "note": "this finds and verifies; it does not generate the answer"}
    d.update(extra)
    return d


def test_new_thread_persists_and_has_valid_id():
    rec = threads.new_thread("secular")
    assert threads._valid_id(rec["thread_id"])
    assert threads.get(rec["thread_id"]) is not None
    assert rec["exchanges"] == [] and rec["head_hash"] == ""


def test_append_builds_a_hash_chain():
    tid = threads.new_thread("witness")["thread_id"]
    e0 = threads.append(tid, "what is grace", _resp())
    e1 = threads.append(tid, "and mercy", _resp())
    assert e0["prev_hash"] == "" and e0["seq"] == 0
    assert e1["prev_hash"] == e0["hash"] and e1["seq"] == 1  # the chain links
    rec = threads.get(tid)
    assert rec["head_hash"] == e1["hash"]
    assert rec["title"] == "what is grace"  # title derived from the first user text
    assert len(rec["exchanges"]) == 2


def test_notes_are_verbatim_and_not_generated():
    tid = threads.new_thread("secular")["thread_id"]
    r = _resp("verify", verify={"verdict": "HOLDS", "seal": {"content_hash": "abc"}})
    ex = threads.append(tid, "2+2 = 4", r)
    assert ex["user"] == "2+2 = 4"                 # verbatim
    assert ex["response"]["verify"]["verdict"] == "HOLDS"  # exact response kept
    assert ex["generated"] is False                # conduit, flagged as such


def test_verify_thread_detects_tampering():
    tid = threads.new_thread("secular")["thread_id"]
    threads.append(tid, "2+2 = 4", _resp("verify"))
    threads.append(tid, "John 3:16", _resp("scripture"))
    ok, msg = threads.verify_thread(tid)
    assert ok, msg
    rec = threads.get(tid)
    rec["exchanges"][0]["user"] = "2+2 = 5"  # rewrite a kept note without recomputing its hash
    threads._path(threads._threads_dir(), tid).write_bytes(validate.canonical_json_bytes(rec))
    ok2, _ = threads.verify_thread(tid)
    assert not ok2  # the chain catches the edit — the conversation hands its own receipt


def test_append_autocreates_client_held_id():
    tid = "deadbeefcafe1234"  # a valid browser-held id this box has never seen
    ex = threads.append(tid, "hello", _resp(), surface="secular")
    assert threads.get(tid) is not None and ex["seq"] == 0


def test_invalid_id_is_rejected_before_touching_disk():
    for bad in ("../etc/passwd", "..\\win", "", "nothex!!"):
        try:
            threads.append(bad, "x", _resp())
            assert False, f"should reject {bad!r}"
        except ValueError:
            pass
    assert threads.get("../etc/passwd") is None


def test_list_and_delete():
    tid = threads.new_thread("secular", title="deck A")["thread_id"]
    assert tid in [t["thread_id"] for t in threads.list_threads(limit=1000)]
    assert threads.delete(tid) is True
    assert threads.get(tid) is None


def test_past_exchanges_are_searchable():
    from concordance.corpus import Corpus
    tid = threads.new_thread("secular")["thread_id"]
    # A term no other test file writes. Both this file and test_deck_api set CONCORDANCE_DATA_DIR
    # at import, so under one pytest process the first import wins and they share a store — two
    # threads saying "photosynthesis" made hits[0] a coin flip. The ranking assertion stays strict.
    threads.append(tid, "thylakoid stacking in the chloroplast", _resp())
    for junk in ("grace and mercy", "justice and law", "wind and rain", "bread and wine", "time and tide"):
        threads.append(threads.new_thread("secular")["thread_id"], junk, _resp())
    cards = threads.all_cards()
    assert any(c["kind"] == "exchange" for c in cards.values())
    hits = Corpus(cards, min_idf=0.5).search("thylakoid", limit=5)  # same ranker as the keeping
    assert hits and hits[0]["thread_id"] == tid


def test_search_works_from_the_first_conversation():
    # A personal deck is small — search must find your very first thread (the IDF ranker cannot).
    tid = threads.new_thread("secular")["thread_id"]
    threads.append(tid, "notes on the epistle to the Romans", _resp())
    res = threads.search("Romans", limit=5)
    assert res and res[0]["thread_id"] == tid
    assert threads.search("", limit=5) == []  # empty query finds nothing


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} thread tests passed — the deck is a resumable, tamper-evident chain.")
