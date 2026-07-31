"""D6 — the security sweep over the surfaces built this week, as behavior.

Matt's decision D6 (2026-07-28): sweep the new surfaces (consent, report/block, study routes,
ambiguous-ref, the write-back pilot). Two real holes were found and are pinned shut here.

1. CALENDAR INJECTION (connect_write). `start_iso`/`end_iso` reached DTSTART/DTEND with no
   escaping AND no validation, and `_esc` did not escape a bare \\r. A raw line break inside a
   value ENDS the ICS content line — everything after it parses as a NEW PROPERTY. So one
   consented "create an event" could have written an ATTENDEE, an ORGANIZER, a URL, or a whole
   second VEVENT into the person's calendar. Now: timestamps are validated against the ICS
   grammar, and every newline form collapses to the escaped form.

2. UNSIGNED WITNESSES (moderation). `reporter` and `viewer` were self-asserted strings, so one
   person with three invented names could reach HOLD_AT and hold TRUE content away from public
   reads — a censorship lever inside the witness rule — and anyone could append blocks to
   ANOTHER viewer's list, silently filtering what that person sees. Deuteronomy 19:15 counts
   WITNESSES, not strings: a witness is a key that signed. Now report/block/unblock require a
   detached signature over canonical bytes, fresh, matching the request.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_data():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


# ── 1. the calendar pilot cannot be made to write anything but the event ────────────────────────

def test_calendar_values_cannot_break_out_of_their_lines():
    from concordance.connect_write import build_vevent
    ev = build_vevent("Prayer\r\nATTENDEE:mailto:victim@example.com",
                      "2026-08-01T09:00:00Z",
                      description="ok\nURL:http://evil.example/x\r\nBEGIN:VALARM")
    body = ev["vevent"]
    # The words are KEPT (an honest calendar entry still shows what was asked for); what must
    # never happen is a new LINE — that is what turns text into a property.
    props = {ln.split(":", 1)[0].split(";", 1)[0]
             for ln in body.split("\r\n") if ln and not ln.startswith(" ")}
    assert props == {"BEGIN", "END", "UID", "DTSTAMP", "DTSTART", "SUMMARY", "DESCRIPTION"}, \
        f"unexpected properties reached the event: {props}"
    lines = body.split("\r\n")
    assert sum(1 for ln in lines if ln.startswith("BEGIN:")) == 1, "no second component begins"
    assert sum(1 for ln in lines if ln.startswith("END:")) == 1, "and none ends early"
    assert "\\nATTENDEE" in body, "the break survived as ESCAPED text — words kept, break neutered"


def test_calendar_timestamps_are_validated_not_interpolated():
    from concordance.connect_write import build_vevent
    for bad in ("20260801T090000Z\r\nATTENDEE:mailto:x@y", "not-a-date", "2026-08",
                "20260801T090000Z BEGIN:VEVENT"):
        out = build_vevent("Prayer", bad)
        assert out.get("error"), f"{bad!r} must be refused, never interpolated"
    ok = build_vevent("Prayer", "2026-08-01T09:00:00Z", end_iso="2026-08-01T10:00:00Z")
    assert ok.get("vevent") and "DTSTART:20260801T090000Z" in ok["vevent"]
    allday = build_vevent("Fast", "2026-08-01")
    assert "DTSTART;VALUE=DATE:20260801" in allday["vevent"], "date-only still means all-day"


def test_a_bad_timestamp_refuses_the_whole_write():
    """The consent lock runs first; a malformed time must then stop the write outright rather
    than land a half-built event in someone's calendar."""
    from concordance import connect_write
    r = connect_write.create_event("pub", "agent", "Prayer", "not-a-date")
    assert r.get("ok") is False and ("start_iso" in (r.get("error") or "")
                                     or r.get("refused")), r


# ── 2. witnesses are keys, not strings ──────────────────────────────────────────────────────────

def _keypair():
    """(private, public) — or (None, None) where cryptography is absent, so the suite skips
    honestly on a bare box instead of passing silently."""
    from concordance import signing
    try:
        return signing.generate_keypair()
    except Exception:  # noqa: BLE001 — no cryptography on this machine
        return None, None


def _signed(action, target, priv, pub, extra=""):
    from concordance import moderation, signing
    sg = moderation.signable(action, target, pub, extra=extra)
    msg = base64.urlsafe_b64decode(sg["signable"])
    return sg["fields"], signing.sign_bytes(msg, priv)


def test_an_unsigned_report_is_refused_with_the_way_in():
    from concordance import moderation
    r = moderation.report("mesh_message", "msg1", "spam")
    assert r.get("ok") is False and "sign" in (r.get("error") or "").lower(), r
    r2 = moderation.report("mesh_message", "msg1", "spam",
                           fields={"actor": "someone", "action": "report",
                                   "target_id": "msg1", "at": 0, "extra": ""},
                           signature="not-a-real-signature")
    assert r2.get("ok") is False, "a forged signature must not pass"


