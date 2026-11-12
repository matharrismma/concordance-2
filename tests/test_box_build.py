"""tools/box_build.py, the box build unit (run 2026-11-11-box-build), run here as the real file against a temporary root
that stands in for the box, with every box path passed in: the root, the scratch base and stand-in readings of memory
and disk. Nothing here reaches the box or calls ssh. Also pinned: the listing, the canary and its listed hashes on this
platform, the pins src/concordance/build_pins.json holds, and the one reader of built data, src/concordance/builds.py.

Where a promise is Linux's own (the address-space cap, oom_score_adj, nice and ionice), the test runs on Linux, in CI,
and says that it skips anywhere else. No test waits on a clock that load can run out: a wait is for a state, with a
generous bound only a broken run reaches (checker-101, run 2026-11-11-box-build line 24). Every test that builds is
`@told`: a failure carries each unit run's output, its results, and the stand-in box's builds and scratch base."""
from __future__ import annotations

import ast
import functools
import hashlib
import importlib.util
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "tools" / "box_build.py"
LISTING = ROOT / "tools" / "box_builds.txt"
CANARY = ROOT / "tools" / "build_canary.py"
PINS = ROOT / "src" / "concordance" / "build_pins.json"
PROBE = ROOT / "tests" / "fixtures" / "box_build_probe.py"
LINUX = sys.platform.startswith("linux")
LINUX_ONLY = ("Linux's own (RLIMIT_AS, /proc/self/oom_score_adj, nice, ionice, ru_maxrss): proven by CI on Linux, "
              f"skipped here on {sys.platform}")
GIB = 1024 ** 3
PLENTY_KB = 8 * 1024 * 1024             # 8 GB available
PLENTY_DISK = 100 * GIB
GENEROUS = 600                          # seconds: a bound only a broken run reaches, never a loaded laptop


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bb():
    return _load("box_build_under_test", UNIT)


@pytest.fixture(scope="module")
def probe():
    return _load("box_build_probe", PROBE)


def a_run_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + secrets.token_hex(6)


def hash_of(bb, tmp_path: Path, files: dict) -> str:
    """The unit's own content hash of an output holding exactly `files` ({path: bytes})."""
    out = tmp_path / ("expected-" + secrets.token_hex(4))
    for rel, body in files.items():
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_bytes(body)
    return bb.content_hash(out)


def files_under(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()} if folder.exists() else {}


