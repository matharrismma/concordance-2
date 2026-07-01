"""Stacks — the superposition card model: one card lives ONCE, appears in many stacks.

Matt's model: the old card-system failure was needing a physical copy of a card in each stack. Here
a card lives once in the store; a "stack" is an ordered list of card-REFERENCES (a date, a topic, a
thread). So one card is in many stacks at once — no duplication; "it's all in the stack, just a
matter of how far we go to get it." That distance is TIERING by use: a touched card is hot; a
seldom-used card goes cold (the slower area).

The Journal is a date-stack of the day's ideas, writings, and inputs; the SAME cards also live in
topic-stacks, and the Deck's exchanges surface in the day's journal by date (superposition). Narrow
Highway is the foundation; the Journal is a light extra that rescues what chats waste. Conduit: a
card holds the person's own input (or found/verified material), verbatim — nothing generated.

Sovereign stdlib. Store:
    data/stacks/cards/<id[:2]>/<id[2:]>.json   # one card, lives once
    data/stacks/idx/<kind>/<key>.json          # a stack = ordered card ids (references)
Env: CONCORDANCE_STACKS_DIR / CONCORDANCE_DATA_DIR.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import validate

_LOCK = threading.Lock()
_KEY_RE = re.compile(r"[a-z0-9][a-z0-9_\-]{0,63}\Z")


def _dir() -> Path:
    env = os.environ.get("CONCORDANCE_STACKS_DIR", "").strip()
    if env:
        return Path(env)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / "stacks"


def _now() -> float:
    return round(time.time(), 3)


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _date_of(epoch: float) -> str:
    try:
        return time.strftime("%Y-%m-%d", time.gmtime(float(epoch)))
    except (TypeError, ValueError, OSError):
        return ""


def _card_path(cid: str) -> Path:
    return _dir() / "cards" / cid[:2] / f"{cid[2:]}.json"


def _stack_path(kind: str, key: str) -> Path:
    return _dir() / "idx" / kind / f"{key}.json"


def _safe_key(key: str) -> str:
    """Normalize a stack key to a safe filename token (no traversal)."""
    k = re.sub(r"[^a-z0-9_\-]", "-", (key or "").lower()).strip("-")[:64]
    return k or "misc"


def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(validate.canonical_json_bytes(obj))


def _read(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ── cards: one card, lives once ───────────────────────────────────────

def put_card(text: str, kind: str = "note", topics: Optional[List[str]] = None,
             source: str = "user", extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Mint a card and store it ONCE. Returns the card (with its id). Verbatim; not generated."""
    cid = "c" + secrets.token_hex(11)
    card = {"id": cid, "kind": kind, "text": text or "", "topics": list(topics or []),
            "source": source, "created_at": _now(), "use_count": 0, "last_touched": _now(),
            "tier": "hot"}
    if extra:
        card.update({k: v for k, v in extra.items() if k not in card})
    with _LOCK:
        _write(_card_path(cid), card)
    return card


def get_card(cid: str, bump: bool = True) -> Optional[Dict[str, Any]]:
    """Fetch a card; touching it makes it hot (tiering by use)."""
    card = _read(_card_path(cid))
    if card is None:
        return None
    if bump:
        with _LOCK:
            card["use_count"] = int(card.get("use_count", 0)) + 1
            card["last_touched"] = _now()
            card["tier"] = "hot"
            _write(_card_path(cid), card)
    return card


def _brief(card: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": card.get("id"), "kind": card.get("kind"),
            "text": (card.get("text") or "")[:280], "topics": card.get("topics") or [],
            "source": card.get("source"), "at": card.get("created_at"), "tier": card.get("tier")}


# ── stacks: ordered references to cards (a card can be in many) ────────

def add_to_stack(kind: str, key: str, card_id: str) -> None:
    """Append a card REFERENCE to a stack (no copy). Idempotent per (kind,key,card_id)."""
    key = _safe_key(key)
    with _LOCK:
        p = _stack_path(kind, key)
        st = _read(p) or {"kind": kind, "key": key, "card_ids": [], "created_at": _now()}
        if card_id not in st["card_ids"]:
            st["card_ids"].append(card_id)
        st["updated_at"] = _now()
        _write(p, st)


