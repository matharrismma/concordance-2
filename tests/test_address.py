"""The Address — the faceted coordinate must place the library, and stay honest doing it.

Spec + measurements: `docs/ADDRESS.md`. Matt: *"We need better tagging for recall. The Dewey
decimal system for the next age of computing."*

Three properties this gate holds, because each was earned the hard way:

  * **COVERAGE.** v1 placed only 55.1% because the plane tables were hand-written and missed the
    biggest shelves in the keeping. Nothing was stored until coverage cleared 90%; it now clears
    99.9%. The floor is enforced here so a future vocabulary change cannot quietly un-place
    a third of the library.
  * **DETERMINISM.** The address is *derived*, which is only worth anything if the same card
    always yields the same address. Otherwise drift becomes an argument instead of a bug.
  * **NO GUESSING.** A card whose facets cannot be determined must come back `UNPLACED` — not
    shoved into a default bucket to flatter the coverage number. The test proves the refusal
    still happens on a card with nothing to go on.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

COVERAGE_FLOOR = 0.90        # measured 99.97% on 2026-07-29; the floor is the promise


def test_the_address_parses_back_into_its_facets():
    from concordance import address
    a = "WIT.scripture.EXP/john-3-16/REF.WITNESSED@john-gill"
    p = address.parse(a)
    assert p, "a derived address must round-trip through the parser"
    assert p["plane"] == "WIT" and p["domain"] == "scripture" and p["kind"] == "EXP"
    assert p["subject"] == "john-3-16" and p["authority"] == "REF"
    assert p["verification"] == "WITNESSED" and p["source"] == "john-gill"
    assert address.parse("not an address") is None


def test_every_prefix_is_a_query():
    """The whole point of a notation: a region of the library nameable without reading it."""
    from concordance import address
    a = "SCI.optics.CHK/snell-law/REF.MIXED@engine"
    assert address.matches(a, "SCI.")
    assert address.matches(a, "SCI.optics.CHK/")
    assert address.matches(a, "SCI.*.CHK/")
    assert not address.matches(a, "WIT.")
    assert not address.matches(a, "SCI.optics.EXP/")


def test_it_refuses_to_guess():
    from concordance import address
    a, why = address.derive({"id": "card_x"})           # nothing to go on
    assert a == address.UNPLACED and why, "an unplaceable card is REPORTED, never bucketed"
    assert address.derive({})[0] == address.UNPLACED


def test_derivation_is_deterministic():
    from concordance import address
    card = {"id": "card_comm_john_gill_jhn_3_16", "shelf": "commentary", "box": "john-gill",
            "subject": "John 3:16", "source": {"label": "John Gill's Exposition — Public Domain",
                                               "authority_tier": "reference"},
            "extra": {"commentary_source": "john-gill"}}
    first = address.derive(card)[0]
    assert first != address.UNPLACED
    for _ in range(5):
        assert address.derive(dict(card))[0] == first, "same card, same address, always"


def test_the_whole_keeping_is_addressable():
    """The coverage floor, over the REAL corpus. A coordinate system that cannot place the
    library is a filing cabinet with the drawers missing."""
    from concordance import address, corpus
    cards = corpus.default_corpus().cards
    if len(cards) < 1000:
        pytest.skip("corpus not present on this machine (data, not tracked)")
    placed = unplaced = 0
    for c in cards.values():
        a, _why = address.derive(c)
        if a == address.UNPLACED:
            unplaced += 1
        else:
            assert address.parse(a), f"derived an address the parser rejects: {a}"
            placed += 1
    total = placed + unplaced
    ratio = placed / total
    assert ratio >= COVERAGE_FLOOR, (
        f"only {ratio:.1%} of {total:,} cards are addressable (floor {COVERAGE_FLOOR:.0%}) — "
        f"the vocabulary regressed; fix it before storing anything")


def test_the_facets_actually_discriminate():
    """A facet whose values are 90% one thing is not a facet. v2 had TXT at 84% because every
    `card_src_` card was called primary text; splitting fact from text fixed it."""
    from collections import Counter
    from concordance import address, corpus
    cards = corpus.default_corpus().cards
    if len(cards) < 1000:
        pytest.skip("corpus not present on this machine")
    kinds = Counter()
    for c in cards.values():
        a, _ = address.derive(c)
        p = address.parse(a) if a != address.UNPLACED else None
        if p:
            kinds[p["kind"]] += 1
    top = kinds.most_common(1)[0]
    assert top[1] / sum(kinds.values()) < 0.90, (
        f"the kind facet collapsed: {top[0]} is {100*top[1]/sum(kinds.values()):.0f}% of the "
        f"library, which means it distinguishes nothing")
    assert len(kinds) >= 5, f"only {len(kinds)} kinds in use: {dict(kinds)}"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