class Box:
    """A temporary root standing in for the box: its tools/ with the probe and a listing, its data/, a scratch base
    outside it, and stand-in readings."""
    current = None                      # the box the running test made, for `told`

    def __init__(self, tmp_path: Path, bb, probe, inputs: dict):
        Box.current = self
        self.runs: list = []
        self.tmp, self.bb, self.probe = tmp_path, bb, probe
        self.root = tmp_path / "box"
        self.scratch = tmp_path / "scratch"
        self.builds = self.root / "data" / "builds"
        (self.root / "tools").mkdir(parents=True)
        (self.root / "data").mkdir()
        self.scratch.mkdir()
        (self.root / "tools" / "probe.py").write_bytes(PROBE.read_bytes())
        self.inputs = inputs
        self.fixed = hash_of(bb, tmp_path, {"fixed.txt": probe.FIXED})
        self.report = hash_of(bb, tmp_path, {"report.json": probe.expected_report(inputs)})
        ins = "".join(f" in={p}" for p in sorted(inputs))
        entries = {
            "ok": f'{self.fixed} 128 "fixed"',
            "okin": f'{self.fixed} 128{ins} "fixed"',
            "wrong": f'{"0" * 64} 128 "fixed"',
            "fail": f'{self.fixed} 128 "fail"',
            "empty": f'{self.fixed} 128 "empty"',
            "hog": f'{self.fixed} 128 "hog"',
            "sleep": f'{self.fixed} 128 "sleep"',
            "wait": f'{self.fixed} 128{ins} "wait"',
            "probe": f'{self.report} 128{ins} "probe"',
        }
        lines = []
        for name, rest in entries.items():
            lines += [f"# {name}: a test build, from tools/probe.py", f"{name} tools/probe.py {rest}"]
        (self.root / "tools" / "box_builds.txt").write_bytes(("\n".join(lines) + "\n").encode())
        self.meminfo = tmp_path / "meminfo"
        self.memory(PLENTY_KB)
        self.go = tmp_path / "go"

    def memory(self, kb: int) -> None:
        self.meminfo.write_bytes(f"MemTotal:       16000000 kB\nMemFree:         1000 kB\nMemAvailable:   {kb} kB\n".encode())

    def stage(self, run_id: str, files: dict) -> Path:
        staging = self.builds / ".inputs" / run_id
        for rel, body in files.items():
            (staging / rel).parent.mkdir(parents=True, exist_ok=True)
            (staging / rel).write_bytes(body)
        return staging

    def env(self) -> dict:
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("CONCORDANCE_")}
        env.update(CONCORDANCE_DATA_DIR=str(self.root / "data"), CONCORDANCE_LEAK_PROBE="the unit's own",
                   BOXTEST_BOX_ROOT=str(self.root), BOXTEST_GO=str(self.go))
        return env

    def command(self, name: str, run_id: str, kb=None, disk=PLENTY_DISK, timeout=None) -> list:
        cmd = [sys.executable, str(UNIT), "build", "--root", str(self.root), "--run-id", run_id,
               "--meminfo", str(self.meminfo), "--disk-free-bytes", str(disk), "--scratch-base", str(self.scratch)]
        if timeout:
            cmd += ["--tool-timeout", str(timeout)]
        return cmd + [name]

    def build(self, name: str, run_id=None, stage=None, disk=PLENTY_DISK, timeout=None):
        run_id = run_id or a_run_id()
        if stage is not None:
            self.stage(run_id, stage)
        cmd = self.command(name, run_id, disk=disk, timeout=timeout)
        done = subprocess.run(cmd, env=self.env(), capture_output=True, text=True, timeout=GENEROUS)
        self.runs.append((cmd, done.returncode, done.stdout, done.stderr))
        return done.returncode, self.result(run_id), run_id

    def story(self) -> str:
        """Everything a failure needs to be read."""
        parts = [f"--- the unit ran {' '.join(cmd[2:])}\nexit {rc}\n{out}\n{err}" for cmd, rc, out, err in self.runs]
        if self.builds.exists():
            parts.append("--- data/builds\n" + "\n".join(p.relative_to(self.root).as_posix()
                                                          for p in sorted(self.builds.rglob("*"))))
            for result in sorted((self.builds / ".results").glob("*.json")):
                parts.append(f"--- {result.name}\n{result.read_text(encoding='utf-8', errors='replace')}")
        parts.append("--- the scratch base\n" + "\n".join(p.relative_to(self.scratch).as_posix()
                                                          for p in sorted(self.scratch.rglob("*"))))
        return "\n".join(parts)

    def result(self, run_id: str) -> dict:
        return json.loads((self.builds / ".results" / f"{run_id}.json").read_text(encoding="utf-8"))

    def leftovers(self) -> list:
        """Anything a build left in its temporary or staging directories, or in the scratch base."""
        return [p for d in (self.builds / ".tmp", self.builds / ".inputs", self.scratch) if d.exists()
                for p in d.iterdir()]

    def snapshot(self) -> dict:
        return {**{f"box/{k}": v for k, v in files_under(self.root).items()},
                **{f"scratch/{k}": v for k, v in files_under(self.scratch).items()}}


INPUTS = {"src/concordance/table.json": b'{"author": "Augustine"}\n', "site/page.html": b"<p>a page</p>\n",
          "tools/notes.txt": b"notes\n"}


@pytest.fixture
def box(tmp_path, bb, probe) -> Box:
    return Box(tmp_path, bb, probe, INPUTS)


def told(test):
    """A test that builds: if it fails, the failure carries its box's story."""
    @functools.wraps(test)
    def run(*args, **kwargs):
        Box.current = kwargs["box"] if isinstance(kwargs.get("box"), Box) else None
        try:
            return test(*args, **kwargs)
        except Exception as e:
            if Box.current is None:
                raise
            raise AssertionError(f"{type(e).__name__}: {e}\n\n{Box.current.story()}") from e
    return run


# ------------------------------------------------------------------------------------------------ the hash

