#!/usr/bin/env python3
"""Nest the periodic table — no element left an orphan.

Matt: "We are building one tool, so they all need to be integrated. No more orphans."

The 118 element reference cards (card_ref_el_001 … card_ref_el_118) were seeds with no edges —
the whole periodic table floating disconnected. But the periodic table is not a heap; it is an
ORDER. This grafts each element into the one keeping:

  • the sequence  — element Z ↔ element Z+1 (the table read in order of atomic number)
  • the spine     — each element → the created order (Genesis 1) → the Floor of Discovery
  • the worked    — carbon (Z=6) ↔ its Works demonstration "Carbon, by definition"

Every edge is TRUE by construction (definitional order + membership), so the 0-false-positive
discipline holds. Output is GIT-TRACKED (data/element_bridges.jsonl) — content on github — and is
applied reciprocally at load by corpus._apply_bridges, exactly like the other bridge overlays.

    PYTHONPATH=src python tools/nest_elements.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

CREATED_ORDER = "card_k_spine_created_order"   # the trunk of the created order, rooted in the Floor
_EL_RE = re.compile(r"^card_ref_el_(\d+)$")


def _data_dir() -> Path:
    import os
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(d) if d else Path("data"))


def main() -> int:
    from concordance import corpus
    cards = corpus.load_cards()

    # collect the element cards, ordered by atomic number
    els = []
    for cid, c in cards.items():
        m = _EL_RE.match(str(cid))
        if m:
            els.append((int(m.group(1)), cid, c.get("title") or cid))
    els.sort()
    if not els:
        print("no element cards found (card_ref_el_*)")
        return 1

    edges = []
    seen = set()

    def add(a, b, rel, ev, a_title):
        key = (a, b, rel)
        if a == b or key in seen:
            return
        seen.add(key)
        edges.append({"a": a, "b": b, "relationship": rel, "evidence": ev, "a_title": a_title})

    for idx, (z, cid, title) in enumerate(els):
        # the spine: an element of the created order, rooted (through it) in the Floor
        add(cid, CREATED_ORDER, "member_of",
            "an element of the created order (Genesis 1) — matter God spoke into being", title)
        # the sequence: the next element by atomic number
        if idx + 1 < len(els):
            nz, ncid, ntitle = els[idx + 1]
            add(cid, ncid, "precedes",
                f"the next element by atomic number (Z {z} → {nz})", title)
        # the worked demonstration, where one exists (carbon)
        if z == 6:
            add(cid, "card_works_element", "demonstrated_by",
                "carbon's identity, worked and sealed in The Works", title)

    out = _data_dir() / "element_bridges.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in edges) + "\n", encoding="utf-8")
    tmp.replace(out)
    print(f"nested {len(els)} elements → {len(edges)} edges (sequence + created-order spine) → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
