"""The harness grades by machine, and these tests pin every rule that makes it so (tools/harness.py).

Each rule here is one a well-meaning agent would otherwise bend under pressure: grading its own
step, editing after the check, passing a step whose tests never ran, a test that passes with the fix
taken away, an ignored file that only the checkout has, a baseline that quietly grows or stops being
true, an "every page" red hiding a second page, a step that edits the grader. Every test drives a
throwaway git repo, so nothing here touches the keeping or the real ledger.
"""
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import harness as h  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def _write(root, rel, text):
    full = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _commit_all(root, msg):
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg)


@pytest.fixture
def repo(tmp_path):
    root = str(tmp_path / "r")
    _write(root, "src/app.py", "VALUE = 1\n")
    _write(root, "tests/test_app.py", "import app\n\n\ndef test_value():\n    assert app.VALUE == 2\n")
    _write(root, "tests/MANIFEST.txt", "test_app.py\n")
    _write(root, "README.md", "a repo\n")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    _git(root, "config", "core.autocrlf", "false")
    _commit_all(root, "base")
    return root


def _planned(root, run="r1"):
    h.cmd_open(root, run, "VALUE is 2", ["pytest tests/test_app.py passes"])
    h.cmd_verdict(root, run, "plan", "checker-0", True, [])
    return run


def _stepped(root, run="r1", tests=("tests/test_app.py",), scope=("src/*",)):
    _planned(root, run)
    h.cmd_step(root, run, "s1", "builder-1", "VALUE becomes 2", list(scope), list(tests))
    return run


def _gate(root, run, role, by):
    return h.cmd_gate(root, run, "s1", role, by)


def _checked(root, run):
    assert _gate(root, run, "builder", "builder-1")[0]
    ok, ev = _gate(root, run, "checker", "checker-1")
    assert ok, ev["checks"]
    h.cmd_verdict(root, run, "s1", "checker-1", True, [])


def _msg(root, text="a step\n"):
    path = os.path.join(os.path.dirname(root), "msg.txt")
    _write(os.path.dirname(root), "msg.txt", text)
    return path


# ------------------------------------------------------------------------------ content hash

def test_the_content_hash_is_the_bytes_not_the_moment(repo):
    base = h.head(repo)
    assert h.changed_paths(repo, base) == []
    _write(repo, "src/app.py", "VALUE = 2\n")
    first = h.diff_hash(repo, base)
    assert len(first) == 64                                        # the full digest, never cut
    _write(repo, "src/app.py", "VALUE = 1\n")
    assert h.changed_paths(repo, base) == []
    _write(repo, "src/app.py", "VALUE = 2\n")
    assert h.diff_hash(repo, base) == first
    _write(repo, "src/app.py", "VALUE = 3\n")
    assert h.diff_hash(repo, base) != first
    _write(repo, "docs/harness/runs/x.jsonl", "{}\n")              # the ledger is never step content
    _write(repo, ".gate.lock", "123\n")
    assert h.changed_paths(repo, base) == ["src/app.py"]


# ------------------------------------------------------------------------- the cheap checks

def test_scope_forbidden_secrets_and_hygiene_are_mechanical(repo):
    assert not h.check_scope(["src/a.py", "tests/t.py"], ["src/*"])["ok"]
    assert h.check_scope(["src/a.py", "site/x/y.html"], ["src/*", "site/"])["ok"]

    base = h.head(repo)
    _write(repo, "data/new.jsonl", "{}\n")
    _write(repo, "data/sticks/a.json", "{}\n")
    assert not h.check_forbidden(repo, base, ["data/new.jsonl"], ["data/*"])["ok"]       # a NEW data file
    assert h.check_forbidden(repo, base, ["data/sticks/a.json"], ["data/sticks/*"])["ok"]
    assert not h.check_forbidden(repo, base, ["site/theories.html"], ["site/*"])["ok"]   # box-owned
    assert not h.check_forbidden(repo, base, ["data/domain_goldens.json"], ["data/*"])["ok"]

    key = "-----BEGIN " + "OPENSSH PRIVATE KEY-----"
    found = h.check_secrets({"x.py": [(1, "ok = 1"), (7, key)]})
    assert not found["ok"] and found["detail"] == ["x.py:7 carries a private key block"]  # never the value
    cred = "ELEVENLABS_API" + "_KEY = '" + "a1b2c3d4" * 4 + "'"
    assert h.secret_kind(cred) == "a credential assigned in source"
    assert h.secret_kind('DB_PASSWORD="Hq7$k2Lm9pQ4rT8vW1xZ"') == "a credential assigned in source"
    assert h.secret_kind("password = input()") is None
    assert h.secret_kind('api_token = "your-token-goes-here-0123456789"') is None        # a placeholder
    assert h.secret_kind('tokenizer_path = "models/vocab_2024_bpe_v2.json"') is None     # a path
    assert h.secret_kind('"receipt_token": "sha256:9f86d081884c7d659a2feaa0c55ad015"') is None
    assert h.secret_kind("digest = hashlib.sha256(password.encode()).hexdigest()") is None
    with open(os.path.join(repo, "wide.txt"), "wb") as fh:                               # UTF-16, no BOM
        fh.write(("note\n" + key + "\n").encode("utf-16-le"))
    wide = h.added_lines(repo, base, [], ["wide.txt"])
    assert not h.check_secrets(wide)["ok"]

    _write(repo, "a.py", "def f(:\n")
    _write(repo, "b.jsonl", '{"a": 1}\nnot json\n')
    bad = h.check_hygiene(repo, {"a.py": [(3, "x = 1 ")], "n.md": [(1, "hard break  ")],
                                 "c.py": [(9, "<" * 7 + " HEAD")]}, ["a.py", "b.jsonl"])
    text = " ".join(bad["detail"])
    assert "a.py:3: trailing whitespace" in text and "n.md" not in text
    assert "c.py:9: a conflict marker" in text and "does not compile" in text and "not valid JSON" in text


