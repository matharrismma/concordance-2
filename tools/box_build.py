#!/usr/bin/env python3
"""THE BOX BUILD UNIT: the one place data is built on the box (run 2026-11-11-box-build).

    python tools/box_build.py build  --root DEST --run-id RUN NAME   on the box: build one entry of tools/box_builds.txt
    python tools/box_build.py verify --root DEST NAME HASH           read only: data/builds/NAME/HASH is there and
                                                                     re-hashes to HASH
    python tools/box_build.py hash   DIR                             the content hash the listing holds for an output

tools/build_ship.sh starts `build` on the box, detached, with a fresh run id, and polls for its result. A build only
ever ADDS data/builds/<name>/<content hash>/, and nothing serves that directory until an ordinary gated deploy ships a
pin naming it (src/concordance/build_pins.json, read by src/concordance/builds.py). So a build that fails, a session
that drops or a poll that times out never changes what the site serves.

`build`, in order:
  1. takes data/builds/.lock without waiting, a lock the kernel drops if the unit dies. A second build is refused and
     writes its refusal only to its own data/builds/.results/<run id>.json;
  2. under the lock, removes what an earlier unit left behind in data/builds/.tmp/ and data/builds/.inputs/;
  3. reads the entry from tools/box_builds.txt and checks that its staged inputs, data/builds/.inputs/<run id>/, are
     exactly the entry's inputs;
  4. reads available memory and free disk, and refuses to start with less than the cap plus 256 MB of memory, or less
     than 2 GB plus the size of the last build of that name free on data/'s filesystem; both readings go in the result;
  5. runs the tool, `python -I -S <tool> <inputs> <output> <args...>`, with
       * its inputs copied read-only into a scratch directory outside data/, whose empty `work` is its working directory,
       * a fresh output directory, data/builds/.tmp/<run id>/,
       * no CONCORDANCE_ variable from the unit's environment, and CONCORDANCE_DATA_DIR an empty scratch directory,
       * on Linux: oom_score_adj 1000 and the listed cap as its address-space limit, both set on its own process before
         it starts, under nice and ionice,
       * for at most 40 minutes, so the result lands before build_ship.sh stops polling at 45;
  6. hashes the output. A non-zero exit, an empty output or another hash removes it and fails the build. A match is
     renamed to data/builds/<name>/<hash>/, one rename on one filesystem; if that is already there the new copy is
     discarded, so a build is idempotent;
  7. removes the scratch directory and the staging directory on every exit, and writes the result whole (a rename).
     A removal refused for a moment is tried again briefly; one that still fails is named in the result's `cleanup`,
     never turns a landed build into a failed one, and is removed by the next build under the lock.

It writes, moves and removes nothing else. THE CONTENT HASH: for every file under the output, the line
'<sha256 of its bytes>  <its path relative to the output, with forward slashes>' and a newline; the lines sorted by
path (its UTF-8 bytes); the sha256 of them all. A symlink, a special file or an empty directory is refused, so what
lands is exactly what was hashed. Stdlib only: it runs beside the engines and never imports them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

try:
    import resource                     # POSIX only: the address-space cap and the peak resident memory
except ImportError:                     # pragma: no cover (Windows)
    resource = None

LISTING = "tools/box_builds.txt"
MAX_CAP_MB = 1024
MEM_MARGIN_MB = 256
DISK_FLOOR_BYTES = 2 * 1024 ** 3
TOOL_TIMEOUT_S = 40 * 60
NICE = ("-n", "19")
IONICE = ("-c", "2", "-n", "7")         # best effort at its lowest priority: the engines' reads go first
OOM_SCORE_ADJ = 1000                    # if memory runs short, the kernel ends the build first, never an engine
LINUX = sys.platform.startswith("linux")
TAIL_LINES = 20
CLEANUP_TRIES = 5                       # a removal refused for a moment is tried again, briefly

NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
RUN_ID_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}")
HASH_RE = re.compile(r"[0-9a-f]{64}")
_SEGMENT = r"[A-Za-z0-9_][A-Za-z0-9_.-]*"
PATH_RE = re.compile(rf"{_SEGMENT}(?:/{_SEGMENT})*")
# NAME TOOL SHA256 CAP_MB [in=PATH]... ["ARG"]...: tools/build_ship.sh checks each line against the same pattern.
ENTRY_RE = re.compile(r'([a-z0-9][a-z0-9-]{0,62}) (tools/[A-Za-z0-9_][A-Za-z0-9_-]*\.py) ([0-9a-f]{64}) ([0-9]{1,4})'
                      r'((?: in=[^ ]+)*)((?: "[A-Za-z0-9._:=,+/@%-]*")*)')
EXIT = {"built": 0, "present": 0, "failed": 1, "refused": 3}


class ListingError(ValueError):
    """tools/box_builds.txt holds a line the path will not run."""


class BuildError(Exception):
    """The build failed; nothing landed."""


class Refused(BuildError):
    """The build never started: a floor was not met."""


class Entry(NamedTuple):
    name: str
    tool: str
    hash: str
    cap_mb: int
    inputs: Tuple[str, ...]
    args: Tuple[str, ...]
    line: int


# ------------------------------------------------------------------------------------------------ the listing

def check_input(path: str) -> str:
    """A listed input is a plain repository path outside data/. It is checked after normalizing, so
    'tools/../data/x' is refused as an input under data/."""
    norm = posixpath.normpath(path) if path else ""
    low = norm.lower()
    if low == "data" or low.startswith("data/"):
        raise ListingError(f"an input under data/ is refused: {path}")
    if path.startswith("/") or "\\" in path or re.match(r"[A-Za-z]:", path):
        raise ListingError(f"an input is an absolute path: {path}")
    if norm == ".." or norm.startswith("../"):
        raise ListingError(f"an input leaves the repository by '..': {path}")
    if norm != path or not PATH_RE.fullmatch(path):
        raise ListingError(f"an input is not a plain repository path: {path}")
    return path


def parse_listing(text: str) -> Dict[str, Entry]:
    """Every entry of tools/box_builds.txt by name. Any line the path will not run refuses the whole listing."""
    entries: Dict[str, Entry] = {}
    previous = ""
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            previous = line
            continue
        m = ENTRY_RE.fullmatch(line)
        if not m:
            raise ListingError(f'line {n} is not an entry (NAME TOOL SHA256 CAP_MB [in=PATH]... ["ARG"]...): {line}')
        name, tool, digest, cap, ins, args = m.groups()
        if not previous.startswith("#") or not previous.lstrip("#").strip():
            raise ListingError(f"line {n}: {name} has no comment line just before it saying what it builds and from where")
        if name in entries:
            raise ListingError(f"line {n}: {name} is listed twice")
        cap_mb = int(cap)
        if not 1 <= cap_mb <= MAX_CAP_MB:
            raise ListingError(f"line {n}: {name}'s memory cap is {cap_mb} MB; it must be 1 to {MAX_CAP_MB}")
        inputs = tuple(check_input(tok[len("in="):]) for tok in ins.split())
        if len(set(inputs)) != len(inputs):
            raise ListingError(f"line {n}: {name} lists an input twice")
        entries[name] = Entry(name, tool, digest, cap_mb, inputs, tuple(tok[1:-1] for tok in args.split()), n)
        previous = line
    return entries


def read_listing(root: Path) -> Dict[str, Entry]:
    try:
        with open(root / LISTING, encoding="utf-8") as fh:
            return parse_listing(fh.read())
    except (OSError, UnicodeDecodeError, ListingError) as e:
        raise BuildError(f"{LISTING} is refused: {e}") from None


# ------------------------------------------------------------------------------------------------ the hash

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _collect(folder: str, rel: str, found: List[Tuple[bytes, str]]) -> None:
    with os.scandir(folder) as it:
        entries = sorted(it, key=lambda e: e.name)
    if not entries and rel:
        raise BuildError(f"an empty directory is not part of a build: {rel}")
    for e in entries:
        path = f"{rel}/{e.name}" if rel else e.name
        if any(c in e.name for c in "\\\n\r\t"):
            raise BuildError(f"a name the hash cannot hold: {path!r}")
        try:
            key = path.encode("utf-8")
        except UnicodeEncodeError:
            raise BuildError(f"a name that is not UTF-8: {path!r}") from None
        if e.is_symlink():
            raise BuildError(f"a symlink is not build output: {path}")
        if e.is_dir(follow_symlinks=False):
            _collect(e.path, path, found)
        elif e.is_file(follow_symlinks=False):
            found.append((key, _sha256_file(e.path)))
        else:
            raise BuildError(f"not a regular file: {path}")


def content_hash(top) -> str:
    """The content hash of an output directory (the module docstring defines it)."""
    top = Path(top)
    if top.is_symlink() or not top.is_dir():
        raise BuildError(f"not a directory: {top.name}")
    found: List[Tuple[bytes, str]] = []
    _collect(str(top), "", found)
    if not found:
        raise BuildError("the output is empty")
    found.sort()
    return hashlib.sha256(b"".join(d.encode("ascii") + b"  " + p + b"\n" for p, d in found)).hexdigest()


# ------------------------------------------------------------------------------------------------ the box

def take_lock(path: Path) -> Optional[int]:
    """The builds' lock, without waiting: a descriptor, or None when another build holds it. The kernel drops it when
    the descriptor closes, so a unit that dies frees it."""
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return None
    return fd


def mem_available_kb(meminfo: str) -> Optional[int]:
    """MemAvailable from a /proc/meminfo, in kB, or None when it cannot be read."""
    try:
        with open(meminfo, encoding="ascii", errors="replace") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) == 3 and parts[0] == "MemAvailable:" and parts[1].isdigit() and parts[2] == "kB":
                    return int(parts[1])
    except OSError:
        return None
    return None


def last_build(folder: Path) -> Tuple[Optional[str], int]:
    """The most recent build of a name (its hash) and its size in bytes; (None, 0) when there is none."""
    if not folder.is_dir():
        return None, 0
    built = [d for d in folder.iterdir() if HASH_RE.fullmatch(d.name) and d.is_dir() and not d.is_symlink()]
    if not built:
        return None, 0
    last = max(built, key=lambda d: d.stat().st_mtime)
    size = 0
    for dirpath, _dirs, files in os.walk(last):
        size += sum(os.lstat(os.path.join(dirpath, f)).st_size for f in files)
    return last.name, size


def remove_tree(path: Path, tries: int = CLEANUP_TRIES) -> None:
    """Remove a directory this unit made, read-only parts and all; never follows a symlink out of it. A file another
    process has only just opened (on Windows, a scanner or an indexer) can refuse removal for a moment, so a failure is
    tried again a few times, briefly, before it is raised."""
    for attempt in range(1, tries + 1):
        try:
            _remove_tree_once(path)
            return
        except OSError:
            if attempt == tries:
                raise
            time.sleep(0.1 * attempt)


def _remove_tree_once(path: Path) -> None:
    if not os.path.lexists(path):
        return
    if os.path.islink(path) or not os.path.isdir(path):
        os.unlink(path)
        return
    for dirpath, _dirs, files in os.walk(path):
        os.chmod(dirpath, 0o700)
        for f in files:
            p = os.path.join(dirpath, f)
            if not os.path.islink(p):
                os.chmod(p, 0o600)
    shutil.rmtree(path)


def staged_files(staging: Path) -> List[str]:
    """The files staged for a build, by repository path; an absent staging directory holds none."""
    if not os.path.lexists(staging):
        return []
    if staging.is_symlink() or not staging.is_dir():
        raise BuildError("the staging directory is not a directory")
    found = []
    for dirpath, dirs, files in os.walk(staging):
        for name in dirs + files:
            p = Path(dirpath) / name
            rel = p.relative_to(staging).as_posix()
            if p.is_symlink() or not (p.is_dir() or p.is_file()):
                raise BuildError(f"a staged input is not a plain file: {rel}")
            if p.is_file():
                found.append(rel)
    return sorted(found)


def copy_read_only(staging: Path, into: Path, inputs: Tuple[str, ...]) -> None:
    into.mkdir()
    for rel in sorted(inputs):
        dst = into / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(staging / rel, dst)
        os.chmod(dst, 0o444)
    for dirpath, _dirs, _files in os.walk(into, topdown=False):
        os.chmod(dirpath, 0o555)


def _confine(cap_bytes: int):
    def confine() -> None:              # in the tool's own process, after fork and before exec
        with open("/proc/self/oom_score_adj", "w") as fh:
            fh.write(str(OOM_SCORE_ADJ))
        resource.setrlimit(resource.RLIMIT_AS, (cap_bytes, cap_bytes))
    return confine


def tidy(path: Path, label: str, result: dict, root: Path) -> None:
    """Remove a directory this unit made or found left behind; if it will not go, say so in the result, never fail a
    build that has already landed, and leave it for the next build to remove under the lock."""
    try:
        remove_tree(path)
    except OSError as e:
        result.setdefault("cleanup", []).append(_scrub(f"{label} could not be removed: {e}", (root, Path(path))))


def _scrub(text: str, paths: Tuple[Path, ...]) -> str:
    for p, label in zip(paths, ("<root>", "<scratch>")):
        for form in {str(p), p.as_posix(), str(p.resolve())}:
            text = text.replace(form, label)
    return text


def run_tool(entry: Entry, root: Path, out: Path, scratch: Path, timeout: int) -> dict:
    """Run the entry's tool, confined; what the result records of the run."""
    tool = root / entry.tool
    if tool.is_symlink() or not tool.is_file():
        raise BuildError(f"the tool is not on the box: {entry.tool}")
    cmd = [sys.executable, "-I", "-S", str(tool), str(scratch / "inputs"), str(out), *entry.args]
    confinement = {"address_space_cap_mb": None, "ionice": None, "nice": None, "oom_score_adj": None}
    extra: dict = {}
    if LINUX:
        nice, ionice = shutil.which("nice"), shutil.which("ionice")
        if not nice or not ionice:
            raise BuildError("nice and ionice must both be on the box's PATH")
        cmd = [nice, *NICE, ionice, *IONICE, *cmd]
        extra = {"preexec_fn": _confine(entry.cap_mb * 1024 * 1024), "start_new_session": True}
        confinement = {"address_space_cap_mb": entry.cap_mb, "ionice": " ".join(IONICE), "nice": int(NICE[1]),
                       "oom_score_adj": OOM_SCORE_ADJ}
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("CONCORDANCE_")}
    env.update(CONCORDANCE_DATA_DIR=str(scratch / "data"), TMPDIR=str(scratch / "tmp"), TMP=str(scratch / "tmp"),
               TEMP=str(scratch / "tmp"))
    log = scratch / "tool.log"
    timed_out = False
    with open(log, "wb") as fh:
        try:
            p = subprocess.Popen(cmd, cwd=str(scratch / "work"), env=env, stdin=subprocess.DEVNULL, stdout=fh,
                                 stderr=subprocess.STDOUT, **extra)
        except (OSError, subprocess.SubprocessError) as e:
            raise BuildError(f"the tool could not be started confined: {e}") from None
        try:
            rc = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if extra:
                os.killpg(p.pid, 9)
            else:
                p.kill()
            rc = p.wait()
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss if resource is not None else None
    with open(log, "rb") as fh:
        tail = fh.read().decode("utf-8", "replace").splitlines()[-TAIL_LINES:]
    return {"confinement": confinement, "exit_code": rc, "peak_rss_kb": peak, "timed_out": timed_out,
            "tool_output_tail": [_scrub(t, (root, scratch)) for t in tail]}


