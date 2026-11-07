"""deploy/nh-engine-watch and deploy/install_watch.sh, run here with stub systemctl, curl and logger on PATH, against a stub
root. What they do on the box is the lead's to run; what they promise is pinned here. The watch: a good read clears the
count, four failed reads restart the right unit, a read is bounded and a 5xx fails it, the grace holds, the two units never
share a count, and a failed restart fails the run. The install: one at a time, it snapshots what it replaces, lays each file
down whole, overwrites no drop-in, restarts neither engine, puts everything back when a read-back fails, and says so and
keeps the snapshot when it cannot. Nothing here reaches a live service: every read lands on a stub or on a socket this file
opens on 127.0.0.1, and a shell that is missing fails the test."""
from __future__ import annotations

import contextlib
import functools
import os
import re
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy"
WATCH = DEPLOY / "nh-engine-watch"
INSTALL = DEPLOY / "install_watch.sh"
WATCH_FILES = ("nh-engine-watch", "nh-engine-watch.service", "nh-engine-watch.timer")
SHELL_FILES = ("install_watch.sh",) + WATCH_FILES
ENGINES = ("nh-engine", "nh-mcp")
BOTH_WAYS = [ENGINES, ENGINES[::-1]]

UNITS = "etc/systemd/system"
INSTALLED = {"usr/local/bin/nh-engine-watch": "nh-engine-watch",
             f"{UNITS}/nh-engine-watch.service": "nh-engine-watch.service",
             f"{UNITS}/nh-engine-watch.timer": "nh-engine-watch.timer"}
DROP_INS = {unit: f"{UNITS}/{unit}.service.d/30-oom-policy.conf" for unit in ENGINES}
SNAPSHOTS = "var/lib/nh-engine-watch/snapshots"
DEFAULT_STOP_S = 90                     # systemd's DefaultTimeoutStopSec, for a unit that sets no TimeoutStopSec

# What the box holds today: the stopgap, and each engine's drop-ins, none of which may change.
THE_BOX = {
    "usr/local/bin/nh-engine-watch": "#!/bin/sh\n# the stopgap\n",
    f"{UNITS}/nh-engine-watch.service": "[Service]\nType=oneshot\n# the stopgap\n",
    f"{UNITS}/nh-engine-watch.timer": "[Timer]\nOnUnitActiveSec=30s\n# the stopgap\n",
    f"{UNITS}/nh-engine.service.d/10-no-new-privileges.conf": "[Service]\nNoNewPrivileges=yes\n",
    f"{UNITS}/nh-engine.service.d/20-contain.conf": "[Service]\nProtectHome=yes\n",
    f"{UNITS}/nh-engine.service.d/oom.conf": "[Service]\nOOMScoreAdjust=-700\n",
    f"{UNITS}/nh-mcp.service.d/10-no-new-privileges.conf": "[Service]\nNoNewPrivileges=yes\n",
    f"{UNITS}/nh-mcp.service.d/20-contain.conf": "[Service]\nProtectHome=yes\n",
}