def test_added_lines_carry_their_real_line_numbers_and_ignore_diff_attributes(repo):
    base = h.head(repo)
    _write(repo, ".gitattributes", "*.py -diff\n")                 # would hide a binary-marked diff
    _commit_all(repo, "attributes")
    base = h.head(repo)
    _write(repo, "src/app.py", "VALUE = 1\n# one\n# two\nSECRETLINE\n")
    added = h.added_lines(repo, base, ["src/app.py"], [])
    assert added["src/app.py"] == [(2, "# one"), (3, "# two"), (4, "SECRETLINE")]


def test_a_step_never_edits_what_grades_it(repo):
    base = h.head(repo)
    assert not h.check_machinery(repo, base, ["tools/harness.py"])["ok"]
    assert not h.check_machinery(repo, base, ["tests/conftest.py"])["ok"]
    assert not h.check_machinery(repo, base, ["pyproject.toml"])["ok"]
    _write(repo, "tests/MANIFEST.txt", "test_app.py\ntest_more.py\n")                      # grows: fine
    assert h.check_machinery(repo, base, ["tests/MANIFEST.txt"])["ok"]
    _write(repo, "tests/MANIFEST.txt", "test_more.py\n")                                   # loses one
    assert not h.check_machinery(repo, base, ["tests/MANIFEST.txt"])["ok"]

    _write(repo, h.BASELINE_REL, "tests/a.py::t | aaaaaaaaaaaa\ntests/b.py::t | bbbbbbbbbbbb\n")
    _commit_all(repo, "baseline")
    base = h.head(repo)
    _write(repo, h.BASELINE_REL, "tests/a.py::t | aaaaaaaaaaaa\n")                         # shrinks: fine
    assert h.check_machinery(repo, base, [h.BASELINE_REL])["ok"]
    _write(repo, h.BASELINE_REL, "tests/a.py::t | aaaaaaaaaaaa\ntests/c.py::t | cccccccccccc\n")
    assert not h.check_machinery(repo, base, [h.BASELINE_REL])["ok"]                     # grows
    _write(repo, h.BASELINE_REL, "tests/a.py::t | 000000000000\n")
    assert not h.check_machinery(repo, base, [h.BASELINE_REL])["ok"]                     # altered


def test_a_step_cannot_slip_a_grader_in_under_another_name(repo):
    for p in ("tools/pytest.py", "tools/sitecustomize.py", "tools/fnmatch.py", "src/json/__init__.py",
              "pluggy.py", "tests/_pytest/__init__.py", "src/evil.pth"):
        _write(repo, p, "x = 1\n")
    found = h.check_shadowing(repo, ["tools/pytest.py", "tools/sitecustomize.py", "tools/fnmatch.py",
                                     "src/json/__init__.py", "pluggy.py", "tests/_pytest/__init__.py",
                                     "src/evil.pth"])
    assert not found["ok"] and len(found["detail"]) == 7
    _write(repo, "tools/my_helper.py", "x = 1\n")
    _write(repo, "site/index.html", "<p>\n")
    assert h.check_shadowing(repo, ["tools/my_helper.py", "site/index.html", "src/concordance/json.py"])["ok"]
    for d in ("tools", "site", "tests/_pytest", "src/json"):
        shutil.rmtree(os.path.join(repo, *d.split("/")))
    for f in ("pluggy.py", "src/evil.pth"):
        os.remove(os.path.join(repo, *f.split("/")))
    run = _stepped(repo, scope=("src/*", "tools/*"))
    _write(repo, "src/app.py", "VALUE = 2\n")
    _write(repo, "tools/pytest.py", "import sys\nsys.exit(0)\n")    # "every test passed"
    ok, ev = _gate(repo, run, "builder", "builder-1")
    assert not ok and not ev["checks"]["shadowing"]["ok"]


