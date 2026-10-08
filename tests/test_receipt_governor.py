"""The ambient seal governor (review 2026-10-08): an ambient /ask seal keeps the CAS object and the ledger
link — the /s/<hash> receipt is real — but mints NO card, so receipt_cards.jsonl / verified_cards.jsonl grow only
from explicit seals and the cold-path card bookkeeping never runs inside the warm server. The default (the
explicit /verify door) still mints the card, exactly as before."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import cas, receipts  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.derivation import verify_derivation  # noqa: E402

CFG = EngineConfig(skip_schema_validation=True)


def _holds():
    return verify_derivation([{"id": "s", "domain": "mathematics",
                               "spec": {"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "4", "variables": {}}}}])


def _lines(p: Path) -> int:
    return sum(1 for _ in open(p, encoding="utf-8")) if p.exists() else 0


def test_ambient_seal_keeps_the_receipt_but_mints_no_card(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    rc = tmp_path / "receipt_cards.jsonl"
    vc = tmp_path / "verified_cards.jsonl"
    before = (_lines(rc), _lines(vc))
    out = receipts.attach(_holds(), config=CFG, domain="mathematics", enabled=True, index=False, card=False)
    seal = out.get("seal") or {}
    assert seal.get("content_hash") and seal.get("cite_url")             # the receipt is real
    assert cas.fetch(seal["content_hash"]) is not None                   # the object is in the CAS
    assert (_lines(rc), _lines(vc)) == before                            # ...and no card file grew


def test_explicit_seal_still_mints_the_card(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    rc = tmp_path / "receipt_cards.jsonl"
    before = _lines(rc)
    out = receipts.attach(_holds(), config=CFG, domain="mathematics", enabled=True, index=False)
    assert (out.get("seal") or {}).get("content_hash")
    assert _lines(rc) > before                                           # the default path is unchanged
