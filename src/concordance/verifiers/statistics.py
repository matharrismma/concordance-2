"""Statistics verifier.

Checks performed:
  * pvalue_calibration: given (test, n, statistic, df, claimed_p), recompute
    p from the test distribution and verify within tolerance
  * pvalue_significance_consistency: if the packet claims significance at
    alpha, verify p <= alpha; if it claims non-significance, verify p > alpha
  * effect_size_required: if p <= alpha, an effect size must be reported
  * multiple_comparisons: given k tests with raw p-values and a stated
    correction method (bonferroni, bh), recompute corrected p-values and
    verify the rejection set matches the claim
  * confidence_interval_coverage: given (estimate, ci_low, ci_high, alpha),
    verify the interval is symmetric (or shape-correct) and contains the
    estimate
  * measurement_consistency: given several INDEPENDENT determinations of one
    quantity (value +/- sigma), recompute the inverse-variance weighted mean,
    the Birge ratio, and the worst pairwise sigma-tension, and verify a stated
    claim about the set (consistent / discordant / agree_to_relative)

Recomputed test statistics for two_sample_t are derived from the supplied
(n1, n2, mean1, mean2, sd1, sd2) using Welch's formula.
"""
from __future__ import annotations
from typing import Any, Dict, List
import math

from .base import VerifierResult, na, confirm, mismatch, error, clamp_tol

# numpy + scipy.stats are heavy imports (scipy.stats ~1.5s). They load on
# first use (via _ensure_stats) so the engine's cold start stays fast.
np = scistats = None
_stats_loaded = False


def _ensure_stats() -> None:
    """Import numpy + scipy.stats on first use. Idempotent."""
    global np, scistats, _stats_loaded
    if _stats_loaded:
        return
    import numpy as _np
    from scipy import stats as _scistats
    np, scistats = _np, _scistats
    _stats_loaded = True


# Aliases accepted for the `tail` parameter. The canonical values returned
# by _normalize_tail are exactly: "two-sided", "greater", "less".
_TAIL_TWO_SIDED = frozenset({"two-sided", "two_sided", "twosided", "two", "both", "2", "!="})
_TAIL_GREATER = frozenset({"greater", "right", "right-tailed", "upper", "upper-tailed", ">"})
_TAIL_LESS = frozenset({"less", "left", "left-tailed", "lower", "lower-tailed", "<"})


def _normalize_tail(t):
    """Return canonical tail name. Defaults to two-sided if t is None."""
    if t is None:
        return "two-sided"
    s = str(t).lower().strip()
    if s in _TAIL_TWO_SIDED:
        return "two-sided"
    if s in _TAIL_GREATER:
        return "greater"
    if s in _TAIL_LESS:
        return "less"
    raise ValueError(
        f"unknown tail spec {t!r}; "
        f"use one of: two-sided/two/both, greater/right, less/left"
    )


