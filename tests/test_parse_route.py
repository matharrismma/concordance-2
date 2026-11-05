"""Text from a request is never evaluated, proved through the real doors.

One named test per input class, each sent through both of this repo's request paths with sealing off: web.api.dispatch,
which serves POST /verify with seal 0, and the MCP handler, which serves a tools/call of verify with seal false. Each
input is inert, equality mode for mathematics: it can only set a marker in this test process or print to this test's
stdout. Each test observes the reach itself: the marker in sys.__dict__, the bytes print wrote (a patched builtin could
not see them, because sympy's parser copies only the real builtin functions), or, for a compute limit, the verdict the
evaluated power reads. That no seal was written is read from the seal count and the chain, in a keeping of the test's own.

This file imports nothing the fix adds, so every test here collects at the step's base and is red there by its own
assertion. Each also runs under the tripwire: no str reaches sympy's string parser while the door is read.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent / "fixtures"))

from concordance.config import EngineConfig  # noqa: E402
from concordance.mcp.http import handle_http  # noqa: E402
from concordance.web import api  # noqa: E402
from parse_tripwire import tripwire  # noqa: E402

CONFIG = EngineConfig("secular")
MARKER = "c2_parse_route_marker"
SETS_MARKER = f"__import__('sys').__dict__.__setitem__('{MARKER}', 1)"   # evaluated, it sets one key in this process
JOINED_BIN = "sin((b\nin\n(5)))"           # with its line breaks a comparison; with them dropped a refused call
JOINED_PRINT = "Matrix(1,1,pr\nin\nt)"     # the same, reaching a function that writes to this test's stdout
CALLABLE_VALUE = "Matrix(1,1,print)"       # a refused function handed over as a value, never named in a call
CALLABLE_KEYWORD = "simplify(sin(x)**2+cos(x)**2,measure=print)"
CARET_POWER = "2^20000"                    # a power spelled so that the exponent limit did not see it
BASE_NESTED_POWER = "(2**1000)**2000"      # each exponent small, the base already large
ROOT_ON_THE_BASE = "((2**1000+1)**(1/2))**10000"   # the base shows no integer; sympy multiplies the exponents out
ROOT_IN_POW = "Pow(sqrt(2**1000+1),10000)"         # the same through the function spelling


@pytest.fixture(autouse=True)
def _keeping(tmp_path, monkeypatch):
    """A keeping of this test's own, so the seal count is this test's and nothing here reaches another store."""
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CONCORDANCE_CAS_DIR", str(tmp_path / "cas"))


@pytest.fixture(autouse=True)
def _no_marker():
    sys.__dict__.pop(MARKER, None)
    yield
    sys.__dict__.pop(MARKER, None)


def _seals() -> tuple:
    """This repo has no /ledger/verify: the seal count and the chain's head are what a write would move."""
    status, seals = api.dispatch("GET", "/seals", {}, None, CONFIG)
    assert status == 200, seals
    status, chain = api.dispatch("GET", "/sync/ledger", {"hashes_only": "1"}, None, CONFIG)
    assert status == 200, chain
    return seals["seals"]["minted"], seals["seals"]["receipt_cards"], chain["count"], chain["head"]


def _through_dispatch(domain: str, spec: dict) -> dict:
    body = {"steps": [{"id": "r", "domain": domain, "spec": spec}]}
    status, out = api.dispatch("POST", "/verify", {"seal": "0"}, body, CONFIG)
    assert status == 200, out
    return out


def _through_mcp(domain: str, spec: dict) -> dict:
    call = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "verify", "arguments": {"steps": [{"id": "r", "domain": domain, "spec": spec}], "seal": False}}}
    status, _headers, raw = handle_http("POST", {}, json.dumps(call).encode("utf-8"), CONFIG)
    assert status == 200, raw
    result = json.loads(raw)["result"]
    assert result["isError"] is False, result
    return json.loads(result["content"][0]["text"])


DOORS = {"dispatch": _through_dispatch, "mcp": _through_mcp}


@pytest.fixture(params=sorted(DOORS))
def post(request):
    return DOORS[request.param]


