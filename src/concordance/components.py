"""COMPONENTS — the engine as a vacuum-tube computer, computed live (docs/COMPONENTS.md).

Matt, 2026-10-06: *"Think of a vacuum tube computer … regulators, capacitors, diodes, transistors,
Antennae, Vacuum tubes … I see it kind of steam punk."* And: *"Motion executive is conductor."*

This is the live, computed form of docs/COMPONENTS.md: every engine part classified by electronic
PRIMITIVE, placed on an AUTHORITY PLANE (the one chain — Main → Steward → Conductor → Reflex → Scribe →
witness+seal), given a LAYER (permanent / precision / wear / consumable) and an EVIDENCE STATUS (earned,
never claimed). The REGULATORS — the Steward and Reflex parts that govern what passes rather than compute
data — carry a firing order and a LIVE READING pulled from the running engine where it is cheap and real,
and an honest `pending` where a meter needs more plumbing. Never a faked needle.

Vocabulary is Matt's own hardware design system (one vocabulary across the robot, the watch and the
engine). Stdlib + cheap disk/import resolution only — safe on every request, like systems.py; it loads no
corpus. The Bridge (site/bridge.html, GET /components) renders this.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── The authority chain (the orchestration) ──────────────────────────────────────────────────────
# One chain, in order; each plane may do less than the plane above it, never more.
PLANES: List[Dict[str, str]] = [
    {"plane": "Main", "owns": "perceive, reason, propose a bounded action",
     "cannot": "self-authorize; emit a verdict"},
    {"plane": "Steward", "owns": "admit a bounded capability; fails closed",
     "cannot": "run the work itself; relax a hard limit"},
    {"plane": "Conductor", "owns": "deterministic, bounded execution of an approved corridor",
     "cannot": "enlarge the mission/force/corridor; author a tactic"},   # the robot bible's Motion Executive
    {"plane": "Reflex", "owns": "the hard envelope, in real time",
     "cannot": "be overridden by Main or the Conductor"},
    {"plane": "Scribe", "owns": "capture events, prepare receipts",
     "cannot": "alter authority or state"},
    {"plane": "Witness", "owns": "verify independently, seal permanently (outside the requester)",
     "cannot": "run inside the requesting process"},
]
_PLANE_ORDER = [p["plane"] for p in PLANES]

LAYERS = ["Permanent structure", "Precision cartridge", "Wear element", "Consumable"]
# Evidence status, earned never claimed (robot bible §14.1).
STATUS_LADDER = ["Concept", "Prototype-pending", "Experimental", "Verified",
                 "Supplier-dependent", "Production-ready"]

# ── The parts, by primitive (docs/COMPONENTS.md §4) ──────────────────────────────────────────────
# Each row names code that exists; `modules` are resolved live so a part that cannot even import shows OUT.
# `status` is the DECLARED evidence class; report() downgrades a part to its wired reality, never up.
COMPONENTS: List[Dict[str, Any]] = [
    {"primitive": "vacuum tube", "name": "Verifiers", "plane": "Conductor", "layer": "Precision cartridge",
     "status": "Verified", "modules": ["derivation", "receipts", "validate"],
     "note": "a claim in, an amplified verdict out — the active logic"},
    {"primitive": "transistor", "name": "Discern / Router", "plane": "Main", "layer": "Precision cartridge",
     "status": "Verified", "modules": ["discern", "router", "ask"],
     "note": "a small control signal switches the path (propose, never decide)"},
    {"primitive": "transistor", "name": "Gates / Kernel gate", "plane": "Steward", "layer": "Precision cartridge",
     "status": "Verified", "modules": ["gates", "kernel"],
     "note": "admit or reject — the switch that governs the flow"},
    {"primitive": "diode", "name": "Airlock / Diode", "plane": "Reflex", "layer": "Permanent structure",
     "status": "Verified", "modules": ["airlock"],
     "note": "one-way flow — proof can't exit, a miss can't pass as a hit"},
    {"primitive": "capacitor", "name": "The Keeping", "plane": "Plant", "layer": "Wear element",
     "status": "Experimental", "modules": ["corpus", "corpus_db"],
     "note": "stores charge, smooths, releases on demand — the reservoir (55.8% substance / 44.2% stub, "
             "measured 2026-10-06; stubs concentrated in science/OEIS, world, dictionary)"},
    {"primitive": "capacitor", "name": "Wants / Candidates", "plane": "Plant", "layer": "Consumable",
     "status": "Verified", "modules": ["wants", "candidates"],
     "note": "holds a miss until it is filled; a held commitment"},
    {"primitive": "antenna", "name": "The Doors", "plane": "Main", "layer": "Precision cartridge",
     "status": "Verified", "modules": ["doors"],
     "note": "receive + transmit across the gap — the five doors + MCP"},
    {"primitive": "antenna", "name": "The Mesh", "plane": "Scribe", "layer": "Precision cartridge",
     "status": "Verified", "modules": ["mesh"],
     "note": "the LoRa radio, literal — the fellowship across the gap"},
    {"primitive": "resistor", "name": "Rate limiter / Damp", "plane": "Reflex", "layer": "Precision cartridge",
     "status": "Verified", "modules": ["ratelimit", "alignment"],
     "note": "limits / damps the flow (the read bucket, the ×0.6 down-weight)"},
    {"primitive": "transformer", "name": "Bridges / Tongue", "plane": "Conductor", "layer": "Precision cartridge",
     "status": "Experimental", "modules": ["graph"],
     "note": "couples two circuits — cross-domain bridges, the reader's tongue"},
    {"primitive": "relay", "name": "Node sync / Mesh relay", "plane": "Scribe", "layer": "Precision cartridge",
     "status": "Verified", "modules": ["replicate", "mesh"],
     "note": "a signed bundle trips a far node"},
    {"primitive": "clock", "name": "The Tick / Escapement", "plane": "Conductor", "layer": "Permanent structure",
     "status": "Verified", "modules": ["receipts"],
     "note": "the beat that paces each checked step — one step, one seal"},
    {"primitive": "fuse", "name": "Crisis backstop", "plane": "Reflex", "layer": "Permanent structure",
     "status": "Verified", "modules": ["ask"],
     "note": "fails safe on overload — a cry for help goes to real people first"},
    {"primitive": "bus", "name": "Fascia / Backplane", "plane": "Conductor", "layer": "Permanent structure",
     "status": "Verified", "modules": ["graph", "systems"],
     "note": "wires every part to every part — the concordance graph + the import graph"},
]

# ── The regulators (docs/COMPONENTS.md §5): the Steward + Reflex parts that GOVERN ───────────────
# Firing order is the authority chain. Each closes against a number, an owner, and a fallback.
_FIRE_ORDER = ["crisis", "ingest", "verify", "deploy", "continuous"]
REGULATORS: List[Dict[str, Any]] = [
    {"slug": "crisis", "name": "Crisis backstop", "plane": "Reflex", "fires_at": "crisis",
     "governs": "a cry for help outranks everything → real people",
     "modules": ["ask"], "fallback": "the semantic backstop catches the near-miss"},
    {"slug": "pd", "name": "PD / License gate", "plane": "Steward", "fires_at": "ingest",
     "governs": "only public-domain text is voiced / served",
     "modules": ["witness"], "fallback": "hold to reference, never voice"},
    {"slug": "alignment", "name": "Alignment gate", "plane": "Steward", "fires_at": "ingest",
     "governs": "the tier a source enters at (aligned / reference ×0.6 / sectioned)",
     "modules": ["alignment"], "fallback": "down-weight, then explicit-only"},
    {"slug": "diode", "name": "Diode / airlock", "plane": "Reflex", "fires_at": "ingest",
     "governs": "one-way flow — proof can't exit, a miss can't pass as a hit",
     "modules": ["airlock"], "fallback": "refuse, quarantine"},
    {"slug": "gauges", "name": "Gauges", "plane": "Reflex", "fires_at": "verify",
     "governs": "the tolerance on every verdict — the width of the door",
     "modules": [], "fallback": "tighten to a scaled tolerance"},
    {"slug": "kernel", "name": "Kernel", "plane": "Steward", "fires_at": "verify",
     "governs": "a proposed state-change vs the five moves + covenant",
     "modules": ["kernel"], "fallback": "refuse; born-quarantined"},
    {"slug": "balance", "name": "Balance (governance)", "plane": "Steward", "fires_at": "continuous",
     "governs": "the true rate — a discordance indicts the method, not the constant",
     "modules": [], "fallback": "suspect the method before the world"},
    {"slug": "gate", "name": "Gate (deploy)", "plane": "Steward", "fires_at": "deploy",
     "governs": "what change is admitted to the live engine",
     "modules": [], "fallback": "revert to the pre-deploy snapshot"},
]


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def _resolvable(modules: List[str]) -> Dict[str, Any]:
    """Which of a part's modules import-resolve. A module that cannot resolve is the engine's 'tube not
    seated' signal — reported, never hidden. Cheap: import resolution, no execution, no corpus."""
    missing = []
    for m in modules:
        try:
            if importlib.util.find_spec("concordance." + m) is None:
                missing.append(m)
        except Exception:  # noqa: BLE001 — a resolution error IS an out signal, never a crash
            missing.append(m)
    return {"wired": not missing, "missing": missing}


