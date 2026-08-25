"""M0 wiring: a work order flows capture -> the ENGINE's gates -> the chain, using only existing organs.

This is the "thin package over the engine." The gates here are the deployed kernel's — validate_and_seal
runs RED -> FLOOR -> PATH -> WITNESS -> WAIT and returns the trail; the manufacturing envelope rides as
red_items / floor_items inside the engine's DECISION_PACKET (a domain profile, fuller in M2). The
reference's standalone gates (reference.py) remain canon FOR BEHAVIOR, not this production path — so the
kernel's RED-005 (identity branding) and RED-006 (harm to children) still govern every shop packet.

Only a PASS record seals to the chain (ledger.seal_to_ledger). A predatory plan trips RED and never
seals; an order still inside its WAIT window quarantines and never seals. The engine decides, not us.
"""
from __future__ import annotations

import time
from typing import Optional

from concordance.config import EngineConfig
from concordance.engine import validate_and_seal
from concordance import ledger as _ledger

from . import reference as _ref
from .contracts import GateResult, SealedPacket, WorkOrder


def work_order_to_packet(wo: WorkOrder, created_epoch: int) -> dict:
    """Map a manufacturing work order onto the engine's DECISION_PACKET envelope."""
    work_type, _conf = _ref.classify({"request": wo.request})
    red = _ref.REFERENCE["RED"]
    floor = _ref.REFERENCE["FLOOR"]
    witnesses = list(wo.witnesses) or ["shop_owner"]
    return {
        "domain": "governance",
        "kind": "DECISION_PACKET",
        "scope": "local",
        "created_epoch": created_epoch,
        "wait_window_seconds": 0,          # scope default governs the deliberate window
        "witness_count": len(witnesses),   # kept consistent with the DECISION_PACKET list
        "DECISION_PACKET": {
            "title": f"{work_type} — order {wo.order_id or '?'} @ {wo.shop_id or '?'}",
            "scope": "local",
            "red_items": [
                f"spindle rpm <= {red['spindle_rpm_max']}",
                "tolerances come from the customer print, never the agent",
                "coolant required for titanium and inconel",
            ],
            "floor_items": [
                f"margin >= {floor['min_margin_pct']}%",
                f"tool life >= {floor['min_tool_life_remaining']:.0%}",
                f"schedule load <= {floor['max_schedule_load']:.0%}",
            ],
            "way_path": wo.request.strip() or "no request text supplied",
            "execution_steps": ["classify the work", "dispatch the agent", "run the gates", "seal the record"],
            "witnesses": witnesses,
        },
    }


def _default_config() -> EngineConfig:
    # Run the gates and the governance/moral scan without the corpus-heavy schema path (M0 wiring).
    return EngineConfig(skip_schema_validation=True)


def gate_result(wo: WorkOrder, *, now_epoch: Optional[int] = None,
                config: Optional[EngineConfig] = None) -> GateResult:
    """Run the work order through the engine gates; return the trail without sealing."""
    created = int(wo.target.get("created_epoch") or (now_epoch or int(time.time())))
    packet = work_order_to_packet(wo, created)
    record = validate_and_seal(packet, config=config or _default_config(), now_epoch=now_epoch)
    verdicts = tuple((g.gate, g.status, "; ".join(getattr(g, "reasons", ()) or ())) for g in record.gate_results)
    tripped = next((g.gate for g in record.gate_results if g.status != "PASS"), None)
    return GateResult(overall=record.overall, verdicts=verdicts, tripped=tripped)


def gate_and_seal(wo: WorkOrder, *, now_epoch: Optional[int] = None,
                  config: Optional[EngineConfig] = None, ledger_dir=None) -> SealedPacket:
    """capture -> validate_and_seal (engine gates) -> chain (on PASS). Existing organs only."""
    work_type, _conf = _ref.classify({"request": wo.request})
    created = int(wo.target.get("created_epoch") or (now_epoch or int(time.time())))
    packet = work_order_to_packet(wo, created)
    record = validate_and_seal(packet, config=config or _default_config(), now_epoch=now_epoch)

    ledger_path = None
    if record.overall == "PASS":
        summary = f"{work_type}: {(wo.request.strip() or 'order')[:60]}"
        ledger_path = str(_ledger.seal_to_ledger(record, summary=summary, ledger_dir=ledger_dir))

    return SealedPacket(
        kind="SUCCESS" if record.overall == "PASS" else "FAILURE",
        work_type=work_type,
        overall=record.overall,
        summary=packet["DECISION_PACKET"]["title"],
        ledger_path=ledger_path,
    )