def get_stack(kind: str, key: str, bump: bool = False) -> Dict[str, Any]:
    """Resolve a stack to its cards (briefs), in order. The cards live once; this is a view."""
    key = _safe_key(key)
    st = _read(_stack_path(kind, key))
    if not st:
        return {"kind": kind, "key": key, "count": 0, "cards": []}
    cards = []
    for cid in st.get("card_ids", []):
        c = get_card(cid, bump=bump)
        if c:
            cards.append(_brief(c))
    return {"kind": kind, "key": key, "count": len(cards), "cards": cards}


def stack_keys(kind: str) -> List[str]:
    base = _dir() / "idx" / kind
    if not base.exists():
        return []
    return sorted(p.stem for p in base.glob("*.json"))


# ── the Journal: a date-stack of the day's inputs (+ topics + the Deck) ─

def journal_add(text: str, kind: str = "idea", topics: Optional[List[str]] = None,
                date: Optional[str] = None) -> Dict[str, Any]:
    """Keep an idea/writing/input: mint a card (lives once) and reference it into today's date-stack
    AND any topic-stacks (superposition — the same card in many stacks, no duplication)."""
    day = date or _today()
    card = put_card(text, kind=kind, topics=topics, source="journal")
    add_to_stack("date", day, card["id"])
    for t in (topics or []):
        if t and t.strip():
            add_to_stack("topic", t, card["id"])
    return {"card": _brief(card), "date": day}


def _deck_cards_for_date(day: str) -> List[Dict[str, Any]]:
    """The Deck's exchanges from this day, surfaced in the journal (superposition: the same exchange
    card lives in its thread AND appears here by date — never copied)."""
    out: List[Dict[str, Any]] = []
    try:
        from . import threads
        for c in threads.all_cards().values():
            if _date_of(c.get("at")) == day:
                out.append({"id": c.get("id"), "kind": "exchange", "text": (c.get("title") or "")[:280],
                            "topics": [], "source": "deck", "at": c.get("at"),
                            "thread_id": c.get("thread_id")})
    except Exception:  # noqa: BLE001 — the journal stands even if the Deck is unavailable
        pass
    return out


def journal_day(date: Optional[str] = None) -> Dict[str, Any]:
    """The whole day: explicit journal entries + the Deck's exchanges from that day, by time."""
    day = date or _today()
    entries = get_stack("date", day)["cards"]
    everything = entries + _deck_cards_for_date(day)
    everything.sort(key=lambda c: c.get("at") or 0)
    return {"date": day, "count": len(everything), "entries": everything}


def journal_dates() -> List[Dict[str, Any]]:
    """Every day that has journal entries, newest first (with counts)."""
    out = []
    for key in stack_keys("date"):
        st = _read(_stack_path("date", key)) or {}
        out.append({"date": key, "count": len(st.get("card_ids", [])),
                    "updated_at": st.get("updated_at", 0)})
    out.sort(key=lambda r: r["date"], reverse=True)
    return out


# ── tiering: seldom-used cards go cold (the slower area) ───────────────

def tier_sweep(cold_after_days: float = 30.0) -> int:
    """Mark cards untouched for cold_after_days as tier='cold' (the slower area). Returns the count.
    The tier is the 'how far to get it' distance; physical cold-storage relocation can follow."""
    base = _dir() / "cards"
    if not base.exists():
        return 0
    cutoff = time.time() - float(cold_after_days) * 86400.0
    moved = 0
    for prefix in base.iterdir():
        if not prefix.is_dir():
            continue
        for f in prefix.glob("*.json"):
            c = _read(f)
            if not c or c.get("tier") == "cold":
                continue
            if float(c.get("last_touched", 0)) < cutoff:
                c["tier"] = "cold"
                _write(f, c)
                moved += 1
    return moved


__all__ = ["put_card", "get_card", "add_to_stack", "get_stack", "stack_keys",
           "journal_add", "journal_day", "journal_dates", "tier_sweep"]
