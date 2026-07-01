"""Migrate public-domain commentary from bible.helloao.org into the sovereign store.

Streamed, budgeted, resumable, PD-only. NEVER HANGS by design: every request has a timeout, and
--limit caps how many chapters a single run fetches (the full pull is large — the earlier Adam
Clarke build hung ~2h, so we cap and stream instead of pulling everything at once). Re-run to
expand; already-fetched chapters are skipped.

    python -m tools.migrate_commentary --source matthew-henry --books JHN --limit 30
    python -m tools.migrate_commentary --source matthew-henry --limit 40   # capped default
    python -m tools.migrate_commentary --source matthew-henry --books JHN,ROM,GEN,PSA
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from concordance import commentary  # noqa: E402

BASE = "https://bible.helloao.org/api/c"


def _get(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": "narrow-highway/commentary-migrate"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Migrate PD commentary (streamed, budgeted, resumable).")
    ap.add_argument("--source", default="matthew-henry")
    ap.add_argument("--books", default="", help="comma list of OSIS codes (e.g. JHN,ROM); empty = all")
    ap.add_argument("--limit", type=int, default=40, help="max chapters to fetch this run (budget)")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args(argv)

    out = commentary._dir() / a.source
    out.mkdir(parents=True, exist_ok=True)
    books = _get(f"{BASE}/{a.source}/books.json").get("books", [])
    index = [{"code": b.get("id"), "name": b.get("name"), "commonName": b.get("commonName"),
              "chapters": b.get("numberOfChapters")} for b in books]
    (out / "_books.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"[index] {len(index)} books for {a.source}")

    want = {c.strip().upper() for c in a.books.split(",") if c.strip()}
    fetched = 0
    for b in books:
        code = b.get("id")
        if want and code not in want:
            continue
        n = b.get("numberOfChapters") or 0
        (out / code).mkdir(parents=True, exist_ok=True)
        for ch in range(1, n + 1):
            if fetched >= a.limit:
                print(f"[budget] hit --limit {a.limit}; re-run to continue (resumable).")
                return 0
            fp = out / code / f"{ch}.json"
            if fp.exists() and not a.overwrite:
                continue
            try:
                cj = _get(f"{BASE}/{a.source}/{code}/{ch}.json").get("chapter", {})
                parsed = commentary.parse_chapter(cj)
                parsed.update({"source": a.source, "book_code": code,
                               "book": b.get("commonName"), "chapter": ch})
                fp.write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")
                fetched += 1
                print(f"  {code} {ch}  ({len(parsed['blocks'])} blocks)")
                time.sleep(0.05)
            except Exception as e:  # noqa: BLE001 — skip a bad chapter, never hang the whole run
                print(f"  !! {code} {ch}: {type(e).__name__} {str(e)[:80]}")
    print(f"[done] fetched {fetched} chapters into {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
