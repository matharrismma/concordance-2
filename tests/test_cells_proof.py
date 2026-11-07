"""tools/cells_proof.sh, run here with stub systemctl, systemd-run and sudo on PATH, against a stub tree. What it does on the
box is the lead's to run, on the owner's word. What it promises is pinned here: the hash it prints is harness.diff_hash of
the unpacked bytes, printed before any test and with no git; the tests run under the unit's hardening at nice 19 with a
limit; nothing it prints names a path; the directory goes, whatever the tests did; and an engine that moved is said."""
from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "cells_proof.sh"
sys.path.insert(0, str(ROOT / "tools"))

import harness  # noqa: E402

PATHS = ["src/one.py", "tests/test_cells.py"]
GREEN = "def test_a_stand_in():\n    print('CELL DATA FILES []')\n"
RED = "def test_a_stand_in():\n    assert False\n"
SYSTEMCTL = r"""#!/bin/sh
# systemctl show -p NAME --value UNIT
name=$3 unit=$5
echo "$unit $name" >> "$STUB_LOG.systemctl"
case "$name" in
    User) echo engine-user ;;
    MainPID) cat "$STUB_LOG.pid" ;;
    NRestarts) echo 0 ;;
    ProtectSystem) echo strict ;;
    NoNewPrivileges) echo yes ;;
    PrivateTmp) echo yes ;;
    *) echo "" ;;
esac
"""
SYSTEMD_RUN = r"""#!/bin/sh
printf '%s\n' "$@" > "$STUB_LOG.run"
for arg in "$@"; do
    case "$arg" in --working-directory=*) cd "${arg#--working-directory=}" ;; esac
done
while [ "$1" != "--" ]; do shift; done
shift
[ -z "${STUB_MOVES:-}" ] || echo 2 > "$STUB_LOG.pid"
"$@"
"""
SUDO = '#!/bin/sh\nexec "$@"\n'
CHOWN = "#!/bin/sh\nexit 0\n"
GIT = '#!/bin/sh\necho "$*" >> "$STUB_LOG.git"\nexit 1\n'


def a_shell() -> str:
    """A POSIX sh. On Windows the gate's PATH may not hold Git's, and System32's bash is no shell without WSL."""
    for found in (shutil.which("sh"), r"C:\Program Files\Git\bin\sh.exe"):
        if found and Path(found).exists() and "system32" not in found.lower():
            return found
    pytest.fail("no sh here")


def stub_tree(test_body: str) -> tuple:
    """A tar of a tree, and the bytes of each path, the way the checkout would hold them: one with a carriage return, so
    a route that changed line endings would change the hash."""
    files = {"src/one.py": b"one = 1\r\n", "tests/test_cells.py": test_body.encode(), "tools/harness.py": (ROOT / "tools" / "harness.py").read_bytes()}
    held = io.BytesIO()
    with tarfile.open(fileobj=held, mode="w") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return held.getvalue(), files


def run(tmp_path: Path, test_body: str = GREEN, env=None) -> tuple:
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    for name, body in (("systemctl", SYSTEMCTL), ("systemd-run", SYSTEMD_RUN), ("sudo", SUDO), ("chown", CHOWN), ("git", GIT)):
        (stubs / name).write_bytes(body.encode())
        (stubs / name).chmod(0o755)
    tar, _files = stub_tree(test_body)
    (tmp_path / "tree.tar").write_bytes(tar)
    (tmp_path / "paths.txt").write_text("\n".join(PATHS) + "\n", encoding="utf-8")
    base = tmp_path / "base"
    base.mkdir()
    log = (tmp_path / "log").as_posix()
    Path(log + ".pid").write_text("1\n", encoding="ascii")
    wrapper = ('case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) STUBS=$(cygpath -u "$STUBS") ;; esac; '
               'PATH="$STUBS:$PATH"; export PATH; exec sh "$0" "$@"')
    done = subprocess.run(
        [a_shell(), "-c", wrapper, SCRIPT.as_posix(), "--tree", (tmp_path / "tree.tar").as_posix(),
         "--paths", (tmp_path / "paths.txt").as_posix(), "--python", Path(sys.executable).as_posix(), "--base", base.as_posix()],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
        env={**os.environ, "STUBS": stubs.as_posix(), "STUB_LOG": log, **(env or {})})
    return done, log, base


