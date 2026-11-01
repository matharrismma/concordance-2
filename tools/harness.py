#!/usr/bin/env python3
"""THE HARNESS — plan, build, check, fix — and the grade comes from machines, never from the lead.

    "The gates declare completion, not this table. ... The implementing model does not declare
     completion in prose; the gates declare it."                — docs/COMPLETION_CONTRACT.md §8

One run is one goal. One step has one owner. The LEAD holds the goal and the ledger and dispatches;
a BUILDER owns the next smallest faithful step; a CHECKER — never the step's owner, never the lead —
reviews it and re-runs every test itself. Nothing here takes anyone's word for anything:

  * a step opens only after a checker has passed the plan;
  * the checker's gate grades the COMMIT-TO-BE, not the checkout: a fresh worktree at the step's
    base with exactly the step's paths laid over — so an ignored file cannot pass a test;
  * a step's tests must go red in that worktree with the fix taken away (the pin check);
  * the full suite must match the baseline exactly — no new red, no red failing differently, no
    stale entry, no new vacuous pass — and the baseline only shrinks;
  * a step never edits what grades it (this file, the moat, the vacuity plugin, conftest, the pytest
    config, the role files); and whatever the working copy says, the harness that runs is HEAD's;
  * a step closes only when a builder gate, a full checker gate and that checker's verdict all pass
    on the SAME content hash as the tree at that moment; a later FAIL voids the close;
  * a commit stages exactly the step's paths, then proves the commit holds exactly them, byte for
    byte and mode for mode, or takes itself back;
  * three failed verdicts block the step: the lead stops and a human decides.

    python tools/harness.py open    RUN --goal "..." --done "..." [--done ...]
    python tools/harness.py replan  RUN --goal "..." --done "..." [--done ...]
    python tools/harness.py step    RUN STEP --owner builder-N --claim "..." --scope GLOB,.. --tests ID,..
    python tools/harness.py brief   RUN STEP
    python tools/harness.py gate    RUN STEP --role builder|checker --by NAME
    python tools/harness.py verdict RUN STEP|plan|live --by checker-N (--pass|--fail) [--finding "..."]..
    python tools/harness.py close   RUN STEP
    python tools/harness.py commit  RUN STEP -F MESSAGE_FILE
    python tools/harness.py abandon RUN STEP --reason "..."
    python tools/harness.py note    RUN --by NAME --kind KIND --text "..." [--pass|--fail]
    python tools/harness.py record  RUN -F MESSAGE_FILE        (commit the ledger alone)
    python tools/harness.py status  RUN
    python tools/harness.py done    RUN
    python tools/harness.py measure                            (baseline lines for HEAD, measured)

The runbook — the roles, the loop, what "smallest" and "faithful" mean — is docs/HARNESS.md.
Stdlib only, like the engine it guards.
"""
import os
import sys

if __name__ == "__main__":
    # Run as a script this file needs only the standard library, so nothing in the repo may sit
    # ahead of it on the import path: a step's tools/fnmatch.py would otherwise be imported HERE,
    # inside the grader. (os and sys are loaded before any path entry is consulted.)
    _here = os.path.dirname(os.path.abspath(__file__))
    _repo = os.environ.get("HARNESS_ROOT") or os.path.dirname(_here)
    _mine = {os.path.normcase(os.path.abspath(p)) for p in
             (_here, _repo, os.path.join(_repo, "src"), os.path.join(_repo, "tools"), os.path.join(_repo, "tests"))}
    sys.path[:] = [p for p in sys.path if os.path.normcase(os.path.abspath(p or os.getcwd())) not in _mine]

import argparse
import contextlib
import fnmatch
import hashlib
import json
import re
import secrets
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF_REL = "tools/harness.py"
RUNS_REL = "docs/harness/runs"
BASELINE_REL = "docs/harness/baseline.txt"
MANIFEST_REL = "tests/MANIFEST.txt"
MAX_ROUNDS = 3                      # failed verdicts before a step is BLOCKED and a human decides
RESERVED = ("plan", "live")         # verdict targets that are not steps
LINGER_SECONDS = 30                 # after the session reports its finish, how long a process may linger
STEP_TESTS_TIMEOUT = 30 * 60
SUITE_TIMEOUT = 90 * 60
MOAT_TIMEOUT = 20 * 60

# Files a run writes while it works; never part of a step's content.
EPHEMERAL = (".gate.lock", "__pycache__/*", "*/__pycache__/*", "*.pyc", ".pytest_cache/*",
             ".coverage", ".coverage.*")

# What GRADES. A step never edits these: the harness would be grading itself with its own hand.
# A change here is a bootstrap — the lead writes it, a checker reviews it outside any run.
MACHINERY = (SELF_REL, "tools/benchmark.py", "tools/vacuity_plugin.py", "tools/check.py",
             "conftest.py", "*/conftest.py", "pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini",
             ".claude/agents/*")
# Two graders a step may move in one direction only: the manifest gains tests, the baseline loses reds.

# A file that would be imported INSTEAD of the standard library or the test runner is a grader in
# disguise (tools/pytest.py, tools/sitecustomize.py, tools/fnmatch.py all faked a green suite).
# These directories are on the gate's import path; a step may not add a module there by such a name.
IMPORT_ROOTS = ("", "src/", "tools/", "tests/")
SHADOW_NAMES = frozenset(getattr(sys, "stdlib_module_names", ()) or (
    "abc argparse ast asyncio base64 collections contextlib copy csv dataclasses datetime decimal enum "
    "fnmatch functools glob hashlib heapq hmac html http importlib inspect io itertools json logging "
    "math os pathlib pickle platform random re shutil signal site socket sqlite3 string struct "
    "subprocess sys tempfile textwrap threading time token tokenize traceback types typing unittest "
    "urllib uuid warnings xml zipfile __future__ encodings codecs").split()) | {
    "pytest", "_pytest", "pluggy", "py", "iniconfig", "packaging", "coverage",
    "sitecustomize", "usercustomize"}

# (pattern, exceptions, why) — a changed path matching fails the gate unless an exception matches.
FORBIDDEN: Tuple[Tuple[str, Tuple[str, ...], str], ...] = (
    ("site/theories.html", (),
     "box-owned: rewritten on the box daily by the hive cycle; the box is the live truth"),
)
NEW_DATA = ("data/*", ("data/sticks/*",),
            "a NEW data file: data is made by seeds run on the box, never added by a step "
            "(data/sticks is the one tracked exception)")
# Tracked paths a step may touch only when its scope names them EXACTLY, and only surgically.
GUARDED: Dict[str, str] = {
    "data/domain_goldens.json": "never regenerate it whole; name it exactly and keep the change surgical",
    "tools/card_theories.py": "never run it; editing it needs an exact scope entry",
}
GUARDED_MAX_CHANGED_LINES = 40

# Added lines (and every ledger event) are scanned. A hit names the path, line and kind — never the value.
SECRET_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "a private key block"),
    (r"(?<![A-Za-z0-9])sk-(?:ant-)?[A-Za-z0-9_-]{20,}", "an API secret key"),
    (r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{30,}", "a GitHub token"),
    (r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])", "an AWS access key id"),
    (r"(?<![A-Za-z0-9])xox[abprs]-[A-Za-z0-9-]{10,}", "a Slack token"),
)
# name=value where the name says credential and the value looks like one (letters AND digits, 20+).
# Compound names count: ELEVENLABS_API_KEY, client_secret, DB_PASSWORD. A value that BEGINS as a
# placeholder (your-…, ${VAR}, <…>), a path, or a content digest (sha256:…) is not a secret.
_CRED = re.compile(r"(?i)(?:api[_-]?key|secret|token|passw(?:or)?d|pwd|credential)[a-z0-9_]*[\"']?"
                   r"\s*[:=]\s*[\"']?([^\s\"'`,;(){}\[\]]{20,})")
_PLACEHOLDER = re.compile(r"(?i)^(?:your|example|dummy|fake|test|sample|placeholder|redacted|changeme"
                          r"|xxx|\*\*\*|\$\{?[a-z_]|<|(?:sha\d+|md5|blake2\w*):"
                          r"|(?!eyJ)[a-z_][a-z0-9_]*\.[a-z_])"      # attribute access, not a JWT
                          r"|[/\\]|\.[a-z]{2,5}$")
# Box hosts, key file names and the like stay OUT of this public file: one regex per line here.
LOCAL_SECRET_FILES = (os.environ.get("HARNESS_SECRET_PATTERNS", ""),
                      os.path.join(os.path.expanduser("~"), ".config", "harness", "secret_patterns.txt"))

CONFLICT = re.compile(r"^(?:<{7}|>{7}) ")
TRAILING_WS = re.compile(r"[ \t]+$")
_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,80}$")
_BUILDER = re.compile(r"^builder-[a-z0-9]+$")
_CHECKER = re.compile(r"^checker-[a-z0-9]+$")
_NAME = re.compile(r"^(?:lead|builder-[a-z0-9]+|checker-[a-z0-9]+)$")


class HarnessError(Exception):
    """A refusal: the harness will not do what was asked, and says why."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _name(by: str, rx: re.Pattern = _NAME, what: str = "a name") -> str:
    if not by or not rx.match(by):
        raise HarnessError(f"{by!r} is not {what} (lead · builder-N · checker-N, lowercase)")
    return by


# ---------------------------------------------------------------------------------------- git

def _git(root: str, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=root, capture_output=True)
    if check and r.returncode != 0:
        raise HarnessError(f"git {' '.join(args[:3])}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8", "replace")


def _git_ok(root: str, *args: str) -> bool:
    return subprocess.run(["git", *args], cwd=root, capture_output=True).returncode == 0


def head(root: str) -> str:
    return _git(root, "rev-parse", "HEAD").strip()


def _show(root: str, rev: str, path: str) -> Optional[str]:
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=root, capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


def _tracked_at(root: str, rev: str) -> Set[str]:
    return {p for p in _git(root, "ls-tree", "-r", "--name-only", "-z", rev).split("\0") if p}


def _is_ledger(p: str) -> bool:
    return p.startswith(RUNS_REL + "/")


def _ephemeral(p: str) -> bool:
    return any(fnmatch.fnmatchcase(p, g) for g in EPHEMERAL)


def _changes(root: str, base: str) -> Tuple[List[str], List[str]]:
    """(tracked paths that differ from `base`, untracked paths) — ledgers and ephemera excluded."""
    tracked = [p for p in _git(root, "diff", "--name-only", "-z", "--no-renames", base, "--").split("\0")
               if p and not _is_ledger(p) and not _ephemeral(p)]
    untracked = [p for p in _git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
                 if p and not _is_ledger(p) and not _ephemeral(p)]
    return sorted(set(tracked)), sorted(set(untracked) - set(tracked))


def changed_paths(root: str, base: str) -> List[str]:
    t, u = _changes(root, base)
    return sorted(set(t) | set(u))


def diff_hash(root: str, base: str, paths: Optional[Sequence[str]] = None) -> str:
    """Content address of a step's work: every changed path and the bytes it holds now (full sha256)."""
    paths = changed_paths(root, base) if paths is None else sorted(paths)
    h = hashlib.sha256()
    for p in paths:
        h.update(p.encode("utf-8") + b"\0")
        full = os.path.join(root, p)
        if os.path.islink(full):
            h.update(b"<link>" + os.readlink(full).encode("utf-8", "replace"))
        elif os.path.isdir(full):
            h.update(b"<dir>")
        elif os.path.isfile(full):
            with open(full, "rb") as fh:
                h.update(hashlib.sha256(fh.read()).digest())
        else:
            h.update(b"<deleted>")
    return h.hexdigest()


