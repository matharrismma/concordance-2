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

  form      - the SAME FORM on different planes (Matt, 2026-11-25: "systems are fractals on planes. Different planes
              will have the same fractal."): a stick belongs to a form hub (stick_forms.json) only when a verbatim piece
              of its own SEALED or CITED mark carries that form - checked here against the ledger, never against a note.
  chain     - DOWN CHAIN: the lineage the chain map records (a work builds on a work), drawn as itself; a stick joins it
              at a work its own card builds on or cites, or that its own cited text names (author and year), and the
              lineage is walked back to its root, which sits under its floor.
  topic     - a found link that shares only a topic (stick_link_kinds.json, the audit of 2026-11-25): kept, drawn faint,
              never counted as a cross-link.

FLOORS, JOINTS AND FORMS ARE NODES, never cliques: three sticks under one floor are three lines to that floor, not three lines
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
_NOT_LINEAGE = ("card_floor_", "card_joint_", "card_question_", "card_chart_", "card_spine_")
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


_TABLES: Dict[str, Any] = {"key": None, "forms": [], "topic": set()}
_EVIDENCE = TS.SEALED_KINDS + TS.CITED_KINDS
_HERE = Path(__file__).resolve().parent


def _tables() -> Tuple[List[dict], Set[frozenset]]:
    """stick_forms.json and stick_link_kinds.json beside this file, re-read when either changes."""
    files = (_HERE / "stick_forms.json", _HERE / "stick_link_kinds.json")
    key = tuple(f.stat().st_mtime_ns if f.exists() else None for f in files)
    if _TABLES["key"] != key:
        forms, topic = [], set()
        try:
            forms = (json.loads(files[0].read_text(encoding="utf-8")) or {}).get("forms") or []
        except (OSError, ValueError):
            forms = []
        try:
            for pr in (json.loads(files[1].read_text(encoding="utf-8")) or {}).get("topic") or []:
                topic.add(frozenset((pr.get("a"), pr.get("b"))))
        except (OSError, ValueError):
            topic = set()
        _TABLES.update({"key": key, "forms": forms, "topic": topic})
    return _TABLES["forms"], _TABLES["topic"]


def _cited_text(st: Dict[str, Any]) -> str:
    """What a stick CITES: its references, its marks' sources, and every mark that is not a note."""
    return " ".join([str(r) for r in st.get("references") or []] +
                    [str(t.get("source") or "") + " " + (str(t.get("claim") or "") if t.get("kind") != "note" else "")
                     for t in st.get("ticks") or []])


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
    # 5. DOWN CHAIN - the lineage the chain map records, drawn as itself
    lineage = set()
    for a, outs in out.items():
        for b, rel in outs:
            if rel == "builds_on":
                lineage.update((a, b))
    lineage = {c for c in lineage if c and not c.startswith(_NOT_LINEAGE)}
    works: Dict[str, Tuple[str, str]] = {}
    for c in lineage:
        m = re.match(r"^(?:[A-Z]\.\s*)*([A-Z][A-Za-z\-' ]{1,40}?)\s+(\d{4})\b", str((cards.get(c) or {}).get("title") or ""))
        if m:
            works[c] = (m.group(1).split()[-1].split("-")[0], m.group(2))
    attach: Dict[str, Set[str]] = {}
    for cid, sid in stands.items():
        for b, rel in out.get(cid, []):
            if rel in ("builds_on", "cites") and b in lineage:
                attach.setdefault(sid, set()).add(b)
    for sid, st in sticks.items():
        text = _cited_text(st)
        for c, (sur, yr) in works.items():
            if sur in text and yr in text and re.search(rf"\b{re.escape(sur)}\b[^.;]{{0,40}}\b{yr}\b", text):
                attach.setdefault(sid, set()).add(c)
    chain_nodes: Set[str] = set()
    for sid in sorted(attach):
        for c in sorted(attach[sid]):
            link(sid, c, "chain", "cites")
            stack = [c]
            while stack:
                x = stack.pop()
                if x in chain_nodes:
                    continue
                chain_nodes.add(x)
                for b, rel in out.get(x, []):
                    if rel == "builds_on" and b in lineage:
                        link(x, b, "chain", "builds_on")
                        stack.append(b)
                    elif rel in ("part_of", "open_end_of", "member_of") and b in floors:
                        link(x, b, "nested", rel)
    # 6. THE SAME FORM ON DIFFERENT PLANES - each membership proved by the stick's own sealed or cited mark
    forms, topic = _tables()
    form_meta: Dict[str, dict] = {}
    unverified = []
    for f in forms:
        fid = "form:" + str(f.get("id"))
        for m in f.get("members") or []:
            ms, ev = m.get("stick"), str(m.get("evidence") or "")
            mst = sticks.get(ms)
            if mst and ev and any(ev in str(t.get("claim") or "") for t in mst.get("ticks") or [] if t.get("kind") in _EVIDENCE):
                link(ms, fid, "form", ev[:80])
                form_meta[fid] = f
            else:
                unverified.append({"form": f.get("id"), "stick": ms})
    # 7. A found link that shares only a topic is kept, drawn faint, and never counted as a cross-link
    for e in edges.values():
        if e["kind"] == "found" and frozenset((e["source"], e["target"])) in topic:
            e["kind"] = "topic"
    used_floors = {e["target"] for e in edges.values() if e["kind"] == "nested" and e["target"] in floors}
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
        elif nid in form_meta:
            f = form_meta[nid]
            planes = set()                                      # a member's plane: its floor, else its own field
            for ms in {m.get("stick") for m in f.get("members") or []}:
                fl = {e["target"] for e in edges.values() if e["kind"] == "nested" and e["source"] == ms and e["target"] in floors}
                planes |= fl or {"field:" + str((sticks.get(ms) or {}).get("field") or ms)}
            nodes.append({"id": nid, "kind": "form", "title": f.get("title") or nid, "law": f.get("law"),
                          "planes": len(planes), "shelf": "form", "degree": degree[nid] * 2})
        elif nid in chain_nodes:
            nodes.append({"id": nid, "kind": "chain", "title": (cards.get(nid) or {}).get("title") or nid,
                          "shelf": "chain", "degree": degree[nid]})
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
    real = [e for e in links if e["kind"] not in ("nested", "topic")]
    cross = {e["source"] for e in real} | {e["target"] for e in real}
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
                   "by_kind": kinds, "via_alias": kinds.get("crossing", 0), "dead": len(dead), "components": comps,
                   "forms": sum(1 for n in nodes if n["kind"] == "form"), "chain_works": len(chain_nodes),
                   "sticks_on_a_chain": len(attach), "unverified_forms": len(unverified)},
        "unverified_forms": unverified[:50],
        "note": ("Every line is a connection the keeping records: a stick naming a stick or a card, a card on the chain "
                 "map charting, building on or citing another, a joint two questions meet at, the floor a stick sits "
                 "under. Floors and joints are nodes, never cliques. A stick nothing reaches is listed as alone."),
    }
