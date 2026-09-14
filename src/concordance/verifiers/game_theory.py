"""Game-theory verifier — strategic interaction, checked deterministically.

Public-domain checks:

  * game_theory.expected_payoff — the row player's payoff under mixed strategies
        u = p^T · A · q         (A = row payoff matrix, p/q = mixed strategies)
  * game_theory.nash_pure — is a pure strategy profile a Nash equilibrium?
        each player's chosen action is a best response to the other's
  * game_theory.dominant_strategy — does one of a player's rows dominate another?
        strictly:  A[i][j] > A[k][j] for every column j

GAME_VERIFY packet (any subset):
    {
      "row_payoff": [[3,0],[5,1]], "p": [0.5,0.5], "q": [0.5,0.5], "claimed_payoff": 2.25,

      "row_payoff_A": [[3,0],[5,1]], "col_payoff_B": [[3,5],[0,1]],
      "profile": [1,1], "claimed_is_nash": true,

      "dom_matrix": [[5,1],[3,0]], "dom_row": 0, "dominated_row": 1, "claimed_dominates": true,
    }
"""
from __future__ import annotations
from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error
from .base import dispatch


def _num_matrix(M):
    return [[float(x) for x in row] for row in M]


def verify_expected_payoff(spec: Dict[str, Any]) -> VerifierResult:
    """u = sum_i sum_j p_i A_ij q_j."""
    name = "game_theory.expected_payoff"
    A, p, q, claimed = spec.get("row_payoff"), spec.get("p"), spec.get("q"), spec.get("claimed_payoff")
    if any(v is None for v in (A, p, q, claimed)):
        return na(name)
    try:
        Af = _num_matrix(A); pf = [float(x) for x in p]; qf = [float(x) for x in q]; cl = float(claimed)
    except (TypeError, ValueError):
        return error(name, "payoff matrix and strategies must be numeric")
    if len(Af) != len(pf) or any(len(r) != len(qf) for r in Af):
        return error(name, "strategy lengths must match the payoff-matrix dimensions")
    if abs(sum(pf) - 1.0) > 1e-6 or abs(sum(qf) - 1.0) > 1e-6:
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
        i, j = int(prof[0]), int(prof[1])
    except (TypeError, ValueError, IndexError):
        return error(name, "payoff matrices must be numeric and profile a pair of indices")
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
        Mf = _num_matrix(M); ii, kk = int(i), int(k)
    except (TypeError, ValueError):
        return error(name, "matrix must be numeric and rows must be indices")
    if not (0 <= ii < len(Mf)) or not (0 <= kk < len(Mf)):
        return error(name, "row indices out of range")
    dominates = all(Mf[ii][j] > Mf[kk][j] for j in range(len(Mf[ii])))
    data = {"dom_row": ii, "dominated_row": kk, "strictly_dominates": dominates, "claimed": bool(claimed)}
    if dominates == bool(claimed):
        return confirm(name, f"row {ii} {'strictly dominates' if dominates else 'does NOT dominate'} row {kk} (matches claim)", data)
    return mismatch(name, f"row {ii} {'dominates' if dominates else 'does not dominate'} row {kk}; claim said {bool(claimed)}", data)


_RULES = [
    (("row_payoff", "p", "q", "claimed_payoff"), verify_expected_payoff),
    (("row_payoff_A", "col_payoff_B", "profile", "claimed_is_nash"), verify_nash_pure),
    (("dom_matrix", "dom_row", "dominated_row", "claimed_dominates"), verify_dominant_strategy),
]


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    return dispatch(packet, "GAME_VERIFY", _RULES, domain="game_theory",
                    none_reason="no GAME_VERIFY artifacts present")