def _utf16(data: bytes) -> Optional[str]:
    """UTF-16 text, with or without a byte-order mark — or None."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", "replace")
    if len(data) >= 4:
        half = len(data) // 2
        if data[1::2].count(0) > half * 0.6:
            return data.decode("utf-16-le", "replace")
        if data[0::2].count(0) > half * 0.6:
            return data.decode("utf-16-be", "replace")
    return None


def _decode(data: bytes) -> Tuple[str, bool]:
    """(text, is_text). UTF-16 (BOM or not) is text; anything else holding a NUL is binary."""
    wide = _utf16(data) if b"\0" in data or data[:2] in (b"\xff\xfe", b"\xfe\xff") else None
    if wide is not None:
        return wide, True
    if b"\0" in data:
        return data.decode("latin-1"), False
    return data.decode("utf-8", "replace"), True


def _read(full: str, limit: int = 20_000_000) -> Optional[bytes]:
    try:
        with open(full, "rb") as fh:
            return fh.read(limit)
    except OSError:
        return None


def added_lines(root: str, base: str, tracked: Sequence[str],
                untracked: Sequence[str]) -> Dict[str, List[Tuple[int, str]]]:
    """Every line a step ADDS, per path, with its line number in the new file."""
    out: Dict[str, List[Tuple[int, str]]] = {}
    if tracked:
        text = _git(root, "diff", "-U0", "--no-color", "--no-ext-diff", "--text", "--no-textconv",
                    base, "--", *tracked)
        cur: Optional[str] = None
        in_hunk, n = False, 0
        for line in text.split("\n"):
            if line.startswith("diff --git "):
                cur, in_hunk = None, False
                continue
            if line.startswith("@@"):
                m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
                n, in_hunk = (int(m.group(1)) if m else 0), True
                continue
            if not in_hunk:
                if line.startswith("+++ "):
                    tgt = line[4:].rstrip("\r").rstrip("\t")
                    cur = None if tgt == "/dev/null" else (tgt[2:] if tgt.startswith("b/") else tgt)
                continue
            if line.startswith("+") and cur is not None:
                out.setdefault(cur, []).append((n, line[1:].rstrip("\r")))
                n += 1
        for p in tracked:                             # a wide (UTF-16) file's diff is bytes, not lines:
            data = _read(os.path.join(root, p))       # judge the whole file, decoded
            if data and (b"\0" in data or data[:2] in (b"\xff\xfe", b"\xfe\xff")) and _utf16(data) is not None:
                out[p] = [(i, ln.rstrip("\r")) for i, ln in enumerate(_decode(data)[0].split("\n"), 1)]
    for p in untracked:
        data = _read(os.path.join(root, p))
        if data is not None:
            text, _ = _decode(data)
            out[p] = [(i, ln.rstrip("\r")) for i, ln in enumerate(text.split("\n"), 1)]
    return out


def _numstat(root: str, base: str, path: str) -> int:
    row = _git(root, "diff", "--numstat", base, "--", path).split()
    try:
        return int(row[0]) + int(row[1])
    except (IndexError, ValueError):
        return 10 ** 9                                 # binary or unreadable: treat as a rewrite


# ------------------------------------------------------------------------------------- checks

def _ok(detail="") -> dict:
    return {"ok": True, "detail": detail}


def _fail(detail) -> dict:
    return {"ok": False, "detail": detail}


def _in_scope(path: str, glob: str) -> bool:
    glob = glob.replace("\\", "/")
    if glob.endswith("/"):
        return path.startswith(glob)
    return path == glob or fnmatch.fnmatchcase(path, glob)


def check_content(root: str, paths: Sequence[str]) -> dict:
    bad = [f"{p}: {'a symlink' if os.path.islink(os.path.join(root, p)) else 'a directory or embedded repository'}"
           f" is not step content" for p in paths
           if os.path.islink(os.path.join(root, p)) or os.path.isdir(os.path.join(root, p))]
    return _fail(bad[:20]) if bad else (_ok(f"{len(paths)} path(s)") if paths
                                        else _fail(["nothing changed — no step"]))


def shadowing(path: str) -> Optional[str]:
    """The module name `path` would put ahead of the stdlib or the test runner, or None."""
    if path.endswith(".pth"):
        return path.rsplit("/", 1)[-1]
    for r in IMPORT_ROOTS:
        if not path.startswith(r):
            continue
        parts = path[len(r):].split("/")
        mod = parts[0][:-3] if len(parts) == 1 and parts[0].endswith(".py") else \
            (parts[0] if len(parts) == 2 and parts[1] in ("__init__.py", "__main__.py") else None)
        if mod and mod in SHADOW_NAMES:
            return mod
    return None


def check_shadowing(root: str, paths: Sequence[str]) -> dict:
    bad = [f"{p}: would be imported instead of `{shadowing(p)}` — a grader in disguise"
           for p in paths if os.path.exists(os.path.join(root, p)) and shadowing(p)]
    return _fail(bad[:20]) if bad else _ok("no module shadows the standard library or the test runner")


def check_scope(paths: Sequence[str], scope: Sequence[str]) -> dict:
    outliers = [p for p in paths if not any(_in_scope(p, g) for g in scope)]
    return _fail(["outside the step's scope: " + p for p in outliers][:20]) if outliers \
        else _ok(f"{len(paths)} path(s), all inside the scope")


def check_forbidden(root: str, base: str, paths: Sequence[str], scope: Sequence[str]) -> dict:
    bad: List[str] = []
    at_base = _tracked_at(root, base)
    for p in paths:
        for pat, exc, why in FORBIDDEN:
            if fnmatch.fnmatchcase(p, pat) and not any(fnmatch.fnmatchcase(p, e) for e in exc):
                bad.append(f"{p}: {why}")
        pat, exc, why = NEW_DATA
        if (fnmatch.fnmatchcase(p, pat) and not any(fnmatch.fnmatchcase(p, e) for e in exc)
                and p not in at_base and os.path.exists(os.path.join(root, p))):
            bad.append(f"{p}: {why}")
        if p in GUARDED:
            if p not in scope:
                bad.append(f"{p}: {GUARDED[p]} (not named exactly in the scope)")
            elif _numstat(root, base, p) > GUARDED_MAX_CHANGED_LINES:
                bad.append(f"{p}: {GUARDED[p]} (more than {GUARDED_MAX_CHANGED_LINES} lines changed "
                           f"— that is a regeneration, not a fix)")
    return _fail(bad[:20]) if bad else _ok("no forbidden or guarded path touched")


def _manifest_entries(text: Optional[str]) -> Set[str]:
    return {ln.strip().lstrip("﻿") for ln in (text or "").splitlines()
            if ln.strip() and not ln.strip().lstrip("﻿").startswith("#")}


_BASE_RED = re.compile(r"^(?P<id>.+?) \| (?P<fp>[0-9a-f]{12})(?:\s+#.*)?$")
_BASE_VAC = re.compile(r"^vacuous (?P<id>\S.*?)(?:\s+#\s.*)?$")


def parse_baseline(text: Optional[str]) -> Tuple[Dict[str, str], Set[str]]:
    """({red nodeid: failure fingerprint}, {vacuous nodeid}).

    `<id> | <12-hex fingerprint>  # reason` and `vacuous <id>  # reason`. An id may itself hold
    '#' or '|' (a parametrized id); a line that fits neither shape is kept as a red with no
    fingerprint, so it can only fail — never quietly excuse a test.
    """
    reds: Dict[str, str] = {}
    vac: Set[str] = set()
    for ln in (text or "").splitlines():
        body = ln.lstrip("﻿").strip()
        if not body or body.startswith("#"):
            continue
        m = _BASE_VAC.match(body)
        if m:
            vac.add(m.group("id"))
            continue
        m = _BASE_RED.match(body)
        if m:
            reds[m.group("id")] = m.group("fp")
        else:
            reds[body] = ""
    return reds, vac


def _read_text(full: str) -> Optional[str]:
    data = _read(full)
    return None if data is None else _decode(data)[0]


def check_machinery(root: str, base: str, paths: Sequence[str]) -> dict:
    bad = [f"{p}: a step never edits what grades it — a machinery change is a bootstrap, reviewed "
           f"by a checker outside any run" for p in paths if any(fnmatch.fnmatchcase(p, g) for g in MACHINERY)]
    if MANIFEST_REL in paths:
        before = _manifest_entries(_show(root, base, MANIFEST_REL))
        after = _manifest_entries(_read_text(os.path.join(root, MANIFEST_REL)))
        gone = sorted(before - after)
        if gone:
            bad.append(f"{MANIFEST_REL}: a step adds tests to the suite, never removes one: " + ", ".join(gone[:8]))
    if BASELINE_REL in paths:
        r0, v0 = parse_baseline(_show(root, base, BASELINE_REL))
        r1, v1 = parse_baseline(_read_text(os.path.join(root, BASELINE_REL)))
        grew = sorted(f"{n} | {fp}" for n, fp in r1.items() if r0.get(n) != fp) + \
            sorted(f"vacuous {n}" for n in v1 - v0)
        if grew:
            bad.append(f"{BASELINE_REL}: the baseline only shrinks — a step may delete lines, never add "
                       f"or alter one: " + "; ".join(grew[:5]))
    return _fail(bad[:20]) if bad else _ok("no grader touched (the manifest may grow, the baseline may shrink)")


def _secret_patterns() -> List[Tuple[re.Pattern, str]]:
    pats = [(re.compile(p), why) for p, why in SECRET_PATTERNS]
    for f in LOCAL_SECRET_FILES:
        if f and os.path.isfile(f):
            with open(f, encoding="utf-8-sig") as fh:
                for ln in fh:
                    ln = ln.strip()
                    if ln and not ln.startswith("#"):
                        pats.append((re.compile(ln), "a locally-declared private pattern"))
    return pats


def secret_kind(text: str, pats: Optional[List[Tuple[re.Pattern, str]]] = None) -> Optional[str]:
    """What kind of secret `text` carries, or None. Never returns the secret itself."""
    for rx, why in (pats if pats is not None else _secret_patterns()):
        if rx.search(text):
            return why
    for m in _CRED.finditer(text):
        val = m.group(1)
        if re.search(r"[A-Za-z]", val) and re.search(r"\d", val) and not _PLACEHOLDER.search(val):
            return "a credential assigned in source"
    return None


def check_secrets(added: Dict[str, List[Tuple[int, str]]]) -> dict:
    pats = _secret_patterns()
    hits = []
    for p, lines in added.items():
        for n, ln in lines:
            kind = secret_kind(ln, pats)
            if kind:
                hits.append(f"{p}:{n} carries {kind}")
    return _fail(hits[:20]) if hits else _ok(f"{len(pats) + 1} pattern(s), no hit")


def check_hygiene(root: str, added: Dict[str, List[Tuple[int, str]]], paths: Sequence[str]) -> dict:
    bad: List[str] = []
    text_now: Dict[str, bool] = {}
    for p in paths:
        data = _read(os.path.join(root, p))
        text_now[p] = data is not None and _decode(data)[1]
    for p, lines in added.items():
        if not text_now.get(p, True):
            continue                                  # binary content: no lines to judge
        for n, ln in lines:
            if CONFLICT.match(ln):
                bad.append(f"{p}:{n}: a conflict marker")
            elif not p.endswith(".md") and TRAILING_WS.search(ln):
                bad.append(f"{p}:{n}: trailing whitespace")
    for p in paths:
        full = os.path.join(root, p)
        if not os.path.isfile(full):
            continue
        if p.endswith(".py"):
            try:
                compile(_read_text(full) or "", p, "exec", dont_inherit=True)
            except SyntaxError as e:
                bad.append(f"{p}: does not compile — {e.msg} (line {e.lineno})")
        elif p.endswith(".json"):
            try:
                json.loads(_read_text(full) or "")
            except ValueError as e:
                bad.append(f"{p}: not valid JSON — {e}")
        elif p.endswith(".jsonl"):
            for i, ln in enumerate((_read_text(full) or "").split("\n"), 1):
                if ln.strip():
                    try:
                        json.loads(ln)
                    except ValueError:
                        bad.append(f"{p}:{i}: not valid JSON")
                        break
    return _fail(bad[:20]) if bad else _ok("clean")


def check_manifest(root: str, base: str) -> dict:
    """The suite must be whole before its result means anything (the same rule as tools/check.py)."""
    man = os.path.join(root, *MANIFEST_REL.split("/"))
    if not os.path.isfile(man):
        return _fail([f"{MANIFEST_REL} is gone"]) if _show(root, base, MANIFEST_REL) is not None \
            else _ok(f"no {MANIFEST_REL} in this tree")
    want = _manifest_entries(_read_text(man))
    tdir = os.path.join(root, "tests")
    have = {f for f in os.listdir(tdir) if f.startswith("test_") and f.endswith(".py")}
    bad = [f"MISSING (listed, absent): {m}" for m in sorted(want - have)] + \
          [f"UNLISTED (add to {MANIFEST_REL}): {e}" for e in sorted(have - want)]
    return _fail(bad[:20]) if bad else _ok(f"{len(have)} test files, all listed")


# ------------------------------------------------------------------------------------- pytest

_RANK = {"skipped": 0, "passed": 1, "failed": 2, "error": 3}

# THE STREAM. A report file the child leaves behind can be rewritten by the code under test (an
# atexit hook turned a red junit green, and printed a matching summary). So results are not read
# from anything the child writes to disk: this plugin — written outside the tree under a random
# name, loaded with -p before any test module is imported — sends every report over a localhost
# socket the moment pytest makes it. The parent accepts ONE connection (the plugin's) and grades
# from what it received; nothing that runs later can take a delivered failure back. In-process
# code that hunts this module down by name can still lie — code a checker reading the diff sees.
_STREAM_PLUGIN = r'''
import json as _json, os as _os, socket as _socket, sys as _sys
import pytest as _pytest
# Everything this plugin uses is bound HERE, at import, before any test module exists: a test that
# monkeypatches json.dumps, socket.sendall or a builtin afterwards cannot reach these references.
_esc = _json.encoder.encode_basestring_ascii
_port = int(_os.environ.pop("@@VAR@@"))
_token = _os.environ.pop("@@TOK@@")
_sock = _socket.create_connection(("127.0.0.1", _port))
_sendall = _sock.sendall
_Skipped, _XFailed = _pytest.skip.Exception, _pytest.xfail.Exception
_str, _int, _isinstance, _getattr, _hasattr = str, int, isinstance, getattr, hasattr
_norm, _abspath, _sep = _os.path.normcase, _os.path.abspath, _os.sep
_root = _norm(_abspath(_os.getcwd()))
_me = _norm(_abspath(__file__))
try:
    from _pytest.skipping import xfailed_key as _xfailed_key    # pytest's own xfail decision
except Exception:
    _xfailed_key = None
# Hooks through which a plugin could change what a test's result is, or which tests run at all.
_JUDGING = ("pytest_runtest_", "pytest_report_", "pytest_collection", "pytest_collectreport",
            "pytest_make_collect_report", "pytest_pycollect_", "pytest_itemcollected",
            "pytest_ignore_collect", "pytest_collect_file", "pytest_deselected", "pytest_generate_tests")


def _enc(v):
    if v is None:
        return "null"
    if v is True or v is False:
        return "true" if v else "false"
    if _isinstance(v, _int):
        return _str(_int(v))
    if _isinstance(v, (list, tuple)):
        return "[" + ",".join(_enc(x) for x in v) + "]"
    if _isinstance(v, dict):
        return "{" + ",".join(_esc(_str(k)) + ":" + _enc(x) for k, x in v.items()) + "}"
    return _esc(_str(v))


def _send(obj):
    _sendall((_enc(obj) + "\n").encode("ascii"))


def _msg(rep):
    crash = _getattr(rep.longrepr, "reprcrash", None)
    m = crash.message if crash is not None else _str(rep.longrepr)
    return m if rep.when == "call" else "failed on %s with \"%s\"" % (rep.when, m)


_send({"ev": "hello", "token": _token})


def _origin(plugin):
    f = _getattr(plugin, "__file__", None)
    if not f:
        f = _getattr(_sys.modules.get(_getattr(type(plugin), "__module__", "") or ""), "__file__", None)
    return f


def pytest_plugin_registered(plugin, manager):
    # Historic: this sees every plugin, including those registered before it. A plugin from INSIDE
    # the tree that hooks how tests are judged is refused — save the graders a step cannot edit
    # (any conftest.py, tools/vacuity_plugin.py). Installed plugins are the environment, not a step.
    try:
        hooks = [n for n in dir(plugin) if n.startswith(_JUDGING)]
        if not hooks:
            return
        f = _origin(plugin)
        where = "an object of unknown origin"
        if f:
            p = _norm(_abspath(f))
            if p == _me or not (p == _root or p.startswith(_root + _sep)):
                return
            rel = p[len(_root) + 1:].replace("\\", "/")
            if rel == "conftest.py" or rel.endswith("/conftest.py") or rel == "tools/vacuity_plugin.py":
                return
            where = rel
        _send({"ev": "plugin", "origin": where, "hooks": hooks[:8]})
    except BaseException:
        _send({"ev": "plugin", "origin": "an unreadable plugin", "hooks": []})


def _xfail(item):
    if _xfailed_key is not None:
        try:
            return item.stash.get(_xfailed_key, None) is not None
        except Exception:
            pass
    return item.get_closest_marker("xfail") is not None


def pytest_collection_finish(session):
    _send({"ev": "collected", "ids": [i.nodeid for i in session.items]})


def pytest_collectreport(report):
    if report.failed:
        _send({"ev": "collecterror", "id": report.nodeid})


@_pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item, call):
    # The innermost wrapper: it sees the report as pytest made it, before any later wrapper can
    # change it, and sends a failure at once. Nothing that runs after can take it back.
    outcome = yield
    try:
        rep = outcome.get_result()
    except BaseException:
        return
    if _xfail(item):
        return                                   # xfail is pytest's to judge (its own decision, not a marker)
    exc = call.excinfo
    if exc is not None and _isinstance(exc.value, (_Skipped, _XFailed)):
        return
    if rep.outcome == "failed":
        _send({"ev": "raw", "id": item.nodeid, "when": call.when, "msg": _msg(rep)})
    elif exc is not None:                        # it raised, yet the report says it did not fail
        _send({"ev": "raw", "id": item.nodeid, "when": call.when,
               "msg": "the report says %s, but the test raised %s: %s"
                      % (rep.outcome, exc.typename, _str(exc.value)[:4000])})


def pytest_runtest_logreport(report):
    _send({"ev": "report", "id": report.nodeid, "when": report.when, "outcome": report.outcome,
           "msg": _msg(report) if report.failed else ""})


def pytest_sessionfinish(session, exitstatus):
    _send({"ev": "finish", "status": _int(exitstatus)})
'''


class Stream:
    """What the reporter delivered: outcomes, every failure message, the session's exit status,
    and anything that makes the stream untrustworthy."""
    def __init__(self) -> None:
        self.results: Dict[str, str] = {}
        self.messages: Dict[str, str] = {}
        self.status: Optional[int] = None
        self.problems: List[str] = []


def parse_stream(lines: Sequence[bytes], token: Optional[str] = None) -> Stream:
    """Grade from the streamed events.

    The stream must open with this run's token (so a process that connected first can only make
    the run fail, never pass). A test's outcome is the WORST any of its reports said, and EVERY
    distinct failure message is kept, in order — a second failure inside a test, a teardown error
    after a failed call, a later failing subtest all change the fingerprint. A late line can add a
    failure but never retract one. Every collected test must report, and the session must finish.
    """
    s = Stream()
    reported: Dict[str, List[str]] = {}     # every report's failure message, repeats kept
    sightings: Dict[str, List[str]] = {}    # the reporter's own sightings, kept only if no report says so
    collected: Optional[List[str]] = None
    terminal: Set[str] = set()
    collect_errors, bad, opened = 0, 0, token is None

    def note(nid: str, o: str, msg: Optional[str] = None, *, sighting: bool = False) -> None:
        if nid not in s.results or _RANK[o] > _RANK[s.results[nid]]:
            s.results[nid] = o
        if msg is not None and o in ("failed", "error"):
            (sightings if sighting else reported).setdefault(nid, []).append(msg)
    for raw in lines:
        try:
            ev = json.loads(raw.decode("utf-8", "surrogatepass"))
            if not isinstance(ev, dict):
                raise ValueError("not an event")
            kind = ev.get("ev")
            if not opened:
                if kind == "hello" and ev.get("token") == token:
                    opened = True
                    continue
                s.problems.append("the result stream did not open with this run's token — "
                                  "something else connected first")
                break
            if kind == "collected" and collected is None:
                collected = [str(x) for x in (ev.get("ids") or [])]
            elif kind == "collecterror":
                collect_errors += 1
                note(str(ev["id"]), "error", "collection failure")
            elif kind == "plugin":
                s.problems.append(f"a plugin from inside the tree ({ev.get('origin')}) hooks "
                                  f"{', '.join(map(str, ev.get('hooks') or [])) or 'test judging'} — a test "
                                  f"may not change how tests are judged")
            elif kind in ("report", "raw"):
                nid, when, out = str(ev["id"]), ev.get("when"), ev.get("outcome", "failed")
                if out == "failed" or kind == "raw":
                    note(nid, "failed" if when == "call" else "error", str(ev.get("msg", "")),
                         sighting=kind == "raw")
                elif out == "skipped":
                    note(nid, "skipped")
                elif out == "passed" and when == "call":
                    note(nid, "passed")
                if kind == "report" and (when == "call" or (when == "setup" and out in ("skipped", "failed"))):
                    terminal.add(nid)
            elif kind == "finish":
                s.status = int(ev.get("status", -1))
        except (ValueError, TypeError, KeyError, AttributeError, UnicodeDecodeError):
            bad += 1
    for n in set(reported) | set(sightings):
        mine = reported.get(n, [])
        s.messages[n] = "\n".join(mine + [m for m in dict.fromkeys(sightings.get(n, [])) if m not in mine])
    if not opened and not s.problems:
        s.problems.append("the result stream never opened")
    if bad:
        s.problems.append(f"{bad} unreadable line(s) on the result stream")
    if s.status is None:
        s.problems.append("the session never reported its finish — it was cut short")
    if collected is not None and not collect_errors:      # a collection error stops the run: red anyway
        missing = [n for n in collected if n not in terminal]
        if missing:
            s.problems.append(f"{len(missing)} collected test(s) never reported, e.g. {missing[0]}")
    return s


def fingerprint(message: str) -> str:
    """How a test fails, addressed: the same failure hashes the same; a different failure does not."""
    m = re.sub(r"0x[0-9a-fA-F]+", "0x?", message or "")
    m = re.sub(r"pytest-\d+", "pytest-N", m)
    m = re.sub(r"\s+", " ", m).strip()
    return hashlib.sha256(m.encode("utf-8", "surrogatepass")).hexdigest()[:12]


def _unroot(message: str, root: str) -> str:
    """A failure that names the tree's own path must not fingerprint differently per worktree."""
    r = os.path.abspath(root)
    for v in sorted({r, r.replace("\\", "/"), r.replace("\\", "\\\\")}, key=len, reverse=True):
        message = message.replace(v, "<root>")
    return message


