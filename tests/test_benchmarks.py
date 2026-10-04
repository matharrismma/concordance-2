"""THE ENGINE MEASURES ITSELF IN PUBLIC (Gen 3 · 7, 2026-10-04). The standing benchmarks run on a scratch
keeping: a golden pair is judged the way the gate judges it (seal the truth, refuse the falsehood, never confirm
a falsehood), a regression against the previous run is named, --gate exits 1, and GET /benchmarks serves the
file with its age — a number measured, never typed in."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="nh-bench-"))
os.environ["CONCORDANCE_DATA_DIR"] = str(TMP)
os.environ["ASSAY_DIR"] = str(TMP / "assay")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import benchmarks as BM  # noqa: E402
from concordance.engine import EngineConfig  # noqa: E402
from concordance.web import api  # noqa: E402

GOLDENS = {
    "number_theory": {"packet_key": "NUM_VERIFY",
                      "true": {"n_prime": 17, "claimed_prime": True},
                      "false": {"n_prime": 17, "claimed_prime": False}},
    "electrical": {"packet_key": "ELEC_VERIFY",
                   "true": {"voltage_V": 12.0, "current_A": 0.5, "resistance_ohm": 24.0},
                   "false": {"voltage_V": 13.0, "current_A": 0.5, "resistance_ohm": 24.0}},
}


def _write_goldens(g):
    (TMP / "domain_goldens.json").write_text(json.dumps(g), encoding="utf-8")


def test_a_golden_pair_is_judged_as_the_gate_judges_it():
    d = BM.bench_domains(GOLDENS)
    assert d["number_theory"]["ok"] and d["electrical"]["ok"]
    assert d["electrical"]["sealed_truth"] and d["electrical"]["refused_falsehood"] and not d["electrical"]["false_positive"]
    # a pair whose falsehood the engine would confirm is a FALSE POSITIVE, named
    bad = {"electrical": {"packet_key": "ELEC_VERIFY",
                          "true": {"voltage_V": 12.0, "current_A": 0.5, "resistance_ohm": 24.0},
                          "false": {"voltage_V": 12.0, "current_A": 0.5, "resistance_ohm": 24.0}}}   # "false" is true
    d = BM.bench_domains(bad)
    assert d["electrical"]["false_positive"] and not d["electrical"]["ok"]


def test_the_run_writes_the_file_and_names_a_regression_against_the_previous_run():
    _write_goldens(GOLDENS)
    s = BM.run()
    assert s["domains"]["ok"] == 2 and s["regressed"] is False and (TMP / "benchmarks.json").exists()
    assert s["moat"]["false_positives"] == 0 and s["moat"]["cases"] > 20
    # the next night a domain breaks: the previous run makes it a regression
    broken = json.loads(json.dumps(GOLDENS))
    broken["electrical"]["true"]["voltage_V"] = 99.0
    _write_goldens(broken)
    s2 = BM.run()
    assert s2["domains"]["ok"] == 1 and s2["regressions"] == ["electrical"] and s2["regressed"] is True
    assert s2["previous"]["domains_ok"] == 2 and (TMP / "benchmarks.prev.json").exists()
    assert BM.main(["--gate"]) == 1 and BM.main([]) == 0


def test_the_route_serves_the_measured_file_with_its_age():
    _write_goldens(GOLDENS)
    BM.run()
    st, body = api.dispatch("GET", "/benchmarks", {}, None, EngineConfig())[:2]
    assert st == 200 and body["domains"]["ok"] == 2 and body["stale"] is False and body["age_hours"] < 1
    # an old file says so
    p = TMP / "benchmarks.json"
    old = json.loads(p.read_text(encoding="utf-8"))
    old["generated_at"] = "2026-01-01T00:00:00+00:00"
    p.write_text(json.dumps(old), encoding="utf-8")
    st, body = api.dispatch("GET", "/benchmarks", {}, None, EngineConfig())[:2]
    assert st == 200 and body["stale"] is True
    p.unlink()
    st, body = api.dispatch("GET", "/benchmarks", {}, None, EngineConfig())[:2]
    assert st == 404 and "never run" in body["error"]
