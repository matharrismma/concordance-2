"""The airlock — the chamber that works something without absorbing it. Two sides, one principle.

INPUT/FILE side — a dragged file becomes cards + a map, and the file is kicked back out: cards map back
to the USER's file (their link is the waybill), are PRIVATE and never merged into core, and ingest
persists NOTHING to disk.

CONTEXT side (through) — remove context, operate on ONLY the de-identified skeleton, reapply. The
guarantee is structural: operate never receives the PII map or the framing, so it cannot leak what it
never sees; a skeleton that would leak is quarantined; a string result has PII reapplied on the way out.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance import airlock, context  # noqa: E402

_TEXT = ("# Chapter One\n\nThe quick brown fox jumps over the lazy dog; faith and grace abound in the "
         "morning light.\n\n# Chapter Two\n\nAnother section, on wisdom and knowledge and the fear of "
         "the Lord, which is the beginning of understanding.\n")


# ── the input/file airlock: ingest ──────────────────────────────────────────────────────────────────

def test_ingest_mints_cards_that_map_back_to_the_users_file():
    r = airlock.ingest(_TEXT, source="mybook.txt", title="My Book", link="file:///D:/mybook.txt")
    assert r["ok"] and len(r["cards"]) >= 1
    c = r["cards"][0]
    assert c["shelf"] == "dropbox" and c["visibility"] == "private" and c["author"] == "user"
    assert c["source"]["url"] == "file:///D:/mybook.txt"          # the waybill back to their file
    assert c["extra"]["carried_by_user"] is True and c["generated"] is False
    assert r["map"]["sections"] == len(r["cards"]) and r["map"]["outline"] and r["map"]["top_terms"]
    assert "kept nothing" in r["note"].lower()


def test_empty_file_is_refused():
    assert airlock.ingest("   ")["ok"] is False


def test_ingest_persists_nothing_to_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    airlock.ingest(_TEXT, source="x.txt")
    assert not any(tmp_path.iterdir())                           # nothing deposited — the file was ejected


# ── the context airlock: through ─────────────────────────────────────────────────────────────────────

def test_operate_sees_only_the_clean_skeleton():
    """The framing and the PII never enter the clean zone — operate sees a de-identified skeleton only."""
    seen = {}

    def op(clean):
        seen["arg"] = clean
        return clean

    run = airlock.through("my mom said email me at a@b.com and 2 plus 2 is 4", op, minimal=True)
    assert run.ok and not run.leaked
    assert "mom" not in seen["arg"]          # attribution framing held home
    assert "a@b.com" not in seen["arg"]      # PII placeheld, never the raw value
    assert "[EMAIL_1]" in seen["arg"]        # …it travels only as a typed placeholder


def test_string_result_has_pii_reapplied():
    run = airlock.through("email me at a@b.com", lambda clean: "reply to " + clean, minimal=False)
    assert run.ok
    assert "a@b.com" in run.result           # reapplied at the out-door for the caller
    assert "[EMAIL_1]" not in run.result


def test_framing_is_held_local_not_sent():
    seen = {}
    run = airlock.through("my mom said 2 plus 2 is 4",
                          lambda c: seen.setdefault("c", c) or c, minimal=True)
    assert "mom" in run.framing               # the framing is returned to the caller…
    assert "mom" not in seen["c"]             # …but never handed to operate


def test_round_trip_is_exact():
    text = "my mom said email me at a@b.com about 2 plus 2 is 4"
    run = airlock.through(text, lambda c: c, minimal=True)
    assert run.stripped.reattach() == text    # the floor: strip → reattach is byte-exact


def test_leaking_skeleton_is_quarantined(monkeypatch):
    """Fail-closed: if the strip would let PII through, operate NEVER runs."""
    called = {"n": 0}

    def op(clean):
        called["n"] += 1
        return clean

    monkeypatch.setattr(context, "leaks", lambda s: True)   # force the leak check to trip
    run = airlock.through("2 plus 2 is 4", op, minimal=False)
    assert run.leaked and not run.ok
    assert run.checked is None
    assert called["n"] == 0                                 # operate did not run on leaking input


def test_through_wraps_discern():
    """The whole cycle over discern: context removed → discerned (with chaining) → the proposal comes
    back, and the framing never reached the clean zone."""
    from concordance import discern as D
    seen = {}

    def op(clean):
        seen["c"] = clean
        return D.discern(clean)

    run = airlock.through("my mom said a rectangle 4 by 6 has area 24, so 24 x 2 = 48", op, minimal=True)
    assert run.ok
    assert "mom" not in seen["c"]                           # removed before discerning
    assert isinstance(run.result, dict) and run.result.get("kind") == "claim"
    # the chain survived inside the clean zone: the discerned claims carry a `uses` edge
    assert any(c.get("uses") for c in (run.result.get("claims") or []))


def test_non_string_result_passes_through_untouched():
    marker = {"kind": "proposal", "n": 3}
    run = airlock.through("2 plus 2 is 4", lambda c: marker, minimal=False)
    assert run.result is marker               # a structured result is not string-revealed


if __name__ == "__main__":
    import pytest
    raise SystemExit(int(pytest.main([__file__, "-q"])))
