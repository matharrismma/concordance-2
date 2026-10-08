"""Stated precision (2026-10-07): the claim's own precision sets the bar — never looser than that.

"earth gravity is 9.81 m/s^2" was MISMATCHED live: a flat rel_tol of 1e-4 (threshold 0.00098) against
9.80665 (diff 0.00335). The person was RIGHT to the three figures they stated. The fix: read the precision
off the literal as written and allow half a unit in the last stated place — but only when two or more
significant figures were stated, so a one-digit "3e8" or "300000000" never passes as exact. A caller can
only STATE a claim, never hand in a tolerance, so the window cannot be widened past what the claim says.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance.verifiers import base as B  # noqa: E402
from concordance.verifiers import physical_constants as PC  # noqa: E402
from concordance.verifiers import astronomy as AST  # noqa: E402


def _sp(literal, sig, half):
    got = B.stated_precision(literal)
    assert got is not None and got[0] == sig and math.isclose(got[1], half, rel_tol=1e-9), (literal, got)


def test_stated_precision_reads_the_literal():
    _sp("9.81", 3, 0.005)
    _sp("9.80665", 6, 0.000005)
    _sp("5730", 3, 5.0)            # trailing zero of an integer: not significant
    _sp("11186", 5, 0.5)
    _sp("3.0e8", 2, 5e6)
    _sp("3e8", 1, 5e7)
    _sp("300000000", 1, 5e7)
    _sp("0.0025", 2, 0.00005)
    _sp("1,234.5", 5, 0.05)
    assert B.stated_precision("nine") is None
    assert B.stated_precision("") is None


def test_stated_tolerance_refuses_one_significant_figure():
    assert B.stated_tolerance_abs("3e8") is None
    assert B.stated_tolerance_abs("300000000") is None
    assert math.isclose(B.stated_tolerance_abs("3.0e8"), 5e6, rel_tol=1e-9)
    assert math.isclose(B.stated_tolerance_abs("9.81"), 0.005, rel_tol=1e-9)
    assert math.isclose(B.stated_tolerance_abs("11.2", unit_factor=1000.0), 50.0, rel_tol=1e-9)


def test_physical_constant_honors_stated_precision():
    ok = PC.verify_physical_constant({"constant": "standard_gravity", "claimed_value": 9.81,
                                      "claimed_literal": "9.81"})
    assert ok.status == "CONFIRMED", ok.detail
    assert ok.data.get("stated_sigfigs") == 3
    bad = PC.verify_physical_constant({"constant": "standard_gravity", "claimed_value": 9.91,
                                       "claimed_literal": "9.91"})
    assert bad.status == "MISMATCH"
    two = PC.verify_physical_constant({"constant": "speed_of_light", "claimed_value": 3.0e8,
                                       "claimed_literal": "3.0e8", "claimed_unit": "m/s"})
    assert two.status == "CONFIRMED", two.detail
    one = PC.verify_physical_constant({"constant": "speed_of_light", "claimed_value": 3e8,
                                       "claimed_literal": "3e8", "claimed_unit": "m/s"})
    assert one.status == "MISMATCH"                        # one figure never buys an exact pass


def test_physical_constant_without_a_literal_is_unchanged():
    """The structured door keeps the strict default: no literal, no loosening (the pinned contract)."""
    assert PC.verify_physical_constant({"constant": "standard_gravity", "claimed_value": 9.81}).status == "MISMATCH"
    assert PC.verify_physical_constant({"constant": "speed_of_light", "claimed_value": 1.0e8,
                                        "claimed_unit": "m/s"}).status == "MISMATCH"


def test_escape_velocity_as_written_at_stated_precision():
    spec = {"escape_mass_kg": 5.9722e24, "escape_radius_m": 6.371e6,
            "claimed_escape_velocity_m_s": 11200.0, "claimed_escape_velocity_as_written": "11.2 km/s"}
    r = AST.verify_gravitational_scale(spec)
    assert r.status == "CONFIRMED", r.detail
    spec_f = {**spec, "claimed_escape_velocity_m_s": 15000.0, "claimed_escape_velocity_as_written": "15 km/s"}
    assert AST.verify_gravitational_scale(spec_f).status == "MISMATCH"
    # without the as-written form the strict 1e-3 default stands (11200 vs 11186 is 1.25e-3 off)
    strict = {k: v for k, v in spec.items() if k != "claimed_escape_velocity_as_written"}
    assert AST.verify_gravitational_scale(strict).status == "MISMATCH"


def test_numeric_mode_honors_stated_precision():
    """mathematics.numeric (2026-10-07): the route for sqrt of a non-perfect square — the same three pins as
    physical_constants: the stated-precision pass, the one-figure refusal, the no-literal strictness."""
    from concordance.verifiers import mathematics as M
    ok = M.verify_numeric({"numeric_expr": "sqrt(2)", "claimed_value": 1.41421, "claimed_literal": "1.41421"})
    assert ok.status == "CONFIRMED", ok.detail
    assert ok.data.get("stated_sigfigs") == 6 and "6 significant figure" in ok.detail
    bad = M.verify_numeric({"numeric_expr": "sqrt(2)", "claimed_value": 1.51421, "claimed_literal": "1.51421"})
    assert bad.status == "MISMATCH"
    two = M.verify_numeric({"numeric_expr": "sqrt(2)", "claimed_value": 1.4, "claimed_literal": "1.4"})
    assert two.status == "CONFIRMED", two.detail
    edge = M.verify_numeric({"numeric_expr": "sqrt(2)", "claimed_value": 1.5, "claimed_literal": "1.5"})
    assert edge.status == "MISMATCH"                     # 0.086 off; half a unit in the tenths is 0.05
    one = M.verify_numeric({"numeric_expr": "sqrt(2)", "claimed_value": 1.0, "claimed_literal": "1"})
    assert one.status == "MISMATCH"                      # one figure never buys a pass


def test_numeric_mode_without_a_literal_is_unchanged():
    from concordance.verifiers import mathematics as M
    assert M.verify_numeric({"numeric_expr": "sqrt(2)", "claimed_value": 1.41421}).status == "MISMATCH"
    assert M.verify_numeric({"numeric_expr": "sqrt(2)", "claimed_value": 1.41421356237}).status == "CONFIRMED"
    # a handed-in tolerance still only tightens (clamp_tol): it cannot do what the literal does
    assert M.verify_numeric({"numeric_expr": "sqrt(2)", "claimed_value": 1.41421, "rel_tol": 1e-2}).status == "MISMATCH"


def test_escape_velocity_unknown_unit_earns_no_window():
    """Review 2026-10-08: an as-written claim in a unit the verifier does not know must not widen the window
    in the wrong unit — '24,000 mph' is 4% off and would have passed at a factor of 1."""
    spec = {"escape_mass_kg": 5.9722e24, "escape_radius_m": 6.371e6,
            "claimed_escape_velocity_m_s": 10729.0, "claimed_escape_velocity_as_written": "24,000 mph"}
    assert AST.verify_gravitational_scale(spec).status == "MISMATCH"