class Run:
    """One pytest run: exit code, streamed outcomes and failure messages, pytest's summary line,
    vacuous passes, and anything wrong with the stream itself."""
    def __init__(self, rc: int, results: Dict[str, str], messages: Dict[str, str], tail: str,
                 vacuous: Optional[Set[str]], stream_problems: Sequence[str] = ()):
        self.rc, self.results, self.messages, self.tail, self.vacuous = rc, results, messages, tail, vacuous
        self.stream_problems = list(stream_problems)

    def disagreement(self) -> Optional[str]:
        """Is the stream whole, and does pytest's own summary line tell the same story? (None = yes.)

        A summary is printed by the child and can be forged; a mismatch with the stream is a
        tripwire that something tampered, never a source of results.
        """
        if self.stream_problems:
            return "the result stream is not whole: " + "; ".join(self.stream_problems)
        n = {k: int(m.group(1)) if (m := re.search(rf"(\d+) {k}\b", self.tail)) else 0
             for k in ("failed", "errors?")}
        c = counts(self.results)
        # Red or green is the one thing both must agree on (pytest counts subtests and a teardown
        # error beside a pass differently from per-test outcomes, so the counts themselves may not).
        if (n["failed"] + n["errors?"] > 0) != (c["failed"] + c["error"] > 0):
            return (f"the streamed results ({c}) and pytest's printed summary ({self.tail!r}) disagree — "
                    f"something tampered with the run's output")
        return None


