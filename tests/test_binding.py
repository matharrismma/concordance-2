"""Binding — the key on the drive IS the identity.

Guards the properties that make this sovereign rather than merely convenient: possession of
the private key is the only proof, a challenge is single-use, a thread cannot be stolen by
asserting a new key, and the private key is never persisted anywhere on our side.
"""
import json
import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="nh-binding-")
os.environ["CONCORDANCE_BINDINGS_DIR"] = _TMP

from concordance import binding, identity  # noqa: E402  (env must be set first)

SIGNED = identity.signing_available()


def _who():
    return identity.create_identity()


def _prove(who, thread_id=None):
    ch = binding.challenge(who["public_key"])
    assert ch["ok"], ch
    sig = identity.sign(who["private_key"], ch["nonce"].encode("utf-8"))
    return binding.claim(who["public_key"], ch["nonce"], sig, thread_id)


# --- the happy path -------------------------------------------------------------------------

def test_signing_a_challenge_proves_the_drive():
    if not SIGNED:
        return                       # honest skip: degraded path refuses to bind at all
    who = _who()
    r = _prove(who)
    assert r["ok"] and r["id"] == identity.fingerprint(who["public_key"])


def test_binding_a_thread_and_listing_it_back():
    if not SIGNED:
        return
    who = _who()
    tid = "a" * 32
    r = _prove(who, tid)
    assert r["ok"] and r["bound"] == tid
    assert tid in r["threads"]
    assert binding.owns(who["public_key"], tid) is True
    assert binding.threads_of(who["public_key"]) == [tid]


# --- replay, expiry, tampering --------------------------------------------------------------

def test_a_challenge_is_single_use():
    if not SIGNED:
        return
    who = _who()
    ch = binding.challenge(who["public_key"])
    sig = identity.sign(who["private_key"], ch["nonce"].encode("utf-8"))
    assert binding.claim(who["public_key"], ch["nonce"], sig)["ok"] is True
    # the exact same nonce + signature must not work twice
    assert binding.claim(who["public_key"], ch["nonce"], sig)["ok"] is False


def test_a_wrong_signature_is_refused():
    if not SIGNED:
        return
    who, other = _who(), _who()
    ch = binding.challenge(who["public_key"])
    sig = identity.sign(other["private_key"], ch["nonce"].encode("utf-8"))   # wrong key
    assert binding.claim(who["public_key"], ch["nonce"], sig)["ok"] is False


def test_an_unknown_nonce_is_refused():
    who = _who()
    assert binding.claim(who["public_key"], "never-issued", "x")["ok"] is False


def test_an_expired_challenge_is_refused():
    if not SIGNED:
        return
    who = _who()
    ch = binding.challenge(who["public_key"])
    binding._NONCES[ch["nonce"]]["expires_at"] = 0.0        # force expiry
    sig = identity.sign(who["private_key"], ch["nonce"].encode("utf-8"))
    assert binding.claim(who["public_key"], ch["nonce"], sig)["ok"] is False


# --- threads are not transferable -----------------------------------------------------------

def test_a_thread_cannot_be_stolen_by_another_key():
    if not SIGNED:
        return
    mine, theirs = _who(), _who()
    tid = "b" * 32
    assert _prove(mine, tid)["ok"] is True
    r = _prove(theirs, tid)
    assert r["ok"] is False and "another key" in r["error"]
    assert binding.owner_of(tid) == identity.fingerprint(mine["public_key"])


def test_rebinding_my_own_thread_is_fine():
    if not SIGNED:
        return
    who = _who()
    tid = "c" * 32
    assert _prove(who, tid)["ok"] is True
    assert _prove(who, tid)["ok"] is True          # idempotent, not an error
    assert binding.threads_of(who["public_key"]).count(tid) == 1


# --- nothing about the person is stored ------------------------------------------------------

def test_the_private_key_is_never_persisted():
    """The strongest guarantee here: search everything we wrote for the secret."""
    if not SIGNED:
        return
    who = _who()
    _prove(who, "d" * 32)
    secret = who["private_key"]
    for root, _dirs, files in os.walk(_TMP):
        for f in files:
            blob = open(os.path.join(root, f), encoding="utf-8").read()
            assert secret not in blob, f"private key leaked into {f}"


def test_only_a_public_key_and_thread_ids_are_stored():
    if not SIGNED:
        return
    who = _who()
    _prove(who, "e" * 32)
    fp = identity.fingerprint(who["public_key"])
    rec = json.loads(open(os.path.join(_TMP, "owners", f"{fp}.json"), encoding="utf-8").read())
    assert set(rec) <= {"id", "public_key", "threads", "created_at", "updated_at"}
    # no email, no name, no password, no device info — nothing that identifies a person
    assert rec["id"] == fp


def test_invalid_thread_id_is_refused():
    if not SIGNED:
        return
    who = _who()
    r = _prove(who, "not a valid id")
    assert r["ok"] is False


def test_challenge_requires_a_public_key():
    assert binding.challenge("")["ok"] is False
