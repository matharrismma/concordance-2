"""The ops log — operational events recorded with the same discipline as the keeping.

Task #104: CARD EVERY PIECE — operational objects into the keeping + ops log discipline.
And GAPS.md G1's stated fix, verbatim: "publish both numbers in `capabilities` and the ops log,
every time the count is claimed."

WHY A COUNT NEEDS TWO NUMBERS. Measured 2026-07-29: 228,697 of 496,559 cards (46.1%) have bodies
under 120 characters — stubs. Stubs are legitimate by design (stub+link, the lazy Hare), but a
single headline count lets the million-card goal be hit without adding a sentence of substance.
That would be a count, not a library. So the count is never claimed alone: every claim carries
total, substance, stubs, and the ratio, with the threshold that defined them. A card whose body
is a pointer is inventory; a card that answers something is stock.

THE DISCIPLINE LIVES IN CODE; THE RECORDS LIVE IN DATA. The schema, the stub threshold, and the
meaning of every field are defined here, in a tracked file, so a fresh box carries the same
discipline. The log itself is operational data and goes to the data directory, like the ledger.

CARD EVERY PIECE. Every record can be rendered as a card (`to_card`) — same shape as the rest of
the keeping, generated=False, the event stated plainly. Merging ops cards into the shared corpus
is a steward's CHOICE (ask before writes), never automatic; the helper exists so the choice is
one call, not a format project.

Sovereign: stdlib only. A log that silently drops a record is a lie to the next reader, so IO
failures raise — they are never swallowed.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

# The G1 threshold, from the measured register (docs/GAPS.md). A body under this many characters
# is a pointer, not an answer. Changing this number changes what "substance" means everywhere the
# count is claimed — which is exactly why it is a named constant in code and not a literal.
STUB_BODY_CHARS = 120

_LOG_NAME = "ops_log.jsonl"


def _log_path() -> Path:
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / _LOG_NAME


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def substance(cards: Mapping[str, dict]) -> Dict[str, Any]:
    """The two-number count: total, substance, stubs, ratio — with its own definitions attached.

    Pure function over an explicit mapping, so it can be measured against any card set (the live
    singleton, a fixture, a shard) and so its tests never depend on which corpus a sibling test
    left loaded. Connection cards are edges, not holdings, and are excluded from all three counts.
    """
    total = 0
    stubs = 0
    frozen = 0
    for c in cards.values():
        if c.get("kind") == "connection":
            continue
        total += 1
        # A FROZEN card's body lives on its SQLite shard; in memory it is deliberately stripped
        # to a stub so the graph stays resident and the weight stays on disk. Measuring its
        # in-memory body length would report a full card as a stub — which is exactly what the
        # first deploy of this function did on the live box: 91% "stubs" against G1's measured
        # 46%, because most shelves there are frozen. Our load strategy is not the keeping's
        # substance. Frozen cards are counted as their own bucket, judged by nobody.
        if c.get("frozen"):
            frozen += 1
        elif len(str(c.get("body") or "")) < STUB_BODY_CHARS:
            stubs += 1
    measured = total - frozen
    sub = measured - stubs
    return {
        "total": total,
        "substance_cards": sub,
        "stub_cards": stubs,
        "frozen_cards": frozen,
        "measured_cards": measured,
        "stub_ratio": round(stubs / measured, 4) if measured else 0.0,
        "stub_threshold_chars": STUB_BODY_CHARS,
        "means": {
            "total": "cards excluding connection edges",
            "substance_cards": f"measured cards whose body is >= {STUB_BODY_CHARS} chars — they answer something",
            "stub_cards": f"measured cards whose body is < {STUB_BODY_CHARS} chars — a pointer, not an answer",
            "frozen_cards": ("cards whose body lives on a shard, not in memory — NOT judged; "
                             "counting a frozen card as a stub would report our load strategy "
                             "as the library's poverty"),
            "measured_cards": "total minus frozen — the only cards this walk could honestly judge",
            "stub_ratio": "stub_cards / measured_cards; the number G1 requires beside every count claim",
        },
    }


_SUBSTANCE_CACHE: Optional[Dict[str, Any]] = None


def substance_of_the_keeping() -> Dict[str, Any]:
    """substance() over the live corpus singleton, memoized per process.

    Walking 548k bodies costs real time, and a public endpoint must not pay it per request —
    reading must not knock out proving. The corpus is immutable under a running service, so one
    walk is honest for the process lifetime. If the corpus is empty or unloadable this REPORTS
    that as coverage rather than returning zeros dressed as a measurement.
    """
    global _SUBSTANCE_CACHE
    if _SUBSTANCE_CACHE is None:
        try:
            from . import corpus
            cards = corpus.default_corpus().cards
        except Exception:                                     # noqa: BLE001 — degrade honestly
            cards = {}
        s = substance(cards)
        if s["total"] == 0:
            s["coverage"] = "EMPTY — no corpus loaded in this process; these are not counts of the keeping"
        _SUBSTANCE_CACHE = s
    return _SUBSTANCE_CACHE


def log(event: str, **fields: Any) -> Dict[str, Any]:
    """Append one operational record. Returns the record as written.

    Raises on IO failure on purpose: an ops log that silently drops records reports a calmer
    history than the one that happened.
    """
    if not str(event).strip():
        raise ValueError("an ops record needs an event name")
    rec: Dict[str, Any] = {"ts": _utc(), "event": str(event).strip(), **fields}
    p = _log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    return rec


def claim_count(cards: Mapping[str, dict], *, where: str) -> Dict[str, Any]:
    """Claim a corpus count THE ONLY WAY a count may be claimed: with its substance split, logged.

    `where` names the surface making the claim (a page, an endpoint, a report), so the log shows
    every place a number reached a reader and what that number actually said.
    """
    s = substance(cards)
    log("count_claimed", where=where,
        total=s["total"], substance_cards=s["substance_cards"],
        stub_cards=s["stub_cards"], stub_ratio=s["stub_ratio"])
    return s


def tail(n: int = 50) -> List[Dict[str, Any]]:
    """The last n records, oldest first. Missing log -> empty list (a new box has no history yet)."""
    p = _log_path()
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # a torn line is REPORTED, not skipped silently — coverage over comfort
                out.append({"event": "unreadable_record", "raw": line[:120]})
    return out[-n:]


def to_card(rec: Mapping[str, Any]) -> Dict[str, Any]:
    """Render one ops record as a card — CARD EVERY PIECE, at the mint path.

    The card is fully formed (id, shelf, nesting via member_of the ops spine, generated=False)
    so that merging it into the keeping is a single steward decision, not a format project.
    Nothing here writes to the corpus: agents ask before writes.
    """
    import hashlib
    ev = str(rec.get("event") or "event")
    ts = str(rec.get("ts") or "")
    detail = ", ".join(f"{k}={rec[k]}" for k in sorted(rec) if k not in ("event", "ts"))
    h = hashlib.sha256(json.dumps(dict(rec), sort_keys=True, default=str).encode()).hexdigest()[:12]
    return {
        "id": f"card_ops_{ev}_{h}",
        "kind": "ops",
        "shelf": "operations",
        "title": f"Ops: {ev} at {ts}",
        "body": f"Operational record — {ev} at {ts}. {detail}".strip(),
        "generated": False,
        "source": {"authority_tier": "engine", "ref": _LOG_NAME},
        "connections": [{"to_card_id": "card_spine_operations", "relationship": "member_of",
                         "evidence": "an operational record kept on the operations shelf"}],
    }