@contextlib.contextmanager
def _scratch() -> Iterator[str]:
    """A temp dir whose removal never raises: a grandchild may still hold a file in it (Windows)."""
    td = tempfile.mkdtemp(prefix="harness-run-")
    try:
        yield td
    finally:
        shutil.rmtree(td, ignore_errors=True)


def run_pytest(root: str, args: Sequence[str], timeout: int, *, vacuity: bool = False,
               verbose: bool = False) -> Run:
    env = dict(os.environ)
    for k in ("VACUITY_ENFORCE", "HARNESS_ROOT", "HARNESS_REEXEC"):
        env.pop(k, None)
    with _scratch() as td:
        nonce = secrets.token_hex(8)
        token = secrets.token_hex(16)
        plugin, var, tok = f"harness_stream_{nonce}", f"HARNESS_STREAM_{nonce.upper()}", f"HARNESS_TOKEN_{nonce.upper()}"
        with open(os.path.join(td, plugin + ".py"), "w", encoding="utf-8") as fh:
            fh.write(_STREAM_PLUGIN.replace("@@VAR@@", var).replace("@@TOK@@", tok))
        env["PYTHONPATH"] = os.pathsep.join([td, os.path.join(root, "src"), os.path.join(root, "tools")])
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(0.5)
        env[var], env[tok] = str(listener.getsockname()[1]), token
        received: List[bytes] = []
        stop, finished = threading.Event(), threading.Event()

        def pump() -> None:
            conn = None
            while not stop.is_set():
                try:
                    conn, _ = listener.accept()
                    break
                except socket.timeout:
                    continue
                except OSError:
                    return
            try:
                listener.close()                         # the first connection, and no other
            except OSError:
                pass
            if conn is None:
                return
            conn.settimeout(None)
            parts: List[bytes] = []
            with conn:
                while True:
                    try:
                        chunk = conn.recv(1 << 20)
                    except OSError:
                        break
                    if not chunk:
                        break
                    if b"\n" not in chunk:
                        parts.append(chunk)
                        continue
                    *full, rest = (b"".join(parts) + chunk).split(b"\n")
                    parts = [rest] if rest else []
                    for line in full:
                        if line.strip():
                            received.append(line)
                            if line.startswith(b'{"ev":"finish"'):
                                finished.set()
            tail_bytes = b"".join(parts)
            if tail_bytes.strip():
                received.append(tail_bytes)

        reader = threading.Thread(target=pump, daemon=True)
        reader.start()
        extra: List[str] = ["-p", plugin]
        use_vac = vacuity and os.path.isfile(os.path.join(root, "tools", "vacuity_plugin.py"))
        if use_vac:
            env["VACUITY_OUT"] = os.path.join(td, "vacuity.json")
            extra += ["-p", "vacuity_plugin"]
        # -vv for the suite: a fingerprint must hash the WHOLE failure, not pytest's elided -q repr.
        cmd = [sys.executable, "-m", "pytest", "-vv" if verbose else "-q", "-p", "no:cacheprovider",
               *extra, *args]
        late: List[str] = []
        out_path = os.path.join(td, "stdout.txt")
        try:
            with open(out_path, "wb") as out_fh:
                proc = subprocess.Popen(cmd, cwd=root, env=env, stdout=out_fh, stderr=subprocess.STDOUT)
                deadline, done_at, exited = time.monotonic() + timeout, None, False
                while True:
                    try:
                        proc.wait(timeout=1.0)
                        exited = True
                        break
                    except subprocess.TimeoutExpired:
                        pass
                    now = time.monotonic()
                    if now > deadline:
                        proc.kill()
                        proc.wait()
                        if not finished.is_set():
                            late.append(f"timed out after {timeout}s")
                        break
                    if finished.is_set():
                        # The session has finished and its results are in hand; a thread left
                        # running must not hold the grade hostage for the whole timeout.
                        done_at = done_at or now
                        if now - done_at > LINGER_SECONDS:
                            proc.kill()
                            proc.wait()
                            break
        finally:
            stop.set()
            reader.join(60)
            try:
                listener.close()
            except OSError:
                pass
        with open(out_path, "rb") as fh:
            lines = [ln for ln in fh.read().decode("utf-8", "replace").splitlines() if ln.strip()]
        tail = next((ln for ln in reversed(lines) if re.search(r"\d+ (passed|failed|error)", ln)),
                    lines[-1] if lines else "")
        stream = parse_stream(list(received), token)
        results = stream.results
        messages = {n: _unroot(m, root) for n, m in stream.messages.items()}
        problems = late + stream.problems
        if reader.is_alive():
            problems.append("the result stream was still open after the run ended")
        # A process that ended by itself reports its own exit code (it may have failed after the
        # finish, in unconfigure); one we stopped after its finish reports the session's status.
        rc = proc.returncode if exited or stream.status is None else stream.status
        vac: Optional[Set[str]] = None
        if use_vac:
            vac = set()
            rep = env["VACUITY_OUT"]
            if os.path.isfile(rep):
                with open(rep, encoding="utf-8") as fh:
                    for row in json.load(fh).get("rows", []):
                        if row.get("cards_seen", 0) <= 0 and row.get("outcome") == "passed" \
                                and not row.get("exempt"):
                            vac.add(row["nodeid"])
            else:
                vac = None
    return Run(rc, results, messages, tail, vac, problems)