def lines_of(path: str) -> list:
    return Path(path).read_text(encoding="utf-8").splitlines()


def test_it_prints_the_hash_of_the_unpacked_bytes_before_any_test_and_with_no_git(tmp_path):
    done, log, _base = run(tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert not Path(log + ".git").exists()              # nothing here asked for git
    stub = tmp_path / "expected"
    _tar, files = stub_tree(GREEN)
    for name, data in files.items():
        (stub / name).parent.mkdir(parents=True, exist_ok=True)
        (stub / name).write_bytes(data)
    want = harness.diff_hash(str(stub), "", PATHS)
    assert f"PROOF diff_hash {want}\n" in done.stdout
    assert done.stdout.index("PROOF diff_hash") < done.stdout.index("test session starts")
    assert re.search(r"PROOF python Python \d", done.stdout)


def test_it_runs_only_the_cell_tests_under_the_units_hardening_and_its_limits(tmp_path):
    done, log, _base = run(tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    args = lines_of(log + ".run")
    held = [args[i + 1] for i, arg in enumerate(args) if arg == "-p"]
    assert {"Nice=19", "PrivateNetwork=yes", "RuntimeMaxSec=1800", "MemoryMax=3G", "OOMScoreAdjust=1000"} <= set(held)
    assert {"ProtectSystem=strict", "NoNewPrivileges=yes", "PrivateTmp=yes"} <= set(held)     # read from the unit
    assert "--uid=engine-user" in args and "--wait" in args and "--pipe" in args
    assert args[args.index("--") + 2:args.index("--") + 4] == ["-m", "pytest"]
    assert args[-1] == "tests/test_cells.py" and "tests/test_cells_proof.py" not in args
    assert "tests/test_cells.py::test_a_stand_in PASSED" in done.stdout


def test_what_it_prints_names_no_path_and_the_directory_is_gone(tmp_path):
    done, log, base = run(tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "PROOF removed" in done.stdout and "PROOF engines unchanged" in done.stdout and "PROOF green" in done.stdout
    assert list(base.iterdir()) == []
    named = [arg.split("=", 1)[-1] for arg in lines_of(log + ".run") if "--working-directory=" in arg]
    assert named and not Path(named[0]).exists()
    assert base.as_posix() not in done.stdout and str(base) not in done.stdout
    assert Path(sys.executable).as_posix() not in done.stdout and "rootdir: <tree>" in done.stdout


def test_a_red_test_reads_red_and_the_directory_still_goes(tmp_path):
    done, _log, base = run(tmp_path, RED)
    assert done.returncode == 1
    assert "PROOF RED" in done.stdout and "PROOF removed" in done.stdout and "FAILED" in done.stdout
    assert list(base.iterdir()) == []


def test_an_engine_that_moved_is_said_and_refuses_the_proof(tmp_path):
    done, _log, base = run(tmp_path, env={"STUB_MOVES": "1"})
    assert done.returncode == 2
    assert "PROOF AN ENGINE MOVED" in done.stdout and "PROOF green" not in done.stdout
    assert list(base.iterdir()) == []


def test_it_refuses_to_run_without_what_it_needs(tmp_path):
    done = subprocess.run([a_shell(), SCRIPT.as_posix(), "--tree", "nothing"], capture_output=True, text=True, timeout=60)
    assert done.returncode == 64 and "usage" in done.stderr


def test_the_script_names_no_box_path():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "\r" not in text                             # a carriage return would break it on the box
    assert not re.search(r"/home/|/srv/|/etc/|/var/|/opt/|/root/|\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", text)
