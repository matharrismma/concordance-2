"""tools/uptime.py and .github/workflows/uptime.yml: the outside watch (harness run 2026-11-07-outside-uptime, plan five).

What is pinned here: the five faces and the body only each one gives; each try held to its deadline from outside the read;
a face down only when all three tries fail; the pure decision fed sequences (outage, blip, flapping, long outage, lost
cache, the daily cap, refusals and catch-ups, the heartbeat); the real ntfy sender against a stand-in; nothing written but
public facts (marker strings from the resolver, the socket, TLS, bodies and headers, the topic, a crash); exit 0 on every
path; a state that does not parse, has another version or other faces starts clean; and the workflow file itself.

Nothing here reaches beyond 127.0.0.1: every read lands on a server this file opens there or on a resolver it injects, and
a guard on every test refuses any other lookup or connection. Deadlines and gaps are shrunk by parameter and asserted with
wide margins, so a loaded machine cannot turn them red.
"""
from __future__ import annotations

import errno
import importlib.util
import io
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, NamedTuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "uptime.py"
WORKFLOW = ROOT / ".github" / "workflows" / "uptime.yml"
UTC = timezone.utc
TEN = timedelta(minutes=10)

COM = "https://narrowhighway.com/health"
TV = "https://narrowhighway.tv/health"
API = "https://api.narrowhighway.com/health"
MCP = "https://api.narrowhighway.com/mcp"
ORG = "https://narrowhighway.org/health"
PUBLIC = [COM, TV, API, MCP, ORG]

MARKER = "zqmark7f3a"
TOPIC = "uptimetopicZQ7x"
WORDS = {"ok", "slow", "timeout", "refused", "dns", "tls", "reset", "status", "body", "redirect", "ratelimited"}

ENGINE_OK = json.dumps({"ok": True, "version": "2.0.0a0", "surface": "secular", "schema_active": True,
                        "jsonschema": True, "shards": {"open": 3, "peak": 9}}).encode()
ENGINE_WITNESS = json.dumps({"ok": True, "version": "2.0.0a0", "surface": "witness", "schema_active": True,
                             "jsonschema": True, "shards": {"open": 3, "peak": 9}}).encode()
V3_OK = b'{"ok": true}'
WITNESS_OK = json.dumps({"ok": True, "surface": "witness", "commit": "0" * 40, "doors": ["/verify", "/ask"]}).encode()
MCP_OK = b"retry: 60000\n\n: narrowhighway keeps no server-initiated stream; POST for tools\n\n"
ENGINE_429 = json.dumps({"error": "rate limit exceeded", "code": "RATE_LIMITED"}).encode()

_MODULE = []


def _load():
    if not _MODULE:
        spec = importlib.util.spec_from_file_location("uptime", TOOL)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["uptime"] = mod
        spec.loader.exec_module(mod)
        _MODULE.append(mod)
    return _MODULE[0]


@pytest.fixture
def ut():
    return _load()


# ------------------------------------------------------------------------------------------ the guard: 127.0.0.1 only

_REAL_GETADDRINFO = socket.getaddrinfo
_REAL_CONNECT = socket.socket.connect


class BeyondLoopback(AssertionError):
    """A test reached for something beyond 127.0.0.1."""


@pytest.fixture(autouse=True)
def only_loopback(monkeypatch):
    def getaddrinfo(host, *a, **k):
        if host not in ("127.0.0.1", "localhost"):
            raise BeyondLoopback("lookup refused")
        return _REAL_GETADDRINFO(host, *a, **k)

    def connect(self, address):
        if not (isinstance(address, tuple) and address[0] == "127.0.0.1"):
            raise BeyondLoopback("connect refused")
        return _REAL_CONNECT(self, address)

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", connect)


def test_the_guard_refuses_anything_beyond_loopback():
    with pytest.raises(BeyondLoopback):
        socket.getaddrinfo("narrowhighway.com", 443)
    s = socket.socket()
    try:
        with pytest.raises(BeyondLoopback):
            s.connect(("192.0.2.1", 443))
    finally:
        s.close()


# ------------------------------------------------------------------------------------------ servers on 127.0.0.1

class Request(NamedTuple):
    method: str
    path: str
    headers: List[tuple]
    body: bytes


def response(status, body=b"", headers=()):
    head = f"HTTP/1.1 {status} X\r\nContent-Length: {len(body)}\r\nConnection: close\r\n"
    head += "".join(f"{k}: {v}\r\n" for k, v in headers) + "\r\n"
    return head.encode("latin-1") + body


class Wire:
    """A server on 127.0.0.1 that hands each connection to `handler(wire, conn, n)`, n counting from 0."""

    def __init__(self, handler):
        self.handler = handler
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.requests: List[Request] = []
        self.conns = []
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(32)
        self.listener.settimeout(0.2)
        self.port = self.listener.getsockname()[1]
        threading.Thread(target=self._serve, daemon=True).start()

    def url(self, path="/health", scheme="http"):
        return f"{scheme}://127.0.0.1:{self.port}{path}"

    def _serve(self):
        while not self.stop.is_set():
            try:
                conn, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            with self.lock:
                n = len(self.conns)
                self.conns.append(conn)
            threading.Thread(target=self._one, args=(conn, n), daemon=True).start()

    def _one(self, conn, n):
        try:
            self.handler(self, conn, n)
        except OSError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def read_request(self, conn):
        conn.settimeout(30)
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        head, _, rest = data.partition(b"\r\n\r\n")
        lines = head.decode("latin-1").split("\r\n")
        method, path = (lines[0].split(" ") + ["", ""])[:2]
        headers = []
        for ln in lines[1:]:
            k, _, v = ln.partition(":")
            headers.append((k.strip(), v.strip()))
        size = int(dict((k.lower(), v) for k, v in headers).get("content-length", "0") or 0)
        while len(rest) < size:
            chunk = conn.recv(4096)
            if not chunk:
                break
            rest += chunk
        req = Request(method, path, headers, rest)
        with self.lock:
            self.requests.append(req)
        return req

    def close(self):
        self.stop.set()
        try:
            self.listener.close()
        except OSError:
            pass
        with self.lock:
            conns = list(self.conns)
        for c in conns:
            try:
                c.close()
            except OSError:
                pass


@pytest.fixture
def wire():
    made = []

    def make(handler):
        w = Wire(handler)
        made.append(w)
        return w
    yield make
    for w in made:
        w.close()


def answer(status, body=b"", headers=(), delay=0.0):
    def h(w, conn, n):
        w.read_request(conn)
        if delay:
            w.stop.wait(delay)
        conn.sendall(response(status, body, headers))
    return h


def by_turn(*handlers):
    def h(w, conn, n):
        handlers[min(n, len(handlers) - 1)](w, conn, n)
    return h


def never_answers(w, conn, n):
    w.read_request(conn)
    w.stop.wait(120)


def closes_at_once(w, conn, n):
    conn.close()


def drips(every):
    def h(w, conn, n):
        w.read_request(conn)
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\nConnection: close\r\n\r\n")
        for _ in range(100):
            if w.stop.wait(every):
                return
            conn.sendall(b" ")
    return h


def speaks_plain_http_to_tls(w, conn, n):
    conn.sendall(response(200, ENGINE_OK))
    w.stop.wait(5)


def ntfy(*turns):
    """A stand-in for ntfy.sh: each POST meets the next turn: ok, refuse, hang or close."""
    def h(w, conn, n):
        w.read_request(conn)
        turn = turns[min(n, len(turns) - 1)]
        if turn == "ok":
            conn.sendall(response(200, b'{"id":"x1","event":"message"}', [("Content-Type", "application/json")]))
        elif turn == "refuse":
            conn.sendall(response(500, MARKER.encode(), [("X-Error", MARKER)]))
        elif turn == "hang":
            w.stop.wait(120)
    return h


def closed_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def fast(ut, **kw):
    base = dict(deadline=10.0, gap=0.05, tries=3, slow=60.0, push_deadline=10.0, push_tries=3, push_gap=0.05)
    base.update(kw)
    return ut.Timing(**base)


def face(ut, url, check=None, ratelimit=None):
    return ut.Face(url, check or ut.healthy_secular, ratelimit)


# ------------------------------------------------------------------------------------------ the faces and their bodies

def test_the_five_faces_are_public_gets_each_with_its_own_test(ut):
    assert [f.url for f in ut.FACES] == PUBLIC
    assert [f.healthy for f in ut.FACES] == [ut.healthy_secular, ut.healthy_secular, ut.healthy_v3,
                                             ut.healthy_mcp, ut.healthy_witness]
    assert [f.ratelimit for f in ut.FACES] == [ut.engine_ratelimited, ut.engine_ratelimited, None,
                                               ut.engine_ratelimited, None]
    assert ut.DRILL_FACE.url == "http://127.0.0.1:9/health"
    assert ut.DRILL_FACE.healthy(ENGINE_OK) is False and ut.DRILL_FACE.healthy(V3_OK) is False


BODIES = {"engine": ENGINE_OK, "engine-witness": ENGINE_WITNESS, "v3": V3_OK, "witness": WITNESS_OK, "mcp": MCP_OK,
          "429": ENGINE_429, "html": b"<html>ok</html>", "empty": b"", "not-utf8": b"\xff\xfe{",
          "ok-is-1": b'{"ok": 1, "surface": "secular"}', "ok-is-text": b'{"ok": "true", "surface": "secular"}',
          "v3-plus": b'{"ok": true, "version": "3.0.0a0"}', "v3-one": b'{"ok": 1}',
          "witness-no-doors": json.dumps({"ok": True, "surface": "witness", "commit": "0" * 40}).encode(),
          "list": b'[{"ok": true}]', "mcp-crlf": MCP_OK.replace(b"\n", b"\r\n")}


def test_each_face_accepts_only_the_body_only_it_gives(ut):
    own = {COM: "engine", TV: "engine", API: "v3", MCP: "mcp", ORG: "witness"}
    for f in ut.FACES:
        accepted = {name for name, body in BODIES.items() if f.healthy(body)}
        assert accepted == {own[f.url]}, f.url


