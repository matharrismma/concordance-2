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
    # an arithmetic claim a verifier covers -> the claim branch (no corpus touched)
    r = d.discern("my mom said 2 + 2 = 4")
    assert r["kind"] == "claim"
    assert r["claim"] == "2 + 2 = 4"                 # framing dropped — only the checkable core
    assert r["held"] == "my mom said"                # held home, available for the response
    assert r["next"] == "check"


def test_a_truth_bearing_condition_survives_discernment():
    # routes to search (no verifier for boiling points) -> a question; the necessity skeleton survives
    r = d.discern("she said it was 100C in Dayton", search_fn=lambda q, n: [])
    assert r["kind"] == "question"
    assert r["claim"] == "it was 100C in Dayton"     # the location bears on it — kept in the query too
    assert r["held"] == "she said"


def test_discern_names_the_member_that_should_verify():
    r = d.discern("2 + 2 = 4")                       # a checkable claim routes to a verifier
    assert r["route"] and r["route"].get("member") == "verify"
    assert r["kind"] == "claim" and r["next"] == "check" and r["why"]


def test_discern_only_ever_proposes_never_confirms():
    # search_fn kept empty so the retrieval branch stays pure (no corpus in the fast suite)
    for text in ["", "i want to die", "my mom said 2 + 2 = 4", "is 17 prime"]:
        r = d.discern(text, search_fn=lambda q, n: [])
        assert r["proposes"] is True and r["confirms"] is False
        assert r["authority"] == "proposed"          # authority is earned at the gate, not the door
        assert r["kind"] in d.KINDS and r["next"] in d.NEXT


# ── the relevance floor, folded (#5): a retrieval proposes only genuine matches ─────────────────────
def test_a_retrieval_proposes_only_genuinely_matching_cards():
    fire = {"id": "c1", "title": "Making and keeping a fire", "shelf": "survival"}
    knots = {"id": "c2", "title": "The knots worth knowing", "shelf": "survival"}
    r = d.discern("how do i start a fire",
                  search_fn=lambda q, n: [knots, fire],
                  relevant_fn=lambda q, c: "fire" in c["title"].lower())   # the real floor: title names subject
    assert r["kind"] == "question" and r["next"] == "retrieve"
    ids = [c["id"] for c in r["candidates"]]
    assert "c1" in ids and "c2" not in ids           # the word-collision (knots) is dropped


def test_a_retrieval_with_no_genuine_match_is_an_honest_miss():
    knots = {"id": "c2", "title": "The knots worth knowing", "shelf": "survival"}
    r = d.discern("how do i start a fire",
                  search_fn=lambda q, n: [knots], relevant_fn=lambda q, c: False)
    assert r["kind"] == "question" and r["next"] == "miss" and r["candidates"] == []


def test_a_checkable_claim_never_takes_the_retrieval_branch():
    r = d.discern("2 + 2 = 4")                       # routes to a verifier, not search -> no corpus touched
    assert r["kind"] == "claim" and r["next"] == "check" and "candidates" not in r


def test_routing_reads_the_discerned_claim_not_the_framing():
    # framing must not sway the route — it routes on the necessary claim
    framed = d.discern("my doctor told me that 2 + 2 = 4")
    bare = d.discern("2 + 2 = 4")
    assert framed["claim"] == bare["claim"] == "2 + 2 = 4"
    assert framed["route"].get("member") == bare["route"].get("member")
