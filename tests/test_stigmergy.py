"""STIGMERGY — the keeping's pheromone layer (ACO for recall). Pins: OFF by default (byte-for-byte
unchanged ranking), a retrieval deposits aggregate pheromone, trails evaporate, the boost only lifts
WITHIN a tier and is capped, and the store is aggregate (card->strength, no identity/query)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import stigmergy  # noqa: E402


def _reset():
    stigmergy._TRAILS.clear()
    stigmergy._LOADED[0] = False
    stigmergy._LAST_EVAP[0] = 0.0
    stigmergy._DIRTY[0] = 0


@pytest.fixture()
def on(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CONCORDANCE_STIGMERGY", "1")
    _reset()
    yield
    _reset()


@pytest.fixture()
def off(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("CONCORDANCE_STIGMERGY", raising=False)
    _reset()
    yield
    _reset()


def test_off_by_default_is_byte_for_byte_inert(off):
    assert stigmergy.enabled() is False
    stigmergy.deposit(["a", "b", "c"])            # no-op
    assert stigmergy.strength("a") == 0.0
    assert stigmergy.boost_factor("a") == 1.0     # ranking unchanged
    assert stigmergy.top() == []


def test_deposit_strengthens_and_boost_lifts_within_a_tier(on):
    stigmergy.deposit(["a", "a", "a"])            # a well-travelled trail
    stigmergy.deposit(["b"])                       # a lightly-used one
    assert stigmergy.strength("a") > stigmergy.strength("b") > 0
    ba, bb = stigmergy.boost_factor("a"), stigmergy.boost_factor("b")
    assert 1.0 < bb < ba <= stigmergy._CAP         # capped; never crosses a tier
    assert stigmergy.boost_factor("never-seen") == 1.0   # an untravelled card is untouched


def test_trails_evaporate(on):
    stigmergy.deposit(["a"])
    s0 = stigmergy.strength("a")
    stigmergy._LAST_EVAP[0] = time.time() - 2 * stigmergy._HALFLIFE_S   # two half-lives pass, unrefreshed
    s1 = stigmergy.strength("a")
    assert 0 < s1 < s0                              # faded, not hoarded
    assert s1 == pytest.approx(s0 * (stigmergy._RHO ** 2), rel=0.1)


def test_the_trail_is_aggregate_and_carries_no_identity(on):
    stigmergy.deposit(["card_x"])
    stigmergy.flush()
    import json
    d = json.loads((Path(__import__("os").environ["CONCORDANCE_DATA_DIR"]) / "stigmergy.json").read_text())
    # only {trails: {card_id: strength}} + a decay clock — no who, no query, no per-read log
    assert set(d.keys()) <= {"trails", "last_evap"}
    assert list(d["trails"].keys()) == ["card_x"] and isinstance(d["trails"]["card_x"], (int, float))


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
