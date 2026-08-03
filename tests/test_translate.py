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


# ── parallel alignment ────────────────────────────────────────────────────────────────────
# Alignment LOCATES text across two languages; it never renders it. Both sides are quoted from
# held sources, which is why this is composition and is permitted where translation is not.

GREEK_JOHN = [
    "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος.",
    "οὗτος ἦν ἐν ἀρχῇ πρὸς τὸν θεόν.",
    "πάντα διʼ αὐτοῦ ἐγένετο, καὶ χωρὶς αὐτοῦ ἐγένετο οὐδὲ ἕν ὃ γέγονεν.",
    "ἐν αὐτῷ ζωὴ ἦν, καὶ ἡ ζωὴ ἦν τὸ φῶς τῶν ἀνθρώπων.",
    "καὶ τὸ φῶς ἐν τῇ σκοτίᾳ φαίνει, καὶ ἡ σκοτία αὐτὸ οὐ κατέλαβεν.",
]
ENGLISH_JOHN = [
    "In the beginning was the Word, and the Word was with God, and the Word was God.",
    "The same was in the beginning with God.",
    "All things were made through him. Without him, nothing was made that has been made.",
    "In him was life, and the life was the light of men.",
    "The light shines in the darkness, and the darkness hasn’t overcome it.",
]


def test_alignment_by_address_is_a_lookup_not_an_inference():
    """When both sides carry the same reference scheme, nothing is guessed and the card says so."""
    refs = ["John 1:%d" % v for v in range(1, 6)]
    r = T.align(GREEK_JOHN, ENGLISH_JOHN, refs, refs)
    assert r["method"] == "address"
    assert r["coverage"]["paired"] == 5
    assert "EXACT" in r["confidence"]
    assert all(p["cost"] == 0.0 for p in r["pairs"])


def test_alignment_by_length_recovers_known_ground_truth():
    """GROUND TRUTH: John 1:1-5 is one-to-one between Greek and English.

    Gale & Church works from character counts alone — no dictionary, no model — so recovering
    this is a real check that the dynamic program is right rather than merely running."""
    r = T.align(GREEK_JOHN, ENGLISH_JOHN)
    assert r["method"] == "length"
    got = [(p["bead"], p["a_index"], p["b_index"]) for p in r["pairs"]]
    want = [("1-1", [i], [i]) for i in range(5)]
    assert got == want, f"failed to recover the known 1-1 alignment: {got}"
    assert r["coverage"]["weak_pairings"] == 0


def test_an_omission_is_found_at_the_right_place_and_flagged():
    """REGRESSION for a real defect. With one Greek verse removed the correct answer needs a 0-1
    bead, and the first version priced that out: _bead_cost charged a LENGTH penalty on a
    deletion, where the length difference is the whole unit by definition. Insertions cost ~16
    against a 4.0 prior, so the aligner preferred merging two unrelated verses (a 1-2 at 4.98).
    Found by driving the stress case, not by reading the code."""
    short = [GREEK_JOHN[0]] + GREEK_JOHN[2:]        # verse 2 missing on the Greek side
    r = T.align(short, ENGLISH_JOHN)
    beads = [p["bead"] for p in r["pairs"]]
    assert beads == ["1-1", "0-1", "1-1", "1-1", "1-1"], (
        f"the omission was not located correctly: {beads}")
    flagged = [p for p in r["pairs"] if p["flag"]]
    assert len(flagged) == 1 and flagged[0]["bead"] == "0-1"


def test_every_non_one_to_one_bead_is_flagged_whatever_its_cost():
    """A split, merge or omission is inherently a weaker claim than a clean substitution — the
    same rule that labels a prefix-stripped gloss weaker than a direct hit. A cost threshold
    alone let the one doubtful pairing through at 4.98 against a 5.0 cutoff."""
    short = [GREEK_JOHN[0]] + GREEK_JOHN[2:]
    r = T.align(short, ENGLISH_JOHN)
    for p in r["pairs"]:
        if p["bead"] != "1-1":
            assert p["flag"], f"a {p['bead']} bead was left unflagged"


