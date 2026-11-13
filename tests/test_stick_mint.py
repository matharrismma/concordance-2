"""tools/stick_mint.py, the mint unit (run 2026-11-13-stick-ship), run here as the real file in a temporary root that
stands in for the box: a copy of src/, a small catalog of data entries and an empty keeping, with every box path passed
in (the root, the scratch base, a stand-in reading of memory) and a stand-in systemctl. Nothing here reaches the box or
calls ssh. Also pinned: tools/stick_mints.txt, each listed line's entry, its file hash and its seals, and each listed
hash as an isolated run mints it, in the gate on Windows and in CI on Linux, so both platforms mint the same hashes.

Where a promise is Linux's own (oom_score_adj, nice, ionice, the address-space cap), the test runs on Linux, in CI, and
says that it skips anywhere else. No test waits on a clock that load can run out: a wait is for a process to end, with a
generous bound only a broken run reaches. Every test that runs the unit is `told`: a failure carries each run's output,
its results and the stand-in box's files. The keeping is read back here by the engine's own readers with explicit
directories (cas.verify, ledger.verify_chain, tickstick.fold), never through the unit's own predicate."""
from __future__ import annotations

import ast
import functools
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "tools" / "stick_mint.py"
LISTING = ROOT / "tools" / "stick_mints.txt"
CATALOG = ROOT / "data" / "sticks"
LINUX = sys.platform.startswith("linux")
LINUX_ONLY = ("Linux's own (/proc/self/oom_score_adj, nice, ionice, RLIMIT_AS, ru_maxrss): proven by CI on Linux, "
              f"skipped here on {sys.platform}")
GENEROUS = 600                          # seconds: a bound only a broken run reaches, never a loaded laptop
PLENTY_KB = 8 * 1024 * 1024             # 8 GB available
STATUS_EXIT = {"minted": 0, "present": 0, "retracted": 0, "absent": 0, "failed": 1, "refused": 3}

sys.path.insert(0, str(ROOT / "src"))
from concordance import cas, ledger, tickstick  # noqa: E402

ISOLATED = r"""
import json, os, shutil, sys, tempfile
root, catalog, names = sys.argv[1], sys.argv[2], sys.argv[3:]
for k in [k for k in os.environ if k.upper().startswith("CONCORDANCE_")]:
    del os.environ[k]
os.environ.update(CONCORDANCE_SEAL_INDEX="0", CONCORDANCE_VERIFY_TIMEOUT_S="1800", CONCORDANCE_RIEMANN_MAX="1e9",
                  WEB_FIND_DISABLED="1")
sys.path.insert(0, os.path.join(root, "src"))
from concordance import cas, sticks
entries = sticks.load_catalog(catalog).entries if catalog != "-" else {e["name"]: e for e in json.load(sys.stdin)}
out = {}
for name in names:
    tmp = tempfile.mkdtemp(prefix="nh-test-isolated-")
    os.environ["CONCORDANCE_DATA_DIR"] = os.path.join(tmp, "data")
    from concordance import science_cards
    cas._COLD_CARDS_WRITTEN.clear(); cas._COLD_SPINE_WRITTEN = False; science_cards._MINTED = None
    entry = entries[name]
    pairs = [[s["key"], sticks.seal(s)] for s in entry.get("seals", [])]
    rc = sticks.run(entry) if "sticks" in entry and all(h for _, h in pairs) else None
    out[name] = {"seals": pairs, "rc": rc, "cas": sorted(cas.list_hashes())}
    shutil.rmtree(tmp, ignore_errors=True)
print("ISOLATED " + json.dumps(out))
"""


def isolated(names, entries=None) -> dict:
    """Each entry run in a fresh temporary keeping in the environment tools/tick_golden.py uses, in a process of its
    own: its seals' hashes in order, the run's return code and the CAS it leaves."""
    catalog = "-" if entries is not None else str(CATALOG)
    done = subprocess.run([sys.executable, "-I", "-B", "-c", ISOLATED, str(ROOT), catalog, *names],
                          input=json.dumps(entries or []), capture_output=True, text=True, timeout=GENEROUS,
                          env={k: v for k, v in os.environ.items() if not k.upper().startswith("CONCORDANCE_")})
    found = [line for line in done.stdout.splitlines() if line.startswith("ISOLATED ")]
    assert done.returncode == 0 and found, done.stdout[-3000:] + done.stderr[-3000:]
    return json.loads(found[-1][len("ISOLATED "):])


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sm():
    return _load("stick_mint_under_test", UNIT)


def a_run_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + secrets.token_hex(6)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def files_under(folder: Path, skip=()) -> dict:
    return {p.relative_to(folder).as_posix(): sha(p.read_bytes()) for p in sorted(folder.rglob("*"))
            if p.is_file() and p.relative_to(folder).as_posix() not in skip} if folder.exists() else {}


# ------------------------------------------------------------------------------------------------ a test catalog

def numeric(key: str, expr: str, value, nid: str = None) -> dict:
    return {"key": key, "nid": nid or key, "expr": expr, "value": value, "tol": 1e-12, "domain": "mathematics"}


SHARED_QUESTION = "A test stick for the mint path"


def an_entry(name: str, seals: list, marks: list, question: str = SHARED_QUESTION) -> dict:
    return {"schema": 1, "name": name, "aliases": [f"{name}_test_alias"], "doc": f"{name}: a test entry",
            "seals": seals,
            "sticks": [{"question": question, "statement": "A stick the tests mint.", "field": "mathematics",
                        "references": ["a test reference"], "by": f"tests - {name}", "marks": marks}]}


ALPHA = an_entry("alpha", [numeric("two_to_ten", "2**10", 1024), numeric("three_squared", "3**2", 9)], [
    {"kind": "witness", "claim": "[alpha] 2**10 = 1024 (sealed)", "seal": "two_to_ten"},
    {"kind": "witness", "claim": "[alpha] 3**2 = 9 (sealed)", "seal": "three_squared"},
    {"kind": "equivalence", "claim": "[alpha] a cited test mark", "source": "A. Tester, A Book of Tests (2026)"},
    {"kind": "note", "claim": "[alpha] a note needs no seal"}])
# beta marks the same stick as alpha with a seal of its own
BETA = an_entry("beta", [numeric("five_cubed", "5**3", 125)], [
    {"kind": "witness", "claim": "[beta] 5**3 = 125 (sealed)", "seal": "five_cubed"}])
# gamma states a mark with the same stick and the same seal as alpha's two_to_ten (the same seal mints the same hash)
GAMMA = an_entry("gamma", [numeric("two_to_ten_again", "2**10", 1024, nid="two_to_ten")], [
    {"kind": "witness", "claim": "[gamma] 2**10 = 1024 again (sealed)", "seal": "two_to_ten_again"}])
CONDMAT = an_entry("condmat", [{"key": "von_klitzing", "domain": "condensed_matter", "artifact": "CONDMAT_VERIFY",
                                "spec": {"claimed_von_klitzing_ohm": 25812.807}}], [
    {"kind": "witness", "claim": "[condmat] the von Klitzing constant h/e^2 (sealed)", "seal": "von_klitzing"}],
    question="A test stick whose seal's domain holds an underscore")
