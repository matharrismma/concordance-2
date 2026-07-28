"""No agent tool asks for a private key — and none accepts one.

Contract §3: keys "are born on the device… the server holds only public keys and verifies signed
challenges." Until 2026-07-28 three MCP tool SCHEMAS advertised a `private_key` field —
`badges_issue`, `study_export`, `group_contribute` — and passed it through. Advertising it is worse
than merely accepting it: a tool schema is documentation an agent reads and imitates, so the field
taught agents that surrendering their key is the normal way to work here.

The guard is deliberately written over the WHOLE tool list rather than the three known names, so a
tool added later cannot quietly reintroduce the field. That is the difference between fixing three
bugs and closing a class of them.

The actions still succeed unsigned — for a badge, "the evidence, not the signature, is the badge" —
and identity is bound afterward by signing the returned content_hash locally. Runnable with pytest
OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402

from concordance import mcp  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

SEC = EngineConfig("secular")
WIT = EngineConfig("witness")


@pytest.fixture(autouse=True, scope="module")
def _isolate_data_dir():
    """badges/groups write; keep it in a temp dir and restore after (see the leak lesson in
    tests/test_scripture.py and tests/test_mesh_signed_speech.py)."""
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


def _tools(config):
    return mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, config,
                      {"gate_open": True})["result"]["tools"]


def _call(name, args, config=SEC):
    r = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": name, "arguments": args}}, config, {"gate_open": True})
    if "error" in r:
        return {"_rpc_error": r["error"].get("message", "")}
    return json.loads(r["result"]["content"][0]["text"])


def test_no_tool_on_either_surface_advertises_a_private_key():
    """The class-wide guard: not the three we knew about — ANY tool, now or later."""
    for config, label in ((SEC, "secular"), (WIT, "witness")):
        offenders = [t["name"] for t in _tools(config)
                     if "private_key" in json.dumps(t.get("inputSchema") or {})]
        assert offenders == [], (
            f"{label} tools advertise a private_key field: {offenders}. A schema is documentation an "
            f"agent imitates — never ask for a key.")


def test_the_previously_offending_three_now_refuse_a_key():
    for name, args in (("badges_issue", {"seal_hashes": [], "private_key": "AAAA"}),
                       ("study_export", {"key": "k", "private_key": "AAAA"}),
                       ("group_contribute", {"id": "g", "text": "hi", "private_key": "AAAA"})):
        r = _call(name, args)
        assert "does not take a private key" in str(r.get("error", "")), \
            f"{name} did not refuse a private key: {r}"
        assert r.get("sign_locally") is True


def test_the_refusal_tells_the_caller_what_to_do_instead():
    """A refusal that leaves the caller stuck just gets worked around."""
    r = _call("badges_issue", {"seal_hashes": [], "private_key": "AAAA"})
    msg = str(r.get("error", "")).lower()
    assert "content_hash" in msg and "your own machine" in msg
    assert r.get("over") == "content_hash"


def test_the_action_still_succeeds_unsigned():
    """The evidence, not the signature, is the badge — refusing the key must not refuse the work."""
    b = _call("badges_issue", {"seal_hashes": [], "title": "unsigned still stands"})
    assert "_rpc_error" not in b
    assert b.get("signed") is False
    assert b.get("checks") == 0, "no seals were passed, so exactly zero must be claimed"


def test_mesh_write_tools_also_refuse_keys():
    """The mesh paths were ported first; keep them in the same guard so the rule is one rule."""
    for name in ("mesh_post", "mesh_leave_on_door"):
        r = _call(name, {"fp": "x", "target": "y", "text": "t", "nonce": "n",
                         "created_at": 1, "signature": "s", "private_key": "AAAA"})
        assert "private key" in str(r.get("error", "")).lower()


if __name__ == "__main__":
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — no agent tool asks for a key, and none takes one.")
