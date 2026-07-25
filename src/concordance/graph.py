"""Connection-graph over the keeping — the data floor for the visual map.

FOUND data only; nothing generated. Nodes are the 'note' cards (the ideas); edges are
the 'connection' cards — each one carries extra.left_card_id / right_card_id /
relationship_kind, and the connection card's OWN id is the sealed receipt for that edge
(so every line on the map links back to a re-checkable seal). We surface and cite; the
engine invents no connection.

Three public views (the keeping is one shared library — both surfaces draw the whole thing):
  overview()             → shelf-clusters + weighted inter-shelf links (the constellation)
  shelf_graph(shelf)     → one shelf embedded in its connections (capped, HONESTLY reported)
  neighborhood(card_id)  → a card + its 1-hop neighbors (the per-card local graph)

Private / archived / quarantined / retracted cards are EXCLUDED — the map shows only the
public keeping. Built once per process (the corpus is immutable at runtime) and cached.
"""
from __future__ import annotations

import threading
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from . import corpus

# Public-visibility is decided by corpus.is_public — ONE source of truth shared with the
# corpus read paths, so this map and the rest of the engine can never disagree on what is
# public (private / public_review / archived / quarantine / retracted are all withheld).

# Caps — keep every view tractable in the browser (no hairball) and honest about it.
_SHELF_SEED_CAP = 260      # top-degree members of a shelf used as the seed set
_SHELF_NODE_CAP = 560      # total nodes (seed + their neighbors) in a shelf view
_NEIGHBOR_CAP = 90         # neighbors shown around one card in the local graph

_GRAPH: Optional[Dict[str, Any]] = None
_GRAPH_LOCK = threading.Lock()


def _tier(c: dict) -> str:
    return ((c.get("source") or {}).get("authority_tier")) or "?"


def _is_public(c: dict) -> bool:
    return corpus.is_public(c)  # ONE source of truth (see corpus.is_public)


def _build() -> Dict[str, Any]:
    """Scan the corpus once: note cards → nodes, connection cards → edges."""
    cards = corpus.default_corpus().cards
    # The endpoints any connection card references — only these can be nodes, so we never build
    # 400k dicts for unconnected cards. Any public card (ANY kind but connection) may be a node;
    # connection cards ARE the edges. This was note-only, which hid every reference deck (history,
    # the builders, the foreshadows, the churches, the acquired sources) from the map.
    endpoints: set = set()
    for c in cards.values():
        if c.get("kind") != "connection" or not _is_public(c):
            continue
        ex = c.get("extra") or {}
        a, b = ex.get("left_card_id"), ex.get("right_card_id")
        if a and b:
            endpoints.add(a)
            endpoints.add(b)
    nodes: Dict[str, Dict[str, Any]] = {}
    for cid in endpoints:
        c = cards.get(cid)
        if not c or c.get("kind") == "connection" or not _is_public(c):
            continue
        nodes[cid] = {"id": cid, "title": c.get("title") or cid,
                      "shelf": c.get("shelf") or "?", "box": c.get("box") or "",
                      "tier": _tier(c), "degree": 0}

    edges: List[Dict[str, str]] = []
    adj: Dict[str, List[tuple]] = defaultdict(list)
    seen_edges = set()  # dedupe: one logical (source, target, kind) edge, not N connection cards
    for cid, c in cards.items():
        if c.get("kind") != "connection" or not _is_public(c):
            continue
        ex = c.get("extra") or {}
        a, b = ex.get("left_card_id"), ex.get("right_card_id")
        if not a or not b or a == b:
            continue
        # Both endpoints must be public note nodes — no dangling or private edges.
        if a not in nodes or b not in nodes:
            continue
        kind = ex.get("relationship_kind") or "see_also"
        if (a, b, kind) in seen_edges:
            continue  # a duplicate connection card for an edge already counted — skip
        seen_edges.add((a, b, kind))
        edges.append({"source": a, "target": b, "kind": kind, "seal": cid})
        nodes[a]["degree"] += 1
        nodes[b]["degree"] += 1
        adj[a].append((b, kind, cid, "out"))
        adj[b].append((a, kind, cid, "in"))

    # The map is the CONNECTED keeping — drop isolated nodes (degree 0) so the constellation is the
    # web that actually exists, and grows exactly as connections are found or minted. (Now that any
    # kind can be a node, without this the 400k+ unconnected cards would swamp the view.)
    nodes = {cid: n for cid, n in nodes.items() if n["degree"] > 0}
    return {"nodes": nodes, "edges": edges, "adj": adj}


def _graph() -> Dict[str, Any]:
    global _GRAPH
    if _GRAPH is None:  # double-checked lock: build once, even under concurrent first-hits
        with _GRAPH_LOCK:
            if _GRAPH is None:
                _GRAPH = _build()
    return _GRAPH


def _node_payload(n: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": n["id"], "title": n["title"], "shelf": n["shelf"],
            "tier": n["tier"], "degree": n["degree"]}


# the nesting-plane relationships (the skeleton) — the plane on which EVERYTHING connects: every
# card is member_of its spine, every spine part_of the Floor/Word. Nothing is an orphan; it may only
# be on a different plane (Matt, 2026-07-25).
_NESTING = {"member_of", "part_of", "nested_in", "figure_of",
            "has_member", "has_part", "contains", "has_figure"}