def test_the_content_hash_is_the_sorted_manifest_of_forward_slash_paths(bb, tmp_path):
    files = {"b/c.txt": b"c\n", "a.txt": b"a\n", "b/a/z.bin": bytes(range(256))}
    out = tmp_path / "out"
    for rel in reversed(list(files)):
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_bytes(files[rel])
    manifest = "".join(f"{hashlib.sha256(files[rel]).hexdigest()}  {rel}\n" for rel in sorted(files))
    want = hashlib.sha256(manifest.encode()).hexdigest()
    assert bb.content_hash(out) == want
    shown = subprocess.run([sys.executable, str(UNIT), "hash", str(out)], capture_output=True, text=True,
                           timeout=GENEROUS)
    assert (shown.returncode, shown.stdout.strip()) == (0, want)


def test_the_hash_refuses_an_empty_output_an_empty_directory_and_a_symlink(bb, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(bb.BuildError, match="empty"):
        bb.content_hash(empty)
    hollow = tmp_path / "hollow"
    (hollow / "nothing").mkdir(parents=True)
    (hollow / "a.txt").write_bytes(b"a")
    with pytest.raises(bb.BuildError, match="empty directory"):
        bb.content_hash(hollow)
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "a.txt").write_bytes(b"a")
    try:
        os.symlink(linked / "a.txt", linked / "b.txt")
    except (OSError, NotImplementedError):
        return                          # this platform makes no symlink for this user (Windows without the right)
    with pytest.raises(bb.BuildError, match="symlink"):
        bb.content_hash(linked)


# ------------------------------------------------------------------------------------------------ the listing

def test_the_listing_holds_the_canary_and_canary_fail_each_after_a_comment(bb):
    text = LISTING.read_text(encoding="utf-8")
    entries = bb.parse_listing(text)
    assert sorted(entries) == ["canary", "canary-fail"]
    assert {e.tool for e in entries.values()} == {"tools/build_canary.py"}
    assert (entries["canary"].args, entries["canary-fail"].args) == (("ok",), ("fail",))
    assert all(e.inputs == () and 1 <= e.cap_mb <= 1024 for e in entries.values())
    lines = text.splitlines()
    for e in entries.values():
        before = lines[e.line - 2]
        assert before.startswith(f"# {e.name}:") and len(before) > len(e.name) + 10, before


def test_the_canary_writes_bytes_whose_hash_is_listed(bb, tmp_path):
    """Observation (2), line 12: run on the Windows gate and in Linux CI, the canary's output hashes as listed."""
    entries = bb.parse_listing(LISTING.read_text(encoding="utf-8"))
    for name, rc in (("canary", 0), ("canary-fail", 1)):
        inputs, out = tmp_path / name / "inputs", tmp_path / name / "out"
        inputs.mkdir(parents=True)
        out.mkdir()
        ran = subprocess.run([sys.executable, "-I", "-S", str(CANARY), str(inputs), str(out), *entries[name].args],
                             capture_output=True, timeout=GENEROUS)
        assert ran.returncode == rc, ran.stderr
        assert bb.content_hash(out) == entries[name].hash, name
    assert (tmp_path / "canary" / "out" / "canary.txt").stat().st_size == 74


STDLIB = set(getattr(sys, "stdlib_module_names", ()))


def imports_outside_the_stdlib(source: str) -> list:
    """Every import a build tool may not make: anything outside the standard library, the concordance package, a
    relative import, or an import made at run time."""
    bad = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            bad += [a.name for a in node.names if a.name.split(".")[0] not in STDLIB or a.name.startswith("importlib")]
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] not in STDLIB or (node.module or "").startswith("importlib"):
                bad.append("." * node.level + (node.module or ""))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "__import__":
            bad.append("__import__")
    return bad


@pytest.mark.parametrize("planted", ["import concordance", "from concordance import corpus", "from . import sibling",
                                     "import numpy", "import importlib", "__import__('concordance')",
                                     "import os, concordance.corpus"])
def test_the_import_check_refuses_anything_but_the_standard_library(planted):
    assert STDLIB, "this Python names no standard library modules"
    assert imports_outside_the_stdlib(planted) != []


def test_every_listed_tool_imports_only_the_standard_library(bb):
    for e in bb.parse_listing(LISTING.read_text(encoding="utf-8")).values():
        assert imports_outside_the_stdlib((ROOT / e.tool).read_text(encoding="utf-8")) == [], e.tool
    assert imports_outside_the_stdlib(UNIT.read_text(encoding="utf-8")) == []


def test_every_listed_input_is_a_file_here_outside_data(bb):
    for e in bb.parse_listing(LISTING.read_text(encoding="utf-8")).values():
        for p in e.inputs:
            assert (ROOT / p).is_file() and not p.startswith("data/"), p


