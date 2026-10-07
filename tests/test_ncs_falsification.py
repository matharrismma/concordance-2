"""A3 — pin the NCS falsification rubric (2026-10-06). The frozen H1/H2/H3 falsifiers, applied
deterministically to synthetic statistics (NO real NHANES data). Proves: a result below the falsifier is
FALSIFIED; a result that clears its bar AND its suites is SUPPORTED; a result between floor and clinical
bar (or missing a suite) is INCONCLUSIVE; and with no results everything is AWAITING_EXECUTION (never a
self-declared verdict, never a fabricated number)."""
from __future__ import annotations

from concordance import ncs_falsification as NF


def test_no_results_is_awaiting():
    v = NF.verdict(None)
    assert v["verdicts"] == {"H1": NF.AWAITING, "H2": NF.AWAITING, "H3": NF.AWAITING}
    assert "not yet executed" in v["status"].lower() or "NOT yet executed" in NF.STATUS


def test_h1_falsified_and_supported():
    assert NF.evaluate_h1({"auc": 0.55, "delta_auc_vs_agesex": 0.03}) == NF.FALSIFIED          # AUC < 0.60
    assert NF.evaluate_h1({"auc": 0.70, "delta_auc_vs_agesex": 0.0}) == NF.FALSIFIED            # no lift
    assert NF.evaluate_h1({"auc": 0.70, "delta_auc_vs_agesex": 0.05,
                           "stability_ok": True, "sensitivity_ok": True}) == NF.SUPPORTED
    assert NF.evaluate_h1({"auc": 0.70, "delta_auc_vs_agesex": 0.05,
                           "stability_ok": False, "sensitivity_ok": True}) == NF.INCONCLUSIVE  # suite failed


def test_h2_thresholds():
    assert NF.evaluate_h2({"best_k": 1, "medication_chi2_p": 0.01, "bootstrap_ari": 0.5}) == NF.FALSIFIED
    assert NF.evaluate_h2({"best_k": 3, "medication_chi2_p": 0.20, "bootstrap_ari": 0.5}) == NF.FALSIFIED  # p too high
    assert NF.evaluate_h2({"best_k": 3, "medication_chi2_p": 0.01, "bootstrap_ari": 0.30}) == NF.FALSIFIED  # ARI low
    assert NF.evaluate_h2({"best_k": 3, "medication_chi2_p": 0.01, "bootstrap_ari": 0.5,
                           "stability_ok": True, "sensitivity_ok": True}) == NF.SUPPORTED


def test_h3_clinical_bar_band():
    assert NF.evaluate_h3({"delta_auc_l5_pooled": 0.01}) == NF.FALSIFIED                        # below floor
    assert NF.evaluate_h3({"delta_auc_l5_pooled": 0.03, "any_powered_cycle_negative": True}) == NF.FALSIFIED
    assert NF.evaluate_h3({"delta_auc_l5_pooled": 0.017}) == NF.INCONCLUSIVE                    # floor<x<bar
    assert NF.evaluate_h3({"delta_auc_l5_pooled": 0.025,
                           "stability_ok": True, "sensitivity_ok": True}) == NF.SUPPORTED


def test_protocol_is_machine_readable_and_unexecuted():
    p = NF.protocol()
    assert set(p["protocol"].keys()) == {"H1", "H2", "H3"}
    assert "NOT yet executed" in p["status"]