def test_a_429_is_up_only_with_the_engines_own_rate_limit_body(ut):
    for f in ut.FACES:
        engine = f.url in (COM, TV, MCP)
        assert ut.classify(f, 429, ENGINE_429, 0.1, 10.0) == ("ratelimited" if engine else "status"), f.url
        assert ut.classify(f, 429, b'{"error": "slow down"}', 0.1, 10.0) == "status"
        assert ut.classify(f, 429, b"", 0.1, 10.0) == "status"


def test_status_redirect_body_and_slow_are_read_from_the_answer(ut):
    com = ut.FACES[0]
    assert ut.classify(com, 200, ENGINE_OK, 0.2, 10.0) == "ok"
    assert ut.classify(com, 200, ENGINE_OK, 10.5, 10.0) == "slow"
    assert ut.classify(com, 200, ENGINE_WITNESS, 0.2, 10.0) == "body"
    assert ut.classify(com, 200, ENGINE_OK + b" " * 70000, 0.2, 10.0) == "body"
    for status in (301, 302, 307, 308):
        assert ut.classify(com, status, ENGINE_OK, 0.2, 10.0) == "redirect"
    for status in (500, 502, 503, 404, 403, 204):
        assert ut.classify(com, status, ENGINE_OK, 0.2, 10.0) == "status"
    assert set(ut.WORDS) == WORDS


# ------------------------------------------------------------------------------------------ one try, on the wire

def test_each_server_reads_as_its_word(ut, wire):
    t = fast(ut)
    cases = [
        (answer(200, ENGINE_OK), ut.healthy_secular, ut.engine_ratelimited, "ok", 200),
        (answer(500, ENGINE_OK), ut.healthy_secular, ut.engine_ratelimited, "status", 500),
        (answer(200, ENGINE_WITNESS), ut.healthy_secular, ut.engine_ratelimited, "body", 200),
        (answer(301, b"", [("Location", "/elsewhere")]), ut.healthy_secular, ut.engine_ratelimited, "redirect", 301),
        (answer(429, ENGINE_429), ut.healthy_secular, ut.engine_ratelimited, "ratelimited", 429),
        (answer(429, ENGINE_429), ut.healthy_witness, None, "status", 429),
        (answer(200, MCP_OK), ut.healthy_mcp, ut.engine_ratelimited, "ok", 200),
        (answer(200, V3_OK), ut.healthy_v3, None, "ok", 200),
        (answer(200, WITNESS_OK), ut.healthy_witness, None, "ok", 200),
        (closes_at_once, ut.healthy_secular, None, "reset", None),
    ]
    for handler, check, rl, word, status in cases:
        w = wire(handler)
        got = ut.read_try(face(ut, w.url(), check, rl), t)
        assert (got.word, got.status) == (word, status), word
        assert got.seconds < t.deadline
    redirect = wire(answer(302, b"", [("Location", "/health")]))
    assert ut.read_try(face(ut, redirect.url()), t).word == "redirect"
    assert len(redirect.requests) == 1, "a redirect is never followed"


def test_a_healthy_answer_over_the_slow_line_is_slow_and_up(ut, wire):
    w = wire(answer(200, ENGINE_OK, delay=1.0))
    got = ut.read_try(face(ut, w.url()), fast(ut, slow=0.2))
    assert got.word == "slow" and got.word in ut.UP_WORDS


def test_a_closed_port_is_refused_and_a_failed_lookup_is_dns(ut):
    t = fast(ut)
    assert ut.read_try(face(ut, f"http://127.0.0.1:{closed_port()}/health"), t).word == "refused"

    def no_such_host(host, *a, **k):
        raise socket.gaierror(socket.EAI_NONAME, MARKER)
    assert ut.read_try(face(ut, "http://nosuch.invalid/health"), t, resolver=no_such_host).word == "dns"


def test_tls_is_read_with_the_default_context_and_a_bad_handshake_is_tls(ut, wire):
    ctx = ut.tls_context()
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname is True
    src = TOOL.read_text(encoding="utf-8")
    for off in ("CERT_NONE", "CERT_OPTIONAL", "check_hostname", "_create_unverified_context", "verify_mode"):
        assert off not in src, off
    w = wire(speaks_plain_http_to_tls)
    assert ut.read_try(face(ut, w.url(scheme="https")), fast(ut)).word == "tls"


def _held(ut, read, deadline):
    start = time.monotonic()
    got = read()
    took = time.monotonic() - start
    assert got.word == "timeout"
    assert deadline * 0.9 <= took <= deadline + 12, took
    return got


def test_a_server_that_never_answers_is_held_to_the_deadline(ut, wire):
    w = wire(never_answers)
    _held(ut, lambda: ut.read_try(face(ut, w.url()), fast(ut, deadline=2.0)), 2.0)


def test_a_server_that_drips_a_byte_every_2_s_is_held_to_the_deadline(ut, wire):
    # Every byte comes inside any per-read socket timeout of 3 s; only a deadline kept from outside the read ends it.
    w = wire(drips(2.0))
    _held(ut, lambda: ut.read_try(face(ut, w.url()), fast(ut, deadline=3.0)), 3.0)


def test_a_resolver_that_stalls_is_held_to_the_deadline(ut):
    release = threading.Event()

    def stalls(host, *a, **k):
        release.wait(60)
        raise socket.gaierror("released")
    try:
        _held(ut, lambda: ut.read_try(face(ut, "http://stall.invalid/health"), fast(ut, deadline=2.0),
                                      resolver=stalls), 2.0)
    finally:
        release.set()


class NotTheNetwork(RuntimeError):
    """An exception no network failure raises: a bug in the code, never a down face."""


@pytest.mark.parametrize("stage", ["dns", "connect", "tls", "http", "body"])
def test_a_non_network_exception_during_a_read_is_a_crash_never_a_word(ut, wire, monkeypatch, stage):
    w = wire(answer(200, ENGINE_OK))
    url, check, resolver, ctx_factory = w.url(), ut.healthy_secular, None, None

    def raises(*a, **k):
        raise NotTheNetwork(MARKER)
    if stage == "dns":
        resolver = raises
    elif stage == "connect":
        monkeypatch.setattr(socket.socket, "connect", raises)
    elif stage == "tls":
        url = w.url(scheme="https")

        class Raises:
            wrap_socket = staticmethod(raises)
        ctx_factory = Raises
    elif stage == "http":
        monkeypatch.setattr(ut.http.client.HTTPConnection, "getresponse", raises)
    else:
        check = raises
    f = face(ut, url, check)
    with pytest.raises(NotTheNetwork):
        ut.read_try(f, fast(ut), resolver=resolver, ctx_factory=ctx_factory)
    with pytest.raises(NotTheNetwork):
        ut.read_face(f, fast(ut), resolver=resolver, ctx_factory=ctx_factory)


def test_a_non_network_exception_in_a_run_is_a_crash_and_no_face_reads_down(ut, wire, tmp_path):
    w = wire(answer(200, ENGINE_OK))

    def raises(host, *a, **k):
        raise NotTheNetwork(MARKER)
    r = run_main(ut, tmp_path, [face(ut, w.url())], now=T0, name="a", resolver=raises)
    assert r.rc == 0 and r.log.splitlines()[-1] == "crash NotTheNetwork"
    assert face_lines(r.log) == [] and r.output == "" and not (tmp_path / "state.json").exists()
    stand_in = wire(ntfy("ok"))
    with pytest.raises(NotTheNetwork):
        ut.send_push(f"http://127.0.0.1:{stand_in.port}", TOPIC, push(ut), fast(ut), resolver=raises)
    assert stand_in.requests == []


BAD_FAMILY = 12345                                       # no runner can make a socket of this family


def test_every_address_the_resolver_gives_is_tried_within_the_one_deadline(ut, wire):
    w = wire(answer(200, ENGINE_OK))
    good = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", w.port))]
    uncreatable = [(BAD_FAMILY, socket.SOCK_STREAM, 0, "", ("::1", w.port, 0, 0))]
    refused = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", closed_port()))]
    f = face(ut, "http://two.test/health")
    for first in (uncreatable, refused, uncreatable + refused):
        got = ut.read_try(f, fast(ut), resolver=lambda *a, _first=first, **k: _first + good)
        assert got.word == "ok", first
    assert len(w.requests) == 3
    assert ut.read_try(f, fast(ut), resolver=lambda *a, **k: uncreatable + refused).word == "refused"
    silent = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", wire(never_answers).port))]
    _held(ut, lambda: ut.read_try(f, fast(ut, deadline=2.0), resolver=lambda *a, **k: uncreatable + silent), 2.0)


def test_a_read_sends_no_session_and_names_the_repository(ut, wire):
    w = wire(answer(200, MCP_OK))
    assert ut.read_try(face(ut, w.url("/mcp"), ut.healthy_mcp), fast(ut)).word == "ok"
    (req,) = w.requests
    names = {k.lower() for k, _ in req.headers}
    assert req.method == "GET" and req.path == "/mcp" and req.body == b""
    assert "mcp-session-id" not in names and "cookie" not in names and "authorization" not in names
    assert "matharrismma/concordance-2" in dict((k.lower(), v) for k, v in req.headers)["user-agent"]


# ------------------------------------------------------------------------------------------ three tries, side by side

def test_a_face_is_down_only_when_all_three_tries_fail(ut, wire):
    t = fast(ut, gap=0.3)
    flaky = wire(by_turn(answer(500), answer(500), answer(200, ENGINE_OK)))
    got = ut.read_face(face(ut, flaky.url()), t)
    assert got.up is True and [x.word for x in got.tries] == ["status", "status", "ok"]

    dead = wire(answer(503))
    start = time.monotonic()
    got = ut.read_face(face(ut, dead.url()), t)
    assert got.up is False and [x.word for x in got.tries] == ["status"] * 3
    assert time.monotonic() - start >= 2 * 0.3 * 0.9, "the tries are spaced by the gap"

    first = wire(answer(200, ENGINE_OK))
    got = ut.read_face(face(ut, first.url()), t)
    assert got.up is True and len(got.tries) == 1 and len(first.requests) == 1


