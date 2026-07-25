"""Web Push — the crypto must be right, and the network hop must stay off by default.

The delivery leg needs a real phone (field-test-pending), but RFC 8291 encryption is fully checkable
here: encrypt with the server side, then DECRYPT with the receiver's private key exactly as a browser
would, and confirm the payload round-trips. A wrong info string, HKDF step, or framing byte breaks it.
"""
from __future__ import annotations

import base64
import os
import struct
import tempfile

import pytest

from concordance import push


@pytest.fixture()
def push_dir(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_PUSH_DIR", tempfile.mkdtemp(prefix="push_"))
    monkeypatch.delenv("CONCORDANCE_PUSH_ENABLED", raising=False)
    yield


def _b64e(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _decrypt(body, ua_priv, ua_public, auth):
    """Reverse RFC 8291 with the receiver's private key — what a compliant browser does."""
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, idlen = body[:16], body[20]
    as_public = body[21:21 + idlen]
    ct = body[21 + idlen:]
    as_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), as_public)
    ecdh = ua_priv.exchange(ec.ECDH(), as_key)
    prk_key = push._hmac(auth, ecdh)
    key_info = b"WebPush: info\x00" + ua_public + as_public
    ikm = push._hmac(prk_key, key_info + b"\x01")
    prk = push._hmac(salt, ikm)
    cek = push._hmac(prk, b"Content-Encoding: aes128gcm\x00\x01")[:16]
    nonce = push._hmac(prk, b"Content-Encoding: nonce\x00\x01")[:12]
    pt = AESGCM(cek).decrypt(nonce, ct, None)
    assert pt.endswith(b"\x02")                     # the last-record delimiter
    return pt[:-1]


def test_rfc8291_encrypt_round_trips(push_dir):
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    ua_priv = ec.generate_private_key(ec.SECP256R1())
    ua_public = ua_priv.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    auth = os.urandom(16)
    msg = b'{"title":"A word on your door","body":"Grace and peace","url":"/mesh.html#way"}'
    body = push.encrypt(msg, _b64e(ua_public), _b64e(auth))
    # framing: salt(16) | rs(4)=4096 | idlen(1)=65 | as_public(65) | ciphertext
    assert struct.unpack("!L", body[16:20])[0] == 4096 and body[20] == 65
    assert _decrypt(body, ua_priv, ua_public, auth) == msg


def test_vapid_header_is_a_signed_jwt(push_dir):
    pub = push.public_key_b64()
    assert len(base64.urlsafe_b64decode(pub + "==")) == 65      # uncompressed P-256 point
    hdr = push._vapid_header("https://web.push.apple.com/abc123")
    assert hdr.startswith("vapid t=") and ", k=" in hdr
    jwt = hdr.split("t=", 1)[1].split(",", 1)[0]
    assert jwt.count(".") == 2                                  # header.payload.signature


def test_subscribe_store_and_no_pii(push_dir):
    fp = "nh_" + "a" * 20
    sub = {"endpoint": "https://web.push.apple.com/xyz", "keys": {"p256dh": _b64e(os.urandom(65)), "auth": _b64e(os.urandom(16))}}
    assert push.subscribe(fp, sub)["devices"] == 1
    assert push.subscribe(fp, sub)["devices"] == 1              # idempotent by endpoint
    assert push.unsubscribe(fp)["devices"] == 0
    assert push.subscribe("not a fingerprint", sub)["ok"] is False


def test_network_hop_is_off_by_default(push_dir):
    assert push.enabled() is False
    fp = "nh_" + "b" * 20
    push.subscribe(fp, {"endpoint": "https://example.com/e", "keys": {"p256dh": _b64e(os.urandom(65)), "auth": _b64e(os.urandom(16))}})
    r = push.notify(fp, "test", "test")                        # must NOT touch the network
    assert r["ok"] is True and r["sent"] == 0 and r["enabled"] is False
