"""The child processes behind tests/test_cells.py. A read that holds the lock freezes the process it runs in, so
each mode runs apart from pytest, and its parent kills it at a bound whatever happens here. Every mode ends with one
line of JSON on stdout, except `thread`, which never ends by itself and streams what it saw until it is killed.

    python tests/fixtures/cell_probe.py thread              a held lock on a thread, as library use still runs it
    python tests/fixtures/cell_probe.py cells               a held lock in a cell, read through the API
    python tests/fixtures/cell_probe.py flood               as many held locks as there are cells
    python tests/fixtures/cell_probe.py orphan              a held lock in a cell whose forkserver is killed (Linux)
    python tests/fixtures/cell_probe.py wall                serve() whole, then one read of everything, watched
    python tests/fixtures/cell_probe.py library             what importing and verifying starts
    python tests/fixtures/cell_probe.py moat cells|process  the moat and both goldens of each domain, one digest per case
    python tests/fixtures/cell_probe.py stub                stub Strong's data, thesaurus and spec, in process and in a cell
    python tests/fixtures/cell_probe.py keeper              the keeper's line, before and after sympy loads
    python tests/fixtures/cell_probe.py memory              what a forkserver and four cells hold after reads (Linux)

Nothing here opens a port and nothing here sends anything anywhere: a read reaches the API by dispatch, as a handler
would call it, and the wall runs serve() with its socket calls taken away.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
for _path in (HERE, os.path.join(ROOT, "src"), os.path.join(ROOT, "tools")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

WINDOW_S = float(os.environ.get("CELL_PROBE_WINDOW_S", "1.0"))
HOLD = {"mode": "hold", "params": {}}
QUICK = {"mode": "quick", "params": {}}
# The modes the moat's claims do not reach, each with a true claim.
MORE_MODES = {
    "integral": {"integrand": "2*x", "variable": "x", "claimed_antiderivative": "x**2"},
    "limit": {"function": "sin(x)/x", "variable": "x", "point": "0", "claimed_limit": "1"},
    "solve": {"equation": "x**2 = 4", "variable": "x", "claimed_solutions": ["2", "-2"]},
    "numeric": {"numeric_expr": "2**10", "claimed_value": 1024},
    "calc_chain": {"calc_steps": ["2+2 = 4", "4*3 = 12"]},
    "system": {"equations": ["x + y = 3", "x - y = 1"], "claimed_solution": {"x": 2, "y": 1}},
    "number_theory": {"gcd": [12, 18], "claimed_gcd": 6},
}
SHELF_CARDS = {
    "card_src_pron_cat": {"id": "card_src_pron_cat", "shelf": "pronunciation", "title": "cat",
                          "body": "cat: pronounced (ARPABET) K AE1 T. From the CMU Pronouncing Dictionary."},
    "card_src_pron_hat": {"id": "card_src_pron_hat", "shelf": "pronunciation", "title": "hat",
                          "body": "hat: pronounced (ARPABET) HH AE1 T. From the CMU Pronouncing Dictionary."},
}
RHYME = {"word_a": "cat", "word_b": "hat", "claimed_rhyme": True}
# A spec of its own domain, so nothing but the file on disk can answer for it.
STUB_SPEC = {"id": "spec_stub", "domain": "stub_doubling", "packet_key": "STUB_VERIFY", "status": "admitted",
             "checks": [{"check": "doubled", "inputs": {"x": "x"}, "claimed": "claimed_double", "compute": "x * 2",
                         "tolerance": {"rel": 0.001, "abs": 1e-06},
                         "goldens": {"true": {"x": 2.0, "claimed_double": 4.0}, "false": {"x": 2.0, "claimed_double": 5.0}}}]}
STUB_READS = {
    "strongs": ("linguistics", {"LING_VERIFY": {"strongs": "G26", "transliteration_claim": "agape", "gloss_claim": "love",
                                                "claimed_count": 36, "cognate_pair": ["G25", "G26"]}}),
    "strongs_wrong_count": ("linguistics", {"LING_VERIFY": {"strongs": "G26", "claimed_count": 37}}),
    "thesaurus": ("linguistics", {"LING_VERIFY": {"relation_a": "car", "relation_b": "automobile", "claimed_relation": "synonym"}}),
    "thesaurus_is_a": ("linguistics", {"LING_VERIFY": {"relation_a": "car", "relation_b": "vehicle", "claimed_relation": "is_a"}}),
    "spec": ("stub_doubling", {"STUB_VERIFY": {"x": 3.0, "claimed_double": 6.0}}),
    "spec_wrong": ("stub_doubling", {"STUB_VERIFY": {"x": 3.0, "claimed_double": 7.0}}),
}


def stub_data(root: str) -> None:
    """Strong's, thesaurus and spec data of a few rows, each file the shape the real one has, under `root`. A fresh
    worktree holds none of them, so without this a read of them declines on both sides and proves nothing."""
    base = Path(root)
    lexicon = base / "strongs" / "original" / "lexicon"
    web = base / "strongs" / "web"
    lexicon.mkdir(parents=True, exist_ok=True)
    web.mkdir(parents=True, exist_ok=True)
    greek = {"G25": {"lemma": "ἀγαπάω", "translit": "agapáō", "strongs_def": "to love", "derivation": "perhaps from G26"},
             "G26": {"lemma": "ἀγάπη", "translit": "agápē", "strongs_def": "love, affection", "derivation": "from G25"}}
    (lexicon / "strongs_greek.json").write_text(json.dumps(greek, ensure_ascii=False), encoding="utf-8")
    (lexicon / "strongs_hebrew.json").write_text("{}", encoding="utf-8")
    with sqlite3.connect(web / "web.db") as db:
        db.execute("create table t_web (b int, c int, v int, t text)")
        db.executemany("insert into t_web values (?, ?, ?, ?)", [(43, 13, v, "stub verse") for v in range(1, 37)])
    with sqlite3.connect(web / "concordance.db") as db:
        db.execute("create table concordance (b int, c int, v int, word_pos int, word text, strongs text)")
        db.executemany("insert into concordance values (?, ?, ?, ?, ?, ?)",
                       [(43, 13, v, 1, "stub", "G26") for v in range(1, 37)])       # the golden's own count
    with sqlite3.connect(base / "thesaurus.db") as db:
        db.execute("create table thes (word text, syn text, broader text)")
        db.executemany("insert into thes values (?, ?, ?)", [("car", '["automobile"]', '["vehicle"]'),
                                                             ("automobile", '["car"]', '["vehicle"]'),
                                                             ("vehicle", "[]", "[]")])
    (base / "verifier_specs.jsonl").write_text(json.dumps(STUB_SPEC) + "\n", encoding="utf-8")


def _stand_ins():
    import lock_holder
    from concordance import derivation as D
    D._VERIFY_TIMEOUT_S = WINDOW_S
    D._MATH_MODES["hold"] = lock_holder.hold
    D._MATH_MODES["quick"] = lock_holder.quick
    return D


def _say(obj) -> None:
    print(json.dumps(obj, default=str), flush=True)


def _api():
    from concordance.config import EngineConfig
    from concordance.web import api
    config = EngineConfig("secular")

    def post(body: dict) -> dict:
        _status, out = api.dispatch("POST", "/verify", {"seal": "0"}, body, config)
        return out

    def health() -> tuple:
        return api.dispatch("GET", "/health", {}, None, config)

    return post, health


def thread_mode() -> None:
    D = _stand_ins()

    def beat():
        while True:
            print("beat", time.monotonic(), flush=True)
            time.sleep(0.02)

    threading.Thread(target=beat, daemon=True).start()
    time.sleep(0.3)
    print("read", time.monotonic(), flush=True)
    out = D.verify_step("mathematics", HOLD)
    print("shed", time.monotonic(), json.dumps(out), flush=True)


def cells_mode() -> None:
    _stand_ins()
    from concordance import cells
    post, health = _api()
    health()                                                    # the front's own first read is not this test's
    pool = cells.enable(1, preload=("lock_holder",))
    first = post(QUICK)                                         # the cell is up before the window is watched
    beats = []

    def beat():
        while True:
            beats.append(time.monotonic())
            time.sleep(0.02)

    threading.Thread(target=beat, daemon=True).start()
    time.sleep(0.2)
    got = {}

    def read():
        began = time.monotonic()
        got["body"] = post(HOLD)
        got["began"], got["ended"] = began, time.monotonic()

    reader = threading.Thread(target=read)
    reader.start()
    answers = []
    while reader.is_alive():
        began = time.monotonic()
        status, body = health()
        answers.append({"at": began, "status": status, "ok": body.get("ok"), "secs": time.monotonic() - began})
        time.sleep(0.05)
    reader.join()
    after = post(QUICK)
    during = [b for b in beats if got["began"] <= b <= got["ended"]]
    gaps = [b - a for a, b in zip(during, during[1:])]
    answers = [h for h in answers if got["began"] <= h["at"] <= got["ended"]]
    held = got["body"]
    _say({"first": first["verdict"], "secs": got["ended"] - got["began"], "beats": len(during),
          "widest_gap": max(gaps or [0]), "health": answers, "verdict": held["verdict"],
          "status": held["trail"][0]["status"], "detail": held["trail"][0]["detail"], "next": after["verdict"],
          "pool": pool.status(), "window": WINDOW_S})


def flood_mode() -> None:
    D = _stand_ins()
    from concordance import cells
    size = 2
    pool = cells.enable(size, preload=("lock_holder",))
    got = []

    def read():
        began = time.monotonic()
        out = D.verify_step("mathematics", HOLD)
        got.append({"out": out, "secs": time.monotonic() - began})

    readers = [threading.Thread(target=read) for _ in range(size)]
    for r in readers:
        r.start()
    while pool.status()["taken"] < size:
        time.sleep(0.005)
    began = time.monotonic()
    busy = D.verify_step("mathematics", QUICK)
    busy_secs = time.monotonic() - began
    for r in readers:
        r.join()
    during = pool.status()
    after = D.verify_step("mathematics", QUICK)
    _say({"stuck": got, "busy": busy, "busy_secs": busy_secs, "during": during, "after": after,
          "status": pool.status(), "window": WINDOW_S})


def orphan_mode() -> None:
    os.environ["CELL_PROBE_WINDOW_S"] = "30"
    global WINDOW_S
    WINDOW_S = 30.0
    D = _stand_ins()
    import signal
    from multiprocessing import forkserver
    from concordance import cells
    pool = cells.enable(1, preload=("lock_holder",))
    D.verify_step("mathematics", QUICK)
    cell = pool.status()["pids"][0]
    got = {}

    def read():
        began = time.monotonic()
        got["out"] = D.verify_step("mathematics", HOLD)
        got["secs"] = time.monotonic() - began

    reader = threading.Thread(target=read)
    reader.start()
    while pool.status()["taken"] < 1:
        time.sleep(0.005)
    time.sleep(0.2)
    os.kill(forkserver._forkserver._forkserver_pid, signal.SIGKILL)
    reader.join()
    end = time.monotonic() + 5
    while time.monotonic() < end and _running(cell):
        time.sleep(0.02)
    _say({**got, "gone": not _running(cell), "after": D.verify_step("mathematics", QUICK), "window": WINDOW_S})


def _running(pid: int) -> bool:
    """Is it running? A zombie is not: it holds no memory and is only waiting for init to read it."""
    try:
        with open(f"/proc/{pid}/stat", encoding="ascii") as fh:
            return fh.read().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return False


# ── the wall ─────────────────────────────────────────────────────────────────────────────────────────
def _goldens() -> dict:
    with open(os.path.join(ROOT, "data", "domain_goldens.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _one_of_each() -> dict:
    """The true golden of each domain and a true claim of each mathematics mode, as /verify takes them. The mathematics
    golden is a MATH_VERIFY packet, which derivation.py here has no branch for, so that domain reads by its modes."""
    import benchmark as B
    picked = {}
    for domain, pair in _goldens().items():
        if pair["packet_key"] != "MATH_VERIFY":
            picked[domain] = {"id": "g", "domain": domain, "spec": {pair["packet_key"]: pair["true"]}}
    for label, spec, _desc in B.CLAIMS:
        if label:
            picked.setdefault("mathematics " + spec["mode"], {"id": "m", "domain": "mathematics", "spec": spec})
    for mode, params in MORE_MODES.items():
        picked["mathematics " + mode] = {"id": "m", "domain": "mathematics", "spec": {"mode": mode, "params": params}}
    return picked


def _no_port() -> None:
    """serve() runs whole and nothing listens: its socket calls go, and serve_forever returns at once."""
    import http.server
    import socketserver
    http.server.HTTPServer.server_bind = lambda self: None
    socketserver.TCPServer.server_activate = lambda self: None
    socketserver.BaseServer.serve_forever = lambda self, *_a, **_k: None


def _routes() -> dict:
    """The doors that read request text before a verifier does, each as a handler would call it."""
    from concordance.config import EngineConfig
    from concordance.web import api
    config = EngineConfig("secular")
    calls = {"plain claim": ("POST", "/verify", {"seal": "0"}, {"claim": "2 + 2 = 4"}),
             "audit": ("POST", "/audit", {"seal": "0"}, {"text": "The sum is 2 + 2 = 4, and 3 * 3 = 10."}),
             "ask a claim": ("POST", "/ask", {}, {"text": "is 17 prime?"}),
             "ask a sum": ("POST", "/ask", {}, {"text": "what is 15 percent of 240"})}
    answers = {}
    for name, (method, path, query, body) in calls.items():
        status, out = api.dispatch(method, path, query, body, config)
        answers[name] = {"status": status, "verdict": (out.get("verify") or {}).get("verdict") or out.get("verdict"),
                         "message": out.get("message"), "sympy": "sympy" in sys.modules}
    return answers


def wall_mode() -> None:
    """A front as the unit starts one, with the stigmergy flag on. What each read cost is its first read in this one new
    cell, what the cell touched is read back from a hook put in it before the first read, and what entered the front
    is read from sys.modules, which is the read that can say yes."""
    os.environ["CONCORDANCE_STIGMERGY"] = "1"
    _no_port()
    import lock_holder
    from concordance import cells, corpus, derivation as D
    from concordance.web import api
    assert cells.active() is None
    api.serve("127.0.0.1", 0, "secular")                        # what turns cells on, before the warm
    pool = cells.active()
    while pool.status()["idle"] < 1:                            # the warm cell is up, and it is the only one
        time.sleep(0.05)
    heavy = {lib: lib in sys.modules for lib in D._HEAVY_LIBS}
    window, D._VERIFY_TIMEOUT_S = D._VERIFY_TIMEOUT_S, 120.0    # a shed on a loaded laptop is not what this measures
    pool.call(lock_holder.audit_on, ({},), 60)
    post, _health = _api()
    verdicts, first_read_s = {}, {}
    for name, step in _one_of_each().items():
        began = time.monotonic()
        verdicts[name] = post({"steps": [step]})["verdict"]
        first_read_s[name] = round(time.monotonic() - began, 3)
    corpus._DEFAULT = corpus.Corpus(dict(SHELF_CARDS))
    verdicts["shelf"] = post({"steps": [{"id": "s", "domain": "wordcraft", "spec": {"WORD_VERIFY": RHYME}}]})["verdict"]
    routes = _routes()
    touched = pool.call(lock_holder.audit_read, ({},), 60).data
    threads = pool.call(lock_holder.threads, ({},), 60).data["threads"]
    D._VERIFY_TIMEOUT_S = window
    _say({"sympy": "sympy" in sys.modules, "heavy_after_serve": heavy, "verdicts": verdicts, "first_read_s": first_read_s,
          "routes": routes, "touched": touched, "threads": threads, "pool": pool.status()})


def library_mode() -> None:
    from concordance import cells, derivation as D
    before = cells.active()
    pair = _goldens()["real_estate"]
    out = D.verify_derivation([{"id": "a", "domain": "real_estate", "spec": {pair["packet_key"]: pair["true"]}}])
    import multiprocessing
    _say({"verdict": out["verdict"], "before": before, "after": cells.active(),
          "children": len(multiprocessing.active_children()),
          "threads": [t.name for t in threading.enumerate() if t.name.startswith("verify")]})


# ── the same readings ────────────────────────────────────────────────────────────────────────────────
def _cases():
    import benchmark as B
    cases = [(desc, "mathematics", spec, label) for label, spec, desc in B.CLAIMS]
    for domain, pair in _goldens().items():
        if pair["packet_key"] != "MATH_VERIFY":
            for side in ("true", "false"):
                cases.append((f"{domain} {side}", domain, {pair["packet_key"]: pair[side]}, side == "true"))
    return cases


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode("utf-8", "surrogatepass")).hexdigest()


def _sympy_values(value) -> int:
    """How many sympy values a verifier's data holds, at any depth."""
    if type(value).__module__.partition(".")[0] == "sympy":
        return 1
    if isinstance(value, dict):
        return sum(_sympy_values(k) + _sympy_values(v) for k, v in value.items())
    if isinstance(value, (list, tuple, set, frozenset)):
        return sum(_sympy_values(v) for v in value)
    return 0


