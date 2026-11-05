"""CONCORDANCE_ALLOW_CODE_EXEC is the real control on computer_science's exec, proved through both doors.

computer_science.py says of itself that a restricted namespace is no sandbox, so what stands between a request and
exec is one flag, default off. tests/conftest.py turns it on for the rest of the suite. Here it is off: a code packet
sent through web.api.dispatch and through the MCP handler runs nothing and is refused. The same packet with the flag on
sets the marker, which is what shows the packet would run. The marker is one attribute on the math module in this test
process.
"""
from __future__ import annotations

import json
import math

import pytest

from concordance.config import EngineConfig
from concordance.mcp.http import handle_http
from concordance.web import api

CONFIG = EngineConfig("secular")
FLAG = "CONCORDANCE_ALLOW_CODE_EXEC"
MARKER = "c2_code_exec_marker"
PACKET = {"CS_VERIFY": {"function_name": "f", "code": f"math.{MARKER} = 1\ndef f():\n    return 1\n",
                        "test_cases": [{"args": [], "expected": 1}]}}
STEPS = [{"id": "r", "domain": "computer_science", "spec": PACKET}]


@pytest.fixture(autouse=True)
def _keeping(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CONCORDANCE_CAS_DIR", str(tmp_path / "cas"))


@pytest.fixture(autouse=True)
def _no_marker():
    math.__dict__.pop(MARKER, None)
    yield
    math.__dict__.pop(MARKER, None)


def _through_dispatch() -> dict:
    status, out = api.dispatch("POST", "/verify", {"seal": "0"}, {"steps": STEPS}, CONFIG)
    assert status == 200, out
    return out


def _through_mcp() -> dict:
    call = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "verify", "arguments": {"steps": STEPS, "seal": False}}}
    status, _headers, raw = handle_http("POST", {}, json.dumps(call).encode("utf-8"), CONFIG)
    assert status == 200, raw
    return json.loads(json.loads(raw)["result"]["content"][0]["text"])


DOORS = {"dispatch": _through_dispatch, "mcp": _through_mcp}


@pytest.fixture(params=sorted(DOORS))
def post(request):
    return DOORS[request.param]


def test_with_the_flag_off_a_code_packet_runs_nothing_and_is_refused(monkeypatch, post):
    monkeypatch.delenv(FLAG, raising=False)
    r = post()
    assert not hasattr(math, MARKER), "the code ran with the flag off"
    assert r["verdict"] not in ("HOLDS", "BROKEN"), r
    assert not r.get("seal")
    assert "disabled" in json.dumps(r["trail"]), r


@pytest.mark.parametrize("value", ["", "0", "true", "yes", "2"])
def test_only_the_exact_value_turns_it_on(monkeypatch, post, value):
    monkeypatch.setenv(FLAG, value)
    r = post()
    assert not hasattr(math, MARKER), "the code ran"
    assert r["verdict"] not in ("HOLDS", "BROKEN"), r


def test_with_the_flag_on_the_same_packet_runs(monkeypatch, post):
    """The control: the packet above is live, so its refusal is the flag's doing and nothing else's."""
    monkeypatch.setenv(FLAG, "1")
    assert post()["verdict"] == "HOLDS"
    assert getattr(math, MARKER) == 1
