"""Measurement-consistency verifier — do independent determinations of one quantity agree?

This is the check that turns "the witnesses agree" into a deterministic verdict: given a set
of value +/- sigma measurements of the SAME quantity, recompute the inverse-variance weighted
mean, the Birge ratio, and the worst pairwise sigma-tension, and verify a stated claim about
the set. It judges the internal agreement of the reported numbers only — never whether a
measured value is correct.

The worked example is the fine structure constant: three independent modern determinations
that agree to nine significant figures yet are over-dispersed at one sigma (the real Rb-Cs
recoil tension). The engine should confirm the tension and refuse to call the raw set
"consistent."

Runnable with pytest OR `python tests/test_measurement_consistency.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import statistics as S  # noqa: E402

# Three independent determinations of the inverse fine structure constant (published values).
ALPHA_INV = [
    {"label": "Cs-133 recoil", "value": 137.035999046, "sigma": 0.000000027},  # Berkeley 2018
    {"label": "electron g-2", "value": 137.035999166, "sigma": 0.000000015},   # Northwestern 2023
    {"label": "Rb-87 recoil", "value": 137.035999206, "sigma": 0.000000011},   # LKB 2020
]


def _run(spec):
    return S.verify_measurement_consistency(spec)


def test_alpha_set_is_overdispersed_not_consistent():
    r = _run({"quantity": "inverse fine structure constant", "measurements": ALPHA_INV})
    assert r.status == "MISMATCH", r
    d = r.data
    # weighted mean lands near the CODATA value (137.035999177)
    assert abs(d["weighted_mean"] - 137.035999178) < 5e-9
    # Birge ratio ~3.9 (over-dispersed: > 1)
    assert 3.7 < d["birge_ratio"] < 4.1, d["birge_ratio"]
    # worst pairwise tension is Rb vs Cs at ~5.5 sigma
    assert 5.3 < d["max_tension_sigma"] < 5.7, d["max_tension_sigma"]
    assert set(d["worst_pair"]) == {"Rb-87 recoil", "Cs-133 recoil"}
    assert d["dof"] == 2


def test_alpha_tension_is_confirmed_as_discordant():
    r = _run({"measurements": ALPHA_INV, "claim": "discordant"})
    assert r.status == "CONFIRMED", r
    assert "5.4" in r.detail or "5.5" in r.detail  # the ~5.5 sigma tension


def test_alpha_agrees_to_relative_1e8_but_not_1e10():
    ok = _run({"measurements": ALPHA_INV, "claim": "agree_to_relative", "rel_level": 1e-8})
    assert ok.status == "CONFIRMED", ok
    # they agree to ~1.2e-9 relative, so a 1e-10 claim must fail
    tight = _run({"measurements": ALPHA_INV, "claim": "agree_to_relative", "rel_level": 1e-10})
    assert tight.status == "MISMATCH", tight


def test_locate_names_the_suspect_scale_factor_and_correction():
    r = _run({"measurements": ALPHA_INV, "claim": "discordant"})
    assert r.status == "CONFIRMED", r
    d = r.data
    # PDG scale factor == Birge ratio when over-dispersed
    assert abs(d["scale_factor"] - d["birge_ratio"]) < 1e-9
    assert 3.7 < d["scale_factor"] < 4.1
    # prime suspect = largest chi-square contributor = the Cs outlier
    assert d["prime_suspect"] == "Cs-133 recoil"
    # leave-one-out locates Cs: removing it reconciles the set to <= 3 sigma
    assert d["located"] == "Cs-133 recoil"
    loo = {x["removed"]: x["worst_tension_without"] for x in d["leave_one_out"]}
    assert loo["Cs-133 recoil"] <= 3.0 and loo["Rb-87 recoil"] > 3.0
    # the correction: adjusted consensus inflates sigma by the scale factor
    assert abs(d["adjusted_consensus"]["sigma"] - d["sigma_weighted_mean"] * d["scale_factor"]) < 1e-18
    # size of the systematic to find in the suspect
    assert d["systematic_estimate"]["label"] == "Cs-133 recoil"
    assert d["systematic_estimate"]["deviation_sigma"] > 4.0
    # the verdict text names the suspect and the correction
    assert "prime suspect" in r.detail and "Cs-133 recoil" in r.detail and "reconciles" in r.detail


def test_a_genuinely_consistent_set_confirms():
    ms = [
        {"label": "a", "value": 10.00, "sigma": 0.05},
        {"label": "b", "value": 10.03, "sigma": 0.05},
        {"label": "c", "value": 9.98, "sigma": 0.05},
    ]
    r = _run({"measurements": ms})  # default claim = consistent
    assert r.status == "CONFIRMED", r
    assert r.data["max_tension_sigma"] < 3.0
    assert r.data["birge_ratio"] <= 1.5


def test_caller_cannot_loosen_the_threshold_to_force_consistency():
    # An adversarial caller widens the tolerance to try to force CONFIRMED; clamp_tol caps it.
    r = _run({"measurements": ALPHA_INV, "claim": "consistent", "max_tension_sigma": 100.0})
    assert r.status == "MISMATCH", r
    assert r.data["tension_threshold"] <= 3.0


def test_malformed_inputs_error_not_confirm():
    assert _run({"measurements": [{"value": 1.0, "sigma": 0.0}, {"value": 1.1, "sigma": 0.1}]}).status == "ERROR"
    assert _run({"measurements": [{"value": 1.0, "sigma": 0.1}]}).status == "ERROR"  # need >= 2
    assert _run({"measurements": [{"value": 1.0}, {"value": 2.0, "sigma": 0.1}]}).status == "ERROR"
    bad_claim = _run({"measurements": ALPHA_INV, "claim": "please_just_pass"})
    assert bad_claim.status == "ERROR"


def test_run_routes_the_artifact_and_stays_quiet_when_absent():
    # present -> the check fires
    res = S.run({"CONCORDANCE_VERIFY": {"measurements": ALPHA_INV, "claim": "discordant"}})
    assert any(x.name == "statistics.measurement_consistency" and x.status == "CONFIRMED" for x in res), res
    # absent -> non-empty, all NOT_APPLICABLE (the present-vs-null invariant)
    empty = S.run({})
    assert empty and all(x.status == "NOT_APPLICABLE" for x in empty), empty
    # unrelated artifact -> never CONFIRMED/MISMATCH
    unrel = S.run({"TOTALLY_UNRELATED_XYZ": {"measurements": ALPHA_INV}})
    assert not any(x.status in ("CONFIRMED", "MISMATCH") for x in unrel), unrel


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} measurement-consistency tests passed.")
