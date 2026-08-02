"""A comparison names what is missing — it never sets two things side by side when one is absent.

Matt, 2026-08-01, having asked the library to compare and contrast Nazarene vs Wesleyan:
*"Nothing worth reading. We don't want to set our rules so tight we can provide no value."*

Both halves of that are load-bearing. The old behaviour put two subjects in one bag of words,
returned six Wesleyan cards, and said nothing about the missing side — half a question answered as
though it were whole. But the cure is not more refusal: COMPOSITION IS NOT GENERATION. Arranging
two voice cards on shared axes, every cell attributable, is the concordance doing its work.

HAVING THE WORD IS NOT HAVING THE THING — the trap this feature exists to avoid. "Nazarene"
matches five cards about Jesus of Nazareth. A naive count would report the subject held and
cheerfully compare a denomination against a biblical epithet. The `churches` shelf is the registry
of traditions we actually cover, so that is the test.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import compare  # noqa: E402

VOICE = {"id": "c_wes", "title": "Methodist / Wesleyan", "shelf": "churches",
         "body": "Confession: the Articles of Religion (Wesley).",
         "connections": [{"to_card_id": "c_root"}, {"to_card_id": "c_x"}]}
VOICE2 = {"id": "c_bap", "title": "Baptist", "shelf": "churches", "body": "Baptist tradition.",
          "connections": [{"to_card_id": "c_root"}]}
# The word, not the thing: cards that MENTION "Nazarene" but are about Jesus of Nazareth.
WORD_ONLY = [{"id": "c_naz1", "title": "Easton: Nazarene", "shelf": "dictionary", "body": "of Nazareth"},
             {"id": "c_naz2", "title": "ISBE: Nazarene", "shelf": "encyclopedia", "body": "Nazarene"}]


def _fake(mapping):
    return lambda q, limit=8, **k: mapping.get(q.lower(), [])


# ── reading the question ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("q,expect", [
    ("compare and contrast Nazarene vs Wesleyan", ["Nazarene", "Wesleyan"]),
    ("Baptist vs Presbyterian", ["Baptist", "Presbyterian"]),
    ("difference between Anglican and Methodist", ["Anglican", "Methodist"]),
    ("contrast Lutheran with Reformed", ["Lutheran", "Reformed"]),
])
def test_a_comparison_is_read_as_two_subjects(q, expect):
    assert compare.subjects_of(q) == expect


@pytest.mark.parametrize("q", ["what is grace", "Wesleyan Church", "", "   ", "compare"])
def test_an_ordinary_question_is_not_a_comparison(q):
    """The parse must not hijack normal questions — a comparison path for everything is worse."""
    assert compare.subjects_of(q) is None


def test_the_same_subject_twice_is_not_a_comparison():
    assert compare.subjects_of("Baptist vs Baptist") is None


# ── the honesty that was missing ──────────────────────────────────────────────────────────────
def test_a_missing_side_is_named_and_never_filled():
    r = compare.compare("compare and contrast Nazarene vs Wesleyan",
                        search=_fake({"nazarene": WORD_ONLY, "wesleyan": [VOICE]}))
    assert r["missing"] == ["Nazarene"]
    assert "no tradition card for Nazarene" in r["message"]
    assert "will not set two things side by side" in r["message"]


def test_holding_the_WORD_is_not_holding_the_THING():
    """Five cards about Jesus of Nazareth must not count as holding the denomination."""
    r = compare.compare("Nazarene vs Wesleyan",
                        search=_fake({"nazarene": WORD_ONLY, "wesleyan": [VOICE]}))
    naz = [s for s in r["sides"] if s["subject"] == "Nazarene"][0]
    assert naz["mentions"] == len(WORD_ONLY), "the mentions are real and are reported"
    assert naz["held_as_tradition"] is False, (
        "a card that merely contains the word must never count as the tradition")
    assert "dictionary" in naz["shelves"], "and we say WHAT we hold instead"


def test_a_missing_side_offers_the_want_but_does_not_open_it():
    """A person asks, a person chooses — the same rule as the want desk."""
    r = compare.compare("Nazarene vs Wesleyan",
                        search=_fake({"nazarene": [], "wesleyan": [VOICE]}))
    assert r["want"] and r["want"]["queries"] == ["Nazarene"]


def test_both_held_composes_without_asserting():
    r = compare.compare("Baptist vs Wesleyan",
                        search=_fake({"baptist": [VOICE2], "wesleyan": [VOICE]}))
    assert r["missing"] == []
    assert all(s["held_as_tradition"] for s in r["sides"])
    assert [s["voice"]["title"] for s in r["sides"]] == ["Baptist", "Methodist / Wesleyan"]


def test_shared_ground_is_read_from_the_cards_never_claimed():
    """The common root is evidence — an edge both voice cards actually carry."""
    r = compare.compare("Baptist vs Wesleyan",
                        search=_fake({"baptist": [VOICE2], "wesleyan": [VOICE]}))
    assert r["shared_ground"] == ["c_root"], "only the edge BOTH hold"
    assert "c_x" not in r["shared_ground"], "an edge only one side has is not shared ground"


def test_membership_is_not_doctrine():
    """The first live both-sides run (Baptist vs Presbyterian, 2026-08-01) reported the shelf
    spine as the traditions' shared ground — true the way two books share a bookcase, and useless
    in exactly that way, since EVERY tradition on the shelf carries the same member_of edge. A
    vacuous truth presented as a finding teaches a reader to stop reading the findings."""
    a = dict(VOICE, connections=[
        {"to_card_id": "card_spine_churches", "relationship": "member_of"},
        {"to_card_id": "c_creeds", "relationship": "calibrated_against"}])
    b = dict(VOICE2, connections=[
        {"to_card_id": "card_spine_churches", "relationship": "member_of"},
        {"to_card_id": "c_creeds", "relationship": "calibrated_against"}])
    r = compare.compare("Baptist vs Wesleyan",
                        search=_fake({"baptist": [b], "wesleyan": [a]}))
    assert r["shared_ground"] == ["c_creeds"], "the bookcase was reported as common doctrine"

    # and when the spine is ALL they share, the honest answer is nothing — never padded
    a2 = dict(VOICE, connections=[{"to_card_id": "card_spine_churches",
                                   "relationship": "member_of"}])
    b2 = dict(VOICE2, connections=[{"to_card_id": "card_spine_churches",
                                    "relationship": "member_of"}])
    r2 = compare.compare("Baptist vs Wesleyan",
                         search=_fake({"baptist": [b2], "wesleyan": [a2]}))
    assert r2["shared_ground"] == []


def test_the_voice_arrives_full_not_as_a_brief():
    """Search hands back BRIEFS; the first live run presented voice cards with body None while
    the message promised 'the tradition's own voice, in its own reckoning'. The voice is the one
    card whose whole point is its content, so it is rehydrated through `get` — and a `get` that
    fails falls back to the brief rather than losing the column."""
    brief = {"id": "c_wes", "title": "Methodist / Wesleyan", "shelf": "churches", "body": None}
    full = dict(VOICE, body="Confession: the Articles of Religion. Emphasis: grace freely offered.")
    r = compare.compare("Baptist vs Wesleyan",
                        search=_fake({"baptist": [VOICE2], "wesleyan": [brief]}),
                        get={"c_wes": full, "c_bap": VOICE2}.get)
    wes = [s for s in r["sides"] if s["subject"] == "Wesleyan"][0]
    assert wes["voice"]["body"].startswith("Confession:"), "the voice stayed a bodiless brief"

    def boom(_):
        raise RuntimeError("no corpus here")
    r2 = compare.compare("Baptist vs Wesleyan",
                         search=_fake({"baptist": [VOICE2], "wesleyan": [brief]}), get=boom)
    wes2 = [s for s in r2["sides"] if s["subject"] == "Wesleyan"][0]
    assert wes2["held_as_tradition"] is True, "a failed lookup must not unmake the tradition"


def test_shared_ground_is_not_computed_when_a_side_is_missing():
    """Nothing is shared with something that is not here."""
    r = compare.compare("Nazarene vs Wesleyan",
                        search=_fake({"nazarene": WORD_ONLY, "wesleyan": [VOICE]}))
    assert r["shared_ground"] == []


def test_nothing_in_the_answer_is_authored():
    """Every cell must be a card. The module may name absence; it may not write substance."""
    r = compare.compare("Baptist vs Wesleyan",
                        search=_fake({"baptist": [VOICE2], "wesleyan": [VOICE]}))
    for s in r["sides"]:
        for c in s["cards"]:
            assert c.get("id"), "a cell with no card behind it is authored content"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))


# ── the pull: a missing side stands on its own documents ─────────────────────────────────────
SPAN = {"id": "card_span_naz1", "title": "PREAMBLE", "shelf": "sources",
        "body": "the doctrine and experience of sanctification as a second work of grace",
        "source": {"authority_tier": "primary_pd"}}


def test_a_missing_side_stands_on_documents_already_held_without_going_out():
    """SEARCH ONCE PER QUESTION (Matt, 2026-08-02). The Nazarene Manual's passages sat on the
    sources shelf while the comparison said "not here" — having the thing and not presenting it
    is a miss wearing a refusal. And when the keeping already holds the documents, the pull must
    NOT run: going out for what we hold is the search-once rule broken from the other side."""
    calls = []
    def spy_acquire(subject):
        calls.append(subject)
        return {"cards": []}
    r = compare.compare("Nazarene vs Wesleyan",
                        search=_fake({"nazarene": [SPAN], "wesleyan": [VOICE]}),
                        acquire=spy_acquire)
    naz = [s for s in r["sides"] if s["subject"] == "Nazarene"][0]
    assert naz["held_as_tradition"] is False, "documents are not a curated voice"
    assert naz.get("their_own_documents"), "held passages were not presented"
    assert calls == [], "the pull ran for a subject the keeping already holds"
    assert r["want"] is None, "a side standing on documents does not also beg"
    assert "its own documents" in r["message"]


def test_a_truly_absent_side_is_pulled_on_the_call_and_the_want_dies():
    """"I asked it to find the information, and it couldn't do that." Now it can: nothing held ->
    acquire runs -> the passages stand the side up -> no want, because offering a person a chore
    we just did is the want desk's rule inverted."""
    def acquire(subject):
        assert subject == "Nazarene"
        return {"status": "carded", "cards": [SPAN]}
    r = compare.compare("Nazarene vs Wesleyan",
                        search=_fake({"nazarene": [], "wesleyan": [VOICE]}),
                        acquire=acquire)
    naz = [s for s in r["sides"] if s["subject"] == "Nazarene"][0]
    assert naz.get("their_own_documents") == [SPAN]
    assert r["want"] is None
    assert "fetched and kept" in r["message"]


