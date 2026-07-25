"""The Fellowship Mesh — a network of believers. LoRa mesh, but for the church.

Matt: "We need a map with each node. You can message the nodes around you." / "LoRa mesh
but for Christians. A network of believers."

Each believer is a NODE, identified by their own key (the key on their drive IS the identity —
no account, no password, no email; see binding.py). A node is a self-chosen CALLSIGN (a handle,
never PII) bound to a public key. You LINK to the nodes you know — you must be handed their exact
fingerprint (their node id), the way a ham operator learns a callsign; there is no directory of
persons to browse (groups.py's floor, applied to the mesh). The mesh grows transitively: your
neighbors' neighbors are within reach, hop by hop, exactly like a LoRa mesh with a TTL.

You MESSAGE the nodes around you. Every message carries the bulletin's TWO HONEST LAYERS
(api/bulletin.py, ported): UNALTERED — the id IS the sha256 of the canonical message, so any edit
changes the name (verifiable with NO key, offline); and AUTHENTIC — an Ed25519 signature against
the sender's PINNED public key (verifiable offline once you hold the key). A message with no
signature is honestly marked unsigned — integrity without authenticity, never laundered.

Sovereign: stdlib + identity + signing only. Imports NOTHING from verifiers/derivation. Personal
data (nodes, messages) lives in data/mesh/ — gitignored, theirs, never committed (the carry-your-
own-data thesis: a seized server yields only the public corpus). The relay is ONE node among many;
online today, and the SAME signed bundle rides Reticulum/LoRa when the grid is down (the AI lives
behind the radio). Conduit, not source: a message is a member's own words, attributed — never
engine-generated, never presented as a verified verdict. Points to the body of Christ, never
replaces it (John 3:30). Crisis is surfaced to real people first, never filed away.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import identity, signing

_LOCK = threading.Lock()
_HANDLE_RE = re.compile(r"[^A-Za-z0-9 _.\-]")     # a callsign is a pseudonym, never PII
_FP_RE = re.compile(r"[A-Za-z0-9_\-]{8,80}")      # a fingerprint id, as minted by identity.fingerprint
_MAX_TEXT = 2000
_MAX_LINKS = 256                                  # bound the graph a single node can attach to
_MAX_TTL = 4                                      # hop limit, like a LoRa mesh
# A post is not only a word. Believers serve each other: an OFFER (I can give / help with this), a
# NEED (I am seeking this — a ride, a tire, an advocate to stand with me), a BLESSING (encouragement),
# CONTENT (something made to share), a plain WORD, or a BROADCAST — the Emergency Broadcast System for
# the church: in daily life a wide call, and in the worst case the signal that gathers the remnant
# (Revelation 12:17). Everything is offering-based — no obligation, no tithe, no money moves through the mesh.
_KINDS = ("word", "offer", "need", "blessing", "content", "broadcast")
_MSG_TTL_SECONDS = 30 * 24 * 3600                 # a message ages off the relay after 30 days
_MAX_MAP_NODES = 400                              # the map around you is bounded — no global crawl


def _dir() -> Path:
    base = os.environ.get("CONCORDANCE_MESH_DIR", "").strip() or (
        (os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data") + "/mesh")
    d = Path(base)
    (d / "nodes").mkdir(parents=True, exist_ok=True)
    (d / "msgs").mkdir(parents=True, exist_ok=True)
    return d


def _now() -> int:
    return int(time.time())


def _clean_callsign(h: str) -> str:
    h = _HANDLE_RE.sub("", str(h or "")).strip()[:40]
    return h or "anon"


def _valid_fp(fp: str) -> bool:
    return bool(_FP_RE.fullmatch(str(fp or "")))


def _node_path(fp: str) -> Path:
    return _dir() / "nodes" / (fp + ".json")


def _msg_path(mid: str) -> Path:
    # the id is "nhm1:<hex>" — the ':' is not a safe filename char, so key files by the hex
    return _dir() / "msgs" / (mid.split(":", 1)[-1] + ".json")


def _read_json(p: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_json(p: Path, rec: Dict[str, Any]) -> None:
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


def _read_node(fp: str) -> Optional[Dict[str, Any]]:
    if not _valid_fp(fp):
        return None
    return _read_json(_node_path(fp))


# ── Nodes ────────────────────────────────────────────────────────────────

# A node is usually a believer, but a church, ministry, or fellowship that serves in the community
# becomes a node too — right alongside the people. We support the churches; we do not replace them.
_NODE_TYPES = ("believer", "church", "ministry", "fellowship")

# Roles in the fold — gentle names on the surface (so no one is scared off), the shepherd's imagery
# underneath. A MEMBER is everyone (the flock). A GUIDE leads and feeds and shows the way (the
# shepherd — Acts 20:28; 1 Peter 5:2). A GUARDIAN watches the perimeter and turns away the wolves
# (the sheepdog — John 10:12): watchful, never a wolf itself. Roles are CONFERRED, never self-claimed:
# you raise up a guide, you do not appoint yourself one. Only a guide may confer (see tend); the
# first guide is the founding foot-washer.
_ROLES = ("member", "guide", "guardian")
_SHEPHERDING = ("guide",)                          # roles that may tend / confer (raise others up)

# THE GATE (Romans 10:9; 1 Corinthians 12:3; Matthew 16:16). The whole tool is open to everyone — the
# Word, the corpus, the Coach scare no one off. But the FELLOWSHIP of believers is a protected inner
# court: eyes to see and ears to hear (Matthew 13:9-16). You enter it by CONFESSING Jesus Christ as
# Lord and Messiah. We name "Messiah" (Mashiach) on purpose — the confession reaches the Jewish
# people too. We do not, and cannot, judge the heart (1 Samuel 16:7) — God does; we only require that
# the confession be MADE, with the mouth (Romans 10:10), and we bind it to the believer's own key.
CONFESSION = "Jesus Christ is Lord and Messiah"
CONFESSION_SCRIPTURE = "Romans 10:9-10; 1 Corinthians 12:3; Matthew 16:16"


def _confesses(text: str) -> bool:
    """Does this confession affirm Jesus as Lord AND as the Christ / Messiah? Permissive on wording
    (the confession is with the mouth, not a password) but the essence must be present. Reuses
    ask.normalize so a phone's smart quotes cannot walk past it."""
    from .ask import normalize
    t = normalize(text)
    return ("jesus" in t) and ("lord" in t) and (
        "christ" in t or "messiah" in t or "mashiach" in t or "moshiach" in t)


