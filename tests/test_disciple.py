"""Disciple — a member's walked path with the coach, computed from their own progress.

The coach is stateless about the learner; a disciple's progress (`done` units) lives in their sovereign
profile, and walk() reads it back. Empty is the trailhead, not failure. Pure — profiles in a temp dir.
"""
import json

from concordance import disciple


def test_the_trailhead_is_honest_not_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    r = disciple.walk("nh_newcomer")
    assert r["done_count"] == 0 and "journey" in r and "next" in r and "mastery" in r


def test_walk_counts_a_members_completed_units(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    d = tmp_path / "profiles"
    d.mkdir()
    (d / "nh_walker.json").write_text(json.dumps({"done": ["u1", "u2", "u3"], "subject": "read"}),
                                      encoding="utf-8")
    r = disciple.walk("nh_walker")
    assert r["done_count"] == 3 and r["subject"] == "read"        # the road walked, honestly counted


def test_walk_ignores_non_string_progress(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    d = tmp_path / "profiles"
    d.mkdir()
    (d / "nh_x.json").write_text(json.dumps({"done": ["u1", 5, None, "u2"]}), encoding="utf-8")
    assert disciple.walk("nh_x")["done_count"] == 2               # only real unit ids count
