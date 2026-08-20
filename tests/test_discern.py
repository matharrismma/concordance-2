"""Discern — the one door to discernment. It PROPOSES what matters; it never confirms.

The seed unifies the front of discernment: kind (crisis vs claim vs empty), the necessity extraction
(reduce to only what is needed to check, de-identified), and the route (which member verifies). Pure —
no corpus, no model.
"""
from concordance import discern as d


def test_nothing_brought_asks_rather_than_guesses():
    r = d.discern("   ")
    assert r["kind"] == "empty" and r["next"] == "ask_user" and r["claim"] is None
    assert r["confirms"] is False


def test_a_cry_for_help_is_discerned_first_and_never_verified():
    r = d.discern("i want to end it all")
    assert r["kind"] == "crisis" and r["next"] == "real_help"
    assert r["claim"] is None                       # never reduced to a claim, never sent to the gate
    assert any("988" in x["label"] for x in r["resources"])
    assert r["confirms"] is False


def test_a_claim_is_reduced_to_only_what_is_necessary():
    r = d.discern("my mom said water boils at 100C")
    assert r["kind"] == "claim"
    assert r["claim"] == "water boils at 100C"       # framing dropped — only the checkable core
    assert r["held"] == "my mom said"                # held home, available for the response
    assert r["next"] == "check"


def test_a_truth_bearing_condition_survives_discernment():
    r = d.discern("she said it was 100C in Dayton")
    assert r["claim"] == "it was 100C in Dayton"     # the location bears on the verdict — kept


def test_discern_names_the_member_that_should_verify():
    r = d.discern("is 17 a prime number")
    assert r["route"] and r["route"].get("member")   # a member is proposed
    assert r["why"]                                  # and it explains itself


def test_discern_only_ever_proposes_never_confirms():
    for text in ["", "i want to die", "my mom said 2 + 2 = 4", "is 17 prime"]:
        r = d.discern(text)
        assert r["proposes"] is True and r["confirms"] is False
        assert r["authority"] == "proposed"          # authority is earned at the gate, not the door
        assert r["kind"] in d.KINDS and r["next"] in d.NEXT


def test_routing_reads_the_discerned_claim_not_the_framing():
    # framing must not sway the route — it routes on the necessary claim
    framed = d.discern("my doctor told me that 2 + 2 = 4")
    bare = d.discern("2 + 2 = 4")
    assert framed["claim"] == bare["claim"] == "2 + 2 = 4"
    assert framed["route"].get("member") == bare["route"].get("member")
