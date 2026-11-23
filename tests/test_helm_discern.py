"""THE HELM's discernment tier — the three outcomes, and the one that matters.

A readout with two states (green / red) cannot tell an operator anything he did not already assume.
A discernment has THREE:

    it holds            ok=True,  tell=True
    it does not hold    ok=False, tell=True  — and it names WHICH inputs disagree
    it cannot be judged           tell=False — and it names the MISSING input

The middle one is the reason this tier exists. When two independent walks of the same record
disagree, the finding is not which is right but that the method is in question. These tests force
each outcome, including the two that a healthy machine never produces on its own — which is exactly
why they have to be forced rather than waited for.
"""
from __future__ import annotations

import http.client
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

SITE = ROOT / "site"
TOKEN = "helm-discern-test-token"


@pytest.fixture(scope="module")
def server():
    from concordance.web import api
    prior = {k: os.environ.get(k) for k in ("CONCORDANCE_HELM_TOKEN", "CONCORDANCE_DATA_DIR")}
    os.environ["CONCORDANCE_HELM_TOKEN"] = TOKEN
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    httpd = api.build_server(host="127.0.0.1", port=0, surface="secular",
                            site_dir=str(SITE), warm=False)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield ("127.0.0.1", httpd.server_address[1])
    finally:
        httpd.shutdown()
        for k, v in prior.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _req(addr, method, path, body=None, token=None):
    conn = http.client.HTTPConnection(addr[0], addr[1], timeout=120)
    try:
        hdrs, payload = {}, None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            hdrs = {"content-type": "application/json", "content-length": str(len(payload))}
        if token:
            hdrs["X-Helm-Token"] = token
        conn.request(method, path, body=payload, headers=hdrs)
        r = conn.getresponse()
        raw = r.read()
        try:
            return r.status, json.loads(raw or b"{}")
        except ValueError:
            return r.status, {}
    finally:
        conn.close()


def _fake_probes(monkeypatch, answers):
    """Force the probe layer's answers so a rule can be tested on inputs a healthy engine will
    never produce. The rule under test is the subject; the probes are not."""
    from concordance.web import helm_discern

    def fake(pid, **kw):
        return dict(answers[pid], probe=pid, ms=1, at=int(time.time()))
    monkeypatch.setattr(helm_discern.helm_probes, "run", fake)
    return helm_discern


# --- the gate -----------------------------------------------------------------------------------

def test_the_discernment_door_is_404_without_the_operator_token(server):
    for method, body in (("GET", None), ("POST", {"discernment": "truth"})):
        status, payload = _req(server, method, "/helm/discern", body=body)
        assert status == 404, (method, status)
        assert payload == {"error": "not found"}


def test_the_catalog_opens_for_the_operator_and_says_how_many_probes_it_fires(server):
    status, body = _req(server, "GET", "/helm/discern", token=TOKEN)
    assert status == 200, body
    by = {d["discernment"]: d for d in body["discernments"]}
    assert {"truth", "served"} <= set(by)
    assert by["truth"]["fires"] == 2 and by["truth"]["probes"] == ["ledger_chain", "integrity"]
    assert by["served"]["fires"] == 1
    for d in by.values():
        assert d["tier"] == "discernment" and d["question"]


def test_an_unknown_discernment_is_the_only_400(server):
    status, body = _req(server, "POST", "/helm/discern", body={"discernment": "nope"}, token=TOKEN)
    assert status == 400
    assert body["verdict"] == "no such discernment"
    assert "truth" in body["next"]


# --- outcome 1: it holds ------------------------------------------------------------------------

def test_two_walks_that_agree_read_as_the_record_standing(monkeypatch):
    hd = _fake_probes(monkeypatch, {
        "ledger_chain": {"ok": True, "verdict": "chain holds — 9/9 verified"},
        "integrity": {"ok": True, "verdict": "INTEGRITY: OK"},
    })
    res = hd.run("truth")
    assert res["ok"] is True and res["tell"] is True
    assert "two independent walks agree" in res["verdict"]
    assert [t["probe"] for t in res["trail"]] == ["ledger_chain", "integrity"]


# --- outcome 2: it does not hold, and names which inputs disagree -------------------------------

def test_a_discordance_between_the_two_walks_indicts_the_METHOD(monkeypatch):
    """THE TEST THIS TIER EXISTS FOR. One walk sound, the other not: the verdict must refuse to
    pick a winner and say the method is in question."""
    hd = _fake_probes(monkeypatch, {
        "ledger_chain": {"ok": True, "verdict": "chain holds — 9/9 verified"},
        "integrity": {"ok": False, "verdict": "INTEGRITY: FAIL"},
    })
    res = hd.run("truth")
    assert res["ok"] is False and res["tell"] is True
    assert "DISCORDANCE" in res["verdict"]
    assert "the chain probe" in res["verdict"] and "the integrity sweep" in res["verdict"]
    assert "indicts the METHOD" in res["verdict"]
    assert "do not act on either verdict" in res["verdict"]

    # and the other way round, so the naming is not hard-coded to one side
    hd = _fake_probes(monkeypatch, {
        "ledger_chain": {"ok": False, "verdict": "CHAIN BROKEN — 1 tampered (8/9 verified)"},
        "integrity": {"ok": True, "verdict": "INTEGRITY: OK"},
    })
    res = hd.run("truth")
    assert "DISCORDANCE" in res["verdict"]


