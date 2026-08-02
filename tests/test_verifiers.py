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
    ("physics",
     {"PHYS_VERIFY": {"v0": 0, "a": 10, "t": 2, "claimed_displacement": 20}},
     {"PHYS_VERIFY": {"v0": 0, "a": 10, "t": 2, "claimed_displacement": 21}}),
    ("finance",
     {"FIN_VERIFY": {"assets": 100, "liabilities": 60, "equity": 40}},
     {"FIN_VERIFY": {"assets": 100, "liabilities": 60, "equity": 30}}),
    ("governance",
     {"DECISION_PACKET": {"title": "t", "scope": "local", "red_items": ["x"],
                          "floor_items": ["y"], "way_path": "choose the careful reversible path",
                          "execution_steps": ["do it"], "witnesses": ["Alice"]}},
     {"DECISION_PACKET": {"title": "t", "scope": "local", "red_items": ["x"],
                          "floor_items": [], "way_path": "choose the careful reversible path",
                          "execution_steps": ["do it"], "witnesses": ["Alice"]}}),
]


def test_verifiers_confirm_truth_and_catch_falsehood():
    for domain, true_pkt, false_pkt in CASES:
        assert _status(domain, true_pkt) == "PASS", f"{domain} failed to CONFIRM a truth: {true_pkt}"
        assert _status(domain, false_pkt) == "FAIL", f"{domain} failed to CATCH a falsehood: {false_pkt}"


def test_all_registered_verifiers_load_and_run():
    """Structural guard: every registered secular domain imports and runs on an empty
    packet (returns NOT_APPLICABLE, never crashes). Catches a broken/missing port."""
    from concordance.verifiers import VERIFIERS, run_for_domain
    for d in sorted(VERIFIERS):
        res = run_for_domain(d, {})
        assert isinstance(res, list) and res, f"{d}: no result on empty packet"


if __name__ == "__main__":
    test_verifiers_confirm_truth_and_catch_falsehood()
    doms = sorted({c[0] for c in CASES})
    print(f"  ok  {len(CASES)} cases across {len(doms)} domains: {', '.join(doms)}")
    print("  ok  each confirms a truth and catches a falsehood")
    test_all_registered_verifiers_load_and_run()
    from concordance.verifiers import VERIFIERS
    print(f"  ok  all {len(VERIFIERS)} registered domain names load + run on an empty packet")


def test_modular_arithmetic_is_in_the_grammar():
    """The fleet could not check "n mod m = k" AT ALL — '%' sat on the invalid-character list
    though SymPy computes Mod natively, and every such claim returned INCOMPLETE. Found when the
    vortex-math assay tried to seal the doubling cycle and could not. Casting out nines is the
    oldest integrity check in bookkeeping — the ancestor of this project's hashes — and the
    fleet could not perform it. Word form and operator form both; falsity still breaks."""
    from concordance.derivation import verify

    # the doubling cycle mod 9: 2^n walks 1,2,4,8,7,5 and repeats — checked, not believed
    cycle = [(2, 2), (4, 4), (8, 8), (16, 7), (32, 5), (64, 1),
             (128, 2), (256, 4), (512, 8), (1024, 7)]
    for n, root in cycle:
        r = verify({"mode": "equality",
                    "params": {"expr_a": f"{n} mod 9", "expr_b": str(root), "variables": {}}})
        assert r.get("verdict") == "HOLDS", f"{n} mod 9 should be {root}: {r}"
    r = verify({"mode": "equality",
                "params": {"expr_a": "16 % 9", "expr_b": "7", "variables": {}}})
    assert r.get("verdict") == "HOLDS", "the operator form must parse too"
    r = verify({"mode": "equality",
                "params": {"expr_a": "16 mod 9", "expr_b": "3", "variables": {}}})
    assert r.get("verdict") == "BROKEN", "a false congruence must still break"
    # Mod-the-function and ordinary words are untouched by the normalization
    r = verify({"mode": "equality",
                "params": {"expr_a": "Mod(16, 9)", "expr_b": "7", "variables": {}}})
    assert r.get("verdict") == "HOLDS"
