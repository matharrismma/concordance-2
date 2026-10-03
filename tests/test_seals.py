"""THE SEAL LEDGER as a public number, and the sealed constitution (moat levers 1 and 3, 2026-10-03). The numbers
are computed from the status file and the chain at request time — zeros and nulls when nothing is there, never
invented; the foundation's sha256 is the file's own hash, recomputed on every request."""
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = tempfile.mkdtemp(prefix="nh-seals-")
os.environ["CONCORDANCE_DATA_DIR"] = TMP

from concordance import seals  # noqa: E402
from concordance.engine import EngineConfig  # noqa: E402
from concordance.web import api  # noqa: E402


def test_an_empty_keeping_reports_zeros_and_nulls_never_invented():
    s = seals.summary(Path(TMP))["seals"]
    assert s["minted"] == 0 and s["verified"] == 0 and s["ok"] is None and s["re_verified_at"] is None
    assert s["oldest"] is None and s["cas_records"] == 0 and s["cite_url"].endswith("/s/<content_hash>")


def test_the_status_and_the_chain_are_read_not_recomputed():
    d = Path(TMP)
    (d / "ledger").mkdir(exist_ok=True)
    t0 = time.time() - 86400
    for i, name in enumerate(("mathematics-aaaa.json", "physics-bbbb.json")):
        (d / "ledger" / name).write_text(json.dumps({"precedent_id": f"ledger://x/{i}", "sealed_at": t0 + i * 3600,
                                                     "content_hash": "c" * 64, "prev_hash": "p" * 64}), encoding="utf-8")
    (d / "integrity_status.json").write_text(json.dumps({"ok": True, "checked_at": time.time() - 120,
                                                          "ledger": {"ok": True, "total": 2, "verified": 2, "tampered": [], "broken_links": []},
                                                          "cas": {"total": 5, "bad": []}}), encoding="utf-8")
    (d / "receipt_cards.jsonl").write_text('{"id": "r1"}\n{"id": "r2"}\n\n', encoding="utf-8")
    s = seals.summary(d, cite_base="https://narrowhighway.org/")["seals"]
    assert s["minted"] == 2 and s["verified"] == 2 and s["verified_of"] == 2 and s["ok"] is True
    assert s["cas_records"] == 5 and s["cas_bad"] == 0 and s["receipt_cards"] == 2
    assert s["oldest"] < s["newest"] and s["re_verified_at"].endswith("+00:00")
    assert s["cite_url"] == "https://narrowhighway.org/s/<content_hash>"


def test_the_route_serves_the_ledger_and_identity_carries_the_foundations_hash():
    st, p = api.dispatch("GET", "/seals", {}, None, EngineConfig())[:2]
    assert st == 200 and "seals" in p and "re-verified every hour" in p["note"]
    st, ident = api.dispatch("GET", "/identity", {}, None, EngineConfig())[:2]
    docs = {d["file"]: d for d in ident["foundation"]["documents"]}
    want = hashlib.sha256((ROOT / "FOUNDATION.md").read_bytes()).hexdigest()
    assert docs["FOUNDATION.md"]["sha256"] == want and docs["FOUNDATION.md"]["bytes"] > 100
    assert "frozen 2026-07-25" in docs["FOUNDATION.md"]["what"] and "docs/WORLD.md" in docs
    assert "tamper-evident" in ident["foundation"]["note"]


def test_the_psalm_of_the_day_is_the_old_calendar_rule():
    import datetime as dt
    assert api.psalm_of_the_day(dt.date(2026, 1, 1))["ref"] == "Psalm 1"
    assert api.psalm_of_the_day(dt.date(2026, 5, 30))["ref"] == "Psalm 150"      # day 150
    assert api.psalm_of_the_day(dt.date(2026, 5, 31))["ref"] == "Psalm 1"        # wraps
    assert api.psalm_of_the_day(dt.date(2026, 10, 3))["ref"] == "Psalm 126"      # day 276 -> 126
    st, p = api.dispatch("GET", "/daily", {}, None, EngineConfig())[:2]
    assert st in (200, 404) and (st == 404 or p["psalm_of_the_day"]["ref"].startswith("Psalm "))
