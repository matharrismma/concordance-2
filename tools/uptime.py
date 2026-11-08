"""The outside watch: read the public faces from off the box, and push to the owner's phone when the site stays down,
and once more when every face is back. Run by .github/workflows/uptime.yml; its record is harness run
2026-11-07-outside-uptime, plan five.

    python3 tools/uptime.py --state PATH [--ntfy BASE_URL]

    NTFY_TOPIC     the repository secret: the topic is the only credential ntfy.sh has, so it is never written
    UPTIME_DRILL   "yes" for a drill run by hand
    GITHUB_RUN_ID, GITHUB_RUN_ATTEMPT, GITHUB_STEP_SUMMARY, GITHUB_OUTPUT   given by the runner

It only reads and reports. Five public GETs, no POST, no seal page, no session id; it holds no key to the box,
restarts nothing, writes nothing on any face, opens no issue and sends no email. Standard library only.

THE READS. Healthy is a 200 with the body only that face gives (see FACES). A 429 is up, as ratelimited, only with the
engine's own rate-limit body. A healthy answer over 10 s is slow and up. Redirects are not followed. Certificates are
checked with the default context. Each try has a hard deadline of 25 s kept from outside the read, so it covers the
lookup, the connection, TLS and the whole body; a face is down in a run only when all three tries, 20 s apart, fail.
The faces are read side by side, so the reads end within 115 s.

THE DECISION is pure (observe, due, settle) over a small versioned state kept between runs by actions/cache. The site
is called down when some face is down in two of its last three runs, and back when every face is healthy in three
runs in a row. A push goes out whenever the call differs from the call last delivered, at most six in a UTC day, the
weekly heartbeat aside; a push withheld by the cap or refused by ntfy stays owed and the next run sends it as a
catch-up. A state that is missing, does not parse, fails validation or has another version is no state: the run
starts clean, called up with up delivered, so it pushes nothing.

WHAT IT WRITES, to the push, the job summary and the run log alike: the face URLs, times, HTTP status numbers and one
word per try from WORDS. Never an exception's text, a body or a header; a crash writes the word crash and the
exception's class name, and the tool exits 0 on every path. It sets the step output finished only when it finished,
so the workflow saves no state after a crash.

NAMED MISSES, by design: a face that answers one read in three is up and is never called down; a face can be called
back while still failing some reads; a cache lost in the middle of an outage starts the next run from up, so its back
push can be missed; a crash that comes from the code repeats every run and pushes nothing, which the missing Monday
heartbeat shows. It does not see a face that answers health while failing other reads.
"""
from __future__ import annotations

import copy
import http.client
import json
import os
import re
import socket
import ssl
import sys
import tempfile
import threading
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

VERSION = 1                                  # the state's format; any other version is no state
UA = "matharrismma/concordance-2 uptime watch (+https://github.com/matharrismma/concordance-2)"
WORDS = ("ok", "slow", "timeout", "refused", "dns", "tls", "reset", "status", "body", "redirect", "ratelimited")
UP_WORDS = frozenset({"ok", "slow", "ratelimited"})
DAILY_CAP = 6                                # pushes in a UTC day, the heartbeat aside
LOG_MAX = 12                                 # undelivered call changes kept for the next push
MAX_BODY = 65536                             # a health body is small; anything larger is not healthy
STATE_MAX = 262144
HEARTBEAT_HOUR = 13                          # Monday 13:00 UTC
TOPIC_RX = re.compile(r"^[A-Za-z0-9_-]{1,64}\Z")
RUN_RX = re.compile(r"^(?:[0-9]{1,20}|local)\Z")
STAMP_RX = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")
DAY_RX = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
WEEK_RX = re.compile(r"^[0-9]{4}-W[0-9]{2}\Z")
STAMP = "%Y-%m-%dT%H:%M:%SZ"
# Each pattern ends at \Z, never $: in Python $ also matches before a trailing newline.

READ_HEADERS = (("User-Agent", UA), ("Accept", "*/*"), ("Accept-Encoding", "identity"), ("Connection", "close"))


