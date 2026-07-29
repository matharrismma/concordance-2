"""The great questions — a stranger's biggest question gets a real answer, never a filing cabinet.

Matt, 2026-07-28: "We are after sinners not saints... engaging and useful to any that enter...
the language of the people... we never hide who we are, but we are here to demonstrate not preach."

When the seeker category was first probed, SIX of NINE questions dead-ended in a keyword shrug and
three more were handed card lists. Pinned here:

  * the perennial questions match and answer — plainly, honestly, with the actual text beside;
  * the great questions OUTRANK the card search ("is God even real" matches thousands of cards by
    keyword, and a card list is the wrong answer to a person asking their biggest question);
  * mundane text can never match (the 'is 15 = Isaiah 15' discipline, applied again);
  * the answers never preach AND never hide: honest that a tool cannot settle the question,
    plain that the builders concluded yes;
  * every reference resolves; comfort never arrives without a word (the zero-scripture gap);
  * the mundane-question gate behavior is untouched.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import seekers  # noqa: E402


def test_the_perennial_questions_match():
    for q, want in (("is God even real", "is_god_real"),
                    ("what happens when we die", "what_happens_when_we_die"),
                    ("why do bad things happen to good people", "why_bad_things"),
                    ("is there any point to all this", "meaning_point"),
                    ("how do I forgive someone who hurt me", "how_forgive"),
                    ("who is jesus really", "who_is_jesus"),
                    ("how do I pray", "how_to_pray"),
                    ("am I good enough for God", "good_enough")):
        m = seekers.match(q)
        assert m and m["id"] == want, f"{q!r} -> {m and m['id']}"
        assert len(m["answer"]) > 200, "a real answer, not a caption"
        assert m["refs"], "the actual text always comes along"


def test_mundane_text_never_matches():
    for q in ("what is 15 percent of 240", "convert 10 miles to kilometers",
              "the weather is nice today", "what is the boiling point of water"):
        assert seekers.match(q) is None, f"{q!r} must never be met with the great questions"


def test_every_reference_resolves():
    from concordance.verifiers.scripture import read_passage
    bad = [r for r in seekers.all_refs() if read_passage(r).get("status") != "ok"]
    assert not bad, f"refs that do not resolve: {bad}"


def test_the_answers_demonstrate_and_never_hide():
    """Never hide: the builders' own conclusion is named. Never preach: the person's freedom to
    weigh is explicit, and no answer commands belief."""
    blob = " ".join(q["answer"] for q in seekers.QUESTIONS).lower()
    assert "concluded" in blob or "built by people who" in blob, "who we are is said plainly"
    for q in seekers.QUESTIONS:
        a = q["answer"].lower()
        assert "you must believe" not in a and "you have to accept" not in a, \
            f"{q['id']}: demonstrate, don't command"
    # honesty about the tool's limits appears where the biggest claims live
    assert "no website settles" in seekers.QUESTIONS[0]["answer"].lower() or \
           "settles it" in seekers.QUESTIONS[0]["answer"].lower()


def test_the_great_questions_outrank_the_card_search():
    from concordance import ask
    from concordance.config import EngineConfig
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    try:
        cfg = EngineConfig("witness")
        d = ask.respond("is God even real", cfg, gate_open=True)
        assert d.get("kind") == "seeker", f"routed to {d.get('kind')} — the filing cabinet again"
        assert d.get("scripture"), "the actual text comes with the answer"
        assert d.get("generated") is False, "curated, never generated at answer time"
        # comfort never arrives without a word (the zero-scripture gap, fixed the same day)
        d2 = ask.respond("I feel like everything is falling apart around me", cfg, gate_open=True)
        if d2.get("kind") == "comfort":
            assert d2.get("scripture"), "kindness with no word is the gap the probe caught"
        # and the mundane gate behavior is untouched
        d3 = ask.respond("what is 15 percent of 240", cfg, gate_open=True)
        assert d3.get("kind") != "seeker"
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior


if __name__ == "__main__":
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the biggest questions get real answers, plainly.")
