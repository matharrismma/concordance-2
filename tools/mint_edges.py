#!/usr/bin/env python3
"""Harvest the map — mint sealed connection cards from the keeping's real semantic edges.

Matt: "Run the harvest." And: "Let the work define the structure." The map (graph.py) renders only
`kind:connection` cards; but the living connection structure of the keeping is carried INLINE on each
card's `connections[]`. This mints the inline SEMANTIC edges (cites, proof-texts, shared sections and
families, the two-tree grafts, shared Scripture…) as content-addressed connection cards, so the map
reflects the whole keeping — found, never invented, each a re-checkable sealed record.

Deliberately EXCLUDED: the `member_of` / nesting backbone (460k edges). That is the SKELETON — the
floor tree already walks it. Dumping it on the constellation would bury every idea under a spine-hub
hairball. The map is the web of ideas; the floor is the skeleton. Two views, one keeping.

0-FP + idempotent: each edge is content-addressed from its (endpoints, relationship); re-running skips
what already exists (both the legacy minted cards and this file). Both endpoints must be public nodes.
Output is additive and reversible — a separate git-ignored file, never mutating cards.jsonl.

    PYTHONPATH=src python tools/mint_edges.py --check      # measure, write nothing
    PYTHONPATH=src python tools/mint_edges.py --apply
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from concordance import corpus  # noqa: E402

# the nesting backbone — the floor tree's job, never the map's (would be a hub hairball)
_SKELETON = {"member_of", "has_member", "part_of", "has_part", "nested_in", "contains",
             "figure_of", "has_figure"}
# how each surviving (semantic) relationship reads in a human sentence
_HUMAN = {
    "cites": "cites", "proof_text": "is a proof-text for", "same_section": "shares a section with",
    "same_family": "shares a family with", "names_the_created_thing": "names the created thing",
    "shares_scripture": "shares Scripture with", "illuminates": "illuminates",
    "demonstrates": "demonstrates", "paves": "paves the way to", "kindred": "is kindred to",
    "adjacent": "is adjacent to", "precedes": "precedes", "related": "is related to",
    "see_also": "see also", "points_beyond_itself": "points beyond itself to",
}


def _out_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "minted_edges.jsonl"


def _key(a: str, b: str, rel: str) -> str:
    lo, hi = sorted((a, b))
    return hashlib.blake2b(f"{lo}|{hi}|{rel}".encode("utf-8"), digest_size=6).hexdigest()


def main() -> int:
    apply = "--apply" in sys.argv
    cards = corpus.default_corpus().cards
    public = {cid for cid, c in cards.items() if corpus.is_public(c)}

    # every edge already represented as a connection card — so we never double-mint
    seen: set = set()
    for c in cards.values():
        if c.get("kind") != "connection":
            continue
        ex = c.get("extra") or {}
        a, b = ex.get("left_card_id"), ex.get("right_card_id")
        rel = ex.get("relationship_kind") or "see_also"
        if a and b:
            seen.add((frozenset((a, b)), rel))

    minted, skipped_skel, skipped_dup, skipped_priv = [], 0, 0, 0
    for cid, c in cards.items():
        if c.get("kind") == "connection" or cid not in public:
            continue
        for l in (c.get("connections") or []):
            if not isinstance(l, dict):
                continue
            b = l.get("to_card_id")
            rel = l.get("relationship") or "see_also"
            if not b or b == cid:
                continue
            if rel in _SKELETON:
                skipped_skel += 1
                continue
            if b not in public:
                skipped_priv += 1
                continue
            k = (frozenset((cid, b)), rel)
            if k in seen:
                skipped_dup += 1
                continue
            seen.add(k)
            ta = (c.get("title") or cid)[:70]
            tb = (cards[b].get("title") or b)[:70]
            phrase = _HUMAN.get(rel, rel.replace("_", " "))
            ev = l.get("evidence") or ""
            minted.append({
                "id": f"card_c_m_{_key(cid, b, rel)}", "kind": "connection",
                "title": f"{ta} {phrase} {tb}"[:180],
                "body": (ev or f"{ta} {phrase} {tb}."),
                "source": {"label": "Found in the keeping", "url": "", "ref": ev,
                           "authority_tier": "engine_derived"},
                "shelf": "connections", "box": rel,
                "bands": ["connection", "found", rel],
                "connections": [{"to_card_id": cid, "relationship": "see_also"},
                                {"to_card_id": b, "relationship": "see_also"}],
                "extra": {"left_card_id": cid, "right_card_id": b, "relationship_kind": rel,
                          "evidence": ev},
                "author": "engine", "created_at": 0.0, "updated_at": 0.0,
                "visibility": "public", "lifecycle_stage": "public",
                "volatility": "permanent", "surface": "secular", "generated": False,
            })

    print(f"  existing minted (legacy) edges: {len(seen) - len(minted):,}")
    print(f"  new semantic edges to mint:     {len(minted):,}")
    print(f"  skipped — skeleton/nesting:     {skipped_skel:,}")
    print(f"  skipped — already a connection: {skipped_dup:,}")
    print(f"  skipped — private endpoint:     {skipped_priv:,}")
    from collections import Counter
    by = Counter(m["box"] for m in minted)
    print("  by relationship:", ", ".join(f"{r}:{n}" for r, n in by.most_common(10)))

    if not apply:
        print("  --check: nothing written (pass --apply)")
        return 0
    out = _out_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for m in minted:
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")
    os.replace(tmp, out)
    print(f"  wrote {len(minted):,} sealed connection cards -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
