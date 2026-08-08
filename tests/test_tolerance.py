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


def test_every_scalar_tolerance_read_goes_through_clamp_tol():
    """No verifier may read a caller tolerance without clamping it — otherwise the
    FP-widening hole reopens. Scans the verifier sources; fails on any unclamped read.

    The receiver is unanchored on purpose: an earlier form matched only `spec.get(...)` and
    silently missed tolerances pulled from a sub-dict (`pv.get(...)` in physics, `dr.get(...)`
    in biology) — the exact reads that reopened the hole. Any `.get("...tol...")` is scanned now."""
    import re
    from pathlib import Path
    vdir = Path(__file__).resolve().parent.parent / "src" / "concordance" / "verifiers"
    pat = re.compile(r'\.get\("([^"]*(?:tolerance|_tol|rtol|atol|rel_tol|abs_tol)[^"]*)"')
    bad = []
    for f in sorted(vdir.glob("*.py")):
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            m = pat.search(line)
            if not m:
                continue
            if m.group(1) == "tolerances":   # a list of inputs to combine, not a match-window
                continue
            if "clamp_tol(" in line:          # already clamped
                continue
            bad.append(f"{f.name}:{n}: {line.strip()}")
    assert not bad, "unclamped caller tolerance reads:\n" + "\n".join(bad)


def test_physics_conservation_ignores_adversarial_wide_tolerance():
    """A packet claiming energy is conserved while it drops 100 -> 5 must MISMATCH even when the
    caller widens tolerance_relative/absolute — the driver clamps both to the verifier default."""
    from concordance.verifiers import physics
    pkt = {"PHYS_VERIFY": {"before": {"E": 100.0}, "after": {"E": 5.0},
                           "tolerance_relative": 1e9, "tolerance_absolute": 1e9}}
    statuses = {r.status for r in physics.run(pkt)}
    assert "MISMATCH" in statuses, "a widened tolerance forced a false CONFIRMED on non-conservation"
    # a genuinely conserved quantity still confirms (the clamp tightens, it does not break truth)
    ok_pkt = {"PHYS_VERIFY": {"before": {"E": 100.0}, "after": {"E": 100.0}}}
    assert {r.status for r in physics.run(ok_pkt)} == {"CONFIRMED"}


def test_biology_dose_response_ignores_adversarial_wide_tolerance():
    """A clear sign-reversal (1 -> 5 -> 2, declared increasing) must MISMATCH even when the caller
    passes a huge tolerance meant to classify every step as 'flat' and hide the reversal."""
    from concordance.verifiers import biology
    spec = {"dose_response": {"doses": [1, 2, 3], "responses": [1.0, 5.0, 2.0],
                              "expected_direction": "increasing", "tolerance": 1e9}}
    assert biology.verify_dose_response_monotonicity(spec).status == "MISMATCH"
