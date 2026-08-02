"""CRAFT — cutting cards out of a source we hold, and proving each one is where it says it is.

Matt, 2026-08-01: *"We should be able to pull the information and then craft the card from that
call. It may be 5-10 cards."*

The claim under test is not "the cards look good". It is that **a crafted card cannot say anything
the source does not say**, and that this is checkable by a stranger rather than trusted.

Three conditions, in order of how much they matter:

  * **the span is the body** — re-read the file, slice [start:end], and it equals the card. If that
    ever fails, the card is a quotation that does not match its own citation, which is worse than
    no card at all.
  * **there is no door for prose** — `card_from_span` takes offsets. It has no `body` parameter, so
    "craft" cannot quietly become "compose". A structural guarantee, not a policy.
  * **a check that cannot run says so** — four states (true/false/absent/malformed), never a silent
    pass for a source this device no longer holds.

Every test runs against a real ark on disk (a temp `CONCORDANCE_SOURCES`), not a mock, because the
bug this module actually shipped with was invisible to any test that did not touch a real offset:
`_LEAD_MARK` was `^`-anchored, so it fired on a title (a fresh string, position 0) and was
structurally unable to fire on a body (position 11,687 of a 311k-character book). It looked like it
worked. Verified against the Manual of the Church of the Nazarene, 1923 (public domain).

Runnable with pytest OR directly.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


# A miniature of the real thing: a Gutenberg envelope, headings, numbered clauses with the
# paragraph marks a scanner leaves behind, a passage that opens mid-word at a paragraph break,
# and an index at the back that will outscore every real passage if nothing stops it.
DOC = """The Project Gutenberg eBook of A Manual

*** START OF THE PROJECT GUTENBERG EBOOK A MANUAL ***

I. Of the Fellowship

