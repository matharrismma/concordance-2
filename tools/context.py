#!/usr/bin/env python3
"""THE RECORDS — the harness's working context, kept as files a machine reads and a stranger can check.

A builder, a checker, a new session or the lead after a compaction gets its working context from
RECORDS (tracked files and the harness's append-only ledgers), never from memory or a transcript,
and every line it is given names the record it came from (run 2026-11-03-assemble-reapply). This
module holds the records format: the parser for docs/harness/RULES.md (the standing rules) and
docs/harness/BACKLOG.md (the wants), the pointer grammar both use, the scan that keeps private
words out of them, and the private configuration directory that scan reads.

THE FILES. RULES.md and BACKLOG.md share one layout:

    # Any title                          the preamble: the prose before the first entry (not parsed)

    ## <id>                              an entry: '## ' and an id — lowercase letters and digits in
    - scope: all                         hyphen-joined words, at most 64 characters, unique in its file
    - source: <pointer>                  one field per line, '- <name>: <value>', any order, each once
    - check: <how a checker decides held or failed>          RULES.md
    - status: open|filed-as-run|done|refused                 BACKLOG.md
    > The verbatim words, one '> ' line  the text: one contiguous block, '>' alone an empty line, never
    > each.                              starting or ending with an empty line

A scope is 'all' or one repository from PUBLIC_REPOS. Blank lines may stand anywhere in an entry
except inside its text. Any other line in an entry is refused, and so is any preamble line that
reads as an entry's field (scope, source, check, status) or text ('>'), even indented: an entry
under a wrong heading is refused, never skipped, so nothing in the file escapes the parser. Line
endings and a byte-order mark never change what is parsed.

THE POINTER GRAMMAR. A source is exactly one of four kinds, fields separated by single spaces:

    LEDGER <repo> <run> <line>                  the 1-based line of the run's append-only .jsonl in
                                                <repo> (never a timestamp: events share them)
    FILE <repo> <path> <sha> "<anchor>"         the anchor, verbatim, occurs in <path> at commit <sha>
                                                (40 hex; never path:line; the anchor runs to the
                                                pointer's last quote)
    ORIGIN <YYYY-MM-DD> <who>                   a want first filed in BACKLOG.md itself, and its filer
                                                (owner, lead, builder-N or checker-N)
    OWNER owner, chat, <YYYY-MM-DD> "<words>"   the owner's words, quoted

<repo> is one of PUBLIC_REPOS, <run> a harness run id, <path> repo-relative with '/' separators. A
rule's source is LEDGER, FILE or OWNER; a want's is LEDGER, FILE or ORIGIN (a public record where one
exists, its first filing where none does). LEDGER and FILE pointers resolve against a record; ORIGIN
and OWNER pointers are unresolvable by kind.

THE SCAN names the line and the kind of every hit, never the matched text: absolute paths (a drive
letter, a Git Bash drive like /c/, /home/, /Users/, /tmp/), IPv4 and IPv6 addresses, e-mail
addresses, ssh key file names (id_rsa and its kin, *.pem, *.ppk), the harness's secret patterns,
and every word of the private-names file (case-insensitive, as a whole word).

THE PRIVATE CONFIGURATION lives outside the repo, in one directory: HARNESS_CONFIG_DIR when it is
set (set but empty means no directory at all), else ~/.config/harness. On Windows Python finds '~'
through USERPROFILE, so pointing HOME elsewhere hides nothing; the override does. With the override
set, the default directory is never computed, so it is never opened. The directory may hold three
files, where '#' lines and blank lines are skipped and any of them, or the directory, may be absent:

    private_names.txt    words the scan rejects. Every whitespace-separated word is its own entry,
                         so list each joined form of a name explicitly (a-b, a_b, ab), and never a
                         phrase whose common word would then become private.
    secret_patterns.txt  one regex a line: the file the harness reads from its own default directory.
    roots.txt            '<repo> <absolute path of its local checkout>' a line, the repo name first,
                         the rest of the line the path; a repo listed twice is refused.

The harness's own HARNESS_SECRET_PATTERNS file is not read here: the harness also reads its default
file whenever that override is set, so this module builds its own list (the harness's built-in
patterns, then this directory's file) and hands it to harness.secret_kind.

CHECK. `python tools/context.py check [ROOT]` reads ROOT's RULES.md and BACKLOG.md (ROOT is the
concordance-2 checkout holding them; by default the one this file is in), says which configuration
directory it used ('none' when there is none) and what it held, scans both files, parses them, and
resolves every pointer: a LEDGER pointer when its run's ledger in that repo's checkout (ROOT for
concordance-2, else the roots file) has that line and it is an event; a FILE pointer when the
commit is in that checkout and the file at that commit holds the anchor. A rule's text must also
occur verbatim, whitespace aside, in what its source names (the file at that commit, the ledger
event's strings, or the owner's quoted words). It prints every pointer that does not resolve and
every rule that is not verbatim, and lists ORIGIN and OWNER pointers as unresolvable by kind; an
entry the scan hits is named by its line only. Exit 0 when nothing is unresolved, unquoted or hit;
1 when something is; 2 when the records or the configuration cannot be read.

BRIEF. `python tools/context.py brief --role builder|checker|lead [--wants-cap N] ROOT RUN [STEP]`
assembles a role's working context from records. ROOT is the checkout holding the run's ledger: this
concordance-2 checkout, or a public repository's checkout the roots file names. RULES.md, BACKLOG.md
and the harness (its Ledger class, cmd_brief and done_problems) are read through git from one
concordance-2 commit, never the working copy: for a step of a run in concordance-2, the step's base,
so no step can change the brief its own checker receives; otherwise concordance-2's HEAD. The
ledgers are read from their checkouts, since a run's ledger is append-only and uncommitted while the
run is open. The brief prints the commit it used, then:

    CORE       every rule in scope (all, or the run's repo), by id, its text verbatim on one line
    IN FLIGHT  every step not committed or abandoned in the public repositories' ledgers: repo,
               run, step, owner and state, never a path; a private repository is never read
    RUN        goal and criteria; for a builder the step's claim, scope, tests and previous
               findings; for a checker the harness's own cmd_brief instead (none of the builder's
               notes); for the lead every step's state; for every role what done_problems says
    WANTS      the open and filed-as-run wants of this run, its repo and all repos; past
               --wants-cap characters each prints as its pointer only (the cap never touches CORE)
    DUE        the clock, every rule in scope due under the schedule below, the confirmations
               listed but not counted, and the ones ignored with the reason

Every line quoted from a record ends with its pointer in brackets, resolved: one that does not
resolve prints UNRESOLVED, never dropped. A line quoted from a ledger that names a path or an
address (the path, IP, e-mail and ssh-key rules) prints as its pointer instead of its text. Then the
whole output is scanned: a private name or a secret pattern anywhere, or a path or an address in the
brief's own text, refuses the brief (exit 2), naming the line and the kind, never the word. brief
also refuses when tools/context.py differs from HEAD; check never does.

THE SCHEDULE. A confirmation is a ledger note of kind confirm reading 'RULE <id> held|failed:
<evidence>', by a checker-N with a verdict in the same ledger; any other is ignored and listed, as
is one naming no rule of the records commit or a ledger outside the rule's scope. THE CLOCK: a run
completes at its last passing live verdict once the harness's done_problems is empty; completed
runs are ordered by that time, ties by repo name, then run id. A rule's entry, its run 0, is the
time of the first commit, along first-parent history, whose RULES.md holds it; its runs are the
runs in its scope (all public
repositories, or its one repo) completed after that. A confirmation at time t sits in run 1 + those
completed before t, so a run that stalls never pins it; a brief is assembled after every record it
reads, so it sits in run 1 + all of them. THE GEAR: a rule at interval index i (from 1) whose last
counted confirmation is in run c is due in run n when n - c >= F(i+1): 1, 2, 3, 5, 8, ...; held
while due sets c = n and i = i + 1, failed sets c = n and i = 1 at any time, and anything else is
listed, not counted. A rule never confirmed must be checked soon, so its first due run (c = start - 1
at entry) is staggered over at most the first 13 runs after its entry (F(7)): the j-th rule ever
entered first falls due in run 1 + floor(frac(j*phi) * 13). j is frozen at entry, the rule's place
among all rules ever entered in RULES.md's first-parent history, by the commit that first added
it, then id; with the spread fixed at 13, adding or removing a rule never moves another's start.
For today's 30 rules, every rule held and confirmed whenever due, at most 9 are due in any one of
the first 100 runs, and the longest wait for a first check is 13 runs. Old versions of RULES.md are
read by their '## <id>' headings alone, never by the parser, so a change to the file's format can
never change what an old version entered. All of this needs RULES.md's whole history: in a shallow
clone, when git cannot give it, or when a version is not text, DUE is one line saying the schedule
is not computed, and no start or due rule is printed; the other sections print as usual.

CI. `python tools/context.py ci OWNER/REPO SHA` reads a commit's CI and changes nothing: it runs `gh
run list` and `gh run view` and no other gh command, ever. SHA is the full 40-hex id, and a run gh
lists on any other commit is ignored and counted as ignored. It prints each run, each job's
conclusion, and pytest's summary lines from that job's log ('SUITE none' for a log with none). Exit 0,
CI GREEN, needs at least one run on that commit, every run and every job of it completed with
conclusion success (skipped, cancelled or neutral is not green), every finished job's log readable, at
least one suite count line among them, and every count line in a successful job showing a test passed
and no failure or error. A line that passed nothing (no tests ran, or only skips or deselections) is a
suite that checked nothing, so it is not green beside any other job or line. A job that prints no count
line at all is named and changes nothing, since a job need not hold a suite. Anything else is exit 1, CI
NOT GREEN, saying why; exit 2, REFUSED, is a loose repository or commit, or a gh that gives no answer.
ci, like check, changes nothing and so never refuses on a modified tools/context.py.

RECORD. `python tools/context.py record ROOT RUN [-F MESSAGE_FILE]` carries out RULES.md's
record-a-run-from-a-worktree up to the push. ROOT is the checkout holding the run's ledger, in any
repository. It runs the procedure's steps (1) to (4) and (6): it asks origin for its default branch,
fetches, and confirms that branch is at the run's last pushed commit; adds a detached worktree there
in a temporary directory; copies the ledger in; runs harness record with HARNESS_ROOT at that worktree;
and compares the recorded ledger with the working copy, ignoring CRLF. It keeps the worktree, and
prints steps (5), (7) and (8), the push and the cleanup through bringing the checkout to the record
commit, and never runs one of them: only the lead pushes, and a printed line is read before it runs.
The printed commands compare the ledger once more after the push and before the discard, so a line
that reaches the ledger after this record stops the procedure instead of being discarded. Nothing in
ROOT changes but its remote-tracking refs and its list of worktrees.

The run's last pushed commit is the last commit event's sha, or the head of a rebase note after it,
since a rebase leaves the commit events at their old shas. Origin is at it when its default branch is
that commit, or when every commit above it touches this run's ledger and nothing else: the run's own
records, so a note written after a record is recorded on top of it. Any other commit above it, another
run's record, an empty commit or a pair that cancels out included, is not this run's last pushed
commit, and refuses.

record makes history, so it is conservative. It runs only from committed code: it refuses when
tools/context.py, or the tools/harness.py beside it that it will run, differs from that checkout's HEAD
or is not committed there, since whatever harness runs could do anything record says it will not. Exit
2, REFUSED, comes before anything is made, on those and on: a step in flight, a secret in the ledger, a
ledger naming no commit, origin anywhere else, a ledger with nothing new, or one that does not extend
origin's, which is a checkout lacking a record commit. Exit 1, RECORD FAIL, is a worktree add or a
harness record that failed, or a comparison that differs: no push is printed and the cleanup is. Exit 0
is RECORD PASS.
The harness that runs is the one beside this file, or the worktree's HEAD's when that differs, by the
harness's own rule; so a repository that tracks no harness is served too. Without -F the commit
message is one plain line naming the run.

Refusals name lines and fields, never a record's words. Stdlib only, like the harness it serves.
"""
from __future__ import annotations

