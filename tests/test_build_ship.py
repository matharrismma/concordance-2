"""tools/build_ship.sh and the lines tools/deploy.sh hands it with (run 2026-11-11-box-build), run here with logging
stand-ins for ssh, scp, tar, python and python3 first on PATH, against a stand-in box: a temporary directory.

The stand-ins record every call and refuse to run anything. ssh never connects and never runs the command it is given;
scp copies the one file named between this machine and the stand-in box, as the transfer would, and refuses any other
host; tar and python refuse outright. Where the box would run the unit, the test runs it, the real file the stand-in
scp put on the stand-in box, so the poll and the result are the unit's own. The host is one no resolver answers, the
key a file that does not exist and HOME a temporary directory, so a call that slipped past the stand-ins could reach
nothing; and every test asserts that tar and python were never called and that each ssh and scp call named the
stand-in host. tools/deploy.sh is held to its base (85c3dda) by a fixture of per-line digests, never its lines: the
base names the box at lines 23-25.

NOTHING HERE WAITS ON A CLOCK that load can run out (checker-101, run 2026-11-11-box-build line 24). A wait is for a
state: the start call in the ssh stand-in's log, the unit's own result, the script's exit, each with a generous bound
that only a broken run reaches. Only the test of a timeout uses a short poll, since the timeout is what it shows. A
stand-in writes each call as one record and a reader takes only the records that are whole, so a log read while the
script runs never holds half a call (a torn read, measured while looking for the red at line 22, raised IndexError in
Laptop.sent()). Every test runs inside `telling()`, so a
failure carries the script's output, every stand-in's log, the unit's output and the stand-in box's builds."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHIP = ROOT / "tools" / "build_ship.sh"
DEPLOY = ROOT / "tools" / "deploy.sh"
UNIT = ROOT / "tools" / "box_build.py"
LISTING = ROOT / "tools" / "box_builds.txt"
PINS = ROOT / "src" / "concordance" / "build_pins.json"
PROBE = ROOT / "tests" / "fixtures" / "box_build_probe.py"
BASE_DIGESTS = ROOT / "tests" / "fixtures" / "deploy_sh_85c3dda.sha256"
HOST = "nobody@standin.invalid"
KEY = "/standin/no-such-key"
DEST = "/standin/dest"
SEP = "\x1f"
GENEROUS = 600                          # seconds: a bound only a broken run reaches, never a loaded laptop

# The stand-ins. Each logs a call as one record, its arguments each ended by \x1f and the record by a newline, in one
# write, so that a reader never meets half an argument list.
LOG = ('us=$(printf \'\\037\'); rec=; for a in "$@"; do rec="$rec$a$us"; done\n'
       'printf \'%s\\n\' "$rec" >> "$STUB_DIR/${0##*/}.log"\n')
SSH = ("#!/bin/sh\n# ssh's stand-in: it records the call and its stdin, never connects and never runs its command. Its exit\n"
       "# is the test's: STUB_DIR/ssh.N.rc for the Nth call, else 0.\n" + LOG +
       'n=$(( $(cat "$STUB_DIR/ssh.count" 2>/dev/null || echo 0) + 1 ))\n'
       'echo "$n" > "$STUB_DIR/ssh.count"\n'
       'cat > "$STUB_DIR/ssh.$n.stdin"\n'
       'exit "$(cat "$STUB_DIR/ssh.$n.rc" 2>/dev/null || echo 0)"\n')
SCP = ("#!/bin/sh\n# scp's stand-in: it records the call and copies the one file named between here and the stand-in box,\n"
       "# as the transfer would. It never connects and runs nothing; any other host is refused.\n" + LOG +
       r'''src= dst=
while [ "$#" -gt 0 ]; do
    case "$1" in
        -i|-o|-P|-F|-J|-l|-S|-c) shift 2 ;;
        -*) shift ;;
        *) if [ -z "$src" ]; then src=$1; else dst=$1; fi; shift ;;
    esac
done
for side in src dst; do
    eval "p=\$$side"
    case "$p" in
        "$STANDIN_REMOTE"*) p="$STANDIN_BOX/${p#"$STANDIN_REMOTE"}" ;;
        *@*:*|*:/*) echo "scp stand-in: not the stand-in box: $p" >&2; exit 98 ;;
    esac
    eval "$side=\$p"
done
[ -f "$src" ] || exit 1
mkdir -p "$(dirname "$dst")"
cp "$src" "$dst"
''')
REFUSE = "#!/bin/sh\n# a stand-in that runs nothing: this path never needs it\n" + LOG + "exit 97\n"
STUBS = {"ssh": SSH, "scp": SCP, "tar": REFUSE, "python": REFUSE, "python3": REFUSE}

# Runs a script with the stand-ins first on PATH, under dash where there is one (the box's /bin/sh is dash; Git Bash's
# sh is bash). On Windows the paths the stand-ins use are turned into the shell's own. PRELUDE and ARGS are filled in
# per run: ARGS is "$@" unless a test builds its arguments inside the shell.
WRAPPER = ('case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) STUBS=$(cygpath -u "$STUBS"); STUB_DIR=$(cygpath -u "$STUB_DIR"); '
           'STANDIN_BOX=$(cygpath -u "$STANDIN_BOX") ;; esac; export STUB_DIR STANDIN_BOX; '
           'PATH="$STUBS:$PATH"; export PATH; PRELUDE'
           'if command -v dash >/dev/null; then exec dash "$0" ARGS; fi; exec sh "$0" ARGS')

# The lines tools/deploy.sh gains after line 26, exactly: nothing else may run before its base lines do. A DELIBERATE
# CONTRACT CHANGE of run 2026-11-13-stick-ship, step path (its plan, ledger line 8): the block gains exactly the mint
# path's nine lines after the build path's, in their place, and the length assertion follows; every other assertion is
# unchanged. tests/test_mint_ship.py holds every line of f6a1d1d, the base with the build block, unchanged and in order.
NEW_BLOCK = [
    "# THE BUILD PATH (run 2026-11-11-box-build): `--build <name>` and `--build-verify <name>` never reach the lines below.",
    "# They go whole to tools/build_ship.sh, handed the box in its environment so that no other file names it. A deploy",
    "# without them runs exactly as before.",
    'case "${1:-}" in',
    "    --build|--build-verify)",
    "        BUILD_HOST=$HOST BUILD_KEY=$KEY BUILD_DEST=$DEST",
    "        export BUILD_HOST BUILD_KEY BUILD_DEST",
    '        exec sh "$REPO/tools/build_ship.sh" "$@" ;;',
    "esac",
    "# THE MINT PATH (run 2026-11-13-stick-ship): `--mint <name>`, `--mint-check <name>` and `--mint-retract <name>` never",
    "# reach the lines below. They go whole to tools/mint_ship.sh, handed the box in its environment so that no other file",
    "# names it. A deploy without them runs exactly as before.",
    'case "${1:-}" in',
    "    --mint|--mint-check|--mint-retract)",
    "        MINT_HOST=$HOST MINT_KEY=$KEY MINT_DEST=$DEST",
    "        export MINT_HOST MINT_KEY MINT_DEST",
    '        exec sh "$REPO/tools/mint_ship.sh" "$@" ;;',
    "esac",
]


def a_shell() -> str:
    """A POSIX sh. On Windows the gate's PATH may not hold Git's, and System32's bash is no shell without WSL."""
    for found in (shutil.which("sh"), r"C:\Program Files\Git\bin\sh.exe"):
        if found and Path(found).exists() and "system32" not in found.lower():
            return found
    pytest.fail("no sh here")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bb():
    return _load("box_build_for_ship", UNIT)


