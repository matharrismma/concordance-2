"""Verifiers — the deterministic complications mounted on the going train.

Each domain verifier is a pure function `spec -> VerifierResult`. They are
registered LAZILY (never eager-imported at package load — that was a 1.0
coupling hotspot). The witness-surface verifiers (scripture, theology, witness)
are surfaced only when EngineConfig.surface == "witness".

For now this package exposes the verifier base; the domain verifiers and the
registry port here next (see PORT_PLAN.md).
"""
from __future__ import annotations

from .base import VerifierResult, VerifierStatus, confirm, error, mismatch, na

__all__ = ["VerifierResult", "VerifierStatus", "confirm", "error", "mismatch", "na"]
