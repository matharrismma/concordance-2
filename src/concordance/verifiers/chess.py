"""Chess as a chainable verifier domain — the third triangulation point (Matt, 2026-10-06).

Strategy has three independent witnesses in this engine: game_theory (the abstract math), pressure_fighting
(the body under pressure), and CHESS (the mind under perfect information). Chess is the one where optimal is
literally COMPUTABLE, so it is the calibration rig: a strategic claim can be checked against ground truth.

The chess rules engine already exists and is PERFT-proven (src/concordance/chess.py); it VERIFIES what is
true of a position, it never plays. This module only adapts it to the verifier interface so a chess claim
chains and seals through the same door as the other two witnesses (POST /verify steps, derivation, seal) —
no new chess logic, nothing generated, the math determines truth.

CHESS_VERIFY packet:
  {"fen": "...", "claim": "checkmate"|"check"|"stalemate"|"legal_move"|"material",
   "move": "e2e4"            # required for legal_move
   "claimed": true,          # the claimed truth of check/checkmate/stalemate/legal_move
   "claimed_balance": 0}     # the claimed material balance (white - black), for claim=material
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base import VerifierResult, na, confirm, mismatch, error

_BOOL_CLAIMS = ("check", "checkmate", "stalemate", "legal_move")


def verify_position(spec: Dict[str, Any]) -> VerifierResult:
    name = "chess.position"
    if not isinstance(spec, dict):
        return error(name, "chess spec must be an object")
    fen = spec.get("fen")
    claim = spec.get("claim")
    if not isinstance(fen, str) or not fen.strip():
        return error(name, "a FEN string is required")
    if claim not in _BOOL_CLAIMS + ("material",):
        return error(name, f"claim must be one of {_BOOL_CLAIMS + ('material',)}")
    from .. import chess as _chess
    move = spec.get("move")
    try:
        res = _chess.verify(fen, claim, str(move) if move is not None else None)
    except Exception as e:  # noqa: BLE001 — a computation that fails is an error, never a verdict
        return error(name, f"chess computation failed: {type(e).__name__}: {e}")
    verdict = res.get("verdict")
    if verdict == "INCOMPLETE":
        return error(name, res.get("detail") or "chess verify incomplete")
    data = {"fen": fen, "claim": claim, "detail": res.get("detail"), "chess_verdict": verdict}

    if claim == "material":
        # chess.verify always HOLDS for material; the trail carries the computed balance to check the claim
        trail = (res.get("trail") or [{}])[0]
        import ast
        try:
            mat = ast.literal_eval(trail.get("detail") or "{}")
            balance = int(mat.get("balance"))
        except Exception:  # noqa: BLE001
            return error(name, "could not read the material balance")
        data["balance"] = balance
        claimed = spec.get("claimed_balance")
        if claimed is None:
            return na(name, "claim claimed_balance (white - black material, in points)")
        try:
            claimed_i = int(claimed)
        except (TypeError, ValueError):
            return error(name, "claimed_balance must be an integer")
        if claimed_i != balance:
            return mismatch(name, f"material balance is {balance:+d}, claimed {claimed_i:+d}", data)
        return confirm(name, f"material balance {balance:+d} (white - black) — matches the claim", data)

    computed = (verdict == "HOLDS")      # the property is true of the position
    data["computed"] = computed
    claimed = spec.get("claimed")
    if claimed is None:
        return na(name, f"claim claimed (the claimed truth of {claim})")
    if bool(claimed) != computed:
        return mismatch(name, f"{claim} is {computed} for this position; claimed {bool(claimed)}", data)
    return confirm(name, f"{claim} is {computed} — matches the claim ({res.get('detail')})", data)


def run(packet: Dict[str, Any]) -> List[VerifierResult]:
    cv = packet.get("CHESS_VERIFY")
    if isinstance(cv, dict) and cv:
        return [verify_position(cv)]
    return [na("chess", "no CHESS_VERIFY artifact present")]
