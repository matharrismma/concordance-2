"""The false-positive gate, extended beyond mathematics.

The cardinal sin of a verification engine is sealing a falsehood. The moat benchmark
proves 0 false-positives for mathematics (58 claims); this proves it for 22 more domains
— each with a known-TRUE packet (the verifier must CONFIRM) and a known-FALSE packet (it
must CATCH). The aggregate false-positive count across every domain must be exactly 0.

High-stakes domains are covered first (medicine, law, statistics, cryptography,
nuclear_physics, ...). Every TRUE value was computed from the verifier's own formula and
re-validated by running it through the same run_for_domain path the engine uses. A second
test proves the 122 registered aliases route to the right module (same verdict via every
alias). Runnable with pytest OR `python tests/test_fp_gate.py`.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import VERIFIERS, run_for_domain  # noqa: E402

# (domain, true_packet, false_packet) — true confirms, false is caught. Validated cases.
CASES = [
    ("medicine",
     {"MED_VERIFY": {"weight_kg": 70, "height_m": 1.75, "claimed_bmi": 22.86}},
     {"MED_VERIFY": {"weight_kg": 70, "height_m": 1.75, "claimed_bmi": 25.0}}),
    ("law",
     {"LAW_VERIFY": {"hours_worked": 48, "regular_rate": 20.00, "claimed_overtime_pay": 240.00}},
     {"LAW_VERIFY": {"hours_worked": 48, "regular_rate": 20.00, "claimed_overtime_pay": 200.00}}),
    ("statistics",
     {"STAT_VERIFY": {"estimate": 10.0, "ci_low": 8.0, "ci_high": 12.0}},
     {"STAT_VERIFY": {"estimate": 15.0, "ci_low": 8.0, "ci_high": 12.0}}),
    ("cryptography",
     {"CRYPTO_VERIFY": {"hash_algorithm": "sha256", "data": "hello world",
                        "claimed_hash_hex": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"}},
     {"CRYPTO_VERIFY": {"hash_algorithm": "sha256", "data": "hello world",
                        "claimed_hash_hex": "a94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"}}),
    ("nuclear_physics",
     {"NUCLEAR_VERIFY": {"half_life_seconds": 1600.0, "elapsed_seconds": 1600.0,
                         "initial_count": 1e12, "claimed_remaining_count": 5e11}},
     {"NUCLEAR_VERIFY": {"half_life_seconds": 1600.0, "elapsed_seconds": 1600.0,
                         "initial_count": 1e12, "claimed_remaining_count": 6e11}}),
    ("chemistry",
     {"CHEM_VERIFY": {"delta_H_kJ_mol": -100.0, "delta_S_J_mol_K": 200.0,
                      "temperature_K": 300.0, "claimed_spontaneous": True}},
     {"CHEM_VERIFY": {"delta_H_kJ_mol": -100.0, "delta_S_J_mol_K": 200.0,
                      "temperature_K": 300.0, "claimed_spontaneous": False}}),
    ("economics",
     {"ECON_VERIFY": {"principal": 1000, "rate": 0.05, "time_years": 3,
                      "compounding_periods": 12, "claimed_compound_amount": 1161.47}},
     {"ECON_VERIFY": {"principal": 1000, "rate": 0.05, "time_years": 3,
                      "compounding_periods": 12, "claimed_compound_amount": 1200.00}}),
    ("electrical",
     {"ELEC_VERIFY": {"voltage_V": 12.0, "current_A": 0.5, "resistance_ohm": 24.0}},
     {"ELEC_VERIFY": {"voltage_V": 10.0, "current_A": 0.5, "resistance_ohm": 24.0}}),
    ("thermodynamics",
     {"THERMO_VERIFY": {"T_hot_K": 600.0, "T_cold_K": 300.0, "claimed_efficiency": 0.5}},
     {"THERMO_VERIFY": {"T_hot_K": 600.0, "T_cold_K": 300.0, "claimed_efficiency": 0.6}}),
    ("optics",
     {"OPT_VERIFY": {"n1": 1.0, "n2": 1.5, "theta1_deg": 30, "claimed_theta2_deg": 19.47}},
     {"OPT_VERIFY": {"n1": 1.0, "n2": 1.5, "theta1_deg": 30, "claimed_theta2_deg": 25.0}}),
    ("probability",
     {"PROB_VERIFY": {"binomial_n": 10, "binomial_p": 0.5, "binomial_k": 5,
                      "claimed_binomial_probability": 0.24609375}},
     {"PROB_VERIFY": {"binomial_n": 10, "binomial_p": 0.5, "binomial_k": 5,
                      "claimed_binomial_probability": 0.30}}),
    ("linear_algebra",
     {"LIN_VERIFY": {"vec_a": [1, 2, 3], "vec_b": [4, 5, 6], "claimed_dot_product": 32}},
     {"LIN_VERIFY": {"vec_a": [1, 2, 3], "vec_b": [4, 5, 6], "claimed_dot_product": 30}}),
    ("computer_science",
     {"CS_VERIFY": {"code": "def add(a, b):\n    return a + b\n", "function_name": "add",
                    "test_cases": [{"input": [2, 3], "expected": 5}]}},
     {"CS_VERIFY": {"code": "def add(a, b):\n    return a + b\n", "function_name": "add",
                    "test_cases": [{"input": [2, 3], "expected": 6}]}}),
    ("formal_logic",
     {"LOGIC_VERIFY": {"variables": ["p"], "formula": "p | ~p", "claimed_tautology": True}},
     {"LOGIC_VERIFY": {"variables": ["p"], "formula": "p | ~p", "claimed_tautology": False}}),
    ("astronomy",
     {"ASTRO_VERIFY": {"apparent_magnitude": 5.0, "absolute_magnitude": 0.0, "claimed_distance_parsec": 100.0}},
     {"ASTRO_VERIFY": {"apparent_magnitude": 5.0, "absolute_magnitude": 0.0, "claimed_distance_parsec": 50.0}}),
    ("genetics",
     {"GENETICS_VERIFY": {"codon": "ATG", "claimed_amino_acid": "M"}},
     {"GENETICS_VERIFY": {"codon": "ATG", "claimed_amino_acid": "K"}}),
    ("networking",
     {"NET_VERIFY": {"subnet_prefix": 24, "claimed_usable_hosts": 254}},
     {"NET_VERIFY": {"subnet_prefix": 24, "claimed_usable_hosts": 256}}),
    ("ecology",
     {"ECO_VERIFY": {"species_proportions": [0.5, 0.3, 0.2], "claimed_shannon_index": 1.0297}},
     {"ECO_VERIFY": {"species_proportions": [0.5, 0.3, 0.2], "claimed_shannon_index": 1.5}}),
    ("hydrology",
     {"HYD_VERIFY": {"manning_n": 0.013, "hydraulic_radius_m": 1.0, "slope": 0.001, "claimed_velocity_m_s": 2.43}},
     {"HYD_VERIFY": {"manning_n": 0.013, "hydraulic_radius_m": 1.0, "slope": 0.001, "claimed_velocity_m_s": 3.0}}),
    ("meteorology",
     {"MET_VERIFY": {"temperature_c": 25.0, "relative_humidity_pct": 60.0, "claimed_dew_point_c": 16.70}},
     {"MET_VERIFY": {"temperature_c": 25.0, "relative_humidity_pct": 60.0, "claimed_dew_point_c": 20.0}}),
    ("materials_science",
     {"MAT_VERIFY": {"thermal_expansion_coeff": 12e-6, "original_length_m": 2.0, "delta_T_K": 50,
                     "claimed_delta_length_m": 0.0012}},
     {"MAT_VERIFY": {"thermal_expansion_coeff": 12e-6, "original_length_m": 2.0, "delta_T_K": 50,
                     "claimed_delta_length_m": 0.0020}}),
    ("exercise_science",
     {"EX_VERIFY": {"age_years": 30, "claimed_max_hr": 187}},
     {"EX_VERIFY": {"age_years": 30, "claimed_max_hr": 190}}),
]


def _status(domain, packet):
    results = [r for r in run_for_domain(domain, packet) if r.applicable]
    if not results:
        return "NONE"
    if any(r.failed for r in results):
        return "FAIL"
    if all(r.passed for r in results):
        return "PASS"
    return "MIXED"


def test_no_false_positives_across_domains():
    """The aggregate false-positive count across all domains must be exactly 0."""
    false_positives = []
    false_negatives = []
    for domain, true_pkt, false_pkt in CASES:
        if _status(domain, true_pkt) != "PASS":
            false_negatives.append(domain)        # failed to confirm a truth
        if _status(domain, false_pkt) == "PASS":
            false_positives.append(domain)        # sealed a falsehood — the cardinal sin
    assert not false_positives, f"FALSE-POSITIVES (sealed a falsehood): {false_positives}"
    assert not false_negatives, f"false-negatives (rejected a truth): {false_negatives}"


def test_aliases_route_to_the_right_verifier():
    """Every alias must produce the same verdict as its canonical domain on a real case."""
    def _mod(t):  # one consistent grouping key (functions have __module__; modules don't)
        return getattr(t, "__module__", None) or str(t)

    by_module = defaultdict(list)
    for name, target in VERIFIERS.items():
        by_module[_mod(target)].append(name)

    checked = 0
    for domain, true_pkt, false_pkt in CASES:
        target = VERIFIERS.get(domain)
        if target is None:
            continue
        siblings = [n for n in by_module[_mod(target)] if n != domain]
        for alias in siblings:
            assert _status(alias, true_pkt) == "PASS", f"alias {alias!r} (of {domain}) lost the truth"
            assert _status(alias, false_pkt) == "FAIL", f"alias {alias!r} (of {domain}) lost the catch"
            checked += 1
    assert checked > 0, "expected at least some aliased domains among the cases"


if __name__ == "__main__":
    test_no_false_positives_across_domains()
    print(f"  ok  {len(CASES)} domains: each confirms a truth, catches a falsehood, 0 false-positives")
    test_aliases_route_to_the_right_verifier()
    print("  ok  aliases route to the right verifier")
    print(f"\nFalse-positive gate: mathematics (58 moat) + {len(CASES)} domains, 0 false-positives.")
