"""The keep — the operator's window into the live engine.

This is how the operator SEES what the engine is doing: health, the keeping's size, the
seal/ledger counts, and a live feed of recent activity (verifications, searches, seals).

Operator-gated, like 1.0's keep: it serves only to the operator and returns 404 to
everyone else (hide-existence — the keep is not a public surface). Operator =
  - localhost on the box (the box itself is always trusted), OR
  - a request carrying the right token (env CONCORDANCE_KEEP_TOKEN), passed as
    ?token=… or the X-Keep-Token header.
No token set + non-localhost  →  the keep is closed (404 to all). Sovereign: stdlib only.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .. import __version__, cas, corpus, ledger, telemetry
from ..config import EngineConfig

_LOCAL = {"127.0.0.1", "::1", "localhost", "", None}


def is_operator(token: Optional[str], client_ip: Optional[str]) -> bool:
    """True if this request may see the keep. Localhost always; otherwise a matching token."""
    if client_ip in _LOCAL:
        return True
    want = os.environ.get("CONCORDANCE_KEEP_TOKEN", "").strip()
    return bool(want) and (token or "").strip() == want


def dashboard(config: EngineConfig) -> Dict[str, Any]:
    """The live state — what the operator needs to see at a glance. All best-effort."""
    try:
        cards = len(corpus.default_corpus().cards)
    except Exception:
        cards = None
    try:
        seal_stats = cas.stats()
    except Exception:
        seal_stats = {}
    try:
        chain = ledger.verify_chain()
    except Exception:
        chain = {"ok": None}
    try:
        precedents = len(ledger.list_precedents())
    except Exception:
        precedents = None

    return {
        "ok": True,
        "version": __version__,
        "surface": config.surface,
        "identity": config.identity,
        "keeping": {"cards": cards, "precedents": precedents},
        "seals": {
            "count": seal_stats.get("count"),
            "total_bytes": seal_stats.get("total_bytes"),
        },
        "ledger": {
            "ok": chain.get("ok"),
            "total": chain.get("total"),
            "verified": chain.get("verified"),
        },
        "activity": {
            "stats": telemetry.stats(),
            "recent": list(reversed(telemetry.recent(50))),  # newest first for the feed
        },
    }