def _gate() -> Dict[str, Any]:
    return {"ok": False, "gated": True, "confession": CONFESSION, "scripture": CONFESSION_SCRIPTURE,
            "message": ("The fellowship of believers opens to those who confess Jesus Christ as Lord "
                        "and Messiah (Romans 10:9). The rest of the tool is already yours; this inner "
                        "court is kept for His own. Whoever confesses Him, He confesses before the "
                        "Father (Matthew 10:32). Confess, and enter.")}


def register_node(public_key: str, callsign: str = "", node_type: str = "believer",
                  confession: str = "", confession_sig: Optional[str] = None) -> Dict[str, Any]:
    """Enter the mesh — GATED by confession (Romans 10:9). To receive a node you must confess Jesus
    Christ as Lord and Messiah; without it the gate returns the confession as an invitation, not a
    rejection. Your fingerprint is DERIVED from your public key — the key on your drive is the
    identity; there is no account. A node may be a believer or a church / ministry / fellowship.
    Idempotent for a node already inside. No PII is stored, ever."""
    public_key = str(public_key or "").strip()
    if not public_key:
        return {"ok": False, "error": "public_key required (the key on your drive is your identity)"}
    node_type = node_type if node_type in _NODE_TYPES else "believer"
    try:
        fp = identity.fingerprint(public_key)
    except Exception:  # noqa: BLE001 — a malformed key is a user error, not a crash
        return {"ok": False, "error": "public_key not a valid identity key"}
    existing = _read_node(fp)
    # The gate: a new believer must confess. One already inside (confessed before) may refresh freely.
    if not (existing and existing.get("confessed")):
        if not _confesses(confession):
            return _gate()
    # If they signed the confession with their key, bind it — Peter's confession, now attributable.
    confession_signed = False
    if confession_sig and confession:
        try:
            if identity.signing_available():
                confession_signed = signing.verify_bytes(
                    confession.strip().encode("utf-8"), confession_sig, public_key)
        except Exception:  # noqa: BLE001 — signing the confession is optional
            confession_signed = False
    with _LOCK:
        node = existing or {"fp": fp, "public_key": public_key, "links": [], "joined_at": _now()}
        node["public_key"] = public_key
        node["callsign"] = _clean_callsign(callsign or node.get("callsign"))
        node["type"] = node_type
        node["role"] = node.get("role", "member")   # roles are conferred (tend), never self-claimed
        node["confessed"] = True
        if confession.strip():
            node["confession"] = confession.strip()[:200]   # their own words, verbatim
        if confession_signed:
            node["confession_sig"] = confession_sig
            node["confession_signed"] = True
        node["last_seen"] = _now()
        _write_json(_node_path(fp), node)
    return {"ok": True, "fp": fp, "callsign": node["callsign"], "type": node["type"],
            "confessed": True, "confession_signed": node.get("confession_signed", False),
            "links": len(node.get("links", [])),
            "note": "Welcome. This is your node id — hand it to believers (or a church) you know so they can link to you."}


