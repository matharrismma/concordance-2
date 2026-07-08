"""Door 2 — the auditor verifies ARGUMENTS (chains) and CODE, via the shipped /verify path.

reason.html drives POST /verify with either a chained `steps` derivation (an argument) or a
computer_science functional_correctness packet (code). Both were already backed by the engine;
this locks the contract the page depends on: a chain names WHERE it breaks; code runs.

Runnable with pytest OR `python tests/test_reason.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance.config import EngineConfig  # noqa: E402
from concordance.web.api import dispatch  # noqa: E402

CFG = EngineConfig("secular")


def _verify(body):
    status, payload = dispatch("POST", "/verify", {"seal": "0"}, body, CFG)
    assert status == 200, (status, payload)
    return payload


def test_argument_chain_holds():
    body = {"steps": [
        {"id": "s1", "domain": "mathematics", "spec": {"mode": "equality", "params": {"expr_a": "3**2+4**2", "expr_b": "25"}}},
        {"id": "s2", "domain": "mathematics", "spec": {"mode": "equality", "params": {"expr_a": "sqrt(25)", "expr_b": "5"}}, "uses": ["s1"]},
    ]}
    d = _verify(body)
    assert d["verdict"] == "HOLDS", d


def test_argument_chain_names_where_trust_breaks():
    body = {"steps": [
        {"id": "s1", "domain": "mathematics", "spec": {"mode": "equality", "params": {"expr_a": "2+2", "expr_b": "4"}}},
        {"id": "s2", "domain": "mathematics", "spec": {"mode": "equality", "params": {"expr_a": "4*10", "expr_b": "39"}}, "uses": ["s1"]},
        {"id": "s3", "domain": "mathematics", "spec": {"mode": "equality", "params": {"expr_a": "39/3", "expr_b": "13"}}, "uses": ["s2"]},
    ]}
    d = _verify(body)
    assert d["verdict"] == "BROKEN" and d["broken_at"] == "s2", d
    trail = {t["id"]: t["status"] for t in d["trail"]}
    assert trail["s1"] == "CONFIRMED" and trail["s2"] == "MISMATCH"


def test_code_correct_holds_and_buggy_breaks():
    good = {"steps": [{"id": "a", "domain": "computer_science", "spec": {"CS_VERIFY": {
        "function_name": "square", "code": "def square(n):\n    return n * n",
        "test_cases": [{"args": [3], "expected": 9}, {"args": [-4], "expected": 16}]}}}]}
    assert _verify(good)["verdict"] == "HOLDS"
    bug = {"steps": [{"id": "a", "domain": "computer_science", "spec": {"CS_VERIFY": {
        "function_name": "square", "code": "def square(n):\n    return n + n",
        "test_cases": [{"args": [3], "expected": 9}]}}}]}
    assert _verify(bug)["verdict"] == "BROKEN"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} reason tests passed — arguments name where trust breaks; code runs.")
