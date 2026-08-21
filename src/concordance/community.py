"""Community — a member's fellowship, gathered by their fingerprint, GATED by the narrow path.

The goal is community, serving, developing disciples. Serving is built (serve.py); this is COMMUNITY: the
same key that opens a member's keeping is their membership in the Body. Groups and shelves key off the
identity fingerprint (a member = a self-owned fingerprint + a chosen handle, no PII).

But the fellowship is not shown to everyone at once. Matt: *"We don't provide access to those aspects
immediately. We allow them to go down the narrow path. They must be a confessing Christian to see the
profiles of other members."* So seeing OTHER members is GATED — a viewer must have confessed Jesus Christ
as Lord and Messiah, read from the SAME identity that opens the mesh (`mesh.py`; the fingerprint is one).
Your OWN keeping is always yours; an unconfessed viewer is shown the PATH — the invitation — never the
network (Matthew 13:44: treasure hidden in a field; Romans 10:9: confess and believe). Reach WIDENS as the
walk goes on (the mesh stages: confessor → joined → community), so not everyone is given full reach at
once — it is earned by the walk (vouched, serving), the promotion-by-fruit.

Cross-member viewing is SIGNED: the viewer proves they hold their key, so the gate cannot be walked past by
merely quoting a confessor's fingerprint. Reads only — joining and dropping stay their own signed acts.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def _fruit(fp: str) -> int:
    """A member's FRUIT — their writing, reflecting, and serving: the words they have shared with the body,
    and what they have put on their shelf for the fellowship. This is what 'pays for wisdom' — with vouching,
    it is what promotes a member to more reach (Matt: people write and reflect and are promoted to a higher
    level to have more reach; we do not give everyone full reach at once). Conservative and crash-safe — a
    missing store simply counts zero, so fruit is never over-counted."""
    fp = str(fp or "").strip()
    if not fp:
        return 0
    n = 0
    try:
        from . import mesh
        n += int(mesh._outgoing_counts().get(fp, 0))    # words / reflections shared on the mesh
    except Exception:  # noqa: BLE001
        pass
    try:
        from . import shelves
        n += int(shelves.shelf_of(fp, viewer=fp).get("count", 0))   # what they have put on their shelf
    except Exception:  # noqa: BLE001
        pass
    return n


def _walk(fp: Optional[str]) -> Dict[str, Any]:
    """A member's WALK on the shared mesh identity: have they confessed, and where do they stand on the
    narrow path (confessor / joined / community as they are vouched and serve). A seeker has not yet
    confessed — the gate to the fellowship has not opened. Never a verdict on a soul; a description of the
    walk. Reach is EARNED: promotion needs both being known (vouched by believers) AND bearing fruit
    (writing, reflecting, serving) — so it cannot be gamed by one alone. Not everyone is given full reach
    at once."""
    fp = str(fp or "").strip()
    if not fp:
        return {"confessed": False, "stage": "seeker"}
    from . import mesh
    node = mesh._read_node(fp)
    if not node or not node.get("confessed"):
        return {"confessed": False, "stage": "seeker"}
    fruit = _fruit(fp)
    return {"confessed": True, "stage": mesh._stage(node, posts=fruit),
            "fruit": fruit, "vouched": len(node.get("links", []))}


def _the_gate() -> Dict[str, Any]:
    """The narrow-path gate, shown to a viewer who has not confessed: the way IN, never the network. Not a
    rejection — an invitation (the confession that opens the door, and the whole path with its gates)."""
    from . import mesh
    return {"gated": True, "ok": False,
            "why": "the fellowship opens to those who walk the path — confess Jesus Christ as Lord and "
                   "Messiah to see the members around you",
            "confession": mesh.CONFESSION, "scripture": mesh.CONFESSION_SCRIPTURE, "path": mesh.path()}


def for_member(member_fp: str, viewer_fp: Optional[str] = None) -> Dict[str, Any]:
    """A member's fellowship: the groups they belong to and their shelf. Your OWN (viewer == member) is
    always served in full. To see ANOTHER member you must be a confessor — else you are shown the gate (the
    invitation), never their data. Reach is staged by the viewer's walk; the horizon widens as they go."""
    member_fp = str(member_fp or "").strip()
    viewer_fp = str(viewer_fp or "").strip() or None
    if not member_fp:
        return {"groups": [], "shelf": {}, "belongs": 0}
    own = viewer_fp is not None and viewer_fp == member_fp
    if not own:
        walk = _walk(viewer_fp)
        if not walk["confessed"]:                   # not on the path yet — shown the way in, not the members
            gate = _the_gate()
            gate["your_walk"] = walk                # so the viewer sees where they stand and what opens next
            return gate
    from . import groups, mesh
    mine = groups.groups_of(member_fp)
    out: Dict[str, Any] = {"groups": mine, "belongs": len(mine), "own": own}
    if own:
        out["shelf"] = _shelf(member_fp, member_fp)  # your own — the fullest view, always
        out["walk"] = _walk(member_fp)               # your own walk — so the profile can show the confess step
        return out
    # Cross-member: reach is STAGED — not everyone sees everything at once, it is earned by the walk.
    #   confessor  → that the believers belong (the fellowship immediately around them),
    #   joined     → their shelf too — the offers and needs, to serve and be served,
    #   community+ → the fullest view (the woven center).
    stage = _walk(viewer_fp)["stage"]
    out["viewer_stage"] = stage
    if mesh._STAGE.get(stage, {}).get("rank", 0) >= mesh._STAGE["joined"]["rank"]:
        out["shelf"] = _shelf(member_fp, viewer_fp)
    else:
        out["reach"] = ("a confessor sees that the believers belong; their shelf — the offers and needs — "
                        "opens as you are vouched and serve (the 'joined' stage)")
    return out


