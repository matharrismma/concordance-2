#!/usr/bin/env python3
"""Bridge the reference cards to Scripture — the two trees graft where the Bible names a thing.

Matt: "They just aren't getting connected. We are there to show how all of the pieces connect."

Carding the science was step one. This is the connection: many things the periodic table and the
field guide describe are the very things Scripture names — the metals of the temple (gold, silver,
bronze/copper, iron, tin) and the plants of the land (wheat, barley, the olive, the vine, garlic,
leek, onion). Where a reference card's `subject` EXACTLY matches an Easton dictionary card's
subject, we draw one evidence-backed edge between them. Exact-subject only, so 0-FP — no stray
token like "no" ever matches.

The edges are written to a small, GIT-TRACKED overlay `data/reference_bridges.jsonl`, applied
reciprocally by `corpus.load_cards` at load time. The 25k `cards.jsonl` is never mutated, and the
bridges survive any regeneration of the reference cards (they live in their own file). Reproducible
from the two card stores at any time.

    python tools/bridge_reference_to_scripture.py --check   # preview, write nothing
    python tools/bridge_reference_to_scripture.py           # write the overlay
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

_EASTON = re.compile(r"^\s*Easton'?s?:\s*", re.I)
# subjects too generic to be a faithful single-thing bridge even on an exact match
_STOP = {"no", "an", "am", "or", "so", "on", "at", "if", "us", "ye", "go", "do", "he"}


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def _load(path: Path):
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue
    return out


def _easton_subject(card) -> str:
    """The single thing an Easton dictionary card is about, normalized — or '' if not one."""
    if card.get("shelf") != "dictionary":
        return ""
    t = _EASTON.sub("", (card.get("title") or "")).strip().lower()
    # a single word (or hyphen/space compound) that is not a generic stopword
    if not t or t in _STOP or len(t) < 3:
        return ""
    return t


def compute(ref_cards, base_cards):
    """Return the list of reciprocal bridge edges (deterministic order)."""
    # index Easton cards by subject; keep the FIRST (dictionary order) for determinism
    subj_to_id = {}
    for c in base_cards:
        s = _easton_subject(c)
        if s and s not in subj_to_id:
            subj_to_id[s] = c["id"]
    edges = []
    seen = set()
    for c in sorted(ref_cards, key=lambda x: x.get("id", "")):
        subj = (c.get("subject") or "").strip().lower()
        if not subj or subj in _STOP:
            continue
        target = subj_to_id.get(subj)
        if not target:
            continue
        key = (c["id"], target)
        if key in seen:
            continue
        seen.add(key)
        edges.append({"a": c["id"], "b": target, "subject": subj,
                      "relationship": "names_the_created_thing",
                      "evidence": f"Scripture names “{subj}”; this is its verified reference.",
                      "a_title": (c.get("title") or "")[:60]})
    return edges


def main() -> int:
    check = "--check" in sys.argv
    d = _data_dir()
    ref_cards = _load(d / "reference_cards.jsonl")
    base_cards = _load(d / "cards.jsonl")
    if not ref_cards:
        print(f"  no reference cards at {d / 'reference_cards.jsonl'}")
        return 1
    if not base_cards:
        print(f"  no cards.jsonl at {d / 'cards.jsonl'} — run where the keeping lives (droplet)")
        return 1
    edges = compute(ref_cards, base_cards)
    print(f"  reference cards: {len(ref_cards)} | Easton subjects matched: {len(edges)}")
    for e in edges:
        print(f"    {e['a_title']!r}  <->  Easton: {e['subject'].capitalize()}")
    if check:
        print("  --check: nothing written")
        return 0
    out = d / "reference_bridges.jsonl"
    tmp = out.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for e in edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    os.replace(tmp, out)
    print(f"  written: {out} ({len(edges)} bridges) — git-tracked, applied at corpus load")
    return 0


if __name__ == "__main__":
    sys.exit(main())
