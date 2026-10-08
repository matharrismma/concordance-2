"""The systems handicap — a grounded operational number per subsystem, and one for the course.
Pure (no corpus): disk stats + import resolution. Proves the number is REAL — it moves when a test or
an SOP appears, and every module resolves (nothing is silently 'out')."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import systems  # noqa: E402


def test_report_shape_and_course_handicap():
    r = systems.report()
    assert 0 <= r["course_handicap"] <= 10
    assert r["counts"]["total"] == len(systems.SUBSYSTEMS) == len(r["subsystems"])
    assert r["counts"]["connected"] + r["counts"]["degraded"] + r["counts"]["out"] == r["counts"]["total"]
    # sorted worst-first so the dashboard surfaces what needs attention
    hs = [s["handicap"] for s in r["subsystems"]]
    assert hs == sorted(hs, reverse=True)


def test_no_subsystem_is_secretly_out():
    """Every listed module must RESOLVE on the import path — an 'out' here means a real broken wire,
    which is exactly what the dashboard exists to surface. On a healthy tree, zero are out."""
    r = systems.report()
    out = [s["name"] + ": " + s["live"]["detail"] for s in r["subsystems"] if s["live"]["status"] == "out"]
    assert not out, f"subsystems reporting OUT (unresolved modules): {out}"


def test_handicap_moves_when_an_sop_lands():
    """The number must be LIVE, not hand-set: writing an SOP drops that subsystem's handicap by 2."""
    sub = systems.SUBSYSTEMS[0]
    before = systems._one(sub)["handicap"]
    sop = systems._SOP_DIR / f"{sub['slug']}.md"
    created = False
    try:
        if not sop.exists():
            sop.parent.mkdir(parents=True, exist_ok=True)
            sop.write_text("# temp SOP for parity test\n", encoding="utf-8")
            created = True
            assert systems._one(sub)["handicap"] == before - 2
    finally:
        if created:
            sop.unlink()


def test_endpoint_serves_the_report():
    from concordance.web.api import dispatch
    from concordance.config import EngineConfig
    st, payload = dispatch("GET", "/systems", {}, None, EngineConfig("secular"))
    assert st == 200
    assert payload["course_handicap"] == systems.report()["course_handicap"]
    assert payload["subsystems"] and "handicap" in payload["subsystems"][0]


# ---- THE LAUNCH ROLL-CALL (2026-10-08): every subsystem checks in with speed and memory ----

def test_measure_times_a_step_and_never_raises():
    ok = systems.measure("noop", lambda: None)
    assert ok["ok"] and ok["ms"] >= 0 and ok["error"] is None
    bad = systems.measure("boom", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    assert not bad["ok"] and "RuntimeError" in bad["error"] and bad["ms"] >= 0


def test_checkin_every_subsystem_reports(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    out = systems.checkin(extra=[systems.measure("fake singleton", lambda: None)], write=True, log=False)
    assert out["total"] == len(systems.SUBSYSTEMS) == len(out["subsystems"])
    for r in out["subsystems"]:
        assert r["status"] in ("ready", "degraded", "absent"), r
        assert r["ms"] >= 0
        assert r["rss_kb"] is None or r["rss_kb"] >= 0
        assert set(r["loaded_now"]) | set(r["preloaded"]) | {m.split(":")[0] for m in r["missing"]} == set(
            next(s["modules"] for s in systems.SUBSYSTEMS if s["slug"] == r["slug"]))
    assert out["absent"] == [], out["absent"]            # on a healthy tree nothing is absent
    assert out["singletons"][0]["label"] == "fake singleton"
    assert all("pulls_ms" in e for e in out["edges"])     # every edge priced by what it pulls in
    assert (tmp_path / "boot_checkin.json").exists()
    assert systems.last_checkin()["at"] == out["at"]     # the report reads what the boot wrote
    assert systems.report()["boot"]["total"] == out["total"]


def test_rss_reading_is_a_number_or_honestly_none():
    v = systems.rss_kb()
    assert v is None or (isinstance(v, int) and v > 0)


def test_isolated_checkin_tool_measures_a_piece_alone():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import checkin as C
    out = C.run(only=["crisis"], singletons=False, timeout=120, write=False)
    assert out["rows"] and out["rows"][0]["slug"] == "crisis"
    r = out["rows"][0]
    assert r.get("error") is None, r
    assert r["ms"] >= 0 and r["loaded"] >= 1
    assert "baseline" in out and out["baseline"].get("base_ms", 0) >= 0
    assert C.table(out).splitlines()[0].startswith("baseline")
