"""Signing test — Ed25519 seal attestations (the soulbound receipt).

Proves: a keypair signs a seal's content_hash and verification holds; a wrong hash or a
tampered packet fails; seal_record(sign_key=...) attaches a verifiable attestation.
Requires the optional `cryptography` dep — skips cleanly if absent. Runnable with
`pytest` OR `python tests/test_signing.py`.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import EngineConfig, ledger, validate_and_seal  # noqa: E402
from concordance import signing  # noqa: E402

try:
    signing.generate_keypair()
    _HAS_CRYPTO = True
except Exception:
    _HAS_CRYPTO = False


def test_sign_and_verify_seal():
    if not _HAS_CRYPTO:
        print("  skip (cryptography not installed)")
        return
    priv, pub = signing.generate_keypair()
    h = "a" * 64
    att = signing.sign_seal(h, priv)
    assert att["pubkey"] == pub and att["alg"] == "ed25519"
    ok, _ = signing.verify_seal(h, att)
    assert ok
    bad, _ = signing.verify_seal("b" * 64, att)  # different content_hash
    assert not bad


def test_packet_sign_verify_tamper():
    if not _HAS_CRYPTO:
        return
    priv, pub = signing.generate_keypair()
    signed = signing.sign_packet({"claim": "x", "n": 1}, priv)
    ok, _ = signing.verify_packet(signed, pub)
    assert ok
    signed["n"] = 2  # tamper
    bad, _ = signing.verify_packet(signed, pub)
    assert not bad


def test_seal_record_attaches_verifiable_attestation():
    if not _HAS_CRYPTO:
        return
    priv, pub = signing.generate_keypair()
    with tempfile.TemporaryDirectory() as t:
        ld, cb = Path(t) / "ledger", Path(t) / "cas"
        rec = validate_and_seal(
            {"domain": "combinatorics",
             "COMB_VERIFY": {"comb_n": 5, "comb_k": 2, "claimed_combinations": 10},
             "created_epoch": 1_700_000_000, "required_witnesses": 0},
            now_epoch=1_700_000_000 + 3601, config=EngineConfig())
        assert rec.overall == "PASS"
        res = ledger.seal_record(rec, summary="signed seal", ledger_dir=ld, cas_base=cb,
                                 sealed_at=1000.0, sign_key=priv)
        assert "attestation" in res, "sign_key should attach an attestation"
        assert res["attestation"]["pubkey"] == pub
        ok, _ = signing.verify_seal(res["content_hash"], res["attestation"])
        assert ok, "the attestation must verify against the seal's content_hash"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    tag = "" if _HAS_CRYPTO else " (cryptography absent — signing tests skipped)"
    print(f"\n{len(fns)} signing tests passed — Ed25519 seal attestations hold{tag}.")
