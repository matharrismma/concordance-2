"""Every verifier produces a card — the science and math join the one keeping.

Guards: the card is a faithful, deterministic record of the verification (pay once); bare
arithmetic does not flood the graph; a minted card is searchable in the live corpus; and the
seal path is never broken by minting.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-scicard-")

from concordance import science_cards, corpus  # noqa: E402

_SEAL = {"cite_url": "https://narrowhighway.com/s/abc123", "content_hash": "abc"}


def _result(claim, verdict="HOLDS", domain="chemistry"):
    return {"verdict": verdict,
            "trail": [{"id": "a", "domain": domain, "claim": claim,
                       "detail": claim + " — both sides reduce equal", "status": "CONFIRMED"}]}


def test_a_verification_becomes_a_faithful_card():
    c = science_cards.card_for(_result("Avogadro's number times two is 1.2044e24"),
                               "chemistry", _SEAL)
    assert c["kind"] == "verified" and c["shelf"] == "chemistry"
    assert "HOLDS" in c["body"] and _SEAL["cite_url"] in c["body"]
    assert c["generated"] is False and c["source"]["authority_tier"] == "engine"


def test_pay_once_same_fact_is_one_card():
    a = science_cards.card_for(_result("the speed of light is 299792458 m/s"), "physics", _SEAL)
    b = science_cards.card_for(_result("the speed of light is 299792458 m/s"), "physics", _SEAL)
    assert a["id"] == b["id"]                      # deterministic — one card, however often checked


def test_bare_arithmetic_does_not_flood_the_graph():
    assert science_cards.card_for(_result("2 + 2 = 4", domain="mathematics"),
                                  "mathematics", _SEAL) is None
    # a named concept, even in mathematics, is worth keeping
    assert science_cards.card_for(_result("Pythagoras: a^2 + b^2 = c^2"), "mathematics", _SEAL)


def test_a_scripture_naming_claim_carries_its_verse_for_bridging():
    c = science_cards.card_for(_result("Genesis 1:1 anchors the beginning"),
                               "scripture_anchors", _SEAL)
    assert c["source"]["ref"] == "Genesis 1:1"     # the growth engine can bridge it to the Word


def test_minting_persists_joins_the_live_corpus_and_pays_once():
    cor = corpus.default_corpus()                  # build the live corpus first
    r = _result("photosynthesis fixes carbon in the chloroplast stroma", domain="biology")
    card = science_cards.mint(r, "biology", _SEAL)
    assert card and card["id"]
    assert science_cards.mint(r, "biology", _SEAL) is None      # pay once — second is a no-op
    # it JOINED the graph: present by id, and indexed by its words (ranked search over a 1-card
    # test corpus is degenerate on IDF; production has 25k cards — verified live after deploy)
    assert corpus.get_card(card["id"]) is not None
    assert card["id"] in cor._by_token.get("photosynthesis", [])
    # and it persisted to the second source
    assert card["id"] in {json.loads(ln)["id"]
                          for ln in science_cards._store_path().read_text(encoding="utf-8").splitlines()
                          if ln.strip()}


def test_minting_never_breaks_a_malformed_result():
    assert science_cards.mint({}, "physics", _SEAL) is None
    assert science_cards.mint({"trail": []}, "physics", _SEAL) is None


def test_boilerplate_and_non_results_never_become_cards():
    """The leaks caught live: a bare equality carries only engine boilerplate ('both sides
    reduce to 4'), and INCOMPLETE / 'no applicable verifier' are not facts. Neither earns a card."""
    boiler = {"verdict": "HOLDS",
              "trail": [{"id": "a", "domain": "mathematics", "claim": "",
                         "detail": "2+2 = 4; both sides reduce to 4", "status": "CONFIRMED"}]}
    assert science_cards.card_for(boiler, "mathematics", _SEAL) is None
    incomplete = _result("some real chemistry claim", verdict="INCOMPLETE")
    assert science_cards.card_for(incomplete, "chemistry", _SEAL) is None
    noverifier = {"verdict": "HOLDS",
                  "trail": [{"id": "a", "claim": "no applicable secular verifier for this domain",
                             "detail": "", "status": "CONFIRMED"}]}
    assert science_cards.card_for(noverifier, "chemistry", _SEAL) is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} science-card tests passed — every verifier joins the keeping, pay once.")