LOGGER = '#!/bin/sh\necho "$*" >> "$STUB_DIR/logger.log"\n'
CURL = r"""#!/bin/sh
# curl URL, with its flags read as curl reads them. A unit marked down refuses the connection. One marked 5xx answers 500,
# which fails the read only under -f (--fail). One marked frozen takes the connection and never answers: under -m
# (--max-time) the read ends as curl's does when the time is up; with no bound curl would wait for ever, and this stub,
# which cannot, marks the hang instead.
fail= max=
while [ "$#" -gt 1 ]; do
    case "$1" in
        -m|--max-time) max=$2; shift ;;
        --fail) fail=1 ;;
        --*) ;;
        -*f*) fail=1 ;;
    esac
    shift
done
url=$1
echo "$url" >> "$STUB_DIR/curl.log"
echo "fail=$fail max=$max" >> "$STUB_DIR/curlflags.log"
case "$url" in
    *:8002/health) unit=nh-engine ;;
    *:8003/health) unit=nh-mcp ;;
    *) exit 6 ;;
esac
[ ! -e "$STUB_DIR/$unit.down" ] || exit 7
if [ -e "$STUB_DIR/$unit.5xx" ]; then [ -z "$fail" ] || exit 22; exit 0; fi
if [ -e "$STUB_DIR/$unit.frozen" ]; then [ -z "$max" ] || exit 28; echo "$url" >> "$STUB_DIR/curlhung.log"; exit 99; fi
exit 0
"""
WATCH_SYSTEMCTL = r"""#!/bin/sh
# systemctl is-active UNIT, systemctl show UNIT -p ActiveEnterTimestampMonotonic --value, systemctl restart UNIT
echo "$*" >> "$STUB_DIR/systemctl.log"
case "$1" in
    is-active) cat "$STUB_DIR/$2.active" ;;
    show) awk -v ago="$(cat "$STUB_DIR/$2.ago")" '{printf "%d", ($1 - ago) * 1000000}' /proc/uptime ;;
    restart) [ ! -e "$STUB_DIR/restart.fails.$2" ] ;;
    *) echo "unexpected: $*" >&2; exit 64 ;;
esac
"""
RM = '#!/bin/sh\necho "$*" >> "$STUB_DIR/rm.log"\n'
INSTALL_SYSTEMCTL = r"""#!/bin/sh
# What the real one does for install_watch.sh: holds a timer's state, reads each unit's drop-ins into its OOMPolicy, and
# answers for each engine. A mark in $STUB_DIR spoils one thing, once, so that each read-back can be made to fail; a mark
# read at the install's reload stands in the restore's way, so that a restore can be made to half work.
echo "$*" >> "$STUB_DIR/systemctl.log"
units=$STUB_ROOT/etc/systemd/system
timer=$units/nh-engine-watch.timer
stuck=$(cat "$STUB_DIR/timer.stuck" 2>/dev/null)
case "$1" in
    daemon-reload)
        if [ -e "$STUB_DIR/reload.fails" ]; then
            n=$(cat "$STUB_DIR/reload.fails")
            echo $((n - 1)) > "$STUB_DIR/reload.fails"
            [ "$n" -le 0 ] || exit 1
        fi
        if [ -e "$STUB_DIR/reload.kills" ]; then
            rm "$STUB_DIR/reload.kills"
            kill -9 "$PPID"
        fi
        if [ -e "$STUB_DIR/reload.spoils" ]; then
            echo spoiled >> "$STUB_ROOT/$(cat "$STUB_DIR/reload.spoils")"
            rm "$STUB_DIR/reload.spoils"
        fi
        if [ -e "$STUB_DIR/reload.removes" ]; then
            rm -f "$STUB_ROOT/$(cat "$STUB_DIR/reload.removes")"
            rm "$STUB_DIR/reload.removes"
        fi
        if [ -e "$STUB_DIR/reload.blocks" ]; then
            # a directory where the file was: no copy can land on it and no rm -f can take it away
            in_the_way=$STUB_ROOT/$(cat "$STUB_DIR/reload.blocks")
            rm -f "$in_the_way"
            mkdir -p "$in_the_way/blocked"
            rm "$STUB_DIR/reload.blocks"
        fi
        if [ -e "$STUB_DIR/reload.moves" ]; then
            what=$(cat "$STUB_DIR/reload.moves")
            echo $(( $(cat "$STUB_DIR/$what") + 1 )) > "$STUB_DIR/$what"
            rm "$STUB_DIR/reload.moves"
        fi
        if [ -e "$STUB_DIR/reload.again" ]; then
            # a second run of the script while this one holds its lock
            again=$(cat "$STUB_DIR/reload.again")
            rm "$STUB_DIR/reload.again"
            sh "$STUB_INSTALL" --root "$STUB_ROOT" $again > "$STUB_DIR/nested.out" 2> "$STUB_DIR/nested.err"
            echo $? > "$STUB_DIR/nested.rc"
        fi ;;
    show)
        if [ "$4" != OOMPolicy ]; then cat "$STUB_DIR/$2.$4"
        elif [ ! -e "$STUB_DIR/$2.oom-stuck" ] && grep -qs '^OOMPolicy=continue$' "$units/$2.service.d/"*; then echo continue
        else echo stop; fi ;;
    is-enabled) if [ -e "$timer" ]; then cat "$STUB_DIR/timer.enabled"; else echo not-found; fi ;;
    is-active) cat "$STUB_DIR/timer.active" ;;
    enable)
        [ -e "$timer" ] || exit 1
        [ "$2" = --now ] || [ "$stuck" != enabled ] || exit 1
        wont=$(cat "$STUB_DIR/timer.wont" 2>/dev/null)
        rm -f "$STUB_DIR/timer.wont"
        case "$wont" in enabled) echo disabled > "$STUB_DIR/timer.enabled" ;; *) echo enabled > "$STUB_DIR/timer.enabled" ;; esac
        case "$wont" in
            active) echo inactive > "$STUB_DIR/timer.active" ;;
            *) [ "$2" != --now ] || echo active > "$STUB_DIR/timer.active" ;;
        esac ;;
    disable)
        [ -e "$timer" ] || exit 1
        echo disabled > "$STUB_DIR/timer.enabled" ;;
    start)
        [ "$stuck" != active ] || exit 1
        echo active > "$STUB_DIR/timer.active" ;;
    stop) echo inactive > "$STUB_DIR/timer.active" ;;
    *) echo "unexpected: $*" >&2; exit 64 ;;
esac
"""
# Logs the mode asked for, then does it, so a file's mode is pinned on a laptop whose filesystem does not hold one. A mark
# makes it fail on the last file laid down, with the others already in place.
CHMOD = r"""#!/bin/sh
echo "$*" >> "$STUB_DIR/chmod.log"
case "$*" in *nh-mcp*) [ ! -e "$STUB_DIR/chmod.fails" ] || exit 1 ;; esac
command -p chmod "$@"
"""
# util-linux's flock -n FD, for a shell that has none (Git Bash). It locks the open file behind FD with the msys runtime's
# own locks, which outlive this process and go when the last descriptor on that file closes, as the kernel's do on the box,
# so a second holder is truly refused. Where flock is installed, the real one runs instead.
FLOCK = r"""#!/usr/bin/perl
use Fcntl qw(:flock);
my ($n, $fd) = @ARGV;
die "usage: flock -n FD\n" unless defined $fd && $n eq "-n" && $fd =~ /^\d+$/;
open(my $fh, ">&=", $fd) or die "flock: $fd: $!\n";
flock($fh, LOCK_EX | LOCK_NB) or exit 1;
"""
HTTP_500 = b"HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
HTTP_200 = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok"
NO_PROXY = {"no_proxy": "*", "NO_PROXY": "*", "http_proxy": "", "HTTP_PROXY": "", "all_proxy": "", "ALL_PROXY": ""}


def a_shell() -> str:
    """A POSIX sh. On Windows the gate's PATH may not hold Git's, and System32's bash is no shell without WSL."""
    for found in (shutil.which("sh"), r"C:\Program Files\Git\bin\sh.exe"):
        if found and Path(found).exists() and "system32" not in found.lower():
            return found
    pytest.fail("no sh here")


def test_a_missing_shell_fails_and_never_skips(monkeypatch):
    with monkeypatch.context() as patched:
        patched.setattr(shutil, "which", lambda name: None)
        patched.setattr(Path, "exists", lambda self: False)
        with pytest.raises(pytest.fail.Exception):
            a_shell()


