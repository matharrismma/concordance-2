"""RECOMBINE — the expressive half (extractive, v0). Pins: composes ONLY from the given verbatim
instances; orders by the frame (existence → identity → motion) then relevance; every fragment keeps its
source; honest empty when nothing fits; nothing invented."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import recombine  # noqa: E402


def _ins(text, anchor, source="a book"):
    return {"text": text, "anchor": anchor, "source": source}


def test_off_by_default_gate():
    # the wiring gate is off by default; the pure core still composes
    import os
    os.environ.pop("CONCORDANCE_RECOMBINE", None)
    assert recombine.enabled() is False


def test_orders_by_the_frame_then_relevance():
    inst = [
        _ins("I go to the river each morning.", "I go"),           # motion (role 2)
        _ins("There is clean water in the spring.", "there is"),   # existence (role 0)
        _ins("This is the way to purify it.", "this is"),          # identity (role 1)
    ]
    r = recombine.compose("purify water spring", inst)
    assert r["found"] is True and len(r["fragments"]) == 3
    order = [f["anchor"] for f in r["fragments"]]
    assert order == ["there is", "this is", "I go"]               # existence → identity → motion
    assert r["passage"].startswith("There is clean water")
    assert all(f["source"] == "a book" for f in r["fragments"])   # provenance kept


def test_every_fragment_is_verbatim_from_the_pool():
    inst = [_ins("There is a fire on the hill.", "there is")]
    r = recombine.compose("fire", inst)
    assert r["passage"] == "There is a fire on the hill."          # verbatim, not reworded
    assert r["fragments"][0]["text"] in {i["text"] for i in inst}


def test_honest_empty_when_nothing_fits():
    r = recombine.compose("anything", [])
    assert r["found"] is False and r["passage"] == "" and "honest gap" in r["means"]


def test_limit_and_dedup():
    inst = [_ins("There is water.", "there is"), _ins("There is water.", "there is"),  # dup
            _ins("This is good.", "this is"), _ins("I go.", "I go")]
    r = recombine.compose("water", inst, limit=2)
    assert len(r["fragments"]) == 2
    texts = [f["text"] for f in r["fragments"]]
    assert texts == ["There is water.", "This is good."]           # dedup + frame order, capped


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
