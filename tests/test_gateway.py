"""Gateway — the embeddable privacy primitive: scrub-in, restore-out, at the caller's edge.

Proves scrub/restore round-trips, that guard(fn) hides PII from the wrapped call yet returns
the caller a restored result, and that the MCP `redact` tool works + is listed. Runnable with
pytest OR directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import gateway  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.mcp.server import handle  # noqa: E402

SEC = EngineConfig("secular")


def test_scrub_restore_roundtrips():
    clean, m = gateway.scrub("email a@b.com")
    assert "a@b.com" not in clean and "[EMAIL_1]" in clean
    assert gateway.restore(clean, m) == "email a@b.com"


def test_guard_hides_pii_from_the_wrapped_call():
    seen = {}

    def fake_llm(text):
        seen["text"] = text                       # what the external call actually received
        return "noted; replying to " + text.split()[-1]

    ask = gateway.guard(fake_llm)
    out = ask("reply to a@b.com")
    assert "a@b.com" not in seen["text"] and "[EMAIL_1]" in seen["text"]  # the fn never saw it
    assert "a@b.com" in out                                               # caller gets it back


def test_guard_passes_through_non_string_output():
    ask = gateway.guard(lambda t: {"echo": t})
    assert ask("x")["echo"] == "x"


def test_mcp_redact_tool():
    resp = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
        "name": "redact", "arguments": {"text": "ssn 123-45-6789 and a@b.com"}}}, SEC)
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert "[SSN_1]" in payload["clean"] and "[EMAIL_1]" in payload["clean"]
    assert payload["count"] == 2 and "123-45-6789" in json.dumps(payload["mapping"])


def test_redact_tool_is_listed_on_both_surfaces():
    for surface in ("secular", "witness"):
        resp = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, EngineConfig(surface))
        names = [t["name"] for t in resp["result"]["tools"]]
        assert "redact" in names and "verify" in names


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} gateway tests passed — scrub/restore, guard, MCP redact.")