def _public_node(node: Dict[str, Any]) -> Dict[str, Any]:
    """The outward view of a node: callsign + fingerprint + counts. The public key stays for
    offline verification; NO PII exists to leak."""
    return {"fp": node["fp"], "callsign": node.get("callsign", "anon"),
            "type": node.get("type", "believer"), "role": node.get("role", "member"),
            "links": len(node.get("links", [])), "last_seen": node.get("last_seen"),
            "public_key": node.get("public_key", "")}


def link(fp: str, neighbor_fp: str, op: str = "link") -> Dict[str, Any]:
    """Link to a neighbor you KNOW by their exact fingerprint (op='link'), or drop one
    (op='unlink'). Links are mutual (a radio link is bidirectional) — but you can only reach a node
    whose id you were handed, so there is no way to attach to strangers. This is the whole graph."""
    if not _valid_fp(fp) or not _valid_fp(neighbor_fp):
        return {"ok": False, "error": "both fingerprints required"}
    if fp == neighbor_fp:
        return {"ok": False, "error": "a node cannot link to itself"}
    with _LOCK:
        me = _read_node(fp)
        other = _read_node(neighbor_fp)
        if not me:
            return {"ok": False, "error": "register your node first (POST /mesh/node)"}
        if not other:
            return {"ok": False, "error": "no node with that fingerprint — check the id you were handed"}
        for a, b in ((me, other), (other, me)):
            links = a.setdefault("links", [])
            if op == "unlink":
                if b["fp"] in links:
                    links.remove(b["fp"])
            else:
                if b["fp"] not in links:
                    if len(links) >= _MAX_LINKS:
                        return {"ok": False, "error": f"link limit reached ({_MAX_LINKS})"}
                    links.append(b["fp"])
            _write_json(_node_path(a["fp"]), a)
    return {"ok": True, "op": ("unlink" if op == "unlink" else "link"),
            "you": me["fp"], "neighbor": other["fp"], "neighbor_callsign": other.get("callsign", "anon"),
            "links": len(me.get("links", []))}


def _any_guide_exists() -> bool:
    for p in (_dir() / "nodes").glob("*.json"):
        n = _read_json(p)
        if n and n.get("role") in _SHEPHERDING:
            return True
    return False


def tend(by_fp: str, target_fp: str, role: str) -> Dict[str, Any]:
    """Raise up a Guide or Guardian, or set a node back to member. Only a GUIDE may confer (a
    shepherd appoints — you do not appoint yourself). THE ONE EXCEPTION is the founding: when no
    Guide exists yet, a confessed node may be established as the first Guide (the foot-washer at the
    head, lowest and first). A conferral is never a claim of authority over a soul — only a charge to
    serve and to guard (1 Peter 5:2-3)."""
    role = role if role in _ROLES else "member"
    target = _read_node(target_fp)
    if not target or not target.get("confessed"):
        return {"ok": False, "error": "target is not a node in the fold"}
    by = _read_node(by_fp)
    bootstrap = (by_fp == target_fp and role == "guide" and not _any_guide_exists())
    if not bootstrap:
        if not by or by.get("role") not in _SHEPHERDING:
            return {"ok": False, "error": "only a Guide may raise up a Guide or Guardian"}
    with _LOCK:
        target = _read_node(target_fp)
        target["role"] = role
        _write_json(_node_path(target_fp), target)
    return {"ok": True, "fp": target_fp, "callsign": target.get("callsign", "anon"), "role": role,
            "by": (by_fp if not bootstrap else "founding"),
            "note": ("The founding Guide is set — lowest and first, a foot-washer's charge." if bootstrap
                     else f"{target.get('callsign','anon')} is charged as {role} — to serve and to guard, never to lord over.")}


