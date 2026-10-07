"""M3 shadow demo — a SYNTHETIC traveler walked end to end (Conductor Canon Part II Section 5, M3).

The Canon's first chain is the traveler: PO through ship, with quarantine / MRB / re-quote branches,
authored WITH the shop against the real paper. This is NOT that paper — it is a synthetic, benign traveler
of the same SHAPE, to demonstrate that the Chain executor walks the full M3 path end to end: each step
gated and sealed, movement only along the matching verdict edge, the quarantine branch a real wall, the
whole path kept. Swap in the shop's real steps and the same walk runs for the shop owner.
"""
from __future__ import annotations

from typing import Any, Dict

from . import chain as _chain

_ELAPSED = 1_700_000_000   # a step whose deliberate WAIT window has elapsed (ready for its turn)


def synthetic_traveler(inspect_epoch: int = _ELAPSED) -> Dict[str, Dict[str, Any]]:
    """A benign PO->ship traveler with quarantine / MRB / re-quote branches. `inspect_epoch` lets a caller
    make the inspection step 'fresh' (inside its WAIT window) to exercise the QUARANTINE -> MRB branch."""
    step = _chain.step
    return {
        "po": step("po", "accept a purchase order for 40 aluminum brackets to customer print",
                   {"PASS": "program", "QUARANTINE": "requote"}),
        "program": step("program", "program the CAM and set the job up from the print",
                        {"PASS": "machine", "QUARANTINE": "mrb"}),
        "machine": step("machine", "mill the brackets to the print tolerances with coolant",
                        {"PASS": "inspect", "QUARANTINE": "mrb"}),
        "inspect": step("inspect", "first-article inspection of the brackets against the print",
                        {"PASS": "ship", "QUARANTINE": "mrb"}, target={"created_epoch": inspect_epoch}),
        "ship": step("ship", "pack and ship the finished brackets to the customer", {}),        # terminal
        "mrb": step("mrb", "route nonconforming brackets to the material review board", {}),     # branch terminal
        "requote": step("requote", "return the order to re-quote", {}),                          # branch terminal
    }


def walk(*, config=None, ledger_dir=None, inspect_epoch: int = _ELAPSED) -> Dict[str, Any]:
    """Walk the synthetic traveler from the PO. Happy path reaches `ship`; a fresh `inspect` routes to MRB."""
    return _chain.walk(synthetic_traveler(inspect_epoch), "po", config=config, ledger_dir=ledger_dir)
