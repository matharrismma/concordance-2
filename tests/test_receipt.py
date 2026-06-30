"""The receipt — the thesis made real: a verdict you can re-check, not 'trust me'.

Proves the floor is wired END TO END through the live surfaces: POST /verify mints a
content-addressed seal, GET /seal resolves it, cas.verify confirms it; BROKEN claims are
sealed too (proof-of-false) but never enter the ledger; ?seal=0 opts out; the MCP verify
tool seals; the cite_url is surface-correct. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _isolate():
    """Fresh data dir so seals don't pollute (and the store starts empty)."""
    d = tempfile.mkdtemp(prefix="nh-receipt-")
    os.environ["CONCORDANCE_DATA_DIR"] = d
    os.environ.pop("CONCORDANCE_PUBLIC_BASE", None)
    return d


from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

SEC = EngineConfig("secular")
WIT = EngineConfig("witness")


def _verify(body, query=None, config=SEC):
    return dispatch("POST", "/verify", query or {}, body, config)


def test_holds_mints_seal_and_seal_resolves():
    _isolate()
    from concordance import cas
    st, p = _verify({"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "4", "variables": {}}})
    assert st == 200 and p["verdict"] == "HOLDS"
    seal = p.get("seal")
    assert seal and seal["content_hash"] and seal["cite_url"].endswith(seal["content_hash"])
    assert seal["ledgered"] is True  # HOLDS enters the ledger chain
    # GET /seal resolves the receipt
    st2, rec = dispatch("GET", "/seal", {"hash": seal["content_hash"]}, None, SEC)
    assert st2 == 200 and rec["overall"] == "PASS"
    # and it actually re-verifies in the CAS
    ok, _ = cas.verify(seal["content_hash"])
    assert ok is True


def test_broken_is_sealed_but_not_ledgered():
    _isolate()
    st, p = _verify({"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "5", "variables": {}}})
    assert p["verdict"] == "BROKEN"
    seal = p.get("seal")
    assert seal and seal["content_hash"]  # proof-of-false is a receipt too
    assert seal["ledgered"] is False      # but BROKEN never becomes a precedent
    st2, rec = dispatch("GET", "/seal", {"hash": seal["content_hash"]}, None, SEC)
    assert st2 == 200 and rec["overall"] == "REJECT"


def test_pole_guard_sealed_as_false():
    _isolate()
    st, p = _verify({"mode": "equality", "params": {"expr_a": "x/x", "expr_b": "1", "variables": {}}})
    assert p["verdict"] == "BROKEN" and p["seal"]["content_hash"]  # x/x=1 caught + sealed


def test_seal_opt_out():
    _isolate()
    st, p = _verify({"mode": "equality", "params": {"expr_a": "1", "expr_b": "1", "variables": {}}},
                    query={"seal": "0"})
    assert p["verdict"] == "HOLDS" and "seal" not in p


def test_cite_url_is_surface_correct():
    _isolate()
    _, p = _verify({"mode": "equality", "params": {"expr_a": "1", "expr_b": "1", "variables": {}}}, config=WIT)
    assert "narrowhighway.org" in p["seal"]["cite_url"]
    _isolate()
    _, p2 = _verify({"mode": "equality", "params": {"expr_a": "1", "expr_b": "1", "variables": {}}}, config=SEC)
    assert "narrowhighway.com" in p2["seal"]["cite_url"]


def test_public_base_override():
    _isolate()
    os.environ["CONCORDANCE_PUBLIC_BASE"] = "https://example.test/x/"
    _, p = _verify({"mode": "equality", "params": {"expr_a": "1", "expr_b": "1", "variables": {}}})
    assert p["seal"]["cite_url"].startswith("https://example.test/x/s/")
    os.environ.pop("CONCORDANCE_PUBLIC_BASE", None)


def test_mcp_verify_mints_seal():
    _isolate()
    from concordance.mcp.server import handle
    resp = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
        "name": "verify", "arguments": {"mode": "equality",
                                        "params": {"expr_a": "2+2", "expr_b": "4", "variables": {}}}}}, SEC)
    payload = json.loads(resp["result"]["content"][0]["text"])
    assert payload["verdict"] == "HOLDS" and payload["seal"]["content_hash"]


def test_identical_holds_is_idempotent():
    _isolate()
    _, a = _verify({"mode": "equality", "params": {"expr_a": "3*3", "expr_b": "9", "variables": {}}})
    _, b = _verify({"mode": "equality", "params": {"expr_a": "3*3", "expr_b": "9", "variables": {}}})
    assert a["seal"]["content_hash"] == b["seal"]["content_hash"]  # same content -> same seal
    assert a["seal"]["ledgered"] and b["seal"]["ledgered"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} receipt tests passed — the floor is wired: verdict -> seal -> re-checkable.")
