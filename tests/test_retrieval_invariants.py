"""RETRIEVAL INVARIANTS — the librarian's own laws, learned the hard way on 2026-08-02.

One user report ("it doesn't have anything for southern baptists") exposed five defects in the
ranking path, every one invisible to the suites that covered the layers beneath it. These are
those defects encoded as standing, machine-checked law — the fleet turned inward. The 66 domain
verifiers check the world's claims; this file checks the librarian they all depend on.

The invariants:

  I.   DETERMINISM — the same query over the same cards yields the same ranking, regardless of
       construction order or hash seed. The candidate pool once filled in set-iteration order:
       one restart returned 8 Baptist histories, the next returned 1, same query, same corpus.
       A ranking that changes with a restart cannot be trusted or tested.
  II.  NO STARVATION — a common word can never crowd the subject's cards out of the candidate
       pool (df 2,702 vs 160 once flooded the 600-cap before the rare token was reached).
  III. THE FAMILY HOLDS — a card holding the subject in EITHER number reaches the upper tier;
       the singular-only voice card must answer the plural question.
  IV.  THE SEAT IS ASKED — the subject seat belongs to the words the person actually typed;
       neither an absent token (df=0 reads as maximal rarity) nor an expansion variant
       ("southerns") may hold it.
  V.   HELD SUBJECTS ANSWER — the probe queries that actually failed live must return results
       whose top hit is about the subject asked. Run against the real local corpus, so a
       regression on real data cannot hide behind a green fixture.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CONCORDANCE_CARDS_JSONL", str(ROOT / "data" / "cards.jsonl"))

import pytest  # noqa: E402

from concordance import corpus  # noqa: E402


def _fixture_cards():
    cards = {}
    for i in range(650):                    # the flood: a common word far past the cap
        cards[f"s{i}"] = {"id": f"s{i}", "title": f"southern note {i}",
                          "body": "a southern matter", "lifecycle_stage": "public"}
    for i in range(3):                      # the subject: rare, and the point
        cards[f"b{i}"] = {"id": f"b{i}", "title": f"Baptists of town {i}",
                          "body": "the baptists gathered", "lifecycle_stage": "public"}
    cards["v"] = {"id": "v", "title": "Methodist / Wesleyan",
                  "body": "the methodist tradition confesses", "lifecycle_stage": "public"}
    return cards


def test_I_determinism_across_construction_orders():
    """Two corpora over the SAME cards inserted in OPPOSITE orders must rank identically.
    Before the fix, candidate order followed set-iteration order — hash-seed and insertion
    dependent — so this exact assertion would flap between runs."""
    items = list(_fixture_cards().items())
    a = corpus.Corpus(dict(items), min_idf=0.0)
    b = corpus.Corpus(dict(reversed(items)), min_idf=0.0)
    for q in ("southern baptists", "methodists", "baptists gathered"):
        ra = [h["id"] for h in a.search(q, limit=10)]
        rb = [h["id"] for h in b.search(q, limit=10)]
        assert ra == rb, f"construction order changed the ranking for {q!r}: {ra} vs {rb}"
        assert a._candidates({"southern", "baptists"}) == b._candidates({"southern", "baptists"})


def test_II_no_starvation_under_the_cap():
    fix = corpus.Corpus(_fixture_cards(), min_idf=0.0)
    cand = set(fix._candidates({"southern", "baptists"}))
    for i in range(3):
        assert f"b{i}" in cand, "the common word starved the subject from the pool"
    got = {h["id"] for h in fix.search("southern baptists", limit=8)}
    assert {"b0", "b1", "b2"} <= got


def test_III_the_family_holds_in_both_directions():
    fix = corpus.Corpus(_fixture_cards(), min_idf=0.0)
    hits = fix.search("methodists", limit=4)          # plural asks, singular card answers
    assert hits and hits[0]["id"] == "v"
    hits2 = fix.search("baptist gathered", limit=6)   # singular asks, plural cards answer
    assert any(h["id"].startswith("b") for h in hits2)


def test_IV_the_seat_belongs_to_the_asked_words():
    fix = corpus.Corpus(_fixture_cards(), min_idf=0.0)
    asked = {"southern", "baptists"}
    seat = fix._subject_of(asked, fix._idf(asked))
    assert seat in ("baptists", "baptist"), f"the seat left the asked family: {seat!r}"
    # a PRESENT form is never rewritten ("methodist" is in the fixture's voice card verbatim);
    # an ABSENT one maps to its present family member ("baptist" -> "baptists" here, where only
    # the plural exists) — the first draft of this test asserted the opposite of its own fixture
    assert fix._present_form("methodist") == "methodist"
    assert fix._present_form("baptist") == "baptists"


@pytest.mark.skipif(not (ROOT / "data" / "cards.jsonl").exists(),
                    reason="real corpus not present")
def test_V_the_queries_that_failed_live_now_answer_about_their_subject():
    """The regression suite nobody can argue with: the exact asks that failed a real person.
    Runs on the REAL local corpus — a green fixture cannot cover for red data."""
    probes = {
        "Tell me about the Wesleyan Church": ("wesley",),
        "southern baptists": ("baptist",),
        "methodists": ("methodist",),
    }
    for q, needles in probes.items():
        hits = corpus.search(q, limit=6) or []
        assert hits, f"{q!r} returned nothing from a corpus that holds it"
        top = " ".join(str(hits[0].get(k) or "") for k in ("title", "body")).lower()
        assert any(n in top for n in needles), \
            f"{q!r}: top hit {hits[0].get('title')!r} is not about the subject"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))


def test_VI_a_theory_outranks_an_incidental_mention():
    """Matt, 2026-08-02: "Theories should be weighted heavier than a standard card."

    The theories shelf is 99 cards out of ~550,000, each one something the sciences actually run
    on and each now carrying its place in the assembled floor — what it rests on, what limits it,
    what shares its form. When a reader's question touches one, the theory is the card that
    orients everything else, so it must outrank a book that happens to use the same word.

    The boost is applied INSIDE the already-scoring branch, so it can only reorder cards the
    subject partition already admitted — it can never smuggle in an off-subject hit. That is the
    property this test pins, in both directions.

    PADDED WITH DECOYS 2026-11-17, and the padding is the point. On three cards df == n, so
    `_idf` returns 0 for every token and BOTH subject-holders score a base of exactly 0 — this
    test then passed for a reason that had nothing to do with the theories shelf: the only number
    separating them was THEORY_WEIGHT multiplying the tier constant, which is the defect invariant
    X now forbids. test_VII's own docstring had already named this fixture as degenerate. With the
    decoys, idf(cell) is positive, the two cards have real and DIFFERENT base scores (the diary
    repeats "cell" twice as often), and the theory still leads — which is what Matt asked for and
    what this test always meant to check.
    """
    cards = {
        "t": {"id": "t", "title": "Cell theory", "shelf": "theories",
              "body": "cell theory as the sciences run on it", "lifecycle_stage": "public"},
        "b": {"id": "b", "title": "A country diary", "shelf": "gutenberg",
              "body": "the cell of the monk, a cell of bees, cell after cell in the old wall",
              "lifecycle_stage": "public"},
        "x": {"id": "x", "title": "Unrelated", "shelf": "gutenberg",
              "body": "harvesting barley", "lifecycle_stage": "public"},
    }
    for i in range(20):                     # no "cell" at all — so idf(cell) is not flat zero
        cards[f"d{i}"] = {"id": f"d{i}", "title": f"Decoy volume {i}", "shelf": "gutenberg",
                          "body": f"an unrelated passage about decoy subject {i}",
                          "lifecycle_stage": "public"}
    fix = corpus.Corpus(cards, min_idf=0.0)
    assert fix._idf({"cell"})["cell"] > 0, "the fixture is degenerate again — pad it"
    hits = fix.search("cell", limit=5)
    assert hits and hits[0]["id"] == "t", (
        "a book that merely repeats the word outranked the theory: "
        + ", ".join(h["id"] for h in hits))
    # and the boost cannot reach a card the partition refused
    assert all(h["id"] != "x" for h in fix.search("cell", limit=5)), \
        "an off-subject card was admitted"


def test_VII_substance_outranks_a_bare_pointer_that_holds_the_same_subject():
    """docs/SOP/subsystems/keeping.md's own 'Refine': within the subject tier, a card that
    ANSWERS the question must outrank one that merely NAMES it. ~67% of the keeping are stubs
    (a pronunciation guide, a bare title+link); the subject partition alone can tell "about this"
    from "not about this," never a thin gloss from a real excerpt. Padded with 20 unrelated decoy
    cards so the subject token's idf is meaningfully positive — with too small a fixture (as in
    test_VI's 3 cards) two subject-holders can both score a base of 0 and tie in the tier for a
    reason that has nothing to do with this fix; the ranker's own comment on `_score` explains why."""
    stub_body = "zorlaxian"                                       # < STUB_BODY_CHARS: a bare pointer
    substance_body = (
        "Zorlaxian is a fictional demonym invented for this test; it names a people and a place, "
        "and this sentence exists only to push the body length past the substance threshold so "
        "the ranker can tell a real answer from a pointer that merely repeats the headword.")
    assert len(stub_body) < corpus.STUB_BODY_CHARS
    assert len(substance_body) >= corpus.STUB_BODY_CHARS
    cards = {
        # neither title is an exact match to the query "zorlaxian" alone — search()'s own
        # exact-title boost (9.0x, deliberately larger than SUBSTANCE_WEIGHT) is a different,
        # already-tested signal; a title of bare "Zorlaxian" would collide with it here and
        # test the wrong thing.
        "p": {"id": "p", "title": "Zorlaxian pronunciation guide", "shelf": "words",
              "body": stub_body, "lifecycle_stage": "public"},
        "a": {"id": "a", "title": "On the Zorlaxian people", "shelf": "gutenberg",
              "body": substance_body, "lifecycle_stage": "public"},
        "x": {"id": "x", "title": "Unrelated", "shelf": "gutenberg",
              "body": "harvesting barley", "lifecycle_stage": "public"},
    }
    for i in range(20):                                            # decoys: no "zorlaxian" at all
        cards[f"d{i}"] = {"id": f"d{i}", "title": f"Decoy volume {i}", "shelf": "gutenberg",
                          "body": f"an unrelated passage about decoy subject {i}",
                          "lifecycle_stage": "public"}
    fix = corpus.Corpus(cards, min_idf=0.0)
    hits = fix.search("zorlaxian", limit=5)
    assert hits and hits[0]["id"] == "a", (
        "a bare pointer outranked the card that actually answers the question: "
        + ", ".join(h["id"] for h in hits))
    assert "p" in [h["id"] for h in hits], "the pointer should still be admitted, just ranked lower"
    # and the boost cannot reach a card the partition refused
    assert all(h["id"] != "x" for h in hits), "an off-subject card was admitted"
    assert corpus.SUBSTANCE_WEIGHT > 1.0
    assert corpus.THEORY_WEIGHT > 1.0


