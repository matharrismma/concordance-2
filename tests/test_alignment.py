"""ALIGNMENT — gate the keeping by agreement. Pins: OFF by default (keep=True, damp=1.0 for everything);
occult (sectioned) is explicit-only (withheld unless the query names it); other religions/philosophy
(reference) are down-weighted unless sought; aligned material and the charts themselves are untouched."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import alignment  # noqa: E402


@pytest.fixture()
def atlas(monkeypatch, tmp_path):
    # a minimal atlas: one sectioned (occult) chart and one reference (other-religion) chart
    rows = [
        {"id": "card_x_occult", "extra": {"alignment": "sectioned",
                                          "discerns_terms": ["astral projection", "seance"]}},
        {"id": "card_x_islam", "extra": {"alignment": "reference",
                                         "discerns_terms": ["islam", "the quran"]}},
    ]
    (tmp_path / "religions_cards.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    alignment._CACHE["key"] = None                      # drop any cached index
    yield
    alignment._CACHE["key"] = None


_OCCULT = {"id": "src_astral", "title": "The Astral Plane", "bands": ["astral projection"], "subject": "astral projection"}
_ISLAM = {"id": "src_quran", "title": "The Quran", "bands": ["islam"], "subject": "islam"}
_ALIGNED = {"id": "card_ps23", "title": "Psalm 23", "bands": ["shepherd"], "subject": "the good shepherd"}


def test_off_by_default_is_inert(monkeypatch, atlas):
    monkeypatch.delenv("CONCORDANCE_ALIGNMENT", raising=False)
    assert alignment.enabled() is False
    assert alignment.context("astral projection") == set()      # no work when off
    assert alignment.verdict(_OCCULT, set()) == (True, 1.0)      # nothing gated
    assert alignment.verdict(_ISLAM, set()) == (True, 1.0)


def test_occult_is_explicit_only(monkeypatch, atlas):
    monkeypatch.setenv("CONCORDANCE_ALIGNMENT", "1")
    ctx_general = alignment.context("what is the fear of the Lord")
    assert alignment.verdict(_OCCULT, ctx_general) == (False, 1.0)   # withheld — not named
    ctx_explicit = alignment.context("how do I do astral projection")
    assert "card_x_occult" in ctx_explicit
    assert alignment.verdict(_OCCULT, ctx_explicit) == (True, 1.0)   # surfaced only on the explicit call


def test_reference_is_downweighted_unless_sought(monkeypatch, atlas):
    monkeypatch.setenv("CONCORDANCE_ALIGNMENT", "1")
    keep, damp = alignment.verdict(_ISLAM, alignment.context("what is grace"))
    assert keep is True and damp == alignment._REF_DAMP             # referenceable, down-weighted
    keep2, damp2 = alignment.verdict(_ISLAM, alignment.context("what does islam teach"))
    assert keep2 is True and damp2 == 1.0                          # normal weight when the subject is sought


def test_aligned_and_charts_are_untouched(monkeypatch, atlas):
    monkeypatch.setenv("CONCORDANCE_ALIGNMENT", "1")
    assert alignment.verdict(_ALIGNED, set()) == (True, 1.0)       # aligned material unaffected
    chart = {"id": "card_x_occult", "title": "occult chart", "subject": "astral projection"}
    assert alignment.verdict(chart, set()) == (True, 1.0)          # a discernment chart is NEVER gated


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
