"""The Book of Days — written by you, indexed by us, owned by you.

Guards the four promises literally: readable, correctable, exportable, and genuinely
deletable — plus the one that matters most, that nothing is inferred about you beyond what is
already countable in your own chain.
"""
import json
import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="nh-book-")
os.environ["CONCORDANCE_BOOK_DIR"] = _TMP
os.environ["CONCORDANCE_THREADS_DIR"] = tempfile.mkdtemp(prefix="nh-book-threads-")

from concordance import bookofdays as book, threads  # noqa: E402

OWNER = "nh_testowner0001"


# --- written by you, stored verbatim ---------------------------------------------------------

def test_a_note_is_stored_verbatim():
    said = "  Mom's surgery is the 14th. Call Dad Thursday.  "
    e = book.write(OWNER, said)["entry"]
    assert e["text"] == said              # not stripped, not tidied, not "improved"
    assert e["kind"] == "note"


def test_empty_notes_are_refused():
    assert book.write(OWNER, "   ")["ok"] is False
    assert book.write(OWNER, None)["ok"] is False


# --- correctable: a correction is a record, not an erasure -----------------------------------

def test_amend_keeps_the_prior_text_visible():
    e = book.write(OWNER, "the meeting is Tuesday")["entry"]
    r = book.amend(OWNER, e["id"], "the meeting is Wednesday")
    assert r["ok"]
    assert r["entry"]["text"] == "the meeting is Wednesday"
    assert r["entry"]["history"][0]["text"] == "the meeting is Tuesday"


def test_amend_unknown_entry_is_refused():
    assert book.amend(OWNER, "nope", "x")["ok"] is False


# --- deletable: really deleted -----------------------------------------------------------------

def test_forget_is_a_hard_delete_not_a_tombstone():
    secret = "a sentence that must vanish completely 8f3a1c"
    e = book.write(OWNER, secret)["entry"]
    assert book.forget(OWNER, e["id"])["ok"] is True
    # gone from the API...
    ids = [x["id"] for x in book.entries(OWNER)["entries"]]
    assert e["id"] not in ids
    # ...and gone from the file on disk, text and all
    blob = open(os.path.join(_TMP, f"{OWNER}.json"), encoding="utf-8").read()
    assert secret not in blob


def test_forget_removes_corrections_too():
    e = book.write(OWNER, "original wording 5b2")["entry"]
    book.amend(OWNER, e["id"], "corrected wording 9d4")
    book.forget(OWNER, e["id"])
    blob = open(os.path.join(_TMP, f"{OWNER}.json"), encoding="utf-8").read()
    assert "original wording 5b2" not in blob and "corrected wording 9d4" not in blob


def test_forget_unknown_entry_is_refused():
    assert book.forget(OWNER, "nope")["ok"] is False


# --- derived entries: labelled, sourced, deletable, never inferred ---------------------------

def _thread_with_material():
    rec = threads.new_thread()
    tid = rec["thread_id"]
    threads.append(tid, "read John 3:16 and H2617",
                   {"kind": "scripture", "message": "For God so loved",
                    "seal": {"cite_url": "https://narrowhighway.com/s/abc"}})
    threads.append(tid, "John 3:16 again", {"kind": "scripture", "message": "again"})
    return tid


def test_derived_entries_are_labelled_and_sourced():
    owner = "nh_derive0001"
    tid = _thread_with_material()
    r = book.derive(owner, tid)
    assert r["ok"] and r["count"] > 0
    for e in r["added"]:
        assert e["kind"] == "derived"
        assert e["derived_from"]["thread_id"] == tid
        assert e["derived_from"]["fact"]          # exactly what produced it, visible

def test_derived_entries_only_contain_countable_material():
    """Nothing is invented: every derived entry names a ref/strongs/seal from the digest."""
    owner = "nh_derive0002"
    tid = _thread_with_material()
    from concordance import distill
    d = distill.digest(tid)
    known = {r for r, _ in d["scripture_refs"]} | {s for s, _ in d["strongs"]}
    known |= {str(s["seal"]) for s in d["sealed"]}
    for e in book.derive(owner, tid)["added"]:
        assert any(k in e["text"] for k in known), e["text"]


def test_derived_entries_are_deletable_like_any_other():
    owner = "nh_derive0003"
    tid = _thread_with_material()
    e = book.derive(owner, tid)["added"][0]
    assert book.forget(owner, e["id"])["ok"] is True


def test_derive_does_not_duplicate():
    owner = "nh_derive0004"
    tid = _thread_with_material()
    first = book.derive(owner, tid)["count"]
    again = book.derive(owner, tid)["count"]
    assert first > 0 and again == 0


def test_derive_unknown_thread_is_handled():
    assert book.derive("nh_x", "0" * 32)["ok"] is False


# --- readable + exportable --------------------------------------------------------------------

def test_export_returns_everything_and_is_plain_json():
    owner = "nh_export0001"
    book.write(owner, "one")
    book.write(owner, "two")
    x = book.export(owner)
    assert x["ok"] and len(x["entries"]) == 2
    json.dumps(x)                                   # plain, serialisable, no encoding games


def test_a_fresh_book_is_empty_not_an_error():
    r = book.entries("nh_nobody0001")
    assert r["ok"] and r["count"] == 0


# --- ownership is per-key ----------------------------------------------------------------------

def test_books_are_separate_per_owner():
    book.write("nh_ownerA", "mine only")
    assert book.entries("nh_ownerB")["count"] == 0