def test_VIII_a_pronunciation_card_never_leads_a_bare_subject_lookup():
    """Measured live 2026-09-03: EVERY single-word subject lookup led with a phonetic string, because
    a pronunciation card's title IS its headword (all ~125k of them), so it won the exact-title boost
    (9.0x) for any bare word — "gravity" returned "G R AE1 V AH0 T IY0" ahead of the definition and
    every substantive card. The pronunciation genre is enrichment (the tongues->Word weave), never the
    lead answer to "what is X". This pins that the exact-title boost is withheld from that one genre,
    so the substantive card leads — while pronunciation is still ADMITTED (a reader who wants it, or a
    subject we hold nothing else for, still finds it)."""
    # the phonetic body clears STUB_BODY_CHARS on CMU boilerplate alone — proof the substance signal
    # cannot catch this, so the genre rule must (exactly the live case).
    pron_body = ("gravity: pronounced (ARPABET) G R AE1 V AH0 T IY0. From the CMU Pronouncing "
                 "Dictionary, the standard machine-readable pronunciations of North American English.")
    assert len(pron_body) >= corpus.STUB_BODY_CHARS          # NOT a stub — clears the bar on boilerplate
    defn_body = ("gravity: (noun) (physics) the force of attraction between all masses in the "
                 "universe; also a manner that is serious and solemn.")
    cards = {
        "pron": {"id": "pron", "title": "gravity", "shelf": "pronunciation",
                 "body": pron_body, "lifecycle_stage": "public"},
        "defn": {"id": "defn", "title": "gravity", "shelf": "dictionary",
                 "body": defn_body, "lifecycle_stage": "public"},
    }
    for i in range(20):                                       # decoys so "gravity" idf is positive
        cards[f"d{i}"] = {"id": f"d{i}", "title": f"Decoy volume {i}", "shelf": "gutenberg",
                          "body": f"an unrelated passage about decoy subject {i}",
                          "lifecycle_stage": "public"}
    fix = corpus.Corpus(cards, min_idf=0.0)
    hits = fix.search("gravity", limit=5)
    assert hits and hits[0]["id"] == "defn", (
        "a phonetic guide led a bare subject lookup over the definition: "
        + ", ".join(f"{h['id']}[{h.get('shelf')}]" for h in hits))
    assert "pron" in [h["id"] for h in hits], "pronunciation should still be admitted, just not the lead"
    # and when pronunciation is ALL we hold for the subject, it must still answer (nothing to
    # demote it below) — drop only the definition, keep pronunciation + the decoys.
    only_pron = corpus.Corpus({k: v for k, v in cards.items() if k != "defn"}, min_idf=0.0)
    solo = only_pron.search("gravity", limit=3)
    assert solo and solo[0]["id"] == "pron", "with nothing else held, the pronunciation card must still lead"


