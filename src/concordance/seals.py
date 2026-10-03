"""THE SEAL LEDGER, AS A PUBLIC NUMBER — how many seals the engine has minted, that every one is still
re-verified, and when (moat lever 1 of docs/PROJECT_REVIEW_2026-10-03.md; Matt, 2026-10-03: "go in order").

The seals are the engine's whole promise: a verdict alone is "trust me"; a seal is permanent and anyone can
re-check it. The hourly integrity check (tools/integrity_check.py) walks the ledger chain and re-verifies every
sealed CAS record, writing <data>/integrity_status.json. This module reads that status and the chain itself
and hands back the numbers — computed now, never hardcoded (feedback: public numbers are live-wired). Nothing
here re-verifies anything; it reports the last verification and counts the chain.

    GET /seals  ->  {"seals": {minted, verified, ok, re_verified_at, oldest, newest, cas_records, cas_bad,
                               receipt_cards, cite_url}, "note": ...}
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _data_dir() -> Path:
    return Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data")


def _iso(ts: Any) -> Optional[str]:
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, OSError):
        return None


def _count_lines(p: Path) -> int:
    try:
        with open(p, "rb") as f:
            return sum(1 for ln in f if ln.strip())
    except OSError:
        return 0


def summary(data_dir: Optional[Path] = None, cite_base: str = "https://narrowhighway.org") -> Dict[str, Any]:
    """The ledger's public numbers. Cheap: reads the status file, counts the chain, opens its first and
    last entries for their dates. Honest when nothing is there yet: zeros and nulls, never invented."""
    from . import ledger as _ledger
    d = data_dir or _data_dir()
    status: Dict[str, Any] = {}
    sp = d / "integrity_status.json"
    if sp.exists():
        try:
            status = json.loads(sp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            status = {}
    chain = _ledger._ledger_chain_files(d / "ledger")
    oldest = newest = None
    if chain:
        first, last = _ledger._read_precedent_file(chain[0]) or {}, _ledger._read_precedent_file(chain[-1]) or {}
        oldest, newest = _iso(first.get("sealed_at")), _iso(last.get("sealed_at"))
    led = status.get("ledger") if isinstance(status.get("ledger"), dict) else {}
    cas = status.get("cas") if isinstance(status.get("cas"), dict) else {}
    out = {
        "minted": len(chain),
        "verified": int(led.get("verified") or 0),
        "verified_of": int(led.get("total") or 0),
        "ok": status.get("ok") if "ok" in status else None,
        "re_verified_at": _iso(status.get("checked_at")),
        "tampered": len(led.get("tampered") or []),
        "broken_links": len(led.get("broken_links") or []),
        "cas_records": int(cas.get("total") or 0),
        "cas_bad": len(cas.get("bad") or []),
        "receipt_cards": _count_lines(d / "receipt_cards.jsonl"),
        "oldest": oldest,
        "newest": newest,
        "cite_url": cite_base.rstrip("/") + "/s/<content_hash>",
    }
    return {
        "seals": out,
        "note": ("Every seal is permanent and re-checkable by its content hash (GET the cite_url). The chain is "
                 "re-verified every hour by tools/integrity_check.py — recompute every content hash, confirm every "
                 "prev_hash link, re-verify every bound CAS record; this reports that last check and counts the chain "
                 "now. Numbers are computed at request time, never hardcoded."),
    }
