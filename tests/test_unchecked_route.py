"""The ask has to reach a person who has no JavaScript, no account, and no key — and the door it
points at has to open.

This test exists because `tests/test_reachability.py` declares `/unchecked/answer` agent-only, and
that declaration would be a lie if left unbacked. The route is genuinely reader-facing; it is
simply linked from a page the reachability checker cannot see, because that page is built at
request time by `api.render_card_html` rather than sitting in `site/*.html`. So the guarantee is
held HERE instead: render the page, and assert the href is really in the HTML.

That is the whole lesson of the adjoining-card graph, which existed, was correct server-side, and
reached a reader only through a canvas that stayed hidden until scripts ran — a dead end on ~39k
card views for every crawler and every no-JS reader. Correct and invisible is not done.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


def _card():
    from concordance import unchecked
    return unchecked.mark({
        "id": "card_span_abc123", "updated_at": 1.0, "title": "PREAMBLE",
        "kind": "reference",
        "body": "In order that we may preserve our God-given heritage, the faith once delivered "
                "to the saints, especially the doctrine and experience of sanctification.",
        "source": {"label": "Manual of the Church of the Nazarene (1923)",
                   "url": "https://archive.org/details/manualofhistoryd0000vari",
                   "authority_tier": "primary_pd"},
        "shelf": "sources",
        "extra": {"source_sha256": "14ca62004b575bb3", "span": [231643, 232342]},
    })


def test_the_ask_is_real_html_a_reader_without_scripts_can_use():
    from concordance.web import api
    status, html = api.render_card_html("card_span_abc123", _card())
    assert status == 200
    assert "No one has checked this card yet" in html
    assert "fairly represent" in html
    for verdict in ("holds", "wrong", "unsure"):
        href = f"/unchecked/answer?card=card_span_abc123&amp;verdict={verdict}"
        assert href in html or href.replace("&amp;", "&") in html, \
            f"the {verdict} answer is not a real link in the page"
    assert "two or three witnesses" in html, "the count is offered without its caveat"


def test_a_checked_card_page_carries_no_ask():
    from concordance.web import api
    plain = dict(_card())
    plain["extra"] = {"source_sha256": "x"}          # no mark
    # A DIFFERENT id AND version, because present.derive caches by (id, updated_at) and a shared
    # key would hand this card the previous test's block — the exact bug that test caught once
    # before, when two versionless cards served each other's presentation.
    plain["id"], plain["updated_at"] = "card_span_checked", 2.0
    _s, html = api.render_card_html("card_span_checked", plain)
    assert "No one has checked this card yet" not in html
    assert "/unchecked/answer" not in html


def test_the_door_the_link_points_at_actually_opens():
    """A link that 404s is worse than no link: it looks like an invitation and is a dead end."""
    from concordance.web import api
    from concordance.config import EngineConfig
    status, _payload = api.dispatch("GET", "/unchecked/answer",
                                    {"card": "card_span_abc123", "verdict": "holds"},
                                    None, EngineConfig("secular"))
    assert status == 200, f"the ask points at a door that answers {status}"

    from concordance import unchecked
    assert unchecked.state_of("card_span_abc123")["checked_by"] == 1


def test_the_door_refuses_a_nonsense_verdict():
    from concordance.web import api
    from concordance.config import EngineConfig
    status, _p = api.dispatch("GET", "/unchecked/answer",
                              {"card": "x", "verdict": "delete-this-card"},
                              None, EngineConfig("secular"))
    assert status == 400


def test_both_surfaces_report_the_same_live_count():
    """THE PAGE AND THE JSON MUST NOT DISAGREE ABOUT WHETHER ANYONE HAS LOOKED.

    Caught live on 2026-08-01: the HTML renderer had been corrected to read the answer log and the
    /card JSON had not, so a person could be told "checked by 2 readers" while an agent fetching
    the identical card was told nobody had ever looked at it. `present.derive` is pure and cached,
    so neither surface can learn this on its own — both must enrich, and they now share one helper
    rather than two copies that drift.
    """
    from concordance import unchecked
    from concordance.config import EngineConfig
    from concordance.web import api

    card = _card()
    unchecked.answer(card["id"], "holds", by="a reader")

    _s, html = api.render_card_html(card["id"], card)
    assert "Checked by 1 reader(s)" in html
    assert "No one has checked this card yet" not in html

    ask = api._unchecked_live(card["id"], {"headline": "No one has checked this card yet."})
    assert ask["checked_by"] == 1 and ask["open"] is False
    assert "Checked by 1 reader(s)" in ask["headline"]

    unchecked.answer(card["id"], "wrong", by="another reader")
    assert api._unchecked_live(card["id"], {"headline": "x"})["disputed"] is True


def test_the_standing_list_is_published():
    """A library that publishes its own unchecked list is harder to fool than one that waits to
    be audited."""
    from concordance import unchecked
    from concordance.web import api
    unchecked.note_recall(["c1", "c2"])
    unchecked.answer("c1", "holds")
    from concordance.config import EngineConfig
    status, payload = api.dispatch("GET", "/unchecked", {}, None, EngineConfig("secular"))
    assert status == 200
    text = str(payload)
    assert "cards_seen" in text and "asked_and_open" in text


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