def _belongs(nodeid: str, arg: str) -> bool:
    a = arg.replace("\\", "/")
    if "::" in a:
        return nodeid == a or nodeid.startswith(a + "::") or nodeid.startswith(a + "[")
    if a.endswith(".py"):
        return nodeid.split("::")[0] == a
    return nodeid.startswith(a.rstrip("/") + "/")


def vacuous(results: Dict[str, str], args: Sequence[str]) -> List[str]:
    """The test arguments that ran NOTHING here — every case skipped, or none collected.

    A skipped acceptance test proves nothing; in a clean clone the corpus-dependent files skip by
    design (tests/conftest.py), so a step pinned only by one of those has not been tested at all.
    """
    return [a for a in args if not any(_belongs(n, a) and o != "skipped" for n, o in results.items())]


def counts(results: Dict[str, str]) -> Dict[str, int]:
    c = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    for o in results.values():
        c[o] += 1
    return c


def check_step_tests(root: str, tests: Sequence[str]) -> dict:
    missing = [t for t in tests if not os.path.exists(os.path.join(root, t.split("::")[0]))]
    if missing:
        return _fail([f"the step names a test that does not exist: {t}" for t in missing])
    run = run_pytest(root, tests, STEP_TESTS_TIMEOUT)
    if run.disagreement():
        return _fail([run.disagreement()])
    red = sorted(n for n, o in run.results.items() if o in ("failed", "error"))
    empty = vacuous(run.results, tests)
    if run.rc != 0 or red or empty:
        detail = [f"red: {n}" for n in red[:20]] + [f"vacuous (ran nothing here): {a}" for a in empty]
        return _fail(detail or [f"pytest exited {run.rc}: {run.tail}"])
    return _ok(f"{counts(run.results)} — {run.tail}")


def check_pins(wt: str, paths: Sequence[str], tests: Sequence[str]) -> dict:
    """The step's tests must go RED with the fix taken away — or they do not pin the fix.

    `wt` is a worktree at the step's base with only the step's TEST files laid over. A red here
    must be one of the step's own test ids (or a collection error of their file): a skip, an
    unknown id, or a "no tests ran" is not red.
    """
    if not [p for p in paths if not p.startswith("tests/")]:
        return _ok("test-only step: nothing to revert (the checker must justify any changed expectation)")
    present = [t for t in tests if os.path.exists(os.path.join(wt, t.split("::")[0]))]
    if not present:
        return _fail(["none of the step's tests exist at the base, even with the step's test files laid over"])
    run = run_pytest(wt, present, STEP_TESTS_TIMEOUT)
    if run.disagreement():
        return _fail([run.disagreement()])
    red = sorted(n for n, o in run.results.items() if o in ("failed", "error")
                 and any(_belongs(n, a) or n == a.split("::")[0] for a in tests))
    if not red:
        return _fail([f"with the fix reverted none of the step's tests went red (pytest exit {run.rc}: "
                      f"{run.tail}) — they do not pin it"])
    return _ok(f"with the fix reverted: {len(red)} red — e.g. {red[0]}")


def judge_suite(results: Dict[str, str], messages: Dict[str, str], vacuous_now: Optional[Set[str]],
                base_baseline: Optional[str], baseline: Optional[str]) -> List[str]:
    """Everything wrong with a suite run against the baseline; empty means it matches exactly.

    A red must be baselined AND fail the way it was baselined (its fingerprint): an "every page"
    test already red for one page must not hide a second. Every baselined red must still be red,
    every baselined vacuous pass still vacuous — and the baseline may only have lost lines since
    the base.
    """
    b0_reds, b0_vac = parse_baseline(base_baseline)
    reds, vacs = parse_baseline(baseline)
    detail: List[str] = []
    detail += [f"the baseline grew (it only shrinks): {n} | {fp}" for n, fp in sorted(reds.items())
               if b0_reds.get(n) != fp]
    detail += [f"the baseline grew (it only shrinks): vacuous {n}" for n in sorted(vacs - b0_vac)]
    red_now = {n: fingerprint(messages.get(n, "")) for n, o in results.items() if o in ("failed", "error")}
    for n, fp in sorted(red_now.items()):
        if n not in reds:
            detail.append(f"NEW red: {n}")
        elif reds[n] != fp:
            detail.append(f"a baselined red now fails DIFFERENTLY (fingerprint {fp}, baselined {reds[n]}): {n}")
    detail += [f"STALE baseline (passes now — delete its line from {BASELINE_REL}): {n}"
               for n in sorted(reds) if n not in red_now]
    if vacuous_now is None:
        if vacs:
            detail.append("the vacuity report is missing, so the baselined vacuous passes cannot be checked")
    else:
        detail += [f"NEW vacuous pass (asserted against a corpus it never populated): {n}"
                   for n in sorted(vacuous_now - vacs)]
        detail += [f"STALE vacuous baseline (no longer vacuous — delete its line): {n}"
                   for n in sorted(vacs - vacuous_now)]
    return detail


def check_suite(wt: str, root: str, base: str) -> dict:
    run = run_pytest(wt, ["tests"], SUITE_TIMEOUT, vacuity=True, verbose=True)
    if run.rc not in (0, 1) or not run.results:
        return _fail([f"the suite did not complete (pytest exit {run.rc}): {run.tail}"])
    if run.disagreement():
        return _fail([run.disagreement()])
    baseline = _read_text(os.path.join(wt, BASELINE_REL))
    detail = judge_suite(run.results, run.messages, run.vacuous, _show(root, base, BASELINE_REL), baseline)
    if detail:
        return _fail(detail[:30])
    reds, vacs = parse_baseline(baseline)
    return _ok(f"{counts(run.results)} — {len(reds)} baselined red(s) and {len(vacs)} baselined vacuous "
               f"pass(es), none new, none changed — {run.tail}")


def check_moat(wt: str, root: str, base: str) -> dict:
    tool = os.path.join(wt, "tools", "benchmark.py")
    if not os.path.isfile(tool):
        return _fail(["tools/benchmark.py is gone"]) if _show(root, base, "tools/benchmark.py") is not None \
            else _ok("no moat benchmark in this tree")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([os.path.join(wt, "src"), os.path.join(wt, "tools")])
    try:
        r = subprocess.run([sys.executable, tool], cwd=wt, env=env, capture_output=True, timeout=MOAT_TIMEOUT)
    except subprocess.TimeoutExpired:
        return _fail([f"the moat benchmark timed out after {MOAT_TIMEOUT}s"])
    lines = [ln for ln in r.stdout.decode("utf-8", "replace").splitlines() if ln.strip()]
    fp = next((ln.strip() for ln in lines if ln.startswith("FALSE-POSITIVES")), lines[-1] if lines else "")
    return _ok(fp) if r.returncode == 0 else _fail([f"moat exit {r.returncode}: {fp}"])


# ------------------------------------------------------------------- worktrees and the floor

@contextlib.contextmanager
def candidate(root: str, base: str) -> Iterator[str]:
    """A throwaway worktree at `base` — the commit-to-be is built in it by laying paths over."""
    td = tempfile.mkdtemp(prefix="harness-")
    wt = os.path.join(td, "wt")
    try:
        _git(root, "worktree", "add", "--detach", "--force", wt, base)
        yield wt
    finally:
        _git(root, "worktree", "remove", "--force", wt, check=False)
        _git(root, "worktree", "prune", check=False)
        shutil.rmtree(td, ignore_errors=True)


def fresh(root: str, wt: str, paths: Sequence[str]) -> None:
    """Put the worktree back to its base — removing anything a previous stage wrote, ignored files
    included — then lay `paths` over it. Every stage starts from the same commit-to-be."""
    _git(wt, "clean", "-fdxq")
    _git(wt, "checkout", "-q", "--", ".")
    overlay(root, wt, paths)


def overlay(root: str, wt: str, paths: Sequence[str]) -> None:
    for p in paths:
        src, dst = os.path.join(root, p), os.path.join(wt, p)
        if os.path.isfile(src) and not os.path.islink(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        elif os.path.isfile(dst):
            os.remove(dst)


def _pid_alive(pid: int) -> bool:
    """Is `pid` running? Never os.kill(pid, 0) on Windows: there 0 is CTRL_C_EVENT, not a probe."""
    if pid <= 0 or pid > 0xFFFFFFFF:
        return False                                       # no such pid: a corrupt lock holds nothing
    if os.name == "nt":
        import ctypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        hnd = k32.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
        if not hnd:
            # ERROR_ACCESS_DENIED: the process exists under another account — alive, as POSIX
            # treats PermissionError. Anything else (no such process) is dead.
            return ctypes.get_last_error() == 5
        try:
            code = ctypes.c_ulong()
            return bool(k32.GetExitCodeProcess(hnd, ctypes.byref(code))) and code.value == 259
        finally:
            k32.CloseHandle(hnd)
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


@contextlib.contextmanager
def the_floor(root: str) -> Iterator[None]:
    """The heavy gate runs alone (the same lock file tools/check.py takes)."""
    lock = os.path.join(root, ".gate.lock")
    for _ in range(2):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)     # atomic: one holder only
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(f"{os.getpid()} harness.py\n")
            break
        except FileExistsError:
            try:
                with open(lock, encoding="utf-8") as fh:
                    pid = int((fh.read().split() or ["0"])[0])
            except (OSError, ValueError):
                pid = 0
            if _pid_alive(pid):
                raise HarnessError(f"another heavy job holds the floor (pid {pid}); the gate runs alone. "
                                   f"Wait, or remove {lock} if you know it is dead.")
            try:
                os.remove(lock)                                        # stale: reclaim, then retry
            except OSError:
                pass
    else:
        raise HarnessError(f"could not take the floor at {lock}")
    try:
        yield
    finally:
        try:
            with open(lock, encoding="utf-8") as fh:
                mine = int((fh.read().split() or ["0"])[0]) == os.getpid()
            if mine:
                os.remove(lock)
        except (OSError, ValueError):
            pass


# ------------------------------------------------------------------------------------- ledger

