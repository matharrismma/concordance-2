"""Stand-ins for what a read can do inside a cell. No verifier reaches any of them: a test puts one under a
made-up math mode in its own process, or hands it straight to a pool, and every one takes a read's single argument.

hold() is the neutral stand-in for a read that holds Python's global lock: one plain integer power. A power of this
size is a single bytecode that runs in C from start to end without letting go of the lock, so no other thread runs
and a window kept by another thread cannot fire. It is bounded twice, by the kill of whoever runs it and by its own
size: left alone it ends by itself in tens of seconds, so nothing outlives a test for long.
"""
from __future__ import annotations

import os
import sys

from concordance.verifiers.base import VerifierResult, confirm, error

EXPONENT = 3 * 10 ** 7
PAST_THE_FLOOR = 10 ** 6        # 3 to this is over a million and a half bits: past the floor, and done in milliseconds


def hold(_params=None) -> VerifierResult:
    held = 3 ** EXPONENT
    return error("standin.hold", f"the power ended by itself ({held.bit_length()} bits); nothing killed this read")


def quick(_params=None) -> VerifierResult:
    return confirm("standin.quick", "answered")


def pid(_params=None) -> VerifierResult:
    return confirm("standin.pid", "answered", {"pid": os.getpid()})


def die(_params=None) -> VerifierResult:
    os._exit(3)


def die_at_start(*_args) -> None:
    os._exit(3)


def raises(_params=None) -> VerifierResult:
    raise ValueError("a stand-in's own words")


class _Unprintable:
    def __str__(self) -> str:
        raise RuntimeError("no string for this")


def unprintable(_params=None) -> VerifierResult:
    return confirm("standin.unprintable", "answered", {"value": _Unprintable()})


def sympy_values(_params=None) -> VerifierResult:
    import sympy
    return confirm("standin.sympy", "answered", {
        "actual": sympy.Rational(1, 3), "whole": sympy.Integer(5), "flag": sympy.true,
        "nested": [{"root": sympy.sqrt(2)}, (sympy.Symbol("x") + 1, "kept")], "plain": 2.5,
        "members": {sympy.Integer(5)}})


def sympy_key(_params=None) -> VerifierResult:
    import sympy
    return confirm("standin.sympy_key", "answered", {"by_symbol": {sympy.Symbol("x"): 1}})


def numpy_values(_params=None) -> VerifierResult:
    import numpy
    return confirm("standin.numpy", "answered", {
        "inside": numpy.bool_(True), "p": numpy.float64(0.25), "count": numpy.int64(3),
        "row": numpy.array([1.0, 2.0]), "bands": [{"inside": numpy.bool_(False), "used": numpy.float64(1.5)}]})


def stdlib_values(_params=None) -> VerifierResult:
    from decimal import Decimal
    from fractions import Fraction
    return confirm("standin.stdlib", "answered", {
        "third": Fraction(1, 3), "cost": Decimal("1.10"), "wave": 1 + 2j, "tags": {"a"}, "fixed": frozenset({1}),
        "pair": (1, "two")})


def leak(_params=None) -> VerifierResult:
    """Take the cell's filter away, so a class off the list reaches the pipe: what the front's reader is there to
    refuse. The cell is the one that goes for it."""
    import collections
    from concordance import cells
    cells._plain = lambda value: value
    return confirm("standin.leak", "answered", {"value": collections.deque([1])})


def limits(_params=None) -> VerifierResult:
    """What this cell's limits are, read from inside it. Where the platform has no `resource` module, None."""
    try:
        import resource
    except ImportError:
        return confirm("standin.limits", "answered", {"as": None, "data": None})
    return confirm("standin.limits", "answered", {"as": resource.getrlimit(resource.RLIMIT_AS),
                                                  "data": resource.getrlimit(resource.RLIMIT_DATA)})


def oom_score(_params=None) -> VerifierResult:
    with open("/proc/self/oom_score_adj", encoding="ascii") as fh:
        return confirm("standin.oom", "answered", {"oom_score_adj": fh.read().strip()})


# ── the floor and the keeping ────────────────────────────────────────────────────────────────────────
def past_the_floor(_params=None) -> VerifierResult:
    """sympy's own Integer power, by name, with no verifier and no _ensure_sympy in the way: only a floor already on
    this process's sympy can refuse it. Without one it computes, and says so."""
    import sympy
    power = sympy.Integer(3) ** sympy.Integer(PAST_THE_FLOOR)
    return confirm("standin.floor", "computed: nothing refused this power", {"bits": int(power).bit_length()})


