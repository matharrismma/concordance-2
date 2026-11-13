#!/usr/bin/env python3
"""THE MINT UNIT: the one place a tick stick's seals and marks are minted into the box's keeping (run
2026-11-13-stick-ship).

    python tools/stick_mint.py mint    NAME --root DEST --run-id RUN   on the box: mint one entry of tools/stick_mints.txt
    python tools/stick_mint.py retract NAME --root DEST --run-id RUN   on the box: withdraw the sealed marks an earlier
                                                                       mint of NAME recorded as new
    python tools/stick_mint.py entry-check --root DEST NAME HASH       read only: DEST/data/sticks/NAME.json hashes to
                                                                       HASH (CR LF as LF); the standard library only

tools/mint_ship.sh starts `mint` and `retract` on the box, detached, with a fresh run id, and polls for the result,
data/mints/.results/<run id>.json; it streams `entry-check` to the box's python before it sends or starts anything.

THE UNIT. It holds data/mints/.lock, a lock held only by mints that the kernel drops if the process dies: a second mint
is refused and writes its refusal only to its own run id's result. It refuses to start unless available memory is at
least CAP_MB plus 256 MB, and records the reading. On its command-line entry, never on import, it sets its own
oom_score_adj to 1000, its nice to 19, its ionice to best effort at 7 and CAP_MB as its address-space limit (Linux, the
box; elsewhere none of these exist and the result says so), so if memory runs short the kernel ends the mint, never an
engine. THE CAP is 512 MB. Measured on the builder's laptop (peak working set, Windows), a canary mint peaks at 75 MB in
each process that mints (the rehearsal child, 74.4 to 74.7 MB; the unit through step 3, 74.9 MB), and the unit holds
34 MB while its rehearsal runs, since it imports only the package's light modules (sticks, ledger, cas, record) before
the rehearsal and the derivation path (sympy, mpmath) only in step 3, after the rehearsal has exited. So the floor
counts both: at most about 109 MB resident at once, times four for the address space Linux counts beyond what is
resident (thread stacks, allocator reservations, shared libraries), rounded up to a power of two; on Linux the tests
show a mint completing under it. Its environment holds no CONCORDANCE_ variable from its parent and is exactly the one
the listed hashes come from: CONCORDANCE_DATA_DIR=<root>/data, CONCORDANCE_SEAL_INDEX=0 (tools/tick.py's cold seal
path: the CAS object, the ledger link and the receipt card are written, the live corpus is not touched),
CONCORDANCE_VERIFY_TIMEOUT_S=1800, CONCORDANCE_RIEMANN_MAX=1e9, WEB_FIND_DISABLED=1, and <root>/src first on its import
path. It refuses if <root>/.env names a keeping location (CONCORDANCE_DATA_DIR, _CAS_DIR, _LEDGER_DIR, _SEAL_INDEX,
_PUBLIC_BASE; it reads the names only), and unless `systemctl show nh-engine --property=Environment` names
CONCORDANCE_DATA_DIR=<root>/data, so it mints into the keeping the engine reads. Every ledger.verify_chain it reads is taken while it holds the ledger's
own chain lock (src/concordance/ledger.py _chain_lock), so no engine sealer writes mid-read, and the result records how
long each hold took. It never restarts an engine: GET /sticks and GET /stick fold data/sticks.jsonl on each request,
and the receipt cards join at the next corpus load, as they always have for tools/tick.py.

THE ORDER of a mint, fail-closed, writing nothing under data/ but data/mints/ before step 3:
  1. the listing line, the readings and the keeping (above); the catalog, loaded from <root>/data/sticks with
     concordance.sticks.load_catalog: the entry must be a data entry whose file hashes to the listed hash and whose
     seals are the listed keys, in order; ledger.verify_chain must be ok.
  2. REHEARSAL, in a child process of its own (so no module state it leaves, such as cas._COLD_CARDS_WRITTEN,
     cas._COLD_SPINE_WRITTEN or science_cards._MINTED, can reach the mint), with the unit's environment except that
     CONCORDANCE_DATA_DIR names a scratch keeping outside data/ that holds only a copy of <root>/data/sticks.jsonl:
     concordance.sticks.run(entry), exactly as step 3 runs it, so tick's own refusals (the kind, the claim and source
     lengths, the seal, a bound that does not pass the stick's current bound) apply to every mark against the box's
     current sticks. It refuses unless run returns 0, the scratch CAS holds exactly the listed hashes, each has its
     ledger record by the ledger's own naming, and every mark of the entry reads back on its stick: a tick the
     predicate concordance.sticks.mint_marks uses to skip a mark already kept selects (kind, seal, claim; a sealed mark
     whose seal is kept stays kept), holding the mark's source, up_to and unit as tickstick.tick stores them (a cited
     mark's source stripped and cut to 300, a bound's up_to as a float and its unit cut to 40), cited marks and notes
     included. A line marked expect=refused never gets past it.
     Then WOULD ADD, read only from the real keeping: for each listed hash its CAS object; its ledger record, the file
     ledger.seal_to_ledger writes for the precedent id receipts.mint gives it (ledger://<axis>/<first 16 hex>, through
     ledger._slugify, which turns an underscore into a hyphen), checked by its record_hash; its receipt card
     (data/receipt_cards.jsonl, id cas.receipt_card_id) only when the CAS object is not yet there, since the cold path
     writes a card only when it creates the object (src/concordance/cas.py store), an object already present without
     its card being recorded in the result and never required; the receipt spine card (cas._RECEIPT_SPINE), which the
     cold path writes before the first receipt card of each process, when an object would be created and the keeping
     lacks it; its verified card where the rehearsal wrote one, the object is not yet there and
     data/verified_cards.jsonl lacks it; each of the entry's sticks; and each mark the rehearsal added beyond the copy. If nothing would be added the status is present and step 3 never runs; a line
     marked expect=present refuses if anything would be added.
  3. MINT, begun no later than 10 minutes after the unit started (else refused): concordance.sticks.run(entry) on the
     real keeping, the seal path and mint loop tools/tick.py uses.
  4. READ BACK: each listed hash's CAS object verifies and its ledger record is there by the ledger's own naming with
     that record_hash; each CAS object this mint created has its receipt card (and its verified card where the
     rehearsal wrote one), and the receipt spine card is there when any was created; every mark of the entry reads
     back; the events appended to the entry's sticks during the mint equal the rehearsal's exactly; ledger.verify_chain
     is ok. Anything missing makes the status failed, naming each item. The result's marks_added holds only the events
     the rehearsal predicted; anything else that arrived on the entry's sticks meanwhile (the public POST /tick door
     writes the same log) is recorded apart, as arrived_otherwise, and is never this path's mark.
     receipts.mint swallows a failed ledger append, so a mint whose CAS write held and whose chain write failed reads
     failed here, and a later mint of the same name completes it.

WHAT A MINT WRITES: data/cas/ objects, data/ledger/ records with .chain.head and .chain.lock, data/receipt_cards.jsonl,
data/verified_cards.jsonl only where the seal path writes a verified card, data/sticks.jsonl, and data/mints/ (its lock
and its result). The rehearsal's scratch keeping is outside data/ and removed when the unit ends. A refused mint, a
failed one that ended before step 3 and a present one write only data/mints/ and, in a keeping that has none yet,
data/ledger/.chain.lock, which taking the chain lock creates. The result quotes no path but those under data/.

RETRACT refuses a line marked expect=present or expect=refused, runs the same lock, environment and step 1, and withdraws
only the sealed marks an earlier mint of the name recorded as new in its result under data/mints/.results/: a sealed
tick of that result's marks_added that the same result's rehearsal appended, carrying a seal that result listed for the
entry. Each is withdrawn on its own stick and only while it reads present there: one retract event each (concordance.tickstick.retract), none for a
mark already gone, so a second retract appends nothing. It refuses when another catalog data entry states a mark with
the same stick and seal, since a retract drops every mark on that stick carrying that seal, whoever minted it (a
handler entry states no marks in the catalog and is not seen here). It reads back that each withdrawn mark is gone and,
per listed hash, that its CAS object and ledger record are unchanged. What stays served: the stick, with its cited marks
and notes, and every CAS object, ledger record and receipt card. A cited mark or a note has no withdrawal (a want).

Its top-level imports are the standard library's alone, so `entry-check` runs streamed to the box's python; the engine
is imported only inside a mint or a retract, from <root>/src.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

try:
    import resource                     # POSIX only: the address-space cap and the peak resident memory
except ImportError:                     # pragma: no cover (Windows)
    resource = None

LISTING = "tools/stick_mints.txt"
UNIT = "tools/stick_mint.py"
CAP_MB = 512
MEM_MARGIN_MB = 256
START_DEADLINE_S = 10 * 60              # step 3 never begins later than this after the unit started
OOM_SCORE_ADJ = 1000                    # if memory runs short, the kernel ends the mint first, never an engine
NICE = 19
IONICE = ("-c", "2", "-n", "7")         # best effort at its lowest priority: the engines' reads go first
LINUX = sys.platform.startswith("linux")
ENGINE_UNIT = "nh-engine"
KEEPING_NAMES = ("CONCORDANCE_DATA_DIR", "CONCORDANCE_CAS_DIR", "CONCORDANCE_LEDGER_DIR", "CONCORDANCE_SEAL_INDEX",
                 "CONCORDANCE_PUBLIC_BASE")
SEALED_KINDS = ("bound", "instance", "witness")
TAIL_LINES = 40
CLEANUP_TRIES = 5
CHILD_LOG = "child.log"
CHILD_REPORT = "report.json"
CHILD_TASK = "task.json"

NAME_RE = re.compile(r"[a-z0-9][a-z0-9_]{0,62}")
RUN_ID_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}")
HASH_RE = re.compile(r"[0-9a-f]{64}")
# NAME ENTRY_SHA256 [KEY=HASH]... [expect=present|expect=refused]: tools/mint_ship.sh checks each line the same way.
_KEY = r"[A-Za-z0-9_().-]{1,80}"
LINE_RE = re.compile(r"([a-z0-9][a-z0-9_]{0,62}) ([0-9a-f]{64})((?: " + _KEY + r"=[0-9a-f]{64})*)"
                     r"(?: expect=(present|refused))?")
EXIT = {"minted": 0, "present": 0, "retracted": 0, "absent": 0, "failed": 1, "refused": 3}


class ListingError(ValueError):
    """tools/stick_mints.txt holds a line the path will not run."""


class MintError(Exception):
    """The mint failed."""


class Refused(MintError):
    """The mint was refused before step 3: nothing under data/ but data/mints/ was written."""


class Line(NamedTuple):
    name: str
    entry_hash: str
    seals: Tuple[Tuple[str, str], ...]
    expect: Optional[str]
    line: int


class Options(NamedTuple):
    meminfo: str = "/proc/meminfo"
    systemctl: str = "systemctl"
    scratch_base: Optional[str] = None


# ------------------------------------------------------------------------------------------------ the listing

def parse_listing(text: str) -> Dict[str, Line]:
    """Every entry of tools/stick_mints.txt by name. Any line the path will not run refuses the whole listing."""
    entries: Dict[str, Line] = {}
    previous = ""
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            previous = line
            continue
        m = LINE_RE.fullmatch(line)
        if not m:
            raise ListingError(f"line {n} is not an entry (NAME ENTRY_SHA256 [KEY=HASH]... "
                               f"[expect=present|expect=refused]): {line}")
        name, digest, seals_text, expect = m.groups()
        if not previous.startswith("#") or not previous.lstrip("#").strip():
            raise ListingError(f"line {n}: {name} has no comment line just before it saying what it mints and why")
        if name in entries:
            raise ListingError(f"line {n}: {name} is listed twice")
        seals = tuple((tok.rsplit("=", 1)[0], tok.rsplit("=", 1)[1]) for tok in seals_text.split())
        keys = [k for k, _ in seals]
        if len(set(keys)) != len(keys):
            raise ListingError(f"line {n}: {name} lists a seal key twice")
        entries[name] = Line(name, digest, seals, expect, n)
        previous = line
    return entries


def read_listing(root: Path) -> Dict[str, Line]:
    try:
        with open(root / LISTING, encoding="utf-8") as fh:
            return parse_listing(fh.read())
    except (OSError, UnicodeDecodeError, ListingError) as e:
        raise Refused(f"{LISTING} is refused: {e}") from None


def entry_sha256(raw: bytes) -> str:
    """The listing's hash of an entry file: the sha256 of its bytes with CR LF as LF (a Windows checkout writes CRLF)."""
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


