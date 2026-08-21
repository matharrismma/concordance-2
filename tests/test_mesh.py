"""The Fellowship Mesh — the honest invariants that must hold for a network of believers.

A message is verifiable offline (unaltered by its own hash, authentic by signature); tampering is
caught; no PII is ever stored; you only see the nodes around you; a private key that is not the
node's cannot speak as it; crisis reaches real people. These are load-bearing — a mesh people trust
must prove them, not assert them.
"""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from concordance import identity, mesh, signing


@pytest.fixture()
def mesh_dir(monkeypatch):
    d = tempfile.mkdtemp(prefix="mesh_test_")
    monkeypatch.setenv("CONCORDANCE_MESH_DIR", d)
    yield d


def _node(callsign="anon", node_type="believer"):
    idn = identity.create_identity()
    r = mesh.register_node(idn["public_key"], callsign, node_type=node_type,
                           confession="Jesus Christ is Lord and Messiah")
    assert r["ok"], r
    return idn, r["fp"]


def _vouch(a, b):
    """A consensual MUTUAL link under the signed, directed-vouch model: BOTH parties sign a vouch for the
    other. (A single one-sided vouch does NOT form a link — that is the whole point of consent.)"""
    for x, y in ((a, b), (b, a)):
        n = "n" + y["id"][-8:]
        sig = signing.sign_bytes(mesh.link_signable(x["id"], y["id"], "link", n), x["private_key"])
        assert mesh.link(x["id"], y["id"], signature=sig, nonce=n)["ok"]


def test_register_is_keyed_by_fingerprint_and_idempotent(mesh_dir):
    idn = identity.create_identity()
    c = "Jesus Christ is Lord and Messiah"
    r1 = mesh.register_node(idn["public_key"], "Matt", confession=c)
    r2 = mesh.register_node(idn["public_key"], "Matthew")  # already inside — may refresh without re-confessing
    assert r1["fp"] == r2["fp"]                            # identity is the key, not the name
    assert r2["callsign"] == "Matthew"


def test_signed_message_verifies_offline_and_tamper_is_caught(mesh_dir):
    a, afp = _node("Berean")
    b, bfp = _node("Ruth")
    _vouch(a, b)
    r = mesh.post_message(afp, "grace and peace to you", private_key=a["private_key"])
    assert r["ok"] and r["signed"]
    got = mesh.inbox(bfp)["messages"][0]
    assert got["verify"] == {"unaltered": True, "authentic": True, "signed": True}
    # tamper the stored message body; both honest layers must now fail
    p = next((mesh._dir() / "msgs").glob("*.json"))
    m = json.loads(p.read_text(encoding="utf-8"))
    m["text"] = "grace and peace to you — and send money"
    p.write_text(json.dumps(m), encoding="utf-8")
    v = mesh.verify_message(m)
    assert v["unaltered"] is False and v["authentic"] is False


def test_an_unsigned_post_is_refused_but_a_cry_for_help_is_heard(mesh_dir):
    # POLICY (2026-08-21): a normal post must be signed — no one may put words in a node's name without
    # its key. THE ONE EXCEPTION is crisis-first: a cry for help is heard even unsigned.
    a, afp = _node("A")
    b, bfp = _node("B")
    _vouch(a, b)
    r = mesh.post_message(afp, "no key on this device", private_key=None)   # a normal post, unsigned
    assert r["ok"] is False and "signed" in r["error"]                     # refused
    assert mesh.inbox(bfp)["count"] == 0                                   # never delivered
    cry = mesh.post_message(afp, "i dont want to be here anymore", private_key=None)   # a cry for help
    assert cry["ok"] is True and cry["signed"] is False and "crisis" in cry            # heard even unsigned
    assert mesh.inbox(bfp)["count"] == 1                                   # the fellowship hears it


def test_a_foreign_key_cannot_speak_as_a_node(mesh_dir):
    a, afp = _node("A")
    imposter = identity.create_identity()            # a different key than node A registered
    r = mesh.post_message(afp, "this is A", private_key=imposter["private_key"])
    assert r["ok"] is False and "does not match" in r["error"]


def test_ttl_bounds_reach_like_a_lora_hop_limit(mesh_dir):
    a, afp = _node("A")
    b, bfp = _node("B")
    c, cfp = _node("C")
    _vouch(a, b)
    _vouch(b, c)                                     # chain A—B—C
    mesh.post_message(afp, "one hop only", ttl=1, private_key=a["private_key"])   # signed; reaches B, not C
    assert mesh.inbox(bfp)["count"] == 1
    assert mesh.inbox(cfp)["count"] == 0
    mesh.post_message(afp, "two hops", ttl=2, private_key=a["private_key"])       # now reaches C too
    assert mesh.inbox(cfp)["count"] == 1


def test_no_pii_or_private_key_ever_written(mesh_dir):
    a, afp = _node("SecretName")
    mesh.post_message(afp, "hello mesh", private_key=a["private_key"])
    blob = ""
    for root, _dirs, files in os.walk(mesh_dir):
        for f in files:
            blob += open(os.path.join(root, f), encoding="utf-8").read()
    assert a["private_key"] not in blob             # the drive's secret never touches the relay


def test_you_see_only_the_nodes_around_you(mesh_dir):
    a, afp = _node("A")
    b, bfp = _node("B")
    far, farfp = _node("Stranger")                   # registered, but linked to no one you know
    _vouch(a, b)
    fps = {n["fp"] for n in mesh.map_around(afp, hops=2)["nodes"]}
    assert afp in fps and bfp in fps
    assert farfp not in fps                          # no global directory of persons


