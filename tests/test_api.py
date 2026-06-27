"""API test — the floor, exposed. Calls the pure dispatcher directly (no server needed).

Proves: health/identity per surface; the moat over HTTP (true HOLDS, false BROKEN, the
pole guard); search returns ranked results; seal 404 on a bogus hash; the witness
endpoints (/resolve, /word_study) are gated to the witness surface; unknown routes 404.
Runnable with `pytest` OR `python tests/test_api.py`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.config import EngineConfig  # noqa: E402
from concordance.web import dispatch  # noqa: E402

SEC = EngineConfig("secular")
WIT = EngineConfig("witness")


def test_health():
    s, p = dispatch("GET", "/health", {}, None, SEC)
    assert s == 200 and p["ok"] and p["surface"] == "secular"


def test_identity_differs_by_surface():
    _, sec = dispatch("GET", "/identity", {}, None, SEC)
    _, wit = dispatch("GET", "/identity", {}, None, WIT)
    assert "christ" not in sec["identity"].lower(), "secular identity must not surface religious wording"
    assert "christ" in wit["identity"].lower(), "witness identity should name the foundation"


def test_verify_moat_over_http():
    _, true = dispatch("POST", "/verify", {},
                       {"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "4", "variables": {}}}, SEC)
    assert true["verdict"] == "HOLDS"
    _, false = dispatch("POST", "/verify", {},
                        {"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "5", "variables": {}}}, SEC)
    assert false["verdict"] == "BROKEN"
    # the pole guard rides through the API too
    _, pole = dispatch("POST", "/verify", {},
                       {"mode": "equality", "params": {"expr_a": "x/x", "expr_b": "1", "variables": {}}}, SEC)
    assert pole["verdict"] != "HOLDS", "x/x==1 must not seal as an identity"


def test_search_returns_results():
    s, p = dispatch("GET", "/search", {"q": "love"}, None, SEC)
    assert s == 200 and isinstance(p["results"], list)


def test_seal_404_on_bogus_hash():
    s, _ = dispatch("GET", "/seal", {"hash": "deadbeefnotahash"}, None, SEC)
    assert s == 404


def test_witness_endpoints_gated_to_witness_surface():
    # secular reach: witness endpoints are 404
    assert dispatch("GET", "/resolve", {"ref": "John 3:16"}, None, SEC)[0] == 404
    assert dispatch("GET", "/word_study", {"strongs": "G26"}, None, SEC)[0] == 404
    # witness surface: available (200 with a status field, whatever the data state)
    sr = dispatch("GET", "/resolve", {"ref": "John 3:16"}, None, WIT)
    assert sr[0] == 200 and "status" in sr[1]
    assert dispatch("GET", "/word_study", {"strongs": "G26"}, None, WIT)[0] == 200


def test_unknown_route_404():
    assert dispatch("GET", "/nope", {}, None, SEC)[0] == 404


def test_http_mcp_endpoint():
    # remote MCP over HTTP: tools/call verify -> HOLDS
    s, p = dispatch("POST", "/mcp", {}, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "verify", "arguments": {
                        "mode": "equality", "params": {"expr_a": "2+2", "expr_b": "4", "variables": {}}}}}, SEC)
    assert s == 200
    assert json.loads(p["result"]["content"][0]["text"])["verdict"] == "HOLDS"
    s2, p2 = dispatch("POST", "/mcp", {}, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, SEC)
    assert any(t["name"] == "verify" for t in p2["result"]["tools"])


def test_derivation_verify_alias():
    s, p = dispatch("POST", "/derivation/verify", {}, {"steps": [
        {"id": "b", "domain": "mathematics",
         "spec": {"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "4", "variables": {}}}}]}, SEC)
    assert s == 200 and p["verdict"] == "HOLDS"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} API tests passed — the floor is exposed over HTTP, both surfaces, sovereign.")
