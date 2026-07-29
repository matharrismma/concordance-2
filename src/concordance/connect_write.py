"""The first door behind the consent lock — calendar write-back, and only that.

Matt's decision (2026-07-28): a NARROW pilot. One verb (`calendar_write`), one action (create an
event in the user's OWN calendar), chosen because it is the least dangerous write there is — the
user sees it instantly and can delete it instantly. Email and storage writes remain doors that do
not exist.

Deliberately a SEPARATE module from connect.py: the read-only pass-through keeps its purity, and
`tests/test_connect.py` keeps its teeth (it bans write tokens from that module's source). This
module is the one place an on-behalf write lives, and its shape is the covenant's:

  1. `consent.guard()` FIRST — no live grant from this human for this agent for this verb, no
     write; the refusal teaches the way in (member ≠ proxy).
  2. The event is standard RFC 5545, written into THEIR calendar — a local .ics file (sovereign
     mode) or a CalDAV collection (bring-your-own URL). We store NOTHING; the event exists only
     where they keep their days.
  3. A receipt comes back (uid, target, grant id) — the covenant's fifth rule: a consequential
     action produces a receipt.

Configuration is the user's, on the user's box:
    NH_CALENDAR_WRITE = /path/to/calendar.ics      (append locally)
                      | https://…/dav/calendar/    (CalDAV PUT)
"""
from __future__ import annotations

import os
import secrets
import time
import urllib.request
from typing import Any, Dict, Optional

from . import consent

ENV_TARGET = "NH_CALENDAR_WRITE"


def _fold(line: str) -> str:
    """RFC 5545 §3.1: content lines fold at 75 octets."""
    out = []
    while len(line.encode("utf-8")) > 73:
        cut = 73
        while len(line[:cut].encode("utf-8")) > 73:
            cut -= 1
        out.append(line[:cut])
        line = " " + line[cut:]
    out.append(line)
    return "\r\n".join(out)


def _esc(v: str) -> str:
    return (v or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def build_vevent(summary: str, start_iso: str, end_iso: Optional[str] = None,
                 description: str = "") -> Dict[str, str]:
    """A standard VEVENT. Date-only starts become all-day events. Returns {uid, vevent}."""
    uid = f"nh-{secrets.token_hex(8)}@narrowhighway"
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    s = (start_iso or "").strip().replace("-", "").replace(":", "")
    all_day = len(s) == 8
    lines = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}"]
    if all_day:
        lines.append(f"DTSTART;VALUE=DATE:{s}")
        if end_iso:
            lines.append(f"DTEND;VALUE=DATE:{(end_iso or '').strip().replace('-', '')}")
    else:
        lines.append(f"DTSTART:{s}")
        if end_iso:
            lines.append(f"DTEND:{(end_iso or '').strip().replace('-', '').replace(':', '')}")
    lines.append(_fold(f"SUMMARY:{_esc(summary)}"))
    if description:
        lines.append(_fold(f"DESCRIPTION:{_esc(description)}"))
    lines.append("END:VEVENT")
    return {"uid": uid, "vevent": "\r\n".join(lines)}


def create_event(grantor_pubkey: str, agent_fp: str, summary: str, start_iso: str,
                 end_iso: Optional[str] = None, description: str = "",
                 target: Optional[str] = None) -> Dict[str, Any]:
    """The pilot write. The lock is checked before ANYTHING else happens — an unauthorized call
    does not even build the event."""
    g = consent.guard(agent_fp, "calendar_write", grantor_pubkey)
    if not g.get("authorized"):
        return {"ok": False, "refused": True, "error": g.get("detail"),
                "refusal": g.get("refusal"), "tampered_entries": g.get("tampered_entries", 0)}
    if not (summary or "").strip() or not (start_iso or "").strip():
        return {"ok": False, "error": "summary and start_iso are required"}

    dest = (target or os.environ.get(ENV_TARGET, "")).strip()
    if not dest:
        return {"ok": False, "error": f"{ENV_TARGET} is not configured — the user names WHERE "
                                      f"their calendar lives; we never guess a destination"}
    ev = build_vevent(summary, start_iso, end_iso, description)

    if dest.lower().startswith(("http://", "https://")):
        # CalDAV: PUT one .ics resource into the user's collection.
        url = dest.rstrip("/") + f"/{ev['uid']}.ics"
        body = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//NarrowHighway//consented-write//EN\r\n"
                + ev["vevent"] + "\r\nEND:VCALENDAR\r\n").encode("utf-8")
        req = urllib.request.Request(url, data=body, method="PUT",
                                     headers={"Content-Type": "text/calendar; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 — user-named URL
                code = resp.status
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"the calendar did not accept the event: {e}"}
        if code not in (200, 201, 204):
            return {"ok": False, "error": f"the calendar answered {code}"}
        kind = "caldav"
    else:
        # Sovereign mode: the user's own .ics file on their own disk. Insert before the final
        # END:VCALENDAR; create a minimal calendar if the file does not exist yet.
        try:
            if os.path.exists(dest):
                text = open(dest, encoding="utf-8").read()
                marker = "END:VCALENDAR"
                idx = text.rstrip().rfind(marker)
                if idx < 0:
                    return {"ok": False, "error": "the target file is not a VCALENDAR"}
                text = text[:idx] + ev["vevent"] + "\r\n" + text[idx:]
            else:
                text = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
                        "PRODID:-//NarrowHighway//consented-write//EN\r\n"
                        + ev["vevent"] + "\r\nEND:VCALENDAR\r\n")
            with open(dest, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError as e:
            return {"ok": False, "error": f"could not write the calendar file: {e}"}
        kind = "file"

    # The receipt — covenant rule 5. We keep no copy of the event itself; it lives in THEIR days.
    return {"ok": True, "uid": ev["uid"], "target_kind": kind,
            "grant_id": g.get("grant_id"), "scope_used": "calendar_write",
            "note": ("Written into the calendar the user named, under a grant the user signed. "
                     "Nothing was stored here; delete the event there and it is gone everywhere.")}


__all__ = ["create_event", "build_vevent", "ENV_TARGET"]
