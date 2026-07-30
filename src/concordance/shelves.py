"""THE COMMONS · C1a — the member shelf. Every member stocks their own, signed by their own key.

Matt, 2026-07-28: *"Think of it like a giant library with everyone having their own shelf to
stock. People can write and have their words read."* And on identity: *"Ideally we use real
names. We just don't track people and protect their privacy."*

So a shelf is not an account. It is a covenant public key with cards hanging on it, and the
member's own signature over every one.

THE THREE RINGS — visibility is chosen by the member, and the gate is on amplification only:

    private   only you. Never served to anyone else. (`lifecycle_stage: private`)
    shelf     you and the friends who chose you. Ungated — your shelf, your voice.
    commons   site-wide discovery. GATED: enters `public_review` and waits for a steward.

Matt: *"We can curate and evaluate before we make available."* The gate stops nothing from being
SAID — a shelf drop is live the moment it is signed. It governs what the library AMPLIFIES. And
"shared by a member" is never silently upgraded into "evaluated by the library": the authority
tier stays `member` at every ring, forever.

WHAT IS SIGNED, AND WHY IT MATTERS. The member signs the canonical bytes of their own drop on
their own device and sends only the signature — the same detached-signature discipline as
consent and the moderation floor. That makes a shelf card *attributable* rather than merely
labelled: nobody can put words on your shelf, and you cannot later disown what you signed.

APPEND-ONLY (docs/THE_RECORD.md). A drop is never edited. A correction is a NEW drop carrying
`supersedes`; a withdrawal is a `withdrawn` record with its reason. Both remain, because the
trail of a person changing their mind is part of the record, not noise to be swept.

REAL NAMES, NO TRACKING. `display_name` is the only profile field there is — self-asserted,
signed, no verification of documents (that would mean collecting them). Known when you speak,
unseen when you read: nothing here records who read anything.

Store: `data/shelves/drops.jsonl` + `curation.jsonl`, append-only, re-read fresh. Stdlib only.
"""
from __future__ import annotations

import base64
import json
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

RINGS = ("private", "shelf", "commons")
KINDS = ("note", "writing", "recipe", "build", "field_note", "question", "link", "suggestion")
SIGNATURE_TTL_S = 900          # signed bytes are good for 15 minutes — a replay window, not a life
MAX_BODY = 20000
_SIGNED_FIELDS = ("at", "body", "kind", "member", "nonce", "ring", "subject")
_SLUG = re.compile(r"[^a-z0-9]+")

# The one honest authority tier for member work. It is never raised — not by promotion to the
# commons, not by a steward, not by popularity.
MEMBER_TIER = "member"


def _dir() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "shelves"


