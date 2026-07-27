"""Connect — the pass-through to the tools our users already carry.

Matt, 2026-07-26: *"We need to be able to take advantage of the tools they use. Their
calendar. Their email. Their storage."* — the parasitic-connector doctrine: **join their apps,
never absorb their data.** Narrow Highway reaches into a user's OWN calendar, email, and storage
in the moment it needs them, uses what it needs, and keeps NONE of it.

THE BOUNDARY (load-bearing, and enforced by tests/test_connect.py):

  1. **Pass-through — store nothing.** Every function here READS and RETURNS. Nothing is written to
     disk, sealed, cached, or logged. The user's calendar/email/files never enter the keeping.
  2. **Credential-local — it never crosses our wire.** This is an EDGE capability: it runs on the
     user's own box (sovereign mode) or a local companion, reading their tools over standard
     protocols. Their .ics link, IMAP app-password, and folder path come from the LOCAL environment
     (env vars / a local, gitignored config) — never from a public route, never sent to our server.
  3. **Read-only.** Email is fetched with BODY.PEEK (never marks messages seen); nothing is deleted,
     moved, or modified. Writing to a user's tools would require the agent-covenant write-consent
     path — out of scope for this read pass-through.
  4. **Standard protocols, bring-your-own-credential.** Calendar via iCalendar (.ics URL/CalDAV),
     email via IMAP, storage via a local folder (or WebDAV) — so it works with EVERY provider
     (Google, Apple, Outlook, Proton, Nextcloud) with no per-provider OAuth app. OAuth "one-click
     connect" is a later, additive tier; this sovereign path is the foundation.

Stdlib only (urllib, imaplib, email, pathlib) — no dependency, runs offline on the user's box.

    python -m concordance connect            # the whole day, from whatever is connected
    python -m concordance connect calendar    # just today's events
    python -m concordance connect email       # just the inbox that needs you
    python -m concordance connect storage      # just recent files
"""
from __future__ import annotations

import os
import re
import ssl
import urllib.request
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

# ── Config: read ONLY from the local environment. Never a request body, never our server. ──
_ENV = {
    "calendar": "NH_CALENDAR_ICS",     # a private .ics URL, webcal:// link, or a file path
    "imap_host": "NH_IMAP_HOST",
    "imap_user": "NH_IMAP_USER",
    "imap_password": "NH_IMAP_PASSWORD",  # an APP-PASSWORD, not the account password
    "imap_port": "NH_IMAP_PORT",
    "storage": "NH_STORAGE_PATH",      # a local folder the user points us at
}


def sources() -> dict:
    """What the user has connected — by presence only, never revealing the secret itself."""
    return {
        "calendar": bool(os.environ.get(_ENV["calendar"])),
        "email": bool(os.environ.get(_ENV["imap_host"]) and os.environ.get(_ENV["imap_user"])),
        "storage": bool(os.environ.get(_ENV["storage"])),
    }


# ─────────────────────────── Calendar (iCalendar / .ics) ───────────────────────────

def _unfold(text: str) -> list[str]:
    """RFC 5545 line unfolding: a line beginning with a space or tab continues the previous one."""
    out: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and out:
            out[-1] += raw[1:]
        else:
            out.append(raw)
    return out