def moat_mode(how: str) -> None:
    from concordance import cells, derivation as D
    if how == "cells":
        D.use_cells()
        pool = cells.active()
        while pool.status()["idle"] < 1:
            time.sleep(0.05)
    D._VERIFY_TIMEOUT_S = 120.0                                 # the same reads on both sides, on a loaded laptop too
    began = time.monotonic()
    rows, sympy_values = [], 0
    for desc, domain, spec, label in _cases():
        step = D.verify_step(domain, spec)
        res = D.verify_derivation([{"id": "b", "domain": domain, "spec": spec}])
        sympy_values += _sympy_values(step.get("data"))
        rows.append([desc, label, res["verdict"], step["status"], sorted(step), _digest(step), _digest(res)])
    pool = cells.active()
    _say({"rows": rows, "sympy": "sympy" in sys.modules, "sympy_values": sympy_values, "secs": time.monotonic() - began,
          "pool": pool.status() if pool else None})


def stub_mode() -> None:
    """The environment names a stub data directory, so a forkserver and a cell see what this process sees."""
    from concordance import cells, derivation as D
    stub_data(os.environ["CONCORDANCE_DATA_DIR"])
    reads = {name: (domain, spec) for name, (domain, spec) in STUB_READS.items()}
    here = {name: D.verify_step(domain, spec) for name, (domain, spec) in reads.items()}
    pool = cells.enable(1, preload=("concordance.derivation", "concordance.strongs", "concordance.thesaurus",
                                    "concordance.verifiers.linguistics", "concordance.verifiers.scripture",
                                    "concordance.verifiers.spec"))
    there = {name: D.verify_step(domain, spec) for name, (domain, spec) in reads.items()}
    _say({"here": here, "there": there, "pool": pool.status()})


