"""concordance — one engine, built on the Bible, reaching the world two ways.

The foundation is documented in FOUNDATION.md and is load-bearing on every surface;
Christ is at the center. No identity is hardcoded at import — it is injected per
surface via EngineConfig (see config.py). The floor and the watch discipline are in
docs/V2_DEFINITION.md.

The movement (engine, gates, cas, ledger, verifiers) ports here next; see PORT_PLAN.md.
"""
from __future__ import annotations

from .config import SURFACES, EngineConfig

__all__ = ["EngineConfig", "SURFACES"]
__version__ = "2.0.0a0"
