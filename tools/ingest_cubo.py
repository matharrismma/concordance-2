#!/usr/bin/env python3
"""Ingest the Cubo language cubes into the live coach.

Matt, 2026-09-21: "we won't offer translation but we will teach you the language" → the Cubo
deterministic language coach (the cube: five embodied anchors × three times, found-not-generated,
closed-set checks, no model in the loop). Cubo exports its tracks in the exact live Coach schema;
this folds those exports into `data/curriculum/<subject>_en.json`, the files coach.py serves.

SAFE BY CONSTRUCTION:
  • MERGE, never clobber — an existing subject (es already carries the `lectura_es` reading track)
    keeps every unit it has; Cubo units are added only if their id is not already present.
  • Verbatim — units are copied exactly as authored/exported; nothing is rewritten. generated stays
    False on the source. Idempotent (re-run adds nothing new).
  • The coach expects a LIST of unit dicts per subject; that is what is written.

    PYTHONPATH=src python tools/ingest_cubo.py            # merge data/curriculum/cubo/*.json → curriculum
    PYTHONPATH=src python tools/ingest_cubo.py --check     # report what WOULD change, write nothing
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

CURR = Path("data") / "curriculum"
SRC = CURR / "cubo"


def load_units(path: Path) -> list:
    if not path.exists():
        return []
    d = json.loads(path.read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d.get("units", [])


def main() -> int:
    check = "--check" in sys.argv
    exports = sorted(SRC.glob("coach_export_*.json"))
    if not exports:
        print(f"no Cubo exports in {SRC}", file=sys.stderr)
        return 2
    total_added = 0
    for ex in exports:
        d = json.loads(ex.read_text(encoding="utf-8"))
        subject = d.get("subject")
        new_units = d.get("units", [])
        if not subject or not new_units:
            continue
        dest = CURR / f"{subject}_en.json"
        existing = load_units(dest)
        have = {u.get("id") for u in existing}
        add = [u for u in new_units if u.get("id") not in have]
        merged = existing + add
        merged.sort(key=lambda u: (u.get("track", ""), u.get("unit_seq", 10 ** 9)))
        tracks = sorted({u.get("track") for u in merged})
        print(f"  {subject}: {len(existing)} existing + {len(add)} from Cubo = {len(merged)} units "
              f"· tracks {tracks}")
        total_added += len(add)
        if not check:
            dest.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if check:
        print(f"\n  --check: {total_added} units would be added across {len(exports)} subjects. Nothing written.")
    else:
        print(f"\n  merged {total_added} Cubo units into the coach curriculum.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
