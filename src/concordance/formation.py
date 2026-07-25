"""Formation — "make a wish for life," and the tool helps you reach it, then gets out of the way.

Matt, 2026-07-25: "We have people tell what they want to be, where they want to live and who they
want to be, and we help them achieve their goals — like make a wish for life." And: "Online is the
tool. It is NOT the end game." So this layer FINDS the fitting practice for what someone is reaching
for and points them OFF the screen — into a real practice, with real people, this week. It never
generates advice and never stores a person's life: the wish and the walk live on THEIR device (the
carry-your-own-data thesis); the server only retrieves the fitting, already-authored material.

Conduit, not source: every practice returned is a found, attributed card (the Field Kit deck, the
corpus) — generated=False. The win is fruit in a real life, never time on the app.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

# The kinds of wish — each one orients toward embodied, offline action, not an online metric.
KINDS: Dict[str, Dict[str, str]] = {
    "become": {"label": "who I want to become", "lean": "character virtue habit practice",
               "step": "Name one person who already lives this. Ask them to walk with you a while."},
    "overcome": {"label": "something to overcome (a habit, an addiction, a struggle)",
                 "lean": "temptation discipline drift accountability freedom",
                 "step": "Tell one trustworthy person this week — struggle in secret loses; struggle in the open heals (James 5:16)."},
    "mend": {"label": "a relationship to mend", "lean": "forgiveness reconciliation love peace anger",
             "step": "Go to the person, not around them (Matthew 5:23-24). In person if you can, this week."},
    "place": {"label": "where I want to live or go", "lean": "place land home community neighbor work",
              "step": "Visit it. Meet three people who live there. A place is its people."},
    "learn": {"label": "a skill or knowledge to gain", "lean": "learn skill practice craft build make",
              "step": "Do the smallest real version this week, with your hands — not another video."},
    "serve": {"label": "a gift I want to give", "lean": "serve give help offer gift neighbor",
              "step": "Offer it to one real person nearby — post it to the nodes around you (the mesh), then show up."},
}
_MAX = 200


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()[:_MAX]


def kinds() -> Dict[str, Any]:
    return {"kinds": [{"id": k, "label": v["label"]} for k, v in KINDS.items()]}


def help(wish: str, kind: str = "become") -> Dict[str, Any]:
    """Given a life-wish, FIND the fitting practice(s) to reach it — a Field Kit protocol first (a
    real, seven-day, offline practice), then the nearest cards in the keeping — plus a concrete first
    step and the honest reminder that the doing happens off the screen, with real people."""
    wish = _clean(wish)
    if not wish:
        return {"ok": False, "error": "tell me what you are reaching for"}
    kind = kind if kind in KINDS else "become"
    lean = KINDS[kind]["lean"]
    from . import corpus
    query = f"{wish} {lean}".strip()
    # the Field Kit deck holds the practices — reach for those first
    practices: List[Dict[str, Any]] = []
    try:
        for c in corpus.search(query, limit=3, shelves={"fieldkit"}):
            practices.append(corpus._brief(c))
    except TypeError:                     # older corpus.search without the shelves fast-path
        practices = []
    also = [corpus._brief(c) for c in corpus.search(wish, limit=4)
            if c.get("shelf") != "fieldkit"][:4]
    return {
        "ok": True, "wish": wish, "kind": kind, "kind_label": KINDS[kind]["label"],
        "practices": practices,                       # the fitting protocol cards (found, attributed)
        "also_in_the_keeping": also,                  # the nearest cards
        "first_step": KINDS[kind]["step"],            # a concrete, OFFLINE first move
        "with_people": "Do not walk it alone. Bring one real person in — a friend, a mentor, the nodes around you.",
        "generated": False,
        "note": ("Online is the tool, not the end game. Take the practice into a real week, with real "
                 "people, and let the fruit — not the screen — be the measure (Matthew 7:20; John 3:30)."),
    }


def guidance() -> Dict[str, Any]:
    return {
        "identity": "Make a wish for life — who you want to become, what to overcome, where to go — and the "
                    "tool helps you reach it, then gets out of the way.",
        "is": [
            "a finder of the fitting practice (the Field Kit, the keeping) — found and attributed, never generated",
            "oriented off the screen: every path ends in a real practice, with real people, this week",
            "sovereign: your wish and your walk live on YOUR device; we store nothing about your life",
            "measured by fruit in a real life, never by time on the app",
        ],
        "will_not": [
            "generate advice, diagnose, or pretend to be a counselor for a crisis (real people first)",
            "keep a record of your goals, your struggles, or your walk on our servers",
            "reward you for staying online — the aim is that you need it less (John 3:30)",
        ],
        "note": "Online is the tool. It is not the end game — music, community, family, and friends are.",
    }


__all__ = ["kinds", "help", "guidance", "KINDS"]
