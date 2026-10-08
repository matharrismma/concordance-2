"""THE RECEIVER (Matt, 2026-10-08): the engine as one complete system — every superheterodyne stage bound to the
component under its own name and to a proof read from the gate artifacts; complete only when every stage and the
whole are proven. Names stay close to current tech and to the code's own names. Pure over files."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from concordance import receiver as R


def _gates(d: Path, *, good: bool = True) -> None:
    bench = {"domains": {"count": 81, "sealed_truths": 81, "refused_falsehoods": 81, "false_positives": 0, "ok": 81, "not_ok": 0},
             "moat": {"cases": 60, "correct": 60 if good else 59, "false_positives": 0 if good else 1},
             "specs": {"checks": 5, "held": 0, "refused": []},
             "assay": {"probes": 103, "passed": 101, "failed": 2, "floor": 105, "regressed": []}}
    (d / "benchmarks.json").write_text(json.dumps(bench), encoding="utf-8")
    (d / "frontdoor.json").write_text(json.dumps({"reached": 31, "claims": 39, "correct": 31, "found": 8, "false_positives": 0, "regressed": False}), encoding="utf-8")
    rows = [{"reached": True, "verdict": "HOLDS"}, {"reached": False, "verdict": "NOTHING_TO_CHECK"}]
    (d / "recall.json").write_text(json.dumps({"reached": 303, "phrasings": 334, "families": 60, "false_positives": 0, "regressed": False,
                                               "floor": 303, "rows": rows}), encoding="utf-8")
    (d / "boot_checkin.json").write_text(json.dumps({"at": "2026-10-08T00:00:00+00:00", "ready": 15, "total": 15,
                                                     "singletons_ms": 11371.1,
                                                     "singletons": [{"label": "corpus (default_corpus)", "ms": 10016.5, "rss_kb": 1297716, "ok": True, "error": None},
                                                                    {"label": "semantic index", "ms": 900.0, "rss_kb": 40000, "ok": True, "error": None}]}),
                                         encoding="utf-8")


def test_every_stage_has_its_radio_name_its_component_and_a_proof():
    seen = set()
    for s in R.STAGES:
        assert s["stage"] and s["tech"] and s["component"] and s["modules"] and s["proof"]
        assert s["stage"] not in seen
        seen.add(s["stage"])
    assert {"antenna", "preselector", "mixer + local oscillator", "IF filter", "limiter", "discriminator", "AGC",
            "audio stage", "speaker", "squelch", "duplexer", "band switch", "power supply (cathode)"} == seen


def test_with_no_gate_artifacts_the_receiver_is_incomplete_and_says_what_is_not_yet_proven():
    d = Path(tempfile.mkdtemp(prefix="nh-rx-"))
    st = R.status(d)
    assert st["complete"] is False and st["whole"]["ok"] is False
    gated = [s for s in st["stages"] if s["proof"].startswith("gated") or s["proof"].startswith("boot")]
    assert gated and all(s["status"] == "unproven" for s in gated)
    assert "incomplete" in st["read"] and "antenna" in st["missing"]
    # the pins on disk prove the pinned stages even here (the repo's own tests)
    pinned = [s for s in st["stages"] if s["proof"].startswith("pinned")]
    assert pinned and all(s["status"] == "proven" for s in pinned)


def test_with_the_gate_artifacts_green_the_receiver_is_complete():
    d = Path(tempfile.mkdtemp(prefix="nh-rx-"))
    _gates(d)
    st = R.status(d)
    assert st["complete"] is True and st["missing"] == [] and st["proven"] == st["total"] == 13
    assert st["whole"]["ok"] is True and len(st["whole"]["gates"]) == 5
    assert "complete" in st["read"]
    by = {s["stage"]: s for s in st["stages"]}
    assert "303/334" in by["antenna"]["read"] and "60/60" in by["preselector"]["read"]
    assert "1/1 unreached" in by["squelch"]["read"]


def test_one_failing_lamp_makes_the_receiver_incomplete_and_the_whole_unproven():
    d = Path(tempfile.mkdtemp(prefix="nh-rx-"))
    _gates(d, good=False)                                   # the moat lets one false positive through
    st = R.status(d)
    assert st["complete"] is False and st["missing"] == ["preselector"]
    assert st["whole"]["ok"] is False
    assert [g for g in st["whole"]["gates"] if g["status"] == "failing"][0]["gate"] == "benchmarks — the moat"


def test_the_systems_report_carries_the_receiver():
    from concordance import systems
    r = systems.report()
    assert "receiver" in r and "complete" in r["receiver"] and isinstance(r["receiver"]["stages"], list)
