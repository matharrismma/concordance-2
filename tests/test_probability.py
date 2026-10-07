"""Unit-pin the probability verifier (A2, 2026-10-06). Binomial(10,3,0.5)=0.1172; E[X]=2.3 for
outcomes [1,2,3] with p [0.2,0.3,0.5]."""
from __future__ import annotations
from concordance.verifiers import probability as P


def test_binomial_probability():
    assert P.verify_binomial_probability({"binomial_n": 10, "binomial_k": 3, "binomial_p": 0.5,
                                          "claimed_binomial_probability": 0.1172}).status == "CONFIRMED"
    assert P.verify_binomial_probability({"binomial_n": 10, "binomial_k": 3, "binomial_p": 0.5,
                                          "claimed_binomial_probability": 0.5}).status == "MISMATCH"
    assert P.verify_binomial_probability({}).status == "NOT_APPLICABLE"


def test_expected_value():
    assert P.verify_expected_value({"outcomes": [1, 2, 3], "probabilities": [0.2, 0.3, 0.5],
                                    "claimed_expected_value": 2.3}).status == "CONFIRMED"
    assert P.verify_expected_value({"outcomes": [1, 2, 3], "probabilities": [0.2, 0.3, 0.5],
                                    "claimed_expected_value": 2.0}).status == "MISMATCH"
