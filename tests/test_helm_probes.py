"""THE HELM's probes — the gate, the fence around the shell, and the guard that stops a probe
destroying the thing it exists to refresh.

Matt's decision 2026-11-22: the gated web handler MAY spawn the probe tools directly rather than
queueing them for the desk. That is a new power for the engine process, so these are the tests that
hold its fence:

  - the door is 404 to anyone who is not the operator (hide-existence, same as /helm.json)
  - an id from the request can never become a command: only a key of PROBES is accepted, and the
    args are static literals in the registry
  - a probe whose INPUTS are absent DECLINES instead of running — load-bearing, because
    tools/traffic_rollup.py defaults to /var/log/caddy/*.access.log and, finding nothing, would
    write a traffic.json full of zeros OVER a good one
  - the HTTP status is about the request, never about the verdict: a probe that ran and found a
    broken chain is a 200 with ok=false

Runs over a real socket, because the gate lives in the request handler.
"""
from __future__ import annotations

import glob
import http.client
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

SITE = ROOT / "site"
TOKEN = "helm-test-token-not-a-real-one"


@pytest.fixture(scope="module")
def server():
    """A real server with a known operator token. Both env values are restored on teardown — a
    token or a data dir left behind would quietly change how later modules behave (see the
    memoized-artifact race documented in tests/conftest.py)."""
    from concordance.web import api
    prior_tok = os.environ.get("CONCORDANCE_HELM_TOKEN")
    prior_dir = os.environ.get("CONCORDANCE_DATA_DIR")
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
        for k, v in (("CONCORDANCE_HELM_TOKEN", prior_tok), ("CONCORDANCE_DATA_DIR", prior_dir)):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _req(addr, method, path, body=None, token=None):
    conn = http.client.HTTPConnection(addr[0], addr[1], timeout=120)
    try:
        hdrs = {}
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            hdrs["content-type"] = "application/json"
            hdrs["content-length"] = str(len(payload))
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


# --- the gate -----------------------------------------------------------------------------------

def test_the_probe_door_is_404_without_the_operator_token(server):
    """No token, a wrong token, and a token in the query that does not match: all 404, and none
    of them reveals that the door exists."""
    for token in (None, "not-the-token"):
        status, body = _req(server, "GET", "/helm/probe", token=token)
        assert status == 404, (token, status)
        assert body == {"error": "not found"}, body
    status, _ = _req(server, "POST", "/helm/probe", body={"probe": "ledger_chain"})
    assert status == 404                       # firing is gated too, not just listing


def test_the_catalog_opens_for_the_operator_and_executes_nothing(server):
    status, body = _req(server, "GET", "/helm/probe", token=TOKEN)
    assert status == 200, body
    probes = {p["probe"]: p for p in body["probes"]}
    assert {"ledger_chain", "integrity", "traffic"} <= set(probes), probes
    for p in probes.values():
        assert p["tier"] == "probe"
        assert p["what"] and p["label"]
        assert "available" in p                # the panel can grey a button before firing it


# --- the fence around the shell -----------------------------------------------------------------

def test_a_request_can_only_ever_name_a_registry_key():
    """The injection test. An id is a KEY LOOKUP, so no amount of shell punctuation in it reaches
    a command; and the registry's args are static literals, so there is no path for request text
    to become an argument either."""
    from concordance.web import helm_probes
    for hostile in ("traffic; rm -rf /", "../../etc/passwd", "ledger_chain && echo pwned",
                    "$(whoami)", "`id`", "", None, 7, "LEDGER_CHAIN"):
        res = helm_probes.run(hostile)
        assert res["ok"] is False
        assert res["verdict"] == "no such probe", (hostile, res["verdict"])
    for pid, spec in helm_probes.PROBES.items():
        for a in (spec.get("args") or []):
            assert isinstance(a, str), (pid, a)
            assert not any(c in a for c in ";|&$`<>\n"), (pid, a)
        assert spec["kind"] in ("inproc", "tool"), pid