def test_the_junit_report_and_pytests_own_summary_must_agree():
    honest = h.Run(1, {"t::a": "failed", "t::b": "passed"}, {}, "1 failed, 1 passed in 0.10s", None)
    assert honest.disagreement() is None
    doctored = h.Run(1, {"t::a": "passed", "t::b": "passed"}, {}, "1 failed, 1 passed in 0.10s", None)
    assert "disagree" in doctored.disagreement()
    errs = h.Run(1, {"t::a": "error"}, {}, "2 errors in 0.10s", None)
    assert errs.disagreement() is None


# ---------------------------------------------------------------------------- who may do what

def test_no_step_opens_before_a_checker_passes_the_plan(repo):
    h.cmd_open(repo, "r1", "VALUE is 2", ["tests pass"])
    with pytest.raises(h.HarnessError, match="before a checker has passed the plan"):
        h.cmd_step(repo, "r1", "s1", "builder-1", "c", ["src/*"], ["tests/test_app.py"])
    for who in ("lead", "Lead", "planner", "builder-1"):
        with pytest.raises(h.HarnessError, match="not a checker"):
            h.cmd_verdict(repo, "r1", "plan", who, True, [])
    h.cmd_verdict(repo, "r1", "plan", "checker-0", True, [])
    h.cmd_step(repo, "r1", "s1", "builder-1", "c", ["src/*"], ["tests/test_app.py"])


def test_the_owner_never_grades_and_the_lead_never_owns_or_grades(repo):
    _planned(repo)
    with pytest.raises(h.HarnessError, match="never by the lead"):
        h.cmd_step(repo, "r1", "s1", "lead", "c", ["src/*"], ["tests/test_app.py"])
    h.cmd_step(repo, "r1", "s1", "builder-1", "c", ["src/*"], ["tests/test_app.py"])
    with pytest.raises(h.HarnessError, match="one step at a time"):
        h.cmd_step(repo, "r1", "s2", "builder-2", "c", ["src/*"], ["tests/test_app.py"])
    for who in ("builder-1", "lead", "Lead"):
        with pytest.raises(h.HarnessError, match="never grades"):
            _gate(repo, "r1", "checker", who)
        with pytest.raises(h.HarnessError, match="never grades"):
            h.cmd_verdict(repo, "r1", "s1", who, True, [])
    with pytest.raises(h.HarnessError, match="one owner per step"):
        _gate(repo, "r1", "builder", "builder-2")


def test_a_step_opens_on_a_clean_tree_unless_it_adopts_the_work_out_loud(repo):
    _planned(repo)
    _write(repo, "src/app.py", "VALUE = 2\n")
    with pytest.raises(h.HarnessError, match="clean tree"):
        h.cmd_step(repo, "r1", "s1", "builder-1", "c", ["src/*"], ["tests/test_app.py"])
    ev = h.cmd_step(repo, "r1", "s1", "builder-1", "c", ["src/*"], ["tests/test_app.py"], adopt=True)
    assert ev["adopted"] == ["src/app.py"]
    assert "adopted at open: src/app.py" in h.cmd_brief(repo, "r1", "s1")


def test_the_ledger_never_carries_a_secret(repo):
    _planned(repo)
    with pytest.raises(h.HarnessError, match="never carries a secret"):
        h.cmd_step(repo, "r1", "s1", "builder-1", "-----BEGIN " + "RSA PRIVATE KEY-----", ["src/*"],
                   ["tests/test_app.py"])
    h.cmd_step(repo, "r1", "s1", "builder-1", "VALUE becomes 2", ["src/*"], ["tests/test_app.py"])
    _write(repo, "src/app.py", "VALUE = 2\n")
    _checked(repo, "r1")
    h.cmd_close(repo, "r1", "s1")
    with open(h.Ledger(repo, "r1").path, "a", encoding="utf-8") as fh:      # a hand-added line
        fh.write('{"ev": "note", "text": "' + "-----BEGIN " + 'RSA PRIVATE KEY-----"}\n')
    with pytest.raises(h.HarnessError, match="carries a private key block"):
        h.cmd_commit(repo, "r1", "s1", _msg(repo))
    assert h._staged(repo) == []


# ------------------------------------------------------------------------------- the loop

