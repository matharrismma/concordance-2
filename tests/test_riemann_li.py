"""LI'S CRITERION on the Riemann stick (2026-10-09, Matt: "start with Riemann"). RH <=> lambda_n > 0 for all n (Li 1997).
The verifier computes lambda_n from the Taylor expansion of log xi(1/(1 - z)) and cross-checks lambda_1 against its
closed form before any verdict. Known values (Keiper 1992; Bombieri-Lagarias 1999): lambda_1 = 0.0230957089661...,
lambda_2 = 0.0923457352280..., lambda_3 = 0.2076389205..."""
from __future__ import annotations

import math

from concordance.verifiers import number_theory as NT


def test_li_criterion_holds_to_twelve_and_matches_the_known_values():
    r = NT.verify_li_criterion({"li_to": 12, "claimed_li_positive": True})
    assert r.status == "CONFIRMED", r.detail
    lam = r.data["lambda"]
    euler_gamma = 0.57721566490153286
    assert abs(lam[0] - (1 + euler_gamma / 2 - math.log(4 * math.pi) / 2)) < 1e-11
    assert abs(lam[1] - 0.0923457352280) < 1e-9
    assert abs(lam[2] - 0.2076389205543) < 1e-9
    assert all(v > 0 for v in lam) and r.data["least_lambda_n"] == 1 and len(lam) == 12
    assert "no RH counterexample by this route below 12" in r.detail


def test_a_false_claim_is_refused_and_the_cap_is_honest():
    assert NT.verify_li_criterion({"li_to": 6, "claimed_li_positive": False}).status == "MISMATCH"
    assert NT.verify_li_criterion({"li_to": 0, "claimed_li_positive": True}).status == "ERROR"
    assert NT.verify_li_criterion({"li_to": 26, "claimed_li_positive": True}).status == "ERROR"   # the measured cap: 30 took 66 min
    assert NT.verify_li_criterion({"li_to": 4}).status == "NOT_APPLICABLE"


def test_the_criterion_is_routed_through_the_packet():
    out = NT.run({"NUM_VERIFY": {"li_to": 4, "claimed_li_positive": True}})
    assert any(o.name == "number_theory.li_criterion" and o.status == "CONFIRMED" for o in out)
