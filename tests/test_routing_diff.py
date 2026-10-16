"""The routing-basis diff (issue #31) — tools/routing_diff.py.

2026-10-16: a new verifier's docstring said "prime implicants"; `prime` was credited to a third domain,
decorrelation shrank number_theory below the 2.5 floor, and "is 17 prime" went from DECIDING to ASKING —
caught only by one test pin. The tool compares the phrase->domain index of two checkouts and FAILS when a
golden query's decision flips. Pinned here on two small synthetic snapshots shaped like that incident, on
the CLI exit codes, and on a live snapshot of this checkout (which must compare to itself as "no changes").
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import routing_diff  # noqa: E402

TOOL = ROOT / "tools" / "routing_diff.py"


def _g(decision, top, confidence):
    r = {"decision": decision, "top": top, "confidence": confidence, "ask": decision is None, "crisis": False}
    return {"secular": dict(r), "witness": dict(r)}


BASE = {
    "meta": {"domains": 3, "phrases": 3, "goldens": 2},
    "index": {"prime": {"number_theory": 2.69, "elliptic_curves": 0.81},
              "odds": {"probability": 3.0},
              "joist": {"construction": 3.0}},
    "goldens": {"is 17 prime": _g("number_theory", "number_theory", 0.92),
                "what are the odds of rolling two sixes": _g("probability", "probability", 1.0)},
}
# the incident, in miniature: `prime` gains formal_logic and number_theory's share shrinks; a phrase
# appears, a phrase disappears; "is 17 prime" no longer decides
HEAD = json.loads(json.dumps(BASE))
HEAD["index"]["prime"] = {"number_theory": 2.42, "elliptic_curves": 0.73, "formal_logic": 0.73}
HEAD["index"]["implicants"] = {"formal_logic": 1.03}
del HEAD["index"]["joist"]
HEAD["goldens"]["is 17 prime"] = _g(None, "number_theory", 0.55)


def test_compare_reports_domain_set_change_weight_delta_added_removed_and_the_flip():
    lines, flips = routing_diff.compare(BASE, HEAD)
    text = "\n".join(lines)
    assert flips == 2                                   # one query, both surfaces
    assert "FLIP `is 17 prime` [secular]: decision number_theory -> None" in text
    assert "`prime`: ['elliptic_curves', 'number_theory'] -> ['elliptic_curves', 'formal_logic', 'number_theory']" in text
    assert "`prime` / number_theory: 2.690 -> 2.420 (-0.270)" in text
    assert "`implicants` -> {formal_logic: 1.030}" in text
    assert "`joist` was {construction: 3.000}" in text
    assert "FAIL: 2 golden decision(s) flipped" in text
    assert "rolling two sixes" not in text              # the untouched golden is not mentioned anywhere


def test_identical_snapshots_report_nothing():
    lines, flips = routing_diff.compare(BASE, BASE)
    assert flips == 0
    assert any("no routing changes" in ln for ln in lines)
    assert not any(ln.startswith("###") for ln in lines)


def test_a_top_domain_change_without_a_decision_change_is_reported_but_is_not_a_flip():
    head = json.loads(json.dumps(BASE))
    head["goldens"]["is 17 prime"] = _g("number_theory", "elliptic_curves", 0.92)   # contrived, but the shape
    lines, flips = routing_diff.compare(BASE, head)
    assert flips == 0
    assert any(ln.startswith("- top `is 17 prime` [secular]: number_theory -> elliptic_curves") for ln in lines)


def _cli(*args):
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def test_cli_exit_codes(tmp_path):
    base, head = tmp_path / "base.json", tmp_path / "head.json"
    base.write_text(json.dumps(BASE), encoding="utf-8")
    head.write_text(json.dumps(HEAD), encoding="utf-8")
    r = _cli("compare", str(base), str(head), "--fail-on-flip")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "FLIP `is 17 prime`" in r.stdout
    r = _cli("compare", str(base), str(head))                   # without the flag: report only
    assert r.returncode == 0 and "FLIP `is 17 prime`" in r.stdout
    r = _cli("compare", str(base), str(base), "--fail-on-flip")
    assert r.returncode == 0 and "no routing changes" in r.stdout


def test_golden_queries_are_harvested_from_the_resolver_pins():
    qs = routing_diff.golden_queries(ROOT)
    assert "is 17 prime" in qs and "is 17 a prime number" in qs        # the incident's query, both forms
    assert "what does john 3:16 say about the world" in qs             # a witness-surface pin
    assert qs == sorted(set(qs))                                       # deterministic, no duplicates


def test_live_snapshot_of_this_checkout_compares_to_itself_as_no_changes():
    snap = routing_diff.build_snapshot(ROOT)
    assert snap["meta"]["phrases"] > 1000 and snap["meta"]["domains"] >= 60
    assert snap["goldens"]["is 17 prime"]["secular"]["decision"] == "number_theory"
    assert "prime" in snap["index"] and "number_theory" in snap["index"]["prime"]
    lines, flips = routing_diff.compare(snap, json.loads(json.dumps(snap)))
    assert flips == 0 and any("no routing changes" in ln for ln in lines)