# ── IX. THE SEAT IS A SUBJECT ─────────────────────────────────────────────────────────────────
# Measured live on 923,965 cards, 2026-11-16: `i'm` is the RAREST token in a natural first-person
# sentence (idf 10.645, above `doctor` 7.647 and `grief` 7.286) because a public-domain keeping
# spells contractions out, so it took the subject seat — and its +1000 tier — for all five
# pastoral questions at once. Marriage, grief, money, sickness and doubt each came back with the
# same six cards: Dorothy Parker's "Men I'm Not Married To" and a pronunciation card titled `i'm`.
# Stopping contractions moved the seat to `afford`, which the keeping holds one 207-byte gloss
# about, and the answers were still wrong. Rarity is not subjecthood, and this fixture is that
# failure in miniature: the engine's own dictionary shelf says which words it can be ABOUT.

def _seat_cards():
    cards = {}
    for i in range(25):                      # decoys: `see` is common here, as it is in the keeping
        cards[f"d{i}"] = {"id": f"d{i}", "title": f"Decoy volume {i}", "shelf": "gutenberg",
                          "body": f"an unrelated passage about decoy subject {i}; you can see it",
                          "lifecycle_stage": "public"}
    cards["parker"] = {"id": "parker", "title": "Men I'm Not Married To", "shelf": "gutenberg",
                       "body": "I'm not married to any of them, and I'm quite sure of it.",
                       "lifecycle_stage": "public"}
    for i in range(2):
        cards[f"aff{i}"] = {"id": f"aff{i}", "title": f"A Thin Purse {i}", "shelf": "gutenberg",
                            "body": "they could not afford the fare, and could not afford to wait.",
                            "lifecycle_stage": "public"}
    for i in range(4):
        cards[f"doc{i}"] = {"id": f"doc{i}", "title": f"The Country Doctor {i}", "shelf": "gutenberg",
                            "body": "the doctor came at once to the sick man and would take no fee.",
                            "lifecycle_stage": "public"}
    cards["sick5"] = {"id": "sick5", "title": "A Long Convalescence", "shelf": "gutenberg",
                      "body": "the sick man recovered slowly through the winter.", "lifecycle_stage": "public"}
    cards["zorl"] = {"id": "zorl", "title": "Zorlaxia and its people", "shelf": "gutenberg",
                     "body": "zorlaxia is a fictional land invented for this test.",
                     "lifecycle_stage": "public"}
    # the keeping's own lexicography — the ONE thing that separates a subject from a verb
    for w, body in (("afford", "afford: (verb) have the financial means to do something"),
                    ("doctor", "doctor: (noun) a licensed medical practitioner"),
                    ("sick", "sick: (adjective) not in good health - (noun) people who are sick"),
                    ("overwhelm", "overwhelm: (verb) overcome by superior force"),
                    ("build", "build: (verb) make or form by combining materials"),
                    ("building", "building: (noun) a structure that has a roof and walls")):
        cards[w] = {"id": w, "title": w, "shelf": "dictionary", "body": body,
                    "lifecycle_stage": "public"}
    return cards