def test_the_faces_are_read_side_by_side(ut, wire):
    t = fast(ut, deadline=1.5, gap=0.5)
    ws = [wire(never_answers) for _ in range(5)]
    start = time.monotonic()
    got = ut.read_faces([face(ut, w.url()) for w in ws], t)
    took = time.monotonic() - start
    one_face = 3 * 1.5 + 2 * 0.5
    assert [g.up for g in got] == [False] * 5
    assert one_face * 0.9 <= took < one_face * 5 * 0.7, took


def test_one_run_is_bounded(ut):
    t = ut.Timing()
    assert (t.deadline, t.gap, t.tries, t.slow) == (25.0, 20.0, 3, 10.0)
    assert (t.push_deadline, t.push_tries) == (10.0, 3)
    assert t.deadline > 18.8, "above what V3 recorded for its health with 32 busy threads"
    assert t.read_bound() == 115.0
    assert t.read_bound() + 2 * t.push_bound() < 240.0, "one run ends within four minutes"


# ------------------------------------------------------------------------------------------ the pure decision

T0 = datetime(2026, 11, 10, 0, 7, tzinfo=UTC)          # a Tuesday


def sim(ut, state, downs, start, deliver=None):
    """Feed runs ten minutes apart; `downs` is one set of down URLs per run. Returns the state and every push tried."""
    tried = []
    for i, down in enumerate(downs):
        now = start + i * TEN
        state = ut.observe(state, {u: u not in down for u in PUBLIC}, now)
        pushes, capped = ut.due(state, now)
        for p in pushes:
            ok = True if deliver is None else deliver(p, now)
            state = ut.settle(state, p, ok, now)
            tried.append((i, p, ok))
    return state, tried


def calls(tried, delivered=True):
    return [(i, p) for i, p, ok in tried if p.kind == "call" and ok is delivered]