@functools.lru_cache(maxsize=None)
def the_shell_has_flock() -> bool:
    return subprocess.run([a_shell(), "-c", "command -v flock"], capture_output=True).returncode == 0


def stub(folder: Path, name: str, body: str) -> None:
    (folder / name).write_bytes(body.encode())
    (folder / name).chmod(0o755)


def sh(script: Path, args: list, stubs: Path, env: dict, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a script with the stubs first on PATH. The wrapper turns their path into the shell's own on Windows, and runs the
    script under dash where there is one: Git Bash's sh is bash, and strips carriage returns that a plain sh keeps."""
    wrapper = ('case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) STUBS=$(cygpath -u "$STUBS") ;; esac; '
               'PATH="$STUBS:$PATH"; export PATH; '
               'if command -v dash >/dev/null; then exec dash "$0" "$@"; fi; exec sh "$0" "$@"')
    return subprocess.run([a_shell(), "-c", wrapper, script.as_posix(), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout,
                          env={**os.environ, "STUBS": stubs.as_posix(), **env})


def sections(path: Path) -> dict:
    """A unit file's settings by section, comments and blank lines left out."""
    found, at = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("["):
            at = line
            found[at] = []
        elif at and line.strip() and not line.startswith("#"):
            found[at].append(line)
    return found


def seconds(value: str) -> int:
    held = re.fullmatch(r"(\d+)\s*(s|sec|min)?", value.strip())
    assert held, value
    return int(held.group(1)) * (60 if held.group(2) == "min" else 1)


class Watch:
    """A stub machine for the watch: what each unit answers, what it was asked, and the two counts."""

    def __init__(self, tmp_path: Path, curl: bool = True):
        self.dir = tmp_path
        self.stubs = tmp_path / "stubs"
        self.stubs.mkdir()
        for name, body in (("systemctl", WATCH_SYSTEMCTL), ("logger", LOGGER)) + ((("curl", CURL),) if curl else ()):
            stub(self.stubs, name, body)
        self.count_file = {unit: tmp_path / f"{unit}.fails" for unit in ENGINES}
        for unit in ENGINES:
            self.started(unit, 1000)
            self.unit_is(unit, "active")

    def mark(self, name: str, text: str = "") -> None:
        (self.dir / name).write_bytes(text.encode("ascii"))         # bytes: text mode would add a carriage return here

    def started(self, unit: str, seconds_ago: int) -> None:
        self.mark(f"{unit}.ago", str(seconds_ago))

    def unit_is(self, unit: str, word: str) -> None:
        self.mark(f"{unit}.active", word + "\n")

    def down(self, *units: str) -> None:
        for unit in units:
            self.mark(f"{unit}.down")

    def up(self, *units: str) -> None:
        for unit in units:
            (self.dir / f"{unit}.down").unlink(missing_ok=True)

    def read(self, times: int = 1, counts: bool = True, expect: int = 0, timeout: int = 120,
             **env: str) -> subprocess.CompletedProcess:
        """Fire the watch as the timer would. A run that ends other than `expect` is a failure, so a missing script is red."""
        full = {"STUB_DIR": self.dir.as_posix(), **env}
        if counts:
            full.update(NH_WATCH_STATE=self.count_file["nh-engine"].as_posix(),
                        NH_WATCH_MCP_STATE=self.count_file["nh-mcp"].as_posix())
        for _ in range(times):
            done = sh(WATCH, [], self.stubs, full, timeout)
            assert done.returncode == expect, done.stdout + done.stderr
        return done

    def count(self, unit: str):
        held = self.count_file[unit]
        return int(held.read_text(encoding="ascii")) if held.exists() else None

    def counts(self) -> tuple:
        return tuple(self.count(unit) for unit in ENGINES)

    def asked(self, name: str) -> list:
        log = self.dir / f"{name}.log"
        return log.read_text(encoding="utf-8").splitlines() if log.exists() else []

    def restarted(self) -> list:
        return [line.split()[1] for line in self.asked("systemctl") if line.startswith("restart ")]


@pytest.fixture
def watch(tmp_path) -> Watch:
    return Watch(tmp_path)


@pytest.mark.parametrize("unit", ENGINES)
def test_a_good_read_clears_the_count(watch, unit):
    watch.down(unit)
    watch.read(3)
    assert watch.count(unit) == 3
    watch.up(unit)
    watch.read()
    assert watch.count(unit) is None
    watch.down(unit)
    watch.read(3)
    assert watch.count(unit) == 3 and watch.restarted() == []       # the count began again, so no fourth read has come


@pytest.mark.parametrize("unit,other", BOTH_WAYS)
def test_four_failed_reads_restart_that_unit_and_no_other(watch, unit, other):
    watch.down(unit)
    watch.read(3)
    assert watch.restarted() == []
    watch.read()
    assert watch.restarted() == [unit]
    assert watch.counts() == (None, None)
    logged = watch.asked("logger")
    assert f"-t nh-engine-watch {unit} health read failed, 4 of 4" in logged
    assert f"-t nh-engine-watch restarting {unit} after 4 failed reads" in logged
    assert not [line for line in logged if f" {other} " in f"{line} "]


@pytest.mark.parametrize("unit", ENGINES)
def test_a_health_that_answers_5xx_is_a_failed_read(watch, unit):
    watch.mark(f"{unit}.5xx")
    watch.read(3)
    assert watch.count(unit) == 3
    watch.read()
    assert watch.restarted() == [unit]
    assert set(watch.asked("curlflags")) == {"fail=1 max=10"}         # -f is what makes a 500 a failure


@pytest.mark.parametrize("unit", ENGINES)
def test_a_frozen_engine_is_read_under_curls_ten_second_bound(watch, unit):
    watch.mark(f"{unit}.frozen")
    watch.read(3)
    assert watch.count(unit) == 3
    watch.read()
    assert watch.restarted() == [unit]
    assert watch.asked("curlhung") == []                            # no read waited for ever
    assert watch.asked("curlflags") == ["fail=1 max=10"] * 8          # each read is bounded at 10 s, both units' alike


FROZEN_HOLD_S = 25      # past curl's -m 10, and short of the test's bound on a run


@contextlib.contextmanager
def a_local_socket(answer):
    """A socket on 127.0.0.1 that takes each connection and gives `answer`, or, given None, holds it unanswered, as a frozen
    engine does. It is this test's own and nothing else's; it goes when the test does. A held connection is let go after
    FROZEN_HOLD_S, so a watch that waits with no bound fails this test on time instead of hanging it: on Windows a run
    whose shell is killed can leave its curl behind, still waiting."""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)
    listener.settimeout(0.2)
    held, stop = [], threading.Event()

    def serve():
        while not stop.is_set():
            for conn, since in list(held):
                if time.monotonic() - since > FROZEN_HOLD_S:
                    conn.close()
                    held.remove((conn, since))
            try:
                conn, _ = listener.accept()
            except OSError:
                continue
            held.append((conn, time.monotonic()))
            if answer is not None:
                try:
                    conn.settimeout(5)
                    conn.recv(65536)
                    conn.sendall(answer)
                except OSError:
                    pass
                conn.close()
                held.pop()

    serving = threading.Thread(target=serve, daemon=True)
    serving.start()
    try:
        yield f"http://127.0.0.1:{listener.getsockname()[1]}/health"
    finally:
        stop.set()
        serving.join(5)
        for conn, _since in held:
            conn.close()
        listener.close()


def test_with_real_curl_a_frozen_engine_costs_its_ten_seconds_and_a_500_counts(tmp_path):
    watch = Watch(tmp_path, curl=False)
    with a_local_socket(None) as frozen, a_local_socket(HTTP_500) as failing, a_local_socket(HTTP_200) as healthy:
        began = time.monotonic()
        watch.read(NH_WATCH_URL=frozen, NH_WATCH_MCP_URL=failing, timeout=90, **NO_PROXY)
        took = time.monotonic() - began
        assert watch.counts() == (1, 1)
        assert 9 <= took < FROZEN_HOLD_S - 5                        # the read waited on the frozen socket, and -m ended it
        watch.read(NH_WATCH_URL=healthy, NH_WATCH_MCP_URL=healthy, timeout=90, **NO_PROXY)
        assert watch.counts() == (None, None)


@pytest.mark.parametrize("unit", ENGINES)
def test_the_grace_holds_for_180_seconds_after_a_start(watch, unit):
    port = {"nh-engine": ":8002/", "nh-mcp": ":8003/"}[unit]
    watch.down(unit)
    watch.read(2)
    assert watch.count(unit) == 2
    reads = len([url for url in watch.asked("curl") if port in url])
    watch.started(unit, 170)                                        # a start clears what came before it
    watch.read(5)
    assert watch.count(unit) is None and watch.restarted() == []
    assert len([url for url in watch.asked("curl") if port in url]) == reads      # and nothing is read in the grace
    watch.started(unit, 190)
    watch.read()
    assert watch.count(unit) == 1


@pytest.mark.parametrize("fresh,stale", BOTH_WAYS)
def test_each_unit_has_its_own_grace_from_its_own_start(watch, fresh, stale):
    watch.started(fresh, 10)
    watch.down(*ENGINES)
    watch.read(4)
    assert watch.restarted() == [stale]
    assert watch.count(fresh) is None
    asked = watch.asked("systemctl")
    assert f"show {fresh} -p ActiveEnterTimestampMonotonic --value" in asked
    assert f"show {stale} -p ActiveEnterTimestampMonotonic --value" in asked


def test_the_two_units_never_share_a_count(watch):
    engine, mcp = ENGINES
    watch.down(engine)
    watch.read(2)
    assert watch.counts() == (2, None)
    watch.down(mcp)
    watch.read()
    assert watch.counts() == (3, 1)
    watch.read()                                                    # nh-engine's fourth is nh-mcp's second
    assert watch.restarted() == [engine]
    assert watch.counts() == (None, 2)
    watch.up(engine)
    watch.read(2)
    assert watch.restarted() == [engine, mcp]
    assert watch.counts() == (None, None)
    watch.up(mcp)
    watch.down(engine)
    watch.read(2)
    assert watch.counts() == (2, None)
    watch.up(engine)
    watch.down(mcp)
    watch.read()                                                    # a good read clears its own count and no other
    assert watch.counts() == (None, 1)
    watch.down(engine)
    watch.up(mcp)
    watch.read()
    assert watch.counts() == (1, None)


def test_the_counts_live_in_two_files_by_default_and_the_reads_go_to_each_units_port(watch):
    stub(watch.stubs, "rm", RM)                                     # the laptop has no /run; the path is what is asked of rm
    for unit in ENGINES:
        watch.unit_is(unit, "inactive")
    watch.read(counts=False)
    assert watch.asked("rm") == ["-f /run/nh-engine-watch.fails", "-f /run/nh-mcp-watch.fails"]
    for unit in ENGINES:
        watch.unit_is(unit, "active")
    watch.read(counts=False)
    assert watch.asked("curl") == ["http://127.0.0.1:8002/health", "http://127.0.0.1:8003/health"]


@pytest.mark.parametrize("stopped,running", BOTH_WAYS)
def test_a_unit_that_is_not_active_holds_no_count_and_costs_the_other_nothing(watch, stopped, running):
    watch.down(*ENGINES)
    watch.read(2)
    watch.unit_is(stopped, "inactive")
    watch.read(2)
    assert watch.restarted() == [running]
    assert watch.count(stopped) is None


@pytest.mark.parametrize("failing,other", BOTH_WAYS)
def test_a_restart_that_fails_fails_the_run_once_the_other_unit_is_read(watch, failing, other):
    watch.mark(f"restart.fails.{failing}")
    watch.down(failing)
    watch.read(3)
    reads = watch.asked("curl")
    watch.read(expect=1)
    assert watch.restarted() == [failing]
    assert len(watch.asked("curl")) == len(reads) + 2               # the run that failed still read both units
    (watch.dir / f"restart.fails.{failing}").unlink()
    watch.read(3)
    watch.read()                                                    # a restart that works ends the run cleanly
    assert watch.restarted() == [failing, failing]


def test_the_overrides_the_stopgap_had_still_work(watch):
    engine, mcp = ENGINES
    watch.down(engine)
    watch.read(2, NH_WATCH_LIMIT="2")
    assert watch.restarted() == [engine]

    watch.started(engine, 10)
    watch.read(NH_WATCH_GRACE="5")
    assert watch.count(engine) == 1
    watch.read(NH_WATCH_NOGRACE="1")
    assert watch.count(engine) == 2

    watch.started(engine, 1000)
    done = watch.read(2, NH_WATCH_DRY="1")
    assert "DRY: would restart nh-engine" in done.stdout
    assert watch.restarted() == [engine] and watch.count(engine) is None

    watch.up(engine)
    watch.read(NH_WATCH_URL="http://127.0.0.1:9/elsewhere")
    assert watch.asked("curl")[-2:] == ["http://127.0.0.1:9/elsewhere", "http://127.0.0.1:8003/health"]
    assert watch.count(engine) == 1
    watch.read(NH_WATCH_MCP_URL="http://127.0.0.1:9/elsewhere")
    assert watch.asked("curl")[-1] == "http://127.0.0.1:9/elsewhere"
    assert watch.counts() == (None, 1)


def test_the_timer_keeps_every_line_the_stopgap_runs_by():
    timer = sections(DEPLOY / "nh-engine-watch.timer")
    # OnBootSec gives the timer a base after a reboot, before its service has run once; without it the timer never fires
    # and still reads active. AccuracySec keeps each 30 s read from slipping by up to a minute.
    assert timer["[Timer]"] == ["OnBootSec=3min", "OnUnitActiveSec=30s", "AccuracySec=5s"]
    assert timer["[Install]"] == ["WantedBy=timers.target"]


def test_the_watch_service_is_bounded_past_two_reads_and_two_restarts():
    service = sections(DEPLOY / "nh-engine-watch.service")["[Service]"]
    assert "Type=oneshot" in service
    bound = [seconds(line.split("=", 1)[1]) for line in service if line.startswith("TimeoutStartSec=")]
    stops = []
    for unit in ENGINES:
        held = [line.split("=", 1)[1] for line in sections(DEPLOY / f"{unit}.service")["[Service]"]
                if line.startswith(("TimeoutStopSec=", "TimeoutSec="))]
        stops.append(seconds(held[-1]) if held else DEFAULT_STOP_S)
    read = int(re.search(r"curl -fsS -m (\d+) ", WATCH.read_text(encoding="utf-8")).group(1))
    total = 2 * read + sum(stops)
    assert len(bound) == 1 and bound[0] > total
    assert f"= {total} s" in (DEPLOY / "nh-engine-watch.service").read_text(encoding="utf-8")      # the comment's sum


class Stand:
    """A stub root holding what the box holds, a folder holding what the lead copies there, and a stub systemctl."""

    def __init__(self, tmp_path: Path, held: dict):
        self.dir = tmp_path
        self.root = tmp_path / "root"
        self.folder = tmp_path / "folder"
        self.stubs = tmp_path / "stubs"
        for made in (self.root, self.folder, self.stubs, self.root / "run"):
            made.mkdir()
        for rel, text in held.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_bytes(text.encode())
        for name in SHELL_FILES:
            shutil.copyfile(DEPLOY / name, self.folder / name)
        stub(self.stubs, "systemctl", INSTALL_SYSTEMCTL)
        stub(self.stubs, "chmod", CHMOD)
        if not the_shell_has_flock():
            stub(self.stubs, "flock", FLOCK)
        for unit in ENGINES:
            self.mark(f"{unit}.MainPID", "100\n")
            self.mark(f"{unit}.NRestarts", "0\n")
        here = f"{UNITS}/nh-engine-watch.timer" in held
        self.mark("timer.enabled", "enabled\n" if here else "disabled\n")
        self.mark("timer.active", "active\n" if here else "inactive\n")

    def mark(self, name: str, text: str = "") -> None:
        (self.dir / name).write_bytes(text.encode("ascii"))         # bytes: text mode would add a carriage return here

    def run(self, *args: str, script: Path = None, root: bool = True) -> subprocess.CompletedProcess:
        """Run the install. Every run, whatever it does, must leave the engines alone."""
        script = script or self.folder / "install_watch.sh"
        done = sh(script, (["--root", self.root.as_posix()] if root else []) + list(args), self.stubs,
                  {"STUB_DIR": self.dir.as_posix(), "STUB_ROOT": self.root.as_posix(), "STUB_INSTALL": script.as_posix()})
        assert touches_an_engine(self.asked()) == [], done.stdout + done.stderr
        return done

    def asked(self) -> list:
        log = self.dir / "systemctl.log"
        return log.read_text(encoding="utf-8").splitlines() if log.exists() else []

    def held(self) -> dict:
        """Every file under the root, bytes and all, but the snapshots and the lock's file under run/."""
        found = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        return {rel: body for rel, body in found.items() if not rel.startswith((SNAPSHOTS, "run/"))}

    def timer(self) -> tuple:
        return tuple((self.dir / name).read_text(encoding="ascii").strip() for name in ("timer.enabled", "timer.active"))

    def snapshots(self) -> list:
        kept = self.root / SNAPSHOTS
        return sorted(p.name for p in kept.iterdir()) if kept.is_dir() else []


def touches_an_engine(asked: list) -> list:
    """Each systemctl line that names an engine and is anything but a read of one property."""
    named = [line for line in asked if re.search(r"\bnh-(engine|mcp)\b(?!-watch)", line)]
    return [line for line in named if not re.fullmatch(r"show nh-(engine|mcp) -p \w+ --value", line)]


@pytest.fixture
def stand(tmp_path) -> Stand:
    return Stand(tmp_path, THE_BOX)


def test_the_install_lays_each_file_and_a_new_drop_in_and_overwrites_no_other(stand):
    before = stand.held()
    done = stand.run()
    assert done.returncode == 0, done.stdout + done.stderr
    assert "WATCH installed" in done.stdout
    now = stand.held()
    for rel, name in INSTALLED.items():
        assert now[rel] == (DEPLOY / name).read_bytes()
    assert set(now) - set(before) == set(DROP_INS.values())
    for rel in DROP_INS.values():
        assert re.search(r"^\[Service\]\nOOMPolicy=continue\n\Z", now[rel].decode(), re.M)
    assert {rel: now[rel] for rel in set(before) - set(INSTALLED)} == {rel: before[rel] for rel in set(before) - set(INSTALLED)}
    assert "daemon-reload" in stand.asked()
    assert stand.timer() == ("enabled", "active")
    assert stand.folder.as_posix() not in done.stdout and stand.root.as_posix() not in done.stdout    # its lines go in a note


def test_the_service_runs_the_file_the_install_lays_down(stand):
    assert stand.run().returncode == 0
    runs = [line.split("=", 1)[1] for line in sections(DEPLOY / "nh-engine-watch.service")["[Service]"]
            if line.startswith("ExecStart=")]
    assert len(runs) == 1 and runs[0].startswith("/")
    assert (stand.root / runs[0].lstrip("/")).read_bytes() == WATCH.read_bytes()


def test_the_installed_watch_can_run_and_each_file_has_its_mode(stand):
    assert stand.run().returncode == 0
    modes = (stand.dir / "chmod.log").read_text(encoding="ascii").splitlines()
    assert {line.split()[0] for line in modes if "nh-engine-watch.service" in line or ".conf" in line or ".timer" in line} == {"644"}
    assert {line.split()[0] for line in modes if "/bin/nh-engine-watch" in line} == {"755"}
    assert subprocess.run([a_shell(), "-c", 'test -x "$0"', (stand.root / "usr/local/bin/nh-engine-watch").as_posix()]).returncode == 0


def test_each_file_is_laid_down_whole_by_a_rename_and_never_written_in_place(stand):
    """A reader that has the old file open, as a timer firing mid-install would, reads the old file whole: the new one
    lands under another name and is renamed over it. A hard link stands in for that reader."""
    old = {}
    for rel in INSTALLED:
        old[rel] = stand.dir / ("old-" + rel.replace("/", "_"))
        os.link(stand.root / rel, old[rel])
    assert stand.run().returncode == 0
    for rel, name in INSTALLED.items():
        assert old[rel].read_bytes() == THE_BOX[rel].encode()
        assert (stand.root / rel).read_bytes() == (DEPLOY / name).read_bytes()
    assert not [p for p in stand.root.rglob("*.new")]


def test_undo_puts_back_what_the_install_replaced(stand):
    before = stand.held()
    assert stand.run().returncode == 0
    assert stand.held() != before and stand.snapshots() == ["1"]
    done = stand.run("--undo")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "WATCH undone" in done.stdout
    assert stand.held() == before
    assert stand.timer() == ("enabled", "active")
    assert stand.snapshots() == []
    assert stand.asked().count("daemon-reload") == 2


def test_undo_needs_only_the_script_so_the_folder_can_go(stand, tmp_path):
    before = stand.held()
    assert stand.run().returncode == 0
    shutil.rmtree(stand.folder)
    again = tmp_path / "again"
    again.mkdir()
    shutil.copyfile(INSTALL, again / "install_watch.sh")
    done = stand.run("--undo", script=again / "install_watch.sh")
    assert done.returncode == 0, done.stdout + done.stderr
    assert stand.held() == before


def test_with_nothing_left_to_undo_it_refuses_and_touches_nothing(stand):
    before = stand.held()
    done = stand.run("--undo")
    assert done.returncode == 64 and "no snapshot" in done.stderr
    assert stand.held() == before and stand.asked() == []


def test_a_second_install_keeps_the_first_snapshot_and_each_undo_goes_back_one(stand):
    before = stand.held()
    assert stand.run().returncode == 0
    first = stand.held()
    with (stand.folder / "nh-engine-watch.timer").open("ab") as held:
        held.write(b"# a later timer\n")
    assert stand.run().returncode == 0
    assert stand.held() != first and stand.snapshots() == ["1", "2"]
    assert stand.run("--undo").returncode == 0
    assert stand.held() == first and stand.snapshots() == ["1"]
    assert stand.run("--undo").returncode == 0
    assert stand.held() == before and stand.snapshots() == []


def test_on_a_box_with_no_watch_it_starts_one_and_undo_takes_it_all_away(tmp_path):
    without = {rel: text for rel, text in THE_BOX.items() if rel not in INSTALLED}
    stand = Stand(tmp_path, without)
    before = stand.held()
    done = stand.run()
    assert done.returncode == 0, done.stdout + done.stderr
    assert stand.timer() == ("enabled", "active")
    done = stand.run("--undo")
    assert done.returncode == 0, done.stdout + done.stderr
    assert stand.held() == before
    assert stand.timer() == ("disabled", "inactive")


@pytest.mark.parametrize("second", [[], ["--undo"]], ids=["install", "undo"])
def test_a_second_run_is_refused_while_one_holds_the_lock_and_the_lock_goes_with_it(stand, second):
    stand.mark("reload.again", " ".join(second))
    done = stand.run()
    assert done.returncode == 0, done.stdout + done.stderr
    assert (stand.dir / "nested.rc").read_text(encoding="ascii").strip() == "64"
    assert "another install or undo is running" in (stand.dir / "nested.err").read_text(encoding="utf-8")
    assert stand.snapshots() == ["1"]                               # the refused run took nothing and undid nothing
    done = stand.run("--undo")                                      # and once the first has ended, the lock is free
    assert done.returncode == 0, done.stdout + done.stderr


@pytest.mark.parametrize("mark,text,named", [
    ("reload.spoils", "usr/local/bin/nh-engine-watch", "WATCH FAILED nh-engine-watch\n"),
    ("reload.spoils", f"{UNITS}/nh-engine-watch.service", "WATCH FAILED nh-engine-watch.service\n"),
    ("reload.spoils", f"{UNITS}/nh-engine-watch.timer", "WATCH FAILED nh-engine-watch.timer\n"),
    ("reload.spoils", DROP_INS["nh-engine"], "WATCH FAILED 30-oom-policy.conf on nh-engine\n"),
    ("reload.spoils", DROP_INS["nh-mcp"], "WATCH FAILED 30-oom-policy.conf on nh-mcp\n"),
    ("reload.removes", "usr/local/bin/nh-engine-watch", "WATCH FAILED nh-engine-watch can run\n"),
    ("nh-engine.oom-stuck", "", "WATCH FAILED OOMPolicy of nh-engine\n"),
    ("nh-mcp.oom-stuck", "", "WATCH FAILED OOMPolicy of nh-mcp\n"),
    ("timer.wont", "enabled", "WATCH FAILED nh-engine-watch.timer enabled\n"),
    ("timer.wont", "active", "WATCH FAILED nh-engine-watch.timer active\n"),
    ("reload.moves", "nh-mcp.MainPID", "WATCH FAILED engines unmoved"),
    ("reload.moves", "nh-engine.NRestarts", "WATCH FAILED engines unmoved"),
    ("reload.fails", "1", "WATCH FAILED the install"),
    ("chmod.fails", "", "WATCH FAILED the install"),
])
def test_a_read_back_that_fails_restores_the_snapshot_and_exits_non_zero(stand, mark, text, named):
    before = stand.held()
    timer = stand.timer()
    stand.mark(mark, text)
    done = stand.run()
    assert done.returncode == 1, done.stdout + done.stderr
    assert named in done.stdout
    assert "WATCH restored" in done.stdout and "WATCH installed" not in done.stdout
    assert stand.held() == before
    assert stand.timer() == timer
    assert stand.snapshots() == []


def finish_by_undo(stand: Stand, before: dict) -> None:
    done = stand.run("--undo")
    assert done.returncode == 0, done.stdout + done.stderr
    assert stand.held() == before and stand.snapshots() == [] and stand.timer() == ("enabled", "active")


def a_restore_that_failed(done: subprocess.CompletedProcess, stand: Stand, named: str) -> None:
    assert done.returncode == 3, done.stdout + done.stderr
    assert named in done.stdout
    assert "WATCH RESTORE FAILED" in done.stdout and "WATCH restored" not in done.stdout
    assert stand.snapshots() == ["1"]                               # the one copy of what was there is kept


def test_a_restore_whose_reload_fails_says_so_keeps_the_snapshot_and_undo_can_finish_it(stand):
    before = stand.held()
    stand.mark("reload.fails", "1000")
    a_restore_that_failed(stand.run(), stand, "WATCH FAILED the reload\n")
    (stand.dir / "reload.fails").unlink()
    finish_by_undo(stand, before)


@pytest.mark.parametrize("rel", list(INSTALLED) + list(DROP_INS.values()))
def test_a_restore_that_cannot_put_a_file_back_says_so_keeps_the_snapshot_and_undo_can_finish_it(stand, rel):
    before = stand.held()
    stand.mark("reload.blocks", rel)
    named = f"WATCH FAILED {rel} as it was\n" if rel in INSTALLED else f"WATCH FAILED {rel} gone\n"
    a_restore_that_failed(stand.run(), stand, named)
    shutil.rmtree(stand.root / rel)                                 # a human takes away what was in the way
    finish_by_undo(stand, before)


@pytest.mark.parametrize("state", ["enabled", "active"])
def test_a_restore_whose_timer_will_not_come_back_says_so_keeps_the_snapshot_and_undo_can_finish_it(stand, state):
    before = stand.held()
    stand.mark("timer.wont", state)                                 # the install's read-back fails on the timer
    stand.mark("timer.stuck", state)                                # and the restore cannot bring it back
    a_restore_that_failed(stand.run(), stand, "WATCH FAILED nh-engine-watch.timer as it was\n")
    (stand.dir / "timer.stuck").unlink()
    finish_by_undo(stand, before)


def test_an_install_cut_short_leaves_its_snapshot_and_undo_restores_it(stand):
    before = stand.held()
    stand.mark("reload.kills")
    done = stand.run()
    assert done.returncode != 0 and "WATCH installed" not in done.stdout
    assert stand.held() != before and stand.snapshots() == ["1"]
    done = stand.run("--undo")                                      # the lock went with the run that was cut short
    assert done.returncode == 0, done.stdout + done.stderr
    assert stand.held() == before


@pytest.mark.parametrize("in_the_way", ["the snapshots", "a file it would copy"])
def test_a_snapshot_that_cannot_be_taken_refuses_and_leaves_no_half_snapshot(stand, in_the_way):
    if in_the_way == "the snapshots":
        (stand.root / SNAPSHOTS).parent.mkdir(parents=True)
        (stand.root / SNAPSHOTS).write_bytes(b"a file where the snapshots go\n")
    else:
        timer = stand.root / UNITS / "nh-engine-watch.timer"
        timer.unlink()
        (timer / "held").mkdir(parents=True)
    before = stand.held()
    done = stand.run()
    assert done.returncode == 64 and "the snapshot could not be taken" in done.stderr
    assert stand.held() == before and stand.asked() == []
    kept = stand.root / SNAPSHOTS
    assert not kept.is_dir() or list(kept.iterdir()) == []


def test_no_engine_restart_is_ever_called(stand):
    assert stand.run().returncode == 0
    assert stand.run("--undo").returncode == 0
    stand.mark("nh-mcp.oom-stuck")
    assert stand.run().returncode == 1
    asked = stand.asked()
    assert "show nh-engine -p OOMPolicy --value" in asked and "show nh-mcp -p NRestarts --value" in asked
    assert touches_an_engine(asked) == []
    assert not [line for line in asked if line.split()[0] in ("restart", "try-restart", "reload-or-restart", "kill", "reset-failed")]
    for verb in ("restart nh-engine", "stop nh-mcp", "try-restart nh-mcp", "start nh-engine.service", "kill nh-mcp"):
        assert touches_an_engine([verb]) == [verb]                  # and the check above can fail


@pytest.mark.parametrize("name", WATCH_FILES)
def test_it_refuses_a_file_with_carriage_returns_and_touches_nothing(stand, name):
    before = stand.held()
    held = stand.folder / name
    held.write_bytes(held.read_bytes().replace(b"\n", b"\r\n"))
    done = stand.run()
    assert done.returncode == 64 and "carriage returns" in done.stderr
    assert stand.held() == before and stand.asked() == [] and stand.snapshots() == []


@pytest.mark.parametrize("name", WATCH_FILES)
def test_it_refuses_a_folder_missing_a_file_and_touches_nothing(stand, name):
    before = stand.held()
    (stand.folder / name).unlink()
    done = stand.run()
    assert done.returncode == 64 and name in done.stderr
    assert stand.held() == before and stand.asked() == [] and stand.snapshots() == []


def test_it_refuses_a_watch_that_does_not_parse_and_touches_nothing(stand):
    before = stand.held()
    (stand.folder / "nh-engine-watch").write_bytes(b"#!/bin/sh\nif true; then\n")
    done = stand.run()
    assert done.returncode == 64 and "does not parse" in done.stderr
    assert stand.held() == before and stand.asked() == [] and stand.snapshots() == []


@pytest.mark.parametrize("unit", ENGINES)
def test_it_overwrites_no_drop_in_it_did_not_write(tmp_path, unit):
    stand = Stand(tmp_path, {**THE_BOX, DROP_INS[unit]: "[Service]\nOOMPolicy=stop\n"})
    before = stand.held()
    done = stand.run()
    assert done.returncode == 64 and "30-oom-policy.conf" in done.stderr
    assert stand.held() == before and stand.asked() == [] and stand.snapshots() == []


def test_it_refuses_without_root_or_a_stub_root_and_an_unknown_argument(stand):
    stub(stand.stubs, "id", "#!/bin/sh\necho 1000\n")
    done = stand.run(root=False)
    assert done.returncode == 64 and "sudo" in done.stderr
    assert stand.asked() == []
    done = stand.run("--bogus")
    assert done.returncode == 64 and "--bogus" in done.stderr


def test_its_header_says_how_it_is_run():
    header = " ".join(INSTALL.read_text(encoding="utf-8").split("\nset -u")[0].replace("#", " ").split())
    assert "sudo sh" in header and "--undo" in header and "--root" in header
    for name in SHELL_FILES:
        assert name in header
    assert "docs/HARNESS.md" in header
    assert "only root can write" in header                          # it installs as root what the folder holds
    assert "takes OOMPolicy=continue off both engines again" in header      # what --undo costs once cells ship
    assert "flock" in header


@pytest.mark.parametrize("name", SHELL_FILES)
def test_each_file_is_lf_and_stays_lf_and_names_no_box(name):
    held = (DEPLOY / name).read_bytes()
    assert b"\r" not in held                                        # a carriage return would break it on the box
    said = subprocess.run(["git", "check-attr", "eol", "--", f"deploy/{name}"], cwd=ROOT, capture_output=True, text=True)
    assert said.stdout.strip() == f"deploy/{name}: eol: lf"         # or the next Windows checkout turns it CRLF
    text = held.decode("utf-8")
    assert not re.search(r"/home/|/srv/|/opt/|/root/", text)
    assert set(re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", text)) <= {"127.0.0.1"}


@pytest.mark.parametrize("unit", ENGINES)
def test_each_engine_unit_states_oom_policy_continue(unit):
    assert "OOMPolicy=continue" in sections(DEPLOY / f"{unit}.service")["[Service]"]


def test_the_harness_names_the_install_among_the_ship_paths():
    text = (ROOT / "docs" / "HARNESS.md").read_text(encoding="utf-8")
    start = text.index("Only the lead touches the box, and only through a gated ship path, never by hand:")
    assert "`deploy/install_watch.sh`" in text[start:text.index("Subagents never ssh.")]
