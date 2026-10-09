"""GET FAIRLY CLOSE, WITH A PROVEN BOUND (Matt, 2026-10-09: "What we need is a way to get fairly close." - "build").
The approximation verifier: anchor + one step, the error a Taylor/Lagrange or Lipschitz remainder. Pinned: the
bounded estimate is right and the true value lies inside for the known functions; a closeness claim the true value
does NOT satisfy is a MISMATCH and a too-small curvature bound is a MISMATCH (0 false positives); the domain guards
hold; the estimate/bound route through verify_derivation and are sealable."""
from __future__ import annotations

import math

from concordance.verifiers import approximation as A
from concordance.verifiers.base import VerifierResult


def _v(spec) -> VerifierResult:
    return A.verify_get_close(spec)


def test_known_functions_get_close_with_a_bound_that_holds():
    for func, x0, x, fx in [("sqrt", 25, 26, math.sqrt(26)), ("exp", 0, 0.1, math.exp(0.1)),
                            ("ln", 1, 1.1, math.log(1.1)), ("sin", 0, 0.1, math.sin(0.1)),
                            ("recip", 2, 2.1, 1 / 2.1)]:
        r = _v({"func": func, "anchor": x0, "target": x})
        assert r.status == "CONFIRMED", (func, r.detail)
        d = r.data
        assert d["lo"] <= fx <= d["hi"], (func, d)                 # the true value is inside the interval
        assert abs(fx - d["estimate"]) <= d["error_bound"] + 1e-12  # the bound holds


def test_a_false_closeness_claim_is_a_mismatch():
    # sqrt(26) = 5.09902; claiming it is within 0.0001 of 5.1 is false (gap 9.8e-4)
    r = _v({"func": "sqrt", "anchor": 25, "target": 26, "claimed_value": 5.1, "claimed_error": 0.0001})
    assert r.status == "MISMATCH"
    # a generous-enough claim holds
    r = _v({"func": "sqrt", "anchor": 25, "target": 26, "claimed_value": 5.1, "claimed_error": 0.002})
    assert r.status == "CONFIRMED"


def test_a_curvature_bound_that_is_too_small_is_caught():
    # exp on [0,0.1]: sup|f''| = e^0.1 = 1.105; claiming 0.1 is too small, so the Taylor interval misses the truth
    r = _v({"anchor": 0, "anchor_value": 1.0, "slope": 1.0, "second_bound": 0.1, "target": 0.1,
            "true_value": math.exp(0.1)})
    assert r.status == "MISMATCH" and "does NOT hold" in r.detail
    # the true sup confirms
    r = _v({"anchor": 0, "anchor_value": 1.0, "slope": 1.0, "second_bound": math.exp(0.1), "target": 0.1,
            "true_value": math.exp(0.1)})
    assert r.status == "CONFIRMED"


def test_lipschitz_zeroth_order():
    # |sin' | <= 1, so |sin(0.1) - sin(0)| <= 0.1
    r = _v({"anchor": 0, "anchor_value": 0.0, "lipschitz": 1.0, "target": 0.1, "true_value": math.sin(0.1)})
    assert r.status == "CONFIRMED" and r.data["order"] == 0 and r.data["error_bound"] == 0.1


def test_domain_guards_and_missing_inputs():
    assert _v({"func": "sqrt", "anchor": -1, "target": 2}).status == "ERROR"
    assert _v({"func": "ln", "anchor": 0.5, "target": -0.5}).status == "ERROR"
    assert _v({"func": "recip", "anchor": -1, "target": 1}).status == "ERROR"      # straddles 0
    assert _v({"anchor": 1, "target": 2}).status == "NOT_APPLICABLE"               # no func, no anchor_value
    assert _v({"anchor": 1, "anchor_value": 1, "target": 2}).status == "ERROR"      # no bound given


def test_it_routes_through_verify_derivation_and_is_not_applicable_elsewhere():
    from concordance.derivation import verify_derivation as V
    r = V([{"id": "s", "domain": "approximation", "spec": {"APPROX_VERIFY": {"func": "sqrt", "anchor": 25, "target": 26}}}])
    assert r["verdict"] == "HOLDS"
    # a packet with no APPROX_VERIFY artifact is NOT_APPLICABLE, never a false HOLDS
    assert A.run({})[0].status == "NOT_APPLICABLE"