def verify_pvalue_calibration(spec: Dict[str, Any]) -> VerifierResult:
    """Recompute p-value from supplied test inputs and verify the claim."""
    _ensure_stats()
    test = spec.get("test", "").lower()
    claimed_p = spec.get("claimed_p")
    # Default tolerance raised from 1e-3 to 5e-3: published p-values are typically
    # rounded to 2-3 decimal places, so a 0.001 window rejects legitimate claims
    # whose reported p differs from the recomputed p only by rounding.
    tol = clamp_tol(spec, "tolerance", 5e-3)

    try:
        if test in ("two_sample_t", "welch_t"):
            n1, n2 = spec["n1"], spec["n2"]
            m1, m2 = spec["mean1"], spec["mean2"]
            s1, s2 = spec["sd1"], spec["sd2"]
            tail = _normalize_tail(spec.get("tail"))
            se = math.sqrt(s1 ** 2 / n1 + s2 ** 2 / n2)
            t = (m1 - m2) / se
            df = (s1 ** 2 / n1 + s2 ** 2 / n2) ** 2 / (
                (s1 ** 2 / n1) ** 2 / (n1 - 1) + (s2 ** 2 / n2) ** 2 / (n2 - 1)
            )
            if tail == "two-sided":
                p = 2 * scistats.t.sf(abs(t), df)
            elif tail == "greater":
                p = scistats.t.sf(t, df)
            else:  # "less"
                p = scistats.t.cdf(t, df)
            data = {"recomputed_t": t, "df": df, "recomputed_p": p, "tail": tail}

        elif test == "one_sample_t":
            n = spec["n"]
            m = spec["mean"]
            s = spec["sd"]
            mu0 = spec.get("mu0", 0.0)
            tail = _normalize_tail(spec.get("tail"))
            t = (m - mu0) / (s / math.sqrt(n))
            df = n - 1
            if tail == "two-sided":
                p = 2 * scistats.t.sf(abs(t), df)
            elif tail == "greater":
                p = scistats.t.sf(t, df)
            else:  # "less"
                p = scistats.t.cdf(t, df)
            data = {"recomputed_t": t, "df": df, "recomputed_p": p, "tail": tail}

        elif test == "z":
            z = spec["z"]
            tail = _normalize_tail(spec.get("tail"))
            if tail == "two-sided":
                p = 2 * scistats.norm.sf(abs(z))
            elif tail == "greater":
                p = scistats.norm.sf(z)
            else:  # "less"
                p = scistats.norm.cdf(z)
            data = {"recomputed_z": z, "recomputed_p": p, "tail": tail}

        elif test == "chi2":
            stat = spec["statistic"]
            df = spec["df"]
            p = scistats.chi2.sf(stat, df)
            data = {"recomputed_stat": stat, "df": df, "recomputed_p": p}

        elif test == "f":
            stat = spec["statistic"]
            df1 = spec["df1"]
            df2 = spec["df2"]
            p = scistats.f.sf(stat, df1, df2)
            data = {"recomputed_stat": stat, "df1": df1, "df2": df2, "recomputed_p": p}

        elif test == "paired_t":
            # Either supply (mean_diff, sd_diff, n) or supply (paired1, paired2)
            tail = _normalize_tail(spec.get("tail"))
            if "mean_diff" in spec:
                n = spec["n"]
                d = spec["mean_diff"]
                sd = spec["sd_diff"]
            else:
                a = np.asarray(spec["paired1"], dtype=float)
                b = np.asarray(spec["paired2"], dtype=float)
                if a.shape != b.shape:
                    raise ValueError("paired1 and paired2 must be same length")
                diffs = a - b
                n = len(diffs)
                d = float(np.mean(diffs))
                sd = float(np.std(diffs, ddof=1))
            t = d / (sd / math.sqrt(n))
            df = n - 1
            if tail == "two-sided":
                p = 2 * scistats.t.sf(abs(t), df)
            elif tail == "greater":
                p = scistats.t.sf(t, df)
            else:
                p = scistats.t.cdf(t, df)
            data = {"recomputed_t": t, "df": df, "recomputed_p": p, "tail": tail}

        elif test == "one_proportion_z":
            n = spec["n"]
            x = spec.get("successes")
            phat = (x / n) if x is not None else spec["phat"]
            p0 = spec["p0"]
            tail = _normalize_tail(spec.get("tail"))
            se = math.sqrt(p0 * (1 - p0) / n)
            z = (phat - p0) / se
            if tail == "two-sided":
                p = 2 * scistats.norm.sf(abs(z))
            elif tail == "greater":
                p = scistats.norm.sf(z)
            else:
                p = scistats.norm.cdf(z)
            data = {"recomputed_z": z, "recomputed_p": p, "tail": tail}

        elif test == "two_proportion_z":
            n1, n2 = spec["n1"], spec["n2"]
            x1 = spec.get("successes1"); x2 = spec.get("successes2")
            p1 = (x1 / n1) if x1 is not None else spec["phat1"]
            p2 = (x2 / n2) if x2 is not None else spec["phat2"]
            ppool = ((x1 if x1 is not None else p1 * n1) + (x2 if x2 is not None else p2 * n2)) / (n1 + n2)
            se = math.sqrt(ppool * (1 - ppool) * (1 / n1 + 1 / n2))
            z = (p1 - p2) / se
            tail = _normalize_tail(spec.get("tail"))
            if tail == "two-sided":
                p = 2 * scistats.norm.sf(abs(z))
            elif tail == "greater":
                p = scistats.norm.sf(z)
            else:
                p = scistats.norm.cdf(z)
            data = {"recomputed_z": z, "recomputed_p": p, "tail": tail}

        elif test == "fisher_exact":
            table = spec["table"]  # 2x2
            tail_raw = spec.get("tail")
            tail = _normalize_tail(tail_raw)
            alt = {"two-sided": "two-sided", "greater": "greater", "less": "less"}[tail]
            res = scistats.fisher_exact(table, alternative=alt)
            # scipy >= 1.10 returns SignificanceResult; older returns tuple
            if hasattr(res, "pvalue"):
                p = float(res.pvalue); odds = float(res.statistic)
            else:
                odds, p = float(res[0]), float(res[1])
            data = {"odds_ratio": odds, "recomputed_p": p, "tail": tail}

        elif test == "mannwhitney":
            x = spec["x"]; y = spec["y"]
            tail = _normalize_tail(spec.get("tail"))
            alt = {"two-sided": "two-sided", "greater": "greater", "less": "less"}[tail]
            res = scistats.mannwhitneyu(x, y, alternative=alt)
            p = float(res.pvalue); u = float(res.statistic)
            data = {"U": u, "recomputed_p": p, "tail": tail}

        elif test in ("wilcoxon_signed_rank", "wilcoxon"):
            tail = _normalize_tail(spec.get("tail"))
            alt = {"two-sided": "two-sided", "greater": "greater", "less": "less"}[tail]
            if "x" in spec and "y" in spec:
                res = scistats.wilcoxon(spec["x"], spec["y"], alternative=alt)
            else:
                res = scistats.wilcoxon(spec["d"], alternative=alt)
            p = float(res.pvalue); w = float(res.statistic)
            data = {"W": w, "recomputed_p": p, "tail": tail}

        elif test == "regression_coefficient_t":
            beta = spec["beta"]
            se = spec["se"]
            n = spec["n"]
            k = spec.get("k", 1)  # number of predictors (excluding intercept)
            tail = _normalize_tail(spec.get("tail"))
            t = beta / se
            df = n - k - 1
            if tail == "two-sided":
                p = 2 * scistats.t.sf(abs(t), df)
            elif tail == "greater":
                p = scistats.t.sf(t, df)
            else:
                p = scistats.t.cdf(t, df)
            data = {"recomputed_t": t, "df": df, "recomputed_p": p, "tail": tail}

        else:
            return error("statistics.pvalue_calibration", f"unknown test {test!r}")

    except KeyError as e:
        return error("statistics.pvalue_calibration", f"missing field: {e}")
    except Exception as e:
        return error("statistics.pvalue_calibration", f"computation failure: {e}")

    if claimed_p is None:
        return confirm("statistics.pvalue_calibration",
                       f"recomputed p={p:.6g} (no claimed_p to compare)", data)

    diff = abs(p - claimed_p)
    # Ratio check (relative agreement) supplements the absolute tolerance.
    # Without it, the 5e-3 absolute window accepts cases like claimed=0.0014
    # vs recomputed=0.0028 (wrong_tail: ratio=2.0) or claimed=0.001379 vs
    # recomputed=0.000276 (wrong_p_value: ratio=5.0) — the diffs are tiny in
    # absolute terms but the inferential errors are large. A ratio threshold
    # of 1.5 catches wrong_tail (ratio=2 exactly) while still allowing
    # published rounding (typically ratio<1.2). Both p-values must be above a
    # floor (1e-6) for the ratio check to apply — below that, scipy's
    # underflow can pin one side to 0 and the ratio loses meaning.
    ratio_threshold = float(spec.get("ratio_threshold", 1.5))
    p_floor = 1e-6
    if p > p_floor and claimed_p > p_floor:
        ratio = max(p, claimed_p) / min(p, claimed_p)
        ratio_ok = ratio <= ratio_threshold
    else:
        ratio = 1.0
        ratio_ok = True
    if diff <= tol and ratio_ok:
        return confirm("statistics.pvalue_calibration",
                       f"claimed p={claimed_p}, recomputed p={p:.6g} "
                       f"(diff {diff:.2e}, ratio {ratio:.2f})", data)
    failures = []
    if diff > tol:
        failures.append(f"diff {diff:.2e} > tol {tol}")
    if not ratio_ok:
        failures.append(f"ratio {ratio:.2f} > {ratio_threshold}")
    return mismatch("statistics.pvalue_calibration",
                    f"claimed p={claimed_p}, recomputed p={p:.6g}: " + "; ".join(failures),
                    data)


