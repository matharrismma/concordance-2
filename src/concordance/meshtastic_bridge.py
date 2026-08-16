"""MESHTASTIC BRIDGE — the same signed Fellowship post, over LoRa when the grid is down.

Matt, 2026-06-23: *"LoRa Radio and Meshtastic… a great community… Can we make the whole AI work on
Meshtastic?"* — and the honest architecture that answers it: **the AI lives BEHIND the radio, never on
it.** A Meshtastic board is a microcontroller (~200 bytes/message, duty-cycle-limited); the sovereign
engine runs on a node beside it (a Pi / old phone / mini-PC) and RELAYS the Fellowship Mesh over LoRa.

The SAME post that travels online rides the mesh unchanged: `mesh.post_message` builds a canonical body,
its id is `nhm1:<sha256>`, and it carries an Ed25519 signature. This bridge does not re-sign or re-shape
anything — it TRANSPORTS the signed body, and any node VERIFIES it OFFLINE with the two honest layers:

    UNALTERED   recompute nhm1:sha256 over the reconstructed canonical body — no key needed.
    AUTHENTIC   Ed25519 signature vs the sender's key; AND, if the receiver has PINNED this sender,
                that the carried key IS the pinned one. An unpinned key proves only internal
                consistency — stated plainly, never laundered into trust.

Bounded for LoRa: the body is framed as stable ASCII (short field keys → zlib → base64) and CHUNKED to
the radio's payload, reassembled on the far side (out-of-order safe). The framing is chosen for
correctness, not size: base64 keeps every byte ASCII so the MTU budget is counted exactly and a chunk
never splits a multi-byte character, and zlib claws back most of base64's overhead (and genuinely shrinks
long bodies) — for a short signed message the incompressible signature/id/key dominate, so the wire ends
up about the size of the raw JSON, not smaller. The Meshtastic transport is import-guarded — `import
meshtastic` lives only inside serve() — so this whole module is PURE and testable with NO radio, and
simulate() proves the round trip. serve() is written to the meshtastic API and is FIELD-TEST-PENDING on
real hardware (there is no radio where this is authored); that boundary is honest, not hidden.

Stdlib only (json / zlib / base64 / hashlib); the crypto is the mesh's own (signing.verify_bytes).
"""
from __future__ import annotations

import base64
import hashlib
import json
import zlib
from typing import Any, Dict, List, Optional

MTU = 200                     # a conservative Meshtastic payload budget (bytes) — leaves header room
WIRE_V = "nhm1"               # the wire tag — the same lineage as the nhm1: content id
CHUNK_TAG = "NHMc"            # a chunk envelope: NHMc:<gid>:<i>:<n>:<data>, reassembled on the far side
MAX_CHUNKS = 16               # a single post never exceeds this many LoRa packets (a fellowship word is short)

# Compact wire keys → the canonical mesh field names (mesh._message_core), so the signed body is
# reconstructed EXACTLY on the far side and the sha256 id + Ed25519 signature verify unchanged.
_K = {"f": "from", "c": "callsign", "k": "kind", "t": "text", "r": "refs",
      "l": "ttl", "a": "created_at", "n": "nonce"}