# ------------------------------------------------------------------------------------------------ the commands

def _built(root: Path, builds: Path, run_id: str, name: str, staging: Path, result: dict, meminfo: str,
           disk_free: Optional[int], scratch_base: Optional[str], timeout: int) -> None:
    entry = read_listing(root).get(name)
    if entry is None:
        raise BuildError(f"{name} is not an entry of {LISTING}")
    result.update(cap_mb=entry.cap_mb, listed_hash=entry.hash, tool=entry.tool)
    staged = staged_files(staging)
    if staged != sorted(entry.inputs):
        raise BuildError(f"the staged inputs {staged} are not the entry's inputs {sorted(entry.inputs)}")

    mem = mem_available_kb(meminfo)
    last_hash, last_bytes = last_build(builds / name)
    free = disk_free if disk_free is not None else shutil.disk_usage(str(root / "data")).free
    need_mem = (entry.cap_mb + MEM_MARGIN_MB) * 1024
    need_disk = DISK_FLOOR_BYTES + last_bytes
    result["readings"] = {"disk_free_bytes": free, "disk_needed_bytes": need_disk, "last_build": last_hash,
                          "last_build_bytes": last_bytes, "mem_available_kb": mem, "mem_needed_kb": need_mem}
    if mem is None:
        raise Refused("available memory could not be read")
    if mem < need_mem:
        raise Refused(f"available memory is {mem} kB, below the floor of {need_mem} kB "
                      f"(the cap, {entry.cap_mb} MB, plus {MEM_MARGIN_MB} MB)")
    if free < need_disk:
        raise Refused(f"data/'s filesystem has {free} bytes free, below the floor of {need_disk} bytes "
                      f"(2 GB plus the {last_bytes} bytes of the last build of {name})")

    scratch = Path(tempfile.mkdtemp(prefix="nh-build-", dir=scratch_base))
    out = builds / ".tmp" / run_id
    try:
        for part in ("data", "work", "tmp"):
            (scratch / part).mkdir()
        copy_read_only(staging, scratch / "inputs", entry.inputs)
        (builds / ".tmp").mkdir(exist_ok=True)
        try:
            out.mkdir()
        except FileExistsError:
            raise BuildError(f"data/builds/.tmp/{run_id} already exists") from None
        ran = run_tool(entry, root, out, scratch, timeout)
        result.update(ran)
        if ran["timed_out"]:
            raise BuildError(f"the tool ran past {timeout} seconds and was ended")
        if ran["exit_code"] != 0:
            raise BuildError(f"the tool exited {ran['exit_code']}")
        got = content_hash(out)
        result["output_hash"] = got
        if got != entry.hash:
            raise BuildError(f"the output hashes to {got}, not to the listed {entry.hash}")
        final = builds / name / got
        final.parent.mkdir(exist_ok=True)
        result["dir"] = f"data/builds/{name}/{got}"
        if os.path.lexists(final):
            result.update(status="present", reason="this build is already there; the new copy was discarded")
        else:
            os.rename(out, final)
            result.update(status="built", reason="the output matched its listed hash and landed")
    finally:
        tidy(out, f"data/builds/.tmp/{run_id}", result, root)
        tidy(scratch, "the scratch directory", result, root)


