"""Integrity watchdog — proves it passes a clean store and CATCHES a tampered one.

The seals are the whole promise; this is the check that proves they still stand. It must
pass when the ledger + CAS are sound and fail (non-zero) on any tamper. Runnable with pytest
OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))


def _isolate():
    d = tempfile.mkdtemp(prefix="nh-integ-")
    os.environ["CONCORDANCE_DATA_DIR"] = d
    return d


from concordance import ledger  # noqa: E402
from concordance.gates import ok as gate_ok  # noqa: E402
from concordance.packet import EngineResult  # noqa: E402
from concordance.record import build_record  # noqa: E402


def _seal(pid):
    rec = build_record(engine_result=EngineResult("PASS", [gate_ok("RED"), gate_ok("FLOOR")]),
                       packet_id=pid)
    return ledger.seal_record(rec, summary=f"claim {pid}")


def test_clean_store_passes():
    _isolate()
    _seal("p1")
    _seal("p2")
    import integrity_check
    r = integrity_check.run()
    assert r["ok"] is True
    assert r["ledger"]["ok"] is True
    assert r["cas"]["total"] >= 2 and not r["cas"]["bad"]


def test_tampered_cas_record_is_caught():
    d = _isolate()
    _seal("p1")
    import integrity_check
    assert integrity_check.run()["ok"] is True
    # tamper: overwrite a sealed CAS record with altered content
    for p in (Path(d) / "cas").rglob("*.json"):
        p.write_text('{"tampered": true}', encoding="utf-8")
        break
    r = integrity_check.run()
    assert r["ok"] is False
    assert r["cas"]["bad"]  # the sweep names the bad record


def test_write_status_roundtrips():
    d = _isolate()
    import integrity_check
    r = integrity_check.run()
    integrity_check.write_status(r)
    sp = Path(d) / "integrity_status.json"
    assert sp.exists() and json.loads(sp.read_text())["ok"] == r["ok"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} integrity tests passed — clean store passes, tamper is caught.")