class Ledger:
    def __init__(self, root: str, run: str):
        if not _ID.match(run):
            raise HarnessError(f"run id {run!r}: use lowercase letters, digits, '.', '_' or '-'")
        self.root, self.run = root, run
        self.rel = f"{RUNS_REL}/{run}.jsonl"
        self.path = os.path.join(root, *self.rel.split("/"))

    def exists(self) -> bool:
        return os.path.isfile(self.path)

    def events(self) -> List[dict]:
        if not self.exists():
            raise HarnessError(f"no run {self.run!r} — open it first")
        with open(self.path, encoding="utf-8") as fh:
            return [json.loads(ln) for ln in fh if ln.strip()]

    def append(self, ev: dict) -> dict:
        ev = {"ts": _now(), **ev}
        line = json.dumps(ev, ensure_ascii=False, sort_keys=True)
        kind = secret_kind(line)
        if kind:
            raise HarnessError(f"the ledger is public and never carries a secret: this event holds {kind}")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line + "\n")
        return ev

    # --- reading
    def plan(self) -> Tuple[int, dict]:
        evs = self.events()
        idx = [i for i, e in enumerate(evs) if e["ev"] == "plan"]
        if not idx:
            raise HarnessError("the run has no plan")
        return idx[-1], evs[idx[-1]]

    def plan_approved(self) -> bool:
        i, plan = self.plan()
        later = [e for e in self.events()[i + 1:] if e["ev"] == "verdict" and e["step"] == "plan"]
        return bool(later) and later[-1]["pass"] and bool(_CHECKER.match(later[-1]["by"]))

    def steps(self) -> Dict[str, dict]:
        return {e["step"]: e for e in self.events() if e["ev"] == "step"}

    def step(self, sid: str) -> dict:
        st = self.steps().get(sid)
        if st is None:
            raise HarnessError(f"no step {sid!r} in run {self.run!r}")
        return st

    def of(self, _ev: str, sid: Optional[str] = None, **match) -> List[dict]:
        """Events of one type (optionally for one step), matching every given field."""
        return [e for e in self.events() if e["ev"] == _ev and (sid is None or e.get("step") == sid)
                and all(e.get(k) == v for k, v in match.items())]

    def _indexed(self, sid: str) -> List[Tuple[int, dict]]:
        return [(i, e) for i, e in enumerate(self.events()) if e.get("step") == sid]

    def closed(self, sid: str) -> bool:
        """Closed — unless a FAIL verdict came after the close, which voids it."""
        ev = self._indexed(sid)
        closes = [i for i, e in ev if e["ev"] == "close"]
        if not closes:
            return False
        return not any(i > closes[-1] and e["ev"] == "verdict" and not e["pass"] for i, e in ev)

    def state(self, sid: str) -> str:
        if self.of("abandon", sid):
            return "abandoned"
        if self.of("commit", sid):
            return "committed"
        if self.closed(sid):
            return "closed"
        if self.failed_rounds(sid) >= MAX_ROUNDS:
            return "BLOCKED"
        v = self.of("verdict", sid)
        if v and not v[-1]["pass"]:
            return "fixing"
        if self.of("gate", sid, role="checker", **{"pass": True}):
            return "checked"
        if self.of("gate", sid, role="builder", **{"pass": True}):
            return "built"
        return "open"

    def failed_rounds(self, sid: str) -> int:
        return sum(1 for e in self.of("verdict", sid) if not e["pass"])


# ----------------------------------------------------------------------------------- commands

def cmd_open(root: str, run: str, goal: str, done: Sequence[str]) -> dict:
    L = Ledger(root, run)
    if L.exists():
        raise HarnessError(f"run {run!r} already exists — replan it instead")
    stuck = blocked_anywhere(root)
    if stuck:
        raise HarnessError(f"{stuck[0]} is BLOCKED and waits for a human — no new run opens past it")
    if not goal.strip() or not done:
        raise HarnessError("a run needs a goal and at least one done criterion (how the gates will prove it)")
    L.append({"ev": "open", "by": "lead", "head": head(root)})
    return L.append({"ev": "plan", "by": "lead", "goal": goal, "done": list(done)})


def cmd_replan(root: str, run: str, goal: str, done: Sequence[str]) -> dict:
    L = Ledger(root, run)
    L.events()
    if not goal.strip() or not done:
        raise HarnessError("a plan needs a goal and at least one done criterion")
    return L.append({"ev": "plan", "by": "lead", "goal": goal, "done": list(done)})


def cmd_step(root: str, run: str, sid: str, owner: str, claim: str, scope: Sequence[str],
             tests: Sequence[str], adopt: bool = False) -> dict:
    L = Ledger(root, run)
    if not _ID.match(sid) or sid in RESERVED:
        raise HarnessError(f"step id {sid!r} is not allowed")
    _name(owner, _BUILDER, "a builder (a step is owned by a builder, never by the lead)")
    if not L.plan_approved():
        raise HarnessError("no step opens before a checker has passed the plan")
    if sid in L.steps():
        raise HarnessError(f"step {sid!r} already exists")
    unfinished = [s for s in L.steps() if L.state(s) not in ("committed", "abandoned")]
    if unfinished:
        raise HarnessError(f"one step at a time: {unfinished[0]!r} is still {L.state(unfinished[0])}")
    if not claim.strip() or not scope or not tests:
        raise HarnessError("a step needs a claim, a scope, and at least one test that pins it")
    base = head(root)
    dirty = changed_paths(root, base)
    if dirty and not adopt:
        raise HarnessError("a step opens on a clean tree (or with --adopt, recorded as such): "
                           + ", ".join(dirty[:8]))
    return L.append({"ev": "step", "step": sid, "owner": owner, "by": owner, "claim": claim,
                     "scope": list(scope), "tests": list(tests), "base": base,
                     "adopted": sorted(dirty) if adopt else []})


def cmd_gate(root: str, run: str, sid: str, role: str, by: str) -> Tuple[bool, dict]:
    L = Ledger(root, run)
    st = L.step(sid)
    state = L.state(sid)
    if state in ("closed", "committed", "abandoned"):
        raise HarnessError(f"step {sid!r} is {state}")
    if state == "BLOCKED":
        raise HarnessError(f"step {sid!r} is BLOCKED after {MAX_ROUNDS} failed verdicts — the lead "
                           f"stops and a human decides")
    if role == "builder":
        if by != st["owner"]:
            raise HarnessError(f"one owner per step: only {st['owner']} builds {sid!r}")
    elif role == "checker":
        _name(by, _CHECKER, "a checker (the owner never grades its own step; the lead never grades)")
    else:
        raise HarnessError("role is builder or checker")
    base = st["base"]
    tracked, untracked = _changes(root, base)
    paths = sorted(set(tracked) | set(untracked))
    h = diff_hash(root, base, paths)
    checks: Dict[str, dict] = {}
    checks["content"] = check_content(root, paths)
    checks["scope"] = check_scope(paths, st["scope"])
    checks["forbidden"] = check_forbidden(root, base, paths, st["scope"])
    checks["machinery"] = check_machinery(root, base, paths)
    checks["shadowing"] = check_shadowing(root, paths)
    added = added_lines(root, base, tracked, untracked)
    checks["secrets"] = check_secrets(added)
    checks["hygiene"] = check_hygiene(root, added, paths)
    checks["manifest"] = check_manifest(root, base)
    cheap = all(c["ok"] for c in checks.values())
    if role == "builder":
        # The builder's tests run where the checker's do — a fresh worktree holding the commit-to-be —
        # so one checkout serves every role, and no local keeping or ignored file can sway a result.
        with the_floor(root), candidate(root, base) as wt:
            fresh(root, wt, paths)
            checks["tests"] = check_step_tests(wt, st["tests"])
    elif not cheap:
        checks["tests"] = _fail(["not run: an earlier check failed"])
    else:
        # Grade the commit-to-be, not the checkout: base + exactly the step's paths.
        # Every stage starts from a freshly reset worktree: nothing one stage writes reaches the next.
        with the_floor(root), candidate(root, base) as wt:
            fresh(root, wt, [p for p in paths if p.startswith("tests/")])
            checks["pins"] = check_pins(wt, paths, st["tests"])
            fresh(root, wt, paths)
            checks["tests"] = check_step_tests(wt, st["tests"])
            if checks["tests"]["ok"]:
                fresh(root, wt, paths)
                checks["suite"] = check_suite(wt, root, base)
                fresh(root, wt, paths)
                checks["moat"] = check_moat(wt, root, base)
            else:
                checks["suite"] = _fail(["not run: the step's own tests failed"])
    if diff_hash(root, base) != h:
        checks["stable"] = _fail(["the tree changed while the gate ran"])
    ok = all(c["ok"] for c in checks.values())
    full = role == "checker" and all(k in checks for k in ("pins", "suite", "moat"))
    ev = L.append({"ev": "gate", "step": sid, "role": role, "by": by, "pass": ok, "diff": h,
                   "paths": paths, "full": full, "checks": checks})
    return ok, ev


def cmd_verdict(root: str, run: str, target: str, by: str, passed: bool, findings: Sequence[str]) -> dict:
    L = Ledger(root, run)
    _name(by, _CHECKER, "a checker (only a checker records a verdict; the lead never grades)")
    if not passed and not findings:
        raise HarnessError("a FAIL carries at least one finding — what breaks, and the input that breaks it")
    if target == "plan":
        L.plan()
        return L.append({"ev": "verdict", "step": "plan", "by": by, "pass": passed,
                         "findings": list(findings)})
    if target == "live":
        evs = L.events()
        ships = [e for e in evs if e["ev"] == "note" and e.get("kind") == "ship"]
        if not ships or not ships[-1].get("pass"):
            raise HarnessError("nothing has shipped (the last ship note must pass) — no live verdict yet")
        return L.append({"ev": "verdict", "step": "live", "by": by, "pass": passed,
                         "findings": list(findings), "head": head(root)})
    st = L.step(target)
    if by == st["owner"]:
        raise HarnessError("the owner never grades its own step")
    if L.state(target) in ("committed", "abandoned"):
        raise HarnessError(f"step {target!r} is {L.state(target)} — open a new step to change it")
    h = diff_hash(root, st["base"])
    if passed:
        mine = L.of("gate", target, role="checker", by=by)
        if not mine or not mine[-1]["pass"] or mine[-1]["diff"] != h or not mine[-1].get("full"):
            raise HarnessError("a PASS rests on a gate: run your own full checker gate on exactly this "
                               "content first")
    return L.append({"ev": "verdict", "step": target, "by": by, "pass": passed, "diff": h,
                     "findings": list(findings)})


