"""Migrate the Strong's / original-language backend data into 2.0 (gitignored).

Copies the public-domain WEB+Strong's databases and the Strong's lexicons the
triangulation backend reads, mirroring the web/ + original/lexicon/ layout under
data/strongs/. Data lives beside the engine, not in git.

    python tools/migrate_strongs.py [SRC_LW_00_SOURCE] [OUT_STRONGS_DIR]
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

_DEFAULT_SRC = Path(r"C:\Users\hdven\OneDrive\Documents\Claude\Projects\Lighthouse\lw\00_source")

_FILES = [
    ("web/web.db", "web/web.db"),
    ("web/concordance.db", "web/concordance.db"),
    ("original/lexicon/strongs_greek.json", "original/lexicon/strongs_greek.json"),
    ("original/lexicon/strongs_hebrew.json", "original/lexicon/strongs_hebrew.json"),
]


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT_SRC
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        Path(__file__).resolve().parent.parent / "data" / "strongs")
    n = 0
    for sr, dr in _FILES:
        s = src / sr
        d = out / dr
        if not s.exists():
            print(f"  MISSING {s}")
            continue
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
        n += 1
        print(f"  copied {sr} ({d.stat().st_size // 1024} KB)")
    print(f"migrated {n}/{len(_FILES)} -> {out}")
    return 0 if n == len(_FILES) else 1


if __name__ == "__main__":
    sys.exit(main())