def stamp(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_a_clean_outage_and_recovery_push_once_down_and_once_back(ut):
    s = ut.clean_state(ut.FACES, T0)
    s, tried = sim(ut, s, [set(), {COM}, {COM}, {COM}, set(), set(), set(), set()], T0)
    (i_down, down), (i_back, back) = calls(tried)
    assert (i_down, i_back) == (2, 6)
    assert down.title == "Narrow Highway: DOWN" and down.priority == "high"
    assert COM in down.body and TV not in down.body and "Catch-up" not in down.body
    assert f"Down since {stamp(T0 + 2 * TEN)}" in down.body
    assert back.title == "Narrow Highway: BACK"
    assert f"Down from {stamp(T0 + 2 * TEN)} to {stamp(T0 + 6 * TEN)}" in back.body
    assert len(tried) == 2


def test_a_one_run_blip_pushes_nothing(ut):
    s = ut.clean_state(ut.FACES, T0)
    s, tried = sim(ut, s, [set(), {API}, set(), set(), set(), {MCP}, set()], T0)
    assert tried == []
    assert s["call"]["call"] == "up"


def test_a_face_that_flaps_every_other_run_is_caught(ut):
    s = ut.clean_state(ut.FACES, T0)
    flaps = [{ORG} if i % 2 == 0 else set() for i in range(20)]
    s, tried = sim(ut, s, flaps, T0)
    ((i, p),) = calls(tried)
    assert i == 2 and ORG in p.body
    assert s["call"]["call"] == "down", "never three healthy runs in a row, so never called back"


def test_a_long_outage_pushes_once(ut):
    s = ut.clean_state(ut.FACES, T0)
    s, tried = sim(ut, s, [set(PUBLIC)] * 40 + [set()] * 3, T0)
    (i_down, down), (i_back, back) = calls(tried)
    assert (i_down, i_back) == (1, 42)
    assert all(u in down.body for u in PUBLIC)


def test_a_lost_cache_starts_clean_and_misses_the_back_push_by_design(ut):
    s = ut.clean_state(ut.FACES, T0)
    s, tried = sim(ut, s, [{COM}, {COM}, {COM}], T0)
    assert len(calls(tried)) == 1
    lost = T0 + 3 * TEN
    s = ut.clean_state(ut.FACES, lost)               # the cache lapsed mid-outage
    s, tried = sim(ut, s, [set()] * 10, lost)
    assert tried == [], "a lost cache starts from up: its back push is missed, as named"
    hb = ut.compose_heartbeat(s, lost + 10 * TEN, "2026-W47")
    assert f"since {stamp(lost)}" in hb.body, "the heartbeat's since-when shows the restart"


def test_the_daily_cap_withholds_an_outage_past_it_and_the_next_day_catches_up(ut):
    s = ut.clean_state(ut.FACES, T0)
    cycle = [{TV}, {TV}, set(), set(), set()]
    runs = cycle * 3 + [{TV}] * 140
    s, tried = sim(ut, s, runs, T0)
    sent = calls(tried)
    assert len(sent) == 7 and ut.DAILY_CAP == 6
    i, late = sent[6]
    first_tomorrow = (datetime(2026, 11, 11, 0, 7, tzinfo=UTC) - T0) // TEN
    assert i == first_tomorrow, "withheld until the next UTC day"
    called = T0 + 16 * TEN
    assert late.title == "Narrow Highway: DOWN"
    assert f"Catch-up: this push was owed since {stamp(called)}" in late.body
    assert calls(tried, delivered=False) == [], "a withheld push is not even tried"


def test_a_refused_push_is_sent_by_the_next_run_as_a_catch_up(ut):
    s = ut.clean_state(ut.FACES, T0)
    answers = iter([False, True, True])
    s, tried = sim(ut, s, [{API}, {API}, {API}, {API}], T0, deliver=lambda p, now: next(answers))
    assert [(i, ok) for i, p, ok in tried] == [(1, False), (2, True)]
    assert f"Catch-up: this push was owed since {stamp(T0 + TEN)}" in tried[1][1].body


def test_the_first_run_with_no_state_pushes_nothing(ut):
    monday = datetime(2026, 11, 16, 14, 7, tzinfo=UTC)
    s = ut.clean_state(ut.FACES, monday)
    assert (s["call"]["call"], s["delivered"]["call"]) == ("up", "up")
    s, tried = sim(ut, s, [set(PUBLIC)], monday)
    assert tried == [], "being called down needs two runs, and the heartbeat is not due on a clean start"


def test_two_runs_from_one_restored_state_each_push_the_same_call(ut):
    s = ut.clean_state(ut.FACES, T0)
    s, _ = sim(ut, s, [{ORG}], T0)
    a, tried_a = sim(ut, s, [{ORG}], T0 + TEN)
    b, tried_b = sim(ut, s, [{ORG}], T0 + TEN + timedelta(minutes=3))
    assert len(calls(tried_a)) == 1 and len(calls(tried_b)) == 1, "the worst case of an overlap: a duplicate push"


def test_a_recovery_while_a_down_push_is_owed_sends_one_push(ut):
    s = ut.clean_state(ut.FACES, T0)
    s, tried = sim(ut, s, [set(), {COM}, {COM}, set(), set(), set()], T0,
                   deliver=lambda p, now: now >= T0 + 5 * TEN)
    sent = calls(tried)
    assert len(sent) == 1
    i, p = sent[0]
    assert i == 5 and p.title == "Narrow Highway: BACK"
    assert f"Down from {stamp(T0 + 2 * TEN)} to {stamp(T0 + 5 * TEN)}: {COM}" in p.body
    assert f"Back since {stamp(T0 + 5 * TEN)}" in p.body
    assert s["log"] == [] and s["delivered"] == {"call": "up", "since": stamp(T0 + 5 * TEN)}


# ------------------------------------------------------------------------------------------ the heartbeat

SUNDAY = datetime(2026, 11, 15, 12, 7, tzinfo=UTC)
MONDAY_1307 = datetime(2026, 11, 16, 13, 7, tzinfo=UTC)


def heartbeats(tried, delivered=True):
    return [(i, p) for i, p, ok in tried if p.kind == "heartbeat" and ok is delivered]


def test_two_runs_on_a_monday_afternoon_send_one_heartbeat(ut):
    s = ut.clean_state(ut.FACES, SUNDAY)
    assert ut.due_week(SUNDAY) == "2026-W46" and ut.due_week(MONDAY_1307 - TEN) == "2026-W46"
    assert ut.due_week(MONDAY_1307) == "2026-W47"
    s, tried = sim(ut, s, [set(), set()], MONDAY_1307)
    ((i, hb),) = heartbeats(tried)
    assert i == 0 and hb.title == "Narrow Highway: watch running" and hb.week == "2026-W47"
    assert s["heartbeat"]["week"] == "2026-W47"


def test_a_monday_whose_afternoon_runs_were_dropped_sends_it_at_the_first_later_run(ut):
    s = ut.clean_state(ut.FACES, SUNDAY)
    s, tried = sim(ut, s, [set()], datetime(2026, 11, 16, 9, 7, tzinfo=UTC))
    assert tried == []
    s, tried = sim(ut, s, [set()], datetime(2026, 11, 17, 8, 7, tzinfo=UTC))
    assert len(heartbeats(tried)) == 1


def test_a_refused_heartbeat_is_sent_by_the_next_run_with_the_counts_still_running(ut):
    s = ut.clean_state(ut.FACES, SUNDAY)
    s, _ = sim(ut, s, [set()] * 6, SUNDAY)
    answers = iter([False, True])
    s, tried = sim(ut, s, [set(), set()], MONDAY_1307, deliver=lambda p, now: next(answers))
    assert [(i, p.kind, ok) for i, p, ok in tried] == [(0, "heartbeat", False), (1, "heartbeat", True)]
    assert "8 runs, 8 of them with every face up" in tried[1][1].body
    assert s["heartbeat"]["runs"] == 0 and s["heartbeat"]["since"] == stamp(MONDAY_1307 + TEN)


def test_a_false_alarm_on_a_thursday_is_in_the_next_mondays_heartbeat(ut):
    wednesday = datetime(2026, 11, 11, 12, 7, tzinfo=UTC)
    s = ut.clean_state(ut.FACES, wednesday)
    thursday = datetime(2026, 11, 12, 10, 7, tzinfo=UTC)
    s, tried = sim(ut, s, [{MCP}, {MCP}, set(), set(), set()], thursday)
    assert len(calls(tried)) == 2 and s["heartbeat"]["false_alarms"] == 1
    s, tried = sim(ut, s, [set()], MONDAY_1307)
    ((_, hb),) = heartbeats(tried)
    assert "Down calls that recovered within 3 runs (likely false alarms): 1." in hb.body
    s, tried = sim(ut, s, [set()], MONDAY_1307 + timedelta(days=7))
    ((_, hb),) = heartbeats(tried)
    assert "(likely false alarms): 0." in hb.body, "the counts reset only when a heartbeat is delivered"


def test_the_false_alarm_window_is_three_runs_from_the_down_call(ut):
    s = ut.clean_state(ut.FACES, T0)
    three, tried = sim(ut, s, [{COM}, {COM}, set(), set(), set()], T0)          # back 3 runs after the down call
    assert [i for i, _ in calls(tried)] == [1, 4] and three["heartbeat"]["false_alarms"] == 1
    four, tried = sim(ut, s, [{COM}, {COM}, {COM}, set(), set(), set()], T0)    # back 4 runs after it
    assert [i for i, _ in calls(tried)] == [1, 5] and four["heartbeat"]["false_alarms"] == 0


def test_a_long_outage_is_not_counted_as_a_false_alarm(ut):
    s = ut.clean_state(ut.FACES, T0)
    s, tried = sim(ut, s, [{COM}] * 6 + [set()] * 3, T0)
    assert len(calls(tried)) == 2 and s["heartbeat"]["false_alarms"] == 0


# ------------------------------------------------------------------------------------------ the sender, against a stand-in

def push(ut, title="Narrow Highway: DOWN", body="Down since 2026-11-10T00:07:00Z: https://narrowhighway.com/health\n"):
    return ut.Push("call", title, body, "high", None)


def test_the_sender_posts_plain_text_with_a_title_and_a_priority(ut, wire):
    w = wire(ntfy("ok"))
    assert ut.send_push(f"http://127.0.0.1:{w.port}", TOPIC, push(ut), fast(ut)) is True
    (req,) = w.requests
    assert req.method == "POST" and req.path == "/" + TOPIC
    assert req.body == push(ut).body.encode("utf-8")
    h = dict((k.lower(), v) for k, v in req.headers)
    assert h["title"] == "Narrow Highway: DOWN" and h["priority"] == "high"
    assert h["content-type"] == "text/plain; charset=utf-8"
    assert "matharrismma/concordance-2" in h["user-agent"]
    for k, v in req.headers:
        assert all(32 <= ord(c) < 127 for c in k + v), k
    for banned in ("click", "attach", "actions", "action", "icon", "email", "call", "markdown", "filename",
                   "x-click", "x-attach", "x-actions", "x-email", "x-icon", "authorization", "cookie"):
        assert banned not in h, banned


def test_a_title_holding_non_ascii_text_still_sends(ut, wire):
    w = wire(ntfy("ok"))
    p = push(ut, title="Narrow Highway \u2014 caf\u00e9 \u2620 down\r\nX-Click: evil", body="d\u00e9j\u00e0 vu\n")
    assert ut.send_push(f"http://127.0.0.1:{w.port}", TOPIC, p, fast(ut)) is True
    (req,) = w.requests
    h = dict((k.lower(), v) for k, v in req.headers)
    assert h["title"].startswith("Narrow Highway ") and all(32 <= ord(c) < 127 for c in h["title"])
    assert "x-click" not in h
    assert req.body == "d\u00e9j\u00e0 vu\n".encode("utf-8")


def test_a_refused_push_is_tried_twice_more(ut, wire):
    w = wire(ntfy("refuse", "refuse", "ok"))
    assert ut.send_push(f"http://127.0.0.1:{w.port}", TOPIC, push(ut), fast(ut)) is True
    assert len(w.requests) == 3
    w = wire(ntfy("refuse"))
    assert ut.send_push(f"http://127.0.0.1:{w.port}", TOPIC, push(ut), fast(ut)) is False
    assert len(w.requests) == 3, "three tries, then the push is owed"
    w = wire(ntfy("close"))
    assert ut.send_push(f"http://127.0.0.1:{w.port}", TOPIC, push(ut), fast(ut)) is False


def test_a_push_that_never_answers_is_held_to_its_deadline_and_stays_owed(ut, wire):
    w = wire(ntfy("hang"))
    t = fast(ut, push_deadline=1.5, push_gap=0.1)
    start = time.monotonic()
    assert ut.send_push(f"http://127.0.0.1:{w.port}", TOPIC, push(ut), t) is False
    took = time.monotonic() - start
    assert 3 * 1.5 * 0.9 <= took <= 3 * 1.5 + 0.2 + 15, took
    assert len(w.requests) == 3


def test_the_sender_sends_the_topic_over_https_only_beyond_loopback(ut):
    for base in ("http://ntfy.sh", "ftp://ntfy.sh", "http://192.0.2.1", "http://localhost", "http://localhost:8080",
                 "http://127.0.0.2:8080", "http://127.0.0.1.test", "http://[::1]:8080"):
        with pytest.raises(ValueError):
            ut.push_url(base, TOPIC)
    assert ut.push_url("https://ntfy.sh", TOPIC) == "https://ntfy.sh/" + TOPIC
    assert ut.push_url("http://127.0.0.1:8080", TOPIC) == "http://127.0.0.1:8080/" + TOPIC
    for bad in ("", "a/b", "a b", "x" * 65, "caf\u00e9", TOPIC + "\n", "\n" + TOPIC):
        with pytest.raises(ValueError):
            ut.push_url("https://ntfy.sh", bad)


# ------------------------------------------------------------------------------------------ whole runs

class Ran(NamedTuple):
    rc: int
    log: str
    summary: str
    output: str


def run_main(ut, tmp_path, faces, *, now, name, topic=None, ntfy_port=None, drill=False, timing=None,
             state=None, run_id="1001", attempt="1", resolver=None, ctx_factory=None):
    summary, output = tmp_path / f"summary-{name}.md", tmp_path / f"output-{name}.txt"
    env = {"GITHUB_STEP_SUMMARY": str(summary), "GITHUB_OUTPUT": str(output),
           "GITHUB_RUN_ID": run_id, "GITHUB_RUN_ATTEMPT": attempt}
    if topic:
        env["NTFY_TOPIC"] = topic
    if drill:
        env["UPTIME_DRILL"] = "yes"
    argv = ["--state", str(state or tmp_path / "state.json"),
            "--ntfy", f"http://127.0.0.1:{ntfy_port or closed_port()}"]
    stream = io.StringIO()
    rc = ut.main(argv, environ=env, faces=tuple(faces), now=lambda: now, timing=timing or fast(ut),
                 resolver=resolver, ctx_factory=ctx_factory, stream=stream)
    read = (lambda p: p.read_text(encoding="utf-8") if p.exists() else "")
    return Ran(rc, stream.getvalue(), read(summary), read(output))


def face_lines(text):
    return [ln for ln in text.splitlines() if re.match(r"^\S+: (up|down); ", ln)]


def test_the_summary_is_printed_to_the_log_line_for_line(ut, wire, tmp_path):
    w = wire(answer(200, ENGINE_OK))
    r = run_main(ut, tmp_path, [face(ut, w.url())], now=T0, name="a")
    assert r.rc == 0
    assert [ln for ln in r.summary.splitlines() if ln] == r.log.splitlines()
    (line,) = face_lines(r.log)
    assert re.fullmatch(re.escape(f"{w.url()}: up; ok 200 ") + r"\d+\.\ds", line), line


def test_a_run_writes_only_public_facts(ut, wire, tmp_path, monkeypatch):
    """Markers from the resolver, the socket, the TLS layer, bodies and headers, and the topic, reach nothing written."""
    tls_wire = wire(answer(200, ENGINE_OK))
    faces = [
        face(ut, "http://dns-marker.test/health"),
        face(ut, "http://sock-marker.test/health"),
        face(ut, tls_wire.url(scheme="https")),
        face(ut, wire(answer(500, MARKER.encode(), [("X-Marker", MARKER)])).url()),
        face(ut, wire(answer(200, b'{"ok": true, "surface": "' + MARKER.encode() + b'"}',
                             [("Set-Cookie", MARKER)])).url()),
        face(ut, wire(answer(429, MARKER.encode())).url(), ratelimit=ut.engine_ratelimited),
        face(ut, wire(answer(302, b"", [("Location", "https://" + MARKER + ".test/")])).url()),
        face(ut, wire(lambda w, c, n: (w.read_request(c), c.sendall((MARKER + " 200\r\n\r\n").encode()))).url()),
    ]

    def resolver(host, port, *a, **k):
        if host == "dns-marker.test":
            raise socket.gaierror(socket.EAI_NONAME, MARKER)
        if host == "sock-marker.test":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 1))]
        return _REAL_GETADDRINFO(host, port, *a, **k)

    guarded = socket.socket.connect

    def connect(self, address):
        if address == ("127.0.0.1", 1):
            raise OSError(errno.ENETUNREACH, MARKER)
        return guarded(self, address)
    monkeypatch.setattr(socket.socket, "connect", connect)

    class MarkedTLS:
        def wrap_socket(self, sock, server_hostname=None):
            raise ssl.SSLError(1, MARKER)

    stand_in = wire(ntfy("refuse", "ok"))
    runs = [run_main(ut, tmp_path, faces, now=SUNDAY, name="a", topic=TOPIC, ntfy_port=stand_in.port,
                     resolver=resolver, ctx_factory=MarkedTLS, run_id="2001"),
            run_main(ut, tmp_path, faces, now=MONDAY_1307 + timedelta(hours=1), name="b", topic=TOPIC,
                     ntfy_port=stand_in.port, resolver=resolver, ctx_factory=MarkedTLS, run_id="2002")]
    state = (tmp_path / "state.json").read_text(encoding="utf-8")
    assert all(r.rc == 0 for r in runs) and "crash" not in runs[0].log + runs[1].log
    assert len(stand_in.requests) >= 3, "the second run pushed: a down call and a heartbeat, one refused once"
    written = [state] + [x for r in runs for x in (r.log, r.summary, r.output)]
    for req in stand_in.requests:
        written.append(req.body.decode("utf-8"))
        written.extend(k + ": " + v for k, v in req.headers)
        assert req.path == "/" + TOPIC
    for text in written:
        assert MARKER not in text
        assert TOPIC not in text
    for r in runs:
        lines = face_lines(r.log)
        assert len(lines) == len(faces)
        for ln in lines:
            for one in ln.split("; ", 1)[1].split(", "):
                word, status, secs = one.split(" ")
                assert word in WORDS and (status == "-" or status.isdigit()) and re.fullmatch(r"\d+\.\ds", secs)
    words = [ln.split("; ", 1)[1].split(" ")[0] for ln in face_lines(runs[0].log)]
    assert words == ["dns", "refused", "tls", "status", "body", "status", "redirect", "reset"]


