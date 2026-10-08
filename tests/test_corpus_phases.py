"""The corpus load, phased (2026-10-08): the launch roll-call measured the corpus warm at ~40 s on the box —
one number nobody can optimize. load_cards() and default_corpus() now report where the time went (the
cards.jsonl pass, the extras, the frozen-shelf DF tokenization, the index build) in corpus.LOAD_PHASES.
Pinned on a tiny corpus so it stays fast; the counts must reconcile with what was loaded."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import corpus  # noqa: E402


def _tiny(tmp_path: Path) -> Path:
    p = tmp_path / "cards.jsonl"
    rows = [{"id": "c1", "title": "Light", "body": "the speed of light is constant", "shelf": "physics_notes"},
            {"id": "c2", "title": "Salt", "body": "sodium chloride dissolves in water", "shelf": "physics_notes"},
            {"id": "c3", "title": "Shepherd", "body": "the LORD is my shepherd", "shelf": "scripture_notes"}]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def test_load_cards_reports_phases_and_counts_reconcile(tmp_path):
    p = _tiny(tmp_path)
    df, fz = {}, {}
    cards = corpus.load_cards(p, _df_out=df, _frozen_out=fz)
    ph = corpus.LOAD_PHASES
    assert ph["resident_cards"] + ph["frozen_cards"] == 3 == len(cards) + ph["frozen_cards"]
    for k in ("cards_jsonl_ms", "extras_ms", "frozen_df_ms"):
        assert k in ph and ph[k] >= 0, (k, ph)


def test_default_corpus_reports_load_vs_index_build(tmp_path, monkeypatch):
    p = _tiny(tmp_path)
    # the whole data dir, not just the cards file: load_cards also folds in the extras and the prophecy
    # signposts from the data dir, and the real ones must not leak into a 3-card corpus
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CONCORDANCE_CARDS_JSONL", str(p))
    monkeypatch.setattr(corpus, "frozen_shelves", lambda: frozenset())
    prior = corpus._DEFAULT
    corpus._DEFAULT = None
    try:
        c = corpus.default_corpus()
        ph = dict(corpus.LOAD_PHASES)
    finally:
        corpus._DEFAULT = prior
    assert len(c.cards) == ph["resident_cards"] == 3
    assert ph["index_build_ms"] >= 0 and ph["load_cards_ms"] >= 0
    assert abs(ph["total_ms"] - (ph["load_cards_ms"] + ph["index_build_ms"])) < 50   # the two parts are the whole
    assert ph["frozen_index"] == 0 and ph["df_tokens"] == 0                           # nothing frozen here
