"""Chains / floors / connections — walk a lineage of discovery, and find where two chains connect.

A CHAIN is an ordered path through the keeping's connection graph: each link BUILDS_ON the one before
(reciprocally, the floor ENABLES what follows), rooted in a FLOOR — a spine/root card its members are
PART_OF. This module adds the only logic the engine lacked: a traversal BETWEEN cards and the INTERSECTION
of two chains. It walks the existing connection graph (edges live in bridge overlays — see
`corpus._apply_bridges`), so it NEVER duplicates card bodies: it takes ids and returns ids. Size-aware by
construction.

The graph accessor is injected (`get_card`) so the logic is pure and testable without building the corpus;
it defaults to `corpus.get_card`.
"""
from __future__ import annotations

import json
from collections import deque
from typing import Callable, Dict, List, Optional, Set

BUILDS_ON = "builds_on"   # a later work builds on an earlier one (directional)
ENABLES = "enables"       # the reciprocal: an earlier work enables a later one (floor -> forward)
PART_OF = "part_of"
HAS_PART = "has_part"           # the reciprocal of part_of: a floor's parts (what is proven, what the chain stands on)
CONNECTS_AT = "connects_at"     # an open question meets another at a proven or observed hub (lateral, symmetric)
OPEN_END_OF = "open_end_of"     # an open question hangs off a floor (reciprocal has_open_end)
HAS_OPEN_END = "has_open_end"

# THE FLOORS ON THE ONE MAP (Matt, 2026-10-09: "put them on one map, but make it the one map for the project").
# A registry the map page lists, not a scan of the keeping. Add a floor here when its seed lands.
FLOORS = ("card_floor_standard_model", "card_floor_millennium")


def _default_get_card(card_id: str) -> Optional[dict]:
    from . import corpus
    return corpus.get_card(card_id)


def _neighbors(card: Optional[dict], rels: Optional[Set[str]]) -> List[str]:
    """The ids this card points to, optionally filtered to edges whose relationship is in `rels`
    (None = any relationship). Order-preserving."""
    out: List[str] = []
    for c in ((card or {}).get("connections") or []):
        if not isinstance(c, dict):
            continue
        if rels is None or c.get("relationship") in rels:
            t = c.get("to_card_id")
            if t:
                out.append(t)
    return out


def walk(start: str, rel: str = ENABLES, *, get_card: Callable = _default_get_card,
         max_steps: int = 128) -> List[str]:
    """The ordered lineage from `start`, following edges labelled `rel` (default 'enables' = from the
    floor forward). Linear: at each node take the first `rel` edge not yet visited; stop at a leaf, a
    cycle, or `max_steps`. Returns the ordered card ids — ids only, bounded, no bodies."""
    path: List[str] = []
    seen: Set[str] = set()
    cur: Optional[str] = start
    rels = {rel}
    while cur and cur not in seen and len(path) < max_steps:
        path.append(cur)
        seen.add(cur)
        nxt = [n for n in _neighbors(get_card(cur), rels) if n not in seen]
        cur = nxt[0] if nxt else None
    return path


def intersect(a_start: str, b_start: str, *, rels: Optional[Set[str]] = None,
              get_card: Callable = _default_get_card, max_nodes: int = 512) -> Optional[str]:
    """The NEAREST card reached by both chains — where the two lineages connect. Breadth-first from
    each start over edges whose relationship is in `rels` (None = any); returns the first shared node,
    or None. Bidirectional BFS, so the result is the closest meeting point, not just any shared node."""
    if a_start == b_start:
        return a_start
    seen_a: Set[str] = {a_start}
    seen_b: Set[str] = {b_start}
    qa: deque = deque([a_start])
    qb: deque = deque([b_start])
    visited = 0
    while (qa or qb) and visited < max_nodes:
        if qa:
            cid = qa.popleft()
            visited += 1
            for n in _neighbors(get_card(cid), rels):
                if n in seen_b:
                    return n
                if n not in seen_a:
                    seen_a.add(n)
                    qa.append(n)
        if qb:
            cid = qb.popleft()
            visited += 1
            for n in _neighbors(get_card(cid), rels):
                if n in seen_a:
                    return n
                if n not in seen_b:
                    seen_b.add(n)
                    qb.append(n)
    return None