GOOD = f'canary tools/build_canary.py {"a" * 64} 128'


@pytest.mark.parametrize("line,why", [
    (GOOD + " in=data/x.json", "under data/"),
    (GOOD + " in=tools/../data/x.json", "under data/"),
    (GOOD + " in=Data/x.json", "under data/"),
    (GOOD + " in=/etc/passwd", "absolute"),
    (GOOD + " in=../x.json", "'..'"),
    (GOOD + " in=src/./x.json", "not a plain"),
    (GOOD + " in=src//x.json", "not a plain"),
    (GOOD + " in=src/x.json in=src/x.json", "twice"),
    (f'canary tools/build_canary.py {"a" * 64} 1025', "1 to 1024"),
    (f'canary tools/build_canary.py {"a" * 64} 0', "1 to 1024"),
    (f'canary src/concordance/x.py {"a" * 64} 128', "not an entry"),
    (f'canary tools/build_canary.py {"a" * 63} 128', "not an entry"),
    (GOOD + " ok", "not an entry"),
    (GOOD + ' "two words"', "not an entry"),
    (GOOD.replace(" ", "\t"), "not an entry"),
])
def test_the_listing_refuses_what_the_path_will_not_run(bb, line, why):
    with pytest.raises(bb.ListingError, match=re.escape(why)):
        bb.parse_listing(f"# canary: a test line\n{line}\n")


def test_the_listing_refuses_an_entry_without_its_comment_and_a_name_twice(bb):
    with pytest.raises(bb.ListingError, match="no comment line"):
        bb.parse_listing(GOOD + "\n")
    with pytest.raises(bb.ListingError, match="no comment line"):
        bb.parse_listing(f"# canary: a test line\n\n{GOOD}\n")
    with pytest.raises(bb.ListingError, match="listed twice"):
        bb.parse_listing(f"# canary: one\n{GOOD}\n# canary: two\n{GOOD}\n")
    assert list(bb.parse_listing(f"# canary: a test line\r\n{GOOD}\r\n")) == ["canary"]     # a Windows checkout


# ------------------------------------------------------------------------------------------------ serving

def test_the_pins_equal_the_listings_hashes(bb):
    listed = {e.name: e.hash for e in bb.parse_listing(LISTING.read_text(encoding="utf-8")).values()}
    text = PINS.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert json.loads(text) == listed
    assert text == json.dumps(listed, indent=2, sort_keys=True) + "\n"      # the form tools/build_ship.sh reads


@pytest.fixture
def builds_module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "src"))
    from concordance import builds
    return builds


def test_the_reader_reads_only_the_pinned_hash(builds_module, tmp_path, monkeypatch):
    pin = builds_module.pinned_hash("canary")
    assert pin == json.loads(PINS.read_text(encoding="utf-8"))["canary"]
    data = tmp_path / "data"
    other = data / "builds" / "canary" / ("b" * 64)
    other.mkdir(parents=True)
    (other / "canary.txt").write_bytes(b"another hash's data\n")
    assert builds_module.built_dir("canary", data_dir=data) is None          # not built: a miss, never another hash
    (data / "builds" / "canary" / pin).mkdir()
    assert builds_module.built_dir("canary", data_dir=data) == data / "builds" / "canary" / pin
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(data))
    assert builds_module.built_dir("canary") == data / "builds" / "canary" / pin
    assert builds_module.built_dir("no-such-build") is None
    assert builds_module.built_dir("../canary") is None


def test_no_runtime_store_uses_data_builds():
    named = [p.relative_to(ROOT).as_posix() for p in (ROOT / "src").rglob("*.py")
             if re.search(r"""["']builds["']|data/builds""", p.read_text(encoding="utf-8", errors="replace"))]
    assert named == ["src/concordance/builds.py"]


# ------------------------------------------------------------------------------------------------ the unit

@told
def test_a_listed_tool_whose_output_matches_lands_in_its_hash_directory(box):
    rc, result, run_id = box.build("ok")
    assert (rc, result["status"], result["run_id"]) == (0, "built", run_id), result
    assert result["dir"] == f"data/builds/ok/{box.fixed}" and result["output_hash"] == box.fixed
    assert (box.builds / "ok" / box.fixed / "fixed.txt").read_bytes() == box.probe.FIXED
    assert box.leftovers() == []
    assert result["readings"]["mem_available_kb"] == PLENTY_KB and result["readings"]["disk_free_bytes"] == PLENTY_DISK