def test_when_both_walks_agree_it_is_broken_it_says_so_plainly(monkeypatch):
    hd = _fake_probes(monkeypatch, {
        "ledger_chain": {"ok": False, "verdict": "CHAIN BROKEN — 1 tampered (8/9 verified)"},
        "integrity": {"ok": False, "verdict": "INTEGRITY: FAIL"},
    })
    res = hd.run("truth")
    assert res["ok"] is False and res["tell"] is True
    assert "THE RECORD IS BROKEN" in res["verdict"]
    assert "stop writing" in res["next"]


# --- outcome 3: it cannot be judged, and names the missing input --------------------------------

def test_a_declined_probe_makes_the_discernment_say_I_CANNOT_TELL(monkeypatch):
    """One walk alone cannot confirm the other, so a missing input is not a green light."""
    hd = _fake_probes(monkeypatch, {
        "ledger_chain": {"ok": True, "verdict": "chain holds — 9/9 verified"},
        "integrity": {"ok": False, "verdict": "declined — tools/integrity_check.py is not present in this tree"},
    })
    res = hd.run("truth")
    assert res["tell"] is False
    assert res["ok"] is False                       # never ok when it cannot be judged
    assert res["verdict"].startswith("I cannot tell —")
    assert "integrity" in res["missing"]
    assert "one walk alone cannot confirm the other" in res["verdict"]


def test_served_cannot_tell_without_a_rollup(server, monkeypatch):
    """The data dir is a fresh temp dir, so there is no traffic.json to read."""
    hd = _fake_probes(monkeypatch, {
        "traffic": {"ok": False, "verdict": "declined — no files match /var/log/caddy/*.access.log"},
    })
    res = hd.run("served")
    assert res["tell"] is False and res["ok"] is False
    assert "no traffic rollup to read" in res["verdict"]
    assert res["missing"] == ["traffic.json"]


def test_a_rule_that_raises_is_reported_as_cannot_tell_not_propagated(monkeypatch):
    from concordance.web import helm_discern
    hd = _fake_probes(monkeypatch, {"traffic": {"ok": True, "verdict": "fine"}})
    monkeypatch.setitem(helm_discern.DISCERNMENTS["served"], "rule",
                        lambda res: (_ for _ in ()).throw(RuntimeError("boom")))
    res = hd.run("served")
    assert res["tell"] is False
    assert "the rule itself failed" in res["verdict"] and "RuntimeError: boom" in res["verdict"]
    assert "defect in the discernment" in res["next"]


# --- the served rule on real rollup shapes ------------------------------------------------------

def _write_rollup(data_dir, generated_at, doors):
    p = Path(data_dir) / "traffic.json"
    p.write_text(json.dumps({"generated_at": generated_at, "window_days": 30,
                             "fruit": {"doors": doors}}), encoding="utf-8")


def test_served_quotes_the_busiest_door_and_flags_a_stale_rollup(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    hd = _fake_probes(monkeypatch, {"traffic": {"ok": True, "verdict": "rolled up"}})

    _write_rollup(tmp_path, time.time(), {"/mcp": {"agent": 77981}, "/ask": {"human": 5, "agent": 15}})
    fresh = hd.run("served")
    assert fresh["tell"] is True and fresh["ok"] is True
    assert "/mcp" in fresh["verdict"] and "77981" in fresh["verdict"]
    assert "the agent door carries" in fresh["verdict"]      # the inversion, stated as a ratio
    assert fresh["detail"]["doors"]["/ask"] == 20

    _write_rollup(tmp_path, time.time() - 14 * 86400, {"/mcp": {"agent": 10}, "/ask": {"human": 1}})
    stale = hd.run("served")
    assert stale["tell"] is True
    assert stale["ok"] is False, "a 14-day-old rollup must not read as a current answer"
    assert "14.0 days old" in stale["verdict"]
    assert "describes the past, not now" in stale["verdict"]
    assert "refresh traffic" in stale["next"]


def test_served_cannot_tell_when_every_door_reads_zero(monkeypatch, tmp_path):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    hd = _fake_probes(monkeypatch, {"traffic": {"ok": True, "verdict": "rolled up"}})
    _write_rollup(tmp_path, time.time(), {"/mcp": {"agent": 0}, "/ask": {"human": 0}})
    res = hd.run("served")
    assert res["tell"] is False
    assert "every watched door reads zero" in res["verdict"]
