"""tools/mint_ship.sh and the lines tools/deploy.sh hands it with (run 2026-11-13-stick-ship), run here with logging
stand-ins for ssh, scp, python and python3 first on PATH, in a temporary git repository with a stand-in origin, against
a stand-in box: a temporary directory. git and sha256sum are the real ones: the path's binding to HEAD and to origin's
default branch is what several tests show.

The stand-ins record every call and run nothing. ssh never connects and never runs the command it is given; its exit is
the test's (STUB_DIR/ssh.N.rc for the Nth call, else 0), so where the box would answer the streamed entry-check, the
test runs that check itself, the real unit fed on its stdin as the box's python would be, against the stand-in box, and
hands ssh its exit. scp copies the one file named between this machine and the stand-in box, as the transfer would, and
refuses any other host; python and python3 refuse outright. Where the box would run the unit, the test runs it, the real
file the stand-in scp put on the stand-in box, so the poll and the result are the unit's own. The host is one no
resolver answers, the key a file that does not exist and HOME a temporary directory, so a call that slipped past the
stand-ins could reach nothing; every test asserts that python was never called and that each ssh and scp call named the
stand-in host. tools/deploy.sh is held to its base (f6a1d1d) by a fixture of per-line digests, never its lines: the
script names the box at lines 23-25.

NOTHING HERE WAITS ON A CLOCK that load can run out (the precedent's rule, tests/test_build_ship.py): a wait is for a
state, with a generous bound only a broken run reaches; only the test of a timeout uses a short poll. Every test runs
inside `telling()`, so a failure carries the script's output, every stand-in's log and the stand-in box's results."""
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
SHIP = ROOT / "tools" / "mint_ship.sh"
DEPLOY = ROOT / "tools" / "deploy.sh"
UNIT = ROOT / "tools" / "stick_mint.py"
BASE_DIGESTS = ROOT / "tests" / "fixtures" / "deploy_sh_f6a1d1d.sha256"
HOST = "nobody@standin.invalid"
KEY = "/standin/no-such-key"
DEST = "/standin/dest"
SEP = "\x1f"
GENEROUS = 600                          # seconds: a bound only a broken run reaches, never a loaded laptop

# The stand-ins, as tests/test_build_ship.py has them: each logs a call as one record, its arguments each ended by \x1f
# and the record by a newline, in one write, so that a reader never meets half an argument list.
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
STUBS = {"ssh": SSH, "scp": SCP, "python": REFUSE, "python3": REFUSE}

# Runs a script with the stand-ins first on PATH, under dash where there is one (the box's /bin/sh is dash; Git Bash's
# sh is bash). On Windows the paths the stand-ins use are turned into the shell's own.
WRAPPER = ('case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) STUBS=$(cygpath -u "$STUBS"); STUB_DIR=$(cygpath -u "$STUB_DIR"); '
           'STANDIN_BOX=$(cygpath -u "$STANDIN_BOX") ;; esac; export STUB_DIR STANDIN_BOX; '
           'PATH="$STUBS:$PATH"; export PATH; PRELUDE'
           'if command -v dash >/dev/null; then exec dash "$0" ARGS; fi; exec sh "$0" ARGS')

# The lines tools/deploy.sh gains after its build block (line 35 of f6a1d1d), exactly.
MINT_BLOCK = [
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
def sm():
    return _load("stick_mint_for_ship", UNIT)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else "(none)"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------------------------------------ a laptop's repository

ALPHA = {"schema": 1, "name": "alpha", "aliases": ["alpha_ship_alias"], "doc": "alpha: a test entry",
         "seals": [{"key": "two_to_ten", "nid": "two_to_ten", "expr": "2**10", "value": 1024, "tol": 1e-12,
                    "domain": "mathematics"}],
         "sticks": [{"question": "A test stick for the mint ship", "statement": "A stick the tests mint.",
                     "field": "mathematics", "references": ["a test reference"], "by": "tests - alpha",
                     "marks": [{"kind": "witness", "claim": "[alpha] 2**10 = 1024 (sealed)", "seal": "two_to_ten"}]}]}
ALPHA_BYTES = (json.dumps(ALPHA, indent=1) + "\n").encode("utf-8")
FAKE_SEAL = "b" * 64


def git_env(home: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"), GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="tests", GIT_AUTHOR_EMAIL="tests@standin.invalid", GIT_COMMITTER_NAME="tests",
               GIT_COMMITTER_EMAIL="tests@standin.invalid")
    return env


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=str(repo), env=git_env(repo.parent / "home"), capture_output=True,
                          text=True, timeout=GENEROUS)
    assert done.returncode == 0, (args, done.stdout, done.stderr)
    return done.stdout


