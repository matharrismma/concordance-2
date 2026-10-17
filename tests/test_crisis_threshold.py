"""Issue #41 — the backstop threshold is derived from the UNGUARDED benign lines, and a rebuild can never
shrink the net.

Found while fixing #23: `build_crisis_semantic.py` set threshold = top score over ALL of CLEARLY_BENIGN
+ margin. CLEARLY_BENIGN had grown lines a structural guard now handles (profession_only, the lookup
frames …) that score up to 0.72 — so the NEXT rebuild would have raised the threshold 0.6568 -> 0.7406
and silently dropped 37 of the 62 pinned catches. Nothing was wrong at HEAD; the hazard was the rebuild.
These pins run against the sealed artifact, so they hold without a rebuild (and skip if it is absent).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import pytest  # noqa: E402

from concordance import ask, crisis_semantic as cs  # noqa: E402
import build_crisis_semantic as build  # noqa: E402
import test_crisis_coverage as T  # noqa: E402

PINNED = tuple(T.CLEARLY_BENIGN) + tuple(T.CRISIS_FLOOR) + tuple(T.RED_TEAM_BLIND)


def _need_artifact():
    if not cs.available():
        pytest.skip("crisis_semantic.json artifact not present")


def test_guarded_is_exactly_the_guard_set_flags_consults():
    """flags() == (not guarded) and score > threshold, line for line — the refactor moved no behavior.
    (guarded is what the build tool excludes; if flags ever consulted a guard guarded did not, the
    build would derive from lines the runtime never scores, and #41 would be back.)"""
    _need_artifact()
    thr = cs._load()["threshold"]
    for q in PINNED:
        assert cs.flags(q) == ((not cs.guarded(q)) and cs.score(q) > thr), q


def test_is_crisis_is_the_substring_net_unioned_with_the_backstop():
    for q in PINNED:
        assert ask.is_crisis(q) == (ask.substring_net(q) or cs.flags(q)), q


def test_no_structural_guard_touches_a_pinned_cry():
    """A guard that fires on a cry the substring net does not catch is a cry lost — none may."""
    lost = [q for q in tuple(T.CRISIS_FLOOR) + tuple(T.RED_TEAM_BLIND)
            if cs.guarded(q) and not ask.substring_net(q)]
    assert not lost, lost


def test_the_derivation_excludes_guard_handled_lines_and_keeps_every_catch():
    """Derived with the sealed scorer over today's sets, the threshold passes the fail-closed check:
    0 false positives, every curated cry caught, the red-team ratchet held, and NOTHING the sealed
    artifact catches is lost."""
    _need_artifact()
    thr = build.derive_threshold(cs.score)
    guarded_n = sum(1 for q in T.CLEARLY_BENIGN if cs.guarded(q))
    assert guarded_n > 0, "the guard-handled benign lines are what the derivation must exclude"
    problems, report = build.check_net(cs.score, thr, old_flags=cs.flags)
    assert not problems, problems
    assert report["dropped"] == 0 and report["fp"] == 0 and report["floor_missed"] == 0
    assert report["union"] >= T._RED_TEAM_FLOOR


def test_the_naive_derivation_over_every_benign_line_would_shrink_the_net():
    """The hazard itself, pinned so the derivation is never quietly reverted to 'max over all benign'."""
    _need_artifact()
    naive = max(cs.score(q) for q in T.CLEARLY_BENIGN) + build.MARGIN
    fixed = build.derive_threshold(cs.score)
    assert naive > fixed, (naive, fixed)
    problems, report = build.check_net(cs.score, naive, old_flags=cs.flags)
    assert report["dropped"] > 0 and problems, "the naive threshold no longer drops a catch — re-measure #41"


def test_a_shrinking_candidate_is_refused_not_sealed():
    """check_net is the gate: a threshold above the sealed one that loses even one catch is a problem."""
    _need_artifact()
    thr = cs._load()["threshold"]
    problems, report = build.check_net(cs.score, thr, old_flags=cs.flags)
    assert not problems and report["dropped"] == 0
    # a scorer that never fires loses every backstop-only catch -> refused
    problems, report = build.check_net(lambda _q: 0.0, thr, old_flags=cs.flags)
    assert problems and report["dropped"] > 0
