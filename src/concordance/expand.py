"""EXPAND ON THE CALL — one mechanism, two planes, and the want list only when there is no way out.

Matt, 2026-08-01, two sentences that settled the design:

    "It should be the same just different planes."
    "The want list is for when we don't have internet. Otherwise, we just execute then and allow
     the user to assist."

So a miss is not a dead end and not a queue ticket. It is a slower answer. The library goes and
gets it, cards it, hands it over, and is permanently larger — and the person may assist (choose
among what came back, refine the ask) rather than wait on anyone.

WHY THIS MODULE EXISTS AT ALL. The behaviour was already built and already good — `/ask` has run
the tortoise for months, and a live probe proved it: `/search?q=Rigveda` returned 0, two `/ask`
calls later it returned 3 public-domain sources that the tortoise had found and carded on the
call. But `/search` and the MCP `search` tool never invoked it. Same question, same engine, two
doors, two different answers — and the door AGENTS use (about 35% of traffic) was the deaf one. An
agent got `count: 0` and reasonably concluded the library was empty on the Rigveda, while the
other door was busy acquiring it.

That is this project's recurring failure in its purest form: correct in one place, absent where
the reader actually stands. So the capability moves here, where every door can call the same thing.

THE TWO PLANES — the act is identical, the authority is not:

    human   the person's own ask authorises it. Cards enter `public`.
    agent   cards enter `public_review`, which `corpus.is_public()` withholds from every public
            read path until a human looks. The agent still RECEIVES its answer — only the entry
            into everyone else's library waits. "We ask the next human that looks at it."

THE WANT LIST IS THE OFFLINE QUEUE, nothing more. If the network is reachable we execute now; a
want is opened only when we could not reach out at all, so the miss survives until a connection
does. Opening a want for something we could have simply fetched turns a slower answer into a
chore for a person, which is exactly backwards.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

PLANES = ("human", "agent")


def offline() -> bool:
    """True when no outward path exists — the one condition that justifies queueing a want."""
    from . import find
    return not find.enabled()


def expand(query: str, config, plane: str = "human",
           note: str = "") -> Dict[str, Any]:
    """Try to answer a miss NOW. Returns what happened, in words a caller can act on.

    {"status": "acquired", cards, documents, source_note}   found and carded (slower lane)
    {"status": "nothing_found"}                             we looked, the archives had nothing
    {"status": "queued", want_id}                           no network — the want waits for one
    """
    plane = plane if plane in PLANES else "human"
    q = str(query or "").strip()
    if not q:
        return {"status": "nothing_found", "reason": "an empty query asks nothing"}

    if offline():
        # THE ONLY CASE THAT BECOMES A WANT. Offline is not a failure of the library, it is a
        # postponement — the miss is kept so the miners can work it when a connection returns.
        from . import wants
        r = wants.open_want(kind="missing", query=q, plane=plane,
                            note=note or "no network at the time of asking")
        return {"status": "queued", "want_id": r.get("id"), "ok": r.get("ok", False),
                "message": "There is no connection right now, so this is written down and will be "
                           "fetched when there is one."}

    from . import find
    try:
        found = find.find_and_check(q, config, plane=plane)
    except Exception:  # noqa: BLE001 — the slow lane must never break the fast one
        found = None

    docs: List[Dict[str, Any]] = list((found or {}).get("documents") or [])
    if not found or not (found.get("answer") or docs):
        # WE LOOKED AND THE ARCHIVES HAD NOTHING. That is not a want either: queueing it would ask
        # a person to do what the miners just failed to do. Say so plainly instead.
        return {"status": "nothing_found",
                "message": "I went to the public-domain archives for this and they had nothing I "
                           "could stand behind. I won't invent one."}

    return {"status": "acquired", "plane": plane, "documents": docs,
            "answer": found.get("answer"), "framed": found.get("framed", ""),
            "checks": found.get("checks_verdict"), "source_note": found.get("source_note") or "",
            "held_for_review": plane != "human",
            "message": ("Not in the keeping, so I went and found it — public-domain sources, "
                        "kept for next time."
                        + (" Carded and waiting for a person to look before it joins the shared "
                           "library." if plane != "human" else ""))}


__all__ = ["expand", "offline", "PLANES"]
