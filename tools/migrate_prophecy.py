"""Port signpost / Christ-pointer traces from the 1.0 almanac -> signposts.jsonl.

Keeps entries whose id starts with 'signpost_'. These are the operator's curated, attributed
pointers to Christ (verdict CONCORDANT / MIXED — never HOLDS). Deterministic filter, no network.

    python -m tools.migrate_prophecy --src <path to almanac entries.jsonl> [--out <signposts.jsonl>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from concordance import prophecy  # noqa: E402

_KEEP = ("id", "title", "category", "verdict", "verification", "wisdom", "triggers", "domains")


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
            if not str(rec.get("id", "")).startswith("signpost_"):
                continue
            w.write(json.dumps({k: rec.get(k) for k in _KEEP}, ensure_ascii=False) + "\n")
            n += 1
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Port signpost traces from the 1.0 almanac.")
    ap.add_argument("--src", required=True, help="path to the 1.0 almanac entries.jsonl")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    out = Path(a.out) if a.out else prophecy._file()
    n = build(Path(a.src), out)
    print(f"wrote {n} signpost traces -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
