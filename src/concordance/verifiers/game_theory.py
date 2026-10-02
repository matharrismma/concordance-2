"""Game-theory verifier — strategic interaction, checked deterministically.

Public-domain checks:

  * game_theory.expected_payoff — the row player's payoff under mixed strategies
        u = p^T · A · q         (A = row payoff matrix, p/q = mixed strategies)
  * game_theory.nash_pure — is a pure strategy profile a Nash equilibrium?
        each player's chosen action is a best response to the other's
  * game_theory.dominant_strategy — does one of a player's rows dominate another?
        strictly:  A[i][j] > A[k][j] for every column j
  * game_theory.iterated — the Prisoner's Dilemma with a shadow of the future w (Axelrod 1984):
        a dilemma iff T > R > P > S and 2R > T + S; TIT FOR TAT cannot be invaded iff
        w >= max((T-R)/(R-S), (T-R)/(T-P)); cooperating forever earns R/(1-w), defecting once and
        being punished earns T + wP/(1-w)
  * game_theory.population — MANY players, no true opponent (Matt, 2026-10-02: "there are many and
        no true opponents … it can expand and contract"): a share x of reciprocators (TIT FOR TAT)
        among defectors, pairwise random matching, replicator direction dx/dt ∝ x(1-x)(f_TFT - f_D).
        Cooperation EXPANDS above the threshold share x* = (P-S) / ((R-T+w(T-P))/(1-w) + P-S) and
        CONTRACTS below it; with no shadow of the future (w below (T-R)/(T-P)) it only contracts.
        The opponent is the population's current mix, and the mix moves.

  Matt's frame for the game (2026-10-02): OPENING = the optimal path (wayfind.path — one next step);
  MIDGAME = reciprocity (tit for tat) until the finish position is reached; CLOSING = run the final
  play to the seal. Two gates on every move: GREEN = the FLOOR holds (attest_floor), RED = aligned
  (attest_red) — kernel.gate: a RED hit or a FLOOR error rejects.

GAME_VERIFY packet (any subset):
    {
      "row_payoff": [[3,0],[5,1]], "p": [0.5,0.5], "q": [0.5,0.5], "claimed_payoff": 2.25,

      "row_payoff_A": [[3,0],[5,1]], "col_payoff_B": [[3,5],[0,1]],
      "profile": [1,1], "claimed_is_nash": true,

      "dom_matrix": [[5,1],[3,0]], "dom_row": 0, "dominated_row": 1, "claimed_dominates": true,

      "pd_T": 5, "pd_R": 3, "pd_P": 1, "pd_S": 0, "shadow_w": 0.9,
      "claimed_is_dilemma": true, "claimed_tft_stable": true,
      "claimed_cooperate_forever_payoff": 30, "claimed_defect_then_punished_payoff": 14,

      "pd_T": 5, "pd_R": 3, "pd_P": 1, "pd_S": 0, "shadow_w": 0.9, "cooperator_share": 0.5,
      "claimed_direction": "expands", "claimed_threshold_share": 0.0588,
    }
"""
from __future__ import annotations
import math
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error
from .base import dispatch


def _num_matrix(M):
    """A finite, rectangular, non-empty numeric matrix — or ValueError. (Handoff review 2026-10-02:
    a ragged matrix, a NaN, or an empty list must be MALFORMED INPUT, never a false MISMATCH.)"""
    rows = [[float(x) for x in row] for row in M]
    if not rows or not rows[0]:
        raise ValueError("empty matrix")
    if any(len(r) != len(rows[0]) for r in rows):
        raise ValueError("ragged matrix")
    if any(not math.isfinite(x) for r in rows for x in r):
        raise ValueError("non-finite entry")
    return rows


def _as_bool(v):
    """A STRICT boolean claim: True/False, 0/1, or the words true/false/yes/no. Anything else is
    malformed — never bool(\"false\") == True (a claim of 'false' was CONFIRMED as 'true' before)."""
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)) and v in (0, 1):
        return bool(v)
    if isinstance(v, str):
        t = v.strip().lower()
        if t in ("true", "yes", "1"):
            return True
        if t in ("false", "no", "0"):
            return False
    raise ValueError(f"claim must be a boolean (true/false), got {v!r}")


def _index(v):
    """An integral index — 1.7 is not row 1 (it was silently truncated before)."""
    f = float(v)
    if not f.is_integer():
        raise ValueError(f"index must be integral, got {v!r}")
    return int(f)


def _distribution(p):
    """A probability vector: finite, nonnegative, summing to one. [-1, 2] sums to one and was
    accepted — a negative probability 'verified' a payoff of nonsense."""
    pf = [float(x) for x in p]
    if not pf or any(not math.isfinite(x) or x < 0 for x in pf):
        raise ValueError("strategy entries must be finite and nonnegative")
    if abs(sum(pf) - 1.0) > 1e-6:
        raise ValueError("strategy must sum to one")
    return pf