@pytest.fixture(scope="module")
def probe():
    return _load("box_build_probe_for_ship", PROBE)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else "(none)"


class Laptop:
    """The stand-ins first on PATH, the stand-in box, and everything each stand-in was asked."""

    def __init__(self, tmp_path: Path, repo: Path = ROOT):
        self.tmp, self.repo = tmp_path, repo
        self.stubs, self.logs, self.box = tmp_path / "stubs", tmp_path / "logs", tmp_path / "box"
        self.home, self.scratch = tmp_path / "home", tmp_path / "scratch"
        self.out, self.err = tmp_path / "out.txt", tmp_path / "err.txt"
        self.procs: list = []
        self.box_runs: list = []
        for d in (self.stubs, self.logs, self.box / "tools", self.box / "data", self.home, self.scratch):
            d.mkdir(parents=True)
        for name, body in STUBS.items():
            (self.stubs / name).write_bytes(body.encode())
            (self.stubs / name).chmod(0o755)
        self.meminfo = tmp_path / "meminfo"
        self.meminfo.write_bytes(b"MemAvailable:   8388608 kB\n")

    def env(self, **extra) -> dict:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("BUILD_", "STUB", "STANDIN"))}
        env.pop("DEPLOY_NO_GATE", None)
        env.update(BUILD_HOST=HOST, BUILD_KEY=KEY, BUILD_DEST=DEST, BUILD_POLL_SECONDS=str(GENEROUS),
                   BUILD_POLL_INTERVAL="1", STUBS=self.stubs.as_posix(), STUB_DIR=self.logs.as_posix(),
                   STANDIN_BOX=self.box.as_posix(), STANDIN_REMOTE=f"{HOST}:{DEST}/", HOME=self.home.as_posix())
        env.update(extra)
        return {k: v for k, v in env.items() if v is not None}

    def start(self, args, script: Path = None, prelude: str = "", inner: str = '"$@"', **extra) -> subprocess.Popen:
        script = script or self.repo / "tools" / "build_ship.sh"
        wrapper = WRAPPER.replace("PRELUDE", prelude).replace("ARGS", inner)
        with open(self.out, "wb") as out, open(self.err, "wb") as err:
            proc = subprocess.Popen([a_shell(), "-c", wrapper, script.as_posix(), *args], stdin=subprocess.DEVNULL,
                                    stdout=out, stderr=err, env=self.env(**extra))
        self.procs.append(proc)
        return proc

    def finish(self, proc: subprocess.Popen, timeout: int = GENEROUS + 300):
        rc = proc.wait(timeout=timeout)
        return rc, _text(self.out), _text(self.err)

    def run(self, args, script: Path = None, **extra):
        return self.finish(self.start(args, script, **extra))

    def calls(self, tool: str) -> list:
        """Every whole call a stand-in has recorded; one it is still writing is not a call yet."""
        log = self.logs / f"{tool}.log"
        if not log.exists():
            return []
        text = log.read_text(encoding="utf-8")
        return [line.split(SEP)[:-1] for line in text[:text.rfind("\n") + 1].splitlines()]

    def story(self) -> str:
        """Everything a failure needs to be read: the script's output, each stand-in's log, what the box ran, and the
        stand-in box's builds and results."""
        parts = [f"--- build_ship.sh stdout\n{_text(self.out)}", f"--- build_ship.sh stderr\n{_text(self.err)}"]
        for tool in STUBS:
            log = self.logs / f"{tool}.log"
            if log.exists():
                parts.append(f"--- the {tool} stand-in's log\n" + _text(log).replace(SEP, " | "))
        for cmd, done in self.box_runs:
            parts.append(f"--- the box ran {cmd}\nexit {done.returncode}\n{done.stdout}\n{done.stderr}")
        builds = self.box / "data" / "builds"
        if builds.exists():
            parts.append("--- the stand-in box's data/builds\n" + "\n".join(
                p.relative_to(self.box).as_posix() for p in sorted(builds.rglob("*"))))
            for result in sorted((builds / ".results").glob("*.json")):
                parts.append(f"--- {result.name}\n{_text(result)}")
        return "\n".join(parts)

    @contextlib.contextmanager
    def telling(self):
        """Run a test's body so that any failure in it carries the story, and no script it started outlives it."""
        try:
            yield self
        except Exception as e:
            raise AssertionError(f"{type(e).__name__}: {e}\n\n{self.story()}") from e
        finally:
            for proc in self.procs:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=60)

    def nothing_got_past(self) -> None:
        """No call went anywhere but to the stand-ins, and those that reach a box named the stand-in host."""
        assert self.calls("tar") == [] and self.calls("python") == [] and self.calls("python3") == []
        for call in self.calls("ssh"):
            assert call[:5] == ["-i", KEY, "-o", "ConnectTimeout=10", HOST], call
        for call in self.calls("scp"):
            assert call[:5] == ["-q", "-i", KEY, "-o", "ConnectTimeout=10"], call
            assert sum(a.startswith(f"{HOST}:{DEST}/") for a in call[5:]) == 1, call

    def started(self, proc: subprocess.Popen):
        """Wait for the state, not a clock: the call that starts the unit on the box. Its command, run id and name."""
        began = time.time()
        while True:
            for call in reversed(self.calls("ssh")):
                m = re.search(r" build --root '" + re.escape(DEST) + r"' --run-id (\S+) (\S+) < /dev/null", call[-1])
                if m:
                    return call[-1], m.group(1), m.group(2)
            assert proc.poll() is None, "build_ship.sh ended before it started the unit"
            assert time.time() - began < GENEROUS, f"no start call in {GENEROUS}s"
            time.sleep(0.1)

    def polls(self) -> list:
        return [c for c in self.calls("scp") if c[5].startswith(f"{HOST}:")]

    def play_the_box(self, run_id: str, name: str) -> int:
        """What the box does with the start call: run the unit the stand-in scp put there, on the stand-in box, with
        stand-in readings."""
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("CONCORDANCE_")}
        env["BOXTEST_BOX_ROOT"] = str(self.box)
        cmd = [sys.executable, str(self.box / "tools" / "box_build.py"), "build", "--root", str(self.box), "--run-id",
               run_id, "--meminfo", str(self.meminfo), "--disk-free-bytes", str(100 * 1024 ** 3), "--scratch-base",
               str(self.scratch), name]
        done = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=GENEROUS)
        self.box_runs.append((" ".join(cmd[1:]), done))
        return done.returncode

    def sent(self) -> dict:
        """What each scp call sent to the box: {path under the destination: the local file}."""
        return {call[6][len(f"{HOST}:{DEST}/"):]: call[5] for call in self.calls("scp")
                if call[6].startswith(f"{HOST}:{DEST}/")}


