"""A3 — the NCS pre-registered falsification rubric, made runnable (2026-10-06).

The keystone `card_k_ncs_validation` records a FROZEN, pre-registered falsification program for the
nested-control-systems framework against NHANES 2011-2018: three hypotheses, each with explicit falsifiers
set BEFORE the data are touched, and a three-outcome rubric (SUPPORTED / FALSIFIED / INCONCLUSIVE) that
forbids self-declaration.

This module turns that prose protocol into a deterministic DECISION FUNCTION. Feed it the statistical
results and it applies the frozen falsifiers mechanically — the verdict the protocol is forbidden to
declare by hand. It FABRICATES NOTHING: with no results every hypothesis is AWAITING_EXECUTION and the
program's status stays "pre-registered, not executed". A hypothesis is SUPPORTED only if it clears its
bar AND survives its stability and sensitivity suites — never on the primary result alone.

This is research validation of a framework. It is not medical advice, not a diagnosis, and renders no
verdict about any person.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

AWAITING = "AWAITING_EXECUTION"
SUPPORTED = "SUPPORTED"
FALSIFIED = "FALSIFIED"
INCONCLUSIVE = "INCONCLUSIVE"

STATUS = "pre-registered protocol, frozen 2026-03-04 — NOT yet executed; no verdict is claimed"

# The frozen criteria, verbatim from the keystone (operational definitions pinned to NHANES variables).
PROTOCOL = {
    "H1": {"prediction": "the upstream manifold predicts 10-year mortality",
           "falsifier": "AUC < 0.60 OR dAUC <= 0 vs age+sex",
           "support_bar": "AUC >= 0.60 AND dAUC > 0, surviving stability + sensitivity"},
    "H2": {"prediction": "hyperglycemia is mechanistically heterogeneous (clusters)",
           "falsifier": "best_k < 2 OR medication chi^2 p > 0.05 OR bootstrap ARI < 0.40",
           "support_bar": "best_k >= 2 AND p <= 0.05 AND ARI >= 0.40, surviving stability + sensitivity"},
    "H3": {"prediction": "Layer 5 (systemic) adds predictive lift for diabetes",
           "falsifier": "dAUC_L5 < 0.015 pooled OR negative in any adequately-powered cycle",
           "support_bar": "dAUC_L5 >= 0.02 (clinical bar) AND no powered-cycle negative, surviving suites"},
}


def _suites_ok(r: Dict[str, Any]) -> bool:
    """SUPPORTED is never self-declared on the primary alone — the stability and sensitivity suites must pass."""
    return bool(r.get("stability_ok")) and bool(r.get("sensitivity_ok"))


def evaluate_h1(r: Optional[Dict[str, Any]]) -> str:
    if not r or r.get("auc") is None or r.get("delta_auc_vs_agesex") is None:
        return AWAITING
    auc = float(r["auc"]); d = float(r["delta_auc_vs_agesex"])
    if auc < 0.60 or d <= 0:
        return FALSIFIED
    return SUPPORTED if _suites_ok(r) else INCONCLUSIVE


def evaluate_h2(r: Optional[Dict[str, Any]]) -> str:
    if not r or any(r.get(k) is None for k in ("best_k", "medication_chi2_p", "bootstrap_ari")):
        return AWAITING
    k = int(r["best_k"]); p = float(r["medication_chi2_p"]); ari = float(r["bootstrap_ari"])
    if k < 2 or p > 0.05 or ari < 0.40:
        return FALSIFIED
    return SUPPORTED if _suites_ok(r) else INCONCLUSIVE


def evaluate_h3(r: Optional[Dict[str, Any]]) -> str:
    if not r or r.get("delta_auc_l5_pooled") is None:
        return AWAITING
    pooled = float(r["delta_auc_l5_pooled"])
    any_negative = bool(r.get("any_powered_cycle_negative"))
    if pooled < 0.015 or any_negative:
        return FALSIFIED
    if pooled < 0.02:               # cleared the falsifier floor but below the clinical bar
        return INCONCLUSIVE
    return SUPPORTED if _suites_ok(r) else INCONCLUSIVE


def verdict(results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Apply the frozen rubric to results {'H1':{...},'H2':{...},'H3':{...}} (or None -> all awaiting).

    Returns a per-hypothesis verdict and the program status. Deterministic; renders only what the results
    earn, never a self-declared SUPPORTED, never a fabricated number.
    """
    results = results or {}
    per = {"H1": evaluate_h1(results.get("H1")),
           "H2": evaluate_h2(results.get("H2")),
           "H3": evaluate_h3(results.get("H3"))}
    executed = any(v != AWAITING for v in per.values())
    return {
        "status": STATUS if not executed else "executed (partial)" if AWAITING in per.values() else "executed",
        "protocol": PROTOCOL,
        "verdicts": per,
        "note": ("the rubric is wired; the data is not. Feed real NHANES-derived statistics to render a "
                 "verdict. No hypothesis is SUPPORTED without its stability and sensitivity suites. This "
                 "validates a framework; it is not medical advice."),
    }


def protocol() -> Dict[str, Any]:
    """The frozen pre-registered protocol, machine-readable, with no verdict."""
    return {"status": STATUS, "protocol": PROTOCOL,
            "data_source": "NHANES 2011-2018 (molecular L1 claims need UK Biobank Olink — honest next step)"}
