#!/usr/bin/env python3
"""Build the offline search index — so the whole keeping can be FOUND with no server.

Matt: "take this as far as possible." Offline that only serves what you already visited is thin.
This emits one compact static file, `site/search-index.json`, holding every public seed as a tiny
row — {i: id, t: title, s: shelf, x: a short snippet} — so a browser can search the WHOLE keeping
locally, on the device, with no network. The card's full body still loads from the (cached) /card
endpoint when opened; this is the finding layer.

Compact by design (short keys, trimmed snippet) so it stays small enough to carry. Deterministic
order. Deployed as a static asset (gitignored, like cards.jsonl) and cached by the service worker.

    PYTHONPATH=src python tools/build_offline_index.py            # -> site/search-index.json
    PYTHONPATH=src python tools/build_offline_index.py --check    # count + size only
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

_WS = re.compile(r"\s+")


def _out_path() -> Path:
    # site/ is served statically; allow override for tests
    base = os.environ.get("CONCORDANCE_SITE_DIR", "").strip()
    root = Path(base) if base else (Path(__file__).resolve().parent.parent / "site")
    return root / "search-index.json"


def _snippet(card) -> str:
    body = (card.get("body") or card.get("snippet") or "")
    if not body:
        src = card.get("source") or {}
        body = src.get("label") or ""
    return _WS.sub(" ", str(body)).strip()[:90]


def build():
    from concordance import corpus
    cor = corpus.default_corpus()
    rows = []
    for c in cor.cards.values():
        if not corpus.is_public(c):
            continue
        cid, title = c.get("id"), (c.get("title") or "").strip()
        if not cid or not title:
            continue
        rows.append({"i": cid, "t": title[:120], "s": c.get("shelf") or "", "x": _snippet(c)})
    rows.sort(key=lambda r: r["i"])
    return rows


def main() -> int:
    check = "--check" in sys.argv
    rows = build()
    blob = json.dumps({"v": 1, "rows": rows}, ensure_ascii=False, separators=(",", ":"))
    print(f"  offline index: {len(rows)} seeds · {len(blob.encode('utf-8')) / 1e6:.2f} MB (uncompressed)")
    if check:
        print("  --check: nothing written")
        return 0
    p = _out_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(blob, encoding="utf-8")
    os.replace(tmp, p)
    print(f"  written: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
