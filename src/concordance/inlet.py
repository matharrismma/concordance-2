"""Inlet — bring anything; it is filed without you filing it, and it comes back when it matters.

This is the promise the whole thing opens with: *"It routes everything in the background.
Brings you what you need when you need it."* Two halves:

**Receiving.** You throw something in — a bill, a verse that stopped you, a half-thought about
your daughter's reading. The Router (rule-based, no model) names the member it belongs to, the
Scribe appends it to the chain verbatim, and you are told exactly where it went. **You never
file anything, and nothing is filed invisibly** — every receipt says what happened and why.

**Returning.** Three triggers decide what comes back, and each carries its reason:
  - **time** — the deferral queue: "the Steward has this in April" (`branch.due`).
  - **concordance** — what in the keeping genuinely concords with what you are carrying,
    found by the same index the whole engine runs on.
  - **state** — a thread that produced sealed receipts and then went quiet; work left open.

Every trigger is arithmetic over your own record and a search over a fixed corpus. Nothing is
inferred about you, nothing is generated, and every returned item answers *why now?*
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from . import branch, corpus, distill, router, threads

_STOP_SHORT = 3          # ignore very short tokens when concording
_QUIET_AFTER = 7 * 86400  # a thread with open work, untouched a week, is worth surfacing


def _now() -> float:
    return round(time.time(), 3)


def receive(owner: str, text: str, *, thread_id: str = "",
            surface: str = "secular") -> Dict[str, Any]:
    """Take in anything. Route it, record it, and say plainly where it went."""
    text = text if isinstance(text, str) else ""
    if not text.strip():
        return {"ok": False, "error": "nothing brought"}

    decision = router.route(text)
    member = decision.get("member")

    # The Scribe records it verbatim — the note, not a summary. Crisis is never filed away
    # quietly: it is surfaced immediately and marked, because a person may be in danger.
    tid = thread_id
    if not tid:
        tid = threads.new_thread(surface=surface)["thread_id"]
        # Bind it to them from the very first exchange. A thread protected only by an
        # unguessable id is protected by secrecy; bound, it is protected by ownership.
        from . import binding as _binding
        _binding.attach(owner, tid)
    ex = threads.append(tid, text,
                        {"kind": member, "message": "", "filed_by": "inlet",
                         "why": decision.get("why"), "generated": False},
                        surface=surface)

    return {"ok": True, "thread_id": tid, "seq": ex.get("seq"), "hash": ex.get("hash"),
            "routed_to": member, "why": decision.get("why"),
            "alternatives": decision.get("alternatives", []),
            "urgent": member == "crisis",
            "note": ("real people first — this was not filed away"
                     if member == "crisis" else
                     "filed for you; nothing was filed invisibly — this receipt says where it went")}


def _carrying(owner: str, *, threads_scanned: int = 8) -> Dict[str, Any]:
    """What the person is currently carrying — counted from their own record, never inferred."""
    terms: Dict[str, int] = {}
    refs: Dict[str, int] = {}
    open_work: List[Dict[str, Any]] = []
    now = _now()

    for brief in threads.list_threads(limit=threads_scanned):
        tid = brief.get("thread_id")
        if not tid:
            continue
        d = distill.digest(tid)
        if not d.get("ok"):
            continue
        for t, n in (d.get("recurring_terms") or []):
            if len(t) > _STOP_SHORT:
                terms[t] = terms.get(t, 0) + n
        for r, n in (d.get("scripture_refs") or []):
            refs[r] = refs.get(r, 0) + n
        last = d.get("last_at") or 0
        if d.get("sealed") and (now - float(last)) > _QUIET_AFTER:
            open_work.append({"thread_id": tid, "title": d.get("title", ""),
                              "sealed": len(d["sealed"]), "last_at": last})

    return {"terms": sorted(terms.items(), key=lambda kv: (-kv[1], kv[0]))[:8],
            "refs": sorted(refs.items(), key=lambda kv: (-kv[1], kv[0]))[:8],
            "open_work": open_work}


def returns(owner: str, *, now: Optional[float] = None, limit: int = 10) -> Dict[str, Any]:
    """What should come back right now, and why. Deterministic; every item answers 'why now?'."""
    t = _now() if now is None else float(now)
    out: List[Dict[str, Any]] = []

    # 1. TIME — a thing was handed forward to a member and that time has arrived.
    for item in branch.due(owner, now=t).get("due", []):
        out.append({"trigger": "time", "member": item.get("member"),
                    "why": f"you handed this to the {item.get('member')} for now",
                    "item": item})

    carrying = _carrying(owner)

    # 2. STATE — work that produced sealed receipts and then went quiet.
    for w in carrying["open_work"]:
        out.append({"trigger": "state", "member": "search",
                    "why": f"{w['sealed']} sealed receipt(s) here, untouched for a while",
                    "item": w})

    # 3. CONCORDANCE — what the keeping holds that concords with what you are carrying.
    seen = set()
    # Two per term, so what returns spreads across what you are carrying instead of one word
    # crowding out the rest — and each reason names the card, so no two lines read the same.
    for term, n in carrying["terms"][:5]:
        for card in (corpus.search(term, limit=2) or [])[:2]:
            cid = card.get("id")
            if not cid or cid in seen or not corpus.is_public(card):
                continue
            seen.add(cid)
            title = card.get("title", "") or "(untitled)"
            out.append({"trigger": "concordance", "member": "search",
                        "why": f"you keep returning to {term!r} ({n}×) — the keeping holds {title[:48]!r}",
                        "item": {"card_id": cid, "title": card.get("title", ""),
                                 "shelf": card.get("shelf", ""), "term": term}})

    order = {"time": 0, "state": 1, "concordance": 2}
    out.sort(key=lambda r: (order.get(r["trigger"], 9), str(r.get("why"))))
    return {"ok": True, "owner": owner, "now": t, "count": len(out[:limit]),
            "returns": out[:limit],
            "carrying": {"terms": carrying["terms"], "refs": carrying["refs"]},
            "note": "every item says why now — time, state, or concordance; nothing inferred, nothing generated"}
