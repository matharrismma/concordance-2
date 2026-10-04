"""VERIFIERS AS DATA, NOT DEPLOYS (Gen 3 · 2, 2026-10-04). A law held as data, run by one generic evaluator:
the electrical domain re-expressed as a spec gives the Python module's verdicts on the domain goldens; a NEW
check ships as data and runs without any code; a spec that cannot prove itself is refused at load; the
expression language is a whitelist; a spec never contradicts code (shadowing)."""
import json
import os
import tempfile
from pathlib import Path

import pytest

TMP = Path(tempfile.mkdtemp(prefix="nh-specs-"))
os.environ["CONCORDANCE_DATA_DIR"] = str(TMP)

from concordance import verifiers as V  # noqa: E402
from concordance.engine import EngineConfig  # noqa: E402
from concordance.verifiers import spec as S  # noqa: E402
from concordance.web import api  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ELECTRICAL = json.loads((ROOT / "eval" / "specs" / "electrical.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _own_data_dir():
    """The suite's fixtures re-point CONCORDANCE_DATA_DIR per test; the router reads the env at call
    time, so every test here pins it back to this module's scratch dir and re-reads the specs."""
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = str(TMP)
    S.load(TMP, force=True)
    try:
        yield
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior


def _write_specs(*specs):
    with open(TMP / S.SPEC_FILE, "w", encoding="utf-8") as f:
        for s in specs:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    S.load(TMP, force=True)


def test_the_expression_language_is_a_whitelist():
    assert S.safe_eval("I * R", {"I": 0.5, "R": 24}) == 12.0
    assert S.safe_eval("sum(V)", {"V": [9, -4.5, -4.5]}) == 0.0
    assert abs(S.safe_eval("V * (1 - exp(-t / (R * C)))", {"V": 5.0, "t": 1e-3, "R": 1000, "C": 1e-6}) - 3.1606) < 1e-3
    assert S.safe_eval("pi * r ** 2", {"r": 2}) == pytest.approx(12.566, abs=1e-3)
    for evil in ("__import__('os').system('x')", "(1).__class__", "[x for x in y]", "open('f')", "lambda: 1",
                 "I.real", "'a' + 'b'", "R if R else 1", "exec('1')"):
        with pytest.raises(S.SpecError):
            S.safe_eval(evil, {"I": 1, "R": 2, "y": [1]})
    with pytest.raises(S.SpecError):
        S.safe_eval("unknown + 1", {})


def test_the_electrical_spec_proves_itself_and_matches_the_code_on_the_goldens():
    assert S.validate(ELECTRICAL) == [] and S.prove(ELECTRICAL) == []
    goldens = json.loads((ROOT / "data" / "domain_goldens.json").read_text(encoding="utf-8"))["electrical"]
    mod = V._get_module("electrical")
    _write_specs(dict(ELECTRICAL, status="admitted"))
    for side in ("true", "false"):
        packet = {goldens["packet_key"]: goldens[side]}
        code = {r.name: r.status for r in mod.run(packet)}
        data = {r.name: r.status for r in S.run_for_domain("electrical", packet, data_dir=TMP)}
        shared = set(code) & set(data)
        assert shared >= {"electrical.ohms_law", "electrical.power", "electrical.kirchhoff_voltage_loop",
                          "electrical.rc_time_constant"}
        assert all(code[n] == data[n] for n in shared), (side, {n: (code[n], data[n]) for n in shared})


def test_a_new_check_ships_as_data_and_runs_with_no_code_behind_it():
    _write_specs(dict(ELECTRICAL, status="admitted"))
    packet = {"ELEC_VERIFY": {"vin_V": 12.0, "r1_ohm": 1000, "r2_ohm": 2000, "claimed_vout_V": 8.0}}
    res = V.run_for_domain("electrical", packet)                     # through the real router
    names = {r.name: r for r in res}
    assert names["electrical.voltage_divider"].status == "CONFIRMED" and names["electrical.voltage_divider"].data["spec"] is True
    packet["ELEC_VERIFY"]["claimed_vout_V"] = 4.0
    res = V.run_for_domain("electrical", packet)
    assert {r.name: r.status for r in res}["electrical.voltage_divider"] == "MISMATCH"
    # a brand-new domain with no module at all is served by its spec alone
    new = {"id": "spec_hydraulics", "domain": "hydraulics_test", "packet_key": "HYD_VERIFY", "status": "admitted",
           "checks": [{"check": "pascal", "law": "F2 = F1 · A2 / A1", "inputs": {"F1": "f1_N", "A1": "a1_m2", "A2": "a2_m2"},
                       "claimed": "claimed_f2_N", "compute": "F1 * A2 / A1",
                       "goldens": {"true": {"f1_N": 10, "a1_m2": 0.01, "a2_m2": 0.1, "claimed_f2_N": 100},
                                   "false": {"f1_N": 10, "a1_m2": 0.01, "a2_m2": 0.1, "claimed_f2_N": 50}}}]}
    _write_specs(dict(ELECTRICAL, status="admitted"), new)
    res = V.run_for_domain("hydraulics_test", {"HYD_VERIFY": {"f1_N": 10, "a1_m2": 0.01, "a2_m2": 0.1, "claimed_f2_N": 100}})
    assert [r.status for r in res] == ["CONFIRMED"] and res[0].name == "hydraulics_test.pascal"


def test_a_spec_never_contradicts_code_and_a_failing_spec_is_refused_at_load():
    # shadow: the spec's ohms_law would say CONFIRMED where the code says CONFIRMED — only one result appears
    _write_specs(dict(ELECTRICAL, status="admitted"))
    res = V.run_for_domain("electrical", {"ELEC_VERIFY": {"voltage_V": 12.0, "current_A": 0.5, "resistance_ohm": 24.0}})
    assert [r.name for r in res].count("electrical.ohms_law") == 1 and not res[0].data.get("spec")
    # a spec whose goldens do not hold does not run — and says why
    broken = json.loads(json.dumps(ELECTRICAL))
    broken["id"] = "spec_broken"
    broken["checks"][0]["compute"] = "I * R * 2"
    _write_specs(dict(broken, status="admitted"))
    lo = S.load(TMP, force=True)
    assert lo["specs"] == [] and lo["refused"][0]["id"] == "spec_broken" and "true golden did not CONFIRM" in lo["refused"][0]["why"]
    # held (not admitted) specs are listed, never run
    _write_specs(dict(ELECTRICAL, status="public_review"))
    lo = S.load(TMP, force=True)
    assert lo["specs"] == [] and lo["held"][0]["id"] == "spec_electrical"
    assert S.run_for_domain("electrical", {"ELEC_VERIFY": {"vin_V": 12.0, "r1_ohm": 1, "r2_ohm": 1, "claimed_vout_V": 6}}, data_dir=TMP) == []
    # malformed shapes are named
    assert any("not inputs" in w for w in S.validate({"id": "x", "domain": "d", "packet_key": "K", "checks": [
        {"check": "c", "inputs": {"a": "a_key"}, "claimed": "c_key", "compute": "a * b", "goldens": {"true": {}, "false": {}}}]}))


def test_admit_seals_and_the_catalog_route_serves_the_data():
    # admit without the CAS seal here (cas.store mints into the live corpus — a scratch keeping is not one)
    r = S.admit(dict(ELECTRICAL), data_dir=TMP, seal=False)
    assert r["ok"] and r["checks"] == 5
    cat = S.catalog(TMP)
    assert cat["count"] == 5 and cat["domains"] == ["electrical"] and cat["checks"][4]["check"] == "voltage_divider"
    st, body = api.dispatch("GET", "/specs", {}, None, EngineConfig())[:2]
    assert st == 200 and body["count"] == 5 and body["file"] == "verifier_specs.jsonl"
    st, body = api.dispatch("GET", "/capabilities", {}, None, EngineConfig())[:2]
    assert st == 200 and body["verifiers"]["spec_checks"]["count"] == 5