import datetime
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

import harness

RULES_REL = "docs/harness/RULES.md"
BACKLOG_REL = "docs/harness/BACKLOG.md"
PUBLIC_REPOS = ("concordance-2", "Concordance-V3", "witness")     # each has a public remote
SCOPES = ("all",) + PUBLIC_REPOS
STATUSES = ("open", "filed-as-run", "done", "refused")
KINDS = ("LEDGER", "FILE", "ORIGIN", "OWNER")
RESOLVABLE = ("LEDGER", "FILE")
RULE_SOURCES = ("LEDGER", "FILE", "OWNER")
WANT_SOURCES = ("LEDGER", "FILE", "ORIGIN")

CONFIG_ENV = "HARNESS_CONFIG_DIR"
PRIVATE_NAMES_FILE = "private_names.txt"
SECRET_PATTERNS_FILE = "secret_patterns.txt"
ROOTS_FILE = "roots.txt"
SELF_REPO = "concordance-2"                                       # the repo RULES.md and BACKLOG.md live in
LOCAL_PATTERN = "a locally-declared private pattern"              # the harness's word for one


class RecordsError(ValueError):
    """A record that does not parse. The message names lines and fields, never the record's words."""

    def __init__(self, problems: Sequence[str]):
        self.problems = list(problems)
        super().__init__("\n".join(self.problems))


# ------------------------------------------------------------------------------- the pointer grammar

_FORMS = {
    "LEDGER": re.compile(r"LEDGER (?P<repo>\S+) (?P<run>\S+) (?P<line>\S+)"),
    "FILE": re.compile(r'FILE (?P<repo>\S+) (?P<path>\S+) (?P<sha>\S+) "(?P<anchor>.*)"'),
    "ORIGIN": re.compile(r"ORIGIN (?P<date>\S+) (?P<who>\S+)"),
    "OWNER": re.compile(r'OWNER owner, chat, (?P<date>\S+) "(?P<words>.*)"'),
}
_USAGE = {
    "LEDGER": "a LEDGER pointer reads: LEDGER <repo> <run> <line>",
    "FILE": 'a FILE pointer reads: FILE <repo> <path> <sha> "<anchor>"',
    "ORIGIN": "an ORIGIN pointer reads: ORIGIN <YYYY-MM-DD> <who>",
    "OWNER": 'an OWNER pointer reads: OWNER owner, chat, <YYYY-MM-DD> "<words>"',
}
_LINE = re.compile(r"[1-9][0-9]*")
_SHA = re.compile(r"[0-9a-f]{40}")
_DATE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
_SEGMENT = re.compile(r"[A-Za-z0-9_.+@-]+")
_WHO = re.compile(r"owner|lead|builder-[a-z0-9]+|checker-[a-z0-9]+")


@dataclass(frozen=True)
class Pointer:
    """One source pointer. Only the fields of its kind are set; render() gives it back verbatim."""
    kind: str
    repo: str = ""
    run: str = ""
    line: int = 0
    path: str = ""
    sha: str = ""
    anchor: str = ""
    date: str = ""
    who: str = ""
    words: str = ""

    @property
    def resolvable(self) -> bool:
        """LEDGER and FILE pointers name a record to check; ORIGIN and OWNER are unresolvable by kind."""
        return self.kind in RESOLVABLE

    def render(self) -> str:
        if self.kind == "LEDGER":
            return f"LEDGER {self.repo} {self.run} {self.line}"
        if self.kind == "FILE":
            return f'FILE {self.repo} {self.path} {self.sha} "{self.anchor}"'
        if self.kind == "ORIGIN":
            return f"ORIGIN {self.date} {self.who}"
        return f'OWNER owner, chat, {self.date} "{self.words}"'


def _valid_date(text: str) -> bool:
    m = _DATE.fullmatch(text)
    if not m:
        return False
    try:
        datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return False
    return True


def _path_problem(path: str) -> Optional[str]:
    if re.search(r":[0-9]+$", path):
        return "a FILE pointer names a path and a verbatim anchor, never path:line"
    if any(not _SEGMENT.fullmatch(s) or s in (".", "..") for s in path.split("/")):
        return ("a FILE pointer's path is repo-relative, '/'-separated, with no empty, '.' or '..' "
                "segment and no other characters than letters, digits and _ . + @ -")
    return None


def parse_pointer(text: str) -> Pointer:
    """The pointer `text` names, or RecordsError. Exactly the grammar above: nothing before, after or between."""
    kind = text.split(" ", 1)[0] if isinstance(text, str) else ""
    form = _FORMS.get(kind)
    if form is None:
        raise RecordsError(["a pointer begins LEDGER, FILE, ORIGIN or OWNER, in capitals"])
    m = form.fullmatch(text)
    if m is None:
        raise RecordsError([_USAGE[kind] + " (single spaces, nothing after it)"])
    g = m.groupdict()
    if "repo" in g and g["repo"] not in PUBLIC_REPOS:
        raise RecordsError([f"a {kind} pointer names a repository with a public remote: "
                            + ", ".join(PUBLIC_REPOS)])
    if kind == "LEDGER":
        if not harness._ID.fullmatch(g["run"]):
            raise RecordsError(["a LEDGER pointer's run is a harness run id"])
        if not _LINE.fullmatch(g["line"]):
            raise RecordsError(["a LEDGER pointer names a 1-based line number, never a timestamp"])
        return Pointer("LEDGER", repo=g["repo"], run=g["run"], line=int(g["line"]))
    if kind == "FILE":
        why = _path_problem(g["path"])
        if why:
            raise RecordsError([why])
        if not _SHA.fullmatch(g["sha"]):
            raise RecordsError(["a FILE pointer names a full commit sha: 40 lowercase hex digits"])
        if not g["anchor"].strip():
            raise RecordsError(["a FILE pointer carries a verbatim anchor, not an empty one"])
        return Pointer("FILE", repo=g["repo"], path=g["path"], sha=g["sha"], anchor=g["anchor"])
    if not _valid_date(g["date"]):
        raise RecordsError([f"an {kind} pointer's date is a real date, YYYY-MM-DD"])
    if kind == "ORIGIN":
        if not _WHO.fullmatch(g["who"]):
            raise RecordsError(["an ORIGIN pointer names its filer: owner, lead, builder-N or checker-N"])
        return Pointer("ORIGIN", date=g["date"], who=g["who"])
    if not g["words"].strip():
        raise RecordsError(["an OWNER pointer quotes the owner's words, not an empty string"])
    return Pointer("OWNER", date=g["date"], words=g["words"])


# ------------------------------------------------------------------------- RULES.md and BACKLOG.md

@dataclass(frozen=True)
class Rule:
    """One standing rule. `line` (its heading's line) locates it; it is no part of the rule."""
    id: str
    scope: str
    text: str
    source: Pointer
    check: str
    line: int = field(default=0, compare=False)


@dataclass(frozen=True)
class Want:
    """One backlog item. `line` (its heading's line) locates it; it is no part of the want."""
    id: str
    status: str
    scope: str
    text: str
    source: Pointer
    line: int = field(default=0, compare=False)


_ENTRY_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_FIELD = re.compile(r"- (?P<name>[a-z][a-z-]*):(?P<value>.*)")
_ENTRY_FIELDS = ("scope", "source", "check", "status")      # every field either file's entries carry