def test_IX_the_seat_is_a_subject_never_a_contraction_or_a_verb():
    fix = corpus.Corpus(_seat_cards(), min_idf=0.0)
    asked = {"i'm", "sick", "can't", "afford", "see", "doctor"}
    idf = fix._idf(asked)

    # the trap, stated: ungated, the seat goes to a contraction — in the fixture as in the keeping
    ungated = max(asked, key=lambda t: idf.get(t, 0.0))
    assert ungated in ("can't", "i'm"), f"the fixture no longer reproduces the trap (rarest: {ungated!r})"

    assert fix._subject_of(asked, idf) == "doctor", (
        "the seat left the subject: " + repr(fix._subject_of(asked, idf)))

    # and the whole answer follows the seat: the Parker card is not merely demoted, the subject
    # partition excludes it, because nothing in it is about a doctor
    hits = fix.search("I'm sick and I can't afford to see a doctor", limit=5)
    assert hits, "a question the keeping can answer returned nothing"
    assert hits[0]["id"].startswith("doc"), (
        "top hit is not about the subject: " + ", ".join(h["id"] for h in hits))
    assert all(h["id"] != "parker" for h in hits), (
        "a card held only by a contraction reached the answer: " + ", ".join(h["id"] for h in hits))


def test_IX_the_gate_refuses_only_what_the_keeping_calls_a_non_noun():
    from concordance.corpus_db import carries_subject
    fix = corpus.Corpus(_seat_cards(), min_idf=0.0)

    # a clitic spells out to a word the stop list already holds — no list of contractions needed
    for t in ("i'm", "can't", "don't", "that's", "he's", "i've", "we're", "i'd", "i'll", "isn't"):
        assert not carries_subject(t), f"{t!r} carries no subject of its own"
    # a POSSESSIVE does (its head is the subject), and an apostrophe that is not a clitic is untouched
    for t in ("shepherd's", "god's", "o'clock", "doctor", "grief"):
        assert carries_subject(t), f"{t!r} names something"

    assert fix._seatable("doctor") and not fix._seatable("afford")
    assert not fix._seatable("i'm")
    # an INFLECTED form is judged by its lemma — looked up, never rewritten — and the token's own
    # entry is always tried first, so a word the dictionary knows in its own right is safe
    assert not fix._seatable("overwhelmed"), "a participle of a verb is not a subject"
    assert fix._seatable("building"), "its own noun sense must outrank its stem's verb sense"
    # THE SAFE DEFAULT: a word the dictionary never held is admitted, so the gate can never refuse
    # the seat to a subject it simply does not know (`taoism`, `carburetor`, `baofeng`, `zoroaster`
    # are all measured cases — one-word titles, short bodies, unknown to no fault of their own)
    assert fix._seatable("zorlaxia")
    assert fix._subject_of({"zorlaxia", "doctor"}, fix._idf({"zorlaxia", "doctor"})) == "zorlaxia"

    # AND IT STANDS ASIDE RATHER THAN ABOLISH THE PARTITION: when every asked word is refused, the
    # rarest takes the seat exactly as before — a gate that cannot name a better subject has no
    # business removing the one protection the ranking has.
    both_refused = {"afford", "can't"}
    assert fix._subject_of(both_refused, fix._idf(both_refused)) is not None

    # a keeping with no dictionary shelf (every other fixture in this file) gates nothing. The shard
    # half is stubbed out explicitly: whether a built corpus.db sits beside this checkout is an
    # accident of the machine, and an invariant may not depend on one.
    from concordance import corpus_db as _cdb
    _real = _cdb.noun_senses
    _cdb.noun_senses = lambda shelf="dictionary": {}
    try:
        bare = corpus.Corpus(_fixture_cards(), min_idf=0.0)
        assert bare._senses() == {}
        assert bare._seatable("afford"), "with no lexicography held, the gate must stand down"
    finally:
        _cdb.noun_senses = _real


