"""UNCHECKED — the card goes in wearing its question, and the first reader is asked to close it.

Matt, 2026-08-01: *"We put them in, when you write, but you ask the first person that recalls the
cards to verify them."*

Four conditions, in order of how much damage getting them wrong would do:

  * **the ask reaches the READER** — not the log, not the route, the person and the agent. A
    guarantee that is correct server-side and invisible on the page has failed five separate times
    in this project, so it is tested where a reader actually stands: the presentation block that
    both the card page and the /card JSON render from.
  * **one reader is a check, not a proof** — the count is reported and never repainted as
    "verified". `checked_by: 1` is true; "verified" would be a lie told in the reader's favour.
  * **one "wrong" never erases anything** — a single anonymous verdict with delete power is a
    vandalism vector wearing the clothes of diligence.
  * **asking never blocks reading** — the card is IN. A library that fails to serve because it
    could not append a log line has its priorities backwards.

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


def _card(cid="card_span_x"):
    from concordance import unchecked
    return unchecked.mark({
        "id": cid, "updated_at": 1.0, "title": "PREAMBLE",
        "body": "In order that we may preserve our God-given heritage...",
        "source": {"label": "Manual (1923)", "url": "https://archive.org/details/x"},
        "extra": {"source_sha256": "14ca62", "span": [231643, 232342]},
    })


# ── the reader ────────────────────────────────────────────────────────────────────────────────
def test_the_ask_reaches_the_reader_not_just_the_log():
    """THE rule. present.derive is what BOTH the card page and the /card JSON render from."""
    from concordance import present
    p = present.derive(_card())
    assert "unchecked" in p, "an unchecked card presented as though it had been checked"
    ask = p["unchecked"]
    assert ask["open"] is True
    assert "fairly represent" in ask["question"]
    assert set(ask["answers"]) == {"holds", "wrong", "unsure"}
    assert ask["source"]["sha256"] == "14ca62" and ask["source"]["span"] == [231643, 232342]


def test_a_checked_card_carries_no_ask():
    from concordance import present
    plain = {"id": "c", "updated_at": 1.0, "title": "x", "extra": {"drop_kind": "note"}}
    assert "unchecked" not in present.derive(plain)


def test_the_ask_is_pure_so_presentation_keeps_its_contract():
    """present.derive promises to be free, cacheable and side-effect-free. Reading the log inside
    it would break all three — and the cache would then serve a stale answer count forever."""
    from concordance import present, unchecked
    c = _card()
    a, b = present.derive(c), present.derive(c)
    assert a is b, "the presentation stopped being cacheable"
    # no store was created merely by presenting
    assert not (Path(os.environ["CONCORDANCE_DATA_DIR"]) / "unchecked.jsonl").exists(), \
        "presenting a card wrote to the store — derive is supposed to be pure"
    assert unchecked.question(c)["open"] is True


# ── the count ─────────────────────────────────────────────────────────────────────────────────
def test_one_reader_is_a_check_not_a_proof():
    from concordance import unchecked
    unchecked.note_recall(["card_span_x"])
    r = unchecked.answer("card_span_x", "holds", by="a reader")
    assert r["ok"] and r["checked_by"] == 1
    assert "two or three witnesses" in r["note"]
    for value in r.values():
        assert str(value).lower() != "verified", "one answer was repainted as verification"
    assert "verified" not in r["message"].lower()


def test_the_first_recall_is_the_one_that_asks():
    from concordance import unchecked
    first = unchecked.note_recall(["card_a", "card_b"], reader="anon")
    assert set(first["asked"]) == {"card_a", "card_b"} and first["already"] == []
    again = unchecked.note_recall(["card_a"])
    assert again["asked"] == [] and again["already"] == ["card_a"], \
        "the same card asked twice — the question goes to the FIRST reader"
    assert unchecked.state_of("card_a")["asked"] is True


# ── the dispute ───────────────────────────────────────────────────────────────────────────────
def test_one_wrong_marks_disputed_and_erases_nothing():
    """A single anonymous verdict with delete power is a vandalism vector."""
    from concordance import unchecked
    unchecked.note_recall(["card_span_x"])
    r = unchecked.answer("card_span_x", "wrong", note="this is out of context")
    assert r["ok"] and r["disputed"] is True and r["disputed_by"] == 1
    assert "steward" in r["message"] and "must not erase" in r["message"]
    st = unchecked.state_of("card_span_x")
    assert len(st["answers"]) == 1, "the record of the dispute is the point; it must persist"


def test_a_nonsense_verdict_is_refused_with_a_reason():
    from concordance import unchecked
    r = unchecked.answer("card_x", "DELETE")
    assert r["ok"] is False and "verdict must be one of" in r["reason"]
    assert unchecked.answer("", "holds")["ok"] is False


# ── the ledger ────────────────────────────────────────────────────────────────────────────────
def test_standing_reports_what_it_measured_over():
    """A count of open questions means nothing without knowing how many cards were seen."""
    from concordance import unchecked
    unchecked.note_recall(["c1", "c2", "c3"])
    unchecked.answer("c1", "holds")
    unchecked.answer("c2", "wrong")
    s = unchecked.standing()
    assert s["cards_seen"] == 3
    assert s["asked_and_open"] == 1 and s["open_ids"] == ["c3"]
    assert s["checked"] == 1 and s["disputed"] == 1 and s["disputed_ids"] == ["c2"]


def test_a_corrupt_line_never_takes_down_the_read():
    from concordance import unchecked
    unchecked.note_recall(["c1"])
    p = Path(os.environ["CONCORDANCE_DATA_DIR"]) / "unchecked.jsonl"
    p.write_text(p.read_text(encoding="utf-8") + "{not json at all\n", encoding="utf-8")
    assert unchecked.state_of("c1")["asked"] is True
    assert unchecked.standing()["cards_seen"] == 1


def test_asking_never_blocks_reading(monkeypatch):
    """A library that fails to serve a card because it could not append a log line has its
    priorities backwards."""
    from concordance import unchecked
    monkeypatch.setattr(unchecked, "_append", lambda rec: False)
    r = unchecked.note_recall(["c1"])
    assert r["asked"] == [] and r == {"asked": [], "already": []}
    assert unchecked.answer("c1", "holds")["ok"] is False   # honest, not silent


# ── the mint ──────────────────────────────────────────────────────────────────────────────────
def test_every_crafted_card_is_born_carrying_the_question():
    """Stamped AT THE MINT, so no path exists by which an engine-written card reaches a store
    without it."""
    import hashlib
    import json as _json
    from concordance import craft, sources, unchecked

    prior = os.environ.get("CONCORDANCE_SOURCES")
    os.environ["CONCORDANCE_SOURCES"] = tempfile.mkdtemp()
    try:
        text = ("I. Of Sanctification\n\n"
                "In order that we may preserve our heritage, the faith once delivered to the "
                "saints, especially the doctrine and experience of sanctification as a second "
                "work of grace, we do hereby ordain and set forth this statement, that it may "
                "stand for those who come after us as a plain witness of what has been believed "
                "from the beginning until this present day and hour.\n")
        raw = text.encode("utf-8")
        sha = hashlib.sha256(raw).hexdigest()
        p = sources.path_for(sha, ".txt")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        (p.parent / (sha + ".waybill.json")).write_text(_json.dumps({
            "sha256": sha, "origin_url": "https://archive.org/details/x",
            "label": "A Manual (1923)", "path": str(p)}), encoding="utf-8")

        cards = craft.craft(sha, "sanctification grace")["cards"]
        assert cards, "the fixture yielded no card to check"
        for c in cards:
            assert unchecked.is_open(c), f"{c['id']} was minted without its question"
            assert c["extra"][unchecked.MARK] is True
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_SOURCES", None)
        else:
            os.environ["CONCORDANCE_SOURCES"] = prior


def test_the_mark_survives_a_round_trip_through_json():
    """The card is stored as JSON; a mark that does not survive serialization marks nothing."""
    import json as _json
    from concordance import unchecked
    back = _json.loads(_json.dumps(_card()))
    assert unchecked.is_open(back)
    assert unchecked.question(back)["open"] is True


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