def _lines(text: str) -> List[str]:
    if text.startswith("\ufeff"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


class _Entry:
    def __init__(self, line: int, eid: Optional[str]):
        self.line, self.id = line, eid
        self.fields: Dict[str, List[Tuple[int, str]]] = {}
        self.text: List[Tuple[int, str]] = []
        self.closed = False                     # the text block has ended; no more '> ' lines


def _entries(text: str, problems: List[str]) -> List[_Entry]:
    out: List[_Entry] = []
    cur: Optional[_Entry] = None
    for n, ln in enumerate(_lines(text), 1):
        if ln.startswith("##"):
            if ln.startswith("## "):
                cur = _Entry(n, ln[3:])
            else:
                problems.append(f"line {n}: an entry heading reads '## <id>'")
                cur = _Entry(n, None)
            out.append(cur)
        elif cur is None:                       # the preamble: prose, but never an entry's body
            m = _FIELD.fullmatch(ln.strip())
            if (m and m.group("name") in _ENTRY_FIELDS) or ln.lstrip().startswith(">"):
                problems.append(f"line {n}: before the first '## <id>' heading no line reads as an "
                                f"entry's field or text; an entry begins with '## <id>'")
        elif not ln.strip():
            cur.closed = cur.closed or bool(cur.text)
        elif ln.startswith(">"):
            if ln != ">" and not ln.startswith("> "):
                problems.append(f"line {n}: a text line reads '> ' and the words, or '>' alone")
            elif cur.closed:
                problems.append(f"line {n}: an entry's text is one contiguous block of '> ' lines")
            else:
                cur.text.append((n, ln[2:]))
        else:
            m = _FIELD.fullmatch(ln)
            if m is None:
                problems.append(f"line {n}: inside an entry a line is a field ('- <name>: <value>'), "
                                f"a '> ' text line, or blank")
                continue
            cur.closed = cur.closed or bool(cur.text)
            value = m.group("value")
            value = value[1:] if value.startswith(" ") else None
            if not value or value != value.strip():
                problems.append(f"line {n}: a field reads '- <name>: <value>', one space after the "
                                f"colon and a value with no space around it")
                continue
            cur.fields.setdefault(m.group("name"), []).append((n, value))
    return out


def _parse(text: str, what: str, names: Sequence[str], sources: Sequence[str]) -> List[Tuple[_Entry, Dict]]:
    problems: List[str] = []
    entries = _entries(text, problems)
    seen: Dict[str, int] = {}
    good: List[Tuple[_Entry, Dict]] = []
    for e in entries:
        ok = e.id is not None
        if e.id is not None:
            if len(e.id) > 64 or not _ENTRY_ID.fullmatch(e.id):
                problems.append(f"line {e.line}: an id is lowercase letters and digits in hyphen-joined "
                                f"words, at most 64 characters")
                ok = False
            elif e.id in seen:
                problems.append(f"line {e.line}: this id is already used at line {seen[e.id]}")
                ok = False
            else:
                seen[e.id] = e.line
        values: Dict = {}
        for name, uses in e.fields.items():
            if name not in names:
                problems.append(f"line {uses[0][0]}: a {what} entry has no such field "
                                f"(its fields are {', '.join(names)})")
                ok = False
                continue
            if len(uses) > 1:
                problems.append(f"line {uses[1][0]}: the {name} field appears twice")
                ok = False
            n, value = uses[0]
            if name == "scope" and value not in SCOPES:
                problems.append(f"line {n}: the scope is 'all' or one repository with a public "
                                f"remote: {', '.join(PUBLIC_REPOS)}")
                ok = False
            elif name == "status" and value not in STATUSES:
                problems.append(f"line {n}: the status is one of {', '.join(STATUSES)}")
                ok = False
            elif name == "source":
                try:
                    ptr = parse_pointer(value)
                except RecordsError as err:
                    problems.extend(f"line {n}: {p}" for p in err.problems)
                    ok = False
                    continue
                if ptr.kind not in sources:
                    problems.append(f"line {n}: a {what} entry's source is a {', '.join(sources)} pointer")
                    ok = False
                values[name] = ptr
                continue
            values[name] = value
        for name in names:
            if name not in e.fields:
                problems.append(f"line {e.line}: the entry has no {name} field")
                ok = False
        words = [t for _, t in e.text]
        if not words:
            problems.append(f"line {e.line}: the entry has no '> ' text")
            ok = False
        elif not words[0].strip() or not words[-1].strip():
            problems.append(f"line {e.text[0][0]}: an entry's text never starts or ends with an empty line")
            ok = False
        values["text"] = "\n".join(words)
        if ok:
            good.append((e, values))
    if problems:
        raise RecordsError(problems)
    return good


def parse_rules(text: str) -> List[Rule]:
    """Every entry of a RULES.md, in file order, or RecordsError naming every bad line."""
    return [Rule(e.id, v["scope"], v["text"], v["source"], v["check"], line=e.line)
            for e, v in _parse(text, "RULES", ("scope", "source", "check"), RULE_SOURCES)]


def parse_backlog(text: str) -> List[Want]:
    """Every entry of a BACKLOG.md, in file order, or RecordsError naming every bad line."""
    return [Want(e.id, v["status"], v["scope"], v["text"], v["source"], line=e.line)
            for e, v in _parse(text, "BACKLOG", ("status", "scope", "source"), WANT_SOURCES)]


# --------------------------------------------------------------------- the private configuration

@dataclass(frozen=True)
class Config:
    """What the private configuration directory held when it was read (`dir` None: no directory)."""
    dir: Optional[str]
    private_names: Tuple[str, ...] = ()
    secret_patterns: Tuple[Tuple["re.Pattern[str]", str], ...] = ()


def config_dir(environ: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """HARNESS_CONFIG_DIR when it is set (None when set but empty), else ~/.config/harness.

    The default is computed only when there is no override, so an override can never reach it."""
    env = os.environ if environ is None else environ
    if CONFIG_ENV in env:
        return env[CONFIG_ENV] or None
    return os.path.join(os.path.expanduser("~"), ".config", "harness")


def _config_numbered(directory: Optional[str], name: str) -> List[Tuple[int, str]]:
    """The kept (line number, line) pairs of one file of the directory; none when the directory or
    the file is absent. Any other failure to read it (a directory in its place, no permission, bad
    UTF-8) is raised."""
    if directory is None:
        return []
    try:
        with open(os.path.join(directory, name), encoding="utf-8-sig") as fh:
            raw = fh.read()
    except (FileNotFoundError, NotADirectoryError):
        return []
    return [(n, s) for n, s in ((n, ln.strip()) for n, ln in enumerate(_lines(raw), 1))
            if s and not s.startswith("#")]


def _config_lines(directory: Optional[str], name: str) -> List[str]:
    return [s for _, s in _config_numbered(directory, name)]


def load_config(environ: Optional[Mapping[str, str]] = None) -> Config:
    """Read the private configuration directory, once. Works when it, or either file, is absent."""
    d = config_dir(environ)
    names = tuple(w for ln in _config_lines(d, PRIVATE_NAMES_FILE) for w in ln.split())
    pats = [(re.compile(p), why) for p, why in harness.SECRET_PATTERNS]
    pats += [(re.compile(p), LOCAL_PATTERN) for p in _config_lines(d, SECRET_PATTERNS_FILE)]
    return Config(d, names, tuple(pats))


_REPO_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def load_roots(directory: Optional[str]) -> Dict[str, str]:
    """The roots file of a configuration directory: repo name -> local checkout. Empty when the
    directory or the file is absent; RecordsError (lines only, never their words) when malformed."""
    roots: Dict[str, str] = {}
    first: Dict[str, int] = {}
    problems: List[str] = []
    for n, ln in _config_numbered(directory, ROOTS_FILE):
        parts = ln.split(None, 1)
        if len(parts) != 2 or not _REPO_NAME.fullmatch(parts[0]):
            problems.append(f"{ROOTS_FILE} line {n}: a line reads '<repo> <absolute path>'")
        elif not os.path.isabs(parts[1]):
            problems.append(f"{ROOTS_FILE} line {n}: the checkout's path is absolute")
        elif parts[0] in roots:
            problems.append(f"{ROOTS_FILE} line {n}: this repo is already listed at line {first[parts[0]]}")
        else:
            roots[parts[0]], first[parts[0]] = parts[1], n
    if problems:
        raise RecordsError(problems)
    return roots


def describe_config(config: Config, environ: Optional[Mapping[str, str]] = None,
                    roots: Optional[Mapping[str, str]] = None) -> List[str]:
    """Which configuration directory was used, and what it held — never its path or its words."""
    env = os.environ if environ is None else environ
    if config.dir is None:
        where = f"none ({CONFIG_ENV} is set but empty)"
    elif CONFIG_ENV in env:
        where = f"{CONFIG_ENV} (the override)"
    else:
        where = "~/.config/harness (the default)"
    local = len(config.secret_patterns) - len(harness.SECRET_PATTERNS)
    out = [f"config: {where}",
           f"  private names: {len(config.private_names)}"
           + ("" if config.private_names else " (the scan can reject no private name)"),
           f"  secret patterns: {len(harness.SECRET_PATTERNS)} built in, {local} local"]
    if roots is not None:
        public = [r for r in PUBLIC_REPOS if r in roots]
        out.append(f"  roots: {len(roots)} repo(s); public: {', '.join(public) or 'none'}")
    return out


# ------------------------------------------------------------------------------------------ the scan

SCAN_KINDS = ("path", "ip", "email", "ssh-key", "secret", "private-name")
HIT = {
    "path": "an absolute path",
    "ip": "an IP address",
    "email": "an e-mail address",
    "ssh-key": "an ssh key file name",
    "private-name": "a private name",
}
_ABS_PATH = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]"                                   # C:\ or C:/
    r"|(?<![A-Za-z0-9._~%-])/(?:[A-Za-z]|home|Users|tmp)/")             # /c/, /home/, /Users/, /tmp/
_IPV4 = re.compile(r"(?<![0-9])(?<![0-9]\.)(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])(?!\.[0-9])")
_IPV6 = re.compile(r"(?<![0-9A-Za-z:.])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![0-9A-Za-z:])")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}")
_SSH_KEY = re.compile(r"(?<![A-Za-z0-9])id_(?:rsa|dsa|ecdsa|ed25519|xmss)(?![A-Za-z])"
                      r"|[A-Za-z0-9_.-]+\.(?:pem|ppk)(?![A-Za-z0-9])", re.IGNORECASE)


def _has_ip(line: str) -> bool:
    if any(all(int(o) <= 255 for o in m.group(0).split(".")) for m in _IPV4.finditer(line)):
        return True
    for m in _IPV6.finditer(line):
        tok = m.group(0)
        if re.search(r"[0-9]", tok):
            try:
                ipaddress.IPv6Address(tok)
                return True
            except ValueError:
                pass
    return False


