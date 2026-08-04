"""The tool contract: strict schemas out, typed errors back. Tasks #124 (floor) and #125.

Before this existed, measured: 32 call sites returned {"error": ...} as ordinary data with
isError:false — an agent had to sniff every result body to learn whether its call worked — and
schemas shipped with unbounded strings, arrays, and open objects. These tests pin the two sides
of the contract at the ONE place each is enforced: schemas where they are served, errors where
they are wrapped. Site-by-site vocabulary enums remain #124's open half, tracked there.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.config import EngineConfig  # noqa: E402
from concordance.mcp import handle  # noqa: E402
from concordance.mcp.server import (  # noqa: E402
    ERROR_CODES, _ERROR_PATTERNS, classify_error, _strictify)

SEC = EngineConfig()


def _served_tools():
    return handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, SEC)["result"]["tools"]


def _walk(schema, path=""):
    yield path, schema
    for k, v in (schema.get("properties") or {}).items():
        yield from _walk(v, f"{path}.{k}" if path else k)
    if isinstance(schema.get("items"), dict):
        yield from _walk(schema["items"], f"{path}[]")


# ── schemas (the #124 floor) ─────────────────────────────────────────────────────────────────

def test_every_served_schema_is_closed_and_bounded():
    """The floor, on all 83 at once: objects closed, strings bounded (or enum/pattern/format),
    arrays bounded with typed items, numbers bounded. Applied where schemas are SERVED, so a
    loose literal in the source cannot reach a client."""
    loose = []
    for t in _served_tools():
        for path, s in _walk(t["inputSchema"]):
            where = f"{t['name']}:{path or '<root>'}"
            typ = s.get("type")
            if (typ == "object" or "properties" in s) and s.get("additionalProperties") is not False:
                loose.append(f"{where} open object")
            if typ == "string" and not any(k in s for k in ("enum", "pattern", "maxLength", "format", "const")):
                loose.append(f"{where} unbounded string")
            if typ == "array" and ("maxItems" not in s or not isinstance(s.get("items"), dict)):
                loose.append(f"{where} unbounded array")
            if typ in ("integer", "number") and ("minimum" not in s or "maximum" not in s):
                loose.append(f"{where} unbounded number")
    assert not loose, f"{len(loose)} loose spots reached a client: {loose[:8]}"


def test_hand_written_constraints_survive_the_floor():
    """_strictify is a FLOOR, not a steamroller: now.tz's pattern and maxLength must pass
    through untouched, and a tighter hand bound is never widened."""
    tz = next(t for t in _served_tools() if t["name"] == "now")["inputSchema"]["properties"]["tz"]
    assert tz["maxLength"] == 64 and tz["pattern"].startswith("^")
    tight = _strictify({"type": "object", "properties": {
        "n": {"type": "integer", "minimum": 1, "maximum": 5}}, "additionalProperties": False})
    assert tight["properties"]["n"] == {"type": "integer", "minimum": 1, "maximum": 5}


# ── errors (the #125 envelope) ───────────────────────────────────────────────────────────────

def test_a_business_error_leaves_typed_with_iserror_true():
    """The failure this replaces: {"error": "card not found"} with isError:false. Now the same
    site's message rides out classified, flagged, and carrying its remedy."""
    r = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "card_get", "arguments": {"id": "card_that_does_not_exist"}}},
               SEC)
    res = r["result"]
    assert res["isError"] is True, "a business error left with isError false"
    body = json.loads(res["content"][0]["text"])
    assert body["code"] == "CARD_NOT_FOUND"
    assert body["remedy"] == ERROR_CODES["CARD_NOT_FOUND"]
    assert body["error"], "the human message must survive beside the code"


def test_a_success_is_untouched_by_the_envelope():
    r = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "now", "arguments": {}}}, SEC)
    assert r["result"]["isError"] is False
    assert "code" not in json.loads(r["result"]["content"][0]["text"])


def test_a_rich_payload_with_an_error_field_is_data_not_failure():
    """The narrowness that keeps the classifier honest: a substantive result that happens to
    carry an 'error' key beside real fields must not be recast as a failure."""
    from concordance.mcp.server import _is_business_error
    assert _is_business_error({"error": "not found"})
    assert _is_business_error({"error": "x", "detail": "y", "available": []})
    assert not _is_business_error({"error": "minor", "cards": [1, 2], "total": 2})
    assert not _is_business_error({"verdict": "HOLDS"})
    assert not _is_business_error("plain text")


def test_the_taxonomy_is_total_and_every_code_carries_a_remedy():
    for code, remedy in ERROR_CODES.items():
        assert remedy.strip(), f"{code} has no remedy — a code nobody can act on"
    for pattern, code in _ERROR_PATTERNS:
        assert code in ERROR_CODES, f"pattern '{pattern}' maps to undeclared code {code}"
    assert classify_error("completely novel wording") == "UNCLASSIFIED"
    assert classify_error("card not found") == "CARD_NOT_FOUND"
    assert classify_error("ref required") == "INVALID_SPEC"
    assert classify_error("rate limit exceeded") == "RATE_LIMITED"
    assert classify_error(None) == "UNCLASSIFIED"


def test_the_cross_plane_refusal_and_crash_paths_carry_codes_too():
    r = handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                "params": {"name": "verify", "arguments": {}}}, SEC, profile="library")
    # a mount refusal is a protocol-level error (the tool is not callable here at all)
    assert "error" in r and "/mcp/core" in r["error"]["message"]
    assert classify_error(r["error"]["message"]) == "SURFACE_FORBIDDEN"
