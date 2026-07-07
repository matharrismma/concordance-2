"""Caller-supplied tolerances are clamped (tighten-only).

A verifier lets the caller pass a tolerance, but an adversarial caller must not be able to
LOOSEN it past the verifier's default to force a CONFIRMED on a value that is actually wrong.
clamp_tol enforces: missing/malformed -> default; larger -> capped at default; smaller -> kept.
"""
from concordance.verifiers.base import clamp_tol


def test_missing_or_malformed_returns_default():
    assert clamp_tol({}, "tolerance", 5e-3) == 5e-3
    assert clamp_tol({"tolerance": None}, "tolerance", 5e-3) == 5e-3
    assert clamp_tol({"tolerance": "wide"}, "tolerance", 5e-3) == 5e-3
    assert clamp_tol({"other": 1.0}, "rel_tol", 1e-4) == 1e-4


def test_loosening_is_capped_at_default():
    assert clamp_tol({"tolerance": 1e6}, "tolerance", 5e-3) == 5e-3
    assert clamp_tol({"rel_tol": 0.9}, "rel_tol", 1e-4) == 1e-4
    assert clamp_tol({"abs_tol": 1000}, "abs_tol", 1e-6) == 1e-6


def test_tightening_is_allowed():
    assert clamp_tol({"tolerance": 1e-6}, "tolerance", 5e-3) == 1e-6
    assert clamp_tol({"rel_tol": 1e-9}, "rel_tol", 1e-4) == 1e-9


def test_negative_is_treated_as_magnitude_and_capped():
    # abs() so a negative can't sneak past; still capped at the default
    assert clamp_tol({"tolerance": -1e6}, "tolerance", 5e-3) == 5e-3
    assert clamp_tol({"tolerance": -1e-6}, "tolerance", 5e-3) == 1e-6
