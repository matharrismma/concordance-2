"""connect.py — the pass-through to a user's own tools. Tests the iCalendar parser (the testable
core) and ENFORCES the boundary: store nothing, read-only, credential-local."""
from __future__ import annotations

import re
from datetime import date, timezone
from pathlib import Path

from concordance import connect

_SRC = (Path(__file__).resolve().parents[1] / "src" / "concordance" / "connect.py").read_text(encoding="utf-8")


def _ics(*vevents: str) -> str:
    body = "\n".join(vevents)
    return f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//test//EN\n{body}\nEND:VCALENDAR\n"


def _vevent(**props) -> str:
    # A value beginning with ';' carries iCalendar params (e.g. DTSTART;VALUE=DATE:20260726),
    # so it attaches without the ':' separator; otherwise it's NAME:VALUE.
    lines = ["BEGIN:VEVENT"]
    for k, v in props.items():
        sep = "" if v.startswith(";") else ":"
        lines.append(f"{k}{sep}{v}")
    lines.append("END:VEVENT")
    return "\n".join(lines)


# ── the boundary (load-bearing) ──

def test_store_nothing_no_writes_in_module():
    # No file writes, no disk persistence anywhere in the pass-through.
    assert not re.search(r"open\([^)]*['\"][wax]", _SRC), "connect.py must never open a file for writing"
    for banned in (".write(", "json.dump", "pickle.dump", "shelve", "sqlite3", "seal(", "add_card"):
        assert banned not in _SRC, f"connect.py must not persist ({banned})"


def test_email_is_read_only():
    # readonly select + BODY.PEEK (never marks seen); no destructive IMAP verbs.
    assert "readonly=True" in _SRC
    assert "BODY.PEEK" in _SRC
    for verb in ("STORE", "\\Deleted", ".copy(", ".store(", "expunge"):
        assert verb not in _SRC, f"connect.py email path must not mutate the mailbox ({verb})"


def test_credentials_come_from_local_env_only():
    # Config is read from os.environ, not from a request/argument coming off the wire.
    assert 'os.environ.get(_ENV["imap_password"])' in _SRC
    assert "NH_IMAP_PASSWORD" in _SRC
    # sources() reports presence only — never the secret value.
    s = connect.sources()
    assert set(s) == {"calendar", "email", "storage"}
    assert all(isinstance(v, bool) for v in s.values())


# ── the iCalendar parser ──

def test_all_day_event_on_target_date():
    ics = _ics(_vevent(SUMMARY="Sabbath rest", DTSTART=";VALUE=DATE:20260726", DTEND=";VALUE=DATE:20260727"))
    evs = connect.parse_ics(ics, on=date(2026, 7, 26))
    assert len(evs) == 1
    assert evs[0]["summary"] == "Sabbath rest"
    assert evs[0]["all_day"] is True
    assert evs[0]["start"] == "all day"


def test_event_excluded_on_other_day():
    ics = _ics(_vevent(SUMMARY="Elsewhere", DTSTART=";VALUE=DATE:20260726"))
    assert connect.parse_ics(ics, on=date(2026, 7, 27)) == []


def test_timed_event_utc_parses_and_sorts():
    ics = _ics(
        _vevent(SUMMARY="Second", DTSTART="20260726T140000Z", DTEND="20260726T150000Z"),
        _vevent(SUMMARY="First", DTSTART="20260726T090000Z", DTEND="20260726T093000Z"),
    )
    evs = connect.parse_ics(ics, on=date(2026, 7, 26), tz=timezone.utc)
    assert [e["summary"] for e in evs] == ["First", "Second"], "timed events sort by start"


def test_line_unfolding():
    folded = "BEGIN:VEVENT\nSUMMARY:A very long title that the calendar has\n  wrapped onto two lines\nDTSTART;VALUE=DATE:20260726\nEND:VEVENT"
    ics = _ics(folded)
    evs = connect.parse_ics(ics, on=date(2026, 7, 26))
    assert evs[0]["summary"] == "A very long title that the calendar has wrapped onto two lines"


def test_text_unescaping():
    ics = _ics(_vevent(SUMMARY="Call Bob\\, then Sue\\; bring notes", DTSTART=";VALUE=DATE:20260726"))
    evs = connect.parse_ics(ics, on=date(2026, 7, 26))
    assert evs[0]["summary"] == "Call Bob, then Sue; bring notes"


def test_weekly_recurrence_byday():
    # A Sunday standup that recurs weekly; 2026-08-02 is a Sunday.
    ics = _ics(_vevent(SUMMARY="Fellowship", DTSTART="20260726T160000Z",
                       RRULE="FREQ=WEEKLY;BYDAY=SU"))
    assert connect.parse_ics(ics, on=date(2026, 8, 2), tz=timezone.utc)  # a later Sunday → recurs
    assert connect.parse_ics(ics, on=date(2026, 8, 3), tz=timezone.utc) == []  # Monday → not


def test_daily_recurrence_with_until():
    ics = _ics(_vevent(SUMMARY="Morning prayer", DTSTART="20260726T120000Z",
                       RRULE="FREQ=DAILY;UNTIL=20260801"))
    assert connect.parse_ics(ics, on=date(2026, 7, 30), tz=timezone.utc)       # within window
    assert connect.parse_ics(ics, on=date(2026, 8, 5), tz=timezone.utc) == []  # past UNTIL


def test_empty_and_garbage_are_safe():
    assert connect.parse_ics("", on=date(2026, 7, 26)) == []
    assert connect.parse_ics("not a calendar at all", on=date(2026, 7, 26)) == []


def test_corrupt_dates_decline_instead_of_crashing():
    # A real calendar can carry one bad field (typo'd year, a nonexistent Feb 30) — this must
    # decline that field, never raise (found: an uncaught ValueError from strptime).
    for bad in (
        _ics(_vevent(SUMMARY="bad year", DTSTART=";VALUE=DATE:99999999")),
        _ics(_vevent(SUMMARY="no such day", DTSTART=";VALUE=DATE:20260230")),   # Feb 30
        _ics(_vevent(SUMMARY="bad timed", DTSTART="20269999T999999Z")),
    ):
        assert connect.parse_ics(bad, on=date(2026, 7, 26)) == []  # unparseable -> excluded, not raised


def test_read_calendar_from_file(tmp_path):
    p = tmp_path / "cal.ics"
    p.write_text(_ics(_vevent(SUMMARY="From a file", DTSTART=";VALUE=DATE:20260726")), encoding="utf-8")
    evs = connect.read_calendar(str(p), on=date(2026, 7, 26))
    assert evs and evs[0]["summary"] == "From a file"


def test_read_calendar_no_source_returns_empty(monkeypatch):
    monkeypatch.delenv("NH_CALENDAR_ICS", raising=False)
    assert connect.read_calendar(on=date(2026, 7, 26)) == []


def test_day_brief_marks_stored_false():
    b = connect.day_brief(on=date(2026, 7, 26))
    assert b["stored"] is False
    assert set(b["connected"]) == {"calendar", "email", "storage"}
