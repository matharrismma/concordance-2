"""Scripture verifier test (witness surface) — resolve + verify citations on the WEB.

Proves: a ref resolves to its WEB text (incl. common abbreviations); a bad ref or a
mismatched quotation is caught; the verifier is witness-surface-gated (absent on the
secular reach); and it degrades gracefully when the bible data isn't provisioned. Uses a
tiny fixture bible via CONCORDANCE_BIBLE_EN. Runnable with `pytest` OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.verifiers import run_for_domain  # noqa: E402
from concordance.verifiers import scripture as S  # noqa: E402

FIXTURE = [
    {"book": "John", "book_abbr": "JHN", "chapter": 3, "verse": 16,
     "text": "For God so loved the world, that he gave his one and only Son..."},
    {"book": "Genesis", "book_abbr": "GEN", "chapter": 1, "verse": 1,
     "text": "In the beginning, God created the heavens and the earth."},
]


def _setup(tmp: str) -> None:
    p = Path(tmp) / "bible_en.jsonl"
    p.write_text("\n".join(json.dumps(v) for v in FIXTURE), encoding="utf-8")
    os.environ["CONCORDANCE_BIBLE_EN"] = str(p)
    S._reset()


def test_resolve_ref_and_abbreviations():
    with tempfile.TemporaryDirectory() as t:
        _setup(t)
        assert S.resolve_ref("John 3:16")["status"] == "ok"
        assert "loved the world" in S.resolve_ref("John 3:16")["text"]
        assert S.resolve_ref("Jn 3:16")["status"] == "ok"      # common abbreviation
        assert S.resolve_ref("John 99:99")["status"] == "not_found"


def test_confirms_good_anchors_on_witness():
    with tempfile.TemporaryDirectory() as t:
        _setup(t)
        res = run_for_domain("scripture", {"scripture_anchors": ["John 3:16", "Genesis 1:1"]},
                             surface="witness")
        assert res and all(r.status == "CONFIRMED" for r in res), [(r.status, r.detail) for r in res]


def test_catches_bad_ref_and_text_mismatch():
    with tempfile.TemporaryDirectory() as t:
        _setup(t)
        bad = run_for_domain("scripture", {"scripture_anchors": ["John 99:99"]}, surface="witness")
        assert any(r.status == "MISMATCH" for r in bad)
        wrong = run_for_domain("scripture",
                               {"scripture_anchors": [{"ref": "Genesis 1:1", "text": "a totally wrong quotation"}]},
                               surface="witness")
        assert any(r.status == "MISMATCH" for r in wrong)
        good = run_for_domain("scripture",
                              {"scripture_anchors": [{"ref": "Genesis 1:1", "text": "In the beginning"}]},
                              surface="witness")
        assert all(r.status == "CONFIRMED" for r in good)


def test_witness_gated():
    with tempfile.TemporaryDirectory() as t:
        _setup(t)
        # the secular reach does NOT surface the scripture verifier
        assert run_for_domain("scripture", {"scripture_anchors": ["John 3:16"]}, surface="secular") == []


def test_source_missing_degrades_gracefully():
    os.environ["CONCORDANCE_BIBLE_EN"] = str(Path(tempfile.gettempdir()) / "no_such_bible_xyzzy.jsonl")
    S._reset()
    res = run_for_domain("scripture", {"scripture_anchors": ["John 3:16"]}, surface="witness")
    assert res and res[0].status == "NOT_APPLICABLE"
    S._reset()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} scripture tests passed — citations resolve & verify on the WEB, witness-gated.")
