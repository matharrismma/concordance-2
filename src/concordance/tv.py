"""narrowhighway.tv — the museum as an old-school cable network (the SHELL).

Matt, 2026-08-29: "curate feeds like an old school cable network. You can watch live or go back to
start. Curate it with everything the person is seeking." And: "sketch the .tv shell, then fill the
hall — we let what is useful dictate what we build." So this is the FRAME, not the full programming:
channels over the halls we already have, a broadcast schedule (a 'now playing' that rotates by the
clock, and a 'from the start' you can wind back to), and a 'For You' lane curated to what you seek.

The bones are the keeping we already hold: each channel is a HALL with a seed, and its lineup is
pulled from the corpus (the same retrieval the Coach uses). Conduit, not source — nothing here is
generated; every item is a card that already passed the gate, shown in a broadcast frame. The
'automatons' (the witnesses who walked it before you) ride the include_witness lane.

Deterministic and light by design: the caller passes the clock (now_epoch) so the module never reads
it itself (testable, and no hidden time). Fill — real programs, series, the live/start-over media —
comes later, and usefulness dictates which halls earn it first.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from . import corpus

# The channels ARE the museum's halls. Plainly named by the relationship each holds with the viewer
# (the naming method: "to you, this is your ___"). Start small; let usefulness pull the rest in.
CHANNELS: List[Dict[str, Any]] = [
    {"id": "witnesses", "name": "Witnesses", "line": "Voices who walked it before you",
     "seed": "faith trial perseverance testimony endurance", "witness": True},
    {"id": "scripture", "name": "Scripture", "line": "The Word, read through",
     "seed": "gospel psalm the word of God covenant", "witness": True},
    {"id": "field", "name": "The Field", "line": "Getting it done, off-grid and at home",
     "seed": "water shelter garden repair fire preserve", "witness": False},
    {"id": "golf", "name": "Golf", "line": "Find the leak in your game",
     "seed": "golf swing putting short game practice", "witness": False},
    {"id": "grappling", "name": "Grappling", "line": "Measure your rolls, find your leak",
     "seed": "grappling wrestling jiu jitsu guard escape", "witness": False},
    {"id": "music", "name": "Music", "line": "Learn your instrument — find the leak in your practice",
     "seed": "mandolin fiddle guitar chords scales practice music", "witness": False},
]

# A broadcast 'slot' — how long each program sits in 'now playing' before the schedule advances. The
# rotation is derived from the clock, so a channel feels live without any stored schedule.
PROGRAM_SECONDS = 15 * 60


def _trim(s: str, n: int = 180) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def _items(seed: str, limit: int, witness: bool) -> List[Dict[str, str]]:
    """One channel's lineup, pulled from the keeping — real cards, already gated, shown as programs."""
    out: List[Dict[str, str]] = []
    try:
        hits = corpus.search(seed, limit=limit, include_witness=witness)
    except Exception:  # noqa: BLE001 — a channel that can't load is simply dark, never a crash
        return out
    for h in hits or []:
        if isinstance(h, dict) and h.get("id") and (h.get("title") or "").strip():
            out.append({
                "id": h["id"],
                "title": _trim(h.get("title") or "", 90),
                "blurb": _trim(h.get("snippet") or h.get("surface") or ""),
                "ref": f"/card/{h['id']}",
            })
    return out


def _now_index(n: int, now_epoch: float) -> int:
    """Which program is 'on' now — derived from the clock so the channel rotates like a broadcast."""
    if n <= 0:
        return 0
    return int(max(0.0, now_epoch) // PROGRAM_SECONDS) % n


def lineup(seeking: str = "", now_epoch: float = 0.0, per: int = 6) -> Dict[str, Any]:
    """The whole guide: each channel with what's ON NOW (clock-rotated), what's UP NEXT, and the full
    line 'from the start' (wind back to the top). When the viewer says what they're seeking, a 'For
    You' lane leads — the relationship engine, curating the museum to them. Nothing is generated."""
    seeking = (seeking or "").strip()
    defs: List[Dict[str, Any]] = list(CHANNELS)
    if seeking:
        defs = [{"id": "foryou", "name": "For You", "line": f"Because you're seeking: {seeking}",
                 "seed": seeking, "witness": True}] + defs

    channels: List[Dict[str, Any]] = []
    for c in defs:
        items = _items(c["seed"], per, bool(c.get("witness")))
        if not items:
            continue                                    # a hall with nothing to show stays dark
        i = _now_index(len(items), now_epoch)
        channels.append({
            "id": c["id"], "name": c["name"], "line": c["line"],
            "now": items[i],
            "up_next": items[(i + 1) % len(items)] if len(items) > 1 else None,
            "from_start": items,                        # 'go back to start' = the lineup from the top
        })
    return {"seeking": seeking, "channels": channels, "slot_seconds": PROGRAM_SECONDS,
            "generated": False, "note": "conduit"}


__all__ = ["lineup", "CHANNELS", "PROGRAM_SECONDS"]