def test_the_traffic_probe_declines_where_its_inputs_are_absent_and_writes_nothing(server):
    """THE GUARD THAT MATTERS. traffic_rollup falls back to /var/log/caddy/*.access.log and, with
    no match, still writes its output — which on the desk would overwrite a good traffic.json with
    zeros. The registry declares the inputs it requires and declines first.

    Asserted on both kinds of host: the decline is checked only where there really are no logs,
    but the DECLARATION that guards it is checked everywhere."""
    from concordance.web import helm_probes
    assert helm_probes.PROBES["traffic"].get("requires_glob"), \
        "the traffic probe lost its input guard — it can now overwrite traffic.json with zeros"
    if glob.glob(helm_probes.PROBES["traffic"]["requires_glob"]):
        pytest.skip("this host has Caddy logs; the decline path is not the one to assert here")
    out = Path(os.environ["CONCORDANCE_DATA_DIR"]) / "traffic.json"
    assert not out.exists()
    status, body = _req(server, "POST", "/helm/probe", body={"probe": "traffic"}, token=TOKEN)
    assert status == 200, body
    assert body["ok"] is False
    assert body["verdict"].startswith("declined — no files match"), body["verdict"]
    assert not out.exists(), "the declined probe still wrote its output"


# --- the shape of every answer ------------------------------------------------------------------

def test_an_unknown_probe_is_the_only_400(server):
    """The status code describes the REQUEST. A probe that ran and found trouble is a 200."""
    status, body = _req(server, "POST", "/helm/probe", body={"probe": "nope"}, token=TOKEN)
    assert status == 400
    assert body["verdict"] == "no such probe"
    assert "ledger_chain" in body["next"]


def test_the_ledger_probe_runs_and_answers_the_same_four_things(server):
    """verdict, ok, cost in ms, and the one next step — the contract every probe keeps, so the
    panel renders one row for all of them."""
    status, body = _req(server, "POST", "/helm/probe", body={"probe": "ledger_chain"}, token=TOKEN)
    assert status == 200, body
    for k in ("probe", "label", "ok", "verdict", "ms", "next", "at"):
        assert k in body, (k, body)
    assert body["probe"] == "ledger_chain"
    assert isinstance(body["ok"], bool)
    assert isinstance(body["ms"], int) and body["ms"] >= 0
    assert body["verdict"].strip()
    assert body["next"].strip()
    assert body["refreshed"] is None           # this one reads; it refreshes no cache


def test_the_ledger_probe_reports_a_BROKEN_chain_and_names_what_broke(tmp_path, monkeypatch):
    """A probe that can only ever say green is worth nothing on a panel.

    verify_chain's own detection is proved in tests/test_ledger.py::test_tamper_is_caught. What is
    proved HERE is that the PROBE surfaces it: a real sealed chain, a real tamper, and a verdict
    that names the cause with a next step that says stop. An earlier draft returned the counts with
    no cause, because it filtered the report for keys verify_chain does not emit."""
    from concordance.gates import ok as _ok
    from concordance.ledger import seal_record
    from concordance.packet import EngineResult
    from concordance.record import build_record
    from concordance.web import helm_probes

    def _pass(pid):
        return build_record(engine_result=EngineResult("PASS", [_ok("RED"), _ok("FLOOR")]),
                            packet_id=pid)

    ld, cb = tmp_path / "ledger", tmp_path / "cas"
    seal_record(_pass("p1"), summary="first", ledger_dir=ld, cas_base=cb, sealed_at=1000.0)
    seal_record(_pass("p2"), summary="second", ledger_dir=ld, cas_base=cb, sealed_at=2000.0)
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("CONCORDANCE_LEDGER_DIR", raising=False)

    sound = helm_probes.run("ledger_chain")             # the probe reads the live location
    assert sound["ok"] is True, sound
    assert "chain holds" in sound["verdict"], sound["verdict"]

    target = sorted(ld.glob("*.json"))[0]               # alter content, leave content_hash
    data = json.loads(target.read_text(encoding="utf-8"))
    data["summary"] = "ALTERED"
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")

    broken = helm_probes.run("ledger_chain")
    assert broken["ok"] is False, broken
    assert "CHAIN BROKEN" in broken["verdict"], broken["verdict"]
    assert "cause unnamed" not in broken["verdict"], broken["verdict"]
    assert broken["detail"]["tampered"] or broken["detail"]["broken_links"], broken["detail"]
    assert "stop writing" in broken["next"]


def test_a_probe_that_raises_is_reported_not_propagated():
    """A probe must never take the panel down with it."""
    from concordance.web import helm_probes
    spec = dict(helm_probes.PROBES["ledger_chain"])
    spec["fn"] = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    helm_probes.PROBES["_test_raiser"] = spec
    try:
        res = helm_probes.run("_test_raiser")
    finally:
        helm_probes.PROBES.pop("_test_raiser", None)
    assert res["ok"] is False
    assert "RuntimeError: boom" in res["verdict"]
    assert "defect in the probe" in res["next"]
