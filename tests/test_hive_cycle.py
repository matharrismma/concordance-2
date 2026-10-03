"""THE HIVE's apply flag must reach the workers that write (2026-10-03): the first timer-run turn printed
"Nothing was written. Re-run with --apply" from the shepherd and "--check: nothing written" from grow — the cycle
was in apply mode, the workers were not. A dry run still runs nothing."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from tools import hive_cycle as hc  # noqa: E402


def _step(key):
    return next(s for s in hc.STEPS if s["key"] == key)


def test_the_writing_workers_carry_their_apply_form():
    assert _step("shepherd")["apply_argv"][-1] == "--apply" and _step("grow")["apply_argv"][-1] == "--apply"
    assert "--apply" not in _step("shepherd")["argv"] and "--apply" not in _step("grow")["argv"]
    for key in ("watch", "connections", "theorymap"):
        assert "apply_argv" not in _step(key)                    # they never write; nothing to pass


def test_apply_mode_runs_the_apply_form_and_dry_run_runs_nothing(monkeypatch):
    seen = []

    class _Proc:
        returncode = 0
        stdout = "ok\n"
        stderr = ""

    monkeypatch.setattr(hc.subprocess, "run", lambda argv, **kw: seen.append(argv) or _Proc())
    monkeypatch.setattr(hc.spend_guard, "can_spend", lambda est: True)
    monkeypatch.setattr(hc.spend_guard, "record", lambda *a, **k: None)
    r = hc.run_step(_step("grow"), apply_it=True)
    assert r["status"] in ("ok", "done", "success") or r.get("rc") == 0
    assert seen and seen[-1][-1] == "--apply"
    seen.clear()
    r = hc.run_step(_step("grow"), apply_it=False)
    assert r["status"] == "planned" and seen == []
