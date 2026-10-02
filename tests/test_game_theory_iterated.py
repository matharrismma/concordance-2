"""The Prisoner's Dilemma beyond two players and one round (Matt, 2026-10-02: "there are many and no
true opponents … it can expand and contract"). game_theory.iterated = Axelrod's shadow of the future;
game_theory.population = a share of reciprocators among defectors, moving by replicator direction."""
import math

from concordance.verifiers import run_for_domain, game_theory as G

PD = {"pd_T": 5, "pd_R": 3, "pd_P": 1, "pd_S": 0}


def test_the_standard_payoffs_are_a_dilemma_and_tft_is_stable_only_with_a_future():
    r = G.verify_iterated({**PD, "shadow_w": 0.9, "claimed_is_dilemma": True, "claimed_tft_stable": True,
                           "claimed_cooperate_forever_payoff": 30, "claimed_defect_then_punished_payoff": 14})
    assert r.status == "CONFIRMED", r
    assert math.isclose(r.data["tft_stability_threshold_w"], 2 / 3)           # max(2/3, 1/2) — Axelrod Prop. 2
    assert G.verify_iterated({**PD, "shadow_w": 0.4, "claimed_tft_stable": True}).status == "MISMATCH"   # no future, no stability
    assert G.verify_iterated({**PD, "shadow_w": 0.4, "claimed_tft_stable": False}).status == "CONFIRMED"


def test_not_every_matrix_is_a_dilemma():
    not_pd = {"pd_T": 5, "pd_R": 1, "pd_P": 3, "pd_S": 0}                     # R < P: no dilemma
    assert G.verify_iterated({**not_pd, "claimed_is_dilemma": False}).status == "CONFIRMED"
    assert G.verify_iterated({**not_pd, "claimed_is_dilemma": True}).status == "MISMATCH"
    weak = {"pd_T": 5, "pd_R": 2, "pd_P": 1, "pd_S": 0}                       # 2R = 4 < T+S = 5: alternating beats cooperating
    assert G.verify_iterated({**weak, "claimed_is_dilemma": False}).status == "CONFIRMED"


def test_population_expands_above_the_critical_mass_and_contracts_below():
    # with w = 0.9 the critical mass is 1/17 ≈ 0.0588: six reciprocators in a hundred are enough
    hi = G.verify_population({**PD, "shadow_w": 0.9, "cooperator_share": 0.5, "claimed_direction": "expands",
                              "claimed_threshold_share": 1 / 17})
    assert hi.status == "CONFIRMED", hi
    lo = G.verify_population({**PD, "shadow_w": 0.9, "cooperator_share": 0.02, "claimed_direction": "contracts"})
    assert lo.status == "CONFIRMED", lo
    assert G.verify_population({**PD, "shadow_w": 0.9, "cooperator_share": 0.02, "claimed_direction": "expands"}).status == "MISMATCH"


def test_without_a_shadow_of_the_future_cooperation_only_contracts():
    for x in (0.1, 0.5, 0.9):
        r = G.verify_population({**PD, "shadow_w": 0.0, "cooperator_share": x, "claimed_direction": "contracts"})
        assert r.status == "CONFIRMED", r
    # exactly at Axelrod's lower threshold (T-R)/(T-P) = 0.5 the per-share gain A is 0: the critical mass is 1 (never)
    r = G.verify_population({**PD, "shadow_w": 0.5, "cooperator_share": 0.5, "claimed_threshold_share": 1.0})
    assert r.status == "CONFIRMED", r


def test_edges_and_dispatch():
    assert G.verify_iterated({}).status == "NOT_APPLICABLE"
    assert G.verify_iterated({**PD, "shadow_w": 1.0, "claimed_tft_stable": True}).status == "ERROR"     # w must be < 1
    assert G.verify_population({**PD, "shadow_w": 0.9, "cooperator_share": "half", "claimed_direction": "expands"}).status == "ERROR"
    assert G.verify_population({**PD, "shadow_w": 0.9, "cooperator_share": 1.0, "claimed_direction": "stationary"}).status == "CONFIRMED"
    rs = run_for_domain("game_theory", {"GAME_VERIFY": {**PD, "shadow_w": 0.9, "cooperator_share": 0.5,
                                                        "claimed_direction": "expands", "claimed_tft_stable": True}})
    names = {r.name: r.status for r in rs}
    assert names.get("game_theory.iterated") == "CONFIRMED" and names.get("game_theory.population") == "CONFIRMED", names
