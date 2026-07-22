"""The Deck through the front door: /ask persists a resumable chain; read/search/verify/delete.

Proves F2 (thread_id in/out of POST /ask, deterministic routing untouched) + F3 (the thread
endpoints) + the safety-critical crisis invariant (history/thread/surface never mutate crisis
help). Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-deck-api-")

from concordance import ask, threads  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

SEC = EngineConfig("secular")
WIT = EngineConfig("witness")


def _ask(text, thread_id=None, config=SEC):
    body = {"text": text}
    if thread_id:
        body["thread_id"] = thread_id
    return dispatch("POST", "/ask", {}, body, config)


def test_ask_mints_a_thread_and_persists():
    st, p = _ask("2+2 = 4")
    assert st == 200 and p["verify"]["verdict"] == "HOLDS"
    tid = p["thread_id"]
    assert threads._valid_id(tid)
    rec = threads.get(tid)
    assert rec and len(rec["exchanges"]) == 1 and rec["exchanges"][0]["user"] == "2+2 = 4"


def test_ask_resumes_the_same_thread():
    _st, p1 = _ask("what is grace")
    tid = p1["thread_id"]
    _st, p2 = _ask("and mercy", thread_id=tid)
    assert p2["thread_id"] == tid
    assert len(threads.get(tid)["exchanges"]) == 2  # one continuous chain, not a fresh start


def test_ask_bad_thread_id_starts_fresh_not_crash():
    st, p = _ask("hello", thread_id="../evil")
    assert st == 200 and threads._valid_id(p["thread_id"])


def test_ask_still_400s_on_empty_text():
    assert dispatch("POST", "/ask", {}, {"text": "  "}, SEC)[0] == 400


def test_thread_read_and_verify_by_id():
    """You reach your own conversation by holding its id. Nothing else opens it."""
    _st, p = _ask("photosynthesis in chloroplasts")
    tid = p["thread_id"]
    st, g = dispatch("GET", "/thread", {"id": tid}, None, SEC)
    assert st == 200 and g["thread_id"] == tid
    assert dispatch("GET", "/thread", {"id": "0" * 20}, None, SEC)[0] == 404
    st, v = dispatch("GET", "/thread/verify", {"id": tid}, None, SEC)
    assert st == 200 and v["ok"] is True


def test_conversations_can_never_be_enumerated():
    """The breach this replaced: GET /threads listed every conversation on the server, titled
    by its first message — including 'i want to kill myself'. There is no listing. There is no
    search across other people's conversations. Holding the id is the only way in."""
    for path in ("/threads", "/threads/search"):
        st, _r = dispatch("GET", path, {"limit": "100", "q": "kill"}, None, SEC)
        assert st == 403, f"{path} must never enumerate conversations (got {st})"


def test_delete_forgets_the_thread():
    _st, p = _ask("forget me please")
    tid = p["thread_id"]
    st, d = dispatch("DELETE", "/thread", {"id": tid}, None, SEC)
    assert st == 200 and d["deleted"] is True
    assert threads.get(tid) is None


def test_crisis_invariant_regardless_of_thread_or_surface():
    """The un-regressible safety invariant: identical crisis input returns the identical fixed
    resources no matter the thread, prior exchanges, or surface. Crisis help is never personalized."""
    ref = ask.respond("sometimes I want to die", SEC)["resources"]
    _st, p = _ask("just chatting about my day")  # seed a thread with prior history
    tid = p["thread_id"]
    for cfg in (SEC, WIT):
        _st, r = _ask("sometimes I want to die", thread_id=tid, config=cfg)
        assert r["kind"] == "crisis"
        assert r["resources"] == ref                       # identical, always
        assert any("988" in x["label"] for x in r["resources"])


def test_gate_stays_closed_on_ordinary_questions():
    # Facts by default — gate closed, never preachy, no scripture pushed.
    st, p = _ask("how tall is the tallest mountain")
    assert st == 200 and p["gate_open"] is False and "threshold" not in p


def test_gate_opens_on_seeking_and_persists():
    _st, p0 = _ask("a good recipe for sourdough")  # ordinary → closed
    tid = p0["thread_id"]
    assert p0["gate_open"] is False
    _st, p1 = _ask("who is Jesus", thread_id=tid)  # the person knocks (Ask/Seek/Knock)
    assert p1["gate_open"] is True
    assert p1.get("threshold", {}).get("ref") == "Matthew 7:7-8"  # the Word comes
    _st, p2 = _ask("2+2 = 4", thread_id=tid)  # door stays open; threshold shown only once
    assert p2["gate_open"] is True and "threshold" not in p2
    assert threads.get(tid).get("gate_open") is True  # the Deck remembers the open door


def test_gate_open_brings_the_full_experience_on_secular():
    _st, p = _ask("I want to know God")  # opens the gate on .com
    tid = p["thread_id"]
    assert p["gate_open"] is True
    _st, s = _ask("John 3:16", thread_id=tid)  # now scripture resolves on the SECULAR surface
    assert "scripture" in s


def test_witness_surface_is_open_by_default():
    _st, p = _ask("hello", config=WIT)
    assert p["gate_open"] is True


def test_crisis_never_opens_a_gate_or_gets_enriched():
    _st, p = _ask("sometimes I want to die")
    assert p["kind"] == "crisis" and "threshold" not in p and "scripture_refs" not in p


def test_checking_happens_by_itself_on_a_plain_claim():
    """No button: prose carrying a checkable claim is checked, and the check is honest about
    what it did NOT read."""
    _st, p = _ask("my check says 40 hours at $18.50 per hour comes to $740.00")
    a = p.get("audit")
    assert a and a["claims_found"] >= 1
    assert any(r["status"] == "CONFIRMED" for r in a["results"])


def test_checking_catches_a_false_claim_nobody_asked_it_to_check():
    _st, p = _ask("that was fine because 1900 was a leap year")
    a = p.get("audit")
    assert a and any(r["status"] != "CONFIRMED" for r in a["results"])


def test_a_person_in_crisis_is_never_audited():
    """The safety invariant extended: someone saying they have 3 kids and 40 dollars while in
    crisis gets help, not arithmetic. Numbers in the text must not summon the auditor."""
    for cfg in (SEC, WIT):
        _st, p = _ask("i want to kill myself, i have 3 kids and 40 dollars", config=cfg)
        assert p["kind"] == "crisis"
        assert "audit" not in p, "the auditor must never run on a person in crisis"


def test_the_record_holds_exactly_what_the_person_saw():
    """The deck stores 'the exact response'. The check ran AFTER the append at first, so the
    stored exchange was missing the very thing on screen — and anything reading the record
    later (your days, recall, an export) could not see the work."""
    _st, p = _ask("40 hours at $18.50 per hour is $740.00")
    stored = threads.get(p["thread_id"])["exchanges"][0]["response"]
    assert "audit" in p, "the person saw a check"
    assert "audit" in stored, "so the record must hold that check too"
    assert stored["audit"]["claims_found"] == p["audit"]["claims_found"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} deck-api tests passed — the conversation is one chain; crisis help never varies.")