@told
def test_nothing_outside_the_temporary_and_final_directories_is_written(box):
    run_id = a_run_id()
    box.stage(run_id, INPUTS)
    before = box.snapshot()
    rc, result, _ = box.build("okin", run_id=run_id)
    after = box.snapshot()
    assert (rc, result["status"]) == (0, "built"), result
    added = {k for k in after if k not in before}
    removed = {k for k in before if k not in after}
    changed = {k for k in before if k in after and before[k] != after[k]}
    assert added == {f"box/data/builds/okin/{box.fixed}/fixed.txt", f"box/data/builds/.results/{run_id}.json",
                     "box/data/builds/.lock"}
    assert removed == {f"box/data/builds/.inputs/{run_id}/{p}" for p in INPUTS}            # its own staging, gone
    assert changed == set()
    assert box.leftovers() == []


@pytest.mark.parametrize("name,why", [("fail", "the tool exited 1"), ("empty", "the output is empty"),
                                      ("wrong", "not to the listed")])
@told
def test_a_failing_tool_an_empty_output_and_a_wrong_hash_leave_nothing(box, name, why):
    rc, result, _ = box.build(name)
    assert (rc, result["status"]) == (1, "failed"), result
    assert why in result["reason"]
    assert not (box.builds / name).exists()
    assert box.leftovers() == []
    if name == "wrong":
        assert result["output_hash"] == box.fixed and result["listed_hash"] == "0" * 64
        assert box.fixed in result["reason"] and "0" * 64 in result["reason"]       # it names both hashes


@told
def test_a_second_build_of_the_same_hash_is_a_no_op(box):
    first = box.build("ok")
    landed = box.builds / "ok" / box.fixed / "fixed.txt"
    stamp = landed.stat().st_mtime_ns
    rc, result, _ = box.build("ok")
    assert (first[0], first[1]["status"], rc, result["status"]) == (0, "built", 0, "present"), result
    assert landed.stat().st_mtime_ns == stamp and landed.read_bytes() == box.probe.FIXED
    assert [d.name for d in (box.builds / "ok").iterdir()] == [box.fixed]
    assert box.leftovers() == []


@told
def test_the_lock_refuses_a_second_build_and_the_refusal_writes_only_its_own_result(box):
    first_id, second_id = a_run_id(), a_run_id()
    box.stage(first_id, INPUTS)
    first = box.command("wait", first_id)
    with open(box.tmp / "first.out", "wb") as out:
        running = subprocess.Popen(first, env=box.env(), stdout=out, stderr=subprocess.STDOUT)
    try:
        began = time.time()
        while not (box.builds / ".tmp" / first_id).exists():          # made under the lock, before the tool starts
            assert running.poll() is None, "the first build ended before it started its tool"
            assert time.time() - began < GENEROUS, f"the first build did not start its tool in {GENEROUS}s"
            time.sleep(0.05)
        rc, refused, _ = box.build("ok", run_id=second_id, stage={"src/x.txt": b"x\n"})
        assert (rc, refused["status"], refused["run_id"]) == (3, "refused", second_id), refused
        assert "lock" in refused["reason"]
        assert not (box.builds / ".inputs" / second_id).exists()      # its own staging, removed on the refusal
        assert (box.builds / ".inputs" / first_id).is_dir() and (box.builds / ".tmp" / first_id).is_dir()
        assert not (box.builds / ".results" / f"{first_id}.json").exists()
        box.go.write_bytes(b"go")
        assert running.wait(timeout=GENEROUS) == 0
    finally:
        box.go.write_bytes(b"go")
        running.wait(timeout=GENEROUS)
        box.runs.append((first, running.returncode, (box.tmp / "first.out").read_text(errors="replace"), ""))
    done = box.result(first_id)
    assert (done["status"], done["run_id"]) == ("built", first_id), done
    assert box.result(second_id) == refused