def verify_significance_consistency(spec: Dict[str, Any]) -> VerifierResult:
    """If author claims 'significant', verify p <= alpha. Same for 'not significant'."""
    p = spec.get("p_value")
    alpha = spec.get("alpha", 0.05)
    claimed_significance = spec.get("claimed_significance")  # "significant" or "not_significant"
    if p is None or claimed_significance is None:
        return na("statistics.significance_consistency")
    is_sig = p <= alpha
    if claimed_significance.lower() in ("significant", "sig", "yes", "true"):
        if is_sig:
            return confirm("statistics.significance_consistency",
                           f"p={p} <= alpha={alpha}, claim of significance is consistent")
        return mismatch("statistics.significance_consistency",
                        f"claimed significant but p={p} > alpha={alpha}")
    else:
        if not is_sig:
            return confirm("statistics.significance_consistency",
                           f"p={p} > alpha={alpha}, claim of non-significance is consistent")
        return mismatch("statistics.significance_consistency",
                        f"claimed non-significant but p={p} <= alpha={alpha}")


def verify_effect_size_present(spec: Dict[str, Any]) -> VerifierResult:
    p = spec.get("p_value")
    alpha = spec.get("alpha", 0.05)
    if p is None:
        return na("statistics.effect_size_present")
    has_effect = (
        spec.get("effect_size") is not None
        or spec.get("effect_size_type") is not None
    )
    has_ci = spec.get("confidence_interval") is not None
    if p <= alpha and not has_effect:
        return mismatch(
            "statistics.effect_size_present",
            f"significant result (p={p} <= alpha={alpha}) without effect_size",
        )
    if has_effect and not has_ci:
        return mismatch(
            "statistics.effect_size_present",
            "effect_size reported without a confidence_interval",
        )
    return confirm("statistics.effect_size_present", "effect size reporting consistent")


