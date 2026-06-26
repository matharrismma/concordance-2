"""Migrate the WEB Bible verses into 2.0 (data, gitignored — like the keeping).

Copies the World English Bible (public domain) verse rows the scripture verifier reads.
The deep Strong's / original-language layer (lw/00_source) is NOT migrated here — it is
a separate subsystem; this is verse-text ref-resolution only.

    python tools/migrate_bible.py [SRC_VERSES_JSONL] [OUT_JSONL]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_DEFAULT_SRC = Path(r"C:\Users\hdven\OneDrive\Documents\Claude\Projects\Lighthouse\data\bible_en\verses.jsonl")


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT_SRC
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        Path(__file__).resolve().parent.parent / "data" / "bible_en.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        print(f"source not found: {src}")
        return 1
    n = 0
    with open(src, encoding="utf-8") as r, open(out, "w", encoding="utf-8") as w:
        for line in r:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("book") and d.get("chapter") is not None and d.get("verse") is not None:
                # keep only the fields the verifier needs (slim, faithful)
                w.write(json.dumps({
                    "book": d["book"], "book_abbr": d.get("book_abbr"),
                    "chapter": d["chapter"], "verse": d["verse"],
                    "text": d.get("text", ""), "translation": d.get("translation"),
                }, ensure_ascii=False) + "\n")
                n += 1
    print(f"wrote {n} verses -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
