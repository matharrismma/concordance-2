"""Verifier proof tests — each ported domain confirms a truth and catches a falsehood.

One true + one false case per domain, run through the registry's run_for_domain (the
same path the engine uses). Keeps coverage honest: a faithful port is not trusted
until it both confirms and rejects. Runnable with `pytest` OR `python tests/test_verifiers.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import run_for_domain  # noqa: E402


def _status(domain, packet):
    """The strongest applicable verdict for a domain/packet (first failure wins)."""
    results = [r for r in run_for_domain(domain, packet) if r.applicable]
    assert results, f"{domain}: no applicable verifier ran for {packet}"
    if any(r.failed for r in results):
        return "FAIL"
    if all(r.passed for r in results):
        return "PASS"
    return "MIXED"


# (domain, true_packet, false_packet)
CASES = [
    ("number_theory",
     {"NUM_VERIFY": {"n_prime": 17, "claimed_prime": True}},
     {"NUM_VERIFY": {"n_prime": 18, "claimed_prime": True}}),
    ("number_theory",
     {"NUM_VERIFY": {"factorial_n": 5, "claimed_factorial": 120}},
     {"NUM_VERIFY": {"factorial_n": 5, "claimed_factorial": 121}}),
    ("information_theory",
     {"INFO_VERIFY": {"string_a": "1010", "string_b": "1001", "claimed_hamming": 2}},
     {"INFO_VERIFY": {"string_a": "1010", "string_b": "1001", "claimed_hamming": 1}}),
    ("geometry",
     {"GEOM_VERIFY": {"pyth_a": 3, "pyth_b": 4, "pyth_c": 5, "claimed_right_triangle": True}},
     {"GEOM_VERIFY": {"pyth_a": 3, "pyth_b": 4, "pyth_c": 6, "claimed_right_triangle": True}}),
    ("geometry",
     {"GEOM_VERIFY": {"polygon_n": 4, "claimed_interior_angle_sum_deg": 360}},
     {"GEOM_VERIFY": {"polygon_n": 4, "claimed_interior_angle_sum_deg": 999}}),
]


def test_verifiers_confirm_truth_and_catch_falsehood():
    for domain, true_pkt, false_pkt in CASES:
        assert _status(domain, true_pkt) == "PASS", f"{domain} failed to CONFIRM a truth: {true_pkt}"
        assert _status(domain, false_pkt) == "FAIL", f"{domain} failed to CATCH a falsehood: {false_pkt}"


if __name__ == "__main__":
    test_verifiers_confirm_truth_and_catch_falsehood()
    doms = sorted({c[0] for c in CASES})
    print(f"  ok  {len(CASES)} cases across {len(doms)} domains: {', '.join(doms)}")
    print("  ok  each confirms a truth and catches a falsehood")
