"""The null assay, kept as a gate — a claim that outruns its evidence must fail loudly.

Matt, 2026-07-28: "You will review all theories and find the ones that do not align."

The assay found one unbacked claim (agriculture said `seals`; no sealed run in the whole
keeping exercised it) and it was corrected to `partial`. This test makes the finding
permanent: from here on, ANY theory card claiming `seals` without a verifier, or without a
real sealed run behind it, fails the gate. Drift in the other direction — a verifier that
raises or answers nothing — fails too.

The assay's own honesty is pinned as well: a `map-only` card must NOT be reported as a finding
merely because a verifier exists in its domain. That error (the first draft's, which produced
nine false findings) would make the instrument lie in the safe direction, which is still lying.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402


def _assay():
    import null_assay
    return null_assay.ring_a()


def test_no_theory_claims_more_than_the_engine_can_show():
    rows, findings = _assay()
    if not rows:
        pytest.skip("theory cards not present on this machine (data, not tracked)")
    bad = [f for f in findings if f["verdict"] in ("OVER_CLAIM", "UNPROVEN_CLAIM", "MISALIGNED")]
    assert not bad, "claims that outrun their evidence: " + "; ".join(
        f"{f['title']} [{f['verdict']}] claim={f['claim']} domain={f['domain']} "
        f"sealed_runs={f['sealed_runs']}" for f in bad)


def test_every_verifier_a_theory_names_actually_loads_and_behaves():
    rows, _ = _assay()
    if not rows:
        pytest.skip("theory cards not present on this machine")
    broken = [r for r in rows if r["engine"] in ("RAISES", "SILENT", "NO_VERIFIER")]
    assert not broken, "a theory card points at a domain the engine cannot honour: " + "; ".join(
        f"{r['title']} -> {r['domain']} ({r['engine']}: {r['detail']})" for r in broken)


def test_map_only_cards_are_not_reported_as_findings_for_existing_verifiers():
    """The instrument must not manufacture findings. A theory carded `map-only` claims no seal;
    the presence of a verifier in that domain (biology verifies Punnett squares) says nothing
    about sealing the theory (Darwinian evolution) and must never be flagged."""
    rows, findings = _assay()
    if not rows:
        pytest.skip("theory cards not present on this machine")
    map_only = [r for r in rows if r["claim"] == "map-only"]
    assert map_only, "the catalog must keep honest map-only entries"
    flagged = [f for f in findings if f["claim"] == "map-only" and f["engine"] == "VERIFIER_OK"]
    assert not flagged, ("map-only cards flagged only because a verifier exists: "
                         + ", ".join(f["title"] for f in flagged))


def test_the_assay_runs_as_a_tool_and_reports_honestly():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "null_assay.py")],
                       capture_output=True, text=True, cwd=str(ROOT),
                       env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")})
    assert r.returncode == 0, r.stderr[-400:]
    out = r.stdout
    assert "COULD_NOT_CHECK" in out, "the third state is always shown — our failure is not their falsehood"
    assert "ALIGNED" in out and "OVER_CLAIM" in out


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
