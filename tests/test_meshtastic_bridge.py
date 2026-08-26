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


# ── frames/radio, the hardware guard, malformed inputs, and the field-operator CLI ────────────────
def test_frames_for_and_radio_available():
    msg, pub, _ = _signed_msg()
    frames = mb.frames_for(msg, public_key=pub)
    assert frames and all(f.startswith(mb.CHUNK_TAG + ":") for f in frames)
    assert all(len(f) <= mb.MTU for f in frames)
    assert isinstance(mb.radio_available(), bool)     # library present-or-not, never crashes


def test_serve_without_a_radio_degrades_honestly():
    r = mb.serve()
    assert r["ok"] is False and "meshtastic" in r["error"].lower()   # the software mesh still works


def test_dechunk_ignores_foreign_and_malformed_packets():
    assert mb.dechunk(["not a chunk", "NHMc:onlytwo", "OTHER:1:0:1:x"]) is None
    assert mb.dechunk(["NHMc:g:9:2:x"]) is None        # i >= n is rejected
    assert mb.dechunk([]) is None


def test_from_wire_and_verify_wire_reject_garbage():
    assert mb.from_wire("not a wire payload") is None
    assert mb.from_wire("") is None
    v = mb.verify_wire("garbage")                      # a nonsense payload is neither unaltered nor authentic
    assert not (v.get("unaltered") and v.get("authentic"))


def test_cli_self_test_and_serve(capsys):
    assert mb.main([]) == 0                            # default self-test: sign -> frame -> reassemble -> verify
    out = capsys.readouterr().out
    assert "authentic" in out and "packets" in out
    assert mb.main(["--serve"]) == 1                   # no radio on the test box -> not started
    out2 = capsys.readouterr().out
    assert "not started" in out2.lower() or "meshtastic" in out2.lower()
