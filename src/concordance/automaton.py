"""The Automaton — a witness who faced your situation, testifying in his OWN recorded words.

The hall of the museum (narrowhighway.tv, [[project_the_tv_museum_and_automatons]]): you bring a
situation — a struggle, a question — and the one who has been there answers. NOT a fabricated "what
he would say," but his ACTUAL public-domain words, gathered and cited, matched to your situation. A
museum of TRUE testimony, never a hall of talking deepfakes that lie.

THE AUTOMATON DISCIPLINE. It TESTIFIES; it never IMPERSONATES. The no-generation law is load-bearing
here — this is exactly where the impersonation temptation is strongest, so it is the ONE place the law
must be structural, not a matter of taste. The words are the witness's because they ARE his: this
composes `witness.py` (the strict, fail-closed public-domain cloud) and never reaches past that gate.
The curation — WHICH real words, matched to your situation, and WHICH figure has stood where you
stand — is the whole intelligence. Honest-empty where no gathered witness has faced this yet: a miss
stays a miss, nothing is invented to fill it. And it points past itself — the cloud surrounds; Christ
is the finish (Hebrews 12:1-2). Stdlib only, deterministic.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import witness as _witness


def hall(*, corpus: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """The witnesses who can be consulted — those whose real, public-domain words are gathered. As the
    cloud grows (the fathers, the reformers, the founders), the hall fills; today, whoever is gathered."""
    return _witness.witnesses(corpus=corpus)


def _discipline(name: str) -> str:
    """The frame that makes impersonation impossible — stated in the answer itself, every time."""
    return (f"These are {name}'s own recorded words — testimony, gathered and cited, never imitated. "
            f"He is not speaking to you; you are reading what he wrote, who faced what you face. "
            f"The cloud surrounds; Christ is the finish (Hebrews 12:1-2).")


def consult(situation: str, *, witness: Optional[str] = None,
            corpus: Optional[List[Dict[str, Any]]] = None, k: int = 4) -> Dict[str, Any]:
    """A witness who faced `situation`, testifying in his own cited words.

    Picks the FIGURE whose gathered public-domain words most frame the situation (an automaton is a
    person, not a scatter of quotes — so one voice emerges), or the named `witness` when asked for one
    by name. Returns his testimony (verbatim, attributed passages matched to the situation), and names
    the rest of the hall you can also consult. Nothing generated; honest-empty when the cloud does not
    reach — the answer then says so plainly rather than inventing a match."""
    situation = (situation or "").strip()
    roster = hall(corpus=corpus)
    if not situation:
        return {"situation": "", "witness": None, "testimony": [], "hall": roster,
                "generated": False, "proposes": True, "confirms": False,
                "note": "Bring a situation — a struggle, a question — and the one who faced it testifies."}

    # Over-fetch across the whole cloud (or the one requested witness), then let ONE figure emerge.
    # witness.see() is the strict-PD retrieval; this never voices a passage it did not return.
    seen = _witness.see(situation, witness=witness, corpus=corpus, k=max(6, k * 3))
    passages = seen.get("seeing") or []
    if not passages:
        return {"situation": situation, "witness": None, "testimony": [], "hall": roster,
                "gathered": seen.get("gathered", 0),
                "generated": False, "proposes": True, "confirms": False,
                "note": ("No one gathered in the hall has faced this yet — the cloud is still being "
                         "gathered. A miss stays a miss; nothing is invented to fill it.")}

    # THE FIGURE WHO SPEAKS MOST TO THIS. Group the top passages by witness in the order they ranked;
    # the automaton is the one holding the most of them (depth on the situation), ties broken toward
    # the earlier-ranked (whose single strongest passage led). One person testifies, not a chorus.
    order: List[str] = []
    by: Dict[str, List[Dict[str, Any]]] = {}
    for p in passages:
        w = (p.get("witness") or "").strip()
        if w not in by:
            by[w] = []
            order.append(w)
        by[w].append(p)
    chosen = max(order, key=lambda w: (len(by[w]), -order.index(w)))
    testimony = by[chosen][:max(1, int(k))]
    also = [w for w in roster if w and w != chosen]
    return {
        "situation": situation,
        "witness": chosen,                       # the figure who testifies
        "testimony": testimony,                  # his verbatim, cited words matched to the situation
        "also_in_the_hall": also,                # who else can be consulted (front can re-scope to them)
        "hall": roster,
        "gathered": seen.get("gathered", 0),
        "discipline": _discipline(chosen),
        "generated": False, "proposes": True, "confirms": False,
        "note": f"{chosen} faced this. These are his own words — testimony, not imitation.",
    }


__all__ = ["consult", "hall"]
