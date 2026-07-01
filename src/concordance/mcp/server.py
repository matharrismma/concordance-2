"""Sovereign MCP server — the engine for AI agents.

Stdlib only: newline-delimited JSON-RPC 2.0 over stdio, no MCP SDK dependency. `handle()`
is a pure, testable request handler; `serve_stdio()` is the thin read/write loop. Surface-
aware like everything else: the witness tools (resolve, word_study) are listed and callable
only on surface="witness". The engine verifies and finds; it does not generate the answer.
"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

from .. import __version__, cas, corpus
from ..config import EngineConfig
from ..derivation import verify_derivation
# scripture (witness verifier) is imported LAZILY in the witness-gated tool branches below —
# never at module top, so the secular surface never loads witness code.

PROTOCOL_VERSION = "2024-11-05"


def _secular_tools() -> List[dict]:
    return [
        {"name": "verify",
         "description": ("Verify a claim deterministically — returns a verdict "
                         "(HOLDS / BROKEN / INCOMPLETE), the worked trail, AND a sealed receipt "
                         "{content_hash, cite_url} you can re-fetch and re-verify (seal_fetch). "
                         "The engine eliminates what is not the answer; it does not generate it."),
         "inputSchema": {"type": "object", "properties": {
             "mode": {"type": "string", "description": "equality | inequality | derivative | integral | limit | solve"},
             "params": {"type": "object", "description": "e.g. {expr_a, expr_b, variables} for equality"},
             "seal": {"type": "boolean", "description": "mint a re-checkable seal (default true)"}},
             "required": ["mode", "params"]}},
        {"name": "search",
         "description": "Ranked search over the keeping (the kept library).",
         "inputSchema": {"type": "object", "properties": {
             "query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}},
        {"name": "seal_fetch",
         "description": "Fetch a sealed verification record (the receipt) by its content hash.",
         "inputSchema": {"type": "object", "properties": {"hash": {"type": "string"}}, "required": ["hash"]}},
        {"name": "redact",
         "description": ("Strip PII (emails, SSNs, credit cards, IPs, URLs) from text to stable "
                         "placeholders before you pass it onward; the mapping is returned so YOU "
                         "reveal replies locally. For true privacy run this on a LOCAL/sovereign "
                         "engine (the text never leaves your machine) or use the client libraries — "
                         "the strip belongs at your edge. Deterministic; pair with verify for a receipt."),
         "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
        {"name": "card_get",
         "description": "Fetch one card (the full record) from the keeping by id.",
         "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
        {"name": "cards_browse",
         "description": "Browse the keeping — paginated, optional shelf filter. Returns card briefs.",
         "inputSchema": {"type": "object", "properties": {
             "shelf": {"type": "string"}, "limit": {"type": "integer"}, "offset": {"type": "integer"}}}},
        {"name": "cards_stats",
         "description": "Counts over the keeping — total, by shelf, by surface.",
         "inputSchema": {"type": "object", "properties": {}}},
        {"name": "daily_card",
         "description": "The deterministic card of the day from the keeping (same all day).",
         "inputSchema": {"type": "object", "properties": {"seed": {"type": "string"}}}},
        {"name": "grid_axis",
         "description": "The map: a read-only view of one axis (its scaffold members, depth, "
                        "neighbors, umbrella children). Omit `axis` for an overview of all axes.",
         "inputSchema": {"type": "object", "properties": {"axis": {"type": "string"}}}},
        {"name": "grid_dimension",
         "description": "The axes that sit on a given scaffold member (dimension).",
         "inputSchema": {"type": "object", "properties": {"dimension": {"type": "string"}}, "required": ["dimension"]}},
        {"name": "card_connections",
         "description": "Cards related to one card — its explicit links + same-shelf siblings.",
         "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
        {"name": "locate",
         "description": "Find the card for a query — by exact id, then title, else ranked search.",
         "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}},
        {"name": "library_health",
         "description": "Corpus health — is the keeping loaded and sound (totals, shelves, surfaces).",
         "inputSchema": {"type": "object", "properties": {}}},
        {"name": "pronounce",
         "description": ("A synthesized pronunciation guide (respelling + approximate IPA) for a "
                         "transliteration or word — honestly labeled, not a native speaker."),
         "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
        {"name": "steward_budget",
         "description": ("Steward — a household budget (income, expenses -> net, savings rate, by "
                         "category). Shows and plans; NEVER moves money."),
         "inputSchema": {"type": "object", "properties": {
             "income": {"type": "number"}, "expenses": {"type": "array"}}, "required": ["income"]}},
        {"name": "steward_cost_destroyed",
         "description": "Steward — cost destroyed: money you did NOT spend (was -> now), kept in your currency.",
         "inputSchema": {"type": "object", "properties": {"items": {"type": "array"}}, "required": ["items"]}},
    ]


def _witness_tools() -> List[dict]:
    return [
        {"name": "resolve",
         "description": "Resolve a Scripture reference to its World English Bible text.",
         "inputSchema": {"type": "object", "properties": {"ref": {"type": "string"}}, "required": ["ref"]}},
        {"name": "read_passage",
         "description": ("Read a passage of the WEB — a single verse, a range (John 3:16-18), or a "
                         "whole chapter (John 3)."),
         "inputSchema": {"type": "object", "properties": {"ref": {"type": "string"}}, "required": ["ref"]}},
        {"name": "word_study",
         "description": "Strong's word study — original-language definition + pronunciation + every occurrence.",
         "inputSchema": {"type": "object", "properties": {
             "strongs": {"type": "string", "description": "e.g. G26, H2617"}}, "required": ["strongs"]}},
        {"name": "cross_references",
         "description": ("Verses connected to a reference by SHARED original words (Strong's) — the "
                         "dots, connected; deterministic and found, ranked by shared-word count."),
         "inputSchema": {"type": "object", "properties": {"ref": {"type": "string"}}, "required": ["ref"]}},
        {"name": "word_occurrences",
         "description": "Every verse where a Strong's word occurs (the concordance).",
         "inputSchema": {"type": "object", "properties": {
             "strongs": {"type": "string", "description": "e.g. G26, H2617"}}, "required": ["strongs"]}},
        {"name": "commentary",
         "description": ("Public-domain, attributed commentary (Matthew Henry) on a reference — the "
                         "commentator's own words, found and cited, never generated."),
         "inputSchema": {"type": "object", "properties": {
             "ref": {"type": "string"}, "source": {"type": "string"}}, "required": ["ref"]}},
        {"name": "tsk_cross_references",
         "description": ("Editorial cross-references for a verse (openbible.info, CC BY — expansion of "
                         "the public-domain TSK), ranked by relevance votes. Found + attributed."),
         "inputSchema": {"type": "object", "properties": {
             "ref": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["ref"]}},
        {"name": "character_get",
         "description": ("A Bible figure from Easton's Bible Dictionary (1897, PD) — summary + every "
                         "verse that speaks of them (found + attributed; category tag is imperfect)."),
         "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
        {"name": "characters_browse",
         "description": "Browse/search Easton's Bible Dictionary (people, places, terms).",
         "inputSchema": {"type": "object", "properties": {
             "letter": {"type": "string"}, "search": {"type": "string"}, "limit": {"type": "integer"}}}},
    ]


def _tools_for(config: EngineConfig) -> List[dict]:
    tools = _secular_tools()
    if config.witness_surfaced:
        tools += _witness_tools()
    return tools


def _call_tool(name: str, args: dict, config: EngineConfig) -> Any:
    args = args or {}
    if name == "verify":
        if isinstance(args.get("steps"), list):
            res = verify_derivation(args["steps"])
            dom = str(args["steps"][0].get("domain") or "mathematics") if args["steps"] else "mathematics"
        else:
            res = verify_derivation([{"id": "b", "domain": "mathematics",
                                      "spec": {"mode": args.get("mode"), "params": args.get("params", {})}}])
            dom = "mathematics"
        # Agents get a receipt too: a re-checkable seal, not just a verdict. seal:false opts out.
        from .. import receipts
        return receipts.attach(res, config=config, domain=dom, enabled=args.get("seal", True) is not False)
    if name == "search":
        res = corpus.search(args.get("query", ""), limit=int(args.get("limit", 10)))
        return {"count": len(res), "results": [
            {"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf"),
             "snippet": (c.get("body", "") or "")[:200]} for c in res]}
    if name == "seal_fetch":
        rec = cas.fetch(args.get("hash", ""))
        return rec if rec is not None else {"error": "seal not found"}
    if name == "redact":
        from .. import redact as _redact  # the strip-context-then-reapply gateway
        clean, mapping = _redact.redact(args.get("text", ""))
        return {"clean": clean, "mapping": mapping, "count": len(mapping)}
    if name == "card_get":
        c = corpus.get_card(args.get("id", ""))
        return c if c is not None else {"error": "card not found"}
    if name == "cards_browse":
        return corpus.browse(shelf=args.get("shelf"), limit=int(args.get("limit", 20)),
                             offset=int(args.get("offset", 0)))
    if name == "cards_stats":
        return corpus.stats()
    if name == "daily_card":
        c = corpus.daily(args.get("seed"))
        return c if c is not None else {"error": "the keeping is empty"}
    if name == "grid_axis":
        from .. import grid
        ax = args.get("axis")
        if ax:
            v = grid.axis_view(ax)
            return v if v is not None else {"error": "unknown axis"}
        return grid.overview()
    if name == "grid_dimension":
        from .. import grid
        d = args.get("dimension", "")
        return {"dimension": d, "axes": grid.dimension_axes(d)}
    if name == "card_connections":
        r = corpus.connections(args.get("id", ""))
        return r if r is not None else {"error": "card not found"}
    if name == "locate":
        return corpus.locate(args.get("q", ""))
    if name == "library_health":
        return corpus.health()
    if name == "pronounce":
        from .. import pronounce as _pron  # neutral phonetic helper, both surfaces
        return _pron.guide(args.get("text", ""))
    if name == "steward_budget":
        from .. import steward  # shows + plans; never moves money
        return steward.budget(args.get("income"), args.get("expenses") or [])
    if name == "steward_cost_destroyed":
        from .. import steward
        return steward.cost_destroyed(args.get("items") or [])
    if name == "resolve" and config.witness_surfaced:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.resolve_ref(args.get("ref", ""))
    if name == "read_passage" and config.witness_surfaced:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.read_passage(args.get("ref", ""))
    if name == "word_study" and config.witness_surfaced:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.word_study(args.get("strongs", ""))
    if name == "cross_references" and config.witness_surfaced:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.cross_references(args.get("ref", ""))
    if name == "word_occurrences" and config.witness_surfaced:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.word_occurrences(args.get("strongs", ""))
    if name == "commentary" and config.witness_surfaced:
        from .. import commentary  # lazy: witness-only
        return commentary.for_ref(args.get("ref", ""), source=args.get("source") or commentary.DEFAULT_SOURCE)
    if name == "tsk_cross_references" and config.witness_surfaced:
        from .. import xrefs  # lazy: witness-only
        return xrefs.for_ref(args.get("ref", ""), limit=int(args.get("limit", 20)))
    if name == "character_get" and config.witness_surfaced:
        from .. import characters  # lazy: witness-only
        rec = characters.get(args.get("name", ""))
        return rec if rec is not None else {"error": "not found in Easton's"}
    if name == "characters_browse" and config.witness_surfaced:
        from .. import characters  # lazy: witness-only
        return characters.browse(letter=args.get("letter"), search=args.get("search"),
                                 limit=int(args.get("limit", 100)))
    raise KeyError(f"unknown tool {name!r} (on the {config.surface} surface)")


def handle(request: dict, config: EngineConfig) -> Optional[dict]:
    """Pure JSON-RPC handler. Returns a response dict, or None for notifications."""
    rid = request.get("id")
    method = request.get("method")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}},
            "serverInfo": {"name": "narrow-highway", "version": __version__, "surface": config.surface}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": _tools_for(config)}}
    if method == "tools/call":
        p = request.get("params") or {}
        name, args = p.get("name"), p.get("arguments") or {}
        try:
            result = _call_tool(name, args, config)
        except KeyError as e:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": str(e)}}
        except Exception as e:  # noqa: BLE001 — tool errors are results, not crashes
            from .. import telemetry  # log detail server-side; return a generic message
            telemetry.record("mcp_error", surface=config.surface, tool=str(name),
                             detail=f"{type(e).__name__}: {str(e)[:160]}")
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text", "text": json.dumps({"error": "tool error"})}], "isError": True}}
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}], "isError": False}}
    if method and method.startswith("notifications/"):
        return None  # notifications get no response
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}}


def serve_stdio(surface: str = "secular") -> None:
    """Read newline-delimited JSON-RPC from stdin, write responses to stdout. Stdlib only."""
    config = EngineConfig(surface)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(req, config)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
