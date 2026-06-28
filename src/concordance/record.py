"""Canonical sealed-result schema — the WitnessRecord.

One object, two surfaces: agents serialize it to JSON; humans see it unfolded as
a walkthrough. Nothing here *executes* verification — the engine produces a
WitnessRecord, the CAS seals it, and the surfaces render it.

Design constraints (load-bearing):
  * Frozen dataclasses — a sealed record is immutable.
  * Every field JSON-round-trippable via to_dict / from_dict.
  * No `final_answer` / `answer` field anywhere. The engine categorizes; it does
    not answer. The doctrine is expressed in the *absence* of such a field.
  * Anchors carry their `layer` (provenance tier), so provenance is on every
    cited rule, not bolted on.

REFACTOR FROM 1.0 (the surface seam): `Anchor.layer` is a plain `str`, NOT a
hardcoded enum. The set of VALID layers is supplied by the active surface
(EngineConfig.source_layers — secular tiers on `.com`, the witness layers on
`.org`) and enforced at verification time. This makes records from both surfaces
structurally identical — only the layer *values* differ. See layers.py.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, FrozenSet, Optional, Tuple

from .layers import SECULAR_LAYERS, WITNESS_LAYERS  # noqa: F401  (re-exported for convenience)
from .packet import DecisionStatus, EngineResult, GateResult
from .verifiers.base import VerifierResult


@dataclass(frozen=True)
class Anchor:
    """A citation with its provenance layer.

    `ref`   — the citation string ("Compendium 2011, code 02060"; "Mat 5:37").
    `layer` — the provenance tier (a str); validated against the active surface's
              source_layers at verification time, never hardcoded here.
    `text`  — optional; present for human display, absent for agents.
    """
    ref: str
    layer: str
    text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Anchor":
        return cls(ref=d["ref"], layer=d["layer"], text=d.get("text"))


@dataclass(frozen=True)
class AxisCoordinates:
    """The packet's position in the scaffold (the grid). `dimensions` is the set
    of scaffold-member names the axis sits on; `umbrella` is the parent axis if
    this is a subsystem (genetics -> biology)."""
    axis: str
    dimensions: FrozenSet[str]
    umbrella: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"axis": self.axis, "dimensions": sorted(self.dimensions)}
        if self.umbrella is not None:
            out["umbrella"] = self.umbrella
        return out

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AxisCoordinates":
        return cls(axis=d["axis"], dimensions=frozenset(d.get("dimensions", [])),
                   umbrella=d.get("umbrella"))


@dataclass(frozen=True)
class ClosestCase:
    """The closest already-solved precedent the engine matched — a contact point
    with the existing keeping. May legitimately be None for novel claims."""
    precedent_id: Optional[str]
    shared_dimensions: FrozenSet[str] = field(default_factory=frozenset)
    shared_anchors: Tuple[str, ...] = ()
    distance: Optional[float] = None
    reasoning_overlay: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"precedent_id": self.precedent_id}
        if self.shared_dimensions:
            out["shared_dimensions"] = sorted(self.shared_dimensions)
        if self.shared_anchors:
            out["shared_anchors"] = list(self.shared_anchors)
        if self.distance is not None:
            out["distance"] = self.distance
        if self.reasoning_overlay is not None:
            out["reasoning_overlay"] = self.reasoning_overlay
        return out

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ClosestCase":
        return cls(
            precedent_id=d.get("precedent_id"),
            shared_dimensions=frozenset(d.get("shared_dimensions", [])),
            shared_anchors=tuple(d.get("shared_anchors", [])),
            distance=d.get("distance"),
            reasoning_overlay=d.get("reasoning_overlay"),
        )


@dataclass(frozen=True)
class WitnessRecord:
    """The canonical sealed record. One object, two surfaces.

    There is deliberately no `final_answer` field — the engine categorizes; it
    does not answer. `content_hash` is computed in to_dict() as the SHA-256 of
    the canonical JSON of everything except itself and `permanent_ref`.
    """
    overall: DecisionStatus
    gate_results: Tuple[GateResult, ...]
    verifier_results: Tuple[VerifierResult, ...]
    anchors: Tuple[Anchor, ...] = ()
    axis_coords: Optional[AxisCoordinates] = None
    closest_case: Optional[ClosestCase] = None
    packet_id: Optional[str] = None
    subject_pubkey: Optional[str] = None
    witness_attestations: Tuple[Dict[str, Any], ...] = ()
    permanent_ref: Optional[str] = None
    schema_version: str = "2.0"

    @property
    def passed(self) -> bool:
        return self.overall == "PASS"

    @property
    def hard_gate_failures(self) -> Tuple[GateResult, ...]:
        return tuple(gr for gr in self.gate_results
                     if gr.gate in ("RED", "FLOOR") and gr.status == "REJECT")

    def confirmed_verifiers(self) -> Tuple[VerifierResult, ...]:
        return tuple(v for v in self.verifier_results if v.status == "CONFIRMED")

    def failed_verifiers(self) -> Tuple[VerifierResult, ...]:
        return tuple(v for v in self.verifier_results if v.status in ("MISMATCH", "ERROR"))

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "overall": self.overall,
            "gate_results": [
                {"gate": gr.gate, "status": gr.status, "reasons": list(gr.reasons),
                 "details": gr.details}
                for gr in self.gate_results
            ],
            "verifier_results": [
                {"name": v.name, "status": v.status, "detail": v.detail, "data": v.data}
                for v in self.verifier_results
            ],
            "anchors": [a.to_dict() for a in self.anchors],
        }
        if self.axis_coords is not None:
            out["axis_coords"] = self.axis_coords.to_dict()
        if self.closest_case is not None:
            out["closest_case"] = self.closest_case.to_dict()
        if self.packet_id is not None:
            out["packet_id"] = self.packet_id
        if self.subject_pubkey is not None:
            out["subject_pubkey"] = self.subject_pubkey
        if self.witness_attestations:
            out["witness_attestations"] = list(self.witness_attestations)
        from .validate import canonical_json_bytes  # the ONE canonical form (ensure_ascii=False)
        out["content_hash"] = hashlib.sha256(canonical_json_bytes(out)).hexdigest()
        if self.permanent_ref is not None:
            out["permanent_ref"] = self.permanent_ref
        return out

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WitnessRecord":
        gates = tuple(
            GateResult(gate=g["gate"], status=g["status"],
                       reasons=list(g.get("reasons", [])), details=g.get("details"))
            for g in d.get("gate_results", [])
        )
        verifiers = tuple(
            VerifierResult(name=v["name"], status=v["status"],
                           detail=v.get("detail", ""), data=v.get("data"))
            for v in d.get("verifier_results", [])
        )
        anchors = tuple(Anchor.from_dict(a) for a in d.get("anchors", []))
        axis_coords = AxisCoordinates.from_dict(d["axis_coords"]) if "axis_coords" in d else None
        closest_case = ClosestCase.from_dict(d["closest_case"]) if "closest_case" in d else None
        return cls(
            overall=d["overall"], gate_results=gates, verifier_results=verifiers,
            anchors=anchors, axis_coords=axis_coords, closest_case=closest_case,
            packet_id=d.get("packet_id"), subject_pubkey=d.get("subject_pubkey"),
            witness_attestations=tuple(d.get("witness_attestations") or []),
            permanent_ref=d.get("permanent_ref"),
            schema_version=d.get("schema_version", "2.0"),
        )


# ── Builders (return new frozen records) ─────────────────────────────────

def build_record(*, engine_result: EngineResult,
                 verifier_results: Tuple[VerifierResult, ...] = (),
                 anchors: Tuple[Anchor, ...] = (),
                 axis_coords: Optional[AxisCoordinates] = None,
                 closest_case: Optional[ClosestCase] = None,
                 packet_id: Optional[str] = None) -> WitnessRecord:
    """Assemble a WitnessRecord from engine output + rendering-layer concerns."""
    return WitnessRecord(
        overall=engine_result.overall,
        gate_results=tuple(engine_result.gate_results),
        verifier_results=tuple(verifier_results),
        anchors=tuple(anchors),
        axis_coords=axis_coords,
        closest_case=closest_case,
        packet_id=packet_id,
    )


def _replace(record: WitnessRecord, **changes: Any) -> WitnessRecord:
    base = dict(
        overall=record.overall, gate_results=record.gate_results,
        verifier_results=record.verifier_results, anchors=record.anchors,
        axis_coords=record.axis_coords, closest_case=record.closest_case,
        packet_id=record.packet_id, subject_pubkey=record.subject_pubkey,
        witness_attestations=record.witness_attestations,
        permanent_ref=record.permanent_ref, schema_version=record.schema_version,
    )
    base.update(changes)
    return WitnessRecord(**base)


def bind_subject(record: WitnessRecord, subject_pubkey: str) -> WitnessRecord:
    """Bind the record to an identity (Ed25519 public key)."""
    return _replace(record, subject_pubkey=subject_pubkey)


def embed_attestations(record: WitnessRecord,
                       attestations: Tuple[Dict[str, Any], ...]) -> WitnessRecord:
    """Embed witness attestations so the record is self-contained for transport."""
    return _replace(record, witness_attestations=tuple(attestations))


def with_permanent_ref(record: WitnessRecord, ref: str) -> WitnessRecord:
    """Record the content_hash after CAS storage, confirming it is addressable."""
    return _replace(record, permanent_ref=ref)


def axis_coords_for(domain: str) -> Optional[AxisCoordinates]:
    """Look up grid coordinates for a domain. Returns None when the grid is not
    present (it ports later) or the domain is unregistered — grid-safe."""
    try:
        from . import grid  # noqa: PLC0415 — lazy by design (grid ports later)
    except ImportError:
        return None
    if domain not in getattr(grid, "AXIS_DIMENSIONS", {}):
        return None
    umbrella: Optional[str] = None
    for parent, children in getattr(grid, "UMBRELLAS", {}).items():
        if domain in children:
            umbrella = parent
            break
    return AxisCoordinates(axis=domain, dimensions=grid.AXIS_DIMENSIONS[domain], umbrella=umbrella)