# ── the codec: a signed mesh message <-> a compact LoRa payload ────────────────────────────────────
def to_wire(msg: Dict[str, Any], public_key: str = "") -> str:
    """A stored/posted mesh message + the sender's public key -> an ASCII-safe, zlib-framed wire payload
    carrying the signed body, its id, the signature, and the key. Verifiable offline by anyone; the
    transport never touches the signed bytes."""
    core = {short: msg.get(full) for short, full in _K.items()}
    packet = {"v": 1, "core": core, "i": msg.get("id") or "",
              "s": msg.get("signature") or "", "p": public_key or msg.get("public_key") or ""}
    raw = json.dumps(packet, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return WIRE_V + ":" + base64.b64encode(zlib.compress(raw, 9)).decode("ascii")


def from_wire(payload: str) -> Optional[Dict[str, Any]]:
    """Parse a wire payload back to {core (mesh field names), id, signature, public_key}. None if
    malformed — a corrupt packet is dropped, never guessed."""
    p = (payload or "").strip()
    if not p.startswith(WIRE_V + ":"):
        return None
    try:
        raw = zlib.decompress(base64.b64decode(p[len(WIRE_V) + 1:]))
        packet = json.loads(raw)
        c = packet.get("core") or {}
        core = {full: c.get(short) for short, full in _K.items()}
        return {"core": core, "id": packet.get("i") or "",
                "signature": packet.get("s") or "", "public_key": packet.get("p") or ""}
    except Exception:  # noqa: BLE001 — an unparseable packet is simply not a message
        return None


def verify_wire(payload: str, pinned_pubkey: str = "") -> Dict[str, Any]:
    """The two honest layers, entirely offline. Rebuilds the canonical body through the mesh's own
    `_message_core` so the bytes are byte-for-byte what the sender signed."""
    from . import mesh, signing
    d = from_wire(payload)
    if not d:
        return {"ok": False, "error": "unparseable wire payload"}
    c = d["core"]
    try:
        core = mesh._message_core(str(c.get("from") or ""), str(c.get("callsign") or "anon"),
                                  str(c.get("kind") or "word"), str(c.get("text") or ""),
                                  list(c.get("refs") or []), int(c.get("ttl") or 1),
                                  int(c.get("created_at") or 0), str(c.get("nonce") or ""))
        canon, mid = mesh._seal_core(core)
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": "the body could not be reconstructed"}
    unaltered = bool(d["id"]) and d["id"] == mid
    carried = str(d.get("public_key") or "")
    try:
        signed = bool(d["signature"]) and bool(carried) and signing.verify_bytes(canon, d["signature"], carried)
    except Exception:  # noqa: BLE001
        signed = False
    pinned = bool(pinned_pubkey)
    pin_match = carried == pinned_pubkey
    # AUTHENTIC is the strong claim and it requires a PIN: a valid signature alone proves only that the
    # body was not altered after signing (signed), never WHO signed it. An unpinned key is never
    # laundered into authentication.
    authentic = bool(signed and pinned and pin_match)
    if authentic:
        note = "Verified offline: unchanged, and signed by the key you pinned for this sender."
    elif signed and pinned:  # a valid signature, but NOT the key you pinned
        note = ("The signature is valid, but the signing key is NOT the one you pinned for this sender "
                "— treat this as a different or unverified sender.")
    elif signed:             # a valid signature from an unpinned sender
        note = ("The signature is internally consistent — the body was not altered after signing — but "
                "this sender is not pinned here, so it does not establish WHO signed it.")
    else:
        note = "Unsigned or the signature did not verify — trust only the tamper-evident id."
    return {
        "ok": True, "id": mid, "core": core,
        "unaltered": unaltered,
        "signed": signed,
        "authentic": authentic,
        "pinned": pinned,
        "note": note,
    }


# ── chunking to the LoRa payload budget ────────────────────────────────────────────────────────────
def chunk(payload: str, mtu: int = MTU) -> List[str]:
    """Split a wire payload into LoRa-sized packets, each `NHMc:<gid>:<i>:<n>:<data>`. `gid` groups the
    packets of one message; reassembly is order-independent."""
    gid = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
    room = max(16, int(mtu) - (len(CHUNK_TAG) + len(gid) + 8))     # header: tag:gid:i:n: + colons
    pieces = [payload[i:i + room] for i in range(0, len(payload), room)] or [""]
    n = len(pieces)
    return [f"{CHUNK_TAG}:{gid}:{i}:{n}:{piece}" for i, piece in enumerate(pieces)]


def dechunk(packets: List[str]) -> Optional[str]:
    """Reassemble the packets of ONE message (they all share a gid). Returns the wire payload once every
    chunk of a group is present, else None. Extra/foreign packets are ignored."""
    groups: Dict[str, Dict[int, str]] = {}
    totals: Dict[str, int] = {}
    for pk in packets or []:
        s = (pk or "").strip()
        if not s.startswith(CHUNK_TAG + ":"):
            continue
        try:
            _tag, gid, i, n, data = s.split(":", 4)
            i, n = int(i), int(n)
        except (ValueError, TypeError):
            continue
        if n < 1 or n > MAX_CHUNKS or i < 0 or i >= n:
            continue
        groups.setdefault(gid, {})[i] = data
        totals[gid] = n
    for gid, parts in groups.items():
        n = totals.get(gid, 0)
        if n and len(parts) == n:
            return "".join(parts[i] for i in range(n))
    return None


def frames_for(msg: Dict[str, Any], public_key: str = "", mtu: int = MTU) -> List[str]:
    """The whole outbound path in one call: a signed mesh message -> the LoRa packets to transmit."""
    return chunk(to_wire(msg, public_key=public_key), mtu=mtu)


# ── the transport (import-guarded; field-test-pending on real hardware) ────────────────────────────
def radio_available() -> bool:
    """Is the Meshtastic Python library importable on this node? (Not whether a radio is attached.)"""
    try:
        import meshtastic  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def serve(dev_path: Optional[str] = None, on_message=None, channel_index: int = 0) -> Dict[str, Any]:
    """Attach to a Meshtastic radio and relay the Fellowship Mesh over LoRa. FIELD-TEST-PENDING: this is
    written to the meshtastic API (SerialInterface + pubsub) but has never run on a radio where authored.

    Returns a control object: {ok, send(msg, public_key), close()} on success, or {ok:False, error} if
    the library or a radio is absent — the software mesh keeps working regardless. `on_message(result)`
    is called with a verify_wire() result for every fully-reassembled inbound post.
    """
    try:
        import meshtastic
        import meshtastic.serial_interface as _serial
        from pubsub import pub
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"meshtastic not installed on this node ({e}); "
                                      "pip install meshtastic — the software mesh still works"}
    try:
        iface = _serial.SerialInterface(devPath=dev_path)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"no Meshtastic radio reachable ({e})"}

    inbox: List[str] = []

    def _on_receive(packet=None, interface=None):  # noqa: ANN001
        try:
            text = (((packet or {}).get("decoded") or {}).get("text")) or ""
        except Exception:  # noqa: BLE001
            return
        if not text.startswith(CHUNK_TAG + ":"):
            return
        inbox.append(text)
        payload = dechunk(inbox)
        if payload is not None and callable(on_message):
            inbox.clear()
            try:
                on_message(verify_wire(payload))
            except Exception:  # noqa: BLE001
                pass

    pub.subscribe(_on_receive, "meshtastic.receive")

    def send(msg: Dict[str, Any], public_key: str = ""):
        for pk in frames_for(msg, public_key=public_key):
            iface.sendText(pk, channelIndex=channel_index)
        return {"ok": True, "packets": len(frames_for(msg, public_key=public_key))}

    return {"ok": True, "send": send, "close": getattr(iface, "close", lambda: None),
            "note": "Relaying the Fellowship Mesh over LoRa. Field-test this on your RNode/Meshtastic radio."}