def floor_map(floor: str, *, get_card: Optional[Callable] = None, max_nodes: int = 512) -> Optional[Dict]:
    """A floor as the one map reads it: its PARTS (what is proven - part_of the floor), its OPEN ENDS (the questions
    hanging off it), and WHERE THE ENDS CONNECT. For each pair of ends: the hub both touch directly (a shared
    connects_at neighbour, with the two edges' own evidence), else the nearest node both reach over connects_at
    edges (an indirect path, reported as `via`), else nothing - and a pair with no direct hub is a recorded MISS,
    never a joint. A floor with no open ends pairs its parts over the forward `enables` edges instead (the
    Standard Model: Fermi and Maxwell meet at Weinberg). Ids, titles and the edges' evidence only; no bodies."""
    get_card = get_card or _default_get_card          # resolved at call time, never bound at import
    fc = get_card(floor)
    if fc is None:
        return None

    def node(cid: str) -> Dict:
        c = get_card(cid) or {}
        return {"id": cid, "title": c.get("title") or cid, "stick": str((c.get("source") or {}).get("ref") or "")}

    def hubs(cid: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for c in ((get_card(cid) or {}).get("connections") or []):
            if isinstance(c, dict) and c.get("relationship") == CONNECTS_AT and c.get("to_card_id"):
                out.setdefault(c["to_card_id"], c.get("evidence") or "")
        return out

    parts = _neighbors(fc, {HAS_PART})
    ends = _neighbors(fc, {HAS_OPEN_END})
    nodes = ends if ends else parts
    joints: List[Dict] = []
    misses: List[Dict] = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            if ends:
                ha, hb = hubs(a), hubs(b)
                shared = [h for h in ha if h in hb]
                if shared:
                    for h in shared:
                        joints.append({"a": a, "b": b, "at": h, "via": None, "evidence": [ha[h], hb[h]]})
                    continue
                via = intersect(a, b, rels={CONNECTS_AT}, get_card=get_card, max_nodes=max_nodes)
            else:
                via = intersect(a, b, rels={ENABLES}, get_card=get_card, max_nodes=max_nodes)
                if via and via != floor:
                    joints.append({"a": a, "b": b, "at": via, "via": None, "evidence": [node(via)["title"], ""]})
                    continue
            misses.append({"a": a, "b": b, "at": None, "via": (via if via != floor else None), "evidence": []})
    hub_ids = sorted({j["at"] for j in joints})
    return {"floor": floor, "title": fc.get("title") or floor,
            "parts": [node(p) for p in parts], "ends": [node(e) for e in ends],
            "hubs": [node(h) for h in hub_ids], "joints": joints, "misses": misses}


def _read_jsonl(p) -> List[dict]:
    if not p.exists():
        return []
    out: List[dict] = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return out


def merge_seed(data_dir, cards: List[dict], bridges: List[dict]) -> Dict[str, int]:
    """THE ONE MAP has one pair of files - data/chain_cards.jsonl and data/chain_bridges.jsonl - and more than one
    seed writes them (the Standard Model, the Millennium floor, the next). Each seed MERGES: by card id and by edge
    (a, b, relationship), its own rows replacing older copies, every other seed's rows kept in order. Idempotent,
    order-independent, the same bytes on every platform."""
    from pathlib import Path
    d = Path(data_dir)
    d.mkdir(parents=True, exist_ok=True)
    cp, bp = d / "chain_cards.jsonl", d / "chain_bridges.jsonl"
    mine = {c["id"]: c for c in cards}
    out_c = [mine.pop(c["id"]) if c.get("id") in mine else c for c in _read_jsonl(cp)] + list(mine.values())

    def key(e):
        return (e.get("a"), e.get("b"), e.get("relationship"))

    mine_b = {key(e): e for e in bridges}
    out_b = [mine_b.pop(key(e)) if key(e) in mine_b else e for e in _read_jsonl(bp)] + list(mine_b.values())
    nl = "\n"
    cp.write_text(nl.join(json.dumps(c, ensure_ascii=False) for c in out_c) + nl, encoding="utf-8", newline=nl)
    bp.write_text(nl.join(json.dumps(e, ensure_ascii=False) for e in out_b) + nl, encoding="utf-8", newline=nl)
    return {"cards": len(out_c), "bridges": len(out_b), "mine_cards": len(cards), "mine_bridges": len(bridges)}


def chain(root: str, *, rel: str = ENABLES, get_card: Callable = _default_get_card) -> Dict:
    """A chain's shape for a reader: its floor (the root), its ordered steps, and its length. Ids only."""
    steps = walk(root, rel, get_card=get_card)
    return {"floor": root, "rel": rel, "steps": steps, "length": len(steps)}
