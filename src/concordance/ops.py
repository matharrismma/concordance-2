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
import threading
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
        t, s, f = _share(c)
        total += t
        stubs += s
        frozen += f
    return _split(total, stubs, frozen)


def _share(c: Mapping[str, Any]) -> tuple:
    """ONE card's part of substance() — (total, stubs, frozen), each 0 or 1 — so the walk and a live add
    (substance_note) count a card by the one definition."""
    if c.get("kind") == "connection":
        return (0, 0, 0)
    # A FROZEN card's body lives on its SQLite shard; in memory it is deliberately stripped
    # to a stub so the graph stays resident and the weight stays on disk. Measuring its
    # in-memory body length would report a full card as a stub — which is exactly what the
    # first deploy of this function did on the live box: 91% "stubs" against G1's measured
    # 46%, because most shelves there are frozen. Our load strategy is not the keeping's
    # substance. Frozen cards are counted as their own bucket, judged by nobody.
    if c.get("frozen"):
        return (1, 0, 1)
    return (1, 1 if len(str(c.get("body") or "")) < STUB_BODY_CHARS else 0, 0)


def _split(total: int, stubs: int, frozen: int) -> Dict[str, Any]:
    """The two-number count from its three tallies, with its own definitions attached."""
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
# The adds that land while the walk runs — (old dict or None, new dict) — applied when it ends; None when no
# walk is running. Written only under the default corpus's add lock.
_SUBSTANCE_PENDING: Optional[List[tuple]] = None
_SUBSTANCE_WALK = threading.Lock()          # one walk at a time; a second caller waits for its memo
_EMPTY = "EMPTY — no corpus loaded in this process; these are not counts of the keeping"


def _settled(s: Mapping[str, Any], notes: Iterable[tuple]) -> Dict[str, Any]:
    """The split `s` with each (old, new) add applied — the replaced dict's share taken out (old is None for a
    new id) and the new one's put in — as a fresh dict, so a reader of the old memo never sees it half-moved."""
    total, stubs, frozen = s["total"], s["stub_cards"], s["frozen_cards"]
    for old, new in notes:
        if old is not None:
            t, st, f = _share(old)
            total, stubs, frozen = total - t, stubs - st, frozen - f
        t, st, f = _share(new)
        total, stubs, frozen = total + t, stubs + st, frozen + f
    out = _split(total, stubs, frozen)
    if out["total"] == 0:
        out["coverage"] = _EMPTY
    return out


def substance_note(notes: Iterable[tuple]) -> None:
    """A live add to the DEFAULT corpus (corpus.Corpus.add_cards), told here under that corpus's add lock: the
    memo, while it exists, moves by exactly those cards, with no walk; while the walk runs, they wait for it."""
    global _SUBSTANCE_CACHE
    if _SUBSTANCE_CACHE is not None:
        _SUBSTANCE_CACHE = _settled(_SUBSTANCE_CACHE, notes)
    elif _SUBSTANCE_PENDING is not None:
        _SUBSTANCE_PENDING.extend(notes)


def substance_of_the_keeping() -> Dict[str, Any]:
    """substance() over the live corpus singleton, memoized per process.

    Walking 548k bodies costs real time, and a public endpoint must not pay it per request —
    reading must not knock out proving. The corpus is NOT immutable under a running service: a live
    add (corpus.Corpus.add_cards — a warm seal, an acquisition, a release) grows it. So one walk stays
    honest for the process lifetime only because every add to the default corpus moves the memo under
    the corpus's add lock (substance_note: the replaced dict's old share out, the new one's in), and
    the walk takes its snapshot of the cards under that lock and, when it ends, applies under it every
    add that landed meanwhile before it sets the memo — so no add is lost however the threads
    interleave, and substance_if_cached() equals substance(default_corpus().cards). If the corpus is
    empty or unloadable this REPORTS that as coverage rather than returning zeros dressed as a
    measurement.
    """
    global _SUBSTANCE_CACHE, _SUBSTANCE_PENDING
    if _SUBSTANCE_CACHE is not None:
        return _SUBSTANCE_CACHE
    with _SUBSTANCE_WALK:
        if _SUBSTANCE_CACHE is not None:
            return _SUBSTANCE_CACHE
        try:
            from . import corpus
            cp = corpus.default_corpus()
        except Exception:                                     # noqa: BLE001 — degrade honestly
            cp = None
        if cp is None:
            s = substance({})
            s["coverage"] = _EMPTY
            _SUBSTANCE_CACHE = s
            return _SUBSTANCE_CACHE
        with cp._add_lock:
            cards = dict(cp.cards)        # the snapshot: a replaced value is set in place on the live dict
            _SUBSTANCE_PENDING = []
        try:
            s = substance(cards)
        except BaseException:
            with cp._add_lock:
                _SUBSTANCE_PENDING = None
            raise
        with cp._add_lock:
            pending, _SUBSTANCE_PENDING = _SUBSTANCE_PENDING, None
            _SUBSTANCE_CACHE = _settled(s, pending or ())
        return _SUBSTANCE_CACHE


