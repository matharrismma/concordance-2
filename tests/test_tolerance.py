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
    FP-widening hole reopens. Scans the verifier sources; fails on any unclamped read."""
    import re
    from pathlib import Path
    vdir = Path(__file__).resolve().parent.parent / "src" / "concordance" / "verifiers"
    pat = re.compile(r'spec\.get\("([^"]*(?:tolerance|_tol|rtol|atol|rel_tol|abs_tol)[^"]*)"')
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