( 9. The fellowship severally are to be composed of such regenerate persons as by providential
permission, and by the leadings of the Spirit, become associated together for holy fellowship and
labours, and who shall be received according to the rules hereinafter set forth. This paragraph is
made long enough on purpose that it clears the minimum span the module requires of any card.

II. Of Sanctification

€ 472. In order that we may preserve our heritage, the faith once delivered to the saints,
especially the doctrine and experience of sanctification as a second work of grace, we do hereby
ordain and set forth this statement, that it may stand for those who come after us and be a plain
witness of what this fellowship has believed from its beginning until the present day.

III. Of the Pastor

6 59. A Pastor is a person who, under the call of God and His people, has the oversight of a local
assembly, and whose duties are to preach the Word, to administer the ordinances, and to have care
of the flock committed to that charge, giving account thereof at the proper season each year.

INDEX

Fellowship, 9, 32, 44. Sanctification, 472, 480. Pastor, 59, 61, 63, 70. Grace, 472, 12, 88.
Doctrine, 29, 34, 35, 40. Heritage, 472. Ordinances, 59, 61. Assembly, 59, 201, 208, 282, 421.

*** END OF THE PROJECT GUTENBERG EBOOK A MANUAL ***

This footer is licensing boilerplate and must never become a card that is attributed to the author.
"""


@pytest.fixture(autouse=True)
def _ark():
    """A real ark on disk for every test — a sha, a body, a waybill, exactly as sources.py lays
    them out. `held()` reads the drive, so a mock here would test nothing that matters."""
    prior_src = os.environ.get("CONCORDANCE_SOURCES")
    prior_data = os.environ.get("CONCORDANCE_DATA_DIR")
    base = Path(tempfile.mkdtemp())
    os.environ["CONCORDANCE_SOURCES"] = str(base)
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    for k, v in (("CONCORDANCE_SOURCES", prior_src), ("CONCORDANCE_DATA_DIR", prior_data)):
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _anchor(text: str = DOC) -> str:
    """Put a body in the ark the way sources.fetch would, and return its sha."""
    from concordance import sources
    raw = text.encode("utf-8")
    sha = hashlib.sha256(raw).hexdigest()
    p = sources.path_for(sha, ".txt")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(raw)
    (p.parent / (sha + ".waybill.json")).write_text(json.dumps({
        "sha256": sha, "bytes": len(raw), "media_type": "text/plain",
        "origin_url": "https://www.gutenberg.org/ebooks/00000",
        "label": "A Manual (1923)", "license": "public_domain", "path": str(p),
    }), encoding="utf-8")
    return sha


# ── THE RULE ──────────────────────────────────────────────────────────────────────────────────
def test_the_span_is_the_body():
    """THE invariant. Every card, re-read from the file at its own offsets, IS the card."""
    from concordance import craft
    sha = _anchor()
    r = craft.craft(sha, "sanctification fellowship pastor")
    assert r["status"] == "crafted", r
    assert r["cards"], "a document full of relevant passages yielded nothing"

    text = craft.decode(Path(json.loads(
        (Path(os.environ["CONCORDANCE_SOURCES"]) / sha[:2] / (sha + ".waybill.json"))
        .read_text(encoding="utf-8"))["path"]).read_bytes())
    for c in r["cards"]:
        s, e = c["extra"]["span"]
        assert text[s:e].strip() == c["body"].strip(), \
            f"card {c['id']} does not match the file at its own offsets"


def test_verify_spans_agrees_and_can_be_made_to_disagree():
    """The check is only worth having if it FAILS when it should. Tamper with one body and the
    verdict must flip — otherwise it is a rubber stamp."""
    from concordance import craft
    sha = _anchor()
    cards = craft.craft(sha, "sanctification grace")["cards"]
    assert cards

    good = craft.verify_spans(cards)
    assert good["true"] == len(cards) and good["false"] == 0, good

    forged = [dict(cards[0])]
    forged[0]["body"] = cards[0]["body"] + " And the Manual endorses this addition."
    bad = craft.verify_spans(forged)
    assert bad["false"] == 1 and bad["true"] == 0, \
        "a tampered body passed verification — the check is a rubber stamp"


def test_there_is_no_door_for_prose():
    """The STRUCTURAL guarantee, asserted against the signature itself.

    Every other honesty rule in this project is enforced by a check that could in principle be
    bypassed. This one cannot: there is no parameter through which authored text could enter, so
    the only way to fill a card is to point at words already in a document we hold.
    """
    import inspect
    from concordance import craft
    params = set(inspect.signature(craft.card_from_span).parameters)
    for forbidden in ("body", "text_body", "content", "summary"):
        assert forbidden not in params, \
            f"card_from_span grew a {forbidden!r} parameter — craft can now become compose"
    assert {"sha", "start", "end"} <= params, "the span is no longer the way a card is filled"


def test_a_check_that_cannot_run_never_reports_a_pass():
    """Four states, not two. A source this device no longer anchors is `absent` — not `true`."""
    from concordance import craft
    sha = _anchor()
    cards = craft.craft(sha, "sanctification")["cards"]
    assert cards

    for p in (Path(os.environ["CONCORDANCE_SOURCES"]) / sha[:2]).iterdir():
        p.unlink()                       # the drive went away; the cards did not

    v = craft.verify_spans(cards)
    assert v["absent"] == len(cards), v
    assert v["true"] == 0 and v["false"] == 0
    assert v["checked"] == 0, "cards we could not check were counted as checked"

    assert craft.verify_spans([{"id": "x", "extra": {}}])["malformed"] == 1


# ── THE CUT ───────────────────────────────────────────────────────────────────────────────────
def test_the_envelope_is_not_the_book():
    """Gutenberg's licence opens and closes every file. Carding it would attribute boilerplate to
    the author and fill a shelf with legal notices."""
    from concordance import craft
    lo, hi = craft.trim(DOC)
    inside = DOC[lo:hi]
    assert "START OF THE PROJECT GUTENBERG" not in inside
    assert "licensing boilerplate" not in inside
    assert "sanctification as a second work of grace" in inside


def test_the_index_is_never_carded():
    """AN INDEX OUTSCORES EVERY REAL PASSAGE — it is the densest concentration of a book's subject
    terms anywhere in it. The tenth card of the first real run against the 1923 Manual was exactly
    this, and it is caught by SHAPE (numbers without sentences), not by matching the word."""
    from concordance import craft
    lo, hi = craft.trim(DOC)
    kept = craft.rank(DOC, craft.sections(DOC, lo, hi), "sanctification fellowship pastor grace")
    for (s, e, _h) in kept:
        body = DOC[s:e]
        assert "Numbers refer" not in body
        assert not (body.count(",") > 12 and body.count(".") > 8 and
                    sum(c.isdigit() for c in body) / len(body) > 0.08), \
            "an index was selected as a card"


def test_nothing_is_padded_to_fill_the_set():
    """"5-10 cards" is a CEILING. A subject the document does not discuss yields nothing, the same
    no-padding rule the search ranker holds."""
    from concordance import craft
    lo, hi = craft.trim(DOC)
    secs = craft.sections(DOC, lo, hi)
    assert craft.rank(DOC, secs, "thermodynamics carburettor)", limit=10) == []

    sha = _anchor()
    r = craft.craft(sha, "thermodynamics carburettor")
    assert r["status"] == "nothing_relevant" and r["cards"] == []
    assert "won't cut a card" in r["message"]


def test_the_cap_holds():
    from concordance import craft
    sha = _anchor()
    assert len(craft.craft(sha, "the of a", limit=3)["cards"]) <= 3
    assert craft.MAX_CARDS == 10


def test_a_card_never_opens_mid_word_or_on_a_paragraph_mark():
    """"costal Church of the Nazarene" — the first run's worst defect, because it misquotes the
    source in its opening breath. The paragraph mark ("( 9.", "€ 472.") is the printed book's
    address, not the passage's first words."""
    from concordance import craft
    sha = _anchor()
    for c in craft.craft(sha, "sanctification fellowship pastor")["cards"]:
        first = c["body"].lstrip()
        assert first[0].isupper() or first[0] in "\"'“‘", \
            f"card opens mid-sentence: {first[:40]!r}"
        assert not first[:6].strip().startswith(("(", "€", "¶")), \
            f"card opens on a paragraph mark: {first[:40]!r}"


def test_the_offset_follows_the_words_that_are_shown():
    """Snapping the start is only honest if the RECORDED span moves with it. An offset that means
    one thing to the writer and another to the reader is worse than no offset."""
    from concordance import craft
    sha = _anchor()
    cards = craft.craft(sha, "sanctification")["cards"]
    assert cards
    assert craft.verify_spans(cards)["false"] == 0, \
        "a span was snapped without updating the address it records"


def test_a_title_is_derived_never_invented():
    """Where the document gives a heading, use it. Where it gives only furniture, fall back to the
    passage's OWN opening words — so the title is the source's language either way."""
    from concordance import craft
    sha = _anchor()
    cards = craft.craft(sha, "sanctification fellowship pastor")["cards"]
    titles = [c["title"] for c in cards]
    assert titles and all(t.strip() for t in titles)
    for t in titles:
        assert not t.strip().startswith(("(", "€", "6 ", "¶")), f"furniture became a title: {t!r}"
        assert not t.strip().isdigit()
        # derived: every title is either a heading in the doc or the opening of its own body
        assert t.split(",")[0][:24] in DOC, f"title {t!r} is not in the document"


def test_furniture_is_stripped_from_labels_and_never_from_bodies():
    """A body we "cleaned" would no longer match its span. The label is derived; the body is
    quoted. The two are allowed to differ in exactly this way and no other."""
    from concordance import craft
    assert craft._strip_furniture("( 9. The fellowship severally") == "The fellowship severally"
    assert craft._strip_furniture("6 390] RITUAL 133 The Minister may") == "The Minister may"
    assert craft._strip_furniture("II. The Churches Severally").startswith("The Churches") or \
        craft._strip_furniture("II. The Churches Severally") == "II. The Churches Severally"
    # and a real sentence is left entirely alone
    assert craft._strip_furniture("In 1900, the first Church was organized") == \
        "In 1900, the first Church was organized"


# ── THE PLANES ────────────────────────────────────────────────────────────────────────────────
def test_the_agent_plane_waits_for_a_human():
    """Same mechanism, different authority — the rule find.py and expand.py already hold."""
    from concordance import craft
    sha = _anchor()
    human = craft.craft(sha, "sanctification", plane="human")
    agent = craft.craft(sha, "sanctification", plane="agent")
    assert all(c["lifecycle_stage"] == "public" for c in human["cards"])
    assert all(c["lifecycle_stage"] == "public_review" for c in agent["cards"])
    assert agent["held_for_review"] is True and human["held_for_review"] is False


def test_a_crafted_card_carries_its_provenance_and_is_not_an_orphan():
    from concordance import craft
    sha = _anchor()
    c = craft.craft(sha, "sanctification", parent_id="card_src_manual")["cards"][0]
    assert c["extra"]["source_sha256"] == sha
    assert c["extra"]["crafted_from"].startswith("https://")
    assert c["source"]["authority_tier"] == "primary_pd"
    assert c["generated"] is False
    assert c["connections"] and c["connections"][0]["to_card_id"] == "card_src_manual"
    assert c["connections"][0]["relationship"] == "excerpt_of"


def test_an_unheld_source_is_refused_not_guessed():
    from concordance import craft
    r = craft.craft("deadbeef" * 8, "anything")
    assert r["status"] == "not_held" and r["cards"] == []


def test_the_decode_rule_is_shared_by_writer_and_reader():
    """If these two ever differ, every offset in the keeping silently means something else."""
    from concordance import craft
    raw = "sanctification — a second work".encode("utf-8")
    assert craft.decode(raw) == raw.decode("utf-8")
    assert len(craft.decode(b"\xff\xfe bad bytes")) == len(b"\xff\xfe bad bytes")


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
