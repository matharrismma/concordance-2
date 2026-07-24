"""The floor, made visible — the structure behind /floor.html.

Matt: "Seeds of knowledge, identified, categorized and mapped to create a floor of reality, and by
seeing the design we will fear God. This is the first step to wisdom." (Proverbs 9:10)

The Nesting made the keeping one walkable tree rooted in the Floor of Discovery. This walks that
tree DOWN from the root (via the directional edges the nesting drew — contains / has_part /
has_member / has_figure) and returns a BOUNDED shape of it: the design, not the 25k-seed data dump.
Each node carries its real child-count, so a spine says "118 elements" while showing only a few — the
form is legible at a glance. It also gathers the two-tree GRAFTS (the created things Scripture names,
joined to their verified science) so the surface can draw the threads that cross the one floor.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import corpus

ROOT = "card_k_floor_of_discovery"
# the reciprocal (downward) relationships the Nesting drew — parent -> child
_DOWN = {"contains", "has_part", "has_member", "has_figure"}
_GRAFT = "names_the_created_thing"


def _title(c: Dict[str, Any]) -> str:
    return (c.get("title") or c.get("id") or "").strip()


def _node(cid: str, cards: Dict[str, Dict], seen: set, depth: int,
          max_depth: int, max_children: int) -> Optional[Dict[str, Any]]:
    c = cards.get(cid)
    if not c or cid in seen:
        return None
    seen.add(cid)
    n: Dict[str, Any] = {"id": cid, "title": _title(c), "shelf": c.get("shelf") or ""}
    kids = [l.get("to_card_id") for l in (c.get("connections") or [])
            if isinstance(l, dict) and l.get("relationship") in _DOWN and l.get("to_card_id")]
    kids = [k for k in kids if k not in seen]
    n["child_count"] = len(kids)
    if depth < max_depth and kids:
        children = [_node(k, cards, seen, depth + 1, max_depth, max_children) for k in kids[:max_children]]
        n["children"] = [x for x in children if x]
    else:
        n["children"] = []
    return n


def tree(max_depth: int = 4, max_children: int = 10) -> Optional[Dict[str, Any]]:
    """The rooted floor, bounded — the Floor of Discovery and what nests beneath it, both halves."""
    cards = corpus.default_corpus().cards
    if ROOT not in cards:
        return None
    return _node(ROOT, cards, set(), 0, max_depth, max_children)


def grafts(limit: int = 24) -> List[Dict[str, str]]:
    """The two trees, joined — the created things Scripture names, beside their verified science
    (gold the metal ⟷ gold element 79). The threads that cross the one floor."""
    cards = corpus.default_corpus().cards
    def _is_science(card: Dict[str, Any]) -> bool:
        return str(card.get("id", "")).startswith("card_ref_") \
            or card.get("shelf") in ("chemistry", "physics", "agriculture", "science")

    out: List[Dict[str, str]] = []
    seen = set()
    for c in cards.values():
        for l in (c.get("connections") or []):
            if isinstance(l, dict) and l.get("relationship") == _GRAFT:
                a, b = c.get("id"), l.get("to_card_id")
                key = tuple(sorted([str(a), str(b)]))
                if key in seen or not b:
                    continue
                seen.add(key)
                bc = cards.get(b) or {}
                # label each side correctly: the element/crop card is the science, the other Scripture
                sci, scr = (c, bc) if _is_science(c) else (bc, c)
                out.append({"science": _title(sci), "scripture": _title(scr)})
                if len(out) >= limit:
                    return out
    return out


def payload() -> Dict[str, Any]:
    """Everything /floor.html needs: the rooted design, the grafts, and the plain measure."""
    cards = [c for c in corpus.default_corpus().cards.values() if corpus.is_public(c)]
    return {
        "root": tree(),
        "grafts": grafts(),
        "verse": {"ref": "Proverbs 9:10",
                  "text": "The fear of the LORD is the beginning of wisdom."},
        "stats": {"seeds": len(cards),
                  "shelves": len({c.get("shelf") for c in cards})},
        "note": ("This finds and maps; it does not generate. By seeing the design — Scripture and "
                 "the created order, one floor — the eye is turned upward, to the Maker."),
    }
