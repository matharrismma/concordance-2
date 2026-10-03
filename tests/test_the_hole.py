"""THE HOLE (Matt, 2026-10-02): "It was before Christ. You have to see this as showing what is missing.
They all have the hole that Christ filled … I see them as the nations at the tower of babel having parts
of the story, but Christ fulfilled them, and he became the way. Everything after that is in opposition."

Pinned here: the shelf's lead card says it in those three clauses; the Tao signpost reads as parts-with-
a-hole, not equivalence; the signposts are CARDS the doors can reach (one source); the Chinese classics
meet under every spelling; a found shadow is walked as a shadow (the fulfillment verse it names)."""
import json
import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-hole-"))

from concordance import corpus, path  # noqa: E402

_REPO = Path(__file__).resolve().parent.parent


def _records(p: Path):
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def test_the_lead_card_carries_the_three_clauses():
    cards = {c["id"]: c for c in _records(_REPO / "data" / "religions_cards.jsonl")}
    lead = cards["card_foreshadow_praeparatio_evangelica"]["body"]
    for words in ("Babel", "Genesis 11", "Hebrews 1:1", "PARTS of the story", "HOLE", "John 14:6",
                  "Acts 2:6-11", "AFTER CHRIST", "1 John 4:2-3", "never aimed at persons"):
        assert words in lead, words
    frame = cards["card_foreshadow_praeparatio_evangelica"]["extra"]["frame"]
    assert set(frame) == {"before_christ", "christ", "after_christ"}
    assert "Babel" in cards["card_spine_foreshadows"]["body"]          # the shelf's first sentence names it
    assert "the hole Christ filled" in cards["card_spine_foreshadows"]["body"]


def test_the_tao_signpost_is_parts_with_a_hole_not_equivalence():
    sp_file = _REPO / "data" / "prophecy" / "signposts.jsonl"
    if not sp_file.exists():
        pytest.skip("data/prophecy is data-only (gitignored): the signposts live on the box, not in git")
    recs = {r["id"]: r for r in _records(sp_file)}
    sp = recs["signpost_tao_logos_derek_the_way"]
    assert " = " not in sp["title"] and "hole" in sp["title"] and "John 14:6" in sp["title"]
    assert "太初有道" in sp["verification"] and "道成了肉身" in sp["verification"]   # verified 2026-10-02
    assert "THE HOLE" in sp["verification"] and "a Person" in sp["verification"]
    assert "Hebrews 1:1-2" in sp["wisdom"] and "Acts 2:6-11" in sp["wisdom"]
    assert len(recs) == 30


def test_signposts_load_as_cards_from_the_one_file(monkeypatch):
    tmp = Path(tempfile.mkdtemp(prefix="nh-sp-"))
    (tmp / "cards.jsonl").write_text(json.dumps({
        "id": "card_x", "kind": "reference", "title": "x", "body": "x", "shelf": "reference",
        "visibility": "public", "lifecycle_stage": "public", "surface": "secular"}) + "\n", encoding="utf-8")
    (tmp / "prophecy").mkdir()
    (tmp / "prophecy" / "signposts.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [
        {"id": "signpost_tao_logos_derek_the_way", "title": "The nations reached for the Way — fulfilled (John 14:6)",
         "verdict": "CONCORDANT", "verification": "太初有道 — In the beginning was the Tao.",
         "wisdom": "The hole has a Person.", "triggers": {"keywords": ["Tao Logos", "the Way"]},
         "domains": ["scripture"]},
        {"id": "signpost_list_triggers", "title": "triggers as a list", "verdict": "MIXED",
         "verification": "v", "wisdom": "w", "triggers": ["a", "b"]},
        {"title": "no id — skipped"},
    ]) + "\n", encoding="utf-8")
    monkeypatch.setenv("CONCORDANCE_PROPHECY_DIR", str(tmp / "prophecy"))
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp))
    # other test modules set these at import for the whole process (CI runs one process): a cards
    # path that is not this keeping, or a freeze list — neither may reach this test
    monkeypatch.delenv("CONCORDANCE_CARDS_JSONL", raising=False)
    monkeypatch.delenv("CONCORDANCE_FREEZE_SHELVES", raising=False)
    out = corpus.load_cards()                 # the default keeping: the extras (and the signposts) load only there
    sp = out["signpost_tao_logos_derek_the_way"]
    assert sp["shelf"] == "signposts" and corpus.is_public(sp) and sp["generated"] is False
    assert sp["body"] == "太初有道 — In the beginning was the Tao. The hole has a Person."   # its own two paragraphs
    assert sp["extra"]["verdict"] == "CONCORDANT" and "tao logos" in sp["bands"]
    assert sp["connections"][0]["to_card_id"] == "card_spine_foreshadows"
    assert "signpost_list_triggers" in out and len(out) == 3                   # a list of triggers does not crash