def keeper_mode() -> None:
    """A fast keeper, and nothing here configures logging, as the service does not. The test reads stderr."""
    from concordance import cells
    cells.enable(1, preload=("lock_holder",), say_s=0.05)
    time.sleep(0.5)
    print("-- loading --", file=sys.stderr, flush=True)
    import sympy  # noqa: F401
    time.sleep(0.5)
    cells.disable()
    _say({"sympy": "sympy" in sys.modules})


# ── memory ───────────────────────────────────────────────────────────────────────────────────────────
def _held_kb(pid: int) -> dict:
    """RSS and PSS now, where a page shared with others counts by its share in PSS, and the peak RSS of its life."""
    held = {}
    with open(f"/proc/{pid}/smaps_rollup", encoding="ascii") as fh:
        for line in fh:
            if line.startswith(("Rss:", "Pss:")):
                held[line[:3].lower() + "_kb"] = int(line.split()[1])
    with open(f"/proc/{pid}/status", encoding="ascii") as fh:
        held["peak_rss_kb"] = next(int(ln.split()[1]) for ln in fh if ln.startswith("VmHWM:"))
    return held


def memory_mode() -> None:
    from multiprocessing import forkserver
    from concordance import cells, derivation as D
    size = 4
    pool = cells.enable(size, preload=D.cell_preload(), reads=10 ** 9)
    D._VERIFY_TIMEOUT_S = 120.0
    cases = _cases()
    gate = threading.Barrier(size)

    def read(n: int) -> None:
        gate.wait()
        for _desc, domain, spec, _label in cases[n::size]:
            D.verify_step(domain, spec)

    readers = [threading.Thread(target=read, args=(n,)) for n in range(size)]
    for r in readers:
        r.start()
    for r in readers:
        r.join()
    cells_held = {pid: _held_kb(pid) for pid in pool.status()["pids"]}
    _say({"forkserver": _held_kb(forkserver._forkserver._forkserver_pid), "cells": list(cells_held.values()),
          "front": _held_kb(os.getpid()), "reads": len(cases), "pool": pool.status()})


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "moat":
        moat_mode(sys.argv[2])
    else:
        {"thread": thread_mode, "cells": cells_mode, "flood": flood_mode, "wall": wall_mode, "library": library_mode,
         "orphan": orphan_mode, "stub": stub_mode, "keeper": keeper_mode, "memory": memory_mode}[mode]()
