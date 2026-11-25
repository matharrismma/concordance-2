"""WHERE THE STICKS POINT (2026-11-25; Matt: "We need everything connected and we want the natural shape to be in those
connections. So missing connections gives us a false sense of shape.")

The graph reads every connection the keeping already RECORDS for a stick, and invents none:

  found     - a stick names another stick in its own statement, references or marks; a stick's chart or question card
              charts, builds on or cites another stick's card on the chain map (data/chain_cards.jsonl and
              data/chain_bridges.jsonl); a stick names a card that stands for another stick.
  crossing  - a stick names an OLD id, read through the dead-link table (tickstick.alias) to the stick it means.
  joint     - a stick's card connects at a joint (card_joint_*): a join mathematics already made between two questions.
  nested    - a stick belongs to a floor: the node its chart charts, walked up the chain map; or a floor card it names;
              or the floor its own `field` names. Every floor is part of the one Floor of Discovery.

FLOORS AND JOINTS ARE NODES, never cliques: three sticks under one floor are three lines to that floor, not three lines
between each other, so a shared floor never reads as a found link and the shape stays the shape the keeping holds.
Whatever no recorded connection reaches stays ALONE and is counted - a missing link is reported, never filled in.

Served read-only by GET /sticks/graph and drawn on site/map.html ("Where the sticks point").
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from . import tickstick as TS

ROOT_FLOOR = "card_k_floor_of_discovery"
_STICK = re.compile(r"\bstick_[a-z0-9_]{3,}")
_CARD = re.compile(r"\bcard_[a-z0-9_]{3,}")
_NESTING = ("part_of", "open_end_of", "builds_on", "member_of", "enables")
_FIELD_HUE = {"mathematics": "dictionary", "number_theory": "hymns", "physics": "atlas", "meta": "classics",
              "engineering": "maker", "computer_science": "recipes", "linguistics": "patristics"}
_CHAIN: Dict[str, Any] = {"key": None, "cards": {}, "out": {}}


def _data_dir(data_dir=None) -> Path:
    return Path(data_dir) if data_dir else Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def _chain(data_dir=None) -> Tuple[Dict[str, dict], Dict[str, List[Tuple[str, str]]]]:
    """The chain map's cards and every out-edge (bridges and the cards' own connections), re-read when a file changes."""
    d = _data_dir(data_dir)
    files = (d / "chain_cards.jsonl", d / "chain_bridges.jsonl")
    key = tuple((str(f), f.stat().st_mtime_ns if f.exists() else None) for f in files)
    if _CHAIN["key"] == key:
        return _CHAIN["cards"], _CHAIN["out"]
    cards: Dict[str, dict] = {}
    out: Dict[str, List[Tuple[str, str]]] = {}
    seen: Set[Tuple[str, str, str]] = set()

    def add(a, b, rel):
        if a and b and (a, b, rel) not in seen:
            seen.add((a, b, rel))
            out.setdefault(a, []).append((b, rel))

    if files[0].exists():
        for line in files[0].read_text(encoding="utf-8").splitlines():
            try:
                c = json.loads(line)
            except ValueError:
                continue
            if isinstance(c, dict) and c.get("id"):
                cards[c["id"]] = c
                for conn in c.get("connections") or []:
                    add(c["id"], conn.get("to_card_id"), conn.get("relationship"))
    if files[1].exists():
        for line in files[1].read_text(encoding="utf-8").splitlines():
            try:
                b = json.loads(line)
            except ValueError:
                continue
            if isinstance(b, dict):
                add(b.get("a"), b.get("b"), b.get("relationship"))
    _CHAIN.update({"key": key, "cards": cards, "out": out})
    return cards, out


def _text(st: Dict[str, Any]) -> str:
    return " ".join([str(st.get("statement") or "")] + [str(r) for r in st.get("references") or []] +
                    [str(t.get("claim") or "") + " " + str(t.get("source") or "") for t in st.get("ticks") or []])


def _ids(rx, text: str, known=()) -> List[str]:
    """The ids named in a text. An id cut where a sentence ended may carry a trailing underscore; a real id can end in one
    too (create() slugs a long question to a fixed width), so the exact match is kept when it is a known id."""
    out, seen = [], set()
    for m in rx.findall(text):
        if m not in known:
            m = m.rstrip("_")
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def graph(data_dir=None) -> Dict[str, Any]:
    sticks = TS.fold(data_dir)
    ids = set(sticks)
    cards, out = _chain(data_dir)
    floors = {c for c in cards if c.startswith("card_floor_")}
    joints = {c for c in cards if c.startswith("card_joint_")}
    # which stick a card stands for (its source.ref); a chart card also touches the node it charts
    stands: Dict[str, str] = {}
    charts: Dict[str, str] = {}
    for cid, c in cards.items():
        ref = str((c.get("source") or {}).get("ref") or "")
        if ref in ids:
            stands[cid] = ref
        for b, rel in out.get(cid, []):
            if rel == "charts":
                charts[cid] = b

    def floor_of(nid: Optional[str], depth: int = 0) -> Optional[str]:
        if not nid or depth > 5:
            return None
        if nid in floors:
            return nid
        for b, rel in out.get(nid, []):
            if rel in _NESTING:
                f = floor_of(b, depth + 1)
                if f:
                    return f
        return None

    edges: Dict[Tuple[str, str], Dict[str, Any]] = {}
    dead: Dict[str, Set[str]] = {}

    def link(a: str, b: str, kind: str, via: Optional[str] = None) -> None:
        if not a or not b or a == b:
            return
        k = (a, b) if kind == "nested" else tuple(sorted((a, b)))
        if k in edges:
            return
        if kind != "nested" and (b, a) in edges:
            return
        edges[k] = {"source": a, "target": b, "kind": kind, "via": via}

    def card_target(sid: str, cid: str, via: str) -> bool:
        """Link a stick to what a card is on the map; True when the card was placed."""
        if cid in floors:
            link(sid, cid, "nested", via)
            return True
        if cid in joints:
            link(sid, cid, "joint", via)
            return True
        if stands.get(cid) and stands[cid] != sid:
            link(sid, stands[cid], "found", via)
            return True
        return False

    for sid, st in sorted(sticks.items()):
        text = _text(st)
        for name in _ids(_STICK, text, ids):                  # 1. the stick names another stick
            if name == sid:
                continue
            if name in ids:
                link(sid, name, "found", None)
                continue
            to = TS.alias(name)
            if to and to in ids:
                link(sid, to, "crossing", name)
            elif not (name.startswith(sid + "_") or sid.startswith(name + "_")):
                dead.setdefault(name, set()).add(sid)
        for cid in _ids(_CARD, text, cards):                   # 2. the stick names a card
            if not card_target(sid, cid, cid) and cid in cards:
                f = floor_of(cid)
                if f:
                    link(sid, f, "nested", cid)
    for cid, sid in stands.items():                            # 3. the stick's own cards on the chain map
        if cid in charts:
            t = charts[cid]
            if not card_target(sid, t, "charts"):
                f = floor_of(t)
                if f:
                    link(sid, f, "nested", "charts")
        for b, rel in out.get(cid, []):
            if rel == "charts":
                continue
            if rel == "connects_at" and b in joints:
                link(sid, b, "joint", rel)
            elif rel in _NESTING and (b in floors or floor_of(b)):
                link(sid, b if b in floors else floor_of(b), "nested", rel)
            elif stands.get(b) and stands[b] != sid:
                link(sid, stands[b], "found", rel)
    nested = {e["source"] for e in edges.values() if e["kind"] == "nested"}
    for sid, st in sticks.items():                             # 4. the floor the stick's own field names
        f = "card_floor_" + str(st.get("field") or "")
        if sid not in nested and f in floors:
            link(sid, f, "nested", "field")
    used_floors = {e["target"] for e in edges.values() if e["kind"] == "nested"}
    for f in sorted(used_floors):                              # every floor is part of the one Floor of Discovery
        link(f, ROOT_FLOOR, "nested", "part_of")

    degree: Dict[str, int] = {}
    for e in edges.values():
        degree[e["source"]] = degree.get(e["source"], 0) + 1
        degree[e["target"]] = degree.get(e["target"], 0) + 1
    nodes = []
    for nid in sorted(degree):
        if nid in sticks:
            st = sticks[nid]
            closed = any(t.get("kind") == "closed" for t in st.get("ticks") or [])
            nodes.append({"id": nid, "kind": "stick", "title": st.get("question") or nid, "closed": closed,
                          "shelf": "codex" if closed else _FIELD_HUE.get(str(st.get("field") or ""), "other"),
                          "degree": degree[nid]})
        elif nid == ROOT_FLOOR:
            nodes.append({"id": nid, "kind": "root", "title": "The Floor of Discovery", "shelf": "patristics",
                          "degree": degree[nid] * 2})
        else:
            c = cards.get(nid) or {}
            kind = "joint" if nid in joints else "floor"
            nodes.append({"id": nid, "kind": kind, "title": c.get("title") or nid,
                          "shelf": "animation" if kind == "joint" else "patristics", "degree": degree[nid]})
    links = list(edges.values())
    stick_nodes = {n["id"] for n in nodes if n["kind"] == "stick"}
    cross = {e["source"] for e in links if e["kind"] != "nested"} | {e["target"] for e in links if e["kind"] != "nested"}
    adj: Dict[str, Set[str]] = {}
    for e in links:
        adj.setdefault(e["source"], set()).add(e["target"])
        adj.setdefault(e["target"], set()).add(e["source"])
    comps, seen = 0, set()
    for n in adj:
        if n in seen:
            continue
        comps += 1
        stack = [n]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            stack.extend(adj[x] - seen)
    kinds: Dict[str, int] = {}
    for e in links:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    return {
        "nodes": nodes, "links": links,
        "dead": [{"id": k, "named_by": sorted(v)} for k, v in sorted(dead.items())],
        "alone": sorted(set(sticks) - stick_nodes),
        "counts": {"sticks": len(sticks), "linked": len(stick_nodes), "unlinked": len(sticks) - len(stick_nodes),
                   "only_nested": len(stick_nodes - cross), "floors": sum(1 for n in nodes if n["kind"] == "floor"),
                   "joints": sum(1 for n in nodes if n["kind"] == "joint"), "links": len(links),
                   "by_kind": kinds, "via_alias": kinds.get("crossing", 0), "dead": len(dead), "components": comps},
        "note": ("Every line is a connection the keeping records: a stick naming a stick or a card, a card on the chain "
                 "map charting, building on or citing another, a joint two questions meet at, the floor a stick sits "
                 "under. Floors and joints are nodes, never cliques. A stick nothing reaches is listed as alone."),
    }