def _benchmarks() -> Optional[Dict[str, Any]]:
    """The standing self-measurement the gate writes (data/benchmarks.json). Cheap file read, guarded."""
    import json
    p = _data_dir() / "benchmarks.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _reading(slug: str) -> Dict[str, Any]:
    """A regulator's LIVE reading — real where cheap, honest `pending` where a meter needs plumbing.
    Never raises: a reporting number must never sink the panel."""
    try:
        if slug in ("gate", "balance"):
            b = _benchmarks()
            if not b:
                return {"pending": True, "detail": "benchmarks never run on this node (tools/benchmarks.py)"}
            dom = b.get("domains") or {}
            if slug == "gate":
                return {"domains_ok": dom.get("ok"), "domains_total": dom.get("total"),
                        "false_positives": dom.get("false_positives"),
                        "age_hours": b.get("age_hours"), "stale": b.get("stale")}
            return {"regressions": len(b.get("regressions") or []),
                    "false_positives": dom.get("false_positives"),
                    "note": "a discordance indicts the method; regressions and false-positives are the rate"}
        if slug == "kernel":
            from . import kernel
            d = kernel.doctrine()
            return {"wired": True, "five_moves": len(d.get("five_moves") or []),
                    "covenant_rules": len(d.get("agent_covenant") or [])}
        if slug == "alignment":
            from . import alignment
            return {"enabled": bool(alignment.enabled()),
                    "tiers": ["aligned", "reference ×0.6", "sectioned (explicit-only)"]}
        if slug == "crisis":
            from . import ask
            res = getattr(ask, "_CRISIS_RESOURCES", ())
            return {"wired": hasattr(ask, "is_crisis"), "resources": len(res)}
        if slug == "diode":
            return {"wired": _resolvable(["airlock"])["wired"], "rule": "one-way; the reverse is refused by shape"}
        if slug == "pd":
            return {"rule": "public-domain only; fail-closed",
                    "pending": True, "detail": "withheld-by-license count is on the Bridge via /keep.json composition"}
        if slug == "gauges":
            return {"pending": True, "detail": "survey via tools/gauge_panel.py --json (AST over the source; not loaded per-request)"}
    except Exception as e:  # noqa: BLE001
        return {"pending": True, "detail": f"reading unavailable: {type(e).__name__}"}
    return {"pending": True}


