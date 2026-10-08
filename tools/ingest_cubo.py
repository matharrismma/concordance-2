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

_DATA = __import__("os").environ.get("CONCORDANCE_DATA_DIR", "").strip()
CURR = (Path(_DATA) if _DATA else Path("data")) / "curriculum"
SRC = CURR / "cubo"


def load_choices(src_dir: Path) -> dict:
    """unit id -> the authored distractor `choices`, read from Cubo's bucket files (corpus/<subject>/*.json).
    Cubo's export drops `choices` as a local extension, but the live coach reads them to name a KNOWN wrong
    turn ("incorrect", with the teaching note) instead of "unclear" — reviewed 2026-10-08."""
    out: dict = {}
    for p in sorted(src_dir.rglob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for u in (d.get("units", []) if isinstance(d, dict) else []):
            ch = (u.get("check") or {}).get("choices")
            if u.get("id") and isinstance(ch, list) and ch:
                out[u["id"]] = list(ch)
    return out


def load_units(path: Path) -> list:
    if not path.exists():
        return []
    d = json.loads(path.read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d.get("units", [])


def main() -> int:
    check = "--check" in sys.argv
    choices: dict = {}
    if "--choices-from" in sys.argv:                 # Cubo's bucket files (corpus/<subject>/*.json), carrying `choices`
        choices = load_choices(Path(sys.argv[sys.argv.index("--choices-from") + 1]))
    exports = sorted(SRC.glob("coach_export_*.json"))
    if not exports:
        print(f"no Cubo exports in {SRC}", file=sys.stderr)
        return 2
    total_added = 0
    total_choices = 0
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
        # the authored distractors, added to a unit that lacks them (idempotent; an authored list is never replaced)
        n_ch = 0
        for u in merged:
            ch = choices.get(u.get("id"))
            if ch and isinstance(u.get("check"), dict) and not u["check"].get("choices"):
                u["check"]["choices"] = list(ch)
                n_ch += 1
        print(f"  {subject}: {len(existing)} existing + {len(add)} from Cubo = {len(merged)} units "
              f"· tracks {tracks}" + (f" · choices carried to {n_ch}" if n_ch else ""))
        total_added += len(add)
        total_choices += n_ch
        if not check and (add or n_ch):
            dest.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if check:
        print(f"\n  --check: {total_added} units would be added, choices carried to {total_choices}, "
              f"across {len(exports)} subjects. Nothing written.")
    else:
        print(f"\n  merged {total_added} Cubo units into the coach curriculum; choices carried to {total_choices}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