@pytest.mark.parametrize("short", ["memory", "disk"])
@told
def test_the_unit_refuses_below_its_floor_and_records_both_readings(box, short):
    earlier = box.builds / "okin" / ("c" * 64)
    earlier.mkdir(parents=True)
    (earlier / "old.bin").write_bytes(b"x" * 1000)                   # the last build of that name: 1000 bytes
    need_kb, need_disk = (128 + 256) * 1024, 2 * GIB + 1000
    box.memory(need_kb - 1 if short == "memory" else need_kb)
    run_id = a_run_id()
    rc, result, _ = box.build("okin", run_id=run_id, stage=INPUTS, disk=need_disk - (short == "disk"))
    assert (rc, result["status"]) == (3, "refused"), result
    assert ("below the floor" in result["reason"]) and (("memory" if short == "memory" else "filesystem") in result["reason"])
    assert result["readings"] == {"disk_free_bytes": need_disk - (short == "disk"), "disk_needed_bytes": need_disk,
                                  "last_build": "c" * 64, "last_build_bytes": 1000,
                                  "mem_available_kb": need_kb - (short == "memory"), "mem_needed_kb": need_kb}
    assert not (box.builds / ".inputs" / run_id).exists()            # its staging, removed on the refusal
    assert not (box.builds / "okin" / box.fixed).exists() and box.leftovers() == []
    box.memory(need_kb)
    rc, result, _ = box.build("okin", stage=INPUTS, disk=need_disk)   # at the floor, it builds
    assert (rc, result["status"]) == (0, "built"), result


@told
def test_the_tool_sees_a_scratch_data_directory_read_only_inputs_and_no_inherited_concordance_variable(box):
    run_id = a_run_id()
    rc, result, _ = box.build("probe", run_id=run_id, stage=INPUTS)
    landed = box.builds / "probe" / box.report / "report.json"
    seen = landed.read_text(encoding="utf-8") if landed.exists() else ""
    assert (rc, result["status"]) == (0, "built"), (result, seen)
    assert json.loads(landed.read_text(encoding="utf-8"))["concordance_env"] == ["CONCORDANCE_DATA_DIR"]
    assert not (box.builds / ".inputs" / run_id).exists() and box.leftovers() == []


@pytest.mark.skipif(not LINUX, reason=LINUX_ONLY)
@told
def test_the_tools_oom_score_adj_is_1000_under_nice_and_ionice_and_its_peak_is_recorded(box):
    rc, result, _ = box.build("probe", stage=INPUTS)
    assert (rc, result["status"]) == (0, "built"), result
    report = json.loads((box.builds / "probe" / box.report / "report.json").read_text(encoding="utf-8"))
    assert (report["oom_score_adj"], report["nice"], report["ionice"]) == (1000, 19, "best-effort: prio 7")
    assert result["confinement"] == {"address_space_cap_mb": 128, "ionice": "-c 2 -n 7", "nice": 19,
                                     "oom_score_adj": 1000}
    assert isinstance(result["peak_rss_kb"], int) and result["peak_rss_kb"] > 0


@pytest.mark.skipif(not LINUX, reason=LINUX_ONLY)
@told
def test_a_tool_that_allocates_past_its_cap_fails_closed(box):
    rc, result, _ = box.build("hog")
    assert (rc, result["status"]) == (1, "failed"), result
    assert result["exit_code"] != 0 and "MemoryError" in "\n".join(result["tool_output_tail"])
    assert result["confinement"]["address_space_cap_mb"] == 128
    assert not (box.builds / "hog").exists() and box.leftovers() == []


@told
def test_a_tool_past_its_time_is_ended_and_leaves_nothing(box):
    """The tool sleeps 900 s, past the bound on the unit's own run, so only the unit's timeout can end it in time."""
    rc, result, _ = box.build("sleep", timeout=2)
    assert (rc, result["status"], result["timed_out"]) == (1, "failed", True), result
    assert result["reason"] == "the tool ran past 2 seconds and was ended"
    assert not (box.builds / "sleep").exists() and box.leftovers() == []


def test_a_removal_refused_for_a_moment_is_tried_again(bb, tmp_path, monkeypatch):
    """On Windows a file another process has only just opened can refuse removal briefly; the unit tries again."""
    held = tmp_path / "held"
    (held / "a").mkdir(parents=True)
    (held / "a" / "x.txt").write_bytes(b"x")
    real, tries = bb._remove_tree_once, []

    def refused_twice(path):
        tries.append(path)
        if len(tries) <= 2:
            raise PermissionError(32, "being used by another process")
        real(path)
    monkeypatch.setattr(bb, "_remove_tree_once", refused_twice)
    monkeypatch.setattr(bb.time, "sleep", lambda s: None)
    bb.remove_tree(held)
    assert len(tries) == 3 and not held.exists()


