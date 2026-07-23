"""The tortoise — when the keeping has no answer, find it surely: primary/high-quality sources,
run through our own checks, false claims flagged, and kept for next time.

Network is never touched here — the providers are stubbed. Guards: only relevant, high-quality
findings pass; the finding is run through the Auditor and framed by falsification; the kept card is
tiered web-UNVERIFIED (never masquerading as the verified keeping); and it degrades to nothing when
disabled or empty.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-find-"))

from concordance import find  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

SEC = EngineConfig("secular")
_LOC, _IA, _GUT = find.library_of_congress, find.internet_archive, find.project_gutenberg


def _enable():
    os.environ.pop("WEB_FIND_DISABLED", None)         # on for this test (providers are stubbed)


def _restore():
    find.library_of_congress, find.internet_archive, find.project_gutenberg = _LOC, _IA, _GUT
    os.environ["WEB_FIND_DISABLED"] = "1"             # back to the test-wide default (off)


def test_relevance_keeps_only_what_matches():
    assert find._relevant("speed of light", "the speed of light in a vacuum")
    assert not find._relevant("speed of light", "a novel about sailing pirates")


def test_no_wikipedia_only_primary_public_domain_sources():
    """No Wikipedia, no summary — a factual question we don't hold points to PRIMARY, public-domain
    sources, kept as a primary_pd 'source' card (never masquerading as the verified keeping)."""
    _enable()
    find.internet_archive = lambda q, limit=3: []
    find.project_gutenberg = lambda q, limit=3: []
    find.library_of_congress = lambda q, limit=3: [
        {"title": "The sinking of the Titanic", "url": "http://www.loc.gov/item/titanic/",
         "format": "book", "source": "Library of Congress", "license": "PD", "tier": "primary"}]
    try:
        r = find.find_and_check("what year did the Titanic sink", SEC)
        assert r and r["answer"] is None                     # we don't manufacture an answer
        assert "Wikipedia" not in json.dumps(r)              # never Wikipedia
        assert r["documents"][0]["source"] == "Library of Congress"
        cards = [json.loads(l) for l in find._store_path().read_text(encoding="utf-8").splitlines() if l.strip()]
        c = next(c for c in cards if c["title"] == "The sinking of the Titanic")
        assert c["kind"] == "source" and c["source"]["authority_tier"] == "primary_pd"
        assert c["verified"] is False
    finally:
        _restore()


def test_practical_carries_the_torch_of_foxfire():
    """A how-to question goes to tried-and-true, public-domain sources (Internet Archive +
    Gutenberg) — not the current — and keeps them as a higher-tier practical/PD card."""
    assert find.is_practical("how to preserve food for winter")
    assert not find.is_practical("what year did the Titanic sink")
    _enable()
    find.internet_archive = lambda q, limit=3: [
        {"title": "Food Preservation", "url": "https://archive.org/details/foodpres",
         "year": "1922", "source": "Internet Archive",
         "license": "Public domain (verify per item)", "tier": "primary"}]
    find.project_gutenberg = lambda q, limit=3: [
        {"title": "Woman's Institute Library of Cookery", "url": "https://www.gutenberg.org/ebooks/1",
         "year": "", "creator": "—", "source": "Project Gutenberg", "license": "Public domain",
         "tier": "primary"}]
    try:
        r = find.find_and_check("how to preserve food for winter", SEC)
        assert r and r["answer"] is None                     # practical points to sources, no single answer
        assert "Foxfire" in r["source_note"] and "tortoise" in r["source_note"]
        assert any(d["source"] == "Internet Archive" for d in r["documents"])
        # kept as a PD practical card — a higher tier than the open web
        cards = [json.loads(l) for l in find._store_path().read_text(encoding="utf-8").splitlines() if l.strip()]
        c = next(c for c in cards if c["title"] == "Food Preservation")
        assert c["kind"] == "practical" and c["shelf"] == "practical"
        assert c["source"]["authority_tier"] == "primary_pd" and "foxfire" in c["box"]
    finally:
        _restore()


def test_disabled_and_empty_degrade_to_nothing():
    os.environ["WEB_FIND_DISABLED"] = "1"
    try:
        assert find.find_and_check("anything at all", SEC) is None
    finally:
        _restore()
    _enable()
    find.wikipedia = lambda q: None
    find.library_of_congress = lambda q, limit=3: []
    try:
        assert find.find_and_check("xyzzy nothing here", SEC) is None
    finally:
        _restore()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tortoise tests passed — surest not fastest: primary sources, checked, kept.")