def verify_expected_payoff(spec: Dict[str, Any]) -> VerifierResult:
    """u = sum_i sum_j p_i A_ij q_j."""
    name = "game_theory.expected_payoff"
    A, p, q, claimed = spec.get("row_payoff"), spec.get("p"), spec.get("q"), spec.get("claimed_payoff")
    if any(v is None for v in (A, p, q, claimed)):
        return na(name)
    try:
        Af = _num_matrix(A); pf = _distribution(p); qf = _distribution(q); cl = float(claimed)
    except (TypeError, ValueError) as e:
        return error(name, f"payoff matrix must be finite and rectangular, strategies finite nonnegative distributions, claim numeric ({e})")
    if not math.isfinite(cl):
        return error(name, "claimed payoff must be finite")
    if len(Af) != len(pf) or any(len(r) != len(qf) for r in Af):
        return error(name, "strategy lengths must match the payoff-matrix dimensions")
    if False:
        return error(name, "mixed strategies must each sum to 1")
    actual = sum(pf[i] * Af[i][j] * qf[j] for i in range(len(pf)) for j in range(len(qf)))
    data = {"expected_payoff": actual, "claimed": cl, "formula": "u = p^T A q"}
    if abs(actual - cl) <= max(1e-6, 1e-3 * abs(actual)):
        return confirm(name, f"expected payoff = {actual:.4f} (matches {cl})", data)
    return mismatch(name, f"expected payoff = {actual:.4f}, claimed {cl}", data)


def verify_nash_pure(spec: Dict[str, Any]) -> VerifierResult:
    """A pure profile (i, j) is Nash iff i is a best response to j (in A) and j to i (in B)."""
    name = "game_theory.nash_pure"
    A, B, prof, claimed = spec.get("row_payoff_A"), spec.get("col_payoff_B"), spec.get("profile"), spec.get("claimed_is_nash")
    if any(v is None for v in (A, B, prof, claimed)):
        return na(name)
    try:
        Af, Bf = _num_matrix(A), _num_matrix(B)
        i, j = _index(prof[0]), _index(prof[1])
        claimed = _as_bool(claimed)
    except (TypeError, ValueError, IndexError) as e:
        return error(name, f"payoff matrices must be finite and rectangular, profile a pair of integral indices, claim boolean ({e})")
    if len(Af) != len(Bf) or len(Af[0]) != len(Bf[0]):
        return error(name, "row and column payoff matrices must have identical shape (one game, two players)")
    if not (0 <= i < len(Af)) or not (0 <= j < len(Af[0])):
        return error(name, "profile indices are out of range")
    row_best = all(Af[i][j] >= Af[k][j] for k in range(len(Af)))          # row can't gain by deviating
    col_best = all(Bf[i][j] >= Bf[i][l] for l in range(len(Bf[i])))       # col can't gain by deviating
    is_nash = row_best and col_best
    data = {"profile": [i, j], "row_best_response": row_best, "col_best_response": col_best,
            "is_nash": is_nash, "claimed": bool(claimed)}
    if is_nash == bool(claimed):
        return confirm(name, f"profile ({i},{j}) is {'a' if is_nash else 'NOT a'} Nash equilibrium (matches claim)", data)
    return mismatch(name, f"profile ({i},{j}) is {'a' if is_nash else 'not a'} Nash equilibrium; claim said {bool(claimed)}", data)


def verify_dominant_strategy(spec: Dict[str, Any]) -> VerifierResult:
    """Row dom_row strictly dominates dominated_row iff it pays strictly more in every column."""
    name = "game_theory.dominant_strategy"
    M, i, k, claimed = spec.get("dom_matrix"), spec.get("dom_row"), spec.get("dominated_row"), spec.get("claimed_dominates")
    if any(v is None for v in (M, i, k, claimed)):
        return na(name)
    try:
        Mf = _num_matrix(M); ii, kk = _index(i), _index(k); claimed = _as_bool(claimed)
    except (TypeError, ValueError) as e:
        return error(name, f"matrix must be finite and rectangular, rows integral indices, claim boolean ({e})")
    if not (0 <= ii < len(Mf)) or not (0 <= kk < len(Mf)):
        return error(name, "row indices out of range")
    dominates = all(Mf[ii][j] > Mf[kk][j] for j in range(len(Mf[ii])))
    data = {"dom_row": ii, "dominated_row": kk, "strictly_dominates": dominates, "claimed": bool(claimed)}
    if dominates == bool(claimed):
        return confirm(name, f"row {ii} {'strictly dominates' if dominates else 'does NOT dominate'} row {kk} (matches claim)", data)
    return mismatch(name, f"row {ii} {'dominates' if dominates else 'does not dominate'} row {kk}; claim said {bool(claimed)}", data)