def test_without_the_topic_a_run_reads_and_records_and_pushes_nothing(ut, wire, tmp_path):
    down = wire(answer(500))
    for name, now in (("a", T0), ("b", T0 + TEN)):
        r = run_main(ut, tmp_path, [face(ut, down.url())], now=now, name=name)
        assert r.rc == 0 and r.output == "finished=true\n"
    assert "push call: not sent: NTFY_TOPIC is not set; it stays owed" in r.log
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["call"]["call"] == "down" and state["log"] and state["runs"] == 2


@pytest.mark.parametrize("bad", ["bad topic/" + MARKER, MARKER + "\n", "x" * 65 + MARKER, MARKER + "\u00e9"])
def test_a_malformed_topic_is_named_malformed_never_written_and_never_sent(ut, wire, tmp_path, bad):
    down, stand_in = wire(answer(500)), wire(ntfy("ok"))
    runs = [run_main(ut, tmp_path, [face(ut, down.url())], now=now, name=name, topic=bad, ntfy_port=stand_in.port)
            for name, now in (("a", T0), ("b", T0 + TEN))]
    assert "push call: not sent: NTFY_TOPIC is malformed; it stays owed" in runs[1].log
    assert "not set" not in runs[1].log and stand_in.requests == []
    state = (tmp_path / "state.json").read_text(encoding="utf-8")
    for text in [state] + [x for r in runs for x in (r.log, r.summary, r.output)]:
        assert MARKER not in text and "bad topic" not in text


def test_a_refusal_or_a_timeout_leaves_the_push_owed_in_the_saved_state(ut, wire, tmp_path):
    down = wire(answer(500))
    faces = [face(ut, down.url())]
    refuses, hangs, takes = wire(ntfy("refuse")), wire(ntfy("hang")), wire(ntfy("ok"))
    run_main(ut, tmp_path, faces, now=T0, name="a", topic=TOPIC, ntfy_port=refuses.port)
    r = run_main(ut, tmp_path, faces, now=T0 + TEN, name="b", topic=TOPIC, ntfy_port=refuses.port)
    assert "push call: refused after 3 tries; it stays owed" in r.log and len(refuses.requests) == 3
    assert f"push: owed since {stamp(T0 + TEN)}" in r.log
    r = run_main(ut, tmp_path, faces, now=T0 + 2 * TEN, name="c", topic=TOPIC, ntfy_port=hangs.port,
                 timing=fast(ut, push_deadline=1.0))
    assert "push call: refused after 3 tries; it stays owed" in r.log and len(hangs.requests) == 3
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["log"] and state["delivered"]["call"] == "up" and state["day"]["pushes"] == 0
    r = run_main(ut, tmp_path, faces, now=T0 + 3 * TEN, name="d", topic=TOPIC, ntfy_port=takes.port)
    assert "push call: sent" in r.log
    (req,) = takes.requests
    assert f"Catch-up: this push was owed since {stamp(T0 + TEN)}." in req.body.decode()
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["log"] == [] and state["delivered"]["call"] == "down" and state["day"]["pushes"] == 1


def test_a_face_down_in_one_run_of_three_is_in_the_summary_and_pushes_nothing(ut, wire, tmp_path):
    w = wire(by_turn(answer(200, ENGINE_OK), answer(500), answer(500), answer(500), answer(200, ENGINE_OK)))
    stand_in = wire(ntfy("ok"))
    for name, now in (("a", T0), ("b", T0 + TEN), ("c", T0 + 2 * TEN)):
        r = run_main(ut, tmp_path, [face(ut, w.url())], now=now, name=name, topic=TOPIC, ntfy_port=stand_in.port)
    assert f"{w.url()}: down in 1 of its last 3 runs" in r.log
    assert stand_in.requests == []


def test_the_summary_names_the_run_whose_state_it_restored(ut, wire, tmp_path):
    w = wire(answer(200, ENGINE_OK))
    first = run_main(ut, tmp_path, [face(ut, w.url())], now=T0, name="a", run_id="3001", attempt="2")
    assert "state: none (missing); starting clean" in first.log
    second = run_main(ut, tmp_path, [face(ut, w.url())], now=T0 + TEN, name="b", run_id="3002")
    assert "state: restored, saved by run 3001 attempt 2" in second.log
    assert "carried 1 runs since " + stamp(T0) in second.log


@pytest.mark.parametrize("why, content", [
    ("does not parse", b"{not json"),
    ("does not parse", b"\xff\xfe\x00"),
    ("another version", None),
    ("fails validation", b"[]"),
    ("fails validation", b'{"faces": {}}'),
])
def test_a_state_that_cannot_be_used_starts_clean_and_the_next_run_reads_the_new_state(ut, wire, tmp_path,
                                                                                        why, content):
    w = wire(answer(200, ENGINE_OK))
    faces = [face(ut, w.url())]
    path = tmp_path / "state.json"
    if content is None:
        old = ut.clean_state(faces, T0)
        old["version"] = ut.VERSION - 1
        content = json.dumps(old).encode()
    path.write_bytes(content)
    r = run_main(ut, tmp_path, faces, now=T0 + TEN, name="a", run_id="4001")
    assert r.rc == 0 and f"state: none ({why}); starting clean" in r.log and r.output == "finished=true\n"
    r = run_main(ut, tmp_path, faces, now=T0 + 2 * TEN, name="b", run_id="4002")
    assert "state: restored, saved by run 4001 attempt 1" in r.log


def test_a_state_of_the_same_version_with_other_faces_starts_clean(ut, wire, tmp_path):
    w1, w2, w3 = wire(answer(200, ENGINE_OK)), wire(answer(200, ENGINE_OK)), wire(answer(200, ENGINE_OK))
    then = [face(ut, w1.url()), face(ut, w2.url())]
    now = [face(ut, w1.url()), face(ut, w3.url())]           # one face removed, one added
    run_main(ut, tmp_path, then, now=T0, name="a", run_id="5001")
    assert ut.load_state(tmp_path / "state.json", then)[1] == "restored"
    assert ut.load_state(tmp_path / "state.json", now)[1] == "fails validation"
    assert ut.load_state(tmp_path / "state.json", then[:1])[1] == "fails validation"
    r = run_main(ut, tmp_path, now, now=T0 + TEN, name="b", run_id="5002")
    assert "state: none (fails validation); starting clean" in r.log and "crash" not in r.log
    r = run_main(ut, tmp_path, now, now=T0 + 2 * TEN, name="c", run_id="5003")
    assert "state: restored, saved by run 5002 attempt 1" in r.log


def _mutations(ut, good):
    """States the decision would crash on or misread: each must fail validation, never reach the decision."""
    def edit(fn):
        s = json.loads(json.dumps(good))
        fn(s)
        return s
    u = next(iter(good["faces"]))
    return [
        edit(lambda s: s.pop("streak")),
        edit(lambda s: s.update(extra=1)),
        edit(lambda s: s.update(runs=True)),
        edit(lambda s: s.update(runs=-1)),
        edit(lambda s: s.update(runs="3")),
        edit(lambda s: s.update(created="yesterday")),
        edit(lambda s: s.update(saved_by={"run": "12; rm", "attempt": "1"})),
        edit(lambda s: s.update(saved_by={"run": "12\n", "attempt": "1"})),
        edit(lambda s: s["heartbeat"].update(week=s["heartbeat"]["week"] + "\n")),
        edit(lambda s: s["day"].update(day=s["day"]["day"] + "\n")),
        edit(lambda s: s["faces"].update({u: ["up", "sideways"]})),
        edit(lambda s: s["faces"].update({u: ["up"] * 4})),
        edit(lambda s: s["faces"].update({u: "up"})),
        edit(lambda s: s["call"].update(call="back")),
        edit(lambda s: s["call"].pop("run")),
        edit(lambda s: s["delivered"].update(since=12)),
        edit(lambda s: s.update(log=[{"call": "down", "at": "2026-11-10T00:07:00Z", "faces": ["https://x.test/"]}])),
        edit(lambda s: s.update(log=[{"call": "up"}])),
        edit(lambda s: s.update(log="none")),
        edit(lambda s: s["day"].update(pushes=1.5)),
        edit(lambda s: s["heartbeat"].update(week="week 47")),
        edit(lambda s: s["heartbeat"].pop("false_alarms")),
        edit(lambda s: s.update(faces=[])),
    ] + [edit(fn) for fn in _INVARIANTS.values()]


