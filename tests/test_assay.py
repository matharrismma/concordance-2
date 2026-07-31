"""THE CARD ASSAY — the process for improving or removing a card, and the errors it must not repeat.

Matt, 2026-07-30: *"We need a process of improving or removing cards."*

The first and largest thing pinned here is a NEGATIVE: **length is never the test.** Two false
findings in one session came from length-shaped reasoning about cards —

  * a ≥120-character rule condemned 330 real Clarke notes, whose entire comment on 1 Chr 1:12 is
    *"Caphthorim — 'The Cappadocians.' — T."* (37 characters, and all he wrote);
  * 246 cards were reported as shipping a placeholder because their titles contained `_xxx`, which
    is the Roman numeral XXX.

Both were confident and numeric and wrong, and a process that removes cards cannot afford that
class of error even once. So the assay asks what a body DOES, and these tests make a short complete
card and a long empty one come out the right way round.

The second thing pinned is the bias: **improvement before removal**, and removal that is never a
deletion. A bare cross-reference is FAITHFUL to its source — the entry really does say "see HEADY"
— so it is never EMPTY; it is improvable into an edge. And a retraction mints a card carrying its
reason, because `docs/THE_RECORD.md` settled that deleting destroys the trail.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import assay as A  # noqa: E402


def _card(body, title="A title", **kw):
    c = {"id": "card_x", "title": title, "body": body,
         "source": {"label": "Adam Clarke, Commentary", "ref": "1 Chr 1:12"}}
    c.update(kw)
    return c


# ─────────────────────────────────────────────── length is not the test

def test_a_37_character_card_that_is_complete_STANDS():
    """The exact card a length rule already condemned once. It is the whole of what Clarke wrote."""
    clarke = _card("Caphthorim — \"The Cappadocians.\" — T.", title="Clarke on 1 Chronicles 1:12")
    r = A.assay(clarke)
    assert r["verdict"] == A.STANDS, r


def test_a_long_card_that_says_nothing_does_not_stand():
    """The mirror. Length cuts both ways, so neither direction may be trusted."""
    padded = _card("The full 1915 article renders on this card's page.",
                   title="ISBE: Something")
    assert A.assay(padded)["verdict"] == A.EMPTY

    echo = _card("Headstrong", title="Headstrong")
    r = A.assay(echo)
    assert r["verdict"] == A.EMPTY and "repeats the title" in r["reason"]


def test_a_roman_numeral_is_not_a_placeholder():
    """The `_xxx` retraction, encoded so it cannot happen again. XXX is thirty."""
    c = _card("Even as if any of the gods should tell thee, Thou shalt certainly die tomorrow.",
              title="Aurelius, Meditations §aur_07_xxx: Even as if any of the gods…")
    r = A.assay(c)
    assert r["verdict"] != A.EMPTY, "a Roman numeral was mistaken for a placeholder again"
    assert r["verdict"] == A.IMPROVABLE
    assert r["improvement"]["kind"] == "render_title", r
    # improvable for READABILITY only — the content is sound and nothing suggests removal
    assert "slug" in r["reason"]


# ─────────────────────────────────────────── improvement before removal

def test_a_bare_cross_reference_is_improvable_never_empty():
    """It is FAITHFUL — the source entry really is a pointer. Removing it would lose the fact that
    ISBE has that entry at all. Turning it into an edge makes it carry a reader."""
    c = _card("See HEADY .", title="ISBE: Headstrong")
    r = A.assay(c)
    assert r["verdict"] == A.IMPROVABLE, r
    assert r["improvement"]["kind"] == "resolve_xref"
    assert "HEADY" in r["improvement"]["target"]


def test_a_truncated_body_asks_to_be_refilled_not_removed():
    c = _card("He went up into the mountain and there he sat down with his disci-")
    r = A.assay(c)
    assert r["verdict"] == A.IMPROVABLE and r["improvement"]["kind"] == "refill_from_source"


def test_a_verse_ending_in_a_comma_is_not_truncated():
    """The rule that was wrong. A verse is punctuated with a comma BECAUSE the sentence carries
    into the next verse — 157,130 cards were flagged before this was pinned."""
    verse = _card("Count it all joy, my brothers, when you fall into various temptations,",
                  title="James 1:2")
    assert A.assay(verse)["verdict"] == A.STANDS, "a complete verse was called truncated"
    recipe = _card("2 cups flour · 6 tablespoons cold butter, cubed · 1 cup buttermilk, very cold",
                   title="Biscuits")
    assert A.assay(recipe)["verdict"] == A.STANDS, "an ingredient list was called truncated"
    # A LEXICON GLOSS ENDS IN A PREPOSITION ON PURPOSE. The third misfire of this rule: 105 cards
    # flagged because BDB writes "to violently make gain of" and means exactly that.
    gloss = _card("ba.tsa, Strong's H1214: to cut off. 1b3) to violently make gain of",
                  title="H1214")
    assert A.assay(gloss)["verdict"] == A.STANDS, "a complete BDB gloss was called truncated"
    assert A.assay(_card("1a) cause, reason for 1b) the occasion of"))["verdict"] == A.STANDS


def test_real_truncation_is_still_caught():
    for cut in ("He went up into the mountain and there he sat down with his disci-",
                "In the beginning God created the heaven and the earth..."):
        r = A.assay(_card(cut))
        assert r["verdict"] == A.IMPROVABLE, f"missed a real truncation: {cut!r}"
        assert r["improvement"]["kind"] == "refill_from_source"


def test_an_unsourced_card_is_CANNOT_CHECK_and_never_routes_to_removal():
    """Our gap, not the card's fault — three states, never two."""
    c = {"id": "c", "title": "T", "body": "A real sentence carrying a real claim about the world.",
         "source": {}}
    r = A.assay(c)
    assert r["verdict"] == A.CANNOT_CHECK
    assert "our gap" in r["reason"]
    assert r["verdict"] not in (A.EMPTY,), "an unsourced card must never be queued for removal"