def verify_multiple_comparisons(spec: Dict[str, Any]) -> VerifierResult:
    """Given raw p-values and a correction method, recompute and verify."""
    _ensure_stats()
    raw_p = spec.get("raw_p_values")
    method = (spec.get("method") or "").lower()
    alpha = spec.get("alpha", 0.05)
    claimed_rejected = spec.get("claimed_rejected_indices")  # optional
    if not raw_p:
        return na("statistics.multiple_comparisons")
    p = np.asarray(raw_p, dtype=float)
    k = len(p)
    if method in ("bonferroni", "bonf"):
        adj = np.minimum(p * k, 1.0)
    elif method in ("bh", "benjamini-hochberg", "fdr"):
        order = np.argsort(p)
        ranks = np.empty(k, dtype=int)
        ranks[order] = np.arange(1, k + 1)
        adj_sorted = (p[order] * k / ranks[order]).astype(float)
        # enforce monotonicity
        for i in range(k - 2, -1, -1):
            adj_sorted[i] = min(adj_sorted[i], adj_sorted[i + 1])
        adj = np.empty(k, dtype=float)
        adj[order] = np.minimum(adj_sorted, 1.0)
    else:
        return error("statistics.multiple_comparisons", f"unknown method {method!r}")

    rejected = sorted([i for i, q in enumerate(adj) if q <= alpha])
    data = {"adjusted_p": adj.tolist(), "rejected_indices": rejected}
    if claimed_rejected is None:
        return confirm("statistics.multiple_comparisons",
                       f"{len(rejected)}/{k} rejected at alpha={alpha} after {method}", data)
    if sorted(claimed_rejected) == rejected:
        return confirm("statistics.multiple_comparisons",
                       f"rejection set matches claim: {rejected}", data)
    return mismatch("statistics.multiple_comparisons",
                    f"claimed rejected={sorted(claimed_rejected)}, computed={rejected}", data)


