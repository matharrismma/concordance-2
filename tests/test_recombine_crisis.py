"""The weave refuses a cry for help, and helps instead.

Measured live on 2026-11-20, on master and after the practical lane shipped: GET /recombine is
public and unauthenticated, `recombine.py` contained ZERO mentions of crisis, and "I want to end my
life" was answered in composed prose with **"Blueberries want pH 4"** — the agricultural soil-pH
card, matched on `want` and `life`. /ask has had the backstop for months; this door never did.

What these tests hold:
  1. The weave REFUSES on a cry, and carries the help.
  2. It refuses by `found: False` — a refusal that helps, never an answer. A miss stays a miss.
  3. It never reaches retrieval at all, so nothing is searched, scored or composed.
  4. It uses `ask.is_crisis` rather than its own copy of the net — a copied list drifts.
  5. It FAILS SAFE: if the crisis test raises, the help is returned, not an answer.
  6. The one wording lives in `ask.crisis_help()`, shared with /ask, so the two doors cannot drift.
  7. An ordinary question is untouched.
"""
from __future__ import annotations

import pytest

from concordance import ask, recombine
from concordance.config import EngineConfig

SEC = EngineConfig("secular")

CRIES = [
    "I want to end my life",
    "i want to kill myself",
    "I don't want to be here anymore",
]


# ── 1 & 2. it refuses, and it helps ────────────────────────────────────────────────────────
@pytest.mark.parametrize("cry", CRIES)
def test_the_weave_refuses_a_cry_and_carries_help(cry):
    assert ask.is_crisis(cry), f"the premise is stale: {cry!r} no longer reaches the crisis net"
    out = recombine.answer(cry)
    assert out.get("kind") == "crisis"
    assert out.get("found") is False, "a refusal that helps, never an answer"
    assert not (out.get("passage") or out.get("resolved_passage")), "nothing may be composed"
    assert out.get("message"), "a cry must be answered with help"
    labels = " ".join(str(r.get("label")) for r in (out.get("resources") or []))
    assert "988" in labels, "the help must carry a reachable number"


def test_the_blueberry_answer_is_gone():
    """The exact live failure this closed."""
    out = recombine.answer("I want to end my life")
    blob = (str(out.get("passage")) + str(out.get("resolved_passage"))
            + " ".join(str(s) for s in (out.get("sources") or []))).lower()
    assert "blueberr" not in blob
    assert "ph 4" not in blob


# ── 3. retrieval is never reached ──────────────────────────────────────────────────────────
def test_a_cry_never_reaches_retrieval():
    """If the gate sits after retrieval, the keeping is still searched and scored for a person in
    distress — and a later refactor could let the result through. It must short-circuit."""
    called = []

    def tripwire(_q):
        called.append(_q)
        return []

    recombine.answer("I want to end my life", search_fn=tripwire)
    assert called == [], "the weave searched the keeping for a cry for help"


# ── 4. one net, not a copy ─────────────────────────────────────────────────────────────────
def test_the_gate_calls_ask_is_crisis(monkeypatch):
    """A copied list is a list that drifts. Widening ask.is_crisis must widen this door too."""
    monkeypatch.setattr(ask, "is_crisis", lambda _t: True)
    out = recombine.answer("how do I bake bread")
    assert out.get("kind") == "crisis", "the weave is not consulting ask.is_crisis"


# ── 5. it fails safe ───────────────────────────────────────────────────────────────────────
def test_it_fails_safe_when_the_crisis_test_raises(monkeypatch):
    """A false positive shows 988 to someone asking about gardening. A false negative hands a
    composed answer to someone who said they want to die. On an error, take the first."""
    def boom(_t):
        raise RuntimeError("the net is broken")

    monkeypatch.setattr(ask, "is_crisis", boom)
    out = recombine.answer("how do I bake bread")
    assert out.get("kind") == "crisis"
    assert out.get("found") is False
    labels = " ".join(str(r.get("label")) for r in (out.get("resources") or []))
    assert "988" in labels


# ── 6. the two doors share one wording ─────────────────────────────────────────────────────
def test_both_doors_speak_the_same_words():
    """/ask and the weave must not drift apart in what they say to a person in crisis."""
    weave = recombine.answer("I want to end my life")
    help_ = ask.crisis_help()
    assert weave.get("message") == help_["message"] == ask.CRISIS_MESSAGE
    assert weave.get("resources") == help_["resources"]


def test_the_ask_door_still_carries_the_same_payload():
    """The extraction must not have changed what /ask returns."""
    out = ask.respond("I want to end my life", SEC)
    assert out.get("kind") == "crisis"
    assert out.get("message") == ask.CRISIS_MESSAGE
    assert out.get("resources") == ask.crisis_help()["resources"]
    assert out.get("generated") is False


# ── 7. ordinary questions are untouched ────────────────────────────────────────────────────
@pytest.mark.parametrize("q", ["how do I bake bread at home",
                               "Philippians 4:13",
                               "what does agape mean"])
def test_an_ordinary_question_is_not_swept_into_crisis(q):
    assert not ask.is_crisis(q)
    out = recombine.answer(q)
    assert out.get("kind") != "crisis"
