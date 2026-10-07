"""Unit-pin the sports_analytics verifier (A2, 2026-10-06). Pythagorean expectation RS^2/(RS^2+RA^2)
(100,80 -> ~0.6098); games behind = ((leaderW-teamW)+(teamL-leaderL))/2. Wrong claim caught; NA."""
from __future__ import annotations
from concordance.verifiers import sports_analytics as SP


def test_pythagorean_expectation():
    assert SP.verify_pythagorean_expectation({"runs_scored": 100, "runs_allowed": 80, "pythag_exponent": 2,
                                              "claimed_winning_pct": 0.6098}).status == "CONFIRMED"
    assert SP.verify_pythagorean_expectation({"runs_scored": 100, "runs_allowed": 80, "pythag_exponent": 2,
                                              "claimed_winning_pct": 0.5}).status == "MISMATCH"
    assert SP.verify_pythagorean_expectation({}).status == "NOT_APPLICABLE"


def test_games_behind():
    assert SP.verify_games_behind({"leader_wins": 50, "leader_losses": 30, "team_wins": 45, "team_losses": 35,
                                   "claimed_games_behind": 5}).status == "CONFIRMED"
    assert SP.verify_games_behind({"leader_wins": 50, "leader_losses": 30, "team_wins": 45, "team_losses": 35,
                                   "claimed_games_behind": 2}).status == "MISMATCH"
