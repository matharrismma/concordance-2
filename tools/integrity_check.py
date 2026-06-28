#!/usr/bin/env python3
"""Integrity check — verify the live ledger chain + every sealed CAS record.

The seals are the engine's whole promise; this is the watchdog that proves they still stand.
It walks the ledger hash-chain (verify_chain — recompute every content_hash, confirm every
prev_hash link, confirm each chain-bound CAS record exists + re-verifies) AND sweeps every
CAS record (cas.verify). Exits 0 if all sound, 1 on ANY tamper / broken link / missing or
altered record.

It writes the result to <data>/integrity_status.json so the keep can surface "last integrity
check", and — if CONCORDANCE_ALERT_WEBHOOK is set — POSTs a short JSON alert there on failure
(stdlib urllib; NO credentials are handled here; point the env at any channel: ntfy, a Slack/
Discord webhook, an email-to-webhook bridge). Run it on a timer, and before/after any restore.

Sovereign: stdlib + the floor only.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from concordance import cas, ledger  # noqa: E402


def _data_dir() -> str:
    return os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"


def run() -> dict:
    """Verify chain + sweep CAS. Returns the structured result (ok True iff all sound)."""
    chain = ledger.verify_chain()  # default ledger_dir + cas_base from CONCORDANCE_DATA_DIR
    bad = []
    hashes = cas.list_hashes()
    for h in hashes:
        ok, msg = cas.verify(h)
        if not ok:
            bad.append({"hash": h[:16] + "…", "error": msg})
    ok = bool(chain.get("ok", True)) and not bad
    return {
        "ok": ok,
        "checked_at": int(time.time()),
        "ledger": {"ok": chain.get("ok"), "total": chain.get("total"),
                   "verified": chain.get("verified"), "tampered": chain.get("tampered"),
                   "broken_links": chain.get("broken_links"),
                   "missing_records": chain.get("missing_records")},
        "cas": {"total": len(hashes), "bad": bad},
    }


def write_status(result: dict) -> None:
    try:
        p = os.path.join(_data_dir(), "integrity_status.json")
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(result, f)
    except OSError:
        pass  # best-effort; the exit code is the authoritative signal


def alert(result: dict) -> None:
    url = os.environ.get("CONCORDANCE_ALERT_WEBHOOK", "").strip()
    if not url:
        return
    import urllib.request
    text = (f"[Narrow Highway 2.0] INTEGRITY FAILED @ {result['checked_at']}: "
            f"ledger.ok={result['ledger']['ok']}, cas_bad={len(result['cas']['bad'])}")
    body = json.dumps({"text": text, "result": result}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=body, headers={"content-type": "application/json"})
        urllib.request.urlopen(req, timeout=10)  # noqa: S310 — operator-configured URL
    except Exception as e:  # noqa: BLE001 — alerting must never crash the check
        print(f"alert webhook failed: {type(e).__name__}: {e}", file=sys.stderr)


def main() -> int:
    result = run()
    write_status(result)
    if not result["ok"]:
        alert(result)
        print(json.dumps(result, indent=2))
        print("INTEGRITY: FAIL", file=sys.stderr)
        return 1
    lg = result["ledger"]
    print(f"INTEGRITY: OK — ledger {lg['verified']}/{lg['total']} verified, "
          f"{result['cas']['total']} CAS records all re-verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