def overview() -> Dict[str, Any]:
    """The constellation, PLANAR: one super-node per shelf sized by its FULL card count (every card
    belongs to a shelf — nothing is missing), with inter-shelf links on two planes:
      • nesting  — the member_of/part_of skeleton; everything converges on the Floor.
      • semantic — the found connection cards (cites, proof-texts, families, grafts).
    Everything connects; it may only be on a different plane. Memoized (O(cards+edges), once)."""
    g = _graph()
    if "_overview" in g:
        return g["_overview"]
    cards = corpus.default_corpus().cards
    shelf_count: Counter = Counter()
    shelf_tiers: Dict[str, Counter] = defaultdict(Counter)
    nest_pair: Counter = Counter()
    for cid, c in cards.items():
        if c.get("kind") == "connection" or not _is_public(c):
            continue
        sh = c.get("shelf") or "?"
        shelf_count[sh] += 1
        shelf_tiers[sh][_tier(c)] += 1
        # the nesting plane: this card's structural edges, aggregated per shelf-pair
        for l in (c.get("connections") or []):
            if not isinstance(l, dict) or l.get("relationship") not in _NESTING:
                continue
            tc = cards.get(l.get("to_card_id"))
            if tc is None or tc.get("kind") == "connection" or not _is_public(tc):
                continue
            tsh = tc.get("shelf") or "?"
            if tsh != sh:
                nest_pair[tuple(sorted((sh, tsh)))] += 1

    # the semantic plane: the found connection-card edges, per shelf-pair
    sem_pair: Counter = Counter()
    for e in g["edges"]:
        sa = g["nodes"][e["source"]]["shelf"]
        sb = g["nodes"][e["target"]]["shelf"]
        sem_pair[tuple(sorted((sa, sb)))] += 1

    connected: Counter = Counter(n["shelf"] for n in g["nodes"].values())
    clusters = [{"shelf": s, "count": shelf_count[s], "tiers": dict(shelf_tiers[s]),
                 "connected": connected.get(s, 0)}
                for s in sorted(shelf_count, key=lambda x: -shelf_count[x])]
    sem_links = [{"source": a, "target": b, "weight": w, "plane": "semantic"}
                 for (a, b), w in sem_pair.items()]
    nest_links = [{"source": a, "target": b, "weight": w, "plane": "nesting"}
                  for (a, b), w in nest_pair.items()]
    g["_overview"] = {"scope": "overview", "clusters": clusters,
                      "links": sem_links,   # default (back-compat): the semantic plane
                      "planes": {"nesting": nest_links, "semantic": sem_links},
                      "total_nodes": sum(shelf_count.values()),   # the WHOLE keeping — nothing isolated
                      "total_edges": len(g["edges"]),
                      "connected_nodes": len(g["nodes"])}
    return g["_overview"]


def shelf_graph(shelf: str, seed_cap: int = _SHELF_SEED_CAP,
                node_cap: int = _SHELF_NODE_CAP) -> Dict[str, Any]:
    """One shelf embedded in its connections: its top-degree members plus their direct
    neighbors (of any shelf), capped and honestly reported."""
    g = _graph()
    shelf = (shelf or "").strip()
    cache = g.setdefault("_shelf_cache", {})
    ckey = (shelf.lower(), seed_cap, node_cap)
    if ckey in cache:
        return cache[ckey]
    members = [n for n in g["nodes"].values() if (n["shelf"] or "").lower() == shelf.lower()]
    total = len(members)
    members.sort(key=lambda n: -n["degree"])
    seed = members[:max(1, min(seed_cap, 600))]
    keep: Dict[str, Dict[str, Any]] = {n["id"]: n for n in seed}

    node_cap = max(len(keep), min(node_cap, 1200))
    for n in seed:
        if len(keep) >= node_cap:
            break
        for (nb, _k, _s, _d) in g["adj"].get(n["id"], []):
            if nb not in keep:
                keep[nb] = g["nodes"][nb]
                if len(keep) >= node_cap:
                    break

    links = [e for e in g["edges"] if e["source"] in keep and e["target"] in keep]
    nodes = [_node_payload(n) for n in keep.values()]
    out = {"scope": "shelf", "shelf": shelf, "nodes": nodes, "links": links,
           "shown_from_shelf": len(seed), "total_in_shelf": total,
           "nodes_shown": len(nodes)}
    cache[ckey] = out
    return out


def neighborhood(card_id: str, limit: int = _NEIGHBOR_CAP) -> Optional[Dict[str, Any]]:
    """A card + its 1-hop neighbors — the per-card local graph. Neighbors ranked by their
    own connectedness so the most important show first. None if the id is not a public node."""
    g = _graph()
    cid = (card_id or "").strip()
    center = g["nodes"].get(cid)
    if center is None:
        return None
    nbrs = g["adj"].get(cid, [])
    total = len(nbrs)
    nbrs = sorted(nbrs, key=lambda t: -g["nodes"].get(t[0], {}).get("degree", 0))
    shown = nbrs[:max(1, min(limit, 300))]

    keep = {cid: center}
    links = []
    for (nb, kind, seal, direction) in shown:
        keep.setdefault(nb, g["nodes"][nb])
        if direction == "out":
            links.append({"source": cid, "target": nb, "kind": kind, "seal": seal})
        else:
            links.append({"source": nb, "target": cid, "kind": kind, "seal": seal})

    nodes = [_node_payload(n) for n in keep.values()]
    return {"scope": "card", "center": cid, "nodes": nodes, "links": links,
            "shown": len(shown), "total": total}