def _called_down_last_logged_up(s):
    """Typed right, and inconsistent: due() would read log[-1]['faces'] off an up entry and crash every run."""
    s["call"] = {"call": "down", "since": s["created"], "run": 0}
    s["log"] = [{"call": "up", "at": s["created"]}]


def _empty_log_delivered_differs(s):
    """Typed right, and inconsistent: nothing would ever come due, so the call would never be pushed."""
    s["delivered"] = {"call": "down", "since": s["created"]}


def _empty_log_with_dropped_calls(s):
    s["log_dropped"] = 1


_INVARIANTS = {"called down, last logged up": _called_down_last_logged_up,
               "empty log, delivered differs": _empty_log_delivered_differs,
               "empty log, calls dropped": _empty_log_with_dropped_calls}


@pytest.mark.parametrize("name", sorted(_INVARIANTS))
def test_a_state_typed_right_but_inconsistent_starts_clean_and_never_crashes(ut, wire, tmp_path, name):
    w = wire(answer(200, ENGINE_OK))
    faces = [face(ut, w.url())]
    bad = ut.clean_state(faces, T0)
    bad["saved_by"] = {"run": "8000", "attempt": "1"}
    _INVARIANTS[name](bad)
    path = tmp_path / "state.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    assert ut.load_state(path, faces) == (None, "fails validation")
    r = run_main(ut, tmp_path, faces, now=T0 + TEN, name="a", run_id="8001")
    assert r.rc == 0 and "crash" not in r.log and r.output == "finished=true\n"
    assert "state: none (fails validation); starting clean" in r.log
    r = run_main(ut, tmp_path, faces, now=T0 + 2 * TEN, name="b", run_id="8002")
    assert "state: restored, saved by run 8001 attempt 1" in r.log and "crash" not in r.log


def test_validation_refuses_every_state_the_decision_would_crash_on(ut, tmp_path):
    faces = ut.FACES
    good = ut.clean_state(faces, T0)
    good["saved_by"] = {"run": "1", "attempt": "1"}
    path = tmp_path / "s.json"
    path.write_text(json.dumps(good), encoding="utf-8")
    assert ut.load_state(path, faces) == (good, "restored")
    for bad in _mutations(ut, good):
        path.write_text(json.dumps(bad), encoding="utf-8")
        assert ut.load_state(path, faces) == (None, "fails validation"), bad
    assert ut.load_state(tmp_path / "absent.json", faces) == (None, "missing")
    assert ut.run_ref({"GITHUB_RUN_ID": "12\n", "GITHUB_RUN_ATTEMPT": "1"}) == {"run": "local", "attempt": "1"}


def test_a_crash_writes_only_its_class_name_saves_nothing_and_exits_0(ut, wire, tmp_path):
    w = wire(answer(200, ENGINE_OK))
    good = run_main(ut, tmp_path, [face(ut, w.url())], now=T0, name="a", run_id="6001")
    before = (tmp_path / "state.json").read_bytes()

    def bursts(body):
        raise RuntimeError(MARKER)
    r = run_main(ut, tmp_path, [face(ut, w.url(), bursts)], now=T0 + TEN, name="b", run_id="6002")
    assert good.rc == 0 and r.rc == 0
    assert r.log.splitlines()[-1] == "crash RuntimeError" and "crash RuntimeError" in r.summary
    assert MARKER not in r.log + r.summary + r.output and "Traceback" not in r.log + r.summary
    assert r.output == "", "no step output, so the save step does not run"
    assert (tmp_path / "state.json").read_bytes() == before, "the saved state is left as it was"
    nxt = run_main(ut, tmp_path, [face(ut, w.url())], now=T0 + 2 * TEN, name="c", run_id="6003")
    assert "state: restored, saved by run 6001 attempt 1" in nxt.log


@pytest.mark.parametrize("raised", [SystemExit(3), KeyboardInterrupt(), KeyError("k"), MemoryError()])
def test_every_path_exits_0(ut, wire, tmp_path, raised):
    w = wire(answer(200, ENGINE_OK))

    def check(body):
        raise raised
    r = run_main(ut, tmp_path, [face(ut, w.url(), check)], now=T0, name="a")
    assert r.rc == 0 and r.log.splitlines()[-1] == "crash " + type(raised).__name__ and r.output == ""


def test_the_tool_exits_0_from_the_command_line_when_it_crashes():
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GITHUB_", "NTFY_", "UPTIME_"))}
    p = subprocess.run([sys.executable, str(TOOL), "--no-such-flag", MARKER], capture_output=True, env=env,
                       timeout=120, cwd=str(ROOT))
    assert p.returncode == 0
    assert p.stdout.decode().splitlines() == ["crash ValueError"] and p.stderr == b""


def test_the_drill_pushes_once_from_a_closed_port_and_leaves_the_state_alone(ut, wire, tmp_path):
    w = wire(answer(200, ENGINE_OK))
    stand_in = wire(ntfy("ok"))
    run_main(ut, tmp_path, [face(ut, w.url())], now=T0, name="a", run_id="7001")
    before = (tmp_path / "state.json").read_bytes()
    r = run_main(ut, tmp_path, [face(ut, w.url())], now=T0 + TEN, name="b", run_id="7002", drill=True,
                 topic=TOPIC, ntfy_port=stand_in.port, timing=fast(ut, deadline=5.0))
    assert r.rc == 0 and r.output == "" and (tmp_path / "state.json").read_bytes() == before
    assert f"{w.url()}: up; ok 200" in r.log and "http://127.0.0.1:9/health: down; " in r.log
    (req,) = stand_in.requests
    h = dict((k.lower(), v) for k, v in req.headers)
    assert h["title"] == "Narrow Highway: DRILL"
    assert "http://127.0.0.1:9/health" in req.body.decode() and w.url() not in req.body.decode()
    assert "state: restored, saved by run 7001 attempt 1" in r.log


# ------------------------------------------------------------------------------------------ what the log says
# Every sentence of plan five that promises the summary or the log says something, pinned on a run with no push due
# and on a run with one due wherever the promise holds for both. Each check reads the run log and the job summary.

TOPICS = {"not set": None, "malformed": TOPIC + "\n", "set": TOPIC}


def says(r, text):
    """`text` is on a line of the run log and of the job summary alike, and the two hold the same lines."""
    assert [ln for ln in r.summary.splitlines() if ln] == r.log.splitlines(), "the summary and the log differ"
    assert any(text in ln for ln in r.log.splitlines()), text


def silent(r, text):
    assert not any(text in ln for ln in r.log.splitlines() + r.summary.splitlines()), text


def sub(tmp_path, name):
    d = tmp_path / name
    d.mkdir()
    return d


@pytest.mark.parametrize("state", ["not set", "malformed", "set"])
def test_the_log_says_the_topics_state_on_a_run_with_no_push_due(ut, wire, tmp_path, state):
    w, stand_in = wire(answer(200, ENGINE_OK)), wire(ntfy("ok"))
    r = run_main(ut, tmp_path, [face(ut, w.url())], now=T0, name="a", topic=TOPICS[state], ntfy_port=stand_in.port)
    says(r, "push: none due")
    says(r, f"topic: NTFY_TOPIC is {state}")
    assert [ln for ln in r.log.splitlines() if ln.startswith("topic: ")] == [f"topic: NTFY_TOPIC is {state}"]
    assert stand_in.requests == [] and TOPIC not in r.log + r.summary


@pytest.mark.parametrize("state", ["not set", "malformed", "set"])
def test_the_log_says_the_topics_state_and_the_push_on_a_run_with_one_due(ut, wire, tmp_path, state):
    down, stand_in = wire(answer(500)), wire(ntfy("ok"))
    a, b = (run_main(ut, tmp_path, [face(ut, down.url())], now=now, name=name, topic=TOPICS[state],
                     ntfy_port=stand_in.port) for name, now in (("a", T0), ("b", T0 + TEN)))
    for r in (a, b):
        says(r, f"topic: NTFY_TOPIC is {state}")
    says(a, "push: none due")
    silent(b, "push: none due")
    if state == "set":
        says(b, "push call: sent")
        silent(b, "push: owed since")
        assert len(stand_in.requests) == 1
    else:
        says(b, f"push call: not sent: NTFY_TOPIC is {state}; it stays owed")
        says(b, f"push: owed since {stamp(T0 + TEN)}")
        assert stand_in.requests == []
    assert TOPIC not in a.log + a.summary + b.log + b.summary


@pytest.mark.parametrize("why, content", [
    ("missing", None), ("does not parse", b"{not json"), ("another version", "old"),
    ("fails validation", b'{"faces": {}}')])
def test_the_log_says_which_no_state_it_found_and_why(ut, wire, tmp_path, why, content):
    w = wire(answer(500))
    faces = [face(ut, w.url())]
    if content == "old":
        old = ut.clean_state(faces, T0)
        old["version"] = ut.VERSION - 1
        content = json.dumps(old).encode()
    if content is not None:
        (tmp_path / "state.json").write_bytes(content)
    r = run_main(ut, tmp_path, faces, now=MONDAY_1307 + timedelta(hours=1), name="a", topic=TOPIC,
                 ntfy_port=wire(ntfy("ok")).port)
    says(r, f"state: none ({why}); starting clean: called up, with up last delivered")
    says(r, "push: none due")          # no state can have a push due: every face down, on a Monday afternoon


def test_the_log_says_which_runs_state_it_restored_with_and_without_a_push_due(ut, wire, tmp_path):
    down, stand_in = wire(answer(500)), wire(ntfy("ok"))
    a, b, c = (run_main(ut, tmp_path, [face(ut, down.url())], now=T0 + i * TEN, name=n, run_id=rid, attempt=att,
                        topic=TOPIC, ntfy_port=stand_in.port)
               for i, (n, rid, att) in enumerate([("a", "3101", "2"), ("b", "3102", "1"), ("c", "3103", "1")]))
    says(a, "state: none (missing)")
    says(b, f"state: restored, saved by run 3101 attempt 2; carried 1 runs since {stamp(T0)}")
    says(b, "push call: sent")
    says(c, f"state: restored, saved by run 3102 attempt 1; carried 2 runs since {stamp(T0)}")
    says(c, "push: none due")


