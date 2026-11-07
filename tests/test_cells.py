"""A stuck read costs one cell, never the site.

A verifier on a thread of the engine shares one lock with every other thread, so a read that holds it stops them all
and the window around it never wakes. These tests show that with a neutral stand-in, tests/fixtures/lock_holder.py (a
plain integer power, reached by no verifier), and pin what src/concordance/cells.py does about it. Whatever holds the
lock runs in a cell a pool kills, or in a child its parent kills (tests/fixtures/cell_probe.py). No test here opens a
port: a read reaches the API by dispatch, and the wall runs serve() with its socket calls taken away.

Windows has no forkserver, so the harness gate runs the spawn path, and every case here runs there but the few marked
for Linux. Those are proved on Linux by tools/cells_proof.sh, whose note the checker reads by test id.
"""
from __future__ import annotations

import ast
import importlib
import importlib.util
import io
import json
import multiprocessing
import os
import pickle
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
PROBE = FIXTURES / "cell_probe.py"
sys.path.insert(0, str(ROOT / "src"))
if str(FIXTURES) not in sys.path:
    sys.path.insert(0, str(FIXTURES))

import cell_probe  # noqa: E402
import lock_holder  # noqa: E402
from concordance import corpus, derivation as D, engine as E  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402
from concordance.verifiers import base as B, mathematics as M, physics as P  # noqa: E402
from concordance.web import api  # noqa: E402

TIMED_OUT = "verification timed out (> {}s)"
BUSY = "verifier busy (too many concurrent verifications) — retry shortly"
LEAN = ("concordance.cells", "lock_holder")     # what a cell in these tests loads: no heavy library, so it starts fast
BOUND_S = 300                                   # no child outlives this, whatever it is doing
WIDE = {"CELL_PROBE_WINDOW_S": "2.0"}           # wider than a machine paging under the suite ever stalls a thread
LINUX = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="a forkserver case: tools/cells_proof.sh runs it")
READ_DATA = ("zeta_zeros.jsonl", "pfs_grammar.json", "pfs_card_schema.json")   # tracked, and read by path in a cell


def stub_keeping_free_data(tmp) -> dict:
    """The environment of a read over data outside the tree: the tracked files a cell reads, and stub Strong's, thesaurus
    and spec data, since a fresh worktree has none and a read of them would decline on both sides and prove nothing."""
    for name in READ_DATA:
        shutil.copy(ROOT / "data" / name, Path(tmp) / name)
    cell_probe.stub_data(str(tmp))
    return {"CONCORDANCE_DATA_DIR": str(tmp), "CONCORDANCE_STRONGS_DIR": str(Path(tmp) / "strongs"), "PYTHONIOENCODING": "utf-8"}


def probe(*args, tmp_path, env=None):
    """One mode of the probe, its last line of stdout as JSON, killed at the bound whatever it is doing."""
    return json.loads(run_probe(*args, tmp_path=tmp_path, env=env)[0].strip().splitlines()[-1])


