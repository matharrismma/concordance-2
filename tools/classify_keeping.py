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

  CALL NUMBER   shelf . class . item …    e.g.  classics.augustine.confessions
                                                 gutenberg.thomas_jefferson.the_declaration…
                                                 geography.ad.ordino   hebrew_ot.genesis.1.1
  FACETS        a fixed schedule of facet-TYPES; every other band is a VALUE under one of them
                (a verse, a person, a place, a taxon), never a free top-level tag.

The call number itself comes from `concordance.corpus.deep_call` (imported — one source of truth,
so the tool and the runtime that walks the tree can never drift). `deep_call` reads each shelf's
REAL order out of its resident title/bands: the flat acquired shelves — whose box is the generic
"source" — get their true sublayer (a wordlist A→Z, books by author, places by country, verse
cards by book, numbered series by range) instead of one 150k bucket.

    PYTHONPATH=src python tools/classify_keeping.py                 # --check: print the SCHEDULE, change nothing
    PYTHONPATH=src python tools/classify_keeping.py --apply         # add card['call'] + card['facets']
    PYTHONPATH=src python tools/classify_keeping.py --apply --frozen-only   # skip cards.jsonl (acquired shelves only)

It classifies cards.jsonl AND every `*_cards.jsonl` (the frozen acquired shelves — the 637k stub
cards live on disk there as full cards; call + facets ride into the RAM stub via corpus._STUB_KEEPS).
`--apply` is idempotent, streamed card-by-card (the acquired shelves reach 330 MB), atomic
(temp+rename), and backs each file up first. It keeps the content-hash id and adds the call + facets.
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

# The call number derives from the LIBRARY — one source of truth, imported so the tool and the
# runtime can never drift (corpus.deep_call is what browse walks). Works with `PYTHONPATH=src`;
# fall back to inserting src/ so the tool also runs from a bare checkout.
try:
    from concordance.corpus import call_number, deep_call
except ModuleNotFoundError:  # pragma: no cover - convenience for a bare invocation
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from concordance.corpus import call_number, deep_call