# ──────────────────────────────────────────────── removal is a record

def test_a_retraction_is_a_card_with_a_reason_not_a_deletion():
    r = A.retraction("card_bad", "the source it cited does not contain this claim", "matt")
    assert r["ok"]
    c = r["card"]
    assert c["connections"][0] == {"to_card_id": "card_bad", "relationship": "retracts",
                                   "evidence": "the source it cited does not contain this claim"}
    assert c["body"] == "the source it cited does not contain this claim"
    assert c["extra"]["by"] == "matt"


def test_no_anonymous_and_no_unexplained_removals():
    assert A.retraction("card_bad", "", "matt")["ok"] is False
    assert A.retraction("card_bad", "a reason", "")["ok"] is False
    assert A.retraction("", "a reason", "matt")["ok"] is False


def test_a_retracted_card_is_left_alone_by_the_assay():
    """Once withdrawn it is part of the trail; the assay must not keep re-judging it."""
    assert A.assay(_card("x", retracted=True))["verdict"] == A.STANDS


# ───────────────────────────────────────────────────── the survey

def test_the_survey_reports_and_changes_nothing():
    cards = [_card("Caphthorim — \"The Cappadocians.\" — T."),
             _card(""), _card("See HEADY ."), _card("Headstrong", title="Headstrong")]
    before = [dict(c) for c in cards]
    s = A.survey(cards)
    assert s["total"] == 4
    assert s["counts"][A.EMPTY] == 2 and s["counts"][A.IMPROVABLE] == 1
    assert s["counts"][A.STANDS] == 1
    assert cards == before, "the survey mutated the cards it was asked to judge"


def test_the_assay_never_raises_on_junk():
    """It will be run over half a million records; one odd card must not stop the process."""
    for junk in (None, "a string", 42, {}, {"body": None}, {"body": 123}):
        assert A.assay(junk)["verdict"] in (A.STANDS, A.IMPROVABLE, A.EMPTY, A.CANNOT_CHECK)


# ────────────────────────────── does what it POINTS AT arrive?

def test_a_citation_to_a_shim_is_named_as_a_broken_promise():
    """4,743 cards cite /encyclopedia.html or /canon.html — paths that ANSWER (200 / 301) and
    deliver nothing. Not a broken link in the ordinary sense; a citation that reads as provenance
    and leads nowhere."""
    c = _card("real words", title="T")
    c["source"] = {"label": "Easton", "url": "/encyclopedia.html?ref=Slave"}
    pr = A.resolves(c)
    assert [p["kind"] for p in pr] == ["repoint_citation"]
    assert "delivers nothing" in pr[0]["how"]
    c["source"]["url"] = "/characters.html?search=Slave"
    assert A.resolves(c) == [], "a citation that arrives must not be flagged"


def test_a_seal_that_is_not_in_the_keeping_is_named():
    """11,084 cards advertised a receipt never minted. A fingerprint is not a verdict."""
    c = _card("real words")
    c["extra"] = {"seal_hash": "deadbeef" * 8}
    assert A.resolves(c, resolve_seal=lambda h: None)[0]["kind"] == "mint_or_drop_seal"
    assert A.resolves(c, resolve_seal=lambda h: {"verdict": "HOLDS"}) == []


def test_an_edge_into_nothing_is_named():
    c = _card("real words")
    c["connections"] = [{"to_card_id": "card_gone", "relationship": "cites"},
                        {"to_card_id": "card_here", "relationship": "cites"}]
    known = {"card_here": {"id": "card_here"}}
    pr = A.resolves(c, resolve_card=known.get)
    assert len(pr) == 1 and pr[0]["target"] == "card_gone"


def test_an_unsupplied_resolver_is_UNCHECKED_never_counted_as_sound():
    """The rule the whole night argues for: a thing we did not check must never be reported as
    passing. Omitting a resolver skips that class AND says so."""
    c = _card("real words")
    c["extra"] = {"seal_hash": "deadbeef" * 8}
    assert A.resolves(c) == [], "without a resolver the seal class must be skipped, not judged"
    s = A.survey([c])
    assert "seals" in s["unchecked"] and "edges" in s["unchecked"]
    assert s["cards_with_a_broken_promise"] == 0
    s2 = A.survey([c], resolve_seal=lambda h: None, resolve_card=lambda i: None)
    assert s2["unchecked"] == [] and s2["cards_with_a_broken_promise"] == 1


def test_a_resolver_that_throws_is_our_failure_not_the_cards():
    """Three states: an unusable resolver must not become an accusation against the card."""
    def boom(_):
        raise RuntimeError("shard locked")
    c = _card("real words")
    c["extra"] = {"seal_hash": "deadbeef" * 8}
    pr = A.resolves(c, resolve_seal=boom)
    assert pr and pr[0]["kind"] == "mint_or_drop_seal"   # reported, and never raised


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
