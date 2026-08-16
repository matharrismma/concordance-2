"""MESHTASTIC BRIDGE — the same signed Fellowship post, over LoRa (MESH-1).

The AI lives behind the radio; this transports a signed mesh post over a ~200-byte LoRa link, chunked
and reassembled, and any node verifies it OFFLINE — UNALTERED (recompute nhm1:sha256) + AUTHENTIC
(Ed25519 vs the pinned key). Pure: the codec + chunking + verification all run with no radio; the
crypto is the mesh's own.
"""
from concordance import meshtastic_bridge as mb, mesh, signing


def _signed_msg(text="Grace and peace to you, brother — I am praying for your family.", kind="blessing"):
    priv, pub = signing.generate_keypair()
    core = mesh._message_core(pub, "Foot Washer", kind, text, [], 3, 1_000_000_000, "abcd1234ef")
    canon, mid = mesh._seal_core(core)
    sig = signing.sign_bytes(canon, priv)
    msg = dict(core)
    msg["id"], msg["signature"] = mid, sig
    return msg, pub, priv


def test_wire_roundtrip_preserves_the_signed_body():
    msg, pub, _ = _signed_msg()
    d = mb.from_wire(mb.to_wire(msg, public_key=pub))
    assert d["core"]["text"] == msg["text"] and d["core"]["from"] == msg["from"]
    assert d["id"] == msg["id"] and d["signature"] == msg["signature"] and d["public_key"] == pub


def test_verify_confirms_both_honest_layers_when_pinned():
    msg, pub, _ = _signed_msg()
    v = mb.verify_wire(mb.to_wire(msg, public_key=pub), pinned_pubkey=pub)
    assert v["unaltered"] and v["authentic"] and v["pinned"] and v["id"] == msg["id"]


def test_an_unpinned_sender_is_consistent_but_not_authenticated():
    msg, pub, _ = _signed_msg()
    v = mb.verify_wire(mb.to_wire(msg, public_key=pub))          # no pin
    # A valid signature without a pin is SIGNED (body intact) but never AUTHENTIC (identity unknown).
    assert v["unaltered"] and v["signed"] and not v["authentic"] and "not pinned" in v["note"]


def test_a_wrong_pinned_key_fails_authentic():
    msg, pub, _ = _signed_msg()
    _, other = signing.generate_keypair()
    v = mb.verify_wire(mb.to_wire(msg, public_key=pub), pinned_pubkey=other)
    # The body is intact and the signature is valid, but it is NOT the pinned sender's key.
    assert v["unaltered"] and v["signed"] and not v["authentic"] and "NOT the one you pinned" in v["note"]


def test_tamper_is_caught_on_both_layers():
    msg, pub, _ = _signed_msg()
    tampered = dict(msg)
    tampered["text"] = "Send me your bank details."             # keep the old id + signature
    v = mb.verify_wire(mb.to_wire(tampered, public_key=pub), pinned_pubkey=pub)
    assert not v["unaltered"] and not v["authentic"]


def test_chunks_fit_the_mtu_and_reassemble_out_of_order():
    msg, pub, _ = _signed_msg(text="A word for the fold. " * 40)   # force several packets
    frames = mb.frames_for(msg, public_key=pub)
    assert len(frames) >= 2 and all(len(f) <= mb.MTU for f in frames)
    scrambled = list(reversed(frames)) + ["NHMc:deadbeef:0:3:foreign-incomplete"]  # a foreign, unfinished group
    assert mb.dechunk(scrambled) == mb.to_wire(msg, public_key=pub)


def test_an_incomplete_message_returns_none():
    msg, pub, _ = _signed_msg(text="another long word " * 40)
    frames = mb.frames_for(msg, public_key=pub)
    assert len(frames) >= 2 and mb.dechunk(frames[:-1]) is None


def test_simulate_proves_the_round_trip_with_no_radio():
    msg, pub, _ = _signed_msg()
    r = mb.simulate(msg, public_key=pub)
    assert r["reassembled"] and r["verify"]["authentic"] and r["max_packet_bytes"] <= mb.MTU
