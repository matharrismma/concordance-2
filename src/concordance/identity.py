"""Identity — a SOVEREIGN, OPT-IN, PORTABLE identity the person OWNS.

A person is not an account on our server; they are a keypair they hold. This module
mints a portable identity whose PRIVATE KEY is returned to the caller ONCE and is NEVER
stored server-side. What we persist/reference is only the stable public FINGERPRINT — a
content-addressed id derived from the public key. The person can walk away with their key
and re-prove who they are anywhere; nothing here binds them to us.

    idn = create_identity()          # {id, public_key, private_key, signing_available}
    #   idn["private_key"]  -> hand to the user ONCE, then forget it (never persisted)
    #   idn["id"]           -> the stable fingerprint we may reference
    sig = sign(idn["private_key"], b"message")
    verify(idn["public_key"], b"message", sig)   # True

Success is measured the John 3:30 way: the person needs the tool LESS. A key they own is
theirs to take. We reference the fingerprint; we do not own the person.

TWO PATHS, ONE INTERFACE:
  * SIGNED (preferred) — when the optional `cryptography` package is present, the identity is
    a real Ed25519 keypair. sign()/verify() carry cryptographic proof; verify() rejects any
    tampered message or signature. `signing_available` is True.
  * DEGRADED (never crash) — when `cryptography` is absent, we still mint a usable, PORTABLE,
    content-addressed local id: a random 32-byte "public key" (b64u) and a stable fingerprint
    derived from it. There is no real signing, so sign() returns an honest UNSIGNED marker and
    verify() only confirms the marker binds to that public key + message (integrity, not
    authenticity). `signing_available` is False. The id is still stable and portable.

The fingerprint is computed the same way in BOTH paths, so an id minted while degraded stays
valid if `cryptography` is later installed for the same public key material.

Sovereign: stdlib + the shared signing primitives (which lazily need `cryptography` only on
the signed path). No I/O, no persistence — pure functions returning new dicts. Secrets never
touch disk here; the caller owns the private key.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any, Dict, Optional

from . import signing

# Version tag baked into the fingerprint domain so ids are self-describing and future
# fingerprint schemes can coexist without collision.
_FP_VERSION = "nhid1"
# Prefix on every fingerprint id so it is recognizable and namespaced.
_ID_PREFIX = "nh"
# Length (hex chars) of the fingerprint digest kept in the id. 32 hex = 128 bits — ample
# collision resistance for a public reference while staying short enough to show a user.
_FP_HEX_LEN = 32


def signing_available() -> bool:
    """Capability flag: True iff real Ed25519 signing is available (the `cryptography`
    package is importable). When False, create_identity() degrades to an unsigned, stable,
    content-addressed local id — it never crashes."""
    try:
        signing.generate_keypair()
        return True
    except Exception:  # noqa: BLE001 — any import/runtime failure means "not available"
        return False


def fingerprint(public_key: str) -> str:
    """Derive the stable public id from a public key (b64u).

    Deterministic and path-independent: the same public_key always yields the same id, in
    both the signed and degraded paths, so an id survives a later install of `cryptography`.
    Content-addressed via SHA-256 over a version-tagged domain (mirrors cas.py's discipline)."""
    material = f"{_FP_VERSION}:{public_key or ''}".encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()[:_FP_HEX_LEN]
    return f"{_ID_PREFIX}_{digest}"


def create_identity() -> Dict[str, Any]:
    """Mint a sovereign, portable identity the person owns.

    Returns {id, public_key, private_key, signing_available}. The `private_key` is returned
    ONCE, here, and is NEVER persisted server-side — the caller must hand it to the user and
    then forget it. Only the `id` (fingerprint) is safe to reference/persist.

    Signed path (cryptography present): a real Ed25519 keypair.
    Degraded path (cryptography absent): a random 32-byte public key (b64u) with an unsigned
    private-key marker — the id is still stable and portable; sign()/verify() are honest about
    the lack of authenticity via `signing_available`.
    """
    if signing_available():
        priv, pub = signing.generate_keypair()
        return {
            "id": fingerprint(pub),
            "public_key": pub,
            "private_key": priv,   # returned ONCE — caller owns it; never stored by us
            "signing_available": True,
        }
    # Degraded: no cryptography. Still portable and content-addressed.
    pub_bytes = os.urandom(32)
    priv_bytes = os.urandom(32)
    pub = signing._b64u_encode(pub_bytes)   # same b64u encoding as the signed path
    priv = signing._b64u_encode(priv_bytes)
    return {
        "id": fingerprint(pub),
        "public_key": pub,
        "private_key": priv,   # local-only secret; still never persisted by us
        "signing_available": False,
    }


# ── sign / verify — one interface over both paths ────────────────────────────────────

# Marker prefix for the degraded (unsigned) path so a caller can always tell an authenticated
# signature from an integrity-only marker. verify() enforces the distinction.
_UNSIGNED_TAG = "u1:"


def _as_bytes(msg: Any) -> bytes:
    if isinstance(msg, bytes):
        return msg
    return str(msg).encode("utf-8")


def _unsigned_marker(private_key: str, message: bytes) -> str:
    """Degraded-path 'signature': an HMAC binding the message to the private key material.

    This is NOT authentication (the verifier only holds the public key, not this secret, so it
    cannot recompute the HMAC) — it is a self-consistency/integrity marker so the degraded path
    has a stable, honestly-labeled return value. Real authenticity requires the signed path."""
    tag = hmac.new(private_key.encode("utf-8"), message, hashlib.sha256).hexdigest()[:32]
    return f"{_UNSIGNED_TAG}{tag}"


def sign(private_key: str, msg: Any) -> str:
    """Sign a message with a private key. Returns a b64u Ed25519 signature on the signed path,
    or an honestly-labeled unsigned integrity marker (prefixed `u1:`) on the degraded path.

    The message may be bytes or str (str is UTF-8 encoded)."""
    message = _as_bytes(msg)
    if signing_available():
        return signing.sign_bytes(message, private_key)
    return _unsigned_marker(private_key, message)


def verify(public_key: str, msg: Any, sig: str) -> bool:
    """Verify a signature over a message against a public key. Returns True/False; never raises.

    Signed path: real Ed25519 verification — rejects a tampered message OR a tampered signature.
    Degraded path: a signature is only ever the unsigned marker (`u1:`); with only the public
    key we cannot recompute the HMAC secret, so degraded verify() returns False for real (signed)
    signatures and treats the marker as unverifiable-by-public-key. Authenticity lives on the
    signed path alone — this keeps the degraded path from ever *claiming* authenticity it lacks.
    """
    if not isinstance(sig, str) or not sig:
        return False
    message = _as_bytes(msg)
    if sig.startswith(_UNSIGNED_TAG):
        # An unsigned marker can never be authenticated by a public key alone — say so honestly.
        return False
    if signing_available():
        return signing.verify_bytes(message, sig, public_key)
    return False


def describe() -> Dict[str, Any]:
    """What this identity is, and the boundary it keeps — for a capabilities/identity surface."""
    avail = signing_available()
    return {
        "identity": "A sovereign, opt-in, portable identity the person owns.",
        "signing_available": avail,
        "mode": "ed25519" if avail else "unsigned-content-addressed",
        "owns": [
            "the private key — returned to you ONCE, never stored on our side",
            "a stable public fingerprint id — the only thing we reference",
        ],
        "will_not": [
            "store your private key server-side (ever)",
            "bind you to us — take your key and re-prove yourself anywhere",
        ],
        "note": ("Success is you needing the tool less (John 3:30). A key you hold is yours to "
                 "carry. We point to the fingerprint; we do not own the person."),
    }


__all__ = [
    "signing_available",
    "create_identity",
    "fingerprint",
    "sign",
    "verify",
    "describe",
]
