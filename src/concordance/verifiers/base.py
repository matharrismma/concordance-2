"""Verifier framework — the deterministic computational checks.

A verifier is a PURE function: it takes a spec and returns a VerifierResult.
No I/O, no LLM, no network. It either confirms the artifact's math/logic,
finds a mismatch, errors on malformed input, or declares itself not-applicable.

    CONFIRMED      — the artifact ran and agreed with the claim
    MISMATCH       — the artifact ran and contradicted the claim
    NOT_APPLICABLE — the relevant artifact was absent (verifier could not run)
    ERROR          — the artifact was present but malformed

Ported as-is from 1.0 — domain-neutral.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional, Sequence, Tuple, Union

VerifierStatus = Literal["CONFIRMED", "MISMATCH", "NOT_APPLICABLE", "ERROR"]


@dataclass(frozen=True)
class VerifierResult:
    name: str
    status: VerifierStatus
    detail: str = ""
    data: Optional[Dict[str, Any]] = None

    @property
    def passed(self) -> bool:
        return self.status == "CONFIRMED"

    @property
    def failed(self) -> bool:
        return self.status in ("MISMATCH", "ERROR")

    @property
    def applicable(self) -> bool:
        return self.status != "NOT_APPLICABLE"


def na(name: str, reason: str = "no artifact provided") -> VerifierResult:
    return VerifierResult(name=name, status="NOT_APPLICABLE", detail=reason)


def confirm(name: str, detail: str = "", data: Optional[Dict[str, Any]] = None) -> VerifierResult:
    return VerifierResult(name=name, status="CONFIRMED", detail=detail, data=data)


def mismatch(name: str, detail: str, data: Optional[Dict[str, Any]] = None) -> VerifierResult:
    return VerifierResult(name=name, status="MISMATCH", detail=detail, data=data)


def error(name: str, detail: str, data: Optional[Dict[str, Any]] = None) -> VerifierResult:
    return VerifierResult(name=name, status="ERROR", detail=detail, data=data)


def clamp_tol(spec: Dict[str, Any], key: str, default: float) -> float:
    """Caller-supplied tolerance, clamped: a caller may TIGHTEN a tolerance but never LOOSEN
    it past the verifier's default — otherwise an adversarial caller could widen the window to
    force a CONFIRMED on a value that is actually wrong. Missing/malformed -> the default."""
    try:
        v = spec.get(key)
        if v is None:
            return default
        return min(abs(float(v)), abs(default))
    except (TypeError, ValueError):
        return default


# A rule is (requirement, verify_fn). requirement is EITHER a sequence of keys that must ALL
# be present in the artifact, OR a callable(artifact)->bool for irregular conditions (or/
# is-not-None/non-empty). verify_fn is callable(artifact)->VerifierResult.
Requirement = Union[Sequence[str], Callable[[Dict[str, Any]], bool]]
Rule = Tuple[Requirement, Callable[[Dict[str, Any]], "VerifierResult"]]


def dispatch(packet: Dict[str, Any], artifact_key: str, rules: Iterable[Rule], *,
             domain: str, none_reason: str = "") -> List["VerifierResult"]:
    """Declarative run() driver — read ONE artifact, fire each matching rule, and apply
    UNIFORM present-vs-null handling: an absent artifact OR no rule firing yields exactly one
    na(domain, ...). This is behaviour-identical to the hand-written pattern

        art = packet.get(KEY) or {}
        if <keys present>: results.append(fn(art))   # for each rule
        if not results: results.append(na(domain, ...))

    but declarative and consistent, so every verifier reports "nothing applicable" the same
    way and a new check is one line in a rules table. A requirement is a tuple of required
    keys (ALL must be present) or a callable(artifact)->bool for or/is-not-None conditions."""
    art = packet.get(artifact_key) or {}
    out: List["VerifierResult"] = []
    for req, fn in rules:
        fires = req(art) if callable(req) else all(k in art for k in req)
        if fires:
            out.append(fn(art))
    if not out:
        out.append(na(domain, none_reason or f"no {artifact_key} artifacts present"))
    return out
