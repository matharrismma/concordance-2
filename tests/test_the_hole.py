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


def test_the_discernment_is_never_gated_by_shelf(monkeypatch):
    """With the alignment gate on, a signpost whose title names Tao was tiered `reference` (×0.6) by the
    chart that discerns Taoism and fell out of the first screen; the discernment is never gated — by
    shelf, not only by chart id. A primary source of the tradition is still damped (the gate still works)."""
    from concordance import alignment
    monkeypatch.setenv("CONCORDANCE_ALIGNMENT", "1")
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(_REPO / "data"))
    alignment._CACHE["key"] = None                                   # re-read the atlas under this data dir
    sp = corpus._signpost_card({"id": "signpost_tao_logos_derek_the_way",
                                "title": "The nations reached for the Way — Tao, Logos, Derek — each with the hole; Christ filled it (John 14:6)",
                                "verification": "v", "wisdom": "w", "triggers": {"keywords": ["Lao Tzu", "Tao Teh King"]}})
    assert alignment.verdict(sp, set()) == (True, 1.0)
    fore = {"id": "card_foreshadow_x", "shelf": "foreshadows", "title": "A Taoism chart with no terms", "bands": ["lao tzu"]}
    assert alignment.verdict(fore, set()) == (True, 1.0)
    legge = {"id": "card_src_book_216", "shelf": "gutenberg", "title": "The Tao Teh King — Laozi", "bands": ["lao tzu"]}
    keep, damp = alignment.verdict(legge, set())
    assert keep and damp == alignment._REF_DAMP                       # a primary source: referenceable, damped
    alignment._CACHE["key"] = None


def test_every_foreshadow_card_carries_the_frame():
    """Matt, 2026-10-03: "apply the same frame to the other foreshadow cards." Every pre-Christ card names
    its three movements in the frame's words (a part of the story · THE HOLE · Christ filled it) and keeps
    the fulfillment verse findable; every after-Christ card carries the third clause (opposition where it
    denies the Son, tested in love, never persons)."""
    from concordance import ask
    cards = _records(_REPO / "data" / "religions_cards.jsonl")
    fore = [c for c in cards if (c.get("box") == "foreshadow")]
    after = [c for c in cards if c["id"].endswith("_under_the_test") or c["id"].endswith("post_christ_pattern")]
    assert len(fore) == 10 and len(after) == 10, (len(fore), len(after))
    for c in fore:
        b = c["body"]
        for words in ("a part of the story carried by the nations scattered at Babel", "The part it kept:",
                      "THE HOLE — what was missing:", "Christ filled it — the fulfillment", "never a parallel"):
            assert words in b, (c["id"], words)
        assert set(c["extra"]["frame"]) == {"part", "hole", "filled"}
        assert ask._fulfillment_ref(c["title"], b), c["id"]              # the verse it names is still found
    for c in after:
        assert "AFTER CHRIST: it arose after him" in c["body"] and "stands in opposition (1 John 4:2-3)" in c["body"], c["id"]
        assert "never of persons" in c["body"] and c["extra"]["frame"]["after_christ"].startswith("opposition")


def test_a_signpost_in_the_results_never_trips_another_chart():
    """"what did the stoics believe": the Tao signpost (bands: "lao tzu") sat in the results, tripped the
    Chinese chart as if it were a Taoist source, and the Chinese card led over the Stoicism chart the
    question named. Discernment never trips discernment."""
    from types import SimpleNamespace
    from concordance import ask
    pub = {"lifecycle_stage": "public", "visibility": "public", "surface": "secular"}
    stoic = {"id": "card_foreshadow_stoicism", "title": "Stoicism", "shelf": "foreshadows", "body": "s",
             "extra": {"discerns_terms": ["stoicism", "the stoics"]}, **pub}
    chinese = {"id": "card_foreshadow_chinese", "title": "Chinese traditions", "shelf": "foreshadows", "body": "c",
               "extra": {"discerns_terms": ["taoism", "lao tzu"]}, **pub}
    cp = SimpleNamespace(cards={stoic["id"]: stoic, chinese["id"]: chinese})
    signpost = {"id": "signpost_tao_logos_derek_the_way", "title": "The nations reached for the Way",
                "shelf": "signposts", "bands": ["signpost", "lao tzu"], "body": "x"}
    hits = ask._pair_discernment([signpost], "what did the stoics believe", cp=cp)
    assert hits[0]["id"] == "card_foreshadow_stoicism" and all(h["id"] != "card_foreshadow_chinese" for h in hits)
    # a real primary source still trips its chart
    legge = {"id": "card_src_book_216", "title": "The Tao Teh King — Laozi", "shelf": "gutenberg", "bands": ["lao tzu"], "body": "y"}
    hits = ask._pair_discernment([legge], "what does this book say", cp=cp)
    assert hits[0]["id"] == "card_foreshadow_chinese"


def test_a_chart_names_its_subject_by_its_terms_and_bands():
    """"what did the magi of zoroaster expect" routed to the web fallback (kind "web", no results) because the
    gap guard reads only the TITLE ("Zoroastrianism") and the question says "zoroaster"/"magi". A chart names
    its subject by the terms it discerns and the bands it carries; other shelves keep the strict guard."""
    from concordance import ask
    zoro = {"id": "card_foreshadow_zoroastrianism", "title": "Zoroastrianism", "shelf": "foreshadows",
            "bands": ["foreshadow", "zoroaster", "magi", "saoshyant"],
            "extra": {"discerns_terms": ["zoroastrianism", "zoroaster", "ahura mazda"]}}
    assert ask._title_names_subject("what did the magi of zoroaster expect", zoro)
    assert ask._title_names_subject("who was zoroaster", zoro)
    assert not ask._title_names_subject("how do I purify water", zoro)
    other = dict(zoro, id="card_src_book_x", shelf="gutenberg")
    assert not ask._title_names_subject("what did the magi of zoroaster expect", other)   # unchanged elsewhere