# ── X. THE TIER IS A PARTITION, AND THE BOOSTS ORDER WITHIN IT ────────────────────────────────
# Measured over the 68 real questions 2026-11-17, with the engine's own scorer. `_score` ADDS
# SUBJECT_TIER (1000.0) and search()'s `_finalize` then MULTIPLIED the sum, so the shelf boost
# scaled the tier constant instead of ordering cards inside it. Twenty-six of the sixty-eight
# questions were led by a `theories` card whose term frequency of the subject was ONE OR TWO:
#
#   "i want to end my life"                   Agricultural science (base 2.94) led
#                                             17.2 End-of-Life Care (base 24.35)
#   "how do I keep a wound from bleeding"     The double helix (base 11.8) led
#                                             8.3 Wound Management (base 58.2)
#   "a man who built his house on the rock"   Hydrologic cycle (base 9.9) led
#                                             John Gill on Deuteronomy 32:4 (base 21.6)
#
# In every case the demoted card had the HIGHER base score, so the order contradicted the engine's
# own measure of relevance — and it did so most loudly for the readers who can least afford it.
# Three aboutness gates on tier ENTRY were measured first and all three refused: requiring the
# subject in the card's own prose, and requiring it outside the source label, each changed NOTHING
# on 68 of 68 (vacuous); the one with teeth dropped "7.3 Prepare Financial Budgets" for a Greek
# lexicon entry and Newton's law of universal gravitation for "1.4 Inverse Functions". The defect
# was never which cards the tier admits. It was the arithmetic.