def start_command(run_id: str, name: str) -> str:
    return (f"cd '{DEST}' && nohup setsid nice -n 19 ionice -c 2 -n 7 .venv/bin/python -I tools/box_build.py build "
            f"--root '{DEST}' --run-id {run_id} {name} < /dev/null > /dev/null 2>&1 &")


def a_repo(tmp_path: Path, listing: str, pins: dict, files: dict) -> Path:
    """A stand-in laptop checkout: the real build_ship.sh and unit, the probe, and the listing, pins and files given."""
    repo = tmp_path / "repo"
    for rel, body in {"tools/build_ship.sh": SHIP.read_bytes(), "tools/box_build.py": UNIT.read_bytes(),
                      "tools/probe.py": PROBE.read_bytes(), "tools/box_builds.txt": listing.encode(),
                      "src/concordance/build_pins.json": (json.dumps(pins, indent=2, sort_keys=True) + "\n").encode(),
                      **files}.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes(body)
    return repo


# ------------------------------------------------------------------------------------------------ the stand-ins

def test_a_log_read_while_a_call_is_written_holds_only_whole_calls(tmp_path):
    """Found while looking for the red at line 22: Laptop.sent() read the scp log while the script polled, and a read
    that met half a call indexed past its end (measured beside CPU burners). A reader now takes only whole records, and
    each stand-in writes a record in one write."""
    laptop = Laptop(tmp_path)
    with laptop.telling():
        full = SEP.join(["-q", "-i", KEY, "-o", "ConnectTimeout=10", f"{HOST}:{DEST}/x", "/tmp/x"]) + SEP
        (laptop.logs / "scp.log").write_bytes((full + "\n" + full[:20]).encode())        # a second call, half written
        assert laptop.calls("scp") == [full.split(SEP)[:-1]]
        assert laptop.sent() == {}
        assert LOG.count(">>") == 1                                                       # one write per call


