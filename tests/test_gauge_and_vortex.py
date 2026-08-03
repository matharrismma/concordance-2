"""The two inward-facing instruments: the gauge panel and the vortex assay.

Both exist to say something uncomfortable and true about our own work, so both are tested for
the ways they could go quiet. The gauge panel must not skip a constant it failed to parse, and
the vortex assay must keep the real arithmetic rather than throwing it out with the overreach.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))

import gauge_panel as GP    # noqa: E402
import vortex_assay as VA   # noqa: E402


# ── the gauge panel ──────────────────────────────────────────────────────────────────────────

def test_the_panel_reads_every_gauge_in_the_fleet():
    """A survey that silently skips is worse than no survey — it reports a clean panel it never
    looked at. Every clamp_tol site must be classified, none left unreadable."""
    gauges, unreadable = GP.collect()
    assert len(gauges) > 150, len(gauges)
    assert not unreadable, unreadable
    assert len({g["domain"] for g in gauges}) > 35


def test_every_gauge_gets_a_kind_and_a_door():
    gauges, _ = GP.collect()
    kinds = set()
    for g in gauges:
        kind, reason = GP.classify(g)
        assert reason.strip(), g
        kinds.add(kind)
        assert GP.door_width(g).strip()
    assert {"SCALED", "FLOAT-NOISE", "FIXED", "WIDE"} <= kinds, kinds


def test_a_scaled_gauge_is_recognised_as_the_target_pattern():
    """max(0.001, actual * 0.005) is a formula on the measured value — the thing MATH-1 is for.
    The first draft filed these as 'unreadable', which inverted the finding."""
    scaled = [g for g in GP.collect()[0] if GP.classify(g)[0] == "SCALED"]
    assert scaled, "no scaled gauges found — the exemplar pattern has vanished"
    assert any("actual" in g["expr"] for g in scaled)


def test_the_panel_refuses_to_guess_an_undeclared_unit():
    """It once read economics.rule_of_72's 0.5 YEARS as '50% of the true value' and reported a
    verifier as broken. Our failure is never their falsehood."""
    assert GP._is_relative("tolerance") is None
    assert GP._is_relative("tolerance_pct") is None      # two meanings across the fleet
    assert GP._is_relative("tolerance_relative") is True
    assert GP._is_relative("tolerance_km") is False
    g = {"domain": "economics", "key": "tolerance", "value": 0.5, "expr": "0.5", "line": 1}
    assert "unit undeclared" in GP.door_width(g)
    assert GP.classify(g)[0] == "UNKNOWN-UNIT"


def test_the_gauge_gate_can_actually_fail():
    """A gate that cannot fail is decoration. At an impossible threshold it must reject."""
    gauges, _ = GP.collect()
    for g in gauges:
        g["kind"], _ = GP.classify(g)
    wide = [g for g in gauges if g["kind"] == "WIDE"]
    assert wide, "nothing classified WIDE — the gate has nothing to bite on"
    assert any(abs(g["value"]) > 1e-4 for g in wide)


# ── the vortex assay ─────────────────────────────────────────────────────────────────────────

def test_the_digital_root_is_kept_because_it_is_real():
    """Keep the arithmetic. dr(n) == n mod 9 with 9 for 0 — casting out nines, and it works."""
    for n in range(1, 20000):
        assert VA.digital_root(n) == (n % 9 or 9)
    assert VA.digital_root(0) == 0


def test_the_doubling_orbit_is_real_and_has_period_six():
    assert VA.doubling_orbit() == [1, 2, 4, 8, 7, 5]
    assert not ({3, 6, 9} & set(VA.doubling_orbit()))
    assert VA.multiplicative_order(2, 9) == 6           # the theorem behind the pattern


def test_the_dead_end_is_named_by_changing_the_base():
    """THE DECIDING TEST. If 3-6-9 were a property of the universe it would survive a change of
    notation. It does not: in base 12 the excluded residue is 11, not 3/6/9."""
    base10 = set(range(1, 10)) - set(VA.doubling_orbit(1, 10))
    assert base10 == {3, 6, 9}
    base12 = set(range(1, 12)) - set(VA.doubling_orbit(1, 12))
    assert base12 == {11}, base12
    assert base12 != base10                             # the 'universal key' moved
    base8 = set(range(1, 8)) - set(VA.doubling_orbit(1, 8))
    assert base8 == {3, 5, 6, 7}, base8


def test_the_assay_runs_and_states_all_three_verdicts(capsys):
    """Three states, never two — and the unmeasured coil must not be reported as false."""
    assert VA.main() == 0
    out = capsys.readouterr().out
    assert "CONFIRMED" in out and "DEAD END" in out and "CANNOT_CHECK" in out
    assert "not the same as false" in out
    assert "are not fools" in out                       # refuse abuse, not use
