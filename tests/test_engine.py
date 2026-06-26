"""Engine pipeline test — the going train turns end to end.

Feeds a packet through validate_and_seal: a true claim PASSes (verifier confirms,
gates clear), a false claim REJECTs at RED (verifier mismatch), a true claim with no
wait elapsed QUARANTINEs at WAIT. Proves claim -> gates -> verifier -> (verdict,
trail, seal). Runnable with `pytest` OR `python tests/test_engine.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import EngineConfig, validate_and_seal, validate_packet  # noqa: E402

_T0 = 1_700_000_000          # a fixed base epoch (no wall-clock in tests)
_PAST = _T0 + 3600 + 1       # past the default "local" wait window (3600s)


def _packet(claimed: int, created_epoch: int = _T0):
    return {
        "domain": "combinatorics",
        "COMB_VERIFY": {"comb_n": 5, "comb_k": 2, "claimed_combinations": claimed},
        "created_epoch": created_epoch,
        "required_witnesses": 0,
    }


def test_true_claim_passes():
    rec = validate_and_seal(_packet(10), now_epoch=_PAST, config=EngineConfig())
    assert rec.overall == "PASS", [(g.gate, g.status) for g in rec.gate_results]
    # the verifier result rode along in the sealed record
    names = [v.name for v in rec.verifier_results]
    assert "combinatorics.combinations" in names
    assert rec.confirmed_verifiers(), "expected a confirmed verifier"


def test_false_claim_rejects_at_red():
    rec = validate_and_seal(_packet(99), now_epoch=_PAST, config=EngineConfig())
    assert rec.overall == "REJECT"
    assert rec.hard_gate_failures and rec.hard_gate_failures[0].gate == "RED"
    assert rec.failed_verifiers(), "expected a mismatched verifier"


def test_true_claim_without_wait_quarantines():
    # created now, no wait elapsed -> WAIT gate quarantines (true claim, not sealed yet)
    rec = validate_and_seal(_packet(10, created_epoch=_PAST), now_epoch=_PAST, config=EngineConfig())
    assert rec.overall == "QUARANTINE"
    assert any(g.gate == "WAIT" and g.status == "QUARANTINE" for g in rec.gate_results)


def test_sealed_record_has_hash_and_no_answer():
    d = validate_and_seal(_packet(10), now_epoch=_PAST, config=EngineConfig()).to_dict()
    assert len(d["content_hash"]) == 64
    assert "final_answer" not in d and "answer" not in d


def test_gate_names_are_secular():
    rec = validate_and_seal(_packet(10), now_epoch=_PAST, config=EngineConfig())
    names = {g.gate for g in rec.gate_results}
    assert names <= {"RED", "FLOOR", "PATH", "WITNESS", "WAIT"}
    assert not (names & {"WAY", "BROTHERS", "GOD"}), "no religious gate names on the secular core"


def test_validate_packet_shape():
    er = validate_packet(_packet(10), now_epoch=_PAST, config=EngineConfig())
    assert er.overall == "PASS" and er.passed_hard_gates


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} engine tests passed — the going train turns, the seal holds.")
