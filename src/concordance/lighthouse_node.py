"""LIGHTHOUSE NODE — the engine as INFRASTRUCTURE, standing behind a radio where the grid can't reach.

Not a site anyone visits — a node other people RUN. Drop this on a cheap offline computer (a Pi, an
old phone, a solar mini-PC) beside a Meshtastic radio and it gives a whole LoRa mesh two gifts, free,
sovereign, with no account and no internet:

  DAILY WORD   a signed verse / card of the day, broadcast to every node in range.
  ANSWERS      a question typed into the mesh comes back as a VERIFIED card — crisis-first, byte-
               budgeted to the ~200-byte LoRa payload, carrying a /c/<id> pull-ref the reader can
               open later when they have signal.

Why this and not another web page: the engine's two real superpowers — it PROVES what it says, and it
WORKS WHEN THE INTERNET DOESN'T — are invisible on the open web, where everything claims to be
trustworthy and everything works online. They are only *felt* off the grid. This is the engine standing
in the one place the giants can't follow.

The composer is SOVEREIGN and DETERMINISTIC: crisis net → the verified keeping (corpus) → an honest
miss. No model, no oracle, no outbound call — a cry for help is answered with real-person help
immediately, a checkable claim is answered from a card that carries its own re-checkable ref, and a
gap stays a gap (never a fabricated answer). Every reply the node emits is signed with the station's
Ed25519 key, so any node PINS the lighthouse once and then verifies its broadcasts offline forever
(meshtastic_bridge's UNALTERED + SIGNED + AUTHENTIC layers).

Pure and testable with NO hardware and NO corpus: compose_reply/daily_word take injectable
search/crisis/daily functions; the Meshtastic transport is import-guarded inside serve(). simulate_*()
prove the whole chain in memory, and a field-operator CLI runs it without writing Python. serve() is
written to the meshtastic API and is FIELD-TEST-PENDING on a real radio — stated honestly, not hidden.

Stdlib only here; the brain is the project's own (corpus, ask), the crypto is the mesh's own (signing),
the wire is meshtastic_bridge.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import mesh, meshtastic_bridge as _wire, signing

DEFAULT_CALLSIGN = "Lighthouse"
ANSWER_TTL = 3                 # LoRa hops a lighthouse answer is allowed to travel
ANSWER_BYTES = 200             # the answer text budget (the signed wire then chunks to a few packets)

# The 988 line and a real person, spelled out so a crisis reply needs NO lookup and NO network — the
# most important message on the mesh must never depend on retrieval succeeding.
_CRISIS_TEXT = ("You matter, and this can get better. Reach a real person now: call or text 988 "
                "(US Suicide & Crisis Lifeline, 24/7); findahelpline.com for your country; and tell "
                "a friend, a pastor, or a doctor today.")

_STOP = {"the", "a", "an", "to", "of", "and", "or", "how", "do", "does", "did", "i", "is", "it", "its",
         "my", "me", "in", "on", "for", "with", "what", "why", "when", "who", "can", "could", "should",
         "would", "you", "your", "not", "no", "without", "am", "are", "be", "get", "got", "this", "that"}


# ── the composer: sovereign, deterministic, byte-budgeted ──────────────────────────────────────────
def _content_tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(w) > 2 and w not in _STOP}


def _fit(text: str, max_bytes: int) -> str:
    """Trim to a UTF-8 byte budget at a word boundary, marking the cut with an ellipsis. Byte-based so
    the LoRa payload accounting is exact and a multi-byte character is never split."""
    b = text.encode("utf-8")
    if len(b) <= max_bytes:
        return text
    cut = b[:max(1, max_bytes - 3)]                     # leave room for the 3-byte "..." marker
    while cut and (cut[-1] & 0xC0) == 0x80:             # don't end mid-character
        cut = cut[:-1]
    s = cut.decode("utf-8", "ignore").rstrip()
    if " " in s:
        s = s[:s.rfind(" ")].rstrip()                   # back off to the last whole word
    return s + "..."                                    # ASCII — rugged on cheap field displays


def _ref_for(card: Dict[str, Any]) -> str:
    cid = card.get("id")
    return f"/c/{cid}" if cid else ""


def _answer_text(title: str, body: str, ref: str, max_bytes: int) -> str:
    """Title — body, fitted so the PULL-REF always survives (a reader with no signal still gets a
    handle to open the full, cited card later)."""
    tail = ("  " + ref) if ref else ""
    budget = max(16, max_bytes - len(tail.encode("utf-8")))
    head = (title or "").strip()
    body = (body or "").strip()
    if body:
        head = f"{head} - {body}" if head else body     # ASCII separator — rugged on cheap field displays
    return _fit(head, budget) + tail


def _best_relevant(hits: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
    """The relevance FLOOR: return the top hit that actually shares a content word with the question.
    If nothing does, return None so the reply is an honest miss — a tangential card that merely ranked
    first must never be dressed up as the answer (a gap stays a gap)."""
    qt = _content_tokens(query)
    if not qt:
        return hits[0] if hits else None
    for h in hits:
        if qt & _content_tokens((h.get("title") or "") + " " + (h.get("body") or "")):
            return h
    return None


def _default_search(query: str, limit: int) -> List[Dict[str, Any]]:
    from . import corpus
    return corpus.search(query, limit)


def _default_is_crisis(text: str) -> bool:
    from . import ask
    return ask.is_crisis(text)


def compose_reply(query: str, max_bytes: int = ANSWER_BYTES, *,
                  search_fn: Optional[Callable[[str, int], List[Dict[str, Any]]]] = None,
                  is_crisis_fn: Optional[Callable[[str], bool]] = None) -> Dict[str, Any]:
    """A mesh question -> a byte-budgeted, VERIFIED reply. Sovereign and deterministic: crisis net
    first, then the verified keeping, then an honest miss. Never fabricates. Injectable search/crisis
    so it runs with no corpus (tests) and stays the one code path in production."""
    q = (str(query) if query else "").strip()
    if not q:
        return {"ok": False, "error": "empty question"}
    crisis = is_crisis_fn or _default_is_crisis
    if crisis(q):
        return {"ok": True, "kind": "crisis", "found": True, "verified": True,
                "text": _fit(_CRISIS_TEXT, max_bytes), "ref": "tel:988"}
    search = search_fn or _default_search
    try:
        hits = search(q, 3) or []
    except Exception:  # noqa: BLE001 — a node with a missing/partial corpus answers "miss", never crashes
        hits = []
    hit = _best_relevant(hits, q)
    if hit:
        ref = _ref_for(hit)
        return {"ok": True, "kind": "answer", "found": True, "verified": True,
                "card_id": hit.get("id"), "ref": ref,
                "text": _answer_text(hit.get("title") or "card", hit.get("body") or "", ref, max_bytes)}
    return {"ok": True, "kind": "miss", "found": False, "verified": False, "ref": "",
            "text": _fit("No verified card for that yet — ask narrowhighway.com when you have signal, "
                         "and it will be kept for the next traveler.", max_bytes)}


def daily_word(seed: str, max_bytes: int = ANSWER_BYTES, *,
               daily_fn: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None) -> Dict[str, Any]:
    """The verse / card of the day, deterministic in `seed` (pass the date; the node has no clock it
    should trust for signing). Byte-budgeted, carries its pull-ref."""
    pick = daily_fn
    if pick is None:
        from . import corpus
        pick = corpus.daily
    card = pick(seed)
    if not card:
        return {"ok": False, "error": "no card of the day (empty corpus?)"}
    ref = _ref_for(card)
    return {"ok": True, "kind": "daily", "found": True, "verified": True,
            "seed": seed, "card_id": card.get("id"), "ref": ref,
            "text": _answer_text(card.get("title") or "card", card.get("body") or "", ref, max_bytes)}


# ── signing the reply into a mesh post (the station speaks with ONE pinned identity) ───────────────
def new_station() -> Tuple[str, str]:
    """A fresh station identity (private, public). The operator generates this ONCE, keeps the private
    key on the node, and publishes the public key so the mesh can pin the lighthouse and verify its
    broadcasts offline forever."""
    return signing.generate_keypair()


def sign_reply(reply: Dict[str, Any], node_priv: str, node_pub: str,
               callsign: str = DEFAULT_CALLSIGN, *, ttl: int = ANSWER_TTL,
               created_at: int = 0, nonce: str = "") -> Dict[str, Any]:
    """Turn a composed reply into a SIGNED mesh message (mesh's canonical body + Ed25519), ready for
    the wire. The kind rides along (crisis/answer/daily/miss) so the reader sees the boundary."""
    refs = [reply["ref"]] if reply.get("ref") else []
    core = mesh._message_core(node_pub, callsign, reply.get("kind", "word"), reply.get("text", ""),
                              refs, ttl, created_at, nonce)
    canon, mid = mesh._seal_core(core)
    msg = dict(core)
    msg["id"], msg["signature"] = mid, signing.sign_bytes(canon, node_priv)
    return msg


def frames_for_reply(reply: Dict[str, Any], node_priv: str, node_pub: str,
                     callsign: str = DEFAULT_CALLSIGN, **kw) -> List[str]:
    """Compose-to-air in one step: a reply -> the signed LoRa packets to transmit."""
    return _wire.frames_for(sign_reply(reply, node_priv, node_pub, callsign, **kw), public_key=node_pub)


# ── the transport (import-guarded; field-test-pending on real hardware) ────────────────────────────
def serve(node_priv: str, node_pub: str, callsign: str = DEFAULT_CALLSIGN, *,
          dev_path: Optional[str] = None, channel_index: int = 0,
          search_fn=None, is_crisis_fn=None, on_answer=None) -> Dict[str, Any]:
    """Attach to a Meshtastic radio and answer the mesh. FIELD-TEST-PENDING: written to the meshtastic
    SerialInterface + pubsub API, never run on a radio where authored.

    A RAW text message on the mesh (a human typing a question) is answered; an NHMc-chunked packet is
    a node-to-node signed post and is left for meshtastic_bridge, not treated as a question. Returns a
    control object {ok, answer(q)->packets, broadcast_daily(seed)->packets, close()} on success, or
    {ok:False, error} if the library/radio is absent — the composer still works offline regardless.
    """
    try:
        import meshtastic  # noqa: F401
        import meshtastic.serial_interface as _serial
        from pubsub import pub
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"meshtastic not installed on this node ({e}); "
                                      "pip install meshtastic — compose_reply still works offline"}
    try:
        iface = _serial.SerialInterface(devPath=dev_path)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"no Meshtastic radio reachable ({e})"}

    def _send_frames(frames: List[str]) -> int:
        for f in frames:
            iface.sendText(f, channelIndex=channel_index)
        return len(frames)

    def answer(q: str) -> int:
        reply = compose_reply(q, search_fn=search_fn, is_crisis_fn=is_crisis_fn)
        frames = frames_for_reply(reply, node_priv, node_pub, callsign)
        n = _send_frames(frames)
        if callable(on_answer):
            try:
                on_answer(q, reply, n)
            except Exception:  # noqa: BLE001
                pass
        return n

    def broadcast_daily(seed: str) -> int:
        return _send_frames(frames_for_reply(daily_word(seed), node_priv, node_pub, callsign))

    def _on_receive(packet=None, interface=None):  # noqa: ANN001
        try:
            text = (((packet or {}).get("decoded") or {}).get("text")) or ""
        except Exception:  # noqa: BLE001
            return
        text = text.strip()
        if not text or text.startswith(_wire.CHUNK_TAG + ":"):
            return                                          # empty, or an inter-node post — not a question
        try:
            answer(text)
        except Exception:  # noqa: BLE001
            pass

    pub.subscribe(_on_receive, "meshtastic.receive")
    return {"ok": True, "answer": answer, "broadcast_daily": broadcast_daily,
            "close": getattr(iface, "close", lambda: None),
            "note": "Lighthouse is answering the mesh over LoRa. Field-test on your Meshtastic radio."}


# ── simulate the whole chain with NO radio ─────────────────────────────────────────────────────────
def _simulate_over_air(reply: Dict[str, Any], node: Optional[Tuple[str, str]] = None) -> Dict[str, Any]:
    node_priv, node_pub = node or new_station()
    frames = frames_for_reply(reply, node_priv, node_pub)
    payload = _wire.dechunk(list(reversed(frames)))         # out of order, to prove reassembly
    verdict = _wire.verify_wire(payload or "", pinned_pubkey=node_pub)
    return {"ok": True, "reply": reply, "packets": len(frames),
            "max_packet_bytes": max((len(f) for f in frames), default=0),
            "reassembled": payload is not None, "verify": verdict, "station_pubkey": node_pub}


def context_loop(text: str, *, seal: bool = True) -> Dict[str, Any]:
    """Run the PRIVATE context loop on this node: strip a claim to only what is necessary to check,
    verify that de-identified skeleton in-process, and reattach the verdict with the boundary declared.
    Nothing leaves the node — the verifier is local. This is the sovereign-node form of the loop; it is
    also exposed over HTTP as POST /context/run when the operator sets CONCORDANCE_SOVEREIGN_NODE. Lazy
    import keeps the loop off the minimal field-pack closure."""
    from . import context
    return context.run_verified(text, seal=seal)


def simulate_answer(query: str, *, node=None, search_fn=None, is_crisis_fn=None) -> Dict[str, Any]:
    """A question -> composed -> signed -> LoRa packets -> reassembled -> verified offline. The whole
    lighthouse, minus the air."""
    return _simulate_over_air(
        compose_reply(query, search_fn=search_fn, is_crisis_fn=is_crisis_fn), node=node)


def simulate_daily(seed: str, *, node=None, daily_fn=None) -> Dict[str, Any]:
    return _simulate_over_air(daily_word(seed, daily_fn=daily_fn), node=node)


__all__ = ["compose_reply", "daily_word", "new_station", "sign_reply", "frames_for_reply",
           "serve", "simulate_answer", "simulate_daily", "context_loop", "ANSWER_BYTES", "DEFAULT_CALLSIGN"]


# ── a field-operator CLI: run the lighthouse without writing Python ────────────────────────────────
_DEMO_CARD = {"id": "first-aid-bleeding-control",
              "title": "Control severe bleeding",
              "body": "Press hard directly on the wound with a clean cloth and do not let up. Keep "
                      "pressing for at least 15 minutes. If it soaks through, add more cloth on top — "
                      "do not remove it. Raise the limb above the heart if you can. Get help."}


def main(argv=None) -> int:
    import argparse
    import json as _json
    p = argparse.ArgumentParser(
        prog="lighthouse_node",
        description="The engine as infrastructure behind a Meshtastic radio: verified answers + a "
                    "signed daily word, sovereign and offline. Run this on the node beside your radio.")
    p.add_argument("--ask", metavar="QUESTION", help="answer one question from the local corpus")
    p.add_argument("--daily", nargs="?", const="today", metavar="SEED",
                   help="the signed card of the day (optionally seeded, default 'today')")
    p.add_argument("--serve", action="store_true", help="attach to a radio and answer the mesh")
    p.add_argument("--dev", default=None, help="serial device path for the radio (e.g. /dev/ttyUSB0)")
    p.add_argument("--simulate", action="store_true",
                   help="prove the whole chain with NO radio and NO corpus (a first-aid demo)")
    a = p.parse_args(argv)

    if a.serve:
        priv, pub = new_station()
        print("station public key (pin this on the mesh):", pub)
        ctl = serve(priv, pub, on_answer=lambda q, r, n: print(f"  answered {q!r} -> {n} packets [{r['kind']}]"))
        if not ctl.get("ok"):
            print("lighthouse not started:", ctl.get("error"))
            return 1
        print(ctl.get("note"))
        print("Listening. Ctrl-C to stop.")
        try:
            import time
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            ctl.get("close", lambda: None)()
            print("\nstopped.")
        return 0

    if a.ask is not None:
        r = compose_reply(a.ask)
        print(f"[{r.get('kind')}] verified={r.get('verified')}")
        print(r.get("text"))
        return 0

    if a.daily is not None:
        r = daily_word(a.daily)
        print(_json.dumps(r, indent=2) if not r.get("ok") else f"[daily] {r['text']}")
        return 0

    # default: the self-test — proves the pipeline with no radio and no corpus
    print("== crisis (answered with real help, no lookup) ==")
    cr = simulate_answer("i want to end it all", is_crisis_fn=lambda t: True)
    print(f"  {cr['reply']['text']}")
    print(f"  packets={cr['packets']} authentic={cr['verify']['authentic']}")
    print("== answer (a verified card over LoRa) ==")
    an = simulate_answer("how do i stop bad bleeding", search_fn=lambda q, n: [_DEMO_CARD])
    v = an["verify"]
    print(f"  {an['reply']['text']}")
    print(f"  packets={an['packets']} max={an['max_packet_bytes']}B authentic={v['authentic']} ref={an['reply']['ref']}")
    print("== daily word (signed card of the day) ==")
    da = simulate_daily("2026-08-16", daily_fn=lambda s: _DEMO_CARD)
    print(f"  {da['reply']['text']}")
    print(f"  packets={da['packets']} authentic={da['verify']['authentic']}")
    ok = cr["verify"]["authentic"] and an["verify"]["authentic"] and da["verify"]["authentic"]
    print("station pubkey:", an["station_pubkey"])
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.exit(main())