BADSOURCE = an_entry("badsource", [numeric("two_to_ten", "2**10", 1024)], [
    {"kind": "witness", "claim": "[badsource] 2**10 = 1024 (sealed)", "seal": "two_to_ten"},
    {"kind": "equivalence", "claim": "[badsource] a cited mark whose source is too short", "source": "x"}],
    question="A test stick with a cited mark whose source is too short")
BADKIND = an_entry("badkind", [numeric("two_to_ten", "2**10", 1024)], [
    {"kind": "witnes", "claim": "[badkind] a mark of a kind tick does not know", "seal": "two_to_ten"}],
    question="A test stick with a mark of an unknown kind")
BOUND_QUESTION = "A test stick that already has a bound"
BADBOUND = an_entry("badbound", [numeric("two_to_ten", "2**10", 1024)], [
    {"kind": "bound", "claim": "[badbound] verified to 10, short of the stick's bound", "seal": "two_to_ten",
     "up_to": 10, "unit": "n"}], question=BOUND_QUESTION)
BROKEN = an_entry("broken", [numeric("two_to_ten", "2**10", 1000)], [
    {"kind": "witness", "claim": "[broken] 2**10 = 1000, which does not hold", "seal": "two_to_ten"}],
    question="A test stick whose seal does not hold")
HANDLED = {"schema": 1, "name": "handled", "aliases": ["handled_test_alias"], "handler": "riemann", "params": [],
           "why_python": "a test handler entry"}
ENTRIES = {e["name"]: e for e in (ALPHA, BETA, GAMMA, CONDMAT, BADSOURCE, BADKIND, BADBOUND, BROKEN, HANDLED)}


def entry_bytes(entry: dict) -> bytes:
    return (json.dumps(entry, indent=1) + "\n").encode("utf-8")


@pytest.fixture(scope="module")
def hashes() -> dict:
    """Every test entry's seal hashes as an isolated run mints them; None for a seal that does not hold."""
    found = isolated([n for n in ENTRIES if "seals" in ENTRIES[n]], list(ENTRIES.values()))
    return {name: dict(got["seals"]) for name, got in found.items()}


def a_line(name: str, hashes: dict, expect: str = None, change: str = None) -> str:
    seals = dict(hashes.get(name) or {})
    for key in seals:
        seals[key] = seals[key] or "a" * 64
    if change:
        seals[change] = seals[change][:-1] + ("0" if seals[change][-1] != "0" else "1")
    tail = "".join(f" {k}={h}" for k, h in seals.items()) + (f" expect={expect}" if expect else "")
    return f"# {name}: a test entry, minted by the tests\n{name} {sha(entry_bytes(ENTRIES[name]))}{tail}"


def stand_in_systemctl(folder: Path, environment: str) -> Path:
    """A systemctl that prints a canned `show` output and logs its arguments, for this platform's shell."""
    out, log = folder / "systemctl.out", folder / "systemctl.log"
    out.write_text(f"Environment={environment}\n", encoding="utf-8")
    if os.name == "nt":
        path = folder / "systemctl.cmd"
        path.write_text(f'@echo off\r\necho %*>> "{log}"\r\ntype "{out}"\r\n', encoding="utf-8")
    else:
        path = folder / "systemctl"
        path.write_text(f'#!/bin/sh\nprintf \'%s\\n\' "$*" >> "{log}"\ncat "{out}"\n', encoding="utf-8")
        path.chmod(0o755)
    return path


class Box:
    """A temporary root standing in for the box: a copy of src/, its catalog and listing, its keeping under data/, a
    scratch base outside it, a stand-in memory reading and a stand-in systemctl naming <root>/data."""
    current = None                      # the box the running test made, for `told`

    def __init__(self, tmp_path: Path, names, lines, ledger_lock: bool = True):
        Box.current = self
        self.tmp, self.runs = tmp_path, []
        self.root, self.scratch = tmp_path / "box", tmp_path / "scratch"
        shutil.copytree(ROOT / "src", self.root / "src", ignore=shutil.ignore_patterns("__pycache__"))
        (self.root / "tools").mkdir()
        (self.root / "data" / "sticks").mkdir(parents=True)
        self.scratch.mkdir()
        self.data = self.root / "data"
        for name in names:
            (self.data / "sticks" / f"{name}.json").write_bytes(entry_bytes(ENTRIES[name]))
        self.listing(lines)
        if ledger_lock:                 # the box's keeping already holds the ledger's lock file
            (self.data / "ledger").mkdir()
            (self.data / "ledger" / ".chain.lock").write_bytes(b"")
        self.meminfo = tmp_path / "meminfo"
        self.memory(PLENTY_KB)
        self.engine = tmp_path / "engine"
        self.engine.mkdir()
        self.systemctl = stand_in_systemctl(self.engine, f'"CONCORDANCE_DATA_DIR={self.data.as_posix()}" '
                                                         f'"CONCORDANCE_STRONGS_DIR={self.data.as_posix()}/strongs"')

    def listing(self, lines) -> None:
        head = "# THE MINT LISTING of a test box\n\n"
        (self.root / "tools" / "stick_mints.txt").write_bytes((head + "\n".join(lines) + "\n").encode("utf-8"))

    def memory(self, kb: int) -> None:
        self.meminfo.write_bytes(f"MemTotal:       16000000 kB\nMemAvailable:   {kb} kB\n".encode())

    def command(self, cmd: str, name: str, run_id: str) -> list:
        return [sys.executable, "-I", str(UNIT), cmd, name, "--root", str(self.root), "--run-id", run_id,
                "--meminfo", str(self.meminfo), "--systemctl", str(self.systemctl), "--scratch-base", str(self.scratch)]

    def run(self, cmd: str, name: str, run_id: str = None, **extra):
        run_id = run_id or a_run_id()
        env = dict(os.environ)          # the test process's own CONCORDANCE_ variables ride along: the unit drops them
        env.update(extra)
        argv = self.command(cmd, name, run_id)
        done = subprocess.run(argv, env=env, cwd=str(self.root), capture_output=True, text=True, timeout=GENEROUS)
        self.runs.append((argv, done.returncode, done.stdout, done.stderr))
        result = self.result(run_id)
        assert done.returncode == STATUS_EXIT[result["status"]], (done.returncode, result["status"])
        return done.returncode, result, run_id

    def result(self, run_id: str) -> dict:
        return json.loads((self.data / "mints" / ".results" / f"{run_id}.json").read_text(encoding="utf-8"))

    def snapshot(self, skip=()) -> dict:
        """Every file of the box and the scratch base by its sha256; `skip`, by path under the box, is never read."""
        return {**{f"box/{k}": v for k, v in files_under(self.root, skip).items()},
                **{f"scratch/{k}": v for k, v in files_under(self.scratch).items()}}

    def story(self) -> str:
        parts = [f"--- the unit ran {' '.join(a[3:5])}\nexit {rc}\n{out}\n{err}" for a, rc, out, err in self.runs]
        parts.append("--- the box's data/\n" + "\n".join(p.relative_to(self.root).as_posix()
                                                         for p in sorted(self.data.rglob("*")) if "sticks" not in p.parts))
        for result in sorted((self.data / "mints" / ".results").glob("*.json")):
            parts.append(f"--- {result.name}\n{result.read_text(encoding='utf-8', errors='replace')}")
        parts.append("--- the scratch base\n" + "\n".join(p.relative_to(self.scratch).as_posix()
                                                          for p in sorted(self.scratch.rglob("*"))))
        return "\n".join(parts)