def test_when_even_the_pull_comes_back_empty_the_refusal_and_the_want_stand():
    r = compare.compare("Nazarene vs Wesleyan",
                        search=_fake({"nazarene": [], "wesleyan": [VOICE]}),
                        acquire=lambda s: {"status": "nothing_found", "cards": []})
    assert "cannot compare these honestly" in r["message"]
    assert r["want"] and r["want"]["queries"] == ["Nazarene"]


def test_a_pull_that_crashes_leaves_an_honest_refusal_not_a_500():
    def boom(subject):
        raise RuntimeError("the archives are down")
    r = compare.compare("Nazarene vs Wesleyan",
                        search=_fake({"nazarene": [], "wesleyan": [VOICE]}), acquire=boom)
    assert r["want"] is not None and "cannot compare" in r["message"]


def test_a_plural_finds_the_voice():
    """"methodists" failed to match the Methodist / Wesleyan voice LIVE, on a shelf that plainly
    holds the tradition — the plural blindness in its fourth home, the voice matcher."""
    r = compare.compare("southern baptists vs methodists",
                        search=_fake({"southern baptists": [],
                                      "methodists": [VOICE]}))
    m = [s for s in r["sides"] if s["subject"] == "methodists"][0]
    assert m["held_as_tradition"] is True, "the plural could not find its tradition"
    assert m["voice"]["title"] == "Methodist / Wesleyan"


