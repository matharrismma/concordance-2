"""Community — a member's fellowship, gathered by their fingerprint. The belonging bridge.

The goal is community, serving, developing disciples. Serving is built (serve.py); this is COMMUNITY:
the same key that opens a member's keeping is their membership in the Body. Groups and shelves already
key off the identity fingerprint (a member = a self-owned fingerprint + a chosen handle, no PII) — so a
member does not need a second account to belong. This surfaces what they belong to: the groups they are
in and their own shelf, so their profile and their fellowship are one identity.

Anonymity is the floor: only handles and counts are surfaced, never the raw ids. Reads only — joining a
group and dropping to a shelf stay their own signed acts on the community plane; this just lets a member
SEE their place in the Body.
"""
from __future__ import annotations

from typing import Any, Dict


def for_member(fp: str) -> Dict[str, Any]:
    """A member's fellowship: the groups they belong to and their shelf. Keyed by fingerprint; empty for
    anyone who has not yet joined or dropped (belonging is opt-in, like everything here)."""
    fp = str(fp or "").strip()
    if not fp:
        return {"groups": [], "shelf": {}, "belongs": 0}
    from . import groups, shelves
    mine = groups.groups_of(fp)
    try:
        shelf = shelves.shelf_of(fp, viewer=fp)     # a member sees their own shelf in full
    except Exception:  # noqa: BLE001
        shelf = {"ok": False}
    return {"groups": mine, "shelf": shelf, "belongs": len(mine)}


__all__ = ["for_member"]
