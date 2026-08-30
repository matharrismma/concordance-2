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
from . import field_canon as _canon

# The channels ARE the museum's halls. Plainly named by the relationship each holds with the viewer
# (the naming method: "to you, this is your ___"). Start small; let usefulness pull the rest in.
# `vseed` (optional) is the theme the channel's FILM programs are matched on in the video canon — a
# little broader than the text `seed`, so a channel airs the openly-licensed films that fit it.
CHANNELS: List[Dict[str, Any]] = [
    {"id": "witnesses", "name": "Witnesses", "line": "Voices who walked it before you",
     "seed": "martyr persecution faithful witness testimony of Christ", "witness": True},
    {"id": "scripture", "name": "Scripture", "line": "The Word, read through",
     "seed": "gospel psalm the word of God covenant", "witness": True},
    {"id": "field", "name": "The Field", "line": "Getting it done, off-grid and at home",
     "seed": "water shelter garden repair fire preserve", "witness": False,
     "vseed": "garden gardening farm farming poultry soil land food home homestead conservation harvest"},
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


# Bodiless stub shelves — dictionary/pronunciation/lexicon entries are word-cards with no body to air.
# The audit found raw search aired these (off-topic keyword collisions like "endurance riding" on the
# Witnesses channel) with the license label as the "blurb". A program needs a real body to describe.
_STUB_SHELVES = {"dictionary", "pronunciation", "lexicon"}


def _video_items(vseed: str, limit: int) -> List[Dict[str, str]]:
    """A channel's FILM programs — from the kept VIDEO canon (Prelinger public-domain films), matched
    to the channel's theme. A program links out to the archive.org player, which also credits the
    source and drives traffic to it. Kept, so the guide stays fast; the video reach grows the canon
    out of band, never on a page load. The same find/canon mechanism as the text plane, on film."""
    out: List[Dict[str, str]] = []
    if not vseed:
        return out
    try:
        for d in _canon.lookup(vseed, plane="video", limit=limit):
            url = (d.get("url") or "").strip()
            title = (d.get("title") or "").strip()
            if not url or not title:
                continue
            ident = url.rstrip("/").split("/")[-1]
            blurb = " · ".join(x for x in [(d.get("source") or ""), str(d.get("year") or "")] if x)
            out.append({"id": "vid_" + ident, "title": _trim(title, 90), "blurb": blurb,
                        "ref": url, "video": "1"})
    except Exception:  # noqa: BLE001 — a channel that can't load its films is simply text-only
        return []
    return out


def _items(seed: str, limit: int, witness: bool, vseed: str = "") -> List[Dict[str, str]]:
    """One channel's lineup — its FILM programs (from the video canon) lead, then REAL, described
    cards from the keeping. We over-fetch the cards, then keep those that have a body to describe and a
    clean title, and use the card's own snippet as the program blurb (never the license label). A
    bodiless stub or a mojibake title is skipped; a channel with nothing real goes dark."""
    out: List[Dict[str, str]] = _video_items(vseed, max(2, limit // 2))
    seen_ids = {it["id"] for it in out}
    try:
        hits = corpus.search(seed, limit=max(limit * 4, 12), include_witness=witness)
    except Exception:  # noqa: BLE001 — a channel that can't load is simply dark, never a crash
        return out
    for h in hits or []:
        if not isinstance(h, dict):
            continue
        cid = h.get("id")
        title = (h.get("title") or "").strip()
        if not cid or not title or "�" in title or cid in seen_ids:   # no id/title, mojibake, or dupe
            continue
        if (h.get("shelf") or "").lower() in _STUB_SHELVES:      # a bodiless dictionary/lexicon stub
            continue
        # a program blurb is a REAL description only — never the `surface` license label ("secular"),
        # and the internal snippet is often empty, so we simply omit the blurb rather than air a label.
        snippet = (h.get("snippet") or "").strip()
        blurb = _trim(snippet, 170) if (len(snippet) >= 30 and " " in snippet) else ""
        out.append({"id": cid, "title": _trim(title, 90), "blurb": blurb, "ref": f"/card/{cid}"})
        if len(out) >= limit:
            break
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
                 "seed": seeking, "witness": True, "vseed": seeking}] + defs

    channels: List[Dict[str, Any]] = []
    for c in defs:
        items = _items(c["seed"], per, bool(c.get("witness")), vseed=c.get("vseed", ""))
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
