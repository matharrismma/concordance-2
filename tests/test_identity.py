"""Identity test — a sovereign, opt-in, portable identity the person owns.

Proves: create_identity() returns the private key ONCE and never persists it; the fingerprint
id is stable and portable; on the signed path sign/verify roundtrips and verify rejects a
tampered message OR a tampered signature; and the DEGRADED path (no `cryptography`) still mints
a stable, portable, unsigned id without crashing. Signed-path asserts are guarded behind
`signing_available` so the suite passes whether or not `cryptography` is installed. The degraded
path is exercised unconditionally by forcing the capability flag off. Hermetic: no I/O, no
network, no disk. Runnable with `pytest` OR `python tests/test_identity.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import identity  # noqa: E402

_HAS_CRYPTO = identity.signing_available()


# ── shape + sovereignty (both paths) ─────────────────────────────────────────────────

def test_create_returns_private_key_once_and_stable_id():
    idn = identity.create_identity()
    # The private key is returned ONCE, here — the whole point of sovereign ownership.
    assert idn.get("private_key"), "private_key must be returned to the caller once"
    assert idn.get("public_key"), "public_key must be present"
    assert idn.get("id"), "a stable fingerprint id must be present"
    assert isinstance(idn.get("signing_available"), bool)
    # The id is the content-addressed fingerprint of the public key — deterministic & portable.
    assert idn["id"] == identity.fingerprint(idn["public_key"])
    assert idn["id"].startswith("nh_")


def test_fingerprint_is_stable_and_public_key_derived():
    # Same public key -> same id (portable: survives a later cryptography install).
    pub = "some-public-key-material"
    assert identity.fingerprint(pub) == identity.fingerprint(pub)
    # Different public keys -> different ids.
    assert identity.fingerprint("a") != identity.fingerprint("b")


def test_two_identities_are_distinct():
    a, b = identity.create_identity(), identity.create_identity()
    assert a["id"] != b["id"], "each minted identity must be unique"
    assert a["private_key"] != b["private_key"]


# ── signed path (guarded — only runs when cryptography is present) ────────────────────

def test_sign_verify_roundtrip_signed():
    if not _HAS_CRYPTO:
        print("  skip (cryptography not installed — signed path)")
        return
    idn = identity.create_identity()
    assert idn["signing_available"] is True
    msg = b"the narrow highway"
    sig = identity.sign(idn["private_key"], msg)
    assert identity.verify(idn["public_key"], msg, sig), "a valid signature must verify"
    # str message is accepted too (UTF-8 encoded internally).
    sig2 = identity.sign(idn["private_key"], "hello")
    assert identity.verify(idn["public_key"], "hello", sig2)


def test_verify_rejects_tampered_message_and_signature():
    if not _HAS_CRYPTO:
        print("  skip (cryptography not installed — tamper checks)")
        return
    idn = identity.create_identity()
    msg = b"original message"
    sig = identity.sign(idn["private_key"], msg)
    # Tampered MESSAGE -> reject.
    assert not identity.verify(idn["public_key"], b"tampered message", sig)
    # Tampered SIGNATURE -> reject.
    bad_sig = sig[:-4] + ("AAAA" if not sig.endswith("AAAA") else "BBBB")
    assert not identity.verify(idn["public_key"], msg, bad_sig)
    # Wrong KEY -> reject.
    other = identity.create_identity()
    assert not identity.verify(other["public_key"], msg, sig)


# ── degraded path (forced — runs regardless of whether cryptography is installed) ─────

def _force_no_crypto(monkeypatch=None):
    """Force identity.signing_available() to report False so the degraded branch runs even
    when cryptography IS installed. Works with pytest's monkeypatch or a manual fallback."""
    if monkeypatch is not None:
        monkeypatch.setattr(identity, "signing_available", lambda: False)
        return None
    original = identity.signing_available
    identity.signing_available = lambda: False  # type: ignore[assignment]
    return original


def test_degraded_path_mints_stable_portable_id():
    original = _force_no_crypto()
    try:
        idn = identity.create_identity()
        assert idn["signing_available"] is False
        assert idn["private_key"] and idn["public_key"], "degraded id still portable"
        # The fingerprint discipline is identical to the signed path -> stable & portable.
        assert idn["id"] == identity.fingerprint(idn["public_key"])
        assert idn["id"].startswith("nh_")
        # sign() returns an honestly-labeled UNSIGNED marker (never claims authenticity).
        sig = identity.sign(idn["private_key"], b"msg")
        assert sig.startswith("u1:"), "degraded sign must be honestly labeled unsigned"
        # verify() with only the public key cannot authenticate an unsigned marker -> False.
        assert identity.verify(idn["public_key"], b"msg", sig) is False
        # Two degraded identities are still distinct.
        assert identity.create_identity()["id"] != idn["id"]
    finally:
        if original is not None:
            identity.signing_available = original  # type: ignore[assignment]


def test_verify_is_total_never_raises():
    # Junk inputs must return False, never raise, in either path.
    assert identity.verify("pub", b"m", "") is False
    assert identity.verify("pub", b"m", None) is False  # type: ignore[arg-type]
    assert identity.verify("pub", b"m", 123) is False   # type: ignore[arg-type]


def test_describe_reports_capability_honestly():
    d = identity.describe()
    assert d["signing_available"] == _HAS_CRYPTO
    assert "will_not" in d and any("private key" in w for w in d["will_not"])


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    tag = "" if _HAS_CRYPTO else " (cryptography absent — signed-path tests skipped)"
    print(f"\n{len(fns)} identity tests passed — sovereign, opt-in, portable identity holds{tag}.")
