"""The teaching-review workspace — GATHER, do not author. teachings.py was at 19% with no test.

It holds the work queue (the teachings of Christ) and, for a teaching, searches the body and surfaces
the cross-history wisdom that ALIGNS to it — attributed, capped per source so the SPREAD shows, the
Word's own passage excluded (that is Step 1), and Scripture concord kept separately. The engine never
writes the reading. The test drives a synthetic search result through gather() and asserts the
attribution, the per-source cap, the own-passage exclusion, and the anchor — plus the pure helpers.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import corpus, teachings  # noqa: E402


# ---- the work queue (pure) ----

def test_queue_is_grouped_and_complete():
    q = teachings.queue()
    assert q["total"] == 46 and q["note"] == teachings.NOTE
    groups = {g["group"]: g["count"] for g in q["groups"]}
    assert groups["Sermon on the Mount"] == 20
    assert set(groups) == {"Sermon on the Mount", "The Discourses",
                           "The I AM Sayings", "The Parables"}
    assert sum(groups.values()) == 46
    # each entry carries its anchor ref
    som = next(g for g in q["groups"] if g["group"] == "Sermon on the Mount")
    assert all({"id", "title", "ref"} <= set(t) for t in som["teachings"])


# ---- pure helpers ----

def test_parse_ref_handles_ranges_and_singletons():
    assert teachings._parse_ref("Matthew 5:3-12") == ("Matthew", 5, 3, 12)
    assert teachings._parse_ref("John 8:58") == ("John", 8, 58, 58)
    assert teachings._parse_ref("1 John 4:1") == ("1 John", 4, 1, 1)
    assert teachings._parse_ref("not a ref") is None


def test_tradition_of_maps_the_spread_of_history():
    assert teachings._tradition_of("Seneca, Letters 47", "", "")[0].startswith("Stoic")
    assert teachings._tradition_of("Analects 4.15", "", "") == ("Chinese · ~500 BC", -500)
    assert teachings._tradition_of("On photosynthesis", "science", "")[0].startswith("The book of nature")
    assert teachings._tradition_of("Devotional on the vine", "", "matt")[1] == 2020
    # canonical Scripture / a dictionary entry concords but is not the cross-history witness
    assert teachings._tradition_of("Psalm 1:1", "", "") == (None, None)


# ---- gather: attributed, capped, own-passage excluded ----

def _note(cid, title, body="wisdom here", shelf="", tier="", url=""):
    return {"id": cid, "kind": "note", "title": title, "body": body, "shelf": shelf,
            "source": {"authority_tier": tier, "url": url}}


@pytest.fixture
def gathered(monkeypatch):
    hits = [
        _note("s1", "Seneca, Letter 1"), _note("s2", "Seneca, Letter 2"),
        _note("s3", "Seneca, Letter 3"), _note("s4", "Seneca, Letter 4"),   # a 4th — must be capped
        _note("a1", "Augustine, Confessions"),
        _note("c1", "Analects 4.15"),
        _note("sci", "On the lilies of the field", shelf="science"),
        _note("lens", "Devotional on worry", tier="matt", url="/s/abcdef12"),
        _note("ps", "Psalm 37:25"),                          # canonical -> scripture_concord
        _note("eas", "Easton: worry"),                       # Easton is excluded from concord
        _note("own", "Matthew 6:26 commentary"),             # the teaching's OWN passage -> skipped
        {"id": "x", "kind": "connection", "title": "Seneca, Letter 9"},  # non-note -> skipped
    ]
    monkeypatch.setattr(corpus, "search", lambda *a, **k: hits)
    monkeypatch.setattr(teachings, "_passage_text", lambda ref: "do not worry about your life")
    return teachings.gather("som_14")   # "Do not worry", Matthew 6:25-34


def test_gather_attributes_and_caps_each_source(gathered):
    g = gathered
    assert g["id"] == "som_14" and g["group"] == "Sermon on the Mount"
    srcs = [w["source"] for w in g["wisdom"]]
    assert srcs.count("Seneca, Letter 1") + srcs.count("Seneca, Letter 2") \
        + srcs.count("Seneca, Letter 3") + srcs.count("Seneca, Letter 4") == 3, "per-source cap is 3"
    assert "Augustine, Confessions" in srcs and "Analects 4.15" in srcs
    assert all("tradition" in w and "year" in w for w in g["wisdom"]), "every fragment attributed"
    lens = next(w for w in g["wisdom"] if w["source"].startswith("Devotional"))
    assert lens["seal"] == "/s/abcdef12", "a receipt-backed fragment keeps its seal"


def test_gather_excludes_the_words_own_passage_and_easton(gathered):
    titles = [w["source"] for w in gathered["wisdom"]] + \
             [s["source"] for s in gathered["scripture_concord"]]
    assert not any(t.startswith("Matthew 6") for t in titles), "the teaching's own passage is Step 1"
    assert "Easton: worry" not in titles
    assert "Psalm 37:25" in [s["source"] for s in gathered["scripture_concord"]]


def test_gather_reports_traditions_and_anchor(gathered):
    assert gathered["traditions"] == sorted(set(gathered["traditions"]))
    assert gathered["count"] == len(gathered["wisdom"])
    assert "ref=Matthew+6" in gathered["anchor"]["original"]
    assert gathered["note"] == teachings.NOTE


def test_gather_unknown_is_none_and_get_is_an_alias(monkeypatch):
    monkeypatch.setattr(corpus, "search", lambda *a, **k: [])
    monkeypatch.setattr(teachings, "_passage_text", lambda ref: "")
    assert teachings.gather("no_such_teaching") is None
    assert teachings.get("no_such_teaching") is None
    assert teachings.get("iam_way")["title"] == "I am the Way, the Truth, and the Life"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
