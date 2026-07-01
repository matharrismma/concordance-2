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
    assert dispatch("GET", "/canon", {}, None, SEC)[0] == 404


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
    assert dispatch("GET", "/original", {"ref": "John 3:16"}, None, SEC)[0] == 404
    assert dispatch("GET", "/original", {}, None, WIT)[0] == 400
    st, p = dispatch("GET", "/original", {"ref": "John 3:16"}, None, WIT)
    assert st == 200 and "status" in p and "words" in p


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} canon/original B4 tests passed — the 66 stays the 66; the original word is tappable.")
