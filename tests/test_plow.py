"""THE PLOW — a stateless personal-formation engine (LH-4). The walk lives on the person's device; the
server only computes signals + prior state → next state, and stores nothing.

It works the FIELD, never judges the farmer: every number describes today's signals, not the person's
worth. Pure: deterministic, no I/O, no clock.
"""
from concordance import plow


def test_assess_sorts_chaff_align_and_fruit():
    chaff = plow.assess({"rumination": 3, "grudge": 3, "shame": 2, "peace": 0, "obedience": 0})
    assert chaff["state"] == "chaff" and chaff["word"]["ref"] == "Psalm 1:4"
    fruit = plow.assess({"peace": 3, "obedience": 3, "clarity": 3, "rumination": 0})
    assert fruit["state"] == "fruit" and fruit["obeying"]
    mid = plow.assess({"peace": 1, "obedience": 1, "rumination": 1})
    assert mid["state"] == "align"


def test_flow_triad_rewards_harmony_not_height():
    lopsided = plow.flow_triad({"spirit": 3, "mind": 0, "body": 0})
    whole = plow.flow_triad({"spirit": 2, "mind": 2, "body": 2})
    assert lopsided["balance"] < whole["balance"]          # in-true beats one strong leg
    assert lopsided["weakest"] in ("mind", "body")
    assert whole["health"] > lopsided["health"]


def test_step_advances_the_cycle_by_what_the_field_shows():
    burn = plow.step(plow.blank(), {"rumination": 3, "grudge": 3, "shame": 3})
    assert burn["next_state"]["phase"] == "burn" and burn["next_state"]["state"] == "chaff"
    fr = plow.step({"phase": "burn", "tier": "milk", "streak": 0},
                   {"peace": 3, "obedience": 3, "clarity": 3})
    assert fr["next_state"]["phase"] == "firstfruits"


def test_streak_is_grace_not_a_ladder():
    # one hard day dents but does not undo; a chaff day is -1, a fruit day +1, align holds
    s = plow.step({"tier": "milk", "streak": 3}, {"rumination": 3, "grudge": 3})
    assert s["next_state"]["streak"] == 2
    hold = plow.step({"tier": "milk", "streak": 3}, {"peace": 1, "obedience": 1})
    assert hold["next_state"]["streak"] == 3               # align holds steady


def test_a_tier_rises_only_on_a_sustained_walk_and_eases_gently():
    up = plow.step({"tier": "milk", "streak": plow.ADVANCE_STREAK - 1},
                   {"peace": 3, "obedience": 3, "clarity": 3})
    assert up["next_state"]["tier"] == "growth" and up["advanced"]
    # a single chaff day at a high tier does NOT drop it (streak just above the decline floor)
    steady = plow.step({"tier": "growth", "streak": 0}, {"rumination": 3, "grudge": 3})
    assert steady["next_state"]["tier"] == "growth"


def test_it_works_the_field_never_judges_the_farmer():
    r = plow.step(plow.blank(), {"peace": 2})
    assert r["generated"] is False
    assert "does not judge the farmer" in r["note"] and "device" in r["held"]
    # no field anywhere scores the PERSON — only the field's signals + a next step + a word
    assert set(r["next_state"]) == {"day", "phase", "tier", "streak", "state"}
    assert r["step"]["word"]["ref"]                        # always points to Scripture
