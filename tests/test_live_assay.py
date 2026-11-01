"""THE LIVE ASSAY WITH A RATCHET — the pure parts: the path resolver, the expectations, the ratchet, and the
probe file's own shape. The wire is exercised nightly on the box, never here."""
import json
import sys
from pathlib import Path

import pytest  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))                 # so `from tools import live_assay` resolves (as test_coach does)
from tools import live_assay as la  # noqa: E402

ANSWER = {"kind": "found", "lead": {"id": "card_a", "excerpt": "x" * 120}, "results": [{"id": "c1"}, {"id": "c2"}],
          "path": {"type": "shadow", "anchor": {"ref": "John 14:6"}}, "resources": [{"label": "Call or text 988"}],
          "house": {"next_step": {"do": "Reach a real person right now", "door": "WALK"}}, "gate_open": False, "doors": {"a": 1, "b": 2}}


def test_resolve_walks_keys_indexes_and_stars():
    assert la.resolve(ANSWER, "lead.id") == ["card_a"]
    assert la.resolve(ANSWER, "results[*].id") == ["c1", "c2"]
    assert la.resolve(ANSWER, "results[1].id") == ["c2"] and la.resolve(ANSWER, "results[-1].id") == ["c2"]
    assert la.resolve(ANSWER, "path.anchor.ref") == ["John 14:6"]
    assert la.resolve(ANSWER, "nowhere.at.all") == [] and la.resolve(ANSWER, "") == [ANSWER]


def test_every_expectation_kind():
    r = lambda at: la.resolve(ANSWER, at)
    assert la.check(r("kind"), {"at": "kind", "eq": "found"})[0]
    assert la.check(r("kind"), {"at": "kind", "ne": "crisis"})[0]
    assert la.check(r("kind"), {"at": "kind", "in": ["found", "compute"]})[0]
    assert la.check(r("resources[0].label"), {"at": "x", "contains": "988"})[0]
    assert la.check(r("house.next_step.do"), {"at": "x", "startswith": "reach a real"})[0]       # case-blind
    assert la.check(r("results[*].id"), {"at": "x", "has": "c2"})[0] and not la.check(r("results[*].id"), {"at": "x", "has": "c9"})[0]
    assert la.check(r("doors"), {"at": "x", "len": 2})[0] and la.check(r("lead.excerpt"), {"at": "x", "min_len": 100})[0]
    assert la.check(r("house.next_step.tool"), {"at": "x", "absent": True})[0]
    assert la.check(r("lead"), {"at": "x", "exists": True})[0]
    assert la.check(r("gate_open"), {"at": "x", "eq": False})[0] and la.check(r("gate_open"), {"at": "x", "truthy": False})[0]
    ok, why = la.check([], {"at": "lead.id", "eq": "card_a"})
    assert not ok and "absent" in why


def test_evaluate_requires_status_and_every_expectation():
    probe = {"id": "p", "expect": [{"at": "lead.id", "eq": "card_a"}, {"at": "kind", "eq": "crisis"}]}
    ok, fails = la.evaluate(probe, ANSWER, 200)
    assert not ok and len(fails) == 1 and "kind" in fails[0]
    ok, fails = la.evaluate({"id": "p", "expect": [{"at": "lead.id", "eq": "card_a"}]}, ANSWER, 500)
    assert not ok and fails[0].startswith("status 500")
    assert la.evaluate({"id": "p", "expect": []}, {}, 200) == (True, [])


def test_the_floor_only_rises_and_a_known_miss_never_regresses():
    floor = {"ids": ["a", "b", "k"], "since": "2026-10-03"}
    r = la.ratchet(floor, passed=["a", "c"], failed=["b", "k", "m"], known_miss=["k", "m"])
    assert r["regressed"] == ["b"]                      # in the floor, failed, not a known miss
    assert r["newly_passing"] == ["c"]
    assert r["ids"] == ["a", "b", "c", "k"]              # b stays in the floor: the floor never falls
    r2 = la.ratchet(r, passed=["a", "b", "c", "k", "m"], failed=[], known_miss=["k", "m"])
    assert r2["regressed"] == [] and r2["newly_passing"] == ["m"] and "m" in r2["ids"]


