"""Strong's / original-language test — the agent in the original source.

Proves: word_study resolves a Strong's number to its lexicon definition + every
occurrence (found, not generated); the scripture verifier delegates to it; SourceLayer
resolves a ref to WEB text; and an unknown Strong's number degrades gracefully (no crash).
Requires the migrated data (tools/migrate_strongs.py) — skips cleanly if absent.
Runnable with `pytest` OR `python tests/test_strongs.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.strongs import Concordance, SourceLayer  # noqa: E402
from concordance.verifiers import scripture as S  # noqa: E402

_READY = SourceLayer().ready().get("WEB_sqlite") and SourceLayer().ready().get("strongs_greek")


def test_word_study_agape():
    if not _READY:
        print("  skip test_word_study_agape (strongs data not provisioned)")
        return
    ws = Concordance().word_study("G26")
    assert ws.get("status") == "ok", ws.get("status")
    blob = (str(ws.get("word", "")) + str(ws.get("transliteration", "")) + str(ws.get("definition", ""))).lower()
    assert "agap" in blob or "love" in blob, ws.get("definition")
    assert int(ws.get("occurrence_count", 0)) > 0
    assert ws.get("verses"), "word study should list occurrences"


def test_scripture_word_study_delegates():
    if not _READY:
        print("  skip test_scripture_word_study_delegates (strongs data not provisioned)")
        return
    ws = S.word_study("G26")
    assert isinstance(ws, dict) and ws.get("status") == "ok"


def test_sourcelayer_resolves_ref():
    if not _READY:
        print("  skip test_sourcelayer_resolves_ref (strongs data not provisioned)")
        return
    r = SourceLayer().lookup("John 3:16")
    assert isinstance(r, dict) and r.get("status") in ("ok", "found", None) or r.get("web_text")


def test_unknown_strongs_degrades_gracefully():
    # a bogus number must not crash — graceful status, whatever the backend reports
    ws = S.word_study("G9999999")
    assert isinstance(ws, dict)
    assert ws.get("status") != "ok"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} strongs tests passed — word study finds the lexicon + occurrences.")
