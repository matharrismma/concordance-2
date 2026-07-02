"""Groups — pseudonymous shared-study groups (Arc 4 community: connect around what you study).

Anonymity is the FLOOR: a member is a self-owned identity fingerprint + a chosen handle — NO PII,
no account, no email. You DISCOVER a group by TOPIC (what people are studying), JOIN by choice, and
CONTRIBUTE cards (a verse, a note, a question) attributed to your handle and OPTIONALLY signed. The
Word-gate pattern, applied to people: connection opens a rung at a time, by consent — never a
directory of persons, only of topics.

SAFETY (load-bearing): this is an ADULT community surface. The Coach (children) is a SEPARATE,
parent-mediated surface and is NEVER joined into a group — this module imports nothing from coach and
never accepts a learner identity. Member contributions are clearly MEMBER content: attributed, and
NOT engine-verified. The engine hosts, organizes, and can verify a scripture reference; a member's
note stays a member's note.

Storage: group metadata (mutable membership) lives in data/groups/<id>.json; the group's CARDS use
the superposition study stack (stacks.py 'study_maps', key 'group:<id>') — one card lives once,
referenced, never copied. Sovereign: stdlib + stacks + identity/signing only. Imports NOTHING from
concordance.verifiers.* or concordance.derivation. Conduit: contributions are verbatim, never generated.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import identity, signing, stacks

_LOCK = threading.Lock()
_STUDY_KIND = "study_maps"                       # reuse the shared-study superposition shelf
_HANDLE_RE = re.compile(r"[^A-Za-z0-9 _.\-]")    # a handle is a display pseudonym, never PII
_MAX_TEXT = 4000


def _dir() -> Path:
    base = os.environ.get("CONCORDANCE_GROUPS_DIR", "").strip() or (
        (os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data") + "/groups")
    d = Path(base)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _path(gid: str) -> Path:
    return _dir() / (gid + ".json")


def _now() -> int:
    return int(time.time())


def _clean_handle(h: str) -> str:
    """A handle is a chosen pseudonym: printable, bounded, never PII. Empty → 'anon'."""
    h = _HANDLE_RE.sub("", str(h or "")).strip()[:40]
    return h or "anon"


def _study_key(gid: str) -> str:
    return "group:" + gid


def _read(gid: str) -> Optional[Dict[str, Any]]:
    if not re.fullmatch(r"grp_[0-9a-f]{12}", str(gid or "")):
        return None
    try:
        return json.loads(_path(gid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write(g: Dict[str, Any]) -> None:
    p = _path(g["id"])
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def _public(g: Dict[str, Any], with_cards: bool = False) -> Dict[str, Any]:
    """The safe, outward view: topic/title, member HANDLES only (never ids/PII), counts. The stored
    member ids stay server-side (dedup + your-own-membership checks); they are never surfaced."""
    out: Dict[str, Any] = {
        "id": g["id"], "topic": g.get("topic", ""), "title": g.get("title", ""),
        "description": g.get("description", ""),
        "member_count": len(g.get("members", [])),
        "card_count": g.get("card_count", 0),
        "members": [{"handle": m.get("handle", "anon"), "role": m.get("role", "member")}
                    for m in g.get("members", [])],
        "created_at": g.get("created_at"), "updated_at": g.get("updated_at"),
        "generated": False,
        "note": ("A shared study group. Members are pseudonymous — a handle, no personal information. "
                 "Contributions are members' own words, attributed; they are not engine-verified."),
    }
    if with_cards:
        st = stacks.get_stack(_STUDY_KIND, g["study_key"])
        out["cards"] = st["cards"]
        out["card_count"] = st["count"]
    return out


def create_group(topic: str, *, title: str = "", description: str = "",
                 creator_id: str = "", handle: str = "") -> Dict[str, Any]:
    """Open a new study group around a TOPIC. The creator auto-joins as founder (pseudonymous)."""
    topic = str(topic or "").strip()[:120]
    if not topic:
        return {"ok": False, "error": "topic required"}
    gid = "grp_" + secrets.token_hex(6)
    g = {
        "id": gid, "topic": topic,
        "title": (str(title or "").strip()[:160] or topic),
        "description": str(description or "").strip()[:600],
        "study_key": _study_key(gid),
        "members": [{"id": str(creator_id or ""), "handle": _clean_handle(handle),
                     "role": "founder", "joined_at": _now()}],
        "card_count": 0, "created_at": _now(), "updated_at": _now(), "generated": False,
    }
    with _LOCK:
        _write(g)
    return {"ok": True, **_public(g)}


def list_groups(q: str = "") -> Dict[str, Any]:
    """Discover groups by TOPIC (not by person). Optional substring filter over topic/title/description."""
    q = str(q or "").strip().lower()
    groups: List[Dict[str, Any]] = []
    for fp in sorted(_dir().glob("grp_*.json")):
        try:
            g = json.loads(fp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        hay = (g.get("topic", "") + " " + g.get("title", "") + " " + g.get("description", "")).lower()
        if q and q not in hay:
            continue
        groups.append(_public(g))
    groups.sort(key=lambda x: (-x["member_count"], -(x["updated_at"] or 0)))
    return {"total": len(groups), "groups": groups}


def get_group(gid: str) -> Optional[Dict[str, Any]]:
    g = _read(gid)
    return _public(g, with_cards=True) if g else None


def join_group(gid: str, *, member_id: str = "", handle: str = "") -> Optional[Dict[str, Any]]:
    """Join a group (consent-based, pseudonymous). Idempotent by identity id (or handle if no id)."""
    handle = _clean_handle(handle)
    with _LOCK:
        g = _read(gid)
        if not g:
            return None
        mid = str(member_id or "")
        exists = (any(m.get("id") == mid for m in g["members"]) if mid
                  else any(m.get("handle") == handle for m in g["members"]))
        if not exists:
            g["members"].append({"id": mid, "handle": handle, "role": "member", "joined_at": _now()})
            g["updated_at"] = _now()
            _write(g)
    return get_group(gid)


def contribute(gid: str, *, member_id: str = "", handle: str = "", text: str = "",
               kind: str = "note", topics: Optional[List[str]] = None,
               refs: Optional[List[str]] = None, private_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Add a card (verse / note / question) to the group's shared study — attributed to the member's
    handle, optionally SIGNED (binds their key to the text hash; still no PII). Conduit: verbatim."""
    text = str(text or "").strip()[:_MAX_TEXT]
    if not text:
        return {"ok": False, "error": "text required"}
    g = _read(gid)
    if not g:
        return None
    handle = _clean_handle(handle)
    signed, att = False, None
    if private_key:
        try:
            if identity.signing_available():
                th = hashlib.sha256(text.encode("utf-8")).hexdigest()
                att = signing.sign_seal(th, private_key)
                signed = True
        except Exception:  # noqa: BLE001 — signing is optional; a contribution never fails for it
            signed, att = False, None
    extra = {"by": handle, "by_id": str(member_id or ""), "refs": list(refs or []), "signed": signed}
    if att:
        extra["attestation"] = att
    card = stacks.put_card(text, kind=str(kind or "note"), topics=list(topics or []),
                           source="member:" + handle, extra=extra)
    stacks.add_to_stack(_STUDY_KIND, g["study_key"], card["id"])
    with _LOCK:
        g = _read(gid)
        g["card_count"] = int(g.get("card_count", 0)) + 1
        g["updated_at"] = _now()
        _write(g)
    return {"ok": True, "group": gid, "card_id": card["id"], "by": handle, "signed": signed}


def guidance() -> Dict[str, Any]:
    return {
        "identity": "A study group is people gathered around a TOPIC, pseudonymously — connect without giving up who you are.",
        "is": [
            "discovered by topic, never by person (no directory of people)",
            "pseudonymous: a handle + a self-owned key, no personal information",
            "consent-based: you choose to join and what to contribute",
            "contributions attributed and optionally signed — members' own words, not engine-verified",
        ],
        "will_not": [
            "require or store personal information (no account, no email)",
            "include the Coach or children — that surface is separate and parent-mediated",
            "present a member's note as a verified verdict (the engine verifies scripture refs, not opinions)",
        ],
        "note": "Anonymity is the floor; connection is a door you open. Success is real fellowship — pointing to the body, not replacing it (John 3:30).",
    }


__all__ = ["create_group", "list_groups", "get_group", "join_group", "contribute", "guidance"]
