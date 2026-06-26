"""Migrate the 1.0 keeping (one JSON per card) into a single surface-tagged cards.jsonl.

The corpus is DATA, not code — it lives beside the engine, never in git (like 1.0). This
script consolidates the ~11k individual card files into one JSONL the 2.0 ranker reads,
tagging each card's surface so the secular reach (.com) and the witness surface (.org)
draw the right slice from one keeping.

  surface = "witness" if shelf in {codex, patristics, hymns}
            or source.authority_tier in {words_in_red, scripture, creed, catechism, father}
          = "secular" otherwise

Skips archived / quarantine / retracted cards.

    python tools/migrate_cards.py [SRC_CARDS_DIR] [OUT_JSONL]
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

_DEFAULT_SRC = Path(r"C:\Users\hdven\OneDrive\Documents\Claude\Projects\Lighthouse\data\cards")

WITNESS_SHELVES = {"codex", "patristics", "hymns"}
WITNESS_TIERS = {"words_in_red", "scripture", "creed", "catechism", "father"}


def surface_for(card: dict) -> str:
    shelf = (card.get("shelf") or "").lower()
    tier = ((card.get("source") or {}).get("authority_tier") or "").lower()
    if shelf in WITNESS_SHELVES or tier in WITNESS_TIERS:
        return "witness"
    return "secular"


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT_SRC
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        Path(__file__).resolve().parent.parent / "data" / "cards.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        print(f"source not found: {src}")
        return 1

    n = 0
    skipped = 0
    surf = {"secular": 0, "witness": 0}
    with open(out, "w", encoding="utf-8") as w:
        for f in sorted(glob.glob(str(src / "*.json"))):
            try:
                c = json.load(open(f, encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                skipped += 1
                continue
            if not isinstance(c, dict) or not c.get("id"):
                skipped += 1
                continue
            if c.get("retracted") or c.get("lifecycle_stage") in ("archived", "quarantine"):
                skipped += 1
                continue
            c["surface"] = surface_for(c)
            surf[c["surface"]] += 1
            w.write(json.dumps(c, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} cards -> {out} (skipped {skipped}) | "
          f"secular={surf['secular']} witness={surf['witness']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
