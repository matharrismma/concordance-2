"""Branch — fork a conversation, hand work forward to a member and a time.

The property that matters for fork: the shared past is provable by HASH EQUALITY, not by a
pointer we ask you to trust. For defer: what comes back, comes back because a time arrived —
and nothing is silently dropped.
"""
import os
import tempfile

os.environ["CONCORDANCE_THREADS_DIR"] = tempfile.mkdtemp(prefix="nh-branch-threads-")
os.environ["CONCORDANCE_DEFERRED_DIR"] = tempfile.mkdtemp(prefix="nh-branch-defer-")

from concordance import branch, threads  # noqa: E402

OWNER = "nh_branchowner01"


def _thread(n=4):
    rec = threads.new_thread()
    tid = rec["thread_id"]
    for i in range(n):
        threads.append(tid, f"turn {i}", {"kind": "search", "message": f"reply {i}"})
    return tid


# --- fork ---------------------------------------------------------------------------------

def test_fork_carries_the_prefix():
    tid = _thread()
    r = branch.fork(tid, 1)
    assert r["ok"] and r["carried"] == 2
    assert len(threads.get(r["thread_id"])["exchanges"]) == 2


def test_the_shared_past_keeps_its_hashes():
    """Ancestry is provable: identical hashes mean genuinely the same history."""
    tid = _thread()
    r = branch.fork(tid, 2)
    src = threads.get(tid)["exchanges"]
    new = threads.get(r["thread_id"])["exchanges"]
    assert [e["hash"] for e in new] == [e["hash"] for e in src[:3]]


def test_both_branches_stay_live_and_independent():
    tid = _thread()
    child = branch.fork(tid, 1)["thread_id"]
    threads.append(tid, "parent goes on", {"kind": "search"})
    threads.append(child, "child goes elsewhere", {"kind": "search"})
    assert len(threads.get(tid)["exchanges"]) == 5
    assert len(threads.get(child)["exchanges"]) == 3
    assert threads.get(tid)["head_hash"] != threads.get(child)["head_hash"]


def test_fork_defaults_to_the_whole_thread():
    tid = _thread()
    assert branch.fork(tid)["carried"] == 4


def test_lineage_verifies_by_hash_not_by_claim():
    tid = _thread()
    child = branch.fork(tid, 2)["thread_id"]
    lin = branch.lineage(child)
    assert lin["ok"] and lin["verified"] is True and lin["shared"] == 3
    assert lin["forked_from"]["thread_id"] == tid


def test_lineage_of_an_original_thread():
    lin = branch.lineage(_thread())
    assert lin["ok"] and lin["forked_from"] is None and lin["verified"] is True


def test_fork_refuses_bad_input():
    tid = _thread()
    assert branch.fork("0" * 32)["ok"] is False
    assert branch.fork(tid, 99)["ok"] is False
    assert branch.fork(tid, -1)["ok"] is False
    empty = threads.new_thread()["thread_id"]
    assert branch.fork(empty)["ok"] is False


def test_fork_carries_the_open_gate():
    """The Gate is sticky (Mt 7:7) — a branch does not close a door already opened."""
    rec = threads.new_thread()
    tid = rec["thread_id"]
    threads.append(tid, "seeking", {"kind": "search"}, gate_open=True)
    child = branch.fork(tid)["thread_id"]
    assert threads.get(child)["gate_open"] is True


# --- defer / due ---------------------------------------------------------------------------

def test_defer_and_it_comes_due():
    r = branch.defer(OWNER, member="steward", when=1000.0, note="the April invoice")
    assert r["ok"]
    d = branch.due(OWNER, now=2000.0)
    assert d["count"] >= 1
    assert any(i["note"] == "the April invoice" for i in d["due"])


def test_not_yet_due_stays_out_of_the_way():
    branch.defer("nh_later01", member="coach", when=9_000_000_000.0, note="far future")
    assert branch.due("nh_later01", now=1000.0)["count"] == 0
    assert branch.pending("nh_later01")["count"] == 1     # waiting, not lost


def test_dates_are_accepted_as_well_as_epochs():
    r = branch.defer("nh_dates01", member="steward", when="2026-04-01", note="tax")
    assert r["ok"]
    assert branch.due("nh_dates01", now=r["item"]["when"] + 1)["count"] == 1


def test_ambiguous_when_is_refused():
    assert branch.defer("nh_x", member="steward", when="next April", note="x")["ok"] is False
    assert branch.defer("nh_x", member="steward", when=None, note="x")["ok"] is False


def test_unknown_member_is_refused():
    assert branch.defer("nh_x", member="butler", when=1.0, note="x")["ok"] is False


def test_deferring_nothing_is_refused():
    assert branch.defer("nh_x", member="steward", when=1.0)["ok"] is False


def test_release_takes_it_out_of_due_but_keeps_the_record():
    r = branch.defer("nh_rel01", member="coach", when=1.0, note="vowel set")
    iid = r["item"]["id"]
    assert branch.release("nh_rel01", iid)["ok"] is True
    assert branch.due("nh_rel01", now=9e9)["count"] == 0
    assert branch.release("nh_rel01", iid)["note"] == "already released"


def test_release_unknown_is_refused():
    assert branch.release("nh_rel01", "nope")["ok"] is False


def test_due_is_ordered_and_deterministic():
    o = "nh_order01"
    branch.defer(o, member="steward", when=300.0, note="third")
    branch.defer(o, member="coach", when=100.0, note="first")
    branch.defer(o, member="shepherd", when=200.0, note="second")
    notes = [i["note"] for i in branch.due(o, now=1000.0)["due"]]
    assert notes == ["first", "second", "third"]
    assert branch.due(o, now=1000.0) == branch.due(o, now=1000.0)


def test_queues_are_separate_per_owner():
    branch.defer("nh_ownA", member="steward", when=1.0, note="mine")
    assert branch.due("nh_ownB", now=9e9)["count"] == 0
