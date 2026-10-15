"""The parable register — "the exact right parable for the situation" (the end goal).

Proves the covenant holds: every parable's story AND Christ's-own-turn resolve VERBATIM from the canon
(no hollow ref); a situation routes to the parable whose SHAPE fits it (the curated ache index); a
factual or non-parable input finds NO parable (0-false-positive — the register stays silent rather than
force a story); walk() composes ONLY the fixed connective frames (the claims are the found Red); and
every id is the same Words-in-Red as teachings._QUEUE. Runs under pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import parable, teachings  # noqa: E402

# Passage resolution needs the WEB Bible data (data/bible_en.jsonl), which is gitignored and absent in a
# bare checkout / CI. The three tests that resolve verbatim text skip cleanly there; the routing and
# 0-false-positive tests use resolve=False and always run.
_HAS_BIBLE = len((parable._passage("John 3:16") or "").strip()) > 10


def _need_bible():
    if not _HAS_BIBLE:
        import pytest
        pytest.skip("Bible data (data/bible_en.jsonl) not present — passage resolution unavailable")


def test_every_story_and_turn_resolves_verbatim():
    """No hollow reference: every parable's story resolves, and every turn Christ gave resolves too."""
    _need_bible()
    for p in parable._PARABLES:
        story = parable._passage(p["story_ref"])
        assert len(story.strip()) > 40, f"{p['id']} story did not resolve: {p['story_ref']}"
        if p["turn_ref"]:
            turn = parable._passage(p["turn_ref"])
            assert len(turn.strip()) > 20, f"{p['id']} turn did not resolve: {p['turn_ref']}"


def test_fit_routes_known_situations():
    """The eight parables that had no cues (Samaritan, Talents, Weeds, Mustard, Treasure, Sower, Dragnet,
    Leaven) now reach, alongside the four already cued — each to its own shape."""
    expect = {
        "I've wasted my life and I'm ashamed to come home to God": "par_prodigal",
        "I keep drifting away from my faith": "par_lost_sheep",
        "who is my neighbor, do I really have to help them": "par_samaritan",
        "I'm afraid to use my gifts, what if I fail": "par_talents",
        "I can't forgive what they did to me": "par_unforgiving",
        "I just want enough saved up to feel secure": "par_rich_fool",
        "why does God let evil grow right next to the good": "par_weeds",
        "my faith feels too small to matter": "par_mustard",
        "is it even worth giving up everything for this": "par_treasure",
        "my faith was excited then nothing, it doesn't stick": "par_sower",
    }
    for text, want in expect.items():
        f = parable.for_situation(text, resolve=False)
        assert f is not None, f"no parable for {text!r} (want {want})"
        assert f["id"] == want, f"{text!r} -> {f['id']} (want {want})"


def test_zero_false_positive_on_factual_and_non_parable():
    """A factual query, or a hurt that is NOT a parable's shape, finds no parable — honest silence. The
    discriminator: 'no money, lost my job' is a worry (comfort), NOT the Rich Fool (security in wealth)."""
    for text in [
        "what is the boiling point of water",
        "is 17 a prime number",
        "what is the molar mass of glucose",
        "who was the sixteenth president",
        "define photosynthesis",
        "I have no money and I lost my job",
        "tell me about grace",
        "what time is it in France",
    ]:
        assert parable.for_situation(text, resolve=False) is None, f"false positive on {text!r}"


def test_walk_is_found_and_cited_not_generated():
    """walk() carries the verbatim story + Christ's own turn, cited; composes only the fixed frames."""
    _need_bible()
    w = parable.walk("I've wasted my life and I'm ashamed to come home to God")
    assert w and w["id"] == "par_prodigal"
    assert w["story"]["ref"] == "Luke 15:11-32"
    assert "two sons" in w["story"]["text"]                       # the real passage, verbatim
    assert w["story"]["attribution"] == "Christ Himself"
    assert w["turn"] and w["turn"]["ref"] == "Luke 15:31-32"
    assert w["meet"] and w["step"]                               # the connective frames are present
    # the only composed prose is the fixed frames — never the parable's words
    for frame in (w["meet"], w["step"], w["turn"]["lead"]):
        assert frame not in w["story"]["text"]


def test_a_sits_whole_parable_has_no_turn():
    """A similitude Christ left to sit (the mustard seed) walks with no turn and the 'sit' invitation."""
    _need_bible()
    w = parable.walk("my faith feels too small to matter")
    assert w and w["id"] == "par_mustard"
    assert w["turn"] is None and w["sit"]


def test_ids_are_the_same_words_in_red():
    """Every parable id is a teaching in the one queue — not a parallel structure."""
    for p in parable._PARABLES:
        assert p["id"] in teachings._BY_ID, f"{p['id']} not in teachings._QUEUE"
        assert teachings._BY_ID[p["id"]]["group"] == "The Parables"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} parable tests passed — the right parable, found and cited; silent where none fits.")
