"""A build tool for the tests of tools/box_build.py and tools/build_ship.sh: copied into a stand-in box's tools/ and
listed there, it is run by the real unit exactly as a listed tool is.

    python probe.py INPUTS OUTPUT MODE

fixed  writes fixed.txt              fail   writes partial.txt, exits 1        empty  writes nothing
hog    allocates 1 GiB, then fixed   sleep  sleeps 900 s, then fixed           wait   waits for $BOXTEST_GO, then fixed
probe  writes report.json: what it sees of its inputs, its environment, its working directory and its confinement

`expected_report` is what a probe run should write, worked out from the inputs and the platform alone, never from
what the probe saw. Stdlib only, as every build tool must be.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

FIXED = b"fixed\n"
LINUX = sys.platform.startswith("linux")


def _inside(path, folder):
    try:
        path, folder = os.path.realpath(path), os.path.realpath(folder)
        return os.path.commonpath([path, folder]) == folder
    except ValueError:                   # another drive
        return False


def observe(inputs):
    seen = []
    for dirpath, _dirs, names in os.walk(inputs):
        for name in names:
            with open(os.path.join(dirpath, name), "rb") as fh:
                rel = os.path.relpath(os.path.join(dirpath, name), inputs).replace(os.sep, "/")
                seen.append([rel, hashlib.sha256(fh.read()).hexdigest()])
    writable = []
    for rel, _digest in seen:
        try:
            with open(os.path.join(inputs, *rel.split("/")), "ab"):
                writable.append(rel)
        except PermissionError:
            pass
    dir_writable = None                  # a directory's read-only flag stops nothing on Windows
    if os.name != "nt":
        try:
            with open(os.path.join(inputs, "new.txt"), "wb"):
                dir_writable = True
        except PermissionError:
            dir_writable = False
    try:
        import concordance  # noqa: F401
        imports_concordance = True
    except ImportError:
        imports_concordance = False
    oom = None
    if os.path.exists("/proc/self/oom_score_adj"):
        with open("/proc/self/oom_score_adj") as fh:
            oom = int(fh.read())
    ionice = None
    if LINUX:
        ionice = subprocess.run(["ionice", "-p", str(os.getpid())], capture_output=True, text=True).stdout.strip()
    data = os.environ.get("CONCORDANCE_DATA_DIR", "")
    box = os.environ["BOXTEST_BOX_ROOT"]
    return {
        "concordance_env": sorted(k for k in os.environ if k.upper().startswith("CONCORDANCE_")),
        "cwd_is_empty": os.listdir(os.getcwd()) == [],
        "cwd_outside_the_box": not _inside(os.getcwd(), box),
        "data_dir_is_empty": os.path.isdir(data) and os.listdir(data) == [],
        "data_dir_outside_the_box": not _inside(data, box),
        "imports_concordance": imports_concordance,
        "inputs": sorted(seen),
        "inputs_dir_writable": dir_writable,
        "inputs_writable": writable,
        "ionice": ionice,
        "nice": os.nice(0) if hasattr(os, "nice") else None,
        "oom_score_adj": oom,
        "sys_path_outside_the_box": not any(_inside(p, box) for p in sys.path if p),
    }


def expected_report(inputs):
    """What a probe run must write, given its inputs as {repository path: bytes}."""
    report = {
        "concordance_env": ["CONCORDANCE_DATA_DIR"],
        "cwd_is_empty": True,
        "cwd_outside_the_box": True,
        "data_dir_is_empty": True,
        "data_dir_outside_the_box": True,
        "imports_concordance": False,
        "inputs": sorted([rel, hashlib.sha256(body).hexdigest()] for rel, body in inputs.items()),
        "inputs_dir_writable": None if os.name == "nt" else False,
        "inputs_writable": [],
        "ionice": "best-effort: prio 7" if LINUX else None,
        "nice": 19 if LINUX else (0 if hasattr(os, "nice") else None),
        "oom_score_adj": 1000 if LINUX else None,
        "sys_path_outside_the_box": True,
    }
    return json.dumps(report, indent=1, sort_keys=True).encode("ascii") + b"\n"


def _write(out, name, body):
    with open(os.path.join(out, name), "wb") as fh:
        fh.write(body)


def main(argv):
    inputs, out, mode = argv
    if mode == "fail":
        _write(out, "partial.txt", b"partial\n")
        return 1
    if mode == "empty":
        return 0
    if mode == "hog":
        held = bytearray(1024 * 1024 * 1024)
        held[-1] = 1
    if mode == "sleep":
        time.sleep(900)                 # far past any bound a test waits: only the unit's timeout ends it
    if mode == "wait":
        began = time.time()
        while not os.path.exists(os.environ["BOXTEST_GO"]):
            if time.time() - began > 900:
                return 5
            time.sleep(0.05)
    if mode == "probe":
        report = observe(inputs)
        _write(out, "report.json", json.dumps(report, indent=1, sort_keys=True).encode("ascii") + b"\n")
        return 0
    _write(out, "fixed.txt", FIXED)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
