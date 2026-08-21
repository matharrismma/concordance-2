"""Disciple — a member's walked path with the coach, computed from their own progress. Discipleship.

The goal is community, serving, developing disciples. Serving and community are built; this is the third:
a member has a PATH walked over time. The coach is stateless about the learner — it takes the units a
learner has completed and computes where they are, the next step, and an honest mastery COUNT (the moat's
arithmetic applied to progress, never a verdict on the person). So a disciple's progress is THEIRS: it
lives in their sovereign profile (`done`, signed like everything else), and this reads it back through
the coach to show the road walked and the next stone.

Nothing is generated, and nothing judges the person: the count is a re-checkable integer, the next step
is the curriculum's own order. A member with no progress yet simply stands at the trailhead — honest, not
empty-as-failure. Reads only; a disciple marks a unit done by a signed save to their own profile.
"""
from __future__ import annotations

from typing import Any, Dict, List


def walk(fp: str) -> Dict[str, Any]:
    """A member's walked path: how far, where they stand, the next step, and their subject — all computed
    from the units they have completed (held in their own profile). Empty means the trailhead, not failure."""
    fp = str(fp or "").strip()
    if not fp:
        return {"done_count": 0, "next": None, "journey": None, "mastery": None}
    from . import coach, profile
    prof = profile.get(fp)
    done: List[str] = [str(x) for x in (prof.get("done") or []) if isinstance(x, (str,))]
    subject = str(prof.get("subject") or getattr(coach, "DEFAULT_SUBJECT", "read"))
    out: Dict[str, Any] = {"done_count": len(done), "subject": subject}
    for key, fn in (("journey", lambda: coach.journey(done)),
                    ("next", lambda: coach.where_next(done)),
                    ("mastery", lambda: coach.mastery(done))):
        try:
            out[key] = fn()
        except Exception:  # noqa: BLE001 — a missing curriculum is a trailhead, never a crash
            out[key] = None
    return out


__all__ = ["walk"]