def test_the_log_says_a_face_down_in_one_run_of_three_with_and_without_a_push_due(ut, wire, tmp_path):
    stand_in = wire(ntfy("ok"))
    quiet = wire(by_turn(answer(200, ENGINE_OK), answer(500), answer(500), answer(500), answer(200, ENGINE_OK)))
    for name, now in (("a", T0), ("b", T0 + TEN), ("c", T0 + 2 * TEN)):
        r = run_main(ut, tmp_path, [face(ut, quiet.url())], now=now, name="q" + name, topic=TOPIC,
                     ntfy_port=stand_in.port)
    says(r, f"{quiet.url()}: down in 1 of its last 3 runs")
    says(r, "push: none due")
    assert stand_in.requests == []
    monday = wire(by_turn(answer(200, ENGINE_OK), answer(200, ENGINE_OK), answer(500)))
    there = sub(tmp_path, "monday")
    for name, now in (("a", SUNDAY), ("b", SUNDAY + TEN), ("c", MONDAY_1307)):
        r = run_main(ut, there, [face(ut, monday.url())], now=now, name=name, topic=TOPIC, ntfy_port=stand_in.port)
    says(r, f"{monday.url()}: down in 1 of its last 3 runs")
    says(r, "push heartbeat: sent")
    silent(r, "push call")


def test_the_log_says_what_the_cap_withheld_and_the_next_day_sends_it(ut, wire, tmp_path):
    down, stand_in = wire(answer(500)), wire(ntfy("ok"))
    faces = [face(ut, down.url())]
    s = ut.clean_state(faces, T0)
    s["runs"], s["faces"][down.url()], s["saved_by"] = 1, ["down"], {"run": "3200", "attempt": "1"}
    s["day"]["pushes"] = ut.DAILY_CAP
    (tmp_path / "state.json").write_text(json.dumps(s), encoding="utf-8")
    r = run_main(ut, tmp_path, faces, now=T0 + TEN, name="a", topic=TOPIC, ntfy_port=stand_in.port)
    says(r, f"push call: withheld by the daily cap ({ut.DAILY_CAP} sent today); it stays owed")
    says(r, f"push: owed since {stamp(T0 + TEN)}")
    silent(r, "push: none due")
    assert stand_in.requests == []
    r = run_main(ut, tmp_path, faces, now=T0 + timedelta(days=1), name="b", topic=TOPIC, ntfy_port=stand_in.port)
    says(r, "push call: sent")
    silent(r, "withheld")
    assert f"Catch-up: this push was owed since {stamp(T0 + TEN)}." in stand_in.requests[0].body.decode()


def test_the_log_says_a_refused_or_timed_out_push_stays_owed(ut, wire, tmp_path):
    down = wire(answer(500))
    faces = [face(ut, down.url())]
    refuses, hangs = wire(ntfy("refuse")), wire(ntfy("hang"))
    run_main(ut, tmp_path, faces, now=T0, name="a", topic=TOPIC, ntfy_port=refuses.port)
    r = run_main(ut, tmp_path, faces, now=T0 + TEN, name="b", topic=TOPIC, ntfy_port=refuses.port)
    says(r, "push call: refused after 3 tries; it stays owed")
    says(r, f"push: owed since {stamp(T0 + TEN)}")
    r = run_main(ut, tmp_path, faces, now=T0 + 2 * TEN, name="c", topic=TOPIC, ntfy_port=hangs.port,
                 timing=fast(ut, push_deadline=1.0))
    says(r, "push call: refused after 3 tries; it stays owed")
    says(r, f"push: owed since {stamp(T0 + TEN)}")


def test_the_log_says_crash_and_the_class_name_only_with_and_without_a_push_due(ut, wire, tmp_path):
    healthy = wire(answer(200, ENGINE_OK))

    def bursts(body):
        raise NotTheNetwork(MARKER)
    r = run_main(ut, sub(tmp_path, "read"), [face(ut, healthy.url(), bursts)], now=T0, name="a")
    says(r, "crash NotTheNetwork")
    assert r.log.splitlines()[-1] == "crash NotTheNetwork" and r.output == "" and MARKER not in r.log + r.summary

    down, stand_in = wire(answer(500)), wire(ntfy("ok"))
    there = sub(tmp_path, "push")

    def resolver(host, port, *a, **k):
        if port == stand_in.port:
            raise NotTheNetwork(MARKER)
        return _REAL_GETADDRINFO(host, port, *a, **k)
    run_main(ut, there, [face(ut, down.url())], now=T0, name="a", topic=TOPIC, ntfy_port=stand_in.port)
    before = (there / "state.json").read_bytes()
    r = run_main(ut, there, [face(ut, down.url())], now=T0 + TEN, name="b", topic=TOPIC, ntfy_port=stand_in.port,
                 resolver=resolver)
    says(r, f"{down.url()}: down; ")
    says(r, "crash NotTheNetwork")
    assert r.log.splitlines()[-1] == "crash NotTheNetwork" and r.output == "" and MARKER not in r.log + r.summary
    assert (there / "state.json").read_bytes() == before and stand_in.requests == []


def test_the_log_says_one_word_per_try_with_and_without_a_push_due(ut, wire, tmp_path):
    limited = wire(answer(429, ENGINE_429))
    slow = wire(answer(200, ENGINE_OK, delay=1.0))
    moved = wire(answer(302, b"", [("Location", "/elsewhere")]))
    fine = wire(answer(200, ENGINE_OK))
    stand_in = wire(ntfy("ok"))
    faces = [face(ut, limited.url(), ratelimit=ut.engine_ratelimited), face(ut, slow.url()), face(ut, moved.url()),
             face(ut, fine.url())]
    t = fast(ut, slow=0.2)
    a, b = (run_main(ut, tmp_path, faces, now=now, name=name, topic=TOPIC, ntfy_port=stand_in.port, timing=t)
            for name, now in (("a", T0), ("b", T0 + TEN)))
    says(a, "push: none due")
    says(b, "push call: sent")
    for r in (a, b):
        says(r, f"{limited.url()}: up; ratelimited 429 ")
        says(r, f"{slow.url()}: up; slow 200 ")
        says(r, f"{moved.url()}: down; redirect 302 ")
        says(r, f"{fine.url()}: up; ok 200 ")
        (line,) = [ln for ln in r.log.splitlines() if ln.startswith(moved.url() + ": down; ")]
        assert re.fullmatch(re.escape(moved.url()) + r": down; (redirect 302 \d+\.\ds, ){2}redirect 302 \d+\.\ds", line)


def test_the_log_says_what_was_pushed_and_what_the_state_carried(ut, wire, tmp_path):
    w, stand_in = wire(answer(200, ENGINE_OK)), wire(ntfy("ok"))
    a, b = (run_main(ut, tmp_path, [face(ut, w.url())], now=now, name=name, run_id=rid, topic=TOPIC,
                     ntfy_port=stand_in.port) for name, now, rid in (("a", SUNDAY, "3301"), ("b", MONDAY_1307, "3302")))
    says(a, f"uptime: run 3301 attempt 1 at {stamp(SUNDAY)}")
    says(a, "push: none due")
    says(a, f"site: up since {stamp(SUNDAY)}; every face healthy 1 runs in a row; 0 pushes sent today")
    says(a, f"heartbeat: last sent for 2026-W46; since {stamp(SUNDAY)}: 1 runs, 1 with every face up, "
            "0 down calls recovered within 3 runs")
    says(a, f"state: written; carried 1 runs since {stamp(SUNDAY)}")
    says(b, f"uptime: run 3302 attempt 1 at {stamp(MONDAY_1307)}")
    says(b, "push heartbeat: sent")
    silent(b, "push: none due")
    says(b, f"heartbeat: last sent for 2026-W47; since {stamp(MONDAY_1307)}: 0 runs")
    says(b, f"state: written; carried 2 runs since {stamp(SUNDAY)}")


@pytest.mark.parametrize("state", ["not set", "malformed", "set"])
def test_the_log_says_the_topics_state_and_the_drill_in_a_drill(ut, wire, tmp_path, state):
    w, stand_in = wire(answer(200, ENGINE_OK)), wire(ntfy("ok"))
    r = run_main(ut, tmp_path, [face(ut, w.url())], now=T0, name="a", drill=True, topic=TOPICS[state],
                 ntfy_port=stand_in.port, timing=fast(ut, deadline=5.0))
    says(r, f"topic: NTFY_TOPIC is {state}")
    says(r, "state: none (missing)")
    says(r, "drill: a sixth face at a closed port on the runner; one push marked as a drill")
    says(r, f"{w.url()}: up; ok 200 ")
    says(r, "http://127.0.0.1:9/health: down; ")
    says(r, "drill: finished; the saved state is left alone")
    if state == "set":
        says(r, "push drill: sent")
        assert len(stand_in.requests) == 1
    else:
        says(r, f"push drill: not sent: NTFY_TOPIC is {state}")
        silent(r, "owed")
        assert stand_in.requests == []
    assert r.output == "" and not (tmp_path / "state.json").exists()


# ------------------------------------------------------------------------------------------ the tool's own source

def test_the_tool_is_standard_library_only_and_starts_nothing():
    import ast
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            mods.add(node.module.split(".")[0])
    assert mods <= set(sys.stdlib_module_names), mods - set(sys.stdlib_module_names)
    assert not mods & {"subprocess", "smtplib", "multiprocessing", "webbrowser", "urllib3", "requests"}
    calls_ = {f"{n.func.value.id}.{n.func.attr}" for n in ast.walk(tree) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)}
    assert not {c for c in calls_ if c.split(".")[0] == "os" and c.split(".")[1].startswith(
        ("system", "popen", "exec", "spawn", "fork", "kill"))}


# ------------------------------------------------------------------------------------------ the workflow file

class YamlSubsetError(ValueError):
    pass


_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*):(?: (.*))?$")