def _word(name: str) -> "re.Pattern[str]":
    return re.compile(r"(?<![^\W_])" + re.escape(name) + r"(?![^\W_])", re.IGNORECASE)


def scan(text: str, config: Config, kinds: Iterable[str] = SCAN_KINDS) -> List[Tuple[int, str]]:
    """Every (1-based line, kind of hit) in `text`, sorted; empty when it is clean. Never the match.

    `kinds` narrows the scan to some of SCAN_KINDS (a brief quoting a ledger scans for private names
    and secrets only). The configuration is passed in, never read here."""
    kinds = tuple(kinds)
    unknown = [k for k in kinds if k not in SCAN_KINDS]
    if unknown:
        raise ValueError("a scan kind is one of " + ", ".join(SCAN_KINDS))
    words = [_word(w) for w in config.private_names] if "private-name" in kinds else []
    pats = list(config.secret_patterns)
    hits = set()
    for n, ln in enumerate(_lines(text), 1):
        if "path" in kinds and _ABS_PATH.search(ln):
            hits.add((n, HIT["path"]))
        if "ip" in kinds and _has_ip(ln):
            hits.add((n, HIT["ip"]))
        if "email" in kinds and _EMAIL.search(ln):
            hits.add((n, HIT["email"]))
        if "ssh-key" in kinds and _SSH_KEY.search(ln):
            hits.add((n, HIT["ssh-key"]))
        if "secret" in kinds:
            kind = harness.secret_kind(ln, pats)
            if kind:
                hits.add((n, kind))
        if any(rx.search(ln) for rx in words):
            hits.add((n, HIT["private-name"]))
    return sorted(hits)


# ---------------------------------------------------------------------------- resolution and check

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _git(root: str, *args: str, timeout: int = 60) -> Optional[bytes]:
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def _shallow(root: str) -> Optional[bool]:
    """Is this clone shallow? None when git cannot say: it failed, or is too old to know the flag and
    echoes it back."""
    return {b"true": True, b"false": False}.get((_git(root, "rev-parse", "--is-shallow-repository") or b"").strip())


def _ledger_lines(root: str, run: str) -> Optional[List[str]]:
    try:
        with open(os.path.join(root, "docs", "harness", "runs", run + ".jsonl"), "rb") as fh:
            lines = _lines(fh.read().decode("utf-8"))
    except (FileNotFoundError, NotADirectoryError):
        return None
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _strings(obj: object) -> Iterator[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def fetch(p: Pointer, roots: Mapping[str, str]) -> Tuple[Optional[str], Optional[str]]:
    """(the text the pointer names, None) when it resolves, else (None, why not).

    A LEDGER pointer names the event's strings; a FILE pointer the file at that commit. `roots` maps
    a repo to its local checkout. The reason never carries a path, the anchor or the record's words."""
    if not p.resolvable:
        return None, f"{p.kind} pointers are unresolvable by kind"
    root = roots.get(p.repo)
    if root is None:
        return None, "the roots file names no checkout for this repository"
    if not os.path.isdir(root):
        return None, "this repository's checkout is missing"
    if p.kind == "LEDGER":
        lines = _ledger_lines(root, p.run)
        if lines is None:
            return None, "the checkout holds no ledger for this run"
        if p.line > len(lines):
            return None, f"the ledger has {len(lines)} line(s)"
        try:
            ev = json.loads(lines[p.line - 1])
        except ValueError:
            ev = None
        if not isinstance(ev, dict) or "ev" not in ev:
            return None, "that line is not a ledger event"
        return "\n".join(_strings(ev)), None
    blob = _git(root, "cat-file", "blob", f"{p.sha}:{p.path}")
    if blob is None:                      # only now ask why: one git call when the pointer resolves
        if _git(root, "cat-file", "-e", p.sha + "^{commit}") is None:
            return None, "the commit is not in this checkout" + (" (a shallow clone)" if _shallow(root) else "")
        return None, "the file does not exist at that commit"
    text = blob.decode("utf-8", "replace")
    if p.anchor not in text:
        return None, "the anchor does not occur in the file at that commit"
    return text, None


def resolve(p: Pointer, roots: Mapping[str, str]) -> Optional[str]:
    """None when the pointer resolves, else why not (see fetch)."""
    return fetch(p, roots)[1]


def _collapse(text: str) -> str:
    return " ".join(text.split())


def verbatim(rule: Rule, roots: Mapping[str, str]) -> Optional[str]:
    """None when the rule's text occurs, whitespace aside, in what its source names; else why not."""
    if rule.source.kind == "OWNER":
        record: Optional[str] = rule.source.words
    else:
        record, why = fetch(rule.source, roots)
        if why:
            return "its source does not resolve"
    return None if _collapse(rule.text) in _collapse(record or "") else "its text is not verbatim in its source"


def check(root: str, environ: Optional[Mapping[str, str]] = None) -> Tuple[int, List[str]]:
    """(exit code, lines to print) for `check ROOT`: see the module docstring."""
    try:
        cfg = load_config(environ)
        listed = load_roots(cfg.dir)
    except RecordsError as e:
        return 2, ["REFUSED: the configuration cannot be read:"] + ["  " + p for p in e.problems]
    except (OSError, UnicodeError, re.error) as e:
        return 2, [f"REFUSED: the configuration cannot be read ({type(e).__name__})"]
    out = describe_config(cfg, environ, listed)
    out.append(f"  {SELF_REPO} resolves against the checkout checked, never the roots file")
    roots = dict(listed)
    roots[SELF_REPO] = root
    bad = resolved = by_kind = quoted = 0
    for rel, parse in ((RULES_REL, parse_rules), (BACKLOG_REL, parse_backlog)):
        try:
            with open(os.path.join(root, *rel.split("/")), "rb") as fh:
                text = fh.read().decode("utf-8")
        except FileNotFoundError:
            out.append(f"MISSING {rel}")
            bad += 1
            continue
        hits = scan(text, cfg)
        out += [f"SCAN {rel} line {n}: {kind}" for n, kind in hits]
        bad += len(hits)
        try:
            entries = parse(text)
        except RecordsError as e:
            out += [f"PARSE {rel} {p}" for p in e.problems]
            bad += len(e.problems)
            continue
        out.append(f"{rel}: {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")
        bounds = [e.line for e in entries] + [len(_lines(text)) + 1]
        for i, e in enumerate(entries):
            hidden = any(bounds[i] <= n < bounds[i + 1] for n, _ in hits)
            name = f"{rel} line {e.line}" if hidden else f"{rel} {e.id}"
            ptr = "(withheld: the scan hits this entry)" if hidden else e.source.render()
            if not e.source.resolvable:
                by_kind += 1
                out.append(f"BY KIND {name}: {ptr} (unresolvable by kind)")
            else:
                why = resolve(e.source, roots)
                if why:
                    bad += 1
                    out.append(f"UNRESOLVED {name}: {ptr} - {why}")
                    continue
                resolved += 1
            if isinstance(e, Rule):
                why = verbatim(e, roots)
                if why:
                    bad += 1
                    out.append(f"NOT VERBATIM {name}: {why}")
                else:
                    quoted += 1
    tally = f"{resolved} pointer(s) resolved, {by_kind} unresolvable by kind, {quoted} rule(s) verbatim"
    if bad:
        out.append(f"CHECK FAIL: {bad} problem(s); {tally}")
        return 1, out
    out.append(f"CHECK PASS: 0 unresolved; {tally}")
    return 0, out


# --------------------------------------------------------------------------------------- the schedule

PHI = (1 + 5 ** 0.5) / 2
# Old ledgers are read with this forever, so it knows no id form: the rule names any token, and the
# rule list at the records commit decides whether it exists.
_CONFIRM = re.compile(r"RULE (?P<rule>\S+) (?P<verdict>held|failed): (?P<evidence>\S.*)", re.S)


def fib(k: int) -> int:
    """F(1) = F(2) = 1, F(k) = F(k-1) + F(k-2)."""
    a, b = 1, 1
    for _ in range(k - 1):
        a, b = b, a + b
    return a


def interval(i: int) -> int:
    """The runs a rule at interval index i waits after its last counted confirmation: F(i+1)."""
    return fib(i + 1)


SPREAD = fib(7)                          # 13: a rule never confirmed is first due within 13 runs of entry


def first_due(j: int) -> int:
    """The first due run of the j-th rule ever entered (j from 1): 1 + floor(frac(j*phi) * 13). It
    depends on j alone, so no rule added or removed later moves it."""
    return 1 + int(((j * PHI) % 1.0) * SPREAD)


def stagger_starts(n_rules: int) -> List[int]:
    """The first due runs of the rules ranked 1..n_rules."""
    return [first_due(j) for j in range(1, n_rules + 1)]


def max_due(starts: Sequence[int], runs: int = 100) -> int:
    """The largest number of rules due in any one of the first `runs` runs, every rule always held
    and confirmed whenever due, each first due at its start."""
    c, i, most = [s - 1 for s in starts], [1] * len(starts), 0
    for n in range(1, runs + 1):
        due = [r for r in range(len(starts)) if n - c[r] >= interval(i[r])]
        most = max(most, len(due))
        for r in due:
            c[r], i[r] = n, i[r] + 1
    return most


def stagger_measure(n_rules: int, runs: int = 100) -> Tuple[int, int]:
    """(the largest number of rules due in one of the first `runs` runs, the longest wait in runs from
    entry to a rule's first check), every rule entered at once, always held and confirmed whenever due."""
    starts = stagger_starts(n_rules)
    return max_due(starts, runs), max(starts, default=0)


def _when(ts: str) -> datetime.datetime:
    t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=datetime.timezone.utc)


@dataclass(frozen=True)
class Completed:
    """A run that done_problems calls complete, at its last passing live verdict (`line`)."""
    ts: datetime.datetime
    repo: str
    run: str
    line: int