def the_keeping_doors(_params=None) -> VerifierResult:
    """What each door to the keeping does here, read one at a time and caught past `except Exception`."""
    from concordance import corpus
    from concordance.verifiers.base import NeedsTheKeeping
    seen = {}
    for door, args in (("loaded", ()), ("default_corpus", ()), ("get_card", ("card_standin",))):
        try:
            getattr(corpus, door)(*args)
            seen[door] = "answered"
        except NeedsTheKeeping:
            seen[door] = "needs the keeping"
    return confirm("standin.doors", "read", seen)


def shelf_read(_params=None) -> VerifierResult:
    """A read that asks for the keeping as wordcraft does, behind its `except Exception`: a read that took the refusal
    for a miss would answer here, and the process that really read the shelf says who it is."""
    from concordance import corpus
    try:
        held = corpus.loaded()
    except Exception:  # noqa: BLE001 — what a shelf read does, and what must not catch the reroute
        return confirm("standin.shelf", "read as a miss", {"pid": os.getpid(), "held": None})
    return confirm("standin.shelf", "read the shelf", {"pid": os.getpid(), "held": held})


def accelerator(_params=None) -> VerifierResult:
    """What a read finds of the accelerator: None means its probe and compile are still ahead, in the read."""
    from concordance.verifiers import riemann_accel
    return confirm("standin.accelerator", "read", {"settled": riemann_accel._C is not None})


def accelerated_read(_params=None) -> VerifierResult:
    """A read that reaches the accelerator as the zero counts do, so a hook sees what its first use would touch."""
    from concordance.verifiers import riemann_accel
    return confirm("standin.accelerated", "read", {"values": len(riemann_accel.z_array([1000.0, 1001.0]))})


def bytecode(_params=None) -> VerifierResult:
    """Would an import in this read write a .pyc? A read that loads what the preload missed must still write nothing."""
    return confirm("standin.bytecode", "read", {"written": not sys.dont_write_bytecode})


# ── what a read touches ──────────────────────────────────────────────────────────────────────────────
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
WRITES = frozenset({"os.remove", "os.rename", "os.mkdir", "os.rmdir", "os.truncate", "os.link", "os.symlink", "os.chmod",
                    "os.chown", "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.move", "shutil.rmtree",
                    "tempfile.mkstemp", "tempfile.mkdtemp"})
PROCESSES = frozenset({"subprocess.Popen", "os.system", "os.exec", "os.fork", "os.forkpty", "os.posix_spawn", "os.spawn",
                       "os.startfile", "pty.spawn"})
_seen = {"writes": [], "processes": [], "data": []}


def _is_data(path: str) -> bool:
    roots = [os.environ.get(name, "").strip() for name in ("CONCORDANCE_DATA_DIR", "CONCORDANCE_STRONGS_DIR")]
    full = os.path.abspath(path)
    return any(root and full.startswith(os.path.abspath(root) + os.sep) for root in roots)


def _watch(event: str, args: tuple) -> None:
    if event == "open":
        path, mode, flags = args
        if isinstance(path, (str, bytes, os.PathLike)):
            path = os.fsdecode(path)
            if (isinstance(flags, int) and flags & WRITE_FLAGS) or (isinstance(mode, str) and set(mode) & set("wax+")):
                _seen["writes"].append(path)
            elif _is_data(path):
                _seen["data"].append(os.path.basename(path))
    elif event == "sqlite3.connect":
        _seen["data"].append(os.path.basename(str(args[0]).partition("?")[0]))
    elif event in WRITES:
        _seen["writes"].append(f"{event} {args[0]}")
    elif event in PROCESSES:
        _seen["processes"].append(f"{event} {args[0]}")


def audit_on(_params=None) -> VerifierResult:
    """Put the hook in this cell. It stays for the cell's life, so this comes after the cell has started, and every
    read from here on is watched: what a cell does at its start is allowed, and what a read does is not."""
    sys.addaudithook(_watch)
    return confirm("standin.audit", "watching")


def audit_read(_params=None) -> VerifierResult:
    return confirm("standin.audit", "read", {**{name: sorted(set(found)) for name, found in _seen.items()},
                                             "stigmergy": os.environ.get("CONCORDANCE_STIGMERGY")})


def threads(_params=None) -> VerifierResult:
    import threading
    return confirm("standin.threads", "read", {"threads": [thread.name for thread in threading.enumerate()]})


def write_a_file(path) -> VerifierResult:
    """What the hook is there to see, so the test can show it can fail."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("x")
    return confirm("standin.write", "written")


def start_a_process(_params=None) -> VerifierResult:
    import subprocess
    subprocess.run([sys.executable, "-c", "pass"], check=True)
    return confirm("standin.process", "started")
