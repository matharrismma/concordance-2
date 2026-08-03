"""THE TRANSLATION LAYER — it must gloss, report its coverage, and never compose a sentence.

Matt, 2026-08-03: "We need to work on our translation layer, so we can study books no matter the
language."

The boundary is the whole design. Machine translation GENERATES prose, and fluent output that no
source contains is the one artefact this library must not hand anyone — it reads like knowledge
and carries no chain to a source. So the layer glosses from held lexicons, names what it cannot
resolve, and stops. These tests pin that boundary so a later "improvement" cannot quietly cross
it.

The tokenizer test is a REGRESSION. The first version used explicit Unicode ranges and shattered
Hebrew: b'reshit came apart into its consonant and its pointing, because a character-class edge
fell between a letter and its combining marks. Coverage read 28.6% and I diagnosed it as a
morphology problem, which was plausible and wrong — the tokens themselves were nonsense, so the
hit rate was measuring the tokenizer rather than the lexicon. Driving the real output found it in
one line. This test makes that specific failure impossible to reintroduce.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import translate as T  # noqa: E402

GREEK = "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος."
HEBREW = "בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ"

_HAVE_LEX = bool(T.lexicons()["held"])
needs_lex = pytest.mark.skipif(not _HAVE_LEX, reason="no lexicon on disk")


def test_it_never_composes_a_sentence():
    """THE DOCTRINAL ONE, and deliberately unskippable.

    No function here may return translated prose. If a later change adds a 'translation' or
    'english' field holding a composed sentence, this fails — which is the point. The engine may
    arrange attributed material and may not author substance."""
    for fn in ("gloss", "study"):
        out = getattr(T, fn)(GREEK if _HAVE_LEX else "hello world")
        assert isinstance(out, dict)
        for banned in ("translation", "translated", "english", "rendering", "prose"):
            assert banned not in out, (
                f"{fn}() returned a '{banned}' field — this layer glosses and must never "
                f"compose a sentence")


def test_a_script_with_no_lexicon_refuses_and_names_the_gap():
    """A refusal must say what IS available, never merely fail."""
    out = T.gloss("это русский текст")          # Cyrillic: no lexicon held
    assert out["status"] == "NO_LEXICON"
    assert out["script"] == "cyrillic"
    assert "gap" in out["detail"].lower() or "lexicon" in out["detail"].lower()
    assert "held" in out, "a refusal must name what IS reachable"


def test_script_detection_does_not_claim_a_language():
    """Script is a fact about the bytes; language is an inference we do not make."""
    g = T.script_of(GREEK)
    assert g["script"] == "greek"
    h = T.script_of(HEBREW)
    assert h["script"] == "hebrew"
    assert "not asserted" in g["detail"]


@needs_lex
def test_the_tokenizer_does_not_shatter_hebrew():
    """REGRESSION. Hebrew words must survive tokenisation with their pointing attached.

    The broken version produced 14 tokens for a 7-word verse by splitting each word at its first
    combining mark. Seven space-separated words must yield seven tokens."""
    out = T.gloss(HEBREW)
    assert out["coverage"]["total"] == 7, (
        "Genesis 1:1 has 7 space-separated words; got %d tokens — the tokenizer is splitting "
        "letters from their combining marks again" % out["coverage"]["total"])
    for tk in out["tokens"]:
        assert len(tk["token"]) > 1, f"token {tk['token']!r} is a bare character — shattered"


@needs_lex
def test_coverage_is_reported_and_arithmetically_honest():
    """The coverage block is the difference between a reader who knows how much they are seeing
    and one who does not. It must agree with the tokens it describes."""
    out = T.gloss(GREEK)
    cov = out["coverage"]
    resolved = sum(1 for t in out["tokens"] if t["status"] == "resolved")
    assert cov["resolved"] == resolved
    assert cov["unresolved"] == cov["total"] - resolved
    assert cov["total"] == len(out["tokens"])


@needs_lex
def test_an_unresolved_word_stays_visible():
    """A word with no entry is NAMED, never dropped and never guessed — a miss must stay a miss."""
    out = T.gloss(GREEK)
    for tk in out["tokens"]:
        assert tk["status"] in ("resolved", "unresolved")
        if tk["status"] == "unresolved":
            assert "note" in tk and tk["note"], "an unresolved token must explain itself"


@needs_lex
def test_an_ambiguous_fold_shows_every_candidate():
    """Folding accents is LOSSY, so a hit is a candidate rather than a proof.

    Hebrew 'et' folds to at least four distinct lexicon entries — the direct-object marker
    (H853), a portent (H852), a preposition (H854) and a hoe (H855). The engine must show them
    all and say it did not choose; picking one silently would be exactly the 'silently upgrade
    authority' failure."""
    out = T.gloss("אֵת")
    tk = out["tokens"][0]
    assert tk["status"] == "resolved"
    assert len(tk["candidates"]) > 1, "ambiguous form collapsed to a single candidate"
    assert tk["note"] and "rather than one being chosen" in tk["note"]
    nums = {c["strongs"] for c in tk["candidates"]}
    assert "H853" in nums, "the direct-object marker must be among the candidates offered"


@needs_lex
def test_a_prefix_stripped_match_is_labelled_as_weaker():
    """Hebrew fuses particles onto the word. Stripping one to find a match is a WEAKER claim than
    a direct hit, and the reader must be told which they are looking at."""
    out = T.gloss(HEBREW)
    kinds = {t.get("match") for t in out["tokens"] if t["status"] == "resolved"}
    assert "prefix_stripped" in kinds, "no prefix match fired on Genesis 1:1"
    for tk in out["tokens"]:
        if tk.get("match") == "prefix_stripped":
            assert "weaker" in (tk["note"] or "").lower()


def test_lexicons_are_measured_from_disk_not_claimed():
    """`lexicons()` must report what is actually present, so the promise cannot outrun the files."""
    lx = T.lexicons()
    assert "held" in lx and "missing" in lx
    for h in lx["held"]:
        assert h["entries"] > 0, f"{h['language']} is listed as held with zero entries"
    assert lx["total_entries"] == sum(h["entries"] for h in lx["held"])


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