@dataclass(frozen=True)
class Confirmation:
    """A checker's 'RULE <id> held|failed: <evidence>' note, by a checker with a verdict in its ledger."""
    ts: datetime.datetime
    repo: str
    run: str
    line: int
    by: str
    rule: str
    verdict: str


@dataclass(frozen=True)
class Gear:
    """One rule's place in the schedule: due in run n when n - c >= interval(i)."""
    n: int
    c: int
    i: int
    due: bool
    counted: Tuple[Tuple[Confirmation, int], ...]
    listed: Tuple[Tuple[Confirmation, int], ...]


def clock(done: Iterable[Completed]) -> List[Completed]:
    """The completed runs in order: by completion time, ties by repo name, then run id."""
    return sorted(done, key=lambda d: (d.ts, d.repo, d.run))


def run_number(entry: datetime.datetime, done: Iterable[Completed], t: Optional[datetime.datetime] = None) -> int:
    """1 + the runs completed after the rule's entry (its run 0) and before t (None: after every record)."""
    return 1 + sum(1 for d in done if d.ts > entry and (t is None or d.ts < t))


def gear(entry: datetime.datetime, done: Sequence[Completed], confirmations: Iterable[Confirmation],
         start: int = 1, t: Optional[datetime.datetime] = None) -> Gear:
    """The rule's gear: each confirmation placed in run 1 + the runs completed before its own time
    (so a stalled run never pins it); failed sets c and resets i to 1 at any time, held while due sets
    c and steps i, anything else is listed, not counted. `start` is the rule's first due run."""
    c, i = start - 1, 1
    counted: List[Tuple[Confirmation, int]] = []
    listed: List[Tuple[Confirmation, int]] = []
    for cf in sorted(confirmations, key=lambda x: (x.ts, x.repo, x.run, x.line)):
        k = run_number(entry, done, cf.ts)
        if cf.verdict == "failed":
            c, i = k, 1
            counted.append((cf, k))
        elif k - c >= interval(i):
            c, i = k, i + 1
            counted.append((cf, k))
        else:
            listed.append((cf, k))
    n = run_number(entry, done, t)
    return Gear(n, c, i, n - c >= interval(i), tuple(counted), tuple(listed))


def read_runs(H, located: Sequence[Tuple[str, str]]
              ) -> Tuple[List[Completed], List[Confirmation], List[Tuple[str, str, int, str]]]:
    """Every completed run and every confirmation in the ledgers of `located` (repo, checkout), and
    the confirmations ignored (repo, run, line, why). H is the harness at the records commit."""
    done: List[Completed] = []
    found: List[Confirmation] = []
    ignored: List[Tuple[str, str, int, str]] = []
    for repo, root in located:
        for run in _runs(root):
            evs = _numbered(root, run) or []
            try:
                complete = not H.done_problems(root, H.Ledger(root, run))
            except H.HarnessError:
                complete = False
            lives = [(n, e) for n, e in evs if e.get("ev") == "verdict" and e.get("step") == "live" and e.get("pass")]
            if complete and lives:
                done.append(Completed(_when(lives[-1][1]["ts"]), repo, run, lives[-1][0]))
            judges = {e.get("by") for _, e in evs if e.get("ev") == "verdict"}
            for n, e in evs:
                if e.get("ev") != "note" or e.get("kind") != "confirm":
                    continue
                m = _CONFIRM.fullmatch(e.get("text") or "")
                by = e.get("by") or ""
                if m is None:
                    ignored.append((repo, run, n, "it does not read 'RULE <id> held|failed: <evidence>'"))
                elif not harness._CHECKER.fullmatch(by):
                    ignored.append((repo, run, n, "it is not by a checker"))
                elif by not in judges:
                    ignored.append((repo, run, n, "its checker has no verdict in this ledger"))
                else:
                    found.append(Confirmation(_when(e["ts"]), repo, run, n, by, m.group("rule"), m.group("verdict")))
    return done, found, ignored


class NoHistory(Exception):
    """RULES.md's whole history cannot be read, so no rule's entry or first due run can be known."""


_SHALLOW = "this clone is shallow, so RULES.md's history cannot be read and no rule's entry or first due run can be known"
_GIT_FAILED = "git could not give RULES.md's whole history, so no rule's entry or first due run can be known"
_NOT_TEXT = "a version in RULES.md's history is not text, so no rule's entry or first due run can be known"
_NOT_HELD = ("RULES.md's history does not hold every rule of the records commit, so no rule's entry or first "
             "due run can be known")
_HEADING = re.compile(r"## +(\S+)[ \t]*")


def heading_ids(text: str) -> List[str]:
    """The ids one version of RULES.md enters, in order: every line that is exactly '## ' and one token.

    The history walk reads old versions with this and nothing else, and it must stay that way: no
    parse_rules, no fields, no _ENTRY_ID, not even _lines. Reading old bytes through today's format
    would let a change to that format change what an old version entered, and every rank after it.
    It matches whole lines, so a heading quoted in a '> ' text line is no heading. A one-token
    heading that is no rule takes a place, but the same place forever, so it moves nothing later."""
    return [m.group(1) for m in map(_HEADING.fullmatch, re.split(r"\r\n|\r|\n", text.removeprefix("\ufeff"))) if m]


def _rules_history(sha: str) -> List[Tuple[datetime.datetime, List[str]]]:
    """RULES.md's versions up to `sha` along first-parent history, oldest first: (commit time, ids).

    NoHistory unless that history is whole. A shallow clone shows its boundary commit as a root that
    adds every current rule, which looks complete and is not: a rule removed before the boundary
    vanishes, and every rule after it re-ranks. So nothing here reads one, and a schedule is never
    computed from it. The other ways in are git failing and bytes that are not text: a part of the
    history is no better. A version the parser refuses is neither, and counts like any other."""
    shallow = _shallow(_REPO)
    if shallow:
        raise NoHistory(_SHALLOW)
    log = _git(_REPO, "log", "--first-parent", "--reverse", "--format=%H %cI", sha, "--", RULES_REL)
    if shallow is None or log is None:
        raise NoHistory(_GIT_FAILED)
    out: List[Tuple[datetime.datetime, List[str]]] = []
    for ln in log.decode().split("\n"):
        if not ln.strip():
            continue
        commit, when = ln.split(" ", 1)
        try:
            text = _blob(_REPO, commit, RULES_REL)
        except UnicodeError:
            raise NoHistory(_NOT_TEXT) from None
        if text is None:
            if _git(_REPO, "ls-tree", commit, "--", RULES_REL) != b"":
                raise NoHistory(_GIT_FAILED)          # the file is there, and its bytes cannot be read
            out.append((_when(when), []))             # this commit deleted RULES.md
        elif "\0" in text:
            raise NoHistory(_NOT_TEXT)                # UTF-16 with no mark decodes as UTF-8, and no heading matches
        else:
            out.append((_when(when), heading_ids(text)))
    return out


def _schedule_basis(sha: str, every_rule: Sequence[Rule]) -> Tuple[Dict[str, datetime.datetime], Dict[str, int]]:
    """(entries, ranks) of the rules at the records commit, or NoHistory. A whole history holds every
    rule of that commit, so a rule it lacks means git gave a part of it, or the heading reader and
    the parser no longer agree on what a heading is. Either way a rank would be a guess."""
    entries, ranks = rule_entries(sha), rule_ranks(sha)
    if any(r.id not in ranks for r in every_rule):
        raise NoHistory(_NOT_HELD)
    return entries, ranks


def rule_entries(sha: str) -> Dict[str, datetime.datetime]:
    """Each rule's entry: the commit time of the first commit, along first-parent history up to
    `sha`, whose RULES.md holds it. NoHistory when that history cannot be read whole."""
    entries: Dict[str, datetime.datetime] = {}
    for when, ids in _rules_history(sha):
        for rid in ids:
            entries.setdefault(rid, when)
    return entries


def rule_ranks(sha: str) -> Dict[str, int]:
    """Each rule's j, frozen at its entry: its place (from 1) among every rule ever entered in
    RULES.md's first-parent history up to `sha`, by the commit that first added it, then id. A rule
    removed keeps its place, so removing one re-ranks nothing, and a rule added ranks after all before.
    NoHistory when that history cannot be read whole."""
    ranks: Dict[str, int] = {}
    for _, ids in _rules_history(sha):
        for rid in sorted(set(ids) - set(ranks)):
            ranks[rid] = len(ranks) + 1
    return ranks


# ------------------------------------------------------------------------------------------ brief

ROLES = ("builder", "checker", "lead")
WANTS_CAP = 3000                         # characters of WANTS text before the rest print as pointers
LIVE_STATUSES = ("open", "filed-as-run")
DETAIL_KINDS = ("path", "ip", "email", "ssh-key")    # a quoted ledger line these hit prints as its pointer
OUTPUT_KINDS = ("private-name", "secret")            # any hit in the whole output refuses the brief
_WITHHELD = "(withheld: it names a path or an address; read it at its pointer)"


class BriefRefused(Exception):
    """brief will not print. The reason names lines and kinds, never a matched word or a path."""


def _same(a: str, b: str) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def _blob(repo: str, sha: str, rel: str) -> Optional[str]:
    raw = _git(repo, "cat-file", "blob", f"{sha}:{rel}")
    return None if raw is None else raw.decode("utf-8")


def _committed_here(rel: str) -> Optional[str]:
    """Why `rel`, in the checkout this file is in, may not run (it differs from HEAD, or is not committed),
    or None."""
    blob = _git(_REPO, "cat-file", "blob", f"HEAD:{rel}")
    if blob is None:
        return f"{rel} is not committed at this checkout's HEAD"
    with open(os.path.join(_REPO, *rel.split("/")), "rb") as fh:
        here = fh.read()
    if here.replace(b"\r\n", b"\n") != blob.replace(b"\r\n", b"\n"):
        return f"{rel} differs from HEAD; a brief or a record runs only from committed code"
    return None


def _self_unchanged() -> Optional[str]:
    """Why tools/context.py may not brief or record, or None."""
    return _committed_here("tools/context.py")