def test_the_probe_file_is_sound():
    probes = la.load_probes(Path(__file__).resolve().parent.parent / "eval" / "live_probes.jsonl")
    ids = [p["id"] for p in probes]
    assert len(ids) == len(set(ids)) and len(probes) >= 30
    for p in probes:
        assert p["path"].startswith("/") and isinstance(p.get("expect"), list), p["id"]
        assert p.get("face", "secular") in ("secular", "witness", "public"), p["id"]
        for spec in p["expect"]:
            assert "at" in spec and len([k for k in spec if k != "at"]) == 1, (p["id"], spec)
        if p.get("body") is not None:
            json.dumps(p["body"])
    known = [p["id"] for p in probes if p.get("known_miss")]
    assert "verify.lookup.fact.iron.melts.holds.someday" in known            # the assay's want list
    assert "verify.wrong.constant.km.per.s.breaks" not in known               # graduated to the floor (R4, 2026-10-03)
    assert "ask.cry.help.first" not in known


def _http_error(code, retry_after=None):
    import io
    import urllib.error
    from email.message import Message
    hdrs = Message()
    if retry_after is not None:
        hdrs["Retry-After"] = str(retry_after)
    return urllib.error.HTTPError("http://x/stick", code, "refused", hdrs, io.BytesIO(b'{"error": "rate limit exceeded"}'))


class _Resp:
    status = 200

    def __init__(self, body: bytes):
        self._b = body

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_a_429_is_not_a_verdict_the_wire_waits_retry_after_once(monkeypatch):
    """The gate refused a good deploy (2026-11-01) on two /stick probes the limiter answered 429 — every
    probe shares the box's one loopback key and the probe set crossed the write bucket. A 429 says "come
    back later": honour Retry-After once, then judge the answer the door actually gives."""
    calls, slept = [], []

    def fake_urlopen(req, timeout=None):
        calls.append(req.full_url)
        if len(calls) == 1:
            raise _http_error(429, retry_after=7)
        return _Resp(b'{"fit": {"record": 5}}')
    monkeypatch.setattr(la.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(la.time, "sleep", lambda s: slept.append(s))
    status, body = la.fetch({"id": "stick.x", "path": "/stick", "query": {"id": "stick_x"}})
    assert (status, body) == (200, {"fit": {"record": 5}})
    assert len(calls) == 2 and slept == [7]                      # one wait, the Retry-After the door named


def test_a_second_429_still_counts_and_the_wait_is_bounded(monkeypatch):
    slept = []
    monkeypatch.setattr(la.urllib.request, "urlopen", lambda req, timeout=None: (_ for _ in ()).throw(_http_error(429, retry_after=600)))
    monkeypatch.setattr(la.time, "sleep", lambda s: slept.append(s))
    status, body = la.fetch({"id": "stick.y", "path": "/stick"})
    assert status == 429 and body == {"error": "rate limit exceeded"}
    assert slept == [65]                                          # bounded, and only once
    # any other refusal is returned as it came, with no wait
    slept.clear()
    monkeypatch.setattr(la.urllib.request, "urlopen", lambda req, timeout=None: (_ for _ in ()).throw(_http_error(404)))
    assert la.fetch({"id": "z", "path": "/nowhere"})[0] == 404 and slept == []


def test_seal_clean_reads_the_receipt(monkeypatch):
    calls = []
    def fake_fetch(probe):
        calls.append(probe["path"])
        return 200, {"_text": "verdict HOLDS; claim: my patient [PERSON], [ID], weighs 80 kg"}
    monkeypatch.setattr(la, "fetch", fake_fetch)
    probe = {"id": "p", "seal_clean": ["John Smith", "123-45-6789"]}
    assert la.seal_clean(probe, {"receipt": "https://narrowhighway.org/s/abc"}) == [] and calls == ["/s/abc"]
    monkeypatch.setattr(la, "fetch", lambda probe: (200, {"_text": "claim: my patient John Smith"}))
    assert la.seal_clean(probe, {"receipt": "/s/abc"}) == ["seal carries 'John Smith'"]
    assert la.seal_clean(probe, {}) == ["seal_clean: no receipt on the answer"]
