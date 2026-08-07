"""The keep — the operator's window into the live engine.

This is how the operator SEES what the engine is doing: health, the keeping's size, the
seal/ledger counts, and a live feed of recent activity (verifications, searches, seals).

TRUST BOUNDARY (load-bearing): the ledger + seals (CAS) are the AUTHORITATIVE integrity
record — hash-chained, content-addressed, independently re-verifiable. The activity feed is
ADVISORY — a best-effort, tamperable ops log, NOT part of the integrity chain. The dashboard
labels them so an operator never reads an activity count as sealed truth.

Operator-gated, like 1.0's keep: it serves only to the operator and returns 404 to
everyone else (hide-existence — the keep is not a public surface). Operator =
  - localhost on the box (the box itself is always trusted), OR
  - a request carrying the right token (env CONCORDANCE_KEEP_TOKEN), passed as
    ?token=… or the X-Keep-Token header, OR
  - a request from an allow-listed IP (env CONCORDANCE_KEEP_IPS, comma-separated). Behind our
    own proxy the real client IP is the LAST hop Caddy appends to X-Forwarded-For — trusted
    ONLY because the socket peer is our loopback proxy (an outside attacker can never be that).
No credential set + non-localhost  →  the keep is closed (404 to all). Sovereign: stdlib only.

CAVEAT for the IP tie: a residential IP can rotate (you re-set it), and if your ISP uses CGNAT
your public IP is SHARED with strangers who would then reach the keep — so an IP allowlist is a
convenience, not a substitute for the token/covenant on an untrusted network.
"""
from __future__ import annotations

import hmac
import os
import time
from typing import Any, Dict, List, Optional

from .. import __version__, cas, corpus, ledger, telemetry
from ..config import EngineConfig

_TRUE = {"1", "true", "yes", "on"}
_LOOPBACK = {"127.0.0.1", "::1"}


def _allowed_ips() -> set:
    raw = os.environ.get("CONCORDANCE_KEEP_IPS", "")
    return {ip.strip() for ip in raw.replace(";", ",").split(",") if ip.strip()}


def _client_ip(peer_ip: Optional[str], headers: Any) -> Optional[str]:
    """The real client IP. Behind our proxy the socket peer is loopback, so the true client is the
    LAST hop Caddy appended to X-Forwarded-For (earlier hops are client-spoofable and ignored). We
    trust that hop ONLY when the peer is loopback — a direct outside connection can never be."""
    if peer_ip in _LOOPBACK and headers is not None:
        xff = (headers.get("x-forwarded-for") or "").strip()
        if xff:
            return xff.split(",")[-1].strip()
    return peer_ip


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
    if is_operator(token, peer_ip):
        return True
    # the IP tie — additive, and inert unless CONCORDANCE_KEEP_IPS is set. The client IP is resolved
    # from the trusted proxy hop (never the spoofable first X-Forwarded-For entry).
    ips = _allowed_ips()
    if ips:
        cip = _client_ip(peer_ip, headers)
        if cip and cip in ips:
            return True
    return False


def _read_integrity_status() -> Optional[Dict[str, Any]]:
    """The last scheduled integrity check's result (tools/integrity_check.py writes it).
    Cheap file read — the heavy verify_chain + CAS sweep runs on the timer, not per poll."""
    import json
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    path = os.path.join(base, "integrity_status.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _read_traffic() -> Optional[Dict[str, Any]]:
    """The last traffic rollup (tools/traffic_rollup.py writes it) — where visitors come from and
    go, split human/bot/agent. Advisory ops data (from the access logs), not the integrity chain."""
    import json
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    path = os.path.join(base, "traffic.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


# One full-corpus scan is ~1–2s at 670k cards; the operator dashboard refreshes on a timer, so the
# composition is cached and recomputed at most once a minute. Best-effort throughout.
_KEEP_CACHE: Dict[str, Any] = {"ts": 0.0, "data": None}
_KEEP_TTL = 60.0


def _keeping_stats() -> Dict[str, Any]:
    """Composition + license boundary + nesting health of the keep, in ONE pass (cached ~60s).

    This is where the corpus-growth and PD/CC0 work becomes VISIBLE to the operator: how many
    cards, how many are actually SERVED vs withheld and WHY (share-alike / stage / generated /
    retracted), the makeup by shelf, and whether the nesting still holds (spines, orphans)."""
    now = time.time()
    cached = _KEEP_CACHE.get("data")
    if cached is not None and (now - _KEEP_CACHE.get("ts", 0.0)) < _KEEP_TTL:
        return cached
    cards = corpus.default_corpus().cards
    total = len(cards)
    public = spines = sa = stage = gen = retr = orphans = 0
    by_shelf: Dict[str, List[int]] = {}
    public_ids: set = set()
    for cid, c in cards.items():
        shelf = c.get("shelf") or "(none)"
        row = by_shelf.setdefault(shelf, [0, 0])
        row[0] += 1
        sid = str(cid)
        if shelf == "spine" or sid.startswith("card_spine") or sid.startswith("card_k_spine"):
            spines += 1
        if corpus.is_public(c):
            public += 1
            row[1] += 1
            public_ids.add(cid)
        elif c.get("retracted"):
            retr += 1
        elif (c.get("lifecycle_stage") or "public") not in corpus.PUBLIC_STAGES:
            stage += 1
        elif corpus._is_share_alike(c):
            sa += 1
        elif c.get("generated") is True:
            gen += 1
    # a public card whose member/part SPINE target is not itself public = a dangling edge (orphan)
    for cid in public_ids:
        for e in (cards[cid].get("connections") or []):
            if (e.get("relationship") in ("member_of", "part_of")
                    and (t := e.get("to_card_id")) and t not in public_ids):
                orphans += 1
                break
    shelves = sorted(([s, v[0], v[1]] for s, v in by_shelf.items()), key=lambda r: (-r[1], r[0]))
    data = {
        "cards": total,
        "public": public,
        "withheld": {"total": total - public, "share_alike": sa,
                     "not_public_stage": stage, "generated": gen, "retracted": retr},
        "spines": spines,
        "shelf_count": len(by_shelf),
        "orphans": orphans,
        "shelves": [{"shelf": s, "cards": n, "public": p} for s, n, p in shelves[:24]],
        "computed_at": now,
    }
    _KEEP_CACHE["ts"] = now
    _KEEP_CACHE["data"] = data
    return data


def dashboard(config: EngineConfig) -> Dict[str, Any]:
    """The live state — what the operator needs to see at a glance. All best-effort."""
    try:
        keeping = _keeping_stats()
    except Exception:
        try:
            keeping = {"cards": len(corpus.default_corpus().cards)}
        except Exception:
            keeping = {"cards": None}
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
        # The trust boundary, stated so the operator never mistakes one for the other:
        "trust": {
            "authoritative": "ledger + seals (CAS) — hash-chained, content-addressed, re-verifiable",
            "advisory": "activity — a best-effort ops log; tamperable, NOT part of the integrity chain",
        },
        "keeping": {**keeping, "precedents": precedents},
        "seals": {
            "count": seal_stats.get("count"),
            "total_bytes": seal_stats.get("total_bytes"),
        },
        "ledger": {
            "ok": chain.get("ok"),
            "total": chain.get("total"),
            "verified": chain.get("verified"),
        },
        "integrity": _read_integrity_status(),  # last scheduled check (tools/integrity_check.py)
        "traffic": _read_traffic(),  # where visitors come from / go, human/bot/agent (tools/traffic_rollup.py)
        "activity": {
            "stats": telemetry.stats(),
            "recent": list(reversed(telemetry.recent(50))),  # newest first for the feed
        },
    }