def _status_live(declared: str, wired: bool) -> str:
    """The reported status: the declared evidence class, downgraded to reality if the part is not wired.
    Never upgraded — a part cannot claim a status its code does not support."""
    if not wired:
        return "Concept"          # it cannot even import here; it is an idea on this node, nothing more
    return declared if declared in STATUS_LADDER else "Concept"


def report() -> Dict[str, Any]:
    """The whole machine, computed now. Cheap: import resolution + one small JSON read, no corpus."""
    comps: List[Dict[str, Any]] = []
    for c in COMPONENTS:
        r = _resolvable(c.get("modules") or [])
        comps.append({**c, "wired": r["wired"], "missing": r["missing"],
                      "status_live": _status_live(c.get("status", "Concept"), r["wired"])})
    regs: List[Dict[str, Any]] = []
    for g in REGULATORS:
        r = _resolvable(g.get("modules") or [])
        regs.append({**g, "wired": r["wired"], "missing": r["missing"], "reading": _reading(g["slug"])})
    regs.sort(key=lambda x: _FIRE_ORDER.index(x["fires_at"]) if x["fires_at"] in _FIRE_ORDER else 99)
    # count parts by primitive and by plane — the panel's at-a-glance tallies
    by_primitive: Dict[str, int] = {}
    by_plane: Dict[str, int] = {}
    for c in comps:
        by_primitive[c["primitive"]] = by_primitive.get(c["primitive"], 0) + 1
        by_plane[c["plane"]] = by_plane.get(c["plane"], 0) + 1
    return {
        "chain": PLANES, "plane_order": _PLANE_ORDER,
        "layers": LAYERS, "status_ladder": STATUS_LADDER,
        "components": comps, "regulators": regs, "fire_order": _FIRE_ORDER,
        "counts": {"components": len(comps), "wired": sum(1 for c in comps if c["wired"]),
                   "regulators": len(regs), "by_primitive": by_primitive, "by_plane": by_plane},
        "note": ("The engine as a vacuum-tube computer: every part classified by primitive, placed on the "
                 "one authority chain, given a layer and an earned evidence status. Regulators carry a live "
                 "reading where it is cheap and real, `pending` where a meter needs plumbing — never faked. "
                 "Computed live; see docs/COMPONENTS.md for the definition."),
    }


__all__ = ["report", "PLANES", "LAYERS", "STATUS_LADDER", "COMPONENTS", "REGULATORS"]
