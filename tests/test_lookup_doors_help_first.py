"""Every door a person types into answers a cry with help — the lookup doors too.

Matt, 2026-11-20: "Same as composing." The composing doors each hold their own gate (/ask,
/discern, /recombine since c8d563d). A structural audit of all 218 handler blocks then found 27
reading a prose-shaped parameter, ~17 of them search boxes that answered a cry with a record list
and no help.

One gate at the one chokepoint (`dispatch`), because a per-handler gate is a gate someone forgets
when they add door eighteen. What these tests hold:

  1. The lookup doors help, across several unrelated ones.
  2. Ordinary lookups on those same doors are untouched.
  3. EVERY prose parameter is checked, not just the first.
  4. It is GET-scoped: POST bodies belong to /ask and /discern, which hold their own gates.
  5. It fails safe if the crisis net raises.
  6. It uses `ask.is_crisis` and `ask.crisis_help()`, not a copy.
  7. The measured cost is pinned, so a future reader sees the trade rather than discovering it.
  8. /recombine's shipped contract still holds when this gate fires ahead of the weave's own.
"""
from __future__ import annotations

import pytest

from concordance import ask
from concordance.config import EngineConfig
from concordance.web import api

SEC = EngineConfig("secular")
CRY = "I want to end my life"

LOOKUP_DOORS = ["/search", "/dictionary", "/thesaurus", "/locate", "/study_find", "/prophecy"]


def _get(path, query):
    return api.dispatch("GET", path, query, None, SEC)


def _payload(resp):
    """dispatch returns (status, payload) in some shape — pull the dict out either way."""
    if isinstance(resp, tuple):
        for part in resp:
            if isinstance(part, dict):
                return part
        return {}
    return resp if isinstance(resp, dict) else getattr(resp, "payload", {}) or {}


def _body(resp):
    p = _payload(resp)
    return p.get("data") if isinstance(p.get("data"), dict) else p


# ── 1. the lookup doors help ───────────────────────────────────────────────────────────────
@pytest.mark.parametrize("path", LOOKUP_DOORS)
def test_a_lookup_door_answers_a_cry_with_help(path):
    b = _body(_get(path, {"q": CRY}))
    assert b.get("kind") == "crisis", f"{path} answered a cry with a search result"
    assert b.get("found") is False
    labels = " ".join(str(r.get("label")) for r in (b.get("resources") or []))
    assert "988" in labels


# ── 2. ordinary lookups untouched ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("path,q", [("/search", "how do I bake bread"),
                                    ("/dictionary", "agape"),
                                    ("/thesaurus", "courage"),
                                    ("/locate", "Jerusalem")])
def test_an_ordinary_lookup_is_untouched(path, q):
    b = _body(_get(path, {"q": q}))
    assert b.get("kind") != "crisis", f"{path} swept {q!r} into crisis"


# ── 3. every prose parameter, not just the first ───────────────────────────────────────────
def test_a_cry_in_a_later_parameter_is_still_caught():
    b = _body(_get("/search", {"q": "bread", "text": CRY}))
    assert b.get("kind") == "crisis", "only the first prose parameter was checked"


# ── 4. GET-scoped ──────────────────────────────────────────────────────────────────────────
def test_the_gate_is_get_scoped():
    """POST doors hold their own gates and their own shapes; this one must not reshape them."""
    b = _body(api.dispatch("POST", "/ask", {}, {"text": CRY}, SEC))
    assert b.get("kind") == "crisis", "/ask must still answer a cry itself"
    assert b.get("message") == ask.CRISIS_MESSAGE
    # and it is /ask's own payload, not the lookup gate's note
    assert "search result" not in str(b.get("note") or "")


# ── 5. fails safe ──────────────────────────────────────────────────────────────────────────
def test_it_fails_safe_when_the_net_raises(monkeypatch):
    def boom(_t):
        raise RuntimeError("net down")

    monkeypatch.setattr(ask, "is_crisis", boom)
    b = _body(_get("/search", {"q": "how do I bake bread"}))
    assert b.get("kind") == "crisis"
    labels = " ".join(str(r.get("label")) for r in (b.get("resources") or []))
    assert "988" in labels


# ── 6. one net, one wording ────────────────────────────────────────────────────────────────
def test_the_gate_uses_the_shared_net_and_words(monkeypatch):
    monkeypatch.setattr(ask, "is_crisis", lambda _t: True)
    b = _body(_get("/search", {"q": "anything at all"}))
    assert b.get("kind") == "crisis", "the gate is not consulting ask.is_crisis"
    assert b.get("message") == ask.CRISIS_MESSAGE
    assert b.get("resources") == ask.crisis_help()["resources"]


# ── 7. the measured cost, pinned ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("term", ["suicide", "suicidal", "self-harm", "overdose"])
def test_the_known_cost_is_intercepted_on_purpose(term):
    """Looking these words up returns the helpline instead of a definition. That is the accepted
    trade, measured and stated — not an accident to be discovered later."""
    assert _body(_get("/dictionary", {"q": term})).get("kind") == "crisis"


@pytest.mark.parametrize("term", ["euthanasia", "grief", "hospice", "laudanum", "hemlock",
                                  "end of life care", "Samson", "Judas",
                                  "Saul fell on his own sword"])
def test_the_scripture_history_and_medical_lookups_are_NOT_intercepted(term):
    """The boundary of the cost. If one of these starts firing, the net widened and the lookup
    doors got quieter without anyone deciding to."""
    assert _body(_get("/dictionary", {"q": term})).get("kind") != "crisis"


# ── 8. /recombine's contract survives this gate firing first ───────────────────────────────
def test_recombine_still_reports_the_same_shape():
    b = _body(_get("/recombine", {"q": CRY}))
    assert b.get("kind") == "crisis"
    assert b.get("found") is False
    assert b.get("message") == ask.CRISIS_MESSAGE
