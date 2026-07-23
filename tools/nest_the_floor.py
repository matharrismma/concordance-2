#!/usr/bin/env python3
"""The Nesting — make the floor one instrument instead of a pile of parts.

Matt: "It needs a complete recalibration to optimize the system. It's currently a bunch of parts."

The survey proved it: 483 orphan seeds, almost all the science half — 113 of 118 elements, every
physical constant, 80 science essays (the whole radio spectrum told as 12 unlinked essays), the
crops, the nutrients. The growth engine can't reach them: it only draws SHARED-VERSE edges, and an
element names no verse. So the science sat in the floor connected to nothing.

This nests it. One root, everything hung from its spine, every spine rooted in the Floor of
Discovery — so nothing is an orphan and every seed traces to the one floor and thence to the Word
(Romans 1:20: the created order makes the Maker plain). Deterministic and 0-FP: these are true
memberships (an element IS in the periodic table; a crop of the same family IS a rotation sibling),
never speculative.

  • reference seeds  -> their domain spine -> the created order -> the Floor of Discovery
  • science essays   -> the created order  -> the Floor of Discovery
  • crops of one family <-> each other      (real taxonomy, from the agriculture verifier)

New spine seeds (git-tracked, faithful headers, author matt) go to data/nesting_seeds.jsonl; the
edges to data/nesting_bridges.jsonl, applied reciprocally at corpus load (the same overlay the
reference->Scripture grafts use). The 25k cards.jsonl is never mutated on disk.

    python tools/nest_the_floor.py --check   # preview counts, write nothing
    python tools/nest_the_floor.py           # write both files (run where cards.jsonl lives)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
# existing spine essays already in the keeping (verified live 2026-07-23)
PERIODIC = "card_n_6e7a5b14e556"     # "The periodic table — the map of the elements"
CHEMISTRY = "card_n_4d5234cab477"    # "Chemistry — the bookkeeping of atoms"

# spine seeds this pass creates (git-tracked). The one floor has two halves that each root in it:
# the created order (general revelation) and the Word (special revelation).
CREATED_ORDER = "card_k_spine_created_order"
THE_WORD = "card_k_spine_the_word"
ARCHETYPES = "card_k_spine_archetypes"
SPINES = [
    {"id": CREATED_ORDER, "surface": "secular",
     "title": "The created order — the science of the floor",
     "body": ("General revelation, mapped. Every verified thing in nature — the elements, the "
              "constants, the spectrum, the living code — is a seed on the one floor, and the floor "
              "is rooted in Scripture. The invisible things of God are clearly seen, understood by "
              "the things that are made (Romans 1:20); so the science does not compete with the Word "
              "but nests beneath it and points to the Maker."),
     "bands": ["created order", "general revelation", "science", "Romans 1:20", "spine", "floor"]},
    {"id": "card_k_spine_constants", "surface": "secular",
     "title": "The physical constants — the fixed numbers of creation",
     "body": ("The unchanging numbers the universe is measured by — the speed of light, Planck's "
              "constant, the charge of the electron. They are not chosen by us; they are found. "
              "Each constant is a seed here, and together they are a spine of the created order."),
     "bands": ["physics", "constants", "measurement", "spine", "created order"]},
    {"id": "card_k_spine_crops", "surface": "secular",
     "title": "The crops — what the ground brings forth",
     "body": ("The plants the ground yields and the soil and season each needs. Every crop is a "
              "seed here, joined to its kind (botanical family) and, where Scripture names it, to "
              "the Word. Let the earth bring forth (Genesis 1:11)."),
     "bands": ["agriculture", "crops", "Genesis 1:11", "spine", "created order"]},
    {"id": "card_k_spine_nutrition", "surface": "secular",
     "title": "Nutrition — what the body is given to need",
     "body": ("What the body requires to be sustained — the nutrients and the amounts. Each is a "
              "seed here, a spine of the created order concerned with the keeping of the body."),
     "bands": ["nutrition", "diet", "the body", "spine", "created order"]},
    {"id": THE_WORD, "surface": "witness",
     "title": "The Word — special revelation, the other half of the floor",
     "body": ("The floor has two halves and they are one. Alongside the created order stands the "
              "Word — the Scripture, its figures, its teachings. Special and general revelation are "
              "not two domains but one floor (see the Floor of Discovery). This spine gathers the "
              "seeds of the Word so they too hang from the one root."),
     "bands": ["the Word", "special revelation", "Scripture", "spine", "floor", "witness"]},
    {"id": ARCHETYPES, "surface": "witness",
     "title": "The archetypes — figures of the Word",
     "body": ("The people and scenes of Scripture read as living patterns — Jonah fleeing, Elijah "
              "under the juniper, Peter at the fire, Thomas doubting. Each is a seed of the Word, "
              "a figure the reader is invited to recognize and enter."),
     "bands": ["archetypes", "figures", "Scripture", "spine", "the Word", "witness"]},
]
SPINE_IDS = {s["id"] for s in SPINES}


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def _load(path: Path):
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except ValueError:
                pass
    return out


def _spine_seed(s):
    surface = s.get("surface", "secular")
    return {"id": s["id"], "kind": "note", "title": s["title"], "body": s["body"],
            "source": {"label": "Operator's seed (Matt) — the Nesting: one floor, one root",
                       "url": "", "ref": "created_order", "authority_tier": "matt"},
            "shelf": "science" if surface == "secular" else "codex", "box": "floor",
            "bands": s["bands"], "connections": [],
            "author": "matt", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": surface,
            "generated": False}


def compute(cards):
    by_id = {c.get("id"): c for c in cards}
    have = lambda i: i in by_id or i in SPINE_IDS  # noqa: E731
    edges = []

    def add(a, b, rel, ev):
        if have(a) and have(b) and a != b:
            edges.append({"a": a, "b": b, "relationship": rel, "evidence": ev})

    # 1. reference seeds -> their spine
    ref = [c for c in cards if str(c.get("id", "")).startswith("card_ref_")]
    for c in ref:
        cid = c["id"]
        if cid.startswith("card_ref_el_"):
            add(cid, PERIODIC, "member_of", "an element of the periodic table")
        elif cid.startswith("card_ref_pc_"):
            add(cid, "card_k_spine_constants", "member_of", "a physical constant")
        elif cid.startswith("card_ref_crop_"):
            add(cid, "card_k_spine_crops", "member_of", "a crop of the field")
        elif cid.startswith("card_ref_rda_"):
            add(cid, "card_k_spine_nutrition", "member_of", "a nutrient the body needs")

    # 2. the spine chain up to the one floor
    add(PERIODIC, CHEMISTRY, "part_of", "the periodic table is the map of chemistry")
    add(CHEMISTRY, CREATED_ORDER, "part_of", "chemistry is part of the created order")
    for sp in ("card_k_spine_constants", "card_k_spine_crops", "card_k_spine_nutrition"):
        add(sp, CREATED_ORDER, "part_of", "a spine of the created order")
    add(CREATED_ORDER, FLOOR, "nested_in", "the created order is rooted in the one floor (Romans 1:20)")

    # 3. orphan science / concept essays -> the created order (general revelation, mapped)
    def links(c):
        return c.get("connections") or c.get("links") or []
    for c in cards:
        cid = c.get("id", "")
        if cid in SPINE_IDS or cid in (PERIODIC, CHEMISTRY):
            continue
        if c.get("shelf") in ("science", "concepts") and c.get("kind") != "reference" \
                and len(links(c)) == 0:
            add(cid, CREATED_ORDER, "part_of", "a seed of the created order")

    # 3b. the WORD half — the archetypes and the orphan codex seeds root in the one floor too
    for c in cards:
        cid = c.get("id", "")
        if cid in SPINE_IDS:
            continue
        if c.get("box") == "archetypes" and len(links(c)) == 0:
            add(cid, ARCHETYPES, "figure_of", "a figure of the Word")
        elif c.get("shelf") == "codex" and len(links(c)) == 0:
            add(cid, THE_WORD, "part_of", "a seed of the Word")
    add(ARCHETYPES, THE_WORD, "part_of", "the archetypes are figures of the Word")
    add(THE_WORD, FLOOR, "nested_in", "the Word is the other half of the one floor")

    # 3c. catch-all: no seed left outside the floor. Any remaining orphan roots in the created
    # order (or the Word, if it is a witness seed) — every seed is on the one floor.
    for c in cards:
        cid = c.get("id", "")
        if cid in SPINE_IDS or len(links(c)) != 0:
            continue
        if any(e["a"] == cid or e["b"] == cid for e in edges):
            continue
        root = THE_WORD if c.get("surface") == "witness" else CREATED_ORDER
        add(cid, root, "part_of", "a seed on the one floor")

    # 4. crop laterals — same botanical family are rotation siblings (real taxonomy)
    try:
        from concordance.verifiers import agriculture as ag
        fam = ag._CROP_FAMILY
        by_family = {}
        for crop, f in fam.items():
            cid = f"card_ref_crop_{crop}"
            if cid in by_id:
                by_family.setdefault(f, []).append(cid)
        for f, ids in by_family.items():
            ids = sorted(ids)
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    add(ids[i], ids[j], "same_family", f"both of the {f} family (rotation siblings)")
    except Exception as e:  # noqa: BLE001
        print(f"  (crop laterals skipped: {e})")

    # dedup
    seen, uniq = set(), []
    for e in edges:
        k = (e["a"], e["b"])
        if k not in seen:
            seen.add(k)
            uniq.append(e)
    return uniq


def main() -> int:
    check = "--check" in sys.argv
    d = _data_dir()
    cards = _load(d / "cards.jsonl") + _load(d / "reference_cards.jsonl") \
        + _load(d / "keystone_seeds.jsonl") + _load(d / "nesting_seeds.jsonl")
    if not cards:
        print(f"  no cards under {d}")
        return 1
    edges = compute(cards)
    from collections import Counter
    rels = Counter(e["relationship"] for e in edges)
    print(f"  spine seeds: {len(SPINES)}  | nesting edges: {len(edges)}")
    print("  by relationship: " + ", ".join(f"{k} {v}" for k, v in rels.most_common()))
    if check:
        print("  --check: nothing written")
        return 0
    sp_path, br_path = d / "nesting_seeds.jsonl", d / "nesting_bridges.jsonl"
    for path, rows in ((sp_path, [_spine_seed(s) for s in SPINES]), (br_path, edges)):
        tmp = path.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
        print(f"  written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
