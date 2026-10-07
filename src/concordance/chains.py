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

from collections import deque
from typing import Callable, Dict, List, Optional, Set

BUILDS_ON = "builds_on"   # a later work builds on an earlier one (directional)
ENABLES = "enables"       # the reciprocal: an earlier work enables a later one (floor -> forward)
PART_OF = "part_of"


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


def chain(root: str, *, rel: str = ENABLES, get_card: Callable = _default_get_card) -> Dict:
    """A chain's shape for a reader: its floor (the root), its ordered steps, and its length. Ids only."""
    steps = walk(root, rel, get_card=get_card)
    return {"floor": root, "rel": rel, "steps": steps, "length": len(steps)}
