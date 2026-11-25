"""WHERE THE STICKS POINT (2026-11-25, the list Matt said to build: "the stick-to-stick graph on the map").

A stick names other sticks in its statement, its references and its marks ("ties stick_the_zeta_function", "see
stick_hilbert_polya"). Those names were prose: nothing drew them, and the stick audit found 45 of them pointing nowhere.
This reads them as edges. Each named id resolves to a stick on this node, or through the dead-link table
(tickstick.alias, kind "via_alias", so an old name is still visible as one), or stays DEAD - a want, shown as such.

Served read-only by GET /sticks/graph and drawn on site/map.html ("Where the sticks point"). Only sticks with at least
one link are nodes; the rest are counted.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from . import tickstick as TS

_ID = re.compile(r"\bstick_[a-z0-9_]{3,}")
# what a stick's node is coloured by on the map: closed first, then the field (keys of site/graph.js SHELF)
_FIELD_HUE = {"mathematics": "dictionary", "number_theory": "hymns", "physics": "atlas", "meta": "classics",
              "engineering": "maker", "computer_science": "recipes", "linguistics": "patristics"}


def _named(st: Dict[str, Any]) -> List[str]:
    text = " ".join([str(st.get("statement") or "")] + [str(r) for r in st.get("references") or []] +
                    [str(t.get("claim") or "") + " " + str(t.get("source") or "") for t in st.get("ticks") or []])
    out, seen = [], set()
    for m in _ID.findall(text):
        m = m.rstrip("_")
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def graph(data_dir=None) -> Dict[str, Any]:
    sticks = TS.fold(data_dir)
    ids = set(sticks)
    links: List[Dict[str, Any]] = []
    seen = set()
    dead: Dict[str, List[str]] = {}
    for sid, st in sorted(sticks.items()):
        for name in _named(st):
            if name == sid:
                continue
            target: Optional[str] = name if name in ids else None
            kind = "found"
            if target is None:
                to = TS.alias(name)
                if to and to in ids:
                    target, kind = to, "via_alias"
            if target is None:
                if name.startswith(sid + "_") or sid.startswith(name + "_"):
                    continue                     # a stick's own id, cut where a sentence ended - not a link
                dead.setdefault(name, []).append(sid)
                continue
            if target == sid or (sid, target) in seen:
                continue
            seen.add((sid, target))
            links.append({"source": sid, "target": target, "kind": "crossing" if kind == "via_alias" else "found",
                          "via": name if kind == "via_alias" else None})
    degree: Dict[str, int] = {}
    for l in links:
        degree[l["source"]] = degree.get(l["source"], 0) + 1
        degree[l["target"]] = degree.get(l["target"], 0) + 1
    nodes = []
    for sid in sorted(degree):
        st = sticks[sid]
        closed = any(t.get("kind") == "closed" for t in st.get("ticks") or [])
        nodes.append({"id": sid, "title": st.get("question") or sid, "closed": closed,
                      "shelf": "codex" if closed else _FIELD_HUE.get(str(st.get("field") or ""), "other"),
                      "degree": degree[sid]})
    return {
        "nodes": nodes, "links": links,
        "dead": [{"id": k, "named_by": sorted(set(v))} for k, v in sorted(dead.items())],
        "counts": {"sticks": len(sticks), "linked": len(nodes), "unlinked": len(sticks) - len(nodes),
                   "links": len(links), "via_alias": sum(1 for l in links if l["via"]), "dead": len(dead)},
        "note": ("Edges are the stick names a stick's own statement, references and marks carry. 'crossing' is a name "
                 "resolved through the dead-link table; a dead name points at no stick on this node - a want."),
    }