def told(test):
    """A test that runs the unit: if it fails, the failure carries its box's story."""
    @functools.wraps(test)
    def run(*args, **kwargs):
        Box.current = None
        try:
            return test(*args, **kwargs)
        except Exception as e:
            if Box.current is None:
                raise
            raise AssertionError(f"{type(e).__name__}: {e}\n\n{Box.current.story()}") from e
    return run


def only_mints_changed(before: dict, after: dict) -> list:
    """Every path added, removed or changed outside data/mints/."""
    paths = set(before) | set(after)
    return sorted(p for p in paths if before.get(p) != after.get(p) and not p.startswith("box/data/mints/"))


def ledger_name(domain: str, h: str) -> str:
    """The file the ledger writes for a seal, by its own naming (ledger.seal_to_ledger, the precedent id receipts.mint
    gives it)."""
    return ledger._slugify(f"{domain}/{h[:16]}") + ".json"


def receipt_ids(data: Path) -> set:
    path = data / "receipt_cards.jsonl"
    return {json.loads(line)["id"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()} \
        if path.exists() else set()


def has_mark(ticks: list, mark: dict, seal: str) -> bool:
    want = {"kind": mark["kind"], "claim": mark["claim"], **({"seal": seal} if seal else {}),
            **({"source": mark["source"]} if "source" in mark else {})}
    return any(all(t.get(k) == v for k, v in want.items()) and (seal or "seal" not in t) for t in ticks)


# ------------------------------------------------------------------------------------------------ the listing

def test_the_listing_holds_the_two_canaries_each_after_its_comment(sm):
    text = LISTING.read_text(encoding="utf-8")
    lines = sm.parse_listing(text)
    assert {n: line.expect for n, line in lines.items() if line.expect} == {"euler_e": "present", "calculus": "refused"}
    rows = text.splitlines()
    for line in lines.values():
        before = rows[line.line - 2]
        assert before.startswith(f"# {line.name}:") and len(before) > len(line.name) + 20, before


def test_every_listed_line_is_a_data_entry_whose_file_hashes_as_listed_with_every_seal_in_order(sm):
    for line in sm.parse_listing(LISTING.read_text(encoding="utf-8")).values():
        path = CATALOG / f"{line.name}.json"
        assert path.is_file(), line.name
        entry = json.loads(path.read_text(encoding="utf-8"))
        assert entry["name"] == line.name and "handler" not in entry, line.name
        assert sm.entry_sha256(path.read_bytes()) == line.entry_hash, line.name
        assert sha(path.read_bytes().replace(b"\r\n", b"\n")) == line.entry_hash, line.name
        assert [k for k, _ in line.seals] == [s["key"] for s in entry.get("seals", [])], line.name


def test_every_listed_hash_is_what_an_isolated_run_mints_and_the_refused_canary_differs_in_exactly_one(sm):
    """Run here in the gate on Windows and in CI on Linux: both platforms mint the listed hashes."""
    lines = sm.parse_listing(LISTING.read_text(encoding="utf-8"))
    got = isolated(sorted(lines))
    for name, line in lines.items():
        minted = dict(got[name]["seals"])
        assert got[name]["rc"] == 0 and set(got[name]["cas"]) == set(minted.values()), (name, got[name])
        listed = dict(line.seals)
        assert list(listed) == list(minted), name
        differ = [k for k in listed if listed[k] != minted[k]]
        if line.expect == "refused":
            assert len(differ) == 1, (name, differ)
            assert listed[differ[0]] not in minted.values()
        else:
            assert differ == [], (name, differ)


GOOD = f"alpha {'a' * 64} two_to_ten={'b' * 64}"


@pytest.mark.parametrize("line,why", [
    (GOOD + " expect=maybe", "not an entry"),
    (GOOD.replace("alpha", "Alpha", 1), "not an entry"),
    (f"alpha {'a' * 63} two_to_ten={'b' * 64}", "not an entry"),
    (f"alpha {'a' * 64} two_to_ten={'b' * 63}", "not an entry"),
    (GOOD + " expect=present three=" + "c" * 64, "not an entry"),
    (GOOD.replace(" ", "\t"), "not an entry"),
    (f"data/sticks/alpha.json {'a' * 64}", "not an entry"),
    (GOOD + " two_to_ten=" + "c" * 64, "a seal key twice"),
    (GOOD + " free", "not an entry"),
])
def test_the_listing_refuses_what_the_path_will_not_run(sm, line, why):
    with pytest.raises(sm.ListingError, match=re.escape(why)):
        sm.parse_listing(f"# alpha: a test line\n{line}\n")


def test_the_listing_refuses_an_entry_without_its_comment_and_a_name_twice(sm):
    with pytest.raises(sm.ListingError, match="no comment line"):
        sm.parse_listing(GOOD + "\n")
    with pytest.raises(sm.ListingError, match="no comment line"):
        sm.parse_listing(f"# alpha: a test line\n\n{GOOD}\n")
    with pytest.raises(sm.ListingError, match="listed twice"):
        sm.parse_listing(f"# alpha: one\n{GOOD}\n# alpha: two\n{GOOD}\n")
    assert list(sm.parse_listing(f"# alpha: a test line\r\n{GOOD} expect=present\r\n")) == ["alpha"]   # Windows


# ------------------------------------------------------------------------------------------------ a first mint

@pytest.fixture(scope="module")
def first(tmp_path_factory, hashes):
    """One first mint of alpha into an empty keeping (no data/ledger/ yet), with CONCORDANCE_ variables in the unit's
    parent that name other keepings."""
    tmp = tmp_path_factory.mktemp("first")
    box = Box(tmp, ["alpha"], [a_line("alpha", hashes)], ledger_lock=False)
    elsewhere = tmp / "elsewhere"
    elsewhere.mkdir()
    before = box.snapshot()
    rc, result, run_id = box.run("mint", "alpha", CONCORDANCE_LEAK_PROBE="inherited",
                                 CONCORDANCE_CAS_DIR=str(elsewhere / "cas"),
                                 CONCORDANCE_LEDGER_DIR=str(elsewhere / "ledger"),
                                 CONCORDANCE_DATA_DIR=str(elsewhere / "data"))
    return {"box": box, "before": before, "after": box.snapshot(), "rc": rc, "result": result, "run_id": run_id,
            "elsewhere": elsewhere, "listed": hashes["alpha"]}


def _story(first):
    Box.current = first["box"]


@told
def test_a_listed_entry_mints_its_seals_each_with_its_ledger_record_and_receipt_card_and_every_mark_reads_back(first):
    _story(first)
    box, result, listed = first["box"], first["result"], first["listed"]
    assert (first["rc"], result["status"], result["step"]) == (0, "minted", 4), result
    data = box.data
    for key, h in listed.items():
        assert cas.verify(h, base_dir=data / "cas") == (True, "ok"), key
        record = json.loads((data / "ledger" / ledger_name("mathematics", h)).read_text(encoding="utf-8"))
        assert record["record_hash"] == h, key
        assert cas.receipt_card_id(h) in receipt_ids(data), key
    chain = ledger.verify_chain(data / "ledger", cas_base=data / "cas")
    assert chain["ok"] and chain["total"] == 2 and chain["verified"] == 2, chain
    ticks = tickstick.fold(data)["stick_a_test_stick_for_the_mint_path"]["ticks"]
    for mark in ALPHA["sticks"][0]["marks"]:
        assert has_mark(ticks, mark, listed.get(mark.get("seal"), "")), mark
    assert len(ticks) == 4
    assert result["sticks"] == [{"stick": "stick_a_test_stick_for_the_mint_path", "ticks_after": 4, "ticks_before": 0}]
    assert [e["event"] for e in result["marks_added"]] == ["stick", "tick", "tick", "tick", "tick"]
    assert result["marks_added"] == result["rehearsal"]["appended"]
    assert all(item["ok"] for item in result["read_back"]), result["read_back"]
    assert sorted(i["item"] for i in result["would_add"]) == sorted(
        ["cas object", "receipt card", "ledger record"] * 2 + ["receipt spine card", "stick"] + ["mark"] * 4)
    assert [c["when"] for c in result["chain"]] == ["before", "after"]
    assert all(isinstance(c["lock_held_s"], float) for c in result["chain"])
    assert result["totals"] == {"after": {"cas_objects": 2, "ledger_records": 2},
                                "before": {"cas_objects": 0, "ledger_records": 0}}
    assert result["memory"]["mem_available_kb"] == PLENTY_KB and result["memory"]["cap_mb"] == 512


@told
def test_a_unit_run_that_rehearses_then_mints_writes_a_receipt_card_for_each_object_it_creates(first):
    """The rehearsal ran in its own process: had its cold-path caches reached the mint, the real keeping would hold the
    CAS objects with no receipt card (checker-102, run 2026-11-13-stick-ship line 6, measured that in one process)."""
    _story(first)
    box, result, listed = first["box"], first["result"], first["listed"]
    assert sorted(result["mint"]["created"]) == sorted(listed.values())
    assert result["rehearsal"]["exit_code"] == 0 and sorted(result["rehearsal"]["cas"]) == sorted(listed.values())
    assert {cas.receipt_card_id(h) for h in listed.values()} <= receipt_ids(box.data)
    assert {c["seal"] for c in result["receipt_cards_written"]} == set(listed.values())
    cards = [i for i in result["read_back"] if i["item"] == "receipt card"]
    assert len(cards) == 2 and all(i["ok"] for i in cards)


@told
def test_the_receipt_spine_card_a_first_receipt_card_writes_is_named_in_would_add_and_read_back(first):
    """The cold path writes the receipt spine card before the first receipt card of each process (cas._RECEIPT_SPINE,
    _COLD_SPINE_WRITTEN), so a mint that creates an object in a keeping without it writes it: checker-104, run
    2026-11-13-stick-ship line 17's observation (c)."""
    _story(first)
    result, box = first["result"], first["box"]
    spine = cas._RECEIPT_SPINE
    assert [i for i in result["would_add"] if i["item"] == "receipt spine card"] == [
        {"id": spine, "item": "receipt spine card", "path": "data/receipt_cards.jsonl"}]
    assert [(i["id"], i["ok"]) for i in result["read_back"] if i["item"] == "receipt spine card"] == [(spine, True)]
    assert spine in receipt_ids(box.data) and result["receipt_spine_cards_written"] == 1


@told
def test_the_files_a_first_mint_writes_are_exactly_the_list(first):
    _story(first)
    box, listed, run_id = first["box"], first["listed"], first["run_id"]
    before, after = first["before"], first["after"]
    added = {p for p in after if p not in before}
    assert {p for p in before if p not in after} == set() and {p for p in before if before[p] != after.get(p)} == set()
    want = {f"box/data/cas/{h[:2]}/{h[2:]}.json" for h in listed.values()}
    want |= {f"box/data/ledger/{ledger_name('mathematics', h)}" for h in listed.values()}
    want |= {"box/data/ledger/.chain.head", "box/data/ledger/.chain.lock", "box/data/receipt_cards.jsonl",
             "box/data/sticks.jsonl", "box/data/mints/.lock", f"box/data/mints/.results/{run_id}.json"}
    assert added == want                                    # no verified card: a numeric seal's trail has no claim
    assert list(box.scratch.iterdir()) == []                # the rehearsal's scratch keeping, removed
    assert files_under(first["elsewhere"]) == {}


@told
def test_the_unit_sees_no_inherited_concordance_variable_and_runs_with_exactly_the_environment_named(first):
    _story(first)
    result = first["result"]
    want = {"CONCORDANCE_DATA_DIR": "<root>/data", "CONCORDANCE_RIEMANN_MAX": "1e9", "CONCORDANCE_SEAL_INDEX": "0",
            "CONCORDANCE_VERIFY_TIMEOUT_S": "1800", "WEB_FIND_DISABLED": "1"}
    assert result["environment"] == want
    assert result["rehearsal"]["environment"] == {**want, "CONCORDANCE_DATA_DIR": "<scratch>/data"}
    assert result["import_path"] == "<root>/src" and result["rehearsal"]["import_path"] == "<root>/src"
    assert result["engine_from"] == "<root>/src/concordance" == result["rehearsal"]["engine_from"]
    text = json.dumps(result)
    box = first["box"]
    for absolute in (str(box.root), box.root.as_posix(), str(box.scratch), box.scratch.as_posix(), str(ROOT)):
        assert absolute not in text                         # a result quotes no path but those under data/


@pytest.mark.skipif(not LINUX, reason=LINUX_ONLY)
@told
def test_on_linux_the_unit_runs_at_oom_score_adj_1000_under_nice_and_ionice_and_a_mint_completes_under_the_cap(first):
    _story(first)
    result = first["result"]
    assert result["status"] == "minted"
    assert result["confinement"] == {"address_space_cap_mb": 512, "ionice": "-c 2 -n 7", "nice": 19,
                                     "oom_score_adj": 1000}
    assert result["rehearsal"]["confinement"] == {"address_space_limit_mb": 512, "nice": 19, "oom_score_adj": 1000}
    assert isinstance(result["memory"]["peak_rss_kb_unit"], int) and result["memory"]["peak_rss_kb_unit"] > 0
    assert isinstance(result["memory"]["peak_rss_kb_children"], int) and result["memory"]["peak_rss_kb_children"] > 0


# ------------------------------------------------------------------------------------------------ present

@told
def test_a_second_mint_is_present_and_leaves_every_file_under_data_byte_identical_but_data_mints(tmp_path, hashes):
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    assert box.run("mint", "alpha")[1]["status"] == "minted"
    before = box.snapshot()
    rc, result, _ = box.run("mint", "alpha")
    assert (rc, result["status"], result["step"], result["would_add"]) == (0, "present", 2, []), result
    assert "mint" not in result and "read_back" not in result            # step 3 never ran
    assert only_mints_changed(before, box.snapshot()) == []
    assert result["sticks"] == [{"stick": "stick_a_test_stick_for_the_mint_path", "ticks_before": 4}]


@told
def test_a_seal_in_the_cas_without_its_ledger_record_is_named_in_would_add_and_an_expect_present_line_refuses(
        tmp_path, hashes):
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    assert box.run("mint", "alpha")[1]["status"] == "minted"
    h = hashes["alpha"]["three_squared"]                    # sealed last: its record is the chain's tip
    (box.data / "ledger" / ledger_name("mathematics", h)).unlink()
    assert ledger.verify_chain(box.data / "ledger", cas_base=box.data / "cas")["ok"]
    box.listing([a_line("alpha", hashes, expect="present")])
    before = box.snapshot()
    rc, result, _ = box.run("mint", "alpha")
    assert (rc, result["status"], result["step"]) == (3, "refused", 2), result
    assert result["would_add"] == [{"hash": h, "item": "ledger record", "path": f"data/ledger/{ledger_name('mathematics', h)}",
                                    "seal": "three_squared"}]
    assert "expect=present would add 1 item(s): ledger record" in result["reason"]
    assert only_mints_changed(before, box.snapshot()) == []


@told
def test_a_cas_object_present_without_its_receipt_card_reads_present_records_the_card_and_writes_nothing(
        tmp_path, hashes):
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    assert box.run("mint", "alpha")[1]["status"] == "minted"
    h = hashes["alpha"]["two_to_ten"]
    cards = box.data / "receipt_cards.jsonl"
    kept = [line for line in cards.read_text(encoding="utf-8").splitlines(keepends=True)
            if json.loads(line)["id"] != cas.receipt_card_id(h)]
    cards.write_text("".join(kept), encoding="utf-8")
    before = box.snapshot()
    rc, result, _ = box.run("mint", "alpha")
    assert (rc, result["status"], result["would_add"]) == (0, "present", []), result
    assert result["present_without_receipt_card"] == [{"hash": h, "id": cas.receipt_card_id(h), "seal": "two_to_ten"}]
    assert only_mints_changed(before, box.snapshot()) == []


@told
def test_a_seal_whose_domain_holds_an_underscore_mints_finds_its_record_by_the_ledgers_naming_and_is_then_present(
        tmp_path, hashes):
    box = Box(tmp_path, ["condmat"], [a_line("condmat", hashes)])
    h = hashes["condmat"]["von_klitzing"]
    rc, result, _ = box.run("mint", "condmat")
    assert (rc, result["status"]) == (0, "minted"), result
    name = f"condensed-matter-{h[:16]}.json"                # ledger._slugify turns the underscore into a hyphen
    assert ledger_name("condensed_matter", h) == name
    assert json.loads((box.data / "ledger" / name).read_text(encoding="utf-8"))["record_hash"] == h
    assert [i["path"] for i in result["read_back"] if i["item"] == "ledger record"] == [f"data/ledger/{name}"]
    before = box.snapshot()
    rc, result, _ = box.run("mint", "condmat")
    assert (rc, result["status"], result["would_add"]) == (0, "present", []), result
    assert only_mints_changed(before, box.snapshot()) == []


# ------------------------------------------------------------------------------------------------ refusals

def seed_a_bound(data: Path) -> None:
    """The box's sticks already hold BOUND_QUESTION's stick with a bound at 100."""
    sid = "stick_" + tickstick._slug(BOUND_QUESTION)
    events = [{"event": "stick", "id": sid, "question": BOUND_QUESTION, "statement": "", "field": "mathematics",
               "references": [], "at": 1},
              {"event": "tick", "stick": sid, "kind": "bound", "claim": "verified to 100 already", "at": 2,
               "by": "an earlier run", "seal": "c" * 64, "up_to": 100.0, "unit": "n"}]
    (data / "sticks.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")


@pytest.mark.parametrize("name,why", [
    ("badsource", "the rehearsal refused equivalence on stick_a_test_stick_with_a_cited_mark_whose_source_is_too_short"),
    ("badkind", "the rehearsal refused witnes on stick_a_test_stick_with_a_mark_of_an_unknown_kind"),
    ("badbound", "the rehearsal refused bound on stick_a_test_stick_that_already_has_a_bound"),
])
@told
def test_ticks_own_refusals_refuse_at_the_rehearsal_and_leave_data_byte_identical_but_data_mints(
        tmp_path, hashes, name, why):
    box = Box(tmp_path, [name], [a_line(name, hashes)])
    if name == "badbound":
        seed_a_bound(box.data)
    before = box.snapshot()
    rc, result, _ = box.run("mint", name)
    assert (rc, result["status"], result["step"]) == (3, "refused", 2), result
    assert why in result["reason"]
    assert result["rehearsal"]["rc"] == 0                   # sticks.run returned 0: only the read back saw it
    assert only_mints_changed(before, box.snapshot()) == []


def test_a_mark_reads_back_only_with_its_source_up_to_and_unit_as_tick_stores_them(sm):
    """The plan's read back names mint_marks' fields kind, claim, seal, source, up_to and unit: a tick that mint_marks'
    skip predicate selects reads back only when it holds the mark's source (stripped, cut to 300), up_to (a float) and
    unit (cut to 40) as tickstick.tick stores them."""
    seal = "a" * 64
    bound = {"kind": "bound", "claim": "[bound] verified to 10", "seal": "k", "up_to": 10, "unit": "u" * 50}
    assert sm.stored_fields(bound) == {"up_to": 10.0, "unit": "u" * 40}
    kept = {"kind": "bound", "claim": bound["claim"], "seal": seal, "up_to": 10.0, "unit": "u" * 40}
    for tick, reads in ((kept, True), ({**kept, "up_to": 20.0}, False), ({**kept, "unit": "v" * 40}, False)):
        assert sm.mark_reads_back([tick], "bound", bound["claim"], seal, sm.stored_fields(bound)) is reads, tick
    cited = {"kind": "equivalence", "claim": "[cited] a theorem", "source": "  A. Tester, Tests (2026)" + "x" * 400}
    assert sm.stored_fields(cited) == {"source": ("A. Tester, Tests (2026)" + "x" * 400)[:300]}
    stored = {"kind": "equivalence", "claim": cited["claim"], "source": ("A. Tester, Tests (2026)" + "x" * 400)[:300]}
    assert sm.mark_reads_back([stored], "equivalence", cited["claim"], "", sm.stored_fields(cited))
    assert not sm.mark_reads_back([{**stored, "source": "Another Book (2025)"}], "equivalence", cited["claim"], "",
                                  sm.stored_fields(cited))
    note = {"kind": "note", "claim": "[note] a remark"}
    assert sm.stored_fields(note) == {} and sm.mark_reads_back([dict(note)], "note", note["claim"], "", {})


@told
def test_a_kept_mark_that_differs_from_the_entrys_only_in_its_source_refuses_at_the_rehearsal(tmp_path, hashes):
    """mint_marks skips a cited mark whose kind and whole claim are kept, whatever its source, so the entry's mark as
    stated never lands; the read back compares the source too, and the rehearsal refuses: checker-104, run
    2026-11-13-stick-ship line 17's observation (a)."""
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    sid = "stick_a_test_stick_for_the_mint_path"
    cited = ALPHA["sticks"][0]["marks"][2]
    events = [{"event": "stick", "id": sid, "question": SHARED_QUESTION, "statement": "", "field": "mathematics",
               "references": [], "at": 1},
              {"event": "tick", "stick": sid, "kind": "equivalence", "claim": cited["claim"], "at": 2,
               "by": "an earlier run", "source": "Another Book of Tests (2025)"}]
    (box.data / "sticks.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    before = box.snapshot()
    rc, result, _ = box.run("mint", "alpha")
    assert (rc, result["status"], result["step"]) == (3, "refused", 2), result
    assert f"the rehearsal refused equivalence on {sid}: '[alpha] a cited test mark'" in result["reason"]
    assert [m for m in result["rehearsal"]["marks"] if not m["kept"]] == [
        {"claim": cited["claim"], "kept": False, "kind": "equivalence", "seal": None, "stick": sid}]
    assert only_mints_changed(before, box.snapshot()) == []


def a_broken_chain(data: Path) -> None:
    (data / "ledger" / "mathematics-0000000000000000.json").write_text(json.dumps(
        {"precedent_id": "ledger://mathematics/0000000000000000", "axis": "mathematics", "summary": "tampered",
         "sealed_at": 1.0, "prev_hash": "GENESIS", "content_hash": "0" * 64}), encoding="utf-8")


@pytest.mark.parametrize("case,step,why", [
    ("a wrong listed hash", 2, "listed and not minted ['two_to_ten="),
    ("a seal that does not hold", 2, "the rehearsal's run returned 1"),
    ("an entry file whose hash differs", 1, "data/sticks/alpha.json hashes to "),
    ("a handler entry", 1, "handled is a handler entry"),
    ("an unlisted name", 1, "beta is not listed in tools/stick_mints.txt"),
    ("a broken chain", 1, "ledger.verify_chain is not ok before the mint"),
])
@told
def test_each_wrong_input_is_refused_and_leaves_data_byte_identical_but_data_mints(tmp_path, hashes, case, step, why):
    name = {"a seal that does not hold": "broken", "a handler entry": "handled", "an unlisted name": "beta"}.get(
        case, "alpha")
    lines = [a_line("alpha", hashes, change="two_to_ten" if case == "a wrong listed hash" else None)]
    if name in ("broken", "handled"):
        lines.append(a_line(name, hashes))
    box = Box(tmp_path, ["alpha", name] if name != "alpha" else ["alpha"], lines)
    if case == "an entry file whose hash differs":
        (box.data / "sticks" / "alpha.json").write_bytes(entry_bytes({**ALPHA, "doc": "alpha: edited after listing"}))
    if case == "a broken chain":
        a_broken_chain(box.data)
    before = box.snapshot()
    rc, result, _ = box.run("mint", name)
    assert (rc, result["status"], result["step"]) == (3, "refused", step), result
    assert why in result["reason"], result["reason"]
    assert only_mints_changed(before, box.snapshot()) == []


@told
def test_the_lock_refuses_a_second_mint_and_its_refusal_writes_only_its_own_result(tmp_path, hashes, sm):
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    (box.data / "mints").mkdir()
    held = sm.take_lock(box.data / "mints" / ".lock")       # held as a running mint holds it
    assert held is not None
    lock = ("data/mints/.lock",)                            # on Windows a held lock cannot be read, even when empty
    try:
        before = box.snapshot(lock)
        rc, result, run_id = box.run("mint", "alpha")
        assert (rc, result["status"], result["step"]) == (3, "refused", 0), result
        assert result["reason"] == "another mint holds the lock, data/mints/.lock"
        assert [p for p in box.snapshot(lock) if p not in before] == [f"box/data/mints/.results/{run_id}.json"]
        assert only_mints_changed(before, box.snapshot(lock)) == []
        assert (box.data / "mints" / ".lock").is_file()
    finally:
        os.close(held)
    assert box.run("mint", "alpha")[1]["status"] == "minted"                # the lock released, a mint runs


@pytest.mark.parametrize("setting,why", [
    ("env CONCORDANCE_CAS_DIR=/elsewhere/another/cas", "<root>/.env names a keeping location: CONCORDANCE_CAS_DIR"),
    ("env export CONCORDANCE_DATA_DIR=/elsewhere/another/data", "<root>/.env names a keeping location: CONCORDANCE_DATA_DIR"),
    ("env CONCORDANCE_PUBLIC_BASE=https://example.invalid", "names a keeping location: CONCORDANCE_PUBLIC_BASE"),
    ("engine another", "does not name CONCORDANCE_DATA_DIR=<root>/data, and only that (1 CONCORDANCE_DATA_DIR"),
    ("engine none", "does not name CONCORDANCE_DATA_DIR=<root>/data, and only that (0 CONCORDANCE_DATA_DIR"),
    ("engine twice", "does not name CONCORDANCE_DATA_DIR=<root>/data, and only that (2 CONCORDANCE_DATA_DIR"),
])
@told
def test_a_keeping_named_elsewhere_makes_the_unit_refuse(tmp_path, hashes, setting, why):
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    kind, value = setting.split(" ", 1)
    if kind == "env":
        (box.root / ".env").write_text(f"CONCORDANCE_STRONGS_DIR=/x\n# a comment\n{value}\n", encoding="utf-8")
    else:
        mine = f'"CONCORDANCE_DATA_DIR={box.data.as_posix()}"'
        other = f'"CONCORDANCE_DATA_DIR={(tmp_path / "another" / "data").as_posix()}"'
        stand_in_systemctl(box.engine, {"another": other, "none": "WEB_FIND_DISABLED=1",
                                        "twice": f"{mine} {other}"}[value])
    before = box.snapshot()
    rc, result, _ = box.run("mint", "alpha")
    assert (rc, result["status"], result["step"]) == (3, "refused", 1), result
    assert why in result["reason"], result["reason"]
    assert "another" not in result["reason"] and "/elsewhere" not in result["reason"]   # names only, never values
    assert only_mints_changed(before, box.snapshot()) == []
    log = box.engine / "systemctl.log"
    assert (log.read_text().split() if log.exists() else []) == (["show", "nh-engine", "--property=Environment"]
                                                                 if kind == "engine" else [])


def test_the_env_file_is_read_by_names_only_and_a_name_that_is_no_keeping_location_is_not_refused(sm, tmp_path):
    env = tmp_path / ".env"
    env.write_text("# c\nCONCORDANCE_STRONGS_DIR=/a\nexport STIGMERGY=1\n  CONCORDANCE_QUORUM = 2\nnoequals\n\n",
                   encoding="utf-8")
    assert sm.env_file_names(env) == ["CONCORDANCE_STRONGS_DIR", "STIGMERGY", "CONCORDANCE_QUORUM"]
    assert not set(sm.env_file_names(env)) & set(sm.KEEPING_NAMES)
    assert sm.KEEPING_NAMES == ("CONCORDANCE_DATA_DIR", "CONCORDANCE_CAS_DIR", "CONCORDANCE_LEDGER_DIR",
                                "CONCORDANCE_SEAL_INDEX", "CONCORDANCE_PUBLIC_BASE")


@pytest.mark.parametrize("reading", ["below", "unreadable"])
@told
def test_the_memory_floor_refuses_with_stand_in_readings_and_records_them(tmp_path, hashes, reading):
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    need = (512 + 256) * 1024
    if reading == "below":
        box.memory(need - 1)
    else:
        box.meminfo.write_bytes(b"MemTotal:       16000000 kB\n")
    before = box.snapshot()
    rc, result, _ = box.run("mint", "alpha")
    assert (rc, result["status"], result["step"]) == (3, "refused", 1), result
    assert result["memory"]["mem_needed_kb"] == need
    if reading == "below":
        assert result["memory"]["mem_available_kb"] == need - 1 and "below the floor of 786432 kB" in result["reason"]
    else:
        assert result["memory"]["mem_available_kb"] is None and result["reason"] == "available memory could not be read"
    assert only_mints_changed(before, box.snapshot()) == []


# ------------------------------------------------------------------------------------------------ in process

def in_process(monkeypatch, sm, box: Box) -> None:
    """The unit's environment for a run of its mint in this process; never its process limits, which only its
    command-line entry sets. The cold path's caches start empty and are restored after."""
    for k in [k for k in os.environ if k.upper().startswith("CONCORDANCE_")]:
        monkeypatch.delenv(k)
    for k, v in sm.expected_environment(box.root).items():
        monkeypatch.setenv(k, v)
    from concordance import science_cards
    monkeypatch.setattr(cas, "_COLD_CARDS_WRITTEN", set())
    monkeypatch.setattr(cas, "_COLD_SPINE_WRITTEN", False)
    monkeypatch.setattr(science_cards, "_MINTED", None)


@told
def test_with_the_ledger_append_failing_the_mint_reads_failed_naming_each_record_and_a_later_mint_completes_it(
        tmp_path, hashes, sm, monkeypatch):
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    in_process(monkeypatch, sm, box)
    real = ledger.seal_to_ledger

    def refused(*args, **kwargs):
        raise OSError("the ledger append is made to fail")
    monkeypatch.setattr(ledger, "seal_to_ledger", refused)
    run_id = a_run_id()
    rc = sm.run_unit("mint", box.root, run_id, "alpha", sm.Options(str(box.meminfo), str(box.systemctl),
                                                                    str(box.scratch)))
    result = box.result(run_id)
    assert (rc, result["status"], result["step"]) == (1, "failed", 4), result
    for key, h in hashes["alpha"].items():
        assert f"the ledger record of {key} (data/ledger/{ledger_name('mathematics', h)})" in result["reason"]
        assert cas.verify(h, base_dir=box.data / "cas") == (True, "ok")
    assert sorted(p.name for p in (box.data / "ledger").glob("*.json")) == []
    assert result["confinement"] == {"address_space_cap_mb": None, "ionice": None, "nice": None, "oom_score_adj": None}
    monkeypatch.setattr(ledger, "seal_to_ledger", real)
    rc, later, _ = box.run("mint", "alpha")                 # the append restored: a later mint completes it
    assert (rc, later["status"]) == (0, "minted"), later
    assert sorted(i["item"] for i in later["would_add"]) == ["ledger record", "ledger record"]
    for h in hashes["alpha"].values():
        assert json.loads((box.data / "ledger" / ledger_name("mathematics", h)).read_text(encoding="utf-8"))[
            "record_hash"] == h
    assert ledger.verify_chain(box.data / "ledger", cas_base=box.data / "cas")["ok"]


@told
def test_a_rehearsal_still_running_at_the_start_deadline_is_ended_and_the_mint_refused(tmp_path, hashes, sm,
                                                                                         monkeypatch):
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    in_process(monkeypatch, sm, box)
    before = box.snapshot()
    run_id = a_run_id()
    rc = sm.run_unit("mint", box.root, run_id, "alpha", sm.Options(str(box.meminfo), str(box.systemctl),
                                                                    str(box.scratch)),
                     started=time.monotonic() - sm.START_DEADLINE_S - 1)
    result = box.result(run_id)
    assert (rc, result["status"], result["step"]) == (3, "refused", 2), result
    assert "step 3 never begins later than that" in result["reason"]
    assert only_mints_changed(before, box.snapshot()) == []


@told
def test_the_start_deadline_check_before_step_3_refuses_a_mint_whose_rehearsal_ended_in_time(tmp_path, hashes, sm,
                                                                                               monkeypatch):
    """The check itself, not the rehearsal's own timeout: the rehearsal ends in time, then the unit's clock reads past
    the deadline before step 3 (checker-104, run 2026-11-13-stick-ship line 17's observation (b)). Only the unit's own
    clock is moved, after its rehearsal returns."""
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    in_process(monkeypatch, sm, box)
    late = {"by": 0.0}

    class Clock:
        def monotonic(self):
            return time.monotonic() + late["by"]

        def __getattr__(self, name):
            return getattr(time, name)
    real = sm.rehearse

    def rehearsed_then_late(*args, **kwargs):
        report = real(*args, **kwargs)
        late["by"] = sm.START_DEADLINE_S + 1
        return report
    monkeypatch.setattr(sm, "time", Clock())
    monkeypatch.setattr(sm, "rehearse", rehearsed_then_late)
    before = box.snapshot()
    run_id = a_run_id()
    rc = sm.run_unit("mint", box.root, run_id, "alpha", sm.Options(str(box.meminfo), str(box.systemctl),
                                                                    str(box.scratch)))
    result = box.result(run_id)
    assert (rc, result["status"], result["step"]) == (3, "refused", 2), result
    assert result["reason"] == ("more than 600 seconds have passed since the unit started; step 3 never begins later "
                                "than that")
    assert result["rehearsal"]["rc"] == 0 and result["rehearsal"]["timed_out"] is False and result["would_add"]
    assert "mint" not in result
    assert only_mints_changed(before, box.snapshot()) == []


@told
def test_a_mark_that_lands_on_the_stick_during_the_mint_is_recorded_apart_and_never_retracted(tmp_path, hashes, sm,
                                                                                                monkeypatch):
    """checker-104's race (run 2026-11-13-stick-ship, lines 16 and 17), with the real unit: a visitor's sealed witness,
    a HOLDS seal no catalog entry states, the kind the public POST /tick accepts, lands on alpha's stick during step 3.
    The mint reads failed, the visitor's tick is recorded apart, never as this path's mark, and the retract that
    follows withdraws alpha's two sealed marks alone."""
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes)])
    in_process(monkeypatch, sm, box)
    from concordance import sticks
    real = sticks.run
    sid = "stick_a_test_stick_for_the_mint_path"
    visitor: dict = {}

    def the_mint_and_a_visitor(entry):
        rc = real(entry)
        visitor["seal"] = sticks.seal(numeric("six_times_seven", "6*7", 42))
        visitor["tick"] = tickstick.tick(sid, "witness", "[a visitor] 6*7 = 42, sealed at the verify door",
                                         seal=visitor["seal"], by="a visitor")
        return rc
    monkeypatch.setattr(sticks, "run", the_mint_and_a_visitor)
    run_id = a_run_id()
    rc = sm.run_unit("mint", box.root, run_id, "alpha", sm.Options(str(box.meminfo), str(box.systemctl),
                                                                    str(box.scratch)))
    result = box.result(run_id)
    assert visitor["tick"]["ok"] and visitor["seal"] not in hashes["alpha"].values()
    assert (rc, result["status"], result["step"]) == (1, "failed", 4), result
    assert "not the rehearsal's exactly (1 arrived otherwise)" in result["reason"]
    assert result["marks_added"] == result["rehearsal"]["appended"]
    assert [(e["kind"], e["seal"], e["by"]) for e in result["arrived_otherwise"]] == [
        ("witness", visitor["seal"], "a visitor")]
    monkeypatch.setattr(sticks, "run", real)
    rc, retracted, _ = box.run("retract", "alpha")
    assert (rc, retracted["status"]) == (0, "retracted"), retracted
    assert sorted(w["seal"] for w in retracted["withdrawn"]) == sorted(hashes["alpha"].values())
    assert sorted(c["seal"] for c in retracted["recorded_as_new"]) == sorted(hashes["alpha"].values())
    ticks = tickstick.fold(box.data)[sid]["ticks"]
    assert [t["seal"] for t in ticks if t.get("seal")] == [visitor["seal"]]               # the visitor's still reads


