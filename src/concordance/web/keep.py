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

import hmac
import os
from typing import Any, Dict, Optional

from .. import __version__, cas, corpus, ledger, telemetry
from ..config import EngineConfig

_TRUE = {"1", "true", "yes", "on"}
_LOOPBACK = {"127.0.0.1", "::1"}


def is_operator(token: Optional[str], peer_ip: Optional[str]) -> bool:
    """True if this request may see the keep. FAIL CLOSED.

    SECURITY: access requires a matching CONCORDANCE_KEEP_TOKEN (constant-time compare).
    Loopback is trusted ONLY when CONCORDANCE_KEEP_TRUST_LOCAL is set — which it is NOT in
    production, because behind a proxy every request's socket peer is the proxy (loopback),
    so trusting loopback would expose the keep to the world. The empty/unknown IP is never
    trusted. The caller passes the REAL socket peer, never X-Forwarded-For (spoofable)."""
    want = os.environ.get("CONCORDANCE_KEEP_TOKEN", "").strip()
    if want and token and hmac.compare_digest(str(token).strip(), want):
        return True
    if os.environ.get("CONCORDANCE_KEEP_TRUST_LOCAL", "").strip().lower() in _TRUE \
            and peer_ip in _LOOPBACK:
        return True
    return False


def request_is_operator(peer_ip: Optional[str], headers: Any, query: Optional[dict]) -> bool:
    """Operator decision for a keep request. The token may come from ?token= or the
    X-Keep-Token header. X-Forwarded-For is deliberately NOT consulted — it is client-
    spoofable, so the gate trusts only the real socket peer + the token."""
    token = None
    if query:
        token = query.get("token")
    if not token and headers is not None:
        token = headers.get("x-keep-token")
    return is_operator(token, peer_ip)


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