def a_line(name: str, entry: bytes, seals: str, expect: str = None) -> str:
    digest = sha(entry.replace(b"\r", b""))
    return f"# {name}: a test entry, minted by the tests\n{name} {digest} {seals}" + (f" expect={expect}" if expect else "")


def a_repo(tmp_path: Path, lines: list, files: dict = None) -> Path:
    """A stand-in laptop checkout: the real mint_ship.sh and unit, the listing given, data/sticks/alpha.json and the
    files given, committed and pushed to a stand-in origin whose default branch this laptop records."""
    repo, origin = tmp_path / "repo", tmp_path / "origin.git"
    (tmp_path / "home").mkdir(exist_ok=True)
    for rel, body in {"tools/mint_ship.sh": SHIP.read_bytes(), "tools/stick_mint.py": UNIT.read_bytes(),
                      "tools/stick_mints.txt": ("# THE MINT LISTING of a test laptop\n\n" + "\n".join(lines) + "\n").encode(),
                      "data/sticks/alpha.json": ALPHA_BYTES, **(files or {})}.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes(body)
    origin.mkdir()
    git(origin, "init", "-q", "--bare")
    git(origin, "symbolic-ref", "HEAD", "refs/heads/master")
    git(repo, "init", "-q")
    git(repo, "symbolic-ref", "HEAD", "refs/heads/master")
    git(repo, "config", "core.autocrlf", "false")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the base")
    git(repo, "remote", "add", "origin", origin.as_posix())
    git(repo, "push", "-q", "origin", "master")
    git(repo, "fetch", "-q", "origin")
    git(repo, "remote", "set-head", "origin", "master")
    return repo


def commit(repo: Path, message: str, push: bool = True) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    if push:
        git(repo, "push", "-q", "origin", "master")
        git(repo, "fetch", "-q", "origin")


