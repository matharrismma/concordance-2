"""THE RESIDUAL REPORT MUST BE TRUSTWORTHY OR IT IS WORSE THAN NOTHING.

`tools/boost_residuals.py` exists so that nobody has to find a bad ranking constant the way it was
found on 2026-11-17 — by reading sixty-eight answers by hand. It earns that trust from one property:
it writes search()'s boost arithmetic out a second time, and REFUSES TO REPORT if that copy no longer
reproduces `Corpus.search`'s order. A silent drift between the two would make every number it prints
a measurement of an engine that no longer exists, which is the most expensive kind of wrong.

So these tests pin, in order of what would hurt most:
  1. the drift detector actually detects drift (if this fails, nothing else here matters);
  2. the mirror reproduces the engine on a fixture;
  3. the override ratio means what the report says it means, in the direction it says;
  4. the question extractor refuses anything that is not a plain question (the voided-run lesson);
  5. the report never changes the keeping.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import corpus  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "boost_residuals", ROOT / "tools" / "boost_residuals.py")
BR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BR)


def _fixture(n_decoys: int = 24):
    """A theories card that MENTIONS the subject once, and a card that is plainly ABOUT it —
    the shape of the 2026-11-17 defect, so the ratio has something real to measure."""
    cards = {
        "th": {"id": "th", "title": "Plasma physics (the fourth state of matter)",
               "shelf": "theories", "lifecycle_stage": "public",
               "body": ("A plasma is an ionised gas whose free charges make it respond to fields "
                        "collectively; it carries current, supports waves, and in a pinch can be "
                        "wound into a torus by the magnets that confine it.")},
        "ab": {"id": "ab", "title": "Wound management", "shelf": "medicine",
               "lifecycle_stage": "public",
               "body": ("Clean the wound with running water. A wound that keeps bleeding needs "
                        "direct pressure held on the wound for ten minutes. Dress the wound, "
                        "raise the wound above the heart, and watch the wound for redness.")},
    }
    for i in range(n_decoys):
        cards[f"d{i}"] = {"id": f"d{i}", "title": f"Decoy volume {i}", "shelf": "gutenberg",
                          "body": f"an unrelated passage about decoy subject {i}",
                          "lifecycle_stage": "public"}
    return corpus.Corpus(cards, min_idf=0.0)


def test_the_drift_detector_detects_drift():
    """THE LOAD-BEARING TEST. If `_finalize` and the tool's copy of it ever disagree, `validate`
    must say so — that refusal is the only thing standing between a stale mirror and a confident
    wrong number. Simulated by making the engine answer in a different order than it really would."""
    fix = _fixture()
    qs = ["wound"]
    assert BR.validate(fix, qs) == [], "the mirror should be in step with the engine to begin with"

    real_search = fix.search
    try:
        fix.search = lambda q, limit=25, **kw: list(reversed(real_search(q, limit, **kw)))
        drifted = BR.validate(fix, qs)
    finally:
        fix.search = real_search
    assert drifted == qs, (
        "validate() did not notice that the engine's order no longer matches the mirror's — the "
        "tool would have reported numbers for an engine that does not exist")


def test_the_mirror_reproduces_the_engine():
    """Beyond the one query above: every question the fixture can answer, in the served order."""
    fix = _fixture()
    qs = ["wound", "wound management", "plasma", "decoy subject 3"]
    assert BR.validate(fix, qs) == []


def test_the_override_ratio_points_the_way_the_report_says():
    """base(promoted)/base(demoted) < 1 means the boost overrode the engine's own relevance.

    Under the OLD arithmetic the theories shelf decides this query against a card with a far higher
    base score — that is the defect — so the ratio must come out BELOW 1. Under the CURRENT
    arithmetic the boost no longer decides the top hit at all, so there is nothing to report."""
    fix = _fixture()
    qs = ["wound"]

    old = BR.residuals(fix, qs, old=True)
    assert old["theories"], "under the old arithmetic the theories boost should decide this query"
    r = old["theories"][0]
    assert r["ratio"] < 1.0, f"expected an override, got ratio {r['ratio']}"
    assert r["base_p"] < r["base_d"], "a promoted card with the HIGHER base is not an override"
    assert "Plasma" in r["promoted"] and "Wound" in r["demoted"]

    now = BR.residuals(fix, qs, old=False)
    assert not now["theories"], (
        "after the fix the shelf boost must not decide the top hit here: "
        + str(now["theories"]))


def test_fire_counts_are_the_denominator_not_a_guess():
    """A zero change-count is uninterpretable without this: 'fired often and decided nothing' and
    'never fired' are different facts and only the first says anything about the constant."""
    fix = _fixture()
    per_q, per_card, total = BR.fire_counts(fix, ["wound"])
    assert total > 0
    assert per_card["theories"] >= 1, "the theories card holds the subject and must be counted"
    assert per_q["theories"] == 1
    assert per_card["survival"] == 0, "nothing here is on the survival shelf"
    assert per_card["substance"] >= 2, "both substantive cards clear STUB_BODY_CHARS"


def test_questions_refuses_anything_that_is_not_a_question(tmp_path):
    """FOUND BY A VOIDED RUN: an extractor that read the wrong field fed 127 stringified Python
    dicts in as 'questions', and a junk token earns high idf, so it steered selection. A question
    is a plain string of plausible length or it is refused."""
    (tmp_path / "face_routes.json").write_text(json.dumps({"routes": [
        {"text": "how do I keep a wound from bleeding"},
        {"text": "{'q': 'baofeng', 'limit': 5}"},      # a stringified mapping
        {"text": "short"},                              # too short
        {"text": ["not", "a", "string"]},               # not a string at all
        {"text": "how do I keep a wound from bleeding"},  # a duplicate
    ]}), encoding="utf-8")
    (tmp_path / "live_probes.jsonl").write_text(
        json.dumps({"path": "/ask", "body": {"text": "is it a sin to doubt my faith"}}) + "\n"
        + json.dumps({"path": "/verify", "body": {"text": "ignored: not the ask door"}}) + "\n"
        + "not json at all\n", encoding="utf-8")
    got = BR.questions(tmp_path)
    assert got == ["how do I keep a wound from bleeding", "is it a sin to doubt my faith"], got


def test_the_report_is_reporting_only():
    """It may not add, seal or mutate anything. Pinned by count, and by the shape of the text."""
    fix = _fixture()
    before = len(fix.cards)
    res = BR.residuals(fix, ["wound"], old=True)
    per_q, per_card, total = BR.fire_counts(fix, ["wound"])
    text = BR.report(["wound"], res, per_q, per_card, total, old=True, validated=False)
    assert len(fix.cards) == before, "the report changed the keeping"
    assert "MIRROR NOT VALIDATED" in text, "an unvalidated arm must say so in its own output"
    for name in BR.BOOSTS:
        assert name in text
    assert "NOT MEASURED" in text and BR.NOT_MEASURED, (
        "the report must name what it cannot measure, or a zero reads as a clean bill")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
