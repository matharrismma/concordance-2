"""Arc 2 (the Bible) B1 — passage reading + the pronunciation fix in the LIVE word-study path.

Proves read_passage (single verse / range / whole chapter / errors), the /passage endpoint
(witness-gated), and that the live Concordance.word_study now carries a pronunciation (it used to
return none — the tapped-word reader was mute). Hermetic: uses an in-memory Bible fixture and
monkeypatched lexicon, so it needs no provisioned data. Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-bible-")
os.environ["CONCORDANCE_STRONGS_DIR"] = tempfile.mkdtemp(prefix="nh-strongs-")  # isolate: no real DB

from concordance.verifiers import scripture  # noqa: E402
from concordance.strongs import Concordance  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

WIT = EngineConfig("witness")
SEC = EngineConfig("secular")

FIX = [
    {"book": "John", "chapter": 3, "verse": 16, "text": "For God so loved the world..."},
    {"book": "John", "chapter": 3, "verse": 17, "text": "For God didn't send his Son..."},
    {"book": "John", "chapter": 3, "verse": 18, "text": "He who believes in him is not judged..."},
]


def test_passage_single_verse():
    r = scripture.Bible(FIX).passage("John 3:16")
    assert r["status"] == "ok" and r["count"] == 1 and r["verses"][0]["verse"] == 16


def test_passage_range():
    r = scripture.Bible(FIX).passage("John 3:16-18")
    assert r["status"] == "ok" and [v["verse"] for v in r["verses"]] == [16, 17, 18]
    assert r["ref"] == "John 3:16-18"


def test_passage_whole_chapter():
    r = scripture.Bible(FIX).passage("John 3")
    assert r["status"] == "ok" and r["count"] == 3 and r["ref"] == "John 3"


def test_passage_reversed_range_is_normalized():
    r = scripture.Bible(FIX).passage("John 3:18-16")
    assert r["status"] == "ok" and [v["verse"] for v in r["verses"]] == [16, 17, 18]


def test_passage_unknown_book_and_bad_parse_and_missing_source():
    b = scripture.Bible(FIX)
    assert b.passage("Zzz 1:1")["status"] == "not_found"
    assert b.passage("nonsense")["status"] == "not_found"
    assert b.passage("John 9:9")["status"] == "not_found"       # ref valid, verse absent
    assert scripture.Bible([]).passage("John 3:16")["status"] == "source_missing"


def test_word_study_now_carries_pronunciation():
    c = Concordance()
    # Greek entry: no native pron field -> the transliteration IS the phonetic guide.
    c._lex_entry = lambda s: {"translit": "agape", "lemma": "agape", "strongs_def": "love"}
    c.strongs_verses = lambda s, limit=200: {"status": "concordance_not_built"}
    r = c.word_study("G26")
    assert "pronunciation" in r and r["pronunciation"] == "agape"
    # Hebrew-style entry with a native pron -> use it.
    c._lex_entry = lambda s: {"pron": "khes'-ed", "translit": "checed"}
    assert c.word_study("H2617")["pronunciation"] == "khes'-ed"
    # Unknown word: field still present, empty (never silently absent).
    c._lex_entry = lambda s: None
    assert c.word_study("G99999").get("pronunciation") == ""


def test_passage_endpoint_witness_gated():
    st, p = dispatch("GET", "/passage", {"ref": "John 3:16"}, None, WIT)
    assert st == 200 and "status" in p
    assert dispatch("GET", "/passage", {}, None, WIT)[0] == 400          # ref required
    assert dispatch("GET", "/passage", {"ref": "John 3:16"}, None, SEC)[0] == 404  # witness-only


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} bible B1 tests passed — passages read; the tapped word can be pronounced.")
