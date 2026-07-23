"""Growth — the standing engine by which the keeping improves itself, never regressing.

The assay proved the engine can discern one thing at a time. This makes discernment continuous:
a re-runnable cycle that MEASURES where the keeping is thin, PROPOSES only evidence-backed
improvements, and RECORDS every action so drift is chartable and nothing is done twice.

Three disciplines, load-bearing:

* **It reveals, it never invents.** A growth edge is a fact already in the data — two cards that
  name the SAME scripture — surfaced, not generated. The engine eliminates and connects what is
  there; it does not author. (Conduit, not source.)
* **0-FP or nothing.** A false connection is worse than a missing one. The gate joins two cards
  only on a shared, normalized scripture reference that is RARE enough to be specific — a hub
  verse everyone cites is low signal and is skipped. No guess is ever applied.
* **It serves; it does not rule.** `measure()` is a steering instrument for the keeper — it says
  where the map is thin and asks a person where to point. The engine cannot be the idol: it only
  shows what already holds.

Pure functions over a passed-in card list (the CLI supplies the real corpus; tests supply small
sets). Nothing here mutates a file — `tools/grow.py` owns the atomic, idempotent write.
"""
from __future__ import annotations

import json
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

_REF = re.compile(r"\b([1-3]?\s?[A-Za-z][A-Za-z.]{1,}\.?)\s+(\d{1,3}):(\d{1,3})\b")

# canonical book forms so " Matt 28:19", "Matt. 28:19", "Matthew 28:19" all join as one verse
_BOOK = {
    "matt": "Matthew", "mt": "Matthew", "matthew": "Matthew", "mrk": "Mark", "mk": "Mark",
    "mark": "Mark", "luk": "Luke", "lk": "Luke", "luke": "Luke", "jn": "John", "joh": "John",
    "john": "John", "act": "Acts", "acts": "Acts", "rom": "Romans", "romans": "Romans",
    "gen": "Genesis", "genesis": "Genesis", "exo": "Exodus", "exod": "Exodus", "exodus": "Exodus",
    "psa": "Psalm", "psalm": "Psalm", "psalms": "Psalm", "isa": "Isaiah", "isaiah": "Isaiah",
    "heb": "Hebrews", "hebrews": "Hebrews", "rev": "Revelation", "revelation": "Revelation",
    "1cor": "1 Corinthians", "2cor": "2 Corinthians", "1john": "1 John", "2john": "2 John",
    "3john": "3 John", "gal": "Galatians", "eph": "Ephesians", "phil": "Philippians",
    "col": "Colossians", "1pet": "1 Peter", "2pet": "2 Peter", "jas": "James", "james": "James",
}


def norm_ref(book: str, ch: str, vs: str) -> str:
    key = re.sub(r"[\s.]", "", book).lower()
    return f"{_BOOK.get(key, book.strip())} {int(ch)}:{int(vs)}"


def refs_of(card: Dict[str, Any]) -> Set[str]:
    """Every distinct, normalized verse a card names — in its source ref, bands, or title."""
    hay = " ".join([str((card.get("source") or {}).get("ref", "")),
                    " ".join(card.get("bands") or []), str(card.get("title", ""))])
    return {norm_ref(m.group(1), m.group(2), m.group(3)) for m in _REF.finditer(hay)}


def _links(card: Dict[str, Any]) -> List[Dict[str, Any]]:
    return card.get("connections") or card.get("links") or []


def _is_public(card: Dict[str, Any]) -> bool:
    return str(card.get("visibility", "public")) == "public"


def measure(cards: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """The steering report: how large, how connected, where thin, and how much safe growth is
    still available to draw. Deterministic — same corpus, same numbers."""
    cards = list(cards)
    n = len(cards)
    orphans = sum(1 for c in cards if not _links(c))
    shelves = Counter(c.get("shelf") for c in cards)
    with_ref = sum(1 for c in cards if refs_of(c))
    available = len(safe_edges(cards, limit=10_000))
    return {
        "ok": True, "cards": n,
        "orphans": orphans, "orphan_pct": round(100 * orphans / n, 2) if n else 0.0,
        "cards_naming_scripture": with_ref,
        "safe_edges_available": available,
        "shelves": dict(shelves.most_common()),
        "note": ("Where the map is thin, and how many evidence-backed connections remain to "
                 "draw. A steering instrument — the keeper decides where to point."),
    }


def safe_edges(cards: Iterable[Dict[str, Any]], *, max_share: int = 6,
               limit: int = 200) -> List[Dict[str, Any]]:
    """0-FP connection proposals: pairs of public cards that name the SAME verse, where that
    verse is RARE (named by <= max_share cards, so it is specific, not a hub everyone cites),
    and are not already linked. Each edge carries the verse as its evidence.

    Deterministic order: rarer verses first (stronger signal), then by card id."""
    cards = [c for c in cards if _is_public(c)]
    by_id = {c.get("id"): c for c in cards}
    verse_cards: Dict[str, List[str]] = defaultdict(list)
    for c in cards:
        for r in refs_of(c):
            verse_cards[r].append(c.get("id"))

    linked: Set[Tuple[str, str]] = set()
    for c in cards:
        a = c.get("id")
        for ln in _links(c):
            b = ln.get("to_card_id")
            if b:
                linked.add((a, b))
                linked.add((b, a))

    proposals: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()
    # rarer shared verses first — a verse two cards share and few others is the strong bridge
    for verse, ids in sorted(verse_cards.items(), key=lambda kv: (len(kv[1]), kv[0])):
        ids = sorted(set(ids))
        if len(ids) < 2 or len(ids) > max_share:
            continue
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                key = (a, b)
                if key in seen or (a, b) in linked:
                    continue
                seen.add(key)
                proposals.append({
                    "a": a, "b": b, "relationship": "shares_scripture", "evidence": verse,
                    "a_title": (by_id[a].get("title") or "")[:60],
                    "b_title": (by_id[b].get("title") or "")[:60],
                })
                if len(proposals) >= limit:
                    return proposals
    return proposals


# ── the ledger: every growth action, so improvement is chartable and never repeated ─────────

def _ledger_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "growth_ledger.jsonl"


def ledger_append(action: str, detail: Dict[str, Any], *, at: float = None) -> None:
    p = _ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    row = {"at": at if at is not None else time.time(), "action": action, **detail}
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def ledger_read(limit: int = 50) -> List[Dict[str, Any]]:
    p = _ledger_path()
    if not p.exists():
        return []
    rows = [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return rows[-limit:]