# ------------------------------------------------------------------------------------------------ deploy.sh

def digests(text: str) -> list:
    return [hashlib.sha256(line.encode("utf-8")).hexdigest() for line in text.replace("\r\n", "\n").split("\n")[:-1]]


def test_deploy_sh_keeps_every_base_line_in_order_and_adds_exactly_one_block_after_the_box_lines():
    base = [line.split()[1] for line in BASE_DIGESTS.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")]
    assert len(base) == 171
    text = DEPLOY.read_text(encoding="utf-8").replace("\r\n", "\n")
    now, lines = digests(text), text.split("\n")[:-1]
    shown = "\n".join(f"{n:4} {line}" for n, line in enumerate(lines[20:40], 21))
    assert now[:26] == base[:26], shown                # lines 1-26 in place, so lines 23-25, which name the box, untouched
    assert lines[26:26 + len(NEW_BLOCK)] == NEW_BLOCK, shown                            # the new lines, exactly
    assert now[26 + len(NEW_BLOCK):] == base[26:], shown                                # every other base line, in order
    assert len(lines) == len(base) + len(NEW_BLOCK)
    assert not any(re.search(r"\w@\w", line) or "/home" in line for line in NEW_BLOCK)  # the box is named by 23-25 alone


@pytest.mark.parametrize("args,extra", [(["--build", "no-such-build"], {}), (["--build-verify", "no-such-build"], {}),
                                        (["--build", "canary"], {"DEPLOY_NO_GATE": "1"})])
def test_deploy_sh_hands_build_and_build_verify_to_build_ship(tmp_path, args, extra):
    """The real deploy.sh, refused by build_ship.sh before any call. The base (85c3dda) says 'not a file' instead."""
    laptop = Laptop(tmp_path)
    with laptop.telling():
        rc, out, err = laptop.run(args, script=DEPLOY, BUILD_HOST=None, BUILD_KEY=None, BUILD_DEST=None, **extra)
        assert rc == 2 and "build_ship: refused:" in err
        assert "not a file" not in out + err
        assert all(laptop.calls(t) == [] for t in STUBS)


def test_deploy_sh_hands_build_ship_its_own_host_key_and_destination(tmp_path):
    """A copy of deploy.sh whose box lines (23-25) name the stand-in box, and nothing else changed."""
    lines = DEPLOY.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    assert [lines[i].split("=")[0] for i in (22, 23, 24)] == ["HOST", "KEY", "DEST"]
    copy = list(lines)
    copy[22], copy[23], copy[24] = f'HOST="{HOST}"', f'KEY="{KEY}"', f'DEST="{DEST}"'
    assert [i for i in range(len(lines)) if lines[i] != copy[i]] == [22, 23, 24]
    repo = tmp_path / "repo"
    for rel in ("tools/build_ship.sh", "tools/box_build.py", "tools/box_builds.txt", "tools/build_canary.py",
                "src/concordance/build_pins.json"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes((ROOT / rel).read_bytes())
    (repo / "tools" / "deploy.sh").write_bytes("\n".join(copy).encode())
    laptop = Laptop(tmp_path, repo)
    with laptop.telling():
        rc, out, err = laptop.run(["--build-verify", "canary"], script=repo / "tools" / "deploy.sh",
                                  BUILD_HOST=None, BUILD_KEY=None, BUILD_DEST=None)
        pin = json.loads(PINS.read_text(encoding="utf-8"))["canary"]
        assert rc == 0
        assert laptop.calls("ssh") == [["-i", KEY, "-o", "ConnectTimeout=10", HOST,
                                        f"cd '{DEST}' && .venv/bin/python -I - verify --root '{DEST}' canary {pin}"]]
        laptop.nothing_got_past()


# ------------------------------------------------------------------------------------------------ refusals

@pytest.mark.parametrize("args,extra,why", [
    (["--build", "no-such-build"], {}, "not a listed name"),
    (["--build", "tools/build_canary.py"], {}, "never a path"),
    (["--build", "canary", "fail"], {}, "not a switch"),
    (["--build", "canary", "--arg", "fail"], {}, "not a switch"),
    (["--build"], {}, "usage"),
    (["canary"], {}, "usage"),
    (["--build", "canary evil"], {}, "never a path or a free argument"),
    (["--build", "canary;evil"], {}, "never a path or a free argument"),
    (["--build", "canary"], {"DEPLOY_NO_GATE": "1"}, "DEPLOY_NO_GATE"),
    (["--build", "canary"], {"BUILD_HOST": None}, "named only by tools/deploy.sh"),
    (["--build", "canary"], {"BUILD_DEST": "relative/dest"}, "not an absolute path"),
    (["--build", "canary"], {"BUILD_POLL_SECONDS": "2701"}, "at most 2700 seconds"),
    (["--build-verify", "no-such-build"], {}, "not a listed name"),
    (["--build", "canary", "--build", "no-such-build"], {}, "not a listed name"),
])
def test_build_ship_refuses_before_any_call(tmp_path, args, extra, why):
    laptop = Laptop(tmp_path)
    with laptop.telling():
        rc, out, err = laptop.run(args, **extra)
        assert rc == 2 and "build_ship: refused:" in err and why in err
        assert all(laptop.calls(t) == [] for t in STUBS)


@pytest.mark.parametrize("prelude,name", [
    ("nl=$(printf 'canary\\nevil'); ", "a newline inside it"),
    ("nl=$(printf 'canary\\nx'); nl=${nl%x}; ", "a newline at its end"),
])
def test_a_name_holding_a_newline_is_refused_before_any_call(tmp_path, prelude, name):
    """Built inside the shell: a Windows argument list splits a newline into two words before any script sees it."""
    laptop = Laptop(tmp_path)
    with laptop.telling():
        rc, out, err = laptop.finish(laptop.start([], prelude=prelude, inner='--build "$nl"'))
        assert rc == 2 and "build_ship: refused: not a listed name (a name, never a path or a free argument)" in err, name
        assert all(laptop.calls(t) == [] for t in STUBS)


def test_build_ship_reaches_the_box_only_through_ssh_and_scp_by_name():
    text = SHIP.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert "verify_deploy" not in code and "command -p" not in code and "env -i" not in code
    assert not re.search(r"/(ssh|scp|tar)\b", code)
    assert re.findall(r"\S*python\S*", code) == [".venv/bin/python", ".venv/bin/python"]   # only in the box's commands


# ------------------------------------------------------------------------------------------------ a build

def test_an_accepted_name_sends_exactly_the_listing_the_unit_and_its_tool(tmp_path, bb):
    laptop = Laptop(tmp_path)
    with laptop.telling():
        proc = laptop.start(["--build", "canary"])
        command, run_id, name = laptop.started(proc)
        assert (command, name) == (start_command(run_id, "canary"), "canary")
        assert laptop.play_the_box(run_id, name) == 0
        rc, out, err = laptop.finish(proc)
        listed = bb.parse_listing(LISTING.read_text(encoding="utf-8"))["canary"].hash
        assert rc == 0
        assert laptop.sent() == {p: p for p in ("tools/box_builds.txt", "tools/box_build.py", "tools/build_canary.py")}
        for p in laptop.sent():
            assert (laptop.box / p).read_bytes() == (ROOT / p).read_bytes()
        assert [c[-1] for c in laptop.calls("ssh")] == [command]               # no staging: the canary has no inputs
        polls = laptop.polls()
        assert polls and {c[5] for c in polls} == {f"{HOST}:{DEST}/data/builds/.results/{run_id}.json"}
        assert f'"dir": "data/builds/canary/{listed}"' in out and "-- build canary: done" in out
        assert (laptop.box / "data" / "builds" / "canary" / listed / "canary.txt").is_file()
        laptop.nothing_got_past()


STALE = {"dir": "data/builds/canary/" + "a" * 64, "name": "canary", "run_id": "20200101T000000Z-aaaaaaaaaaaa",
         "status": "built"}


def stale_result() -> bytes:
    return (json.dumps(STALE, indent=1, sort_keys=True) + "\n").encode()


def test_a_timeout_exits_non_zero_says_so_and_a_stale_result_of_the_same_name_is_never_read(tmp_path):
    """The one short poll here: the timeout is what this test shows, so load can only make it come later."""
    laptop = Laptop(tmp_path)
    with laptop.telling():
        results = laptop.box / "data" / "builds" / ".results"
        results.mkdir(parents=True)
        (results / f"{STALE['run_id']}.json").write_bytes(stale_result())   # already present when the build starts
        proc = laptop.start(["--build", "canary"], BUILD_POLL_SECONDS="3")
        _command, run_id, _name = laptop.started(proc)
        rc, out, err = laptop.finish(proc)
        assert rc == 1 and f"no result for run {run_id} within 3s" in err and "Nothing the site serves has changed" in err
        assert "done" not in out
        assert {c[5] for c in laptop.polls()} == {f"{HOST}:{DEST}/data/builds/.results/{run_id}.json"}
        laptop.nothing_got_past()


def test_a_result_at_its_path_that_holds_another_run_id_is_never_accepted(tmp_path):
    laptop = Laptop(tmp_path)
    with laptop.telling():
        proc = laptop.start(["--build", "canary"])
        _command, run_id, name = laptop.started(proc)
        results = laptop.box / "data" / "builds" / ".results"
        results.mkdir(parents=True, exist_ok=True)
        (results / f"{run_id}.json").write_bytes(stale_result())          # at this run's path, but not this run's
        seen = len(laptop.polls())
        began = time.time()
        while len(laptop.polls()) < seen + 2:                              # two whole polls that read it
            assert proc.poll() is None, "build_ship.sh took a result that is not this run's"
            assert time.time() - began < GENEROUS, "no poll read the stale result"
            time.sleep(0.1)
        assert laptop.play_the_box(run_id, name) == 0                      # now the unit writes this run's own
        rc, out, err = laptop.finish(proc)
        assert rc == 0 and f'"run_id": "{run_id}"' in out and STALE["run_id"] not in out
        laptop.nothing_got_past()


def test_a_failed_build_exits_non_zero_says_so_and_leaves_nothing(tmp_path):
    laptop = Laptop(tmp_path)
    with laptop.telling():
        proc = laptop.start(["--build", "canary-fail"])
        _command, run_id, name = laptop.started(proc)
        assert laptop.play_the_box(run_id, name) == 1
        rc, out, err = laptop.finish(proc)
        assert rc == 1 and f"build canary-fail failed (run {run_id})" in err
        assert '"reason": "the tool exited 1"' in out
        builds = laptop.box / "data" / "builds"
        assert not (builds / "canary-fail").exists() and list((builds / ".tmp").iterdir()) == []
        laptop.nothing_got_past()


INPUTS = {"src/concordance/table.json": b'{"author": "Augustine"}\n', "site/page.html": b"<p>the laptop's</p>\n",
          "tools/notes.txt": b"notes\n"}
ON_THE_BOX = {"src/concordance/table.json": b'{"served": true}\n', "site/page.html": b"<p>served</p>\n",
              "tools/notes.txt": b"the box's notes\n"}


def test_inputs_land_only_in_the_staging_directory_and_the_tool_sees_them_read_only(tmp_path, bb, probe):
    report = tmp_path / "expected"
    report.mkdir()
    (report / "report.json").write_bytes(probe.expected_report(INPUTS))
    digest = bb.content_hash(report)
    ins = " ".join(f"in={p}" for p in sorted(INPUTS))
    listing = f'# probe: what a tool sees of three inputs outside data/, from tools/probe.py\nprobe tools/probe.py {digest} 128 {ins} "probe"\n'
    repo = a_repo(tmp_path, listing, {"probe": digest}, INPUTS)
    laptop = Laptop(tmp_path, repo)
    with laptop.telling():
        for rel, body in ON_THE_BOX.items():                               # what the site serves from those paths
            (laptop.box / rel).parent.mkdir(parents=True, exist_ok=True)
            (laptop.box / rel).write_bytes(body)
        proc = laptop.start(["--build", "probe"])
        command, run_id, name = laptop.started(proc)
        stage = f"data/builds/.inputs/{run_id}"
        assert laptop.sent() == {"tools/box_builds.txt": "tools/box_builds.txt", "tools/box_build.py": "tools/box_build.py",
                                 "tools/probe.py": "tools/probe.py", **{f"{stage}/{p}": p for p in INPUTS}}
        mkdir = [c[-1] for c in laptop.calls("ssh")][0]
        assert mkdir == "mkdir -p " + " ".join(f"'{DEST}/{stage}/{d}'" for d in ("site", "src/concordance", "tools"))
        for rel, body in INPUTS.items():
            assert (laptop.box / stage / rel).read_bytes() == body         # staged, at its repository path inside
            assert (laptop.box / rel).read_bytes() == ON_THE_BOX[rel]      # and the file at that path, unchanged
        assert laptop.play_the_box(run_id, name) == 0
        rc, out, err = laptop.finish(proc)
        assert rc == 0
        landed = laptop.box / "data" / "builds" / "probe" / digest / "report.json"
        assert landed.read_bytes() == probe.expected_report(INPUTS)        # read-only inputs, those three and no other
        assert not (laptop.box / stage).exists()                           # the staging directory, gone after the build
        assert '"cleanup"' not in out                                      # and nothing the unit could not remove
        for rel, body in ON_THE_BOX.items():
            assert (laptop.box / rel).read_bytes() == body
        laptop.nothing_got_past()


@pytest.mark.parametrize("path,why", [("data/x.json", "an input under data/ is refused"),
                                      ("tools/../data/x.json", "holds '.', '..'"),
                                      ("/etc/x.json", "absolute path")])
def test_an_input_under_data_or_outside_the_repository_is_refused_before_any_call(tmp_path, path, why):
    listing = f'# bad: a test entry\nbad tools/probe.py {"a" * 64} 128 in={path} "fixed"\n'
    repo = a_repo(tmp_path, listing, {}, {"data/x.json": b"{}\n"})
    laptop = Laptop(tmp_path, repo)
    with laptop.telling():
        rc, out, err = laptop.run(["--build", "bad"])
        assert rc == 2 and why in err
        assert all(laptop.calls(t) == [] for t in STUBS)


@pytest.mark.parametrize("on_the_box", ["absent", "altered", "built"])
def test_build_verify_reads_the_laptops_pin_and_fails_for_an_absent_or_altered_build(tmp_path, bb, probe, on_the_box):
    fixed = tmp_path / "fixed"
    fixed.mkdir()
    (fixed / "fixed.txt").write_bytes(probe.FIXED)
    laptops_pin = bb.content_hash(fixed)
    listing = f'# fixed: one fixed file, from tools/probe.py\nfixed tools/probe.py {laptops_pin} 128 "fixed"\n'
    repo = a_repo(tmp_path, listing, {"fixed": laptops_pin}, {})
    laptop = Laptop(tmp_path, repo)
    with laptop.telling():
        boxes_pin = "b" * 64                                               # the box's own pins file names another hash
        (laptop.box / "src" / "concordance").mkdir(parents=True)
        (laptop.box / "src" / "concordance" / "build_pins.json").write_bytes(
            (json.dumps({"fixed": boxes_pin}, indent=2) + "\n").encode())
        built = laptop.box / "data" / "builds" / "fixed"
        (built / boxes_pin).mkdir(parents=True)
        (built / boxes_pin / "fixed.txt").write_bytes(b"what the box's pin names\n")
        if on_the_box != "absent":
            (built / laptops_pin).mkdir()
            (built / laptops_pin / "fixed.txt").write_bytes(probe.FIXED if on_the_box == "built" else b"altered\n")
        sent = (repo / "tools" / "box_build.py").read_bytes().replace(b"\r", b"")
        verdict = subprocess.run([sys.executable, "-I", "-", "verify", "--root", str(laptop.box), "fixed", laptops_pin],
                                 input=sent, capture_output=True, timeout=GENEROUS)       # what the box's python answers
        assert verdict.returncode == (0 if on_the_box == "built" else 1), verdict.stdout
        (laptop.logs / "ssh.1.rc").write_bytes(str(verdict.returncode).encode())
        rc, out, err = laptop.run(["--build-verify", "fixed"])
        assert rc == verdict.returncode
        assert laptop.calls("ssh") == [["-i", KEY, "-o", "ConnectTimeout=10", HOST,
                                        f"cd '{DEST}' && .venv/bin/python -I - verify --root '{DEST}' fixed {laptops_pin}"]]
        assert (laptop.logs / "ssh.1.stdin").read_bytes() == sent          # this laptop's unit, streamed: nothing written
        assert laptop.calls("scp") == []                                   # the box's pins file is never read
        assert boxes_pin not in out + err
        if on_the_box == "built":
            assert f"verified: data/builds/fixed/{laptops_pin}" in out
        else:
            assert f"data/builds/fixed/{laptops_pin} is not on the box as pinned" in err
        laptop.nothing_got_past()
