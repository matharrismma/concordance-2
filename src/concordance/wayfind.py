"""Wayfinding — a floorplan of the keeping, so you get where you are going without wandering off.

Matt, 2026-07-27: "We need to create maps like floorplans so we get where we need to go. It
shouldn't take you off topic, and we can use past searches and selections to better map our paths."

On-topic BY CONSTRUCTION and deterministic — nothing generated:
  • here   — the card you are standing on (the anchor for what you asked)
  • near   — the rooms actually CONNECTED to it (graph edges, not a fresh search that could wander)
  • trail  — where you have already been (from this thread's own history — past searches/selections)
  • toward — the next on-topic step: the strongest connected room you have not visited yet

Sovereign: reads the corpus, the connection graph, and the thread record; writes nothing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import corpus, graph


def _subject(text: str) -> str:
    # reuse the front door's subject extractor (one-way import; ask never imports wayfind)
    try:
        from . import ask
        return ask.subject(text) or (text or "").strip()
    except Exception:  # noqa: BLE001
        return (text or "").strip()


def _anchor(q: str) -> Optional[dict]:
    subj = _subject(q)
    hits = corpus.search(subj, limit=1) or (corpus.search(q, limit=1) if subj != q else [])
    return hits[0] if hits else None


def path(q: Optional[str] = None, thread_id: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Return the floorplan around what the person is asking, staying strictly on-topic."""
    trail: List[Dict[str, Any]] = []
    if thread_id:
        try:
            from . import threads
            rec = threads.get(thread_id)
        except Exception:  # noqa: BLE001
            rec = None
        if rec:
            for ex in (rec.get("exchanges") or [])[-8:]:
                s = _subject(ex.get("user_text", ""))
                if s and (not trail or trail[-1]["subject"] != s):
                    trail.append({"subject": s})
            if not q and trail:            # no explicit query → stand where the conversation last was
                q = trail[-1]["subject"]

    if not q:
        return {"here": None, "near": [], "trail": trail, "toward": [],
                "note": "Nothing to stand on yet — search or choose a card to open the map."}

    anchor = _anchor(q)
    if not anchor:
        return {"here": None, "near": [], "trail": trail, "toward": [],
                "note": f"No room in the keeping for “{_subject(q)}” yet."}

    hood = graph.neighborhood(anchor.get("id"), limit=limit) or {}
    center = hood.get("center")
    near: List[Dict[str, Any]] = []
    for n in (hood.get("nodes") or []):
        if isinstance(n, dict) and n.get("id") and n.get("id") != center:
            near.append({"id": n.get("id"), "title": n.get("title", ""), "shelf": n.get("shelf", "")})
    visited = {t["subject"].lower() for t in trail}
    toward = [n for n in near if n["title"].lower() not in visited][:3]

    return {
        "here": corpus._brief(anchor),
        "near": near[:limit],                 # the adjacent rooms — connected, never off-topic
        "trail": trail,                       # where you have been
        "toward": toward,                     # the next step, still in the neighborhood
        "note": ("Your map: where you are, the rooms it connects to, and where you have been — "
                 "all within the neighborhood, so the path never wanders off topic."),
    }