def _held(capsys, post, domain: str, spec: dict) -> None:
    before = _seals()
    capsys.readouterr()
    with tripwire() as hits:
        r = post(domain, spec)
    out = capsys.readouterr().out
    assert MARKER not in sys.__dict__, "the input was evaluated: the marker is set"
    assert out == "", f"the refused function was reached: {out!r}"
    assert r.get("verdict") not in ("HOLDS", "BROKEN"), f"the input was read: {r.get('verdict')}"
    assert not r.get("seal"), "a seal was written"
    assert _seals() == before, "the seal count moved"
    assert hits == [], f"text reached sympy's string parser: {hits!r}"


def _equality(capsys, post, expr_a: str, expr_b: str) -> None:
    _held(capsys, post, "mathematics", {"mode": "equality", "params": {"expr_a": expr_a, "expr_b": expr_b}})


def _physics(capsys, post, equation: str, symbols: dict) -> None:
    _held(capsys, post, "physics", {"PHYS_VERIFY": {"equation": equation, "symbols": symbols}})


def test_physics_equation_text_is_not_evaluated(capsys, post):
    _physics(capsys, post, f"x = {SETS_MARKER}", {"x": "m"})


def test_physics_unit_text_is_not_evaluated(capsys, post):
    _physics(capsys, post, "x = x", {"x": SETS_MARKER})


def test_joined_lines_read_as_a_refused_call_in_equality(capsys, post):
    _equality(capsys, post, JOINED_BIN, "sin(5)")


def test_joined_lines_reach_a_refused_function_in_equality(capsys, post):
    _equality(capsys, post, JOINED_PRINT, "1")


def test_joined_lines_read_as_a_refused_call_in_a_physics_equation(capsys, post):
    _physics(capsys, post, f"x = {JOINED_BIN}", {"x": "m"})


def test_joined_lines_reach_a_refused_function_in_a_physics_equation(capsys, post):
    _physics(capsys, post, f"x = {JOINED_PRINT}", {"x": "m"})


def test_joined_lines_read_as_a_refused_call_in_a_physics_unit(capsys, post):
    _physics(capsys, post, "x = x", {"x": JOINED_BIN})


def test_joined_lines_reach_a_refused_function_in_a_physics_unit(capsys, post):
    _physics(capsys, post, "x = x", {"x": JOINED_PRINT})


def test_caret_power_passes_no_limit_in_equality(capsys, post):
    _equality(capsys, post, CARET_POWER, CARET_POWER)


def test_base_nested_power_passes_no_limit_in_equality(capsys, post):
    _equality(capsys, post, BASE_NESTED_POWER, BASE_NESTED_POWER)


def test_caret_power_passes_no_limit_in_a_physics_equation(capsys, post):
    _physics(capsys, post, f"x = x*{CARET_POWER}/{CARET_POWER}", {"x": "m"})


def test_base_nested_power_passes_no_limit_in_a_physics_equation(capsys, post):
    _physics(capsys, post, f"x = x*{BASE_NESTED_POWER}/{BASE_NESTED_POWER}", {"x": "m"})


def test_root_on_the_base_side_passes_no_limit_in_equality(capsys, post):
    _equality(capsys, post, ROOT_ON_THE_BASE, ROOT_ON_THE_BASE)


def test_root_in_the_function_spelling_passes_no_limit_in_equality(capsys, post):
    _equality(capsys, post, ROOT_IN_POW, ROOT_IN_POW)


def test_root_on_the_base_side_passes_no_limit_in_a_physics_equation(capsys, post):
    _physics(capsys, post, f"x = x*{ROOT_ON_THE_BASE}/{ROOT_ON_THE_BASE}", {"x": "m"})


def test_root_on_the_base_side_passes_no_limit_in_a_physics_unit(capsys, post):
    _physics(capsys, post, "x = x", {"x": ROOT_ON_THE_BASE})


def test_callable_value_reaches_nothing_in_equality(capsys, post):
    _equality(capsys, post, CALLABLE_VALUE, CALLABLE_VALUE)


def test_callable_value_reaches_nothing_in_a_physics_equation(capsys, post):
    _physics(capsys, post, f"x = {CALLABLE_VALUE}", {"x": "m"})


def test_callable_value_reaches_nothing_in_a_physics_unit(capsys, post):
    _physics(capsys, post, "x = x", {"x": CALLABLE_VALUE})


def test_callable_keyword_reaches_nothing_in_equality(capsys, post):
    _equality(capsys, post, CALLABLE_KEYWORD, "1")
