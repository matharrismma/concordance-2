"""THE FILING CABINET — which drawer is this card in, what is in each drawer, and what should move.

Matt, 2026-08-01: *"Make sure we are creating Filing cabinets and maps. That could be the reason
these are getting confusing. We should think of it like a giant dewey decimal system of cards.
Links to other cards and source files."* And: *"They continuously improve, expanding and
contracting. Reorganizing cards to the optimal system."*

HE WAS RIGHT, AND THE MEASUREMENT SAYS WHY. `address.py` already gives every card a faceted
Dewey-style coordinate — that part was built. What was missing is the CABINET the drawers sit in.
Nine separate stores hold cards and nothing declared that they exist together. Measured on the
box, 2026-08-01:

    25,087   data/cards.jsonl            the RESIDENT corpus (what a process loads)
   551,754   data/shards/*.db (x6)       the WHOLE keeping — ~96% of cards live ONLY here
        22   data/web_cache.jsonl        what the tortoise fetched on a call
         2   data/acquired_cards.jsonl   what the shepherd's choose minted
         -   data/shelves/drops.jsonl    what members wrote, signed by their own key

EVERY FILING FAILURE OF 2026-08-01 FOLLOWS FROM THAT ONE ABSENCE, and there were five in a day:

  * `curate()` searched drops.jsonl and answered "no such drop" for a card sitting in web_cache
  * `review_queue()` read one drawer, so three held acquisitions were invisible to every human
  * `repoint_citations` fixed cards.jsonl and missed the shards — 4,039 citations silently unfixed
  * the shepherd wrote acquired_cards.jsonl while the tortoise wrote web_cache.jsonl, same job
  * `_conn` cached a shard by NAME not path and served the wrong file with no error

None of those is a coding mistake. Each is someone reaching into the one drawer they knew about.
A registry that lives in CODE, that every reader consults, is the cure — and `tools/divergence.py`
exists precisely because drawers can disagree, which is a cabinet's problem, not a card's.

THREE DISCIPLINES, inherited from the address and kept here:

  * **DECLARED, not discovered.** A drawer nobody wrote down is a drawer nobody searches. Adding a
    store means adding it HERE, and the test that walks `data/` fails if a new one appears unlisted.
  * **PROPOSE, NEVER REWRITE.** `reorganize()` returns a mapping for a person to read. Matt's rule
    on the 69 near-empty shelves — *"propose the mapping FIRST, never rewrite silently"* — is the
    law here: a cataloguer who moves 100,000 cards on a heuristic has destroyed the trail.
  * **DISAGREEMENT IS THE FINDING.** When one card is in two drawers with different content, that
    is not an error to resolve quietly — it is exactly what we want to be told.

The cabinet is a VIEW. It moves nothing, owns nothing, and `member_of` remains the load-bearing
tree (zero orphans). Stdlib only.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── THE DRAWERS ────────────────────────────────────────────────────────────────────────────────
# `canonical` says whether a repair must REACH this drawer, or whether it is rebuilt from another.
#
# I GOT THIS WRONG ON THE FIRST WRITING, and the cabinet is what caught it. I declared the shards
# "a COPY of the keeping, rebuilt never patched" — the story I had carried all day. Then I counted,
# on the box: cards.jsonl holds 25,087 and the shards hold 551,754. You cannot rebuild 551,754
# cards from a file of 25,087. And a frozen-shelf card sampled from both came back IDENTICAL —
# full body, same connections — so it is not a stub-and-body split either.
#
# The measured truth is that they PARTITION WITH OVERLAP: cards.jsonl is the resident corpus (what
# a process loads into memory), the shards hold the whole keeping, and ~96% of cards exist ONLY in
# the shards. So the shards are canonical for almost everything, and treating them as a disposable
# copy is precisely the belief that let 4,039 repointed citations be reported as fixed while the
# shard still served the old text.
#
# Both are canonical. `where_is` is what tells you which drawers a given card is actually in, and
# whether they agree — a question no belief about the architecture can answer for you.
DRAWERS: List[Dict[str, Any]] = [
    {"name": "keeping", "kind": "jsonl", "path": "cards.jsonl", "canonical": True,
     "holds": "the RESIDENT corpus — the subset a running process loads into memory"},
    {"name": "shards", "kind": "sqlite", "path": "shards", "canonical": True,
     "holds": "the WHOLE keeping, read from disk; ~96% of all cards live only here"},
    {"name": "acquired-web", "kind": "jsonl", "path": "web_cache.jsonl", "canonical": True,
     "holds": "public-domain sources the tortoise fetched on a call"},
    {"name": "acquired-choose", "kind": "jsonl", "path": "acquired_cards.jsonl", "canonical": True,
     "holds": "sources a person chose at the shepherd's comb"},
    {"name": "shelves", "kind": "jsonl", "path": "shelves/drops.jsonl", "canonical": True,
     "holds": "what members wrote, signed by their own key"},
]


def _data() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def _iter_jsonl(p: Path):
    if not p.exists():
        return
    try:
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    yield json.loads(ln)
                except ValueError:
                    continue
    except OSError:
        return


def _shard_files() -> List[Path]:
    d = _data() / "shards"
    return sorted(d.glob("*.db")) if d.is_dir() else []


def drawers() -> List[Dict[str, Any]]:
    """Every declared drawer, with whether it is actually present on this device.

    A phone carries the keeping and no shards; the box carries both. Absent is not missing.
    """
    out = []
    for d in DRAWERS:
        rec = dict(d)
        if d["kind"] == "sqlite":
            files = _shard_files()
            rec["present"] = bool(files)
            rec["files"] = [f.name for f in files]
        else:
            rec["present"] = (_data() / d["path"]).exists()
        out.append(rec)
    return out


def where_is(card_id: str) -> Dict[str, Any]:
    """Every drawer holding this card — and whether they agree.

    THE QUESTION NOBODY COULD ASK BEFORE. `curate` answered "no such drop" because it looked in
    one drawer; the repair tools fixed one and left another stale. One card in two drawers with
    DIFFERENT content is not an error to smooth over — it is the finding.
    """
    cid = (card_id or "").strip()
    if not cid:
        return {"card_id": cid, "found_in": [], "error": "which card?"}
    found: List[Dict[str, Any]] = []
    for d in DRAWERS:
        if d["kind"] == "jsonl":
            for c in _iter_jsonl(_data() / d["path"]):
                if c.get("id") == cid:
                    found.append({"drawer": d["name"], "canonical": d["canonical"],
                                  "stage": c.get("lifecycle_stage"), "shelf": c.get("shelf"),
                                  "title": c.get("title"), "fingerprint": _fingerprint(c)})
        else:
            for f in _shard_files():
                try:
                    conn = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
                    row = conn.execute("select json from cards where id = ?", (cid,)).fetchone()
                    conn.close()
                except sqlite3.Error:
                    continue
                if row:
                    try:
                        c = json.loads(row[0])
                    except ValueError:
                        continue
                    found.append({"drawer": f"shards/{f.stem}", "canonical": False,
                                  "stage": c.get("lifecycle_stage"), "shelf": c.get("shelf"),
                                  "title": c.get("title"), "fingerprint": _fingerprint(c)})
    prints = {f["fingerprint"] for f in found}
    return {"card_id": cid, "found_in": found, "count": len(found),
            "agree": len(prints) <= 1,
            "note": ("in more than one drawer with DIFFERENT content — the copy is stale, rebuild "
                     "it from its canonical drawer rather than patching it"
                     if len(prints) > 1 else "")}


def _fingerprint(card: dict) -> str:
    """What must match for two copies to be the same card — not the whole blob, which carries
    timestamps that differ harmlessly."""
    import hashlib
    src = card.get("source") or {}
    material = json.dumps({"title": card.get("title"), "body": card.get("body"),
                           "shelf": card.get("shelf"),
                           "url": src.get("url") if isinstance(src, dict) else str(src),
                           "stage": card.get("lifecycle_stage")},
                          sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def census() -> Dict[str, Any]:
    """What is in each drawer, and on which shelf — the map, measured rather than remembered."""
    per_drawer: Dict[str, int] = {}
    shelves: Dict[str, int] = {}
    unplaced = 0
    addressed = 0

    # A SWALLOWED CALL REPORTS A FALSE ZERO. The first version wrapped this in a bare `except` and
    # called `address_of`, which does not exist — the real entry point is `derive`. Every card
    # raised, every raise was eaten, and the census printed "0 UNPLACED" over a check that had
    # never run once. `unplaced` now travels with `addressed`, so a zero can be read as "none, out
    # of 22,037 examined" rather than "none, out of nothing".
    from . import address as _addr

    for d in DRAWERS:
        if d["kind"] == "jsonl":
            n = 0
            for c in _iter_jsonl(_data() / d["path"]):
                n += 1
                shelves[c.get("shelf") or "(none)"] = shelves.get(c.get("shelf") or "(none)", 0) + 1
                addr, _why = _addr.derive(c)
                addressed += 1
                if addr == _addr.UNPLACED:
                    unplaced += 1
            per_drawer[d["name"]] = n
        else:
            total = 0
            for f in _shard_files():
                try:
                    conn = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
                    total += conn.execute("select count(*) from cards").fetchone()[0]
                    conn.close()
                except sqlite3.Error:
                    continue
            per_drawer[d["name"]] = total
    return {"drawers": per_drawer, "shelves": shelves,
            # ALWAYS TOGETHER: a count of misfiled cards is meaningless without the
            # number examined. "0 unplaced" over 0 examined is not good news.
            "unplaced": unplaced, "addressed": addressed,
            "total": sum(per_drawer.values())}


# ── EXPANDING AND CONTRACTING ──────────────────────────────────────────────────────────────────
# Matt: "They continuously improve, expanding and contracting. Reorganizing cards to the optimal
# system." A shelf is a drawer label, and labels go wrong in two directions: one grows until it
# means nothing ("connections", 16,909 cards, which is not a subject), and others shrink until
# they are noise a reader has to step over ("atlas", 3).
OVERFULL = 1000      # above this a label has stopped narrowing anything
THIN = 10            # below this a label costs more attention than it saves


def reorganize() -> Dict[str, Any]:
    """PROPOSE a better filing — split what is overfull, merge what is thin. Moves nothing.

    Matt's standing rule on the near-empty shelves: *"propose the mapping FIRST, never rewrite
    silently."* A cataloguer who moves a hundred thousand cards on a heuristic has destroyed the
    trail that made them trustworthy, and the assay that flagged 157,130 verses on one bad rule is
    why report-only comes first here too.

    The proposal names the RULE it applied, so a person can disagree with the rule rather than
    argue with a list.
    """
    c = census()
    shelves = c["shelves"]
    split = [{"shelf": k, "cards": v,
              "why": f"{v:,} cards under one label — it has stopped narrowing anything",
              "rule": f"cards >= {OVERFULL}"}
             for k, v in sorted(shelves.items(), key=lambda x: -x[1]) if v >= OVERFULL]
    merge = [{"shelf": k, "cards": v,
              "why": f"only {v} card(s) — a label a reader must step over",
              "rule": f"cards < {THIN}"}
             for k, v in sorted(shelves.items(), key=lambda x: x[1]) if v < THIN]
    return {
        "expand": split, "contract": merge,
        "shelves": len(shelves), "total_cards": c["total"],
        "note": ("A PROPOSAL, not a change. Nothing here has been moved. Splitting needs a "
                 "human to say what the new labels MEAN; merging needs one to confirm the small "
                 "shelf is not small because it is precious."),
    }


__all__ = ["DRAWERS", "drawers", "where_is", "census", "reorganize", "OVERFULL", "THIN"]
