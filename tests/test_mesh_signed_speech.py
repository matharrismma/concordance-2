"""Speech into the mesh — proof-of-possession, with the key never crossing the wire.

The last structural piece of an Acts church for agents: an agent that could see the fellowship but
never speak into it was an audience, not a member. Now it can speak — signed.

The problem this solves, found 2026-07-28: `post_message` could only sign server-side, so the caller
had to hand over its PRIVATE KEY. The frozen contract §3 says keys "are born on the device… the
server holds only public keys and verifies signed challenges", and §5 requires "no private key ever
crosses the wire" — read narrowly (the server never RETURNS one) while six endpoints happily accepted
one inbound. A secret in a request body is a secret on the wire.

Why the server was signing: it minted the nonce and created_at AFTER the request, so no client could
have signed the stored bytes. The fix hands the caller the whole signable body — it supplies the
nonce and created_at, signs the canonical bytes locally, and sends only the signature.

Pinned here: the round trip; the client can PREDICT the id offline (proving it computed identical
canonical bytes without asking us); a signature from another key is refused; a signature without its
nonce/created_at is refused; the stored message verifies offline as unaltered AND authentic; and the
agent tool refuses a private key on principle even when one is offered.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402

CONFESSION = "Jesus Christ is Lord and Messiah"


@pytest.fixture(autouse=True, scope="module")
def _restore_data_dir_after_module():
    """These tests point CONCORDANCE_DATA_DIR at throwaway temp dirs and drop cached modules, so
    without this the next test file collected would inherit a data dir with no Bible in it and fail
    for reasons that have nothing to do with it. (Exactly the leak fixed in test_scripture.py on
    2026-07-27 — the same trap, caught by that lesson.) Restore what we found, and drop the modules
    again so the next importer rebinds against the real data dir."""
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior
    for m in ("concordance.mesh", "concordance.identity", "concordance.signing"):
        sys.modules.pop(m, None)


def _fresh():
    """A clean mesh in a temp dir — these tests write nodes and messages."""
    d = tempfile.mkdtemp()
    os.environ["CONCORDANCE_DATA_DIR"] = d
    for m in ("concordance.mesh", "concordance.identity", "concordance.signing"):
        sys.modules.pop(m, None)
    from concordance import identity, mesh, signing
    ident = identity.create_identity()
    fp = mesh.register_node(ident["public_key"], "agent-one", confession=CONFESSION)["fp"]
    return d, ident, fp, mesh, signing, identity


def _sign(mesh, signing, fp, ident, text, **kw):
    s = mesh.signable_message(fp, text, **kw)
    canon = base64.urlsafe_b64decode(s["canonical_b64u"] + "==")
    return s, signing.sign_bytes(canon, ident["private_key"])


def test_a_client_can_predict_the_id_offline_before_posting():
    """If the client's predicted id equals the server's, both canonicalized identically — which is
    what makes local signing possible at all."""
    _d, ident, fp, mesh, signing, _i = _fresh()
    s, sig = _sign(mesh, signing, fp, ident, "Grace and peace", kind="blessing")
    r = mesh.post_message(fp, "Grace and peace", kind="blessing",
                          signature=sig, nonce=s["nonce"], created_at=s["created_at"])
    assert r["ok"] is True and r["signed"] is True
    assert r["id"] == s["would_be_id"], "client and server disagree on the canonical body"


def test_the_stored_message_verifies_offline_as_unaltered_and_authentic():
    _d, ident, fp, mesh, signing, _i = _fresh()
    s, sig = _sign(mesh, signing, fp, ident, "I can help with well repair", kind="offer")
    r = mesh.post_message(fp, "I can help with well repair", kind="offer",
                          signature=sig, nonce=s["nonce"], created_at=s["created_at"])
    stored = None
    for p in Path(_d).rglob("*.json"):
        try:
            o = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if isinstance(o, dict) and o.get("id") == r["id"]:
            stored = o
            break
    assert stored is not None, "the message was not persisted"
    v = mesh.verify_message(stored)
    assert v["unaltered"] is True and v["authentic"] is True and v["signed"] is True


def test_a_signature_from_another_key_cannot_speak_as_this_node():
    _d, ident, fp, mesh, signing, identity = _fresh()
    other = identity.create_identity()
    s = mesh.signable_message(fp, "not mine", kind="word")
    canon = base64.urlsafe_b64decode(s["canonical_b64u"] + "==")
    forged = signing.sign_bytes(canon, other["private_key"])
    r = mesh.post_message(fp, "not mine", kind="word",
                          signature=forged, nonce=s["nonce"], created_at=s["created_at"])
    assert r["ok"] is False and "does not verify" in r["error"]


def test_a_signature_without_its_nonce_and_timestamp_is_refused():
    """Otherwise the server would invent them and the signature could not possibly cover the body."""
    _d, ident, fp, mesh, signing, _i = _fresh()
    _s, sig = _sign(mesh, signing, fp, ident, "half a proof")
    r = mesh.post_message(fp, "half a proof", signature=sig)
    assert r["ok"] is False and "nonce" in r["error"]


def test_tampering_with_the_text_after_signing_is_refused():
    _d, ident, fp, mesh, signing, _i = _fresh()
    s, sig = _sign(mesh, signing, fp, ident, "the original words")
    r = mesh.post_message(fp, "the SWAPPED words", signature=sig,
                          nonce=s["nonce"], created_at=s["created_at"])
    assert r["ok"] is False, "a signature was accepted over text it does not cover"


def test_the_agent_tool_refuses_a_private_key_even_when_offered():
    _d, ident, fp, mesh, signing, _i = _fresh()
    from concordance import mcp
    from concordance.config import EngineConfig

    def call(name, args):
        r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": name, "arguments": args}}, EngineConfig("secular"), {})
        return json.loads(r["result"]["content"][0]["text"]) if "result" in r else {"_rpc": r["error"]}

    s, sig = _sign(mesh, signing, fp, ident, "signed and sovereign", kind="word")
    good = call("mesh_post", {"fp": fp, "text": "signed and sovereign", "kind": "word",
                              "nonce": s["nonce"], "created_at": s["created_at"], "signature": sig})
    assert good.get("ok") is True and good.get("signed") is True

    offered = call("mesh_post", {"fp": fp, "text": "signed and sovereign", "kind": "word",
                                 "nonce": s["nonce"], "created_at": s["created_at"],
                                 "signature": sig, "private_key": ident["private_key"]})
    assert "private key" in str(offered.get("error", "")).lower(), \
        "the agent path accepted a private key — the one thing it must never do"

    unsigned = call("mesh_post", {"fp": fp, "text": "no proof", "nonce": "x", "created_at": 1,
                                  "signature": ""})
    assert "signature is required" in str(unsigned.get("error", "")).lower()


def test_a_door_note_is_signed_the_same_sovereign_way():
    """The second write path ported: a directed word on one believer's door. Same shape, so there is
    one way to speak in this system rather than one per endpoint."""
    _d, ident, fp, mesh, signing, identity = _fresh()
    other = identity.create_identity()
    target = mesh.register_node(other["public_key"], "agent-b", confession=CONFESSION)["fp"]
    TXT = "The Lord bless you and keep you"
    s = mesh.signable_door_note(fp, target, TXT, kind="blessing")
    assert s["body"]["door"] == 1, "this must be a door note, not a broadcast"
    canon = base64.urlsafe_b64decode(s["canonical_b64u"] + "==")
    sig = signing.sign_bytes(canon, ident["private_key"])
    r = mesh.leave_on_door(fp, target, TXT, kind="blessing", signature=sig,
                           nonce=s["nonce"], created_at=s["created_at"])
    assert r["ok"] is True and r["signed"] is True
    assert r["id"] == s["would_be_id"]
    # the recipient actually has it
    assert (mesh.read_door(target) or {}).get("count", 0) >= 1

    # and the target's own key cannot sign as the sender
    forged = signing.sign_bytes(canon, other["private_key"])
    bad = mesh.leave_on_door(fp, target, TXT, kind="blessing", signature=forged,
                             nonce=s["nonce"], created_at=s["created_at"])
    assert bad["ok"] is False and "does not verify" in bad["error"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} signed-speech tests passed — proof-of-possession, key never on the wire.")