def _append(name: str, rec: Dict[str, Any]) -> None:
    d = _dir()
    d.mkdir(parents=True, exist_ok=True)
    with open(d / name, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _read(name: str) -> List[Dict[str, Any]]:
    p = _dir() / name
    if not p.exists():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
    return out


def _canon(fields: Dict[str, Any]) -> bytes:
    """The exact bytes both sides sign and verify — sorted-key JSON, nothing else. The same
    canonicalisation consent and moderation use, so one signing routine serves the house."""
    return json.dumps({k: fields.get(k) for k in _SIGNED_FIELDS}, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _slug(s: Any, limit: int = 60) -> str:
    return _SLUG.sub("-", str(s or "").lower()).strip("-")[:limit]


def signable_drop(member: str, kind: str, subject: str, body: str,
                  ring: str = "shelf") -> Dict[str, Any]:
    """Step 1: the canonical bytes of a drop, ready to sign ON THE DEVICE. The server mints the
    nonce and the clock so the stored drop and the signed bytes cannot drift; the key never
    travels."""
    member, kind, ring = (member or "").strip(), (kind or "").strip(), (ring or "").strip()
    if not member:
        return {"ok": False, "error": "a drop needs the member's public key — a shelf belongs to "
                                      "a key, not to an account"}
    if kind not in KINDS:
        return {"ok": False, "error": f"kind must be one of {list(KINDS)} — a closed set, so "
                                      f"every shelf reads the same way"}
    if ring not in RINGS:
        return {"ok": False, "error": f"ring must be one of {list(RINGS)}"}
    body = (body or "").strip()
    if not body:
        return {"ok": False, "error": "a drop with no words is not a drop"}
    if len(body) > MAX_BODY:
        return {"ok": False, "error": f"body over {MAX_BODY} chars — split it into more than one"}
    fields = {"member": member, "kind": kind, "subject": (subject or "").strip()[:180],
              "body": body, "ring": ring, "nonce": secrets.token_urlsafe(12),
              "at": int(time.time())}
    return {"ok": True, "fields": fields,
            "signable": base64.urlsafe_b64encode(_canon(fields)).decode("ascii"),
            "note": "sign these exact bytes with your own key ON YOUR DEVICE, then send the "
                    "fields plus the signature. The private key never travels."}


def _verify(fields: Optional[Dict[str, Any]], signature: str) -> Dict[str, Any]:
    if not isinstance(fields, dict) or not isinstance(signature, str) or not signature.strip():
        return {"ok": False, "error": "signed fields and a signature are required — call "
                                      "signable_drop() first and sign those bytes"}
    if "private_key" in fields:
        return {"ok": False, "error": "a detached signature is required — never a private key"}
    missing = [k for k in _SIGNED_FIELDS if k not in fields]
    if missing:
        return {"ok": False, "error": f"the signed fields must carry {list(_SIGNED_FIELDS)}; "
                                      f"missing {missing}"}
    member = str(fields.get("member") or "").strip()
    try:
        at = int(fields.get("at") or 0)
    except (TypeError, ValueError):
        return {"ok": False, "error": "the signed bytes carry no readable timestamp"}
    now = int(time.time())
    if not (now - SIGNATURE_TTL_S <= at <= now + 300):
        return {"ok": False, "error": "these signed bytes are stale — sign a fresh set"}
    from . import signing
    if not signing.verify_bytes(_canon(fields), signature.strip(), member):
        return {"ok": False, "error": "that signature does not verify against the named key — "
                                      "nobody can put words on another member's shelf"}
    return {"ok": True, "member": member}


def _stage_for(ring: str) -> str:
    """The ring decides the lifecycle stage, and therefore who is served this card.

    `private` and `shelf` are BOTH withheld from public reads by `corpus.is_public` — the shelf
    ring is served to the member and to friends by the shelf reader below, never by the public
    surface. Only a steward's promotion makes a card public, and only from `commons`.
    """
    return {"private": "private", "shelf": "private", "commons": "public_review"}[ring]


def drop(fields: Optional[Dict[str, Any]] = None, signature: str = "",
         display_name: str = "") -> Dict[str, Any]:
    """Step 2: verify the member's signature over those exact bytes, and stock the shelf.

    `display_name` is the ONLY profile field — self-asserted, carried on the card so the words
    have a name on them. No email, no phone, no verified documents (verifying would mean
    collecting them), and nothing anywhere records who READ this.
    """
    v = _verify(fields, signature)
    if not v.get("ok"):
        return {"ok": False, "error": v["error"]}
    member, f = v["member"], dict(fields or {})
    ring = f["ring"]
    card_id = f"card_shelf_{_slug(member, 24)}_{f['nonce']}"
    card = {
        "id": card_id, "kind": "note",
        "title": (f.get("subject") or f["body"][:60]).strip()[:180],
        "body": f["body"],
        "source": {"label": (f"{display_name.strip()} — a member of the Commons"
                             if display_name.strip() else "A member of the Commons"),
                   "url": "", "ref": member[:16], "authority_tier": MEMBER_TIER},
        "shelf": "commons", "box": f["kind"],
        "bands": ["commons", "member", f["kind"]] + _slug(f.get("subject")).split("-")[:3],
        "subject": f.get("subject") or f["body"][:60],
        "connections": [{"to_card_id": f"card_spine_shelf_{_slug(member, 24)}",
                         "relationship": "member_of",
                         "evidence": "stocked on this member's own shelf"}],
        "author": "member", "created_at": float(f["at"]), "updated_at": float(f["at"]),
        "visibility": "public" if ring == "commons" else "private",
        "lifecycle_stage": _stage_for(ring),
        "volatility": "durable", "surface": "secular", "generated": False,
        "extra": {"member": member, "ring": ring, "display_name": display_name.strip()[:80],
                  "signature": signature.strip(), "drop_kind": f["kind"],
                  "signed_at": f["at"]},
    }
    _append("drops.jsonl", card)
    return {"ok": True, "card_id": card_id, "ring": ring,
            "stage": card["lifecycle_stage"], "authority_tier": MEMBER_TIER,
            "note": ("Signed by your key and stocked on your shelf. "
                     + ("Waiting for a steward before it reaches the commons — the gate is on "
                        "what the library amplifies, never on what you may say."
                        if ring == "commons" else
                        "Visible to you and to the friends who chose you.")),
            "never": "Your words stay attributed to you at the member tier. Promotion to the "
                     "commons does not make them the library's claim."}


def shelf_of(member: str, viewer: Optional[str] = None) -> Dict[str, Any]:
    """One member's shelf. `viewer` decides what is served, and nothing records that they looked.

    * the member themselves sees every ring;
    * anyone else sees `shelf` and promoted `commons` cards — never `private`;
    * withdrawn and superseded drops are excluded from the shelf view but never deleted.
    """
    member = (member or "").strip()
    if not member:
        return {"ok": False, "error": "which shelf?"}
    own = bool(viewer and viewer.strip() == member)
    curation = {c["card_id"]: c for c in _read("curation.jsonl")}
    superseded = {str((d.get("extra") or {}).get("supersedes"))
                  for d in _read("drops.jsonl") if (d.get("extra") or {}).get("supersedes")}
    cards, held = [], 0
    for d in _read("drops.jsonl"):
        extra = d.get("extra") or {}
        if extra.get("member") != member or d["id"] in superseded:
            continue
        act = curation.get(d["id"], {})
        if act.get("action") == "withdrawn":
            continue
        ring = extra.get("ring")
        if not own:
            if ring == "private":
                continue
            if ring == "commons" and act.get("action") != "promoted":
                held += 1
                continue
        card = dict(d)
        if act.get("action") == "promoted":
            card["lifecycle_stage"] = "public"
            card["extra"] = dict(extra, promoted_by=act.get("steward"),
                                 promoted_reason=act.get("reason"), promoted_at=act.get("at"))
        cards.append(card)
    cards.sort(key=lambda c: -(c.get("created_at") or 0))
    return {"ok": True, "member": member, "own_view": own, "count": len(cards),
            "awaiting_review": held if not own else None, "cards": cards,
            "note": "A shelf is a key with cards on it. Nothing here records who read them."}


def commons(limit: int = 40) -> Dict[str, Any]:
    """What the fellowship has put on the commons — promoted drops only, newest first. Member
    tier is stated on every card, because the library carrying a voice is not the library
    agreeing with it."""
    promoted = {c["card_id"]: c for c in _read("curation.jsonl") if c.get("action") == "promoted"}
    out = []
    for d in _read("drops.jsonl"):
        act = promoted.get(d["id"])
        if not act:
            continue
        card = dict(d, lifecycle_stage="public")
        card["extra"] = dict(d.get("extra") or {}, promoted_by=act.get("steward"),
                             promoted_reason=act.get("reason"))
        out.append(card)
    out.sort(key=lambda c: -(c.get("created_at") or 0))
    return {"ok": True, "count": len(out), "cards": out[:max(1, min(int(limit), 200))],
            "authority": MEMBER_TIER,
            "note": "Every card here is a member's own work, carried at the member tier. The "
                    "library amplified it; the library did not verify it."}


def review_queue() -> Dict[str, Any]:
    """What waits on a HUMAN. The counter never promotes; it only decides when a person looks."""
    acted = {c["card_id"] for c in _read("curation.jsonl")}
    waiting = [d for d in _read("drops.jsonl")
               if (d.get("extra") or {}).get("ring") == "commons" and d["id"] not in acted]
    waiting.sort(key=lambda c: (c.get("created_at") or 0))
    return {"ok": True, "count": len(waiting),
            "items": [{"card_id": d["id"], "title": d.get("title"),
                       "member": (d.get("extra") or {}).get("member"),
                       "kind": (d.get("extra") or {}).get("drop_kind"),
                       "at": d.get("created_at")} for d in waiting],
            "note": "A steward promotes or refuses, and either way says why."}


_CURATE_FIELDS = ("action", "at", "card_id", "member", "nonce")


def signable_curate(card_id: str, member: str, action: str = "withdrawn") -> Dict[str, Any]:
    """The canonical bytes for a MEMBER's own act on their OWN card — today, withdrawal.

    A member does not need anyone's permission to take their own words down, so this path exists
    beside the steward token: the proof is the same key that signed the drop in the first place."""
    card_id, member, action = (card_id or "").strip(), (member or "").strip(), (action or "").strip()
    if action != "withdrawn":
        return {"ok": False, "error": "a member may withdraw their own card; promoting and "
                                      "refusing are a steward's acts"}
    if not card_id or not member:
        return {"ok": False, "error": "which card, and whose?"}
    fields = {"card_id": card_id, "member": member, "action": action,
              "nonce": secrets.token_urlsafe(12), "at": int(time.time())}
    canon = json.dumps({k: fields.get(k) for k in _CURATE_FIELDS}, sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
    return {"ok": True, "fields": fields,
            "signable": base64.urlsafe_b64encode(canon).decode("ascii"),
            "note": "sign these exact bytes with the same key that signed the drop"}


def _steward_authorized(token: str) -> bool:
    """A steward's act needs a steward. Reuses the operator gate the keep already uses
    (`CONCORDANCE_KEEP_TOKEN`, constant-time compare) rather than inventing a second secret —
    one authority, one place to rotate it. FAILS CLOSED: no token configured, no promotion."""
    from .web import keep as _keep
    return _keep.is_operator(token, None)


def _member_authorized(card_id: str, fields: Optional[Dict[str, Any]], signature: str) -> bool:
    """A member withdrawing their own card, proven by the key that signed the drop."""
    if not isinstance(fields, dict) or not signature:
        return False
    if str(fields.get("card_id") or "") != card_id or str(fields.get("action") or "") != "withdrawn":
        return False
    at = fields.get("at")
    if not isinstance(at, int) or abs(int(time.time()) - at) > SIGNATURE_TTL_S:
        return False
    member = str(fields.get("member") or "")
    owner = next((d for d in _read("drops.jsonl") if d.get("id") == card_id), None)
    if not owner or (owner.get("extra") or {}).get("member") != member:
        return False   # you may withdraw YOUR card, not someone else's
    canon = json.dumps({k: fields.get(k) for k in _CURATE_FIELDS}, sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
    from . import signing
    try:
        return bool(signing.verify_bytes(canon, signature, member))
    except Exception:  # noqa: BLE001 — an unusable signature is simply not authorization
        return False


def curate(card_id: str, action: str, steward: str, reason: str = "", token: str = "",
           fields: Optional[Dict[str, Any]] = None, signature: str = "") -> Dict[str, Any]:
    """A recorded act on one drop: `promoted` · `refused` · `withdrawn`.

    Every act names who did it and carries a reason — there is no anonymous judgement here, and a
    refusal that gives no reason teaches the community nothing. Acts are appended, never replaced:
    a later act supersedes an earlier one and both remain readable.

    WHO MAY ACT. C1a took the name on faith, and C1b shipped that to the live box for a few
    minutes: any passer-by could have promoted their own drop into the commons or pulled someone
    else's card down, because a name is a string anyone can type. Two authorizations now, and
    nothing else:

      * `promoted` / `refused` — the STEWARD token. These decide what the whole library amplifies,
        so they belong to whoever answers for the library.
      * `withdrawn` — the steward token OR the member's own signature over `signable_curate`
        bytes. A member never needs permission to take their own words down.

    Fails closed: no token and no valid member signature means no act.
    """
    card_id, action, steward = (card_id or "").strip(), (action or "").strip(), (steward or "").strip()
    if action not in ("promoted", "refused", "withdrawn"):
        return {"ok": False, "error": "action must be promoted, refused, or withdrawn"}
    if not card_id:
        return {"ok": False, "error": "which card?"}
    if not steward:
        return {"ok": False, "error": "no anonymous judgement — a steward's act carries a name"}
    if not (reason or "").strip():
        return {"ok": False, "error": "a reason is required; a refusal without one teaches the "
                                      "community nothing and an approval without one teaches us "
                                      "nothing"}
    if not any(d["id"] == card_id for d in _read("drops.jsonl")):
        return {"ok": False, "error": "no such drop"}
    by_steward = _steward_authorized(token)
    by_member = (action == "withdrawn"
                 and not by_steward
                 and _member_authorized(card_id, fields, signature))
    if not (by_steward or by_member):
        return {"ok": False, "error": (
            "not authorized. Promoting or refusing is a steward's act and needs the steward token; "
            "withdrawing your own card needs your own signature over /curate/signable bytes. A "
            "typed name is not authority — anyone can type a name.")}
    rec = {"card_id": card_id, "action": action, "steward": steward,
           "reason": reason.strip()[:500], "at": int(time.time()),
           "by": "steward" if by_steward else "member"}
    _append("curation.jsonl", rec)
    return {"ok": True, **rec,
            "note": ("Promoted to the commons — still the member's own words, at the member "
                     "tier." if action == "promoted" else
                     "Recorded with its reason. The drop stays on the member's own shelf; only "
                     "amplification was withheld." if action == "refused" else
                     "Withdrawn from the shelf view. The record remains.")}


def history(card_id: str) -> Dict[str, Any]:
    """Every act on one drop, oldest first. Append-only means the trail is always there: what we
    did, who did it, and why — including the times we changed our minds."""
    acts = [c for c in _read("curation.jsonl") if c.get("card_id") == (card_id or "").strip()]
    acts.sort(key=lambda c: c.get("at") or 0)
    return {"ok": True, "card_id": card_id, "acts": acts, "count": len(acts)}


__all__ = ["signable_drop", "signable_curate", "drop", "shelf_of", "commons", "review_queue",
           "curate", "history", "RINGS", "KINDS", "MEMBER_TIER", "SIGNATURE_TTL_S"]
