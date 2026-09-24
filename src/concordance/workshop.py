"""THE WORKSHOP — the operator's improvement queue. You file through the site; the agent drains it.

Matt, 2026-09-23: *"Can you create an interface with narrowhighway, so I can begin working to
improve it through the site? We can structure you as a call back."*

This is that interface, built on the bones already here rather than beside them: the append-only
ledger of the want list (`wants.py`) and the detached-signature discipline of the member shelf
(`shelves.py`). It is the QUEEN's cousin, with one deliberate inversion.

  * The want list records **no** requester identity — a want is a fact about the library's gaps,
    never about the person who found one (privacy by construction).
  * The Workshop is the exact opposite: it is the OPERATOR's own tasking, so every filing is
    **provably you** (a detached Ed25519 signature over canonical bytes) and **verbatim** (no
    scrub — your words are meant to be recorded and acted on, not anonymised).

TWO GATES, and they are not the same question (a typed name is not authority):

  1. AUTHENTICITY — the filing carries the author's public key and a signature over the canonical
     bytes of the fields; `_verify` checks the signature against that key. This proves possession
     of the key. It proves nothing about *authorization*.
  2. AUTHORIZATION — the signer's fingerprint must be in the operator allowlist
     (`CONCORDANCE_OPERATOR_FPS`, a box config; fingerprints are public, safe to pin). A valid
     signature from an UNLISTED key is refused: anyone can hold a key; only an operator may task
     the queue. Unset allowlist => filing is CLOSED (fail-safe, default lock-in).

THE DRAIN (the "call back"). The agent that services the queue is NOT the operator and must never
hold the operator's private key. So the drain — reading the queue and marking status — is gated at
the API layer by the EXISTING operator gate (`keep.request_is_operator`: the box's
`CONCORDANCE_KEEP_TOKEN` or an allow-listed IP, fail-closed, X-Forwarded-For never trusted for
access), reusing the one operator concept rather than minting a second secret. Filing (write) is
signed by the operator's covenant key; draining (read + status) uses the keep operator gate; the two
credentials are separate on purpose — a machine drainer never needs the operator's private key.

NEVER EXECUTES. The Workshop only records intent and status. Nothing here edits the corpus, deploys,
or touches a live system — the agent does the work in the repo, through tests and an explicit deploy,
exactly as always. The steward records; it does not execute.

Store: `data/workshop.jsonl`, append-only, box-local (gitignored), re-read fresh. Offline-tolerant
(a jsonl file; no internet for a week means the queue waits a week). Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import identity

_LOCK = threading.Lock()

# The kinds of improvement a filing can be — a closed set so every item reads the same way.
KINDS = ("improve", "fix", "observe", "feature", "question")
# open -> in_progress -> done | declined. `declined` is the drainer's recorded refusal, never silent.
STATES = ("open", "in_progress", "done", "declined")

SIGNATURE_TTL_S = 900          # signed bytes are good for 15 minutes — a replay window, not a life
# The fields covered by the signature. `target` is the empty string when a filing names no target;
# empty-but-present keeps ONE canonicalisation for every kind (the shelf's discipline).
_SIGNED_FIELDS = ("at", "author", "body", "kind", "nonce", "target", "title")

MAX_TITLE = 200
MAX_BODY = 8000
MAX_TARGET = 200
MAX_NOTE = 2000


def _path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "workshop.jsonl"


def _canon(fields: Dict[str, Any]) -> bytes:
    """The exact bytes both sides sign and verify — sorted-key JSON over the signed fields, nothing
    else. The same canonicalisation the shelf, consent and moderation use, so one signing routine
    serves the whole house."""
    return json.dumps({k: fields.get(k) for k in _SIGNED_FIELDS}, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


# ── the operator gates ───────────────────────────────────────────────────────────────────────

def operator_fps() -> set:
    """The fingerprints authorized to FILE — from `CONCORDANCE_OPERATOR_FPS` (comma/space
    separated). Read fresh each call so config can change without a restart. Empty/unset => the
    queue is unclaimed and filing is closed (fail-safe)."""
    raw = os.environ.get("CONCORDANCE_OPERATOR_FPS", "")
    return {t for t in raw.replace(",", " ").split() if t}


def is_operator(public_key: str) -> bool:
    """True iff the key's fingerprint is an authorized operator. The check is on the fingerprint
    (public, deterministic from the key), never on a self-asserted name."""
    return identity.fingerprint((public_key or "").strip()) in operator_fps()


# ── the ledger (append-only; replaying events IS the state) ─────────────────────────────────────

def _append(ev: Dict[str, Any]) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")


def _events() -> List[Dict[str, Any]]:
    p = _path()
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue                     # a torn line is skipped, never fatal
    return out


def fold() -> Dict[str, Dict[str, Any]]:
    """The ledger, folded to current state. Dumb on purpose: replaying events IS the state."""
    items: Dict[str, Dict[str, Any]] = {}
    for ev in _events():
        wid = ev.get("id") or ""
        e = ev.get("ev")
        if e == "open":
            if wid in items:
                continue                     # a repeat open (same nonce) is idempotent, not a reset
            items[wid] = {"id": wid, "kind": ev.get("kind"), "title": ev.get("title", ""),
                          "body": ev.get("body", ""), "target": ev.get("target", ""),
                          "author_fp": ev.get("author_fp", ""), "state": "open",
                          "notes": [], "opened_at": ev.get("at"), "updated_at": ev.get("at")}
        elif wid not in items:
            continue                          # an event for an item never opened: ignored, dumbly
        elif e == "status":
            st = ev.get("state")
            if st in STATES:
                items[wid]["state"] = st
                items[wid]["updated_at"] = ev.get("at")
                items[wid]["by"] = ev.get("by", "")
                if ev.get("note"):
                    items[wid]["notes"].append({"at": ev.get("at"), "by": ev.get("by", ""),
                                                "text": ev.get("note", ""), "state": st})
        elif e == "note":
            items[wid]["notes"].append({"at": ev.get("at"), "by": ev.get("by", ""),
                                        "text": ev.get("note", "")})
            items[wid]["updated_at"] = ev.get("at")
    return items


# ── filing (signed + authorized) ─────────────────────────────────────────────────────────────

def signable(author: str, kind: str, title: str, body: str,
             target: str = "") -> Dict[str, Any]:
    """Step 1: the canonical bytes of a filing, ready to sign ON THE DEVICE. The server mints the
    nonce and the clock so the stored filing and the signed bytes cannot drift; the key never
    travels. Anyone may ASK for these bytes — signing them needs an operator's key, and filing them
    needs an operator's fingerprint.
    """
    author, kind = (author or "").strip(), (kind or "").strip()
    title, body, target = (title or "").strip(), (body or "").strip(), (target or "").strip()
    if not author:
        return {"ok": False, "error": "a filing needs the operator's public key"}
    if kind not in KINDS:
        return {"ok": False, "error": f"kind must be one of {list(KINDS)}"}
    if not title:
        return {"ok": False, "error": "a filing needs a title — one line on what to improve"}
    if len(title) > MAX_TITLE:
        return {"ok": False, "error": f"title over {MAX_TITLE} chars — shorten it"}
    if not body:
        return {"ok": False, "error": "a filing with no words is not a filing — say what you want"}
    if len(body) > MAX_BODY:
        return {"ok": False, "error": f"body over {MAX_BODY} chars — split it into more than one"}
    if len(target) > MAX_TARGET:
        return {"ok": False, "error": f"target over {MAX_TARGET} chars"}
    fields = {"at": int(time.time()), "author": author, "body": body, "kind": kind,
              "nonce": hashlib.sha256(os.urandom(16)).hexdigest()[:24], "target": target,
              "title": title}
    import base64
    return {"ok": True, "fields": fields,
            "signable": base64.urlsafe_b64encode(_canon(fields)).decode("ascii"),
            "note": "sign these exact bytes with your own key ON YOUR DEVICE, then send the fields "
                    "plus the signature. The private key never travels."}


def _verify(fields: Optional[Dict[str, Any]], signature: str) -> Dict[str, Any]:
    """Both gates, in order: the fields are well-formed and fresh, the signature verifies against
    the author's own key (AUTHENTICITY), and that key is an authorized operator (AUTHORIZATION)."""
    if not isinstance(fields, dict) or not isinstance(signature, str) or not signature.strip():
        return {"ok": False, "error": "signed fields and a signature are required — call "
                                      "signable() first and sign those bytes"}
    if "private_key" in fields:
        return {"ok": False, "error": "a detached signature is required — never a private key"}
    missing = [k for k in _SIGNED_FIELDS if k not in fields]
    if missing:
        return {"ok": False, "error": f"the signed fields must carry {list(_SIGNED_FIELDS)}; "
                                      f"missing {missing}"}
    if fields.get("kind") not in KINDS:
        return {"ok": False, "error": f"kind must be one of {list(KINDS)}"}
    author = str(fields.get("author") or "").strip()
    try:
        at = int(fields.get("at") or 0)
    except (TypeError, ValueError):
        return {"ok": False, "error": "the signed bytes carry no readable timestamp"}
    now = int(time.time())
    if not (now - SIGNATURE_TTL_S <= at <= now + 300):
        return {"ok": False, "error": "these signed bytes are stale — sign a fresh set"}
    from . import signing
    try:
        if not signing.verify_bytes(_canon(fields), signature.strip(), author):
            return {"ok": False, "error": "that signature does not verify against the named key"}
    except Exception:  # noqa: BLE001 — any verification error is simply "unverified"
        return {"ok": False, "error": "that signature does not verify against the named key"}
    # AUTHENTICITY passed; now AUTHORIZATION. A valid signature from a key that is not an operator
    # is a real signature by someone who may not task this queue — refuse it, and say why plainly.
    if not is_operator(author):
        return {"ok": False, "error": "that key is not an authorized operator — a valid signature "
                                      "proves you hold the key, not that you may file here"}
    return {"ok": True, "author": author, "fp": identity.fingerprint(author)}