class Laptop:
    """The stand-ins first on PATH, the stand-in box, and everything each stand-in was asked."""

    def __init__(self, tmp_path: Path, repo: Path):
        self.tmp, self.repo = tmp_path, repo
        self.stubs, self.logs, self.box = tmp_path / "stubs", tmp_path / "logs", tmp_path / "box"
        self.out, self.err = tmp_path / "out.txt", tmp_path / "err.txt"
        self.procs: list = []
        self.box_runs: list = []
        for d in (self.stubs, self.logs, self.box / "tools", self.box / "data" / "sticks"):
            d.mkdir(parents=True)
        for name, body in STUBS.items():
            (self.stubs / name).write_bytes(body.encode())
            (self.stubs / name).chmod(0o755)
        (self.box / "data" / "sticks" / "alpha.json").write_bytes(ALPHA_BYTES.replace(b"\n", b"\r\n"))  # sent from Windows

    def env(self, **extra) -> dict:
        env = git_env(self.tmp / "home")
        env = {k: v for k, v in env.items() if not k.startswith(("MINT_", "STUB", "STANDIN"))}
        env.pop("DEPLOY_NO_GATE", None)
        env.update(MINT_HOST=HOST, MINT_KEY=KEY, MINT_DEST=DEST, MINT_POLL_SECONDS=str(GENEROUS),
                   MINT_POLL_INTERVAL="1", STUBS=self.stubs.as_posix(), STUB_DIR=self.logs.as_posix(),
                   STANDIN_BOX=self.box.as_posix(), STANDIN_REMOTE=f"{HOST}:{DEST}/")
        env.update(extra)
        return {k: v for k, v in env.items() if v is not None}

    def start(self, args, script: Path = None, prelude: str = "", inner: str = '"$@"', **extra) -> subprocess.Popen:
        script = script or self.repo / "tools" / "mint_ship.sh"
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
        parts = [f"--- mint_ship.sh stdout\n{_text(self.out)}", f"--- mint_ship.sh stderr\n{_text(self.err)}"]
        for tool in STUBS:
            log = self.logs / f"{tool}.log"
            if log.exists():
                parts.append(f"--- the {tool} stand-in's log\n" + _text(log).replace(SEP, " | "))
        for cmd, done in self.box_runs:
            parts.append(f"--- the box ran {cmd}\nexit {done.returncode}\n{done.stdout}\n{done.stderr}")
        results = self.box / "data" / "mints" / ".results"
        for result in sorted(results.glob("*.json")) if results.exists() else []:
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
        assert self.calls("python") == [] and self.calls("python3") == []
        for call in self.calls("ssh"):
            assert call[:5] == ["-i", KEY, "-o", "ConnectTimeout=10", HOST], call
        for call in self.calls("scp"):
            assert call[:5] == ["-q", "-i", KEY, "-o", "ConnectTimeout=10"], call
            assert sum(a.startswith(f"{HOST}:{DEST}/") for a in call[5:]) == 1, call

    def no_call(self) -> bool:
        return all(self.calls(t) == [] for t in STUBS)

    def entry_check_answer(self, name: str, digest: str) -> int:
        """What the box's python answers to the streamed entry-check, run here against the stand-in box: its exit is
        the first ssh call's."""
        sent = (self.repo / "tools" / "stick_mint.py").read_bytes().replace(b"\r", b"")
        done = subprocess.run([sys.executable, "-I", "-B", "-", "entry-check", "--root", str(self.box), name, digest],
                              input=sent, capture_output=True, timeout=GENEROUS)
        (self.logs / "ssh.1.rc").write_bytes(str(done.returncode).encode())
        return done.returncode

    def started(self, proc: subprocess.Popen, after: int = 0):
        """Wait for the state, not a clock: the call that starts the unit on the box, among the ssh calls past the
        first `after`. Its command, verb, name and run id."""
        began = time.time()
        while True:
            for call in reversed(self.calls("ssh")[after:]):
                m = re.search(r"tools/stick_mint\.py (mint|retract) (\S+) --root '" + re.escape(DEST) +
                              r"' --run-id (\S+) < /dev/null", call[-1])
                if m:
                    return call[-1], m.group(1), m.group(2), m.group(3)
            assert proc.poll() is None, "mint_ship.sh ended before it started the unit"
            assert time.time() - began < GENEROUS, f"no start call in {GENEROUS}s"
            time.sleep(0.1)

    def polls(self) -> list:
        return [c for c in self.calls("scp") if c[5].startswith(f"{HOST}:")]

    def sent(self) -> dict:
        """What each scp call sent to the box: {path under the destination: the local file}."""
        return {call[6][len(f"{HOST}:{DEST}/"):]: call[5] for call in self.calls("scp")
                if call[6].startswith(f"{HOST}:{DEST}/")}

    def results(self) -> Path:
        path = self.box / "data" / "mints" / ".results"
        path.mkdir(parents=True, exist_ok=True)
        return path


def start_command(verb: str, name: str, run_id: str) -> str:
    return (f"cd '{DEST}' && nohup setsid nice -n 19 ionice -c 2 -n 7 .venv/bin/python -I -B tools/stick_mint.py "
            f"{verb} {name} --root '{DEST}' --run-id {run_id} < /dev/null > /dev/null 2>&1 &")


def check_command(name: str, digest: str) -> str:
    return f"cd '{DEST}' && .venv/bin/python -I -B - entry-check --root '{DEST}' {name} {digest}"


# ------------------------------------------------------------------------------------------------ deploy.sh

def digests(text: str) -> list:
    return [hashlib.sha256(line.encode("utf-8")).hexdigest() for line in text.replace("\r\n", "\n").split("\n")[:-1]]


