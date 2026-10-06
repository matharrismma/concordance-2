"""The trajectory method (2026-10-06): success guides, failure narrows, and the coaching tree.

Wilson floor is earned by evidence (3/3 floors lower than 30/30); a SUCCESS needs a witness (never
self-graded) while a FAILURE is free; a microposition inherits its parent's floor; downline value sums
the whole line; and the fruit test asks both questions — does it bear, and is it good."""
import os
import tempfile

TMP = tempfile.mkdtemp(prefix="nh-traj-")
os.environ["CONCORDANCE_DATA_DIR"] = TMP

from concordance import trajectory as T                       # noqa: E402
from concordance.verifiers import statistics as S             # noqa: E402


def test_wilson_floor_is_earned_by_evidence():
    lo3 = T.wilson(3, 3)[0]
    lo30 = T.wilson(30, 30)[0]
    assert 0.0 < lo3 < lo30 < 1.0                             # perfect 3/3 floors BELOW perfect 30/30
    assert abs(T.wilson(9, 10)[0] - 0.5958) < 1e-3            # a known value
    # the interval narrows as n grows (the path narrowing)
    assert (T.wilson(30, 30)[2] - T.wilson(30, 30)[0]) < (T.wilson(3, 3)[2] - T.wilson(3, 3)[0])


def test_success_needs_a_witness_failure_is_free():
    assert T.record("p_guard", True)["ok"] is False           # a success with no witness is refused
    assert T.record("p_guard", True, witness="film+coach")["ok"] is True
    assert T.record("p_guard", False)["ok"] is True           # a failure is recorded freely


def test_measure_reports_floor_rate_and_direction():
    for ok in (True, True, True, False, True, True):
        T.record("p_measure", ok, witness="film")             # failures still recorded (witness ignored)
    m = T.measure("p_measure")
    assert m["n"] == 6 and m["successes"] == 5
    assert 0.0 < m["floor"] <= m["rate"] <= 1.0
    assert m["direction"] in ("improving", "steady", "declining")


def test_a_microposition_inherits_its_parents_floor():
    for _ in range(18):
        T.record("root_std", True, witness="film")
    T.record("root_std", False)
    T.record("root_std", False)                               # root: 18/20, a high floor
    T.record("child_new", True, witness="film", parent="root_std")   # child, tiny own evidence
    child = T.measure("child_new")
    assert child["parent"] == "root_std" and child["generation"] == 1
    # the child starts ABOVE its own thin floor, lifted toward the parent's standard
    assert child["own_floor"] is not None and child["floor"] > child["own_floor"]


def test_downline_value_sums_the_whole_line():
    for _ in range(5):
        T.record("dl_root", True, witness="film")
    for _ in range(4):
        T.record("dl_kid", True, witness="film", parent="dl_root")
    for _ in range(3):
        T.record("dl_grandkid", True, witness="film", parent="dl_kid")
    dv = T.downline_value("dl_root")
    assert dv["own_fruit"] == 5 and dv["downline_fruit"] == 12 and dv["total_descendants"] == 2


def test_fruit_asks_both_questions():
    assert T.fruit("never_touched")["verdict"] == "barren"    # no fruit -> taken away
    for _ in range(8):
        T.record("good_tree", True, witness="film")
    f = T.fruit("good_tree")
    assert f["produces_fruit"] is True and f["fruit_is_good"] is True and f["verdict"] == "good"
    for _ in range(6):
        T.record("bad_tree", False)
    T.record("bad_tree", True, witness="log")                 # one witnessed win, mostly losses
    bad = T.fruit("bad_tree")
    assert bad["produces_fruit"] is True and bad["fruit_is_good"] is False and bad["verdict"] == "corrupt"


def test_the_wilson_floor_is_gated_as_a_verifier():
    ok = S.verify_trajectory({"successes": 9, "trials": 10, "confidence": 0.95,
                              "claimed_floor": round(T.wilson(9, 10)[0], 4)})
    assert ok.status == "CONFIRMED"
    bad = S.verify_trajectory({"successes": 9, "trials": 10, "confidence": 0.95, "claimed_floor": 0.80})
    assert bad.status == "MISMATCH"
