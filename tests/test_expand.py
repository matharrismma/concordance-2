"""Expand on the call — a miss is a slower answer, not a dead end. expand.py was at 25%, no test.

Two planes, one act: try to answer a miss NOW (find + card), and open a want ONLY when offline (the
one case a miss becomes a queue ticket). `pull_and_card` joins the citation path to the craft path —
fetch a public-domain source, cut verified span cards, keep them so the next asking never goes out,
and a verified-PD source releases straight to the shared library while an uncertain one is held for
review. The test drives injected providers/fetch/craft so no network is touched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import corpus, craft, expand, find, sources, unchecked, wants  # noqa: E402


# ---- offline gate ----

def test_offline_reflects_find_enabled(monkeypatch):
    monkeypatch.setattr(find, "enabled", lambda: True)
    assert expand.offline() is False
    monkeypatch.setattr(find, "enabled", lambda: False)
    assert expand.offline() is True


# ---- expand(): the four outcomes ----

def test_expand_empty_query_asks_nothing(monkeypatch):
    monkeypatch.setattr(expand, "offline", lambda: False)
    assert expand.expand("   ", config=None)["status"] == "nothing_found"


def test_expand_offline_opens_a_want(monkeypatch):
    monkeypatch.setattr(expand, "offline", lambda: True)
    monkeypatch.setattr(wants, "open_want", lambda **k: {"id": "w7", "ok": True})
    r = expand.expand("Rigveda", config=None, plane="agent")
    assert r["status"] == "queued" and r["want_id"] == "w7" and r["ok"] is True


def test_expand_online_acquires_when_the_slow_lane_finds(monkeypatch):
    monkeypatch.setattr(expand, "offline", lambda: False)
    monkeypatch.setattr(find, "find_and_check",
                        lambda q, cfg, plane="human": {"documents": [{"title": "X"}], "answer": "a",
                                                       "framed": "f", "checks_verdict": "ok",
                                                       "source_note": "PD"})
    r = expand.expand("Rigveda", config=None, plane="nonsense")   # bad plane -> human
    assert r["status"] == "acquired" and r["plane"] == "human"
    assert r["held_for_review"] is True and r["documents"] == [{"title": "X"}]


def test_expand_online_nothing_found_is_not_a_want(monkeypatch):
    monkeypatch.setattr(expand, "offline", lambda: False)
    monkeypatch.setattr(find, "find_and_check", lambda q, cfg, plane="human": {"documents": [], "answer": None})
    assert expand.expand("obscure", config=None)["status"] == "nothing_found"


def test_expand_survives_a_broken_slow_lane(monkeypatch):
    monkeypatch.setattr(expand, "offline", lambda: False)
    def boom(*a, **k):
        raise RuntimeError("tortoise fell over")
    monkeypatch.setattr(find, "find_and_check", boom)
    assert expand.expand("x", config=None)["status"] == "nothing_found"   # never breaks the fast lane


# ---- the PD check ----

def test_pd_ok_by_provider_and_year():
    assert expand._pd_ok({"source": "Project Gutenberg"}) is True
    assert expand._pd_ok({"source": "Internet Archive", "year": "1900"}) is True
    assert expand._pd_ok({"source": "Internet Archive", "year": "1990"}) is False
    assert expand._pd_ok({"source": "Some Blog"}) is False


# ---- pull_and_card: early returns ----

def test_pull_early_returns(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(expand, "offline", lambda: True)
    assert expand.pull_and_card("q", "subj")["status"] == "offline"
    monkeypatch.setattr(expand, "offline", lambda: False)
    monkeypatch.setattr(sources, "sources_dir", lambda: None)
    assert expand.pull_and_card("q", "subj")["status"] == "no_ark"
    assert expand.pull_and_card("", "")["status"] == "nothing_found"


# ---- pull_and_card: the whole pull, injected end to end ----

@pytest.fixture
def wired(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(expand, "offline", lambda: False)
    monkeypatch.setattr(sources, "sources_dir", lambda: tmp_path)
    monkeypatch.setattr(sources, "resolve_text_url", lambda u: (u + ".txt") if u else "")
    monkeypatch.setattr(find, "is_practical", lambda q: True)
    monkeypatch.setattr(find, "_spine_card", lambda shelf: None)
    monkeypatch.setattr(craft, "verify_spans", lambda cards: {"false": 0, "true": len(cards)})
    monkeypatch.setattr(corpus, "add_to_default", lambda c: None)
    monkeypatch.setattr(unchecked, "mark", lambda c: {**c, "_marked": True})
    cards = [{"id": f"card_x{i}", "body": "span"} for i in range(3)]

    def craft_fn(sha, subj, parent_id=None, plane="human"):
        return {"cards": cards, "quality": {"heading_hits": 1, "lead_hits": 1, "cards": 3}}

    def make(source, year="1900"):
        doc = {"url": "http://ex/book", "title": "Woodcraft", "license": "public domain",
               "year": year, "source": source}
        return expand.pull_and_card(
            "how do I start a fire", "start fire", plane="human",
            providers=[lambda subj, limit=3: [doc]],
            fetch=lambda url, **k: {"status": "held", "sha256": "a" * 64},
            craft_fn=craft_fn)
    return make, tmp_path


def test_pull_releases_a_verified_pd_source(wired):
    make, tmp_path = wired
    r = make("Project Gutenberg")
    assert r["status"] == "carded" and r["released_public"] is True and r["held_for_review"] is False
    assert r["source_card"]["lifecycle_stage"] == "public"
    assert len(r["cards"]) == 3 and all(c["extra"]["tortoise"] for c in r["cards"])
    # kept on disk in the mint's own store
    kept = (tmp_path / "web_cache.jsonl").read_text(encoding="utf-8")
    assert "card_x0" in kept


def test_pull_holds_an_uncertain_source_for_review(wired):
    make, _tmp = wired
    r = make("Internet Archive", year="1990")     # too recent -> not verified PD
    assert r["status"] == "carded" and r["released_public"] is False and r["held_for_review"] is True
    assert r["source_card"].get("_marked") is True   # routed through unchecked.mark
    assert all(c["lifecycle_stage"] == "public_review" for c in r["cards"])


def test_keep_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(corpus, "add_to_default", lambda c: None)
    cards = [{"id": "k1"}, {"id": "k2"}]
    assert expand._keep(cards) == 2
    assert expand._keep(cards) == 0            # already written — nothing new
    lines = (tmp_path / "web_cache.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