def write_result(results: Path, run_id: str, result: dict) -> None:
    part = results / f"{run_id}.json.part"
    with open(part, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(result, indent=1, sort_keys=True) + "\n")
    os.replace(part, results / f"{run_id}.json")


def cmd_build(root: Path, run_id: str, name: str, meminfo: str = "/proc/meminfo", disk_free: Optional[int] = None,
              scratch_base: Optional[str] = None, timeout: int = TOOL_TIMEOUT_S) -> int:
    builds = root / "data" / "builds"
    results = builds / ".results"
    staging = builds / ".inputs" / run_id
    result: dict = {"name": name, "run_id": run_id, "status": "failed", "unit": "tools/box_build.py"}
    lock = None
    try:
        results.mkdir(parents=True, exist_ok=True)
        lock = take_lock(builds / ".lock")
        if lock is None:
            raise Refused("another build holds the lock, data/builds/.lock")
        for held in (builds / ".tmp", builds / ".inputs"):
            if held.is_dir():
                for child in sorted(held.iterdir()):
                    if child.name != run_id:
                        tidy(child, f"data/builds/{held.name}/{child.name}, left by an earlier unit,", result, root)
        _built(root, builds, run_id, name, staging, result, meminfo, disk_free, scratch_base, timeout)
    except Refused as e:
        result.update(status="refused", reason=str(e))
    except BuildError as e:
        result.update(status="failed", reason=str(e))
    except Exception as e:              # the unit itself broke: still a result, still no build
        result.update(status="failed", reason=_scrub(f"the unit failed: {type(e).__name__}: {e}", (root, root)))
    finally:
        tidy(staging, f"data/builds/.inputs/{run_id}", result, root)
        write_result(results, run_id, result)
        if lock is not None:
            os.close(lock)
    return EXIT[result["status"]]


