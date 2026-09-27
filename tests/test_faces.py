"""The expert faces — a face is a deterministic COMPOSER over existing specialists, never a generator.

Pins the Phase 3 contract (docs/EXPERT_FACES.md): route to the right servant; crisis outranks the
servant; the served path gathers from the keeping + turns the eye upward; verifiers run only on a
checkable claim in the face's domain (honest GAP otherwise); it never crashes and never authors.
Runs with pytest OR directly; all dependencies injected, so no corpus/model is touched.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import faces  # noqa: E402


def test_route_picks_the_fitting_servant():
    assert faces.route("how should I budget my money and pay down debt") == "face_steward"
    assert faces.route("explain how photosynthesis works, help me learn") == "face_tutor"
    assert faces.route("I have no food and no power, I need help") == "face_social_worker"
    assert faces.route("why does the inverse square law hold, derive it") == "face_theorist"
    assert faces.route("") is None                       # nothing to route
    assert faces.route("the weather is nice") is None    # no scope overlap → ordinary front door


def test_crisis_outranks_the_servant():
    """A cry is handed to the crisis response before the servant gathers anything (help-first)."""
    out = faces.compose("face_steward", "I can't go on, I want to end it",
                        crisis_fn=lambda t: True,
                        search_fn=lambda q, shelves=None, limit=6: [{"id": "x", "title": "T"}])
    assert out["kind"] == "crisis" and out["handoff"] == "crisis"
    assert out["gathered"] == [] and out["verify"] is None   # nothing gathered over a cry


def test_served_path_gathers_and_turns_the_eye_upward():
    cards = [{"id": "card_a", "title": "Budgeting basics", "shelf": "economics", "body": "..."},
             {"id": "card_b", "title": "Debt", "shelf": "economics", "body": "..."}]
    out = faces.compose("face_steward", "how do I make a budget",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: cards,
                        discern_fn=lambda t: {"kind": "guidance", "claim": None})
    assert out["kind"] == "served" and out["name"] == "the Steward"
    assert [g["id"] for g in out["gathered"]] == ["card_a", "card_b"]   # the keeping's substance
    assert "never" in out["manner"].lower()                            # steward never executes
    assert "upward" in out["means"]                                    # points beyond itself
    assert out["verify"] is None                                       # no checkable claim → honest GAP


def test_verifier_runs_only_on_a_checkable_claim_in_domain():
    """When discern proposes a structured claim in a domain the face verifies, compose runs it."""
    got = {}
    def fake_verify(steps):
        got["steps"] = steps
        return {"verdict": "HOLDS", "trail": [{"id": "s"}]}
    discern = {"kind": "verify", "claim": {"domain": "mathematics",
                                           "spec": {"mode": "arithmetic", "params": {"expr": "2+2"}}}}
    out = faces.compose("face_theorist", "is 2+2=4",
                        crisis_fn=lambda t: False,
                        search_fn=lambda q, shelves=None, limit=6: [],
                        discern_fn=lambda t: discern,
                        verify_fn=fake_verify)
    assert out["verify"] == {"verdict": "HOLDS", "trail": [{"id": "s"}]}
    assert got["steps"][0]["domain"] == "mathematics"       # routed to the face's verifier
    # a claim in a domain the face does NOT verify yields no steps (honest GAP), verifier never called
    out2 = faces.compose("face_theorist", "who won in 1815",
                         crisis_fn=lambda t: False,
                         search_fn=lambda q, shelves=None, limit=6: [],
                         discern_fn=lambda t: {"claim": {"domain": "history", "spec": {"mode": "x"}}},
                         verify_fn=lambda s: (_ for _ in ()).throw(AssertionError("must not run")))
    assert out2["verify"] is None


def test_unknown_face_is_an_honest_error():
    assert faces.compose("face_nope", "anything", crisis_fn=lambda t: False).get("error")


if __name__ == "__main__":
    import pytest
    sys.exit(int(pytest.main([__file__, "-q"])))
