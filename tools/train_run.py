#!/usr/bin/env python3
"""Drive the training loop with the REAL public-domain acquire path (the Tortoise).

This is the runner that makes teaching ≡ training live: it takes the strongest-demand unmet wants and
fills them by pulling + carding a public-domain source, then reinforces and closes each. BOUNDED and
SUPERVISED by design — a small step count, one want at a time, every step printed — because a generator
that picks its own path must never run unwatched (a generator picking its own path is a destructive act).
It mints nothing itself: `expand.pull_and_card` owns the write and all its guards (PD-only public, else
held for review; idempotent; bounded fetch). Gated by CONCORDANCE_TRAINING — off = a no-op.

    PYTHONPATH=src CONCORDANCE_TRAINING=1 python tools/train_run.py [steps]     # steps default 3
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import expand, training  # noqa: E402


def acquire(query: str) -> dict:
    """Adapt the Tortoise's pull_and_card to the loop's {card_id, kept} contract. Honest empty when no
    public-domain source yields real cards — the want then stays open."""
    try:
        r = expand.pull_and_card(query, subject="", config=None)
    except Exception as e:  # noqa: BLE001 — a pull that errors just leaves the want open
        return {"status": f"error:{e.__class__.__name__}"}
    if (r or {}).get("status") != "carded":
        return {"status": (r or {}).get("status") or "no_source"}
    parent = r.get("source_card") or {}
    cards = r.get("cards") or []
    cid = parent.get("id") or (cards[0].get("id") if cards else "")
    return {"card_id": cid, "kept": int(r.get("kept") or 0),
            "trust": "pd" if r.get("released_public") else "held",
            "lifecycle_stage": "public" if r.get("released_public") else "public_review",
            "status": r.get("status")}


def main() -> int:
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    if not training.enabled():
        print("CONCORDANCE_TRAINING is off — set it to run. (No-op.)")
        return 0
    res = training.run(acquire_fn=acquire, steps=steps)
    print(json.dumps(res, indent=2, ensure_ascii=False)[:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
