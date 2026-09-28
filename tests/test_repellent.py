"""REPELLENT — the no-entry pheromone (negative stigmergy). Pins: OFF by default (damp 1.0, repel no-op);
a repelled card is down-weighted WITHIN its tier, floored (never zeroed); the mark decays; and a
concurrent worker's marks are merged, never clobbered."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import repellent  # noqa: E402


def _reset():
    repellent._REPEL.clear()
    repellent._LOADED[0] = False
    repellent._MTIME[0] = 0.0
    repellent._LAST_EVAP[0] = 0.0


@pytest.fixture()
def on(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CONCORDANCE_REPELLENT", "1")
    _reset()
    yield
    _reset()


def test_off_by_default_is_inert(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("CONCORDANCE_REPELLENT", raising=False)
    _reset()
    assert repellent.enabled() is False
    repellent.repel(["x"])                          # no-op
    assert repellent.strength("x") == 0.0
    assert repellent.damp_factor("x") == 1.0        # ranking unchanged
    _reset()


def test_repel_down_weights_within_a_tier(on):
    repellent.repel(["x", "x", "x"])                # flagged several times
    repellent.repel(["y"])                           # flagged once
    dx, dy = repellent.damp_factor("x"), repellent.damp_factor("y")
    assert repellent._FLOOR <= dx < dy < 1.0        # both down-weighted, x more, both floored
    assert repellent.damp_factor("clean") == 1.0    # an unmarked card is untouched


def test_never_below_the_floor(on):
    repellent.repel(["x"] * 500)
    assert repellent.damp_factor("x") == pytest.approx(repellent._FLOOR)   # floored, never zeroed


def test_mark_decays(on):
    repellent.repel(["x"])
    s0 = repellent.strength("x")
    repellent._LAST_EVAP[0] = time.time() - 2 * repellent._HALFLIFE_S     # two half-lives unrefreshed
    s1 = repellent.strength("x")
    assert 0 < s1 < s0
    assert s1 == pytest.approx(s0 * (repellent._RHO ** 2), rel=0.1)       # avoidance fades, not a curse


def test_merges_and_does_not_clobber_a_concurrent_mark(on, tmp_path):
    repellent.repel(["x"])                           # our mark
    # another worker writes the shared store with its own mark y
    (tmp_path / "repellent.json").write_text(json.dumps({"repel": {"y": 5.0}, "last_evap": time.time()}))
    repellent._LOADED[0] = False                     # force a fresh look at the shared store
    repellent.repel(["x"])                           # a second mark on x, merged onto disk
    d = json.loads((tmp_path / "repellent.json").read_text())
    assert set(d["repel"]) == {"x", "y"}             # neither worker's mark was lost


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