def _harness_at(sha: str):
    """The harness module as committed at `sha` (git cat-file, never the working copy)."""
    import types
    src = _blob(_REPO, sha, harness.SELF_REL)
    if src is None:
        raise BriefRefused("concordance-2 has no tools/harness.py at the records commit")
    mod = types.ModuleType("harness_at_" + sha[:12])
    mod.__file__ = os.path.join(_REPO, *harness.SELF_REL.split("/"))
    exec(compile(src, f"{harness.SELF_REL}@{sha[:12]}", "exec"), mod.__dict__)
    return mod


def _numbered(root: str, run: str) -> Optional[List[Tuple[int, dict]]]:
    lines = _ledger_lines(root, run)
    if lines is None:
        return None
    try:
        return [(n, json.loads(ln)) for n, ln in enumerate(lines, 1) if ln.strip()]
    except ValueError:
        raise BriefRefused(f"a line of run {run}'s ledger is not JSON") from None


def _parsed(parse, text: str, rel: str):
    try:
        return parse(text)
    except RecordsError as e:
        raise BriefRefused(f"{rel} at the records commit does not parse: " + "; ".join(e.problems)) from None


def _runs(root: str) -> List[str]:
    d = os.path.join(root, *harness.RUNS_REL.split("/"))
    if not os.path.isdir(d):
        return []
    return sorted(f[:-6] for f in os.listdir(d) if f.endswith(".jsonl") and harness._ID.match(f[:-6]))


class _Out:
    """The brief's lines: own text, or text quoted from a record with the pointer it came from."""

    def __init__(self, cfg: Config, roots: Mapping[str, str]):
        self.cfg, self.roots, self.lines = cfg, roots, []
        self.seen: Dict[Pointer, str] = {}

    def own(self, text: str) -> None:
        self.lines.append(text)

    def ptr(self, p: Pointer) -> str:
        if p not in self.seen:
            if not p.resolvable:
                self.seen[p] = f"{p.render()} (unresolvable by kind)"
            else:
                why = resolve(p, self.roots)
                self.seen[p] = f"UNRESOLVED: {p.render()} - {why}" if why else p.render()
        return self.seen[p]

    def quote(self, label: str, body: str, p: Pointer, from_ledger: bool = True) -> None:
        body = " ".join(body.splitlines())            # one record line is one brief line, its pointer on it
        if from_ledger and scan(body, self.cfg, DETAIL_KINDS):
            body = _WITHHELD
        self.lines.append(f"{label}{body} [{self.ptr(p)}]")


def _checker_fields(o: _Out, out: List[str], plan: dict, st: dict, findings: List[Tuple[int, str]],
                    at_plan: Pointer, at_step: Pointer, at, computed: Pointer) -> None:
    """cmd_brief's lines, attributed field by field in the order it prints them. A field quoted from
    the ledger spans as many lines as its value has and must end with exactly that value, so a
    line break inside a claim or a finding can never shift a pointer; a computed field is one line
    under its known prefix. Anything else refuses: a misattributed line is worse than none."""
    pos = 0

    def take(prefix: Tuple[str, ...], p: Pointer, value: Optional[str] = None) -> None:
        nonlocal pos
        n = 1 if value is None else value.count("\n") + 1
        group = out[pos:pos + n]
        text = "\n".join(group)
        if len(group) < n or not group[0].startswith(prefix) or (value is not None and not text.endswith(value)):
            raise BriefRefused("cmd_brief at the records commit prints a field this brief cannot attribute")
        pos += n
        if p is computed:
            o.quote("", text, p, from_ledger=False)
        elif value is None:
            o.quote("", text, p)
        else:
            o.quote(text[:len(text) - len(value)], value, p)

    take(("RUN ",), at_plan, plan["goal"])
    take(("STEP ",), at_step)
    take(("claim: ",), at_step, st["claim"])
    take(("scope: ",), at_step, ", ".join(st["scope"]))
    take(("tests: ",), at_step, ", ".join(st["tests"]))
    take(("base: ",), at_step)
    take(("changed now (",), computed)
    take(("adopted at open: ",), at_step, ", ".join(st.get("adopted") or []) or "none")
    take(("GRADERS TOUCHED", "graders touched: "), computed)
    take(("content hash now: ",), computed)
    take(("failed rounds so far: ",), computed)
    for i, f in findings:
        take(("previous finding: ",), at(i), f)
    if pos != len(out):
        raise BriefRefused("cmd_brief at the records commit prints a field this brief cannot attribute")


def _role_run(o: _Out, H, role: str, repo: str, root: str, run: str, step: Optional[str],
              evs: List[Tuple[int, dict]], sha: str) -> None:
    L = H.Ledger(root, run)
    try:
        pi, plan = L.plan()
    except H.HarnessError:
        raise BriefRefused("the run has no plan") from None
    line_of = [n for n, _ in evs]
    at = lambda i: Pointer("LEDGER", repo=repo, run=run, line=line_of[i])   # noqa: E731
    code = lambda anchor: Pointer("FILE", repo=SELF_REPO, path=harness.SELF_REL, sha=sha, anchor=anchor)  # noqa: E731
    steps = {e["step"]: i for i, (_, e) in enumerate(evs) if e.get("ev") == "step"}
    if step is not None and step not in steps:
        raise BriefRefused("the run has no such step")
    verdicts = [i for i, (_, e) in enumerate(evs)
                if e.get("ev") == "verdict" and e.get("step") == step and not e.get("pass")]
    o.own(f"== RUN {run} in {repo}")
    if role == "checker" and step is not None:
        _checker_fields(o, H.cmd_brief(root, run, step).split("\n"), plan, evs[steps[step]][1],
                        [(i, f) for i in verdicts for f in evs[i][1].get("findings") or []],
                        at(pi), at(steps[step]), at, code("def cmd_brief"))
    else:
        o.quote("goal: ", plan["goal"], at(pi))
    for d in plan.get("done") or []:
        o.quote("done when: ", d, at(pi))
    if role == "builder" and step is not None:
        st = evs[steps[step]][1]
        o.quote("", f"step {step}: owner {st['owner']}, state {L.state(step)}", at(steps[step]), False)
        o.quote("claim: ", st["claim"], at(steps[step]))
        o.quote("scope: ", ", ".join(st["scope"]), at(steps[step]))
        o.quote("tests: ", ", ".join(st["tests"]), at(steps[step]))
        for i in verdicts:
            for f in evs[i][1].get("findings") or []:
                o.quote("previous finding: ", f, at(i))
    if role == "lead":
        for sid, i in steps.items():
            o.quote("", f"step {sid}: owner {evs[i][1]['owner']}, state {L.state(sid)}", at(i), False)
    problems = H.done_problems(root, L)
    if not problems:
        o.quote("", "run state: complete", code("def done_problems"), False)
    for p in problems:
        o.quote("open: ", p, code("def done_problems"), False)


def _due(o: _Out, H, repo: str, roots: Mapping[str, str], sha: str, every_rule: Sequence[Rule],
         rules: Sequence[Rule]) -> None:
    """The DUE section: the clock, every rule in scope that is due, the confirmations not counted,
    and the ones ignored. The brief is assembled after every record it reads, so its run is
    1 + every run in scope completed after the rule's entry. Without RULES.md's whole history the
    section is one line saying so: a start or a due rule from a part of it would be a guess."""
    try:
        entries, ranks = _schedule_basis(sha, every_rule)
    except NoHistory as e:
        o.own(f"== DUE: not computed: {e}")
        return
    done, found, ignored = read_runs(H, [(n, roots[n]) for n in PUBLIC_REPOS if n in roots])
    starts = {r.id: first_due(ranks[r.id]) for r in every_rule}
    known = {r.id: r for r in every_rule}
    gears = []
    for r in sorted(rules, key=lambda r: r.id):
        scoped = [d for d in done if r.scope == "all" or d.repo == r.scope]
        mine = [cf for cf in found if cf.rule == r.id and (r.scope == "all" or cf.repo == r.scope)]
        gears.append((r, gear(entries[r.id], scoped, mine, starts[r.id])))
    ledger = lambda x: Pointer("LEDGER", repo=x.repo, run=x.run, line=x.line)   # noqa: E731
    o.own(f"== DUE: {sum(g.due for _, g in gears)} of {len(gears)} rule(s) in scope are due; intervals 1, 2, 3, 5, "
          f"8, ... runs; a rule never confirmed is first due within {SPREAD} runs of its entry")
    for scope in ("all", repo):
        ran = clock(d for d in done if scope == "all" or d.repo == scope)
        if ran:
            o.quote("", f"clock {scope}: {len(ran)} run(s) completed, the latest {ran[-1].repo} {ran[-1].run}",
                    ledger(ran[-1]), from_ledger=False)
        else:
            o.own(f"clock {scope}: no run completed")
    for r, g in gears:
        if g.due and g.counted:
            cf, k = g.counted[-1]
            o.quote("", f"DUE {r.id} ({r.scope}): run {g.n}, interval {interval(g.i)}, last counted: {cf.verdict} "
                        f"in run {k}", ledger(cf), from_ledger=False)
        elif g.due:
            o.quote("", f"DUE {r.id} ({r.scope}): run {g.n}, never confirmed, first due in run {starts[r.id]}",
                    r.source, from_ledger=False)
    for r, g in gears:
        for cf, k in g.listed:
            o.quote("", f"not counted: {r.id} {cf.verdict} in run {k}, when it was not due", ledger(cf), False)
    out = [(cf.repo, cf.run, cf.line, "no such rule at the records commit") for cf in found if cf.rule not in known]
    out += [(cf.repo, cf.run, cf.line, "outside the rule's scope") for cf in found
            if cf.rule in known and known[cf.rule].scope not in ("all", cf.repo)]
    for rp, rn, ln, why in sorted(ignored + out):
        o.quote("", f"ignored: a confirmation, because {why}", Pointer("LEDGER", repo=rp, run=rn, line=ln), False)


