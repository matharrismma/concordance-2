"""The frozen cache wired into default_corpus (2026-10-08) — the pins that make a persisted DF honest:

  miss  -> cold build (every frozen card tokenized), cache written with exactly the big contributors;
  hit   -> the cached df/fz are loaded, NO frozen card from a cached file is re-tokenized (frozen_df_ms ~ 0),
           and the corpus is IDENTICAL (same df, same frozen index);
  live  -> a frozen card in a small/volatile file (receipt_cards.jsonl) is handled live on a hit and merged;
  stale -> a changed contributor file misses and rebuilds; the valve turns it all off.
A tiny corpus; the contribution threshold is lowered so a 2-card file counts as "big"."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import corpus, frozen_cache as FC  # noqa: E402

FROZEN = "scripture_notes"


def _rows(p: Path, rows):
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _seed(d: Path):
    _rows(d / "cards.jsonl", [
        {"id": "c1", "title": "Light", "body": "the speed of light is constant", "shelf": "physics_notes"},
        {"id": "c3", "title": "Shepherd", "body": "the LORD is my shepherd I shall not want", "shelf": FROZEN},
        {"id": "c4", "title": "Still waters", "body": "he leadeth me beside the still waters", "shelf": FROZEN}])
    # a BIG contributor (threshold lowered to 2) — a REAL extras source name: load_cards reads a fixed list of
    # extras, and a file outside it is never loaded (the dictionary, for one, lives on its shard)
    _rows(d / "gutenberg_cards.jsonl", [
        {"id": "d1", "title": "Zymurgy", "body": "the chemistry of fermentation", "shelf": FROZEN},
        {"id": "d2", "title": "Yarrow", "body": "a flowering plant of the daisy family", "shelf": FROZEN}])
    _rows(d / "source_cards.jsonl", [                         # a BIG but MIXED contributor: cached, still read
        {"id": "s1", "title": "Nuclide", "body": "the binding energy per nucleon", "shelf": FROZEN},
        {"id": "s2", "title": "Star", "body": "the apparent magnitude of a star", "shelf": FROZEN},
        {"id": "s3", "title": "Port", "body": "a harbour on the eastern coast", "shelf": "physics_notes"}])
    _rows(d / "receipt_cards.jsonl", [                        # a SMALL volatile contributor: always live
        {"id": "r1", "title": "Receipt one", "body": "sealed arithmetic receipt", "shelf": FROZEN}])


def _build(monkeypatch, d: Path, frozen=frozenset({FROZEN})):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(d))
    monkeypatch.delenv("CONCORDANCE_CARDS_JSONL", raising=False)
    monkeypatch.setattr(corpus, "frozen_shelves", lambda: frozenset(frozen))
    corpus._DEFAULT = None
    c = corpus.default_corpus()
    return c, dict(corpus.LOAD_PHASES)


def test_miss_then_hit_is_identical_and_skips_tokenizing(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_FROZEN_CACHE_MIN", "2")
    monkeypatch.delenv("CONCORDANCE_FROZEN_CACHE", raising=False)
    _seed(tmp_path)
    prior = corpus._DEFAULT
    try:
        c1, ph1 = _build(monkeypatch, tmp_path)
        assert ph1["frozen_cache"] == "miss"
        assert FC.peek_contributors(FC.cache_path(tmp_path)) == ["cards.jsonl", "gutenberg_cards.jsonl", "source_cards.jsonl"]
        assert ph1["cached_skip_files"] == ["gutenberg_cards.jsonl"]        # frozen-only: skippable; the mixed one is not
        assert set(c1._frozen) == {"c3", "c4", "d1", "d2", "s1", "s2", "r1"}   # all seven frozen ids known
        assert c1._df_extra.get("shepherd") == 1 and c1._df_extra.get("fermentation") == 1
        c2, ph2 = _build(monkeypatch, tmp_path)
        assert ph2["frozen_cache"] == "hit"
        assert c2._df_extra == c1._df_extra and c2._frozen == c1._frozen   # identical corpus
        assert ph2["files_skipped"] == 1                                    # gutenberg never opened
        assert ph2["files_seeked"] == 2                                     # cards.jsonl + source_cards.jsonl: resident lines only
        assert "s3" in c2.cards and "c1" in c2.cards                       # the mixed file's resident card survived
        assert ph2["frozen_cards_cached"] == 6 and ph2["frozen_cards"] == 1  # c3,c4,d1,d2,s1,s2 from the cache; only r1 seen, live
        # the memory cut: the stored call and surface strings ARE the interned objects (one object per distinct
        # value), and the sharing survives the cache roundtrip. Surfaces share across every entry; calls share
        # only where two cards carry the same call — deep_call gives sublayered shelves a call PER CARD, so the
        # fixture's d1/d2 differ on purpose (measured: that is why interning calls buys little on big shelves).
        import sys as _sys
        for c in (c1, c2):
            assert c._frozen["d1"][2] is c._frozen["c3"][2] is c._frozen["r1"][2]
            assert c._frozen["d1"][0] is _sys.intern(c._frozen["d1"][0])
            assert c._frozen["d1"][0] != c._frozen["d2"][0]
        # RSS deltas are measured, not asserted: in this process the PREVIOUS corpus was just dropped, so the
        # collector can free more than the new build adds and the delta goes negative. At boot it is positive.
        assert ph2["rss_kb_total_delta"] is None or isinstance(ph2["rss_kb_total_delta"], int)
        for k in ("rss_kb_cache_delta", "rss_kb_load_delta", "rss_kb_index_delta"):
            assert k in ph2
    finally:
        corpus._DEFAULT = prior


def test_small_volatile_file_is_live_on_a_hit(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_FROZEN_CACHE_MIN", "2")
    monkeypatch.delenv("CONCORDANCE_FROZEN_CACHE", raising=False)
    _seed(tmp_path)
    prior = corpus._DEFAULT
    try:
        _build(monkeypatch, tmp_path)                                       # cold: writes the cache
        _rows(tmp_path / "receipt_cards.jsonl", [                           # a NEW seal lands (frozen shelf)
            {"id": "r1", "title": "Receipt one", "body": "sealed arithmetic receipt", "shelf": FROZEN},
            {"id": "r2", "title": "Receipt two", "body": "a brachistochrone receipt", "shelf": FROZEN}])
        c3, ph3 = _build(monkeypatch, tmp_path)
        assert ph3["frozen_cache"] == "hit"                                 # the key did NOT move
        assert "r2" in c3._frozen and c3._df_extra.get("brachistochrone") == 1   # ...and r2 is not missing
    finally:
        corpus._DEFAULT = prior


def test_changed_contributor_misses_and_rebuilds(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_FROZEN_CACHE_MIN", "2")
    monkeypatch.delenv("CONCORDANCE_FROZEN_CACHE", raising=False)
    _seed(tmp_path)
    prior = corpus._DEFAULT
    try:
        _build(monkeypatch, tmp_path)
        _rows(tmp_path / "gutenberg_cards.jsonl", [
            {"id": "d1", "title": "Zymurgy", "body": "the chemistry of fermentation", "shelf": FROZEN},
            {"id": "d2", "title": "Yarrow", "body": "a flowering plant of the daisy family", "shelf": FROZEN},
            {"id": "d3", "title": "Xylem", "body": "the water-conducting tissue of plants", "shelf": FROZEN}])
        c4, ph4 = _build(monkeypatch, tmp_path)
        assert ph4["frozen_cache"] == "miss" and "d3" in c4._frozen and c4._df_extra.get("xylem") == 1
    finally:
        corpus._DEFAULT = prior


def test_valve_off_never_reads_or_writes(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_FROZEN_CACHE", "0")
    _seed(tmp_path)
    prior = corpus._DEFAULT
    try:
        _, ph = _build(monkeypatch, tmp_path)
        assert ph["frozen_cache"] == "off" and not FC.cache_path(tmp_path).exists()
    finally:
        corpus._DEFAULT = prior


def test_frozen_non_file_cards_are_not_double_counted_on_a_hit(tmp_path, monkeypatch):
    """Review 2026-10-08: the prophecy signposts are shaped at load from a non-file source. If their shelf is
    frozen, their DF must not be both saved in the cache AND re-tokenized live on a hit."""
    import json as _json
    monkeypatch.setenv("CONCORDANCE_FROZEN_CACHE_MIN", "2")
    monkeypatch.delenv("CONCORDANCE_FROZEN_CACHE", raising=False)
    _seed(tmp_path)
    (tmp_path / "prophecy").mkdir()
    (tmp_path / "prophecy" / "signposts.jsonl").write_text(_json.dumps(
        {"id": "sp1", "title": "The Way", "verification": "the way was found in every nation",
         "wisdom": "and it points to Christ"}) + "\n", encoding="utf-8")
    from concordance import prophecy as _prophecy
    monkeypatch.setattr(_prophecy, "_file", lambda: tmp_path / "prophecy" / "signposts.jsonl")
    sp_shelf = corpus._signpost_card({"id": "x", "title": "x"})["shelf"]     # whatever shelf the shaping assigns
    prior = corpus._DEFAULT
    try:
        c1, ph1 = _build(monkeypatch, tmp_path, frozen={FROZEN, sp_shelf})
        assert ph1["frozen_cache"] == "miss" and "sp1" in c1._frozen and c1._df_extra.get("nation") == 1
        c2, ph2 = _build(monkeypatch, tmp_path, frozen={FROZEN, sp_shelf})
        assert ph2["frozen_cache"] == "hit"
        assert c2._df_extra == c1._df_extra and c2._frozen == c1._frozen     # counted exactly once, both ways
    finally:
        corpus._DEFAULT = prior
