"""Discern — the one door to discernment. It PROPOSES what matters; it never confirms.

The seed unifies the front of discernment: kind (crisis vs claim vs empty), the necessity extraction
(reduce to only what is needed to check, de-identified), and the route (which member verifies). Pure —
no corpus, no model.
"""
import pytest

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


# ── narrowing, folded (#6): the deep mode — propose a field, the gate eliminates ────────────────────
def test_field_proposes_a_committed_routed_narrowing():
    p = d.field("what is 2 + 2", ["2 + 2 = 4", "2 + 2 = 5"])
    assert p["kind"] == "field" and p["next"] == "narrow"
    assert p["committed"] is True and p["n_candidates"] == 2 and p["routable"] == 2
    assert p["proposes"] is True and p["confirms"] is False and p["authority"] == "proposed"


def test_field_routing_is_blind_to_the_generators_weight():
    # the true answer carries a low weight, a false answer a high weight — routing must not favor weight
    p = d.field("what is 2 + 2", [{"raw_text": "2 + 2 = 4", "proposal_weight": 0.01},
                                  {"raw_text": "2 + 2 = 5", "proposal_weight": 0.99}])
    routes = list(p["routing"]["routes"].values())
    assert all(r.get("mode") for r in routes) and p["routable"] == 2   # both routed by SHAPE, not weight


def test_field_fails_closed_on_an_empty_field():
    with pytest.raises(Exception):
        d.field("what is 2 + 2", [])


# ── extraction, folded (#4): the gate receives STRUCTURED claims, not a bare string ─────────────────
def test_extraction_hands_the_gate_structured_claims():
    r = d.discern("2 + 2 = 4")
    assert r["kind"] == "claim" and r["next"] == "check"
    assert r["claims"] and r["claims"][0]["domain"] == "mathematics"
    assert "spec" in r["claims"][0]                  # structured (domain, spec) — not a bare string


def test_framing_is_stripped_before_extraction():
    r = d.discern("my mom said 2 + 2 = 4")
    assert r["claim"] == "2 + 2 = 4" and r["held"] == "my mom said"
    assert r["claims"] and r["claims"][0]["claim"] == "2 + 2 = 4"   # extracted from the de-framed claim


def test_a_structured_extraction_makes_it_a_claim_even_when_routing_would_not():
    # extraction is the claim authority: a structured claim -> check, whatever the router thought
    fake = [{"id": "a1", "domain": "mathematics", "spec": {"mode": "x"}, "claim": "y"}]
    r = d.discern("a phrase the router would send to search",
                  extract_fn=lambda c: fake, search_fn=lambda q, n: [])
    assert r["kind"] == "claim" and r["next"] == "check" and r["claims"] == fake


def test_routing_reads_the_discerned_claim_not_the_framing():
    # framing must not sway the route — it routes on the necessary claim
    framed = d.discern("my doctor told me that 2 + 2 = 4")
    bare = d.discern("2 + 2 = 4")
    assert framed["claim"] == bare["claim"] == "2 + 2 = 4"
    assert framed["route"].get("member") == bare["route"].get("member")
