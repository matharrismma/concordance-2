"""THE CORPUS CACHE (issue #10, corpus_cache.py) — a cache-loaded corpus IS the fresh build, and any changed
input is a miss.

Pinned on a small keeping that exercises every load-time derivation the cache must carry: shelving (call numbers
+ facets), an extra card source, a bridge overlay (directional + symmetric edges, applied reciprocally), a
prophecy signpost shaped at load, an exact duplicate inline edge (deduped at the gate), a private card and a
share-alike card (withheld from the public index), and the frozen index + DF table when a shelf is frozen.

The parity battery here has the same shape as the one-shot proof on the real keeping
(tools/build_corpus_cache.py --verify): card counts, the public order's ends, search top-10s, connections(),
stats(), and the raw structures themselves. Runnable with pytest."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402

from concordance import corpus  # noqa: E402
from concordance import corpus_cache as CC  # noqa: E402

QUERIES = ["chlorophyll sunlight", "shepherd", "fermentation", "hydrogen", "nations", "speed of light",
           "energy", "Zymurgy", "Psalm 23:1", "harbour coast"]


def _rows(p: Path, rows) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _seed(d: Path) -> None:
    _rows(d / "cards.jsonl", [
        {"id": "c1", "title": "Photosynthesis", "shelf": "classics", "surface": "secular", "kind": "note",
         "body": "plants convert sunlight into chemical energy via chlorophyll " * 6,
         "bands": ["biology", "energy"], "source": {"label": "Botany primer (PD)", "ref": "ch. 3"},
         "connections": [{"to_card_id": "c3", "relationship": "cites", "evidence": "the energy currency"},
                         {"to_card_id": "c3", "relationship": "cites", "evidence": "an exact duplicate edge"}]},
        {"id": "c2", "title": "Psalm 23:1", "shelf": "scripture", "surface": "witness", "kind": "verse",
         "body": "The LORD is my shepherd; I shall not want.", "bands": ["psalm_23", "shepherd"],
         "source": {"label": "KJV (PD)", "ref": "Psalm 23:1"}},
        {"id": "c3", "title": "Mitochondria", "shelf": "classics", "surface": "secular", "kind": "note",
         "body": "the powerhouse of the cell produces ATP, the energy currency of life " * 5,
         "bands": ["biology"], "source": {"label": "Botany primer (PD)", "ref": "ch. 4"}},
        {"id": "c4", "title": "Light", "shelf": "physics_notes", "surface": "secular",
         "body": "the speed of light in vacuum is a constant of nature"},
        {"id": "c5", "title": "Salt", "shelf": "physics_notes", "surface": "secular",
         "body": "sodium chloride dissolves in water; a harbour on the eastern coast is salt too"},
        {"id": "c6", "title": "A private draft", "shelf": "classics", "surface": "secular",
         "lifecycle_stage": "private", "body": "chlorophyll sunlight energy — never public"},
        {"id": "c7", "title": "A share-alike import", "shelf": "classics", "surface": "secular",
         "body": "chlorophyll sunlight energy under a viral license",
         "source": {"label": "Some wiki (CC-BY-SA)", "url": "https://example.org/x"}},
        {"id": "w1", "title": "Zymurgy", "shelf": "word_notes", "surface": "secular",
         "body": "the chemistry of fermentation of barley in brewing"},
        {"id": "w2", "title": "Yarrow", "shelf": "word_notes", "surface": "secular",
         "body": "a flowering plant of the daisy family"},
        {"id": "card_spine_foreshadows", "title": "The foreshadows", "shelf": "spines", "surface": "witness",
         "body": "the nations carried parts of the story"},
    ])
    _rows(d / "reference_cards.jsonl", [                               # an EXTRA card source
        {"id": "r1", "title": "Hydrogen", "shelf": "elements", "surface": "secular",
         "body": "hydrogen, atomic number 1, the lightest element", "bands": ["element", "hydrogen"]},
        {"id": "r2", "title": "Helium", "shelf": "elements", "surface": "secular",
         "body": "helium, atomic number 2, a noble gas"},
    ])
    _rows(d / "reference_bridges.jsonl", [                             # a bridge OVERLAY: directional + symmetric
        {"a": "r1", "b": "c4", "relationship": "member_of", "evidence": "a worked example"},
        {"a": "r2", "b": "c5", "relationship": "connects_at", "evidence": "a lateral joint"},
    ])
    _rows(d / "prophecy" / "signposts.jsonl", [                         # a signpost shaped AT LOAD
        {"id": "signpost_test", "title": "The way among the nations", "verdict": "a part of the story",
         "verification": "the nations held a part", "wisdom": "fulfilled in Christ",
         "triggers": {"keywords": ["way", "nations"]}, "domains": ["religion"], "category": "test"},
    ])


def _boot(monkeypatch, d: Path, cache_dir: Path, mode: str = "1", frozen=frozenset()):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(d))
    monkeypatch.delenv("CONCORDANCE_CARDS_JSONL", raising=False)
    monkeypatch.delenv("CONCORDANCE_PROPHECY_DIR", raising=False)
    monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE", mode)
    monkeypatch.setenv("CONCORDANCE_CORPUS_CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(corpus, "frozen_shelves", lambda: frozenset(frozen))
    corpus._DEFAULT = None
    c = corpus.default_corpus()
    return c, dict(corpus.LOAD_PHASES)


def _battery(c: corpus.Corpus) -> dict:
    """The parity battery — the same shape tools/build_corpus_cache.py --verify computes on the real keeping."""
    ps = c._public_sorted
    ids = [ps[i * len(ps) // 5] for i in range(5)] + ["c1", "r1", "signpost_test"]
    return {
        "resident": len(c.cards), "frozen": len(c._frozen), "public": len(ps), "n": c._n,
        "order": list(c.cards), "public_first_last": (ps[:50], ps[-50:]),
        "search": {q: [h["id"] for h in corpus.search(q, limit=10)] for q in QUERIES},
        "connections": {cid: corpus.connections(cid, limit=10) for cid in ids},
        "stats": corpus.stats(),
        "browse": corpus.browse(call="classics", limit=20),
        "locate": corpus.locate("Zymurgy"),
    }


@pytest.fixture
def world(tmp_path, monkeypatch):
    _seed(tmp_path / "data")
    prior = corpus._DEFAULT
    try:
        yield tmp_path / "data", tmp_path / "cache"
    finally:
        corpus._DEFAULT = prior


def _cache_files(cache_dir: Path):
    return sorted(cache_dir.glob(CC.PREFIX + "*" + CC.SUFFIX)) if cache_dir.exists() else []


def test_miss_then_hit_is_the_same_corpus(world, monkeypatch):
    d, cache = world
    c1, ph1 = _boot(monkeypatch, d, cache)
    assert ph1["corpus_cache"] == "miss" and ph1["corpus_cache_saved"] is True, ph1
    assert ph1["dup_edges_dropped"] == 1                                     # the gate ran on the cold path
    files = _cache_files(cache)
    assert len(files) == 1 and files[0] == Path(ph1["corpus_cache_file"])
    b1 = _battery(c1)
    assert b1["search"]["chlorophyll sunlight"] == ["c1"]                   # withheld cards never indexed
    assert "c6" not in c1._public_sorted and "c7" not in c1._public_sorted

    c2, ph2 = _boot(monkeypatch, d, cache)
    assert ph2["corpus_cache"] == "hit" and ph2["load_cards_ms"] == 0.0 and ph2["index_build_ms"] == 0.0, ph2
    assert ph2["resident_cards"] == len(c1.cards) and ph2["frozen_cache"] == "bypassed"
    assert c2 is not c1
    assert c2._search_cache == {}                                             # runtime state: fresh, not restored
    # THE STRUCTURES, EXACTLY — same cards in the same order, same postings, same tree, same public order
    for key, attr in corpus.Corpus._STATE_FIELDS:
        assert getattr(c2, attr) == getattr(c1, attr), key
    assert list(c2.cards) == list(c1.cards)
    assert [list(c2._by_token[t]) for t in c2._by_token] == [list(c1._by_token[t]) for t in c1._by_token]
    assert list(c2._by_token) == list(c1._by_token) and list(c2._cids_by_call) == list(c1._cids_by_call)
    # the derived content made it: bridges on BOTH cards with the declared reverse label, the signpost, facets
    assert any(e["to_card_id"] == "c4" and e["relationship"] == "member_of" for e in c2.cards["r1"]["connections"])
    assert any(e["to_card_id"] == "r1" and e["relationship"] == "has_member" for e in c2.cards["c4"]["connections"])
    assert any(e["relationship"] == "connects_at" for e in c2.cards["c5"]["connections"])
    assert c2.cards["signpost_test"]["shelf"] == "signposts" and c2.cards["c1"]["call"] == c1.cards["c1"]["call"]
    assert len(c2.cards["c1"]["connections"]) == 1                            # the duplicate stayed dropped
    # THE BEHAVIOR, EXACTLY — search / connections / stats / browse / locate
    assert _battery(c2) == b1
    # ONE id object per card, shared by the key, the card and every posting — as a fresh build shares them
    key_obj = {k: k for k in c2.cards}
    for cid, card in c2.cards.items():
        assert card["id"] is cid
    for t, lst in c2._by_token.items():
        for cid in lst:
            assert key_obj[cid] is cid
    for cid in c2._public_sorted:
        assert key_obj[cid] is cid
    # dict keys interned on the way out: one object per distinct key across the keeping
    k1 = next(k for k in c2.cards["c1"] if k == "title")
    k3 = next(k for k in c2.cards["c3"] if k == "title")
    assert k1 is k3
    c2.search("fermentation")                                                 # search works after a restore
    assert c2._search_cache


def test_edit_one_byte_misses_rebuilds_and_prunes(world, monkeypatch):
    d, cache = world
    _, ph1 = _boot(monkeypatch, d, cache)
    old = Path(ph1["corpus_cache_file"])
    _, ph2 = _boot(monkeypatch, d, cache)
    assert ph2["corpus_cache"] == "hit"
    p = d / "cards.jsonl"
    st = p.stat()
    text = p.read_text(encoding="utf-8")
    assert '"title": "Yarrow"' in text
    p.write_text(text.replace('"title": "Yarrow"', '"title": "Yarrom"'), encoding="utf-8")   # same size
    if p.stat().st_mtime_ns == st.st_mtime_ns:                                # a coarse clock: bump it
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000))
    assert p.stat().st_size == st.st_size
    c3, ph3 = _boot(monkeypatch, d, cache)
    assert ph3["corpus_cache"] == "miss" and ph3["corpus_cache_saved"] is True
    assert c3.cards["w2"]["title"] == "Yarrom"                                 # the JSONL is the truth
    new = Path(ph3["corpus_cache_file"])
    assert new != old and new.exists() and not old.exists()                   # the superseded file is gone
    assert ph3["corpus_cache_pruned"] == 1
    _, ph4 = _boot(monkeypatch, d, cache)
    assert ph4["corpus_cache"] == "hit" and ph4["corpus_cache_file"] == str(new)


def test_a_new_source_file_or_overlay_misses(world, monkeypatch):
    d, cache = world
    _boot(monkeypatch, d, cache)
    _rows(d / "theory_cards.jsonl", [{"id": "t1", "title": "A theory", "shelf": "theories", "surface": "secular",
                                      "body": "a load-bearing theory about fermentation"}])
    c2, ph2 = _boot(monkeypatch, d, cache)
    assert ph2["corpus_cache"] == "miss" and "t1" in c2.cards
    _rows(d / "chain_bridges.jsonl", [{"a": "t1", "b": "w1", "relationship": "builds_on", "evidence": "x"}])
    c3, ph3 = _boot(monkeypatch, d, cache)
    assert ph3["corpus_cache"] == "miss"
    assert any(e["relationship"] == "enables" for e in c3.cards["w1"]["connections"])
    _, ph4 = _boot(monkeypatch, d, cache)
    assert ph4["corpus_cache"] == "hit"


def test_off_writes_nothing_and_rebuild_ignores_the_file(world, monkeypatch):
    d, cache = world
    _, ph = _boot(monkeypatch, d, cache, mode="0")
    assert ph["corpus_cache"] == "off" and ph.get("corpus_cache_saved") is None and not _cache_files(cache)
    _, ph1 = _boot(monkeypatch, d, cache)
    assert ph1["corpus_cache"] == "miss"
    _, ph2 = _boot(monkeypatch, d, cache, mode="rebuild")
    assert ph2["corpus_cache"] == "miss" and ph2["corpus_cache_saved"] is True and len(_cache_files(cache)) == 1
    _, ph3 = _boot(monkeypatch, d, cache)
    assert ph3["corpus_cache"] == "hit"


def test_a_corrupt_or_truncated_file_is_a_miss_never_an_error(world, monkeypatch):
    d, cache = world
    _, ph1 = _boot(monkeypatch, d, cache)
    f = Path(ph1["corpus_cache_file"])
    blob = f.read_bytes()
    f.write_bytes(blob[: len(blob) // 2])                                     # truncated mid-record
    c2, ph2 = _boot(monkeypatch, d, cache)
    assert ph2["corpus_cache"] == "stale" and ph2["corpus_cache_saved"] is True and len(c2.cards) == 13
    f.write_bytes(b"\x00" * 64 + blob[64:])                                   # a mangled header
    c3, ph3 = _boot(monkeypatch, d, cache)
    assert ph3["corpus_cache"] == "stale" and len(c3.cards) == 13
    f.write_bytes(blob)                                                       # whole again
    _, ph4 = _boot(monkeypatch, d, cache)
    assert ph4["corpus_cache"] == "hit"
    # a foreign key under the same name is a miss, never a wrong corpus
    assert CC.load(f, "not-the-key") is None


def test_the_frozen_index_and_df_table_round_trip(world, monkeypatch):
    d, cache = world
    frozen = frozenset({"word_notes"})
    c1, ph1 = _boot(monkeypatch, d, cache, frozen=frozen)
    assert ph1["corpus_cache"] == "miss" and set(c1._frozen) == {"w1", "w2"} and "w1" not in c1.cards
    assert c1._df_extra.get("fermentation") == 1 and c1._froze is True
    s1, b1 = corpus.stats(), corpus.browse(call="word_notes")
    c2, ph2 = _boot(monkeypatch, d, cache, frozen=frozen)
    assert ph2["corpus_cache"] == "hit" and ph2["frozen_index"] == 2 and ph2["df_tokens"] == len(c1._df_extra)
    assert c2._frozen == c1._frozen and c2._df_extra == c1._df_extra and c2._froze is True
    assert c2._frozen_shelf_counts == c1._frozen_shelf_counts == {"word_notes": 2}
    assert c2._public_sorted == c1._public_sorted and "w1" in c2._public_sorted
    assert corpus.stats() == s1 and corpus.browse(call="word_notes") == b1
    # a different freeze set is a different key: a miss, and the frozen shelf comes home resident
    c3, ph3 = _boot(monkeypatch, d, cache)
    assert ph3["corpus_cache"] == "miss" and "w1" in c3.cards and not c3._frozen


def test_key_covers_the_deriving_code_and_the_interpreter(world):
    d, _cache = world
    files = corpus.source_files()
    assert files == [] or all(f.exists() for f in files)
    k1 = CC.make_key([d / "cards.jsonl"], (), code="a")
    assert k1 != CC.make_key([d / "cards.jsonl"], (), code="b")              # corpus.py changed -> new key
    assert k1 != CC.make_key([d / "cards.jsonl"], ("x",), code="a")          # freeze set is in the key
    assert k1 == CC.make_key([d / "cards.jsonl"], (), code="a")              # and it is deterministic