def close_problems(root: str, L: Ledger, sid: str) -> List[str]:
    st = L.step(sid)
    owner, base = st["owner"], st["base"]
    state = L.state(sid)
    if state in ("closed", "committed", "abandoned", "BLOCKED"):
        return [f"step {sid!r} is {state}"]
    why: List[str] = []
    if not L.plan_approved():
        why.append("the plan has no passing checker verdict")
    h = diff_hash(root, base)
    bg = L.of("gate", sid, role="builder", by=owner)
    if not bg or not bg[-1]["pass"] or bg[-1]["diff"] != h:
        why.append("no passing builder gate by the owner on the current content")
    cg = [g for g in L.of("gate", sid, role="checker") if g["by"] != owner and _CHECKER.match(g["by"])]
    if not cg or not cg[-1]["pass"] or cg[-1]["diff"] != h or not cg[-1].get("full"):
        why.append("no passing full checker gate on the current content")
    v = L.of("verdict", sid)
    if not v or not v[-1]["pass"] or v[-1].get("diff") != h:
        why.append("no passing checker verdict on the current content")
    elif cg and v[-1]["by"] != cg[-1]["by"]:
        why.append("the verdict's author did not run the checker gate it rests on")
    if head(root) != base:
        why.append("HEAD moved since the step opened — the step's diff is no longer its own")
    return why


def cmd_close(root: str, run: str, sid: str) -> dict:
    L = Ledger(root, run)
    why = close_problems(root, L, sid)
    if why:
        raise HarnessError("close refused: " + "; ".join(why))
    st = L.step(sid)
    return L.append({"ev": "close", "step": sid, "by": "lead", "diff": diff_hash(root, st["base"])})


def _staged(root: str) -> List[str]:
    return sorted(p for p in _git(root, "diff", "--cached", "--name-only", "-z").split("\0") if p)


def verify_commit(root: str, parent: str, paths: Sequence[str], extra: Sequence[str]) -> List[str]:
    """Does HEAD hold exactly `paths` (+ `extra`) over `parent`, byte for byte, with no mode change?"""
    why: List[str] = []
    if _git(root, "rev-parse", "HEAD^", check=False).strip() != parent:
        why.append("the commit's parent is not the step's base")
    raw = [x for x in _git(root, "diff-tree", "-r", "--no-commit-id", "--raw", "-z", "--no-renames",
                           parent, "HEAD").split("\0")]
    entries: Dict[str, Tuple[str, str, str]] = {}
    i = 0
    while i + 1 < len(raw):
        meta, p = raw[i], raw[i + 1]
        i += 2
        if not meta.startswith(":"):
            continue
        old_mode, new_mode, _, _, status = meta[1:].split()[:5]
        entries[p] = (old_mode, new_mode, status)
    expect = set(paths) | set(extra)
    if set(entries) != expect:
        why.append(f"the commit holds {sorted(set(entries) - expect)} and lacks {sorted(expect - set(entries))}")
    for p, (old_mode, new_mode, status) in entries.items():
        if status.startswith("M") and old_mode != new_mode:
            why.append(f"{p}: its mode changed ({old_mode} → {new_mode})")
        if status.startswith("A") and new_mode not in ("100644", "100755"):
            why.append(f"{p}: added as mode {new_mode} (only plain files are step content)")
    for p in paths:
        full = os.path.join(root, p)
        if os.path.isfile(full):
            if _git(root, "hash-object", "--", p).strip() != _git(root, "rev-parse", f"HEAD:{p}", check=False).strip():
                why.append(f"{p}: the committed bytes are not the checked bytes")
        elif _git_ok(root, "cat-file", "-e", f"HEAD:{p}"):
            why.append(f"{p}: deleted in the tree but present in the commit")
    return why


def _scan_ledger(L: "Ledger") -> None:
    """The whole ledger file, line by line, before it is staged: a hand-added line is scanned too."""
    pats = _secret_patterns()
    with open(L.path, encoding="utf-8", errors="replace") as fh:
        for i, ln in enumerate(fh, 1):
            kind = secret_kind(ln, pats)
            if kind:
                raise HarnessError(f"{L.rel}:{i} carries {kind} — the ledger is public; nothing staged")


def _take_back(root: str, parent: str) -> None:
    _git(root, "reset", "-q", "--soft", parent, check=False)
    _git(root, "reset", "-q", check=False)


def cmd_commit(root: str, run: str, sid: str, message_file: str) -> dict:
    L = Ledger(root, run)
    st = L.step(sid)
    base = st["base"]
    state = L.state(sid)
    if state != "closed":
        raise HarnessError(f"step {sid!r} is {state} — only a closed step commits")
    closed = L.of("close", sid)[-1]
    paths = changed_paths(root, base)
    if head(root) != base:
        # Recovery: a commit that landed before its ledger line (a crash between the two).
        if _git(root, "rev-parse", "HEAD^", check=False).strip() == base:
            committed = [p for p in _git(root, "diff-tree", "-r", "--no-commit-id", "--name-only", "-z",
                                         "--no-renames", base, "HEAD").split("\0") if p and p != L.rel]
            if not verify_commit(root, base, committed, [L.rel]) and \
                    diff_hash(root, base, committed) == closed["diff"]:
                return L.append({"ev": "commit", "step": sid, "by": "lead", "sha": head(root),
                                 "paths": sorted(committed), "recovered": True})
        raise HarnessError("HEAD moved since the step opened")
    if diff_hash(root, base, paths) != closed["diff"]:
        raise HarnessError("the tree is not what was checked — re-run the loop")
    stray = [p for p in _staged(root) if p not in paths and p != L.rel]
    if stray:
        raise HarnessError("something else is staged: " + ", ".join(stray[:8]))
    if not os.path.isfile(message_file):
        raise HarnessError(f"no message file {message_file}")
    _scan_ledger(L)
    _git(root, "add", "-A", "--", *paths, L.rel)
    staged = _staged(root)
    if sorted(set(staged) - {L.rel}) != sorted(paths):
        _git(root, "reset", "-q", "--", *paths, L.rel, check=False)
        raise HarnessError(f"staged {staged} is not the step's {paths}")
    _git(root, "commit", "-q", "-F", message_file)
    why = verify_commit(root, base, paths, [L.rel])
    if why:
        _take_back(root, base)
        raise HarnessError("the commit was not the checked step, so it was taken back: " + "; ".join(why))
    return L.append({"ev": "commit", "step": sid, "by": "lead", "sha": head(root), "paths": paths})


def cmd_record(root: str, run: str, message_file: str) -> str:
    """Commit the ledger alone — the end of a run (the last commit event, ship, live) is evidence too."""
    L = Ledger(root, run)
    unfinished = [s for s in L.steps() if L.state(s) not in ("committed", "abandoned")]
    if unfinished:
        raise HarnessError(f"step {unfinished[0]!r} is {L.state(unfinished[0])} — record the ledger "
                           f"only when no step is in flight (a record would move HEAD under it)")
    stray = [p for p in _staged(root) if p != L.rel]
    if stray:
        raise HarnessError("something else is staged: " + ", ".join(stray[:8]))
    if not os.path.isfile(message_file):
        raise HarnessError(f"no message file {message_file}")
    _scan_ledger(L)
    parent = head(root)
    _git(root, "add", "--", L.rel)
    if not _staged(root):
        raise HarnessError("the ledger has nothing new to record")
    _git(root, "commit", "-q", "-F", message_file)
    why = verify_commit(root, parent, [], [L.rel])
    if why:
        _take_back(root, parent)
        raise HarnessError("the record commit held more than the ledger, so it was taken back: " + "; ".join(why))
    return head(root)


def cmd_abandon(root: str, run: str, sid: str, reason: str, human: bool = False) -> dict:
    """Abandon a step. A BLOCKED one only by a human's own hand (--human: agents never pass it)."""
    L = Ledger(root, run)
    st = L.step(sid)
    state = L.state(sid)
    if state in ("committed", "abandoned"):
        raise HarnessError(f"step {sid!r} is {state}")
    if state == "BLOCKED" and not human:
        raise HarnessError("a BLOCKED step waits for a human; it is not abandoned to reset its rounds")
    if changed_paths(root, st["base"]):
        raise HarnessError("put the tree back first (the abandoned work must not ride into the next step)")
    return L.append({"ev": "abandon", "step": sid, "by": "human" if human else "lead", "reason": reason})


def blocked_anywhere(root: str) -> List[str]:
    """Every BLOCKED step in every run — a new run does not open past one."""
    out: List[str] = []
    d = os.path.join(root, *RUNS_REL.split("/"))
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if f.endswith(".jsonl") and _ID.match(f[:-6]):
            L = Ledger(root, f[:-6])
            out += [f"{L.run}/{s}" for s in L.steps() if L.state(s) == "BLOCKED"]
    return out


def cmd_note(root: str, run: str, by: str, kind: str, text: str, passed: Optional[bool]) -> dict:
    L = Ledger(root, run)
    L.events()
    _name(by)
    if kind == "ship" and by != "lead":
        raise HarnessError("only the lead ships (through tools/deploy.sh, whose own gate grades it)")
    return L.append({"ev": "note", "by": by, "kind": kind, "text": text, "pass": passed, "head": head(root)})


def done_problems(root: str, L: Ledger) -> List[str]:
    why: List[str] = []
    if not L.plan_approved():
        why.append("the plan has no passing checker verdict")
    steps = L.steps()
    if not any(L.state(s) == "committed" for s in steps):
        why.append("no step has been committed")
    for s in steps:
        if L.state(s) not in ("committed", "abandoned"):
            why.append(f"step {s!r} is {L.state(s)}")
    evs = L.events()
    commits = [i for i, e in enumerate(evs) if e["ev"] == "commit"]
    ships = [i for i, e in enumerate(evs) if e["ev"] == "note" and e.get("kind") == "ship"]
    if not ships or (commits and ships[-1] < commits[-1]) or not evs[ships[-1]].get("pass"):
        why.append("no passing ship after the last commit (the latest ship note must pass)")
    else:
        lives = [i for i, e in enumerate(evs) if e["ev"] == "verdict" and e.get("step") == "live"]
        if not lives or lives[-1] < ships[-1] or not evs[lives[-1]]["pass"]:
            why.append("no passing live verdict by a checker after the last ship")
    return why