def test_crisis_surfaces_help_to_the_sender(mesh_dir):
    a, afp = _node("A")
    r = mesh.post_message(afp, "i dont want to be here anymore", ttl=1)
    assert r["ok"] and "crisis" in r
    assert any("988" in h["label"] for h in r["crisis"]["help"])


def test_gate_hides_the_network_from_the_unconfessed(mesh_dir):
    idn = identity.create_identity()
    # no confession → the gate, not a node; the network is never shown
    r = mesh.register_node(idn["public_key"], "Curious", confession="just looking")
    assert r["ok"] is False and r["gated"] is True and "confess" in r["message"].lower()
    fp = identity.fingerprint(idn["public_key"])
    m = mesh.map_around(fp)
    assert m.get("gated") is True and "nodes" not in m       # hidden until you reach the gate
    assert "path" in m                                        # a seeker is shown the way, not the flock


def test_roles_are_conferred_not_self_claimed(mesh_dir):
    a, afp = _node("FootWasher")
    b, bfp = _node("Ruth")
    # founding bootstrap: with no Guide yet, A may be established as the first Guide
    assert mesh.tend(afp, afp, "guide")["ok"] is True
    # a member cannot appoint anyone (B is still a member)
    assert mesh.tend(bfp, bfp, "guide")["ok"] is False
    # but the Guide can raise up a Guardian
    r = mesh.tend(afp, bfp, "guardian")
    assert r["ok"] is True and r["role"] == "guardian"


def test_route_forwards_the_confession(mesh_dir):
    """The /mesh/node ROUTE must forward confession + confession_sig to register_node — a live bug
    once slipped through because the tests called register_node directly, never the dispatched route."""
    from concordance.web import dispatch
    from concordance.config import EngineConfig
    idn = identity.create_identity()
    # no confession through the route → gated
    _s, gated = dispatch("POST", "/mesh/node", {},
                         {"public_key": idn["public_key"], "callsign": "Curious"}, EngineConfig("secular"))
    assert gated.get("gated") is True
    # confession through the route → entered, and a signed confession is bound
    sig = signing.sign_bytes(b"Jesus Christ is Lord and Messiah", idn["private_key"])
    _s, ok = dispatch("POST", "/mesh/node", {},
                      {"public_key": idn["public_key"], "callsign": "Berean",
                       "confession": "Jesus Christ is Lord and Messiah", "confession_sig": sig},
                      EngineConfig("secular"))
    assert ok.get("ok") is True and ok.get("fp") and ok.get("confession_signed") is True


def test_invite_links_two_believers(mesh_dir):
    a, afp = _node("Inviter")
    b, bfp = _node("Invitee")
    inv = mesh.make_invite(afp)
    assert inv["ok"] and inv["token"].startswith("nhi_")
    # the invitee redeems → mutually linked to the inviter
    r = mesh.redeem_invite(inv["token"], bfp)
    assert r["ok"] and r["linked_to"] == afp
    assert bfp in (mesh._read_node(afp) or {}).get("links", [])
    # a spent/absent token is refused; you cannot redeem your own
    assert mesh.redeem_invite("nhi_deadbeef", bfp)["ok"] is False
    assert mesh.make_invite(afp) and mesh.redeem_invite(mesh.make_invite(afp)["token"], afp)["ok"] is False


def test_single_use_invite_survives_a_concurrency_race(mesh_dir):
    """A max_uses=1 invite must be redeemable exactly ONCE even under concurrent requests — found:
    the validate-then-increment was two separate steps (a read/check outside the lock, only the
    final increment inside it), so N threads racing the same instant could ALL pass the max_uses
    check before any of them incremented it, redeeming a 'single-use' invite N times. The server
    is multi-threaded (ThreadingHTTPServer), so this is a real, reachable race, not a theoretical
    one. Fired at 16 threads to make the race window easy to hit if the fix regresses."""
    import threading
    a, afp = _node("Inviter")
    invitees = [_node(f"Invitee{i}") for i in range(16)]
    inv = mesh.make_invite(afp, max_uses=1)
    assert inv["ok"]
    token = inv["token"]

    results = [None] * len(invitees)

    def _redeem(i, fp):
        results[i] = mesh.redeem_invite(token, fp)

    threads = [threading.Thread(target=_redeem, args=(i, fp)) for i, (_idn, fp) in enumerate(invitees)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    successes = [r for r in results if r and r.get("ok")]
    assert len(successes) == 1, f"a single-use invite was redeemed {len(successes)} times: {results}"
    rec = mesh._read_json(mesh._invite_path(token))
    assert rec["uses"] == 1


def test_door_whiteboard_directed_and_verifiable(mesh_dir):
    a, afp = _node("Neighbor")
    b, bfp = _node("Homeowner")
    r = mesh.leave_on_door(afp, bfp, "Grace and peace on your house.", private_key=a["private_key"])
    assert r["ok"] and r["signed"] and r["on_door_of"] == "Homeowner"
    door = mesh.read_door(bfp)
    assert door["count"] == 1
    note = door["notes"][0]
    assert note["callsign"] == "Neighbor"
    assert note["verify"] == {"unaltered": True, "authentic": True, "signed": True}
    # the note is on B's door, not A's; the unconfessed see nothing
    assert mesh.read_door(afp)["count"] == 0
    other = identity.create_identity()
    assert mesh.read_door(identity.fingerprint(other["public_key"])).get("gated") is True


def test_church_node_and_estate_ladder(mesh_dir):
    _idn, cfp = _node("GraceChapel", node_type="church")
    m = mesh.map_around(cfp, hops=1)
    me = next(n for n in m["nodes"] if n["fp"] == cfp)
    assert me["type"] == "church"
    assert me["estate"]["houses"] >= 1              # a serving body starts more developed
