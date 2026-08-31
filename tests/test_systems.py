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