def test_the_whole_loop_closes_and_commits_exactly_the_step(repo):
    run = _stepped(repo)
    ok, ev = _gate(repo, run, "builder", "builder-1")
    assert not ok and not ev["checks"]["content"]["ok"]          # nothing built yet: no step
    _write(repo, "src/app.py", "VALUE = 2\n")
    ok, ev = _gate(repo, run, "builder", "builder-1")
    assert ok, ev["checks"]
    ok, ev = _gate(repo, run, "checker", "checker-1")
    assert ok, ev["checks"]
    assert ev["full"] and ev["checks"]["pins"]["ok"] and ev["checks"]["suite"]["ok"]
    h.cmd_verdict(repo, run, "s1", "checker-1", True, [])
    h.cmd_close(repo, run, "s1")
    msg = _msg(repo, "VALUE becomes 2\n")
    # A change staged in the index while the working tree matches the base is invisible to the
    # content hash — and would ride into the commit. The commit refuses it by name.
    _write(repo, "README.md", "a staged stray\n")
    _git(repo, "add", "README.md")
    _write(repo, "README.md", "a repo\n")
    with pytest.raises(h.HarnessError, match="something else is staged: README.md"):
        h.cmd_commit(repo, run, "s1", msg)
    _git(repo, "reset", "-q", "--", "README.md")
    h.cmd_commit(repo, run, "s1", msg)
    shown = subprocess.run(["git", "show", "--name-only", "--format=", "HEAD"], cwd=repo,
                           capture_output=True, text=True).stdout.split()
    assert sorted(shown) == ["docs/harness/runs/r1.jsonl", "src/app.py"]
    assert h.Ledger(repo, run).state("s1") == "committed"


def test_a_commit_that_is_not_the_checked_step_takes_itself_back(repo):
    run = _stepped(repo)
    _write(repo, "src/app.py", "VALUE = 2\n")
    _checked(repo, run)
    h.cmd_close(repo, run, "s1")
    hook = os.path.join(repo, ".git", "hooks", "pre-commit")
    _write(repo, ".git/hooks/pre-commit", "#!/bin/sh\necho extra > extra.txt\ngit add extra.txt\n")
    os.chmod(hook, 0o755)
    base = h.head(repo)
    with pytest.raises(h.HarnessError, match="taken back"):
        h.cmd_commit(repo, run, "s1", _msg(repo))
    assert h.head(repo) == base and h.Ledger(repo, run).state("s1") == "closed"
    os.remove(hook)
    os.remove(os.path.join(repo, "extra.txt"))
    h.cmd_commit(repo, run, "s1", _msg(repo))


def test_one_byte_after_the_check_and_the_close_refuses(repo):
    run = _stepped(repo)
    _write(repo, "src/app.py", "VALUE = 2\n")
    _checked(repo, run)
    _write(repo, "src/app.py", "VALUE = 2  # tweaked after the check\n")
    with pytest.raises(h.HarnessError, match="close refused"):
        h.cmd_close(repo, run, "s1")


def test_a_fail_after_the_close_voids_it(repo):
    run = _stepped(repo)
    _write(repo, "src/app.py", "VALUE = 2\n")
    _checked(repo, run)
    h.cmd_close(repo, run, "s1")
    h.cmd_verdict(repo, run, "s1", "checker-2", False, ["found after the close"])
    assert h.Ledger(repo, run).state("s1") == "fixing"
    with pytest.raises(h.HarnessError, match="only a closed step commits"):
        h.cmd_commit(repo, run, "s1", _msg(repo))


def test_a_pass_rests_on_the_checkers_own_full_gate(repo):
    run = _stepped(repo)
    _write(repo, "src/app.py", "VALUE = 2\n")
    assert _gate(repo, run, "builder", "builder-1")[0]
    with pytest.raises(h.HarnessError, match="rests on a gate"):
        h.cmd_verdict(repo, run, "s1", "checker-1", True, [])
    assert _gate(repo, run, "checker", "checker-2")[0]
    with pytest.raises(h.HarnessError, match="rests on a gate"):     # checker-2 ran it, not checker-1
        h.cmd_verdict(repo, run, "s1", "checker-1", True, [])
    with pytest.raises(h.HarnessError, match="at least one finding"):
        h.cmd_verdict(repo, run, "s1", "checker-1", False, [])


def test_three_failed_verdicts_block_the_step_and_it_cannot_be_abandoned_to_reset(repo):
    run = _stepped(repo)
    _write(repo, "src/app.py", "VALUE = 2\n")
    for i in range(h.MAX_ROUNDS):
        h.cmd_verdict(repo, run, "s1", "checker-1", False, [f"finding {i}"])
    assert h.Ledger(repo, run).state("s1") == "BLOCKED"
    with pytest.raises(h.HarnessError, match="BLOCKED"):
        _gate(repo, run, "builder", "builder-1")
    _write(repo, "src/app.py", "VALUE = 1\n")
    with pytest.raises(h.HarnessError, match="waits for a human"):
        h.cmd_abandon(repo, run, "s1", "start over")
    with pytest.raises(h.HarnessError, match="BLOCKED and waits for a human"):       # nor a new run
        h.cmd_open(repo, "r2", "the same work again", ["tests pass"])
    h.cmd_abandon(repo, run, "s1", "a human decided", human=True)
    h.cmd_open(repo, "r2", "the same work again", ["tests pass"])


