"""FLOOR attestation gate — "reference not advice" is enforced, not just documented.

The FLOOR domain-validator registry was empty, so the protective attestation layer was inert.
Now health/financial domains REJECT at FLOOR unless the packet attests the protective framing.
A normal domain (mathematics) is unaffected — no validator, no attestation required.
Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import EngineConfig, validate_packet  # noqa: E402
from concordance.domains import load_domain_validator  # noqa: E402

_T = 1_700_000_000


def _floor_rejected(packet):
    er = validate_packet(packet, now_epoch=_T, config=EngineConfig())
    return any(g.gate == "FLOOR" and g.status == "REJECT" for g in er.gate_results)


def test_medicine_without_attestation_is_floor_rejected():
    assert _floor_rejected({"domain": "medicine", "created_epoch": _T}) is True


def test_medicine_with_attestation_clears_floor():
    pkt = {"domain": "medicine", "created_epoch": _T, "attestations": ["not_medical_advice"],
           "MED_VERIFY": {"weight_kg": 70, "height_m": 1.75, "claimed_bmi": 22.86}}
    assert _floor_rejected(pkt) is False  # FLOOR clears (may quarantine later at WAIT, not FLOOR)


def test_giving_requires_financial_attestation():
    assert _floor_rejected({"domain": "giving", "created_epoch": _T}) is True
    assert _floor_rejected({"domain": "giving", "created_epoch": _T,
                            "attestations": ["not_financial_advice"]}) is False


def test_herb_and_nutrition_are_gated():
    assert _floor_rejected({"domain": "herb", "created_epoch": _T}) is True
    assert _floor_rejected({"domain": "nutrition", "created_epoch": _T}) is True
    # the medical alias resolves to the same validator
    assert _floor_rejected({"domain": "medical", "created_epoch": _T}) is True


def test_wrong_attestation_does_not_satisfy():
    # a financial attestation does not satisfy a medical domain
    assert _floor_rejected({"domain": "medicine", "created_epoch": _T,
                            "attestations": ["not_financial_advice"]}) is True


def test_normal_domain_has_no_attestation_gate():
    assert load_domain_validator("mathematics") is None
    assert _floor_rejected({"domain": "combinatorics", "created_epoch": _T,
                            "COMB_VERIFY": {"comb_n": 5, "comb_k": 2, "claimed_combinations": 10}}) is False


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} attestation tests passed — 'reference not advice' is gate-enforced.")
