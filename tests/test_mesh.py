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
    mesh.link(afp, bfp)
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


def test_unsigned_message_is_honestly_marked(mesh_dir):
    a, afp = _node("A")
    b, bfp = _node("B")
    mesh.link(afp, bfp)
    r = mesh.post_message(afp, "no key on this device", private_key=None)
    assert r["ok"] and r["signed"] is False
    v = mesh.inbox(bfp)["messages"][0]["verify"]
    assert v["unaltered"] is True and v["signed"] is False and v["authentic"] is False


def test_a_foreign_key_cannot_speak_as_a_node(mesh_dir):
    a, afp = _node("A")
    imposter = identity.create_identity()            # a different key than node A registered
    r = mesh.post_message(afp, "this is A", private_key=imposter["private_key"])
    assert r["ok"] is False and "does not match" in r["error"]


def test_ttl_bounds_reach_like_a_lora_hop_limit(mesh_dir):
    a, afp = _node("A")
    b, bfp = _node("B")
    c, cfp = _node("C")
    mesh.link(afp, bfp)
    mesh.link(bfp, cfp)                               # chain A—B—C
    mesh.post_message(afp, "one hop only", ttl=1)     # reaches B, not C
    assert mesh.inbox(bfp)["count"] == 1
    assert mesh.inbox(cfp)["count"] == 0
    mesh.post_message(afp, "two hops", ttl=2)         # now reaches C too
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
    mesh.link(afp, bfp)
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


def test_church_node_and_estate_ladder(mesh_dir):
    _idn, cfp = _node("GraceChapel", node_type="church")
    m = mesh.map_around(cfp, hops=1)
    me = next(n for n in m["nodes"] if n["fp"] == cfp)
    assert me["type"] == "church"
    assert me["estate"]["houses"] >= 1              # a serving body starts more developed
