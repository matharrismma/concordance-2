"""The book is always on the right page — or we ask which of two possibilities.

Matt, 2026-07-28: "We shouldn't be afraid to allow the human to go the last mile so to speak and
we get it narrowed down." The resolver's tiers, each pinned here:

  1. a FULL book name typed out is exact and never questioned;
  2. the curated abbreviation table is deliberate convention (Phil → Philippians, Ps → Psalms);
  3. an ambiguous short name uses everything the request tells us — 'Jud 5' can only be Judges,
     because Jude has one chapter; the page itself disambiguates;
  4. when two or more books could genuinely hold the page, the answer is a QUESTION carrying the
     candidates — never a silent guess, never a dead end. 'Jud 1:2' exists in both Jude and
     Judges; the last mile belongs to the human.

Found live before the fix: 'Jud 1:2' silently opened Jude via a corpus-declared abbreviation while
Judges 1:2 was equally real — the same sin as planting one flag on a disputed site.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _p(ref):
    from concordance.verifiers.scripture import read_passage
    return read_passage(ref)


def test_full_names_are_never_questioned():
    for ref, book in (("Jude 1:2", "Jude"), ("Judges 1:2", "Judges"),
                      ("Song of Solomon 8:7", "Song of Solomon"), ("John 3:16", "John")):
        r = _p(ref)
        assert r["status"] == "ok" and r["ref"].startswith(book), (ref, r.get("status"))


def test_curated_abbreviations_are_convention_not_ambiguity():
    """'Phil 4:13' is the most common abbreviation in Christendom — asking would be pedantry,
    and Philemon's standard abbreviation is Phlm, not Phil."""
    r = _p("Phil 4:13")
    assert r["status"] == "ok" and r["ref"] == "Philippians 4:13"
    r2 = _p("Ps 23")
    assert r2["status"] == "ok" and r2["ref"].startswith("Psalms 23")


def test_a_unique_prefix_opens_the_right_page():
    assert _p("Song 8:7")["ref"] == "Song of Solomon 8:7"
    assert _p("Phile 1:16")["ref"] == "Philemon 1:16"
    assert _p("Jos 6")["ref"].startswith("Joshua 6")


def test_the_page_itself_disambiguates_when_it_can():
    """'Jud 5' can only be Judges — Jude has one chapter. Everything the request tells us is used
    BEFORE the human is asked; we narrow it down, they go the last mile only when it is truly theirs."""
    r = _p("Jud 5")
    assert r["status"] == "ok" and r["ref"].startswith("Judges 5"), r.get("status")


def test_a_genuine_two_way_tie_asks_instead_of_guessing():
    r = _p("Jud 1:2")
    assert r["status"] == "ambiguous", "both Jude 1:2 and Judges 1:2 exist — a silent pick opens the wrong book for someone"
    assert set(r["candidates"]) == {"Jude 1:2", "Judges 1:2"}
    assert "which did you mean" in r["detail"].lower()


def test_two_letter_fragments_never_infer_a_book():
    """'is 15' is arithmetic, not Isaiah 15. Prefix inference needs three letters, because the
    gate's own test caught 'what is 15 percent of 240' opening the Word the day inference landed.
    The curated table still carries every deliberate two-letter form."""
    assert _p("is 15")["status"] == "not_found", "'is' must stay an English word, not Isaiah"
    assert _p("am 3")["status"] == "not_found", "'am' must stay an English word, not Amos"
    assert _p("Jo 3")["status"] == "not_found", "two letters is not a book name"
    # ...while the deliberate two-letter conventions still open the right page
    assert _p("Ps 23")["status"] == "ok"
    assert _p("Mt 5")["status"] == "ok"


def test_nonsense_stays_not_found_not_a_question():
    assert _p("Zzz 1:1")["status"] == "not_found", "asking about nothing would be noise, not help"


def test_the_question_reaches_the_reader_over_the_wire_and_on_the_page():
    """A question the surface never shows is a guarantee that stopped short of the reader."""
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    st, body = dispatch("GET", "/passage", {"ref": "Jud 1:2"}, None, EngineConfig("witness"))
    assert st == 200 and body.get("status") == "ambiguous" and body.get("candidates")

    html = (ROOT / "site" / "bible.html").read_text(encoding="utf-8")
    assert "ambiguous" in html and "which did you mean" in html, \
        "bible.html must render the candidates as choices, not fall through to 'nothing found'"
    assert "data-pick" in html, "the candidates must be one-tap choices"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the right page, or an honest question.")
