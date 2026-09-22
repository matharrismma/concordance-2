"""THE GUARD — nothing wears a trusted voice unless it earned it.

A coach that can say "Christ says", "a witness says", or "you wrote" is a PROJECTION SURFACE: the
adversary's move (Surkov's move — manufacture a hall of mirrors, project a false message wearing
borrowed authority until no one can tell truth from counterfeit). The counter is a hard boundary at
the mouth: content may be SPOKEN AS a trusted voice only when its provenance is one of the fixed,
curated, provenance-gated corpora —

    red        the Words in Red — the teachings of Christ (teachings.py, refs into Scripture)
    scripture  the rest of the Word (the WEB / original-tongue engine)
    witness    the operator-gathered, strict-PD cloud of witnesses (witness.see)
    lens       the operator's own writing (lens.see, sovereign-node only)

Everything else — a book a reader dropped in, a freshly-acquired source, a search snippet, any
untrusted or unattributed text — may be quoted only AS ITSELF, attributed to its own source. It is
never spoken as Christ, a witness, or the operator. And the tiers do not invert: Red always wins; a
lower voice never overrides it (teachings.py's doctrine, Acts 17 — keep what aligns, refuse the idol).

This module is defense in depth. The trusted fields are already CONSTRUCTED only from those corpora;
`enforce()` re-checks the provenance tag at the door, so a forged or mis-tagged "trusted voice" is
stripped before it can be spoken — and a test can prove the property holds.
"""
from __future__ import annotations

from typing import Any, Dict

# The only tiers that may be SPOKEN AS a trusted voice, in authority order (Red first, and Red wins).
TRUSTED_TIERS = ("red", "scripture", "witness", "lens")
# Which provenance tier each trusted-voice field is allowed to carry.
_FIELD_TIERS = {
    "word": ("red", "scripture"),   # the Word — the teachings of Christ, or the rest of Scripture
    "cloud": ("witness",),          # the operator-gathered PD cloud of witnesses
    "lens": ("lens",),              # the operator's own writing
}


def is_trusted(tier: Any) -> bool:
    return tier in TRUSTED_TIERS


def enforce(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Strip any trusted-voice field whose provenance tier is not the one that field is allowed to
    carry. A word/cloud/lens with no tier, a wrong tier, or a user/acquired tier is dropped — it can
    still be quoted elsewhere as itself, but it will not be SPOKEN as Christ, a witness, or the
    operator. Mutates and returns the payload (the payload is ours; this is the last gate)."""
    if not isinstance(payload, dict):
        return payload
    for field, allowed in _FIELD_TIERS.items():
        item = payload.get(field)
        if isinstance(item, dict) and item.get("tier") not in allowed:
            payload[field] = None
    return payload


__all__ = ["TRUSTED_TIERS", "is_trusted", "enforce"]
