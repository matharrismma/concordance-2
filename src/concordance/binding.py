"""Binding — the key on your drive IS the identity, and it is what your threads answer to.

No account. No password. No email. No row about you. The only thing this server learns is a
public key and the ids of threads it is already storing — nothing that could be compelled out
of us is anything you did not already hand over.

How it works (docs/THE_COMPANION.md §4.2, §6a):
  1. Your drive holds an Ed25519 keypair (`identity.create_identity()`; the private key is
     handed to you ONCE and is never persisted here).
  2. To claim a thread you ask for a **challenge** (a single-use nonce), sign it with the
     private key on the drive, and send the signature back. The server verifies with the
     public key alone.
  3. **Possession of the drive is the whole proof.** Plug it in and the conversation is yours;
     unplug it and this server knows nothing about you.

The honest cost: there is no recovery backdoor. Lose the drive and you lose the thread. Keeping
a second copy is *your* choice, never a silent server-side default — a backdoor we could open
for you is a backdoor that can be opened without you.

Refusals, on purpose:
  - If real signing is unavailable, binding is REFUSED rather than faked. An identity that
    cannot be proven is not an identity.
  - A thread already owned by someone else is never re-bound. Threads are not transferable by
    asserting a new key.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import identity

CHALLENGE_TTL = 300.0          # seconds — long enough to sign, short enough to be useless later
_NONCES: Dict[str, Dict[str, Any]] = {}   # nonce -> {public_key, expires_at}. Memory only.


def _dir() -> Path:
    env = os.environ.get("CONCORDANCE_BINDINGS_DIR", "").strip()
    if env:
        return Path(env)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    if data:
        return Path(data) / "bindings"
    return Path("data") / "bindings"


def _owner_path(fp: str) -> Path:
    return _dir() / "owners" / f"{fp}.json"


def _thread_path(thread_id: str) -> Path:
    return _dir() / "threads" / f"{thread_id}.json"


def _read(p: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write(p: Path, rec: Dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")


def _prune() -> None:
    now = time.time()
    for n in [n for n, v in _NONCES.items() if v["expires_at"] < now]:
        _NONCES.pop(n, None)


def challenge(public_key: str) -> Dict[str, Any]:
    """Mint a single-use nonce for this public key. Signing it proves possession of the drive."""
    _prune()
    if not isinstance(public_key, str) or not public_key.strip():
        return {"ok": False, "error": "public_key required"}
    if not identity.signing_available():
        return {"ok": False, "error": "signing unavailable — binding refused rather than faked"}
    nonce = secrets.token_urlsafe(32)
    _NONCES[nonce] = {"public_key": public_key.strip(), "expires_at": time.time() + CHALLENGE_TTL}
    return {"ok": True, "nonce": nonce, "expires_in": int(CHALLENGE_TTL),
            "sign_this": nonce,
            "note": "sign this nonce with the private key on your drive; it is single-use"}


def _spend(public_key: str, nonce: Any, signature: Any) -> Optional[str]:
    """Consume the nonce and verify the signature. -> fingerprint, or None if not proven."""
    _prune()
    if not isinstance(nonce, str) or not isinstance(signature, str):
        return None
    rec = _NONCES.pop(nonce, None)                     # single-use: spent on sight
    if not rec or rec["public_key"] != (public_key or "").strip():
        return None
    if rec["expires_at"] < time.time():
        return None
    if not identity.verify(public_key, nonce.encode("utf-8"), signature):
        return None
    return identity.fingerprint(public_key)


def prove(public_key: str, nonce: Any, signature: Any) -> Optional[str]:
    """Public: prove possession of the drive for any operation, not just binding.

    -> the owner fingerprint, or None. Spends the nonce (single-use), so callers must send
    each proof exactly once. Used by anything that must answer only to the key-holder.
    """
    if not identity.signing_available():
        return None
    return _spend(public_key, nonce, signature)


def claim(public_key: str, nonce: Any, signature: Any,
          thread_id: Optional[str] = None) -> Dict[str, Any]:
    """Prove the drive, optionally bind a thread, and return everything this key owns."""
    if not identity.signing_available():
        return {"ok": False, "error": "signing unavailable — binding refused rather than faked"}
    fp = _spend(public_key, nonce, signature)
    if not fp:
        return {"ok": False, "error": "not proven — bad, expired, or already-spent challenge"}

    owner = _read(_owner_path(fp)) or {
        "id": fp, "public_key": public_key.strip(), "threads": [],
        "created_at": round(time.time(), 3),
    }
    bound = None
    if thread_id:
        from . import threads as threads_mod
        if not threads_mod._valid_id(thread_id):
            return {"ok": False, "error": "invalid thread_id"}
        existing = _read(_thread_path(thread_id))
        if existing and existing.get("owner") != fp:
            # Threads are not transferable by asserting a new key.
            return {"ok": False, "error": "thread already bound to another key"}
        if not existing:
            _write(_thread_path(thread_id), {"thread_id": thread_id, "owner": fp,
                                             "bound_at": round(time.time(), 3)})
        if thread_id not in owner["threads"]:
            owner["threads"].append(thread_id)
        bound = thread_id

    owner["updated_at"] = round(time.time(), 3)
    _write(_owner_path(fp), owner)
    return {"ok": True, "id": fp, "bound": bound, "threads": list(owner["threads"]),
            "note": "possession of the drive is the proof; no account, no password, nothing stored about you"}


def attach(owner: str, thread_id: str) -> bool:
    """Bind a thread to an already-proven owner (the caller proved the key this request).

    Used by surfaces that create a thread on a person's behalf — the thread must belong to
    them from the first exchange, not merely be protected by an unguessable id.
    """
    if not owner or not thread_id:
        return False
    existing = _read(_thread_path(thread_id))
    if existing and existing.get("owner") != owner:
        return False                      # never re-home someone else's thread
    if not existing:
        _write(_thread_path(thread_id), {"thread_id": thread_id, "owner": owner,
                                         "bound_at": round(time.time(), 3)})
    rec = _read(_owner_path(owner)) or {"id": owner, "public_key": "", "threads": [],
                                        "created_at": round(time.time(), 3)}
    if thread_id not in rec["threads"]:
        rec["threads"].append(thread_id)
    rec["updated_at"] = round(time.time(), 3)
    _write(_owner_path(owner), rec)
    return True


def owner_of(thread_id: str) -> Optional[str]:
    """The fingerprint that owns this thread, if any."""
    rec = _read(_thread_path(thread_id or ""))
    return (rec or {}).get("owner")


def owns(public_key: str, thread_id: str) -> bool:
    """Does this public key own this thread? (Identity only — not a proof of possession.)"""
    if not public_key or not thread_id:
        return False
    return owner_of(thread_id) == identity.fingerprint(public_key)


def threads_of(public_key: str) -> List[str]:
    """Thread ids bound to this key. Callers must authenticate before exposing this."""
    if not public_key:
        return []
    rec = _read(_owner_path(identity.fingerprint(public_key)))
    return list((rec or {}).get("threads", []))
