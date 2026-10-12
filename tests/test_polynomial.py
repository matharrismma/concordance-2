"""The Rational Root Theorem verifier — the complete set of rational roots, found and checked exactly."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import polynomial as P  # noqa: E402


def _status(spec):
    return [r.status for r in P.run(spec)]


def test_the_complete_set_of_rational_roots_is_found_and_matched():
    assert _status({"POLY_VERIFY": {"coeffs": [1, -5, 6], "claimed_rational_roots": [2, 3]}}) == ["CONFIRMED"]
    # fractions, highest-degree-first coeffs
    assert _status({"POLY_VERIFY": {"coeffs": [2, -1, -3], "claimed_rational_roots": ["3/2", -1]}}) == ["CONFIRMED"]
    # a cubic
    assert _status({"POLY_VERIFY": {"coeffs": [1, -6, 11, -6], "claimed_rational_roots": [1, 2, 3]}}) == ["CONFIRMED"]
    # a root at zero (x^3 - x)
    assert _status({"POLY_VERIFY": {"coeffs": [1, 0, -1, 0], "claimed_rational_roots": [-1, 0, 1]}}) == ["CONFIRMED"]


def test_a_wrong_or_incomplete_set_mismatches():
    assert _status({"POLY_VERIFY": {"coeffs": [1, -5, 6], "claimed_rational_roots": [2, 4]}}) == ["MISMATCH"]
    assert _status({"POLY_VERIFY": {"coeffs": [1, -5, 6], "claimed_rational_roots": [2]}}) == ["MISMATCH"]


def test_a_polynomial_with_no_rational_roots_has_the_empty_set():
    # x^2 - 2 has irrational roots only; the rational-root set is empty
    assert _status({"POLY_VERIFY": {"coeffs": [1, 0, -2], "claimed_rational_roots": []}}) == ["CONFIRMED"]
    assert _status({"POLY_VERIFY": {"coeffs": [1, 0, -2], "claimed_rational_roots": [1]}}) == ["MISMATCH"]


def test_a_single_claimed_root_is_checked_by_exact_evaluation():
    assert _status({"POLY_VERIFY": {"coeffs": [1, -5, 6], "claimed_root": 2}}) == ["CONFIRMED"]
    assert _status({"POLY_VERIFY": {"coeffs": [1, -5, 6], "claimed_root": 4}}) == ["MISMATCH"]
    assert _status({"POLY_VERIFY": {"coeffs": [2, -1, -3], "claimed_root": "3/2"}}) == ["CONFIRMED"]


def test_absent_or_unrelated_packet_is_not_applicable():
    assert all(r.status == "NOT_APPLICABLE" for r in P.run({}))
    assert all(r.status == "NOT_APPLICABLE" for r in P.run({"UNRELATED": {"x": 1}}))
