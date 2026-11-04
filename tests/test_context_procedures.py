"""`tools/context.py ci` and `record`: two procedures the lead ran by hand, now run by the records' tool.

ci only reads, so it runs from this checkout against a stub gh on PATH that logs every call and answers
nothing but `gh run list` and `gh run view`. record makes a commit, so it refuses from an uncommitted
tools/context.py: its tests build a checkout with a local bare origin in a temporary directory, commit
this checkout's tools/context.py and tools/harness.py there, and run that committed copy in a subprocess.
The push and cleanup commands record prints are run by the tests, exactly as printed, because a printed
procedure nobody ran is how step (8) of the first record procedure came to be false.

Every name here is invented. In the record tests HOME, USERPROFILE, the system git configuration and the
harness's secret patterns are all pointed away from the machine, so no real configuration reaches them.
"""
import json
import os
import pathlib
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
import context as cx  # noqa: E402

SLUG = "example-owner/lamp-repo"
SHA = "0123456789abcdef0123456789abcdef01234567"
OTHER_SHA = "fedcba9876543210fedcba9876543210fedcba98"


# ---------------------------------------------------------------------------------- ci: the stub gh

STUB = r'''
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[1:]
with open(os.path.join(here, "calls.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps(argv) + "\n")
with open(os.path.join(here, "world.json"), encoding="utf-8") as fh:
    world = json.load(fh)


def answer(text):
    if text is None:
        sys.exit(1)
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.exit(0)


if argv[:2] == ["run", "list"]:
    answer(json.dumps(world["list"]))
if argv[:2] == ["run", "view"] and "--log" in argv:
    answer(world["logs"].get(argv[argv.index("--job") + 1]))
if argv[:2] == ["run", "view"]:
    view = world["views"].get(argv[2])
    answer(None if view is None else json.dumps(view))
sys.exit(97)
'''


def _stub_gh(tmp_path, world):
    """A directory holding a gh that answers from `world`. It is the whole of PATH in _ci."""
    d = tmp_path / "stub"
    d.mkdir()
    (d / "gh_stub.py").write_text(STUB, encoding="utf-8")
    (d / "world.json").write_text(json.dumps(world), encoding="utf-8")
    if os.name == "nt":
        (d / "gh.cmd").write_text(f'@echo off\r\n"{sys.executable}" "{d / "gh_stub.py"}" %*\r\n', encoding="utf-8")
    else:
        launcher = d / "gh"
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{d / "gh_stub.py"}" "$@"\n', encoding="utf-8")
        launcher.chmod(0o755)
    return d


def _ci(stub, *args):
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "context.py"), "ci", *args],
                       env={**os.environ, "PATH": str(stub)}, capture_output=True, encoding="utf-8")
    return r.returncode, r.stdout


