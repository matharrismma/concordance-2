"""The quick-find index — one lookup across the whole reference section.

Matt, 2026-07-28: "We need a quick find index. focus added to the reference section, so you can
use the archetypes." The study helps had grown into seven shelves — archetypes, storyboards, the
back-matter tables, the encyclopedia, the atlas, the Harmony, the Timeline — each excellent and
each its own door. This is the ONE door: type a word, see everywhere the reference section speaks
to it, jump straight there.

Discipline: an INDEX finds, it never ranks truth — results carry their kind and their source
surface, and each hit is a pointer to the real entry (which carries its own refs and its own
honesty). The archetype results carry Matt's framing verbatim, because a quick find must not
quietly become a quick label: "You may be many of these characters at times of your life. They
are just a reference point. We are not saying you are that person, but the characteristics have
been displayed."

Everything searched is already in memory — no disk, no network; quick means quick.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_WS = re.compile(r"\s+")

ARCHETYPE_FRAMING = ("You may be many of these characters at times of your life. They are just a "
                     "reference point. We are not saying you are that person, but the "
                     "characteristics have been displayed.")


def _hit(kind: str, title: str, snippet: str, open_at: str, **extra) -> Dict[str, Any]:
    return {"kind": kind, "title": title, "snippet": _WS.sub(" ", snippet or "").strip()[:220],
            "open": open_at, **extra}


def find(q: str, limit: int = 40) -> Dict[str, Any]:
    """One query across the reference section. Substring, case-insensitive, per-source capped so
    one large shelf (the encyclopedia) cannot drown the others."""
    needle = (q or "").strip().lower()
    if not needle or len(needle) < 2:
        return {"q": q, "hits": [], "count": 0,
                "note": "two characters or more — an index needs something to look up"}
    per_source = max(3, limit // 6)
    hits: List[Dict[str, Any]] = []

    # ── Archetypes — the characters and their micropositions ────────────────────────────
    from . import archetypes as _arch
    n = 0
    for a in _arch.ARCHETYPES:
        for mp in a["micropositions"]:
            blob = " ".join([a["character"], a["condition"], mp["moment"], mp["meets"],
                             " ".join(mp["keywords"])]).lower()
            if needle in blob and n < per_source:
                hits.append(_hit("archetype", f"{a['character']} — {mp['moment']}",
                                 mp["meets"], f"/companion.html",
                                 refs=mp["scripture"], framing=ARCHETYPE_FRAMING))
                n += 1

    # ── Storyboards — narratives and their movements ────────────────────────────────────
    from . import narratives as _narr
    n = 0
    for sb in _narr.NARRATIVES:
        blob = " ".join([sb["name"], sb["meaning"], " ".join(sb["movements"]),
                         " ".join(i["who"] for i in sb["instances"])]).lower()
        if needle in blob and n < per_source:
            hits.append(_hit("storyboard", sb["name"], sb["meaning"],
                             f"/narratives.html?id={sb['id']}",
                             movements=sb["movements"], framing=_narr.FRAMING))
            n += 1
    for mv, meaning in _narr.MOVEMENTS.items():
        if needle in mv or needle in meaning.lower():
            hits.append(_hit("movement", f"movement: {mv}", meaning,
                             f"/narratives.html?movement={mv}"))
            break  # one movement hit is a doorway; the page lists the rest

    # ── The back-matter tables ──────────────────────────────────────────────────────────
    from . import backmatter as _bm
    n = 0
    for key, table in (("weights_measures", _bm.WEIGHTS_MEASURES),
                       ("names_of_god", _bm.NAMES_OF_GOD),
                       ("parables", _bm.PARABLES), ("miracles", _bm.MIRACLES),
                       ("book_intros", _bm.BOOK_INTROS), ("topical_index", _bm.TOPICAL_INDEX)):
        for e in table:
            title = e.get("name") or e.get("topic") or e.get("book") or ""
            blob = " ".join(str(v) for v in e.values() if isinstance(v, str)).lower()
            if needle in blob and n < per_source:
                hits.append(_hit("table:" + key, title,
                                 e.get("meaning") or e.get("theme") or e.get("equivalent") or
                                 e.get("moment") or ", ".join(e.get("refs") or [])[:120],
                                 f"/backmatter.html?table={key}"))
                n += 1

    # ── The atlas ───────────────────────────────────────────────────────────────────────
    from . import bible_places as _bp
    n = 0
    for p in _bp.PLACES:
        blob = " ".join([p["name"], p.get("modern") or "", p.get("note") or "",
                         " ".join(p.get("candidates") or [])]).lower()
        if needle in blob and n < per_source:
            hits.append(_hit("place", p["name"],
                             (p.get("modern") or p["status"]) +
                             (" — location disputed; candidates named" if p["status"] == "disputed"
                              else (" — honestly unlocated" if p["status"] == "unlocated" else "")),
                             f"/places.html?name={p['name']}", status=p["status"]))
            n += 1

    # ── The Harmony and the Timeline ────────────────────────────────────────────────────
    from . import harmony as _h, timeline as _t
    n = 0
    for ev in _h._HARMONY:
        if needle in (ev.get("event") or "").lower() and n < per_source:
            hits.append(_hit("harmony", ev["event"], ev.get("period") or "",
                             f"/harmony.html?id={ev['id']}"))
            n += 1
    n = 0
    for ev in _t._TIMELINE:
        if needle in (ev.get("event") or "").lower() and n < per_source:
            hits.append(_hit("timeline", ev["event"], ev.get("date") or "",
                             f"/timeline.html?id={ev['id']}"))
            n += 1

    # ── The encyclopedia (Easton's) — the largest shelf, searched last and capped ───────
    try:
        from . import characters as _ch
        got = _ch.browse(search=needle, limit=per_source)
        for item in got.get("items", []):
            hits.append(_hit("encyclopedia", item["name"], item.get("preview") or "",
                             f"/characters.html?search={item['name']}"))
    except Exception:  # noqa: BLE001 — an unprovisioned store must not break the index
        pass

    return {"q": q, "hits": hits[:limit], "count": min(len(hits), limit),
            "sources": ["archetype", "storyboard", "movement", "table:*", "place",
                        "harmony", "timeline", "encyclopedia"],
            "note": ("One index across the reference section. Each hit is a pointer to the real "
                     "entry, which carries its own references and its own honesty — the index "
                     "finds; it never ranks truth."),
            "framing": ARCHETYPE_FRAMING}


__all__ = ["find", "ARCHETYPE_FRAMING"]
