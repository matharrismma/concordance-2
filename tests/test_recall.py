"""THE RECALL SET (the failure report H1, 2026-10-08): per-extractor phrasing recall, ratcheted. Pins: the set is
well-formed (every family has true AND false phrasings), the tool runs dry through the real front door with ZERO
false positives, every family that the front-door benchmark already reaches is reached here too, and the one-line
summary carries the numbers the report asked for."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
TMP = Path(tempfile.mkdtemp(prefix="nh-recall-"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", str(TMP))

import recall  # noqa: E402

PHRASINGS = ROOT / "data" / "recall_phrasings.json"


def test_the_set_is_well_formed():
    d = json.loads(PHRASINGS.read_text(encoding="utf-8"))
    fams = d["families"]
    assert len(fams) >= 30
    ids = set()
    for fam, rows in fams.items():
        assert len(rows) >= 4, fam
        truths = {bool(r["truth"]) for r in rows}
        assert truths == {True, False}, f"{fam}: needs both true and false phrasings"
        for r in rows:
            assert r["id"] not in ids, r["id"]
            ids.add(r["id"])
            assert r["text"].strip() and r.get("register")


def test_recall_runs_dry_with_zero_false_positives_and_reaches_the_known_families():
    s = recall.run(dry_run=True, data_dir=TMP, phrasings_path=PHRASINGS)
    assert s["false_positives"] == 0, [r for r in s["rows"] if r["false_positive"]]
    assert s["phrasings"] >= 150 and s["families"] >= 30
    per = s["per_family"]
    # families the front-door benchmark already reaches must be reached here in at least their plain phrasing
    for fam in ("sum", "percent", "physical_constant", "unit_conversion", "molar_mass", "escape_velocity",
                "ohms_law", "kinetic_energy", "pythagorean", "sqrt", "primality", "elapsed_years"):
        assert per[fam]["reached"] >= 2, (fam, per[fam])
    # the two defects the report named by phrasing are reached now
    reached = {r["id"] for r in s["rows"] if r["reached"]}
    assert "hourly_annual_1" in reached and "percent_3" in reached
    assert 0.0 < s["recall"] <= 1.0
    assert not (TMP / "recall.json").exists()          # dry: nothing written


def test_the_ratchet_refuses_a_regression(tmp_path):
    """A phrasing once reached-and-correct that is not correct tonight is a regression; the gate exits 1."""
    d = json.loads(PHRASINGS.read_text(encoding="utf-8"))
    small = {"families": {"sum": d["families"]["sum"][:2]}}
    p = tmp_path / "recall_phrasings.json"; p.write_text(json.dumps(small), encoding="utf-8")
    s1 = recall.run(dry_run=False, data_dir=tmp_path, phrasings_path=p)
    assert not s1["regressed"] and (tmp_path / "recall.floor.json").exists()
    # the same ids, now with a wrong truth label, so the floor phrasing is "not correct": a regression
    wrong = {"families": {"sum": [{**r, "truth": not r["truth"]} for r in small["families"]["sum"]]}}
    p.write_text(json.dumps(wrong), encoding="utf-8")
    s2 = recall.run(dry_run=True, data_dir=tmp_path, phrasings_path=p)
    assert s2["regressed"] and s2["regressions"]