def substance_if_cached() -> Optional[Dict[str, Any]]:
    """The memoized substance split IF it is already computed, else None — NEVER triggers the 548k-body
    walk. For latency-sensitive callers (the capabilities statement, an orientation call) that want the
    split only when it is free and must not block an agent on it."""
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


# ── the clock ────────────────────────────────────────────────────────────────────────────────
# Matt, 2026-08-04: "One thing that concordance must have is the actual date and time always
# current for the time zone you are in." An agent's own sense of "now" is wrong by months — its
# training cutoff — and a trust layer that stamps receipts with time must also be able to TELL
# time, or every agent conversation about deadlines, ages, and "today" builds on a stale clock.

HOME_TZ = os.environ.get("CONCORDANCE_HOME_TZ", "").strip() or "America/New_York"
# The library's home clock — deploys cut over at midnight LOCAL (project doctrine), and this is
# the local they mean. Overridable by env; always reported by name, never silently assumed.


def _zone_now(name: str, at) -> Dict[str, Any]:
    """One zone's reading of the instant `at` — resolved, or honestly unresolved. Never a guess.

    Three states, never two: a zone resolves (full reading), or the tz database cannot supply it
    (unresolved + the reason — Windows without tzdata says so rather than serving a wrong
    offset), or the caller's name is malformed (refused upstream by the schema/route). A silently
    wrong offset is the worst outcome a clock can produce; "cannot resolve" never is.
    """
    try:
        from zoneinfo import ZoneInfo
        z = ZoneInfo(name)
    except Exception as exc:                                   # noqa: BLE001 — the reason ships
        return {"tz": name, "unresolved": f"{type(exc).__name__}: {exc}",
                "note": "IANA name required (e.g. America/New_York); on hosts without a tz "
                        "database only UTC is served — a wrong offset is never served instead"}
    local = at.astimezone(z)
    off = local.utcoffset()
    total = int(off.total_seconds()) if off else 0
    sign = "+" if total >= 0 else "-"
    hh, mm = divmod(abs(total) // 60, 60)
    return {"tz": name,
            "iso": local.isoformat(timespec="seconds"),
            "date": local.strftime("%Y-%m-%d"),
            "time": local.strftime("%H:%M:%S"),
            "day": local.strftime("%A"),
            "utc_offset": f"{sign}{hh:02d}:{mm:02d}",
            "dst_in_effect": bool(local.dst()),
            "abbreviation": local.tzname()}


def now(tz: Optional[str] = None) -> Dict[str, Any]:
    """The actual date and time, current at THIS call. Never cached, coverage stated.

    Always serves UTC (the receipts' clock) and the library's home zone; serves any requested
    IANA zone beside them. The reading is computed inside this call — freshness is the point,
    so nothing here is memoized, and the route serves it no-store.
    """
    from datetime import datetime, timezone as _tz
    at = datetime.now(_tz.utc)
    out: Dict[str, Any] = {
        "utc": {"iso": at.isoformat(timespec="seconds"), "unix": int(at.timestamp()),
                "date": at.strftime("%Y-%m-%d"), "day": at.strftime("%A")},
        "home": _zone_now(HOME_TZ, at),
        "clock_source": ("the serving box's system clock, read at this call; NTP sync is the "
                        "host's duty and is not independently verified here"),
        "freshness": "computed at call time, never cached, served no-store",
        "means": {"utc": "the instant in UTC — the clock every seal and ops record is stamped in",
                  "home": f"the library's home zone ({HOME_TZ}); deploy cutovers are midnight in "
                          f"this zone",
                  "requested": "present only when a zone was asked for; resolved or honestly "
                               "unresolved, never guessed"},
    }
    if tz and str(tz).strip():
        out["requested"] = _zone_now(str(tz).strip(), at)
    return out
