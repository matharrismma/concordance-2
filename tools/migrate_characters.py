"""Port Easton's entries.jsonl -> easton.jsonl (the character / Bible-dictionary source).

Easton's Bible Dictionary (1897, public domain); neuu-org parse (CC BY 4.0). Ports ALL entries —
the parse's category tags are unreliable (Moses is tagged "concept", Paul "place"), so we do NOT
filter on category; every figure resolves. Deterministic, no network.

    python -m tools.migrate_characters --src <path to Easton entries.jsonl> [--out <easton.jsonl>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from concordance import characters  # noqa: E402

_KEEP = ("id", "name", "text", "scripture_refs", "category", "source", "license", "attribution")


def build(src: Path, out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(src, encoding="utf-8") as f, open(out, "w", encoding="utf-8") as w:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not rec.get("name"):
                continue
            w.write(json.dumps({k: rec.get(k) for k in _KEEP}, ensure_ascii=False) + "\n")
            n += 1
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Filter Easton's entries -> persons.jsonl (PD characters).")
    ap.add_argument("--src", required=True, help="path to Easton's entries.jsonl")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    out = Path(a.out) if a.out else characters._file()
    n = build(Path(a.src), out)
    print(f"wrote {n} persons -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
