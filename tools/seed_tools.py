#!/usr/bin/env python3
"""The TOOL CONCORDANCE — discern which tool to reach for, connect to it, incorporate the best.

Matt, 2026-09-13: "We don't need every tool. We need the discernment to know which tool to reach
for and the ability to connect with those tools as well as continue to identify the best tools
being released and incorporate them."

So this is NOT a place to build tools. It is the discernment registry: each card gives a real tool
its due with the same four columns as the theory floor —
    good_at     what it is genuinely good at (its due / strength)
    reach_when  the task where you reach for it (its domain of validity)
    not_when    where it is the wrong tool, or must not be hand-built (its failure edge)
    connect_via HOW you connect to it — the audited library / API / MCP — because we connect, not rebuild
and connections to other tools (alternative_to / complements / supersedes / rests_on) and to the
THEORIES they stand on (rests_on a card_theory_*), each carrying its evidence.

NON-DESTRUCTIVE, idempotent, APPEND-only — same discipline as seed_lone_domains.py.

    python tools/seed_tools.py --tool ecc_ed25519
    python tools/seed_tools.py --all
    python tools/seed_tools.py --check
    python tools/seed_tools.py --ledger
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

STORE = Path("data/tool_cards.jsonl")
THEORY_STORE = Path("data/theory_cards.jsonl")

SPINE_ID = "card_spine_tools"
SPINE_CONN = {"to_card_id": SPINE_ID, "relationship": "member_of",
              "evidence": "a tool the work reaches for, discerned and connected — not rebuilt"}

REL = {"alternative_to", "complements", "supersedes", "rests_on"}

# category -> [ {id,title,subject,category,tier,good_at,reach_when,not_when,connect_via,body,
#                conns:[(rel,target,evidence)]} ]
TOOLS: dict[str, list[dict]] = {
    "cryptography": [
        {
            "id": "card_tool_ecc_ed25519",
            "title": "Elliptic-curve cryptography (ECC / Ed25519)",
            "subject": "Elliptic-curve cryptography",
            "category": "cryptography",
            "tier": "battle-tested standard",
            "good_at": "fast digital signatures and key agreement with tiny keys — a 32-byte Ed25519 key carries security comparable to RSA-3072",
            "reach_when": "signing, identity, attestation, and key exchange — anywhere you must prove authorship or agree a shared secret",
            "not_when": "bulk encryption of data at rest (reach for authenticated symmetric, e.g. AES-GCM/XChaCha20) — and NEVER hand-implement the curve math",
            "connect_via": "an audited library only — libsodium/NaCl, ring, or python 'cryptography'; never a hand-rolled implementation",
            "body": (
                "Ed25519 is deterministic (it needs no per-signature randomness, so it dodges the "
                "catastrophic nonce-reuse failures that have broken ECDSA deployments), fast to verify, "
                "and small on the wire. It is what SSH, TLS 1.3, Signal, and the Narrow Highway covenant "
                "identity already sign with. The tool is not ours to build: the whole point is to DISCERN "
                "that a signature is what the task needs and CONNECT to a trusted implementation. Rolling "
                "your own curve arithmetic is the canonical way to ship a silent, total break — the "
                "cardinal case of 'connect, do not rebuild.'"
            ),
            "conns": [
                ("rests_on", "card_theory_cryptographic_security",
                 "ECC is the applied edge of the cryptographic-security theory (hashing, checksums, PKI) — the tool stands on the theory"),
            ],
        },
        {"id": "card_tool_sha256", "title": "SHA-256 / BLAKE3 cryptographic hashing", "subject": "Cryptographic hashing",
         "category": "cryptography", "tier": "battle-tested standard",
         "good_at": "a fixed-size, collision-resistant fingerprint of any input — same bytes always hash the same, different bytes practically never collide",
         "reach_when": "integrity checks, content-addressing, commitments, deduplication, and signing (you sign the hash, not the message)",
         "not_when": "passwords — use a slow KDF (Argon2/bcrypt); and it is not encryption (it is one-way)",
         "connect_via": "stdlib hashlib; BLAKE3's library when you need speed",
         "body": "A hash turns arbitrary data into a short fixed fingerprint you can compare and store cheaply. SHA-256 is the conservative default; BLAKE3 is far faster and parallel. The kernel's sealed trail and content-addressed store are built on exactly this.",
         "conns": [("rests_on", "card_theory_cryptographic_security", "hashing is a pillar of the cryptographic-security theory"),
                   ("complements", "card_tool_ecc_ed25519", "a signature signs a hash, not the whole message — hashing and ECC work together")]},
        {"id": "card_tool_aes_gcm", "title": "Authenticated symmetric encryption (AES-GCM / XChaCha20-Poly1305)", "subject": "Authenticated encryption",
         "category": "cryptography", "tier": "battle-tested standard",
         "good_at": "fast confidentiality AND integrity together — encrypt-then-authenticate in one AEAD step",
         "reach_when": "encrypting bulk data at rest or in transit once a key is agreed",
         "not_when": "agreeing that key or proving authorship (use ECC) — and never reuse a nonce",
         "connect_via": "libsodium/NaCl, ring, or python 'cryptography'; never hand-roll the mode",
         "body": "AEAD ciphers encrypt and authenticate in one pass, so tampering is caught on decrypt. XChaCha20-Poly1305 tolerates random nonces; AES-GCM is hardware-accelerated. Pair with ECC: the curve agrees the key, the AEAD encrypts the payload.",
         "conns": [("rests_on", "card_theory_cryptographic_security", "symmetric AEAD is the confidentiality half of applied cryptography"),
                   ("complements", "card_tool_ecc_ed25519", "ECC agrees or wraps the key; AES-GCM encrypts the bulk")]},
    ],
    "data": [
        {"id": "card_tool_sqlite_fts5", "title": "SQLite + FTS5 (embedded SQL & full-text search)", "subject": "SQLite",
         "category": "data", "tier": "battle-tested standard",
         "good_at": "a complete SQL database and full-text search engine in a single file — zero config, no server",
         "reach_when": "local, sovereign, offline-capable storage and search — exactly the kernel's shards",
         "not_when": "many concurrent writers or horizontal scale-out (reach for a server DB then)",
         "connect_via": "the stdlib sqlite3 module (FTS5 compiled in); read-only shards open immutable=1",
         "body": "SQLite is the most-deployed database on earth because it is a file, not a service — it fits the sovereign, no-account, runs-offline constraint. FTS5 gives BM25-ranked full-text search in the same file.",
         "conns": [("rests_on", "card_theory_boolean_algebra_propositional_logic", "SQL queries are relational algebra over boolean predicates")]},
    ],
    "connectivity": [
        {"id": "card_tool_mcp", "title": "Model Context Protocol (MCP)", "subject": "MCP",
         "category": "connectivity", "tier": "emerging standard",
         "good_at": "a universal, typed protocol connecting a model to external tools, data and prompts — one interface instead of N bespoke integrations",
         "reach_when": "giving an agent governed access to a capability WITHOUT rebuilding it — the discern-and-connect move made concrete",
         "not_when": "a single hard-wired call is genuinely simpler and won't be reused",
         "connect_via": "an MCP server exposing tools + an MCP client in the host; JSON-RPC over stdio or HTTP",
         "body": "MCP is the fascia of the tool concordance: the kernel reaches any conforming tool through one typed door, so 'connect, don't rebuild' has a standard to ride. The concordance already speaks it.",
         "conns": [("complements", "card_tool_ecc_ed25519", "MCP carries the calls; signatures and identity secure them")]},
    ],
}

_CAT_BANDS = {
    "cryptography": ["cryptography", "security"],
}


def _ids_in(path: Path) -> set[str]:
    ids = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    ids.add(json.loads(line)["id"])
                except (ValueError, KeyError):
                    pass
    return ids


def _spine_card() -> dict:
    return {
        "id": SPINE_ID, "kind": "reference",
        "title": "The tools the work reaches for",
        "body": ("The discernment registry: every tool given its due — what it is good at, when to "
                 "reach for it, when not, and how to connect to it. We do not build every tool; we "
                 "discern which to reach for, connect to it, and keep incorporating the best."),
        "source": {"label": "The Tool Concordance", "url": "", "domain": "", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine", "bands": ["tools", "concordance", "discernment", "spine"],
        "subject": "the tools", "connections": [],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def build_card(cat: str, d: dict) -> dict:
    body = (f"{d['title']} — {cat}. GOOD AT: {d['good_at']}. REACH WHEN: {d['reach_when']}. "
            f"NOT WHEN: {d['not_when']}. CONNECT VIA: {d['connect_via']}. {d['body']}")
    conns = [dict(SPINE_CONN)] + [{"to_card_id": t, "relationship": r, "evidence": e} for r, t, e in d["conns"]]
    return {
        "id": d["id"], "kind": "reference", "title": d["title"][:180], "body": body,
        "source": {"label": "The Tool Concordance — discern, connect, incorporate",
                   "url": "", "domain": cat, "authority_tier": d.get("tier", "reference")},
        "shelf": "tools", "box": "tool",
        "bands": ["tool", cat, "concordance"] + _CAT_BANDS.get(cat, []),
        "subject": d["subject"], "connections": conns,
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": {"category": cat, "tier": d.get("tier", ""), "good_at": d["good_at"],
                  "reach_when": d["reach_when"], "not_when": d["not_when"], "connect_via": d["connect_via"]},
    }


def _all_defs():
    out = []
    for cat, items in TOOLS.items():
        for d in items:
            out.append((cat, d))
    return out


def cmd_ledger():
    if not STORE.exists():
        print("no tool cards yet.")
        return 0
    rows = [json.loads(l) for l in STORE.read_text(encoding="utf-8").splitlines() if l.strip()]
    tools = [r for r in rows if r.get("shelf") == "tools"]
    print(f"{'TOOL':40} {'REACH WHEN':46} CONNECT VIA")
    print("-" * 120)
    for r in tools:
        x = r.get("extra") or {}
        rw = (x.get("reach_when") or "")[:44]
        cv = (x.get("connect_via") or "")[:40]
        print(f"{r['title'][:40]:40} {rw:46} {cv}")
    print(f"\n{len(tools)} tools carded. Discern which to reach for; connect, do not rebuild.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", help="seed one tool by id or bare slug (ecc_ed25519 or card_tool_ecc_ed25519)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--ledger", action="store_true")
    args = ap.parse_args()

    if args.ledger:
        return cmd_ledger()

    existing = _ids_in(STORE)
    known = existing | _ids_in(THEORY_STORE) | {SPINE_ID}

    defs = _all_defs()
    if args.tool:
        want = args.tool if args.tool.startswith("card_tool_") else f"card_tool_{args.tool}"
        defs = [(c, d) for c, d in defs if d["id"] == want]
        if not defs:
            print(f"no definition for tool '{args.tool}'")
            return 1
    elif not (args.all or args.check):
        print("give --tool <slug>, --all, --check, or --ledger")
        return 2

    will_exist = known | {d["id"] for _c, d in defs}
    unresolved = [(d["id"], t) for _c, d in defs for r, t, _e in d["conns"] if t not in will_exist]
    for _c, d in defs:
        for r, _t, _e in d["conns"]:
            if r not in REL:
                print(f"bad relationship '{r}' on {d['id']}")
                return 3
    if unresolved:
        print("UNRESOLVED connection targets (fix before seeding):")
        for s, t in unresolved:
            print(f"   {s}  ->  {t}")
        return 3

    new = [(c, d) for c, d in defs if d["id"] not in existing]
    if args.check:
        print(f"OK: {len(defs)} tool cards planned, {len(new)} new, all connection targets resolve.")
        return 0
    if not new and existing:
        print("nothing to add — planned tools already present (idempotent).")
        return 0

    STORE.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if SPINE_ID not in existing:
        lines.append(json.dumps(_spine_card(), ensure_ascii=False))
    for c, d in new:
        lines.append(json.dumps(build_card(c, d), ensure_ascii=False))
    with STORE.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"appended {len(new)} tool card(s)" + (" + spine" if SPINE_ID not in existing else "") + f" -> {STORE}")
    for c, d in new:
        print(f"   + [{c}] {d['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
