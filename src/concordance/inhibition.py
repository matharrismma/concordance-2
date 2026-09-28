"""INHIBITION — the honeybee STOP signal (cross-inhibition). When scouts advertise two rival sites, a
deciding bee delivers a brief head-butt that SILENCES a scout for the other site; this cross-inhibition
is what breaks a deadlock so the swarm commits to one home instead of splitting (Seeley et al., Science
2012). It is the inhibitory twin of the quorum's recruiting dance.

Our answer is chosen by the ranker (a single lead). Quorum reports how many witnesses CORROBORATE the
lead's subject (reinforcement); this reports the opposite — the strongest COMPETING answer, on a
DIFFERENT subject, that the lead was committed over. It makes the elimination visible (the engine's
method: narrow by elimination), and it keeps the engine honest: rather than present two rival answers as
co-equal, it names the road not taken and invites the person to ask for it by name. A CONFIDENCE / honesty
signal only — it never changes which card leads (the ranker's work), same discipline as quorum/eldership.

GATED OFF by default (CONCORDANCE_INHIBITION): `assess` returns None, so the response is unchanged until a
node opts in. Held for review.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from . import quorum


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_INHIBITION", "").strip().lower() in ("1", "true", "yes", "on")


def assess(hits: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The lead and the strongest competing (different-subject) alternative it was committed over. None
    when gated off or given nothing. Groups subjects exactly as quorum does, so a same-subject hit is a
    corroborating witness (not a rival) and never counts as competition."""
    if not enabled() or not hits:
        return None
    lead = hits[0]
    subj = quorum._subject_toks(lead)
    competing = None
    for h in hits[1:]:
        if subj and not (quorum._subject_toks(h) & subj):     # a different subject = a rival answer
            competing = h
            break
    committed = str(lead.get("title") or lead.get("id") or "the lead")
    if competing is None:
        return {"committed": committed, "inhibited": None,
                "means": "no competing answer surfaced — the results agree on the subject; the lead stands uncontested"}
    rival = str(competing.get("title") or competing.get("id") or "the other")
    return {"committed": committed, "inhibited": rival,
            "means": (f"committed to the lead over a competing answer on a different subject — '{rival}' "
                      "(cross-inhibition, the swarm's stop signal); if you meant that instead, ask for it by name")}
