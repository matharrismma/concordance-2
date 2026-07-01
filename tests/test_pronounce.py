"""Arc 2 (the Bible) B2 — the synthesized pronunciation guide + word-study enrichment.

Proves pronounce.py (plain/respell/ipa/guide are deterministic and honestly labeled), the
/pronounce endpoint, and that scripture.word_study now carries a pronunciation_guide. Hermetic.
Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-pron-")

from concordance import pronounce  # noqa: E402
import concordance.strongs as strongs_pkg  # noqa: E402
from concordance.verifiers import scripture  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402


def test_plain_strips_diacritics():
    assert pronounce.plain("agápē") == "agape"
    assert pronounce.plain("chāsēd") == "chased"


def test_respell_syllabifies():
    assert pronounce.respell("agape") == "a-ga-pe"
    assert pronounce.respell("logos") == "lo-gos"


def test_ipa_is_deterministic_and_bracketed():
    a, b = pronounce.ipa("agápē"), pronounce.ipa("agápē")
    assert a == b and a.startswith("/") and a.endswith("/") and len(a) > 2


def test_guide_is_labeled_synthesized_never_a_native_speaker():
    g = pronounce.guide("agápē")
    assert g["synthesized"] is True and "not a native speaker" in g["note"]
    assert {"input", "plain", "respelling", "ipa", "speakable"} <= set(g)
    assert g["plain"] == "agape" and g["speakable"] == "agape"


def test_pronounce_endpoint_both_surfaces():
    st, p = dispatch("GET", "/pronounce", {"text": "agape"}, None, EngineConfig("secular"))
    assert st == 200 and p["respelling"] == "a-ga-pe" and p["synthesized"] is True
    assert dispatch("GET", "/pronounce", {"text": "logos"}, None, EngineConfig("witness"))[0] == 200
    assert dispatch("GET", "/pronounce", {}, None, EngineConfig("secular"))[0] == 400  # text required


def test_word_study_enriched_with_pronunciation_guide():
    class FakeConc:
        def word_study(self, n):
            return {"strongs": n, "transliteration": "agape", "status": "not_in_lexicon"}
    orig = strongs_pkg.Concordance
    strongs_pkg.Concordance = FakeConc
    try:
        r = scripture.word_study("G26")
        assert "pronunciation_guide" in r
        assert r["pronunciation_guide"]["plain"] == "agape"
        assert r["pronunciation_guide"]["synthesized"] is True
    finally:
        strongs_pkg.Concordance = orig


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} pronounce B2 tests passed — a synthesized guide, honestly labeled.")
