"""CARD CORRECTIONS — tracked, field-level corrections applied to cards as the keeping loads.

2026-11-23. Two corrections Matt directed, applied the way the bridge overlays are (corpus._apply_bridges):
the box's card files are box-owned data and are never rewritten or deployed; the correction lives here, in
code, reviewed and versioned, and is applied to the in-memory card on every load.

  1. "Use the WEB as the user facing content." Twenty-four of his devotionals carried "NKJV" in their
     reference, bands and subject, and two sermons in their body ("Main Text: 1 Peter 5:9–11 NKJV"). The
     verse a reader is shown is the World English Bible (verifiers/scripture.read_passage); the label now
     says so. His own words are untouched.
  2. "Cut the raven story if it isn't scriptural." The sermon *The Raven and the Dove* loses the sentences
     no held text of Genesis 8 supports (the raven gorging on carcasses, "made for a world of death",
     "created to live on judgment and corruption", the predestination reading, and the section built on
     them). What Scripture says stays: Noah sent a raven; it is an unclean bird; the dove's three sendings.
  3. (2026-11-24) "Yes, correct it." The RAS card (card_n_ras7gate0recv), minted by our own assay on 2026-07-23
     (tools/add_ras_bridge.py), said more than its sources: that the RAS "decides what reaches awareness", that
     the bridge to Matthew 6:22 was CONCORDANT ("we have found it"; the 07-29 null assay had already made it
     RESONANCE), and it quoted Mark 8:18 and Matthew 6:22 in the King James wording. It now says what WordNet and
     the two OpenStax textbooks the keeping holds say — arousal, one part of attention, never the chooser — and
     quotes the WEB. Matt's own cards it links to (the eye devotional, the floor) are untouched.

NO PROSE OF HIS IN THE REPO. A body change never stores his text: it names the sha256 of the body it expects and
the character spans to cut from that exact body, `spans: [[start, end, replacement], ...]`, where a replacement is
"" or a Scripture reference (" (Leviticus 11:15)"). Field changes store only references and tags. The one
exception is OUR OWN wording on text OUR OWN TRACKED TOOL MINTED: such a row names `minted_by` (the tool file and
the constant holding the body), and the table test checks that the body hash the row expects IS that constant's —
text already public in this repo, never his. The `author` field cannot say whose a card is (33 devotionals and 80
parables carry "operator", as the RAS card does; corrected 2026-11-24 after 1876410 claimed it could). `expects`
is only an extra fail-closed pin on fields the card must still hold.

FAIL-CLOSED. Every entry names the value it expects to find. A card whose current value differs — a box copy
that has moved on, a regenerated file — is left exactly as it is and counted as `mismatch`; a card is never
half-corrected. Each corrected card carries `corrected: [{rule, date, directive}]`, so the change travels with
its provenance. The table is card_corrections.json beside this file; both are in the corpus cache key
(corpus.default_corpus), so editing either rebuilds the cache instead of serving a stale corpus.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

TABLE_PATH = Path(__file__).with_name("card_corrections.json")
_TABLE: Dict[str, Any] = {"mtime": None, "rows": []}


def _sha(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def table() -> List[dict]:
    """The correction rows (re-read when the file changes); [] when the file is absent or unreadable."""
    try:
        mtime = TABLE_PATH.stat().st_mtime_ns
    except OSError:
        return []
    if _TABLE["mtime"] != mtime:
        try:
            rows = (json.loads(TABLE_PATH.read_text(encoding="utf-8")) or {}).get("corrections") or []
        except (OSError, ValueError):
            rows = []
        _TABLE.update({"mtime": mtime, "rows": [r for r in rows if isinstance(r, dict) and r.get("id")]})
    return _TABLE["rows"]


def _get(card: dict, path: str) -> Any:
    cur: Any = card
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def _set(card: dict, path: str, value: Any) -> None:
    keys = path.split(".")
    cur = card
    for k in keys[:-1]:
        if not isinstance(cur.get(k), dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value


def _matches(card: dict, change: dict) -> bool:
    cur = _get(card, change["path"])
    if "old_sha256" in change:
        return isinstance(cur, str) and _sha(cur) == change["old_sha256"]
    return cur == change.get("old")


def _new_value(cur: Any, change: dict) -> Any:
    """`new` when the change states it; else the current string with its `spans` cut, right to left, from the
    exact text whose hash was just checked — so the offsets are the offsets of THAT text and nothing else."""
    if "new" in change:
        return change["new"]
    s = cur if isinstance(cur, str) else ""
    for start, end, rep in sorted(change.get("spans") or [], key=lambda x: -int(x[0])):
        s = s[:int(start)] + str(rep) + s[int(end):]
    return s


def apply_one(card: Optional[dict], rows: Optional[List[dict]] = None) -> str:
    """Correct one card in place. Returns 'applied', 'already', 'mismatch' or 'none' (no row for it)."""
    if not isinstance(card, dict):
        return "none"
    for row in (rows if rows is not None else table()):
        if row.get("id") != card.get("id"):
            continue
        done = {c.get("rule") for c in (card.get("corrected") or []) if isinstance(c, dict)}
        if row.get("rule") in done:
            return "already"
        if not all(_get(card, p) == v for p, v in (row.get("expects") or {}).items()):
            return "mismatch"                 # `expects`: fields the card must still hold, fail closed (not who wrote it)
        changes = row.get("changes") or []
        if not changes or not all(_matches(card, ch) for ch in changes):
            return "mismatch"                 # fail closed: the card is left exactly as it is
        for ch in changes:
            _set(card, ch["path"], _new_value(_get(card, ch["path"]), ch))
        card.setdefault("corrected", []).append({"rule": row.get("rule"), "date": row.get("date"),
                                                 "directive": row.get("directive")})
        return "applied"
    return "none"


def apply(cards: Dict[str, dict]) -> Dict[str, Any]:
    """Apply every row to the resident cards. Returns {rows, applied, already, mismatch, absent, mismatched}."""
    rows = table()
    st: Dict[str, Any] = {"rows": len(rows), "applied": 0, "already": 0, "mismatch": 0, "absent": 0,
                          "mismatched": []}
    by_id: Dict[str, List[dict]] = {}
    for r in rows:
        by_id.setdefault(r["id"], []).append(r)
    for cid, rs in by_id.items():
        card = cards.get(cid)
        if card is None:
            st["absent"] += len(rs)          # frozen or not on this node: rehydrate() corrects a frozen one on read
            continue
        for r in rs:
            res = apply_one(card, [r])
            if res in ("applied", "already", "mismatch"):
                st[res] += 1
                if res == "mismatch" and len(st["mismatched"]) < 10:
                    st["mismatched"].append(cid)
    return st
