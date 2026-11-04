"""The schedule (tools/context.py): THE CLOCK and THE GEAR that decide when a standing rule is due.

A run completes at its last passing live verdict; a rule's runs are counted from its entry (run 0);
a confirmation is placed by its own time; a rule at interval index i whose last counted confirmation
is in run c is due in run n when n - c >= F(i+1). Every input here is invented.
"""
import datetime
import json
import os
import pathlib
import random
import subprocess
import sys

import pytest

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


def test_a_never_confirmed_rule_is_first_due_within_13_runs_of_its_entry():
    assert cx.SPREAD == cx.fib(7) == 13
    assert cx.stagger_starts(5) == [9, 4, 12, 7, 2]
    assert cx.stagger_measure(30) == (9, 13)          # today's 30 rules: the most due in one run, the longest first wait
    assert [j for j, s in enumerate(cx.stagger_starts(30), 1) if s == 1] == [13, 26]     # some are due in run 1
    assert min(cx.stagger_starts(10000)) == 1 and max(cx.stagger_starts(10000)) == 13
    with open(os.path.join(os.path.dirname(TOOLS), *cx.RULES_REL.split("/")), "rb") as fh:
        n = len(cx.parse_rules(fh.read().decode("utf-8")))
    assert max(cx.stagger_starts(n)) <= 13


def test_adding_a_rule_moves_no_existing_start():
    assert cx.stagger_starts(35)[:30] == cx.stagger_starts(30)
    assert cx.stagger_starts(35)[30:] == [3, 11, 6, 1, 9]
    assert all(cx.first_due(j) == s for j, s in enumerate(cx.stagger_starts(35), 1))


_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid"}


