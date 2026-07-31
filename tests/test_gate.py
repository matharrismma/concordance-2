"""The Gate — witness content opens by CONVERSATION, not by domain.

Proves: on the secular reach a witness endpoint is closed by default (404, marked gate=closed
so a client can invite rather than dead-end); once the session gate is open (the person's own
seeking, carried via session_gate_open) the SAME endpoint unlocks in place — no domain change;
on the witness face it is always open. The gate check precedes any data import, so these are
hermetic. Runs under pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-gate-")

from concordance.web import api
from concordance.web.api import dispatch  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

SEC = EngineConfig("secular")
WIT = EngineConfig("witness")

# every witness path shares the same gate; the check runs before any data import (hermetic)
# The Gate holds the DEEPER READING, never the text. Matt, 2026-07-31: "seeing them is fine —
# understanding the deeper meaning comes after the gate" and "we don't need to refuse use, we
# refuse abuse". This list used to hold the passage, the dictionary, the canon and the original
# tongues too; those are seeing, and refusing them refused use. The set is the one in the code,
# so this test cannot drift from it.
WITNESS_PATHS = tuple(sorted(api.AFTER_THE_GATE))
SEEING_PATHS = ("/passage", "/character", "/characters", "/canon", "/original", "/word_study",
                "/resolve", "/cross_refs", "/tsk")


def test_secular_witness_closed_by_default_and_marked():
    for p in WITNESS_PATHS:
        st, body = dispatch("GET", p, {"ref": "John 3:16", "strongs": "G26", "name": "Moses"}, None, SEC)
        assert st == 404, p
        assert body.get("gate") == "closed", (p, body)   # marked, so a client invites (not a dead end)


def test_the_text_itself_is_never_behind_the_gate():
    """The other half of the same doctrine, and the half that was wrong until 2026-07-31: a
    reader who asks for a verse, a name, or a lexical entry is USING the library."""
    refused = [p for p in SEEING_PATHS
               if dispatch("GET", p, {"ref": "John 3:16", "strongs": "G26", "name": "Moses"},
                           None, SEC)[1].get("gate") == "closed"]
    assert not refused, f"these refuse use: {refused}"


def test_secular_witness_unlocks_when_session_gate_open():
    # /canon is pure (no external data) — proves the unlock in place, on the secular reach
    st, body = dispatch("GET", "/canon", {}, None, SEC, session_gate_open=True)
    assert st == 200 and "traditions" in body
    assert body.get("gate") != "closed"


def test_witness_face_always_open():
    st, body = dispatch("GET", "/canon", {}, None, WIT)
    assert st == 200 and "traditions" in body


def test_ask_opens_gate_on_seeking_and_reports_it():
    # a God-ward message opens the door; the response reports gate_open so the server can set the cookie
    st, body = dispatch("POST", "/ask", {}, {"text": "What does the Bible say about grace?"}, SEC)
    assert st == 200 and body.get("gate_open") is True
    # a neutral message does NOT open it on the secular reach
    st2, body2 = dispatch("POST", "/ask", {}, {"text": "2 + 2 = 4"}, SEC)
    assert st2 == 200 and body2.get("gate_open") is False


def test_ask_gate_sticky_via_session():
    # once the session carries the open gate, even a neutral message stays open (the door, once opened, stays)
    st, body = dispatch("POST", "/ask", {}, {"text": "2 + 2 = 4"}, SEC, session_gate_open=True)
    assert st == 200 and body.get("gate_open") is True


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} gate tests passed — the Word opens by seeking, in place, never by domain.")