# ------------------------------------------------------------------- what the checker grades

def test_a_test_that_passes_without_the_fix_does_not_pin_it(repo):
    run = _stepped(repo, tests=("tests/test_trivial.py",), scope=("src/*", "tests/*"))
    _write(repo, "src/app.py", "VALUE = 2\n")
    _write(repo, "tests/test_trivial.py", "def test_nothing():\n    assert True\n")
    _write(repo, "tests/MANIFEST.txt", "test_app.py\ntest_trivial.py\n")
    assert _gate(repo, run, "builder", "builder-1")[0]
    ok, ev = _gate(repo, run, "checker", "checker-1")
    assert not ok and not ev["checks"]["pins"]["ok"]


def test_a_test_that_merely_skips_without_the_fix_does_not_pin_it(repo):
    run = _stepped(repo, tests=("tests/test_new.py",), scope=("src/*", "tests/*"))
    _write(repo, "src/newmod.py", "ANSWER = 42\n")
    _write(repo, "tests/test_new.py",
           "import pytest\n\nnewmod = pytest.importorskip('newmod')\n\n\ndef test_answer():\n"
           "    assert newmod.ANSWER == 42\n")
    _write(repo, "tests/MANIFEST.txt", "test_app.py\ntest_new.py\n")
    assert _gate(repo, run, "builder", "builder-1")[0]
    ok, ev = _gate(repo, run, "checker", "checker-1")
    assert not ok and not ev["checks"]["pins"]["ok"]                 # at base it skips: not red


def test_a_skipped_acceptance_test_proves_nothing(repo):
    run = _stepped(repo, tests=("tests/test_skips.py",), scope=("src/*", "tests/*"))
    _write(repo, "src/app.py", "VALUE = 2\n")
    _write(repo, "tests/test_skips.py",
           "import pytest\n\n\n@pytest.mark.skip(reason='needs the keeping')\ndef test_it():\n    pass\n")
    _write(repo, "tests/MANIFEST.txt", "test_app.py\ntest_skips.py\n")
    ok, ev = _gate(repo, run, "builder", "builder-1")
    assert not ok and "vacuous" in " ".join(ev["checks"]["tests"]["detail"])


def test_the_checker_grades_the_commit_to_be_not_the_checkout(repo):
    _write(repo, ".gitignore", "src/helper.py\n")
    _commit_all(repo, "ignore the helper")
    run = _stepped(repo)
    _write(repo, "src/helper.py", "VALUE = 2\n")                      # ignored: never committed
    _write(repo, "src/app.py", "from helper import VALUE  # noqa: F401\n")
    ok, ev = _gate(repo, run, "builder", "builder-1")                 # the checkout has the helper...
    assert not ok and not ev["checks"]["tests"]["ok"]                # ...the commit-to-be does not
    ok, ev = _gate(repo, run, "checker", "checker-1")
    assert not ok and not ev["checks"]["tests"]["ok"]


def test_nothing_one_stage_writes_reaches_the_next(repo):
    _write(repo, ".gitignore", "marker.txt\n")
    _commit_all(repo, "ignore the marker")
    run = _stepped(repo, tests=("tests/test_marker.py",), scope=("src/*", "tests/*"))
    _write(repo, "src/app.py", "VALUE = 1  # a 'fix' that changes nothing\n")
    _write(repo, "tests/test_marker.py",
           "import os\n\n\ndef test_marker():\n"
           "    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'marker.txt')\n"
           "    if not os.path.exists(p):\n"
           "        open(p, 'w').write('x')\n"
           "        assert False, 'red only on a first run'\n")
    _write(repo, "tests/MANIFEST.txt", "test_app.py\ntest_marker.py\n")
    for _ in range(2):                                             # every builder run starts fresh too
        assert not _gate(repo, run, "builder", "builder-1")[0]
    ok, ev = _gate(repo, run, "checker", "checker-1")
    assert ev["checks"]["pins"]["ok"]                              # the pin stage went red, wrote one
    assert not ok and not ev["checks"]["tests"]["ok"]              # the next stage never saw it


