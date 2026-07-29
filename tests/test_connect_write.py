"""The calendar pilot — the lock is checked before the door opens, and the write is theirs.

Matt's decision: the narrow pilot. What this file pins:

  * an UNAUTHORIZED call is refused BEFORE anything is built — and the refusal carries the
    covenant's teaching (member ≠ proxy), so an agent learns the way in instead of a wall;
  * a granted call writes a well-formed RFC 5545 event into the user's OWN .ics file, inside the
    VCALENDAR envelope, and returns a RECEIPT (uid + grant id) — covenant rule 5;
  * revoke the grant and the door is shut again — consent is live, not a one-time stamp;
  * no destination is ever guessed: an unconfigured target refuses rather than defaulting;
  * connect.py itself remains byte-for-byte read-only — the write lives in its own module, so the
    store-nothing source scan keeps its teeth.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True, scope="module")
def _isolate_data_dir():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    prior_target = os.environ.get("NH_CALENDAR_WRITE")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    for k, v in (("CONCORDANCE_DATA_DIR", prior), ("NH_CALENDAR_WRITE", prior_target)):
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _grant(verb="calendar_write"):
    from concordance import consent, identity, signing
    human = identity.create_identity()
    agent = "nh_agent_cal"
    s = consent.signable_grant(human["public_key"], agent, [verb])
    sig = signing.sign_bytes(base64.urlsafe_b64decode(s["signable"]), human["private_key"])
    r = consent.grant(s["fields"], sig)
    assert r["ok"]
    return human, agent, r["grant_id"]


def test_no_grant_no_door_and_the_refusal_teaches():
    from concordance import connect_write, identity
    human = identity.create_identity()
    r = connect_write.create_event(human["public_key"], "nh_agent_stranger",
                                   "Coffee", "2026-08-01T09:00:00")
    assert r["ok"] is False and r.get("refused") is True
    assert "member is not a proxy" in (r.get("refusal") or "")


def test_a_granted_write_lands_in_their_calendar_with_a_receipt():
    from concordance import connect_write
    human, agent, gid = _grant()
    ics = os.path.join(tempfile.mkdtemp(), "my.ics")
    r = connect_write.create_event(human["public_key"], agent, "Bible study",
                                   "2026-08-02T19:00:00", end_iso="2026-08-02T20:30:00",
                                   description="Storyboards: exile and return", target=ics)
    assert r["ok"] is True and r["target_kind"] == "file"
    assert r["grant_id"] == gid, "the receipt names the grant that authorized it"
    text = Path(ics).read_text(encoding="utf-8")
    assert text.startswith("BEGIN:VCALENDAR") and text.rstrip().endswith("END:VCALENDAR")
    assert f"UID:{r['uid']}" in text and "SUMMARY:Bible study" in text
    assert "DTSTART:20260802T190000" in text
    # and a second event nests INSIDE the same envelope, not after it
    r2 = connect_write.create_event(human["public_key"], agent, "Prayer", "2026-08-03", target=ics)
    assert r2["ok"] is True
    text2 = Path(ics).read_text(encoding="utf-8")
    assert text2.count("BEGIN:VCALENDAR") == 1 and text2.count("BEGIN:VEVENT") == 2
    assert "DTSTART;VALUE=DATE:20260803" in text2, "a date-only start is an all-day event"


def test_the_write_is_read_back_by_the_read_side():
    """The two modules meet in the user's file: what the pilot writes, connect.read_calendar
    reads — one calendar, both directions, nothing stored anywhere else."""
    from datetime import date
    from concordance import connect, connect_write
    human, agent, _ = _grant()
    ics = os.path.join(tempfile.mkdtemp(), "round.ics")
    r = connect_write.create_event(human["public_key"], agent, "Roundtrip proof",
                                   "2026-08-04", target=ics)
    assert r["ok"] is True
    events = connect.read_calendar(source=ics, on=date(2026, 8, 4))
    assert any("Roundtrip proof" in (e.get("summary") or "") for e in events), \
        "the read side must see what the consented write wrote"


def test_revocation_shuts_the_door_again():
    from concordance import connect_write, consent, signing, identity  # noqa: F401
    human, agent, gid = _grant()
    ics = os.path.join(tempfile.mkdtemp(), "rev.ics")
    assert connect_write.create_event(human["public_key"], agent, "Before", "2026-08-05",
                                      target=ics)["ok"] is True
    body = json.dumps({"revokes": gid, "grantor_pubkey": human["public_key"]},
                      sort_keys=True, separators=(",", ":")).encode()
    from concordance import signing as _s
    consent.revoke(agent, gid, human["public_key"], _s.sign_bytes(body, human["private_key"]))
    r = connect_write.create_event(human["public_key"], agent, "After", "2026-08-06", target=ics)
    assert r["ok"] is False and r.get("refused") is True, "a revoked grant opens nothing"


def test_no_destination_is_ever_guessed():
    from concordance import connect_write
    human, agent, _ = _grant()
    os.environ.pop("NH_CALENDAR_WRITE", None)
    r = connect_write.create_event(human["public_key"], agent, "Nowhere", "2026-08-07")
    assert r["ok"] is False and "never guess" in r["error"]


def test_the_read_module_stays_byte_for_byte_read_only():
    """The pilot must not have leaked a single write into connect.py — the separation IS the
    design, and test_connect's source scan must keep something real to scan."""
    src = (Path(__file__).resolve().parent.parent / "src" / "concordance" / "connect.py") \
        .read_text(encoding="utf-8")
    assert "connect_write" not in src, "the read side must not even import the write side"
    assert ".write(" not in src


if __name__ == "__main__":
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the lock held, the door opened once, and the write is theirs.")
