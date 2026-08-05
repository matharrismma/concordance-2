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

PROTOCOL_VERSION = "2024-11-05"   # kept as the floor; see SUPPORTED_PROTOCOL_VERSIONS

# NEWEST FIRST. The server hard-returned 2024-11-05 to every client regardless of what the
# client asked for — and modern clients make TRANSPORT decisions from the negotiated version.
# A connector requesting 2025-06-18 was answered "2024-11-05", fell back to old-transport
# expectations (a GET server stream, which this endpoint answers 405 by design), and declared
# the server dead. Measured 2026-08-04: narrowhighway.com/mcp answered a raw probe perfectly
# while Claude connectors flapped all day — the wire was fine, the negotiation was the outage.
# The independent MCP assessment flagged exactly this (F-03) before we felt it in production.
#
# What we implement IS Streamable HTTP (POST /mcp, optional SSE response, Mcp-Session-Id,
# DELETE termination) — the 2025 revisions' transport — so declaring them is honest, and
# declaring only 2024-11-05 was the overclaim-in-reverse: describing modern behavior with an
# old label. Batching stays accepted leniently (removed in 2025-06-18; clients on that
# revision simply never send it).
SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")


def negotiate_protocol_version(requested) -> str:
    """The client's requested revision if we support it; otherwise our newest.

    Per the MCP spec the server answers an unsupported request with the latest version it DOES
    support and the client decides whether to proceed. One function, used by both the JSON-RPC
    handler and the HTTP header path, so the body and the header can never disagree.
    """
    r = str(requested or "").strip()
    return r if r in SUPPORTED_PROTOCOL_VERSIONS else SUPPORTED_PROTOCOL_VERSIONS[0]


