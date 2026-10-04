"""Arc 2 (the Bible) B4 — the canon layer + per-verse original words (backend of bible.html).

Proves canon.overview() keeps disputed books OFF the 66, the /canon endpoint, verse_words +
original_words, and the /original endpoint (witness-gated). The page itself (site/bible.html) is
verified live. Hermetic where DB is needed (injected fixture). Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-canon-")

from concordance import canon  # noqa: E402
from concordance.strongs import Concordance  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

WIT = EngineConfig("witness")
SEC = EngineConfig("secular")


def test_canon_overview_keeps_disputed_separate():
    o = canon.overview()
    assert o["undisputed_66"]["count"] == 66
    keys = {t["key"] for t in o["traditions"]}
    assert {"catholic", "eastern_orthodox", "ethiopian_orthodox"} <= keys
    assert "never" in o["note"].lower()  # states disputed are never merged


def test_canon_status_core_vs_disputed():
    assert canon.canon_status("John")["in_undisputed_66"] is True
    tob = canon.canon_status("Tobit")
    assert tob["in_undisputed_66"] is False and "catholic" in tob["held_by"]
    assert canon.canon_status("Znope")["held_by"] == []  # unknown → held by none


def test_canon_endpoint_witness_gated():
    st, p = dispatch("GET", "/canon", {}, None, WIT)
    assert st == 200 and p["undisputed_66"]["count"] == 66
    st2, p2 = dispatch("GET", "/canon", {"book": "Tobit"}, None, WIT)
    assert st2 == 200 and p2["in_undisputed_66"] is False
    # SEEING, not understanding. Matt, 2026-07-31: "seeing them is fine — understanding
    # the deeper meaning comes after the gate" and "we don't need to refuse use, we refuse
    # abuse". The text and its reference apparatus answer on both surfaces now; only
    # exposition waits (api.AFTER_THE_GATE).
    assert dispatch("GET", "/canon", {}, None, SEC)[0] == 200


def _conc_with_fixture() -> Concordance:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE concordance (b INTEGER,c INTEGER,v INTEGER,word_pos INTEGER,word TEXT,strongs TEXT)")
    conn.executemany("INSERT INTO concordance VALUES (?,?,?,?,?,?)", [
        (43, 3, 16, 1, "ēgapēsen", "G25"), (43, 3, 16, 2, "theos", "G2316"), (43, 3, 16, 3, "kosmon", "G2889"),
    ])
    conn.commit()
    c = Concordance()
    c._conc = conn
    return c


def test_verse_words_returns_tagged_originals():
    words = _conc_with_fixture().verse_words(43, 3, 16)
    assert [w["strongs"] for w in words] == ["G25", "G2316", "G2889"]
    assert words[0]["word"] == "ēgapēsen" and words[0]["word_pos"] == 1


def test_original_endpoint_witness_gated():
    # SEEING, not understanding. Matt, 2026-07-31: "seeing them is fine — understanding
    # the deeper meaning comes after the gate" and "we don't need to refuse use, we refuse
    # abuse". The text and its reference apparatus answer on both surfaces now; only
    # exposition waits (api.AFTER_THE_GATE).
    assert dispatch("GET", "/original", {"ref": "John 3:16"}, None, SEC)[0] == 200
    assert dispatch("GET", "/original", {}, None, WIT)[0] == 400
    st, p = dispatch("GET", "/original", {"ref": "John 3:16"}, None, WIT)
    assert st == 200 and "status" in p and "words" in p



# ---------------------------------------------------------------------------------------------
# COVERAGE (2026-10-04) — the tagged words are NOT the whole verse, and the reader is told so.
# concordance.db tags 43.5% of the Greek words (John 1:1: 14 of 17; Revelation 7:4: 5 of 16) and
# 98.1% of the Hebrew; a Greek word_pos is cumulative across the book, a Hebrew one per-verse.
# original_words places the tagged words inside the verse's full word list (from the held verse
# card) and reports what is untagged — with the words, so the verse is shown whole.
# ---------------------------------------------------------------------------------------------
from concordance.verifiers import scripture as S  # noqa: E402

JOHN_1_1 = "Ἐν ἀρχῇ ἦν ὁ λόγος καὶ ὁ λόγος ἦν πρὸς τὸν θεόν καὶ θεὸς ἦν ὁ λόγος".split()
JOHN_1_1_TAGGED = [  # exactly what concordance.db holds for John 1:1 (positions 1, 10, 11 missing)
    (0, "Ἐν", "G1722"), (2, "ἦν", "G2258"), (3, "ὁ", "G3588"), (4, "λόγος,", "G3056"), (5, "καὶ", "G2532"),
    (6, "ὁ", "G3588"), (7, "λόγος", "G3056"), (8, "ἦν", "G2258"), (9, "πρὸς", "G4314"), (12, "καὶ", "G2532"),
    (13, "θεὸς", "G2316"), (14, "ἦν", "G2258"), (15, "ὁ", "G3588"), (16, "λόγος.", "G3056")]
REV_7_4 = ("Καὶ ἤκουσα τὸν ἀριθμὸν τῶν ἐσφραγισμένων ἑκατὸν τεσσεράκοντα τέσσαρες χιλιάδες "
           "ἐσφραγισμένοι ἐκ πάσης φυλῆς υἱῶν Ἰσραήλ").split()
REV_7_4_TAGGED = [  # book-cumulative word_pos, sigla and punctuation on the words — as held
    (2747, "Καὶ", "G2532"), (2753, "⸀ἑκατὸν", "G1540"), (2755, "τέσσαρες", "G5064"),
    (2758, "ἐκ", "G1537"), (2762, "Ἰσραήλ·", "G2474")]
GEN_1_1 = "בְּ/רֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַ/שָּׁמַ֖יִם וְ/אֵ֥ת הָ/אָֽרֶץ".split()


def _rows(spec):
    return [{"word_pos": p, "word": w, "strongs": s} for p, w, s in spec]


def test_coverage_places_greek_words_despite_cumulative_positions_and_punctuation():
    words = _rows(JOHN_1_1_TAGGED)
    cov = S.tag_coverage(words, JOHN_1_1, hebrew=False, card="card_src_greek_nt_john_1_1")
    assert cov["aligned"] is True and cov["complete"] is False
    assert (cov["tagged"], cov["total"]) == (14, 17)
    assert cov["untagged_positions"] == [1, 10, 11]
    assert cov["untagged_words"] == ["ἀρχῇ", "τὸν", "θεόν"]          # the missing words, shown
    assert [w["verse_pos"] for w in words] == [0, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16]
    assert cov["card"] == "card_src_greek_nt_john_1_1"               # the trail names its source


def test_coverage_revelation_7_4_five_of_sixteen():
    words = _rows(REV_7_4_TAGGED)
    cov = S.tag_coverage(words, REV_7_4, hebrew=False)
    assert (cov["tagged"], cov["total"], cov["complete"]) == (5, 16, False)
    assert [w["verse_pos"] for w in words] == [0, 6, 8, 11, 15]     # 2747.. placed within the verse
    assert len(cov["untagged_positions"]) == 11 and "τεσσεράκοντα" in cov["untagged_words"]


def test_coverage_hebrew_is_positional_and_can_be_complete():
    full = _rows([(i, w, f"H{i}") for i, w in enumerate(GEN_1_1)])
    cov = S.tag_coverage(full, GEN_1_1, hebrew=True)
    assert cov["complete"] is True and cov["untagged_positions"] == [] and cov["total"] == 7
    partial = _rows([(i, w, f"H{i}") for i, w in enumerate(GEN_1_1) if i != 3])
    cov2 = S.tag_coverage(partial, GEN_1_1, hebrew=True)
    assert cov2["untagged_positions"] == [3] and cov2["untagged_words"] == ["אֵ֥ת"]
    assert [w["verse_pos"] for w in partial] == [0, 1, 2, 4, 5, 6]  # word_pos IS the verse position


def test_coverage_never_claims_what_it_cannot_show():
    words = _rows(JOHN_1_1_TAGGED)
    unknown = S.tag_coverage(words, None, hebrew=False)             # the verse is not held whole
    assert unknown["total"] is None and unknown["complete"] is None and unknown["aligned"] is False
    assert "not necessarily the whole verse" in S._coverage_note(unknown)
    bogus_rows = _rows([(0, "ζζζ", "G1")])
    bogus = S.tag_coverage(bogus_rows, JOHN_1_1, hebrew=False)       # cannot be placed
    assert bogus["aligned"] is False and bogus["complete"] is None and bogus["untagged_positions"] is None
    assert "no positions are claimed" in S._coverage_note(bogus)
    assert "verse_pos" not in bogus_rows[0]


def _card(text, cid="card_src_greek_nt_john_1_1"):
    return {"id": cid, "visibility": "public", "lifecycle_stage": "public", "extra": {"text": text}}


def test_original_words_reports_coverage_from_the_held_verse_card(monkeypatch):
    from concordance.strongs.concordance import Concordance as C
    from concordance import corpus
    monkeypatch.setattr(C, "verse_words", lambda self, b, c, v: _rows(JOHN_1_1_TAGGED))
    seen = {}
    def fake_get(cid):
        seen["cid"] = cid
        return _card(" ".join(JOHN_1_1))
    monkeypatch.setattr(corpus, "get_card", fake_get)
    p = S.original_words("John 1:1")
    assert seen["cid"] == "card_src_greek_nt_john_1_1"              # the verse card on the greek_nt shelf
    assert p["status"] == "ok" and p["count"] == 14                 # the pinned shape still holds
    assert p["coverage"]["total"] == 17 and p["coverage"]["untagged_words"] == ["ἀρχῇ", "τὸν", "θεόν"]
    assert "14 of 17" in p["note"] and "never dropped" in p["note"]
    assert p["words"][1]["verse_pos"] == 2


def test_original_words_with_no_tagged_words_still_shows_the_verse(monkeypatch):
    # Romans 1:29 has NO row in concordance.db; the verse is held on its card — show it, untagged.
    from concordance.strongs.concordance import Concordance as C
    from concordance import corpus
    monkeypatch.setattr(C, "verse_words", lambda self, b, c, v: [])
    monkeypatch.setattr(corpus, "get_card", lambda cid: _card("πεπληρωμένους πάσῃ ἀδικίᾳ", cid))
    p = S.original_words("Romans 1:29")
    assert p["status"] == "no_words" and p["words"] == []
    assert p["coverage"]["tagged"] == 0 and p["coverage"]["total"] == 3
    assert p["coverage"]["untagged_words"] == ["πεπληρωμένους", "πάσῃ", "ἀδικίᾳ"]
    assert p["coverage"]["card"] == "card_src_greek_nt_romans_1_29"


def test_original_words_without_a_card_says_the_count_is_unknown(monkeypatch):
    from concordance.strongs.concordance import Concordance as C
    from concordance import corpus
    monkeypatch.setattr(C, "verse_words", lambda self, b, c, v: _rows(JOHN_1_1_TAGGED))
    monkeypatch.setattr(corpus, "get_card", lambda cid: None)
    p = S.original_words("John 1:1")
    assert p["status"] == "ok" and p["coverage"]["total"] is None and p["coverage"]["complete"] is None
    assert "not necessarily the whole verse" in p["note"]


def test_verse_card_ids_follow_the_carding_slug():
    assert S._verse_card_id(43, 1, 1) == "card_src_greek_nt_john_1_1"
    assert S._verse_card_id(46, 13, 7) == "card_src_greek_nt_1_corinthians_13_7"
    assert S._verse_card_id(22, 1, 1) == "card_src_hebrew_ot_song_of_solomon_1_1"
    assert S._verse_card_id(99, 1, 1) is None


def test_original_endpoint_always_carries_coverage():
    st, p = dispatch("GET", "/original", {"ref": "John 3:16"}, None, WIT)
    assert st == 200 and "coverage" in p and "note" in p
    assert set(p["coverage"]) >= {"tagged", "total", "untagged_positions", "untagged_words", "complete", "aligned"}


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} canon/original tests passed — the 66 stays the 66; the original word is tappable; the gap is shown.")
