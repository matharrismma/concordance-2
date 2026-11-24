"""A mounted MCP door receives an agent AT THAT DOOR, and says in the protocol's own field what it reads.

2026-11-23, Matt: "Publish" — opening https://narrowhighway.org/mcp/witness to other bots and agents. Probed live
before publishing it, the door had two faults an outside agent meets on its first two calls:

  1. initialize handed every mounted door the whole house's welcome — "START with ask(text) … verify(claim)" —
     and neither tool is on the witness plane, so the first call an agent made as told was refused.
  2. its tools carried our `effect: "read"` and no `annotations.readOnlyHint`, the field an MCP client actually
     reads, so a client presented every call on the read-only door as one that might write.

Pinned here: each mounted door names itself and starts the agent on tools it serves; following that start is
never refused; the unmounted welcome is byte-identical to before; readOnlyHint is true exactly where the
declared effect is `read` (never wider), and on /mcp/witness that is every tool.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import doors  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.mcp import handle  # noqa: E402
from concordance.mcp.server import PROFILES  # noqa: E402

FACES = ("secular", "witness")
MOUNTS = [p for p in PROFILES if p != "community"]   # community is OFF on a hosted box (resolve_mcp_profile)


def _init(face, profile):
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"}}, EngineConfig(face), profile=profile)
    return r["result"]["instructions"]


def _listed(face, profile):
    r = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, EngineConfig(face), profile=profile)
    return r["result"]["tools"]


def _start_tools(welcome):
    m = re.search(r"START on this door with ([a-z_ ·]+)\.", welcome)
    assert m, "a mounted welcome must say where to start on this door"
    return [t.strip() for t in m.group(1).split("·")]


def test_the_unmounted_welcome_is_unchanged():
    for face in FACES:
        assert _init(face, None) == doors.welcome(face)
        assert "THIS DOOR" not in doors.welcome(face)
        assert "START with ask(text) for anything" in doors.welcome(face)


def test_a_mounted_door_names_itself_and_starts_the_agent_on_its_own_tools():
    for face in FACES:
        for p in MOUNTS:
            w = _init(face, p)
            assert f"THIS DOOR — /mcp/{p}," in w, (face, p)
            assert w == doors.welcome(face, p)
            names = {t["name"] for t in _listed(face, p)} | set(PROFILES[p]["tools"])
            starts = _start_tools(w)
            assert starts and all(t in PROFILES[p]["tools"] for t in starts), (face, p, starts)
            assert "START with ask(text) for anything" not in w, (face, p)   # the house's start, replaced
            if "ask" not in names:
                assert "ask(text) is on the whole house, /mcp" in w or "ask(text) and verify(claim) are on" in w
            assert len(w) < 3400, (face, p, len(w))                           # still read every session


def test_following_the_start_on_the_witness_door_is_never_refused():
    """The first call an agent makes as told must reach the tool. Data may be absent in a worktree, so this pins
    the BOUNDARY (no JSON-RPC refusal), not the passage text — the live probe pins the text."""
    for face in FACES:
        w = _init(face, "witness")
        assert _start_tools(w)[0] == "read_passage"
        r = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "read_passage", "arguments": {"ref": "John 15:1-3"}}},
                   EngineConfig(face), profile="witness")
        assert "error" not in r, r
        # and the house's start, called here, is refused WITH where it lives — as the welcome says
        r = handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                    "params": {"name": "ask", "arguments": {"text": "hello"}}},
                   EngineConfig(face), profile="witness")
        assert "it lives on /mcp/library" in r["error"]["message"]


def test_read_only_hint_is_the_declared_effect_and_never_wider():
    for face in FACES:
        for p in MOUNTS:
            for t in _listed(face, p):
                assert t["annotations"]["readOnlyHint"] is (t["effect"] == "read"), (face, p, t["name"])
    wit = _listed("witness", "witness")
    assert len(wit) == len(PROFILES["witness"]["tools"])
    assert all(t["annotations"]["readOnlyHint"] is True for t in wit)          # the published door: all read
    core = {t["name"]: t["annotations"]["readOnlyHint"] for t in _listed("secular", "core")}
    assert core["verify"] is False and core["seal_fetch"] is True              # verify seals; it is not read-only


if __name__ == "__main__":
    for k, v in sorted(globals().items()):
        if k.startswith("test_") and callable(v):
            v(); print("  ok ", k)
