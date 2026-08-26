"""The Profile — your keeping keyed by fingerprint, sovereign and account-free.

profile.py is user-facing (the member surface behind /profile) and security-critical: every write is
SIGNED, and replay is refused three ways — a spent nonce, a stale timestamp, and op domain-separation
(a 'put' signature is not a valid 'delete'). It had no dedicated test. These prove the good path AND
that each defense actually bites: a stranger's signature, a captured-and-replayed write, and a
put-signature aimed at erasing all fail closed, while the anonymous default (no key, no profile) stays
untouched. Real keypairs, real signatures — no mock stands in for the crypto being tested.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import identity, profile, signing  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    """Each test writes into its own data dir — profile.put persists under data/profiles."""
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))


@pytest.fixture
def keys():
    priv, pub = signing.generate_keypair()
    return priv, pub


def _put(priv, pub, patch, nonce="n1", op="put", ts=None):
    """Sign and submit a write exactly as the browser would."""
    ts = int(time.time()) if ts is None else ts
    sig = signing.sign_bytes(profile.signable(pub, patch, nonce, op, ts), priv)
    return profile.put(pub, patch, nonce, sig, ts)


# ---- the anonymous default ----

def test_absent_profile_is_empty_not_an_error(keys):
    _priv, pub = keys
    assert profile.get(identity.fingerprint(pub)) == {}
    assert profile.get("") == {} and profile.get(None) == {}   # no key, no profile


# ---- signable: canonical + op domain-separation ----

def test_signable_is_deterministic_and_op_separated(keys):
    _priv, pub = keys
    a = profile.signable(pub, {"x": 1}, "n", "put", 100)
    assert a == profile.signable(pub, {"x": 1}, "n", "put", 100)   # deterministic
    assert a != profile.signable(pub, {"x": 1}, "n", "delete", 100)  # put != delete bytes
    assert a != profile.signable(pub, {"x": 1}, "n", "put", 101)     # ts is bound


# ---- put: the good path ----

def test_signed_put_persists_and_reads_back(keys):
    priv, pub = keys
    r = _put(priv, pub, {"display_name": "Matt", "wants": ["seed corn"]})
    assert r["ok"], r
    fp = identity.fingerprint(pub)
    assert r["id"] == fp
    got = profile.get(fp)
    assert got["display_name"] == "Matt" and got["wants"] == ["seed corn"]
    assert not any(k.startswith("_") for k in got), "internal bookkeeping leaked into the public view"


# ---- put: input guards ----

def test_put_rejects_bad_patch_and_missing_nonce(keys):
    priv, pub = keys
    assert not profile.put(pub, "not a dict", "n", "sig")["ok"]
    ts = int(time.time())
    huge = {"blob": "x" * (65 * 1024)}
    sig = signing.sign_bytes(profile.signable(pub, huge, "n", "put", ts), priv)
    assert profile.put(pub, huge, "n", sig, ts)["error"] == "patch too large"
    assert not _put(priv, pub, {"a": 1}, nonce="")["ok"], "an empty nonce must be refused"


# ---- put: the three replay defenses ----

def test_put_refuses_a_stale_timestamp(keys):
    priv, pub = keys
    r = _put(priv, pub, {"a": 1}, ts=int(time.time()) - 10_000)   # far outside the freshness window
    assert not r["ok"] and "stale" in r["error"]


def test_put_refuses_a_stranger_signature(keys):
    _priv, pub = keys
    intruder_priv, _intruder_pub = signing.generate_keypair()
    # the intruder signs a write aimed at the victim's key — ownership is by signature, so it fails
    r = _put(intruder_priv, pub, {"a": "hijacked"})
    assert not r["ok"] and "signature does not verify" in r["error"]
    assert profile.get(identity.fingerprint(pub)) == {}, "a refused write must leave nothing behind"


def test_put_refuses_a_replayed_nonce(keys):
    priv, pub = keys
    assert _put(priv, pub, {"a": 1}, nonce="once")["ok"]
    replay = _put(priv, pub, {"a": 2}, nonce="once")     # same nonce, fresh everything else
    assert not replay["ok"] and "replay" in replay["error"]
    assert profile.get(identity.fingerprint(pub))["a"] == 1, "the replay must not have overwritten"


def test_patch_cannot_write_internal_keys(keys):
    priv, pub = keys
    r = _put(priv, pub, {"visible": "yes", "_owner": "evil", "_nonces": ["forged"]})
    assert r["ok"], r
    stored = profile._load(identity.fingerprint(pub))
    assert stored["_owner"] == pub, "the patch overwrote the owner key"
    assert "forged" not in stored["_nonces"], "the patch forged the nonce ledger"
    assert r["profile"].get("visible") == "yes"


# ---- delete: signed erase, op-separated ----

def test_signed_delete_erases_own_profile(keys):
    priv, pub = keys
    assert _put(priv, pub, {"a": 1})["ok"]
    ts = int(time.time())
    sig = signing.sign_bytes(profile.signable(pub, {}, "d1", "delete", ts), priv)
    r = profile.delete(pub, "d1", sig, ts)
    assert r["ok"] and r["erased"] is True
    assert profile.get(identity.fingerprint(pub)) == {}


def test_delete_of_nothing_is_ok_but_erased_false(keys):
    priv, pub = keys
    ts = int(time.time())
    sig = signing.sign_bytes(profile.signable(pub, {}, "d", "delete", ts), priv)
    r = profile.delete(pub, "d", sig, ts)
    assert r["ok"] and r["erased"] is False


def test_a_put_signature_cannot_delete(keys):
    """op domain-separation: a captured 'put' signature must not double as an erase token."""
    priv, pub = keys
    assert _put(priv, pub, {"a": 1})["ok"]
    ts = int(time.time())
    put_sig = signing.sign_bytes(profile.signable(pub, {}, "d", "put", ts), priv)  # signed op='put'
    r = profile.delete(pub, "d", put_sig, ts)                                       # used as a delete
    assert not r["ok"] and "signature does not verify" in r["error"]
    assert profile.get(identity.fingerprint(pub))["a"] == 1, "the profile was erased by a put signature"


def test_delete_needs_a_fresh_timestamp_and_a_key(keys):
    priv, pub = keys
    stale = int(time.time()) - 10_000
    sig = signing.sign_bytes(profile.signable(pub, {}, "d", "delete", stale), priv)
    assert not profile.delete(pub, "d", sig, stale)["ok"]
    # an empty key fingerprints to a fixed hash (never falsy), so this fails at signature verify,
    # not the public_key guard — either way, no key means no erase
    assert not profile.delete("", "d", "sig", int(time.time()))["ok"], "no key, no erase"


# ---- reachable error paths (the guard actually bites) ----

def test_put_refuses_a_non_numeric_timestamp(keys):
    """A ts that is not an int must be treated as missing, not crash the write path (_fresh guard)."""
    priv, pub = keys
    sig = signing.sign_bytes(profile.signable(pub, {"a": 1}, "n", "put", 0), priv)
    r = profile.put(pub, {"a": 1}, "n", sig, "not-a-number")
    assert not r["ok"] and "stale" in r["error"]


def test_a_corrupt_store_reads_as_empty_not_a_crash(keys):
    """A garbage byte-run where a profile should be must read as the anonymous default, never raise."""
    _priv, pub = keys
    fp = identity.fingerprint(pub)
    p = profile._path(fp)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{ this is not json", encoding="utf-8")
    assert profile.get(fp) == {}
    assert profile._load(fp) == {}


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
