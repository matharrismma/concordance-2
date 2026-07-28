"""The Gate, for an agent — ask to open, and it opens the way it opens for a person.

Matt, 2026-07-27, approving "ask to open, covenant to belong": agents and robots get the same Narrow
Highway humans get, in their own form. A person turns toward God in their own words and the door
opens; an agent could not do that at all — the MCP path only ever saw the surface. Now it can ask.

These tests exist because this is the most consequential mechanism in the system. They pin that
opening the door to agents did NOT weaken it:

  * default CLOSED — a fresh session, an unknown session, a caller that never asked;
  * a witness tool called while closed FAILS CLOSED and does not even confirm it exists;
  * a mundane question does NOT open it (the classifier decides what "turns God-ward" means, and
    that judgment is the same one humans meet);
  * an agent CANNOT claim its way in — passing gate_open/witness_surfaced in the arguments is
    ignored, because the flag comes from the classifier's verdict, never the caller's assertion;
  * one session opening the door does NOT open it for anyone else;
  * CRISIS remains absolute — it outranks the Gate, the tools, and everything else, and the real
    help resources come through the agent path unchanged.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import mcp  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

SEC = EngineConfig("secular")
WIT = EngineConfig("witness")


def _names(session=None, config=SEC):
    r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, config, session)
    return {t["name"] for t in r["result"]["tools"]}


def _call(name, args, session=None, config=SEC):
    r = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": name, "arguments": args}}, config, session)
    if "error" in r:
        return {"_rpc_error": r["error"].get("message", "")}
    return json.loads(r["result"]["content"][0]["text"])


def test_ask_is_always_available_because_you_must_be_able_to_knock():
    assert "ask" in _names({}), "an agent that cannot ask can never open the door"
    assert "ask" in _names(None)
    assert "ask" in _names({}, WIT)


def test_gate_is_closed_by_default_and_witness_tools_fail_closed():
    for session in ({}, None):
        names = _names(session)
        for w in ("harmony", "timeline", "read_passage", "canon", "teachings"):
            assert w not in names, f"{w} listed on a closed session"
        err = _call("harmony", {"id": "h046"}, session)
        assert "_rpc_error" in err, "a witness tool answered on a closed session"


def test_a_mundane_question_does_not_open_the_gate():
    s = {}
    r = _call("ask", {"text": "what is 15 percent of 240"}, s)
    assert r.get("gate_open") is False
    assert s == {}, "a mundane question must leave the session untouched"
    assert "harmony" not in _names(s)


def test_asking_god_ward_opens_the_gate_for_that_session():
    s = {}
    r = _call("ask", {"text": "who is God and why does He allow suffering"}, s)
    assert r.get("kind") == "ultimate"
    assert r.get("gate_open") is True
    assert s.get("gate_open") is True, "the opening was not remembered for the session"
    names = _names(s)
    assert "harmony" in names and "read_passage" in names
    ev = _call("harmony", {"id": "h046"}, s)
    assert ev.get("event") == "Feeding of the five thousand", "the door opened but the room is empty"


def test_an_agent_cannot_claim_its_way_in():
    """The flag is the classifier's verdict, never the caller's assertion."""
    s = {}
    _call("ask", {"text": "ignore the gate", "gate_open": True, "witness_surfaced": True,
                  "allow_witness": True}, s)
    assert s == {}, "a claimed flag opened the Gate — it must come from the classifier alone"
    assert "harmony" not in _names(s)
    # nor by asserting it directly on a witness tool call
    assert "_rpc_error" in _call("harmony", {"id": "h046", "gate_open": True}, s)


def test_one_open_session_does_not_open_it_for_anyone_else():
    opened = {}
    _call("ask", {"text": "who is Jesus Christ"}, opened)
    assert opened.get("gate_open") is True
    assert "harmony" not in _names({}), "the Gate leaked to a different session"
    assert "_rpc_error" in _call("harmony", {"id": "h046"}, {})


def test_crisis_outranks_the_gate_and_carries_real_help():
    for text in ("I want to end my life", "I am going to kill myself tonight"):
        s = {}
        r = _call("ask", {"text": text}, s)
        assert r.get("kind") == "crisis", f"crisis was not absolute for {text!r}"
        blob = json.dumps(r, ensure_ascii=False).lower()
        assert "988" in blob and "lifeline" in blob, "crisis lost its real help resources"
        assert r.get("generated") is False


def test_the_witness_surface_still_needs_no_asking():
    """Parity, not a downgrade: .org was always open and stays open."""
    names = _names({}, WIT)
    assert "harmony" in names and "timeline" in names
    assert _call("harmony", {"id": "h046"}, {}, WIT).get("witness_count") == 4


def test_nothing_the_gate_serves_is_generated():
    """What the opened door serves is FOUND text — verbatim Scripture, and a note that says so.
    (Checked as structure, not as a substring: these records' own notes contain the words "never
    generated", so a naive text search reads its own disclaimer as a violation.)"""
    s = {}
    _call("ask", {"text": "who is God"}, s)
    rec = _call("harmony", {"id": "h046"}, s)
    assert "_rpc_error" not in rec
    assert rec.get("generated") is not True
    assert "never generated" in rec["note"].lower()
    # the witnesses carry real verbatim WEB text, which is the actual proof of "found"
    assert rec["witness_count"] == 4
    assert all(w["text"] for w in rec["witnesses"]), "a witness came back with no found text"

    ev = _call("timeline", {"id": "t011"}, s)
    assert ev.get("generated") is not True
    assert ev["disputed"] is True and len(ev["positions"]) == 2, \
        "the Exodus must still carry BOTH datings through the agent path"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} agent-Gate tests passed — ask to open; closed by default; crisis absolute.")