# ------------------------------------------------------------------------------------------------ the box

def take_lock(path: Path) -> Optional[int]:
    """The mints' lock, without waiting: a descriptor, or None when another mint holds it. The kernel drops it when the
    descriptor closes, so a unit that dies frees it."""
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


def env_file_names(path: Path) -> List[str]:
    """The variable names an .env file sets, never their values."""
    names: List[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return names
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        names.append(line.split("=", 1)[0].strip())
    return names


def engine_data_dirs(systemctl: str) -> List[str]:
    """Every CONCORDANCE_DATA_DIR the engine's installed unit sets, as `systemctl show` prints its Environment."""
    found = shutil.which(systemctl)
    if not found:
        raise Refused(f"systemctl is not here, so the engine's unit ({ENGINE_UNIT}) cannot be read")
    try:
        done = subprocess.run([found, "show", ENGINE_UNIT, "--property=Environment"], capture_output=True, text=True,
                              timeout=60, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as e:
        raise Refused(f"systemctl show {ENGINE_UNIT} could not be run: {type(e).__name__}") from None
    if done.returncode != 0:
        raise Refused(f"systemctl show {ENGINE_UNIT} exited {done.returncode}")
    out: List[str] = []
    for line in done.stdout.splitlines():
        if line.startswith("Environment="):
            try:
                tokens = shlex.split(line[len("Environment="):])
            except ValueError:
                raise Refused(f"the Environment systemctl shows for {ENGINE_UNIT} cannot be read") from None
            out += [t.split("=", 1)[1] for t in tokens if t.startswith("CONCORDANCE_DATA_DIR=")]
    return out


def expected_environment(root: Path) -> Dict[str, str]:
    """The environment the listed hashes come from, with the box's keeping as the data directory."""
    return {"CONCORDANCE_DATA_DIR": str(root / "data"), "CONCORDANCE_RIEMANN_MAX": "1e9",
            "CONCORDANCE_SEAL_INDEX": "0", "CONCORDANCE_VERIFY_TIMEOUT_S": "1800", "WEB_FIND_DISABLED": "1"}


def set_environment(root: Path) -> None:
    """The unit's own environment, set on its command-line entry: no CONCORDANCE_ variable from its parent."""
    for k in [k for k in os.environ if k.upper().startswith("CONCORDANCE_")]:
        del os.environ[k]
    os.environ.update(expected_environment(root))


def environment_now() -> Dict[str, str]:
    return {k: os.environ[k] for k in sorted(os.environ) if k.upper().startswith("CONCORDANCE_")
            or k == "WEB_FIND_DISABLED"}


def confine() -> Tuple[Dict[str, Any], Optional[str]]:
    """On Linux: oom_score_adj 1000, nice 19, ionice best effort at 7 and the cap as the address-space limit, set on
    this process, which its rehearsal inherits. Called only from the command-line entry. (what was set, a refusal)"""
    info: Dict[str, Any] = {"address_space_cap_mb": None, "ionice": None, "nice": None, "oom_score_adj": None}
    if not LINUX:
        return info, None
    try:
        with open("/proc/self/oom_score_adj", "w") as fh:
            fh.write(str(OOM_SCORE_ADJ))
        with open("/proc/self/oom_score_adj") as fh:
            info["oom_score_adj"] = int(fh.read().strip())
        now = os.nice(0)
        if now < NICE:
            os.nice(NICE - now)
        info["nice"] = os.nice(0)
        ionice = shutil.which("ionice")
        if not ionice:
            return info, "ionice is not on the box's PATH"
        done = subprocess.run([ionice, *IONICE, "-p", str(os.getpid())], capture_output=True, timeout=60,
                              stdin=subprocess.DEVNULL)
        if done.returncode != 0:
            return info, f"ionice {' '.join(IONICE)} could not be set (exit {done.returncode})"
        info["ionice"] = " ".join(IONICE)
        cap = CAP_MB * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
        info["address_space_cap_mb"] = CAP_MB
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        return info, f"the unit could not confine itself: {type(e).__name__}: {e}"
    if info["oom_score_adj"] != OOM_SCORE_ADJ or info["nice"] != NICE:
        return info, f"the unit's oom_score_adj reads {info['oom_score_adj']} and its nice {info['nice']}"
    return info, None


def inherited_confinement() -> Dict[str, Any]:
    """What a child of the unit runs under, read on Linux: its address-space limit, oom_score_adj and nice."""
    if not LINUX:
        return {"address_space_limit_mb": None, "nice": None, "oom_score_adj": None}
    soft, _hard = resource.getrlimit(resource.RLIMIT_AS)
    with open("/proc/self/oom_score_adj") as fh:
        adj = int(fh.read().strip())
    return {"address_space_limit_mb": None if soft == resource.RLIM_INFINITY else soft // (1024 * 1024),
            "nice": os.nice(0), "oom_score_adj": adj}


def peaks() -> Dict[str, Optional[int]]:
    if resource is None:
        return {"peak_rss_kb_children": None, "peak_rss_kb_unit": None}
    return {"peak_rss_kb_children": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
            "peak_rss_kb_unit": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def remove_tree(path: Path, tries: int = CLEANUP_TRIES) -> None:
    """Remove a scratch directory this unit made. A file another process has only just opened (on Windows, a scanner)
    can refuse removal for a moment, so a failure is tried again a few times, briefly."""
    for attempt in range(1, tries + 1):
        try:
            if os.path.lexists(path):
                shutil.rmtree(path)
            return
        except OSError:
            if attempt == tries:
                raise
            time.sleep(0.1 * attempt)


class Scrub:
    """Every absolute path this unit knows, replaced by a label: a result quotes no path but those under data/."""

    def __init__(self, root: Path):
        self.pairs: List[Tuple[str, str]] = []
        self.add(root, "<root>")

    def add(self, path: Path, label: str) -> None:
        for form in {str(path), Path(path).as_posix(), str(Path(path).resolve()), Path(path).resolve().as_posix()}:
            self.pairs.append((form, label))
        self.pairs.sort(key=lambda p: -len(p[0]))

    def __call__(self, text: str) -> str:
        text = str(text)
        for form, label in self.pairs:
            text = text.replace(form, label)
        return text.replace("\\", "/") if "<root>" in text or "<scratch>" in text else text


def write_result(results: Path, run_id: str, result: dict) -> None:
    part = results / f"{run_id}.json.part"
    with open(part, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(result, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    os.replace(part, results / f"{run_id}.json")


# ------------------------------------------------------------------------------------------------ the keeping

def stick_id(question: str) -> str:
    from concordance import tickstick
    return "stick_" + tickstick._slug((question or "").strip())


def stored_fields(mark: dict) -> Dict[str, Any]:
    """The fields tickstick.tick stores for a mark beside its kind, claim and seal: a cited mark's source, stripped and
    cut to 300; a bound's up_to, as a float, and its unit, cut to 40. Any other kind stores none of them."""
    from concordance import tickstick
    kind = (mark.get("kind") or "").strip().lower()
    if kind in tickstick.CITED_KINDS:
        return {"source": (mark.get("source") or "").strip()[:300]}
    if kind == "bound":
        try:
            up_to: Optional[float] = float(mark.get("up_to"))
        except (TypeError, ValueError):
            up_to = None
        return {"up_to": up_to, "unit": (mark.get("unit") or "")[:40]}
    return {}


def entry_marks(entry: dict, listed: Dict[str, str]) -> List[Tuple[str, str, str, str, Optional[str], Dict[str, Any]]]:
    """(stick id, kind, claim, seal hash or '', seal key or None, the fields tick stores) for every mark of the entry,
    in order."""
    out = []
    for st in entry.get("sticks", []):
        sid = stick_id(st["question"])
        for m in st.get("marks", []):
            key = m.get("seal")
            out.append((sid, m["kind"], m["claim"], listed.get(key, "") if key else "", key, stored_fields(m)))
    return out


def mark_reads_back(ticks: List[dict], kind: str, claim: str, seal: str, fields: Dict[str, Any]) -> bool:
    """A mark reads back when a tick the predicate concordance.sticks.mint_marks uses to skip a mark already kept
    selects (a tick of the same kind and seal whose claim is the mark's whole claim, or, for a sealed mark, any tick of
    that kind and seal that is not a copy cut shorter than the mark: the seal governs) holds the mark's source, up_to
    and unit as tick stores them."""
    from concordance import tickstick
    want = (claim or "").strip()[:getattr(tickstick, "CLAIM_CAP", 600)]
    same = [t for t in ticks if t.get("kind") == kind and (t.get("seal") or "") == (seal or "")]
    cut = any(len(want) > len(t.get("claim") or "") and want.startswith(t.get("claim") or "") for t in same)
    chosen = [t for t in same if (t.get("claim") or "") == want] + (same if seal and not cut else [])
    return any(all(t.get(k) == v for k, v in fields.items()) for t in chosen)


def split_events(got: List[dict], predicted: List[dict]) -> Tuple[List[dict], List[dict]]:
    """The events that arrived, split into those the rehearsal predicted (each matched once, in order of arrival) and
    the rest."""
    left = list(predicted)
    mine, other = [], []
    for ev in got:
        if ev in left:
            left.remove(ev)
            mine.append(ev)
        else:
            other.append(ev)
    return mine, other


def ledger_record(data: Path, domain: str, h: str) -> Tuple[str, str]:
    """The ledger record of a seal by the ledger's own naming: the file ledger.seal_to_ledger writes for the precedent
    id receipts.mint gives it, ledger://<axis>/<first 16 hex>, through ledger._slugify (an underscore becomes a hyphen).
    (its path under data/, and 'present' when it holds that record_hash, 'absent', or 'other' when it holds another)"""
    from concordance import ledger, record
    coords = record.axis_coords_for(domain)
    axis = coords.axis if coords else domain
    name = ledger._slugify(f"ledger://{axis}/{h[:16]}".replace("ledger://", "")) + ".json"
    path = data / "ledger" / name
    if not path.exists():
        return f"data/ledger/{name}", "absent"
    try:
        rec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return f"data/ledger/{name}", "other"
    return f"data/ledger/{name}", ("present" if isinstance(rec, dict) and rec.get("record_hash") == h else "other")


def card_ids_in(path: Path, wanted: List[str]) -> set:
    """Which of the wanted card ids a cards file holds, read line by line without parsing a line that names none."""
    found: set = set()
    if not wanted or not path.exists():
        return found
    needles = {cid: f'"{cid}"' for cid in wanted}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            for cid, needle in needles.items():
                if cid not in found and needle in line:
                    try:
                        if json.loads(line).get("id") == cid:
                            found.add(cid)
                    except (ValueError, AttributeError):
                        pass
    return found


def size_and_sha(path: Path) -> Tuple[int, str]:
    """A log's size and the sha256 of its bytes, read in chunks: the box's logs are large."""
    h, n = hashlib.sha256(), 0
    if path.exists():
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
                n += len(chunk)
    return n, h.hexdigest()


def size_of(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def bytes_past(path: Path, offset: int, prefix_sha: Optional[str] = None) -> Optional[bytes]:
    """The bytes a log holds past `offset`, read without holding the rest; None when `prefix_sha` is given and the
    bytes before `offset` no longer hash to it."""
    if not path.exists():
        return b"" if offset == 0 else None
    with open(path, "rb") as fh:
        if prefix_sha is None:
            fh.seek(offset)
        else:
            h, left = hashlib.sha256(), offset
            while left:
                chunk = fh.read(min(left, 1 << 20))
                if not chunk:
                    return None
                h.update(chunk)
                left -= len(chunk)
            if h.hexdigest() != prefix_sha:
                return None
        return fh.read()


def appended_events(path: Path, offset: int, prefix_sha: str, sticks: set) -> Optional[List[dict]]:
    """The events a file gained past `offset` that touch the given sticks, each without its timestamp; None when the
    bytes before `offset` are not what they were (the log is append-only, so that is never a mint's doing)."""
    tail_bytes = bytes_past(path, offset, prefix_sha)
    if tail_bytes is None:
        return None
    out = []
    for line in tail_bytes.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict) or (ev.get("stick") if ev.get("event") != "stick" else ev.get("id")) not in sticks:
            continue
        out.append({k: v for k, v in ev.items() if k != "at"})
    return out


def appended_cards(path: Path, offset: int) -> List[Dict[str, str]]:
    """The cards a cards file gained past `offset`: each id and the seal its receipt link names."""
    out = []
    for line in (bytes_past(path, offset) or b"").decode("utf-8", errors="replace").splitlines():
        try:
            card = json.loads(line)
        except ValueError:
            continue
        if isinstance(card, dict):
            url = str((card.get("source") or {}).get("url") or "")
            out.append({"id": str(card.get("id")), "seal": url.rsplit("/s/", 1)[1] if "/s/" in url else ""})
    return out


def read_chain(data: Path, when: str) -> Dict[str, Any]:
    """ledger.verify_chain, read while this unit holds the ledger's own chain lock, and how long the hold took."""
    from concordance import ledger
    began = time.monotonic()
    with ledger._chain_lock(data / "ledger"):
        held = time.monotonic()
        report = ledger.verify_chain(data / "ledger", cas_base=data / "cas")
        done = time.monotonic()
    return {"when": when, "ok": bool(report.get("ok")), "total": report.get("total"), "verified": report.get("verified"),
            "problems": {k: len(report.get(k) or []) for k in ("tampered", "broken_links", "missing_records")},
            "lock_wait_s": round(held - began, 3), "lock_held_s": round(done - held, 3)}


def totals(data: Path, chain: Dict[str, Any]) -> Dict[str, Any]:
    from concordance import cas
    return {"cas_objects": len(cas.list_hashes(base_dir=data / "cas")), "ledger_records": chain.get("total")}


def tail(text: str, scrub: Scrub) -> List[str]:
    return [scrub(t) for t in text.splitlines()[-TAIL_LINES:]]


# ------------------------------------------------------------------------------------------------ step 1

def step_one(command: str, root: Path, name: str, result: dict, opts: Options, scrub: Scrub) -> Tuple[Line, dict]:
    """The listing line, the readings, the keeping the engine reads, the catalog entry and the chain."""
    result["step"] = 1
    line = read_listing(root).get(name)
    if line is None:
        raise Refused(f"{name} is not listed in {LISTING}")
    result.update(entry_hash=line.entry_hash, expect=line.expect, listed=dict(line.seals))
    if command == "retract" and line.expect:
        raise Refused(f"{name} is a canary (expect={line.expect}): a canary is never retracted")
    mem = mem_available_kb(opts.meminfo)
    need = (CAP_MB + MEM_MARGIN_MB) * 1024
    result["memory"].update(mem_available_kb=mem, mem_needed_kb=need)
    if mem is None:
        raise Refused("available memory could not be read")
    if mem < need:
        raise Refused(f"available memory is {mem} kB, below the floor of {need} kB (the cap, {CAP_MB} MB, "
                      f"plus {MEM_MARGIN_MB} MB)")
    named = sorted(set(env_file_names(root / ".env")) & set(KEEPING_NAMES))
    if named:
        raise Refused(f"<root>/.env names a keeping location: {', '.join(named)}")
    dirs = engine_data_dirs(opts.systemctl)
    if [os.path.normpath(d) for d in dirs] != [os.path.normpath(str(root / "data"))]:
        raise Refused(f"the engine's unit ({ENGINE_UNIT}) does not name CONCORDANCE_DATA_DIR=<root>/data, and only "
                      f"that ({len(dirs)} CONCORDANCE_DATA_DIR setting(s) read): this is not the keeping it reads")
    result["environment"] = {k: scrub(v) for k, v in environment_now().items()}
    result["import_path"] = scrub(sys.path[0])
    if environment_now() != expected_environment(root):
        raise Refused("the unit's environment is not the one the listed hashes come from")

    from concordance import sticks
    result["engine_from"] = scrub(os.path.dirname(os.path.abspath(sticks.__file__)))
    try:
        catalog = sticks.load_catalog(root / "data" / "sticks")
    except (sticks.StickError, OSError, ValueError) as e:
        raise Refused(f"the catalog is refused: {scrub(e)}") from None
    entry = catalog.entries.get(name)
    if entry is None:
        raise Refused(f"no catalog entry data/sticks/{name}.json")
    if "handler" in entry:
        raise Refused(f"{name} is a handler entry: its run is Python in tools/tick.py, and minting handler entries "
                      "is a want")
    raw = (root / "data" / "sticks" / f"{name}.json").read_bytes()
    got = entry_sha256(raw)
    if got != line.entry_hash:
        raise Refused(f"data/sticks/{name}.json hashes to {got}, not to the listed {line.entry_hash}")
    if json.loads(raw.replace(b"\r\n", b"\n").decode("utf-8")) != entry:
        raise Refused(f"data/sticks/{name}.json changed while it was read")
    keys = [s["key"] for s in entry.get("seals", [])]
    if keys != [k for k, _ in line.seals]:
        raise Refused(f"the listed seal keys {[k for k, _ in line.seals]} are not the entry's seals, in order: {keys}")
    chain = read_chain(root / "data", "before")
    result["chain"].append(chain)
    if not chain["ok"]:
        raise Refused(f"ledger.verify_chain is not ok before the mint: {chain['problems']}")
    return line, entry


# ------------------------------------------------------------------------------------------------ the child

def unit_path() -> str:
    return os.path.abspath(__file__)


def run_child(command: str, root: Path, scratch: Path, name: str, task: dict, timeout: float) -> Dict[str, Any]:
    """Run the rehearsal (or the seal-hash reading) in a child process of its own, in a scratch keeping."""
    (scratch / CHILD_TASK).write_text(json.dumps(task), encoding="utf-8")
    env = dict(os.environ)
    env["CONCORDANCE_DATA_DIR"] = str(scratch / "data")
    cmd = [sys.executable, "-I", "-B", unit_path(), command, "--root", str(root), "--scratch", str(scratch), name]
    began = time.monotonic()
    timed_out = False
    with open(scratch / CHILD_LOG, "wb") as log:
        p = subprocess.Popen(cmd, cwd=str(scratch), env=env, stdin=subprocess.DEVNULL, stdout=log,
                             stderr=subprocess.STDOUT)
        try:
            rc = p.wait(timeout=max(timeout, 0.001))
        except subprocess.TimeoutExpired:
            timed_out = True
            p.kill()
            rc = p.wait()
    try:
        report = json.loads((scratch / CHILD_REPORT).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        report = {}
    log_text = (scratch / CHILD_LOG).read_text(encoding="utf-8", errors="replace")
    return {"exit_code": rc, "timed_out": timed_out, "seconds": round(time.monotonic() - began, 2),
            "report": report, "log": log_text}


def cmd_child(command: str, root: Path, scratch: Path, name: str) -> int:
    """The child's side: `rehearse` runs the entry exactly as step 3 will; `seal-hashes` seals named seals of other
    entries. Either writes only its scratch keeping and its report there."""
    scrub = Scrub(root)
    scrub.add(scratch, "<scratch>")
    report: Dict[str, Any] = {"command": command}
    try:
        data = scratch / "data"
        if os.path.normpath(os.environ.get("CONCORDANCE_DATA_DIR", "")) != os.path.normpath(str(data)):
            raise MintError("the child's data directory is not its scratch keeping")
        if os.path.normpath(str(data)).startswith(os.path.normpath(str(root / "data")) + os.sep):
            raise MintError("a scratch keeping inside data/ is refused")
        task = json.loads((scratch / CHILD_TASK).read_text(encoding="utf-8"))
        report["environment"] = {k: scrub(v) for k, v in environment_now().items()}
        report["import_path"] = scrub(sys.path[0])
        report["confinement"] = inherited_confinement()
        from concordance import cas, sticks, tickstick
        report["engine_from"] = scrub(os.path.dirname(os.path.abspath(sticks.__file__)))
        catalog = sticks.load_catalog(root / "data" / "sticks")
        if command == "seal-hashes":
            hashes: Dict[str, Dict[str, Optional[str]]] = {}
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                for other, keys in task["seals"].items():
                    specs = {s["key"]: s for s in catalog.entries[other].get("seals", [])}
                    hashes[other] = {k: sticks.seal(specs[k]) for k in keys}
            report.update(hashes=hashes, output_tail=tail(out.getvalue(), scrub))
        else:
            entry = catalog.entries[name]
            raw = (root / "data" / "sticks" / f"{name}.json").read_bytes()
            if entry_sha256(raw) != task["entry_hash"]:
                raise MintError(f"data/sticks/{name}.json no longer hashes to the listed hash")
            listed: Dict[str, str] = task["listed"]
            marks = entry_marks(entry, listed)
            ids = {m[0] for m in marks} | {stick_id(st["question"]) for st in entry.get("sticks", [])}
            log = data / "sticks.jsonl"
            offset, prefix = size_and_sha(log)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = sticks.run(entry)
            report.update(rc=rc, output_tail=tail(out.getvalue(), scrub), cas=sorted(cas.list_hashes()))
            domains = {s["key"]: s["domain"] for s in entry.get("seals", [])}
            report["ledger_named"] = {h: ledger_record(data, domains[k], h)[1] for k, h in listed.items()}
            report["appended"] = appended_events(log, offset, prefix, ids)
            report["verified_cards"] = [c for c in appended_cards(data / "verified_cards.jsonl", 0)
                                        if c["seal"] in set(listed.values())]
            folded = tickstick.fold()
            report["marks"] = [{"stick": sid, "kind": kind, "seal": key, "claim": claim[:80],
                                "kept": mark_reads_back((folded.get(sid) or {}).get("ticks") or [], kind, claim, seal,
                                                        fields)}
                               for sid, kind, claim, seal, key, fields in marks]
    except Exception as e:              # the report says so; the unit refuses
        report["error"] = scrub(f"{type(e).__name__}: {e}")
    part = scratch / (CHILD_REPORT + ".part")
    part.write_text(json.dumps(report), encoding="utf-8")
    os.replace(part, scratch / CHILD_REPORT)
    return 0


# ------------------------------------------------------------------------------------------------ mint

def rehearse(root: Path, name: str, line: Line, result: dict, opts: Options, scrub: Scrub, scratches: List[Path],
             started: float) -> Dict[str, Any]:
    result["step"] = 2
    scratch = Path(tempfile.mkdtemp(prefix="nh-mint-", dir=opts.scratch_base))
    scratches.append(scratch)
    scrub.add(scratch, "<scratch>")
    (scratch / "data").mkdir()
    real = root / "data" / "sticks.jsonl"
    if real.exists():
        shutil.copyfile(real, scratch / "data" / "sticks.jsonl")
    left = START_DEADLINE_S - (time.monotonic() - started)
    ran = run_child("rehearse", root, scratch, name, {"entry_hash": line.entry_hash, "listed": dict(line.seals)}, left)
    report = ran["report"]
    listed = dict(line.seals)
    rehearsal = {"exit_code": ran["exit_code"], "timed_out": ran["timed_out"], "seconds": ran["seconds"],
                 **{k: report.get(k) for k in ("rc", "cas", "appended", "marks", "verified_cards", "ledger_named",
                                               "environment", "import_path", "engine_from", "confinement",
                                               "output_tail", "error")}}
    result["rehearsal"] = rehearsal
    if ran["timed_out"]:
        raise Refused(f"the rehearsal had not finished {START_DEADLINE_S} seconds after the unit started; step 3 "
                      "never begins later than that")
    if not report or report.get("error"):
        rehearsal["log_tail"] = tail(ran["log"], scrub)
        raise Refused(f"the rehearsal failed: {report.get('error') or 'it wrote no report'} (exit {ran['exit_code']})")
    if report.get("rc") != 0:
        raise Refused(f"the rehearsal's run returned {report.get('rc')}: a seal did not hold or a stick was refused")
    minted, want = set(report.get("cas") or []), set(listed.values())
    if minted != want:
        names = {h: k for k, h in listed.items()}
        raise Refused("the rehearsal did not mint exactly the listed hashes: listed and not minted "
                      f"{sorted(f'{names[h]}={h}' for h in want - minted)}; minted and not listed {sorted(minted - want)}")
    unnamed = sorted(h for h, state in (report.get("ledger_named") or {}).items() if state != "present")
    if unnamed or set(report.get("ledger_named") or {}) != want:
        raise Refused(f"the rehearsal's ledger does not hold the record of {unnamed} by the ledger's own naming")
    missing = [m for m in report.get("marks") or [] if not m.get("kept")]
    if missing:
        raise Refused("the rehearsal refused " + "; ".join(
            f"{m['kind']} on {m['stick']}" + (f" (seal {m['seal']})" if m.get("seal") else "") + f": {m['claim']!r}"
            for m in missing) + " (each is a mark of the entry the rehearsal does not read back as stated: tick refused "
                                "it, as it refuses a kind, a claim or source too short, a seal or a bound that does not "
                                "go past the stick's, or a kept mark differs from it in its source, bound or unit)")
    if report.get("appended") is None:
        raise Refused("the rehearsal's copy of data/sticks.jsonl changed under it")
    if line.expect == "refused":
        raise Refused("a line marked expect=refused passed its rehearsal: it never mints")
    return report


def would_add(root: Path, entry: dict, line: Line, report: Dict[str, Any], result: dict) -> List[dict]:
    """Every write step 3 can make, read only from the real keeping."""
    from concordance import cas, tickstick
    data = root / "data"
    domains = {s["key"]: s["domain"] for s in entry.get("seals", [])}
    verified = {c["seal"]: c["id"] for c in report.get("verified_cards") or []}
    spine = cas._RECEIPT_SPINE
    have_receipts = card_ids_in(data / "receipt_cards.jsonl", [cas.receipt_card_id(h) for _, h in line.seals] + [spine])
    have_verified = card_ids_in(data / "verified_cards.jsonl", list(verified.values()))
    items: List[dict] = []
    without_receipt, without_verified = [], []
    for key, h in line.seals:
        if not cas.exists(h, base_dir=data / "cas"):
            items.append({"item": "cas object", "path": f"data/cas/{h[:2]}/{h[2:]}.json", "seal": key, "hash": h})
            items.append({"item": "receipt card", "path": "data/receipt_cards.jsonl", "id": cas.receipt_card_id(h),
                          "seal": key, "hash": h})
            if h in verified and verified[h] not in have_verified:
                items.append({"item": "verified card", "path": "data/verified_cards.jsonl", "id": verified[h],
                              "seal": key, "hash": h})
        else:
            if cas.receipt_card_id(h) not in have_receipts:
                without_receipt.append({"id": cas.receipt_card_id(h), "seal": key, "hash": h})
            if h in verified and verified[h] not in have_verified:
                without_verified.append({"id": verified[h], "seal": key, "hash": h})
        path, state = ledger_record(data, domains[key], h)
        if state == "other":
            raise Refused(f"{path}, where the ledger names the record of {key}, holds another record")
        if state == "absent":
            items.append({"item": "ledger record", "path": path, "seal": key, "hash": h})
    if any(i["item"] == "cas object" for i in items) and spine not in have_receipts:
        # the cold path writes the receipt spine card before the first receipt card of each process (cas.py)
        items.append({"item": "receipt spine card", "path": "data/receipt_cards.jsonl", "id": spine})
    folded = tickstick.fold()
    result["sticks"] = []
    for st in entry.get("sticks", []):
        sid = stick_id(st["question"])
        if sid not in folded:
            items.append({"item": "stick", "path": "data/sticks.jsonl", "stick": sid})
        result["sticks"].append({"stick": sid, "ticks_before": len((folded.get(sid) or {}).get("ticks") or [])})
    for ev in report.get("appended") or []:
        if ev.get("event") == "tick":
            items.append({"item": "mark", "path": "data/sticks.jsonl", "stick": ev.get("stick"), "kind": ev.get("kind"),
                          "seal": ev.get("seal") or "", "claim": ev.get("claim")})
    result["present_without_receipt_card"] = without_receipt
    result["present_without_verified_card"] = without_verified
    return items


def read_back(root: Path, entry: dict, line: Line, report: Dict[str, Any], created: List[str], before: dict,
              result: dict) -> List[str]:
    """Step 4: every item the mint must have left, and what is missing."""
    from concordance import cas, tickstick
    data = root / "data"
    domains = {s["key"]: s["domain"] for s in entry.get("seals", [])}
    verified = {c["seal"]: c["id"] for c in report.get("verified_cards") or []}
    spine = cas._RECEIPT_SPINE
    receipts_now = card_ids_in(data / "receipt_cards.jsonl", [cas.receipt_card_id(h) for h in created] + [spine])
    verified_now = card_ids_in(data / "verified_cards.jsonl", [verified[h] for h in created if h in verified])
    items: List[dict] = []
    missing: List[str] = []

    def check(item: dict, ok: bool, what: str) -> None:
        item["ok"] = ok
        items.append(item)
        if not ok:
            missing.append(what)
    for key, h in line.seals:
        ok, _why = cas.verify(h, base_dir=data / "cas")
        check({"item": "cas object", "path": f"data/cas/{h[:2]}/{h[2:]}.json", "seal": key, "hash": h}, ok,
              f"the CAS object of {key} ({h})")
        path, state = ledger_record(data, domains[key], h)
        check({"item": "ledger record", "path": path, "seal": key, "hash": h}, state == "present",
              f"the ledger record of {key} ({path})")
        if h in created:
            check({"item": "receipt card", "path": "data/receipt_cards.jsonl", "id": cas.receipt_card_id(h),
                   "seal": key, "hash": h}, cas.receipt_card_id(h) in receipts_now,
                  f"the receipt card of {key} ({cas.receipt_card_id(h)})")
            if h in verified:
                check({"item": "verified card", "path": "data/verified_cards.jsonl", "id": verified[h], "seal": key,
                       "hash": h}, verified[h] in verified_now, f"the verified card of {key} ({verified[h]})")
    if created:
        check({"item": "receipt spine card", "path": "data/receipt_cards.jsonl", "id": spine}, spine in receipts_now,
              f"the receipt spine card ({spine})")
    folded = tickstick.fold()
    for sid, kind, claim, seal, key, fields in entry_marks(entry, dict(line.seals)):
        check({"item": "mark", "path": "data/sticks.jsonl", "stick": sid, "kind": kind, "seal": seal,
               "claim": claim[:80], **fields},
              mark_reads_back((folded.get(sid) or {}).get("ticks") or [], kind, claim, seal, fields),
              f"the {kind} mark on {sid}" + (f" sealed by {key}" if key else "") + f": {claim[:60]!r}")
    ids = {s["stick"] for s in result.get("sticks", [])}
    added = appended_events(data / "sticks.jsonl", before["sticks_bytes"], before["sticks_sha256"], ids)
    # This path's marks are only those its rehearsal predicted; whatever else arrived on the entry's sticks meanwhile
    # (the public POST /tick door appends to the same log) is recorded apart and is never this path's mark.
    mine, other = split_events(added or [], report.get("appended") or [])
    result["marks_added"] = mine if added is not None else None
    result["arrived_otherwise"] = other if added is not None else None
    check({"item": "marks added", "path": "data/sticks.jsonl"}, added is not None and added == report.get("appended"),
          "the events appended to the entry's sticks during the mint are not the rehearsal's exactly"
          + (f" ({len(other)} arrived otherwise)" if other else "") if added is not None else
          "data/sticks.jsonl was changed other than by an append")
    for s in result.get("sticks", []):
        s["ticks_after"] = len((folded.get(s["stick"]) or {}).get("ticks") or [])
    listed = set(h for _, h in line.seals)
    result["verified_cards_written"] = [c for c in appended_cards(data / "verified_cards.jsonl",
                                                                   before["verified_bytes"]) if c["seal"] in listed]
    receipts_written = appended_cards(data / "receipt_cards.jsonl", before["receipts_bytes"])
    result["receipt_cards_written"] = [c for c in receipts_written if c["seal"] in listed]
    result["receipt_spine_cards_written"] = sum(c["id"] == spine for c in receipts_written)
    chain = read_chain(data, "after")
    result["chain"].append(chain)
    check({"item": "chain", "path": "data/ledger"}, chain["ok"], f"ledger.verify_chain after the mint: "
                                                                 f"{chain['problems']}")
    result["read_back"] = items
    result["totals"]["after"] = totals(data, chain)
    return missing


def do_mint(root: Path, name: str, result: dict, opts: Options, scrub: Scrub, scratches: List[Path],
            started: float) -> None:
    line, entry = step_one("mint", root, name, result, opts, scrub)
    data = root / "data"
    result["totals"] = {"before": totals(data, result["chain"][0])}
    report = rehearse(root, name, line, result, opts, scrub, scratches, started)
    items = would_add(root, entry, line, report, result)
    result["would_add"] = items
    if not items:
        result.update(status="present", reason="nothing would be added: every seal, record, stick and mark is kept; "
                                               "step 3 was not run")
        return
    if line.expect == "present":
        raise Refused(f"a line marked expect=present would add {len(items)} item(s): " +
                      "; ".join(f"{i['item']} {i.get('path')}" + (f" ({i['seal']})" if i.get("seal") else "")
                                for i in items))
    if time.monotonic() - started > START_DEADLINE_S:
        raise Refused(f"more than {START_DEADLINE_S} seconds have passed since the unit started; step 3 never begins "
                      "later than that")
    from concordance import cas, sticks
    created = [h for _, h in line.seals if not cas.exists(h, base_dir=data / "cas")]
    before: Dict[str, Any] = {}
    before["sticks_bytes"], before["sticks_sha256"] = size_and_sha(data / "sticks.jsonl")
    before["verified_bytes"] = size_of(data / "verified_cards.jsonl")
    before["receipts_bytes"] = size_of(data / "receipt_cards.jsonl")
    result["step"] = 3
    out = io.StringIO()
    rc: Any = None
    try:
        with contextlib.redirect_stdout(out):
            rc = sticks.run(entry)
    except Exception as e:              # what it wrote before it broke is read back below
        result["mint_error"] = scrub(f"{type(e).__name__}: {e}")
    created = [h for h in created if cas.exists(h, base_dir=data / "cas")]
    result["mint"] = {"rc": rc, "created": created, "output_tail": tail(out.getvalue(), scrub)}
    result["step"] = 4
    missing = read_back(root, entry, line, report, created, before, result)
    if rc != 0:
        missing.insert(0, f"sticks.run returned {rc}" + (f" ({result['mint_error']})" if "mint_error" in result else ""))
    if missing:
        result.update(status="failed", reason="the read back is missing: " + "; ".join(missing))
        return
    result.update(status="minted", reason=f"minted and read back: {len(items)} item(s) added")


# ------------------------------------------------------------------------------------------------ retract

def do_retract(root: Path, name: str, result: dict, opts: Options, scrub: Scrub, scratches: List[Path],
               run_id: str) -> None:
    line, entry = step_one("retract", root, name, result, opts, scrub)
    from concordance import sticks, tickstick
    data = root / "data"
    candidates: List[Tuple[str, str]] = []
    for p in sorted((data / "mints" / ".results").glob("*.json")):
        try:
            earlier = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(earlier, dict) or earlier.get("unit") != UNIT or earlier.get("command") != "mint" \
                or earlier.get("name") != name:
            continue
        # Only a tick that result's rehearsal appended, carrying a seal that result listed for the entry: nothing that
        # arrived on the stick by another door during its mint, whatever the result recorded.
        listed = set((earlier.get("listed") or {}).values())
        mine, _other = split_events(earlier.get("marks_added") or [],
                                    (earlier.get("rehearsal") or {}).get("appended") or [])
        for ev in mine:
            pair = (str(ev.get("stick")), str(ev.get("seal") or ""))
            if ev.get("event") == "tick" and ev.get("kind") in SEALED_KINDS and HASH_RE.fullmatch(pair[1]) \
                    and pair[1] in listed and pair not in candidates:
                candidates.append(pair)
    result["recorded_as_new"] = [{"stick": s, "seal": h} for s, h in candidates]
    # Another data entry stating a mark with the same stick and seal: a retract would withdraw its mark too. Its seal's
    # hash is what its seal mints, read by sealing it in a scratch keeping in a child process, as the rehearsal does.
    on_sticks = {s for s, _ in candidates}
    stated: List[Tuple[str, str, str]] = []                 # (other entry, its seal key, the stick its mark is on)
    catalog = sticks.load_catalog(data / "sticks")
    for other in catalog:
        if other.get("handler") or other["name"] == name:
            continue
        for st in other.get("sticks", []):
            sid = stick_id(st["question"])
            if sid in on_sticks:
                stated += [(other["name"], m["seal"], sid) for m in st.get("marks", []) if m.get("seal")]
    if stated:
        result["step"] = 2
        scratch = Path(tempfile.mkdtemp(prefix="nh-mint-", dir=opts.scratch_base))
        scratches.append(scratch)
        scrub.add(scratch, "<scratch>")
        (scratch / "data").mkdir()
        seals: Dict[str, List[str]] = {}
        for other, key, _sid in stated:
            if key not in seals.setdefault(other, []):
                seals[other].append(key)
        ran = run_child("seal-hashes", root, scratch, name, {"seals": seals}, START_DEADLINE_S)
        report = ran["report"]
        if ran["timed_out"] or not report or report.get("error"):
            raise Refused(f"the other entries on these sticks could not be sealed in a scratch keeping: "
                          f"{report.get('error') or 'no report'}")
        mine = set(candidates)
        shared = sorted({f"{other}.{key}" for other, key, sid in stated
                         if (sid, (report["hashes"].get(other) or {}).get(key)) in mine})
        result["other_entries_on_these_sticks"] = sorted(seals)
        if shared:
            raise Refused(f"another catalog entry states a mark with the same stick and seal ({', '.join(shared)}): a "
                          "retract drops every mark on that stick carrying that seal, whoever minted it")
    held_before = per_hash_files(root, entry, line)
    result["step"] = 3
    folded = tickstick.fold()
    withdrawn, gone = [], []
    for sid, seal in candidates:
        if any((t.get("seal") or "") == seal for t in (folded.get(sid) or {}).get("ticks") or []):
            tickstick.retract(sid, seal, by="tools/stick_mint.py retract",
                              why=f"run {run_id}: a sealed mark the mint path recorded as new for {name}")
            withdrawn.append({"stick": sid, "seal": seal})
        else:
            gone.append({"stick": sid, "seal": seal})
    result.update(withdrawn=withdrawn, already_gone=gone)
    result["step"] = 4
    folded = tickstick.fold()
    missing = [f"the mark sealed {w['seal']} still reads present on {w['stick']}" for w in withdrawn
               if any((t.get("seal") or "") == w["seal"] for t in (folded.get(w["stick"]) or {}).get("ticks") or [])]
    held_after = per_hash_files(root, entry, line)
    missing += [f"{what} changed" for what in sorted(held_before) if held_before[what] != held_after.get(what)]
    result["unchanged"] = sorted(held_before)
    result["stays_served"] = ("the stick, with its cited marks and notes, and every CAS object, ledger record and "
                              "receipt card, which /s/<hash> and /seals keep serving")
    if missing:
        result.update(status="failed", reason="the read back is missing: " + "; ".join(missing))
    elif withdrawn:
        result.update(status="retracted", reason=f"withdrew {len(withdrawn)} sealed mark(s) this path minted as new")
    else:
        result.update(status="absent", reason="no sealed mark this path recorded as new reads present: nothing appended")


def per_hash_files(root: Path, entry: dict, line: Line) -> Dict[str, Optional[str]]:
    """For each listed hash, the sha256 of its CAS object and of its ledger record (None when absent)."""
    data = root / "data"
    domains = {s["key"]: s["domain"] for s in entry.get("seals", [])}
    out: Dict[str, Optional[str]] = {}
    for key, h in line.seals:
        obj = data / "cas" / h[:2] / f"{h[2:]}.json"
        out[f"data/cas/{h[:2]}/{h[2:]}.json"] = hashlib.sha256(obj.read_bytes()).hexdigest() if obj.exists() else None
        path, _state = ledger_record(data, domains[key], h)
        p = root / path
        out[path] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    return out


# ------------------------------------------------------------------------------------------------ the unit

def run_unit(command: str, root: Path, run_id: str, name: str, opts: Options = Options(),
             confinement: Optional[Dict[str, Any]] = None, refusal: Optional[str] = None,
             started: Optional[float] = None) -> int:
    """One mint or retract, under the lock, its result written whole (a rename) whatever happens."""
    started = time.monotonic() if started is None else started
    root = Path(root)
    mints = root / "data" / "mints"
    results = mints / ".results"
    scrub = Scrub(root)
    result: Dict[str, Any] = {"command": command, "name": name, "run_id": run_id, "status": "failed", "step": 0,
                              "unit": UNIT, "cap_mb": CAP_MB, "chain": [],
                              "confinement": confinement or {"address_space_cap_mb": None, "ionice": None,
                                                             "nice": None, "oom_score_adj": None},
                              "memory": {"cap_mb": CAP_MB}}
    lock = None
    scratches: List[Path] = []
    try:
        results.mkdir(parents=True, exist_ok=True)
        lock = take_lock(mints / ".lock")
        if lock is None:
            raise Refused("another mint holds the lock, data/mints/.lock")
        if refusal:
            raise Refused(refusal)
        if command == "mint":
            do_mint(root, name, result, opts, scrub, scratches, started)
        else:
            do_retract(root, name, result, opts, scrub, scratches, run_id)
    except Refused as e:
        result.update(status="refused", reason=scrub(e))
    except MintError as e:
        result.update(status="failed", reason=scrub(e))
    except Exception as e:              # the unit itself broke: still a result
        result.update(status="failed", reason=scrub(f"the unit failed: {type(e).__name__}: {e}"))
    finally:
        for scratch in scratches:
            try:
                remove_tree(scratch)
            except OSError as e:
                result.setdefault("cleanup", []).append(scrub(f"the scratch keeping could not be removed: {e}"))
        result["memory"].update(peaks())
        result["seconds"] = round(time.monotonic() - started, 2)
        write_result(results, run_id, result)
        if lock is not None:
            os.close(lock)
    return EXIT[result["status"]]


def cmd_entry_check(root: Path, name: str, digest: str) -> int:
    where = f"data/sticks/{name}.json"
    path = root / "data" / "sticks" / f"{name}.json"
    if path.is_symlink() or not path.is_file():
        print(f"ENTRY ABSENT: {where} is not on the box")
        return 1
    got = entry_sha256(path.read_bytes())
    if got != digest:
        print(f"ENTRY DIFFERS: {where} on the box hashes to {got}, not to the listed {digest}")
        return 1
    print(f"ENTRY MATCHES: {where} on the box hashes to the listed {digest}")
    return 0


def main(argv: List[str]) -> int:
    started = time.monotonic()
    ap = argparse.ArgumentParser(prog="stick_mint.py", description="The mint unit (run 2026-11-13-stick-ship).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for cmd in ("mint", "retract"):
        p = sub.add_parser(cmd)
        p.add_argument("name")
        p.add_argument("--root", required=True)
        p.add_argument("--run-id", required=True)
        p.add_argument("--meminfo", default="/proc/meminfo", help="a stand-in reading, for tests")
        p.add_argument("--systemctl", default="systemctl", help="a stand-in systemctl, for tests")
        p.add_argument("--scratch-base", default=None, help="where the scratch keeping goes (default: the system's)")
    c = sub.add_parser("entry-check")
    c.add_argument("--root", required=True)
    c.add_argument("name")
    c.add_argument("hash")
    for cmd in ("rehearse", "seal-hashes"):         # the unit's own children
        p = sub.add_parser(cmd)
        p.add_argument("name")
        p.add_argument("--root", required=True)
        p.add_argument("--scratch", required=True)
    a = ap.parse_args(argv)
    if not NAME_RE.fullmatch(a.name):
        print(f"not a listed name: {a.name!r}", file=sys.stderr)
        return 2
    root = Path(os.path.abspath(a.root))
    if not (root / "data").is_dir():
        print("the root holds no data/ directory", file=sys.stderr)
        return 2
    if a.cmd == "entry-check":
        if not HASH_RE.fullmatch(a.hash):
            print(f"not an entry hash: {a.hash!r}", file=sys.stderr)
            return 2
        return cmd_entry_check(root, a.name, a.hash)
    sys.dont_write_bytecode = True                  # nothing written outside data/, not even a .pyc
    sys.path.insert(0, str(root / "src"))
    if a.cmd in ("rehearse", "seal-hashes"):
        return cmd_child(a.cmd, root, Path(os.path.abspath(a.scratch)), a.name)
    if not RUN_ID_RE.fullmatch(a.run_id):
        print(f"not a run id: {a.run_id!r}", file=sys.stderr)
        return 2
    set_environment(root)
    confinement, refusal = confine()
    return run_unit(a.cmd, root, a.run_id, a.name, Options(a.meminfo, a.systemctl, a.scratch_base), confinement,
                    refusal, started)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
