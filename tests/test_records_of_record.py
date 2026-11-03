"""The records of record: docs/harness/RULES.md and BACKLOG.md, and `tools/context.py check`.

The real files are parsed, scanned and, for every pointer into this repository, resolved here. The
pointers into the other public repositories resolve only where their checkouts are, so `check` does
that on the lead's machine through the roots file. `check` itself is tested on fixture repositories
made in temporary directories, with invented names. A failing assertion prints counts or ids, never
a path, because the harness writes failing test ids into the public ledger.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
import context as cx  # noqa: E402

HAND_BRIEFS = os.path.join(ROOT, "tests", "fixtures", "hand_briefs")
NO_CONFIG = {"HARNESS_CONFIG_DIR": ""}


def _read(rel):
    with open(os.path.join(ROOT, *rel.split("/")), "rb") as fh:
        return fh.read().decode("utf-8")


RULES = cx.parse_rules(_read(cx.RULES_REL))
WANTS = cx.parse_backlog(_read(cx.BACKLOG_REL))
SELF = {cx.SELF_REPO: ROOT}


# ------------------------------------------------------------------------------- the real records

def test_rules_and_backlog_parse_with_unique_ids_and_fixed_statuses():
    assert len(RULES) >= 25 and len(WANTS) >= 30
    for entries in (RULES, WANTS):
        ids = [e.id for e in entries]
        assert len(ids) == len(set(ids))
        assert all(e.scope in cx.SCOPES for e in entries)
    assert {w.status for w in WANTS} <= set(cx.STATUSES)
    assert {r.source.kind for r in RULES} <= set(cx.RULE_SOURCES)
    assert {w.source.kind for w in WANTS} <= set(cx.WANT_SOURCES)


def test_the_rules_carry_the_public_repo_rule_and_the_backlog_its_violation():
    rule = {r.id: r for r in RULES}["public-repo"]
    assert rule.text == "Public repo: no secrets, no box details, none of the operator's private writings."
    assert (rule.source.kind, rule.source.repo, rule.source.path) == ("FILE", cx.SELF_REPO, "docs/HARNESS.md")
    want = {w.id: w for w in WANTS}["public-repo-rule-against-the-runbook"]
    assert want.status == "open" and (want.source.repo, want.source.path) == (cx.SELF_REPO, "docs/RUNBOOK.md")


@pytest.mark.parametrize("rel", [cx.RULES_REL, cx.BACKLOG_REL] + [
    "tests/fixtures/hand_briefs/" + f for f in sorted(os.listdir(HAND_BRIEFS))])
def test_the_scan_passes_on_the_records_and_the_hand_briefs(rel):
    assert cx.scan(_read(rel), cx.load_config(NO_CONFIG)) == []


def test_the_two_hand_briefs_are_the_fixtures():
    assert sorted(os.listdir(HAND_BRIEFS)) == ["builder-10_restate-registry.txt",
                                               "checker-28_restate-registry.txt"]


def _ours(kind):
    return [e for e in RULES + WANTS if e.source.kind == kind and e.source.repo == cx.SELF_REPO]


def _held(e):
    """Does this tree's copy of the pointer's ledger hold the line it names?"""
    lines = cx._ledger_lines(ROOT, e.source.run)
    return lines is not None and e.source.line <= len(lines)


def test_every_ledger_pointer_into_this_repo_resolves_and_its_rules_are_verbatim():
    ours = [e for e in _ours("LEDGER") if _held(e)]
    assert len(ours) >= 3
    unresolved = [e.id for e in ours if cx.resolve(e.source, SELF)]
    assert unresolved == []
    unquoted = [e.id for e in ours if isinstance(e, cx.Rule) and cx.verbatim(e, SELF)]
    assert unquoted == []


def test_a_ledger_pointer_past_this_trees_copy_names_a_ledger_this_tree_holds():
    # The harness commits a run's ledger beside each step, never as one of the step's paths, so a
    # gate's worktree holds the open run's ledger as of the step's base. A pointer to a later line of
    # it resolves in the checkout and at the pushed commit (check, and CI), not in that worktree.
    later = [e for e in _ours("LEDGER") if not _held(e)]
    assert [e.id for e in later if cx._ledger_lines(ROOT, e.source.run) is None] == []
    if later:
        pytest.skip(f"{len(later)} pointer(s) name lines that this tree's copy of their run's ledger does "
                    f"not hold yet; check and CI at the pushed commit resolve them")


def test_every_file_pointer_into_this_repo_resolves_at_its_commit_and_its_rules_are_verbatim():
    ours = _ours("FILE")
    assert len(ours) >= 10
    if cx._git(ROOT, "rev-parse", "--git-dir") is None:
        pytest.skip("this tree is not a git checkout, so no commit can be read")
    missing = {e.source.sha for e in ours if cx._git(ROOT, "cat-file", "-e", e.source.sha + "^{commit}") is None}
    shallow = (cx._git(ROOT, "rev-parse", "--is-shallow-repository") or b"").strip() == b"true"
    if missing and shallow:
        pytest.skip("a shallow clone holds only its own commit, not the commits these pointers name")
    unresolved = [e.id for e in ours if cx.resolve(e.source, SELF)]
    assert unresolved == []
    unquoted = [e.id for e in ours if isinstance(e, cx.Rule) and cx.verbatim(e, SELF)]
    assert unquoted == []


def test_owner_pointers_quote_the_rule_they_source():
    owned = [r for r in RULES if r.source.kind == "OWNER"]
    assert owned and all(cx.verbatim(r, {}) is None for r in owned)


# --------------------------------------------------------------------------- check, on fixtures

def _git(root, *args):
    subprocess.run(["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", "-c",
                    "core.autocrlf=false", *args], cwd=root, check=True, capture_output=True)


def _repo(root, files):
    os.makedirs(root)
    _git(root, "init", "-q")
    for rel, text in files.items():
        full = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "fixture")
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


LEDGER = '{"ev": "open", "by": "lead", "goal": "Keep the lamp lit at the gate."}\n{"ev": "note", "text": "a second event"}\n'
DOC = "# Invented doc\n\nThe gate stays shut after dark.\n"


def _rule(rid, source, text):
    return f"## {rid}\n- scope: all\n- source: {source}\n- check: it holds\n> {text}\n\n"


def _want(wid, source, status="open"):
    return f"## {wid}\n- status: {status}\n- scope: all\n- source: {source}\n> A want.\n\n"


@pytest.fixture
def fixture(tmp_path):
    """A concordance-2 stand-in, a witness stand-in and a configuration directory with a roots file."""
    wit = str(tmp_path / "wit")
    wsha = _repo(wit, {"docs/harness/runs/2026-01-02-wit-run.jsonl": LEDGER, "docs/NOTE.md": DOC})
    c2 = str(tmp_path / "c2")
    csha = _repo(c2, {"docs/harness/runs/2026-01-02-c2-run.jsonl": LEDGER, "docs/DOC.md": DOC})
    cfg = tmp_path / "cfg"
    cfg.mkdir()
    (cfg / "roots.txt").write_text(f"# invented roots\nwitness {wit}\nzorblax-notes {tmp_path / 'zr'}\n",
                                   encoding="utf-8")
    (cfg / "private_names.txt").write_text("zorblax-notes\n", encoding="utf-8")
    return {"c2": c2, "wit": wit, "csha": csha, "wsha": wsha, "cfg": str(cfg),
            "env": {"HARNESS_CONFIG_DIR": str(cfg)}}


def _records(f, rules, wants):
    for rel, text in ((cx.RULES_REL, rules), (cx.BACKLOG_REL, wants)):
        full = os.path.join(f["c2"], *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# Records (an invented fixture)\n\n" + text)


def _good(f):
    c, w = f["csha"], f["wsha"]
    rules = (_rule("c2-ledger", "LEDGER concordance-2 2026-01-02-c2-run 1", "Keep the lamp lit at the gate.")
             + _rule("c2-file", f'FILE concordance-2 docs/DOC.md {c} "stays shut"', "The gate stays shut after dark.")
             + _rule("wit-ledger", "LEDGER witness 2026-01-02-wit-run 2", "a second event")
             + _rule("wit-file", f'FILE witness docs/NOTE.md {w} "The gate"', "The gate stays shut")
             + _rule("owner-word", 'OWNER owner, chat, 2026-01-02 "keep it lit, always"', "keep it lit"))
    wants = _want("w-ledger", "LEDGER witness 2026-01-02-wit-run 1") + _want("w-origin", "ORIGIN 2026-01-02 lead", "done")
    return rules, wants


def test_check_passes_when_every_pointer_resolves_and_every_rule_is_verbatim(fixture):
    _records(fixture, *_good(fixture))
    code, out = cx.check(fixture["c2"], fixture["env"])
    assert code == 0
    assert out[0] == "config: HARNESS_CONFIG_DIR (the override)"
    assert "  private names: 1" in out and "  roots: 2 repo(s); public: witness" in out
    assert [ln for ln in out if ln.startswith("BY KIND")] == [
        'BY KIND docs/harness/RULES.md owner-word: OWNER owner, chat, 2026-01-02 "keep it lit, always" '
        '(unresolvable by kind)',
        "BY KIND docs/harness/BACKLOG.md w-origin: ORIGIN 2026-01-02 lead (unresolvable by kind)"]
    assert out[-1] == "CHECK PASS: 0 unresolved; 5 pointer(s) resolved, 2 unresolvable by kind, 5 rule(s) verbatim"
    assert not any("zorblax" in ln for ln in out)


def test_check_prints_every_pointer_that_does_not_resolve_and_every_rule_not_verbatim(fixture):
    c, w = fixture["csha"], fixture["wsha"]
    other = "f" * 40
    rules = (_rule("anchor-absent", f'FILE concordance-2 docs/DOC.md {c} "stays open"', "x")
             + _rule("commit-absent", f'FILE witness docs/NOTE.md {other} "The gate"', "x")
             + _rule("file-absent", f'FILE witness docs/GONE.md {w} "The gate"', "x")
             + _rule("line-past-the-end", "LEDGER witness 2026-01-02-wit-run 3", "x")
             + _rule("run-absent", "LEDGER witness 2026-01-02-no-such-run 1", "x")
             + _rule("repo-not-in-roots", "LEDGER Concordance-V3 2026-01-02-v3-run 1", "x")
             + _rule("not-verbatim", "LEDGER concordance-2 2026-01-02-c2-run 1", "Keep the lamp dark.")
             + _rule("owner-not-verbatim", 'OWNER owner, chat, 2026-01-02 "keep it lit"', "keep it dark"))
    _records(fixture, rules, _want("fine", "LEDGER witness 2026-01-02-wit-run 1"))
    code, out = cx.check(fixture["c2"], fixture["env"])
    assert code == 1
    got = {ln.split(":")[0].split(" ")[-1]: ln.rsplit(" - ", 1)[-1] for ln in out if ln.startswith("UNRESOLVED")}
    assert got == {
        "anchor-absent": "the anchor does not occur in the file at that commit",
        "commit-absent": "the commit is not in this checkout",
        "file-absent": "the file does not exist at that commit",
        "line-past-the-end": "the ledger has 2 line(s)",
        "run-absent": "the checkout holds no ledger for this run",
        "repo-not-in-roots": "the roots file names no checkout for this repository"}
    assert [ln for ln in out if ln.startswith("NOT VERBATIM")] == [
        "NOT VERBATIM docs/harness/RULES.md not-verbatim: its text is not verbatim in its source",
        "NOT VERBATIM docs/harness/RULES.md owner-not-verbatim: its text is not verbatim in its source"]
    assert out[-1] == ("CHECK FAIL: 8 problem(s); 2 pointer(s) resolved, 1 unresolvable by kind, "
                       "0 rule(s) verbatim")


def test_check_names_a_scan_hit_by_line_only_and_never_prints_the_private_word(fixture):
    rules, wants = _good(fixture)
    wants += "## zorblax-notes-want\n- status: open\n- scope: all\n- source: ORIGIN 2026-01-02 lead\n> A want.\n"
    _records(fixture, rules, wants)
    code, out = cx.check(fixture["c2"], fixture["env"])
    assert code == 1
    assert "SCAN docs/harness/BACKLOG.md line 15: a private name" in out
    assert "BY KIND docs/harness/BACKLOG.md line 15: (withheld: the scan hits this entry) (unresolvable by kind)" in out
    assert not any("zorblax" in ln for ln in out)


def test_check_says_none_when_there_is_no_configuration_directory(fixture):
    _records(fixture, *_good(fixture))
    code, out = cx.check(fixture["c2"], NO_CONFIG)
    assert out[:3] == ["config: none (HARNESS_CONFIG_DIR is set but empty)",
                       "  private names: 0 (the scan can reject no private name)",
                       f"  secret patterns: {len(cx.harness.SECRET_PATTERNS)} built in, 0 local"]
    assert code == 1 and any(ln.startswith("UNRESOLVED docs/harness/RULES.md wit-ledger:") for ln in out)


def test_check_refuses_unreadable_records_and_a_malformed_roots_file(fixture):
    code, out = cx.check(fixture["c2"], fixture["env"])
    assert code == 1 and "MISSING docs/harness/RULES.md" in out
    _records(fixture, "## Bad Id\n", "")
    code, out = cx.check(fixture["c2"], fixture["env"])
    assert code == 1 and any(ln.startswith("PARSE docs/harness/RULES.md line 3:") for ln in out)
    with open(os.path.join(fixture["cfg"], "roots.txt"), "a", encoding="utf-8") as fh:
        fh.write("witness elsewhere\n")
    code, out = cx.check(fixture["c2"], fixture["env"])
    assert code == 2 and out[0].startswith("REFUSED")


def test_the_roots_file_format(tmp_path):
    d = tmp_path / "cfg"
    d.mkdir()
    a, b = str(tmp_path / "a dir with spaces"), str(tmp_path / "b")
    (d / "roots.txt").write_text(f"# comment\n\nwitness   {a}\nConcordance-V3 {b}\n", encoding="utf-8")
    assert cx.load_roots(str(d)) == {"witness": a, "Concordance-V3": b}
    assert cx.load_roots(str(tmp_path / "absent")) == {} and cx.load_roots(None) == {}
    for bad, line in ((f"witness {a}\nwitness {b}\n", 2), ("witness relative/path\n", 1), ("witness\n", 1),
                      (f"-bad {a}\n", 1)):
        (d / "roots.txt").write_text(bad, encoding="utf-8")
        with pytest.raises(cx.RecordsError) as e:
            cx.load_roots(str(d))
        assert [p.split(":")[0] for p in e.value.problems] == [f"roots.txt line {line}"]
        assert str(tmp_path) not in str(e.value)


# Runs `check` in a child process with every open and directory listing recorded (Python's audit
# events), the override set and the home directory pointed at a planted stand-in.
_PROBE = r"""
import json, os, sys
seen = []
def _hook(event, args):
    if event in ("open", "os.listdir", "os.scandir") and args:
        p = args[0]
        if isinstance(p, (str, bytes, os.PathLike)):
            seen.append(os.path.abspath(os.fsdecode(p)))