def test_the_ledger_is_recorded_only_when_no_step_is_in_flight(repo):
    run = _stepped(repo)
    _write(repo, "src/app.py", "VALUE = 2\n")
    _checked(repo, run)
    h.cmd_close(repo, run, "s1")
    with pytest.raises(h.HarnessError, match="in flight"):
        h.cmd_record(repo, run, _msg(repo))


def test_the_run_is_done_only_after_ship_and_a_live_verdict(repo):
    run = _stepped(repo)
    _write(repo, "src/app.py", "VALUE = 2\n")
    _checked(repo, run)
    h.cmd_close(repo, run, "s1")
    h.cmd_commit(repo, run, "s1", _msg(repo))
    L = h.Ledger(repo, run)
    assert any("no passing ship" in w for w in h.done_problems(repo, L))
    with pytest.raises(h.HarnessError, match="nothing has shipped"):
        h.cmd_verdict(repo, run, "live", "checker-2", True, [])
    with pytest.raises(h.HarnessError, match="only the lead ships"):
        h.cmd_note(repo, run, "checker-2", "ship", "deploy exit=0", True)
    h.cmd_note(repo, run, "lead", "ship", "deploy exit=0", True)
    with pytest.raises(h.HarnessError, match="never grades"):
        h.cmd_verdict(repo, run, "live", "lead", True, [])
    assert any("live verdict" in w for w in h.done_problems(repo, L))
    h.cmd_verdict(repo, run, "live", "checker-2", True, ["the doors answer"])
    assert h.done_problems(repo, L) == []
    h.cmd_note(repo, run, "lead", "ship", "a redeploy refused", False)   # a later failed ship reopens it
    assert any("no passing ship" in w for w in h.done_problems(repo, L))
    sha = h.cmd_record(repo, run, _msg(repo, "the ledger\n"))
    shown = subprocess.run(["git", "show", "--name-only", "--format=", sha], cwd=repo,
                           capture_output=True, text=True).stdout.split()
    assert shown == ["docs/harness/runs/r1.jsonl"]


# --------------------------------------------------------------------- the suite and its ids

def test_the_baseline_matches_exactly_and_only_shrinks():
    msg = {"tests/a.py::t1": "pages with no way home: ['gates.html']", "tests/b.py::t3": "boom"}
    fp1, fp3 = h.fingerprint(msg["tests/a.py::t1"]), h.fingerprint(msg["tests/b.py::t3"])
    base = f"tests/a.py::t1 | {fp1}\ntests/b.py::t3 | {fp3}\nvacuous tests/v.py::t\n"
    results = {"tests/a.py::t1": "failed", "tests/a.py::t2": "passed", "tests/b.py::t3": "error"}
    assert h.judge_suite(results, msg, {"tests/v.py::t"}, base, base) == []
    # the same aggregate test, now red for a SECOND page: it fails differently
    worse = dict(msg, **{"tests/a.py::t1": "pages with no way home: ['gates.html', 'new.html']"})
    assert any("DIFFERENTLY" in d for d in h.judge_suite(results, worse, {"tests/v.py::t"}, base, base))
    assert any("NEW red" in d for d in h.judge_suite(dict(results, **{"tests/a.py::t2": "failed"}),
                                                     msg, {"tests/v.py::t"}, base, base))
    fixed = dict(results, **{"tests/b.py::t3": "passed"})
    assert any("STALE baseline" in d for d in h.judge_suite(fixed, msg, {"tests/v.py::t"}, base, base))
    shrunk = f"tests/a.py::t1 | {fp1}\nvacuous tests/v.py::t\n"
    assert h.judge_suite(fixed, msg, {"tests/v.py::t"}, base, shrunk) == []
    assert any("NEW vacuous" in d for d in h.judge_suite(results, msg, {"tests/v.py::t", "tests/w.py::t"},
                                                         base, base))
    hidden = base + "tests/a.py::t2 | 000000000000\n"                # a step baselines its own new red
    assert any("baseline grew" in d for d in h.judge_suite(dict(results, **{"tests/a.py::t2": "failed"}),
                                                          msg, {"tests/v.py::t"}, base, hidden))


def test_a_baseline_id_may_hold_a_hash_or_a_bar():
    reds, vac = h.parse_baseline("tests/a.py::t[h#i] | 0123456789ab  # why\n"
                                 "tests/a.py::t[x|y] | abcdef012345\nvacuous tests/v.py::t[a#b]  # why\n"
                                 "a line that fits nothing\n")
    assert reds == {"tests/a.py::t[h#i]": "0123456789ab", "tests/a.py::t[x|y]": "abcdef012345",
                    "a line that fits nothing": ""}
    assert vac == {"tests/v.py::t[a#b]"}