def run_probe(*args, tmp_path, env=None):
    """Its stdout and stderr, whole."""
    full = {**os.environ, "CONCORDANCE_DATA_DIR": str(tmp_path), "PYTHONIOENCODING": "utf-8", **(env or {})}
    p = subprocess.Popen([sys.executable, str(PROBE), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, encoding="utf-8", env=full)
    try:
        out, err = p.communicate(timeout=BOUND_S)
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
        pytest.fail(f"{args} did not finish in {BOUND_S}s: {err[-2000:]}")
    assert p.returncode == 0, err[-4000:]
    return out, err


@pytest.fixture
def cells():
    return importlib.import_module("concordance.cells")


@pytest.fixture
def pool_of(cells):
    """Pools for one test, each closed at the end whatever the test did."""
    made = []

    def make(size=1, **options):
        options.setdefault("preload", LEAN)
        made.append(cells.Cells(size, **options))
        return made[-1]

    yield make
    for pool in made:
        pool.close()


@pytest.fixture
def cells_on(cells, monkeypatch):
    """Cells on for derivation itself, the way serve() turns them on, with the stand-ins under made-up math modes."""
    for name in ("hold", "quick", "pid", "die", "shelf_read"):
        monkeypatch.setitem(D._MATH_MODES, name, getattr(lock_holder, name))
    yield cells.enable(1, preload=LEAN)
    cells.disable()


def step(mode):
    return D.verify_step("mathematics", {"mode": mode, "params": {}})


def alive(pid: int) -> bool:
    return pid in {p.pid for p in multiprocessing.active_children()}


def wait_until(check, secs=30.0):
    end = time.monotonic() + secs
    while time.monotonic() < end:
        if check():
            return True
        time.sleep(0.005)
    return False


def pid_of(pool) -> int:
    return pool.call(lock_holder.pid, ({},), 30).data["pid"]


# ── a stuck read ─────────────────────────────────────────────────────────────────────────────────────
def test_a_stuck_read_costs_its_cell_and_nothing_else(cells_on, monkeypatch):
    monkeypatch.setattr(D, "_VERIFY_TIMEOUT_S", 0.3)
    first = step("pid")["data"]["pid"]
    assert first != os.getpid()
    beats, stop, got = [], threading.Event(), {}

    def beat():
        while not stop.is_set():
            beats.append(time.monotonic())
            time.sleep(0.01)

    def read():
        got["began"] = time.monotonic()
        got["out"] = step("hold")
        got["ended"] = time.monotonic()

    heart, reader = threading.Thread(target=beat), threading.Thread(target=read)
    heart.start()
    reader.start()
    assert wait_until(lambda: cells_on.status()["taken"] == 1)
    began = time.monotonic()
    busy = step("quick")                                # the one cell is stuck: busy, at once, today's words
    busy_secs = time.monotonic() - began
    reader.join()
    stop.set()
    heart.join()
    assert busy == {"status": "ERROR", "detail": BUSY} and busy_secs < 0.3
    assert got["out"] == {"status": "ERROR", "detail": TIMED_OUT.format(0.3)}      # never a verdict
    assert 0.3 <= got["ended"] - got["began"] < 5
    assert len([b for b in beats if got["began"] <= b <= got["ended"]]) >= 5        # the front never stopped
    assert not alive(first)                             # no slot outlives its cell: it was gone before the slot came back
    assert cells_on.status()["ended"] == {"stuck": 1}   # one end, counted once
    assert cells_on.status()["taken"] == 0 and cells_on.status()["live"] == 0
    assert step("pid")["data"]["pid"] != first          # and it came back by itself


def test_a_held_lock_stops_a_thread_and_costs_only_a_cell(tmp_path):
    # as library use still runs it: the heartbeat stops and the window never fires
    env = dict(os.environ, CONCORDANCE_DATA_DIR=str(tmp_path), CELL_PROBE_WINDOW_S="0.3", PYTHONUNBUFFERED="1")
    p = subprocess.Popen([sys.executable, str(PROBE), "thread"], stdout=subprocess.PIPE, text=True, env=env)
    lines, read_seen = [], threading.Event()

    def pump():
        for line in p.stdout:
            lines.append(line.split())
            if line.startswith("read"):
                read_seen.set()

    threading.Thread(target=pump, daemon=True).start()
    try:
        assert read_seen.wait(60), "the child never reached the read"
        time.sleep(1.8)                                 # six windows
    finally:
        p.kill()
        p.wait()
    read_at = next(float(ln[1]) for ln in lines if ln[0] == "read")
    before = [ln for ln in lines if ln[0] == "beat" and float(ln[1]) <= read_at]
    after = [ln for ln in lines if ln[0] == "beat" and float(ln[1]) > read_at + 0.25]
    assert len(before) >= 3                             # it was beating
    assert not after                                    # the lock stopped it
    assert not [ln for ln in lines if ln[0] == "shed"]  # the window never fired

    # in a cell: the same read costs the cell and nothing else
    seen = probe("cells", tmp_path=tmp_path, env=WIDE)
    assert seen["first"] == "HOLDS"
    assert seen["beats"] >= 5 and seen["widest_gap"] < seen["window"]
    assert len(seen["health"]) >= 3
    assert all(h["status"] == 200 and h["ok"] is True and h["secs"] < seen["window"] for h in seen["health"])
    assert seen["verdict"] == "SYSTEM_ERROR" and seen["status"] == "ERROR"
    assert seen["detail"] == TIMED_OUT.format(seen["window"])
    assert seen["window"] <= seen["secs"] < seen["window"] + 10
    assert seen["next"] == "HOLDS"
    assert seen["pool"]["ended"].get("stuck") == 1 and seen["pool"]["taken"] == 0


def test_as_many_stuck_reads_as_cells_shed_alone_and_the_service_comes_back(tmp_path):
    seen = probe("flood", tmp_path=tmp_path, env=WIDE)
    assert [s["out"]["status"] for s in seen["stuck"]] == ["ERROR", "ERROR"]
    assert [s["out"]["detail"] for s in seen["stuck"]] == [TIMED_OUT.format(seen["window"])] * 2
    assert all(s["secs"] >= seen["window"] for s in seen["stuck"])
    assert seen["busy"]["status"] == "ERROR" and seen["busy"]["detail"] == BUSY
    assert seen["busy_secs"] < seen["window"]           # at once, not at a window
    assert seen["during"]["ended"].get("stuck") == 2
    assert seen["after"]["status"] == "CONFIRMED"       # no restart: a new cell filled the space
    assert seen["status"]["live"] == 1 and seen["status"]["taken"] == 0


@LINUX
def test_a_stuck_cell_ends_with_its_forkserver_and_the_service_comes_back(tmp_path):
    seen = probe("orphan", tmp_path=tmp_path)
    assert seen["out"]["status"] == "ERROR" and "CellFailed" in seen["out"]["detail"]
    assert seen["secs"] < seen["window"] / 2            # the kernel ended it long before its window
    assert seen["gone"] is True                         # the stuck cell is not running
    assert seen["after"]["status"] == "CONFIRMED"       # a new forkserver and a new cell


# ── a read in a cell reads as it did ─────────────────────────────────────────────────────────────────
def test_both_call_sites_read_in_a_cell_and_nothing_runs_in_front(cells_on, monkeypatch):
    def not_here(*_a, **_k):
        raise AssertionError("a read ran in the front process")

    monkeypatch.setattr(D._verifiers, "run_for_domain", not_here)
    assert step("pid")["status"] == "CONFIRMED"
    domain = D.verify_step("real_estate", {"NOT_A_PACKET": {}})
    assert domain["status"] == "NOT_APPLICABLE"          # the front's run_for_domain was never called
    assert cells_on.status()["started"] == 1


def test_a_domain_read_is_a_named_function_a_cell_can_be_told_to_run():
    assert pickle.loads(pickle.dumps(D._read_domain)) is D._read_domain
    assert all(pickle.loads(pickle.dumps(fn)) is fn for fn in D._MATH_MODES.values())


def test_a_cell_preloads_the_heavy_libraries_and_every_verifier():
    preload = set(D.cell_preload())
    assert {"sympy", "sympy.physics.units", "numpy", "scipy.stats"} <= preload
    assert set(D._verifiers.VERIFIERS.values()) <= preload
    assert {"concordance.derivation", "concordance.verifiers.riemann_accel", "concordance.strongs"} <= preload
    assert all(importlib.util.find_spec(name) for name in preload if name.startswith("concordance"))


def test_a_raise_in_a_cell_reads_as_a_raise_in_process(cells, monkeypatch):
    monkeypatch.setitem(D._MATH_MODES, "raises", lock_holder.raises)
    here = step("raises")
    cells.enable(1, preload=LEAN)
    try:
        there = step("raises")
    finally:
        cells.disable()
    assert there == here == {"status": "ERROR", "detail": "verifier raised: ValueError: a stand-in's own words"}


def test_serve_and_serve_many_turn_cells_on_before_the_warm_and_importing_does_not(cells, monkeypatch):
    assert cells.active() is None                       # importing the engine turned nothing on
    order = []

    class Server:
        def serve_forever(self):
            order.append("serve")

        def shutdown(self):
            pass

    def built(*_a, **_k):
        order.append("build")
        return Server()

    monkeypatch.setattr(api, "use_cells", lambda: order.append("cells"))
    monkeypatch.setattr(api, "build_server", built)
    api.serve("127.0.0.1", 0, "secular")
    assert order == ["cells", "build", "serve"]
    order.clear()
    api.serve_many("127.0.0.1", [(0, "witness"), (0, "secular")])
    assert order[:3] == ["cells", "build", "build"] and order.count("cells") == 1


def test_library_use_stays_on_threads_and_starts_no_process(tmp_path):
    seen = probe("library", tmp_path=tmp_path)
    assert seen["verdict"] == "HOLDS"
    assert seen["before"] is None and seen["after"] is None
    assert seen["children"] == 0 and seen["threads"]


# ── what a cell cannot do is ERROR, never a verdict ──────────────────────────────────────────────────
def test_a_cell_that_dies_is_error_and_the_next_read_stands(cells_on):
    out = step("die")
    assert out["status"] == "ERROR" and "verifier raised: CellFailed" in out["detail"]
    full = D.verify_derivation([{"id": "a", "domain": "mathematics", "spec": {"mode": "die", "params": {}}}])
    assert full["verdict"] == "SYSTEM_ERROR"
    assert cells_on.status()["ended"].get("dead") == 2 and cells_on.status()["taken"] == 0
    assert step("quick")["status"] == "CONFIRMED"


def test_an_answer_that_cannot_be_read_is_error(cells, pool_of):
    pool = pool_of()
    with pytest.raises(cells.CellFailed, match="could not be read"):
        pool.call(lock_holder.unprintable, ({},), 30)   # the cell could not write it, and is fine
    assert pool.status()["live"] == 1
    with pytest.raises(cells.CellFailed, match="could not be read"):
        pool.call(lock_holder.leak, ({},), 30)          # the front would not read it, so the cell goes
    assert pool.status()["ended"].get("dead") == 1 and pool.status()["taken"] == 0
    assert pool.call(lock_holder.quick, ({},), 30).status == "CONFIRMED"


def test_a_cell_that_cannot_start_is_error(cells, pool_of, monkeypatch):
    # the operating system refuses the process
    pool = pool_of()

    class Refused:
        def __init__(self, *_a, **_k):
            pass

        def start(self):
            raise OSError("no more processes")

    with monkeypatch.context() as m:
        m.setattr(pool._ctx, "Process", Refused)
        with pytest.raises(cells.CellFailed, match="could not start"):
            pool.call(lock_holder.quick, ({},), 5)
    assert pool.status()["taken"] == 0                  # the slot came back
    assert pool.call(lock_holder.quick, ({},), 30).status == "CONFIRMED"

    # it never says it is ready
    late = pool_of(start_s=0.0)
    with pytest.raises(cells.CellFailed, match="could not start"):
        late.call(lock_holder.quick, ({},), 5)
    assert late.status()["taken"] == 0 and late.status()["live"] == 0

    # it dies before it can say so
    monkeypatch.setattr(cells, "_cell_main", lock_holder.die_at_start)
    gone = pool_of()
    with pytest.raises(cells.CellFailed, match="could not start"):
        gone.call(lock_holder.quick, ({},), 5)
    assert gone.status()["taken"] == 0 and gone.status()["live"] == 0


class Broken:
    """A pipe that passes an idle check and then fails on the read, in a way that is no EOFError and no OSError."""

    def __init__(self, conn, failure):
        self.conn, self.failure = conn, failure

    def poll(self, *window):
        if window:
            raise self.failure
        return False

    def send_bytes(self, data):
        self.conn.send_bytes(data)

    def close(self):
        self.conn.close()


def test_any_failure_on_the_pipe_ends_the_cell_and_reads_as_error(cells, pool_of):
    pool = pool_of()
    first = pid_of(pool)
    pool._idle[0].conn = Broken(pool._idle[0].conn, ValueError("not a pipe problem"))
    with pytest.raises(cells.CellFailed, match="ended before it answered"):
        pool.call(lock_holder.quick, ({},), 30)
    assert not alive(first)                             # no cell left alive with nobody holding it
    assert pool.status()["ended"].get("dead") == 1
    assert pool.status()["live"] == 0 and pool.status()["taken"] == 0
    assert pid_of(pool) != first


def test_a_failure_past_exception_still_ends_the_cell(pool_of):
    class Stop(BaseException):
        pass

    pool = pool_of()
    first = pid_of(pool)
    pool._idle[0].conn = Broken(pool._idle[0].conn, Stop())
    with pytest.raises(Stop):
        pool.call(lock_holder.quick, ({},), 30)
    assert not alive(first)
    assert pool.status()["live"] == 0 and pool.status()["taken"] == 0


def test_a_failure_on_the_pipe_reaches_verify_step_as_error(cells_on):
    step("quick")
    cells_on._idle[0].conn = Broken(cells_on._idle[0].conn, ValueError("not a pipe problem"))
    out = step("quick")
    assert out["status"] == "ERROR" and "verifier raised: CellFailed" in out["detail"]


def test_a_failed_cell_reaches_the_trail_as_error(cells, cells_on, monkeypatch):
    def refused(*_a, **_k):
        raise cells.CellFailed("a cell could not start")

    monkeypatch.setattr(cells_on, "call", refused)
    out = D.verify_derivation([{"id": "a", "domain": "mathematics", "spec": {"mode": "quick", "params": {}}}])
    assert out["verdict"] == "SYSTEM_ERROR" and out["trail"][0]["status"] == "ERROR"
    assert out["error_at"] == "a"


# ── what crosses the wall ────────────────────────────────────────────────────────────────────────────
def crossed(cells, value):
    """A value as the front receives it: through a cell's filter, onto the pipe, through the front's reader."""
    return cells._read(pickle.dumps(cells._plain(value), protocol=pickle.HIGHEST_PROTOCOL))


def test_sympy_leaves_as_the_string_json_prints_for_it(cells):
    pytest.importorskip("sympy")
    made = lock_holder.sympy_values()
    got = crossed(cells, made)
    assert json.dumps(got.data, sort_keys=True, default=str) == json.dumps(made.data, sort_keys=True, default=str)
    assert got.data["actual"] == "1/3" and got.data["whole"] == "5" and got.data["flag"] == "True"
    assert got.data["nested"] == [{"root": "sqrt(2)"}, ("x + 1", "kept")] and got.data["plain"] == 2.5
    assert got.data["members"] == "{5}"
    assert crossed(cells, lock_holder.sympy_key()).data == {"by_symbol": {"x": 1}}


def test_numpy_and_plain_python_leave_as_they_are(cells):
    numpy = pytest.importorskip("numpy")
    got = crossed(cells, lock_holder.numpy_values()).data
    assert type(got["inside"]) is numpy.bool_ and type(got["p"]) is numpy.float64 and type(got["count"]) is numpy.int64
    assert type(got["bands"][0]["inside"]) is numpy.bool_ and not got["bands"][0]["inside"]
    assert type(got["row"]) is numpy.ndarray and got["row"].tolist() == [1.0, 2.0]
    made = lock_holder.stdlib_values().data
    got = crossed(cells, lock_holder.stdlib_values()).data
    assert got == made and {k: type(v) for k, v in got.items()} == {k: type(v) for k, v in made.items()}


def test_the_front_reads_plain_data_and_refuses_everything_else(cells):
    numpy = pytest.importorskip("numpy")
    sympy = pytest.importorskip("sympy")

    def read(value):
        return cells._Reader(io.BytesIO(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))).load()

    assert read(lock_holder.quick()).status == "CONFIRMED"
    assert read(numpy.array([[1.0, 2.0]]).T).tolist() == [[1.0], [2.0]]
    for refused in (sympy.Integer(5), print, os.system, threading.Lock, numpy.load):
        with pytest.raises(pickle.UnpicklingError):
            read(refused)