class Timing(NamedTuple):
    deadline: float = 25.0       # each read try, kept from outside it; above V3's own 18.8 s with 32 busy threads
    gap: float = 20.0            # between tries of one face
    tries: int = 3
    slow: float = 10.0           # a healthy answer over this is slow, and up
    push_deadline: float = 10.0  # each push attempt, kept from outside it
    push_tries: int = 3          # a refused push is tried twice more
    push_gap: float = 5.0

    def read_bound(self) -> float:
        return self.tries * self.deadline + (self.tries - 1) * self.gap

    def push_bound(self) -> float:
        return self.push_tries * self.push_deadline + (self.push_tries - 1) * self.push_gap


class Face(NamedTuple):
    url: str
    healthy: Callable[[bytes], bool]
    ratelimit: Optional[Callable[[bytes], bool]]


class Try(NamedTuple):
    word: str
    status: Optional[int]
    seconds: float


class FaceRead(NamedTuple):
    url: str
    tries: Tuple[Try, ...]
    up: bool


class Push(NamedTuple):
    kind: str                    # call, heartbeat or drill
    title: str
    body: str
    priority: str
    week: Optional[str]


# ------------------------------------------------------------------------------------------ the faces

MCP_RETRY_LINE = b"retry: 60000\n\n: narrowhighway keeps no server-initiated stream; POST for tools\n\n"
ENGINE_RATE_LIMITED = {"error": "rate limit exceeded", "code": "RATE_LIMITED"}


def _json_object(body: bytes) -> Optional[Dict[str, Any]]:
    try:
        obj = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None
    return obj if isinstance(obj, dict) else None


def healthy_secular(body: bytes) -> bool:
    """nh-engine's health on .com and .tv: ok true and surface secular."""
    obj = _json_object(body)
    return obj is not None and obj.get("ok") is True and obj.get("surface") == "secular"


def healthy_v3(body: bytes) -> bool:
    """V3's health on the api: exactly {"ok": true}."""
    obj = _json_object(body)
    return obj is not None and obj == {"ok": True} and obj["ok"] is True


def healthy_mcp(body: bytes) -> bool:
    """nh-mcp's GET /mcp: its fixed retry line. V3 gives the same line, so this face cannot tell which answered."""
    return body == MCP_RETRY_LINE


def healthy_witness(body: bytes) -> bool:
    """The witness app on .org: ok true, surface witness, and the commit and doors fields only the app adds; the
    engine's own witness listener, the documented rollback for .org, answers ok true and surface witness without them."""
    obj = _json_object(body)
    return (obj is not None and obj.get("ok") is True and obj.get("surface") == "witness"
            and isinstance(obj.get("commit"), str) and isinstance(obj.get("doors"), list))


def engine_ratelimited(body: bytes) -> bool:
    """The engine's own 429 body; any other 429 reads as status."""
    return _json_object(body) == ENGINE_RATE_LIMITED


def never_healthy(body: bytes) -> bool:
    return False


FACES: Tuple[Face, ...] = (
    Face("https://narrowhighway.com/health", healthy_secular, engine_ratelimited),
    Face("https://narrowhighway.tv/health", healthy_secular, engine_ratelimited),
    Face("https://api.narrowhighway.com/health", healthy_v3, None),
    Face("https://api.narrowhighway.com/mcp", healthy_mcp, engine_ratelimited),
    Face("https://narrowhighway.org/health", healthy_witness, None),
)
# The drill's sixth face: a closed port on the runner itself, so a drill touches no public face.
DRILL_FACE = Face("http://127.0.0.1:9/health", never_healthy, None)


def tls_context() -> ssl.SSLContext:
    """Certificates are checked with the default context, and nothing here loosens it."""
    return ssl.create_default_context()


# ------------------------------------------------------------------------------------------ one bounded exchange

class _Abandoned(Exception):
    """The deadline passed: the exchange was given up from outside, and its sockets closed."""


class ReadOverrun(Exception):
    """A face's reads outlived every bound; never expected, and written as a class name like any crash."""


