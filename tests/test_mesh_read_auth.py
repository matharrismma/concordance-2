"""The bulletin board is yours alone — mesh.read_door / inbox require PROOF of the node's key.

Closes the gap where anyone who knew a confessed node's fingerprint could read the words on its door
(and its inbox). A fingerprint is public; holding the key is not. Needs the cryptography library for
real Ed25519 proofs, and skips without it.
"""
import os
import tempfile
import time
import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from concordance import identity, mesh, signing  # noqa: E402

CRYPTO = identity.signing_available()


@pytest.mark.skipif(not CRYPTO, reason="needs the cryptography library for real Ed25519 proofs")
def test_door_and_inbox_require_proof_of_key():
    tmp = tempfile.mkdtemp()
    saved = {k: os.environ.get(k) for k in ("CONCORDANCE_DATA_DIR", "CONCORDANCE_MESH_DIR")}
    os.environ["CONCORDANCE_DATA_DIR"] = tmp
    os.environ.pop("CONCORDANCE_MESH_DIR", None)   # so the mesh store is tmp/mesh
    try:
        me = identity.create_identity()
        pub, priv = me["public_key"], me["private_key"]
        reg = mesh.register_node(pub, callsign="tester", confession="Jesus Christ is Lord and Messiah")
        assert reg.get("ok") is True, reg
        fp = reg.get("fp") or identity.fingerprint(pub)
        now = int(time.time())
        good = signing.sign_bytes(mesh._mesh_read_challenge(fp, now), priv)

        # PROVEN — the node's own key over a fresh challenge — serves (zero notes is still ok:True)
        assert mesh.read_door(fp, at=now, signature=good).get("ok") is True
        assert mesh.inbox(fp, at=now, signature=good).get("ok") is True

        # NO PROOF — the gap, closed: knowing the fingerprint reads nothing
        assert mesh.read_door(fp).get("unproven") is True
        assert mesh.inbox(fp).get("unproven") is True

        # WRONG KEY — a valid signature by someone else's key does not open your door
        other = identity.create_identity()
        wrong = signing.sign_bytes(mesh._mesh_read_challenge(fp, now), other["private_key"])
        assert mesh.read_door(fp, at=now, signature=wrong).get("unproven") is True

        # STALE — a real signature over an old timestamp is past its replay window
        old_at = now - 100000
        stale = signing.sign_bytes(mesh._mesh_read_challenge(fp, old_at), priv)
        assert mesh.read_door(fp, at=old_at, signature=stale).get("unproven") is True

        # UNKNOWN fingerprint — refused as "unproven", never revealing whether a node exists
        assert mesh.read_door("nh_" + ("0" * 32), at=now, signature=good).get("unproven") is True
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


if __name__ == "__main__":  # runnable without pytest
    if CRYPTO:
        test_door_and_inbox_require_proof_of_key()
        print("ok: test_door_and_inbox_require_proof_of_key")
    else:
        print("skip: no cryptography library")
    print("done")