def _pd(spec):
    T, R, P, S = (float(spec["pd_T"]), float(spec["pd_R"]), float(spec["pd_P"]), float(spec["pd_S"]))
    return T, R, P, S


def _is_dilemma(T, R, P, S) -> bool:
    return T > R > P > S and 2 * R > T + S


def verify_iterated(spec: Dict[str, Any]) -> VerifierResult:
    """The iterated Prisoner's Dilemma under a shadow of the future w (Axelrod, The Evolution of
    Cooperation, 1984, Propositions 1-2): is it a dilemma; can TIT FOR TAT be invaded; what does
    cooperating forever earn against defecting once and being punished ever after."""
    name = "game_theory.iterated"
    claims = ("claimed_is_dilemma", "claimed_tft_stable", "claimed_cooperate_forever_payoff",
              "claimed_defect_then_punished_payoff")
    if not all(k in spec for k in ("pd_T", "pd_R", "pd_P", "pd_S")) or not any(k in spec for k in claims):
        return na(name)
    try:
        T, R, P, S = _pd(spec)
        w = float(spec.get("shadow_w", 0.0))
        for k in ("claimed_is_dilemma", "claimed_tft_stable"):
            if k in spec:
                spec = dict(spec, **{k: _as_bool(spec[k])})
    except (TypeError, ValueError, KeyError) as e:
        return error(name, f"pd_T, pd_R, pd_P, pd_S and shadow_w must be finite numbers, boolean claims true/false ({e})")
    if not all(math.isfinite(v) for v in (T, R, P, S, w)):
        return error(name, "payoffs and shadow_w must be finite")
    if not (0.0 <= w < 1.0):
        return error(name, "shadow_w must satisfy 0 <= w < 1 (a discount on the next round)")
    dilemma = _is_dilemma(T, R, P, S)
    thr = max((T - R) / (R - S), (T - R) / (T - P)) if (R > S and T > P) else float("inf")
    tft_stable = w >= thr
    coop = R / (1 - w)
    defect_once = T + w * P / (1 - w)
    data = {"T": T, "R": R, "P": P, "S": S, "w": w, "is_dilemma": dilemma,
            "tft_stability_threshold_w": thr, "tft_stable": tft_stable,
            "cooperate_forever_payoff": coop, "defect_then_punished_payoff": defect_once,
            "model": "two players, pairwise, discount w per round; TFT = cooperate first then copy the other's "
                     "last move. 'cooperate forever' = TFT vs TFT (R every round). 'defect then punished' = "
                     "ALL-D vs TFT: T once, then P every round (the defector keeps defecting; TFT answers in kind). "
                     "A single defection followed by repair is a DIFFERENT sequence, not this number.",
            "formula": "TFT stable iff w >= max((T-R)/(R-S), (T-R)/(T-P)); R/(1-w) vs T + wP/(1-w)"}
    bad = []
    if "claimed_is_dilemma" in spec and bool(spec["claimed_is_dilemma"]) != dilemma:
        bad.append(f"is_dilemma is {dilemma}, claim said {bool(spec['claimed_is_dilemma'])}")
    if "claimed_tft_stable" in spec and bool(spec["claimed_tft_stable"]) != tft_stable:
        bad.append(f"TIT FOR TAT {'is' if tft_stable else 'is NOT'} stable at w={w:g} (threshold {thr:.4g}); claim said {bool(spec['claimed_tft_stable'])}")
    for key, val in (("claimed_cooperate_forever_payoff", coop), ("claimed_defect_then_punished_payoff", defect_once)):
        if key in spec:
            try:
                cl = float(spec[key])
            except (TypeError, ValueError):
                return error(name, f"{key} must be numeric")
            if abs(val - cl) > max(1e-6, 1e-3 * abs(val)):
                bad.append(f"{key.replace('claimed_', '')} = {val:.6g}, claimed {cl:.6g}")
    if bad:
        return mismatch(name, "; ".join(bad), data)
    return confirm(name, f"dilemma={dilemma}; TFT {'stable' if tft_stable else 'invadable'} at w={w:g} (threshold {thr:.4g}); "
                         f"cooperate forever {coop:.6g} vs defect-then-punished {defect_once:.6g} (matches claims)", data)


