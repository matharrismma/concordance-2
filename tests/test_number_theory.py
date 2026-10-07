"""Unit-pin the number_theory verifier's elementary checks (A2, 2026-10-06). 7 is prime; gcd(12,8)=4;
5! = 120. (The Riemann/Robin/Nicolas routes are exercised by tools/tick.py; this pins the basics.)"""
from __future__ import annotations
from concordance.verifiers import number_theory as NT


def test_primality():
    assert NT.verify_primality({"n_prime": 7, "claimed_prime": True}).status == "CONFIRMED"
    assert NT.verify_primality({"n_prime": 8, "claimed_prime": True}).status == "MISMATCH"
    assert NT.verify_primality({}).status == "NOT_APPLICABLE"


def test_gcd():
    assert NT.verify_gcd({"gcd_a": 12, "gcd_b": 8, "claimed_gcd": 4}).status == "CONFIRMED"
    assert NT.verify_gcd({"gcd_a": 12, "gcd_b": 8, "claimed_gcd": 3}).status == "MISMATCH"


def test_factorial():
    assert NT.verify_factorial({"factorial_n": 5, "claimed_factorial": 120}).status == "CONFIRMED"
    assert NT.verify_factorial({"factorial_n": 5, "claimed_factorial": 100}).status == "MISMATCH"
