"""`tools/context.py brief`: a role's working context, assembled from records and nothing else.

brief refuses to run from an uncommitted tools/context.py, so every test here builds fixture
repositories in a temporary directory, commits this checkout's tools/context.py and tools/harness.py
into a concordance-2 stand-in, and runs that committed copy in a subprocess. Commit dates are fixed,
so identical records give identical commits. Every name is invented; a failing assertion prints ids
or counts, never a path, because the harness writes failing test ids into the public ledger.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
import context as cx  # noqa: E402
import harness as h  # noqa: E402

FIXED = {"GIT_AUTHOR_DATE": "2026-01-02T03:04:05+00:00", "GIT_COMMITTER_DATE": "2026-01-02T03:04:05+00:00",
         "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
         "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
RUN, RUN2, V3RUN, ZRUN = "2026-01-02-lamp", "2026-01-02-gate", "2026-01-02-v3-run", "2026-01-02-zr-run"
SHA_RX = re.compile(r"\b[0-9a-f]{40}\b")


def _src(rel):
    with open(os.path.join(ROOT, *rel.split("/")), "rb") as fh:
        return fh.read().replace(b"\r\n", b"\n")


def _git(root, *args):
    r = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "init.defaultBranch=main", *args],
                       cwd=root, env={**os.environ, **FIXED}, check=True, capture_output=True)
    return r.stdout.decode().strip()


def _write(root, rel, data):
    full = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))


def _commit(root, files, msg="fixture"):
    for rel, data in files.items():
        _write(root, rel, data)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg)
    return _git(root, "rev-parse", "HEAD")


def _ev(**e):
    return json.dumps({"ts": "2026-01-02T03:04:05+00:00", **e}, sort_keys=True)


def _ledger(base, goal="Keep the lamp lit at the gate.", done=("the lamp is lit",), claim="s1 lights the lamp",
            step="s1", finding="the wick is short"):
    return "\n".join([
        _ev(ev="open", by="lead", head=base),
        _ev(ev="plan", by="lead", goal=goal, done=list(done)),
        _ev(ev="verdict", by="checker-1", step="plan", findings=[], **{"pass": True}),
        _ev(ev="step", by="builder-1", owner="builder-1", step=step, claim=claim, scope=["src/*"],
            tests=["tests/test_lamp.py"], base=base, adopted=[]),
        _ev(ev="gate", by="builder-1", step=step, role="builder", diff="0" * 64, paths=[], full=False,
            checks={}, **{"pass": True}),
        _ev(ev="verdict", by="checker-2", step=step, findings=[finding], **{"pass": False}),
        _ev(ev="note", by="builder-1", kind="correction", text="builder narrative about a zebra"),
    ]) + "\n"


def _rules(sha1, order=1, eol="\n"):
    entries = [
        ("keep-the-lamp-lit", "all", 'OWNER owner, chat, 2026-01-02 "keep the lamp lit"', "Keep the lamp lit."),
        ("the-gate-stays-shut", "all", f'FILE concordance-2 docs/DOC.md {sha1} "stays shut"',
         "The gate stays shut\nafter dark."),
        ("c2-only-rule", "concordance-2", f"LEDGER concordance-2 {RUN} 2", "Keep the lamp lit at the gate."),
        ("v3-only-rule", "Concordance-V3", f"LEDGER Concordance-V3 {V3RUN} 1", "A rule for V3 only."),
        ("anchor-gone", "all", f'FILE concordance-2 docs/DOC.md {sha1} "no such words"', "Words not there."),
    ]
    body = ["".join(f"## {i}\n- scope: {s}\n- source: {p}\n- check: it holds\n"
                    + "".join(f"> {ln}\n" for ln in t.split("\n")) + "\n") for i, s, p, t in entries]
    if order != 1:
        body.reverse()
    return ("# Rules (an invented fixture)\n\n" + "".join(body)).replace("\n", eol)


def _backlog(order=1, eol="\n"):
    entries = [
        ("w-run", "open", "all", f"LEDGER concordance-2 {RUN} 2", "Trim the wick of this run."),
        ("w-c2", "open", "concordance-2", "ORIGIN 2026-01-02 lead", "Oil the hinge of the c2 gate."),
        ("w-v3", "open", "Concordance-V3", "ORIGIN 2026-01-02 lead", "Paint the V3 fence."),
        ("w-done", "done", "all", "ORIGIN 2026-01-02 lead", "A want already done."),
        ("w-all", "filed-as-run", "all", "ORIGIN 2026-01-02 lead", "Sweep every porch."),
    ]
    body = [f"## {i}\n- status: {st}\n- scope: {sc}\n- source: {p}\n> {t}\n\n" for i, st, sc, p, t in entries]
    if order != 1:
        body.reverse()
    return ("# Backlog (an invented fixture)\n\n" + "".join(body)).replace("\n", eol)


def _setup(base, order=1, eol="\n", names="", goal="Keep the lamp lit at the gate.", done=("the lamp is lit",),
           claim="s1 lights the lamp", finding="the wick is short"):
    """A concordance-2 stand-in (two runs), a V3 stand-in, a private repo, and a configuration dir."""
    c2 = os.path.join(base, "c2")
    os.makedirs(c2)
    _git(c2, "init", "-q")
    sha1 = _commit(c2, {"tools/context.py": _src("tools/context.py"), "tools/harness.py": _src("tools/harness.py"),
                        "docs/DOC.md": "# Invented doc\n\nThe gate stays shut after dark.\n"})
    sha2 = _commit(c2, {cx.RULES_REL: _rules(sha1, order, eol), cx.BACKLOG_REL: _backlog(order, eol)}, "records")
    _write(c2, f"docs/harness/runs/{RUN}.jsonl", _ledger(sha2, goal, done, claim, finding=finding))
    _write(c2, f"docs/harness/runs/{RUN2}.jsonl", _ledger(sha2, "Shut the gate.", ("it is shut",), "t1 shuts it", "t1"))
    v3 = os.path.join(base, "v3")
    os.makedirs(v3)
    _git(v3, "init", "-q")
    _commit(v3, {"README.md": "v3\n"})
    _write(v3, f"docs/harness/runs/{V3RUN}.jsonl", _ledger("0" * 40, "A V3 goal.", ("v3 done",), "v1 does it", "v1"))
    zr = os.path.join(base, "zr")
    os.makedirs(zr)
    _write(zr, f"docs/harness/runs/{ZRUN}.jsonl", _ledger("0" * 40, "A private goal.", ("p",), "z1", "z1"))
    cfg = os.path.join(base, "cfg")
    _write(cfg, "roots.txt", f"Concordance-V3 {v3}\nzorblax-notes {zr}\n")
    _write(cfg, "private_names.txt", names)
    return {"base": base, "c2": c2, "v3": v3, "zr": zr, "cfg": cfg, "sha1": sha1, "sha2": sha2}


def _brief(s, role, root, run, step=None, *extra, cfg=None):
    args = [sys.executable, "-B", os.path.join(s["c2"], "tools", "context.py"), "brief", "--role", role, *extra,
            root, run] + ([step] if step else [])
    r = subprocess.run(args, env={**os.environ, "HARNESS_CONFIG_DIR": cfg or s["cfg"]}, capture_output=True,
                       timeout=300)
    return r.returncode, r.stdout.decode("utf-8"), r.stderr.decode("utf-8")


def _section(out, name):
    assert out.endswith("\n") and not out.endswith("\n\n") and "\r" not in out      # LF lines, one final newline
    lines = out[:-1].split("\n")
    start = next(i for i, ln in enumerate(lines) if ln.startswith("== " + name))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("== ")), len(lines))
    return lines[start:end]


@pytest.fixture(scope="module")
def std(tmp_path_factory):
    return _setup(str(tmp_path_factory.mktemp("std")))


# ---------------------------------------------------------------------------------------- the tests

def test_identical_records_give_identical_bytes_wherever_they_live(tmp_path):
    a, b = _setup(str(tmp_path / "a")), _setup(str(tmp_path / "b"))
    assert a["sha2"] == b["sha2"]                              # fixed dates: the same records, the same commit
    for role, step in (("builder", "s1"), ("checker", "s1"), ("lead", None)):
        ra, oa, _ = _brief(a, role, a["c2"], RUN, step)
        rb, ob, _ = _brief(b, role, b["c2"], RUN, step)
        assert (ra, rb) == (0, 0)
        assert oa == ob                                        # no path, no clock: only records
        assert _brief(a, role, a["c2"], RUN, step)[1] == oa    # and again, the same bytes


def test_the_brief_names_its_commit_and_reads_the_records_from_it_never_the_working_copy(tmp_path):
    s = _setup(str(tmp_path))
    _write(s["c2"], cx.RULES_REL, _rules(s["sha1"]) + "## added-uncommitted\n- scope: all\n- source: "
           'OWNER owner, chat, 2026-01-02 "not of record"\n- check: c\n> not of record\n')
    rc, out, _ = _brief(s, "builder", s["c2"], RUN, "s1")
    assert rc == 0 and "added-uncommitted" not in out
    assert out.split("\n")[1].startswith(f"records: concordance-2 {s['sha2']} (the step's base")
    later = _commit(s["c2"], {cx.RULES_REL: _rules(s["sha1"]) + "## added-later\n- scope: all\n- source: OWNER "
                              'owner, chat, 2026-01-02 "added later"\n- check: c\n> added later\n'}, "later")
    rc, out, _ = _brief(s, "builder", s["c2"], RUN, "s1")
    assert rc == 0 and "added-later" not in out                # the step's base: no step changes its brief
    rc, out, _ = _brief(s, "lead", s["c2"], RUN)
    assert rc == 0 and "RULE added-later (all): " in out
    assert out.split("\n")[1].startswith(f"records: concordance-2 {later} (concordance-2's HEAD)")


def test_core_is_byte_identical_for_two_runs_of_one_scope(std):
    cores = [_section(_brief(std, role, std["c2"], run, step)[1], "CORE")
             for role, run, step in (("builder", RUN, "s1"), ("checker", RUN2, "t1"), ("lead", RUN2, None))]
    assert cores[0] == cores[1] == cores[2]
    assert [ln.split(" (")[0] for ln in cores[0][1:]] == [
        "RULE anchor-gone", "RULE c2-only-rule", "RULE keep-the-lamp-lit", "RULE the-gate-stays-shut"]


def test_reordered_entries_and_switched_line_endings_change_nothing_but_the_commit(tmp_path):
    outs = []
    for name, order, eol in (("lf", 1, "\n"), ("crlf-reversed", 2, "\r\n"), ("lf-reversed", 2, "\n")):
        s = _setup(str(tmp_path / name), order, eol)
        rc, out, _ = _brief(s, "builder", s["c2"], RUN, "s1")
        assert rc == 0
        outs.append(out.replace(s["sha2"], "<records>"))
    assert outs[0] == outs[1] == outs[2]


def test_the_wants_cap_never_shortens_core(std):
    full = _brief(std, "builder", std["c2"], RUN, "s1", "--wants-cap", "100000")[1]
    none = _brief(std, "builder", std["c2"], RUN, "s1", "--wants-cap", "0")[1]
    assert _section(full, "CORE") == _section(none, "CORE") == _section(_brief(std, "builder", std["c2"], RUN,
                                                                               "s1")[1], "CORE")
    wf, wn = _section(full, "WANTS")[1:], _section(none, "WANTS")[1:]
    assert [ln.split(" ")[1] for ln in wf] == [ln.split(" ")[1] for ln in wn] == ["w-run", "w-c2", "w-all"]
    assert all("): " in ln for ln in wf) and not any("): " in ln for ln in wn)
    assert wn[0] == f"WANT w-run (open, all) [LEDGER concordance-2 {RUN} 2]"


def test_a_plan_naming_a_home_path_and_loopback_still_yields_a_brief_with_those_lines_as_pointers(tmp_path):
    s = _setup(str(tmp_path), goal="Serve the lamp on 127.0.0.1 for now.",
               done=("it runs from /home/someone/lamp on the box", "a plain criterion"))
    for role in ("builder", "checker", "lead"):
        rc, out, err = _brief(s, role, s["c2"], RUN, None if role == "lead" else "s1")
        assert rc == 0, err.split(":")[0]
        assert "127.0.0.1" not in out and "/home/" not in out
        assert f"done when: {cx._WITHHELD} [LEDGER concordance-2 {RUN} 2]" in out
        assert f"done when: a plain criterion [LEDGER concordance-2 {RUN} 2]" in out


def test_an_invented_private_name_refuses_naming_the_line_and_kind_only(tmp_path):
    s = _setup(str(tmp_path), names="quillfeather\n", claim="s1 sends the lamp to quillfeather")
    rc, out, err = _brief(s, "builder", s["c2"], RUN, "s1")
    assert rc == 2 and out == ""
    assert re.fullmatch(r"REFUSED: line \d+ carries a private name\s*", err)
    assert "quillfeather" not in err.lower()


def test_a_private_repo_in_the_roots_file_never_reaches_a_brief(std):
    for role, root, run, step in (("builder", std["c2"], RUN, "s1"), ("lead", std["v3"], V3RUN, None)):
        rc, out, _ = _brief(std, role, root, run, step)
        assert rc == 0
        assert "zorblax" not in out and ZRUN not in out and "z1" not in out.split()


def test_in_flight_lists_open_steps_of_the_public_repos_only(std):
    rc, out, _ = _brief(std, "lead", std["c2"], RUN)
    assert rc == 0
    assert _section(out, "IN FLIGHT")[1:] == [
        f"concordance-2 {RUN2} t1: owner builder-1, state fixing [LEDGER concordance-2 {RUN2} 4]",
        f"concordance-2 {RUN} s1: owner builder-1, state fixing [LEDGER concordance-2 {RUN} 4]",
        f"Concordance-V3 {V3RUN} v1: owner builder-1, state fixing [LEDGER Concordance-V3 {V3RUN} 4]",
        "not located: witness (no checkout in the roots file)"]


def test_a_run_in_another_repo_is_briefed_from_concordance_2_head(std):
    rc, out, _ = _brief(std, "builder", std["v3"], V3RUN, "v1")
    assert rc == 0
    lines = out.split("\n")
    assert lines[0] == f"BRIEF for the builder of run {V3RUN} in Concordance-V3, step v1"
    assert lines[1].startswith(f"records: concordance-2 {std['sha2']} (concordance-2's HEAD)")
    assert [ln.split(" (")[0] for ln in _section(out, "CORE")[1:]] == [
        "RULE anchor-gone", "RULE keep-the-lamp-lit", "RULE the-gate-stays-shut", "RULE v3-only-rule"]
    assert f"claim: v1 does it [LEDGER Concordance-V3 {V3RUN} 4]" in lines


def test_the_checker_gets_cmd_brief_and_no_builders_narrative(std):
    rc, out, _ = _brief(std, "checker", std["c2"], RUN, "s1")
    assert rc == 0
    lines = out.split("\n")
    want = h.cmd_brief(std["c2"], RUN, "s1").split("\n")
    missing = [i for i, w in enumerate(want) if not any(ln.startswith(w + " [") for ln in lines)]
    assert missing == []
    assert f"previous finding: the wick is short [LEDGER concordance-2 {RUN} 6]" in lines
    assert "zebra" not in out
    built = _brief(std, "builder", std["c2"], RUN, "s1")[1]
    assert "zebra" not in built and "content hash now" not in built
    assert f"claim: s1 lights the lamp [LEDGER concordance-2 {RUN} 4]" in built.split("\n")


def _pointered(out):
    """Every line of CORE, IN FLIGHT, RUN and WANTS ends with a pointer that the grammar parses."""
    quoted = [ln for name in ("CORE", "IN FLIGHT", "RUN", "WANTS", "DUE")
              for ln in _section(out, name)[1:] if not ln.startswith(("not located:", "none"))
              and not ln.endswith(": no run completed")]
    for ln in quoted:
        assert ln.endswith("]")
        p = ln[ln.rindex(" [") + 2:-1].removeprefix("UNRESOLVED: ")
        p = p.split(" - ")[0] if " - the" in p else p.removesuffix(" (unresolvable by kind)")
        cx.parse_pointer(p)
    return quoted


def test_every_quoted_line_names_its_pointer_and_an_unresolved_one_is_printed_never_dropped(std):
    rc, out, _ = _brief(std, "builder", std["c2"], RUN, "s1")
    assert rc == 0
    assert len(_pointered(out)) >= 12
    gone = [ln for ln in _section(out, "CORE") if ln.startswith("RULE anchor-gone ")]
    assert gone == [f'RULE anchor-gone (all): Words not there. | check: it holds [UNRESOLVED: FILE concordance-2 '
                    f'docs/DOC.md {std["sha1"]} "no such words" - the anchor does not occur in the file at that commit]']
    assert "RULE the-gate-stays-shut (all): The gate stays shut after dark. | check: it holds [FILE" in out
    assert "(unresolvable by kind)]" in out
    assert _section(out, "DUE") == [
        "== DUE: 0 of 4 rule(s) in scope are due; intervals 1, 2, 3, 5, 8, ... runs; a rule never confirmed is "
        "first due within 13 runs of its entry",
        "clock all: no run completed", "clock concordance-2: no run completed"]


@pytest.mark.parametrize("second", ["and trims the wick", "served from /home/someone/lamp"],
                         ids=["plain-second-line", "path-on-the-second-line"])
def test_a_line_break_in_a_claim_or_a_finding_keeps_one_line_and_its_ledger_pointer(tmp_path, second):
    s = _setup(str(tmp_path), claim="s1 lights the lamp\n" + second, finding="the wick is short\n" + second)
    withheld = "/home/" in second
    for role, step in (("builder", "s1"), ("checker", "s1"), ("lead", None)):
        rc, out, err = _brief(s, role, s["c2"], RUN, step)
        assert rc == 0, err.split(":")[0]
        lines = out[:-1].split("\n")
        _pointered(out)
        assert not any(ln.startswith(second) for ln in lines) and "/home/" not in out
        if role == "lead":
            continue
        claim = cx._WITHHELD if withheld else "s1 lights the lamp " + second
        finding = cx._WITHHELD if withheld else "the wick is short " + second
        assert f"claim: {claim} [LEDGER concordance-2 {RUN} 4]" in lines
        assert f"previous finding: {finding} [LEDGER concordance-2 {RUN} 6]" in lines


def _completed_run(s, run, ts, confirms=()):
    ev = lambda **e: json.dumps({"ts": ts, **e}, sort_keys=True)          # noqa: E731
    _write(s["c2"], f"docs/harness/runs/{run}.jsonl", "\n".join([
        ev(ev="open", by="lead", head=s["sha2"]),
        ev(ev="plan", by="lead", goal="Finish a run.", done=["it is finished"]),
        ev(ev="verdict", by="checker-1", step="plan", findings=[], **{"pass": True}),
        ev(ev="step", by="builder-1", owner="builder-1", step="d1", claim="d1 finishes", scope=["x"], tests=["t"],
           base=s["sha2"], adopted=[]),
        ev(ev="verdict", by="checker-3", step="d1", findings=[], **{"pass": True}),
        ev(ev="commit", by="lead", step="d1", sha=s["sha2"], paths=[]),
        ev(ev="note", by="lead", kind="ship", text="nothing ships", **{"pass": True}),
        ev(ev="verdict", by="checker-3", step="live", findings=[], head=s["sha2"], **{"pass": True})]
        + [ev(ev="note", by=by, kind="confirm", text=text) for by, text in confirms]) + "\n")


def test_due_lists_the_rules_due_the_confirmations_not_counted_and_the_ones_ignored(tmp_path):
    # The fixture's rules, ranked by id at their one entry commit, start at runs 9, 4, 12, 7 and 2.
    s = _setup(str(tmp_path))
    done = "2026-01-02-done"
    _completed_run(s, done, "2026-01-03T00:00:00+00:00", [
        ("checker-3", "RULE keep-the-lamp-lit failed: the lamp was out"),
        ("checker-3", "RULE the-gate-stays-shut held: it was shut"),
        ("builder-1", "RULE c2-only-rule held: a builder's word"),
        ("checker-9", "RULE c2-only-rule held: a checker with no verdict here"),
        ("checker-3", "RULE no-such-rule held: there is no such rule"),
        ("checker-3", "RULE v3-only-rule held: a V3 rule, confirmed in a concordance-2 run"),
        ("checker-3", "the lamp was fine, in free words")])
    _completed_run(s, done + "-2", "2026-01-04T00:00:00+00:00")
    _completed_run(s, done + "-3", "2026-01-05T00:00:00+00:00")
    rc, out, err = _brief(s, "builder", s["c2"], RUN, "s1")
    assert rc == 0, err.split(":")[0]
    _pointered(out)
    at = f"[LEDGER concordance-2 {done} "
    assert _section(out, "DUE") == [
        "== DUE: 2 of 4 rule(s) in scope are due; intervals 1, 2, 3, 5, 8, ... runs; a rule never confirmed is "
        "first due within 13 runs of its entry",
        f"clock all: 3 run(s) completed, the latest concordance-2 {done}-3 [LEDGER concordance-2 {done}-3 8]",
        f"clock concordance-2: 3 run(s) completed, the latest concordance-2 {done}-3 [LEDGER concordance-2 {done}-3 8]",
        f"DUE c2-only-rule (concordance-2): run 4, never confirmed, first due in run 4 [LEDGER concordance-2 {RUN} 2]",
        f"DUE keep-the-lamp-lit (all): run 4, interval 1, last counted: failed in run 1 {at}9]",
        f"not counted: the-gate-stays-shut held in run 1, when it was not due {at}10]",
        f"ignored: a confirmation, because it is not by a checker {at}11]",
        f"ignored: a confirmation, because its checker has no verdict in this ledger {at}12]",
        f"ignored: a confirmation, because no such rule at the records commit {at}13]",
        f"ignored: a confirmation, because outside the rule's scope {at}14]",
        f"ignored: a confirmation, because it does not read 'RULE <id> held|failed: <evidence>' {at}15]"]


def test_a_records_commit_the_parser_cannot_read_refuses_and_never_guesses(tmp_path):
    s = _setup(str(tmp_path))
    _commit(s["c2"], {cx.RULES_REL: _rules(s["sha1"]) + "Stray prose inside the last entry.\n"}, "a bad version")
    rc, out, err = _brief(s, "lead", s["c2"], RUN)                  # HEAD holds the bad version: CORE cannot be read
    assert rc == 2 and out == ""
    assert "docs/harness/RULES.md at the records commit does not parse: line " in err
    rc, out, err = _brief(s, "builder", s["c2"], RUN, "s1")         # the step's base is the good one
    assert rc == 0, err.split(":")[0]


SHALLOW_DUE = ("== DUE: not computed: this clone is shallow, so RULES.md's history cannot be read and no rule's "
               "entry or first due run can be known")


def test_a_shallow_clone_computes_no_schedule_and_prints_no_start(tmp_path):
    s = _setup(str(tmp_path / "src"))
    later = '## z-later-rule\n- scope: all\n- source: OWNER owner, chat, 2026-01-02 "later"\n- check: c\n> later\n\n'
    kept = "## ".join(p for p in _rules(s["sha1"]).split("## ") if not p.startswith("anchor-gone"))
    _commit(s["c2"], {cx.RULES_REL: kept + later}, "a rule removed, a rule added")      # the ledgers go in too
    url = pathlib.Path(s["c2"]).as_uri()

    def clone(name, *depth):
        dest = str(tmp_path / name)
        _git(str(tmp_path), "clone", "-q", *depth, url, dest)
        return {**s, "c2": dest}

    full = clone("full")
    rc, out, err = _brief(full, "lead", full["c2"], RUN)
    assert rc == 0, err.split(":")[0]
    assert _section(out, "DUE")[0].startswith("== DUE: 0 of 4 rule(s) in scope are due")
    assert _section(out, "DUE")[1:] == ["clock all: no run completed", "clock concordance-2: no run completed"]

    for name, depth, briefs in (("d1", "1", (("lead", None),)), ("d2", "2", (("lead", None), ("builder", "s1")))):
        c = clone(name, "--depth", depth)
        for role, step in briefs:
            rc, out, err = _brief(c, role, c["c2"], RUN, step)
            assert rc == 0, err.split(":")[0]
            assert _section(out, "DUE") == [SHALLOW_DUE]
            assert "first due in run" not in out and "clock " not in out and "\nDUE " not in out
            assert all(len(_section(out, name)) > 1 for name in ("CORE", "IN FLIGHT", "RUN", "WANTS"))
            _pointered(out)


def _snapshot(base):
    got = {}
    for d, _, files in os.walk(base):
        for f in files:
            full = os.path.join(d, f)
            rel = os.path.relpath(full, base).replace(os.sep, "/")
            if rel.endswith(".git/index"):
                continue                                       # git refreshes its index on a read
            with open(full, "rb") as fh:
                got[rel] = hashlib.sha256(fh.read()).hexdigest()
    return got


def test_brief_writes_nothing(tmp_path):
    s = _setup(str(tmp_path))
    before = _snapshot(str(tmp_path))
    for role, root, run, step in (("checker", s["c2"], RUN, "s1"), ("builder", s["v3"], V3RUN, "v1"),
                                  ("lead", s["c2"], RUN2, None)):
        assert _brief(s, role, root, run, step)[0] == 0
    after = _snapshot(str(tmp_path))
    assert sorted(set(before) ^ set(after)) == []
    assert sorted(k for k in before if before[k] != after[k]) == []


def test_brief_refuses_a_modified_tools_context_py_and_check_does_not(tmp_path):
    s = _setup(str(tmp_path))
    with open(os.path.join(s["c2"], "tools", "context.py"), "ab") as fh:
        fh.write(b"# an uncommitted edit\n")
    rc, out, err = _brief(s, "builder", s["c2"], RUN, "s1")
    assert rc == 2 and out == "" and "differs from HEAD" in err
    r = subprocess.run([sys.executable, "-B", os.path.join(s["c2"], "tools", "context.py"), "check", s["c2"]],
                       env={**os.environ, "HARNESS_CONFIG_DIR": s["cfg"]}, capture_output=True, timeout=300)
    assert r.stdout.decode("utf-8").startswith("config: HARNESS_CONFIG_DIR (the override)")
