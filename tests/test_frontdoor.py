"""The front-door benchmark (2026-10-07): sentences through the real funnel, with a ratchet.

Pins the judge (true CONFIRMED = correct; false MISMATCHED = correct; a false claim CONFIRMED = a false
positive; a true claim MISMATCHED = a false negative; unreached = an honest miss), the floor (once a claim
is reached-and-correct it must stay so), and that the shipped claim file produces zero false positives.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import frontdoor as F  # noqa: E402


def test_judge_classifies_outcomes():
    t = {"id": "t", "truth": True}
    f = {"id": "f", "truth": False}
    ok = {"claims_found": 1, "results": [{"status": "CONFIRMED", "extractor": "x", "domain": "d", "detail": ""}]}
    bad = {"claims_found": 1, "results": [{"status": "MISMATCH", "extractor": "x", "domain": "d", "detail": ""}]}
    miss = {"claims_found": 0, "results": []}
    assert F.judge(t, ok)["correct"] and not F.judge(t, ok)["false_negative"]
    assert F.judge(t, bad)["false_negative"] and not F.judge(t, bad)["correct"]
    assert F.judge(f, bad)["correct"] and not F.judge(f, bad)["false_positive"]
    assert F.judge(f, ok)["false_positive"] and not F.judge(f, ok)["correct"]
    m = F.judge(t, miss)
    assert not m["reached"] and not m["correct"] and not m["false_positive"] and not m["found"]
    # the FOUND column (2026-10-07): a sourced-table fact for an unreached claim — never reach, never the floor
    agree, disagree = {"field": "half_life", "agrees": True}, {"field": "half_life", "agrees": False}
    ft = F.judge(t, miss, agree)
    assert ft["found"] and ft["found_correct"] and not ft["reached"] and not ft["correct"]
    ffp = F.judge(f, miss, agree)
    assert ffp["found_false_positive"] and not ffp["found_correct"] and not ffp["false_positive"]
    fw = F.judge(t, miss, disagree)
    assert fw["found_wrong"] and not fw["found_correct"]
    assert F.judge(f, miss, disagree)["found_correct"]
    assert not F.judge(t, miss, {"field": "half_life", "agrees": None})["found_correct"]   # nothing claimed, nothing judged
    assert not F.judge(t, ok, agree)["found"]                 # reached wins; the fact column is for the unreached only


def test_ratchet_names_a_regression(tmp_path):
    claims = {"claims": [{"id": "sum_t", "truth": True, "text": "2 + 2 = 4"},
                         {"id": "sum_f", "truth": False, "text": "2 + 2 = 5"}]}
    (tmp_path / "frontdoor_claims.json").write_text(json.dumps(claims), encoding="utf-8")
    s1 = F.run(data_dir=tmp_path)
    assert s1["correct"] == 2 and s1["false_positives"] == 0 and not s1["regressed"]
    assert set(json.loads((tmp_path / "frontdoor.floor.json").read_text())["claims"]) == {"sum_t", "sum_f"}
    # break a floor claim: swap its text for one the funnel cannot reach -> the floor names it
    claims["claims"][0]["text"] = "the weather was pleasant"
    (tmp_path / "frontdoor_claims.json").write_text(json.dumps(claims), encoding="utf-8")
    s2 = F.run(data_dir=tmp_path)
    assert s2["regressed"] and "sum_t" in s2["regressions"]


def test_shipped_claims_have_no_false_positives(tmp_path):
    # the suite points CONCORDANCE_DATA_DIR at a scratch dir, so name the shipped claim file explicitly
    s = F.run(dry_run=True, data_dir=tmp_path, claims_path=ROOT / "data" / "frontdoor_claims.json")
    assert s["claims"] >= 39
    assert s["false_positives"] == 0, [r for r in s["rows"] if r["false_positive"]]
    assert s["false_negatives"] == [], s["false_negatives"]
    assert s["reached"] >= 31, s["missed"]          # 27 (the 2026-10-07 fix) + the four square roots
    # the found column: the lookup facts (boiling points, half-lives) — agreeing with truth, refusing the twin
    assert s["found"] >= 8 and s["found_correct"] == s["found"], [r for r in s["rows"] if r["found"] and not r["found_correct"]]
    assert s["found_false_positives"] == 0 and s["found_wrong"] == []
    assert s["missed"] == [], s["missed"]           # every shipped claim is reached or found; a new miss is named here
