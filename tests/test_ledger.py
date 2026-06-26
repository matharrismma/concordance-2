"""Ledger test — the append-only hash chain holds, and tampering is caught.

Proves: seal_record stores in the CAS and appends to the chain; prev_hash links each
file to the prior; verify_chain confirms integrity; a tampered file is detected; only
PASS records seal. Runnable with `pytest` OR `python tests/test_ledger.py`.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import cas  # noqa: E402
from concordance.gates import ok, reject  # noqa: E402
from concordance.ledger import (  # noqa: E402
    GENESIS_HASH, list_precedents, seal_record, seal_to_ledger, verify_chain,
)
from concordance.packet import EngineResult  # noqa: E402
from concordance.record import build_record  # noqa: E402


def _pass(packet_id: str):
    return build_record(engine_result=EngineResult("PASS", [ok("RED"), ok("FLOOR")]),
                        packet_id=packet_id)


def test_seal_record_wires_cas_and_chain():
    with tempfile.TemporaryDirectory() as tmp:
        ld = Path(tmp) / "ledger"
        cb = Path(tmp) / "cas"
        r1 = seal_record(_pass("p1"), summary="first claim", ledger_dir=ld, cas_base=cb, sealed_at=1000.0)
        r2 = seal_record(_pass("p2"), summary="second claim", ledger_dir=ld, cas_base=cb, sealed_at=2000.0)
        # CAS holds both sealed records, addressable by hash
        assert cas.exists(r1["content_hash"], base_dir=cb)
        assert cas.exists(r2["content_hash"], base_dir=cb)
        # chain links: first -> GENESIS, second -> first's content_hash
        assert r1["precedent"]["prev_hash"] == GENESIS_HASH
        assert r2["precedent"]["prev_hash"] == r1["precedent"]["content_hash"]
        assert len(list_precedents(ld)) == 2


def test_verify_chain_ok():
    with tempfile.TemporaryDirectory() as tmp:
        ld = Path(tmp) / "ledger"
        cb = Path(tmp) / "cas"
        seal_record(_pass("p1"), summary="first", ledger_dir=ld, cas_base=cb, sealed_at=1000.0)
        seal_record(_pass("p2"), summary="second", ledger_dir=ld, cas_base=cb, sealed_at=2000.0)
        rep = verify_chain(ld)
        assert rep["ok"] and rep["total"] == 2 and rep["verified"] == 2, rep


def test_tamper_is_caught():
    with tempfile.TemporaryDirectory() as tmp:
        ld = Path(tmp) / "ledger"
        cb = Path(tmp) / "cas"
        seal_record(_pass("p1"), summary="first", ledger_dir=ld, cas_base=cb, sealed_at=1000.0)
        seal_record(_pass("p2"), summary="second", ledger_dir=ld, cas_base=cb, sealed_at=2000.0)
        # tamper: alter a precedent's content without fixing its content_hash
        target = sorted(ld.glob("*.json"))[0]
        data = json.loads(target.read_text(encoding="utf-8"))
        data["summary"] = "ALTERED"
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")
        rep = verify_chain(ld)
        assert not rep["ok"], "tampering must break the chain"
        assert rep["tampered"] or rep["broken_links"]


def test_only_pass_seals():
    with tempfile.TemporaryDirectory() as tmp:
        ld = Path(tmp) / "ledger"
        rej = build_record(engine_result=EngineResult("REJECT", [reject("RED", "nope")]))
        try:
            seal_to_ledger(rej, summary="should not seal", ledger_dir=ld)
        except ValueError:
            pass
        else:
            raise AssertionError("a non-PASS record must not seal")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} ledger tests passed — the chain holds, tampering is caught.")
