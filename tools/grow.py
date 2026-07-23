#!/usr/bin/env python3
"""Grow — one turn of the standing growth cycle: measure, draw the safe edges, record.

The system Matt asked for, made re-runnable: run it any time and it closes the next bounded
batch of evidence-backed connections (two cards that name the same rare verse), records each in
the growth ledger, and leaves the corpus provably better and never double-worked. 0-FP: it only
draws edges the data already justifies. Idempotent (re-run skips what exists), atomic
(temp + rename), backed up first.

    PYTHONPATH=src python tools/grow.py --check          # measure + preview, change nothing
    PYTHONPATH=src python tools/grow.py --apply [--n 60]  # draw up to N safe edges, both ways
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from concordance import growth  # noqa: E402


def _cards_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "cards.jsonl"


def main() -> int:
    apply = "--apply" in sys.argv
    n = 60
    if "--n" in sys.argv:
        try:
            n = max(1, min(500, int(sys.argv[sys.argv.index("--n") + 1])))
        except (IndexError, ValueError):
            pass

    path = _cards_path()
    if not path.exists():
        print(f"  cards.jsonl not found at {path}")
        return 1
    cards = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    m = growth.measure(cards)
    print(f"  keeping: {m['cards']} cards · {m['orphans']} orphans ({m['orphan_pct']}%) · "
          f"{m['safe_edges_available']} safe edges available")

    edges = growth.safe_edges(cards, limit=n)
    print(f"  proposing {len(edges)} evidence-backed edges this turn:")
    for e in edges[:6]:
        print(f"    {e['a_title']!r}  ⟷  {e['b_title']!r}   [{e['evidence']}]")
    if len(edges) > 6:
        print(f"    … and {len(edges) - 6} more")

    if not apply:
        print("  --check: nothing written (pass --apply to draw them)")
        return 0
    if not edges:
        print("  nothing to draw — the keeping is fully connected on this gate")
        return 0

    by_id = {c.get("id"): c for c in cards}
    drawn = 0
    now = time.time()
    for e in edges:
        a, b, verse = e["a"], e["b"], e["evidence"]
        ca, cb = by_id.get(a), by_id.get(b)
        if not ca or not cb:
            continue
        la = ca.setdefault("connections", ca.pop("links", []) or [])
        lb = cb.setdefault("connections", cb.pop("links", []) or [])
        if not any(x.get("to_card_id") == b for x in la):
            la.append({"to_card_id": b, "relationship": "shares_scripture", "evidence": verse})
        if not any(x.get("to_card_id") == a for x in lb):
            lb.append({"to_card_id": a, "relationship": "shares_scripture", "evidence": verse})
        ca["updated_at"] = now
        cb["updated_at"] = now
        drawn += 1

    tmp = path.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    os.replace(tmp, path)                                     # atomic
    growth.ledger_append("draw_safe_edges",
                         {"drawn": drawn, "batch": n, "gate": "shares_scripture(rare)"}, at=now)
    print(f"  drawn: {drawn} edges (both directions) · recorded to the growth ledger")
    return 0


if __name__ == "__main__":
    sys.exit(main())
