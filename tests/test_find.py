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
_WIKI, _LOC = find.wikipedia, find.library_of_congress


def _enable():
    os.environ.pop("WEB_FIND_DISABLED", None)         # on for this test (providers are stubbed)


def _restore():
    find.wikipedia, find.library_of_congress = _WIKI, _LOC
    os.environ["WEB_FIND_DISABLED"] = "1"             # back to the test-wide default (off)


def test_relevance_keeps_only_what_matches():
    assert find._relevant("speed of light", "the speed of light in a vacuum")
    assert not find._relevant("speed of light", "a novel about sailing pirates")


def test_find_runs_through_checks_and_keeps_a_web_tier_card():
    _enable()
    find.wikipedia = lambda q: {"title": "Speed of light", "url": "https://en.wikipedia.org/wiki/Speed_of_light",
                                "extract": "The speed of light is a universal physical constant.",
                                "source": "Wikipedia", "license": "CC BY-SA 4.0", "tier": "reference"}
    find.library_of_congress = lambda q, limit=3: [
        {"title": "Stillness at the Speed of Light", "url": "http://www.loc.gov/item/x/",
         "format": "photo", "source": "Library of Congress", "license": "PD", "tier": "primary"}]
    try:
        r = find.find_and_check("what is the speed of light", SEC)
        assert r and r["answer"]["source"] == "Wikipedia"
        assert "tortoise" in r["source_note"]
        assert r["documents"] and r["documents"][0]["source"] == "Library of Congress"
        # it was kept — as an UNVERIFIED, web-tier card, never as the verified keeping
        cards = [json.loads(l) for l in find._store_path().read_text(encoding="utf-8").splitlines() if l.strip()]
        c = next(c for c in cards if c["title"] == "Speed of light")
        assert c["kind"] == "web" and c["verified"] is False
        assert c["source"]["authority_tier"] == "web_unverified"
        assert "not the verified keeping" in c["body"].lower()
    finally:
        _restore()


def test_falsehood_in_a_finding_is_flagged_our_strength():
    # a finding whose arithmetic is wrong — the Auditor catches it and we frame by the falsehood
    _enable()
    find.wikipedia = lambda q: {"title": "A bad figure", "url": "https://en.wikipedia.org/wiki/x",
                                "extract": "This percent report says 15% of 200 is 25, an error.",
                                "source": "Wikipedia", "license": "CC BY-SA 4.0", "tier": "reference"}
    find.library_of_congress = lambda q, limit=3: []
    try:
        r = find.find_and_check("the percent report", SEC)
        assert r and ("flag" in r["framed"].lower() or "false" in r["framed"].lower())
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
