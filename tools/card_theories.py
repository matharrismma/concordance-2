#!/usr/bin/env python3
"""Card the theory assay — review all the theories, CALIBRATING not judging.

Matt: "Let's focus on Academics. Review all theories … we are calibrating not judging. There are
seeds of wisdom across time and space of our realm. We are gathering, and then providing optimal
conditions for others to produce fruit."

docs/THEORY_CATALOG.md already holds the assay: each theory mapped to the engine domain that can
touch it, with a CALIBRATION class — ✓ (a deterministic verifier can seal checkable claims), ~
(partial — some relations verify, the whole does not), ○ (out of scope for sealing → map-only
RESONANCE; for theology, CONCORDANT — a signpost, never HOLDS). The honest column is often ~ or ○.
"A framework that seals everything is an idol." This gathers the assay into cards so every theory
is a findable seed on the map, wearing its calibration — a measurement against the plumb-line, not
a verdict on the thinker.

Conduit, not source: each card is the assay row (gathered, attributed to the catalog), generated
=False. Nested under a theories spine → the Floor. Git-tracked (the calibration is content).

    PYTHONPATH=src python tools/card_theories.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
_slug = re.compile(r"[^a-z0-9]+")
# "1. **Peano arithmetic axioms** — number_theory — ✓ arithmetic identities seal"
_ROW = re.compile(r"^\s*\d+\.\s+\*\*(.+?)\*\*\s*(?:\((.+?)\))?\s*—\s*([a-z_]+)\s*—\s*([✓~○])\s*(.*)$")
_SECTION = re.compile(r"^##\s+[A-Z]\s*·\s*(.+)$")

_CLASS = {
    "✓": ("seals", "a deterministic verifier can CONFIRM or BREAK checkable claims drawn from it, "
                    "and seal them"),
    "~": ("partial", "specific relations verify; the theory as a whole is not a sealable computation"),
    "○": ("map-only", "out of scope for sealing — foundational, empirical or interpretive (RESONANCE); "
                       "for theology, CONCORDANT: a signpost, never HOLDS"),
}


def _sk(*p):
    return _slug.sub("_", "-".join(str(x) for x in p).lower()).strip("_")


def main() -> int:
    src = Path("docs/THEORY_CATALOG.md")
    if not src.exists():
        print("THEORY_CATALOG.md not found"); return 1
    section = ""
    cards, seen = [], set()
    for line in src.read_text(encoding="utf-8").splitlines():
        ms = _SECTION.match(line)
        if ms:
            section = ms.group(1).strip()
            continue
        m = _ROW.match(line)
        if not m:
            continue
        name, paren, domain, cls, note = m.groups()
        name = name.strip()
        cid = f"card_theory_{_sk(name)}"
        if cid in seen:
            continue
        seen.add(cid)
        klabel, kmean = _CLASS.get(cls, ("", ""))
        full = name + (f" ({paren})" if paren else "")
        body = (f"{full} — an engine domain that can touch it: {domain}. "
                f"Calibration: {klabel} — {kmean}." + (f" {note.strip()}" if note.strip() else ""))
        cards.append({
            "id": cid, "kind": "reference", "title": full[:180], "body": body,
            "source": {"label": "The Theory Assay — calibrated, not judged (docs/THEORY_CATALOG.md)",
                       "url": "", "domain": domain, "authority_tier": "reference"},
            "shelf": "theories", "box": "theory",
            "bands": ["theory", domain, klabel, "calibration"] + [w for w in section.lower().split() if len(w) > 3],
            "subject": name, "connections": [{"to_card_id": "card_spine_theories",
                                              "relationship": "member_of",
                                              "evidence": "a theory the sciences and math run on, calibrated"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
            "generated": False,
            "extra": {"calibration": klabel, "engine_domain": domain, "section": section},
        })
    spine = {
        "id": "card_spine_theories", "kind": "reference",
        "title": "The theories the sciences and math run on",
        "body": ("Every theory the academy stands on, calibrated against what can be sealed: ✓ seals, "
                 "~ partial, ○ map-only. The honest column is often not ✓ — a framework that seals "
                 "everything is an idol. We calibrate; we do not judge. Seeds of wisdom, gathered."),
        "source": {"label": "The Theory Assay", "url": "", "domain": "", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine", "bands": ["theories", "assay", "calibration", "academics", "spine"],
        "subject": "the theories", "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                    "evidence": "the academy's theories, rooted in the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    d = Path("data"); d.mkdir(parents=True, exist_ok=True)
    (d / "theory_cards.jsonl").write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in ([spine] + cards)) + "\n", encoding="utf-8")
    from collections import Counter
    by = Counter(c["extra"]["calibration"] for c in cards)
    print(f"carded {len(cards)} theories (+1 spine) -> data/theory_cards.jsonl  | calibration: {dict(by)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
