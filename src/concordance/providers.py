"""The providers — the sources find reaches, with health, rotation, and credit.

Matt, 2026-08-30: "If a source fails us more than once, we cut it. Rotate it out. We can check back
later. Always give them credit. Provide their link with our explanation. We want to drive traffic to
them. Ideally with an easy way back."

Two covenants kept in one place:

  ROTATION — a source that fails us MORE THAN ONCE is benched (cut from the active chain), rested,
  and re-probed after a cooldown ("check back later"). One throttled catalogue can no longer drag
  every answer down to its timeout. This is policy, not a hardcode: Project Gutenberg kept timing out
  on us, so it starts PAUSED here and the health ledger will check back — "cut Gutenberg", done by
  the rule rather than by deletion, so the source is remembered and can rotate back in.

  CREDIT — these projects give their work to the commons freely, so we honour them: every source we
  surface carries their NAME, a one-line who-they-are, and a LINK with an easy way back. We drive
  traffic TO them; the attribution reaches the READER, not just the log ([[guarantee must reach the
  reader]]).

Metadata only — no provider FUNCTIONS live here (find owns those), so there is no import cycle: find
calls `record` at its one network chokepoint and asks `active` which sources to run this request.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

STRIKES_TO_BENCH = 2            # "fails us more than once" — the SECOND failure benches
COOLDOWN_SECONDS = 6 * 3600    # then we check back later


# The registry. `planes` is where a source can serve; `paused` cuts a source by policy (we still
# remember it, and the cooldown/return path can bring it back). Order is the reach order per plane.
PROVIDERS: List[Dict[str, Any]] = [
    {"id": "internet_archive", "name": "Internet Archive", "home": "https://archive.org",
     "blurb": "A non-profit digital library of millions of free public-domain books, films and "
              "recordings, kept for everyone.",
     "planes": ("text", "video"), "paused": False},
    {"id": "usda_bulletins", "name": "USDA Farmers' Bulletins",
     "home": "https://www.nal.usda.gov/collections/farmers-bulletins",
     "blurb": "The U.S. Department of Agriculture's own tried-and-true how-to bulletins — public-"
              "domain government works (17 USC 105), scanned and hosted by the Internet Archive.",
     "planes": ("text",), "paused": False},
    {"id": "library_of_congress", "name": "Library of Congress", "home": "https://www.loc.gov",
     "blurb": "The research library of the United States Congress — primary documents, film, maps "
              "and recordings, largely public domain.",
     "planes": ("text", "video"), "paused": False},
    {"id": "project_gutenberg", "name": "Project Gutenberg", "home": "https://www.gutenberg.org",
     "blurb": "The oldest library of free public-domain ebooks, transcribed and proofread by "
              "volunteers.",
     "planes": ("text",), "paused": True},   # CUT by policy 2026-08-30 (kept timing out); check back
]
_BY_ID = {p["id"]: p for p in PROVIDERS}


def _health_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "provider_health.json"


def _load() -> Dict[str, Any]:
    try:
        p = _health_path()
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save(h: Dict[str, Any]) -> None:
    try:
        p = _health_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(h), encoding="utf-8")
        os.replace(tmp, p)
    except Exception:  # noqa: BLE001
        pass


def record(pid: str, ok: bool, now: Optional[float] = None) -> None:
    """One outcome from a provider. Success clears its slate; a SECOND failure benches it for the
    cooldown. A failure after the cooldown has expired counts as a fresh first strike, not a pile-on,
    so a source that recovered gets a clean two-strike window. Never raises into the caller."""
    if pid not in _BY_ID:
        return
    now = time.time() if now is None else now
    h = _load()
    s = h.get(pid) or {"fails": 0, "benched_until": 0.0}
    if ok:
        s = {"fails": 0, "benched_until": 0.0, "last_ok": now}
    else:
        if float(s.get("benched_until", 0) or 0) and now > float(s["benched_until"]):
            s["fails"] = 1                        # cooldown expired, we checked back — fresh strike
        else:
            s["fails"] = int(s.get("fails", 0)) + 1
        if s["fails"] >= STRIKES_TO_BENCH:
            s["benched_until"] = now + COOLDOWN_SECONDS
        s["last_fail"] = now
    h[pid] = s
    _save(h)


def benched(pid: str, now: Optional[float] = None) -> bool:
    now = time.time() if now is None else now
    s = _load().get(pid) or {}
    return float(s.get("benched_until", 0) or 0) > now


def active(plane: str = "text", now: Optional[float] = None) -> List[Dict[str, Any]]:
    """The sources we may reach on this plane right now — registry order, minus the paused and the
    benched. An empty list is honest: it means every source on this plane is resting, and the answer
    degrades to 'we don't hold that yet' rather than hammering a source we already know is down."""
    out = []
    for p in PROVIDERS:
        if p.get("paused"):
            continue
        if plane not in p.get("planes", ()):
            continue
        if benched(p["id"], now):
            continue
        out.append(p)
    return out


def credit_for(pid: str) -> Dict[str, str]:
    p = _BY_ID.get(pid) or {}
    return {"name": p.get("name", ""), "home": p.get("home", ""), "blurb": p.get("blurb", "")}


def credit(doc: Dict[str, Any]) -> Dict[str, str]:
    """Reader-facing credit for a found doc: who they are, plus the link as an easy way back.
    Resolves the provider from the doc's `provider_id`, else from its human `source` name."""
    pid = (doc or {}).get("provider_id") or ""
    if not pid:
        name = ((doc or {}).get("source") or "").lower()
        for p in PROVIDERS:
            if name and (p["name"].lower() in name or name in p["name"].lower()):
                pid = p["id"]
                break
    c = credit_for(pid)
    c["url"] = (doc or {}).get("url", "")        # the item itself — the way back
    return c


def line(doc: Dict[str, Any]) -> str:
    """One reader-facing sentence of credit, carrying the way back. Empty if we can't name the source
    (better to say nothing than to credit no one)."""
    c = credit(doc)
    if not c.get("name"):
        return ""
    where = c["name"] + ((" (" + c["home"] + ")") if c.get("home") else "")
    tail = (" Go straight to it: " + c["url"]) if c.get("url") else ""
    return ("With thanks to " + where + " — " + (c.get("blurb", "") or "").strip() + tail).strip()


__all__ = ["PROVIDERS", "record", "benched", "active", "credit", "credit_for", "line",
           "STRIKES_TO_BENCH", "COOLDOWN_SECONDS"]
