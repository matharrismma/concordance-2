"""The Almanac — coverage for the re-sealed almanac reader (categories / list / get / search).

almanac.py had no test (20% under the gate). Its whole surface is pure and file-backed, so the
tests point CONCORDANCE_ALMANAC_DIR at a temp store, write same-shape records, and exercise every
function and branch: the empty/missing file, bad-JSON skip, the category filter, case-insensitive
get, search across title/situation/wisdom/category/domain, and the limits.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import almanac  # noqa: E402

RECORDS = [
    {"id": "a2", "title": "Compound interest holds", "kind": "math", "situation": "savings plan",
     "domains": ["finance", "mathematics"], "category": "money", "wisdom": "time in the market",
     "orig_verdict": "HOLDS", "packet": {}, "seal": {"cite_url": "/s/def"}},
    {"id": "a1", "title": "Beta blocker dosing", "kind": "medical", "situation": "chest protocol",
     "domains": ["medicine"], "category": "health", "wisdom": "start low, go slow",
     "orig_verdict": "HOLDS", "packet": {}, "seal": {"cite_url": "/s/abc"}},
    {"id": "a3", "title": "Weather sign for planting", "kind": "weather", "situation": "spring frost",
     "domains": ["meteorology"], "category": "health", "wisdom": "watch the sky",
     "orig_verdict": "HOLDS", "packet": {}, "seal": None},
]


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A fresh almanac dir per test, with the module's mtime cache reset so reads are not stale."""
    monkeypatch.setenv("CONCORDANCE_ALMANAC_DIR", str(tmp_path))
    almanac._ENTRIES, almanac._MTIME = [], 0.0

    def write(records, raw_extra=""):
        p = tmp_path / "resealed.jsonl"
        body = "\n".join(json.dumps(r) for r in records)
        p.write_text(body + ("\n" + raw_extra if raw_extra else ""), encoding="utf-8")
        almanac._ENTRIES, almanac._MTIME = [], 0.0   # force a reload after the write
        return p
    return write


# ---- missing / empty file ----

def test_missing_file_is_empty_not_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_ALMANAC_DIR", str(tmp_path))
    almanac._ENTRIES, almanac._MTIME = [], 0.0
    assert almanac.categories() == []
    le = almanac.list_entries()
    assert le["total"] == 0 and le["entries"] == [] and le["note"] == almanac.NOTE
    assert almanac.get("anything") is None
    assert almanac.search("anything")["total"] == 0


# ---- load: sorting, bad-JSON skip, blank lines ----

def test_entries_sort_by_title_and_skip_bad_json(store):
    store(RECORDS, raw_extra="{ not valid json\n\n")   # a bad line + a blank line, both skipped
    le = almanac.list_entries()
    assert le["total"] == 3
    titles = [e["title"] for e in le["entries"]]
    assert titles == sorted(titles, key=str.lower)     # sorted by title, case-insensitive


# ---- categories ----

def test_categories_counts_and_sorted(store):
    store(RECORDS)
    assert almanac.categories() == [{"category": "health", "count": 2},
                                    {"category": "money", "count": 1}]


# ---- list_entries: filter + limit + brief shape ----

def test_list_filters_by_category(store):
    store(RECORDS)
    assert almanac.list_entries("health")["total"] == 2
    assert almanac.list_entries("MONEY")["total"] == 1          # case-insensitive filter
    assert almanac.list_entries("nope")["total"] == 0


def test_list_limit_caps_entries_not_total(store):
    store(RECORDS)
    le = almanac.list_entries(limit=1)
    assert le["total"] == 3 and len(le["entries"]) == 1
    brief = le["entries"][0]
    assert set(brief) == {"id", "title", "category", "domains", "verdict", "seal"}
    assert brief["verdict"] == "HOLDS"


# ---- get ----

def test_get_returns_full_entry_case_insensitive(store):
    store(RECORDS)
    got = almanac.get("A1")                              # case-insensitive
    assert got is not None and got["id"] == "a1"
    assert got["verdict"] == "HOLDS" and got["note"] == almanac.NOTE
    assert got["wisdom"] == "start low, go slow"         # the full record, not a brief
    assert almanac.get("missing") is None
    assert almanac.get("") is None


# ---- search across every field ----

def test_search_matches_title_domain_and_situation(store):
    store(RECORDS)
    assert {e["id"] for e in almanac.search("compound")["entries"]} == {"a2"}      # title
    assert {e["id"] for e in almanac.search("finance")["entries"]} == {"a2"}       # domain
    assert {e["id"] for e in almanac.search("chest")["entries"]} == {"a1"}         # situation
    assert {e["id"] for e in almanac.search("watch the sky")["entries"]} == {"a3"} # wisdom
    assert {e["id"] for e in almanac.search("health")["entries"]} == {"a1", "a3"}  # category


def test_search_empty_query_returns_all_and_limit_caps(store):
    store(RECORDS)
    assert almanac.search("")["total"] == 3
    capped = almanac.search("", limit=2)
    assert capped["total"] == 2 and len(capped["entries"]) == 2
    assert almanac.search("no-such-needle")["total"] == 0


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