def file(fields: Optional[Dict[str, Any]] = None, signature: str = "") -> Dict[str, Any]:
    """Step 2: verify both gates and record the filing. Append-only; the id is content-addressed on
    the author's fingerprint + the signed nonce, so the same signed bytes filed twice is ONE item,
    not two (idempotent under a client retry)."""
    v = _verify(fields, signature)
    if not v.get("ok"):
        return {"ok": False, "error": v["error"]}
    f = dict(fields or {})
    fp = v["fp"]
    wid = "wk_" + hashlib.sha1(f"{fp}|{f.get('nonce')}".encode("utf-8")).hexdigest()[:12]
    if wid in fold():
        return {"ok": True, "id": wid, "duplicate": True}   # a retry of the same signed filing
    _append({"ev": "open", "id": wid, "kind": f.get("kind"), "title": str(f.get("title"))[:MAX_TITLE],
             "body": str(f.get("body"))[:MAX_BODY], "target": str(f.get("target") or "")[:MAX_TARGET],
             "author_fp": fp, "signature": signature.strip(), "at": int(time.time())})
    return {"ok": True, "id": wid, "state": "open"}


# ── the drain (read + status; gated by the operator token at the API layer) ─────────────────────

def update(item_id: str, state: Optional[str] = None, note: str = "",
           by: str = "") -> Dict[str, Any]:
    """The drainer marks progress: a status change and/or a note. `by` names who acted (the agent
    or an operator label) — never anonymous. Recorded, never overwritten; the trail of the work is
    part of the record. The API gates this call behind the operator token."""
    if not str(by or "").strip():
        return {"ok": False, "error": "an update carries a name — who acted"}
    it = fold().get(item_id)
    if not it:
        return {"ok": False, "error": "no such item"}
    note = str(note or "").strip()[:MAX_NOTE]
    if state is not None:
        if state not in STATES:
            return {"ok": False, "error": f"state must be one of {list(STATES)}"}
        _append({"ev": "status", "id": item_id, "state": state, "note": note,
                 "by": str(by).strip()[:80], "at": int(time.time())})
        return {"ok": True, "id": item_id, "state": state}
    if not note:
        return {"ok": False, "error": "an update is a state change, a note, or both — this is neither"}
    _append({"ev": "note", "id": item_id, "note": note, "by": str(by).strip()[:80],
             "at": int(time.time())})
    return {"ok": True, "id": item_id, "noted": True}


def queue(state: Optional[str] = None, limit: int = 200) -> Dict[str, Any]:
    """The queue the drainer reads. Default shows OPEN and IN_PROGRESS (the live work); a specific
    `state` shows that one. Open first, then most-recently-updated. The API gates this behind the
    operator token — the queue is the operator's own tasking, not a public desk."""
    live = ("open", "in_progress")
    items = [it for it in fold().values()
             if (it["state"] == state if state else it["state"] in live)]
    # open before in_progress, then newest activity first
    order = {"open": 0, "in_progress": 1, "done": 2, "declined": 3}
    items.sort(key=lambda it: (order.get(it["state"], 9), -(it.get("updated_at") or 0)))
    return {"total": len(items), "items": items[: max(1, min(int(limit or 200), 500))]}
