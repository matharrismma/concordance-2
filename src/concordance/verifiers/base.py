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
from typing import Any, Dict, Literal, Optional

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