def verify_confidence_interval(spec: Dict[str, Any]) -> VerifierResult:
    """Verify CI shape and (if raw inputs supplied) recompute bounds.

    Bound-recompute path: pass mean, sd, n, conf_level (default 0.95) plus
    optional ``df`` (default n-1). Compares the recomputed bounds to the
    claimed ci_low/ci_high within ``tolerance`` (default 1e-3).
    """
    _ensure_stats()
    est = spec.get("estimate")
    lo = spec.get("ci_low")
    hi = spec.get("ci_high")
    if est is None or lo is None or hi is None:
        return na("statistics.confidence_interval")
    if not (lo <= hi):
        return mismatch("statistics.confidence_interval", f"ci_low={lo} > ci_high={hi}")
    if not (lo <= est <= hi):
        return mismatch("statistics.confidence_interval",
                        f"estimate {est} not in [{lo}, {hi}]")

    # Optional bound recomputation
    mean = spec.get("mean", est)
    sd = spec.get("sd")
    n = spec.get("n")
    conf = float(spec.get("conf_level", 0.95))
    tol = clamp_tol(spec, "tolerance", 5e-3)
    if sd is not None and n is not None and n >= 2:
        df = spec.get("df", n - 1)
        try:
            tcrit = float(scistats.t.ppf(0.5 + conf / 2.0, df))
            margin = tcrit * (sd / math.sqrt(n))
            recompute_lo = mean - margin
            recompute_hi = mean + margin
            data = {"recomputed_ci_low": recompute_lo,
                    "recomputed_ci_high": recompute_hi,
                    "conf_level": conf, "df": df, "tcrit": tcrit}
            if abs(recompute_lo - lo) > tol or abs(recompute_hi - hi) > tol:
                return mismatch(
                    "statistics.confidence_interval",
                    f"claimed CI [{lo}, {hi}] != recomputed [{recompute_lo:.6g}, {recompute_hi:.6g}] (tol {tol})",
                    data,
                )
            return confirm(
                "statistics.confidence_interval",
                f"recomputed CI matches: [{recompute_lo:.6g}, {recompute_hi:.6g}]",
                data,
            )
        except Exception as e:
            return error("statistics.confidence_interval", f"recompute failed: {e}")

    return confirm("statistics.confidence_interval",
                   f"estimate {est} in [{lo}, {hi}]")