def _uncomment(s, n):
    quote = None
    for i, c in enumerate(s):
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'" and (i == 0 or s[i - 1] == " "):
            quote = c
        elif c == "#" and (i == 0 or s[i - 1] == " "):
            return s[:i].rstrip()
    if quote:
        raise YamlSubsetError(f"line {n}: an open quote")
    return s


def _scalar(s, n):
    if s[0] == '"':
        if len(s) < 2 or s[-1] != '"' or '"' in s[1:-1] or "\\" in s:
            raise YamlSubsetError(f"line {n}: a double-quoted scalar outside the subset")
        return s[1:-1]
    if s[0] == "'":
        inner = s[1:-1]
        if len(s) < 2 or s[-1] != "'" or "'" in inner.replace("''", ""):
            raise YamlSubsetError(f"line {n}: a single-quoted scalar outside the subset")
        return inner.replace("''", "'")
    if s[0] in "&*!|>{[%@`,?:-#" or ": " in s or s.endswith(":"):
        raise YamlSubsetError(f"line {n}: a plain scalar outside the subset")
    low = s.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("yes", "no", "on", "off", "y", "n", "null", "~"):
        raise YamlSubsetError(f"line {n}: an ambiguous plain scalar; quote it")
    if re.fullmatch(r"[0-9]+", s):
        return int(s)
    if re.fullmatch(r"[-+.0-9eE_:]+", s):
        raise YamlSubsetError(f"line {n}: a number outside the subset")
    return s


def parse_yaml_subset(text):
    """Block mappings, block lists and plain or quoted scalars, and nothing else: anything outside is refused."""
    lines = []
    for n, raw in enumerate(text.split("\n"), 1):
        if "\t" in raw or "\r" in raw:
            raise YamlSubsetError(f"line {n}: a tab or a carriage return")
        body = raw.lstrip(" ")
        if not body or body.startswith("#"):
            continue
        ind = len(raw) - len(body)
        body = _uncomment(body.rstrip(), n)
        if body.startswith("- ") and _KEY.match(body[2:].lstrip()):
            rest = body[2:].lstrip()
            lines += [(n, ind, "-"), (n, ind + len(body) - len(rest), rest)]
        else:
            lines.append((n, ind, body))

    def block(i, ind):
        return seq(i, ind) if lines[i][2] == "-" or lines[i][2].startswith("- ") else mapping(i, ind)

    def nested(i, ind):
        if i < len(lines) and lines[i][1] > ind:
            return block(i, lines[i][1])
        return None, i

    def mapping(i, ind):
        out = {}
        while i < len(lines) and lines[i][1] == ind:
            n, _, s = lines[i]
            m = _KEY.match(s)
            if not m:
                raise YamlSubsetError(f"line {n}: not a key")
            if m.group(1) in out:
                raise YamlSubsetError(f"line {n}: a duplicate key")
            i += 1
            if m.group(2):
                out[m.group(1)] = _scalar(m.group(2), n)
            else:
                out[m.group(1)], i = nested(i, ind)
        if i < len(lines) and lines[i][1] > ind:
            raise YamlSubsetError(f"line {lines[i][0]}: an unexpected indent")
        return out, i

    def seq(i, ind):
        out = []
        while i < len(lines) and lines[i][1] == ind:
            n, _, s = lines[i]
            if s == "-":
                v, i = nested(i + 1, ind)
                out.append(v)
            elif s.startswith("- "):
                out.append(_scalar(s[2:].strip(), n))
                i += 1
            else:
                raise YamlSubsetError(f"line {n}: a key where a list item belongs")
        if i < len(lines) and lines[i][1] > ind:
            raise YamlSubsetError(f"line {lines[i][0]}: an unexpected indent")
        return out, i

    value, i = block(0, lines[0][1])
    if i != len(lines):
        raise YamlSubsetError(f"line {lines[i][0]}: left over")
    return value


def test_the_yaml_subset_reader_reads_what_it_claims_and_refuses_the_rest():
    sample = ("# head\non:\n  schedule:\n    - cron: \"7 * * * *\"  # c\na:\n  - one\n  - k: 'it''s'\n    n: 2\n"
              "b: true\nc: x == 'y z' # tail\n")
    assert parse_yaml_subset(sample) == {"on": {"schedule": [{"cron": "7 * * * *"}]},
                                         "a": ["one", {"k": "it's", "n": 2}], "b": True, "c": "x == 'y z'"}
    for bad in ("a: no\n", "a: &x 1\n", "a: [1]\n", "a: |\n  x\n", "a: 1\na: 2\n", "a:\n\tb: 1\n", "a: 3.12\n",
                "a: b: c\n", "a:\n  b: 1\n   c: 2\n"):
        with pytest.raises(YamlSubsetError):
            parse_yaml_subset(bad)
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml is not None and WORKFLOW.exists():
        theirs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        theirs["on"] = theirs.pop(True)
        assert parse_yaml_subset(WORKFLOW.read_text(encoding="utf-8")) == theirs


def workflow():
    text = WORKFLOW.read_bytes().decode("utf-8").replace("\r\n", "\n")
    return text, parse_yaml_subset(text)


def code_of(text):
    """The workflow without its comments: the header names what the file does not do, in words."""
    return "\n".join(_uncomment(ln, n) for n, ln in enumerate(text.split("\n"), 1) if not ln.lstrip().startswith("#"))


def steps_of(wf):
    return wf["jobs"]["watch"]["steps"]


def test_the_workflow_runs_on_a_schedule_and_by_hand_only_in_this_repository(ut):
    text, wf = workflow()
    assert set(wf) == {"name", "on", "permissions", "jobs"}
    assert set(wf["on"]) == {"schedule", "workflow_dispatch"}
    assert wf["on"]["schedule"] == [{"cron": "7,17,27,37,47,57 * * * *"}]
    inputs = wf["on"]["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"drill"}
    assert (inputs["drill"]["type"], inputs["drill"]["options"], inputs["drill"]["default"]) == \
        ("choice", ["no", "yes"], "no")
    assert wf["permissions"] == {"contents": "read"}
    assert list(wf["jobs"]) == ["watch"]
    job = wf["jobs"]["watch"]
    assert job["if"] == "github.repository == 'matharrismma/concordance-2'"
    assert job["runs-on"] == "ubuntu-latest", "the tool runs on the runner's own python3"
    assert set(job) == {"if", "runs-on", "timeout-minutes", "steps"}, "no permissions, concurrency or env of its own"
    assert "concurrency" not in code_of(text)


def test_every_step_continues_on_error_with_its_own_timeout_under_the_jobs(ut):
    _, wf = workflow()
    job = wf["jobs"]["watch"]
    steps = steps_of(wf)
    assert [s.get("uses", "").split("@")[0] or "run" for s in steps] == \
        ["actions/checkout", "actions/cache/restore", "run", "actions/cache/save"]
    for s in steps:
        assert s["continue-on-error"] is True, s["name"]
        assert type(s["timeout-minutes"]) is int, s["name"]
    assert [s["timeout-minutes"] for s in steps] == [2, 2, 6, 2]
    assert sum(s["timeout-minutes"] for s in steps) == 12 < job["timeout-minutes"] == 20
    assert steps[1]["env"] == {"SEGMENT_DOWNLOAD_TIMEOUT_MINS": 1}


def test_the_state_is_saved_under_the_run_and_attempt_only_when_the_tool_finished(ut):
    _, wf = workflow()
    checkout, restore, tool, save = steps_of(wf)
    key = "uptime-state-${{ github.run_id }}-${{ github.run_attempt }}"
    assert restore["with"] == {"path": ".uptime-state.json", "key": key, "restore-keys": "uptime-state-"}
    assert save["with"] == {"path": ".uptime-state.json", "key": key}
    assert save["if"] == "steps.%s.outputs.finished == 'true'" % tool["id"]
    assert "if" not in restore and "if" not in tool and "if" not in checkout
    assert tool["run"] == "python3 tools/uptime.py --state .uptime-state.json --ntfy https://ntfy.sh"
    assert tool["env"] == {"NTFY_TOPIC": "${{ secrets.NTFY_TOPIC }}", "UPTIME_DRILL": "${{ inputs.drill }}"}


def test_the_workflow_pins_every_action_and_holds_one_secret(ut):
    text, wf = workflow()
    checkout = steps_of(wf)[0]
    assert checkout["with"] == {"persist-credentials": False}
    uses = [ln for ln in text.split("\n") if re.match(r"^\s*(-\s+)?uses:", ln)]
    assert len(uses) == 3
    for ln in uses:
        assert re.fullmatch(r"\s*(-\s+)?uses: [a-z-]+/[a-z-]+(/[a-z-]+)?@[0-9a-f]{40} # v\d+\.\d+\.\d+", ln), ln
    assert re.findall(r"secrets\.([A-Za-z0-9_]+)", text) == ["NTFY_TOPIC"]
    code = code_of(text)
    for absent in ("github.token", "GITHUB_TOKEN", "pull_request", "issue", "mention", "assignee", "@v", "email"):
        assert absent not in code.lower() if absent.islower() else absent not in code, absent
    for s in steps_of(wf):
        assert not re.search(r"(^|[\s;&|(])gh(\s|$)", s.get("run", "")), "no gh call"


def test_the_workflow_header_states_githubs_schedule_in_full(ut):
    text, _ = workflow()
    header = " ".join(ln.lstrip("# ").strip() for ln in text.split("\n")[:text.split("\n").index("name: Uptime")])
    for phrase in ("delayed under load", "top of the hour", "dropped", "best case and not a bound", "60 days",
                   "heartbeat", "silence", "rate limits", "per sending address", "runners share addresses",
                   "retried and then owed", "shares nothing with the box", "notice before it turns schedules off",
                   "not known here", "about two minutes", "about twenty", "a lost runner", "an outage of GitHub's own",
                   "a workflow file GitHub rejects", "notification setting", "persist-credentials false",
                   "duplicate push"):
        assert phrase in header, phrase