def cmd_status(root: str, run: str) -> str:
    L = Ledger(root, run)
    _, plan = L.plan()
    out = [f"RUN {run}", f"  goal: {plan['goal']}"]
    out += [f"  done when: {d}" for d in plan["done"]]
    out.append(f"  plan: {'APPROVED' if L.plan_approved() else 'NOT YET APPROVED'}")
    for v in L.of("verdict", "plan")[-1:]:
        out += [f"    plan finding: {f}" for f in v["findings"]]
    for sid, st in L.steps().items():
        out.append(f"  [{L.state(sid)}] {sid} — owner {st['owner']} — base {st['base'][:10]}")
        out.append(f"      claim: {st['claim']}")
        out.append(f"      scope: {', '.join(st['scope'])} | tests: {', '.join(st['tests'])}")
        for g in L.of("gate", sid)[-2:]:
            out.append(f"      gate {g['role']} by {g['by']}: {'PASS' if g['pass'] else 'FAIL'} @ {g['diff'][:12]}")
        for v in L.of("verdict", sid)[-1:]:
            out.append(f"      verdict by {v['by']}: {'PASS' if v['pass'] else 'FAIL'}"
                       + "".join(f"\n        - {f}" for f in v["findings"]))
        for c in L.of("commit", sid):
            out.append(f"      commit {c['sha'][:10]}")
    for n in L.of("note"):
        out.append(f"  note {n['kind']} by {n['by']}: {n['text']}"
                   + ("" if n.get("pass") is None else (" — PASS" if n["pass"] else " — FAIL")))
    for v in L.of("verdict", "live"):
        out.append(f"  live verdict by {v['by']}: {'PASS' if v['pass'] else 'FAIL'}"
                   + "".join(f"\n    - {f}" for f in v["findings"]))
    why = done_problems(root, L)
    out.append("  RUN COMPLETE" if not why else "  open: " + "; ".join(why))
    return "\n".join(out)


def cmd_brief(root: str, run: str, sid: str) -> str:
    """What a checker needs, and nothing of the builder's narrative."""
    L = Ledger(root, run)
    st = L.step(sid)
    paths = changed_paths(root, st["base"])
    _, plan = L.plan()
    graders = [p for p in paths if any(fnmatch.fnmatchcase(p, g) for g in MACHINERY)
               or p in (MANIFEST_REL, BASELINE_REL) or shadowing(p)]
    return "\n".join([
        f"RUN {run} — goal: {plan['goal']}",
        f"STEP {sid} — owner {st['owner']} — state {L.state(sid)}",
        f"claim: {st['claim']}",
        f"scope: {', '.join(st['scope'])}",
        f"tests: {', '.join(st['tests'])}",
        f"base: {st['base']}   (review with: git diff {st['base'][:12]} -- . ; new files listed below)",
        f"changed now ({len(paths)}): " + ", ".join(paths),
        f"adopted at open: {', '.join(st.get('adopted') or []) or 'none'}",
        f"GRADERS TOUCHED — read these first: {', '.join(graders)}" if graders else "graders touched: none",
        f"content hash now: {diff_hash(root, st['base'], paths)[:16]}",
        f"failed rounds so far: {L.failed_rounds(sid)} of {MAX_ROUNDS}",
    ] + [f"previous finding: {f}" for v in L.of("verdict", sid) if not v["pass"] for f in v["findings"]])


def cmd_measure(root: str) -> str:
    """Baseline lines for the commit-to-be (HEAD + the working changes), measured exactly as the
    checker's suite stage measures — a fresh worktree, -vv, the vacuity plugin. Bootstrap only."""
    base = head(root)
    paths = changed_paths(root, base)
    with the_floor(root), candidate(root, base) as wt:
        fresh(root, wt, paths)
        run = run_pytest(wt, ["tests"], SUITE_TIMEOUT, vacuity=True, verbose=True)
    if run.disagreement():
        raise HarnessError(run.disagreement())
    lines = [f"# measured at {base[:10]} + {len(paths)} working change(s): {counts(run.results)} — {run.tail}"]
    lines += [f"{n} | {fingerprint(run.messages.get(n, ''))}" for n, o in sorted(run.results.items())
              if o in ("failed", "error")]
    lines += [f"vacuous {n}" for n in sorted(run.vacuous or ())]
    if run.vacuous is None:
        lines.append("# (no vacuity report: tools/vacuity_plugin.py absent or it did not write)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------- cli

def split_ids(s: Optional[str]) -> List[str]:
    """Comma-separated ids, where commas inside [...] (a parametrized id) do not split."""
    out, cur, depth = [], "", 0
    for ch in s or "":
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


def _print_gate(ok: bool, ev: dict) -> None:
    for name, c in ev["checks"].items():
        mark = "PASS" if c["ok"] else "FAIL"
        d = c["detail"]
        if isinstance(d, list):
            print(f"  {mark} {name}")
            for x in d:
                print(f"       - {x}")
        else:
            print(f"  {mark} {name}: {d}")
    print(f"=== HARNESS GATE {'PASS' if ok else 'FAIL'} ({ev['role']} {ev['by']}, step {ev['step']}, "
          f"content {ev['diff'][:12]}) ===")


def _norm(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def _self_digest() -> str:
    with open(os.path.abspath(__file__), "rb") as fh:
        return hashlib.sha256(_norm(fh.read())).hexdigest()


def _committed_harness(root: str) -> Optional[Tuple[str, str]]:
    """If this copy is not HEAD's tools/harness.py: (a temp copy of HEAD's, its digest). Else None."""
    r = subprocess.run(["git", "show", f"HEAD:{SELF_REL}"], cwd=root, capture_output=True)
    if r.returncode != 0:
        return None                                   # no committed harness (bootstrap, or not a repo)
    digest = hashlib.sha256(_norm(r.stdout)).hexdigest()
    if digest == _self_digest():
        return None
    td = tempfile.mkdtemp(prefix="harness-head-")
    path = os.path.join(td, "harness.py")
    with open(path, "wb") as fh:
        fh.write(r.stdout)
    return path, digest


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = os.environ.get("HARNESS_ROOT") or ROOT
    # No escape hatch: HEAD's own copy matches HEAD and so never re-executes; every other copy does.
    # (A working copy edited to skip this very check is the one thing no file can guard against —
    # which is why the checker reads `git diff --name-only BASE` with git itself, before the gate.)
    other = _committed_harness(root)
    if other:
        path, _ = other
        print("(this working copy of tools/harness.py is not HEAD's — running HEAD's: a step never "
              "grades itself with its own harness)", file=sys.stderr)
        env = dict(os.environ, HARNESS_ROOT=root)
        env.pop("HARNESS_REEXEC", None)
        try:
            return subprocess.call([sys.executable, path, *argv], env=env)
        finally:
            shutil.rmtree(os.path.dirname(path), ignore_errors=True)
    ap = argparse.ArgumentParser(prog="harness", description=(__doc__ or "").split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("open", "replan"):
        p = sub.add_parser(name)
        p.add_argument("run")
        p.add_argument("--goal", required=True)
        p.add_argument("--done", action="append", default=[])
    p = sub.add_parser("step")
    p.add_argument("run"); p.add_argument("step")
    p.add_argument("--owner", required=True); p.add_argument("--claim", required=True)
    p.add_argument("--scope", required=True); p.add_argument("--tests", required=True)
    p.add_argument("--adopt", action="store_true")
    p = sub.add_parser("gate")
    p.add_argument("run"); p.add_argument("step")
    p.add_argument("--role", required=True, choices=("builder", "checker"))
    p.add_argument("--by", required=True)
    p = sub.add_parser("verdict")
    p.add_argument("run"); p.add_argument("step")
    p.add_argument("--by", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--pass", dest="passed", action="store_true")
    g.add_argument("--fail", dest="failed", action="store_true")
    p.add_argument("--finding", action="append", default=[])
    for name in ("close", "status", "brief", "done"):
        p = sub.add_parser(name)
        p.add_argument("run")
        if name in ("close", "brief"):
            p.add_argument("step")
    for name in ("commit", "record"):
        p = sub.add_parser(name)
        p.add_argument("run")
        if name == "commit":
            p.add_argument("step")
        p.add_argument("-F", dest="message", required=True)
    p = sub.add_parser("abandon")
    p.add_argument("run"); p.add_argument("step"); p.add_argument("--reason", required=True)
    p.add_argument("--human", action="store_true", help="a human releasing a BLOCKED step; agents never pass it")
    p = sub.add_parser("note")
    p.add_argument("run"); p.add_argument("--by", required=True); p.add_argument("--kind", required=True)
    p.add_argument("--text", required=True)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--pass", dest="passed", action="store_true")
    g.add_argument("--fail", dest="failed", action="store_true")
    sub.add_parser("measure")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "open":
            cmd_open(root, a.run, a.goal, a.done)
            print(f"opened {a.run} — a checker reviews the plan before any step opens")
        elif a.cmd == "replan":
            cmd_replan(root, a.run, a.goal, a.done)
            print(f"replanned {a.run} — the new plan needs a checker's verdict")
        elif a.cmd == "step":
            ev = cmd_step(root, a.run, a.step, a.owner, a.claim, split_ids(a.scope), split_ids(a.tests), a.adopt)
            print(f"step {a.step} opened at {ev['base'][:10]}, owned by {a.owner}")
        elif a.cmd == "gate":
            ok, ev = cmd_gate(root, a.run, a.step, a.role, a.by)
            _print_gate(ok, ev)
            return 0 if ok else 1
        elif a.cmd == "verdict":
            cmd_verdict(root, a.run, a.step, a.by, bool(a.passed), a.finding)
            print(f"verdict on {a.step} by {a.by}: {'PASS' if a.passed else 'FAIL'}")
        elif a.cmd == "close":
            ev = cmd_close(root, a.run, a.step)
            print(f"closed {a.step} at content {ev['diff'][:12]}")
        elif a.cmd == "commit":
            ev = cmd_commit(root, a.run, a.step, a.message)
            print(f"committed {a.step} as {ev['sha'][:10]} ({len(ev['paths'])} path(s))")
        elif a.cmd == "record":
            print(f"recorded the ledger as {cmd_record(root, a.run, a.message)[:10]}")
        elif a.cmd == "abandon":
            cmd_abandon(root, a.run, a.step, a.reason, a.human)
            print(f"abandoned {a.step}")
        elif a.cmd == "note":
            p = True if a.passed else (False if a.failed else None)
            cmd_note(root, a.run, a.by, a.kind, a.text, p)
            print(f"noted {a.kind}")
        elif a.cmd == "status":
            print(cmd_status(root, a.run))
        elif a.cmd == "brief":
            print(cmd_brief(root, a.run, a.step))
        elif a.cmd == "done":
            why = done_problems(root, Ledger(root, a.run))
            print("RUN COMPLETE" if not why else "RUN INCOMPLETE:\n  - " + "\n  - ".join(why))
            return 0 if not why else 1
        elif a.cmd == "measure":
            print(cmd_measure(root))
    except HarnessError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
