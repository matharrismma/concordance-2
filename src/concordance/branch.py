"""Branch — fork a conversation, and hand work forward to a member and a time.

Two actions that a companion which never resets eventually needs:

**Fork.** Think something through two ways without losing either. The new thread copies the
exchanges up to the chosen turn **verbatim, hashes included**, so the shared past is provable
by hash equality rather than by trusting a pointer: identical hashes = genuinely the same
history. Both branches stay live; neither is a copy-of-record.

**Defer.** Hand a thread or a note to a member and a time — *"the Steward has this in April",
"the Coach picks this up when she finishes the vowel set"*. Deferral is a first-class action,
not a to-do list the person has to maintain. `due()` is what makes the companion able to bring
something back when it matters instead of when you happen to ask.

Deterministic throughout: copying, comparing and dating. No model, nothing generated.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import threads

# Members a thing can be handed to — the same body the Router knows (router.MEMBERS).
_HANDABLE = {"steward", "coach", "shepherd", "teachings", "scripture", "word_study",
             "verify", "almanac", "characters", "prophecy", "cross_refs", "commentary",
             "search", "self"}


def _dir() -> Path:
    env = os.environ.get("CONCORDANCE_DEFERRED_DIR", "").strip()
    if env:
        return Path(env)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    if data:
        return Path(data) / "deferred"
    return Path("data") / "deferred"


def _now() -> float:
    return round(time.time(), 3)


def _load(owner: str) -> Dict[str, Any]:
    try:
        return json.loads((_dir() / f"{owner}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"owner": owner, "items": [], "created_at": _now()}


def _save(rec: Dict[str, Any]) -> None:
    p = _dir() / f"{rec['owner']}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    rec["updated_at"] = _now()
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")


# --- fork -------------------------------------------------------------------------------------

def fork(thread_id: str, at_seq: Optional[int] = None,
         *, surface: str = "secular") -> Dict[str, Any]:
    """Branch a thread at a turn. The shared past keeps its hashes, so ancestry is verifiable."""
    src = threads.get(thread_id)
    if not src:
        return {"ok": False, "error": "no such thread"}
    exs: List[Dict[str, Any]] = src.get("exchanges", []) or []
    if not exs:
        return {"ok": False, "error": "nothing to fork — the thread is empty"}

    last = len(exs) - 1 if at_seq is None else int(at_seq)
    if last < 0 or last > len(exs) - 1:
        return {"ok": False, "error": f"seq out of range (0..{len(exs) - 1})"}

    kept = [dict(e) for e in exs[:last + 1]]          # verbatim, hashes and all
    new = threads._new_record(secrets.token_hex(16), src.get("surface") or surface)
    new["exchanges"] = kept
    new["head_hash"] = kept[-1].get("hash", "")
    new["title"] = (src.get("title") or "")[:80]
    new["gate_open"] = bool(src.get("gate_open"))     # the Gate stays open on a branch
    new["forked_from"] = {"thread_id": thread_id, "seq": last,
                          "hash": kept[-1].get("hash", ""),
                          "at": _now()}
    threads._write(new)
    return {"ok": True, "thread_id": new["thread_id"], "forked_from": new["forked_from"],
            "carried": len(kept),
            "note": "the shared past keeps its hashes — ancestry is provable, not asserted"}


def lineage(thread_id: str) -> Dict[str, Any]:
    """Where this thread came from, and how much of the past it genuinely shares."""
    rec = threads.get(thread_id)
    if not rec:
        return {"ok": False, "error": "no such thread"}
    ff = rec.get("forked_from")
    if not ff:
        return {"ok": True, "thread_id": thread_id, "forked_from": None, "shared": 0,
                "verified": True, "note": "an original thread — nothing upstream"}
    parent = threads.get(ff.get("thread_id") or "")
    shared = 0
    if parent:
        mine = rec.get("exchanges", []) or []
        theirs = parent.get("exchanges", []) or []
        for a, b in zip(mine, theirs):
            if a.get("hash") and a.get("hash") == b.get("hash"):
                shared += 1
            else:
                break
    return {"ok": True, "thread_id": thread_id, "forked_from": ff, "shared": shared,
            "verified": bool(parent) and shared == (ff.get("seq", -1) + 1),
            "note": "shared count is by HASH EQUALITY — the past is the same, not merely claimed"}


# --- defer / due ------------------------------------------------------------------------------

def _when_epoch(when: Any) -> Optional[float]:
    """Accept an epoch, or a plain date/datetime string. Refuse anything ambiguous."""
    if isinstance(when, (int, float)) and not isinstance(when, bool):
        return float(when)
    if isinstance(when, str) and when.strip():
        s = when.strip().replace("Z", "+00:00")
        for parse in (lambda: datetime.fromisoformat(s),
                      lambda: datetime.strptime(s, "%Y-%m-%d")):
            try:
                dt = parse()
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except ValueError:
                continue
    return None


def defer(owner: str, *, member: str, when: Any, note: str = "",
          thread_id: str = "") -> Dict[str, Any]:
    """Hand something forward to a member and a time."""
    member = (member or "").strip().lower()
    if member not in _HANDABLE:
        return {"ok": False, "error": f"unknown member — one of {sorted(_HANDABLE)}"}
    ts = _when_epoch(when)
    if ts is None:
        return {"ok": False, "error": "when must be an epoch or a date like 2026-04-01"}
    if not (note or "").strip() and not thread_id:
        return {"ok": False, "error": "defer what? give a note or a thread_id"}

    rec = _load(owner)
    item = {"id": secrets.token_hex(6), "at": _now(), "member": member, "when": ts,
            "note": note or "", "thread_id": thread_id or "", "released_at": None}
    rec["items"].append(item)
    _save(rec)
    return {"ok": True, "item": item}


def due(owner: str, *, now: Optional[float] = None) -> Dict[str, Any]:
    """What is ready to come back. This is what lets the companion return of its own accord."""
    t = _now() if now is None else float(now)
    rec = _load(owner)
    ready = [i for i in rec.get("items", [])
             if not i.get("released_at") and float(i.get("when", 0)) <= t]
    ready.sort(key=lambda i: (float(i.get("when", 0)), i.get("id") or ""))
    return {"ok": True, "owner": owner, "now": t, "count": len(ready), "due": ready}


def pending(owner: str) -> Dict[str, Any]:
    """Everything still waiting, soonest first — nothing hidden."""
    rec = _load(owner)
    items = [i for i in rec.get("items", []) if not i.get("released_at")]
    items.sort(key=lambda i: (float(i.get("when", 0)), i.get("id") or ""))
    return {"ok": True, "owner": owner, "count": len(items), "pending": items}


def release(owner: str, item_id: str) -> Dict[str, Any]:
    """Done with it (or no longer wanted). Kept, marked released — this is a record, not a queue."""
    rec = _load(owner)
    for i in rec.get("items", []):
        if i.get("id") == item_id:
            if i.get("released_at"):
                return {"ok": True, "item": i, "note": "already released"}
            i["released_at"] = _now()
            _save(rec)
            return {"ok": True, "item": i}
    return {"ok": False, "error": "no such item"}
