"""One canonical form + a ledger bound to the sealed record.

A content-addressed integrity system must have EXACTLY ONE canonical JSON form, or a
non-ASCII seal (Greek/Hebrew — the witness surface) can hash differently in different
places and silently fail to verify. This proves cas / record / validate all agree on
non-ASCII, that such a seal round-trips readable, and that the ledger chain now commits
to the sealed record's content_hash (so tampering the CAS record is detectable via the
chain). Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _isolate():
    d = tempfile.mkdtemp(prefix="nh-canon-")
    os.environ["CONCORDANCE_DATA_DIR"] = d
    return d


from concordance import cas, ledger, validate  # noqa: E402
from concordance.packet import GateResult  # noqa: E402
from concordance.record import Anchor, WitnessRecord  # noqa: E402

GREEK_HEBREW = "ἀγάπη / חֶסֶד"  # agape / chesed — the witness surface in the raw


def _record():
    return WitnessRecord(
        overall="PASS",
        gate_results=(GateResult(gate="RED", status="PASS", reasons=["ok"], details=None),),
        verifier_results=(),
        anchors=(Anchor(ref="John 1:1", layer="scripture", text=GREEK_HEBREW),),
    )


def test_all_canonical_forms_agree_on_non_ascii():
    d = _record().to_dict()
    # the record's own content_hash == cas.content_hash_of == validate.content_hash
    assert d["content_hash"] == cas.content_hash_of(d)
    assert d["content_hash"] == validate.content_hash(d, exclude=("content_hash", "permanent_ref"))


def test_non_ascii_seal_roundtrips_readable_and_reverifies():
    _isolate()
    h = cas.store(_record().to_dict())
    ok, msg = cas.verify(h)
    assert ok, msg
    # stored readable (not \uXXXX-escaped), and re-hash matches the address
    raw = (Path(os.environ["CONCORDANCE_DATA_DIR"]) / "cas" / h[:2] / f"{h[2:]}.json").read_text("utf-8")
    assert "ἀγάπη" in raw
    assert cas.content_hash_of(cas.fetch(h)) == h


def test_ledger_binds_record_hash():
    _isolate()
    res = ledger.seal_record(_record(), summary="agape/chesed binding test")
    h = res["content_hash"]
    assert res["precedent"]["record_hash"] == h  # the chain commits to the CAS record
    rep = ledger.verify_chain()
    assert rep["ok"] and not rep["missing_records"]


def test_chain_detects_missing_bound_record():
    d = _isolate()
    ledger.seal_record(_record(), summary="tamper test")
    assert ledger.verify_chain()["ok"]
    # remove the sealed CAS record -> the chain still references it -> integrity break
    for p in (Path(d) / "cas").rglob("*.json"):
        os.remove(p)
    rep = ledger.verify_chain()
    assert rep["ok"] is False and rep["missing_records"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} canonical/binding tests passed — one form, chain bound to the record.")
