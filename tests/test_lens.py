"""Lens — Matt's writing as the way of seeing. The seed primitive.

see() proposes a way of seeing (his passages that frame the input), attributed, never generated, and
honestly empty where his writing has not yet been gathered. Pure — the corpus is injected here (the
fixtures below are placeholders, NOT his canon; the real lens corpus is his gathered writing).
"""
from concordance import lens

# Placeholder fixtures — deliberately neutral, so nothing here is mistaken for Matt's actual voice.
FIXTURE = [
    {"text": "keeping a fire alive through a cold night takes tending, not luck",
     "work": "TEST-A", "ref": "1", "id": "a1"},
    {"text": "a measure records what someone was afraid to lose",
     "work": "TEST-B", "ref": "2", "id": "b1"},
    {"text": "the narrow path is found by the few who actually look for it",
     "work": "TEST-C", "ref": "3", "id": "c1"},
]


def test_see_proposes_his_words_attributed_and_never_confirms():
    r = lens.see("how do I keep a fire through the night", corpus=FIXTURE)
    assert r["proposes"] is True and r["confirms"] is False
    top = r["seeing"][0]
    assert top["work"] == "TEST-A" and "fire" in top["text"].lower()
    assert top["text"] == FIXTURE[0]["text"]        # his ACTUAL words, verbatim — nothing generated
    assert top["ref"] == "1"                         # attributed


def test_see_is_honest_where_his_writing_does_not_reach():
    r = lens.see("the boiling point of xenon", corpus=[])
    assert r["seeing"] == [] and r["gathered"] == 0 and "still being gathered" in r["note"]


def test_see_ranks_by_shared_subject():
    r = lens.see("what does a measure confess", corpus=FIXTURE, k=1)
    assert r["seeing"][0]["work"] == "TEST-B"        # 'measure' names the subject


def test_see_returns_nothing_when_no_passage_shares_a_word():
    r = lens.see("quantum chromodynamics", corpus=FIXTURE)
    assert r["seeing"] == [] and r["gathered"] == 3  # the lens has writing, but none reaches this


# VOICE — his own words frame the answer; nothing generated, honest where unreached.
def test_voice_leads_with_his_verbatim_words_never_generated():
    r = lens.voice("how do I keep a fire through the night", corpus=FIXTURE)
    assert r["frame"] == FIXTURE[0]["text"]          # his ACTUAL words lead the answer — verbatim
    assert r["work"] == "TEST-A" and r["his_words"] is True and r["generated"] is False
    assert r["proposes"] is True and r["confirms"] is False


def test_voice_imitates_nothing_where_his_writing_does_not_reach():
    r = lens.voice("the boiling point of xenon", corpus=[])
    assert r["frame"] is None and r["his_words"] is False and r["generated"] is False
    assert "stands on its own" in r["note"]          # no imitated voice is put in his mouth


# MAP — the attributed edges his writing draws; only real, never invented.
MAP_FIXTURE = [
    {"text": "tending the fire is a kind of faithfulness, the way Romans 12:1 makes a body an offering",
     "work": "TEST-MAP", "ref": "x", "id": "m1"},
    {"text": "a plain measure and nothing more — no chapter and no verse here at all",
     "work": "TEST-MAP", "ref": "y", "id": "m2"},
]


def test_edges_draws_attributed_scripture_edges():
    r = lens.edges("how do I tend a fire", corpus=MAP_FIXTURE)
    assert r["proposes"] is True and r["confirms"] is False
    assert len(r["edges"]) == 1
    e = r["edges"][0]
    assert e["points_to"] == "Romans 12:1" and e["work"] == "TEST-MAP" and e["theme"] == "fire"


def test_edges_never_invents_an_edge_from_a_passage_that_draws_none():
    r = lens.edges("a plain measure", corpus=MAP_FIXTURE)   # m2 is relevant but names no Scripture
    assert r["edges"] == [] and "still being gathered" in r["note"]


def test_edges_is_honest_where_his_writing_does_not_reach():
    r = lens.edges("the boiling point of xenon", corpus=MAP_FIXTURE)
    assert r["edges"] == [] and r["gathered"] == 2