def test_deploy_sh_keeps_every_line_of_f6a1d1d_unchanged_and_in_order_and_adds_only_the_mint_block():
    base = [line.split()[1] for line in BASE_DIGESTS.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")]
    assert len(base) == 180
    text = DEPLOY.read_text(encoding="utf-8").replace("\r\n", "\n")
    now, lines = digests(text), text.split("\n")[:-1]
    shown = "\n".join(f"{n:4} {line}" for n, line in enumerate(lines[20:50], 21))
    remaining = iter(now)
    assert all(d in remaining for d in base), shown          # every line of f6a1d1d appears, unchanged and in order
    assert now[:35] == base[:35], shown                      # lines 1-35 in place: the box's 23-25, the build block
    assert lines[35:35 + len(MINT_BLOCK)] == MINT_BLOCK, shown
    assert now[35 + len(MINT_BLOCK):] == base[35:], shown    # every other line of f6a1d1d, in order
    assert len(lines) == len(base) + len(MINT_BLOCK)
    assert not any(re.search(r"\w@\w", line) or "/home" in line for line in MINT_BLOCK)  # the box is named by 23-25 alone


@pytest.mark.parametrize("args,extra", [(["--mint", "no_such_entry"], {}), (["--mint-check", "no_such_entry"], {}),
                                        (["--mint-retract", "no_such_entry"], {}),
                                        (["--mint", "euler_e"], {"DEPLOY_NO_GATE": "1"})])
def test_deploy_sh_hands_mint_mint_check_and_mint_retract_to_mint_ship(tmp_path, args, extra):
    """The real deploy.sh, refused by mint_ship.sh before any call. The base (f6a1d1d) says 'not a file' instead."""
    laptop = Laptop(tmp_path, ROOT)
    with laptop.telling():
        rc, out, err = laptop.run(args, script=DEPLOY, MINT_HOST=None, MINT_KEY=None, MINT_DEST=None, **extra)
        assert rc == 2 and "mint_ship: refused:" in err
        assert "not a file" not in out + err
        assert laptop.no_call()


def test_deploy_sh_hands_mint_ship_its_own_host_key_and_destination(tmp_path):
    """A copy of deploy.sh whose box lines (23-25) name the stand-in box, and nothing else changed."""
    lines = DEPLOY.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    assert [lines[i].split("=")[0] for i in (22, 23, 24)] == ["HOST", "KEY", "DEST"]
    copy = list(lines)
    copy[22], copy[23], copy[24] = f'HOST="{HOST}"', f'KEY="{KEY}"', f'DEST="{DEST}"'
    assert [i for i in range(len(lines)) if lines[i] != copy[i]] == [22, 23, 24]
    repo = a_repo(tmp_path, [a_line("alpha", ALPHA_BYTES, f"two_to_ten={FAKE_SEAL}")],
                  {"tools/deploy.sh": "\n".join(copy).encode()})
    laptop = Laptop(tmp_path, repo)
    with laptop.telling():
        listed = sha(ALPHA_BYTES)
        assert laptop.entry_check_answer("alpha", listed) == 0
        rc, out, err = laptop.run(["--mint-check", "alpha"], script=repo / "tools" / "deploy.sh",
                                  MINT_HOST=None, MINT_KEY=None, MINT_DEST=None)
        assert rc == 0, err
        assert laptop.calls("ssh") == [["-i", KEY, "-o", "ConnectTimeout=10", HOST, check_command("alpha", listed)]]
        laptop.nothing_got_past()


# ------------------------------------------------------------------------------------------------ refusals

GOOD = a_line("alpha", ALPHA_BYTES, f"two_to_ten={FAKE_SEAL}")


@pytest.mark.parametrize("args,extra,why", [
    (["--mint", "no_such_entry"], {}, "not a listed name: no_such_entry"),
    (["--mint", "data/sticks/alpha.json"], {}, "never a path"),
    (["--mint", "../alpha"], {}, "never a path"),
    (["--mint", "alpha", "free"], {}, "not a switch"),
    (["--mint", "alpha", "--force", "x"], {}, "not a switch"),
    (["--mint"], {}, "usage"),
    (["alpha"], {}, "usage"),
    (["--mint", "alpha evil"], {}, "never a path or a free argument"),
    (["--mint", "alpha;evil"], {}, "never a path or a free argument"),
    (["--mint", "Alpha"], {}, "never a path or a free argument"),
    (["--mint", "alpha"], {"DEPLOY_NO_GATE": "1"}, "DEPLOY_NO_GATE"),
    (["--mint-check", "alpha"], {"DEPLOY_NO_GATE": "1"}, "DEPLOY_NO_GATE"),
    (["--mint", "alpha"], {"MINT_HOST": None}, "named only by tools/deploy.sh"),
    (["--mint", "alpha"], {"MINT_DEST": "relative/dest"}, "not an absolute path"),
    (["--mint", "alpha"], {"MINT_POLL_SECONDS": "901"}, "at most 900 seconds"),
    (["--mint-check", "alpha", "--mint", "no_such_entry"], {}, "not a listed name"),
])
def test_mint_ship_refuses_before_any_call(tmp_path, args, extra, why):
    laptop = Laptop(tmp_path, a_repo(tmp_path, [GOOD]))
    with laptop.telling():
        rc, out, err = laptop.run(args, **extra)
        assert rc == 2 and "mint_ship: refused:" in err and why in err
        assert laptop.no_call()


def test_a_name_holding_a_newline_is_refused_before_any_call(tmp_path):
    """Built inside the shell: a Windows argument list splits a newline into two words before any script sees it."""
    laptop = Laptop(tmp_path, a_repo(tmp_path, [GOOD]))
    with laptop.telling():
        rc, out, err = laptop.finish(laptop.start([], prelude="nl=$(printf 'alpha\\nevil'); ", inner='--mint "$nl"'))
        assert rc == 2 and "mint_ship: refused: not a listed name (a name, never a path or a free argument)" in err
        assert laptop.no_call()


def uncommitted_listing_line(repo: Path) -> None:
    (repo / "data" / "sticks" / "beta.json").write_bytes(ALPHA_BYTES.replace(b'"alpha"', b'"beta"'))
    commit(repo, "beta's entry, committed and pushed")
    with open(repo / "tools" / "stick_mints.txt", "ab") as fh:
        fh.write((a_line("beta", (repo / "data" / "sticks" / "beta.json").read_bytes(),
                         f"two_to_ten={FAKE_SEAL}") + "\n").encode())


def uncommitted_entry(repo: Path) -> None:
    (repo / "data" / "sticks" / "alpha.json").write_bytes(ALPHA_BYTES.replace(b"a test entry", b"an edited entry"))


def untracked_entry(repo: Path) -> None:
    git(repo, "rm", "-q", "--cached", "data/sticks/alpha.json")
    git(repo, "commit", "-q", "-m", "alpha's entry untracked, its file left in place")
    git(repo, "push", "-q", "origin", "master")
    git(repo, "fetch", "-q", "origin")
    assert (repo / "data" / "sticks" / "alpha.json").is_file()


def uncommitted_unit(repo: Path) -> None:
    with open(repo / "tools" / "stick_mint.py", "ab") as fh:
        fh.write(b"# an uncommitted line\n")


def staged_unit(repo: Path) -> None:
    uncommitted_unit(repo)
    git(repo, "add", "tools/stick_mint.py")


def head_not_on_origin(repo: Path) -> None:
    (repo / "notes.txt").write_bytes(b"a local commit\n")
    commit(repo, "a commit origin's default branch does not hold", push=False)


def laptop_entry_differs(repo: Path) -> None:
    text = (repo / "tools" / "stick_mints.txt").read_text(encoding="utf-8")
    (repo / "tools" / "stick_mints.txt").write_text(text.replace(sha(ALPHA_BYTES), "c" * 64), encoding="utf-8")
    commit(repo, "a listing whose entry hash is not the entry's")


@pytest.mark.parametrize("change,name,why", [
    (uncommitted_listing_line, "beta", "tools/stick_mints.txt and tools/stick_mint.py must be tracked and equal to HEAD"),
    (uncommitted_entry, "alpha", "data/sticks/alpha.json must be tracked and equal to HEAD"),
    (untracked_entry, "alpha", "data/sticks/alpha.json must be tracked and equal to HEAD"),
    (uncommitted_unit, "alpha", "tools/stick_mints.txt and tools/stick_mint.py must be tracked and equal to HEAD"),
    (staged_unit, "alpha", "tools/stick_mints.txt and tools/stick_mint.py must be tracked and equal to HEAD"),
    (head_not_on_origin, "alpha", "HEAD is not contained in origin/master as this laptop records it"),
    (laptop_entry_differs, "alpha", f"this laptop's data/sticks/alpha.json hashes to {sha(ALPHA_BYTES)}, not to the "
                                    f"listed {'c' * 64}"),
])
@pytest.mark.parametrize("switch", ["--mint", "--mint-check"])
def test_only_committed_pushed_bytes_are_sent_or_compared(tmp_path, change, name, why, switch):
    repo = a_repo(tmp_path, [GOOD])
    change(repo)
    laptop = Laptop(tmp_path, repo)
    with laptop.telling():
        rc, out, err = laptop.run([switch, name])
        assert rc == 2 and "mint_ship: refused:" in err and why in err, err
        assert laptop.no_call()


@pytest.mark.parametrize("expect", ["present", "refused"])
def test_mint_retract_on_a_canary_line_is_refused_before_any_call(tmp_path, expect):
    laptop = Laptop(tmp_path, a_repo(tmp_path, [a_line("alpha", ALPHA_BYTES, f"two_to_ten={FAKE_SEAL}", expect)]))
    with laptop.telling():
        rc, out, err = laptop.run(["--mint-retract", "alpha"])
        assert rc == 2 and "alpha is a canary: a line marked expect=present or expect=refused is never retracted" in err
        assert laptop.no_call()


@pytest.mark.parametrize("switch", ["--mint", "--mint-check", "--mint-retract"])
def test_a_box_whose_entry_differs_is_refused_before_anything_is_sent_or_started(tmp_path, switch):
    repo = a_repo(tmp_path, [GOOD])
    laptop = Laptop(tmp_path, repo)
    with laptop.telling():
        (laptop.box / "data" / "sticks" / "alpha.json").write_bytes(ALPHA_BYTES.replace(b"a test entry", b"the box's"))
        listed = sha(ALPHA_BYTES)
        assert laptop.entry_check_answer("alpha", listed) == 1
        rc, out, err = laptop.run([switch, "alpha"])
        assert rc == 2 and "the box's data/sticks/alpha.json is not the listed entry" in err
        assert "Nothing was sent or started" in err
        assert laptop.calls("ssh") == [["-i", KEY, "-o", "ConnectTimeout=10", HOST, check_command("alpha", listed)]]
        assert (laptop.logs / "ssh.1.stdin").read_bytes() == (repo / "tools" / "stick_mint.py").read_bytes().replace(
            b"\r", b"")                                      # this laptop's committed unit, streamed: nothing written
        assert laptop.calls("scp") == []
        laptop.nothing_got_past()


def test_mint_check_sends_nothing_and_starts_nothing(tmp_path):
    laptop = Laptop(tmp_path, a_repo(tmp_path, [GOOD]))
    with laptop.telling():
        assert laptop.entry_check_answer("alpha", sha(ALPHA_BYTES)) == 0
        rc, out, err = laptop.run(["--mint-check", "alpha"])
        assert rc == 0 and "checked: alpha on the box is the listed entry; nothing was sent or started" in out
        assert [c[-1] for c in laptop.calls("ssh")] == [check_command("alpha", sha(ALPHA_BYTES))]
        assert laptop.calls("scp") == [] and not (laptop.box / "tools" / "stick_mint.py").exists()
        laptop.nothing_got_past()


# ------------------------------------------------------------------------------------------------ a mint

ISOLATED = r"""
import json, os, shutil, sys, tempfile
root = sys.argv[1]
for k in [k for k in os.environ if k.upper().startswith("CONCORDANCE_")]:
    del os.environ[k]
tmp = tempfile.mkdtemp(prefix="nh-test-isolated-")
os.environ.update(CONCORDANCE_DATA_DIR=os.path.join(tmp, "data"), CONCORDANCE_SEAL_INDEX="0",
                  CONCORDANCE_VERIFY_TIMEOUT_S="1800", CONCORDANCE_RIEMANN_MAX="1e9", WEB_FIND_DISABLED="1")
sys.path.insert(0, os.path.join(root, "src"))
from concordance import sticks
print("ISOLATED " + json.dumps({s["key"]: sticks.seal(s) for s in json.load(sys.stdin)["seals"]}))
shutil.rmtree(tmp, ignore_errors=True)
"""


def stand_in_systemctl(folder: Path, data: Path) -> Path:
    out, log = folder / "systemctl.out", folder / "systemctl.log"
    out.write_text(f'Environment="CONCORDANCE_DATA_DIR={data.as_posix()}"\n', encoding="utf-8")
    if os.name == "nt":
        path = folder / "systemctl.cmd"
        path.write_text(f'@echo off\r\necho %*>> "{log}"\r\ntype "{out}"\r\n', encoding="utf-8")
    else:
        path = folder / "systemctl"
        path.write_text(f'#!/bin/sh\nprintf \'%s\\n\' "$*" >> "{log}"\ncat "{out}"\n', encoding="utf-8")
        path.chmod(0o755)
    return path


def play_the_box(laptop: Laptop, verb: str, name: str, run_id: str) -> int:
    """What the box does with the start call: run the unit the stand-in scp put there, on the stand-in box, with a
    stand-in memory reading and a stand-in systemctl."""
    box = laptop.box
    if not (box / "src").exists():
        shutil.copytree(ROOT / "src", box / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (laptop.tmp / "engine").mkdir(exist_ok=True)
    (laptop.tmp / "scratch").mkdir(exist_ok=True)
    (laptop.tmp / "meminfo").write_bytes(b"MemAvailable:   8388608 kB\n")
    systemctl = stand_in_systemctl(laptop.tmp / "engine", box / "data")
    cmd = [sys.executable, "-I", str(box / "tools" / "stick_mint.py"), verb, name, "--root", str(box), "--run-id",
           run_id, "--meminfo", str(laptop.tmp / "meminfo"), "--systemctl", str(systemctl), "--scratch-base",
           str(laptop.tmp / "scratch")]
    done = subprocess.run(cmd, cwd=str(box), capture_output=True, text=True, timeout=GENEROUS)
    laptop.box_runs.append((" ".join(cmd[2:5]), done))
    return done.returncode


def test_an_accepted_mint_sends_exactly_the_listing_and_the_unit_starts_one_unit_and_reads_its_result(tmp_path):
    seals = subprocess.run([sys.executable, "-I", "-B", "-c", ISOLATED, str(ROOT)], input=json.dumps(ALPHA),
                           capture_output=True, text=True, timeout=GENEROUS,
                           env={k: v for k, v in os.environ.items() if not k.upper().startswith("CONCORDANCE_")})
    found = [line for line in seals.stdout.splitlines() if line.startswith("ISOLATED ")]
    assert found, seals.stderr
    listed = json.loads(found[-1][len("ISOLATED "):])["two_to_ten"]
    repo = a_repo(tmp_path, [a_line("alpha", ALPHA_BYTES, f"two_to_ten={listed}")])
    laptop = Laptop(tmp_path, repo)
    with laptop.telling():
        assert laptop.entry_check_answer("alpha", sha(ALPHA_BYTES)) == 0
        proc = laptop.start(["--mint", "alpha"])
        command, verb, name, run_id = laptop.started(proc)
        assert (command, verb, name) == (start_command("mint", "alpha", run_id), "mint", "alpha")
        assert laptop.sent() == {"tools/stick_mints.txt": "tools/stick_mints.txt",
                                 "tools/stick_mint.py": "tools/stick_mint.py"}
        for p in laptop.sent():
            assert (laptop.box / p).read_bytes() == (repo / p).read_bytes()
        assert play_the_box(laptop, verb, name, run_id) == 0
        rc, out, err = laptop.finish(proc)
        assert rc == 0, err
        assert [c[-1] for c in laptop.calls("ssh")] == [check_command("alpha", sha(ALPHA_BYTES)), command]   # one unit
        assert {c[5] for c in laptop.polls()} == {f"{HOST}:{DEST}/data/mints/.results/{run_id}.json"}
        assert f'"run_id": "{run_id}"' in out and '"status": "minted"' in out and "-- mint alpha: done" in out
        laptop.nothing_got_past()


def a_result(sm, results: Path, at: str, **fields) -> None:
    """A result at run `at`'s path, written by the unit's own writer, so it is in the form the unit writes; `fields`
    may name another run id or name than the path's."""
    sm.write_result(results, at, {"command": "mint", "name": "alpha", "run_id": at, "status": "present", "step": 2,
                                  "unit": "tools/stick_mint.py", **fields})


def test_a_result_holding_another_run_id_or_name_is_never_accepted(tmp_path, sm):
    laptop = Laptop(tmp_path, a_repo(tmp_path, [GOOD]))
    with laptop.telling():
        proc = laptop.start(["--mint", "alpha"])
        _command, _verb, _name, run_id = laptop.started(proc)
        results = laptop.results()
        for stale in ({"run_id": "20200101T000000Z-aaaaaaaaaaaa"}, {"name": "beta"}):
            a_result(sm, results, run_id, **stale)           # at this run's path, but not this run's, or not alpha's
            seen = len(laptop.polls())
            began = time.time()
            while len(laptop.polls()) < seen + 2:            # two whole polls that read it
                assert proc.poll() is None, f"mint_ship.sh took a result that is not this run's: {stale}"
                assert time.time() - began < GENEROUS, "no poll read the stale result"
                time.sleep(0.1)
        a_result(sm, results, run_id)                        # now this run's own
        rc, out, err = laptop.finish(proc)
        assert rc == 0 and f'"run_id": "{run_id}"' in out and "20200101T000000Z" not in out and '"beta"' not in out
        laptop.nothing_got_past()


@pytest.mark.parametrize("status", ["refused", "failed"])
def test_a_refused_or_failed_result_exits_non_zero_and_says_so(tmp_path, sm, status):
    laptop = Laptop(tmp_path, a_repo(tmp_path, [GOOD]))
    with laptop.telling():
        proc = laptop.start(["--mint", "alpha"])
        _command, _verb, _name, run_id = laptop.started(proc)
        a_result(sm, laptop.results(), run_id, status=status, reason="the rehearsal refused it")
        rc, out, err = laptop.finish(proc)
        assert rc == 1 and f"mint alpha did not succeed (run {run_id})" in err
        assert f'"status": "{status}"' in out and "done" not in out
        laptop.nothing_got_past()


def test_a_timeout_exits_non_zero_and_says_so(tmp_path):
    """The one short poll here: the timeout is what this test shows, so load can only make it come later."""
    laptop = Laptop(tmp_path, a_repo(tmp_path, [GOOD]))
    with laptop.telling():
        proc = laptop.start(["--mint", "alpha"], MINT_POLL_SECONDS="3")
        _command, _verb, _name, run_id = laptop.started(proc)
        rc, out, err = laptop.finish(proc)
        assert rc == 1 and f"no result for run {run_id} within 3s" in err
        assert {c[5] for c in laptop.polls()} == {f"{HOST}:{DEST}/data/mints/.results/{run_id}.json"}
        laptop.nothing_got_past()


def test_mint_retract_starts_the_units_retract_and_accepts_only_retracted_or_absent(tmp_path, sm):
    laptop = Laptop(tmp_path, a_repo(tmp_path, [GOOD]))
    with laptop.telling():
        proc = laptop.start(["--mint-retract", "alpha"])
        command, verb, name, run_id = laptop.started(proc)
        assert (command, verb, name) == (start_command("retract", "alpha", run_id), "retract", "alpha")
        a_result(sm, laptop.results(), run_id, command="retract", status="retracted")
        rc, out, err = laptop.finish(proc)
        assert rc == 0 and "-- retract alpha: done" in out
        calls = len(laptop.calls("ssh"))
        proc = laptop.start(["--mint-retract", "alpha"])
        _command, _verb, _name, run_id = laptop.started(proc, after=calls)
        a_result(sm, laptop.results(), run_id, command="retract", status="present")    # a mint's word, not a retract's
        rc, out, err = laptop.finish(proc)
        assert rc == 1 and f"retract alpha did not succeed (run {run_id})" in err
        laptop.nothing_got_past()


def test_mint_ship_reaches_the_box_only_through_ssh_and_scp_by_name():
    text = SHIP.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert "verify_deploy" not in code and "command -p" not in code and "env -i" not in code
    assert "export" not in code and "exec " not in code and not re.search(r'\bsh "?\$', code)  # no child gets the box
    assert not re.search(r"/(ssh|scp|git|sha256sum)\b", code)
    assert re.findall(r"\S*python\S*", code) == [".venv/bin/python", ".venv/bin/python"]   # only in the box's commands
    assert set(re.findall(r"\b(ssh|scp|git|sha256sum|curl|wget|rsync|tar)\b", code)) == {"ssh", "scp", "git", "sha256sum"}
