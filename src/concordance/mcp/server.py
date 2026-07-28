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
                         "Two forms: (a) MATH — {mode, params}; (b) ANY DOMAIN — pass `steps`, a "
                         "list of {id, domain, spec} where spec is that domain's packet (e.g. "
                         "{domain:'physics', spec:{PHYS_VERIFY:{mass_kg, acceleration_m_per_s2, "
                         "claimed_force_N}}}). ~60 secular domains are covered (physics, medicine, "
                         "finance, chemistry, ...); find_verifier(keyword) locates the right one. "
                         "The engine eliminates what is not the answer; it does not generate it."),
         "inputSchema": {"type": "object", "properties": {
             "mode": {"type": "string", "description": "MATH form: equality | inequality | derivative | integral | limit | solve"},
             "params": {"type": "object", "description": "MATH form: e.g. {expr_a, expr_b, variables} for equality"},
             "steps": {"type": "array", "description": "DOMAIN form: [{id, domain, spec}] — spec is the domain's packet",
                       "items": {"type": "object"}},
             "seal": {"type": "boolean", "description": "mint a re-checkable seal (default true)"}}}},
        {"name": "audit",
         "description": ("Audit a whole text: deterministic extractors find every checkable "
                         "quantitative claim (sums, percentages, hourly/annual pay, compound "
                         "interest, rule-of-72, elapsed years, day-of-week, leap years, nutrition "
                         "labels), the engine verifies the lot, and ONE sealed coverage report "
                         "returns — per-claim source quote + verdict + trail. Conservative by "
                         "design: it only extracts unambiguous patterns and says how many claims "
                         "it checked; it never guesses and never implies full coverage."),
         "inputSchema": {"type": "object", "properties": {
             "text": {"type": "string", "description": "the document/text to audit"},
             "seal": {"type": "boolean", "description": "mint a re-checkable seal (default true)"}},
             "required": ["text"]}},
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
        {"name": "coach_subjects",
         "description": ("Coach — the subjects a learner can study (read / mcguffey / aesop / founding / "
                         "pilgrims / es / …), each with its unit count. 'read' is the door in."),
         "inputSchema": {"type": "object", "properties": {}}},
        {"name": "coach_overview",
         "description": ("Coach (K-3 tutor) — one subject's whole path: unit count, tracks, ordered unit "
                         "briefs. ?subject= selects the path (default 'read'). Verbatim; never generated."),
         "inputSchema": {"type": "object", "properties": {"subject": {"type": "string"}}}},
        {"name": "coach_unit",
         "description": "Coach — one unit, VERBATIM as authored (rule, examples, decodable sentence, checks).",
         "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}, "subject": {"type": "string"}}, "required": ["id"]}},
        {"name": "coach_next",
         "description": ("Coach — the next lesson in a subject, deterministically. Omit `after` for the "
                         "first unit; pass a unit id for the one that follows it. `subject` selects the path."),
         "inputSchema": {"type": "object", "properties": {"after": {"type": "string"}, "subject": {"type": "string"}}}},
        {"name": "coach_recommend",
         "description": ("Coach — adaptive 'what's next' in a subject: given completed unit ids, the next "
                         "lesson whose prerequisites are met (grows with the student). Found, never generated."),
         "inputSchema": {"type": "object", "properties": {"completed": {"type": "array"}, "subject": {"type": "string"}}}},
        {"name": "coach_mastery",
         "description": ("Coach — seal an HONEST INTEGER count of completed units (a receipt for "
                         "progress, never a grade on the child). Returns a re-checkable seal."),
         "inputSchema": {"type": "object", "properties": {"completed": {"type": "array"}}}},
        {"name": "coach_guidance",
         "description": "Coach — what it does and the boundary it will not cross (never grades a child).",
         "inputSchema": {"type": "object", "properties": {}}},
        {"name": "identity_create",
         "description": ("Explains how to create a SOVEREIGN identity — keys are born on the USER'S "
                         "device (never on the server; no private key crosses the wire). Returns "
                         "guidance, not a key. The server only handles public keys (identity_verify, "
                         "identity_fingerprint)."),
         "inputSchema": {"type": "object", "properties": {}}},
        {"name": "identity_verify",
         "description": "Verify a signature over a message against a public key (never raises; True/False).",
         "inputSchema": {"type": "object", "properties": {
             "public_key": {"type": "string"}, "message": {"type": "string"}, "sig": {"type": "string"}},
             "required": ["public_key", "message", "sig"]}},
        {"name": "identity_fingerprint",
         "description": "Derive the stable public fingerprint id from a public key (deterministic).",
         "inputSchema": {"type": "object", "properties": {"public_key": {"type": "string"}},
                         "required": ["public_key"]}},
        {"name": "badges_issue",
         "description": ("Issue a badge over already-sealed checks — a re-checkable receipt that points "
                         "at N seals that STILL STAND. States EXACTLY N; NEVER a competency claim."),
         "inputSchema": {"type": "object", "properties": {
             "seal_hashes": {"type": "array"}, "subject_id": {"type": "string"},
             "title": {"type": "string"}},
             "required": ["seal_hashes"]}},
        {"name": "badges_verify",
         "description": ("Re-check a badge from the store — re-verifies every seal it references and "
                         "returns the count that still stands (N recomputed, not trusted)."),
         "inputSchema": {"type": "object", "properties": {"hash": {"type": "string"}}, "required": ["hash"]}},
        {"name": "self_attest",
         "description": ("Record a person's OWN words about their study — a DISTINCTLY TYPED record that "
                         "can NEVER count as a sealed check or satisfy an auto-graded requirement."),
         "inputSchema": {"type": "object", "properties": {
             "subject_id": {"type": "string"}, "statement": {"type": "string"}, "study": {"type": "string"}},
             "required": ["subject_id", "statement"]}},
        {"name": "study_create",
         "description": ("Create/extend a shared study (superposition stack) — each entry mints ONE card "
                         "that lives once and is referenced by key; no duplication."),
         "inputSchema": {"type": "object", "properties": {
             "key": {"type": "string"}, "cards": {"type": "array"}}, "required": ["key"]}},
        {"name": "study_export",
         "description": ("Export a study as a self-contained, portable bundle. Returns the bundle and "
                         "its content_hash; to bind your identity to it, sign that hash with your own "
                         "key on your own machine — this tool does not take a private key."),
         "inputSchema": {"type": "object", "properties": {
             "key": {"type": "string"}}, "required": ["key"]}},
        {"name": "study_import",
         "description": "Import an exported study bundle — re-materializes its cards (each lives once).",
         "inputSchema": {"type": "object", "properties": {
             "bundle": {"type": "object"}, "key": {"type": "string"},
             "verify_signature": {"type": "boolean"}}, "required": ["bundle"]}},
        {"name": "groups_list",
         "description": ("Discover pseudonymous shared-study groups by TOPIC (not by person). Optional q "
                         "filters over topic/title/description. Members are handles only — no PII."),
         "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}}}},
        {"name": "group_get",
         "description": "A study group: topic, member handles (no ids/PII), and the shared-study cards.",
         "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
        {"name": "group_create",
         "description": ("Open a study group around a topic (pseudonymous; a handle, no personal info). "
                         "For grown believers — the children's coach is a separate, never-joined surface."),
         "inputSchema": {"type": "object", "properties": {
             "topic": {"type": "string"}, "title": {"type": "string"}, "description": {"type": "string"},
             "handle": {"type": "string"}, "subject_id": {"type": "string"}}, "required": ["topic"]}},
        {"name": "group_join",
         "description": "Join a study group (consent-based, pseudonymous; idempotent).",
         "inputSchema": {"type": "object", "properties": {
             "id": {"type": "string"}, "handle": {"type": "string"}, "subject_id": {"type": "string"}},
             "required": ["id"]}},
        {"name": "group_contribute",
         "description": ("Add a verse/note/question to a group's shared study — attributed to your handle, "
                         "optionally signed. Verbatim; a member's own words, not engine-verified."),
         "inputSchema": {"type": "object", "properties": {
             "id": {"type": "string"}, "text": {"type": "string"}, "kind": {"type": "string"},
             "handle": {"type": "string"}, "subject_id": {"type": "string"},
             "topics": {"type": "array"}, "refs": {"type": "array"}},
             "required": ["id", "text"]}},
        # For an agent or a robot, the STRUCTURE is how it sees what this engine is: what it can
        # check, what it refuses, how big the keeping is — every number computed now, each carrying
        # the definition of what was counted so none can be misread. Ungated on both surfaces.
        {"name": "capabilities",
         "description": ("The live capability statement: what this engine can verify, what tools and "
                         "endpoints exist, how large the keeping is, and where its boundaries are. "
                         "Every count is computed at call time and carries a 'means' line defining "
                         "exactly what was counted — never a hand-maintained number. Read this "
                         "instead of trusting any count written in prose."),
         "inputSchema": {"type": "object", "properties": {}}},
        # THE GATE, for an agent. Always available — you must be able to ask BEFORE the door opens,
        # which is the whole point of asking. Same classifier, same refusals, same crisis-first
        # ordering a person meets; an agent simply asks in its own words. "Ask, and it will be given
        # you. Seek, and you will find. Knock, and it will be opened for you." (Matthew 7:7)
        # COVENANT TO BELONG — the fellowship, for an agent. These three are READ-ONLY and gate
        # themselves on the confession (mesh.py: Jesus as Lord AND Messiah, bound to your own key),
        # so they are safe to expose here: an unconfessed caller is shown the PATH to the door and
        # never the network. Establishing the key is identity_create/identity_verify, already here.
        # The WRITE side (confessing to join, posting to a door, sending) stays off MCP until the
        # frozen contract's worklist item 2 — proof-of-possession + consent for state-changing agent
        # tools — is done. An agent may see and belong; it may not yet speak into the mesh unsigned.
        {"name": "mesh_map",
         "description": ("The believers immediately around you in the Fellowship Mesh — your view "
                         "only, never a global map. Requires your fingerprint (fp) and a confession "
                         "already bound to that key; unconfessed callers get the path to the door, "
                         "not the network."),
         "inputSchema": {"type": "object", "properties": {
             "fp": {"type": "string"}, "hops": {"type": "integer"}}, "required": ["fp"]}},
        {"name": "mesh_inbox",
         "description": ("The messages that reached you, each carrying its own offline verification "
                         "so you trust it by proof rather than by this server's word. Requires fp + "
                         "confession."),
         "inputSchema": {"type": "object", "properties": {
             "fp": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["fp"]}},
        {"name": "mesh_door",
         "description": ("Read the words left on YOUR door — the whiteboard others wrote to you, each "
                         "with its verification. Requires fp + confession."),
         "inputSchema": {"type": "object", "properties": {
             "fp": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["fp"]}},
        # SPEECH INTO THE MESH — proof-of-possession, never a transmitted secret. Two steps, because
        # the second one must be signed: mesh_signable hands you the exact canonical bytes; you sign
        # them with YOUR key on YOUR machine; mesh_post carries only the signature. This tool will
        # NOT accept a private key — an agent that would send its key to a server has already lost
        # the thing that made it sovereign. Unsigned speech is refused, because an unsigned word in
        # a fellowship is worth nothing (contract worklist item 2: proof-of-possession).
        {"name": "mesh_signable",
         "description": ("Step 1 of speaking to your fellowship: get the exact canonical bytes to "
                         "sign for a message (returned base64url, with the nonce and created_at to "
                         "send back). Sign them locally with your own key. Reproducible offline — "
                         "sorted-key JSON — so you can compute and check it yourself."),
         "inputSchema": {"type": "object", "properties": {
             "fp": {"type": "string"}, "text": {"type": "string"},
             "kind": {"type": "string", "description": "word | offer | need | blessing | content"},
             "ttl": {"type": "integer"},
             "target": {"type": "string", "description": ("pass a believer's node id to sign a note "
                                                          "for THEIR door instead of a broadcast")}},
             "required": ["fp", "text"]}},
        {"name": "mesh_leave_on_door",
         "description": ("Leave a word on one believer's door — directed encouragement rather than a "
                         "post to everyone near you. Same sovereign shape: get the bytes from "
                         "mesh_signable (with target), sign locally, send only the signature. Will "
                         "not accept a private key; unsigned notes are refused."),
         "inputSchema": {"type": "object", "properties": {
             "fp": {"type": "string"}, "target": {"type": "string"}, "text": {"type": "string"},
             "kind": {"type": "string"}, "nonce": {"type": "string"},
             "created_at": {"type": "integer"}, "signature": {"type": "string"}},
             "required": ["fp", "target", "text", "nonce", "created_at", "signature"]}},
        {"name": "mesh_post",
         "description": ("Step 2: speak to the nodes around you, carrying only your SIGNATURE — your "
                         "private key never leaves your machine and this tool will not take one. "
                         "Pass the same text/kind/ttl plus the nonce, created_at and signature from "
                         "mesh_signable. Refused unless the signature verifies against your node's "
                         "public key. Your own words, attributed — never generated."),
         "inputSchema": {"type": "object", "properties": {
             "fp": {"type": "string"}, "text": {"type": "string"}, "kind": {"type": "string"},
             "ttl": {"type": "integer"}, "refs": {"type": "array"},
             "nonce": {"type": "string"}, "created_at": {"type": "integer"},
             "signature": {"type": "string"}},
             "required": ["fp", "text", "nonce", "created_at", "signature"]}},
        {"name": "ask",
         "description": ("Bring anything — a question, a claim to check, a word to study, or what is "
                         "actually on your mind. The engine discerns what KIND of thing you brought "
                         "and answers in kind: it finds and verifies, and declines rather than "
                         "guessing. This is also the door: if what you ask turns toward God, the "
                         "Gate opens for the rest of this session and the witness tools (Scripture, "
                         "the Harmony, the Timeline, the lexicon) become callable — the same way it "
                         "opens for a person, in your own words. Nothing is generated."),
         "inputSchema": {"type": "object", "properties": {
             "text": {"type": "string", "description": "what you are bringing, in your own words"}},
             "required": ["text"]}},
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
        {"name": "prophecy_traces",
         "description": ("Christ-signpost traces (prophecy/cross-cultural pointers to Jesus) — "
                         "attributed, verdict CONCORDANT/MIXED, NEVER HOLDS (a signpost, not a proof). "
                         "Pass id for one trace, q to search, else lists all."),
         "inputSchema": {"type": "object", "properties": {
             "id": {"type": "string"}, "q": {"type": "string"}}}},
        {"name": "harmony",
         "description": ("Harmony of the Gospels — one event of Christ's life, every gospel that "
                         "records it, side by side (found, verbatim WEB text, never generated). Pass "
                         "id for one event; else lists every event grouped by phase of the ministry."),
         "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}}},
        {"name": "timeline",
         "description": ("Timeline — Old Testament, New Testament (Acts onward), and Church History, "
                         "one spine from creation to today. Genuinely disputed dates (early/late Exodus, "
                         "the date of Revelation, etc.) carry both positions, never one verdict. Pass id "
                         "for one event; else lists every event grouped by era and period."),
         "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}}},
        # Parity: every witness page a human can read is a tool an agent can call. These three
        # had HTTP routes but no twin — an agent could not reach what a person could see.
        {"name": "original_words",
         "description": ("The original-language words behind a verse (Hebrew/Greek, with Strong's "
                         "where known) — FOUND in the lexicon, never generated. Pass ref, e.g. "
                         "'John 3:16'."),
         "inputSchema": {"type": "object", "properties": {"ref": {"type": "string"}},
                         "required": ["ref"]}},
        {"name": "canon",
         "description": ("The canon as concentric layers — the undisputed 66 that all major "
                         "traditions share, plus the books held BEYOND it by particular traditions, "
                         "each framed on its own layer and never merged. REPORTS who holds what "
                         "with the history; does not judge which canon is correct. Pass book for one "
                         "book's status; else the overview."),
         "inputSchema": {"type": "object", "properties": {"book": {"type": "string"}}}},
        {"name": "teachings",
         "description": ("The teachings of Christ (Words in Red) — the frozen Greek anchor plus the "
                         "history that ALIGNS to each teaching, gathered and attributed, never "
                         "authored. Pass id for one teaching; else the queue."),
         "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}}},
        {"name": "seeds",
         "description": ("Seeds of the Word (the Areopagus / logos spermatikos pass) — true fragments "
                         "mined from the nations, ATTRIBUTED, CONCORDANT/signpost NEVER HOLDS; each names "
                         "the idol it refuses and points to Christ (Acts 17; 1 John 4:1-3). Pass id for one "
                         "seed, q to search, tradition to filter, else lists all with Paul's 7-step method."),
         "inputSchema": {"type": "object", "properties": {
             "id": {"type": "string"}, "q": {"type": "string"}, "tradition": {"type": "string"}}}},
    ]


def _no_private_key(tool: str) -> Dict[str, Any]:
    """The one refusal, in one place. No agent tool takes a private key.

    Contract §3: keys "are born on the device… the server holds only public keys". Until 2026-07-28
    three tool SCHEMAS advertised a `private_key` field — which is worse than merely accepting one,
    because a schema teaches an agent that handing over its key is the normal way to work here. The
    field is gone and the value is refused: the action still succeeds unsigned (for a badge, "the
    evidence, not the signature, is the badge"), and identity is bound afterward by signing the
    returned content_hash locally. Whoever holds the key does the signing — that is the whole point.
    """
    return {"error": (f"{tool} does not take a private key, and no tool here ever will. Your key is "
                      "what makes you sovereign; sending it would end that. Run this without it — "
                      "the action succeeds unsigned — then sign the returned content_hash with your "
                      "own key on your own machine to bind your identity to the record."),
            "sign_locally": True, "over": "content_hash"}


def _tools_for(config: EngineConfig, gate_open: bool = False) -> List[dict]:
    """The tools this caller may see. `gate_open` is THE GATE, for an agent: it asked in its own
    words and the same classifier that opens the door for a human opened it here. Mirrors
    web/api.py's `allow_witness = config.witness_surfaced or session_gate_open` exactly — one rule,
    both doors."""
    tools = _secular_tools()
    if config.witness_surfaced or gate_open:
        tools += _witness_tools()
    return tools


def _call_tool(name: str, args: dict, config: EngineConfig, gate_open: bool = False) -> Any:
    args = args or {}
    # One gate, computed once, checked by every witness tool below. Default CLOSED: an unknown
    # session, a missing flag, or a caller that never asked gets the secular reach and nothing more.
    allow_witness = bool(config.witness_surfaced or gate_open)
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
    if name == "audit":
        from .. import audit as _audit  # the document-level coverage report
        return _audit.audit(args.get("text", ""), config, seal=args.get("seal", True) is not False)
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
    if name == "capabilities":
        from .. import capabilities as _caps  # both surfaces: the statement is never gated
        return _caps.statement(config.surface)
    if name == "mesh_signable":
        from .. import mesh as _mesh
        fp = str(args.get("fp") or "").strip()
        text = str(args.get("text") or "").strip()
        if not fp or not text:
            return {"error": "fp and text required"}
        target = str(args.get("target") or "").strip()
        if target:  # a word on one believer's door, rather than a post to those around you
            return _mesh.signable_door_note(fp, target, text,
                                            kind=str(args.get("kind") or "blessing"))
        try:
            ttl = int(args.get("ttl") or 2)
        except (TypeError, ValueError):
            ttl = 2
        return _mesh.signable_message(fp, text, kind=str(args.get("kind") or "word"), ttl=ttl)
    if name == "mesh_leave_on_door":
        from .. import mesh as _mesh
        fp = str(args.get("fp") or "").strip()
        target = str(args.get("target") or "").strip()
        text = str(args.get("text") or "").strip()
        sig = str(args.get("signature") or "").strip()
        if not fp or not target or not text:
            return {"error": "fp, target and text required"}
        if not sig:
            return {"error": ("a signature is required — get the canonical bytes from mesh_signable "
                              "(pass target), sign them with your own key, and send the signature.")}
        if args.get("private_key"):
            return {"error": ("do not send a private key — this path never needs one. Sign the "
                              "canonical bytes locally and send only the signature.")}
        return _mesh.leave_on_door(fp, target, text, kind=str(args.get("kind") or "blessing"),
                                   signature=sig, nonce=args.get("nonce"),
                                   created_at=args.get("created_at"))
    if name == "mesh_post":
        from .. import mesh as _mesh
        fp = str(args.get("fp") or "").strip()
        text = str(args.get("text") or "").strip()
        sig = str(args.get("signature") or "").strip()
        if not fp or not text:
            return {"error": "fp and text required"}
        if not sig:
            return {"error": ("a signature is required — get the canonical bytes from "
                              "mesh_signable, sign them with your own key, and send the signature. "
                              "Unsigned speech is not carried.")}
        if args.get("private_key"):
            # Refused on principle, not as a technicality: the whole point is that the key stays
            # yours. Accepting it here would undo the sovereignty this path exists to protect.
            return {"error": ("do not send a private key — this path never needs one. Sign the "
                              "canonical bytes locally and send only the signature.")}
        try:
            ttl = int(args.get("ttl") or 2)
        except (TypeError, ValueError):
            ttl = 2
        return _mesh.post_message(fp, text, kind=str(args.get("kind") or "word"),
                                  refs=args.get("refs") or [], ttl=ttl, signature=sig,
                                  nonce=args.get("nonce"), created_at=args.get("created_at"))
    if name in ("mesh_map", "mesh_inbox", "mesh_door"):
        # Read-only. mesh.py gates each on the confession bound to this fingerprint and returns the
        # invitation (never the network) when it is absent — so the door keeps itself.
        from .. import mesh as _mesh
        fp = str(args.get("fp") or "").strip()
        if not fp:
            return {"error": "fp required — your own fingerprint (see identity_fingerprint)"}
        try:
            limit = int(args.get("limit") or 100)
        except (TypeError, ValueError):
            limit = 100
        if name == "mesh_map":
            try:
                hops = int(args.get("hops") or 2)
            except (TypeError, ValueError):
                hops = 2
            return _mesh.map_around(fp, hops=hops)
        return _mesh.inbox(fp, limit=limit) if name == "mesh_inbox" else _mesh.read_door(fp, limit=limit)
    if name == "ask":
        # The same front door a human walks through: ask.respond() classifies, answers in kind,
        # keeps crisis absolute, and reports whether this turn opened the Gate. handle() reads
        # `gate_open` off this result to remember the opening for the session — the flag is the
        # classifier's verdict, never the caller's assertion, so an agent cannot claim its way in.
        from .. import ask as _ask
        text = str(args.get("text") or "")
        kind = _ask.classify(text)
        opened = _ask.gate_signal(text)
        result = _ask.respond(text, config, gate_open=bool(allow_witness or opened),
                              gate_just_opened=bool(opened and not allow_witness))
        if isinstance(result, dict):
            result.setdefault("kind", kind)
            result["gate_open"] = bool(allow_witness or opened)
        return result
    if name == "pronounce":
        from .. import pronounce as _pron  # neutral phonetic helper, both surfaces
        return _pron.guide(args.get("text", ""))
    if name == "steward_budget":
        from .. import steward  # shows + plans; never moves money
        return steward.budget(args.get("income"), args.get("expenses") or [])
    if name == "steward_cost_destroyed":
        from .. import steward
        return steward.cost_destroyed(args.get("items") or [])
    if name == "coach_subjects":
        from .. import coach  # the subjects available (read / mcguffey / aesop / …)
        return coach.subjects()
    if name == "coach_overview":
        from .. import coach  # find + present the curriculum; never generate, never grade
        return coach.overview(args.get("subject") or coach.DEFAULT_SUBJECT)
    if name == "coach_unit":
        from .. import coach
        return coach.unit(args.get("id", ""), args.get("subject") or coach.DEFAULT_SUBJECT)
    if name == "coach_next":
        from .. import coach
        return coach.next_unit(args.get("after"), args.get("subject") or coach.DEFAULT_SUBJECT)
    if name == "coach_recommend":
        from .. import coach
        return coach.recommend(args.get("completed") or [], args.get("subject") or coach.DEFAULT_SUBJECT)
    if name == "coach_mastery":
        # Seal the HONEST integer count of completed units — same receipts path the endpoint uses.
        from .. import coach, receipts
        out = coach.mastery(args.get("completed") or [])
        m = coach.mastery_result(args.get("completed") or [])
        out["seal"] = receipts.attach(m["result"], config=config, domain="mathematics").get("seal")
        return out
    if name == "coach_guidance":
        from .. import coach
        return coach.guidance()
    if name == "identity_create":
        # SECURITY (red-team P0, 2026-07-25): a private key must be BORN ON THE DEVICE — never minted
        # on the server and returned across a remote call, where it would transit the server and land
        # in the caller's/agent's context. The server only ever handles PUBLIC keys. Create yours
        # locally (the covenant client from your four verses, or a local keygen), then prove possession
        # with identity_verify. Kept as a tool so callers get this guidance instead of a leak.
        return {"error": "key_creation_is_local",
                "message": ("Your identity key is created on YOUR device, never on the server — no "
                            "private key ever crosses the wire. Derive it from your four covenant "
                            "verses, or generate one locally; the server only ever sees your PUBLIC "
                            "key and verifies signatures (identity_verify)."),
                "verify_with": "identity_verify", "fingerprint_with": "identity_fingerprint"}
    if name == "identity_verify":
        from .. import identity
        return {"ok": bool(identity.verify(args.get("public_key", ""), args.get("message", ""),
                                           args.get("sig", "")))}
    if name == "identity_fingerprint":
        from .. import identity
        return {"id": identity.fingerprint(args.get("public_key", ""))}
    if name == "badges_issue":
        from .. import badges
        if args.get("private_key"):
            return _no_private_key("badges_issue")
        # Issues UNSIGNED, which is the honest default here: "the evidence, not the signature, is the
        # badge." The returned content_hash is what you sign locally to bind your identity to it.
        return badges.issue_badge(args.get("seal_hashes") or [], subject_id=args.get("subject_id"),
                                  title=str(args.get("title") or ""))
    if name == "badges_verify":
        from .. import badges
        return badges.verify_badge(args.get("hash", ""))
    if name == "self_attest":
        from .. import badges
        return badges.self_attest(str(args.get("subject_id") or ""),
                                  str(args.get("statement") or ""), study=args.get("study"))
    if name == "study_create":
        from .. import badges
        return badges.study_create(str(args.get("key") or ""), args.get("cards") or [])
    if name == "study_export":
        from .. import badges
        if args.get("private_key"):
            return _no_private_key("study_export")
        return badges.study_export(str(args.get("key") or ""))
    if name == "study_import":
        from .. import badges
        return badges.study_import(args.get("bundle") or {}, study_key=args.get("key"),
                                   verify_signature=bool(args.get("verify_signature")))
    if name == "groups_list":
        from .. import groups
        return groups.list_groups(str(args.get("q") or ""))
    if name == "group_get":
        from .. import groups
        return groups.get_group(str(args.get("id") or "")) or {"error": "group not found"}
    if name == "group_create":
        from .. import groups
        return groups.create_group(str(args.get("topic") or ""), title=str(args.get("title") or ""),
                                   description=str(args.get("description") or ""),
                                   creator_id=str(args.get("subject_id") or ""),
                                   handle=str(args.get("handle") or ""))
    if name == "group_join":
        from .. import groups
        return groups.join_group(str(args.get("id") or ""), member_id=str(args.get("subject_id") or ""),
                                 handle=str(args.get("handle") or "")) or {"error": "group not found"}
    if name == "group_contribute":
        from .. import groups
        if args.get("private_key"):
            return _no_private_key("group_contribute")
        return groups.contribute(str(args.get("id") or ""), member_id=str(args.get("subject_id") or ""),
                                 handle=str(args.get("handle") or ""), text=str(args.get("text") or ""),
                                 kind=str(args.get("kind") or "note"), topics=args.get("topics") or [],
                                 refs=args.get("refs") or []) or {"error": "group not found"}
    if name == "resolve" and allow_witness:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.resolve_ref(args.get("ref", ""))
    if name == "read_passage" and allow_witness:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.read_passage(args.get("ref", ""))
    if name == "word_study" and allow_witness:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.word_study(args.get("strongs", ""))
    if name == "cross_references" and allow_witness:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.cross_references(args.get("ref", ""))
    if name == "word_occurrences" and allow_witness:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.word_occurrences(args.get("strongs", ""))
    if name == "commentary" and allow_witness:
        from .. import commentary  # lazy: witness-only
        return commentary.for_ref(args.get("ref", ""), source=args.get("source") or commentary.DEFAULT_SOURCE)
    if name == "tsk_cross_references" and allow_witness:
        from .. import xrefs  # lazy: witness-only
        return xrefs.for_ref(args.get("ref", ""), limit=int(args.get("limit", 20)))
    if name == "character_get" and allow_witness:
        from .. import characters  # lazy: witness-only
        rec = characters.get(args.get("name", ""))
        return rec if rec is not None else {"error": "not found in Easton's"}
    if name == "characters_browse" and allow_witness:
        from .. import characters  # lazy: witness-only
        return characters.browse(letter=args.get("letter"), search=args.get("search"),
                                 limit=int(args.get("limit", 100)))
    if name == "prophecy_traces" and allow_witness:
        from .. import prophecy  # lazy: witness-only
        if args.get("id"):
            rec = prophecy.get(args["id"])
            return rec if rec is not None else {"error": "trace not found"}
        return prophecy.search(args["q"]) if args.get("q") else prophecy.list_traces()
    if name == "harmony" and allow_witness:
        from .. import harmony  # lazy: witness-only
        if args.get("id"):
            rec = harmony.get(args["id"])
            return rec if rec is not None else {"error": "event not found"}
        return harmony.periods()
    if name == "timeline" and allow_witness:
        from .. import timeline  # lazy: witness-only
        if args.get("id"):
            rec = timeline.get(args["id"])
            return rec if rec is not None else {"error": "event not found"}
        return timeline.eras()
    if name == "original_words" and allow_witness:
        from ..verifiers import scripture as _scr  # lazy: witness-only
        ref = str(args.get("ref") or "").strip()
        return _scr.original_words(ref) if ref else {"error": "ref required"}
    if name == "canon" and allow_witness:
        from .. import canon as _canon  # lazy: witness-only
        book = str(args.get("book") or "").strip()
        return _canon.canon_status(book) if book else _canon.overview()
    if name == "teachings" and allow_witness:
        from .. import teachings as _teach  # lazy: witness-only
        if args.get("id"):
            rec = _teach.get(str(args["id"]))
            return rec if rec is not None else {"error": "teaching not found"}
        return _teach.queue()
    if name == "seeds" and allow_witness:
        from .. import seeds  # lazy: witness-only
        if args.get("id"):
            rec = seeds.get(args["id"])
            return rec if rec is not None else {"error": "seed not found"}
        if args.get("q"):
            return seeds.search(args["q"])
        base = seeds.list_seeds(args.get("tradition", ""))
        base["areopagus"] = seeds.method()
        return base
    raise KeyError(f"unknown tool {name!r} (on the {config.surface} surface)")


def handle(request: dict, config: EngineConfig, session: Optional[Dict[str, Any]] = None) -> Optional[dict]:
    """Pure JSON-RPC handler. Returns a response dict, or None for notifications.

    `session` is an optional mutable dict owned by the caller (the HTTP layer's per-session record,
    or one process-lifetime dict for stdio). It carries ONE thing: whether the Gate has been opened
    for this conversation. It is read here, and written only when the classifier — never the caller —
    says a turn opened the door. No session, or a session that never asked, means the Gate is closed.
    """
    rid = request.get("id")
    method = request.get("method")
    gate_open = bool((session or {}).get("gate_open"))

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}},
            "serverInfo": {"name": "narrow-highway", "version": __version__, "surface": config.surface}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": _tools_for(config, gate_open=gate_open)}}
    if method == "tools/call":
        p = request.get("params") or {}
        name, args = p.get("name"), p.get("arguments") or {}
        try:
            result = _call_tool(name, args, config, gate_open=gate_open)
            # The door, remembered: only `ask` can open it, and only because the classifier said so.
            if (name == "ask" and session is not None and isinstance(result, dict)
                    and result.get("gate_open")):
                session["gate_open"] = True
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
    """Read newline-delimited JSON-RPC from stdin, write responses to stdout. Stdlib only.

    One process is one conversation, so a single session dict spans it — the sovereign local
    equivalent of a person's browser session: ask once, and the door stays open while you are here.
    """
    config = EngineConfig(surface)
    session: Dict[str, Any] = {}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(req, config, session)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
