"""
CONDUCTOR — reference implementation (PATCHED against the red team of 2026-08-24).

A gated micro-agent architecture for manufacturing. A Conductor classifies incoming shop work and
dispatches small single-purpose agents, the way a breaker panel routes current to branch circuits.
Every agent action passes gates before it counts; halt at first failure, like a fuse. Every dispatch
and return is written to an append-only hash chain before anything reaches the operator. Failures are
decomposed and harvested. Sealed records — success and failure alike — become nutrient packets that
travel between shops over a federation layer that shares proven knowledge without sharing private data.

This file is the CANONICAL BEHAVIOR the package must reproduce. It is stdlib-only, Python 3.10+.
    python -m conductor.reference        # runs the demo

WHAT CHANGED vs the original canon reference, and WHY (red team 2026-08-24):
  1. export_nutrients is now a strict ALLOWLIST, applied RECURSIVELY. The original stripped only
     top-level keys on a denylist, so a gate-trip failure packet leaked price/margin out of the
     building through the nested `reusable` dict — the exact thing the mycelium exists to prevent,
     and an ITAR/EAR exposure for defense work. Only named boundary-knowledge fields ever leave.
  2. The gates FAIL CLOSED. A gate that cannot evaluate its constraint (a required field is absent)
     HALTs — it never PASSES by omission. RED no longer defaults a missing tolerance_source to the
     accepted value. (CANNOT_CHECK != PASS.)
  3. Irreversibility is determined by the DISPATCH (a rule over the work), never by the work order's
     own self-declared flag — an input can no longer clear the witness requirement by omitting it.
     (self_attest never satisfies a gate.)
  4. classify() is CRISIS-FIRST and returns confidence. Unknown work routes to CLARIFY, never a
     silent default to QUOTE — a disguised cry for help can no longer be answered with a price quote.
  5. The Ledger has an optional Ed25519 signer seam and an HONEST integrity claim: a bare hash chain
     is tamper-evident against CORRUPTION, not FORGERY. Production passes the engine's signer.

The gate names here (RED, FLOOR, WITNESS, WAIT) match the LIVE kernel (engine.py), which renamed the
old BROTHERS->WITNESS and GOD->WAIT. In production these DELEGATE to the kernel's
attest_red / attest_floor / validate_packet as a manufacturing DOMAIN PROFILE layered UNDER the
kernel's RED (which still governs RED-005 identity-branding and RED-006 harm-to-children) — they do
not replace it.

Author: Matt Harris / Provident Precision.  License: Public domain.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Optional


# =====================================================================
# LAYER 0: THE IMMUTABLE REFERENCE
# =====================================================================

REFERENCE = MappingProxyType({
    "RED": MappingProxyType({
        "spindle_rpm_max": 12000,
        "coolant_required_materials": ("titanium", "inconel"),
        "guarding_interlock": True,
        "tolerance_source": "customer_print",   # tolerances come from the print, never the agent
    }),
    "FLOOR": MappingProxyType({
        "min_margin_pct": 18.0,
        "min_tool_life_remaining": 0.15,
        "max_schedule_load": 0.90,
    }),
})


class Verdict(str, Enum):
    PASS = "PASS"
    HALT = "HALT"        # RED or FLOOR tripped, OR a required input was absent (fail closed).
    WAIT = "WAIT"        # WITNESS (was BROTHERS): witnesses required, not yet present.
    HOLD = "HOLD"        # WAIT-gate (was GOD): timing gate; everything below holds.


class ReturnState(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE_WITH_HARVEST = "FAILURE_WITH_HARVEST"
    LOSS = "LOSS"
    CLARIFY = "CLARIFY"   # NOT a fourth failure state: the work was never dispatched. Ask, don't guess.
    CRISIS = "CRISIS"     # a cry for help; autonomous action halts and it is surfaced, per crisis-first.


# =====================================================================
# LAYER 1: THE LEDGER (mycelium, local strand)
# Append only. Hash chained. Optionally Ed25519 signed. Written before anything is returned.
# =====================================================================

@dataclass
class Ledger:
    """Append-only hash chain.

    INTEGRITY, stated honestly: the hash chain makes the log tamper-EVIDENT against CORRUPTION —
    flip a byte and verify_chain() fails. It does NOT, by itself, prevent FORGERY: anyone who can
    write the file can regenerate a fully self-consistent alternate history, because nothing binds
    the chain to a key. To resist forgery, pass `sign` (production wires the engine's Ed25519
    signer); verify_chain(verify=...) then also checks each entry's signature, and the head hash
    should be anchored somewhere the writer does not control. Standalone (no signer) = corruption
    evidence only. Do not claim more than that.
    """
    entries: list[dict] = field(default_factory=list)
    sign: Optional[Callable[[bytes], str]] = None

    def append(self, kind: str, body: dict) -> str:
        prev = self.entries[-1]["hash"] if self.entries else "GENESIS"
        entry = {"seq": len(self.entries), "ts": time.time(), "kind": kind, "body": body, "prev": prev}
        raw = json.dumps(entry, sort_keys=True, default=str).encode()
        entry["hash"] = hashlib.sha256(raw).hexdigest()
        if self.sign is not None:
            entry["sig"] = self.sign(raw)           # binds this entry to a key; forgery now needs the key
        self.entries.append(entry)
        return entry["hash"]

    def verify_chain(self, verify: Optional[Callable[[bytes, str], bool]] = None) -> bool:
        prev = "GENESIS"
        for e in self.entries:
            body = {k: v for k, v in e.items() if k not in ("hash", "sig")}
            raw = json.dumps(body, sort_keys=True, default=str).encode()
            if hashlib.sha256(raw).hexdigest() != e["hash"]:
                return False
            if e["prev"] != prev:
                return False
            if verify is not None:                  # forgery resistance only when a verifier is supplied
                if "sig" not in e or not verify(raw, e["sig"]):
                    return False
            prev = e["hash"]
        return True


# =====================================================================
# LAYER 2: THE GATES (fuses). Halt at first failure. FAIL CLOSED.
# =====================================================================

@dataclass
class Submission:
    work_type: str
    payload: dict
    witnesses: int = 0
    timing_clear: bool = True
    irreversible: bool = False        # set by DISPATCH (a rule over the work), never trusted from raw input
    required: tuple = ()              # fields that MUST be present for the gates to mean anything


def presence_gate(sub: Submission) -> tuple[Verdict, str]:
    """CANNOT_CHECK != PASS. A gate cannot vouch for a field it never saw."""
    for f in sub.required:
        if f not in sub.payload or sub.payload[f] is None:
            return Verdict.HALT, f"INPUT: required field '{f}' absent — cannot verify, fail closed"
    return Verdict.PASS, "inputs present"


def red_gate(sub: Submission) -> tuple[Verdict, str]:
    p, red = sub.payload, REFERENCE["RED"]
    if p.get("spindle_rpm", 0) > red["spindle_rpm_max"]:
        return Verdict.HALT, "RED: spindle rpm exceeds safety envelope"
    mat = p.get("material", "")
    if mat in red["coolant_required_materials"] and not p.get("coolant", False):
        return Verdict.HALT, f"RED: {mat} requires coolant, none specified"
    # Fail closed: if the payload carries a tolerance at all, its source MUST be the customer print.
    # No default — an omitted source when a tolerance is present is a RED halt, not a silent pass.
    if ("tolerance" in p) or ("tolerance_source" in p):
        if p.get("tolerance_source") != red["tolerance_source"]:
            return Verdict.HALT, "RED: tolerance must come from the customer print"
    return Verdict.PASS, "RED holds"


def floor_gate(sub: Submission) -> tuple[Verdict, str]:
    p, floor = sub.payload, REFERENCE["FLOOR"]
    if "margin_pct" in p and p["margin_pct"] < floor["min_margin_pct"]:
        return Verdict.HALT, f"FLOOR: margin {p['margin_pct']}% below minimum {floor['min_margin_pct']}%"
    if "tool_life" in p and p["tool_life"] < floor["min_tool_life_remaining"]:
        return Verdict.HALT, f"FLOOR: tool life {p['tool_life']:.0%} below minimum {floor['min_tool_life_remaining']:.0%}"
    if "schedule_load" in p and p["schedule_load"] > floor["max_schedule_load"]:
        return Verdict.HALT, f"FLOOR: schedule load {p['schedule_load']:.0%} exceeds {floor['max_schedule_load']:.0%} ceiling"
    return Verdict.PASS, "FLOOR holds"


def witness_gate(sub: Submission) -> tuple[Verdict, str]:
    # Irreversible actions require human witnesses. The agent can identify the need; it cannot BE the
    # witness. Irreversibility comes from sub.irreversible (set by dispatch), never from raw input.
    if sub.irreversible and sub.witnesses < 2:
        return Verdict.WAIT, f"WITNESS: irreversible action requires 2 witnesses, have {sub.witnesses}"
    return Verdict.PASS, "WITNESS holds"


def wait_gate(sub: Submission) -> tuple[Verdict, str]:
    if not sub.timing_clear:
        return Verdict.HOLD, "WAIT: timing not clear, hold and watch"
    return Verdict.PASS, "WAIT holds"


GATE_SEQUENCE: list[tuple[str, Callable]] = [
    ("INPUT", presence_gate),      # fail closed first
    ("RED", red_gate),
    ("FLOOR", floor_gate),
    ("WITNESS", witness_gate),
    ("WAIT", wait_gate),
]


def run_gates(sub: Submission) -> dict:
    verdicts, tripped = {}, None
    for name, gate in GATE_SEQUENCE:
        verdict, reason = gate(sub)
        verdicts[name] = {"verdict": verdict.value, "reason": reason}
        if verdict is not Verdict.PASS:
            tripped = name
            break
    return {"verdicts": verdicts, "tripped": tripped}


# =====================================================================
# LAYER 3: MICRO AGENTS (pollinators). Single purpose. Narrow contract.
# =====================================================================

@dataclass
class AgentReturn:
    state: ReturnState
    payload: dict = field(default_factory=dict)
    harvest: dict = field(default_factory=dict)


def quote_agent(target: dict) -> AgentReturn:
    try:
        material_cost = target["qty"] * target["unit_material_cost"]
        machine_cost = target["est_hours"] * target["shop_rate"]
        base = material_cost + machine_cost
        price = round(base * (1 + target["target_margin_pct"] / 100), 2)
        return AgentReturn(state=ReturnState.SUCCESS, payload={
            "price": price, "margin_pct": target["target_margin_pct"],
            "material_cost": material_cost, "machine_cost": machine_cost,
        })
    except KeyError as missing:
        return AgentReturn(state=ReturnState.FAILURE_WITH_HARVEST, harvest={
            "gate_context": "pre-gate, input incomplete",
            "missing_field": str(missing),
            "early_signal": "work order arrived without full costing data",
            "redesign_scope": "intake form only, agent unchanged",
        })


def tool_wear_agent(target: dict) -> AgentReturn:
    return AgentReturn(state=ReturnState.SUCCESS, payload={
        "tool_life": target.get("tool_life_remaining", 0.0), "tool_id": target.get("tool_id", "?")})


def schedule_agent(target: dict) -> AgentReturn:
    load = target.get("current_load", 0.0) + target.get("job_load", 0.0)
    return AgentReturn(state=ReturnState.SUCCESS, payload={
        "schedule_load": round(load, 3), "slot": target.get("requested_slot", "next_open")})


# =====================================================================
# LAYER 4: THE CONDUCTOR (breaker panel). Never does work. Classifies, routes, records.
# =====================================================================

TAXONOMY: dict[str, Callable[[dict], AgentReturn]] = {
    "QUOTE": quote_agent,
    "TOOLING": tool_wear_agent,
    "SCHEDULE": schedule_agent,
    # Extend: QUALITY, MATERIAL, MAINTENANCE, PROCESS, HISTORICAL
}

# Fields the gates need present to mean anything, per work type (fail-closed presence check).
REQUIRED_BY_TYPE: dict[str, tuple] = {
    "QUOTE": ("margin_pct",),
    "TOOLING": ("tool_life",),
    "SCHEDULE": ("schedule_load",),
}

# Work whose effect cannot be undone — determined here, by rule, NOT by the work order's own flag.
IRREVERSIBLE_TERMS = ("weld", "scrap", "cut", "heat treat", "anodize", "ship", "destroy", "grind away")

# A cry for help routes CRISIS-FIRST, halts autonomous action, and is surfaced. Standalone list;
# production wires this to the kernel's ask.is_crisis matcher (do not maintain two lists there).
CRISIS_TERMS = ("hurt", "injured", "bleeding", "fire", "trapped", "can't breathe", "suicid",
                "kill myself", "emergency", "help me", "someone is", "911")


def classify(work_order: dict) -> tuple[str, float]:
    """CRISIS-FIRST, confidence-scored. Unknown work is CLARIFY, never a silent default to QUOTE."""
    text = work_order.get("request", "").lower()
    if any(w in text for w in CRISIS_TERMS):
        return "CRISIS", 1.0
    if any(w in text for w in ("quote", "price", "bid", "estimate")):
        return "QUOTE", 0.9
    if any(w in text for w in ("tool", "wear", "insert")):
        return "TOOLING", 0.9
    if any(w in text for w in ("schedule", "slot", "book", "when")):
        return "SCHEDULE", 0.9
    return "CLARIFY", 0.0


def _is_irreversible(work_order: dict, work_type: str) -> bool:
    """A rule over the work — the dispatch decides, not the input. Ratchets UP only: a raw
    irreversible=True is honored, but a raw irreversible=False can never clear the requirement."""
    text = work_order.get("request", "").lower()
    by_words = any(w in text for w in IRREVERSIBLE_TERMS)
    self_declared = bool(work_order.get("target", {}).get("irreversible", False))
    return by_words or self_declared


@dataclass
class Conductor:
    ledger: Ledger = field(default_factory=Ledger)
    well: list[dict] = field(default_factory=list)

    def run(self, work_order: dict) -> dict:
        work_type, confidence = classify(work_order)

        # CRISIS-first: never dispatch a shop agent at a cry for help.
        if work_type == "CRISIS":
            packet = self._seal("CRISIS", "CRISIS", {"early_signal": "crisis language in intake",
                                                     "action": "autonomous action halted; surfaced to a human"})
            self.ledger.append("CRISIS", {"packet": packet["hash"]})
            return {"work_type": "CRISIS", "state": ReturnState.CRISIS.value,
                    "output": {"message": "Routed to a human. No autonomous action taken."}}

        # Unknown work: ask, do not guess. No agent runs.
        if work_type == "CLARIFY" or confidence < 0.7:
            self.ledger.append("CLARIFY", {"request": work_order.get("request", "")})
            return {"work_type": "CLARIFY", "state": ReturnState.CLARIFY.value,
                    "output": {"message": "Ambiguous work order — clarification requested, nothing dispatched."}}

        self.ledger.append("DISPATCH", {"work_type": work_type, "order": work_order})
        agent = TAXONOMY[work_type]
        result = agent(work_order.get("target", {}))

        if result.state is ReturnState.FAILURE_WITH_HARVEST:
            packet = self._seal("FAILURE", work_type, result.harvest)
            self.ledger.append("RETURN", {"state": result.state.value, "packet": packet["hash"]})
            return {"work_type": work_type, "state": result.state.value, "output": result.harvest}

        if result.state is ReturnState.LOSS:
            self.ledger.append("RETURN", {"state": "LOSS"})
            return {"work_type": work_type, "state": "LOSS", "output": {}}

        sub = Submission(
            work_type=work_type,
            payload={**work_order.get("target", {}), **result.payload},
            witnesses=work_order.get("witnesses", 0),
            timing_clear=work_order.get("timing_clear", True),
            irreversible=_is_irreversible(work_order, work_type),
            required=REQUIRED_BY_TYPE.get(work_type, ()),
        )
        gate_result = run_gates(sub)

        if gate_result["tripped"]:
            tripped = gate_result["tripped"]
            harvest = {
                "gate_tripped": tripped,
                "reason": gate_result["verdicts"][tripped]["reason"],
                "early_signal": self._early_signal(tripped, sub.payload),
                "redesign_scope": self._redesign_scope(tripped),
                # NOTE: the sound work is kept LOCALLY for the operator, under a private key, so it
                # never reaches the mycelium. See _seal / export_nutrients (allowlist).
                "_private_reusable": result.payload,
            }
            packet = self._seal("FAILURE", work_type, harvest)
            self.ledger.append("RETURN", {"state": ReturnState.FAILURE_WITH_HARVEST.value,
                                          "gates": gate_result["verdicts"], "packet": packet["hash"]})
            return {"work_type": work_type, "state": ReturnState.FAILURE_WITH_HARVEST.value,
                    "gates": gate_result["verdicts"], "output": harvest}

        packet = self._seal("SUCCESS", work_type, result.payload)
        self.ledger.append("RETURN", {"state": ReturnState.SUCCESS.value,
                                      "gates": gate_result["verdicts"], "packet": packet["hash"]})
        return {"work_type": work_type, "state": ReturnState.SUCCESS.value,
                "gates": gate_result["verdicts"], "output": result.payload}

    # ---- failure harvest protocol ----
    @staticmethod
    def _early_signal(gate: str, payload: dict) -> str:
        return {
            "INPUT": "a required field was missing before the work was trusted",
            "RED": "parameter approached the safety envelope before crossing",
            "FLOOR": "minimum was trending down across recent jobs",
            "WITNESS": "irreversible flag set with no witness lined up",
            "WAIT": "pressure to act arrived before clarity did",
        }.get(gate, "unknown")

    @staticmethod
    def _redesign_scope(gate: str) -> str:
        return {
            "INPUT": "the intake that dropped the field; gates unchanged",
            "RED": "the proposed parameter only; envelope and agent unchanged",
            "FLOOR": "the input that violated the minimum; floor unchanged",
            "WITNESS": "no redesign; supply the witnesses",
            "WAIT": "no redesign; wait and watch the named signal",
        }.get(gate, "full review")

    # ---- sealing ----
    def _seal(self, kind: str, work_type: str, body: dict) -> dict:
        packet = {"kind": kind, "work_type": work_type, "body": body, "sealed_ts": time.time()}
        raw = json.dumps(packet, sort_keys=True, default=str).encode()
        packet["hash"] = hashlib.sha256(raw).hexdigest()
        self.well.append(packet)
        return packet


# =====================================================================
# LAYER 5: MYCELIUM (federation). Only sealed, digested knowledge travels.
# Private data never leaves the building. ALLOWLIST, applied recursively.
# =====================================================================

# The ONLY fields that may cross the shop boundary. An allowlist, not a denylist: anything not named
# here — money, customers, drawings, controlled technical data, any nested private payload — is
# dropped. This is the ITAR/EAR-safe default. To share a new field, add it here on purpose.
SAFE_NUTRIENT_FIELDS = frozenset({
    "kind", "work_type", "gate_tripped", "reason", "early_signal", "redesign_scope",
    "gate_context", "missing_field",
})


def _to_safe(value: Any) -> Any:
    """Recursively keep only allowlisted keys; drop everything else, at every depth."""
    if isinstance(value, dict):
        return {k: _to_safe(v) for k, v in value.items() if k in SAFE_NUTRIENT_FIELDS}
    if isinstance(value, list):
        return [_to_safe(v) for v in value]
    return value


def export_nutrients(conductor: Conductor) -> list[dict]:
    """What leaves the building: gate outcomes, early signals, redesign scopes — boundary knowledge.
    What never leaves: money, customers, drawings, any private or nested payload. Allowlist enforced."""
    out = []
    for packet in conductor.well:
        if packet["kind"] == "CRISIS":
            continue   # a cry for help is never a nutrient
        out.append({
            "kind": packet["kind"],
            "work_type": packet["work_type"],
            "nutrient": _to_safe(packet["body"]),
            "origin_hash": packet["hash"],   # attestation, not identity
        })
    return out


# =====================================================================
# DEMO
# =====================================================================

def demo() -> None:
    conductor = Conductor()
    line = "=" * 64
    orders = [
        {"label": "Quote request, healthy margin", "request": "need a quote on 50 brackets",
         "target": {"qty": 50, "unit_material_cost": 12.40, "est_hours": 22, "shop_rate": 95.0,
                    "target_margin_pct": 24.0}},
        {"label": "Tooling check that trips the FLOOR", "request": "tool wear check before job 4417",
         "target": {"tool_id": "EM-0625-4FL", "tool_life_remaining": 0.08}},
        {"label": "Irreversible weld, no witnesses (by rule, not self-declared)",
         "request": "schedule the weld repair on the fixture",
         "target": {"current_load": 0.62, "job_load": 0.10}, "witnesses": 0},
        {"label": "Disguised crisis in a casual message", "request": "hey someone is hurt in the back, help",
         "target": {}},
        {"label": "Ambiguous work order", "request": "can you look at this thing", "target": {}},
    ]
    for order in orders:
        print(line)
        print(f"WORK ORDER: {order['label']}")
        result = conductor.run(order)
        print(f"  routed to : {result['work_type']}")
        print(f"  state     : {result['state']}")
        for g, v in result.get("gates", {}).items():
            print(f"  {g:9s}: {v['verdict']:5s} {v['reason']}")
        for k, v in result["output"].items():
            print(f"    {k}: {v}")
    print(line)
    print(f"LEDGER: {len(conductor.ledger.entries)} entries, chain verified: {conductor.ledger.verify_chain()}")
    print(f"WELL: {len(conductor.well)} sealed packets")
    print(line)
    print("MYCELIUM EXPORT (what leaves the building — must contain nothing private):")
    for n in export_nutrients(conductor):
        print(f"  [{n['kind']}] {n['work_type']}: {json.dumps(n['nutrient'], default=str)}")


if __name__ == "__main__":
    demo()
