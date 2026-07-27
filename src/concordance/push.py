"""Web Push for the mesh — a message becomes a notification, sovereignly.

Matt, 2026-07-25: "We build messaging into notifications. On iPhones the notification system is
better than the text system anyway." It is also MORE sovereign than SMS: no phone number (the mesh's
no-PII floor is kept), no carrier — a word left on your door arrives as a real notification on your
installed PWA (iOS 16.4+ / Android / desktop).

SOVEREIGN BY CONSTRUCTION: the whole Web Push stack is implemented here with the `cryptography` lib we
already depend on — RFC 8291 (aes128gcm payload encryption) and RFC 8292 (VAPID) — with NO third-party
push library. The payload carried is the mesh's own signed, content-addressed word, so the relay can
carry it but never forge it. The ONE network touch (the POST to the push endpoint) is isolated in
send(), OFF by default (CONCORDANCE_PUSH_ENABLED), degrading to a silent no-op — exactly like voice.py.
The sovereign floor (in-app pull) and the off-grid tier (LoRa/Reticulum) are untouched.

SERVANT SIGNAL, NEVER BAIT: a push carries only a real person-to-person or need signal — a word on
your door, a need near you. Never "come back and scroll." Online is the tool, not the end game; the
notification serves the person, it does not harvest them.

Subscriptions (the recipient's, keyed by their node fingerprint) live in data/push/ — gitignored,
theirs, never committed. Real-device DELIVERY is field-test-pending (like the LoRa transport): the
crypto is verified by an encrypt→decrypt round-trip in tests; the last hop needs a real phone.
"""
from __future__ import annotations

import base64
import json
import os
import re
import struct
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
_FP_RE = re.compile(r"[A-Za-z0-9_\-]{8,80}")