def cmd_verify(root: Path, name: str, digest: str) -> int:
    where = f"data/builds/{name}/{digest}"
    found = root / "data" / "builds" / name / digest
    if found.is_symlink() or not found.is_dir():
        print(f"NOT BUILT: {where} is not on the box")
        return 1
    try:
        got = content_hash(found)
    except (BuildError, OSError) as e:
        print(f"REFUSED: {where}: {e}")
        return 1
    if got != digest:
        print(f"MISMATCH: {where} re-hashes to {got}")
        return 1
    print(f"VERIFIED: {where} is there and re-hashes to its name")
    return 0


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(prog="box_build.py", description="The box build unit (run 2026-11-11-box-build).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--root", required=True)
    b.add_argument("--run-id", required=True)
    b.add_argument("--meminfo", default="/proc/meminfo", help="a stand-in reading, for tests")
    b.add_argument("--disk-free-bytes", type=int, default=None, help="a stand-in reading, for tests")
    b.add_argument("--scratch-base", default=None, help="where scratch directories go (default: the system's)")
    b.add_argument("--tool-timeout", type=int, default=TOOL_TIMEOUT_S)
    b.add_argument("name")
    v = sub.add_parser("verify")
    v.add_argument("--root", required=True)
    v.add_argument("name")
    v.add_argument("hash")
    h = sub.add_parser("hash")
    h.add_argument("dir")
    a = ap.parse_args(argv)
    if a.cmd == "hash":
        try:
            print(content_hash(a.dir))
        except (BuildError, OSError) as e:
            print(f"refused: {e}", file=sys.stderr)
            return 1
        return 0
    if not NAME_RE.fullmatch(a.name):
        print(f"not a build name: {a.name!r}", file=sys.stderr)
        return 2
    root = Path(a.root)
    if not root.is_dir():
        print("the root is not a directory", file=sys.stderr)
        return 2
    if a.cmd == "verify":
        if not HASH_RE.fullmatch(a.hash):
            print(f"not a content hash: {a.hash!r}", file=sys.stderr)
            return 2
        return cmd_verify(root, a.name, a.hash)
    if not RUN_ID_RE.fullmatch(a.run_id):
        print(f"not a run id: {a.run_id!r}", file=sys.stderr)
        return 2
    if not 1 <= a.tool_timeout <= TOOL_TIMEOUT_S:
        print(f"the tool's time is 1 to {TOOL_TIMEOUT_S} seconds", file=sys.stderr)
        return 2
    return cmd_build(root, a.run_id, a.name, a.meminfo, a.disk_free_bytes, a.scratch_base, a.tool_timeout)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