def _calls(stub):
    log = stub / "calls.jsonl"
    return [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []


def _job(jid, name, conclusion="success", status="completed"):
    return {"databaseId": jid, "name": name, "status": status, "conclusion": conclusion}


def _log(job, *lines):
    """A job's log as gh prints it today: tab-separated, the step unknown, a BOM before the first stamp."""
    stamp = "2026-01-02T03:04:05.1234567Z"
    rows = [f"{job}\tUNKNOWN STEP\t\ufeff{stamp} Current runner version: '1.2.3'"]
    return "\n".join(rows + [f"{job}\tUNKNOWN STEP\t{stamp} {ln}" for ln in lines]) + "\n"


def _run(rid, jobs, logs, sha=SHA, status="completed", conclusion="success", event="push"):
    return {"list": {"databaseId": rid, "workflowName": "CI", "event": event, "headSha": sha},
            "view": {"headSha": sha, "status": status, "conclusion": conclusion, "jobs": jobs}, "logs": logs}


def _world(*runs):
    return {"list": [r["list"] for r in runs],
            "views": {str(r["list"]["databaseId"]): r["view"] for r in runs},
            "logs": {str(k): v for r in runs for k, v in r["logs"].items()}}


def _green(rid=11, **kw):
    return _run(rid, [_job(21, "windows"), _job(22, "gate")],
                {21: _log("windows", "44 passed in 2.43s"),
                 22: _log("gate", "....", "3082 passed, 229 skipped, 1 xfailed in 149.97s (0:02:29)")}, **kw)


# ------------------------------------------------------------------------------------- ci: the tests

def test_ci_prints_each_jobs_conclusion_and_the_suite_count_lines(tmp_path):
    code, out = _ci(_stub_gh(tmp_path, _world(_green())), SLUG, SHA)
    assert out.splitlines() == [
        f"CI {SLUG} {SHA}: 1 run(s)",
        "RUN 11 CI (push): success",
        "JOB gate: success",
        "  SUITE 3082 passed, 229 skipped, 1 xfailed in 149.97s (0:02:29)",
        "JOB windows: success",
        "  SUITE 44 passed in 2.43s",
        f"CI GREEN: 1 run(s), 2 job(s), 2 suite count line(s), every job a success, on {SHA}",
    ]
    assert code == 0


def test_ci_only_ever_calls_gh_run_list_and_gh_run_view(tmp_path):
    stub = _stub_gh(tmp_path, _world(_green(), _green(12, event="pull_request")))
    assert _ci(stub, SLUG, SHA)[0] == 0
    calls = _calls(stub)
    assert len(calls) == 7                                     # one list, and per run a view and two logs
    assert {tuple(c[:2]) for c in calls} == {("run", "list"), ("run", "view")}
    assert all(c[c.index("--repo") + 1] == SLUG for c in calls)
    assert calls[0][calls[0].index("--commit") + 1] == SHA
    assert not {"rerun", "cancel", "delete", "watch", "api", "--web"} & {a for c in calls for a in c}


@pytest.mark.parametrize("args", [("run", "rerun", "1"), ("run", "cancel", "1"), ("run", "delete", "1"),
                                  ("run", "watch", "1"), ("workflow", "run", "ci"), ("pr", "merge", "1"),
                                  ("api", "-X", "POST", "repos"), ("run",), ()],
                         ids=lambda a: "-".join(a) or "nothing")
def test_the_gh_helper_refuses_everything_but_run_list_and_run_view(args):
    with pytest.raises(ValueError):
        cx._gh(*args)


@pytest.mark.parametrize("conclusion", ["failure", "cancelled", "skipped", "neutral", "timed_out", "", None],
                         ids=str)
def test_ci_a_job_that_is_anything_but_a_success_is_not_green(tmp_path, conclusion):
    run = _run(11, [_job(21, "windows", conclusion), _job(22, "gate")],
               {21: _log("windows", "2 failed, 42 passed in 2.43s"), 22: _log("gate", "3 passed in 1.00s")})
    code, out = _ci(_stub_gh(tmp_path, _world(run)), SLUG, SHA)
    assert code == 1
    assert out.splitlines()[-1].startswith("CI NOT GREEN: ") and "job windows" in out.splitlines()[-1]
    assert "  SUITE 2 failed, 42 passed in 2.43s" in out.splitlines()      # a red job's count still prints


def test_ci_no_run_on_the_commit_is_not_green(tmp_path):
    stub = _stub_gh(tmp_path, _world())
    code, out = _ci(stub, SLUG, SHA)
    assert code == 1 and out.splitlines()[-1] == "CI NOT GREEN: no workflow run on this commit"


def test_ci_a_green_run_on_another_commit_never_counts(tmp_path):
    stub = _stub_gh(tmp_path, _world(_green(sha=OTHER_SHA)))
    code, out = _ci(stub, SLUG, SHA)
    assert code == 1 and out.splitlines()[-1] == "CI NOT GREEN: no workflow run on this commit"
    assert "IGNORED 1 run(s) on another commit" in out.splitlines()
    assert [c[:2] for c in _calls(stub)] == [["run", "list"]]              # it is never even opened


def test_ci_a_view_that_names_another_commit_is_not_green(tmp_path):
    run = _green()
    run["view"]["headSha"] = OTHER_SHA
    code, out = _ci(_stub_gh(tmp_path, _world(run)), SLUG, SHA)
    assert code == 1 and "run 11 could not be read for this commit" in out.splitlines()[-1]


def test_ci_a_second_run_that_failed_makes_the_commit_not_green(tmp_path):
    red = _run(12, [_job(23, "gate", "failure")], {23: _log("gate", "1 failed in 0.50s")},
               conclusion="failure", event="pull_request")
    code, out = _ci(_stub_gh(tmp_path, _world(_green(), red)), SLUG, SHA)
    assert code == 1 and "RUN 12 CI (pull_request): failure" in out.splitlines()
    assert "run 12" in out.splitlines()[-1] and "job gate" in out.splitlines()[-1]


def test_ci_an_unfinished_run_is_not_green_and_its_logs_are_not_asked_for(tmp_path):
    stub = _stub_gh(tmp_path, _world(_run(11, [_job(21, "gate", None, "in_progress")], {},
                                          status="in_progress", conclusion=None)))
    code, out = _ci(stub, SLUG, SHA)
    assert code == 1 and "JOB gate: in_progress" in out.splitlines()
    assert "RUN 11 CI (push): in_progress" in out.splitlines()
    assert not [c for c in _calls(stub) if "--log" in c]


def test_ci_a_successful_run_that_ran_no_job_is_not_green(tmp_path):
    code, out = _ci(_stub_gh(tmp_path, _world(_run(11, [], {}))), SLUG, SHA)
    assert code == 1 and "run 11 has no job" in out.splitlines()[-1]


def test_ci_a_green_job_whose_count_line_reports_failures_is_not_green(tmp_path):
    run = _run(11, [_job(21, "gate")], {21: _log("gate", "2 failed, 3 passed in 1.00s")})
    code, out = _ci(_stub_gh(tmp_path, _world(run)), SLUG, SHA)
    assert code == 1 and "job gate reports failures in a success" in out.splitlines()[-1]


@pytest.mark.parametrize("line", ["no tests ran in 0.01s", "229 skipped in 1.00s", "12 deselected in 0.10s",
                                  "3 skipped, 9 deselected, 1 warning in 0.20s", "2 xfailed in 0.10s",
                                  "1 xpassed in 0.10s", "0 passed, 4 skipped in 0.10s"],
                         ids=["no-tests", "all-skipped", "all-deselected", "skips-and-deselections", "all-xfailed",
                              "all-xpassed", "zero-passed"])
def test_ci_a_green_job_whose_suite_passed_nothing_is_not_green(tmp_path, line):
    run = _run(11, [_job(21, "gate")], {21: _log("gate", line)})
    code, out = _ci(_stub_gh(tmp_path, _world(run)), SLUG, SHA)
    assert code == 1 and out.splitlines()[-1] == "CI NOT GREEN: job gate has a count line that passed nothing"
    assert f"  SUITE {line}" in out.splitlines()                           # the line still prints, as evidence


def test_ci_a_suite_that_passed_nothing_beside_a_passing_job_is_not_green(tmp_path):
    run = _run(11, [_job(21, "windows"), _job(22, "gate")],
               {21: _log("windows", "44 passed in 2.00s"), 22: _log("gate", "no tests ran in 0.01s")})
    code, out = _ci(_stub_gh(tmp_path, _world(run)), SLUG, SHA)
    assert code == 1 and out.splitlines()[-1] == "CI NOT GREEN: job gate has a count line that passed nothing"


def test_ci_a_passing_suite_does_not_cover_an_empty_one_in_the_same_job(tmp_path):
    run = _run(11, [_job(21, "gate")], {21: _log("gate", "44 passed in 2.00s", "12 deselected in 0.10s")})
    code, out = _ci(_stub_gh(tmp_path, _world(run)), SLUG, SHA)
    assert code == 1 and out.splitlines()[-1] == "CI NOT GREEN: job gate has a count line that passed nothing"


@pytest.mark.parametrize("line", ["1 passed, 229 skipped, 12 deselected in 1.00s", "10 passed in 0.10s"],
                         ids=["one-beside-skips", "ten"])
def test_ci_a_suite_that_passed_a_test_ran(tmp_path, line):
    run = _run(11, [_job(21, "gate")], {21: _log("gate", line)})
    code, out = _ci(_stub_gh(tmp_path, _world(run)), SLUG, SHA)
    assert code == 0 and out.splitlines()[-1].startswith("CI GREEN: ")


def test_ci_an_unreadable_log_is_not_green(tmp_path):
    run = _run(11, [_job(21, "windows"), _job(22, "gate")], {22: _log("gate", "3 passed in 1.00s")})
    code, out = _ci(_stub_gh(tmp_path, _world(run)), SLUG, SHA)
    assert code == 1 and "  LOG unreadable" in out.splitlines()
    assert "job windows has no readable log" in out.splitlines()[-1]


def test_ci_a_job_with_no_count_line_is_named_and_alone_changes_nothing(tmp_path):
    run = _run(11, [_job(21, "lint"), _job(22, "gate")],
               {21: _log("lint", "all clean"), 22: _log("gate", "3 passed in 1.00s")})
    code, out = _ci(_stub_gh(tmp_path, _world(run)), SLUG, SHA)
    assert code == 0 and "  SUITE none: no count line in this job's log" in out.splitlines()


def test_ci_with_no_count_line_in_any_job_is_not_green(tmp_path):
    run = _run(11, [_job(21, "gate")], {21: _log("gate", "all clean")})
    code, out = _ci(_stub_gh(tmp_path, _world(run)), SLUG, SHA)
    assert code == 1 and out.splitlines()[-1] == "CI NOT GREEN: no job printed a suite count line"


@pytest.mark.parametrize("slug,sha", [(SLUG, SHA[:12]), (SLUG, "HEAD"), (SLUG, SHA.upper()),
                                      ("lamp-repo", SHA), ("--web", SHA), ("a/b/c", SHA)],
                         ids=["short", "ref", "upper", "no-owner", "a-flag", "too-deep"])
def test_ci_refuses_a_loose_repository_or_commit_before_calling_gh(tmp_path, slug, sha):
    stub = _stub_gh(tmp_path, _world(_green()))
    code, out = _ci(stub, "--", slug, sha)
    assert code == 2 and out.startswith("REFUSED: ")
    assert _calls(stub) == []


def test_ci_refuses_when_gh_is_absent_or_answers_nothing(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    code, out = _ci(empty, SLUG, SHA)
    assert code == 2 and out.startswith("REFUSED: ")
    broken = _world(_green())
    broken["list"] = {"not": "a list"}
    code, out = _ci(_stub_gh(tmp_path, broken), SLUG, SHA)
    assert code == 2 and out.startswith("REFUSED: ")


@pytest.mark.parametrize("line,want", [
    ("3082 passed, 229 skipped, 1 xfailed in 149.97s (0:02:29)",
     "3082 passed, 229 skipped, 1 xfailed in 149.97s (0:02:29)"),
    ("===== 4 failed, 3077 passed, 230 skipped in 319.08s (0:05:19) =====",
     "4 failed, 3077 passed, 230 skipped in 319.08s (0:05:19)"),
    ("\x1b[32m3 passed\x1b[0m\x1b[32m in 0.10s\x1b[0m", "3 passed in 0.10s"),
    ("1 passed, 2 warnings in 0.10s", "1 passed, 2 warnings in 0.10s"),
    ("1 error in 0.30s", "1 error in 0.30s"),
    ("no tests ran in 0.01s", "no tests ran in 0.01s"),
    ("Installed 3 packages in 2.00s", None),
    ("E   assert '3 passed in 0.10s' == ''", None),
    ("tests/test_lamp.py ... 3 passed", None),
], ids=["quiet", "banner", "colour", "warnings", "error", "no-tests", "pip", "nested", "no-time"])
def test_a_suite_count_line_is_pytests_summary_and_nothing_else(line, want):
    log = _log("gate", line)
    assert cx.suite_lines(log) == ([want] if want else [])


# --------------------------------------------------------------------- record: a checkout and its origin

FIXED = {"GIT_AUTHOR_DATE": "2026-01-02T03:04:05+00:00", "GIT_COMMITTER_DATE": "2026-01-02T03:04:05+00:00",
         "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
         "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
RUN = "2026-01-02-lamp"
REL = f"docs/harness/runs/{RUN}.jsonl"
BRANCH = "trunk"                          # neither main nor master, so nothing can assume either
WORD = "zebra-lantern-token"              # the invented secret: the fixture's only secret pattern
AUTOCRLF = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.autocrlf", "GIT_CONFIG_VALUE_0": "true"}


def _src(rel):
    with open(os.path.join(ROOT, *rel.split("/")), "rb") as fh:
        return fh.read().replace(b"\r\n", b"\n")


def _write(root, rel, data):
    full = os.path.join(str(root), *rel.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))


def _git(env, root, *args):
    r = subprocess.run(["git", *args], cwd=str(root), env=env, check=True, capture_output=True)
    return r.stdout.decode().strip()


def _commit(env, root, files, msg="fixture"):
    for rel, data in files.items():
        _write(root, rel, data)
    _git(env, root, "add", "-A")
    _git(env, root, "commit", "-q", "-m", msg)
    return _git(env, root, "rev-parse", "HEAD")


def _ev(**e):
    return json.dumps({"ts": "2026-01-02T03:04:05+00:00", **e}, sort_keys=True)


def _opened(step=True):
    """The run as its step commit holds it."""
    lines = [_ev(ev="open", by="lead", head="0" * 40),
             _ev(ev="plan", by="lead", goal="Keep the lamp lit.", done=["the lamp is lit"]),
             _ev(ev="verdict", by="checker-1", step="plan", findings=[], **{"pass": True})]
    if step:
        lines.append(_ev(ev="step", by="builder-1", owner="builder-1", step="s1", claim="s1 lights the lamp",
                         scope=["src/*"], tests=["tests/test_lamp.py"], base="0" * 40, adopted=[]))
    return "\n".join(lines) + "\n"


def _tail(sha):
    """What the run appends after its last commit, which no commit holds yet."""
    return "\n".join([_ev(ev="commit", by="lead", step="s1", sha=sha, paths=["src/lamp.py"]),
                      _ev(ev="note", by="lead", kind="ship", text="shipped", head=sha, **{"pass": True}),
                      _ev(ev="verdict", by="checker-2", step="live", findings=[], **{"pass": True})]) + "\n"


@dataclass
class World:
    env: Dict[str, str]
    origin: pathlib.Path
    root: pathlib.Path                    # the checkout holding the run's ledger
    cli: str                              # the committed tools/context.py to run
    pushed: str                           # the run's last pushed commit

    @property
    def ledger(self):
        return self.root.joinpath(*REL.split("/"))

    def append(self, line):
        with open(self.ledger, "ab") as fh:
            fh.write(line.encode("utf-8") + b"\n")

    def tip(self):
        return _git(self.env, self.root, "ls-remote", str(self.origin), f"refs/heads/{BRANCH}").split()[0]

    def worktrees(self):
        listed = _git(self.env, self.root, "worktree", "list", "--porcelain").splitlines()
        return sum(ln.startswith("worktree ") for ln in listed)

    def snapshot(self):
        """Everything of the checkout and origin that record must leave as it found it."""
        return {"head": _git(self.env, self.root, "rev-parse", "HEAD"),
                "status": _git(self.env, self.root, "status", "--porcelain"),
                "staged": _git(self.env, self.root, "diff", "--cached", "--name-only"),
                "ledger": self.ledger.read_bytes(),
                "origin": _git(self.env, self.root, "ls-remote", str(self.origin))}

    def clone(self, name):
        d = self.root.parent / name
        _git(self.env, self.root.parent, "clone", "-q", "-b", BRANCH, str(self.origin), str(d))
        return d


@pytest.fixture
def env(tmp_path):
    home, scratch = tmp_path / "home", tmp_path / "scratch"
    home.mkdir()
    scratch.mkdir()
    patterns = home / "patterns.txt"
    patterns.write_text(WORD + "\n", encoding="utf-8")
    plain = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "HARNESS_ROOT"}
    return {**plain, **FIXED, "HOME": str(home), "USERPROFILE": str(home), "XDG_CONFIG_HOME": str(home),
            "GIT_CONFIG_NOSYSTEM": "1", "HARNESS_CONFIG_DIR": str(home),
            "HARNESS_SECRET_PATTERNS": str(patterns),
            "TMPDIR": str(scratch), "TEMP": str(scratch), "TMP": str(scratch)}


def _build(tmp_path, env, holds_tools=True):
    """A pushed run: its checkout, with the ledger's tail uncommitted, and a local bare origin."""
    origin = tmp_path / "origin.git"
    _git(env, tmp_path, "-c", f"init.defaultBranch={BRANCH}", "init", "-q", "--bare", str(origin))
    root = tmp_path / "checkout"
    _git(env, tmp_path, "clone", "-q", str(origin), str(root))
    _git(env, root, "symbolic-ref", "HEAD", f"refs/heads/{BRANCH}")
    tools = {"tools/context.py": _src("tools/context.py"), "tools/harness.py": _src("tools/harness.py")}
    home = root
    if not holds_tools:                   # V3's shape: the repo tracks no harness, one beside context.py serves
        home = tmp_path / "tools-home"
        home.mkdir()
        _git(env, home, "-c", f"init.defaultBranch={BRANCH}", "init", "-q")
        _commit(env, home, tools)
    files = {REL: _opened(), "src/lamp.py": "LIT = True\n"}
    pushed = _commit(env, root, {**files, **(tools if holds_tools else {})})
    _git(env, root, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")
    _git(env, root, "fetch", "-q", "origin")
    _write(root, REL, _opened() + _tail(pushed))
    return World(env, origin, root, str(home / "tools" / "context.py"), pushed)


@pytest.fixture
def world(tmp_path, env):
    return _build(tmp_path, env)


def _record(w, *extra, run=RUN, root=None):
    r = subprocess.run([sys.executable, w.cli, "record", str(root or w.root), run, *extra],
                       cwd=str(w.root.parent), env=w.env, capture_output=True, encoding="utf-8")
    return r.returncode, r.stdout


def _commands(out):
    return [ln.strip() for ln in out.splitlines() if ln.startswith("  git ")]


def _kept(out):
    return shlex.split(next(c for c in _commands(out) if " push " in c))[2]


def _run_printed(w, out, next_branch="next-work"):
    """Every printed command, in order, exactly as printed."""
    for command in _commands(out):
        subprocess.run(shlex.split(command.replace("<next branch>", next_branch)), cwd=str(w.root.parent),
                       env=w.env, check=True, capture_output=True)


def _held(w):
    """The rule's own check: git diff origin/<default branch> -- <ledger path> is empty in the checkout."""
    _git(w.env, w.root, "fetch", "-q", "origin")
    return _git(w.env, w.root, "diff", f"origin/{BRANCH}", "--", REL) == ""


# --------------------------------------------------------------------------------- record: the tests

def test_record_commits_in_a_kept_worktree_and_changes_neither_origin_nor_the_checkout(world):
    before = world.snapshot()
    code, out = _record(world)
    assert code == 0 and out.splitlines()[-1].startswith("RECORD PASS: ")
    assert world.snapshot() == before                                     # nothing pushed, nothing touched
    assert world.worktrees() == 2                                         # the worktree is kept for the push
    wt = _kept(out)
    assert _git(world.env, wt, "rev-parse", "HEAD~1") == world.pushed     # its parent is origin's default branch
    assert subprocess.run(["git", "symbolic-ref", "-q", "HEAD"], cwd=wt, env=world.env).returncode != 0  # detached
    assert _git(world.env, wt, "diff", "--name-only", "HEAD~1", "HEAD") == REL      # the ledger alone
    recorded = subprocess.run(["git", "show", f"HEAD:{REL}"], cwd=wt, env=world.env, capture_output=True).stdout
    assert recorded == before["ledger"]
    assert _git(world.env, wt, "log", "-1", "--format=%s") == f"Harness run {RUN}: the ledger is recorded"


def test_record_prints_the_push_and_cleanup_commands_in_the_procedures_order(world):
    _, out = _record(world)
    verbs = [shlex.split(c)[3] for c in _commands(out)]
    assert verbs == ["push", "fetch", "diff", "worktree", "checkout", "merge"]
    assert f"push origin HEAD:refs/heads/{BRANCH}" in _commands(out)[0]
    assert f"diff --ignore-cr-at-eol --exit-code origin/{BRANCH} -- {REL}" in _commands(out)[2]
    assert "a non-zero exit means" in out and "prints nothing" not in out
    assert "worktree remove" in _commands(out)[3] and "--force" not in _commands(out)[3]
    assert _commands(out)[4].endswith(f"checkout -- {REL}")
    assert _commands(out)[5].endswith(f"merge --ff-only origin/{BRANCH}")
    assert "never append to this run's ledger in a checkout that lacks the record commit" in out


def test_the_printed_commands_land_the_record_and_bring_the_checkout_to_it(world):
    _, out = _record(world)
    wt = _kept(out)
    record = _git(world.env, wt, "rev-parse", "HEAD")
    _run_printed(world, out)
    assert world.tip() == record
    assert not os.path.exists(wt) and world.worktrees() == 1
    assert _git(world.env, world.root, "rev-parse", "HEAD") == record
    assert _git(world.env, world.root, "status", "--porcelain") == ""
    assert _held(world)


def test_from_another_branch_the_printed_commands_cut_the_next_branch_at_the_record(world):
    _git(world.env, world.root, "switch", "-q", "-c", "work")
    _, out = _record(world)
    assert _commands(out)[-1].endswith(f"switch -c <next branch> origin/{BRANCH}")
    assert not [c for c in _commands(out) if " merge " in c]
    record = _git(world.env, _kept(out), "rev-parse", "HEAD")
    _run_printed(world, out)
    assert _git(world.env, world.root, "symbolic-ref", "--short", "HEAD") == "next-work"
    assert _git(world.env, world.root, "rev-parse", "HEAD") == record
    assert _held(world)


def test_a_crlf_working_copy_compares_equal_to_the_lf_record(world):
    """A Windows checkout: the committed lines are CRLF in the working copy, the harness's appends LF."""
    world.env.update(AUTOCRLF)
    world.ledger.write_bytes(_opened().replace("\n", "\r\n").encode() + _tail(world.pushed).encode())
    code, out = _record(world)
    assert code == 0 and out.splitlines()[-1].startswith("RECORD PASS: ")
    wt = _kept(out)
    recorded = subprocess.run(["git", "show", f"HEAD:{REL}"], cwd=wt, env=world.env, capture_output=True).stdout
    assert b"\r" not in recorded and recorded == (_opened() + _tail(world.pushed)).encode()
    _run_printed(world, out)
    assert _held(world) and not os.path.exists(wt)


def test_the_printed_compare_ignores_carriage_returns_however_git_is_configured(world):
    world.env.update(AUTOCRLF)
    world.ledger.write_bytes(_opened().replace("\n", "\r\n").encode() + _tail(world.pushed).encode())
    _, out = _record(world)
    push, fetch, compare = (shlex.split(c) for c in _commands(out)[:3])
    for command in (push, fetch):
        subprocess.run(command, env=world.env, check=True, capture_output=True)
    plain = {k: v for k, v in world.env.items() if k not in AUTOCRLF}      # git no longer normalises for it
    assert subprocess.run(compare, env=plain, capture_output=True).returncode == 0


def test_a_line_landing_after_the_record_stops_the_printed_commands_before_the_discard(world):
    """Comparing before the push is safe only because the printed compare fails on a late line, and comes
    ahead of the discard: run in order, the commands stop there and the line survives."""
    _, out = _record(world)
    wt = _kept(out)
    late = _ev(ev="note", by="checker-2", kind="observation", text="a note after the record")
    world.append(late)
    with pytest.raises(subprocess.CalledProcessError) as stopped:
        _run_printed(world, out)
    assert stopped.value.cmd[3] == "diff"
    assert late.encode() in world.ledger.read_bytes()
    assert os.path.exists(wt) and world.worktrees() == 2


def test_a_line_landing_during_the_record_fails_the_comparison_and_prints_no_push(world):
    """A hook stands for a checker's note written while the record commits: the copies then differ."""
    note = _ev(ev="note", by="checker-2", kind="observation", text="a late note")
    hook = world.root / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(exist_ok=True)
    hook.write_text(f"#!/bin/sh\nprintf '%s\\n' '{note}' >> \"{world.ledger.as_posix()}\"\n", encoding="utf-8")
    hook.chmod(0o755)
    before = world.tip()
    code, out = _record(world)
    assert code == 1 and out.splitlines()[-1].startswith("RECORD FAIL: ")
    assert "do not push" in out and not [c for c in _commands(out) if " push " in c]
    assert [c for c in _commands(out) if " worktree remove --force " in c]
    assert world.tip() == before and world.worktrees() == 2


@pytest.mark.parametrize("failing", ["pre-commit", "post-checkout"])
def test_a_failure_after_the_worktree_is_added_is_reported_and_prints_no_push(world, failing):
    """A failing pre-commit stops harness record; a failing post-checkout fails the worktree add itself,
    after git has registered it, so that path prints the cleanup too."""
    hook = world.root / ".git" / "hooks" / failing
    hook.parent.mkdir(exist_ok=True)
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    before = world.snapshot()
    code, out = _record(world)
    assert code == 1 and out.splitlines()[-1].startswith("RECORD FAIL: ")
    assert not [c for c in _commands(out) if " push " in c]
    assert [c for c in _commands(out) if " worktree remove --force " in c]
    assert world.snapshot() == before


def _in_flight(w):
    w.append(_ev(ev="step", by="builder-1", owner="builder-1", step="s2", claim="s2 trims the wick",
                 scope=["src/*"], tests=["tests/test_lamp.py"], base=w.pushed, adopted=[]))


def _secret(w):
    w.append(_ev(ev="note", by="lead", kind="observation", text=f"carries {WORD}"))


def _no_commit_event(w):
    _write(w.root, REL, _opened(step=False))


def _rewritten_commit_event(w):
    _write(w.root, REL, _opened() + _tail(OTHER_SHA))


def _edited_tool(w):
    with open(w.cli, "ab") as fh:
        fh.write(b"# a local edit\n")


def _origin_moved(w):
    other = w.clone("other")
    _commit(w.env, other, {"src/oil.py": "OIL = 1\n"})
    _git(w.env, other, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")


def _another_runs_record(w):
    other = w.clone("other")
    _commit(w.env, other, {"docs/harness/runs/2026-01-02-other-run.jsonl": _ev(ev="open", by="lead") + "\n"})
    _git(w.env, other, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")


def _an_empty_commit(w):
    other = w.clone("other")
    _git(w.env, other, "commit", "-q", "--allow-empty", "-m", "fixture")
    _git(w.env, other, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")


def _a_cancelling_pair(w):
    other = w.clone("other")
    _commit(w.env, other, {"src/oil.py": "OIL = 1\n"})
    _git(w.env, other, "rm", "-q", "src/oil.py")
    _git(w.env, other, "commit", "-q", "-m", "fixture")
    _git(w.env, other, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")


def _ledger_behind_origin(w):
    other = w.clone("other")
    _commit(w.env, other, {REL: _opened() + _ev(ev="note", by="lead", kind="observation", text="only origin") + "\n"})
    _git(w.env, other, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")


def _nothing_new(w):
    _git(w.env, w.root, "add", REL)
    _git(w.env, w.root, "commit", "-q", "-m", "fixture")
    _git(w.env, w.root, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")


def _no_origin(w):
    _git(w.env, w.root, "remote", "remove", "origin")


REFUSALS = [
    ("a-step-in-flight", _in_flight, "in flight"),
    ("a-secret-in-the-ledger", _secret, "carries"),
    ("no-commit-in-the-run", _no_commit_event, "names no commit"),
    ("a-commit-origin-never-held", _rewritten_commit_event, "not at the run's last pushed commit"),
    ("an-edited-tool", _edited_tool, "differs from HEAD"),
    ("origin-moved-past-the-run", _origin_moved, "not at the run's last pushed commit"),
    ("another-runs-record-above", _another_runs_record, "not at the run's last pushed commit"),
    ("a-ledger-behind-origin", _ledger_behind_origin, "does not extend origin's"),
    ("nothing-new", _nothing_new, "nothing new"),
    ("no-origin", _no_origin, "origin's default branch cannot be read"),
]


@pytest.mark.parametrize("arrange,why", [r[1:] for r in REFUSALS], ids=[r[0] for r in REFUSALS])
def test_record_refuses_before_making_anything(world, arrange, why):
    arrange(world)
    before = world.snapshot()
    code, out = _record(world)
    assert code == 2 and out.startswith("REFUSED: ") and why in out
    assert WORD not in out                                                # a refusal never quotes the secret
    assert _commands(out) == [] and world.worktrees() == 1
    assert world.snapshot() == before


def test_record_refuses_an_absent_ledger_a_bad_run_id_and_an_absent_message(world):
    for run, why in (("2026-01-02-absent", "holds no ledger"), ("Not A Run", "not a harness run id")):
        code, out = _record(world, run=run)
        assert code == 2 and out.startswith("REFUSED: ") and why in out
    code, out = _record(world, "-F", str(world.root.parent / "absent.txt"))
    assert code == 2 and out.startswith("REFUSED: ") and "message file" in out
    assert world.worktrees() == 1


@pytest.mark.parametrize("where", ["a-subdirectory", "no-checkout"])
def test_record_refuses_a_root_that_is_not_the_top_of_a_checkout(world, where):
    root = world.root / "src" if where == "a-subdirectory" else world.root.parent / "home"
    code, out = _record(world, root=root)
    assert code == 2 and out.startswith("REFUSED: ") and "not the top of a git checkout" in out
    assert world.worktrees() == 1


def test_a_rebase_note_names_the_runs_last_pushed_commit(tmp_path, env):
    """A rebase keeps the ledger's commit events at their old shas; the rebase note's head is the new one."""
    w = _build(tmp_path, env)
    _write(w.root, REL, _opened() + _tail(OTHER_SHA))
    assert "not at the run's last pushed commit" in _record(w)[1]
    w.append(_ev(ev="note", by="lead", kind="rebase", text="rebased onto the tip", head=w.pushed))
    code, out = _record(w)
    assert code == 0 and out.splitlines()[-1].startswith("RECORD PASS: ")


def test_a_second_record_stands_on_the_first(world):
    """The run's own record commit is its last pushed commit: a later note is recorded on top of it."""
    _, out = _record(world)
    first = _git(world.env, _kept(out), "rev-parse", "HEAD")
    _run_printed(world, out)
    world.append(_ev(ev="note", by="lead", kind="observation", text="a note after the record"))
    code, out = _record(world)
    assert code == 0 and out.splitlines()[-1].startswith("RECORD PASS: ")
    assert _git(world.env, _kept(out), "rev-parse", "HEAD~1") == first == world.tip()
    _run_printed(world, out)
    assert _held(world)
    world.append(_ev(ev="note", by="lead", kind="observation", text="a third record stands on two"))
    code, out = _record(world)
    assert code == 0 and out.splitlines()[-1].startswith("RECORD PASS: ")


@pytest.mark.parametrize("arrange", [_origin_moved, _another_runs_record, _an_empty_commit, _a_cancelling_pair],
                         ids=["a-code-commit", "another-runs-record", "an-empty-commit", "a-cancelling-pair"])
def test_any_other_commit_above_a_record_is_not_the_runs_last_pushed_commit(world, arrange):
    _, out = _record(world)
    _run_printed(world, out)
    arrange(world)
    world.append(_ev(ev="note", by="lead", kind="observation", text="a note after the record"))
    code, out = _record(world)
    assert code == 2 and "not at the run's last pushed commit" in out


@pytest.mark.parametrize("holds_tools", [False, True], ids=["tracks-no-harness", "tracks-a-harness"])
def test_record_refuses_a_harness_that_differs_from_what_is_committed_beside_it(tmp_path, env, holds_tools):
    """Whatever harness record runs can do anything record says it will not: this edit pushes."""
    w = _build(tmp_path, env, holds_tools)
    beside = pathlib.Path(w.cli).with_name("harness.py")
    end_of_record = b"    return head(root)\n\n\ndef cmd_abandon"
    source = beside.read_bytes()
    assert source.count(end_of_record) == 1
    pushes = f'    _git(root, "push", "origin", "HEAD:refs/heads/{BRANCH}")\n'.encode()
    beside.write_bytes(source.replace(end_of_record, pushes + end_of_record))
    before = w.snapshot()
    code, out = _record(w)
    assert code == 2 and out.startswith("REFUSED: tools/harness.py differs from HEAD")
    assert _commands(out) == [] and w.worktrees() == 1
    assert w.snapshot() == before and w.tip() == w.pushed


def test_record_refuses_a_harness_that_is_not_committed_beside_it(tmp_path, env):
    w = _build(tmp_path, env, holds_tools=False)
    home = pathlib.Path(w.cli).parent.parent
    _git(env, home, "rm", "-q", "--cached", "tools/harness.py")
    _git(env, home, "commit", "-q", "-m", "fixture")
    code, out = _record(w)
    assert code == 2 and out.startswith("REFUSED: tools/harness.py is not committed")
    assert w.worktrees() == 1


def test_record_serves_a_repository_that_tracks_no_harness(tmp_path, env):
    w = _build(tmp_path, env, holds_tools=False)
    code, out = _record(w)
    assert code == 0 and out.splitlines()[-1].startswith("RECORD PASS: ")
    _run_printed(w, out)
    assert _held(w)


def test_record_takes_the_message_from_a_file(world):
    message = world.root.parent / "message.txt"
    message.write_text("The lamp's run is recorded\n", encoding="utf-8")
    code, out = _record(world, "-F", str(message))
    assert code == 0
    assert _git(world.env, _kept(out), "log", "-1", "--format=%s") == "The lamp's run is recorded"


# ------------------------------------------------------------------------------------- the filed want

def test_the_clock_want_is_filed_as_the_lead_filed_it():
    with open(os.path.join(ROOT, *cx.BACKLOG_REL.split("/")), encoding="utf-8") as fh:
        wants = {w.id: w for w in cx.parse_backlog(fh.read())}
    want = wants["schedule-clock-reads-old-runs-at-the-records-commit"]
    assert (want.status, want.scope, want.source.render()) == ("open", "concordance-2", "ORIGIN 2026-11-03 lead")
    text = " ".join(want.text.split())
    assert "done_problems" in text and "reviewed bootstrap" in text and "loud and safe" in text