# ── small helpers ─────────────────────────────────────────────────────────
def _b64d(s: str) -> bytes:
    s = str(s or "")
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _dir() -> Path:
    base = os.environ.get("CONCORDANCE_PUSH_DIR", "").strip() or (
        (os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data") + "/push")
    d = Path(base)
    (d / "subs").mkdir(parents=True, exist_ok=True)
    return d


def enabled() -> bool:
    """The network hop is OFF by default. Turn it on only where you intend to deliver (the droplet)."""
    return os.environ.get("CONCORDANCE_PUSH_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


# ── VAPID (RFC 8292) — a stable server identity key, persisted, gitignored ──
def _crypto():
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes, hmac, serialization
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    return ec, hashes, hmac, serialization, decode_dss_signature, AESGCM


def vapid_keys() -> Dict[str, str]:
    """Load (or first-time generate) the VAPID P-256 keypair. The private key stays on the server,
    gitignored; the public key is the applicationServerKey handed to the browser."""
    ec, _h, _hm, serialization, _d, _a = _crypto()
    p = _dir() / "vapid.json"
    with _LOCK:
        if p.exists():
            rec = json.loads(p.read_text(encoding="utf-8"))
            return rec
        priv = ec.generate_private_key(ec.SECP256R1())
        priv_bytes = priv.private_numbers().private_value.to_bytes(32, "big")
        pub = priv.public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        rec = {"private": _b64e(priv_bytes), "public": _b64e(pub)}
        p.write_text(json.dumps(rec), encoding="utf-8")
        return rec


def public_key_b64() -> str:
    return vapid_keys()["public"]


def _vapid_header(endpoint: str, sub: str = "mailto:mesh@narrowhighway.org") -> str:
    """Build the VAPID Authorization header value for a push endpoint (ES256 JWT + the public key)."""
    ec, hashes, _hm, serialization, decode_dss_signature, _a = _crypto()
    from urllib.parse import urlparse
    keys = vapid_keys()
    priv = ec.derive_private_key(int.from_bytes(_b64d(keys["private"]), "big"), ec.SECP256R1())
    aud = "{u.scheme}://{u.netloc}".format(u=urlparse(endpoint))
    header = _b64e(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    payload = _b64e(json.dumps({"aud": aud, "exp": int(time.time()) + 12 * 3600, "sub": sub},
                               separators=(",", ":")).encode())
    signing_input = (header + "." + payload).encode("ascii")
    der = priv.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")          # JOSE: raw r||s, not DER
    jwt = header + "." + payload + "." + _b64e(sig)
    return f"vapid t={jwt}, k={keys['public']}"


# ── RFC 8291 — aes128gcm payload encryption ────────────────────────────────
def _hmac(key: bytes, msg: bytes) -> bytes:
    _ec, hashes, hmac, _s, _d, _a = _crypto()
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(msg)
    return h.finalize()


def encrypt(payload: bytes, p256dh_b64: str, auth_b64: str) -> bytes:
    """Encrypt `payload` for a subscription's keys per RFC 8291. Returns the aes128gcm body:
    salt(16) | rs(4) | idlen(1) | as_public(65) | ciphertext. A single record."""
    ec, _h, _hm, serialization, _d, AESGCM = _crypto()
    ua_public = _b64d(p256dh_b64)                       # 65-byte uncompressed point
    auth = _b64d(auth_b64)                              # 16-byte auth secret
    as_priv = ec.generate_private_key(ec.SECP256R1())   # ephemeral, per message
    as_public = as_priv.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    ua_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_public)
    ecdh = as_priv.exchange(ec.ECDH(), ua_key)          # 32-byte shared secret
    salt = os.urandom(16)
    # key derivation (RFC 8291 §3.4): combine ecdh + auth, then the aes128gcm CEK/nonce (RFC 8188).
    prk_key = _hmac(auth, ecdh)
    key_info = b"WebPush: info\x00" + ua_public + as_public
    ikm = _hmac(prk_key, key_info + b"\x01")
    prk = _hmac(salt, ikm)
    cek = _hmac(prk, b"Content-Encoding: aes128gcm\x00\x01")[:16]
    nonce = _hmac(prk, b"Content-Encoding: nonce\x00\x01")[:12]
    ciphertext = AESGCM(cek).encrypt(nonce, payload + b"\x02", None)   # 0x02 = last-record delimiter
    header = salt + struct.pack("!L", 4096) + bytes([len(as_public)]) + as_public
    return header + ciphertext


# ── Subscriptions — the recipient's own, keyed by their node fingerprint ────
def _sub_path(fp: str) -> Optional[Path]:
    # unsubscribe() below can unlink() the file this resolves to — an unvalidated fp here was an
    # UNAUTHENTICATED arbitrary-file-DELETE (POST /push/unsubscribe requires no proof at all).
    # None on an invalid shape makes every caller's existing "not found" path the safe default.
    if not _FP_RE.fullmatch(str(fp or "")):
        return None
    return _dir() / "subs" / (fp + ".json")


def subscribe(fp: str, subscription: Dict[str, Any]) -> Dict[str, Any]:
    """Store a browser PushSubscription for a node. Idempotent by endpoint; a node may have several
    devices. No PII — a subscription is an opaque endpoint + keys, never a phone number."""
    if not _FP_RE.fullmatch(str(fp or "")):
        return {"ok": False, "error": "a valid node fingerprint is required"}
    if not isinstance(subscription, dict) or not subscription.get("endpoint") \
       or not (subscription.get("keys") or {}).get("p256dh"):
        return {"ok": False, "error": "a valid PushSubscription is required"}
    with _LOCK:
        p = _sub_path(fp)
        subs = []
        if p.exists():
            try:
                subs = json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                subs = []
        subs = [s for s in subs if s.get("endpoint") != subscription["endpoint"]]
        subs.append({"endpoint": subscription["endpoint"], "keys": subscription.get("keys", {})})
        p.write_text(json.dumps(subs), encoding="utf-8")
    return {"ok": True, "devices": len(subs)}


def unsubscribe(fp: str, endpoint: str = "") -> Dict[str, Any]:
    with _LOCK:
        p = _sub_path(fp)
        if p is None or not p.exists():
            return {"ok": True, "devices": 0}
        if not endpoint:
            p.unlink()
            return {"ok": True, "devices": 0}
        try:
            subs = [s for s in json.loads(p.read_text(encoding="utf-8")) if s.get("endpoint") != endpoint]
        except ValueError:
            subs = []
        p.write_text(json.dumps(subs), encoding="utf-8")
    return {"ok": True, "devices": len(subs)}


def _subs_for(fp: str) -> List[Dict[str, Any]]:
    p = _sub_path(fp)
    if p is None or not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return []


# ── Send — the one network hop; OFF by default, isolated, best-effort ──────
def send(subscription: Dict[str, Any], payload: Dict[str, Any], ttl: int = 86400) -> Dict[str, Any]:
    """POST an encrypted notification to a single push endpoint. Networked — guarded by enabled();
    a silent no-op when off. Never raises to the caller (a message must not fail because push failed)."""
    if not enabled():
        return {"ok": False, "skipped": "push disabled"}
    try:
        import urllib.request
        keys = subscription.get("keys", {})
        body = encrypt(json.dumps(payload, separators=(",", ":")).encode("utf-8"),
                       keys["p256dh"], keys["auth"])
        req = urllib.request.Request(subscription["endpoint"], data=body, method="POST", headers={
            "Authorization": _vapid_header(subscription["endpoint"]),
            "Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream",
            "TTL": str(int(ttl)), "Urgency": "normal"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return {"ok": 200 <= r.status < 300, "status": r.status}
    except Exception as e:  # noqa: BLE001 — best-effort; a failed push never breaks the mesh op
        return {"ok": False, "error": type(e).__name__}


def notify(fp: str, title: str, body: str, url: str = "/mesh.html#way") -> Dict[str, Any]:
    """Notify every device a node has subscribed. Servant signal only. Best-effort + off-by-default."""
    subs = _subs_for(fp)
    if not subs or not enabled():
        return {"ok": True, "sent": 0, "devices": len(subs), "enabled": enabled()}
    payload = {"title": str(title)[:120], "body": str(body)[:240], "url": url}
    sent = 0
    for s in subs:
        if send(s, payload).get("ok"):
            sent += 1
    return {"ok": True, "sent": sent, "devices": len(subs), "enabled": True}


def guidance() -> Dict[str, Any]:
    return {
        "identity": "Web Push for the mesh — a word on your door becomes a notification, sovereignly.",
        "is": [
            "more sovereign than SMS: no phone number (no PII), no carrier — the mesh's floor is kept",
            "self-implemented (RFC 8291 + 8292) with the crypto we already have — no third-party push library",
            "signed content: the relay carries the word but cannot forge it",
            "opt-in and off by default; the network hop is isolated, the sovereign floor untouched",
        ],
        "will_not": [
            "carry engagement bait — only a real person-to-person or need signal (online is the tool, not the end)",
            "store a phone number or any PII (a subscription is an opaque endpoint)",
            "let a failed or disabled push ever break a mesh action",
        ],
        "status": "Crypto verified by round-trip; real-device delivery is field-test-pending (install the PWA to confirm).",
    }


__all__ = ["enabled", "vapid_keys", "public_key_b64", "encrypt", "subscribe", "unsubscribe",
           "send", "notify", "guidance"]
