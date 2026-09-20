#!/usr/bin/env python3
"""Classify the keeping — give every card a Dewey-style CALL NUMBER and a CONTROLLED FACET set,
derived from the fields that already exist (shelf + box + bands). Nothing is authored; the tree
is already implicit in the box prefixes and the structural bands — this makes it explicit and
controlled, so a filling library stays navigable.

Matt, 2026-09-20: "make sure our labeling system is efficient. Dewey decimal system is a great example."

The problem it fixes: shelf (11 classes) is clean, but `box` (271 bins) hides its hierarchy in a
prefix, and `bands` is a 2,370-tag FOLKSONOMY (58% used once) that explodes as we card 340 GB of
library. Dewey's two disciplines we're missing at that level: one COMPACT HIERARCHICAL CODE, and
one CONTROLLED vocabulary.

  CALL NUMBER   shelf . class . item      e.g.  classics.augustine.confessions
                                                 codex.catechism.heidelberg
                                                 connections.mention  (edges)
  FACETS        a fixed schedule of ~9 facet-TYPES; every other band is a VALUE under one of them
                (a verse, a person, a place, a source), never a free top-level tag.

    PYTHONPATH=src python tools/classify_keeping.py            # --check: derive + print the SCHEDULE, change nothing
    PYTHONPATH=src python tools/classify_keeping.py --apply    # add card['call'] + card['facets'], backed up + atomic

`--apply` is idempotent (re-run skips cards already carrying the same call), atomic (temp+rename),
and backs the file up first. It keeps the content-hash id (identity) and adds the call number (shelf).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

# ── The CONTROLLED FACET SCHEDULE ─────────────────────────────────────────────────────────────
# Each structural band maps to exactly one facet TYPE. Everything else is a VALUE (a name, a ref),
# which folds UNDER a facet instead of floating as its own top-level tag.
FACET_OF_BAND: dict[str, str] = {}
FACET_SCHEDULE = {
    "verse":      ["chapter_verse", "cites", "citation", "cross_reference", "xref"],
    "person":     ["person", "mention_person", "father", "prophet", "apostle"],
    "place":      ["place", "mention_place", "region", "city"],
    "mention":    ["mention"],
    "sequence":   ["sequence", "prev", "next", "chapter", "section", "part"],
    "reference":  ["references", "reference", "proof_text", "proof", "citation_of"],
    "dictionary": ["dictionary", "bible_dictionary", "easton", "isbe", "smith", "vine"],
    "concept":    ["concept", "scripture", "doctrine", "theme", "stoic", "virtue"],
    "provenance": ["auto_detected", "manual", "curated", "imported"],
}
for _facet, _bands in FACET_SCHEDULE.items():
    for _b in _bands:
        FACET_OF_BAND[_b] = _facet

# a scripture reference, spelled many ways: "Luke 21:28", "Ps 90:2", "1 Corinthians 13:1",
# "Rom 8:23-24", "psalm_091", "Jas 1:17". Values that match go under the `verse` facet.
_VERSE_RE = re.compile(
    r"^(?:[1-3]\s?)?(?:[A-Z][a-z]{1,11}\.?|Ps|Jas|Rom|Phil|Matt|Gen|Exod|Deut|Rev)\s?\d{1,3}(?:[:.]\d{1,3})?(?:-\d{1,3})?$"
)
_PSALM_RE = re.compile(r"^psalm_\d+$", re.I)


def _facet_for_value(band: str) -> str:
    """A band that is not a facet-TYPE is a VALUE — place it under a facet by shape."""
    if _VERSE_RE.match(band) or _PSALM_RE.match(band):
        return "verse"
    return "value"  # a name/source token; the source work already lives in the call number's item


def call_number(card: dict) -> str:
    """shelf . class . item — the Dewey-style spine, derived from shelf + box."""
    shelf = (card.get("shelf") or "misc").strip().lower()
    box = (card.get("box") or "").strip().lower()
    if not box:
        return shelf
    if "_" in box:
        cls, item = box.split("_", 1)
    else:
        cls, item = box, ""
    return ".".join(p for p in (shelf, cls, item) if p)


def facets_for(card: dict) -> dict[str, list[str]]:
    """Turn the flat `bands` list into {facet_type: [values]} using the controlled schedule.

    A bare value FOLDS under a facet instead of floating: a verse ref → `verse`; a name that
    co-occurs with a `person`/`place`/`concept` type → that facet; a token already carried by the
    call number's source (the box) → dropped as redundant; anything else → `subject` (kept, never
    lost)."""
    out: dict[str, list[str]] = defaultdict(list)
    bands = card.get("bands") or []
    if not isinstance(bands, list):
        bands = [bands]
    box = (card.get("box") or "").strip().lower()
    redundant = set(box.split("_")) | ({box} if box else set())  # already in the call number
    types: set[str] = set()
    values: list[str] = []
    for b in bands:
        if not isinstance(b, str) or not b:
            continue
        if b in FACET_OF_BAND:
            types.add(FACET_OF_BAND[b])
        else:
            values.append(b)
    for t in types:
        out.setdefault(t, [])  # record the facet-type even when it carries no named value
    for v in values:
        if _VERSE_RE.match(v) or _PSALM_RE.match(v):
            out["verse"].append(v)
        elif v.lower() in redundant:
            continue  # the source work is already the call number's item
        elif "person" in types:
            out["person"].append(v)
        elif "place" in types:
            out["place"].append(v)
        elif "concept" in types:
            out["concept"].append(v)
        else:
            out["subject"].append(v)  # a named value with no clearer facet — kept, not dropped
    return {k: sorted(set(v)) for k, v in out.items()}


def _cards_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "cards.jsonl"


def main() -> int:
    apply = "--apply" in sys.argv
    p = _cards_path()
    if not p.exists():
        print(f"no cards at {p}", file=sys.stderr)
        return 2

    call_tree: dict[str, Counter] = defaultdict(Counter)  # shelf -> class -> count
    class_items: dict[tuple, Counter] = defaultdict(Counter)  # (shelf,class) -> item -> count
    facet_type_hits = Counter()
    band_total = Counter()
    verse_values = 0
    value_tail = 0
    n = 0
    rows = []
    for line in p.open(encoding="utf-8"):
        card = json.loads(line)
        n += 1
        rows.append(card)
        call = call_number(card)
        parts = call.split(".")
        sh = parts[0]
        cls = parts[1] if len(parts) > 1 else "_"
        item = parts[2] if len(parts) > 2 else ""
        call_tree[sh][cls] += 1
        if item:
            class_items[(sh, cls)][item] += 1
        for b in (card.get("bands") or []):
            if isinstance(b, str) and b:
                band_total[b] += 1
                if b in FACET_OF_BAND:
                    facet_type_hits[FACET_OF_BAND[b]] += 1
                elif _VERSE_RE.match(b) or _PSALM_RE.match(b):
                    verse_values += 1
                else:
                    value_tail += 1

    # ── the SCHEDULE ─────────────────────────────────────────────────────────────────────────
    print("=" * 74)
    print("  THE CALL-NUMBER SCHEDULE   (shelf . class . item)")
    print("=" * 74)
    for sh, classes in sorted(call_tree.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"\n  {sh}.  [{sum(classes.values())} cards]")
        for cls, cc in classes.most_common(9):
            items = class_items.get((sh, cls))
            sample = ""
            if items:
                sample = "  { " + ", ".join(k for k, _ in items.most_common(4)) + (" … }" if len(items) > 4 else " }")
            print(f"      {sh}.{cls}  ({cc}){sample}")

    print("\n" + "=" * 74)
    print("  THE CONTROLLED FACET SCHEDULE   (fixed types; everything else is a value)")
    print("=" * 74)
    for facet in FACET_SCHEDULE:
        hits = facet_type_hits.get(facet, 0)
        members = ", ".join(FACET_SCHEDULE[facet])
        print(f"    {facet:11} {hits:>7} cards   ← {members}")
    print(f"    {'verse(val)':11} {verse_values:>7} refs    ← scripture references folded under `verse`")

    distinct = len(band_total)
    singles = sum(1 for _, c in band_total.items() if c == 1)
    controlled = len(FACET_SCHEDULE)
    print("\n" + "-" * 74)
    print("  EFFICIENCY  (before  →  after)")
    print("-" * 74)
    print(f"    band vocabulary : {distinct:>6} free tags ({singles} used once)  →  {controlled} controlled facet-types + values")
    print(f"    identity/place  : opaque hash id only            →  hash id (identity) + call number (place)")
    print(f"    value tail      : {value_tail} bare tokens floating top-level →  folded under a facet or dropped as noise")
    print(f"    cards classified: {n}")
    print("-" * 74)

    if not apply:
        print("\n  --check: nothing written. Review the schedule above; run --apply to write call + facets.")
        return 0

    # ── APPLY: additive, backed up, atomic ───────────────────────────────────────────────────
    bak = p.with_suffix(p.suffix + f".bak-{time.strftime('%Y%m%d%H%M%S')}")
    bak.write_bytes(p.read_bytes())
    tmp = p.with_suffix(p.suffix + ".tmp")
    changed = 0
    with tmp.open("w", encoding="utf-8") as out:
        for card in rows:
            call = call_number(card)
            if card.get("call") != call:
                changed += 1
            card["call"] = call
            card["facets"] = facets_for(card)
            out.write(json.dumps(card, ensure_ascii=False) + "\n")
    os.replace(tmp, p)
    print(f"\n  --apply: wrote call + facets to {changed}/{n} cards. Backup: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
