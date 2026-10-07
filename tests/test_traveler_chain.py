"""M3 end-to-end — the synthetic traveler walked through the gate (conductor/traveler.py, 2026-10-07).
The happy path runs PO->program->machine->inspect->ship, every step gated and sealed; a fresh inspection
(inside its WAIT window) quarantines and routes down the MRB branch instead. Synthetic, not the shop's
real paper traveler."""
from __future__ import annotations

import time

from conductor import traveler as T


def test_happy_path_walks_po_to_ship(tmp_path):
    r = T.walk(ledger_dir=tmp_path)
    assert r["status"] == "complete"
    assert [p["step"] for p in r["walked"]] == ["po", "program", "machine", "inspect", "ship"]
    assert all(p["verdict"] == "PASS" for p in r["walked"])
    assert len(r["sealed_path"]) == 5                      # every step of the traveler sealed


def test_failed_inspection_routes_to_mrb(tmp_path):
    r = T.walk(ledger_dir=tmp_path, inspect_epoch=int(time.time()))   # fresh inspect -> WAIT quarantine
    assert [p["step"] for p in r["walked"]] == ["po", "program", "machine", "inspect", "mrb"]
    assert r["walked"][3]["verdict"] == "QUARANTINE"       # inspection held
    assert r["walked"][-1]["step"] == "mrb"                # routed down the quarantine branch, not to ship