def _bfs(start_fp: str, max_hops: int) -> Dict[str, int]:
    """Breadth-first distances over the undirected link graph, out to max_hops. Bounded by
    _MAX_MAP_NODES so no single call can crawl an unbounded network."""
    dist: Dict[str, int] = {start_fp: 0}
    q: deque = deque([start_fp])
    while q and len(dist) < _MAX_MAP_NODES:
        cur = q.popleft()
        d = dist[cur]
        if d >= max_hops:
            continue
        node = _read_node(cur)
        for nb in (node or {}).get("links", []):
            if nb not in dist:
                dist[nb] = d + 1
                q.append(nb)
    return dist


# THE PATH WITH GATES. We do not show the full deck at once. We discern not by scanning a heart we
# cannot see (1 Samuel 16:7) but by the WALK — what someone comes seeking, and the fruit over time
# (Matthew 7:16-20). The way opens court by court, inward: the open tool for all → a seeker who asks
# → the confession that gives you a node → being known and serving → and at the center, eventually, a
# community that shares as Acts 2 shared. What you SEE of the network unlocks as you walk it.
# The way draws inward to be formed, then turns OUTWARD to be sent (Matthew 28:19; John 20:21). It
# does not end at the center — it flows out. "sent" is the commission: you go into the world to serve
# and make disciples, and plant new nodes. That block unlocks later, with discipleship and further
# understanding — named here so the shape is whole, but not yet auto-granted.
_STAGE = {
    "threshold": {"rank": 0, "max_hops": 0},
    "seeker":    {"rank": 1, "max_hops": 0},
    "confessor": {"rank": 2, "max_hops": 1},
    "joined":    {"rank": 3, "max_hops": 2},
    "community": {"rank": 4, "max_hops": _MAX_TTL},
    "sent":      {"rank": 5, "max_hops": _MAX_TTL},
}
_STAGE_ORDER = ["threshold", "seeker", "confessor", "joined", "community", "sent"]


def _stage(node: Optional[Dict[str, Any]], posts: int = 0) -> str:
    """Where a node stands on the path, read from its WALK: has it confessed, is it vouched by other
    believers (links), has it served (posts). Never a verdict on the soul — a description of the walk."""
    if not node or not node.get("confessed"):
        return "seeker"
    vouches = len(node.get("links", []))
    if vouches >= 8 and posts >= 8:
        return "community"
    if vouches >= 2 and posts >= 1:
        return "joined"
    return "confessor"