def _close(sock: socket.socket) -> None:
    try:
        socket.socket.shutdown(sock, socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        sock.close()
    except OSError:
        pass


class _Cell:
    """What one exchange shares with the watcher that keeps its deadline."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.socks: List[socket.socket] = []
        self.abandoned = False
        self.stage = "dns"
        self.value: Any = None
        self.error: Optional[BaseException] = None

    def adopt(self, sock: socket.socket) -> None:
        with self.lock:
            if not self.abandoned:
                self.socks.append(sock)
                return
        _close(sock)
        raise _Abandoned()

    def abandon(self) -> None:
        with self.lock:
            self.abandoned = True
        self.release()

    def release(self) -> None:
        with self.lock:
            socks, self.socks = list(self.socks), []
        for s in socks:
            _close(s)


def _bounded(fn: Callable[[_Cell], Any], deadline: float) -> Tuple[_Cell, bool]:
    """Run fn on its own thread and wait for it at most `deadline` seconds, from outside it. (cell, timed out)."""
    cell = _Cell()
    done = threading.Event()

    def work() -> None:
        try:
            cell.value = fn(cell)
        except BaseException as e:           # held for the caller; nothing is printed from this thread
            cell.error = e
        finally:
            cell.release()
            done.set()
    threading.Thread(target=work, name="uptime-exchange", daemon=True).start()
    if not done.wait(deadline):
        cell.abandon()
        return cell, True
    return cell, False


def _exchange(cell: _Cell, method: str, url: str, headers: Sequence[Tuple[str, str]], body: Optional[bytes],
              deadline: float, resolver: Optional[Callable], ctx_factory: Optional[Callable]) -> Tuple[int, bytes]:
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    https = parts.scheme == "https"
    port = parts.port or (443 if https else 80)
    target = (parts.path or "/") + ("?" + parts.query if parts.query else "")
    cell.stage = "dns"
    infos = (resolver or socket.getaddrinfo)(host, port, 0, socket.SOCK_STREAM)
    if not infos:
        raise socket.gaierror("no address")
    cell.stage = "connect"
    sock = None
    last: Optional[BaseException] = None
    for family, kind, proto, _, addr in infos:   # every address, within the one deadline kept from outside
        try:
            s = socket.socket(family, kind, proto)   # a family the runner cannot make, such as IPv6, is one more miss
        except OSError as e:
            last = e
            continue
        cell.adopt(s)
        s.settimeout(deadline)               # a backstop for the thread only; the deadline is kept from outside
        try:
            s.connect(addr)
        except OSError as e:
            last = e
            _close(s)
            continue
        sock = s
        break
    if sock is None:
        raise last if last is not None else socket.gaierror("no address")
    if https:
        cell.stage = "tls"
        sock = (ctx_factory or tls_context)().wrap_socket(sock, server_hostname=host)
        cell.adopt(sock)
    cell.stage = "http"
    conn = http.client.HTTPConnection(host, port, timeout=deadline)
    conn.sock = sock
    conn.putrequest(method, target, skip_host=True, skip_accept_encoding=True)
    default = 443 if https else 80
    conn.putheader("Host", host if port == default else f"{host}:{port}")
    for k, v in headers:
        conn.putheader(k, v)
    if body is not None:
        conn.putheader("Content-Length", str(len(body)))
    conn.endheaders(body)
    resp = conn.getresponse()
    data = resp.read(MAX_BODY + 1)
    status = resp.status
    conn.close()
    return status, data


def _word_for(e: BaseException, stage: str) -> Optional[str]:
    """The one word for a failed exchange, or None when the failure is not the network's: then it is a crash."""
    if isinstance(e, TimeoutError):
        return "timeout"
    if stage == "dns":
        return "dns" if isinstance(e, (OSError, UnicodeError)) else None
    if isinstance(e, ssl.SSLError):
        return "tls"
    if stage == "connect":
        return "refused" if isinstance(e, OSError) else None
    if stage == "tls":
        if isinstance(e, ConnectionError):
            return "reset"
        return "tls" if isinstance(e, OSError) else None
    if isinstance(e, (http.client.HTTPException, OSError)):
        return "reset"
    return None


def classify(face: Face, status: int, body: bytes, seconds: float, slow: float) -> str:
    if status == 200:
        if len(body) > MAX_BODY or not face.healthy(body):
            return "body"
        return "slow" if seconds > slow else "ok"
    if 300 <= status < 400:
        return "redirect"
    if status == 429 and face.ratelimit is not None and len(body) <= MAX_BODY and face.ratelimit(body):
        return "ratelimited"
    return "status"


def read_try(face: Face, timing: Timing, resolver: Optional[Callable] = None,
             ctx_factory: Optional[Callable] = None) -> Try:
    start = time.monotonic()
    cell, late = _bounded(lambda c: _exchange(c, "GET", face.url, READ_HEADERS, None, timing.deadline, resolver,
                                              ctx_factory), timing.deadline)
    seconds = time.monotonic() - start
    if late:
        return Try("timeout", None, seconds)
    if cell.error is not None:
        word = _word_for(cell.error, cell.stage)
        if word is None:
            raise cell.error
        return Try(word, None, seconds)
    status, body = cell.value
    return Try(classify(face, status, body, seconds, timing.slow), status, seconds)


def read_face(face: Face, timing: Timing, resolver: Optional[Callable] = None,
              ctx_factory: Optional[Callable] = None) -> FaceRead:
    tries: List[Try] = []
    for n in range(timing.tries):
        if n:
            time.sleep(timing.gap)
        t = read_try(face, timing, resolver, ctx_factory)
        tries.append(t)
        if t.word in UP_WORDS:
            break
    return FaceRead(face.url, tuple(tries), tries[-1].word in UP_WORDS)


def read_faces(faces: Sequence[Face], timing: Timing, resolver: Optional[Callable] = None,
               ctx_factory: Optional[Callable] = None) -> List[FaceRead]:
    """Every face side by side, each on its own thread."""
    out: List[Optional[FaceRead]] = [None] * len(faces)
    errors: List[Optional[BaseException]] = [None] * len(faces)

    def one(i: int, f: Face) -> None:
        try:
            out[i] = read_face(f, timing, resolver, ctx_factory)
        except BaseException as e:
            errors[i] = e
    threads = [threading.Thread(target=one, args=(i, f), name="uptime-face", daemon=True) for i, f in enumerate(faces)]
    for t in threads:
        t.start()
    until = time.monotonic() + timing.read_bound() + 30.0
    for t in threads:
        t.join(max(0.0, until - time.monotonic()))
    for e in errors:
        if e is not None:
            raise e
    if any(t.is_alive() for t in threads) or any(r is None for r in out):
        raise ReadOverrun()
    return [r for r in out if r is not None]


# ------------------------------------------------------------------------------------------ the push

def push_url(base: str, topic: str) -> str:
    """The topic goes in the path, so it goes only over HTTPS, or to a stand-in on 127.0.0.1."""
    parts = urllib.parse.urlsplit(base)
    local = parts.scheme == "http" and parts.hostname == "127.0.0.1"
    if not (parts.scheme == "https" or local) or parts.query or parts.fragment:
        raise ValueError("push base")
    if not TOPIC_RX.match(topic or ""):
        raise ValueError("topic")
    return base.rstrip("/") + "/" + topic


def ascii_header(text: str) -> str:
    """http.client refuses anything but Latin-1 in a header, and a line break would end it: printable ASCII only."""
    return "".join(c if 32 <= ord(c) < 127 else "?" for c in text)[:200]


def send_push(base: str, topic: str, push: Push, timing: Timing, resolver: Optional[Callable] = None,
              ctx_factory: Optional[Callable] = None) -> bool:
    """One push by HTTPS POST, plain text, with a title and a priority and no attachment, link or click action.
    Each attempt is held to its deadline from outside; a refusal or a timeout is tried twice more, then left owed."""
    url = push_url(base, topic)
    headers = (("User-Agent", UA), ("Title", ascii_header(push.title)), ("Priority", ascii_header(push.priority)),
               ("Content-Type", "text/plain; charset=utf-8"), ("Connection", "close"))
    data = push.body.encode("utf-8")
    for n in range(timing.push_tries):
        if n:
            time.sleep(timing.push_gap)
        cell, late = _bounded(lambda c: _exchange(c, "POST", url, headers, data, timing.push_deadline, resolver,
                                                  ctx_factory), timing.push_deadline)
        if late:
            continue
        if cell.error is not None:
            if _word_for(cell.error, cell.stage) is None:
                raise cell.error
            continue
        status, _ = cell.value
        if 200 <= status < 300:
            return True
    return False


# ------------------------------------------------------------------------------------------ the state

def stamp(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime(STAMP)


def due_week(now: datetime) -> str:
    """The ISO week whose Monday 13:00 UTC is the latest at or before `now`."""
    y, w, _ = (now.astimezone(timezone.utc) - timedelta(hours=HEARTBEAT_HOUR)).isocalendar()
    return f"{y:04d}-W{w:02d}"


def clean_state(faces: Sequence[Face], now: datetime) -> Dict[str, Any]:
    """No state: called up with up delivered, and the heartbeat of the week now due counted as sent, so the first run
    pushes nothing."""
    t = stamp(now)
    return {"version": VERSION, "created": t, "runs": 0, "saved_by": None,
            "faces": {f.url: [] for f in faces}, "streak": 0,
            "call": {"call": "up", "since": t, "run": 0},
            "delivered": {"call": "up", "since": t},
            "log": [], "log_dropped": 0,
            "day": {"day": t[:10], "pushes": 0},
            "heartbeat": {"week": due_week(now), "since": t, "runs": 0, "all_up": 0, "false_alarms": 0}}


_TOP = {"version", "created", "runs", "saved_by", "faces", "streak", "call", "delivered", "log", "log_dropped", "day",
        "heartbeat"}


def _count(x: Any) -> bool:
    return type(x) is int and 0 <= x <= 10 ** 9


def _stamp_ok(x: Any) -> bool:
    if not isinstance(x, str) or not STAMP_RX.match(x):
        return False
    try:
        datetime.strptime(x, STAMP)
    except ValueError:
        return False
    return True


def _day_ok(x: Any) -> bool:
    if not isinstance(x, str) or not DAY_RX.match(x):
        return False
    try:
        datetime.strptime(x, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _keys(x: Any, keys: set) -> bool:
    return isinstance(x, dict) and set(x) == keys


def valid(s: Any, urls: Sequence[str]) -> bool:
    """Every field the decision reads, with its type, so a state that passes cannot crash the decision. The faces must
    be exactly the code's faces: a state saved before the face list changed is no state."""
    if not _keys(s, _TOP) or type(s["version"]) is not int or s["version"] != VERSION:
        return False
    if not (_stamp_ok(s["created"]) and _count(s["runs"]) and _count(s["streak"]) and _count(s["log_dropped"])):
        return False
    sb = s["saved_by"]
    if sb is not None and not (_keys(sb, {"run", "attempt"}) and all(isinstance(sb[k], str) and RUN_RX.match(sb[k])
                                                                      for k in ("run", "attempt"))):
        return False
    faces = s["faces"]
    if not isinstance(faces, dict) or set(faces) != set(urls) or len(urls) != len(set(urls)):
        return False
    for h in faces.values():
        if not isinstance(h, list) or len(h) > 3 or any(x not in ("up", "down") for x in h):
            return False
    call, delivered = s["call"], s["delivered"]
    if not (_keys(call, {"call", "since", "run"}) and call["call"] in ("up", "down") and _stamp_ok(call["since"])
            and _count(call["run"]) and call["run"] <= s["runs"]):
        return False
    if not (_keys(delivered, {"call", "since"}) and delivered["call"] in ("up", "down")
            and _stamp_ok(delivered["since"])):
        return False
    log = s["log"]
    if not isinstance(log, list) or len(log) > LOG_MAX:
        return False
    for e in log:
        if _keys(e, {"call", "at", "faces"}) and e["call"] == "down":
            f = e["faces"]
            if not (isinstance(f, list) and f and all(isinstance(u, str) and u in faces for u in f)
                    and len(set(f)) == len(f) and _stamp_ok(e["at"])):
                return False
        elif not (_keys(e, {"call", "at"}) and e["call"] == "up" and _stamp_ok(e["at"])):
            return False
    if log and log[-1]["call"] != call["call"]:
        return False
    if not log and (s["log_dropped"] or delivered != {"call": call["call"], "since": call["since"]}):
        return False
    day, hb = s["day"], s["heartbeat"]
    if not (_keys(day, {"day", "pushes"}) and _day_ok(day["day"]) and _count(day["pushes"])):
        return False
    if not (_keys(hb, {"week", "since", "runs", "all_up", "false_alarms"}) and isinstance(hb["week"], str)
            and WEEK_RX.match(hb["week"]) and _stamp_ok(hb["since"])
            and all(_count(hb[k]) for k in ("runs", "all_up", "false_alarms"))):
        return False
    return True


def load_state(path: Any, faces: Sequence[Face]) -> Tuple[Optional[Dict[str, Any]], str]:
    """(state, "restored"), or (None, why): missing, does not parse, fails validation, another version."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read(STATE_MAX + 1)
    except FileNotFoundError:
        return None, "missing"
    except OSError:
        return None, "does not parse"
    if len(raw) > STATE_MAX:
        return None, "fails validation"
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None, "does not parse"
    if not isinstance(obj, dict) or type(obj.get("version")) is not int:
        return None, "fails validation"
    if obj["version"] != VERSION:
        return None, "another version"
    if not valid(obj, [f.url for f in faces]):
        return None, "fails validation"
    return obj, "restored"


def save_state(path: Any, state: Dict[str, Any]) -> None:
    data = json.dumps(state, separators=(",", ":"), ensure_ascii=True) + "\n"      # the faces keep the code's order
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".uptime-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="ascii", newline="\n") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


# ------------------------------------------------------------------------------------------ the decision (pure)

def _append_log(s: Dict[str, Any], entry: Dict[str, Any]) -> None:
    s["log"].append(entry)
    while len(s["log"]) > LOG_MAX:
        s["log"].pop(0)
        s["log_dropped"] += 1


def observe(state: Dict[str, Any], ups: Dict[str, bool], now: datetime) -> Dict[str, Any]:
    """One run's readings into the state: the faces' last three runs, the streak, the call and the counts."""
    s = copy.deepcopy(state)
    t = stamp(now)
    s["runs"] += 1
    hb = s["heartbeat"]
    hb["runs"] += 1
    for url, hist in s["faces"].items():
        hist.append("up" if ups[url] else "down")
        del hist[:-3]
    if all(ups[url] for url in s["faces"]):
        s["streak"] += 1
        hb["all_up"] += 1
    else:
        s["streak"] = 0
    down = [url for url, hist in s["faces"].items() if hist.count("down") >= 2]
    if s["call"]["call"] == "up" and down:
        s["call"] = {"call": "down", "since": t, "run": s["runs"]}
        _append_log(s, {"call": "down", "at": t, "faces": down})
    elif s["call"]["call"] == "down" and s["streak"] >= 3:
        if s["runs"] - s["call"]["run"] <= 3:
            hb["false_alarms"] += 1          # back within three runs of the down call: a likely false alarm
        s["call"] = {"call": "up", "since": t, "run": s["runs"]}
        _append_log(s, {"call": "up", "at": t})
    return s


def pushes_today(s: Dict[str, Any], now: datetime) -> int:
    return s["day"]["pushes"] if s["day"]["day"] == stamp(now)[:10] else 0


def compose_call(s: Dict[str, Any], now: datetime) -> Push:
    """Every call change since the last delivered push, in one push."""
    log = s["log"]
    lines: List[str] = []
    if log[0]["at"] != stamp(now):
        lines.append(f"Catch-up: this push was owed since {log[0]['at']}.")
    if s["log_dropped"]:
        lines.append(f"{s['log_dropped']} earlier calls are not shown.")
    down_since = s["delivered"]["since"] if s["delivered"]["call"] == "down" and not s["log_dropped"] else None
    down_faces: List[str] = []
    for e in log:
        if e["call"] == "down":
            down_since, down_faces = e["at"], e["faces"]
        else:
            named = (": " + ", ".join(down_faces)) if down_faces else ""
            lines.append(f"Down from {down_since or 'an earlier call'} to {e['at']}{named}.")
            down_since, down_faces = None, []
    if s["call"]["call"] == "down":
        lines.append(f"Down since {s['call']['since']}: " + ", ".join(log[-1]["faces"])
                     + " (each down in 2 of its last 3 runs).")
        return Push("call", "Narrow Highway: DOWN", "\n".join(lines) + "\n", "high", None)
    lines.append(f"Back since {s['call']['since']}: every face healthy in 3 runs in a row.")
    return Push("call", "Narrow Highway: BACK", "\n".join(lines) + "\n", "default", None)


def compose_heartbeat(s: Dict[str, Any], now: datetime, week: str) -> Push:
    hb, c = s["heartbeat"], s["call"]
    lines = ["The outside watch is running.",
             f"Since {hb['since']}: {hb['runs']} runs, {hb['all_up']} of them with every face up.",
             f"Down calls that recovered within 3 runs (likely false alarms): {hb['false_alarms']}.",
             f"The state has carried {s['runs']} runs since {s['created']}.",
             f"Site now: {c['call']} since {c['since']}."]
    return Push("heartbeat", "Narrow Highway: watch running", "\n".join(lines) + "\n", "low", week)


def due(s: Dict[str, Any], now: datetime) -> Tuple[List[Push], bool]:
    """(the pushes due now, whether the daily cap withheld the call push)."""
    pushes: List[Push] = []
    capped = False
    if s["log"]:
        if pushes_today(s, now) < DAILY_CAP:
            pushes.append(compose_call(s, now))
        else:
            capped = True
    week = due_week(now)
    if s["heartbeat"]["week"] < week:
        pushes.append(compose_heartbeat(s, now, week))
    return pushes, capped


def settle(state: Dict[str, Any], push: Push, delivered: bool, now: datetime) -> Dict[str, Any]:
    """A delivered push into the state. One that was not delivered changes nothing: it stays owed."""
    s = copy.deepcopy(state)
    if not delivered:
        return s
    t = stamp(now)
    if push.kind == "call":
        s["delivered"] = {"call": s["call"]["call"], "since": s["call"]["since"]}
        s["log"], s["log_dropped"] = [], 0
        if s["day"]["day"] != t[:10]:
            s["day"] = {"day": t[:10], "pushes": 0}
        s["day"]["pushes"] += 1
    elif push.kind == "heartbeat":
        s["heartbeat"] = {"week": push.week, "since": t, "runs": 0, "all_up": 0, "false_alarms": 0}
    return s


# ------------------------------------------------------------------------------------------ one run

class Report:
    """Each line goes to the run log and to the job summary alike."""

    def __init__(self, environ: Dict[str, str], stream: Any = None) -> None:
        self.path = environ.get("GITHUB_STEP_SUMMARY") or None
        self.stream = stream if stream is not None else sys.stdout

    def __call__(self, line: str) -> None:
        print(line, file=self.stream, flush=True)
        if self.path:
            with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(line + "\n\n")


def parse_args(argv: Sequence[str]) -> Dict[str, str]:
    opts = {"state": "", "ntfy": "https://ntfy.sh"}
    args = list(argv)
    while args:
        a = args.pop(0)
        if a not in ("--state", "--ntfy") or not args:
            raise ValueError("arguments")
        opts[a[2:]] = args.pop(0)
    if not opts["state"]:
        raise ValueError("arguments")
    return opts


def run_ref(environ: Dict[str, str]) -> Dict[str, str]:
    def one(name: str) -> str:
        v = environ.get(name, "")
        return v if RUN_RX.match(v) else "local"
    return {"run": one("GITHUB_RUN_ID"), "attempt": one("GITHUB_RUN_ATTEMPT")}


def face_line(r: FaceRead) -> str:
    tries = ", ".join(f"{t.word} {t.status if t.status is not None else '-'} {t.seconds:.1f}s" for t in r.tries)
    return f"{r.url}: {'up' if r.up else 'down'}; {tries}"


def _restored_line(state: Optional[Dict[str, Any]], why: str) -> str:
    if state is None:
        return f"state: none ({why}); starting clean: called up, with up last delivered"
    sb = state["saved_by"] or {"run": "local", "attempt": "local"}
    return (f"state: restored, saved by run {sb['run']} attempt {sb['attempt']}; "
            f"carried {state['runs']} runs since {state['created']}")


def run_once(argv: Sequence[str], environ: Dict[str, str], report: Report, *, faces: Sequence[Face],
             now: Callable[[], datetime], timing: Timing, resolver: Optional[Callable],
             ctx_factory: Optional[Callable]) -> None:
    opts = parse_args(argv)
    run = run_ref(environ)
    at = now()
    report(f"uptime: run {run['run']} attempt {run['attempt']} at {stamp(at)}")
    topic = environ.get("NTFY_TOPIC", "")
    # Named by its state alone: a malformed topic is never written, not even in part.
    topic_state = "set" if TOPIC_RX.match(topic) else ("malformed" if topic else "not set")

    report(f"topic: NTFY_TOPIC is {topic_state}")    # every run, a push due or not, the drill included
    owed = {"call": "; it stays owed", "heartbeat": "; it stays owed"}    # a drill is never owed

    def deliver(p: Push) -> Optional[bool]:
        if topic_state != "set":
            report(f"push {p.kind}: not sent: NTFY_TOPIC is {topic_state}" + owed.get(p.kind, ""))
            return None
        ok = send_push(opts["ntfy"], topic, p, timing, resolver, ctx_factory)
        refused = f"refused after {timing.push_tries} tries" + owed.get(p.kind, "")
        report(f"push {p.kind}: " + ("sent" if ok else refused))
        return ok

    state, why = load_state(opts["state"], faces)
    report(_restored_line(state, why))

    if environ.get("UPTIME_DRILL", "") == "yes":
        report("drill: a sixth face at a closed port on the runner; one push marked as a drill; "
               "the two-of-three rule is skipped and the saved state is left alone")
        reads = read_faces(tuple(faces) + (DRILL_FACE,), timing, resolver, ctx_factory)
        for r in reads:
            report(face_line(r))
        down = [r.url for r in reads if not r.up]
        body = (f"DRILL from the outside watch, run {run['run']}: not an outage call.\n"
                f"Down in this run: {', '.join(down) if down else 'none'}.\n")
        deliver(Push("drill", "Narrow Highway: DRILL", body, "default", None))
        report("drill: finished; the saved state is left alone")
        return

    if state is None:
        state = clean_state(faces, at)
    reads = read_faces(faces, timing, resolver, ctx_factory)
    for r in reads:
        report(face_line(r))
    state = observe(state, {r.url: r.up for r in reads}, at)
    for f in faces:
        hist = state["faces"][f.url]
        if "down" in hist:
            report(f"{f.url}: down in {hist.count('down')} of its last {len(hist)} runs")
    pushes, capped = due(state, at)
    if capped:
        report(f"push call: withheld by the daily cap ({DAILY_CAP} sent today); it stays owed")
    for p in pushes:
        ok = deliver(p)
        state = settle(state, p, bool(ok), at)
    if not pushes and not capped:
        report("push: none due")
    c, hb = state["call"], state["heartbeat"]
    report(f"site: {c['call']} since {c['since']}; every face healthy {state['streak']} runs in a row; "
           f"{pushes_today(state, at)} pushes sent today (cap {DAILY_CAP}, the heartbeat aside)")
    if state["log"]:
        report(f"push: owed since {state['log'][0]['at']}")
    report(f"heartbeat: last sent for {hb['week']}; since {hb['since']}: {hb['runs']} runs, {hb['all_up']} with every "
           f"face up, {hb['false_alarms']} down calls recovered within 3 runs")
    state["saved_by"] = run
    save_state(opts["state"], state)
    report(f"state: written; carried {state['runs']} runs since {state['created']}")
    out = environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("finished=true\n")


def main(argv: Optional[Sequence[str]] = None, *, environ: Optional[Dict[str, str]] = None,
         faces: Optional[Sequence[Face]] = None, now: Optional[Callable[[], datetime]] = None,
         timing: Optional[Timing] = None, resolver: Optional[Callable] = None,
         ctx_factory: Optional[Callable] = None, stream: Any = None) -> int:
    """Catches everything, writes a crash as its class name only, and exits 0 on every path."""
    env = dict(os.environ if environ is None else environ)
    report = Report(env, stream)
    try:
        run_once(sys.argv[1:] if argv is None else argv, env, report, faces=FACES if faces is None else faces,
                 now=now or (lambda: datetime.now(timezone.utc)), timing=timing or Timing(), resolver=resolver,
                 ctx_factory=ctx_factory)
    except BaseException as e:
        try:
            report("crash " + type(e).__name__)
        except BaseException:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