def test_real_values_cross_a_real_cell(cells, monkeypatch):
    monkeypatch.setitem(D._MATH_MODES, "sympy_values", lock_holder.sympy_values)
    monkeypatch.setitem(D._MATH_MODES, "numpy_values", lock_holder.numpy_values)
    modes = ("sympy_values", "numpy_values")
    here = {m: step(m) for m in modes}
    cells.enable(1, preload=(*LEAN, "sympy", "numpy"))
    try:
        there = {m: step(m) for m in modes}
    finally:
        cells.disable()
    for mode in modes:
        assert json.dumps(there[mode], sort_keys=True, default=str) == json.dumps(here[mode], sort_keys=True, default=str)


def test_a_step_bound_to_a_sympy_value_reads_the_same_through_a_cell_and_in_process(cells, monkeypatch):
    """The value crosses as the string JSON prints for it, and the bound step reads that string. Its spec_hash alone can
    differ: in process it hashes the repr of a value JSON cannot write. No verifier's data holds such a value over the moat
    and the goldens (test_the_moat_and_the_goldens_read_the_same_through_cells counts them), so only a stand-in shows it."""
    monkeypatch.setitem(D._MATH_MODES, "sympy_values", lock_holder.sympy_values)
    steps = [{"id": "a", "domain": "mathematics", "spec": {"mode": "sympy_values", "params": {}}},
             {"id": "b", "domain": "mathematics", "spec": {"mode": "equality", "params": {"expr_a": "1/3", "variables": {}}},
              "bind": {"params.expr_b": "a.actual"}}]
    here = D.verify_derivation(steps)
    assert here["verdict"] == "HOLDS"
    cells.enable(1, preload=(*LEAN, "sympy", "concordance.derivation"))
    try:
        there = D.verify_derivation(steps)
    finally:
        cells.disable()
    assert there["verdict"] == here["verdict"]
    assert [(t["id"], t["status"], t["detail"]) for t in there["trail"]] == [(t["id"], t["status"], t["detail"]) for t in here["trail"]]