def verify_measurement_consistency(spec: Dict[str, Any]) -> VerifierResult:
    """Do several INDEPENDENT determinations of one quantity agree?

    The metrologist's consistency check, in pure arithmetic. Given measurements of the SAME
    quantity, each a value with a one-sigma uncertainty, it computes the inverse-variance
    weighted mean, the reduced chi-square / Birge ratio, and the largest pairwise
    sigma-tension, then verifies a stated CLAIM about the set:

      claim="consistent" (default): the determinations agree within their stated
          uncertainties -> CONFIRMED iff the worst pairwise tension <= max_tension_sigma
          AND (with more than one degree of freedom) the Birge ratio <= birge_max.
      claim="discordant": the set carries a real disagreement -> CONFIRMED iff the worst
          pairwise tension > max_tension_sigma.
      claim="agree_to_relative" (requires rel_level): the values agree to a stated relative
          level -> CONFIRMED iff (max - min) / |weighted_mean| <= rel_level.

    It does NOT and CANNOT judge whether any measured value is correct -- that is what the
    experiment is for, and a claim about a measured constant is out of a verifier's scope.
    It judges only the internal agreement of the reported numbers, which is pure computation.

    Method: inverse-variance weighted mean + Birge ratio (R. T. Birge, Phys. Rev. 40, 207
    (1932)) -- the consistency statistic used in the CODATA and PDG constant adjustments.
    Public-domain method: it grounds the tool, never the verdict.

    Spec (artifact key CONCORDANCE_VERIFY):
        {
          "quantity": "inverse fine structure constant",   # label only, optional
          "measurements": [
             {"label": "Rb-87 recoil", "value": 137.035999206, "sigma": 0.000000011},
             ...   # >= 2 entries, each sigma > 0
          ],
          "claim": "consistent" | "discordant" | "agree_to_relative",   # default consistent
          "max_tension_sigma": 3.0,   # optional; clamped so a caller may only TIGHTEN it
          "birge_max": 1.5,           # optional; clamped (tighten-only)
          "rel_level": 1e-8,          # required for claim="agree_to_relative"
        }
    """
    name = "statistics.measurement_consistency"
    ms = spec.get("measurements")
    if not ms:
        return na(name)
    pts = []
    for i, m in enumerate(ms):
        try:
            v = float(m["value"]); s = float(m["sigma"])
        except (KeyError, TypeError, ValueError):
            return error(name, f"measurement {i} is missing a numeric value/sigma")
        if not (math.isfinite(v) and math.isfinite(s)) or s <= 0:
            return error(name, f"measurement {i} has a non-finite value or sigma <= 0")
        pts.append((str(m.get("label", f"m{i}")), v, s))
    n = len(pts)
    if n < 2:
        return error(name, "need at least two measurements to check agreement")

    def _st(subset):
        """Consistency statistics for a subset of (label, value, sigma) points. Pure arithmetic."""
        w = sum(1.0 / (s * s) for _, _, s in subset)
        xb = sum(v / (s * s) for _, v, s in subset) / w
        sig = math.sqrt(1.0 / w)
        contr = {lab: ((v - xb) / s) ** 2 for lab, v, s in subset}
        c2 = sum(contr.values())
        d = len(subset) - 1
        bg = math.sqrt(c2 / d) if d > 0 else 0.0
        wt, wp = 0.0, None
        for a in range(len(subset)):
            for b in range(a + 1, len(subset)):
                (_, va, sa), (_, vb, sb) = subset[a], subset[b]
                tt = abs(va - vb) / math.sqrt(sa * sa + sb * sb)
                if tt > wt:
                    wt, wp = tt, (subset[a][0], subset[b][0])
        return xb, sig, c2, d, bg, wt, wp, contr

    xbar, sigma_mean, chi2, dof, birge, worst_t, worst_pair, contribs = _st(pts)
    vals = [v for _, v, _ in pts]
    spread = max(vals) - min(vals)
    rel_spread = spread / abs(xbar) if xbar != 0 else float("inf")

    claim = (spec.get("claim") or "consistent").strip().lower()
    tension_thr = clamp_tol(spec, "max_tension_sigma", 3.0)
    birge_thr = clamp_tol(spec, "birge_max", 1.5)

    # LOCATE the fault. Over-dispersion (Birge > 1) means the reported uncertainties are too small
    # for a single common value -- a METHOD is wrong, not the quantity. The scale factor is what
    # CODATA/PDG inflate the consensus uncertainty by; the prime suspect is the largest contributor
    # to chi-square; the leave-one-out shows which single removal (if any) reconciles the set to the
    # tension threshold -- the method to re-examine.
    scale_factor = birge if (dof > 0 and birge > 1.0) else 1.0
    prime_suspect = max(contribs, key=contribs.get) if contribs else None
    leave_one_out = []
    located = None
    best_resid = None
    if n >= 3:
        for k in range(n):
            sub = [p for idx, p in enumerate(pts) if idx != k]
            _, _, _, _, bg_w, wt_w, _, _ = _st(sub)
            leave_one_out.append({"removed": pts[k][0], "birge_without": bg_w,
                                  "worst_tension_without": wt_w})
            if wt_w <= tension_thr and (best_resid is None or wt_w < best_resid):
                best_resid, located = wt_w, pts[k][0]
    # How big is the suspect's departure from the consensus of the OTHERS -- the size of the
    # systematic error to find and correct.
    systematic = None
    if prime_suspect and n >= 2:
        others = [p for p in pts if p[0] != prime_suspect]
        ps = [p for p in pts if p[0] == prime_suspect][0]
        ox, osig, _, _, _, _, _, _ = _st(others)
        dev = ps[1] - ox
        dev_sig = abs(dev) / math.sqrt(ps[2] ** 2 + osig ** 2)
        systematic = {"label": prime_suspect, "deviation_abs": dev, "deviation_sigma": dev_sig,
                      "consensus_of_others": ox, "reconciles_if_removed": (located == prime_suspect)}

    data = {
        "quantity": spec.get("quantity"),
        "n": n,
        "weighted_mean": xbar,
        "sigma_weighted_mean": sigma_mean,
        "chi_square": chi2,
        "dof": dof,
        "birge_ratio": birge,
        "scale_factor": scale_factor,
        "max_tension_sigma": worst_t,
        "worst_pair": list(worst_pair) if worst_pair else None,
        "chi2_contributions": contribs,
        "prime_suspect": prime_suspect,
        "leave_one_out": leave_one_out,
        "located": located,
        "systematic_estimate": systematic,
        "adjusted_consensus": {"value": xbar, "sigma": sigma_mean * scale_factor,
                               "note": "weighted mean; sigma inflated by the PDG scale factor"},
        "spread": spread,
        "relative_spread": rel_spread,
        "method": "inverse-variance weighted mean + Birge ratio + leave-one-out (Birge 1932); "
                  "the CODATA/PDG consistency + scale-factor procedure",
    }
    data["tension_threshold"] = tension_thr
    data["birge_threshold"] = birge_thr

    # a compact locator note, appended to the discordant / over-dispersed details
    loc = ""
    if prime_suspect and (worst_t > tension_thr or (dof > 0 and birge > birge_thr)):
        loc = f" scale x{scale_factor:.2f}; prime suspect {prime_suspect}"
        if systematic:
            loc += f" ({systematic['deviation_sigma']:.1f}sigma from the others)"
        if located:
            loc += f"; removing {located} reconciles the set to {tension_thr:g}sigma"

    if claim in ("consistent", "consistency", "agree", "concordant"):
        if worst_t <= tension_thr and (dof == 0 or birge <= birge_thr):
            return confirm(
                name,
                f"{n} determinations consistent: worst tension {worst_t:.2f}sigma <= "
                f"{tension_thr:g}, Birge {birge:.2f} <= {birge_thr:g}; weighted mean "
                f"{xbar:.12g} +/- {sigma_mean:.2g}",
                data,
            )
        why = []
        if worst_t > tension_thr and worst_pair:
            why.append(f"{worst_pair[0]} vs {worst_pair[1]} at {worst_t:.2f}sigma > {tension_thr:g}")
        if dof > 0 and birge > birge_thr:
            why.append(f"Birge {birge:.2f} > {birge_thr:g} (over-dispersed)")
        return mismatch(name, "not consistent: " + "; ".join(why) + "." + loc, data)

    if claim in ("discordant", "disagree", "tension", "inconsistent"):
        if worst_t > tension_thr and worst_pair:
            return confirm(
                name,
                f"real tension confirmed: {worst_pair[0]} vs {worst_pair[1]} at "
                f"{worst_t:.2f}sigma > {tension_thr:g} (Birge {birge:.2f}).{loc}",
                data,
            )
        return mismatch(
            name,
            f"claimed discordant but the set is consistent: worst tension {worst_t:.2f}sigma "
            f"<= {tension_thr:g}",
            data,
        )

    if claim in ("agree_to_relative", "relative", "agree_to"):
        rl = spec.get("rel_level")
        if rl is None:
            return error(name, "claim=agree_to_relative requires rel_level")
        try:
            rel_level = abs(float(rl))
        except (TypeError, ValueError):
            return error(name, "rel_level is not a number")
        data["rel_level"] = rel_level
        if rel_spread <= rel_level:
            return confirm(
                name,
                f"{n} determinations agree to relative {rel_spread:.2e} <= {rel_level:g} "
                f"(weighted mean {xbar:.12g})",
                data,
            )
        return mismatch(name, f"relative spread {rel_spread:.2e} > {rel_level:g}", data)

    return error(name, f"unknown claim {claim!r}; use consistent | discordant | agree_to_relative")


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    results: List[VerifierResult] = []
    sv = packet.get("STAT_VERIFY") or {}
    inf = packet.get("STAT_INFERENCE") or {}
    cc = packet.get("CONCORDANCE_VERIFY") or {}

    if sv.get("test"):
        results.append(verify_pvalue_calibration(sv))

    sig_spec = {**inf, **sv}
    if sig_spec.get("claimed_significance") and sig_spec.get("p_value") is not None:
        results.append(verify_significance_consistency(sig_spec))

    if inf.get("p_value") is not None:
        results.append(verify_effect_size_present(inf))

    if sv.get("raw_p_values"):
        results.append(verify_multiple_comparisons(sv))

    if all(k in sv for k in ("estimate", "ci_low", "ci_high")):
        results.append(verify_confidence_interval(sv))

    if cc.get("measurements"):
        results.append(verify_measurement_consistency(cc))

    if not results:
        results.append(na("statistics", "no STAT_VERIFY artifacts present"))
    return results
