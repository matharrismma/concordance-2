"""The schedule (tools/context.py): THE CLOCK and THE GEAR that decide when a standing rule is due.

A run completes at its last passing live verdict; a rule's runs are counted from its entry (run 0);
a confirmation is placed by its own time; a rule at interval index i whose last counted confirmation
is in run c is due in run n when n - c >= F(i+1). Every input here is invented.
"""
import datetime
import json
import os
import random
import subprocess
import sys

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
sys.path.insert(0, TOOLS)
import context as cx  # noqa: E402
import harness as h  # noqa: E402

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def _at(hours):
    return T0 + datetime.timedelta(hours=hours)


def _done(*hours, repo="concordance-2"):
    return [cx.Completed(_at(x), repo, f"2026-01-01-run-{k}", 1) for k, x in enumerate(hours, 1)]


def _cf(hours, verdict="held", rule="a-rule", repo="concordance-2", run="2026-01-01-r", line=1):
    return cx.Confirmation(_at(hours), repo, run, line, "checker-1", rule, verdict)


def _whenever_due(runs, start=1):
    """Run n lies between hours n-1 and n (it completes at hour n); confirm held whenever due."""
    done, cfs = _done(*range(1, runs + 1)), []
    for n in range(1, runs + 1):
        if cx.gear(T0, done, cfs, start, t=_at(n - 0.5)).due:
            cfs.append(_cf(n - 0.5, line=n))
    return [k for _, k in cx.gear(T0, done, cfs, start).counted]


