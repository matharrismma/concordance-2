"""TRAINING — the loop where teaching IS training. Pins: OFF by default (no-op); selects the strongest
demand (most-asked open 'missing' want); acquires via the injected proven path; reinforces + closes only
when a card was bound; leaves the want open when nothing was kept."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import training  # noqa: E402


def _fold_two():
    # two open 'missing' wants — one asked far more than the other
    return {
        "w_quiet": {"state": "open", "kind": "missing", "query": "how to ford a river", "asks": 1},
        "w_loud": {"state": "open", "kind": "missing", "query": "how to purify water", "asks": 9},
        "w_closed": {"state": "closed", "kind": "missing", "query": "already done", "asks": 50},
    }


def test_off_by_default_is_noop(monkeypatch):
    monkeypatch.delenv("CONCORDANCE_TRAINING", raising=False)
    assert training.enabled() is False
    r = training.step(acquire_fn=lambda q: {"card_id": "x", "kept": 1}, fold_fn=_fold_two)
    assert r["status"] == "gated_off"


def test_next_want_is_the_strongest_demand():
    picked = training.next_want(fold_fn=_fold_two)
    assert picked is not None and picked[0] == "w_loud"          # most-asked open want, not the closed one


def test_step_learns_reinforces_and_closes(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_TRAINING", "1")
    seen = {}
    def acquire(q):
        seen["query"] = q
        return {"card_id": "card_new", "kept": 1, "trust": "verified", "lifecycle_stage": "public_review"}
    deposited, closed = [], []
    r = training.step(acquire_fn=acquire, fold_fn=_fold_two,
                      deposit_fn=lambda ids: deposited.extend(ids),
                      close_fn=lambda wid, cid, by: closed.append((wid, cid, by)) or {"ok": True})
    assert seen["query"] == "how to purify water"               # acquired the strongest demand
    assert r["status"] == "learned" and r["card_id"] == "card_new" and r["closed"] is True
    assert deposited == ["card_new"]                            # reinforced the bound card
    assert closed == [("w_loud", "card_new", "training")]       # closed the gap it filled


def test_nothing_kept_leaves_the_want_open(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_TRAINING", "1")
    closed = []
    r = training.step(acquire_fn=lambda q: {"status": "rejected"},   # verifier broke it / PII / no PD source
                      fold_fn=_fold_two, close_fn=lambda *a: closed.append(a) or {"ok": True},
                      deposit_fn=lambda ids: None)
    assert r["status"] == "nothing_kept" and closed == []       # the gap stays open — honest


def test_run_advances_past_an_unfillable_want(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_TRAINING", "1")
    tried = []
    def acquire(q):
        tried.append(q)
        return {"status": "no_source"}             # nothing kept — the want stays open
    r = training.run(acquire_fn=acquire, steps=3, fold_fn=_fold_two)
    # must try BOTH open wants (strongest first), never wedge on the first — then run dry
    assert tried == ["how to purify water", "how to ford a river"]
    assert r["learned"] == 0 and r["results"][-1]["status"] == "no_open_wants"


def test_run_stops_when_no_open_wants(monkeypatch):
    monkeypatch.setenv("CONCORDANCE_TRAINING", "1")
    r = training.run(acquire_fn=lambda q: {"card_id": "x", "kept": 1}, steps=5, fold_fn=lambda: {})
    assert r["steps"] == 1 and r["learned"] == 0 and r["results"][0]["status"] == "no_open_wants"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