def _secular_tools() -> List[dict]:
    return [
        {"name": "verify",
         "description": ("Verify a claim deterministically — returns a verdict "
                         "(HOLDS / BROKEN / INCOMPLETE / SYSTEM_ERROR), the worked trail, AND a "
                         "sealed receipt "
                         "{content_hash, cite_url} you can re-fetch and re-verify (seal_fetch). "
                         "Two forms: (a) MATH — {mode, params}; (b) ANY DOMAIN — pass `steps`, a "
                         "list of {id, domain, spec} where spec is that domain's packet (e.g. "
                         "{domain:'physics', spec:{PHYS_VERIFY:{mass_kg, acceleration_m_per_s2, "
                         "claimed_force_N}}}). ~60 secular domains are covered (physics, medicine, "
                         "finance, chemistry, ...); find_verifier(keyword) locates the right one. "
                         "The engine eliminates what is not the answer; it does not generate it. "
                         "READ THE VERDICT EXACTLY: only BROKEN is a finding about the claim. "
                         "SYSTEM_ERROR means OUR verifier could not run (see `means` and `error_at`) "
                         "and says NOTHING about whether the claim is true — never relay it to a "
                         "human as a refutation. INCOMPLETE means no verifier applied (`gap_at`)."),
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
             "topics": {"type": "array"}, "refs": {"type": "array"},
             "attestation": {"type": "object", "description": ("optional: sign sha256(text) with "
                 "your own key (signing.sign_seal) and pass it here — a handle alone is only a "
                 "claim, a signature makes your authorship checkable. Never send a private key.")}},
             "required": ["id", "text"]}},
        # For an agent or a robot, the STRUCTURE is how it sees what this engine is: what it can
        # check, what it refuses, how big the keeping is — every number computed now, each carrying
        # the definition of what was counted so none can be misread. Ungated on both surfaces.
        {"name": "calendar_create",
         "description": ("Create ONE event in a human's calendar — the pilot on-behalf write, and "
                         "the only one. Requires a LIVE consent grant: the human signed a scoped, "
                         "expiring calendar_write grant for YOUR key fingerprint on their own "
                         "device (GET /consent/signable → sign locally → POST /consent). Without "
                         "it this refuses and teaches the way in. The event lands only in the "
                         "calendar THEY configured (their .ics file or CalDAV); nothing is stored "
                         "here, and the receipt names the grant that authorized it. Deleting the "
                         "event in their calendar removes it everywhere."),
         "inputSchema": {"type": "object", "properties": {
             "grantor_pubkey": {"type": "string"}, "agent_fp": {"type": "string"},
             "summary": {"type": "string"}, "start_iso": {"type": "string"},
             "end_iso": {"type": "string"}, "description": {"type": "string"}},
             "required": ["grantor_pubkey", "agent_fp", "summary", "start_iso"]}},
        {"name": "consent_check",
         "description": ("Check whether a human has authorized YOU (this agent's key fingerprint) "
                         "for a named verb — the agent covenant's 'request human authorization "
                         "before writes'. Speaking as YOURSELF (your own key, your own words) "
                         "needs no consent: a member is not a proxy. Consent governs only acting "
                         "on a human's behalf with their data. If unauthorized, the response "
                         "teaches the way: the human issues a grant via GET /consent/signable, "
                         "signs on their device, POSTs to /consent."),
         "inputSchema": {"type": "object", "properties": {
             "agent_fp": {"type": "string"}, "verb": {"type": "string"},
             "grantor_pubkey": {"type": "string"}},
             "required": ["agent_fp", "verb", "grantor_pubkey"]}},
        {"name": "shelf_signable",
         "description": ("THE COMMONS — step 1 of stocking your own shelf. Returns {fields, "
                         "signable}: the exact canonical bytes to sign with YOUR key on YOUR "
                         "machine. A shelf is a covenant key with cards on it, not an account. "
                         "Rings: `private` (only you) · `shelf` (you and the friends who chose "
                         "you — UNGATED, live the moment you sign) · `commons` (site-wide, waits "
                         "for a human steward). The gate is on what the library AMPLIFIES, never "
                         "on what you may say."),
         "inputSchema": {"type": "object", "properties": {
             "member": {"type": "string", "description": "your public key — the shelf is the key"},
             "kind": {"type": "string", "description": "note|writing|recipe|build|field_note|"
                                                       "question|link|suggestion"},
             "subject": {"type": "string"}, "body": {"type": "string"},
             "ring": {"type": "string", "description": "private|shelf|commons"},
             "url": {"type": "string", "description": "kind=link only — the address. We open it "
                                                      "once in an airlock, keep the WAYBILL (its "
                                                      "own title, size, sha256, when we looked) "
                                                      "and discard the bytes. No page of anyone "
                                                      "else's is stored, and nothing is embedded: "
                                                      "an iframe would hand the reader's IP to the "
                                                      "provider. The body is still required — a "
                                                      "bare link is not curation."},
             "quote": {"type": "string", "description": "optional short passage YOU typed, capped; "
                                                        "requires `attribution`"},
             "attribution": {"type": "string", "description": "whose words the quote is"}},
             "required": ["member", "kind", "body"]}},
        {"name": "shelf_drop",
         "description": ("Step 2 — stock the shelf. Send the fields from shelf_signable plus a "
                         "detached signature over those bytes; the private key never travels. "
                         "Your words stay at the `member` tier forever: promotion to the commons "
                         "carries them further, it does not make them the library's claim. "
                         "`display_name` is the ONLY profile field there is."),
         "inputSchema": {"type": "object", "properties": {
             "fields": {"type": "object"}, "signature": {"type": "string"},
             "display_name": {"type": "string"}},
             "required": ["fields", "signature"]}},
        {"name": "shelf_read",
         "description": ("Read one member's shelf. Pass `viewer` (your own key) to see your own "
                         "private drops; anyone else sees the shelf ring and promoted commons "
                         "cards only. Nothing anywhere records who read what."),
         "inputSchema": {"type": "object", "properties": {
             "member": {"type": "string"}, "viewer": {"type": "string"}},
             "required": ["member"]}},
        {"name": "commons_read",
         "description": ("What the fellowship has put on the commons — promoted member work, "
                         "newest first. Every card is a member's own work at the `member` tier: "
                         "the library amplified it; the library did not verify it."),
         "inputSchema": {"type": "object", "properties": {
             "limit": {"type": "integer"}}, "required": []}},
        {"name": "curate_queue",
         "description": ("What waits on a HUMAN steward. The counter never promotes; it only "
                         "decides when a person must look."),
         "inputSchema": {"type": "object", "properties": {}, "required": []}},
        {"name": "curate_signable",
         "description": ("The canonical bytes for withdrawing YOUR OWN card. A member never needs "
                         "permission to take their own words down — the proof is the same key that "
                         "signed the drop. Sign these bytes, then call `curate` with them."),
         "inputSchema": {"type": "object", "properties": {
             "card_id": {"type": "string"}, "member": {"type": "string"}},
             "required": ["card_id", "member"]}},
        {"name": "curate",
         "description": ("A recorded act on one drop: `promoted` · `refused` · `withdrawn`. A name "
                         "AND a reason are always required — no anonymous judgement, and a refusal "
                         "without a reason teaches the community nothing. WHO MAY ACT: promoting or "
                         "refusing needs the steward `token` (these decide what the whole library "
                         "amplifies); withdrawing your own card needs `fields`+`signature` from "
                         "`curate_signable` instead. A typed name is not authority. A refusal "
                         "withholds amplification only — the drop stays on the member's own shelf. "
                         "Acts are appended, never replaced."),
         "inputSchema": {"type": "object", "properties": {
             "card_id": {"type": "string"}, "action": {"type": "string"},
             "steward": {"type": "string"}, "reason": {"type": "string"},
             "token": {"type": "string", "description": "steward token — promote/refuse only"},
             "fields": {"type": "object", "description": "from curate_signable, to withdraw"},
             "signature": {"type": "string", "description": "detached, over those fields"}},
             "required": ["card_id", "action", "steward", "reason"]}},
        {"name": "moderation_signable",
         "description": ("Step 1 of a report or a block: the exact canonical bytes to sign with "
                         "your own key, on your own machine. Returns {fields, signable}. Sign the "
                         "decoded `signable` bytes and pass BOTH fields and signature to `report`. "
                         "The private key never travels."),
         "inputSchema": {"type": "object", "properties": {
             "action": {"type": "string", "description": "report | block | unblock"},
             "target_id": {"type": "string"}, "actor": {"type": "string",
                                                        "description": "your public key"},
             "extra": {"type": "string"}},
             "required": ["action", "target_id", "actor"]}},
        {"name": "want_open",
         "description": ("Ask the library to ACQUIRE something it does not hold (kind=missing, "
                         "give query) or to EXPAND a thin card (kind=expand, give card_id). Opens "
                         "a want on the AGENT PLANE — held separate on the desk until the next "
                         "human who looks seconds it by asking for the same thing. Call this only "
                         "when your principal genuinely needs what the keeping lacks; the same "
                         "miss asked twice is one want asked twice. No requester identity is "
                         "stored; queries are scrubbed before storage."),
         "inputSchema": {"type": "object", "properties": {
             "query": {"type": "string"}, "kind": {"type": "string"},
             "card_id": {"type": "string"}, "note": {"type": "string"}},
             "required": []}},
        {"name": "wants_list",
         "description": ("The library's desiderata desk — open wants, sorted by demand, agent "
                         "plane marked and separate. Read it to find gaps you could dig for."),
         "inputSchema": {"type": "object", "properties": {
             "state": {"type": "string"}, "plane": {"type": "string"}},
             "required": []}},
        {"name": "want_offer",
         "description": ("Return to the comb with a FOUND source for an open want: label + url + "
                         "snippet, attributed. You are a forager, not an author — offer only "
                         "public-domain / openly-licensed sources you actually located, never "
                         "generated text. The offer lands as a QUARANTINED option cell tagged "
                         "with your agent label; a NAMED HUMAN chooses, and only then is a card "
                         "created. There is no path around the comb."),
         "inputSchema": {"type": "object", "properties": {
             "want_id": {"type": "string"}, "label": {"type": "string"},
             "url": {"type": "string"}, "snippet": {"type": "string"},
             "domain": {"type": "string"}, "agent": {"type": "string",
                 "description": "your self-declared name, e.g. 'claude' — the shaft-tag a steward can cut a branch by"}},
             "required": ["want_id", "label"]}},
        {"name": "report",
         "description": ("Report a community item (group_contribution, mesh_message, door_note) "
                         "to the moderation floor. One report is a claim, never a verdict; at "
                         "three DISTINCT reporters the item is held for a HUMAN steward's review "
                         "(Deut 19:15). The counter never judges — it decides when a person must "
                         "look. A report must be SIGNED (call moderation_signable first): three "
                         "witnesses means three keys, never three invented names."),
         "inputSchema": {"type": "object", "properties": {
             "kind": {"type": "string"}, "target_id": {"type": "string"},
             "reason": {"type": "string"}, "note": {"type": "string"},
             "fields": {"type": "object", "description": "the exact fields from moderation_signable"},
             "signature": {"type": "string", "description": "detached signature over those bytes"}},
             "required": ["kind", "target_id", "reason", "fields", "signature"]}},
        {"name": "attest_record",
         "description": ("Bind your identity to a record you already hold — phase 2 of the sovereign "
                         "flow. Do the thing unsigned (badges_issue, study_export, group_contribute), "
                         "take the returned content_hash, sign THAT hash with your own key on your own "
                         "machine, and submit only the attestation {alg, over, content_hash, pubkey, "
                         "sig}. Never send a private key. Several parties may attest to one record: "
                         "one signature is a claim, two or three witnesses begin to establish a "
                         "matter (Deuteronomy 19:15)."),
         "inputSchema": {"type": "object", "properties": {
             "content_hash": {"type": "string"},
             "attestation": {"type": "object", "description": "the dict from signing.sign_seal, built locally"}},
             "required": ["content_hash", "attestation"]}},
        {"name": "witnesses",
         "description": ("Who has borne witness to a record, each signature re-verified as it is read "
                         "(storage is never trusted). Reports invalid entries rather than hiding them."),
         "inputSchema": {"type": "object", "properties": {"content_hash": {"type": "string"}},
                         "required": ["content_hash"]}},
        {"name": "now",
         "description": ("The actual current date and time, fresh at this call — UTC (the clock "
                         "every seal is stamped in), the library's home zone, and optionally any "
                         "IANA zone you name. Your own sense of 'today' is months old; this is "
                         "the correction. Never cached; unresolvable zones are declared, never "
                         "guessed at."),
         "inputSchema": {"type": "object", "properties": {
             "tz": {"type": "string", "maxLength": 64,
                    "pattern": "^[A-Za-z][A-Za-z0-9_+/\\-]*$",
                    "description": "IANA zone name, e.g. America/New_York or Europe/Berlin; "
                                   "omit for UTC + the library's home zone"}},
             "additionalProperties": False}},
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
        {"name": "backmatter",
         "description": ("Back-matter reference tables: weights_measures, names_of_god, parables, "
                         "miracles, book_intros, topical_index. Disputes carried (a cubit's two "
                         "lengths, a book's two datings), refs verified against the corpus, names "
                         "of God carry Strong's numbers that open in word_study. Pass table for one "
                         "table; else the index of all six."),
         "inputSchema": {"type": "object", "properties": {"table": {"type": "string"}}}},
        {"name": "bible_places",
         "description": ("The Atlas — biblical places with REAL coordinates, honestly held: "
                         "located places carry lat/lon (cross-checked against an independent "
                         "gazetteer); disputed sites (Mount Sinai, Cana, Golgotha) NAME their "
                         "candidates instead of planting one flag; unlocatable places (Eden, "
                         "Emmaus, Tarshish, Ophir) are honest blanks with no coordinates. Pass "
                         "name for one place; else all places with by_status counts."),
         "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}}},
        {"name": "narratives",
         "description": ("The storyboards — the common narratives charted in the Bible FIRST "
                         "(exile-and-return, the barren woman bears, down-to-the-pit-raised, the "
                         "great reversal...), each instance real people with verified refs. The 17 "
                         "movements are one shared vocabulary, so components isolate and recombine: "
                         "pass movement='testing' to walk it across every storyboard. Pass id for "
                         "one storyboard; else the index. FRAMING, always: a person may display "
                         "characteristics of many of these at times of their life — a reference "
                         "point, NEVER an identity assignment."),
         "inputSchema": {"type": "object", "properties": {"id": {"type": "string"},
                                                          "movement": {"type": "string"}}}},
        {"name": "study_find",
         "description": ("The quick-find index — ONE lookup across the whole reference section: "
                         "archetypes, storyboards, movements, the six study tables, the atlas, "
                         "harmony, timeline, and the encyclopedia. Each hit is a pointer to the "
                         "real entry, which carries its own refs and its own honesty. The index "
                         "finds; it never ranks truth."),
         "inputSchema": {"type": "object", "properties": {"q": {"type": "string"}},
                         "required": ["q"]}},
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


# ── THE PROFILES — mount narrow, not broad ───────────────────────────────────────────────────
# Task #123, from the adopted external assessment (docs/MCP_ASSESSMENT_2026-08-04.md §3.3) and
# Matt's 2026-07-30 consolidation directive. One 83-tool connector is an overloaded discovery
# surface: tool selection degrades, permission review blurs, and a low-risk read shares a door
# with a consequential write. So the catalog is PARTITIONED — every tool in exactly ONE profile
# (a test enforces the partition), and a client mounts /mcp/<profile> to see only that plane.
# /mcp itself still serves the full catalog for existing clients; narrowing it is a later,
# deliberate cutover, not a silent break.
#
# Each tool carries its EFFECT class (assessment §11.1) — machine-readable risk, not prose:
#   read            fetch what is held
#   derive          compute from inputs (verify, redact, a calculation)
#   preserve        append a durable record (seal, study entry, a want) — user intent required
#   publish         place content where OTHERS see it — the social plane
#   external_action touch a system OUTSIDE the library (calendar) — consent-gated
EFFECTS = ("read", "derive", "preserve", "publish", "external_action")

PROFILES: Dict[str, Dict[str, Any]] = {
    "core": {
        "version": "1.0.0",
        "description": "Deterministic checks and receipts: verify a claim, audit a document, "
                       "fetch and witness seals, read the engine's own capabilities and clock.",
        "tools": {"verify": "derive", "audit": "derive", "seal_fetch": "read",
                  "attest_record": "preserve", "witnesses": "read",
                  "now": "read", "capabilities": "read"},
    },
    "library": {
        "version": "1.0.0",
        "description": "Read-only retrieval over the keeping: search, cards, the grid, the "
                       "conversational door. Provenance attached; nothing here writes.",
        "tools": {"search": "read", "card_get": "read", "cards_browse": "read",
                  "cards_stats": "read", "daily_card": "read", "grid_axis": "read",
                  "grid_dimension": "read", "card_connections": "read", "locate": "read",
                  "library_health": "read", "pronounce": "derive", "study_find": "read",
                  "seeds": "read", "ask": "read"},
    },
    "sovereign": {
        "version": "1.0.0",
        "description": "Identity, consent, and personal sovereignty: keys born on the device, "
                       "signable payloads, the consent lock, private budgeting, redaction — and "
                       "the one consent-gated external action (calendar).",
        "tools": {"identity_create": "preserve", "identity_verify": "derive",
                  "identity_fingerprint": "derive", "badges_issue": "preserve",
                  "badges_verify": "derive", "self_attest": "preserve",
                  "consent_check": "read", "redact": "derive",
                  "steward_budget": "derive", "steward_cost_destroyed": "derive",
                  "calendar_create": "external_action"},
    },
    "coach": {
        "version": "1.0.0",
        "description": "Bounded curriculum access and learning records. Kept apart from the "
                       "community plane on purpose — the assessment's child-surface isolation.",
        "tools": {"coach_subjects": "read", "coach_overview": "read", "coach_unit": "read",
                  "coach_next": "read", "coach_recommend": "read", "coach_mastery": "preserve",
                  "coach_guidance": "read", "study_create": "preserve",
                  "study_export": "read", "study_import": "preserve"},
    },
    "witness": {
        "version": "1.0.0",
        "description": "Attributed Scripture study: the text, the original words, the "
                       "cross-references, the charts — found and cited, never generated. "
                       "Gate semantics unchanged from the main door.",
        "tools": {"resolve": "read", "read_passage": "read", "word_study": "read",
                  "cross_references": "read", "word_occurrences": "read", "commentary": "read",
                  "tsk_cross_references": "read", "character_get": "read",
                  "characters_browse": "read", "prophecy_traces": "read", "harmony": "read",
                  "timeline": "read", "backmatter": "read", "bible_places": "read",
                  "narratives": "read", "original_words": "read", "canon": "read",
                  "teachings": "read"},
    },
    "community": {
        "version": "1.0.0",
        "description": "The social plane: groups, shelves, the commons, the mesh, moderation, "
                       "and the want loop. Every publish-class tool in the catalog lives here, "
                       "and this profile is OFF by default on a hosted box — publishing is a "
                       "separate deployment decision with governance attached.",
        "tools": {"groups_list": "read", "group_get": "read", "group_create": "publish",
                  "group_join": "publish", "group_contribute": "publish",
                  "shelf_signable": "derive", "shelf_drop": "publish", "shelf_read": "read",
                  "commons_read": "read", "curate_queue": "read", "curate_signable": "derive",
                  "curate": "publish", "moderation_signable": "derive", "report": "publish",
                  "mesh_map": "read", "mesh_inbox": "read", "mesh_door": "read",
                  "mesh_signable": "derive", "mesh_leave_on_door": "publish",
                  "mesh_post": "publish",
                  "want_open": "preserve", "wants_list": "read", "want_offer": "publish"},
    },
}


# ── THE ERROR TAXONOMY (task #125, assessment F-06) ──────────────────────────────────────────
# Measured before this existed: 32 sites returned {"error": "card not found"} as ordinary tool
# data with isError:false, forcing every agent to sniff result bodies to learn whether a call
# worked. Now the ENVELOPE classifies at the one wrapping point: a business error leaves as an
# MCP tool error (isError:true) carrying a typed code and what to do about it. The 32 sites
# keep their plain human messages — the classifier reads them; nothing downstream re-learns 32
# call sites.
ERROR_CODES: Dict[str, str] = {
    "INVALID_SPEC": "correct the arguments and retry — the message names what is missing or malformed",
    "VERIFIER_NOT_FOUND": "no deterministic verifier covers this domain; consult capabilities for what does",
    "CLAIM_INCOMPLETE": "supply the missing quantities the trail names; the claim was not testable as given",
    "SEAL_NOT_FOUND": "the content hash resolves to nothing held; check the hash or the seal may be superseded",
    "CARD_NOT_FOUND": "no card by that id; use search or locate to find the right one",
    "AUTHORIZATION_REQUIRED": "this action needs a signed grant or consent record first; see /consent",
    "GRANT_EXPIRED": "the grant's window has closed; a new signable must be issued and signed",
    "SIGNATURE_INVALID": "the signature does not verify over the payload; re-sign locally and resend",
    "SURFACE_FORBIDDEN": "this tool is not served on this surface or plane; the message says where it lives",
    "RATE_LIMITED": "back off and retry after the stated interval",
    "INTERNAL_FAILURE": "our fault, not the claim's; retry once, then report it — never read this as a verdict",
    "UNCLASSIFIED": "read the message; if a pattern is missing from the classifier, that is a bug to file",
}

# Ordered, first match wins. Patterns are matched lowercase against the site's own message —
# the classification is DERIVED from what the tool already says, visible here in one table.
_ERROR_PATTERNS = (
    ("rate limit", "RATE_LIMITED"),
    ("not found", "CARD_NOT_FOUND"),
    ("no card", "CARD_NOT_FOUND"),
    ("no seal", "SEAL_NOT_FOUND"),
    ("unknown hash", "SEAL_NOT_FOUND"),
    ("expired", "GRANT_EXPIRED"),
    ("signature", "SIGNATURE_INVALID"),
    ("consent", "AUTHORIZATION_REQUIRED"),
    ("grant", "AUTHORIZATION_REQUIRED"),
    ("not in the mounted profile", "SURFACE_FORBIDDEN"),
    ("witness surface", "SURFACE_FORBIDDEN"),
    ("gate", "SURFACE_FORBIDDEN"),
    ("required", "INVALID_SPEC"),
    ("must be", "INVALID_SPEC"),
    ("invalid", "INVALID_SPEC"),
    ("malformed", "INVALID_SPEC"),
    ("no verifier", "VERIFIER_NOT_FOUND"),
    ("no applicable", "VERIFIER_NOT_FOUND"),
    ("incomplete", "CLAIM_INCOMPLETE"),
    ("tool error", "INTERNAL_FAILURE"),
)


def classify_error(message: str) -> str:
    m = str(message or "").lower()
    for pattern, code in _ERROR_PATTERNS:
        if pattern in m:
            return code
    return "UNCLASSIFIED"


def _is_business_error(result: Any) -> bool:
    """A result whose substance is an error report. Kept narrow on purpose: a rich payload that
    HAPPENS to include an 'error' field beside real data is data, not a failure."""
    return (isinstance(result, dict) and "error" in result
            and not (set(result) - {"error", "detail", "why", "hint", "available", "status"}))


# ── SCHEMA STRICTNESS FLOOR (task #124, assessment F-05) ─────────────────────────────────────
# Hand-tightening 83 schemas invites drift; the FLOOR is applied uniformly where the schemas are
# SERVED, so every listed tool is bounded even if its literal source is loose: objects close
# (additionalProperties false), bare strings get a length ceiling, bare arrays get items+maxItems,
# bare numbers get bounds. Vocabulary enums (mode/kind/ring) still belong in the source schemas —
# that is the remaining half of #124, per tool, where the vocabularies live.
_STR_MAXLEN = 4000          # a tool argument is an argument, not a document — the airlock takes documents
_ARR_MAXITEMS = 200
_NUM_BOUND = 1e12


def _strictify(schema: Any) -> Any:
    if not isinstance(schema, dict):
        return schema
    s = dict(schema)
    t = s.get("type")
    if t == "object" or "properties" in s:
        s.setdefault("additionalProperties", False)
        if isinstance(s.get("properties"), dict):
            s["properties"] = {k: _strictify(v) for k, v in s["properties"].items()}
    if t == "string" and not any(k in s for k in ("enum", "pattern", "maxLength", "format", "const")):
        s["maxLength"] = _STR_MAXLEN
    if t == "array":
        s.setdefault("maxItems", _ARR_MAXITEMS)
        s["items"] = _strictify(s.get("items") if isinstance(s.get("items"), dict)
                                else {"type": "string", "maxLength": _STR_MAXLEN})
    if t in ("integer", "number"):
        s.setdefault("minimum", -_NUM_BOUND)
        s.setdefault("maximum", _NUM_BOUND)
    return s


# ── VOCABULARY ENUMS (task #124, the finishing half) ─────────────────────────────────────────
# Sourced from the modules that OWN each vocabulary at serving time — never copied into schema
# literals, so the enum and the implementation cannot drift (the vine, not a photograph).
# ENUM_TODO names the props whose vocabularies exist only as scattered comparisons; each needs
# its constant established in its own module before it can be wired — a countable remainder,
# not a vague one.
ENUM_TODO = {
    "curate.action": "shelves.py compares 'promoted'/'withdrawn' inline; needs CURATE_ACTIONS",
    "grid_axis.axis": "dimension names are data-driven and grow; an enum would refuse valid new ones",
}


def _enum_wiring() -> Dict[tuple, list]:
    from ..derivation import _MATH_MODES
    from ..shelves import KINDS, RINGS
    return {
        ("verify", "mode"): sorted(_MATH_MODES),
        ("shelf_signable", "kind"): sorted(KINDS),
        ("shelf_signable", "ring"): sorted(RINGS),
    }


def _apply_enums(tool_name: str, schema: Any) -> Any:
    if not isinstance(schema, dict) or not isinstance(schema.get("properties"), dict):
        return schema
    wiring = _enum_wiring()
    props = dict(schema["properties"])
    for (tname, prop), vocab in wiring.items():
        if tname == tool_name and prop in props and isinstance(props[prop], dict):
            props[prop] = dict(props[prop], enum=vocab)
    return dict(schema, properties=props)


def profile_of(tool_name: str) -> Optional[str]:
    for pname, p in PROFILES.items():
        if tool_name in p["tools"]:
            return pname
    return None


def _tools_for(config: EngineConfig, gate_open: bool = False) -> List[dict]:
    """The tools this caller may see. `gate_open` is THE GATE, for an agent: it asked in its own
    words and the same classifier that opens the door for a human opened it here. Mirrors
    web/api.py's `allow_witness = config.witness_surfaced or session_gate_open` exactly — one rule,
    both doors."""
    # THE SAME LINE, ON THE AGENT'S DOOR. Matt, 2026-07-31: "We don't hide knowledge. We aren't a
    # secret society. Everyone is a part of the group. They experience what they want of it."
    #
    # This is where the HTTP fix would have died quietly. web/api.py opened; twenty tools here
    # stayed shut, so an agent — ClaudeBot alone is ~67k requests across the hosts, 58% of api.narrowhighway.com — could
    # not so much as SEE read_passage, character_get, canon or word_study on the secular surface.
    # Correct server-side and invisible to the caller is the failure this project keeps meeting.
    #
    # `gate_open` survives as the invitation it always was: it still tells ask.py how to meet
    # someone. It no longer decides what exists.
    return _secular_tools() + _witness_tools()


def _call_tool(name: str, args: dict, config: EngineConfig, gate_open: bool = False) -> Any:
    args = args or {}
    # One gate, computed once, checked by every witness tool below. Default CLOSED: an unknown
    # session, a missing flag, or a caller that never asked gets the secular reach and nothing more.
    # THE CLASSIFIER'S VERDICT, never the caller's assertion. This decides the VOICE — how ask.py
    # meets someone — and nothing else. It briefly decided access too, on 2026-07-31, when opening
    # knowledge was done by forcing this True; that let an agent claim its way in and the gate
    # tests caught it within the hour. Access and voice are different questions.
    allow_witness = bool(config.witness_surfaced or gate_open)
    # Knowledge is open to everyone (see _tools_for). A tool that only READS the keeping must not
    # consult the flag above.
    knowledge = True
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
        # Same announced ceiling as GET /search — one rule for both doors, and the agent is TOLD
        # when it applies rather than left to assume it saw everything. (2026-08-01: this door
        # served 1.67 MB / 5.1 s for a 200-byte request asking limit=10^9.)
        from ..web.api import bounded_limit
        _limit, _capped = bounded_limit(args.get("limit"), 10)
        res = corpus.search(args.get("query", ""), limit=_limit)
        out = {"count": len(res), "results": [
            {"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf"),
             "snippet": (c.get("body", "") or "")[:200]} for c in res]}
        if _capped:
            out["limit_capped"] = _capped
        if not res:
            # SAME MECHANISM AS THE HUMAN DOOR, DIFFERENT PLANE. A miss is a slower answer, not a
            # chore handed to a person: we go to the public-domain archives now and card what we
            # find. On the AGENT plane the card enters `public_review`, withheld from every public
            # read path until a human looks — the agent gets its answer, the shared library waits.
            #
            # The want list is only for having NO CONNECTION. Queueing something we could simply
            # have fetched turns a slower answer into someone's homework, which is backwards.
            from .. import expand as _expand
            ex = _expand.expand(args.get("query", ""), config, plane="agent")
            if ex.get("status") == "acquired":
                res = corpus.search(args.get("query", ""), limit=_limit)
                out["count"] = len(res)
                out["results"] = [{"id": c.get("id"), "title": c.get("title"),
                                   "shelf": c.get("shelf"),
                                   "snippet": (c.get("body", "") or "")[:200]} for c in res]
                out["expanded"] = {
                    "status": "acquired", "message": ex.get("message"),
                    "held_for_review": ex.get("held_for_review"),
                    "documents": [{"title": d.get("title"), "url": d.get("url"),
                                   "source": d.get("source"), "license": d.get("license")}
                                  for d in (ex.get("documents") or [])[:5]]}
            else:
                out["expanded"] = {k: v for k, v in ex.items() if k != "documents"}
        return out
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
    if name == "calendar_create":
        from .. import connect_write as _cw
        return _cw.create_event(str(args.get("grantor_pubkey") or ""),
                                str(args.get("agent_fp") or ""),
                                str(args.get("summary") or ""), str(args.get("start_iso") or ""),
                                end_iso=(args.get("end_iso") or None),
                                description=str(args.get("description") or ""))
    if name == "consent_check":
        from .. import consent as _consent
        return _consent.guard(str(args.get("agent_fp") or ""), str(args.get("verb") or ""),
                              str(args.get("grantor_pubkey") or ""))
    if name == "shelf_signable":
        from .. import shelves as _sh
        return _sh.signable_drop(str(args.get("member") or ""), str(args.get("kind") or ""),
                                 str(args.get("subject") or ""), str(args.get("body") or ""),
                                 ring=str(args.get("ring") or "shelf"),
                                 url=str(args.get("url") or ""),
                                 quote=str(args.get("quote") or ""),
                                 attribution=str(args.get("attribution") or ""))
    if name == "shelf_drop":
        from .. import shelves as _sh
        if args.get("private_key") or (isinstance(args.get("fields"), dict)
                                       and args["fields"].get("private_key")):
            return _no_private_key("shelf_drop")
        return _sh.drop(args.get("fields") if isinstance(args.get("fields"), dict) else None,
                        str(args.get("signature") or ""),
                        display_name=str(args.get("display_name") or ""))
    if name == "shelf_read":
        from .. import shelves as _sh
        return _sh.shelf_of(str(args.get("member") or ""),
                            viewer=(str(args["viewer"]) if args.get("viewer") else None))
    if name == "commons_read":
        from .. import shelves as _sh
        return _sh.commons(limit=int(args.get("limit", 40) or 40))
    if name == "curate_queue":
        from .. import shelves as _sh
        return _sh.review_queue()
    if name == "curate":
        from .. import shelves as _sh
        return _sh.curate(str(args.get("card_id") or ""), str(args.get("action") or ""),
                          str(args.get("steward") or ""), reason=str(args.get("reason") or ""),
                          token=str(args.get("token") or ""),
                          fields=(args.get("fields") if isinstance(args.get("fields"), dict)
                                  else None),
                          signature=str(args.get("signature") or ""))
    if name == "curate_signable":
        from .. import shelves as _sh
        return _sh.signable_curate(str(args.get("card_id") or ""), str(args.get("member") or ""),
                                   str(args.get("action") or "withdrawn"))
    if name == "moderation_signable":
        from .. import moderation as _mod
        return _mod.signable(str(args.get("action") or ""), str(args.get("target_id") or ""),
                             str(args.get("actor") or ""), extra=str(args.get("extra") or ""))
    if name == "want_open":
        from .. import wants as _wants
        return _wants.open_want(query=str(args.get("query") or ""),
                                kind=str(args.get("kind") or "missing"),
                                card_id=str(args.get("card_id") or ""),
                                note=str(args.get("note") or ""), plane="agent")
    if name == "wants_list":
        from .. import wants as _wants
        return _wants.listing(state=(str(args.get("state") or "") or None),
                              plane=(str(args.get("plane") or "") or None))
    if name == "want_offer":
        import time as _t
        from .. import wants as _wants
        return _wants.add_option(str(args.get("want_id") or ""), {
            "label": str(args.get("label") or ""), "url": str(args.get("url") or ""),
            "snippet": str(args.get("snippet") or ""), "domain": str(args.get("domain") or ""),
            "miner": "agent:" + (str(args.get("agent") or "unnamed")[:24]),
            "run": _t.strftime("mcp_%Y%m%d", _t.gmtime())})
    if name == "report":
        from .. import moderation as _mod
        if args.get("private_key"):
            return _no_private_key("report")
        return _mod.report(str(args.get("kind") or ""), str(args.get("target_id") or ""),
                           str(args.get("reason") or ""),
                           note=str(args.get("note") or ""),
                           fields=args.get("fields") if isinstance(args.get("fields"), dict) else None,
                           signature=str(args.get("signature") or ""))
    if name == "attest_record":
        from .. import attest as _attest
        if args.get("private_key"):
            return _no_private_key("attest_record")
        return _attest.bear_witness(str(args.get("content_hash") or ""),
                                    args.get("attestation") or {})
    if name == "witnesses":
        from .. import attest as _attest
        return _attest.witnesses(str(args.get("content_hash") or ""))
    if name == "now":
        from .. import ops as _ops   # both surfaces, never gated: the time of day belongs to all
        return _ops.now(str(args.get("tz") or "").strip() or None)
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
                                 refs=args.get("refs") or [],
                                 attestation=args.get("attestation")) or {"error": "group not found"}
    if name == "resolve" and knowledge:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.resolve_ref(args.get("ref", ""))
    if name == "read_passage" and knowledge:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.read_passage(args.get("ref", ""))
    if name == "word_study" and knowledge:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.word_study(args.get("strongs", ""))
    if name == "cross_references" and knowledge:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.cross_references(args.get("ref", ""))
    if name == "word_occurrences" and knowledge:
        from ..verifiers import scripture  # lazy: witness-only
        return scripture.word_occurrences(args.get("strongs", ""))
    if name == "commentary" and knowledge:
        from .. import commentary  # lazy: witness-only
        return commentary.for_ref(args.get("ref", ""), source=args.get("source") or commentary.DEFAULT_SOURCE)
    if name == "tsk_cross_references" and knowledge:
        from .. import xrefs  # lazy: witness-only
        return xrefs.for_ref(args.get("ref", ""), limit=int(args.get("limit", 20)))
    if name == "character_get" and knowledge:
        from .. import characters  # lazy: witness-only
        rec = characters.get(args.get("name", ""))
        return rec if rec is not None else {"error": "not found in Easton's"}
    if name == "characters_browse" and knowledge:
        from .. import characters  # lazy: witness-only
        return characters.browse(letter=args.get("letter"), search=args.get("search"),
                                 limit=int(args.get("limit", 100)))
    if name == "prophecy_traces" and knowledge:
        from .. import prophecy  # lazy: witness-only
        if args.get("id"):
            rec = prophecy.get(args["id"])
            return rec if rec is not None else {"error": "trace not found"}
        return prophecy.search(args["q"]) if args.get("q") else prophecy.list_traces()
    if name == "harmony" and knowledge:
        from .. import harmony  # lazy: witness-only
        if args.get("id"):
            rec = harmony.get(args["id"])
            return rec if rec is not None else {"error": "event not found"}
        return harmony.periods()
    if name == "timeline" and knowledge:
        from .. import timeline  # lazy: witness-only
        if args.get("id"):
            rec = timeline.get(args["id"])
            return rec if rec is not None else {"error": "event not found"}
        return timeline.eras()
    if name == "backmatter" and knowledge:
        from .. import backmatter as _bm  # lazy: witness-only
        if args.get("table"):
            rec = _bm.get_table(str(args["table"]))
            return rec if rec is not None else {"error": "table not found"}
        return _bm.tables()
    if name == "bible_places" and knowledge:
        from .. import bible_places as _bp  # lazy: witness-only
        if args.get("name"):
            rec = _bp.get(str(args["name"]))
            return rec if rec is not None else {"error": "place not found"}
        return _bp.places()
    if name == "narratives" and knowledge:
        from .. import narratives as _narr  # lazy: witness-only
        if args.get("id"):
            rec = _narr.get(str(args["id"]))
            return rec if rec is not None else {"error": "storyboard not found"}
        if args.get("movement"):
            rec = _narr.by_movement(str(args["movement"]))
            return rec if rec is not None else {"error": "movement not found"}
        return _narr.storyboards()
    if name == "study_find" and knowledge:
        from .. import study_index as _si  # lazy: witness-only
        return _si.find(str(args.get("q") or ""), limit=40)
    if name == "original_words" and knowledge:
        from ..verifiers import scripture as _scr  # lazy: witness-only
        ref = str(args.get("ref") or "").strip()
        return _scr.original_words(ref) if ref else {"error": "ref required"}
    if name == "canon" and knowledge:
        from .. import canon as _canon  # lazy: witness-only
        book = str(args.get("book") or "").strip()
        return _canon.canon_status(book) if book else _canon.overview()
    if name == "teachings" and knowledge:
        from .. import teachings as _teach  # lazy: witness-only
        if args.get("id"):
            rec = _teach.get(str(args["id"]))
            return rec if rec is not None else {"error": "teaching not found"}
        return _teach.queue()
    if name == "seeds" and knowledge:
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