def brief(role: str, root: str, run: str, step: Optional[str] = None,
          environ: Optional[Mapping[str, str]] = None, cap: int = WANTS_CAP) -> List[str]:
    """The brief's lines (see the module docstring), or BriefRefused."""
    if role not in ROLES:
        raise BriefRefused("the role is builder, checker or lead")
    why = _self_unchanged()
    if why:
        raise BriefRefused(why)
    try:
        cfg = load_config(environ)
        listed = load_roots(cfg.dir)
    except RecordsError as e:
        raise BriefRefused("the configuration cannot be read: " + "; ".join(e.problems)) from None
    except (OSError, UnicodeError, re.error) as e:
        raise BriefRefused(f"the configuration cannot be read ({type(e).__name__})") from None
    if _same(root, _REPO):
        repo = SELF_REPO
    else:
        named = [n for n, p in listed.items() if _same(p, root)]
        if not named:
            raise BriefRefused("ROOT is neither this concordance-2 checkout nor a checkout the roots file names")
        if named[0] not in PUBLIC_REPOS:
            raise BriefRefused("a brief is only for a run in a repository with a public remote")
        repo = named[0]
    if not harness._ID.match(run):
        raise BriefRefused("the run id is not a harness run id")
    evs = _numbered(root, run)
    if evs is None:
        raise BriefRefused("ROOT holds no ledger for this run")
    head = (_git(_REPO, "rev-parse", "HEAD") or b"").decode().strip()
    if step is not None and repo == SELF_REPO:
        bases = [e.get("base") for _, e in evs if e.get("ev") == "step" and e.get("step") == step]
        if not bases or not bases[-1]:
            raise BriefRefused("the run has no such step")
        sha, whence = bases[-1], "the step's base, which no step can change"
    else:
        sha, whence = head, "concordance-2's HEAD"
    if _git(_REPO, "cat-file", "-e", sha + "^{commit}") is None:
        raise BriefRefused("the records commit is not in this concordance-2 checkout")
    H = _harness_at(sha)
    try:
        return _assemble(H, role, repo, root, run, step, evs, sha, whence, cfg, listed, cap)
    except H.HarnessError as e:
        raise BriefRefused(f"the harness at the records commit refused: {e}") from None


def _assemble(H, role: str, repo: str, root: str, run: str, step: Optional[str], evs: List[Tuple[int, dict]],
              sha: str, whence: str, cfg: Config, listed: Mapping[str, str], cap: int) -> List[str]:
    roots = dict(listed)                  # pointers resolve where the brief reads: the run's repo at ROOT,
    roots.setdefault(SELF_REPO, _REPO)    # the others through the roots file, concordance-2 by default here
    roots[repo] = root
    o = _Out(cfg, roots)
    o.own(f"BRIEF for the {role} of run {run} in {repo}" + (f", step {step}" if step else ""))
    o.own(f"records: concordance-2 {sha} ({whence}); RULES.md, BACKLOG.md and tools/harness.py are read "
          f"from this commit, the ledgers from their checkouts")

    rules_text = _blob(_REPO, sha, RULES_REL)
    every_rule = [] if rules_text is None else _parsed(parse_rules, rules_text, RULES_REL)
    rules = [r for r in every_rule if r.scope in ("all", repo)]
    o.own(f"== CORE: {len(rules)} rule(s) in scope for {repo}, verbatim, by id"
          + ("" if rules_text is not None else " (no docs/harness/RULES.md at the records commit)"))
    for r in sorted(rules, key=lambda r: r.id):
        o.quote(f"RULE {r.id} ({r.scope}): ", r.text.replace("\n", " ") + " | check: " + r.check,
                r.source, from_ledger=False)

    o.own("== IN FLIGHT: open steps in the ledgers of the public repositories")
    flying = 0
    for name in PUBLIC_REPOS:
        where = roots.get(name)
        if where is None:
            o.own(f"not located: {name} (no checkout in the roots file)")
            continue
        for r_id in _runs(where):
            got = _numbered(where, r_id) or []
            L = H.Ledger(where, r_id)
            for n, e in got:
                if e.get("ev") != "step":
                    continue
                state = L.state(e["step"])
                if state in ("committed", "abandoned"):
                    continue
                flying += 1
                o.quote("", f"{name} {r_id} {e['step']}: owner {e.get('owner')}, state {state}",
                        Pointer("LEDGER", repo=name, run=r_id, line=n), from_ledger=False)
    if not flying:
        o.own("none")

    _role_run(o, H, role, repo, root, run, step, evs, sha)

    backlog_text = _blob(_REPO, sha, BACKLOG_REL)
    wants = [] if backlog_text is None else _parsed(parse_backlog, backlog_text, BACKLOG_REL)
    mine = lambda w: w.source.kind == "LEDGER" and w.source.repo == repo and w.source.run == run  # noqa: E731
    live = [w for w in wants if w.status in LIVE_STATUSES and (w.scope in ("all", repo) or mine(w))]
    live.sort(key=lambda w: (0 if mine(w) else 1 if w.scope == repo else 2, w.id))
    o.own(f"== WANTS: {len(live)} open or filed as a run, for this run, {repo} and all repositories "
          f"({len(wants) - len(live)} others not shown); past {cap} characters, pointers only")
    spent = 0
    for w in live:
        text = w.text.replace("\n", " ")
        spent += len(text)
        if spent <= cap:
            o.quote(f"WANT {w.id} ({w.status}, {w.scope}): ", text, w.source, from_ledger=False)
        else:
            o.quote(f"WANT {w.id} ({w.status}, {w.scope})", "", w.source, from_ledger=False)

    _due(o, H, repo, roots, sha, every_rule, rules)

    text = "\n".join(o.lines)
    hits = scan(text, cfg, OUTPUT_KINDS) + scan(text, cfg, DETAIL_KINDS)
    if hits:
        raise BriefRefused("; ".join(f"line {n} carries {kind}" for n, kind in sorted(set(hits))))
    return o.lines


# ------------------------------------------------------------------------- ci: reading a commit's CI

_GH_READS = (("run", "list"), ("run", "view"))        # the only gh commands this module ever runs
_SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9._-]*")
_STAMP = re.compile(r"\ufeff?[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+Z ")
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_TALLY = r"[0-9]+ (?:passed|failed|errors?|skipped|xfailed|xpassed|deselected|warnings?|rerun)"
_SUITE = re.compile(rf"(?:{_TALLY}(?:, {_TALLY})*|no tests ran) in [0-9.]+s(?: \([0-9:]+\))?")
_RED_COUNT = re.compile(r"(?<![0-9])[1-9][0-9]* (?:failed|errors?)\b")
_PASSED_COUNT = re.compile(r"(?<![0-9])[1-9][0-9]* passed\b")