def test_the_committed_baseline_is_well_formed():
    with open(os.path.join(h.ROOT, *h.BASELINE_REL.split("/")), encoding="utf-8") as fh:
        reds, vac = h.parse_baseline(fh.read())
    assert all(n.startswith("tests/") and "::" in n and len(fp) == 12 for n, fp in reds.items())
    assert all(n.startswith("tests/") and "::" in n for n in vac)


def test_the_command_line_refuses_out_loud(capsys):
    assert h.main(["done", "no-such-run-here"]) == 2
    assert "REFUSED" in capsys.readouterr().err
    assert h.main(["status", "Not A Valid Id"]) == 2


def test_a_streamed_failure_cannot_be_taken_back():
    ev = [b'{"ev": "hello", "token": "t0"}',
          b'{"ev": "collected", "ids": ["t.py::a", "t.py::b"]}',
          b'{"ev": "report", "id": "t.py::a", "when": "call", "outcome": "failed", "msg": "boom"}',
          b'{"ev": "report", "id": "t.py::a", "when": "call", "outcome": "passed"}',     # a forged retraction
          b'{"ev": "report", "id": "t.py::b", "when": "setup", "outcome": "skipped"}',
          b'{"ev": "finish", "status": 1}']
    s = h.parse_stream(ev, "t0")
    assert s.results == {"t.py::a": "failed", "t.py::b": "skipped"} and s.messages["t.py::a"] == "boom"
    assert s.problems == [] and s.status == 1
    assert any("never reported its finish" in p for p in h.parse_stream(ev[:3], "t0").problems)
    assert any("never reported" in p for p in h.parse_stream(ev[:3] + ev[-1:], "t0").problems)
    assert any("this run's token" in p for p in h.parse_stream(ev, "another").problems)  # connected first
    assert any("unreadable" in p for p in h.parse_stream(ev[:1] + [b'"stub"'] + ev[1:], "t0").problems)


def test_every_failure_inside_a_test_is_in_its_fingerprint():
    one = [b'{"ev": "hello", "token": "t"}',
           b'{"ev": "report", "id": "a", "when": "call", "outcome": "failed", "msg": "missing: [\'gates.html\']"}',
           b'{"ev": "finish", "status": 1}']
    two = one[:2] + [b'{"ev": "report", "id": "a", "when": "teardown", "outcome": "failed", "msg": "server did not stop"}'] + one[2:]
    m1, m2 = h.parse_stream(one, "t").messages["a"], h.parse_stream(two, "t").messages["a"]
    assert h.fingerprint(m1) != h.fingerprint(m2) and "missing" in m2
    assert h.parse_stream(two, "t").results["a"] == "error"
    assert h.fingerprint("bad \udcff bytes")                               # a lone surrogate hashes


def test_a_plugin_that_flips_a_report_cannot_hide_the_failure(tmp_path):
    root = str(tmp_path)
    _write(root, "tests/test_flip.py",
           "import pytest\n\n\nclass _Flip:\n    @pytest.hookimpl(hookwrapper=True)\n"
           "    def pytest_runtest_makereport(self, item, call):\n        outcome = yield\n"
           "        rep = outcome.get_result()\n        if rep.failed:\n            rep.outcome = 'passed'\n\n\n"
           "@pytest.fixture(autouse=True)\ndef _flip(pytestconfig):\n"
           "    if not pytestconfig.pluginmanager.has_plugin('flip'):\n"
           "        pytestconfig.pluginmanager.register(_Flip(), 'flip')\n\n\n"
           "def test_red():\n    assert False\n\n\n"
           "def test_patched(monkeypatch):\n    import json, socket\n"
           "    monkeypatch.setattr(json, 'dumps', lambda *a, **k: 1 / 0)\n"
           "    monkeypatch.setattr(socket.socket, 'sendall', lambda *a, **k: None)\n    assert False\n")
    run = h.run_pytest(root, ["tests"], 120)
    assert run.results["tests/test_flip.py::test_red"] == "failed"
    assert run.results["tests/test_flip.py::test_patched"] == "failed"
    assert "plugin from inside the tree" in (run.disagreement() or "")


def test_a_plugin_a_test_file_loads_is_refused_even_when_it_reaches_inside(tmp_path):
    root = str(tmp_path)
    # Replaces the report wholesale and clears the exception first: invisible to any reporter that
    # only looks at reports. Refused because of WHERE it comes from and WHAT it hooks.
    _write(root, "tests/flipper.py",
           "import pytest\nfrom _pytest.reports import TestReport\n\n\n@pytest.hookimpl(tryfirst=True)\n"
           "def pytest_runtest_makereport(item, call):\n    call.excinfo = None\n"
           "    return TestReport.from_item_and_call(item, call)\n")
    _write(root, "tests/test_v4.py", "pytest_plugins = ['flipper']\n\n\ndef test_red():\n    assert False\n")
    run = h.run_pytest(root, ["tests"], 120)
    assert "tests/flipper.py" in (run.disagreement() or "")
    # The stream itself says "passed" here; the grade fails only because every check consults the
    # stream's problems before its results. That order is load-bearing, so it is pinned.
    step = h.check_step_tests(root, ["tests/test_v4.py"])
    assert not step["ok"] and "tests/flipper.py" in " ".join(step["detail"])


