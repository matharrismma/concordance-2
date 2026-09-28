"""PHYSIOLOGY — division of labor + homeostasis (the body's flow regulation on the manifold). Pins: OFF
by default; a single clear best is untouched; a TIE is broken toward capacity (least recent load); an
unavailable fittest caste re-allocates to the next available one; load decays (interaction rate); and
faces.route is byte-for-byte unchanged when off."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import faces, physiology  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_load():
    physiology._LOAD.clear()
    yield
    physiology._LOAD.clear()


def test_off_by_default(monkeypatch):
    monkeypatch.delenv("CONCORDANCE_ALLOCATION", raising=False)
    assert physiology.enabled() is False


def test_single_clear_winner_and_none_when_no_fit():
    assert physiology.allocate({"a": 2, "b": 1}) == "a"      # a clear best is chosen, as the plain router would
    assert physiology.allocate({"a": 0, "b": 0}) is None     # nothing fits -> a face is never forced
    assert physiology.allocate({}) is None


def test_tie_breaks_toward_capacity():
    t = 1000.0
    # with no load, a tie is stable by id
    assert physiology.allocate({"a": 1, "b": 1}, now=t) == "a"
    # once 'a' has served (recent load), the tie goes to the caste with capacity
    physiology.note("a", now=t)
    physiology.note("a", now=t)
    assert physiology.allocate({"a": 1, "b": 1}, now=t) == "b"


def test_reallocates_when_fittest_is_unavailable():
    # 'a' is the better fit, but it is out -> spill to the best AVAILABLE caste (resilience)
    assert physiology.allocate({"a": 2, "b": 1}, available=["b"]) == "b"
    # never drops below fitness when the fittest IS available
    assert physiology.allocate({"a": 2, "b": 1}, available=["a", "b"]) == "a"


def test_load_is_a_decaying_rate():
    t = 5000.0
    physiology.note("a", now=t)
    assert physiology.load("a", now=t) == pytest.approx(1.0, rel=1e-6)
    assert physiology.load("a", now=t + physiology._HALFLIFE_S) == pytest.approx(0.5, rel=1e-6)
    assert physiology.load("idle", now=t) == 0.0


def test_route_tie_off_is_unchanged_on_balances(monkeypatch):
    # two castes that fit the same word equally -> a genuine tie
    monkeypatch.setattr(faces, "_FACES", {"face_a": {"scope": ["widget"]},
                                          "face_b": {"scope": ["widget"]}}, raising=True)
    monkeypatch.delenv("CONCORDANCE_ALLOCATION", raising=False)
    assert faces.route("widget") == "face_a"                 # off: dict-first on a tie (unchanged)
    monkeypatch.setenv("CONCORDANCE_ALLOCATION", "1")
    physiology._LOAD.clear()
    physiology.note("face_a")                                # face_a has been busy
    assert faces.route("widget") == "face_b"                 # on: steered to the caste with capacity
    assert faces.route("nothing here") is None               # still never forces a face


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