def _shelf(member_fp: str, viewer_fp: Optional[str]) -> Dict[str, Any]:
    """A member's shelf as the viewer is allowed to see it, never a crash on a partial corpus."""
    from . import shelves
    try:
        return shelves.shelf_of(member_fp, viewer=viewer_fp or member_fp)
    except Exception:  # noqa: BLE001
        return {"ok": False}


def signable_view(public_key: str, member_fp: str, nonce: str) -> bytes:
    """The exact bytes a viewer signs to see a member's fellowship: {public_key, view, nonce}, canonical.
    Signing proves the viewer holds their key — so the confession gate cannot be walked past by quoting
    someone else's fingerprint. Nothing secret leaves the device."""
    from . import signing
    return signing.canonical_json_bytes(
        {"public_key": str(public_key or ""), "view": str(member_fp or ""), "nonce": str(nonce or "")})


def view(public_key: str, member_fp: str, nonce: str, signature: str) -> Dict[str, Any]:
    """SIGNED cross-member view. The viewer proves their key over `signable_view(...)`; their fingerprint is
    derived from it (never trusted as an input), then the narrow-path gate is applied: their own in full, a
    confessor sees the member, anyone else is shown the gate. A read — replaying the signature only re-reads,
    so no nonce store is needed; the nonce is only for freshness."""
    public_key = str(public_key or "").strip()
    member_fp = str(member_fp or "").strip()
    if not public_key or not member_fp:
        return {"ok": False, "error": "public_key and the member fingerprint to view are required"}
    from . import identity, signing
    try:
        ok = signing.verify_bytes(signable_view(public_key, member_fp, str(nonce or "")), signature, public_key)
    except Exception:  # noqa: BLE001
        ok = False
    if not ok:
        return {"ok": False, "error": "signature does not verify — prove your key to see the fellowship"}
    viewer_fp = identity.fingerprint(public_key)            # derived, never taken as an input (unspoofable)
    seen = for_member(member_fp, viewer_fp)
    seen.setdefault("ok", True)                             # a served view is ok; the gate keeps its ok:False
    seen["viewer"] = viewer_fp
    seen["member"] = member_fp
    return seen


__all__ = ["for_member", "signable_view", "view"]