def _g(root, hour, *args):
    when = _at(hour).isoformat()
    env = {**os.environ, **_ENV, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    return subprocess.run(["git", "-c", "core.autocrlf=false", *args], cwd=root, env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


def _rules_at(root, hour, ids, field="", tail="", eol="\n"):
    text = "# Rules\n\n" + "".join(f'## {i}\n- scope: all\n- source: OWNER owner, chat, 2026-01-01 "{i}"\n{field}'
                                   f"- check: c\n> {i}\n\n" for i in ids) + tail
    _bytes_at(root, hour, text.replace("\n", eol).encode("utf-8"))


def _bytes_at(root, hour, data):
    full = os.path.join(root, *cx.RULES_REL.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as fh:
        fh.write(data)
    _g(root, hour, "add", "-A")
    _g(root, hour, "commit", "-q", "-m", f"rules at {hour}")


def test_ranks_are_frozen_at_entry_so_removing_a_rule_reranks_nothing_and_history_is_first_parent(tmp_path,
                                                                                                    monkeypatch):
    root = str(tmp_path / "r")
    os.makedirs(root)
    _g(root, 0, "init", "-q")
    _rules_at(root, 1, ["c", "a", "b"])                     # one commit: ranked by id
    _rules_at(root, 2, ["a", "b", "c", "d"])
    _rules_at(root, 3, ["a", "c", "d"])                      # b removed: nobody moves
    _rules_at(root, 4, ["a", "c", "d", "e"])
    main = _g(root, 4, "rev-parse", "--abbrev-ref", "HEAD")
    _g(root, 4, "checkout", "-q", "-b", "side")
    _rules_at(root, 5, ["z", "a", "c", "d", "e"])           # z is committed first, on a side branch
    _g(root, 5, "checkout", "-q", main)
    _rules_at(root, 6, ["a", "c", "d", "e", "m"])
    _g(root, 7, "merge", "-q", "--no-ff", "-m", "merge side", "side")   # z enters the first-parent history here
    monkeypatch.setattr(cx, "_REPO", root)
    head = _g(root, 7, "rev-parse", "HEAD")
    assert cx.rule_ranks(head) == {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "m": 6, "z": 7}
    assert (cx.rule_entries(head)["m"], cx.rule_entries(head)["z"]) == (_at(6), _at(7))
    removed = _g(root, 7, "rev-parse", "HEAD~2")             # the main commit before m: b long gone
    assert cx.rule_ranks(removed) == {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}


def _repo_with_a_removal(tmp_path):
    """RULES.md goes [c, a, b], [a, c], [a, aa, c], [a, aa, c, z]: b is removed before aa and z enter."""
    root = str(tmp_path / "r")
    os.makedirs(root)
    _g(root, 0, "init", "-q")
    for hour, ids in enumerate((["c", "a", "b"], ["a", "c"], ["a", "aa", "c"], ["a", "aa", "c", "z"]), 1):
        _rules_at(root, hour, ids)
    return root, _g(root, 4, "rev-parse", "HEAD")


def test_a_shallow_clone_gives_no_ranks_and_no_entries_where_a_full_clone_gives_the_true_ones(tmp_path, monkeypatch):
    root, head = _repo_with_a_removal(tmp_path)
    url = pathlib.Path(root).as_uri()
    full = str(tmp_path / "full")
    _g(str(tmp_path), 4, "clone", "-q", url, full)
    monkeypatch.setattr(cx, "_REPO", full)
    ranks = cx.rule_ranks(head)
    assert ranks == {"a": 1, "b": 2, "c": 3, "aa": 4, "z": 5}
    assert [cx.first_due(ranks[r]) for r in ("a", "aa", "c", "z")] == [9, 7, 12, 2]
    assert cx.rule_entries(head) == {"a": _at(1), "b": _at(1), "c": _at(1), "aa": _at(3), "z": _at(4)}
    for depth in ("1", "2"):
        clone = str(tmp_path / ("depth" + depth))
        _g(str(tmp_path), 4, "clone", "-q", "--depth", depth, url, clone)
        monkeypatch.setattr(cx, "_REPO", clone)
        for read in (cx.rule_ranks, cx.rule_entries):
            with pytest.raises(cx.NoHistory, match="shallow"):
                read(head)


def test_git_failing_gives_no_schedule_and_a_deleted_file_is_not_a_failure(tmp_path, monkeypatch):
    root, head = _repo_with_a_removal(tmp_path)
    monkeypatch.setattr(cx, "_REPO", root)
    real = cx._git
    broken = {
        "rev-parse-fails": lambda r, *a: None if a[0] == "rev-parse" else real(r, *a),
        "an-old-git-echoes-the-flag": lambda r, *a: b"--is-shallow-repository\n" if a[0] == "rev-parse" else real(r, *a),
        "log-fails": lambda r, *a: None if a[0] == "log" else real(r, *a),
        "a-blob-cannot-be-read": lambda r, *a: None if a[:2] == ("cat-file", "blob") else real(r, *a),
    }
    for name, git in broken.items():
        monkeypatch.setattr(cx, "_git", git)
        for read in (cx.rule_ranks, cx.rule_entries):
            with pytest.raises(cx.NoHistory, match="git could not"):
                read(head)
    monkeypatch.setattr(cx, "_git", real)
    os.remove(os.path.join(root, *cx.RULES_REL.split("/")))
    _g(root, 5, "add", "-A")
    _g(root, 5, "commit", "-q", "-m", "RULES.md deleted")
    _rules_at(root, 6, ["a", "new"])
    assert cx.rule_ranks(_g(root, 6, "rev-parse", "HEAD")) == {"a": 1, "b": 2, "c": 3, "aa": 4, "z": 5, "new": 6}


def test_a_rule_the_history_does_not_hold_means_no_schedule(monkeypatch):
    text = '## {0}\n- scope: all\n- source: OWNER owner, chat, 2026-01-01 "{0}"\n- check: c\n> {0}\n\n'
    rules = cx.parse_rules(text.format("a") + text.format("b"))
    monkeypatch.setattr(cx, "_rules_history", lambda sha: [(T0, ["a"])])
    assert cx._schedule_basis("0" * 40, rules[:1]) == ({"a": T0}, {"a": 1})
    with pytest.raises(cx.NoHistory, match="does not hold every rule"):
        cx._schedule_basis("0" * 40, rules)


# What a version of RULES.md enters is read from its headings alone. The reader knows nothing of the
# fields, the text block or today's id form, so a change to any of them cannot move an old rank.
HEADINGS = [
    ("plain", "## a-rule\n- scope: all\n", ["a-rule"]),
    ("no-final-newline", "## a\n## b", ["a", "b"]),
    ("crlf", "## a\r\n- scope: all\r\n## b\r\n", ["a", "b"]),
    ("bare-cr", "## a\r## b\r", ["a", "b"]),
    ("mixed-line-endings", "## a\r\n## b\n## c\r", ["a", "b", "c"]),
    ("byte-order-mark", "\ufeff## a\n", ["a"]),
    ("trailing-whitespace", "## a  \t\n", ["a"]),
    ("two-spaces-after-the-hashes", "##  a\n", ["a"]),
    ("another-id-form", "## Keep_The_Lamp.v2\n", ["Keep_The_Lamp.v2"]),
    ("repeated-in-one-version", "## a\n## a\n", ["a", "a"]),
    ("a-heading-quoted-in-a-text-line", "## a\n> ## not-a-rule\n>## nor-this\n", ["a"]),
    ("a-heading-in-a-field", "- check: ## not-a-rule\n", []),
    ("indented", "  ## not-a-rule\n\t## nor-this\n", []),
    ("one-hash", "# a title\n", []),
    ("three-hashes", "### an-aside\n", []),
    ("no-space-after-the-hashes", "##a\n##\tb\n", []),
    ("no-id", "##\n## \n", []),
    ("a-prose-heading", "## How to read this file\n", []),
    # A line of '## ' and one token IS a heading to this format, wherever it stands, and the parser
    # refuses it there. Read here it takes a place, the same place forever, so it moves nothing later.
    ("a-one-word-heading-in-the-preamble", "# Title\n\n## overview\n\nProse.\n\n## a\n", ["overview", "a"]),
]


@pytest.mark.parametrize("text,ids", [(t, i) for _, t, i in HEADINGS], ids=[n for n, _, _ in HEADINGS])
def test_the_heading_reader(text, ids):
    assert cx.heading_ids(text) == ids


def test_the_byte_order_mark_is_an_escape_in_the_source_never_the_invisible_character():
    # A literal U+FEFF in a string works until an editor strips it, and then the reader silently stops
    # handling byte-order marks.
    with open(os.path.join(TOOLS, "context.py"), "rb") as fh:
        assert chr(0xFEFF).encode("utf-8") not in fh.read()


def test_the_heading_reader_and_the_parser_agree_on_the_real_rules():
    with open(os.path.join(os.path.dirname(TOOLS), *cx.RULES_REL.split("/")), "rb") as fh:
        text = fh.read().decode("utf-8")
    assert cx.heading_ids(text) == [r.id for r in cx.parse_rules(text)]


def _repo(tmp_path, monkeypatch):
    root = str(tmp_path / "r")
    os.makedirs(root)
    _g(root, 0, "init", "-q")
    monkeypatch.setattr(cx, "_REPO", root)
    return root


def test_a_version_that_will_not_parse_still_enters_the_rules_it_first_added(tmp_path, monkeypatch):
    root = _repo(tmp_path, monkeypatch)
    _rules_at(root, 1, ["a", "b"])
    _rules_at(root, 2, ["a", "b", "z"], tail="Stray prose inside the last entry.\n")
    _rules_at(root, 3, ["a", "b", "z", "y"])
    head = _g(root, 3, "rev-parse", "HEAD")
    with pytest.raises(cx.RecordsError):
        cx.parse_rules(_g(root, 3, "show", f"HEAD~1:{cx.RULES_REL}"))
    ranks = cx.rule_ranks(head)
    assert ranks == {"a": 1, "b": 2, "z": 3, "y": 4}
    assert (cx.first_due(ranks["z"]), cx.first_due(ranks["y"])) == (12, 7)
    assert (cx.rule_entries(head)["z"], cx.rule_entries(head)["y"]) == (_at(2), _at(3))


def test_a_new_required_field_moves_no_rank_and_no_entry(tmp_path, monkeypatch):
    root = _repo(tmp_path, monkeypatch)
    _rules_at(root, 1, ["c", "a", "b"])
    _rules_at(root, 2, ["a", "c"])
    _rules_at(root, 3, ["a", "c", "aa"])
    _rules_at(root, 4, ["a", "c", "aa"], field="- owner: lead\n")
    head = _g(root, 4, "rev-parse", "HEAD")
    want = {"a": 1, "b": 2, "c": 3, "aa": 4}
    assert cx.rule_ranks(head) == want and cx.first_due(want["aa"]) == 7

    def changed_parser(text):                                # every older version now fails to parse
        raise AssertionError("the history walk read a version with the parser")

    monkeypatch.setattr(cx, "parse_rules", changed_parser)
    assert cx.rule_ranks(head) == want
    assert cx.rule_entries(head) == {"a": _at(1), "b": _at(1), "c": _at(1), "aa": _at(3)}


def test_line_endings_a_byte_order_mark_and_another_id_form_in_old_versions_are_read_alike(tmp_path, monkeypatch):
    root = _repo(tmp_path, monkeypatch)
    _rules_at(root, 1, ["a"], eol="\r\n")
    _bytes_at(root, 2, "\ufeff## a\n## b\n".encode("utf-8"))
    _rules_at(root, 3, ["a", "b", "Odd_Form.v2"], tail="> ## quoted-not-entered\n")
    _rules_at(root, 4, ["a", "b", "c"], eol="\r")
    head = _g(root, 4, "rev-parse", "HEAD")
    assert cx.rule_ranks(head) == {"a": 1, "b": 2, "Odd_Form.v2": 3, "c": 4}
    assert cx.rule_entries(head) == {"a": _at(1), "b": _at(2), "Odd_Form.v2": _at(3), "c": _at(4)}


def test_bytes_that_are_not_text_give_no_schedule_rather_than_no_rules(tmp_path, monkeypatch):
    for name, data in (("not-utf-8", "## a\n".encode("utf-16")), ("nul-bytes", "## a\n".encode("utf-16-le"))):
        root = str(tmp_path / name)
        os.makedirs(root)
        _g(root, 0, "init", "-q")
        monkeypatch.setattr(cx, "_REPO", root)
        _rules_at(root, 1, ["a"])
        _bytes_at(root, 2, data)
        _rules_at(root, 3, ["a", "b"])
        head = _g(root, 3, "rev-parse", "HEAD")
        for read in (cx.rule_ranks, cx.rule_entries):
            with pytest.raises(cx.NoHistory, match="not text"):
                read(head)


def test_a_confirmation_is_read_without_todays_id_form():
    assert cx._CONFIRM.fullmatch("RULE Odd_Form.v2 held: it held").group("rule") == "Odd_Form.v2"
    assert cx._CONFIRM.fullmatch("RULE a-rule failed: it did not").group("verdict") == "failed"
    for text in ("RULE two words held: x", "RULE a-rule held:", "RULE a-rule kept: x", "a-rule held: x"):
        assert cx._CONFIRM.fullmatch(text) is None


def test_rules_md_stays_where_its_history_is():
    # git log -- <path> stops at a rename and shows the move as a commit adding every rule: the same
    # truncation as a shallow clone, with no flag to warn of it. Moving RULES.md means following its
    # old path in _rules_history in the same change, or every rank moves without a word.
    assert cx.RULES_REL == "docs/harness/RULES.md"


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
