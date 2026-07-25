"""Formation — make a wish for life. The honest invariants: it FINDS (never generates), it always
points to a concrete OFFLINE first step, and it stores nothing about the person."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import formation  # noqa: E402


def test_kinds_are_offered():
    ks = {k["id"] for k in formation.kinds()["kinds"]}
    assert {"become", "overcome", "mend", "place", "learn", "serve"} <= ks


def test_help_finds_and_points_offline_never_generates():
    r = formation.help("I want to stop losing my temper with my kids", kind="overcome")
    assert r["ok"] is True and r["kind"] == "overcome"
    assert r["generated"] is False                     # conduit — found, not authored
    assert isinstance(r["practices"], list)            # a list of found cards (may be empty w/o corpus)
    assert r["first_step"] and "person" in r["first_step"].lower()  # a real, offline first move
    assert "online is the tool" in r["note"].lower()   # the reset: online is not the end game


def test_unknown_kind_defaults_and_empty_is_refused():
    assert formation.help("grow in patience", kind="nonsense")["kind"] == "become"
    assert formation.help("   ")["ok"] is False