def test_a_bound_step_reads_the_same_through_a_cell_and_in_process(cells):
    """A step built from a confirmed step's output: a value that crossed the wall is what the next step reads."""
    steps = [{"id": "a1", "domain": "geometry",
              "spec": {"GEOM_VERIFY": {"rect_length": 4, "rect_width": 6, "claimed_rect_area": 24}}},
             {"id": "a2", "domain": "geometry", "spec": {"GEOM_VERIFY": {"rect_width": 1, "claimed_rect_area": 24}},
              "bind": {"GEOM_VERIFY.rect_length": "a1.actual_area"}}]
    here = D.verify_derivation(steps)
    assert here["verdict"] == "HOLDS"
    cells.enable(1, preload=(*LEAN, "concordance.derivation", "concordance.verifiers.geometry"))
    try:
        there = D.verify_derivation(steps)
    finally:
        cells.disable()
    assert there == here                                # the verdict, the trail and each step's spec_hash


# ── the floor ────────────────────────────────────────────────────────────────────────────────────────
def test_a_cells_sympy_carries_the_floor_and_a_refusal_reads_as_on_a_thread(cells, monkeypatch):
    assert M._ensure_sympy()                            # this process's sympy, so the read on a thread is refused too
    monkeypatch.setitem(D._MATH_MODES, "past_the_floor", lock_holder.past_the_floor)
    here = step("past_the_floor")
    cells.enable(1, preload=(*LEAN, "sympy"))           # sympy by name, and nothing calls _ensure_sympy but the cell's start
    try:
        there = step("past_the_floor")
        assert cells.active().status()["ended"] == {}   # a refusal is an answer: the cell stays
    finally:
        cells.disable()
    assert there == here
    assert here["status"] == "NOT_APPLICABLE" and here["detail"].startswith("not checkable: ")


def test_a_cell_that_cannot_put_the_floor_on_does_not_start(cells, monkeypatch):
    def broken():
        raise RuntimeError("the floor did not go on")

    monkeypatch.setattr(M, "sympy_is_loaded", lambda: True)
    monkeypatch.setattr(M, "_ensure_sympy", broken)
    with pytest.raises(RuntimeError):
        cells._settle()


# ── the wall ─────────────────────────────────────────────────────────────────────────────────────────
def test_sympy_does_not_load_in_a_process_with_cells_on(cells, cells_on):
    with pytest.raises(B.PowerFloorRefused):
        M._ensure_sympy()
    with pytest.raises(B.PowerFloorRefused):
        P._ensure_sympy()
    assert issubclass(B.PowerFloorRefused, BaseException) and not issubclass(B.PowerFloorRefused, Exception)
    cells.disable()
    assert M._ensure_sympy() is True                    # library use loads it as it did


def test_the_wall_reads_as_not_checkable_under_the_window_and_in_the_engine(cells_on, monkeypatch):
    def needs_sympy_in_the_front(_params):
        M._ensure_sympy()
        return lock_holder.quick()

    monkeypatch.setattr(cells_on, "call", lambda *_a: (_ for _ in ()).throw(B.NeedsTheKeeping()))
    monkeypatch.setitem(D._MATH_MODES, "walled", needs_sympy_in_the_front)
    out = step("walled")                                # as a rerouted read would reach sympy: on the front's thread
    assert out["status"] == "NOT_APPLICABLE" and out["detail"].startswith("not checkable: ")

    packet = {"domain": "mathematics", "created_epoch": 1, "MATH_VERIFY": {"expr_a": "2+2", "expr_b": "4", "variables": []}}
    config = EngineConfig(skip_schema_validation=True)
    assert E.validate_packet(packet, now_epoch=10 ** 9, config=config).overall == "QUARANTINE"


def test_warm_leaves_the_heavy_libraries_to_the_cells(cells_on, monkeypatch):
    imported = []
    monkeypatch.setattr(importlib, "import_module", imported.append)
    monkeypatch.setattr(M, "_ensure_sympy", lambda: imported.append("_ensure_sympy"))
    D.warm()
    assert imported == []


