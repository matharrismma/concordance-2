"""Pins — the page remembers what you were carrying, and has it out when you come back.

The organizing half of the Companion, first slice: a shopping list pins itself; "remind me"
becomes a reminder that resurfaces when it is due; both greet you at the top of the page on
the next open — on any device that holds your pages. Crossed off, they leave.

Privacy is the same law as /days and the deck: **nothing is enumerable.** Pins live per
thread; the caller presents the thread ids its browser already holds, and ids it does not
hold return nothing. There is no all-pins view and no way to ask for one.

Deterministic throughout — the discernment (what IS a list? when IS Thursday?) is rules,
never a model.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import threads as _threads

# ── discernment: what kind of writing is this? ──────────────────────────────────────────────

_BULLET = re.compile(r"^\s*(?:[-*•◦]|\d{1,2}[.)])\s+")
_REMIND = re.compile(r"\bremind me( to| about)?\b", re.I)
_QUESTION = re.compile(r"\?\s*$|^\s*(who|what|when|where|why|how|is|are|can|does|do|should)\b", re.I)


def looks_like_list(text: str) -> bool:
    """Two or more short lines, or mostly bulleted — the shape of a list, not a letter."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if len(lines) < 2:
        return False
    bulleted = sum(1 for ln in lines if _BULLET.match(ln))
    shortish = sum(1 for ln in lines if len(ln.split()) <= 5)
    return bulleted >= max(2, len(lines) // 2) or shortish == len(lines)


def looks_like_reminder(text: str) -> bool:
    return bool(_REMIND.search(text or ""))


def looks_like_note(text: str) -> bool:
    """First-person prose that asks nothing — a thought to keep, not a query to answer."""
    t = (text or "").strip()
    if not t or _QUESTION.search(t):
        return False
    words = t.split()
    if len(words) < 12:
        return False
    low = " " + t.lower() + " "
    return any(w in low for w in (" i ", " my ", " me ", " im ", " i'm ", " we "))


# ── when is "Thursday"? ─────────────────────────────────────────────────────────────────────

_DAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4,
         "saturday": 5, "sunday": 6}
_IN_N = re.compile(r"\bin\s+(\d{1,3})\s+(minute|hour|day|week)s?\b", re.I)


def parse_when(text: str, *, now: Optional[float] = None) -> Optional[float]:
    """A due time from plain words: tomorrow, tonight, a weekday name, "in 3 days".
    None when no time is named — an undated reminder simply stays until crossed off."""
    now = now or time.time()
    low = (text or "").lower()
    m = _IN_N.search(low)
    if m:
        n = int(m.group(1))
        unit = {"minute": 60, "hour": 3600, "day": 86400, "week": 604800}[m.group(2).lower()]
        return now + n * unit
    lt = time.localtime(now)
    midnight = now - (lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec)
    if "tomorrow" in low:
        return midnight + 86400 + 9 * 3600          # tomorrow morning
    if "tonight" in low:
        return midnight + 19 * 3600                  # this evening
    for name, wd in _DAYS.items():
        if name in low:
            ahead = (wd - lt.tm_wday) % 7 or 7       # always the NEXT one
            return midnight + ahead * 86400 + 9 * 3600
    return None


# ── the store: per-thread, never enumerable ─────────────────────────────────────────────────

def _dir() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "pins"


def _path(thread_id: str) -> Path:
    return _dir() / (thread_id + ".json")


def _load(thread_id: str) -> List[Dict[str, Any]]:
    p = _path(thread_id)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8")) or []
    except (OSError, ValueError):
        return []


def _save(thread_id: str, items: List[Dict[str, Any]]) -> None:
    _dir().mkdir(parents=True, exist_ok=True)
    _path(thread_id).write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


def add(thread_id: str, kind: str, text: str, *, due: Optional[float] = None) -> Dict[str, Any]:
    """Pin something to a page you hold. kind: list | reminder."""
    if not _threads._valid_id(thread_id):
        return {"ok": False, "error": "invalid thread"}
    body = (text or "").strip()
    if not body:
        return {"ok": False, "error": "nothing to pin"}
    item = {"id": uuid.uuid4().hex[:12], "kind": kind, "text": body[:2000],
            "due": due, "done": False, "at": time.time()}
    items = _load(thread_id)
    items.append(item)
    _save(thread_id, items)
    return {"ok": True, "pin": item}


def done(thread_id: str, pin_id: str) -> Dict[str, Any]:
    """Cross it off. It stays in the file (the record keeps everything) but leaves the page."""
    if not _threads._valid_id(thread_id):
        return {"ok": False, "error": "invalid thread"}
    items = _load(thread_id)
    for it in items:
        if it.get("id") == pin_id:
            it["done"] = True
            it["done_at"] = time.time()
            _save(thread_id, items)
            return {"ok": True}
    return {"ok": False, "error": "no such pin"}


def collect(thread_ids: Iterable[str], *, now: Optional[float] = None,
            limit: int = 20) -> Dict[str, Any]:
    """Everything still carried across the pages this browser holds: open lists always,
    reminders when undated or due. Nothing for ids the caller does not hold."""
    now = now or time.time()
    out: List[Dict[str, Any]] = []
    seen = set()
    for tid in thread_ids or []:
        t = str(tid or "").strip()
        if not t or t in seen or not _threads._valid_id(t):
            continue
        seen.add(t)
        for it in _load(t):
            if it.get("done"):
                continue
            due = it.get("due")
            waiting = bool(due and due > now and it.get("kind") == "reminder")
            out.append({"thread_id": t, "id": it["id"], "kind": it["kind"],
                        "text": it["text"], "due": due, "waiting": waiting})
        if len(seen) >= 200:
            break
    # what is due first comes first; undated after; the far future last
    out.sort(key=lambda x: (x["waiting"], x["due"] or float("inf")))
    return {"ok": True, "pins": out[:limit],
            "note": "Only what these pages carry — nothing else is visible, to anyone."}