def _tier_cards(n_decoys: int = 24):
    """A theories card that MENTIONS the subject once, and a card that is plainly ABOUT it."""
    cards = {
        "th": {"id": "th", "title": "Plasma physics (the fourth state of matter)",
               "shelf": "theories", "lifecycle_stage": "public",
               "body": ("A plasma is an ionised gas whose free charges make it respond to fields "
                        "collectively; it carries current, supports waves, and in a pinch can be "
                        "wound into a torus by the magnets that confine it, which is the whole "
                        "difficulty of fusion engineering.")},
        "ab": {"id": "ab", "title": "Wound management", "shelf": "medicine",
               "lifecycle_stage": "public",
               "body": ("Clean the wound with running water. A wound that keeps bleeding needs "
                        "direct pressure held on the wound for ten minutes without lifting it to "
                        "look. Dress the wound, raise the wound above the heart, and watch the "
                        "wound for the spreading redness that means the wound is infected.")},
    }
    for i in range(n_decoys):
        cards[f"d{i}"] = {"id": f"d{i}", "title": f"Decoy volume {i}", "shelf": "gutenberg",
                          "body": f"an unrelated passage about decoy subject {i}",
                          "lifecycle_stage": "public"}
    return cards


def test_X_a_shelf_boost_never_outranks_relevance_inside_the_tier():
    """THE LIVE SHAPE: both cards hold the subject, so both are in the tier; one is about it.

    Red before the fix, by a factor of four: (base + 1000) x THEORY_WEIGHT put the plasma card at
    ~4000 against the wound card's ~1000, so a reader asking how to stop a wound bleeding was
    handed a card about confining fusion plasma. The boosts must order cards WITHIN the tier —
    which is what every comment in `_finalize` already claimed — so they are applied to the BASE
    score and the tier is added afterwards, as a flag that nothing multiplies.
    """
    fix = corpus.Corpus(_tier_cards(), min_idf=0.0)
    hits = fix.search("wound", limit=5)
    ids = [h["id"] for h in hits]
    assert ids and ids[0] == "ab", (
        "a shelf boost outranked the card that is actually about the subject: " + ", ".join(ids))
    # the theory is DEMOTED, never suppressed — invariant VI's law still holds on its own shelf
    assert "th" in ids, "the theories card must still be admitted, just ranked below the answer"
    assert corpus.THEORY_WEIGHT > 1.0 and corpus.SUBSTANCE_WEIGHT > 1.0


