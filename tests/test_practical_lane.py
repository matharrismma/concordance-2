"""The practical lane, and the layering defect it closes.

The weave's retrieval default was `corpus.search(q, limit=top_cards)` alone, so it bypassed every
lane `respond()` has. Measured on the live keeping 2026-11-20, that is what answered "my child has
a deep cut and is bleeding a lot" from the `taxonomy` shelf with *Clerodendrum thomsoniae —
bleeding glory-bower* while "Stop severe bleeding" sat at rank 3.

What these tests hold, in the order the defects actually happened:

  1. THE GATE FIRES ON A DESCRIBED SITUATION, not only on an imperative. `corpus._PRACTICAL` is
     thirty verbs and `_HOWTO` wants "how"; a parent types neither.
  2. THE VETO PROTECTS A WORD QUESTION, including "how do you spell X" — the one row the lane was
     measured to cost. The veto lives outside `word_parse_intent` on purpose: a trigger there would
     re-route the live /ask door.
  3. THE LANE DECLINES BY RETURNING None, so a caller's own default stays the caller's.
  4. THE LANE ONLY REORDERS. It cannot invent or withhold a card — "a miss must stay a miss".
  5. THE WEAVE ACTUALLY CONSULTS IT. This is the regression that matters: the lane can exist and the
     weave can quietly keep its old default, which is exactly the shape of the original defect.
"""
from __future__ import annotations

from concordance import ask, recombine


# ── 1. the gate hears a situation ──────────────────────────────────────────────────────────
def test_the_gate_fires_on_a_described_situation():
    """These two rows are the measured wins. If either stops firing, the win is gone."""
    assert ask.situation_intent("my child has a deep cut and is bleeding a lot")
    assert ask.situation_intent("the linen of someone with a fever")


def test_the_imperative_gate_alone_would_have_missed_them():
    """Pins WHY the situation gate exists: the old triggers are silent on these."""
    from concordance import corpus
    for q in ("my child has a deep cut and is bleeding a lot",
              "the linen of someone with a fever"):
        imperative = (bool(corpus._PRACTICAL & set(q.lower().split()))
                      or bool(ask._HOWTO.search(q)) or bool(ask._MAKE_FROM.search(q)))
        assert not imperative, f"{q!r} now trips an imperative trigger; the test's premise is stale"


def test_the_gate_is_quiet_on_a_lookup():
    assert not ask.situation_intent("Philippians 4:13")
    assert not ask.situation_intent("what does agape mean")
    assert not ask.situation_intent("who wrote the Messiah")


# ── 2. the veto ────────────────────────────────────────────────────────────────────────────
def test_the_veto_catches_how_do_you_spell():
    """The one measured cost of the lane: without this, `etymology spell` loses to a comms card."""
    assert ask.asked_about_a_word("how do you spell conscience")
    assert ask.practical_lane("how do you spell conscience") is None


def test_the_veto_catches_the_existing_word_intents():
    assert ask.asked_about_a_word("what does agape mean")
    assert ask.asked_about_a_word("how many syllables are in Deuteronomy")


def test_the_spell_trigger_was_NOT_added_to_word_parse_intent():
    """It is a veto, not a router. A trigger inside word_parse_intent would change the live /ask
    door's behaviour, which this change deliberately does not touch."""
    kind, _word = ask.word_parse_intent("how do you spell conscience")
    assert kind is None


# ── 3. declining ───────────────────────────────────────────────────────────────────────────
def test_the_lane_declines_by_returning_none():
    assert ask.practical_lane("Philippians 4:13") is None
    assert ask.practical_lane("") is None


# ── 4. it only ever reorders ───────────────────────────────────────────────────────────────
def test_the_lane_only_reorders_what_the_search_already_returned(monkeypatch):
    """A permissive lane must never withhold a card. Same cards, possibly a different order."""
    pool = [{"id": f"c{i}", "title": f"card {i}", "shelf": s}
            for i, s in enumerate(("theories", "first_aid", "dictionary", "sanitation", "foods"))]
    monkeypatch.setattr(ask.corpus, "search", lambda q, limit=10, **k: list(pool))
    got = ask.practical_lane("my child has a cut and is bleeding", limit=10)
    assert got is not None
    assert {c["id"] for c in got} == {c["id"] for c in pool}, "the lane dropped or invented a card"


def test_the_lane_puts_a_field_card_above_a_theory(monkeypatch):
    """The tier sort is the whole mechanism: shares-a-word + instructional beats `theories`."""
    pool = [{"id": "t", "title": "bleeding glory-bower", "shelf": "taxonomy"},
            {"id": "th", "title": "conservation of momentum", "shelf": "theories"},
            {"id": "fa", "title": "Stop severe bleeding — pressure", "shelf": "first_aid"}]
    monkeypatch.setattr(ask.corpus, "search", lambda q, limit=10, **k: list(pool))
    got = ask.practical_lane("my child is bleeding a lot", limit=3)
    assert got and got[0]["id"] == "fa", f"led with {got[0]['title']!r}"


# ── 5. the weave consults it — the regression that matters ─────────────────────────────────
def test_the_weave_consults_the_practical_lane(monkeypatch):
    """THE LAYERING DEFECT. If this fails, the weave has gone back to its own private retrieval and
    every measurement behind this change is void."""
    seen = {}

    def spy(query, limit=12, pool_size=40):
        seen["query"] = query
        return [{"id": "x", "title": "a card", "shelf": "first_aid", "body": "text"}]

    monkeypatch.setattr(ask, "practical_lane", spy)
    recombine.answer("my child has a deep cut and is bleeding a lot")
    assert seen.get("query") == "my child has a deep cut and is bleeding a lot"


def test_the_weave_still_answers_when_the_lane_raises(monkeypatch):
    """A broken lane must never take the weave down with it."""
    def boom(*_a, **_k):
        raise RuntimeError("lane is broken")

    monkeypatch.setattr(ask, "practical_lane", boom)
    out = recombine.answer("how do I stop severe bleeding")
    assert isinstance(out, dict) and "found" in out