# ------------------------------------------------------------------------------------------------ retract

@pytest.mark.parametrize("expect", ["present", "refused"])
@told
def test_retract_refuses_a_canary_line(tmp_path, hashes, expect):
    box = Box(tmp_path, ["alpha"], [a_line("alpha", hashes, expect=expect)])
    before = box.snapshot()
    rc, result, _ = box.run("retract", "alpha")
    assert (rc, result["status"], result["step"]) == (3, "refused", 1), result
    assert f"alpha is a canary (expect={expect}): a canary is never retracted" == result["reason"]
    assert only_mints_changed(before, box.snapshot()) == []


@told
def test_retract_withdraws_only_the_marks_a_mint_recorded_as_new_and_appends_nothing_a_second_time(tmp_path, hashes):
    box = Box(tmp_path, ["alpha", "beta"], [a_line("alpha", hashes), a_line("beta", hashes)])
    assert box.run("mint", "beta")[1]["status"] == "minted"              # a mark on the same stick, not alpha's
    minted = box.run("mint", "alpha")[1]
    assert minted["status"] == "minted"
    # the keeping holds the receipt spine card since beta's mint, so alpha's names none, yet reads it back; the cold
    # path writes it again before the first receipt card of each process, and the result says so
    assert [i for i in minted["would_add"] if i["item"] == "receipt spine card"] == []
    assert [i["ok"] for i in minted["read_back"] if i["item"] == "receipt spine card"] == [True]
    assert minted["receipt_spine_cards_written"] == 1 and minted["arrived_otherwise"] == []
    sid = "stick_a_test_stick_for_the_mint_path"
    alpha = hashes["alpha"]
    held = {p: v for p, v in box.snapshot().items() if p.startswith(("box/data/cas/", "box/data/ledger/"))}
    cards = (box.data / "receipt_cards.jsonl").read_bytes()
    log = (box.data / "sticks.jsonl").read_bytes()
    rc, result, _ = box.run("retract", "alpha")
    assert (rc, result["status"]) == (0, "retracted"), result
    assert result["withdrawn"] == [{"seal": alpha["two_to_ten"], "stick": sid}, {"seal": alpha["three_squared"],
                                                                                 "stick": sid}]
    grown = (box.data / "sticks.jsonl").read_bytes()
    assert grown.startswith(log)
    events = [json.loads(line) for line in grown[len(log):].decode("utf-8").splitlines()]
    assert [(e["event"], e["stick"], e["seal"]) for e in events] == [("retract", sid, alpha["two_to_ten"]),
                                                                     ("retract", sid, alpha["three_squared"])]
    ticks = tickstick.fold(box.data)[sid]["ticks"]
    marks = ALPHA["sticks"][0]["marks"]
    assert not has_mark(ticks, marks[0], alpha["two_to_ten"]) and not has_mark(ticks, marks[1], alpha["three_squared"])
    assert has_mark(ticks, marks[2], "") and has_mark(ticks, marks[3], "")                  # a cited mark, a note
    assert has_mark(ticks, BETA["sticks"][0]["marks"][0], hashes["beta"]["five_cubed"])     # a mark it did not mint
    assert {p: v for p, v in box.snapshot().items() if p.startswith(("box/data/cas/", "box/data/ledger/"))} == held
    assert (box.data / "receipt_cards.jsonl").read_bytes() == cards
    assert len(result["unchanged"]) == 4 and "receipt card" in result["stays_served"]
    before = box.snapshot()
    rc, again, _ = box.run("retract", "alpha")
    assert (rc, again["status"], again["withdrawn"]) == (0, "absent", []), again
    assert len(again["already_gone"]) == 2
    assert only_mints_changed(before, box.snapshot()) == []                                 # appends nothing