# ── The CONTROLLED FACET SCHEDULE ─────────────────────────────────────────────────────────────
# Each structural band maps to exactly one facet TYPE. Everything else is a VALUE (a name, a ref),
# which folds UNDER a facet instead of floating as its own top-level tag.
FACET_OF_BAND: dict[str, str] = {}
FACET_SCHEDULE = {
    "verse":      ["chapter_verse", "cites", "citation", "cross_reference", "xref"],
    "person":     ["person", "mention_person", "father", "prophet", "apostle"],
    "place":      ["place", "mention_place", "region", "city", "geography"],
    "mention":    ["mention"],
    "sequence":   ["sequence", "prev", "next", "chapter", "section", "part"],
    "reference":  ["references", "reference", "proof_text", "proof", "citation_of"],
    "dictionary": ["dictionary", "bible_dictionary", "easton", "isbe", "smith", "vine", "thesaurus"],
    "concept":    ["concept", "scripture", "doctrine", "theme", "stoic", "virtue"],
    # the frozen acquired shelves carry their kind in their bands — fold it into a controlled facet
    # instead of leaving it as top-level noise (unambiguous tokens only, so it never misfires):
    "taxon":      ["organism", "taxonomy", "binomial", "species", "genus"],
    "language":   ["arpabet", "phonetics", "aramaic", "transliteration", "original language"],
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


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def card_files() -> list[Path]:
    """The keeping files to classify. With explicit positional paths, exactly those (so a caller
    can point at just the gitignored frozen shelves and leave git-tracked seeder output alone —
    that output is regenerated from its seeder, never hand-edited here, and the runtime re-derives
    its call at load anyway). With none, auto-discover: the resident substance (cards.jsonl) AND
    the frozen acquired shelves (`*_cards.jsonl` — gutenberg, source, commentary, taxonomy, …),
    which hold the 637k stub cards on disk as full cards, so the finer call + facets ride into the
    stub at load (both are in corpus._STUB_KEEPS). `--frozen-only` skips cards.jsonl."""
    explicit = [Path(a) for a in sys.argv[1:] if not a.startswith("-")]
    if explicit:
        return [p for p in explicit if p.exists()]
    d = _data_dir()
    files: list[Path] = []
    if "--frozen-only" not in sys.argv:
        main_cards = d / "cards.jsonl"
        if main_cards.exists():
            files.append(main_cards)
    files += sorted(p for p in d.glob("*_cards.jsonl") if p.name != "cards.jsonl")
    return files


def _classify_stats(card: dict, call_tree, class_items, facet_type_hits, band_total, tail) -> None:
    """Accumulate one card into the --check schedule counters (no card is held in memory)."""
    call = deep_call(card)
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
                tail[0] += 1  # verse value
            else:
                tail[1] += 1  # bare value


def _apply_file(p: Path) -> tuple[int, int]:
    """Stream a file card-by-card, add call + facets, write atomically after backing up.
    Returns (cards, changed). Never holds the whole file in memory — the acquired shelves reach
    330 MB. Idempotent: re-running only rewrites the same values."""
    bak = p.with_suffix(p.suffix + f".bak-{time.strftime('%Y%m%d%H%M%S')}")
    tmp = p.with_suffix(p.suffix + ".tmp")
    n = changed = 0
    with p.open(encoding="utf-8") as src, tmp.open("w", encoding="utf-8") as out:
        for line in src:
            line = line.strip()
            if not line:
                continue
            try:
                card = json.loads(line)
            except json.JSONDecodeError:
                out.write(line + "\n")  # never drop a line we cannot parse
                continue
            n += 1
            call = deep_call(card)
            if card.get("call") != call:
                changed += 1
            card["call"] = call
            card["facets"] = facets_for(card)
            out.write(json.dumps(card, ensure_ascii=False) + "\n")
    bak.write_bytes(p.read_bytes())  # back up the original only once we have a complete tmp
    os.replace(tmp, p)
    return n, changed


def main() -> int:
    apply = "--apply" in sys.argv
    files = card_files()
    if not files:
        print(f"no card files in {_data_dir()}", file=sys.stderr)
        return 2

    call_tree: dict[str, Counter] = defaultdict(Counter)   # shelf -> class -> count
    class_items: dict[tuple, Counter] = defaultdict(Counter)  # (shelf,class) -> item -> count
    facet_type_hits = Counter()
    band_total = Counter()
    tail = [0, 0]  # [verse values, bare-value tail]
    n = 0
    for p in files:
        for line in p.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                card = json.loads(line)
            except json.JSONDecodeError:
                continue
            n += 1
            _classify_stats(card, call_tree, class_items, facet_type_hits, band_total, tail)

    # ── the SCHEDULE ─────────────────────────────────────────────────────────────────────────
    print("=" * 74)
    print(f"  THE CALL-NUMBER SCHEDULE   (shelf . class . item)   [{len(files)} files, {n} cards]")
    print("=" * 74)
    for sh, classes in sorted(call_tree.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"\n  {sh}.  [{sum(classes.values())} cards, {len(classes)} classes]")
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
    print(f"    {'verse(val)':11} {tail[0]:>7} refs    ← scripture references folded under `verse`")

    distinct = len(band_total)
    singles = sum(1 for _, c in band_total.items() if c == 1)
    controlled = len(FACET_SCHEDULE)
    print("\n" + "-" * 74)
    print("  EFFICIENCY  (before  →  after)")
    print("-" * 74)
    print(f"    band vocabulary : {distinct:>6} free tags ({singles} used once)  →  {controlled} controlled facet-types + values")
    print(f"    identity/place  : opaque hash id only            →  hash id (identity) + call number (place)")
    print(f"    value tail      : {tail[1]} bare tokens floating top-level →  folded under a facet or dropped as noise")
    print(f"    cards classified: {n}")
    print("-" * 74)

    if not apply:
        print("\n  --check: nothing written. Review the schedule above; run --apply to write call + facets.")
        return 0

    # ── APPLY: additive, backed up, atomic, streamed per file ─────────────────────────────────
    total = total_changed = 0
    for p in files:
        cards, changed = _apply_file(p)
        total += cards
        total_changed += changed
        print(f"    {p.name:32} {cards:>7} cards, {changed:>7} call-changed")
    print(f"\n  --apply: wrote call + facets across {len(files)} files — {total_changed}/{total} cards' call deepened.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
