"""ISBE 1915 (D5) — the acquisition is whole, nested, attributed, and reaches the reader.

Matt's decision D5 (2026-07-28): acquisitions in order — ISBE first, then Gill, then Clarke.

Pinned here:
  * the minted cards load, every entry is a stub NESTED under the ISBE spine (zero orphans),
    public, attributed to the PD source — found, never generated;
  * the reader db answers a known headword with the full article (thousands of chars, not a
    caption), and answers junk/missing with None — never an exception;
  * the CARD PAGE renders the FULL article (the sixth guarantee-stops-short lesson applied
    in advance: server-side truth is not done until the person can see it);
  * without the acquisition db the stub still renders — a shorter answer, never a broken page.

Skips honestly (pytest.skip, never a silent pass) if the acquisition artifacts are absent —
they are data, not tracked in git.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

CARDS = ROOT / "data" / "isbe_cards.jsonl"
DB = ROOT / "data" / "acquisitions" / "isbe.db"


def _need(p: Path):
    if not p.exists():
        pytest.skip(f"acquisition artifact absent on this machine: {p.name}")


def test_minted_cards_are_whole_nested_and_attributed():
    _need(CARDS)
    from concordance.corpus import is_public
    spine = None
    n = 0
    with open(CARDS, encoding="utf-8") as f:
        for ln in f:
            c = json.loads(ln)
            if c["id"] == "card_spine_isbe":
                spine = c
                continue
            n += 1
            assert c.get("connections") and any(
                x.get("to_card_id") == "card_spine_isbe" and x.get("relationship") == "member_of"
                for x in c["connections"]), f"{c['id']}: every entry hangs on the spine"
            assert is_public(c), f"{c['id']}: the encyclopedia is for everyone"
            assert c.get("generated") is False and "Public Domain" in c["source"]["label"], \
                f"{c['id']}: found and attributed, never generated"
            assert (c.get("extra") or {}).get("isbe_headword"), \
                f"{c['id']}: the key back to the full article"
    assert spine is not None, "the spine card exists"
    assert any(x.get("relationship") == "part_of" for x in spine["connections"]), \
        "the spine roots in the Floor — no orphan sections"
    assert n > 9000, f"the whole encyclopedia came across (got {n})"


def test_reader_answers_full_articles_and_never_raises():
    _need(DB)
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = str(ROOT / "data")
    try:
        import concordance.isbe as isbe
        isbe._CONN = None  # fresh connection against this data dir
        a = isbe.get("AARON")
        assert a and len(a["text"]) > 2000, "a real article, not a caption"
        assert "Public Domain" in a["source"]
        assert isbe.get("NO SUCH HEADWORD XYZZY") is None
        assert isbe.get("") is None
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior
        import concordance.isbe as isbe
        isbe._CONN = None


def test_the_card_page_carries_the_whole_article():
    _need(DB)
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = str(ROOT / "data")
    try:
        import concordance.isbe as isbe
        isbe._CONN = None
        from concordance.web.api import render_card_html
        stub_card = {
            "id": "card_isbe_aaron", "title": "ISBE: Aaron",
            "body": "stub…", "shelf": "encyclopedia", "lifecycle_stage": "public",
            "source": {"label": isbe.SOURCE},
            "extra": {"isbe_headword": "AARON"},
        }
        status, html = render_card_html("card_isbe_aaron", stub_card)
        assert status == 200
        assert len(html) > 3000, "the FULL article reached the page, not the stub"
        # and a missing db still renders the stub — never a broken page
        os.environ["CONCORDANCE_DATA_DIR"] = str(ROOT / "data" / "no_such_dir")
        isbe._CONN = None
        status2, html2 = render_card_html("card_isbe_aaron", stub_card)
        assert status2 == 200 and "stub" in html2
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior
        import concordance.isbe as isbe
        isbe._CONN = None


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