def test_the_intervals_are_fibonacci_and_a_failure_resets_to_one():
    assert [cx.interval(i) for i in range(1, 11)] == [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    done = _done(*range(1, 20))
    g = cx.gear(T0, done, [_cf(0.5), _cf(2.5, line=2)], t=_at(3.5))          # held in runs 1 and 3
    assert (g.c, g.i, g.n, g.due) == (3, 3, 4, False)                          # next due at 3 + F(4) = 6
    assert cx.gear(T0, done, [_cf(0.5), _cf(2.5, line=2)], t=_at(5.5)).due
    g = cx.gear(T0, done, [_cf(0.5), _cf(2.5, line=2), _cf(3.5, "failed", line=3)], t=_at(4.5))
    assert (g.c, g.i, g.n, g.due) == (4, 1, 5, True)                           # failed in run 4: due in run 5
    g = cx.gear(T0, done, [_cf(3.5, "failed")], t=_at(3.7))                     # a failure counts at any time
    assert (g.c, g.i, g.due) == (4, 1, False)


def test_an_always_held_rule_confirmed_whenever_due_is_confirmed_in_runs_f_m_plus_3_minus_2():
    assert _whenever_due(240) == [cx.fib(m + 3) - 2 for m in range(1, 11)] == [1, 3, 6, 11, 19, 32, 53, 87, 142, 231]


def test_a_staggered_start_shifts_the_sequence_and_nothing_else():
    assert _whenever_due(60, start=5) == [4 + k for k in (1, 3, 6, 11, 19, 32, 53)]


def test_two_held_confirmations_in_one_run_count_once():
    g = cx.gear(T0, _done(1, 2, 3), [_cf(0.2), _cf(0.7, line=2)], t=_at(0.9))
    assert [k for _, k in g.counted] == [1] and [k for _, k in g.listed] == [1]
    assert (g.c, g.i) == (1, 2)


def test_the_tie_rule_orders_runs_by_repo_name_then_run_id_and_a_confirmation_at_a_completion_is_in_that_run():
    t = _at(5)
    runs = [cx.Completed(t, "witness", "a", 1), cx.Completed(t, "Concordance-V3", "z", 1),
            cx.Completed(t, "concordance-2", "b", 1), cx.Completed(t, "Concordance-V3", "a", 1),
            cx.Completed(_at(4), "witness", "z", 1)]
    assert [(d.repo, d.run) for d in cx.clock(runs)] == [
        ("witness", "z"), ("Concordance-V3", "a"), ("Concordance-V3", "z"), ("concordance-2", "b"), ("witness", "a")]
    assert cx.run_number(T0, runs, t) == 2                       # runs completing at t are not before t
    assert cx.run_number(T0, runs) == 6 and cx.run_number(_at(4.5), runs) == 5


def test_a_confirmation_inside_a_run_that_never_completes_still_lets_the_rule_fall_due():
    done = _done(1, 3, 4)                                        # the run holding the confirmation never completes
    cfs = [_cf(2, run="2026-01-01-stalled")]                     # placed in run 2: one run completed before it
    assert [k for _, k in cx.gear(T0, done, cfs).counted] == [2]
    assert not cx.gear(T0, done, cfs, t=_at(3.5)).due             # run 3: 3 - 2 < F(3)
    assert cx.gear(T0, done, cfs).due                             # run 4: 4 - 2 >= 2, though run 2's ledger stalled


def test_runs_before_the_entry_never_count():
    done = _done(1, 2, 3, 4)
    assert cx.run_number(_at(2.5), done) == 3
    g = cx.gear(_at(2.5), done, [_cf(1.5)])                       # a confirmation before entry sits in run 1
    assert [k for _, k in g.counted] == [1] and (g.n, g.due) == (3, True)


def _ledger(root, run, events):
    d = os.path.join(root, "docs", "harness", "runs")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, run + ".jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for e in events:
            fh.write(json.dumps(e, sort_keys=True) + "\n")


def _complete(ts, extra=()):
    base = "0" * 40
    ev = [{"ev": "open", "by": "lead", "head": base, "ts": ts},
          {"ev": "plan", "by": "lead", "goal": "g", "done": ["d"], "ts": ts},
          {"ev": "verdict", "by": "checker-1", "step": "plan", "pass": True, "findings": [], "ts": ts},
          {"ev": "step", "by": "builder-1", "owner": "builder-1", "step": "s", "claim": "c", "scope": ["x"],
           "tests": ["t"], "base": base, "adopted": [], "ts": ts},
          {"ev": "verdict", "by": "checker-1", "step": "s", "pass": True, "findings": [], "ts": ts},
          {"ev": "commit", "by": "lead", "step": "s", "sha": base, "paths": [], "ts": ts},
          {"ev": "note", "by": "lead", "kind": "ship", "text": "nothing ships", "pass": True, "ts": ts},
          {"ev": "verdict", "by": "checker-1", "step": "live", "pass": True, "findings": [], "head": base, "ts": ts}]
    return ev + list(extra)


def _note(by, text, ts="2026-01-01T09:00:00+00:00"):
    return {"ev": "note", "by": by, "kind": "confirm", "text": text, "ts": ts}


def test_ignored_confirmations_are_listed_and_the_schedule_ignores_the_order_ledgers_are_read_in(tmp_path):
    a, b = str(tmp_path / "a"), str(tmp_path / "b")
    _ledger(a, "2026-01-01-one", _complete("2026-01-01T09:00:00+00:00", [
        _note("checker-1", "RULE a-rule held: it held"),
        _note("lead", "RULE a-rule held: the lead's word"),
        _note("builder-1", "RULE a-rule failed: a builder's word"),
        _note("checker-7", "RULE a-rule held: a checker with no verdict here"),
        _note("checker-1", "a-rule held, in free words")]))
    _ledger(a, "2026-01-01-open", [{"ev": "open", "by": "lead", "head": "0" * 40, "ts": "2026-01-01T10:00:00+00:00"},
                                   {"ev": "verdict", "by": "checker-2", "step": "plan", "pass": False,
                                    "findings": ["f"], "ts": "2026-01-01T10:00:00+00:00"},
                                   _note("checker-2", "RULE a-rule failed: in a run that never completes",
                                         "2026-01-01T10:30:00+00:00")])
    _ledger(b, "2026-01-01-two", _complete("2026-01-01T11:00:00+00:00", [
        _note("checker-1", "RULE a-rule held: held again", "2026-01-01T11:00:00+00:00")]))
    one = cx.read_runs(h, [("concordance-2", a), ("Concordance-V3", b)])
    two = cx.read_runs(h, [("Concordance-V3", b), ("concordance-2", a)])
    done, found, ignored = one
    assert [(d.repo, d.run, d.line) for d in cx.clock(done)] == [
        ("concordance-2", "2026-01-01-one", 8), ("Concordance-V3", "2026-01-01-two", 8)]
    assert sorted(ignored) == [
        ("concordance-2", "2026-01-01-one", 10, "it is not by a checker"),
        ("concordance-2", "2026-01-01-one", 11, "it is not by a checker"),
        ("concordance-2", "2026-01-01-one", 12, "its checker has no verdict in this ledger"),
        ("concordance-2", "2026-01-01-one", 13, "it does not read 'RULE <id> held|failed: <evidence>'")]
    assert [(f.run, f.line, f.verdict) for f in found] == [
        ("2026-01-01-one", 9, "held"), ("2026-01-01-open", 3, "failed"), ("2026-01-01-two", 9, "held")]
    gears = [cx.gear(T0, d, random.Random(seed).sample(f, len(f))) for seed, (d, f, _) in enumerate((one, two, one))]
    assert gears[0] == gears[1] == gears[2]
    assert [(cf.run, k) for cf, k in gears[0].counted] == [("2026-01-01-one", 1), ("2026-01-01-open", 2)]
    assert [(cf.run, k) for cf, k in gears[0].listed] == [("2026-01-01-two", 2)]
    assert (gears[0].n, gears[0].c, gears[0].i, gears[0].due) == (3, 2, 1, True)


def test_the_stagger_lowers_the_most_rules_due_in_one_run_so_it_is_adopted():
    assert cx.stagger_starts(5) == [4, 2, 5, 3, 1]
    assert cx.stagger_measure(30) == (30, 6)
    with open(os.path.join(os.path.dirname(TOOLS), *cx.RULES_REL.split("/")), "rb") as fh:
        n = len(cx.parse_rules(fh.read().decode("utf-8")))
    plain, spread = cx.stagger_measure(n)
    assert spread < plain == n


def test_a_rule_enters_at_the_commit_that_added_it(tmp_path, monkeypatch):
    root = str(tmp_path / "r")
    os.makedirs(root)

    def commit(text, when):
        env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when, "GIT_AUTHOR_NAME": "t",
               "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
        full = os.path.join(root, *cx.RULES_REL.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        for args in (["add", "-A"], ["commit", "-q", "-m", "r"]):
            subprocess.run(["git", "-c", "core.autocrlf=false", *args], cwd=root, env=env, check=True, capture_output=True)

    rule = '## {0}\n- scope: all\n- source: OWNER owner, chat, 2026-01-01 "{0}"\n- check: c\n> {0}\n\n'
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    commit(rule.format("first"), "2026-01-01T01:00:00+00:00")
    commit(rule.format("first") + rule.format("second"), "2026-01-01T02:00:00+00:00")
    commit(rule.format("second") + rule.format("first"), "2026-01-01T03:00:00+00:00")     # a reorder enters nothing
    monkeypatch.setattr(cx, "_REPO", root)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    assert cx.rule_entries(head) == {"first": _at(1), "second": _at(2)}
