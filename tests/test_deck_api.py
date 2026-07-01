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


def test_thread_read_list_verify_endpoints():
    _st, p = _ask("photosynthesis in chloroplasts")
    tid = p["thread_id"]
    st, g = dispatch("GET", "/thread", {"id": tid}, None, SEC)
    assert st == 200 and g["thread_id"] == tid
    assert dispatch("GET", "/thread", {"id": "0" * 20}, None, SEC)[0] == 404
    st, lst = dispatch("GET", "/threads", {"limit": "100"}, None, SEC)
    assert st == 200 and any(t["thread_id"] == tid for t in lst["threads"])
    st, v = dispatch("GET", "/thread/verify", {"id": tid}, None, SEC)
    assert st == 200 and v["ok"] is True


def test_thread_search_finds_the_conversation():
    _st, p = _ask("the doctrine of justification by faith alone")
    tid = p["thread_id"]
    for junk in ("weather tomorrow", "how tall is the mountain", "a recipe for sourdough"):
        _ask(junk)
    st, r = dispatch("GET", "/threads/search", {"q": "justification"}, None, SEC)
    assert st == 200 and any(m["thread_id"] == tid for m in r["results"])


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


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} deck-api tests passed — the conversation is one chain; crisis help never varies.")