def test_three_invented_names_cannot_hold_true_content():
    """The old hole, exactly: one actor, three names, no keys — the item must NOT be held."""
    from concordance import moderation
    for name in ("alice", "bob", "carol"):
        moderation.report("mesh_message", "true-thing", "harmful",
                          fields={"actor": name, "action": "report",
                                  "target_id": "true-thing", "at": 0, "extra": ""},
                          signature="x" * 40)
    st = moderation.status("mesh_message", "true-thing")
    assert st["reporters"] == 0 and not st.get("held"), \
        "unsigned claims must not reach the threshold that hides true content"


def test_three_signing_witnesses_do_hold_it():
    from concordance import moderation
    keys = [_keypair() for _ in range(3)]
    if any(p is None for p, _ in keys):
        pytest.skip("no keypair generator available in this build")
    for priv, pub in keys:
        f, sig = _signed("report", "bad-thing", priv, pub)
        r = moderation.report("mesh_message", "bad-thing", "harmful", fields=f, signature=sig)
        assert r.get("ok") is True, r
    st = moderation.status("mesh_message", "bad-thing")
    assert st["reporters"] == 3 and st["held_for_review"],         "three KEYS establish the matter (Deut 19:15)"
    # and the same witness repeating themselves stays one witness
    priv, pub = keys[0]
    f, sig = _signed("report", "bad-thing", priv, pub)
    moderation.report("mesh_message", "bad-thing", "harmful", fields=f, signature=sig)
    assert moderation.status("mesh_message", "bad-thing")["reporters"] == 3


def test_nobody_can_edit_another_persons_eyes():
    from concordance import moderation
    priv, pub = _keypair()
    if priv is None:
        pytest.skip("no keypair generator available in this build")
    # an attacker cannot add a block to this viewer's list without their key
    forged = moderation.block(blocked_handle="someone",
                              fields={"actor": pub, "action": "block",
                                      "target_id": "someone", "at": 0, "extra": ""},
                              signature="x" * 40)
    assert forged.get("ok") is False and not moderation.blocked_by(pub)
    f, sig = _signed("block", "noisy-handle", priv, pub)
    assert moderation.block(blocked_handle="noisy-handle", fields=f, signature=sig).get("ok")
    assert "noisy-handle" in moderation.blocked_by(pub)
    # ...and cannot tear it down either
    assert moderation.unblock(blocked_handle="noisy-handle",
                              fields={"actor": pub, "action": "unblock",
                                      "target_id": "noisy-handle", "at": 0, "extra": ""},
                              signature="x" * 40).get("ok") is False
    assert "noisy-handle" in moderation.blocked_by(pub), "the boundary held"
    f2, sig2 = _signed("unblock", "noisy-handle", priv, pub)
    assert moderation.unblock(blocked_handle="noisy-handle", fields=f2, signature=sig2).get("ok")
    assert "noisy-handle" not in moderation.blocked_by(pub)


def test_signed_bytes_go_stale_and_cannot_be_replayed_elsewhere():
    from concordance import moderation
    priv, pub = _keypair()
    if priv is None:
        pytest.skip("no keypair generator available in this build")
    f, sig = _signed("report", "item-a", priv, pub)
    stale = dict(f, at=f["at"] - (moderation.SIGNATURE_TTL_S + 60))
    assert moderation.report("mesh_message", "item-a", "spam",
                             fields=stale, signature=sig).get("ok") is False, "stale bytes refused"
    # a signature for item-a must not authorize a report against item-b
    assert moderation.report("mesh_message", "item-b", "spam",
                             fields=f, signature=sig).get("ok") is False, \
        "the signed bytes name their target — no cross-target replay"


# ── 3. the read surfaces keep their gate ────────────────────────────────────────────────────────

def test_the_study_routes_refuse_nobody_on_either_surface():
    """This test used to require these four to answer `gate_closed` on the secular surface.

    Matt, 2026-07-31: *"We don't hide knowledge. We aren't a secret society. Everyone is a part of
    the group. They experience what they want of it."* The back-matter tables, the Atlas, the
    quick-find index and the storyboards are knowledge; refusing them refused use. What this file
    guards is the SECURITY surface — authority, privacy, injection, traversal — and none of those
    were ever the Gate's job.
    """
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    sec = EngineConfig("secular")
    for p in ("/backmatter", "/places", "/study_find", "/narratives"):
        st, payload = dispatch("GET", p, {"q": "aaron"}, None, sec)
        assert payload.get("gate") != "closed", f"{p} refuses use, not abuse"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