def _unescape(v: str) -> str:
    return (v.replace("\\n", "\n").replace("\\N", "\n")
            .replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\").strip())


def _parse_dt(value: str, params: dict):
    """Return (datetime|date, all_day: bool). Handles UTC (Z), floating, TZID, and VALUE=DATE."""
    v = value.strip()
    if params.get("VALUE") == "DATE" or (len(v) == 8 and v.isdigit()):
        return datetime.strptime(v[:8], "%Y%m%d").date(), True
    m = re.match(r"^(\d{8}T\d{6})(Z?)$", v)
    if not m:
        # Unknown/partial form — fall back to the date if we can read one.
        try:
            return datetime.strptime(v[:8], "%Y%m%d").date(), True
        except ValueError:
            return None, False
    dt = datetime.strptime(m.group(1), "%Y%m%dT%H%M%S")
    if m.group(2) == "Z":
        return dt.replace(tzinfo=timezone.utc), False
    tzid = params.get("TZID")
    if tzid:
        try:
            from zoneinfo import ZoneInfo  # stdlib 3.9+
            return dt.replace(tzinfo=ZoneInfo(tzid)), False
        except Exception:
            pass
    return dt, False  # floating/local


def _local_date(dt, tz):
    """The calendar date an instant falls on, in the viewer's timezone."""
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt
    if dt.tzinfo is not None:
        return dt.astimezone(tz).date()
    return dt.date()


def _recurs_on(ev: dict, target: date) -> bool:
    """Modest, honest RRULE handling: DAILY and WEEKLY(BYDAY) — the common calendar cases.
    Other frequencies are surfaced only on their start date (marked recurring)."""
    rule = ev.get("_rrule")
    start = ev.get("_start_date")
    if not rule or not start or target < start:
        return False
    until = rule.get("UNTIL")
    if until and target > until:
        return False
    freq = rule.get("FREQ")
    if freq == "DAILY":
        return True
    if freq == "WEEKLY":
        byday = rule.get("BYDAY")
        days = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
        if byday:
            wanted = {days[d[-2:]] for d in byday.split(",") if d[-2:] in days}
            return target.weekday() in wanted
        return target.weekday() == start.weekday()
    return False


def _parse_rrule(value: str) -> dict:
    out: dict = {}
    for part in value.split(";"):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        if k == "UNTIL":
            try:
                out["UNTIL"] = datetime.strptime(v[:8], "%Y%m%d").date()
            except ValueError:
                pass
        else:
            out[k] = v
    return out


def parse_ics(text: str, on: date | None = None, tz=None) -> list[dict]:
    """Parse iCalendar text into the events that fall on `on` (default: today, viewer-local).
    Pure: reads a string, returns a list — writes nothing."""
    tz = tz or datetime.now().astimezone().tzinfo
    target = on or datetime.now(tz).date()
    events: list[dict] = []
    cur: dict | None = None
    for line in _unfold(text):
        if line == "BEGIN:VEVENT":
            cur = {}
            continue
        if line == "END:VEVENT":
            if cur is not None:
                events.append(cur)
            cur = None
            continue
        if cur is None or ":" not in line:
            continue
        name_part, value = line.split(":", 1)
        bits = name_part.split(";")
        name = bits[0].upper()
        params = {}
        for p in bits[1:]:
            if "=" in p:
                pk, pv = p.split("=", 1)
                params[pk.upper()] = pv
        if name == "SUMMARY":
            cur["summary"] = _unescape(value)
        elif name == "LOCATION":
            cur["location"] = _unescape(value)
        elif name == "DTSTART":
            dt, all_day = _parse_dt(value, params)
            cur["_start"] = dt
            cur["all_day"] = all_day
            cur["_start_date"] = _local_date(dt, tz) if dt else None
            cur["start"] = _fmt(dt, all_day, tz)
        elif name == "DTEND":
            dt, all_day = _parse_dt(value, params)
            cur["end"] = _fmt(dt, all_day, tz)
        elif name == "RRULE":
            cur["_rrule"] = _parse_rrule(value)
            cur["recurring"] = True

    out = []
    for ev in events:
        sd = ev.get("_start_date")
        on_day = (sd == target) or _recurs_on(ev, target)
        if not on_day:
            continue
        out.append({
            "summary": ev.get("summary", "(untitled)"),
            "start": ev.get("start", ""),
            "end": ev.get("end", ""),
            "location": ev.get("location", ""),
            "all_day": ev.get("all_day", False),
            "recurring": ev.get("recurring", False),
            "_sort": _sort_key(ev, tz),
        })
    out.sort(key=lambda e: e.pop("_sort"))
    return out


def _fmt(dt, all_day, tz) -> str:
    if dt is None:
        return ""
    if all_day:
        return "all day"
    if isinstance(dt, datetime):
        local = dt.astimezone(tz) if dt.tzinfo else dt
        return local.strftime("%-I:%M %p") if os.name != "nt" else local.strftime("%I:%M %p").lstrip("0")
    return str(dt)


def _sort_key(ev, tz):
    dt = ev.get("_start")
    if isinstance(dt, datetime):
        return (0, (dt.astimezone(tz) if dt.tzinfo else dt).time().isoformat())
    return (-1, "")  # all-day first


def _fetch(url: str) -> str:
    """Fetch an .ics over http(s). webcal:// is normalized to https://. Local files read directly."""
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]
    if url.startswith(("http://", "https://")):
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "NarrowHighway-Connect/1"})
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:  # noqa: S310 (user's own URL)
            return r.read().decode("utf-8", "replace")
    return Path(url).expanduser().read_text(encoding="utf-8", errors="replace")


def read_calendar(source: str | None = None, on: date | None = None) -> list[dict]:
    """Today's events from the user's own calendar (.ics URL / webcal / file path). Stores nothing."""
    source = source or os.environ.get(_ENV["calendar"])
    if not source:
        return []
    return parse_ics(_fetch(source), on=on)


# ─────────────────────────── Email (IMAP, read-only) ───────────────────────────

