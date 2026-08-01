"""The watchman has teeth — every check FAILS when its invariant does.

A watchman nobody has seen bark is decoration. Each check here exists for a defect that actually
happened on 2026-08-01, and each is fed a broken world to prove it notices.

The first version of `the agent plane withholds` PASSED VACUOUSLY — it searched a nonsense term,
got `nothing_found` as it always would, never reached the branch that tests withholding, and
reported ok. That is the same fault as an assay reporting a verdict over one probe of a thousand,
committed by the instrument built to catch it. Hence this file: a green check is worth nothing
until it has been seen red.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

_spec = importlib.util.spec_from_file_location("watch", ROOT / "tools" / "watch.py")
watch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(watch)

HOST = "https://example.invalid"


def _answers(payload, code=200, size=100):
    return lambda h, p, timeout=60: (code, payload, size)


def test_a_climbing_handle_count_is_broken(monkeypatch):
    monkeypatch.setattr(watch, "_get", _answers({"shards": {"open": 900, "peak": 950}}))
    assert watch.check_handles_are_not_accumulating(HOST)["state"] == watch.BROKEN


def test_health_that_stops_reporting_handles_is_broken(monkeypatch):
    """The leak was invisible for days precisely because nothing counted it."""
    monkeypatch.setattr(watch, "_get", _answers({"ok": True}))
    r = watch.check_handles_are_not_accumulating(HOST)
    assert r["state"] == watch.BROKEN and "invisible" in r["detail"]


def test_a_quiet_handle_count_holds(monkeypatch):
    monkeypatch.setattr(watch, "_get", _answers({"shards": {"open": 2, "peak": 9}}))
    assert watch.check_handles_are_not_accumulating(HOST)["state"] == watch.HOLDS


def test_junk_returned_for_a_nonsense_question_is_broken(monkeypatch):
    monkeypatch.setattr(watch, "_get",
                        _answers({"count": 3, "results": [{"title": "Meditations 8.51"}]}))
    r = watch.check_a_miss_stays_a_miss(HOST)
    assert r["state"] == watch.BROKEN and "junk" in r["detail"]


def test_a_silent_cap_is_broken(monkeypatch):
    monkeypatch.setattr(watch, "_get", _answers({"results": [{}] * 200}))
    r = watch.check_the_ceiling_is_announced(HOST)
    assert r["state"] == watch.BROKEN and "silently" in r["detail"]


def test_no_ceiling_at_all_is_broken(monkeypatch):
    monkeypatch.setattr(watch, "_get", _answers({"results": [{}] * 5000}))
    assert watch.check_the_ceiling_is_announced(HOST)["state"] == watch.BROKEN


def test_a_miss_that_never_reaches_the_slow_lane_is_broken(monkeypatch):
    monkeypatch.setattr(watch, "_get", _answers({"count": 0, "results": []}))
    r = watch.check_both_doors_expand(HOST)
    assert r["state"] == watch.BROKEN and "slow lane" in r["detail"]


def test_verify_not_holding_is_broken(monkeypatch):
    monkeypatch.setattr(watch, "_post", lambda h, p, pay, timeout=60: (200, {"verdict": "BROKEN"}, 9))
    assert watch.check_proving_still_works(HOST)["state"] == watch.BROKEN


def test_a_tool_advertising_a_key_is_broken(monkeypatch):
    monkeypatch.setattr(watch, "_post", lambda h, p, pay, timeout=60: (
        200, {"result": {"tools": [{"name": "bad", "inputSchema": {"private_key": {}}}]}}, 9))
    r = watch.check_no_tool_advertises_a_private_key(HOST)
    assert r["state"] == watch.BROKEN and "bad" in r["detail"]


def test_nothing_held_is_CANNOT_CHECK_not_a_pass(monkeypatch):
    """The vacuous pass this file exists to prevent."""
    monkeypatch.setattr(watch, "_get", _answers({"count": 0, "items": []}))
    r = watch.check_the_agent_plane_withholds(HOST)
    assert r["state"] == watch.CANNOT, "with nothing held there is nothing to prove — not a pass"
    assert "not a pass" in r["detail"]


def test_a_held_card_served_publicly_is_broken(monkeypatch):
    def _g(h, p, timeout=60):
        if p.startswith("/curate/queue"):
            return 200, {"count": 1, "items": [{"kind": "acquisition", "card_id": "card_pd_x"}]}, 9
        return 200, {"card": {"id": "card_pd_x", "lifecycle_stage": "public"}}, 9
    monkeypatch.setattr(watch, "_get", _g)
    r = watch.check_the_agent_plane_withholds(HOST)
    assert r["state"] == watch.BROKEN


def test_an_unreachable_review_desk_is_broken(monkeypatch):
    monkeypatch.setattr(watch, "_get", _answers(None, code=500))
    assert watch.check_the_review_desk_is_reachable(HOST)["state"] == watch.BROKEN


def test_the_run_refuses_to_report_when_a_check_crashes(monkeypatch):
    """A tidy table over a subset is worse than no table — it gets believed."""
    def _boom(host):
        raise RuntimeError("the check itself fell over")
    monkeypatch.setattr(watch, "CHECKS", [watch.check_the_front_door_answers, _boom])
    monkeypatch.setattr(watch, "_get", _answers({"version": "x", "surface": "secular"}))
    rep = watch.watch(HOST)
    assert rep["crashed"], "a crashed check must be recorded, never silently dropped"
    assert rep["ran"] < rep["planned"]


def test_every_check_names_the_defect_it_exists_for():
    """A watchman that says 'check 7 failed' teaches nothing at 3am."""
    for fn in watch.CHECKS:
        assert (fn.__doc__ or "").strip(), f"{fn.__name__} must say what it is guarding"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