def test_a_repeated_failure_is_counted_each_time():
    def stream(n):
        lines = [b'{"ev": "hello", "token": "t"}']
        lines += [b'{"ev": "report", "id": "a", "when": "call", "outcome": "failed", "msg": "no title"}'] * n
        return h.parse_stream(lines + [b'{"ev": "finish", "status": 1}'], "t").messages["a"]
    assert h.fingerprint(stream(1)) != h.fingerprint(stream(2))       # one bad page, then two


def test_a_grandchild_holding_the_output_does_not_lose_the_grade(tmp_path):
    root = str(tmp_path)
    _write(root, "tests/test_gc.py", "import subprocess, sys\n\n\ndef test_red(capsys):\n"
                                     "    with capsys.disabled():\n"
                                     "        subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(8)'],"
                                     " stdout=sys.stdout)\n    assert False\n")
    run = h.run_pytest(root, ["tests"], 120)
    assert run.results["tests/test_gc.py::test_red"] == "failed"


def test_a_lingering_thread_does_not_hold_the_grade(tmp_path, monkeypatch):
    monkeypatch.setattr(h, "LINGER_SECONDS", 2)
    root = str(tmp_path)
    _write(root, "tests/test_linger.py", "import threading, time\n\n\ndef test_red():\n"
                                         "    threading.Thread(target=time.sleep, args=(600,)).start()\n"
                                         "    assert False\n")
    t0 = __import__("time").monotonic()
    run = h.run_pytest(root, ["tests"], 300)
    assert __import__("time").monotonic() - t0 < 120
    assert run.results["tests/test_linger.py::test_red"] == "failed" and run.disagreement() is None


def test_a_lock_naming_no_real_process_holds_nothing():
    assert h._pid_alive(os.getpid())
    assert not h._pid_alive(2 ** 40) and not h._pid_alive(0) and not h._pid_alive(-3)


def test_a_run_cut_short_is_not_a_pass(tmp_path):
    root = str(tmp_path)
    _write(root, "tests/test_quit.py", "import os\n\n\ndef test_a():\n    pass\n\n\ndef test_b():\n"
                                       "    os._exit(0)\n\n\ndef test_c():\n    assert False\n")
    run = h.run_pytest(root, ["tests"], 120)
    assert "never reported its finish" in (run.disagreement() or "")


def test_an_exit_hook_cannot_rewrite_the_grade(repo):
    _write(repo, "tests/test_other.py", "import app\n\n\ndef test_other():\n    assert app.OTHER == 1\n")
    _write(repo, "src/app.py", "VALUE = 1\nOTHER = 1\n")
    _write(repo, "tests/MANIFEST.txt", "test_app.py\ntest_other.py\n")
    _write(repo, h.BASELINE_REL, "")
    _commit_all(repo, "a second test")
    run = _stepped(repo, scope=("src/*", "tests/*"))
    _write(repo, "src/app.py", "VALUE = 2\nOTHER = 0\n")                 # fixes one, breaks the other
    _write(repo, "tests/test_evil.py",
           "import atexit, sys\n\n\n@atexit.register\ndef _lie():\n"
           "    sys.stdout.write('\\n3 passed in 0.01s\\n')\n\n\ndef test_fine():\n    pass\n")
    _write(repo, "tests/MANIFEST.txt", "test_app.py\ntest_other.py\ntest_evil.py\n")
    assert _gate(repo, run, "builder", "builder-1")[0]                  # the builder runs only its own tests
    ok, ev = _gate(repo, run, "checker", "checker-1")
    assert not ok and not ev["checks"]["suite"]["ok"]
    assert "test_other" in " ".join(ev["checks"]["suite"]["detail"]) or \
        "tampered" in " ".join(ev["checks"]["suite"]["detail"])


def test_ids_split_and_vacuity_are_counted_per_argument():
    results = {"tests/x.py::a": "skipped", "tests/y.py::b": "passed", "tests/y.py::c[1]": "skipped"}
    assert h.vacuous(results, ["tests/x.py", "tests/y.py", "tests/y.py::c"]) == ["tests/x.py", "tests/y.py::c"]
    assert h.split_ids("tests/a.py::t[x,y],tests/b.py") == ["tests/a.py::t[x,y]", "tests/b.py"]