@pytest.fixture(scope="module")
def front(tmp_path_factory):
    """serve() whole in its own process, then one claim per mathematics mode, one golden per domain and a rerouted shelf
    read, with stub data, a hook in the cell and the stigmergy flag on. One run: a spawned cell pays every import."""
    full = {**os.environ, **stub_keeping_free_data(tmp_path_factory.mktemp("front"))}
    done = subprocess.run([sys.executable, str(PROBE), "wall"], capture_output=True, text=True, encoding="utf-8",
                          env=full, timeout=BOUND_S)
    assert done.returncode == 0, done.stderr[-4000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_a_front_with_cells_on_reads_everything_and_never_loads_sympy(front):
    assert front["sympy"] is False
    assert not [lib for lib, loaded in front["heavy_after_serve"].items() if loaded], "the warm imported a heavy library"
    verdicts = front["verdicts"]
    assert {"mathematics " + mode for mode in D._MATH_MODES} <= set(verdicts)
    assert {verdicts["mathematics " + mode] for mode in D._MATH_MODES} == {"HOLDS"}      # real reads ran: not vacuous
    assert {verdicts[domain] for domain in ("physics", "statistics", "linguistics", "gue", "number_theory")} == {"HOLDS"}
    assert verdicts["shelf"] == "HOLDS"
    assert "SYSTEM_ERROR" not in verdicts.values()
    routes = front["routes"]
    assert {name: route["status"] for name, route in routes.items()} == dict.fromkeys(routes, 200)
    assert not [name for name, route in routes.items() if route["sympy"]]
    assert routes["plain claim"]["verdict"] == "HOLDS" and routes["audit"]["verdict"] == "BROKEN"
    assert routes["ask a claim"]["verdict"] == "HOLDS"  # /ask reaches verify_domain, and it read in a cell
    assert "36" in routes["ask a sum"]["message"]       # compute.answer stays in the front, on plain integers
    assert front["pool"]["started"] == 1 and not front["pool"]["ended"].get("dead")
    assert "sympy" in front["pool"]["cell_loaded"]      # it had it before its first read, outside any window
    assert front["threads"] == ["MainThread"]           # the preload starts none, so a forkserver forks nothing half done
    if not sys.platform.startswith("linux"):
        assert front["pool"]["made_by_front"] is True


def test_a_read_in_a_cell_writes_no_file_and_starts_no_process(front, capsys):
    touched = front["touched"]
    with capsys.disabled():
        print("\nCELL DATA FILES", json.dumps(touched["data"]))
    assert touched["stigmergy"] == "1"                  # the flag was on where the read ran, and still it wrote nothing
    assert touched["writes"] == [] and touched["processes"] == []
    assert {"zeta_zeros.jsonl", "verifier_specs.jsonl", "web.db", "concordance.db", "strongs_greek.json"} <= set(touched["data"])


def test_the_first_read_of_each_domain_in_a_new_cell_is_measured(front, capsys):
    """Printed for the Linux proof, where one over 2 s has its load moved into the preload. Elsewhere it is a number: a
    laptop paging under the suite is no measure of the box."""
    cold = front["first_read_s"]
    slowest = sorted(cold.items(), key=lambda kv: -kv[1])[:8]
    with capsys.disabled():
        print("\nCELL COLD", json.dumps({"reads": len(cold), "slowest": slowest}))
    assert len(cold) > 60
    if sys.platform.startswith("linux"):
        assert slowest[0][1] < 2.0, slowest


def test_the_hook_in_a_cell_can_fail(pool_of, tmp_path):
    pool = pool_of()
    pool.call(lock_holder.audit_on, ({},), 30)
    target = tmp_path / "written.txt"
    pool.call(lock_holder.write_a_file, (str(target),), 30)
    pool.call(lock_holder.start_a_process, ({},), 60)
    touched = pool.call(lock_holder.audit_read, ({},), 30).data
    assert [Path(p).name for p in touched["writes"]] == ["written.txt"]
    assert any(found.startswith("subprocess.Popen") for found in touched["processes"])


def test_the_accelerator_settles_at_a_cells_start_and_not_in_a_read(pool_of, tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    pool = pool_of(preload=(*LEAN, "numpy", "concordance.verifiers.riemann_accel"))
    assert pool.call(lock_holder.accelerator, ({},), 30).data == {"settled": True}
    pool.call(lock_holder.audit_on, ({},), 30)
    assert pool.call(lock_holder.accelerated_read, ({},), 30).data == {"values": 2}
    touched = pool.call(lock_holder.audit_read, ({},), 30).data
    assert touched["writes"] == [] and touched["processes"] == []       # its write probe and compile are behind it


def test_an_import_in_a_read_writes_no_bytecode(cells, pool_of, monkeypatch):
    assert pool_of().call(lock_holder.bytecode, ({},), 30).data == {"written": False}
    monkeypatch.delitem(sys.modules, cells._ACCELERATOR, raising=False)
    monkeypatch.setattr(sys, "dont_write_bytecode", False)              # the run may have it on already: show it goes on here
    cells._settle()
    assert sys.dont_write_bytecode is True


# ── the keeper's line ────────────────────────────────────────────────────────────────────────────────
def test_the_keeper_says_on_stderr_whether_sympy_is_in_the_front(tmp_path):
    """A real process, with logging as the service leaves it: unconfigured. Stderr is what the unit's journal reads."""
    out, err = run_probe("keeper", tmp_path=tmp_path)
    assert json.loads(out.strip().splitlines()[-1]) == {"sympy": True}
    before, _, after = err.partition("-- loading --")
    assert "cells keeper: sympy is not loaded in the front" in before
    assert "cells keeper: sympy is loaded in the front" not in before
    assert "cells keeper: sympy is loaded in the front" in after


def test_the_keeper_speaks_every_five_minutes_by_default(cells, pool_of):
    assert cells._SAY_S == 300
    assert pool_of()._say_s == 300


def test_a_closed_stderr_does_not_end_the_keeper(cells, pool_of, monkeypatch):
    class Closed:
        def write(self, _text):
            raise ValueError("I/O operation on closed file")

        def flush(self):
            pass

    pool = pool_of(idle_s=3600)
    monkeypatch.setattr(cells.sys, "stderr", Closed())
    pool._say()                                         # it does not raise, so the keeper's loop goes on


# ── the keeping ──────────────────────────────────────────────────────────────────────────────────────
def test_a_cell_has_no_keeping_and_every_door_says_so(pool_of):
    doors = pool_of().call(lock_holder.the_keeping_doors, ({},), 30).data
    assert doors == dict.fromkeys(("loaded", "default_corpus", "get_card"), "needs the keeping")
    assert issubclass(B.NeedsTheKeeping, BaseException) and not issubclass(B.NeedsTheKeeping, Exception)


def test_a_read_that_needs_the_keeping_runs_again_in_the_front(cells_on, corpus_left_as_found):
    corpus._DEFAULT = corpus.Corpus(dict(cell_probe.SHELF_CARDS))
    out = step("shelf_read")
    assert out["status"] == "CONFIRMED" and out["detail"] == "read the shelf"   # no `except Exception` read it as a miss
    assert out["data"] == {"pid": os.getpid(), "held": True}                    # the front's verdict is the one returned
    assert cells_on.status()["started"] == 1 and cells_on.status()["ended"] == {}


def test_the_read_again_runs_under_todays_window_and_slots(cells_on, monkeypatch):
    def keeps_going(_params):
        time.sleep(1.0)
        return lock_holder.quick()

    monkeypatch.setattr(cells_on, "call", lambda *_a: (_ for _ in ()).throw(B.NeedsTheKeeping()))
    monkeypatch.setitem(D._MATH_MODES, "keeps_going", keeps_going)
    held = 0
    while D._SLOTS.acquire(blocking=False):             # every slot taken: busy, in today's words
        held += 1
    try:
        assert step("keeps_going") == {"status": "ERROR", "detail": BUSY}
    finally:
        for _ in range(held):
            D._SLOTS.release()
    monkeypatch.setattr(D, "_VERIFY_TIMEOUT_S", 0.1)
    assert step("keeps_going") == {"status": "ERROR", "detail": TIMED_OUT.format(0.1)}


SHELF_CARDS = {
    **cell_probe.SHELF_CARDS,
    "card_src_pron_knight": {"id": "card_src_pron_knight", "shelf": "pronunciation", "title": "knight",
                             "body": "knight: pronounced (ARPABET) N AY1 T. From the CMU Pronouncing Dictionary."},
    "card_src_pron_night": {"id": "card_src_pron_night", "shelf": "pronunciation", "title": "night",
                            "body": "night: pronounced (ARPABET) N AY1 T. From the CMU Pronouncing Dictionary."},
    "card_src_pron_begin": {"id": "card_src_pron_begin", "shelf": "pronunciation", "title": "begin",
                            "body": "begin: pronounced (ARPABET) B IH0 G IH1 N. From the CMU Pronouncing Dictionary."},
    "card_src_pron_play": {"id": "card_src_pron_play", "shelf": "pronunciation", "title": "play",
                           "body": "play: pronounced (ARPABET) P L EY1. From the CMU Pronouncing Dictionary."},
    "card_src_etym_salary": {"id": "card_src_etym_salary", "shelf": "etymology", "title": "salary",
                             "body": "salary: etymology [L. salarium salt money, fr. sal salt.] From Webster 1913."},
}
# Each check that reads a shelf, by its function's name, with a claim the stub shelf confirms.
SHELF_READS = {
    "verify_syllables": {"word": "begin", "claimed_syllables": 2},
    "verify_morphology": {"word": "player", "claimed_root": "play", "claimed_suffix": "er"},
    "verify_rhyme": {"word_a": "cat", "word_b": "hat", "claimed_rhyme": True},
    "verify_homophone": {"word_a": "knight", "word_b": "night", "claimed_homophone": True},
    "verify_stress": {"word": "begin", "claimed_stress_syllable": 2},
    "verify_silent_letter": {"word": "knight", "letter": "k", "claimed_silent": True},
    "verify_vowel_sound": {"word": "play", "claimed_vowel_sound": "long a"},
    "verify_edge_sound": {"word": "cat", "claimed_edge_sound": "k", "position": "first"},
    "verify_origin": {"word": "salary", "claimed_language": "latin"},
}


def reads_a_shelf() -> set:
    """Every verify_ function of wordcraft that reaches the keeping, by the call graph of the module's own functions."""
    tree = ast.parse((ROOT / "src" / "concordance" / "verifiers" / "wordcraft.py").read_text(encoding="utf-8"))
    calls = {node.name: {n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
             for node in tree.body if isinstance(node, ast.FunctionDef)}
    reaching = {"_shelf_card_of"}
    while True:
        more = {name for name, called in calls.items() if called & reaching} - reaching
        if not more:
            return {name for name in reaching if name.startswith("verify_")}
        reaching |= more


def test_each_shelf_check_reads_the_same_through_a_cells_reroute_and_in_process(cells, corpus_left_as_found):
    assert reads_a_shelf() == set(SHELF_READS), "a check reads a shelf: give it a claim here"
    corpus._DEFAULT = corpus.Corpus(dict(SHELF_CARDS))
    here = {name: D.verify_step("wordcraft", {"WORD_VERIFY": spec}) for name, spec in SHELF_READS.items()}
    assert {out["status"] for out in here.values()} == {"CONFIRMED"}, here
    pool = cells.enable(1, preload=(*LEAN, "concordance.derivation", "concordance.verifiers.wordcraft"))
    try:
        there = {name: D.verify_step("wordcraft", {"WORD_VERIFY": spec}) for name, spec in SHELF_READS.items()}
    finally:
        cells.disable()
    assert there == here
    assert pool.status()["started"] == 1


def test_a_shelf_read_with_no_keeping_declines_on_both_sides(cells, corpus_left_as_found):
    corpus._DEFAULT = None
    claim = {"WORD_VERIFY": SHELF_READS["verify_rhyme"]}
    here = D.verify_step("wordcraft", claim)
    cells.enable(1, preload=(*LEAN, "concordance.derivation", "concordance.verifiers.wordcraft"))
    try:
        there = D.verify_step("wordcraft", claim)
    finally:
        cells.disable()
    assert there == here and here["status"] == "NOT_APPLICABLE"
    assert corpus._DEFAULT is None                      # the reroute built nothing


# Three doors, and nothing else of the corpus module, so a read in a cell reaches none of its state by another way.
DOORS = frozenset({"loaded", "default_corpus", "get_card"})


def uses_of_the_corpus(source: str) -> set:
    """Every use of the corpus module in a source other than a call of one of the three doors."""
    found, tree = set(), ast.parse(source)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[-1] == "corpus":
            found |= {alias.name for alias in node.names if alias.name not in DOORS}
        elif isinstance(node, ast.ImportFrom):
            names |= {alias.asname or alias.name for alias in node.names if alias.name == "corpus"}
        elif isinstance(node, ast.Import):
            names |= {alias.asname or alias.name for alias in node.names if alias.name.split(".")[-1] == "corpus"}
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.split(".")[-1] == "corpus":
            found.add("a dynamic import")
    doors = {id(node.value) for node in ast.walk(tree)
             if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.attr in DOORS}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in names and id(node) not in doors:
            found.add(node.id)
    return found


def test_no_verifier_uses_the_corpus_but_by_its_three_doors():
    held = {path.name: uses_of_the_corpus(path.read_text(encoding="utf-8"))
            for path in sorted((ROOT / "src" / "concordance" / "verifiers").rglob("*.py"))}
    assert len(held) > 70
    assert not {name: found for name, found in held.items() if found}


@pytest.mark.parametrize("source", [
    "from .. import corpus\ncorpus.search('x')\n",
    "from .. import corpus as c\nc._DEFAULT\n",
    "from .. import corpus as c\nf(c)\n",
    "from ..corpus import search\n",
    "import concordance.corpus as c\nc.browse()\n",
    "import importlib\nimportlib.import_module('concordance.corpus')\n",
])
def test_the_walk_of_the_corpus_fails_on_a_planted_use(source):
    assert uses_of_the_corpus(source)


def test_the_walk_of_the_corpus_lets_the_three_doors_through():
    assert uses_of_the_corpus("from .. import corpus as c\nc.loaded()\nc.default_corpus()\nc.get_card('x')\n") == set()
    assert uses_of_the_corpus("from ..corpus import loaded\nloaded()\n") == set()


# ── the same readings ────────────────────────────────────────────────────────────────────────────────
def test_the_moat_and_the_goldens_read_the_same_through_cells(tmp_path):
    full = {**os.environ, **stub_keeping_free_data(tmp_path)}

    def run(how):
        p = subprocess.run([sys.executable, str(PROBE), "moat", how], capture_output=True, text=True, encoding="utf-8",
                           env=full, timeout=BOUND_S)
        assert p.returncode == 0, p.stderr[-4000:]
        return json.loads(p.stdout.strip().splitlines()[-1])

    here, there = run("process"), run("cells")
    assert len(here["rows"]) == len(there["rows"]) > 200
    assert here["sympy_values"] == 0                    # so no bound step here can read other than a string of it
    assert there["sympy"] is False                      # the whole moat, and sympy never entered the front
    differ = [a[0] for a, b in zip(here["rows"], there["rows"]) if a != b]
    assert not differ, differ[:10]                      # the verdict, the status, the keys, and every field as JSON prints it
    assert not [desc for desc, label, verdict, *_ in there["rows"] if not label and verdict == "HOLDS"]
    assert not there["pool"]["ended"].get("dead") and not there["pool"]["ended"].get("stuck")


def test_strongs_data_the_thesaurus_and_a_spec_read_the_same_in_a_cell(tmp_path):
    seen = probe("stub", tmp_path=tmp_path, env={"CONCORDANCE_STRONGS_DIR": str(tmp_path / "strongs")})
    assert seen["there"] == seen["here"]
    assert {name: out["status"] for name, out in seen["there"].items()} == {
        "strongs": "CONFIRMED", "strongs_wrong_count": "MISMATCH", "thesaurus": "CONFIRMED", "thesaurus_is_a": "CONFIRMED",
        "spec": "CONFIRMED", "spec_wrong": "MISMATCH"}
    assert seen["pool"]["started"] == 1 and seen["pool"]["ended"] == {}


def test_the_wire_gate_has_a_shelf_read_and_a_strongs_read_that_mint_no_seal():
    import live_assay
    probes = {row["id"]: row for row in live_assay.load_probes(ROOT / "eval" / "live_probes.jsonl")}
    for name, domain in (("verify.shelf.rhyme.holds", "wordcraft"), ("verify.strongs.word.holds", "linguistics")):
        row = probes[name]
        assert row["path"] == "/verify" and row["query"] == {"seal": "0"}
        assert row["body"]["steps"][0]["domain"] == domain and not row.get("known_miss")
        assert {"at": "verdict", "eq": "HOLDS"} in row["expect"] and {"at": "seal", "absent": True} in row["expect"]


# ── a cell has a life ────────────────────────────────────────────────────────────────────────────────
def test_a_used_cell_retires_after_its_reads_and_its_slot_is_used_again(pool_of):
    pool = pool_of(reads=3)
    pids = [pid_of(pool) for _ in range(3)]
    assert len(set(pids)) == 1
    assert pool.status()["ended"].get("used") == 1 and pool.status()["live"] == 0
    assert not alive(pids[0])
    assert pid_of(pool) != pids[0] and pool.status()["started"] == 2


def test_an_idle_cell_retires_by_itself_and_a_new_read_fills_the_space(pool_of):
    pool = pool_of(idle_s=0.05)
    first = pid_of(pool)
    assert wait_until(lambda: pool.status()["live"] == 0)
    assert pool.status()["ended"].get("idle") == 1 and pool.status()["taken"] == 0
    assert not alive(first)
    assert pid_of(pool) != first


def test_a_cell_that_died_while_idle_costs_no_read(pool_of):
    pool = pool_of()
    first = pid_of(pool)
    next(p for p in multiprocessing.active_children() if p.pid == first).kill()
    assert wait_until(lambda: not alive(first))
    assert pid_of(pool) != first
    assert pool.status()["ended"].get("dead") == 1


def test_an_idle_cell_with_something_on_its_pipe_is_not_asked(pool_of):
    """An idle cell has nothing to say, so anything waiting on its pipe is an answer to no read, and the next read must
    not take it for its own."""
    class Stale:
        def __init__(self, conn):
            self.conn = conn

        def poll(self, *_window):
            return True

        def close(self):
            self.conn.close()

    pool = pool_of()
    first = pid_of(pool)
    pool._idle[0].conn = Stale(pool._idle[0].conn)
    assert pid_of(pool) != first                        # a new cell answered
    assert pool.status()["ended"].get("dead") == 1 and not alive(first)


def test_waiting_means_alive_with_nothing_on_the_pipe(cells):
    class Proc:
        def __init__(self, up):
            self.up = up

        def is_alive(self):
            return self.up

    class Conn:
        def __init__(self, polled):
            self.polled = polled

        def poll(self):
            if isinstance(self.polled, Exception):
                raise self.polled
            return self.polled

    assert cells._Cell(Proc(True), Conn(False)).waiting() is True
    assert cells._Cell(Proc(True), Conn(True)).waiting() is False
    assert cells._Cell(Proc(False), Conn(False)).waiting() is False
    assert cells._Cell(Proc(True), Conn(BrokenPipeError())).waiting() is False
    assert cells._Cell(Proc(True), Conn(EOFError())).waiting() is False


def test_a_retiring_cell_holds_its_slot_until_it_is_gone(cells, pool_of, monkeypatch):
    pool = pool_of(idle_s=3600)
    first = pid_of(pool)
    pool._idle[0].since -= 7200
    seen, end = {}, pool._end

    def watched(cell, why):
        seen["during"] = pool.status()
        with pytest.raises(cells.Saturated):            # the process is still there, so the slot is not free
            pool.call(lock_holder.quick, ({},), 30)
        end(cell, why)
        seen["after"] = pool.status()

    monkeypatch.setattr(pool, "_end", watched)
    pool._retire_idle()
    assert seen["during"]["taken"] == 1 and seen["during"]["live"] == 1 and seen["during"]["idle"] == 0
    assert seen["after"]["live"] == 0 and seen["after"]["ended"].get("idle") == 1
    assert pool.status()["taken"] == 0 and not alive(first)


def test_the_count_of_live_cells_never_passes_the_size(pool_of):
    size = 2
    pool = pool_of(size, reads=2)
    stop, widest, outcomes = threading.Event(), [0], []

    def watch():
        while not stop.is_set():
            named = [p for p in multiprocessing.active_children() if p.name == "concordance-cell"]
            widest[0] = max(widest[0], len(named), pool.status()["live"])
            time.sleep(0.001)

    def read():
        for _ in range(3):
            try:
                outcomes.append(pool.call(lock_holder.quick, ({},), 30).status)
            except Exception as exc:  # noqa: BLE001 — busy is an answer here
                outcomes.append(type(exc).__name__)

    watcher = threading.Thread(target=watch)
    readers = [threading.Thread(target=read) for _ in range(4)]
    watcher.start()
    for r in readers:
        r.start()
    for r in readers:
        r.join()
    stop.set()
    watcher.join()
    assert 1 <= widest[0] <= size
    assert set(outcomes) <= {"CONFIRMED", "Saturated"} and "CONFIRMED" in outcomes
    assert pool.status()["taken"] == 0


def test_the_cell_says_how_it_was_made(pool_of):
    pool = pool_of()
    pool.call(lock_holder.quick, ({},), 30)
    assert pool.method == ("spawn" if os.name == "nt" else "forkserver")
    assert pool.status()["made_by_front"] is (os.name == "nt")          # told by the cell, not assumed by the pool


def test_no_in_process_memory_limit_is_set(cells, pool_of):
    source = Path(cells.__file__).read_text(encoding="utf-8")
    assert "setrlimit" not in source and "RLIMIT" not in source
    assert pool_of().call(lock_holder.limits, ({},), 30).data == lock_holder.limits().data


def test_a_cell_asks_the_kernel_to_end_it_with_its_parent(cells, monkeypatch):
    """Once the forkserver has died multiprocessing cannot kill a cell, so the kernel does. On Linux only: elsewhere
    the front is the parent and its kill works."""
    asked = []

    class Libc:
        def prctl(self, *args):
            asked.append(args)
            return 0

    monkeypatch.setattr(cells.sys, "platform", "linux")
    cells._end_with_parent(Libc())
    assert asked == [(1, 9)]                            # PR_SET_PDEATHSIG, SIGKILL
    monkeypatch.setattr(cells.sys, "platform", "win32")
    cells._end_with_parent(Libc())
    assert len(asked) == 1


def test_a_cell_puts_up_its_walls_before_it_loads_anything(cells, monkeypatch):
    """The real effects are Linux's, and the proof's to show. That a cell asks for them, first, is true everywhere."""
    order = []

    class Pipe:
        def send_bytes(self, _data):
            order.append("ready")

        def recv_bytes(self):
            raise EOFError

    monkeypatch.setattr(cells, "_in_a_cell", False)     # put back at the end: this process is no cell
    monkeypatch.setattr(cells, "_raise_oom_score", lambda: order.append("oom"))
    monkeypatch.setattr(cells, "_end_with_parent", lambda: order.append("parent"))
    monkeypatch.setattr(cells, "_settle", lambda: order.append("settled"))
    monkeypatch.setattr(cells.signal, "signal", lambda *_a: None)
    monkeypatch.setattr(cells.importlib, "import_module", lambda name: order.append(name))
    cells._cell_main(Pipe(), ("heavy",))
    assert order == ["oom", "parent", "heavy", "settled", "ready"]
    assert cells.in_a_cell() is True


def test_a_cell_whose_parent_has_already_gone_ends_itself(cells, monkeypatch):
    monkeypatch.setattr(cells.sys, "platform", "linux")
    ppids = iter((10, 1))
    monkeypatch.setattr(cells.os, "getppid", lambda: next(ppids))

    class Libc:
        def prctl(self, *_args):
            return 0

    ended = []
    monkeypatch.setattr(cells.os, "_exit", ended.append)
    cells._end_with_parent(Libc())
    assert ended == [1]


def test_each_cell_raises_its_own_oom_score(cells, pool_of, tmp_path):
    held = tmp_path / "oom_score_adj"
    held.write_text("0", encoding="ascii")
    cells._raise_oom_score(str(held))
    assert held.read_text(encoding="ascii") == "1000"
    cells._raise_oom_score(str(tmp_path / "no" / "such" / "file"))      # where the platform has none, it does nothing
    if sys.platform.startswith("linux"):
        assert pool_of().call(lock_holder.oom_score, ({},), 30).data["oom_score_adj"] == "1000"


# ── forkserver cases, for the Linux proof ────────────────────────────────────────────────────────────
@LINUX
def test_a_cell_is_made_by_a_forkserver_and_shares_what_it_preloaded(cells, tmp_path):
    """The forkserver is this process's for life and holds whatever preload it started with, so this runs in a child."""
    full = dict(os.environ, CONCORDANCE_DATA_DIR=str(tmp_path), PYTHONIOENCODING="utf-8")
    code = ("import json, sys\n"
            f"sys.path[:0] = [{str(ROOT / 'src')!r}]\n"
            "from concordance import cells, derivation as D\n"
            "pool = cells.enable(1, preload=D.cell_preload())\n"
            "print(json.dumps({'read': D.verify_step('real_estate', {}), 'status': pool.status()}))\n")
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=full, timeout=BOUND_S)
    assert done.returncode == 0, done.stderr[-4000:]
    seen = json.loads(done.stdout.strip().splitlines()[-1])["status"]
    assert seen["method"] == "forkserver" and seen["made_by_front"] is False
    assert {"sympy", "numpy", "scipy.stats"} <= set(seen["cell_inherited"])


@LINUX
def test_memory_of_a_forkserver_and_four_cells_after_reads(tmp_path, capsys):
    """Not a bound: the numbers the ship's sum takes, printed past pytest's capture so the proof's output carries them."""
    seen = probe("memory", tmp_path=tmp_path, env=stub_keeping_free_data(tmp_path))
    with capsys.disabled():
        print("\nCELL MEMORY", json.dumps({k: seen[k] for k in ("forkserver", "cells", "front", "reads")}))
    assert len(seen["cells"]) == 4 and not seen["pool"]["ended"].get("dead")
    assert all(cell["pss_kb"] > 0 and cell["peak_rss_kb"] >= cell["rss_kb"] for cell in seen["cells"])
