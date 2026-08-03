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
    fix = corpus.Corpus(cards, min_idf=0.0)
    hits = fix.search("cell", limit=5)
    assert hits and hits[0]["id"] == "t", (
        "a book that merely repeats the word outranked the theory: "
        + ", ".join(h["id"] for h in hits))
    # and the boost cannot reach a card the partition refused
    assert all(h["id"] != "x" for h in fix.search("cell", limit=5)), \
        "an off-subject card was admitted"
    assert corpus.THEORY_WEIGHT > 1.0
