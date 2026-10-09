"""THE FULL BSD FORMULA on one curve (2026-10-09, the Millennium loop). The period is COMPUTED by integration and checked
against Cremona's tables; the Tamagawa product, torsion, Sha and regulator are CITED inputs the spec must source. For
11a1 (rank 0): L(E,1)/Omega = 1/5 = (1 * 5) / 5^2. For 37a1 (rank 1): L'(E,1)/Omega = R = 0.0511114082399688.
Reference periods: Cremona's tables / LMFDB (11.a3, 37.a1, 389.a1, 5077.a1)."""
from __future__ import annotations

from concordance.verifiers import elliptic_curves as EC

SRC = "J. E. Cremona, Algorithms for Modular Elliptic Curves (1997), Table 1; LMFDB"


def test_the_real_period_matches_the_tables_for_both_signs_of_the_discriminant():
    for ainv, ref, comps in (([0, -1, 1, -10, -20], 1.26920930427955, 1), ([0, 0, 1, -1, 0], 5.98691729246392, 2),
                             ([0, 1, 1, -2, 0], 4.98042512171, 2), ([0, 0, 1, -7, 6], 4.15168798308, 2)):
        p = EC.real_period(ainv)
        assert abs(p["omega"] - ref) / ref < 1e-9, (ainv, p)
        assert p["components"] == comps


def test_11a1_rank_0_the_formula_holds_with_its_cited_inputs():
    r = EC.verify_bsd_formula({"a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1,
                               "tamagawa_product": 5, "torsion_order": 5, "sha_order": 1, "inputs_source": SRC,
                               "claimed_bsd_holds": True})
    assert r.status == "CONFIRMED", r.detail
    assert r.data["rank"] == 0 and abs(r.data["right_side"] - 0.2) < 1e-12 and abs(r.data["left_side"] - 0.2) < 2e-5
    assert abs(r.data["computed"]["omega"] - 1.26920930427955) < 1e-9
    assert "Kolyvagin" in r.detail and "cited from" in r.detail


def test_37a1_rank_1_the_formula_holds_with_the_cited_regulator():
    r = EC.verify_bsd_formula({"a_invariants": [0, 0, 1, -1, 0], "conductor": 37, "root_number": -1,
                               "tamagawa_product": 1, "torsion_order": 1, "sha_order": 1, "regulator": 0.0511114082399688,
                               "inputs_source": SRC, "claimed_bsd_holds": True})
    assert r.status == "CONFIRMED", r.detail
    assert r.data["rank"] == 1 and abs(r.data["left_side"] - 0.0511114082399688) < 2e-5
    assert "Gross-Zagier" in r.detail


def test_a_wrong_cited_input_is_refused_and_the_formula_declines_where_no_theorem_carries_it():
    bad = EC.verify_bsd_formula({"a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1,
                                 "tamagawa_product": 1, "torsion_order": 5, "inputs_source": SRC, "claimed_bsd_holds": True})
    assert bad.status == "MISMATCH" and "NOT equal" in bad.detail
    nosrc = EC.verify_bsd_formula({"a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1,
                                   "tamagawa_product": 5, "torsion_order": 5, "claimed_bsd_holds": True})
    assert nosrc.status == "ERROR" and "inputs_source" in nosrc.detail
    r2 = EC.verify_bsd_formula({"a_invariants": [0, 1, 1, -2, 0], "conductor": 389, "root_number": 1,
                                "tamagawa_product": 1, "torsion_order": 1, "inputs_source": SRC, "claimed_bsd_holds": True})
    assert r2.status == "NOT_APPLICABLE"                      # analytic rank 2: no theorem carries the formula


def test_the_formula_is_routed_and_the_l_value_door_still_is():
    out = EC.run({"ELLIPTIC_VERIFY": {"a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1,
                                      "tamagawa_product": 5, "torsion_order": 5, "inputs_source": SRC, "claimed_bsd_holds": True}})
    assert any(o.name == "elliptic_curves.bsd_formula" and o.status == "CONFIRMED" for o in out)
    out2 = EC.run({"ELLIPTIC_VERIFY": {"a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1, "claimed_analytic_rank": 0}})
    assert any(o.name == "elliptic_curves.l_value" and o.status == "CONFIRMED" for o in out2)