@told
def test_a_leftover_the_unit_cannot_remove_is_named_and_never_fails_a_landed_build(box, bb, monkeypatch):
    run_id = a_run_id()
    staging = box.stage(run_id, INPUTS)
    real = bb._remove_tree_once

    def staging_stays(path):
        if Path(path) == staging:
            raise PermissionError(32, "being used by another process")
        real(path)
    monkeypatch.setattr(bb, "_remove_tree_once", staging_stays)
    monkeypatch.setattr(bb.time, "sleep", lambda s: None)
    rc = bb.cmd_build(box.root, run_id, "okin", str(box.meminfo), PLENTY_DISK, str(box.scratch))
    result = box.result(run_id)
    assert (rc, result["status"]) == (0, "built"), result
    assert [c.split(" could not be removed: ")[0] for c in result["cleanup"]] == [f"data/builds/.inputs/{run_id}"]
    assert staging.is_dir() and (box.builds / "okin" / box.fixed / "fixed.txt").is_file()
    monkeypatch.setattr(bb, "_remove_tree_once", real)
    rc, later, _ = box.build("ok")                                     # the next build removes it, under the lock
    assert (rc, later["status"], "cleanup" in later) == (0, "built", False), later
    assert box.leftovers() == []


@told
def test_what_an_earlier_unit_left_is_removed_at_the_next_build(box):
    old = "20200101T000000Z-aaaaaaaaaaaa"
    (box.builds / ".tmp" / old).mkdir(parents=True)
    (box.builds / ".tmp" / old / "half.txt").write_bytes(b"half\n")
    box.stage(old, {"src/x.txt": b"x\n"})
    rc, result, _ = box.build("ok")
    assert (rc, result["status"]) == (0, "built"), result
    assert box.leftovers() == []


@pytest.mark.parametrize("staged", [{}, {**INPUTS, "src/extra.txt": b"extra\n"}])
@told
def test_the_staged_inputs_must_be_exactly_the_entrys_inputs(box, staged):
    rc, result, run_id = box.build("okin", stage=staged)
    assert (rc, result["status"]) == (1, "failed"), result
    assert "staged inputs" in result["reason"]
    assert not (box.builds / "okin").exists() and box.leftovers() == []


@told
def test_verify_reads_that_the_pinned_build_is_there_and_rehashes_to_its_name(box):
    def verify(digest):
        done = subprocess.run([sys.executable, str(UNIT), "verify", "--root", str(box.root), "ok", digest],
                              capture_output=True, text=True, timeout=GENEROUS)
        return done.returncode, done.stdout.strip()
    assert verify(box.fixed) == (1, f"NOT BUILT: data/builds/ok/{box.fixed} is not on the box")
    assert box.build("ok")[0] == 0
    assert verify(box.fixed) == (0, f"VERIFIED: data/builds/ok/{box.fixed} is there and re-hashes to its name")
    (box.builds / "ok" / box.fixed / "fixed.txt").write_bytes(b"altered\n")
    rc, said = verify(box.fixed)
    assert rc == 1 and said.startswith(f"MISMATCH: data/builds/ok/{box.fixed} re-hashes to ")


@told
def test_the_canary_builds_through_the_unit_as_listed_and_canary_fail_leaves_nothing(tmp_path, bb, probe):
    box = Box(tmp_path, bb, probe, {})
    (box.root / "tools" / "box_builds.txt").write_bytes(LISTING.read_bytes())
    (box.root / "tools" / "build_canary.py").write_bytes(CANARY.read_bytes())
    listed = bb.parse_listing(LISTING.read_text(encoding="utf-8"))
    rc, result, _ = box.build("canary")
    assert (rc, result["status"], result["output_hash"]) == (0, "built", listed["canary"].hash), result
    assert [p.name for p in (box.builds / "canary" / listed["canary"].hash).iterdir()] == ["canary.txt"]
    rc, result, _ = box.build("canary-fail")
    assert (rc, result["status"], result["reason"]) == (1, "failed", "the tool exited 1"), result
    assert "canary-fail: exiting 1 on purpose" in result["tool_output_tail"]
    assert not (box.builds / "canary-fail").exists() and box.leftovers() == []
