"""Lock-in tests for the code-review fixes (2026-08-06). Each pins a real defect the review found
and I fixed, so it cannot regress. See docs review batch: energy losses (P0), derivation
error/gap-dependency cascade (P0), calendar tz-resolution (P1). Runnable with pytest OR
`python tests/test_review_fixes.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from concordance.verifiers import energy, calendar_time  # noqa: E402
from concordance import derivation  # noqa: E402


def test_energy_power_balance_uses_losses_both_directions():
    """P0: `losses_kwh_day` is a DATA value, not a tolerance. It was run through clamp_tol (default
    0.0), which returned min(abs(losses), 0.0) == 0.0 for every input — so the losses term was
    silently discarded, producing BOTH a false BROKEN (on true claims) and a false HOLDS."""
    # 12 - 8.5 - 1.5 = 2.0 — TRUE. (The old bug computed 12 - 8.5 - 0 = 3.5 and returned MISMATCH.)
    r = energy.verify_power_balance({"generation_kwh_day": 12.0, "consumption_kwh_day": 8.5,
                                     "losses_kwh_day": 1.5, "claimed_balance_kwh_day": 2.0})
    assert r.status == "CONFIRMED", (r.status, r.detail)
    # And it must NOT confirm the value you'd get if losses were ignored — the false-HOLDS guard.
    r2 = energy.verify_power_balance({"generation_kwh_day": 12.0, "consumption_kwh_day": 8.5,
                                      "losses_kwh_day": 1.5, "claimed_balance_kwh_day": 3.5})
    assert r2.status == "MISMATCH", (r2.status, r2.detail)


def test_derivation_error_or_gap_dependency_is_never_rendered_broken():
    """P0: a step confirmed in isolation but building on a prior that our engine could not check
    (ERROR) or had no verifier for (NOT_APPLICABLE / a gap) was falling through to BROKEN — our
    own failure downgraded into a falsehood about the caller's claim. Only a genuine MISMATCH may
    propagate a break."""
    math_step = {"id": "b", "domain": "mathematics", "uses": ["a"],
                 "spec": {"mode": "equality",
                          "params": {"expr_a": "x + x", "expr_b": "2*x", "variables": ["x"]}}}
    # Sanity: the math step genuinely CONFIRMS on its own (so the verdict below is about the
    # dependency handling, not about this step failing).
    solo = derivation.verify_derivation([{k: v for k, v in math_step.items() if k != "uses"}])
    assert solo["verdict"] == "HOLDS", solo
    # It builds on step 'a', a domain with no verifier — a gap (or, if the router raises, our
    # ERROR). Either way the whole derivation must NOT be BROKEN.
    gap_step = {"id": "a", "domain": "__no_such_domain__", "spec": {}}
    out = derivation.verify_derivation([gap_step, math_step])
    assert out["verdict"] != "BROKEN", out
    assert out["verdict"] in ("INCOMPLETE", "SYSTEM_ERROR"), out


def test_calendar_unresolvable_timezone_is_cannot_check_not_mismatch():
    """P1: a zone that cannot be resolved here (the IANA tz db is absent — the Windows default
    without `tzdata` — or the name is unknown) was sealed as MISMATCH (a false BROKEN) and made
    the verdict machine-dependent. Our gap must be NOT_APPLICABLE, never a verdict."""
    r = calendar_time.verify_utc_offset({"timezone": "Not/AZone",
                                         "at_iso": "2026-01-01T00:00:00",
                                         "claimed_utc_offset_hours": -5})
    assert r.status == "NOT_APPLICABLE", (r.status, r.detail)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} review-fix lock-in tests passed.")