def test_a_held_gutenberg_book_counts_as_a_document_to_stand_on():
    """southern baptists had 8 held PD documents and reported docs=0, because the already-held
    filter admitted only the sources shelf. A book the library holds whole is exactly what a
    missing side may stand on."""
    book = {"id": "g1", "title": "One hundred years with the Baptists of Amherst",
            "shelf": "gutenberg", "body": "the baptists of amherst..."}
    r = compare.compare("southern baptists vs Wesleyan",
                        search=_fake({"southern baptists": [book], "wesleyan": [VOICE]}))
    sb = [s for s in r["sides"] if s["subject"] == "southern baptists"][0]
    assert sb["held_as_tradition"] is False
    assert sb.get("their_own_documents"), "a shelf-full of held PD documents reported as nothing"
    assert r["want"] is None


def test_the_voice_is_asked_of_the_registry_not_won_in_a_popularity_contest():
    """Live, 2026-08-02: "methodists" ranked five Tyerman volumes above the Methodist / Wesleyan
    voice card, so the tradition read as undocumented while its registry card sat on the shelf.
    When the general results miss the voice, the churches shelf is asked DIRECTLY."""
    tyerman = [{"id": f"t{i}", "title": f"The Life of Wesley vol {i}", "shelf": "gutenberg",
                "body": "founder of the methodists"} for i in range(8)]
    def search(q, limit=8, shelves=None):
        if shelves == {"churches"}:
            return [VOICE]
        return tyerman[:limit]
    r = compare.compare("southern baptists vs methodists",
                        search=search)
    m = [s for s in r["sides"] if s["subject"] == "methodists"][0]
    assert m["held_as_tradition"] is True, \
        "the registry held the tradition and the popularity contest hid it"
    assert m["voice"]["title"] == "Methodist / Wesleyan"


def test_a_tradition_card_outranks_a_person_for_the_orienting_seat():
    """Spurgeon was presented as "southern baptists in its own reckoning" — a person is a voice
    OF a tradition, not the tradition's own reckoning. The person still orients when no
    tradition card matches at all."""
    spurgeon = {"id": "sp", "title": "Charles Spurgeon — Baptist", "shelf": "churches",
                "box": "voice", "body": "the voice baptists themselves hold highest"}
    tradition = {"id": "tr", "title": "Baptist", "shelf": "churches", "box": "tradition",
                 "body": "Baptist. Confession: the Second London Baptist Confession."}
    got = compare._voice_card("southern baptists", [spurgeon, tradition])
    assert got["id"] == "tr", "a person took the tradition's seat"
    assert compare._voice_card("southern baptists", [spurgeon])["id"] == "sp", \
        "with no tradition card, the person must still orient"