@told
def test_retract_refuses_when_another_entry_states_the_same_stick_and_seal(tmp_path, hashes):
    assert hashes["gamma"]["two_to_ten_again"] == hashes["alpha"]["two_to_ten"]
    box = Box(tmp_path, ["alpha", "gamma"], [a_line("alpha", hashes)])
    assert box.run("mint", "alpha")[1]["status"] == "minted"
    before = box.snapshot()
    rc, result, _ = box.run("retract", "alpha")
    assert (rc, result["status"]) == (3, "refused"), result
    assert "another catalog entry states a mark with the same stick and seal (gamma.two_to_ten_again)" in \
        result["reason"]
    assert only_mints_changed(before, box.snapshot()) == []
    assert list(box.scratch.iterdir()) == []


# ------------------------------------------------------------------------------------------------ the unit itself

STDLIB = set(getattr(sys, "stdlib_module_names", ()))


def test_the_units_top_level_imports_are_the_standard_librarys_and_it_never_restarts_an_engine():
    """Its entry-check runs streamed to the box's python, so nothing but the standard library is imported until a mint
    or a retract runs; and it reads systemctl only with `show`."""
    assert STDLIB, "this Python names no standard library modules"
    tree = ast.parse(UNIT.read_text(encoding="utf-8"))
    top = []
    for node in tree.body:
        for inner in ([node] + (node.body + [h for t in node.handlers for h in t.body] if isinstance(node, ast.Try)
                                else [])):
            if isinstance(inner, ast.Import):
                top += [a.name.split(".")[0] for a in inner.names]
            elif isinstance(inner, ast.ImportFrom):
                top.append("." * inner.level + (inner.module or "").split(".")[0])
    assert top and set(top) <= STDLIB, sorted(set(top) - STDLIB)
    code = UNIT.read_text(encoding="utf-8")
    assert not re.search(r"""["']restart["']""", code) and '"show", ENGINE_UNIT' in code


@pytest.mark.parametrize("on_the_box", ["matches", "differs", "absent"])
def test_entry_check_streamed_to_python_reads_the_boxs_entry_hash(tmp_path, on_the_box):
    data = tmp_path / "box" / "data" / "sticks"
    data.mkdir(parents=True)
    body = entry_bytes(ALPHA)
    if on_the_box != "absent":
        (data / "alpha.json").write_bytes(body.replace(b"\n", b"\r\n") if on_the_box == "matches" else body + b" ")
    sent = UNIT.read_bytes().replace(b"\r", b"")
    done = subprocess.run([sys.executable, "-I", "-B", "-", "entry-check", "--root", str(tmp_path / "box"), "alpha",
                           sha(body)], input=sent, capture_output=True, timeout=GENEROUS)
    said = done.stdout.decode().strip()
    assert done.returncode == (0 if on_the_box == "matches" else 1), (said, done.stderr)
    assert said.startswith({"matches": "ENTRY MATCHES", "differs": "ENTRY DIFFERS", "absent": "ENTRY ABSENT"}[on_the_box])
    assert str(tmp_path) not in said and list(tmp_path.rglob("*.pyc")) == []
