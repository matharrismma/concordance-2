"""The Codex — the project compiled, indexed, and signed. codex.py was at 15% with no dedicated test.

It is COMPILED, never authored: it inverts connection cards into a per-book cross-reference index,
conceptual bands into a theme web (a theme binds only at >=3 sites — Deut 19:15 plus one), builds a
witnessed connection hub, and seals the whole as an Ed25519-signed manifest that can be re-verified
and drift-checked. The test drives a small synthetic corpus through every face and asserts the
counts, the 3-site theme floor, the seal/verify/drift path, and the navigational surfaces.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

from concordance import codex, corpus  # noqa: E402


def _conn(cid, book, verse, url, title, tier="fathers"):
    return {"id": cid, "kind": "connection", "title": title, "bands": [book],
            "witness_status": "passed", "source_hash": "h_" + cid,
            "source": {"url": url, "authority_tier": tier, "ref": verse},
            "extra": {"verse_refs": [verse], "relationship_kind": "comments_on",
                      "explanation": "on " + verse}}


def _note(cid, bands, tier, url=None):
    return {"id": cid, "kind": "note", "title": "note " + cid, "shelf": "scripture", "bands": bands,
            "source_hash": "h_" + cid, "source": {"authority_tier": tier, **({"url": url} if url else {})}}


# a corpus that exercises every path: 3 witnessed+sealed connections (two on the SAME verse -> a
# witnessed hub), and note cards where "covenant" reaches the 3-site floor but "mercy" does not.
CARDS = {
    "c1": _conn("c1", "genesis", "Genesis 1:1", "/s/abcdef12", "Chrysostom on Gen 1:1"),
    "c2": _conn("c2", "genesis", "Genesis 1:1", "/s/beef1234", "Augustine on Gen 1:1"),
    "c3": _conn("c3", "john", "John 1:1", "/s/1234abcd", "Note on John 1:1", tier="bible"),
    "n1": _note("n1", ["covenant", "mercy"], "bible", "/s/aaaa1111"),
    "n2": _note("n2", ["covenant", "mercy"], "fathers"),
    "n3": _note("n3", ["covenant"], "matt"),
}


@pytest.fixture
def built(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    (tmp_path / "bible_en.jsonl").write_text(
        '{"book": "Genesis"}\n{"book": "John"}\n', encoding="utf-8")
    monkeypatch.setattr(corpus, "default_corpus", lambda *a, **k: types.SimpleNamespace(cards=CARDS))
    monkeypatch.setattr(corpus, "is_public", lambda c: True)
    return tmp_path


# ---- scripture index ----

def test_scripture_index_inverts_connections_per_book(built):
    r = codex.build_scripture_index()
    st = r["stats"]
    assert st["cross_references"] == 3 and st["verse_level"] == 3
    assert st["witnessed"] == 3 and st["sealed"] == 3
    assert st["books_indexed"] == 2
    assert set(r["books"]) == {"Genesis", "John"}
    assert len(r["books"]["Genesis"]) == 2
    assert codex.load_scripture()["stats"]["cross_references"] == 3   # round-trip from disk


def test_scripture_summary_and_book_lookup(built):
    codex.build_scripture_index()
    assert codex.scripture_summary()["books"] == {"Genesis": 2, "John": 1}
    gen = codex.scripture_book("Genesis")
    assert gen["count"] == 2 and len(gen["cross_references"]) == 2
    assert codex.scripture_book("genesis")["book"] == "Genesis"   # case/underscore-insensitive
    assert codex.scripture_book("Nowhere") is None


# ---- theme index: the 3-site floor ----

def test_theme_binds_only_at_three_sites(built):
    r = codex.build_theme_index()
    assert "covenant" in r["themes"], "covenant reaches 3 sites and must bind"
    assert "mercy" not in r["themes"], "mercy has 2 sites — below the Deut 19:15+1 floor"
    assert r["themes"]["covenant"]["count"] == 3
    assert r["stats"]["min_sites"] == 3
    assert codex.theme("covenant")["count"] == 3
    assert codex.theme("mercy") is None


def test_theme_span_counts_distinct_tiers(built):
    codex.build_theme_index()
    # covenant spans bible + fathers + matt -> span 3 (cross-tradition)
    assert codex.theme("covenant")["span"] == 3


# ---- connection index (witnessed hub) ----

def test_connection_index_finds_the_witnessed_hub(built):
    codex.build_scripture_index()
    con = codex.build_connection_index()
    assert "stats" in con
    assert codex.load_connections()["stats"] == con["stats"]


# ---- artifact: seal, verify, drift ----

def test_verify_before_seal_is_honest(built):
    assert codex.verify_artifact() == {"ok": False, "reason": "no artifact sealed yet"}


def test_artifact_seals_and_verifies(built):
    codex.build_all()
    art = codex.load_artifact()
    assert art["manifest"]["codex"] == "narrowhighway"
    assert art["manifest"]["body"]["public_cards"] == 6
    v = codex.verify_artifact()
    assert v["manifest_hash_ok"] is True
    assert v["ok"] is True
    assert v["body_drift_since_seal"] is False


def test_verify_detects_body_drift(built, monkeypatch):
    codex.build_all()
    # the body changes after sealing -> drift must be flagged (authority never silently upgraded)
    fewer = {"c1": CARDS["c1"]}
    monkeypatch.setattr(corpus, "default_corpus", lambda *a, **k: types.SimpleNamespace(cards=fewer))
    v = codex.verify_artifact()
    assert v["body_drift_since_seal"] is True


# ---- overview ----

def test_overview_carries_the_spine_and_stats(built):
    codex.build_all()
    ov = codex.overview()
    assert ov["authority_spine"][0] == "Words in Red"
    assert ov["scripture"]["cross_references"] == 3
    assert ov["themes"]["themes"] >= 1
    assert "faces" in ov and any("/codex/" in f for f in ov["faces"])


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