def path() -> Dict[str, Any]:
    """The path with gates — rendered so a visitor sees the way, not the network. Each gate names what
    it opens, how it opens, and the Scripture that marks it."""
    return {
        "identity": "A path with gates. We do not show the full deck at once — the way opens as you walk it.",
        "gates": [
            {"stage": "threshold", "opens": "the open tool — the Word, the corpus, verification, the Coach",
             "gate": "none — this court is for everyone", "scripture": "Matthew 11:28"},
            {"stage": "seeker", "opens": "the shape of the path, and the confession that opens the door",
             "gate": "you come, and you ask, seek, knock", "scripture": "Matthew 7:7-8"},
            {"stage": "confessor", "opens": "a node of your own, and the believers immediately around you",
             "gate": "confess Jesus Christ as Lord and Messiah", "scripture": "Romans 10:9"},
            {"stage": "joined", "opens": "your fellowship and their neighbors — the offers and needs, to serve and be served",
             "gate": "be known: vouched by believers, and serving", "scripture": "1 John 3:18"},
            {"stage": "community", "opens": "the woven center — where the body provides for its own, so no one is in need",
             "gate": "a life shared with the body over time", "scripture": "Acts 2:44-45; Acts 4:34"},
            {"stage": "sent", "opens": "a commission — to go into the world to serve, make disciples, and plant new nodes",
             "gate": "you have been discipled; now you are sent (the block unlocks with discipleship + further understanding)",
             "scripture": "Matthew 28:19-20; John 20:21", "locked": True},
        ],
        "hidden": ("The path is hidden until a seeker reaches the gate — treasure hidden in a field "
                   "(Matthew 13:44). It is not advertised; it is found. Seek, and you will find (Matthew 7:7)."),
        "center": ("At the center, a community that shares as Acts 2 shared — offering-based, so that there "
                   "is not a needy person among them (Acts 4:34); a place where, together, you would not need "
                   "to pay bills to live. Not a promise, not a scheme, and no money moves through us — the "
                   "aspiration of a body that truly loves its own."),
        "turns_outward": ("The way does not end at the center. It draws you in to be formed, then sends you "
                          "OUT — as the Father sent the Son, so He sends you (John 20:21). The discipled become "
                          "the disciplers; a sent one plants new nodes, and the mesh grows outward."),
    }


def _next_gate(stage: str) -> Optional[Dict[str, Any]]:
    gates = path()["gates"]
    rank = _STAGE.get(stage, _STAGE["seeker"])["rank"]
    for g in gates:
        if _STAGE.get(g["stage"], {}).get("rank", 0) == rank + 1:
            return g
    return None


