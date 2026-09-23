"""The friend-gate — a shelf is served by PROOF, never by a bare (public) `viewer` param.

This pins the fix for two holes in shelf_of:
  1. the friend-gate: the `shelf` ring is scoped to proven MUTUAL friends, not anyone with the key;
  2. the private leak: naming the member's own (public) key as `viewer` no longer yields owner view —
     a valid signature from that key is required, so a stranger can no longer read `private`.

The ring-tier test needs no crypto; the proof tests need the `cryptography` library and skip without it.
"""
import os
import tempfile
import time
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from concordance import identity, shelves, signing  # noqa: E402

CRYPTO = identity.signing_available()


def test_ring_access_tiers():
    """owner sees every ring; a friend sees `shelf` (never `private`); the public floor sees only
    promoted commons — and the DEFAULT access is that safe public floor."""
    tmp = tempfile.mkdtemp()
    old = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tmp
    try:
        member = "PUBKEY_UNDER_TEST"
        now = int(time.time())
        for i, ring in enumerate(("private", "shelf", "commons")):
            shelves._append("drops.jsonl", {
                "id": "card_" + ring, "kind": "note", "title": ring, "body": "a " + ring + " note",
                "created_at": now - i, "extra": {"member": member, "ring": ring}})
        owner = shelves.shelf_of(member, access="owner")
        friend = shelves.shelf_of(member, access="friend")
        public = shelves.shelf_of(member, access="public")
        assert {c["extra"]["ring"] for c in owner["cards"]} == {"private", "shelf", "commons"}
        assert {c["extra"]["ring"] for c in friend["cards"]} == {"shelf"}   # no private, no unpromoted commons
        assert public["cards"] == []                                         # nothing promoted yet
        assert shelves.shelf_of(member)["access"] == "public"               # the safe default
    finally:
        if old is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = old


def test_no_proof_is_public_even_when_naming_the_owner_key():
    """THE LEAK, CLOSED: naming the member's own public key as viewer, with no valid signature, is
    the public floor — not owner view. This holds with or without the crypto library."""
    m = "A_PUBLIC_KEY_ANYONE_CAN_NAME"
    now = int(time.time())
    assert shelves.access_for(m, m, now, None) == "public"
    assert shelves.access_for(m, m, now, "") == "public"
    assert shelves.access_for(m, m, now, "not-a-real-signature") == "public"


@pytest.mark.skipif(not CRYPTO, reason="needs the cryptography library for real Ed25519 proofs")
def test_proof_decides_owner_friend_and_rejects_spoofs():
    me = identity.create_identity()
    pub, priv = me["public_key"], me["private_key"]
    other = identity.create_identity()
    opub, opriv = other["public_key"], other["private_key"]
    now = int(time.time())

    # a valid signature from the member's own key -> owner
    owner_sig = signing.sign_bytes(shelves._read_challenge(pub, pub, now), priv)
    assert shelves.access_for(pub, pub, now, owner_sig) == "owner"

    # a valid signature from another key, and they ARE a mutual friend -> friend; not a friend -> public
    fr_sig = signing.sign_bytes(shelves._read_challenge(pub, opub, now), opriv)
    assert shelves.access_for(pub, opub, now, fr_sig, friend_fn=lambda m, v: True) == "friend"
    assert shelves.access_for(pub, opub, now, fr_sig, friend_fn=lambda m, v: False) == "public"

    # a valid signature but a STALE timestamp -> public (the replay window has closed)
    old = now - 100000
    stale_sig = signing.sign_bytes(shelves._read_challenge(pub, pub, old), priv)
    assert shelves.access_for(pub, pub, old, stale_sig) == "public"

    # a signature by the WRONG key, claiming viewer==member -> does not verify -> public (no owner by spoof)
    wrong_sig = signing.sign_bytes(shelves._read_challenge(pub, pub, now), opriv)
    assert shelves.access_for(pub, pub, now, wrong_sig) == "public"


if __name__ == "__main__":  # runnable without pytest
    test_ring_access_tiers()
    print("ok: test_ring_access_tiers")
    test_no_proof_is_public_even_when_naming_the_owner_key()
    print("ok: test_no_proof_is_public_even_when_naming_the_owner_key")
    if CRYPTO:
        test_proof_decides_owner_friend_and_rejects_spoofs()
        print("ok: test_proof_decides_owner_friend_and_rejects_spoofs")
    else:
        print("skip: proof tests (no cryptography library)")
    print("all passed")