def verify_population(spec: Dict[str, Any]) -> VerifierResult:
    """MANY players, no true opponent: a share x of reciprocators (TIT FOR TAT) among defectors, pairwise
    random matching, repeated with shadow w. Replicator direction dx/dt ∝ x(1-x)(f_TFT - f_D):
    f_TFT = x·R/(1-w) + (1-x)(S + wP/(1-w)), f_D = x(T + wP/(1-w)) + (1-x)P/(1-w). Cooperation EXPANDS
    above x* = (P-S)/((R-T+w(T-P))/(1-w) + P-S) and CONTRACTS below; the mix itself is the opponent."""
    name = "game_theory.population"
    if not all(k in spec for k in ("pd_T", "pd_R", "pd_P", "pd_S", "cooperator_share")) \
            or not any(k in spec for k in ("claimed_direction", "claimed_threshold_share")):
        return na(name)
    try:
        T, R, P, S = _pd(spec)
        w = float(spec.get("shadow_w", 0.0))
        x = float(spec["cooperator_share"])
    except (TypeError, ValueError, KeyError):
        return error(name, "pd_T, pd_R, pd_P, pd_S, shadow_w and cooperator_share must be numeric")
    if not all(math.isfinite(v) for v in (T, R, P, S, w, x)):
        return error(name, "payoffs, shadow_w and cooperator_share must be finite")
    if not (0.0 <= w < 1.0) or not (0.0 <= x <= 1.0):
        return error(name, "shadow_w must satisfy 0 <= w < 1 and cooperator_share 0 <= x <= 1")
    f_tft = x * R / (1 - w) + (1 - x) * (S + w * P / (1 - w))
    f_d = x * (T + w * P / (1 - w)) + (1 - x) * P / (1 - w)
    diff = f_tft - f_d
    A = (R - T + w * (T - P)) / (1 - w)          # the per-share gain of meeting a reciprocator
    denom = A + (P - S)
    if denom > 0 and A > 0:
        thr = (P - S) / denom                     # the critical mass of cooperators
    else:
        thr = 1.0                                 # no shadow of the future large enough: never expands
    thr = max(0.0, min(1.0, thr))
    direction = "stationary" if (x in (0.0, 1.0) or abs(diff) < 1e-12) else ("expands" if diff > 0 else "contracts")
    data = {"T": T, "R": R, "P": P, "S": S, "w": w, "cooperator_share": x,
            "fitness_tft": f_tft, "fitness_defect": f_d, "direction": direction, "threshold_share": thr,
            "model": "exactly two strategies (TIT FOR TAT, ALL-D), random pairwise matching, infinite well-mixed "
                     "population, replicator dynamics, discount w per round — a statement about THIS model, not "
                     "about every community or strategy set",
            "formula": "dx/dt ∝ x(1-x)(f_TFT - f_D); x* = (P-S)/((R-T+w(T-P))/(1-w) + P-S)"}
    bad = []
    if "claimed_direction" in spec and str(spec["claimed_direction"]).strip().lower() != direction:
        bad.append(f"at x={x:g}, w={w:g} cooperation {direction} (f_TFT {f_tft:.4g} vs f_D {f_d:.4g}); claim said {spec['claimed_direction']!r}")
    if "claimed_threshold_share" in spec:
        try:
            cl = float(spec["claimed_threshold_share"])
        except (TypeError, ValueError):
            return error(name, "claimed_threshold_share must be numeric")
        if abs(thr - cl) > max(1e-4, 1e-3 * thr):
            bad.append(f"threshold share x* = {thr:.4g}, claimed {cl:.4g}")
    if bad:
        return mismatch(name, "; ".join(bad), data)
    return confirm(name, f"at x={x:g}, w={w:g} cooperation {direction} (f_TFT {f_tft:.4g} vs f_D {f_d:.4g}); "
                         f"critical mass x* = {thr:.4g} (matches claims)", data)


_RULES = [
    (("row_payoff", "p", "q", "claimed_payoff"), verify_expected_payoff),
    (("row_payoff_A", "col_payoff_B", "profile", "claimed_is_nash"), verify_nash_pure),
    (("dom_matrix", "dom_row", "dominated_row", "claimed_dominates"), verify_dominant_strategy),
    (("pd_T", "pd_R", "pd_P", "pd_S", "claimed_tft_stable"), verify_iterated),
    (("pd_T", "pd_R", "pd_P", "pd_S", "claimed_is_dilemma"), verify_iterated),
    (("pd_T", "pd_R", "pd_P", "pd_S", "claimed_cooperate_forever_payoff"), verify_iterated),
    (("pd_T", "pd_R", "pd_P", "pd_S", "cooperator_share", "claimed_direction"), verify_population),
    (("pd_T", "pd_R", "pd_P", "pd_S", "cooperator_share", "claimed_threshold_share"), verify_population),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "GAME_VERIFY", _RULES, domain="game_theory",
                    none_reason="no GAME_VERIFY artifacts present")
