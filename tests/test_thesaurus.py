"""The Thesaurus — offline synonym/broader lookup, and the recall-safe synonym fallback in search.

Pinned as behavior:
  * lookup returns WordNet synonyms/broader for a word, symmetric, empty for the unknown;
  * search_question BROADENS a subject by its synonyms when the literal query under-fills, so
    "automobile" reaches a card that only says "car" — recall the reader would otherwise miss;
  * literal hits keep the front slots (precision is never traded for recall);
  * absent thesaurus file -> the fallback is a silent no-op (offline-optional, like the shards).
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402

CARDS = [
    {"id": "card_car_maint", "kind": "note", "title": "Keeping a car running",
     "body": "How to maintain a car: change the oil, check the tires and the brakes.",
     "shelf": "survival", "surface": "secular", "visibility": "public",
     "lifecycle_stage": "public", "generated": False, "connections": []},
    {"id": "card_bread", "kind": "note", "title": "Baking bread",
     "body": "Flour, water, yeast and salt make a loaf.",
     "shelf": "practical", "surface": "secular", "visibility": "public",
     "lifecycle_stage": "public", "generated": False, "connections": []},
]


def _filler() -> list:
    """Enough distinct cards that 'car'/'maintenance' clear MIN_DISTINCTIVE_IDF (1.5): a term needs
    n/(df+1) >= ~4.5, so a couple dozen unrelated cards make the target words genuinely rare."""
    topics = ["photosynthesis", "glacier", "sonnet", "trombone", "harbor", "quartz", "meridian",
              "cinnamon", "lantern", "aqueduct", "compass", "meadow", "granite", "willow", "beacon",
              "orchard", "cobalt", "trellis", "hearth", "marsh", "cypress", "amber", "furrow", "kiln"]
    return [{"id": f"card_fill_{t}", "kind": "note", "title": t.capitalize(),
             "body": f"A short note about {t}: the {t} and its uses in the world of {t}.",
             "shelf": "reference", "surface": "secular", "visibility": "public",
             "lifecycle_stage": "public", "generated": False, "connections": []} for t in topics]


def _build(tmp: Path) -> None:
    with open(tmp / "cards.jsonl", "w", encoding="utf-8") as f:
        for c in CARDS + _filler():
            f.write(json.dumps(c) + "\n")
    db = sqlite3.connect(str(tmp / "thesaurus.db"))
    db.executescript("create table thes (word text primary key, syn text, broader text);")
    db.executemany("insert into thes values (?,?,?)", [
        ("automobile", json.dumps(["car"]), json.dumps(["motor vehicle"])),
        ("car", json.dumps(["automobile", "auto"]), json.dumps([])),
    ])
    db.commit()
    db.close()


@pytest.fixture()
def world():
    from concordance import corpus, thesaurus
    tmp = Path(tempfile.mkdtemp())
    _build(tmp)
    keys = ("CONCORDANCE_DATA_DIR", "CONCORDANCE_THESAURUS_DB", "CONCORDANCE_CARDS_JSONL",
            "CONCORDANCE_CORPUS_SHARDS", "CONCORDANCE_FREEZE_SHELVES", "CONCORDANCE_CORPUS_DB")
    prior = {k: os.environ.get(k) for k in keys}
    os.environ["CONCORDANCE_DATA_DIR"] = str(tmp)
    for k in keys:
        if k != "CONCORDANCE_DATA_DIR":
            os.environ.pop(k, None)
    prior_default = corpus._DEFAULT
    corpus._DEFAULT = None
    thesaurus._row.cache_clear()
    yield tmp
    corpus._DEFAULT = prior_default
    thesaurus._row.cache_clear()
    for k, v in prior.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_thesaurus_lookup(world):
    from concordance import thesaurus
    assert thesaurus.available()
    assert "car" in thesaurus.synonyms("automobile")
    assert "automobile" in thesaurus.synonyms("car")
    assert thesaurus.broader("automobile") == ["motor vehicle"]
    assert thesaurus.synonyms("Automobile") == thesaurus.synonyms("automobile"), "case-insensitive"
    assert thesaurus.synonyms("notaword") == []


def test_literal_query_misses_but_synonym_recall_finds_it(world):
    from concordance import corpus
    # no card contains the word "automobile" — the literal search misses the car card
    assert not any(c["id"] == "card_car_maint" for c in corpus.search("automobile", limit=5))
    # the question door broadens "automobile" -> "car" and reaches it
    hits = corpus.search_question("automobile", limit=5)
    assert any(h["id"] == "card_car_maint" for h in hits), \
        "synonym recall should reach the card that only says 'car'"


def test_precise_query_leads_and_is_unchanged(world):
    from concordance import corpus
    hits = corpus.search_question("car maintenance", limit=5)
    assert hits and hits[0]["id"] == "card_car_maint", "the literal hit keeps the front slot"


def test_without_thesaurus_the_fallback_is_a_noop(world):
    from concordance import corpus, thesaurus
    os.environ["CONCORDANCE_THESAURUS_DB"] = str(world / "no_such.db")
    thesaurus._row.cache_clear()
    assert not thesaurus.available()
    assert not any(h["id"] == "card_car_maint"
                   for h in corpus.search_question("automobile", limit=5)), \
        "no thesaurus -> no synonym broadening"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