def test_the_chinese_classics_meet_under_every_spelling():
    alts = corpus._alias_queries("what does the tao te ching say about the way")
    assert "what does the tao teh king say about the way" in alts
    assert "what does the daodejing say about the way" in alts
    assert corpus._alias_queries("How do I purify water") == []
    assert "laozi" in " ".join(corpus._alias_queries("Lao Tzu on water"))
    assert corpus._alias_queries("the Tao Teh King") and "tao te ching" in corpus._alias_queries("the Tao Teh King")[0].lower()


def test_a_found_shadow_is_walked_as_a_shadow(monkeypatch):
    monkeypatch.setattr(path, "_resolve", lambda ref: {"ref": ref, "text": "(the verse's own words)"})
    lead = {"id": "card_foreshadow_chinese", "title": "Chinese traditions — Confucianism & Daoism",
            "shelf": "foreshadows", "anchor_ref": "John 14:6"}
    p = path.compose("is there a connection between taoism and christianity", kind="found",
                     subject="taoism and christianity", lead=lead)
    assert p["type"] == "shadow" and "hole Christ filled" in p["framing"]
    assert p["anchor"]["ref"] == "John 14:6"
    assert "Chinese traditions" in p["step"] and "John 14:6" in p["step"] and "the steps" not in p["step"]
    # a practical lead stays practical — the shadow register is only for the shadow shelves
    q = path.compose("how do I purify water", kind="found",
                     lead={"title": "Making water safe to drink", "shelf": "survival"})
    assert q["type"] == "resource"


def test_the_fulfillment_ref_is_the_cards_own():
    from concordance import ask
    assert ask._fulfillment_ref("Tao = Logos — fulfilled in John 14:6", "") == "John 14:6"
    body = ("Chinese traditions (c. 6th c. BC). The seed it kept: the Way. Where the shadow fell short: a "
            "principle. The fulfillment (named): 'I am the Way' (John 14:6) — the Dao has a face. (Acts 17:23; "
            "Colossians 2:17.)")
    assert ask._fulfillment_ref("Chinese traditions — Confucianism & Daoism", body) == "John 14:6"
    assert ask._fulfillment_ref("no refs anywhere", "none here either") == ""
    lead = ask._lead_card({"id": "c", "title": "Chinese traditions", "shelf": "foreshadows", "body": body})
    assert lead["anchor_ref"] == "John 14:6"
    assert "anchor_ref" not in ask._lead_card({"id": "c", "title": "x", "shelf": "survival", "body": body})


def test_a_lifted_discernment_chart_leads_with_its_own_words():
    """_pair_discernment lifted the chart as a BRIEF (no body): the lead's excerpt was empty, the result's
    snippet empty, and a shadow lead carried no fulfillment verse (measured live 2026-10-02)."""
    from types import SimpleNamespace
    from concordance import ask
    chart = {"id": "card_foreshadow_chinese", "title": "Chinese traditions — Confucianism & Daoism",
             "shelf": "foreshadows", "lifecycle_stage": "public", "visibility": "public", "surface": "secular",
             "body": "The seed it kept: the Way. The fulfillment: 'I am the Way' (John 14:6).",
             "extra": {"discerns_terms": ["taoism", "daoism", "tao te ching"]}}
    cp = SimpleNamespace(cards={chart["id"]: chart})
    hits = ask._pair_discernment([{"id": "card_other", "title": "x", "shelf": "reference", "body": "y"}],
                                 "is there a connection between taoism and christianity", cp=cp)
    assert hits[0]["id"] == "card_foreshadow_chinese" and hits[0].get("body"), hits[0]
    lead = ask._lead_card(hits[0])
    assert lead["excerpt"].startswith("The seed it kept") and lead["anchor_ref"] == "John 14:6"