def test_X_no_boost_however_large_crosses_the_partition():
    """AND THE PARTITION WAS BREACHABLE FROM BELOW — the half nobody had tested.

    SUBJECT_TIER is documented as "larger than any reachable TF-IDF score", but the boosts
    multiplied it, and they multiply an OFF-SUBJECT card's score just as happily: 9x for an exact
    title, 4x for a full-phrase title, 4x for the theories shelf, 2x for substance. A card that
    does not hold the subject at all, with a repeated rare word and an exact verse title, reaches
    several thousand and passes a tier-holder whose own base is near zero. Constructed, not
    observed — but reachable live, and "a partition, not a weight" has to mean it.
    """
    from concordance import growth as _growth
    assert "John 3:16" in _growth.refs_in_text("zorlaxian John 3:16"), \
        "the fixture depends on the verse canonicalizer recognising the ref"
    cards = {
        # off subject (no "zorlaxian"), but an exact verse title (9x) over a huge repeated-token base
        "verse": {"id": "verse", "title": "John 3:16", "shelf": "scripture",
                  "lifecycle_stage": "public", "body": "john " * 1000},
        # holds the subject, and almost nothing else: a short note, no boost of any kind
        "z": {"id": "z", "title": "A zorlaxian note", "shelf": "gutenberg",
              "lifecycle_stage": "public", "body": "zorlaxian"},
        "j": {"id": "j", "title": "Another john", "shelf": "gutenberg",      # so john loses the seat
              "lifecycle_stage": "public", "body": "john was here"},
    }
    for i in range(300):
        cards[f"d{i}"] = {"id": f"d{i}", "title": f"Decoy volume {i}", "shelf": "gutenberg",
                          "body": f"an unrelated passage about decoy subject {i}",
                          "lifecycle_stage": "public"}
    fix = corpus.Corpus(cards, min_idf=0.0)
    asked = {"zorlaxian", "john"}
    assert fix._subject_of(asked, fix._idf(asked)) == "zorlaxian", "the fixture lost its seat"
    hits = fix.search("zorlaxian John 3:16", limit=5)
    ids = [h["id"] for h in hits]
    assert ids and ids[0] == "z", (
        "a boosted off-subject card crossed the subject partition: " + ", ".join(ids))
    assert "verse" not in ids, "and the tier filter must still serve only subject-holders"
