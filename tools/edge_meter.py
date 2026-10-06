#!/usr/bin/env python3
"""THE EDGE METER — audit the keeping's bridges (connection edges) over the WHOLE corpus and write
data/edges.json, so The Bridge shows a real needle for the Bridges component (Matt, 2026-10-06).

    PYTHONPATH=src CONCORDANCE_DATA_DIR=<dir> python tools/edge_meter.py        # writes <dir>/edges.json

An edge is a connection card (kind="connection") linking two card ids with a typed relationship and
evidence. VALID = both endpoints resolve to a real card; DANGLING = an endpoint is missing. CARD-BACKED =
the edge has a stable connection-card id (the graph's re-findable 'seal'=cid) — not bare adjacency. This
is the structural test for the Bridges: does every relation resolve?
"""
from __future__ import annotations

import glob
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def measure() -> dict:
    from concordance import corpus
    resident = corpus.default_corpus().cards
    ids = set(resident.keys())
    for db in sorted(glob.glob(str(_data_dir() / "shards" / "*.db"))):
        con = sqlite3.connect(db)
        for (cid,) in con.execute("SELECT id FROM cards"):
            ids.add(cid)
        con.close()

    edges = valid = dangling = card_backed = 0
    by_kind: dict = {}

    def tally(c):
        nonlocal edges, valid, dangling, card_backed
        if c.get("kind") != "connection":
            return
        edges += 1
        ex = c.get("extra") or {}
        a = ex.get("left_card_id")
        b = ex.get("right_card_id")
        k = ex.get("relationship_kind") or ex.get("relationship") or "?"
        by_kind[k] = by_kind.get(k, 0) + 1
        if a in ids and b in ids:
            valid += 1
        else:
            dangling += 1
        if c.get("id"):
            card_backed += 1

    for c in resident.values():
        tally(c)
    for db in sorted(glob.glob(str(_data_dir() / "shards" / "*.db"))):
        con = sqlite3.connect(db)
        cur = con.execute("SELECT json FROM cards")
        while True:
            batch = cur.fetchmany(5000)
            if not batch:
                break
            for (js,) in batch:
                try:
                    tally(json.loads(js))
                except Exception:  # noqa: BLE001
                    continue
        con.close()

    return {
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "card_ids": len(ids),
        "edges": edges, "valid": valid, "dangling": dangling, "card_backed": card_backed,
        "valid_ratio": round(valid / edges, 4) if edges else 0.0,
        "card_backed_ratio": round(card_backed / edges, 4) if edges else 0.0,
        "by_kind": dict(sorted(by_kind.items(), key=lambda x: -x[1])),
        "note": ("an edge is a connection card linking two cards; valid = both endpoints resolve; "
                 "card-backed = re-findable by its connection-card id (the graph's 'seal'). The structural "
                 "test for the bridges — not a judgment of coverage or cross-domain reach."),
    }


def main() -> int:
    out = _data_dir() / "edges.json"
    data = measure()
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, out)
    print("edges %d · valid %.1f%% · dangling %d · card-backed %.1f%% -> %s"
          % (data["edges"], 100 * data["valid_ratio"], data["dangling"],
             100 * data["card_backed_ratio"], out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
