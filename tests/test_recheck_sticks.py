"""THE STICK RE-CHECK (2026-11-25): every sealed mark re-read - present, unaltered, HOLDS, and the same seal the
current catalog mints. These pin each state on a scratch keeping: MATCHES, MISSING, TAMPERED, NOT_HOLDS, SAME,
DRIFTED and not_in_catalog, and that the tool writes nothing to the keeping."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from concordance import cas, tickstick as TS  # noqa: E402
import recheck_sticks as R  # noqa: E402  (main; recheck/holds re-exported)


def _record(keep: Path, n: int, verdict: str = "HOLDS") -> str:
    rec = {"schema_version": "2.0", "overall": "PASS" if verdict == "HOLDS" else "FAIL", "verdict": verdict,
           "claim": f"test {n}", "n": n}
    h = cas.content_hash_of(rec)
    p = cas._record_path(keep / "cas", h)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, sort_keys=True), encoding="utf-8")
    return h


def _keeping():
    keep = Path(tempfile.mkdtemp(prefix="nh-recheck-"))
    sid = TS.create("A test question for the re-check", data_dir=keep)["id"]
    good = _record(keep, 1)
    later = _record(keep, 2)
    bad = _record(keep, 3)
    assert TS.tick(sid, "witness", "the first sealed mark", seal=good, data_dir=keep)["ok"]
    assert TS.tick(sid, "witness", "the second sealed mark", seal=later, data_dir=keep)["ok"]
    assert TS.tick(sid, "witness", "the third sealed mark", seal=bad, data_dir=keep)["ok"]
    return keep, sid, good, later, bad


def _golden(dirpath: Path, sid: str, marks):
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "entry.json").write_text(json.dumps({"entry": "entry", "rc": 0, "seals": {}, "sticks": {
        sid: {"ticks": [{"kind": k, "claim": c, "seal": s} for k, c, s in marks]}}}), encoding="utf-8")


def test_every_state_is_named_and_nothing_is_written():
    keep, sid, good, later, bad = _keeping()
    # TAMPERED: the third record's bytes change after it was sealed
    p = cas._record_path(keep / "cas", bad)
    rec = json.loads(p.read_text(encoding="utf-8"))
    rec["n"] = 99
    p.write_text(json.dumps(rec, sort_keys=True), encoding="utf-8")
    # MISSING: the second record is gone
    cas._record_path(keep / "cas", later).unlink()
    gdir = keep / "golden"
    _golden(gdir, sid, [("witness", "the first sealed mark", good),           # SAME
                        ("witness", "the second sealed mark", "0" * 64)])     # DRIFTED (and MISSING)
    before = sorted(str(x.relative_to(keep)) for x in keep.rglob("*") if x.is_file())
    r = R.recheck(keep, gdir)
    after = sorted(str(x.relative_to(keep)) for x in keep.rglob("*") if x.is_file())
    assert before == after                                                      # read-only
    assert r["sealed_marks"] == 3 and r["integrity"] == {"MATCHES": 1, "MISSING": 1, "TAMPERED": 1}
    assert r["now"] == {"SAME": 1, "DRIFTED": 1, "not_in_catalog": 1} and r["ok"] is False
    states = {(x["integrity"], x["now"]) for x in r["problems"]}
    assert states == {("MISSING", "DRIFTED"), ("TAMPERED", "not_in_catalog")} and r["failing"] == 2


def test_drift_alone_is_reported_and_never_fails_the_run():
    keep, sid, good, later, bad = _keeping()
    gdir = keep / "golden"
    _golden(gdir, sid, [("witness", "the first sealed mark", "1" * 64)])        # the code mints another seal today
    r = R.recheck(keep, gdir)
    assert r["ok"] and r["failing"] == 0 and r["now"]["DRIFTED"] == 1
    assert r["drift"]["marks"] == 1 and r["drift"]["minted_from"] and "still HOLDS" in r["drift"]["means"]
    assert R.main(["--data", str(keep), "--golden", str(gdir)]) == 0


def test_a_clean_keeping_is_ok_and_a_failed_record_is_not_holds():
    keep, sid, good, later, bad = _keeping()
    gdir = keep / "golden"
    _golden(gdir, sid, [("witness", "the first sealed mark", good)])
    r = R.recheck(keep, gdir)
    assert r["ok"] and r["integrity"] == {"MATCHES": 3} and r["problems"] == []
    assert R.holds({"overall": "FAIL", "verdict": "BROKEN"}) is False
    assert R.holds({"gate_results": [{"details": {"verdict": "HOLDS"}}]}) is True


def test_the_cli_exits_by_the_report_and_writes_only_its_json(tmp_path):
    keep, sid, good, later, bad = _keeping()
    out = tmp_path / "report.json"
    assert R.main(["--data", str(keep), "--golden", str(keep / "nogolden"), "--json", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["sealed_marks"] == 3
    cas._record_path(keep / "cas", good).unlink()
    assert R.main(["--data", str(keep), "--golden", str(keep / "nogolden")]) == 1


def test_get_sticks_recheck_serves_the_report_and_only_failing_problems(monkeypatch):
    keep, sid, good, later, bad = _keeping()
    gdir = keep / "golden"
    _golden(gdir, sid, [("witness", "the first sealed mark", "1" * 64)])          # drift only
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(keep))
    from concordance import stick_recheck as SR
    from concordance.engine import EngineConfig
    from concordance.web import api
    monkeypatch.setattr(SR, "GOLDEN", gdir)
    monkeypatch.setattr(SR.recheck, "__defaults__", (None, gdir))
    st, body = api.dispatch("GET", "/sticks/recheck", {}, None, EngineConfig())[:2]
    assert st == 200 and body["ok"] is True and body["failing"] == 0 and body["sealed_marks"] == 3
    assert body["now"]["DRIFTED"] == 1 and body["problems"] == []              # drift is counted, not listed
    cas._record_path(keep / "cas", good).unlink()
    st, body = api.dispatch("GET", "/sticks/recheck", {}, None, EngineConfig())[:2]
    assert body["ok"] is False and body["failing"] == 1 and body["problems"][0]["integrity"] == "MISSING"
