"""The elliptic-curve L-value door (tick stick, 2026-10-05): a_p by point counting, a_n multiplicatively, L(E,1)
by the approximate functional equation whose cutoff-independence CHECKS the root number; the analytic rank and
the theorem it rests on (Kolyvagin; Gross–Zagier). Four famous curves, two wrong claims, one honest decline."""
from concordance import verifiers
from concordance.verifiers import elliptic_curves as EC


def _run(spec):
    return EC.run({"ELLIPTIC_VERIFY": spec})[0]


def test_11a1_has_a_nonzero_l_value_and_rank_zero_by_kolyvagin():
    r = _run({"a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1,
              "claimed_L1": 0.253842, "claimed_analytic_rank": 0})
    assert r.status == "CONFIRMED" and abs(r.data["L1"] - 0.253842) < 1e-5 and r.data["analytic_rank"] == 0
    assert "Kolyvagin" in r.data["theorem"] and r.data["a_p"]["2"] == -2 and r.data["a_p"]["3"] == -1
    assert r.data["a_p"]["11"] == 1                                     # split multiplicative at the bad prime


def test_37a1_vanishes_at_one_with_nonzero_derivative_rank_one():
    r = _run({"a_invariants": [0, 0, 1, -1, 0], "conductor": 37, "root_number": -1, "claimed_analytic_rank": 1})
    assert r.status == "CONFIRMED" and abs(r.data["L1"]) < 1e-8 and abs(r.data["Lprime1"] - 0.305999) < 1e-5
    assert r.data["analytic_rank"] == 1 and "Gross" in r.data["theorem"]


def test_higher_analytic_rank_is_reported_numerically_and_no_theorem_is_claimed():
    r = _run({"a_invariants": [0, 1, 1, -2, 0], "conductor": 389, "root_number": 1, "claimed_analytic_rank": 2})
    assert r.status == "CONFIRMED" and r.data["analytic_rank"] == ">=2 numerically" and "no theorem" in r.data["theorem"]
    r = _run({"a_invariants": [0, 0, 1, -7, 6], "conductor": 5077, "root_number": -1, "claimed_analytic_rank": 3})
    assert r.status == "CONFIRMED" and r.data["analytic_rank"] == ">=3 numerically"
    r = _run({"a_invariants": [0, 1, 1, -2, 0], "conductor": 389, "root_number": 1, "claimed_analytic_rank": 0})
    assert r.status == "MISMATCH"


def test_a_wrong_root_number_or_l_value_is_refused_and_small_bad_primes_are_declined():
    r = _run({"a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": -1, "claimed_L1": 0.253842})
    assert r.status == "MISMATCH" and "root number" in r.detail
    r = _run({"a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1, "claimed_L1": 0.3})
    assert r.status == "MISMATCH" and "claimed 0.300000" in r.detail
    r = _run({"a_invariants": [1, 0, 1, 4, -6], "conductor": 14, "root_number": 1, "claimed_analytic_rank": 0})
    assert r.status == "NOT_APPLICABLE" and "Tate" in r.detail
    assert _run({"a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1}).status == "NOT_APPLICABLE"


def test_the_domain_is_routed():
    rs = verifiers.run_for_domain("elliptic_curves", {"ELLIPTIC_VERIFY": {
        "a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1, "claimed_analytic_rank": 0}})
    assert [r.status for r in rs if r.name == "elliptic_curves.l_value"] == ["CONFIRMED"]
    rs = verifiers.run_for_domain("bsd", {"ELLIPTIC_VERIFY": {
        "a_invariants": [0, -1, 1, -10, -20], "conductor": 11, "root_number": 1, "claimed_analytic_rank": 0}})
    assert any(r.status == "CONFIRMED" for r in rs)