def test_alignment_composes_nothing():
    """Both sides must be QUOTED from the inputs. If any returned text is not present in the
    source it was composed, which this layer may never do."""
    r = T.align(GREEK_JOHN, ENGLISH_JOHN)
    a_all, b_all = "\n".join(GREEK_JOHN), "\n".join(ENGLISH_JOHN)
    for p in r["pairs"]:
        if p["a"]:
            assert all(ln in a_all for ln in p["a"].split("\n"))
        if p["b"]:
            assert all(ln in b_all for ln in p["b"].split("\n"))
    assert "does not render" in r["boundary"]


def test_alignment_of_nothing_is_empty_not_invented():
    assert T.align([], ENGLISH_JOHN)["status"] == "empty"
    assert T.align(GREEK_JOHN, [])["status"] == "empty"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))


# ── deriving a lexicon from verse-aligned scripture ───────────────────────────────────────
# Matt: "What about a bible as the source of the lexicon for each language? That was the original
# method." It was — and it is the answer to this module's real limit. A dictionary per language
# is a licensing problem; a BIBLE per language is solved in ~700 languages, and every translation
# shares one address scheme, so the alignment is free and exact.

PAR_FOREIGN = {
    "1:1": ["alpha", "beta"], "1:2": ["alpha", "gamma"], "1:3": ["alpha", "delta"],
    "1:4": ["beta", "gamma"], "1:5": ["beta", "delta"], "1:6": ["alpha", "beta"],
}
PAR_KNOWN = {
    "1:1": ["light", "water"], "1:2": ["light", "stone"], "1:3": ["light", "tree"],
    "1:4": ["water", "stone"], "1:5": ["water", "tree"], "1:6": ["light", "water"],
}


def test_derivation_finds_the_planted_correspondence():
    """GROUND TRUTH: alpha co-occurs with light in every verse it appears; beta with water."""
    r = T.derive_lexicon(PAR_FOREIGN, PAR_KNOWN, min_count=2, min_dice=0.1)
    assert r["status"] == "ok"
    by = {e["form"]: e["candidates"][0]["gloss"] for e in r["entries"]}
    assert by.get("alpha") == "light", f"alpha should derive to light, got {by.get('alpha')}"
    assert by.get("beta") == "water", f"beta should derive to water, got {by.get('beta')}"


def test_every_derived_entry_carries_checkable_evidence():
    """An entry a reader cannot go and verify is not worth having. The addresses must be real
    and must actually contain the claimed gloss."""
    r = T.derive_lexicon(PAR_FOREIGN, PAR_KNOWN, min_count=2, min_dice=0.1)
    for e in r["entries"]:
        assert e["evidence"], f"{e['form']} was derived with no evidence"
        top = e["candidates"][0]["gloss"]
        for ref in e["evidence"]:
            assert ref in PAR_KNOWN, f"evidence cites {ref}, which is not in the corpus"
            assert top in PAR_KNOWN[ref], (
                f"{e['form']} cites {ref} as evidence for '{top}', but that verse does not "
                f"contain it — the evidence must be real")


def test_a_form_too_rare_to_judge_is_reported_not_guessed():
    """A miss must stay a miss: forms below the threshold are counted, never glossed."""
    r = T.derive_lexicon(PAR_FOREIGN, PAR_KNOWN, min_count=99, min_dice=0.1)
    assert r["entries"] == []
    assert r["coverage"]["too_rare_to_judge"] > 0


def test_derivation_bands_its_own_confidence():
    """Both tails of the frequency range are unreliable, for opposite reasons, so a single
    accuracy figure would mislead. The band must travel with the entry."""
    r = T.derive_lexicon(PAR_FOREIGN, PAR_KNOWN, min_count=2, min_dice=0.1)
    for e in r["entries"]:
        assert e["confidence"], "a derived entry must state how far to trust it"
        assert any(k in e["confidence"] for k in ("LOW", "MODERATE", "BEST"))


def test_texts_that_share_no_addresses_refuse_rather_than_invent():
    r = T.derive_lexicon({"9:9": ["x"]}, PAR_KNOWN, min_count=1)
    assert r["status"] == "no_overlap"
    assert "cannot be aligned" in r["detail"]