def simulate(msg: Dict[str, Any], public_key: str = "") -> Dict[str, Any]:
    """Prove the whole round trip with NO radio: a signed message -> LoRa packets (shuffled to prove
    order-independent reassembly) -> reassembled -> verified offline. This is what a real relay does,
    minus the air."""
    frames = frames_for(msg, public_key=public_key)
    payload = dechunk(list(reversed(frames)))          # deliberately out of order
    verdict = verify_wire(payload or "", pinned_pubkey=public_key)
    return {"ok": True, "packets": len(frames), "max_packet_bytes": max((len(f) for f in frames), default=0),
            "reassembled": payload is not None, "verify": verdict,
            "note": "No radio was used — the codec, chunking, and offline verification all ran in memory."}


__all__ = ["to_wire", "from_wire", "verify_wire", "chunk", "dechunk", "frames_for",
           "radio_available", "serve", "simulate", "MTU"]


# ── a field-operator CLI: run the proof, or start the relay, with no Python ────────────────────────
def _demo_message():
    """A freshly-signed blessing, so --simulate proves the WHOLE chain (sign -> frame -> chunk ->
    reassemble -> verify) with nothing pre-baked."""
    from . import mesh, signing
    priv, pub = signing.generate_keypair()
    core = mesh._message_core(pub, "Foot Washer", "blessing",
                              "Grace and peace to you — the fellowship is praying for your house tonight.",
                              ["John 15:5"], 3, 0, "demo-nonce")
    canon, mid = mesh._seal_core(core)
    msg = dict(core)
    msg["id"], msg["signature"] = mid, signing.sign_bytes(canon, priv)
    return msg, pub


def main(argv=None) -> int:
    import argparse
    import json as _json
    p = argparse.ArgumentParser(
        prog="meshtastic_bridge",
        description="Relay the Fellowship Mesh over LoRa. The engine lives BEHIND the radio; run this "
                    "on the node beside your Meshtastic board.")
    p.add_argument("--serve", action="store_true", help="attach to a Meshtastic radio and relay")
    p.add_argument("--dev", default=None, help="serial device path for the radio (e.g. /dev/ttyUSB0)")
    p.add_argument("--simulate", action="store_true",
                   help="prove the round trip with NO radio (default when --serve is absent)")
    a = p.parse_args(argv)

    if a.serve:
        ctl = serve(dev_path=a.dev, on_message=lambda r: print("  inbound:", _json.dumps(r.get("note", ""))))
        if not ctl.get("ok"):
            print("relay not started:", ctl.get("error"))
            return 1
        print(ctl.get("note", "relaying"))
        print("Listening. Ctrl-C to stop.")
        try:
            import time
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            ctl.get("close", lambda: None)()
            print("\nstopped.")
        return 0

    # default: the self-test
    msg, pub = _demo_message()
    r = simulate(msg, public_key=pub)
    v = r["verify"]
    print(f"packets        : {r['packets']}")
    print(f"max packet     : {r['max_packet_bytes']} bytes  (LoRa budget {MTU})")
    print(f"reassembled    : {r['reassembled']}")
    print(f"id             : {v.get('id')}")
    print(f"unaltered      : {v.get('unaltered')}")
    print(f"signed         : {v.get('signed')}")
    print(f"authentic      : {v.get('authentic')}")
    print(f"note           : {v.get('note')}")
    print(f"radio library  : {'present' if radio_available() else 'absent (pip install meshtastic to serve)'}")
    return 0 if (r["reassembled"] and v.get("authentic")) else 1


if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.exit(main())