def read_email(host: str | None = None, user: str | None = None, password: str | None = None,
               port: int | None = None, folder: str = "INBOX", unseen_only: bool = True,
               limit: int = 8) -> list[dict]:
    """Recent messages that may need the user, over IMAP. BODY.PEEK — never marks anything seen;
    never deletes or moves. Reads headers only. Stores nothing. Credentials come from the LOCAL
    environment (an app-password), never from our server."""
    import imaplib
    from email import message_from_bytes
    from email.header import decode_header, make_header
    from email.utils import parseaddr

    host = host or os.environ.get(_ENV["imap_host"])
    user = user or os.environ.get(_ENV["imap_user"])
    password = password or os.environ.get(_ENV["imap_password"])
    if not (host and user and password):
        return []
    port = int(port or os.environ.get(_ENV["imap_port"] ) or 993)

    def _h(raw) -> str:
        try:
            return str(make_header(decode_header(raw or "")))
        except Exception:
            return raw or ""

    out: list[dict] = []
    M = imaplib.IMAP4_SSL(host, port)
    try:
        M.login(user, password)
        M.select(folder, readonly=True)  # readonly: the server must not mark anything seen
        typ, data = M.search(None, "UNSEEN" if unseen_only else "ALL")
        ids = data[0].split() if data and data[0] else []
        for num in reversed(ids[-limit:] if len(ids) > limit else ids):
            typ, md = M.fetch(num, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if typ != "OK" or not md or not md[0]:
                continue
            msg = message_from_bytes(md[0][1])
            name, addr = parseaddr(_h(msg.get("From")))
            out.append({
                "from": name or addr,
                "from_addr": addr,
                "subject": _h(msg.get("Subject")),
                "date": _h(msg.get("Date")),
            })
    finally:
        try:
            M.logout()
        except Exception:
            pass
    return out


# ─────────────────────────── Storage (local folder / WebDAV) ───────────────────────────

def read_storage(path: str | None = None, limit: int = 12) -> list[dict]:
    """Most-recently-touched files in a folder the user points us at. Read-only, stores nothing."""
    path = path or os.environ.get(_ENV["storage"])
    if not path:
        return []
    root = Path(path).expanduser()
    if not root.is_dir():
        return []
    items = []
    for p in root.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            try:
                st = p.stat()
            except OSError:
                continue
            items.append((st.st_mtime, p, st.st_size))
    items.sort(key=lambda t: t[0], reverse=True)
    out = []
    for mtime, p, size in items[:limit]:
        out.append({
            "name": p.name,
            "rel": str(p.relative_to(root)),
            "size": size,
            "modified": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return out


# ─────────────────────────── The simple experience: one brief ───────────────────────────

def day_brief(on: date | None = None) -> dict:
    """Assemble the user's day from whatever they've connected — calendar, inbox, files.
    Reads their tools in the moment; returns a plain dict; keeps NOTHING."""
    have = sources()
    brief: dict = {"connected": have, "stored": False}
    errors: dict = {}
    if have["calendar"]:
        try:
            brief["calendar"] = read_calendar(on=on)
        except Exception as e:
            errors["calendar"] = f"{type(e).__name__}: {e}"
    if have["email"]:
        try:
            brief["email"] = read_email()
        except Exception as e:
            errors["email"] = f"{type(e).__name__}: {e}"
    if have["storage"]:
        try:
            brief["storage"] = read_storage()
        except Exception as e:
            errors["storage"] = f"{type(e).__name__}: {e}"
    if errors:
        brief["errors"] = errors
    return brief


# ─────────────────────────── CLI ───────────────────────────

def _print_calendar(evs):
    if not evs:
        print("  (nothing on the calendar today)")
        return
    for e in evs:
        when = "all day" if e["all_day"] else (e["start"] + (f"–{e['end']}" if e["end"] else ""))
        loc = f"  @ {e['location']}" if e["location"] else ""
        rec = "  ↻" if e["recurring"] else ""
        print(f"  {when:>16}  {e['summary']}{loc}{rec}")


def run(argv: list[str]) -> int:
    what = argv[0] if argv else "all"
    have = sources()
    if what in ("all", "calendar") and have["calendar"]:
        print("Today —")
        _print_calendar(read_calendar())
    if what in ("all", "email") and have["email"]:
        print("Inbox —")
        msgs = read_email()
        if not msgs:
            print("  (nothing unread that needs you)")
        for m in msgs:
            print(f"  {m['from'][:28]:<28}  {m['subject'][:60]}")
    if what in ("all", "storage") and have["storage"]:
        print("Recent files —")
        for f in read_storage():
            print(f"  {f['modified']}  {f['rel']}")
    if not any(have.values()):
        print("Nothing connected yet. Point Narrow Highway at your own tools (local, private):")
        print(f"  export {_ENV['calendar']}='https://…/basic.ics'   # your private calendar link")
        print(f"  export {_ENV['imap_host']}='imap.gmail.com'  {_ENV['imap_user']}='you@…'  "
              f"{_ENV['imap_password']}='<app-password>'")
        print(f"  export {_ENV['storage']}='~/Documents'")
        print("Your credentials stay on this machine. We read in the moment and keep nothing.")
    return 0