def _estate(links: int, posts: int, node_type: str) -> Dict[str, Any]:
    """Houses and hotels (Monopoly). A node DEVELOPS as it links up and serves: a lone believer is a
    single house; more links + offerings raise houses; a hub that truly serves the community — or a
    church / ministry — becomes a hotel. The map's growth ladder — never a ranking of a soul's worth."""
    score = int(links) + int(posts)
    if node_type in ("church", "ministry"):
        score += 4                       # a serving body already gathers many — it starts developed
    hotel = score >= 8
    houses = 0 if hotel else max(1, min(4, 1 + score // 2))
    return {"houses": houses, "hotel": hotel, "level": (5 if hotel else houses), "score": score}


def map_around(fp: str, hops: int = 2) -> Dict[str, Any]:
    """The map: the nodes AROUND you — but hidden until you reach the gate, and revealed only as far
    as your walk has taken you. An unconfessed visitor sees the PATH, never the network (we do not
    show the full deck). A confessor sees the believers immediately around them; the horizon widens
    (more hops) as you are known and serve. Your view only — there is no global map."""
    me = _read_node(fp)
    if not me or not me.get("confessed"):
        # Hidden until the first reaches the gate — a seeker is shown the way in, not the network.
        g = _gate()
        g["path"] = path()
        g["stage"] = "seeker"
        return g
    outgoing = _outgoing_counts()
    stage = _stage(me, outgoing.get(fp, 0))
    max_hops = _STAGE[stage]["max_hops"]
    hops = max(1, min(max_hops or 1, int(hops or 2)))
    dist = _bfs(fp, hops)
    incoming = _incoming_counts(fp)
    nodes: List[Dict[str, Any]] = []
    for nfp, d in sorted(dist.items(), key=lambda kv: (kv[1], kv[0])):
        node = _read_node(nfp)
        if not node:
            continue
        v = _public_node(node)
        v["hops"] = d
        v["you"] = (nfp == fp)
        v["reaching_you"] = incoming.get(nfp, 0)
        v["estate"] = _estate(v["links"], outgoing.get(nfp, 0), v.get("type", "believer"))
        v["stage"] = _stage(node, outgoing.get(nfp, 0))
        nodes.append(v)
    inset = set(dist)
    edges: List[List[str]] = []
    seen = set()
    for nfp in inset:
        node = _read_node(nfp)
        for nb in (node or {}).get("links", []):
            if nb in inset:
                key = tuple(sorted((nfp, nb)))
                if key not in seen:
                    seen.add(key)
                    edges.append(list(key))
    return {"ok": True, "you": fp, "callsign": me.get("callsign", "anon"),
            "stage": stage, "horizon": max_hops, "hops": hops, "count": len(nodes),
            "nodes": nodes, "edges": edges, "next_gate": _next_gate(stage),
            "note": "The nodes around you. Message a neighbor, or hand your id to one more believer."}


# ── Messages — signed, content-addressed, hop-limited (LoRa TTL) ──────────

def _message_core(from_fp: str, callsign: str, kind: str, text: str,
                  refs: List[str], ttl: int, created_at: int, nonce: str) -> Dict[str, Any]:
    """The canonical, signed body. Field order is fixed by canonical_json_bytes (sorted keys), so
    the id is reproducible on any machine, offline."""
    return {"v": 1, "from": from_fp, "callsign": callsign, "kind": kind, "text": text,
            "refs": list(refs or []), "ttl": ttl, "created_at": created_at, "nonce": nonce}


def _seal_core(core: Dict[str, Any]) -> Tuple[bytes, str]:
    canon = signing.canonical_json_bytes(core)
    return canon, "nhm1:" + hashlib.sha256(canon).hexdigest()


def post_message(from_fp: str, text: str, *, kind: str = "word", refs: Optional[List[str]] = None,
                 ttl: int = 2, private_key: Optional[str] = None) -> Dict[str, Any]:
    """Post to the nodes around you. `kind` is how believers serve each other: a WORD, an OFFER (I
    can give / help with this), a NEED (I am seeking this), a BLESSING, or CONTENT (something made
    to share) — everything offering-based, no obligation. It reaches every node within `ttl` hops of
    yours (the LoRa TTL). The id IS the content hash (tamper-evident with no key); if your private
    key is present it is also signed (authentic). Conduit: your own words, attributed — never generated.

    Crisis is honored: a cry for help still reaches your fellowship (that is who should hear it), AND
    real-person resources are returned to YOU immediately — never filed away behind a mesh hop."""
    text = str(text or "").strip()[:_MAX_TEXT]
    if not text:
        return {"ok": False, "error": "text required"}
    node = _read_node(from_fp)
    if not node:
        return {"ok": False, "error": "register your node first (POST /mesh/node)"}
    kind = kind if kind in _KINDS else "word"
    ttl = max(1, min(_MAX_TTL, int(ttl or 2)))
    if kind == "broadcast":
        ttl = _MAX_TTL                     # the Emergency Broadcast reaches the farthest fold
    core = _message_core(from_fp, node.get("callsign", "anon"), kind, text,
                         list(refs or []), ttl, _now(), secrets.token_hex(8))
    canon, mid = _seal_core(core)
    signature, signed = None, False
    if private_key:
        try:
            if identity.signing_available():
                signature = signing.sign_bytes(canon, private_key)
                signed = signing.verify_bytes(canon, signature, node.get("public_key", ""))
                if not signed:            # a key that is not this node's does not get to speak as it
                    return {"ok": False, "error": "signature does not match this node's public key"}
        except Exception:  # noqa: BLE001 — signing is optional; a message never fails for it
            signature, signed = None, False
    stored = dict(core)
    stored["id"] = mid
    stored["signature"] = signature
    stored["signed"] = signed
    with _LOCK:
        _write_json(_msg_path(mid), stored)
    out = {"ok": True, "id": mid, "kind": kind, "signed": signed, "ttl": ttl,
           "reach": max(0, len(_bfs(from_fp, ttl)) - 1),
           "note": ("Sent to the nodes around you. Signed — verifiable offline." if signed
                    else "Sent unsigned — tamper-evident by its id, but not cryptographically authenticated.")}
    # Crisis: real people first, always — imported from ask, never a copied list that drifts.
    from .ask import is_crisis, _CRISIS_RESOURCES
    if is_crisis(text):
        out["crisis"] = {"help": list(_CRISIS_RESOURCES),
                         "message": "Your fellowship will see this — and please reach a real person right now."}
    if kind == "need":
        out["advisory"] = ("The nodes around you will see this and can come to serve. If this is immediate "
                           "danger, call local emergency services (911) now — the fold helps, it does not replace them.")
    return out


def _all_messages() -> List[Dict[str, Any]]:
    """Every live message on the relay, pruning any older than the TTL window as we go."""
    cutoff = _now() - _MSG_TTL_SECONDS
    out: List[Dict[str, Any]] = []
    for p in (_dir() / "msgs").glob("*.json"):
        m = _read_json(p)
        if not m:
            continue
        if int(m.get("created_at", 0)) < cutoff:
            try:
                p.unlink()
            except OSError:
                pass
            continue
        out.append(m)
    return out


def _reaches(m: Dict[str, Any], viewer_fp: str) -> bool:
    src = m.get("from")
    if not src or src == viewer_fp:
        return False
    dist = _bfs(src, int(m.get("ttl", 1)))
    return viewer_fp in dist


def _incoming_counts(viewer_fp: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for m in _all_messages():
        if _reaches(m, viewer_fp):
            counts[m["from"]] = counts.get(m["from"], 0) + 1
    return counts


def _outgoing_counts() -> Dict[str, int]:
    """How much each node has posted — its serving activity, which raises its estate on the map."""
    counts: Dict[str, int] = {}
    for m in _all_messages():
        src = m.get("from")
        if src:
            counts[src] = counts.get(src, 0) + 1
    return counts


def verify_message(m: Dict[str, Any]) -> Dict[str, Any]:
    """The two honest layers, recomputed from the message itself — offline, no server needed.
    UNALTERED: the id is the sha256 of the canonical body (no key). AUTHENTIC: the signature checks
    against the sender node's PINNED public key (the one recorded at registration)."""
    core = _message_core(m.get("from", ""), m.get("callsign", ""), m.get("kind", "word"),
                         m.get("text", ""), m.get("refs", []), int(m.get("ttl", 1)),
                         int(m.get("created_at", 0)), m.get("nonce", ""))
    canon, mid = _seal_core(core)
    unaltered = (mid == m.get("id"))
    authentic = False
    sig = m.get("signature")
    if sig:
        node = _read_node(m.get("from", ""))
        if node:
            authentic = signing.verify_bytes(canon, sig, node.get("public_key", ""))
    return {"unaltered": unaltered, "authentic": authentic, "signed": bool(sig)}


def inbox(fp: str, limit: int = 100) -> Dict[str, Any]:
    """The messages that reached you — from a neighbor, or a neighbor's neighbor within their TTL.
    Each carries its verification so you can trust it by proof, not by the server's word."""
    me = _read_node(fp)
    if not me or not me.get("confessed"):
        return _gate()                    # hidden until you reach the gate — protect those inside
    msgs = []
    for m in _all_messages():
        if _reaches(m, fp):
            v = verify_message(m)
            src = _read_node(m.get("from", ""))
            hops = _bfs(m.get("from", ""), int(m.get("ttl", 1))).get(fp, None)
            msgs.append({"id": m["id"], "from": m.get("from"), "callsign": m.get("callsign", "anon"),
                         "kind": m.get("kind", "word"), "text": m.get("text", ""),
                         "refs": m.get("refs", []),
                         "created_at": m.get("created_at"), "hops_away": hops,
                         "from_callsign_current": (src or {}).get("callsign"),
                         "verify": v})
    msgs.sort(key=lambda x: -(x.get("created_at") or 0))
    return {"ok": True, "you": fp, "count": len(msgs), "messages": msgs[:max(1, int(limit or 100))]}


def guidance() -> Dict[str, Any]:
    return {
        "identity": "The Fellowship Mesh — a network of believers who serve each other. Each of you is a "
                    "node; you message the nodes around you, pool resources, collaborate, and create.",
        "is": [
            "a place to SERVE each other — offer what you have, ask for what you need, work together, make and share",
            "offering-based: everything is a gift freely given; no obligation, no money moves through the mesh",
            "sovereign: the key on your drive is your node — no account, no password, no email",
            "pseudonymous: a callsign, never personal information; no directory of persons to browse",
            "consent-based: you link only to believers (or a church) who hand you their node id",
            "hop-limited like a LoRa mesh: a post reaches the nodes within your TTL, and relays onward",
            "houses and hotels: a node develops as it links up and serves — a lone believer grows toward a hub",
            "verifiable offline: every post's id is its own hash (unaltered), and may be signed (authentic)",
        ],
        "is_not": [
            "a church — we support the churches, we do not replace them (a church that serves here is just another node)",
            "a tithe — nothing here is owed; giving is an offering, not a duty",
            "a directory of people, a database of who-believes-what, or an authority over anyone's walk",
        ],
        "will_not": [
            "store personal information or a location, ever",
            "expose a global list of people (you see only the nodes around you)",
            "present a member's post as an engine-verified verdict",
            "send anything on your behalf, or move any money — you post your own words, you give your own gifts",
        ],
        "hidden": "The path is hidden until a seeker reaches the gate. You find it by ASKING, SEEKING, KNOCKING "
                  "(Matthew 7:7) — with eyes to see and ears to hear (Matthew 13:16). It is not advertised.",
        "gated": "The inner court opens by confession: Jesus Christ is Lord and Messiah (Romans 10:9). The path "
                 "with gates unfolds as you walk it; we do not show the full deck. See guidance().path for the way.",
        "duty": "Above all: PROTECT these people and SERVE them. No PII, no directory, no exposure — protection is "
                "the architecture, not a feature. Serving is the whole point (Galatians 5:13; John 13).",
        "flock": "This is the flock. The gate is the door of the sheep (John 10:7,9); it keeps the fold and holds "
                 "off the wolves (John 10:12). We shepherd, we do not lord over (1 Peter 5:2-3) — a foot-washer's watch.",
        "roles": {
            "member": "one of the flock — the default; everyone who confesses and enters",
            "guide": "leads, feeds, and shows the way (the shepherd — Acts 20:28); conferred, never self-claimed",
            "guardian": "a real-world protector — police, military, or any who guard — who can PHYSICALLY DEPLOY "
                        "when someone is in need (the sheepdog — John 10:12); never a wolf itself",
            "how": "roles are raised up by a Guide (tend), not appointed by oneself; the first Guide is the founding foot-washer",
        },
        "incarnate": ("The mesh reaches off the screen. A need posted here draws the nodes around you to SHOW UP — "
                      "build the ramp, mow the yard, sit with the grieving; and in time, a Guardian may help bring "
                      "someone in danger to safety. Faith works with the hands (James 2:15-16; 1 John 3:18)."),
        "purpose": ("So many have no one to serve — and to serve, to provide value with one's gift, is what a person "
                    "is made for. Here everyone may, whatever their gift; we work to find where it is needed and connect "
                    "it (1 Corinthians 12; Ephesians 4:11-12; 1 Peter 4:10). No gift is too small, no one is surplus."),
        "representative": ("A node stands WITH you and FOR you — your advocate in a situation. In our day: the one who "
                           "drives you home or fixes your tire, and also negotiates with the insurance company or has a "
                           "word with the bully. One called alongside (Galatians 6:2)."),
        "worst_case": ("Built for the worst case, to serve the most innocent. When the grid and the world fail, the same "
                       "sovereign, offline mesh gathers the remnant of the church (Revelation 12:17) — an Emergency "
                       "Broadcast used in daily life, growing toward group buys and food shipped to those in need. "
                       "Resilience is love with foresight (Proverbs 22:3)."),
        "growing_toward": ("The social model is presence with text as the floor — group bulletin boards, and a whiteboard "
                           "on your door where others leave a word or an encouragement. Ahead: pooled group buys and food "
                           "shipped to your door, and a real way to be sent out to serve. Text works when nothing else will."),
        "danger_rule": ("For immediate danger, the authorities and professionals come FIRST — call local emergency "
                        "services (911) now. The fold COORDINATES help; it never replaces them, and it never sends "
                        "the untrained into harm. Protection with wisdom (Matthew 10:16)."),
        "offline": "Online today; the same signed post rides Reticulum/LoRa when the grid is down — the AI lives behind the radio.",
        "path": path(),
        "note": "A door toward the body of Christ, not a replacement for it (John 3:30). Crisis reaches real people first.",
    }


__all__ = ["register_node", "link", "tend", "map_around", "post_message", "inbox",
           "verify_message", "guidance", "path", "CONFESSION"]