sys.addaudithook(_hook)
sys.path.insert(0, sys.argv[1])
import context
code, out = context.check(sys.argv[2])
sys.stdout.write(json.dumps({"seen": seen, "code": code, "out": out}))
"""


def _under(path, root):
    path, root = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(root))
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def test_check_never_opens_the_real_configuration_directory_under_the_override(fixture, tmp_path):
    _records(fixture, *_good(fixture))
    real = os.path.join(os.path.expanduser("~"), ".config", "harness")
    home = tmp_path / "home"
    planted = home / ".config" / "harness"
    planted.mkdir(parents=True)
    (planted / "roots.txt").write_text("witness " + str(tmp_path / "nowhere") + "\n", encoding="utf-8")
    env = dict(os.environ)
    env.update({"HOME": str(home), "USERPROFILE": str(home), "HARNESS_CONFIG_DIR": fixture["cfg"],
                "HARNESS_SECRET_PATTERNS": os.path.join(fixture["cfg"], "secret_patterns.txt")})
    r = subprocess.run([sys.executable, "-I", "-B", "-c", _PROBE, TOOLS, fixture["c2"]], cwd=str(tmp_path),
                       env=env, capture_output=True, timeout=300)
    last = (r.stderr.decode("utf-8", "replace").strip().splitlines() or [""])[-1]
    assert r.returncode == 0, "the probe failed: " + last.split(":")[0][:80]
    got = json.loads(r.stdout.decode("utf-8"))
    n_real = sum(_under(p, real) for p in got["seen"])
    n_planted = sum(_under(p, str(planted)) for p in got["seen"])
    read = sorted({os.path.basename(p) for p in got["seen"] if _under(p, fixture["cfg"])})
    assert n_real == 0, "the real configuration directory was opened"
    assert n_planted == 0, "the home configuration directory was opened under the override"
    assert read == ["private_names.txt", "roots.txt", "secret_patterns.txt"]
    assert got["code"] == 0 and got["out"][-1].startswith("CHECK PASS")


def test_the_command_line_prints_the_check_and_exits_with_its_code(fixture):
    _records(fixture, *_good(fixture))
    env = dict(os.environ, HARNESS_CONFIG_DIR=fixture["cfg"])
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "context.py"), "check", fixture["c2"]],
                       env=env, capture_output=True, timeout=300)
    lines = r.stdout.decode("utf-8").splitlines()
    assert r.returncode == 0 and lines[0] == "config: HARNESS_CONFIG_DIR (the override)"
    assert lines[-1].startswith("CHECK PASS: 0 unresolved")