def _gh(*args: str) -> Optional[bytes]:
    """What a read-only gh command printed, or None. Anything but `run list` or `run view` raises."""
    if args[:2] not in _GH_READS:
        raise ValueError("ci reads: it runs gh run list and gh run view and nothing else")
    exe = shutil.which("gh")              # by PATHEXT, which a bare "gh" to CreateProcess would not use
    if exe is None:
        return None
    try:
        r = subprocess.run([exe, *args], stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def _gh_json(*args: str) -> object:
    raw = _gh(*args)
    try:
        return None if raw is None else json.loads(raw)
    except ValueError:
        return None


def suite_lines(log: str) -> List[str]:
    """pytest's summary lines in a job's log, as gh prints one: job, step and '<stamp> <text>', tab
    separated. A line counts only when pytest's summary is all of its text, and the step field, which
    reads UNKNOWN STEP today, is never read."""
    found = []
    for ln in log.splitlines():
        text = _ANSI.sub("", ln.split("\t", 2)[-1])
        stamp = _STAMP.match(text)
        text = (text[stamp.end():] if stamp else text).strip(" =")
        if _SUITE.fullmatch(text):
            found.append(text)
    return found


def _concluded(item: Mapping[str, object]) -> str:
    """A run's or a job's state: its conclusion once completed, else its status."""
    if item.get("status") == "completed":
        return str(item.get("conclusion") or "no conclusion")
    return str(item.get("status") or "unknown")


def ci(slug: str, sha: str) -> Tuple[int, List[str]]:
    """(exit code, lines to print) for `ci OWNER/REPO SHA`: see the module docstring."""
    if not _SLUG.fullmatch(slug):
        return 2, ["REFUSED: the repository is named OWNER/REPO"]
    if not _SHA.fullmatch(sha):
        return 2, ["REFUSED: the commit is its full 40-hex sha, so CI is read for exactly that commit"]
    listed = _gh_json("run", "list", "--repo", slug, "--commit", sha, "--limit", "100",
                      "--json", "databaseId,workflowName,event,headSha")
    if not isinstance(listed, list):
        return 2, ["REFUSED: gh run list gave no answer; is gh installed and signed in?"]
    runs = [r for r in listed if r.get("headSha") == sha]
    out = [f"CI {slug} {sha}: {len(runs)} run(s)"]
    if len(listed) > len(runs):
        out.append(f"IGNORED {len(listed) - len(runs)} run(s) on another commit")
    red: List[str] = []
    n_jobs = n_counts = 0
    for run in sorted(runs, key=lambda r: r["databaseId"]):
        rid = run["databaseId"]
        view = _gh_json("run", "view", str(rid), "--repo", slug, "--json", "status,conclusion,headSha,jobs")
        if not isinstance(view, dict) or view.get("headSha") != sha:
            red.append(f"run {rid} could not be read for this commit")
            continue
        state = _concluded(view)
        out.append(f"RUN {rid} {run.get('workflowName')} ({run.get('event')}): {state}")
        if state != "success":
            red.append(f"run {rid} is {state}")
        jobs = view.get("jobs") or []
        if not jobs:
            red.append(f"run {rid} has no job")
        for job in sorted(jobs, key=lambda j: str(j.get("name"))):
            n_jobs += 1
            name, state = " ".join(str(job.get("name")).split()), _concluded(job)
            out.append(f"JOB {name}: {state}")
            if state != "success":
                red.append(f"job {name} is {state}")
            if job.get("status") != "completed":
                continue
            log = _gh("run", "view", "--job", str(job["databaseId"]), "--repo", slug, "--log")
            if log is None:
                out.append("  LOG unreadable")
                red.append(f"job {name} has no readable log")
                continue
            counts = suite_lines(log.decode("utf-8", "replace"))
            n_counts += len(counts)
            out += [f"  SUITE {c}" for c in counts] or ["  SUITE none: no count line in this job's log"]
            if state == "success" and any(_RED_COUNT.search(c) for c in counts):
                red.append(f"job {name} reports failures in a success")
            elif state == "success" and not all(_PASSED_COUNT.search(c) for c in counts):
                red.append(f"job {name} has a count line that passed nothing")
    if not runs:
        red.append("no workflow run on this commit")
    elif not red and not n_counts:
        red.append("no job printed a suite count line")
    if red:
        out.append("CI NOT GREEN: " + "; ".join(red))
        return 1, out
    out.append(f"CI GREEN: {len(runs)} run(s), {n_jobs} job(s), {n_counts} suite count line(s), "
               f"every job a success, on {sha}")
    return 0, out


# ---------------------------------------------------------------------- record: a run from a worktree

def _refused(why: str) -> Tuple[int, List[str]]:
    return 2, [f"REFUSED: {why}"]


def _lf(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def _quoted(path: str) -> str:
    """A path in a printed command: forward slashes and double quotes read alike in every shell here."""
    return '"' + path.replace("\\", "/") + '"'


def _origin_default(root: str) -> Optional[Tuple[str, str]]:
    """(origin's default branch, its sha) as origin itself says, or None."""
    raw = _git(root, "ls-remote", "--symref", "origin", "HEAD", timeout=120)
    m = re.match(r"ref: refs/heads/(\S+)\tHEAD\n([0-9a-f]{40})\tHEAD\n", (raw or b"").decode("utf-8", "replace"))
    return (m.group(1), m.group(2)) if m else None


def _last_pushed(events: Sequence[dict]) -> Optional[str]:
    """The run's last pushed commit: a rebase leaves the commit events behind, and its note's head is it."""
    for e in reversed(events):
        if e.get("ev") == "commit":
            return e.get("sha")
        if e.get("ev") == "note" and e.get("kind") == "rebase":
            return e.get("head")
    return None


def _at_last_pushed(root: str, tip: str, pushed: str, rel: str) -> bool:
    """Is `tip` the run's last pushed commit: that commit itself, or only this run's own records above it?
    Commit by commit, never the net diff, which an empty commit or a pair that cancels out would pass."""
    if tip == pushed:
        return True
    if _git(root, "merge-base", "--is-ancestor", pushed, tip) is None:
        return False
    above = (_git(root, "rev-list", f"{pushed}..{tip}") or b"").split()
    touched = (_git(root, "log", "--format=", "--name-only", f"{pushed}..{tip}") or b"").decode("utf-8", "replace")
    return bool(above) and touched.split() == [rel] * len(above)


def _record_failed(root: str, wt: str, why: str) -> Tuple[int, List[str]]:
    return 1, ["the worktree is kept for a look, and nothing is pushed; remove it with:",
               f"  git -C {_quoted(root)} worktree remove --force {_quoted(wt)}",
               f"RECORD FAIL: {why}; do not push"]


def _harness_record(wt: str, run: str, message: str) -> Optional[str]:
    """Run harness record with HARNESS_ROOT at the worktree. None when it recorded, else why not."""
    tool = os.path.join(_REPO, *harness.SELF_REL.split("/"))
    try:
        r = subprocess.run([sys.executable, tool, "record", run, "-F", message], cwd=wt,
                           env={**os.environ, "HARNESS_ROOT": wt}, capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"harness record did not finish ({type(e).__name__})"
    if r.returncode == 0:
        return None
    said = r.stderr.decode("utf-8", "replace").strip().splitlines()
    return "harness record failed" + (f": {said[-1]}" if said else "")


def record(root: str, run: str, message: Optional[str] = None) -> Tuple[int, List[str]]:
    """(exit code, lines to print) for `record ROOT RUN`: see the module docstring. Never pushes."""
    why = _self_unchanged() or _committed_here(harness.SELF_REL)
    if why:
        return _refused(why)
    if not harness._ID.match(run):
        return _refused("the run id is not a harness run id")
    if message is not None and not os.path.isfile(message):
        return _refused("there is no such message file")
    if (_git(root, "rev-parse", "--show-prefix") or b"-").strip():
        return _refused("ROOT is not the top of a git checkout")
    L = harness.Ledger(root, run)
    if not L.exists():
        return _refused("ROOT holds no ledger for this run")
    try:
        flying = [s for s in L.steps() if L.state(s) not in ("committed", "abandoned")]
        harness._scan_ledger(L)
        pushed = _last_pushed(L.events())
    except harness.HarnessError as e:
        return _refused(str(e))
    except (ValueError, KeyError):
        return _refused("the run's ledger cannot be read")
    if flying:
        return _refused(f"step {flying[0]} is in flight, and a record would move HEAD under it")
    if not pushed:
        return _refused("the ledger names no commit of this run")

    origin = _origin_default(root)
    if origin is None:
        return _refused("origin's default branch cannot be read")
    branch, tip = origin
    if _git(root, "fetch", "origin", timeout=300) is None:
        return _refused("git fetch failed")
    if (_git(root, "rev-parse", f"refs/remotes/origin/{branch}") or b"").decode().strip() != tip:
        return _refused(f"origin/{branch} is not where origin says after the fetch")
    if not _at_last_pushed(root, tip, pushed, L.rel):
        return _refused(f"origin/{branch} is at {tip[:10]}, not at the run's last pushed commit {pushed[:10]}")
    with open(L.path, "rb") as fh:
        copy = _lf(fh.read())
    held = _lf(_git(root, "cat-file", "blob", f"{tip}:{L.rel}") or b"")
    if copy == held:
        return _refused("the ledger has nothing new to record")
    if not copy.startswith(held):
        return _refused("this checkout's ledger does not extend origin's: bring the checkout to origin first")

    wt = tempfile.mkdtemp(prefix="record-")
    if _git(root, "worktree", "add", "--quiet", "--detach", wt, tip, timeout=600) is None:
        return _record_failed(root, wt, "git worktree add failed")
    target = os.path.join(wt, *L.rel.split("/"))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copyfile(L.path, target)
    with tempfile.TemporaryDirectory(prefix="record-message-") as td:
        if message is None:
            message = os.path.join(td, "message.txt")
            with open(message, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(f"Harness run {run}: the ledger is recorded\n")
        why = _harness_record(wt, run, message)
    if why:
        return _record_failed(root, wt, why)
    recorded = _git(wt, "show", f"HEAD:{L.rel}")
    with open(L.path, "rb") as fh:
        copy = _lf(fh.read())
    if recorded is None or _lf(recorded) != copy:
        return _record_failed(root, wt, "the recorded ledger differs from the working copy, CRLF aside")

    sha = (_git(wt, "rev-parse", "HEAD") or b"").decode().strip()
    on = (_git(root, "symbolic-ref", "-q", "--short", "HEAD") or b"").decode().strip()
    arrive = f"merge --ff-only origin/{branch}" if on == branch else f"switch -c <next branch> origin/{branch}"
    checkout, kept = _quoted(root), _quoted(wt)
    return 0, [
        "recorded in a worktree kept for the push; nothing is pushed, and the checkout's files are as they were",
        "run these yourself, in order; this tool never runs them:",
        f"  git -C {kept} push origin HEAD:refs/heads/{branch}",
        f"  git -C {checkout} fetch origin",
        f"  git -C {checkout} diff --ignore-cr-at-eol --exit-code origin/{branch} -- {L.rel}",
        f"  git -C {checkout} worktree remove {kept}",
        f"  git -C {checkout} checkout -- {L.rel}",
        f"  git -C {checkout} {arrive}",
        "the diff exits 0 when the ledger matches; a non-zero exit means a line reached the ledger after this "
        "record: stop there, before the discard",
        f"held when git diff origin/{branch} -- {L.rel} is empty in the checkout; "
        "never append to this run's ledger in a checkout that lacks the record commit",
        f"RECORD PASS: {run} as {sha} on origin/{branch} at {tip}; the recorded ledger equals the working copy, "
        "CRLF aside",
    ]


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="context.py", description="The harness's records of record.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="scan RULES.md and BACKLOG.md and resolve every pointer")
    c.add_argument("root", nargs="?", default=_REPO, help="the concordance-2 checkout (default: this one)")
    b = sub.add_parser("brief", help="assemble a role's working context from the records")
    b.add_argument("--role", required=True, choices=ROLES)
    b.add_argument("--wants-cap", type=int, default=WANTS_CAP)
    b.add_argument("root", help="the checkout holding the run's ledger")
    b.add_argument("run")
    b.add_argument("step", nargs="?")
    g = sub.add_parser("ci", help="read a commit's CI: each job's conclusion and the suite count lines")
    g.add_argument("repo", metavar="OWNER/REPO")
    g.add_argument("sha")
    r = sub.add_parser("record", help="record a run in a kept worktree at origin's default branch; never pushes")
    r.add_argument("root", help="the checkout holding the run's ledger")
    r.add_argument("run")
    r.add_argument("-F", dest="message", help="the commit message file (default: one plain line naming the run)")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if a.cmd == "brief":
        try:
            lines = brief(a.role, os.path.abspath(a.root), a.run, a.step, cap=a.wants_cap)
        except BriefRefused as e:
            print(f"REFUSED: {e}", file=sys.stderr)
            return 2
        sys.stdout.flush()                # LF bytes on every platform, so a brief is the same file everywhere
        sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()
        return 0
    if a.cmd == "ci":
        code, lines = ci(a.repo, a.sha)
    elif a.cmd == "record":
        code, lines = record(os.path.abspath(a.root), a.run, a.message and os.path.abspath(a.message))
    else:
        code, lines = check(os.path.abspath(a.root))
    for ln in lines:
        print(ln)
    return code


if __name__ == "__main__":
    sys.exit(main())
