"""The airlock — remove context, operate on the clean claim only, reapply context (2026-09-25).

Matt's ask: "a clean airlock method of removing context, discerning and then reapplying context." The
guarantee is STRUCTURAL: `operate` is handed only the de-identified, necessity-only skeleton — never the
PII map or the framing — so it cannot leak what it never sees. A skeleton that would leak is quarantined
(operate does not run). A string result has PII reapplied on the way out; the framing is held local.
Built on the same strip → hold → reattach floor as context.run (its verify-shaped specialization).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import context  # noqa: E402


def test_operate_sees_only_the_clean_skeleton():
    """The framing and the PII never enter the clean zone — operate sees a de-identified skeleton only."""
    seen = {}

    def op(clean):
        seen["arg"] = clean
        return clean

    run = context.airlock("my mom said email me at a@b.com and 2 plus 2 is 4", op, minimal=True)
    assert run.ok and not run.leaked
    assert "mom" not in seen["arg"]          # attribution framing held home
    assert "a@b.com" not in seen["arg"]      # PII placeheld, never the raw value
    assert "[EMAIL_1]" in seen["arg"]        # …it travels only as a typed placeholder


def test_string_result_has_pii_reapplied():
    run = context.airlock("email me at a@b.com", lambda clean: "reply to " + clean, minimal=False)
    assert run.ok
    assert "a@b.com" in run.result           # reapplied at the out-door for the caller
    assert "[EMAIL_1]" not in run.result


def test_framing_is_held_local_not_sent():
    seen = {}
    run = context.airlock("my mom said 2 plus 2 is 4",
                          lambda c: seen.setdefault("c", c) or c, minimal=True)
    assert "mom" in run.framing               # the framing is returned to the caller…
    assert "mom" not in seen["c"]             # …but never handed to operate


def test_round_trip_is_exact():
    text = "my mom said email me at a@b.com about 2 plus 2 is 4"
    run = context.airlock(text, lambda c: c, minimal=True)
    assert run.stripped.reattach() == text    # the floor: strip → reattach is byte-exact


def test_leaking_skeleton_is_quarantined(monkeypatch):
    """Fail-closed: if the strip would let PII through, operate NEVER runs."""
    called = {"n": 0}

    def op(clean):
        called["n"] += 1
        return clean

    monkeypatch.setattr(context, "leaks", lambda s: True)   # force the leak check to trip
    run = context.airlock("2 plus 2 is 4", op, minimal=False)
    assert run.leaked and not run.ok
    assert run.checked is None
    assert called["n"] == 0                                 # operate did not run on leaking input


def test_airlock_wraps_discern():
    """The whole cycle over discern: context removed → discerned (with chaining, increment 2) → the
    proposal comes back, and the framing never reached the clean zone."""
    from concordance import discern as D
    seen = {}

    def op(clean):
        seen["c"] = clean
        return D.discern(clean)

    run = context.airlock("my mom said a rectangle 4 by 6 has area 24, so 24 x 2 = 48", op, minimal=True)
    assert run.ok
    assert "mom" not in seen["c"]                           # removed before discerning
    assert isinstance(run.result, dict) and run.result.get("kind") == "claim"
    # the chain survived inside the clean zone (increment 2): the claims carry a `uses` edge
    assert any(c.get("uses") for c in (run.result.get("claims") or []))


def test_non_string_result_passes_through_untouched():
    marker = {"kind": "proposal", "n": 3}
    run = context.airlock("2 plus 2 is 4", lambda c: marker, minimal=False)
    assert run.result is marker               # a structured result is not string-revealed


if __name__ == "__main__":
    import pytest
    raise SystemExit(int(pytest.main([__file__, "-q"])))