def handle(request: dict, config: EngineConfig, session: Optional[Dict[str, Any]] = None,
           profile: Optional[str] = None) -> Optional[dict]:
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
        negotiated = negotiate_protocol_version(
            (request.get("params") or {}).get("protocolVersion"))
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": negotiated, "capabilities": {"tools": {}},
            "serverInfo": {"name": "narrow-highway", "version": __version__, "surface": config.surface}}}
    if method == "tools/list":
        tools = [dict(t, inputSchema=_strictify(_apply_enums(t["name"],
                                    t.get("inputSchema") or {"type": "object", "properties": {}})))
                 for t in _tools_for(config, gate_open=gate_open)]
        if profile is not None:
            allowed = PROFILES[profile]["tools"]
            # the mounted plane and nothing else — plus the effect class, machine-readable,
            # so a client can review risk from the listing instead of from prose
            tools = [dict(t, effect=allowed[t["name"]]) for t in tools if t["name"] in allowed]
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": tools}}
    if method == "tools/call":
        p = request.get("params") or {}
        name, args = p.get("name"), p.get("arguments") or {}
        if profile is not None and name not in PROFILES[profile]["tools"]:
            # a mount is a BOUNDARY, not a suggestion: the tool may exist on another plane,
            # and the refusal says so by name rather than pretending it does not exist
            home = profile_of(str(name))
            return {"jsonrpc": "2.0", "id": rid, "error": {
                "code": -32602,
                "message": (f"tool '{name}' is not in the mounted profile '{profile}'" +
                            (f" — it lives on /mcp/{home}" if home else " — no such tool"))}}
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
                "content": [{"type": "text", "text": json.dumps(
                    {"error": "tool error", "code": "INTERNAL_FAILURE",
                     "remedy": ERROR_CODES["INTERNAL_FAILURE"]})}], "isError": True}}
        if _is_business_error(result):
            code = classify_error(result.get("error"))
            typed = dict(result, code=code, remedy=ERROR_CODES[code])
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text", "text": json.dumps(typed, ensure_ascii=False)}],
                "isError": True}}
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
