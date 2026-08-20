"""Discern — the one door to DISCERNMENT, the twin of the verify moat.

Matt, 2026-08-20: *"What is necessary? This at its core should do two things. It should verify and
discern."* Verify has a single door already — `check` / the moat: a claim in, a sealed three-state
verdict out. Discernment did not; it was scattered across the router, the auditor's extractor, the
relevance floor, the context loop, the candidate engine, the kernel lattice, the crisis net. This is
its single door.

The whole machine in two primitives: **discern proposes, verify disposes.** Discern decides *what* is
worth checking and *what it means*; the gate decides *whether it holds* and proves it. Everything else
is delivery wrapped around the two.

    proposal = discern(anything)          # what KIND · the necessary CLAIM · which MEMBER · the trail
    verdict  = check(proposal["claim"])   # the gate confirms — never discern

The contract, load-bearing:
  * PROPOSES, NEVER CONFIRMS. discern hands candidates to the gate; it returns no verdict. Authority is
    only ever "proposed" here — quarantined < cited < verified is earned at the gate, never granted at
    the door.
  * CRISIS OUTRANKS EVERYTHING. A cry for help is discerned first and routed to real people — never
    reduced to a claim, never sent to the gate.
  * NOTHING IS GENERATED. Discernment is separation over what is given — the necessary is kept, the
    incidental is set aside, the kind is named. No invention.
  * IT EXPLAINS ITSELF. Every proposal carries its `why` — the trail, like router.route.
  * IT FAILS SAFE. When it cannot discern a single answer (nothing brought, a genuine routing tie), it
    says so and asks — it never guesses.

This is a SEED. It unifies the front of discernment — kind (crisis vs claim), the necessity extraction
(the context loop's discriminator: reduce to only what is necessary to check, de-identified), and the
route (which member should verify). The remaining facets — the relevance floor, the candidate
narrowing, the auditor's multi-claim extraction, the moral RED/FLOOR scan — are named in the inventory
and fold in here one at a time, each keeping this contract. Pure: is_crisis, the context loop, and
router.route are all rule-based, no corpus, no model.
"""
from __future__ import annotations

from typing import Any, Dict

# The kinds discern names, and what to do with each.
KINDS = ("empty", "crisis", "claim", "question")
NEXT = ("ask_user", "real_help", "check", "retrieve", "miss")


def _relevant(query: str, search_fn=None, relevant_fn=None) -> list:
    """The RELEVANCE floor (folded from ask): from a search over the keeping, keep only the cards whose
    TITLE genuinely names the subject — a real match, not a word-collision ("start a fire" must not
    answer with a knots card that merely says 'fire' once). Returns [] on a genuine gap; a miss stays a
    miss. Injectable so the seed stays pure in tests; defaults to the real corpus + ask's own floor."""
    if search_fn is None:
        from . import corpus
        search_fn = corpus.search
    if relevant_fn is None:
        from . import ask
        relevant_fn = ask._title_names_subject
    try:
        hits = search_fn(query, 5) or []
    except Exception:  # noqa: BLE001 — a missing/partial corpus is a gap, never a crash
        hits = []
    out = []
    for c in hits:
        try:
            if relevant_fn(query, c):
                out.append({"id": c.get("id"), "title": c.get("title"), "shelf": c.get("shelf")})
        except Exception:  # noqa: BLE001
            continue
    return out


def discern(text: str, *, search_fn=None, relevant_fn=None) -> Dict[str, Any]:
    """Propose what matters. Given anything, name its KIND, reduce it to the necessary CLAIM
    (de-identified, framing held home), and either name the MEMBER that should verify it (a checkable
    claim) or discern the genuinely-relevant kept cards (a retrieval). Returns a proposal — never a
    verdict. Crisis is discerned first and routed to real people."""
    from . import ask, context, router

    t = (str(text) if text else "").strip()
    if not t:
        return {"input": text, "kind": "empty", "claim": None, "held": None, "route": None,
                "authority": "proposed", "proposes": True, "confirms": False,
                "why": "nothing was brought", "next": "ask_user"}

    # 1. FRONT DOOR — crisis outranks all. Never a claim, never the gate; always real people.
    if ask.is_crisis(t):
        return {"input": t, "kind": "crisis", "claim": None, "held": t,
                "route": {"member": "crisis", "why": "someone may be in danger — real people first"},
                "resources": list(ask._CRISIS_RESOURCES),
                "authority": "proposed", "proposes": True, "confirms": False,
                "why": "discerned as a cry for help — routed to real people, not the gate",
                "next": "real_help"}

    # 2. EXTRACT — reduce to the necessary, de-identified claim; hold the framing home. (The context
    #    loop's discriminator: only what could change the verdict travels.)
    stripped = context.decontextualize(t, minimal=True)
    claim = stripped.travels()
    held = stripped.framing().strip()      # for display; reattach still uses the full holds, exact

    # 3. ROUTE — name the member. router proposes; a tie asks, never guesses. Routed on the discerned
    #    claim, not the raw text, so framing can't sway the routing.
    route = router.route(claim or t)
    member = route.get("member")

    # 4. RELEVANCE (folded) — a member of "search" is a RETRIEVAL, not a checkable claim. Discern the
    #    genuinely-matching cards (real match vs a word-collision) and propose those; a gap stays a gap.
    if member == "search":
        candidates = _relevant(claim or t, search_fn, relevant_fn)
        return {"input": t, "kind": "question", "claim": claim, "held": held or None,
                "route": route, "candidates": candidates, "authority": "proposed",
                "proposes": True, "confirms": False,
                "why": ("discerned a retrieval; %d kept card(s) genuinely name the subject" % len(candidates)
                        if candidates else
                        "discerned a retrieval, but no kept card genuinely names the subject — a gap"),
                "next": ("retrieve" if candidates else "miss")}

    # 5. Otherwise a specialist can verify it — a checkable claim for the gate.
    return {"input": t, "kind": "claim", "claim": claim, "held": held or None,
            "route": route, "authority": "proposed", "proposes": True, "confirms": False,
            "why": "discerned the necessary claim %r; the %s should verify it (%s)" % (
                claim, member, route.get("why")),
            "next": ("ask_user" if member == "ask_user" else "check")}


__all__ = ["discern", "KINDS", "NEXT"]
