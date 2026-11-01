#!/usr/bin/env python3
"""Sorting algorithms on the map — the roll of eighty-six and the bound none can beat (Matt, 2026-10-31: "I'm
interested in all of the sorting algorithms. There are over 80 I know of. Those could integrate.").

The sealed arithmetic lives on the stick (data/sticks/sorting_algorithms.json; run `tick.py sorting_algorithms`)
and the measured counts in tools/sorting_demo.py; this seed puts ONE card in the computer-science box beside the
algorithms pillar and declares its edges on the one map: the floor, the pillar, the logarithm (log2 n! prices the
bound), the reservoir (the readout ends in a sort), Boole's gates (a comparison is one Boolean decision) and the
dictionary's own word. MERGE-writes through chains.merge_seed (idempotent; run on the box, then restart).

    PYTHONPATH=src python tools/seed_sorting_algorithms.py            # merge
    PYTHONPATH=src python tools/seed_sorting_algorithms.py --check    # validate, write nothing
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

CARD = "card_cs_sorting_algorithms"
STICK = "stick_sorting_algorithms_the_roll_and_the_bound_none_can_beat"

FLOOR = "card_floor_computer_science"                 # tools/seed_computer_science.py
ALGORITHMS = "card_cs_algorithms"                     # the pillar: merge sort's 24 at eight items (sealed there)
GATES = "card_cs_logic_gates"                         # a comparison is one Boolean decision; three-way = the third value
F_LOG = "card_floor_logarithm"                        # log2 n! prices the bound
RESERVOIR = "card_tool_reservoir_computing"           # the readout is a weighted sum, then a sort (seed_reservoir_computing.py)
WORD = "card_src_word_sorting_algorithm"              # WordNet: 'an algorithm for sorting a list' (dictionary shelf)
GLOBAL_FLOOR = "card_k_floor_of_discovery"
EXTERNAL = {FLOOR, ALGORITHMS, GATES, F_LOG, RESERVOIR, WORD, GLOBAL_FLOOR}


def _card(cid: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — computer science", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": "reference", "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "computer_science", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    }


CARDS: List[dict] = [
    _card(
        CARD,
        "Sorting algorithms — the roll of eighty-six and the bound none can beat",
        "To sort is to find the one order among n! - and a comparison answers one two-valued question, so no "
        "comparison sort beats log2 n! comparisons (Knuth, TAOCP vol. 3, 5.3.1). Eight items: 8! = 40,320 orders, a "
        "floor of 16 comparisons, and Ford-Johnson's merge insertion (1959) reaches it (sealed on the "
        "sorting_algorithms stick; run tick.py sorting_algorithms). The worst cases, sealed at a thousand items: merge "
        "sort n lg n - 2^lg n + 1 = 8,977 (within 5 percent of the 8,530 floor); heapsort 2 n lg n = 19,932, in place; "
        "insertion n(n-1)/2 = 499,500. Sorting as WIRING: Batcher's odd-even merge network sorts eight wires with 19 "
        "comparators in 6 layers, the proven optimum, and the bitonic sorter with 24 (sealed; tools/sorting_demo.py "
        "builds both and proves them on all 256 zero-one inputs by Knuth's zero-one principle). Shellsort's Knuth gaps "
        "reach 1093 (sealed); the stooge exponent is log 3 / log 1.5 = 2.71 (sealed) - recursion is not speed; "
        "timsort's minrun for a thousand is 63 (sealed) and every list.sort in this engine is timsort with the "
        "powersort merge policy; pancake sort needs at most 18n/11 flips (sealed); bogosort expects (n-1) n! = 282,240 "
        "swaps for eight (sealed) - the roll keeps both ends. EIGHTY-SIX named algorithms in seven families, each with "
        "its origin cited: exchange (bubble, comb, gnome, quicksort and its three-way, dual-pivot, intro and pdq forms, "
        "radix exchange, stooge, slowsort), selection (heapsort, smoothsort, weak-heap, Cartesian tree, tournament, "
        "cycle), insertion (binary, shellsort, library, patience, tree, splay, Ford-Johnson, address calculation), "
        "merge (von Neumann's, natural, timsort, powersort, block, grail, quad/flux/crum, glide, polyphase, cascade, "
        "oscillating), distribution (counting, bucket, LSD and MSD radix back to Hollerith's 1890 census machines, "
        "American flag, multikey quicksort, burstsort, flashsort, spreadsort), networks and parallel (Batcher, "
        "pairwise, Green's sixteen, shear, samplesort, PSRS, merge path, GPU radix, cubesort) and the analog, pessimal and "
        "key-less end (bead, spaghetti, pancake, Franceschini, bogo, sleep, Kahn's and Tarjan's topological sorts). "
        "OUR USE: the engine sorts 362 times in 124 modules (2026-10-31); it relies on STABILITY by name (equal keys "
        "keep the order they were found in - provenance preserved), ranks by a total order with a deterministic "
        "tie-break, walks the priced map with a heap, merges sorted shards, and names its search cache RADIX against "
        "the COMPARISON rung; the ledger's sort of every file per append is the open want. Rests on the "
        "computer-science floor and its algorithms pillar, the logarithm, the reservoir (the readout is a weighted "
        "sum, then a sort), Boole's gates (the three-way comparison is the third value) and the dictionary's word.",
        ["sorting", "sorting algorithm", "sorting algorithms", "sort", "quicksort", "merge sort", "mergesort",
         "heapsort", "insertion sort", "bubble sort", "shellsort", "timsort", "powersort", "radix sort",
         "counting sort", "bucket sort", "sorting network", "batcher", "bitonic", "comparison sort", "lower bound",
         "n log n", "stable sort", "topological sort", "bogosort", "pancake sort", "knuth", "algorithm",
         "computer science", "one map"],
        ref=STICK),
]


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


BRIDGES: List[dict] = [
    _edge(CARD, FLOOR, "part_of",
          "sorting is the algorithms pillar at depth: the roll of eighty-six and the log2 n! bound"),
    _edge(CARD, ALGORITHMS, "connects_at",
          "the pillar seals merge sort's 24 at eight items; the roll seals the exact worst case, 17, and the floor, 16"),
    _edge(CARD, F_LOG, "connects_at",
          "log2 n! prices the comparison bound; the base of the logarithm sits in the stooge exponent log 3 / log 1.5"),
    _edge(CARD, RESERVOIR, "connects_at",
          "the trained readout is a weighted sum and then a sort: top-k by score is a partial sort (a heap)"),
    _edge(CARD, GATES, "connects_at",
          "a comparison is one Boolean decision; the three-way comparison (<, =, >) is the third value, -1 0 1"),
    _edge(CARD, WORD, "connects_at",
          "the dictionary's own definition: an algorithm for sorting a list (WordNet)"),
]


def _validate() -> List[str]:
    errs: List[str] = []
    ids = {c["id"] for c in CARDS} | EXTERNAL
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids:
            errs.append(f"edge target unknown: {e['b']}")
    if len({c["id"] for c in CARDS}) != len(CARDS):
        errs.append("duplicate card ids")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards, {len(BRIDGES)} edges; {'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed) and "
          f"{DATA/'chain_bridges.jsonl'} ({n['bridges']} edges, {len(BRIDGES)} from this seed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
