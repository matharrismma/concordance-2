"""Contact — a public "reach the keeper" form. Messages go straight to the KEEP (the operator's
private window), not to email: each submission is persisted to a durable inbox and shown, newest
first, at the TOP of the keep dashboard. No address is ever shown on the page, and nothing on the
page records who wrote in.

Sovereign: stdlib only. Anti-spam: a honeypot field + the HTTP layer's rate limit.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List

_MAX = {"name": 120, "email": 200, "subject": 160, "message": 8000}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _inbox_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "contact_inbox.jsonl"


def inbox_count() -> int:
    """How many messages are in the inbox. Best-effort."""
    try:
        p = _inbox_path()
        if not p.exists():
            return 0
        with p.open(encoding="utf-8") as f:
            return sum(1 for ln in f if ln.strip())
    except Exception:
        return 0


def recent(limit: int = 25) -> List[Dict[str, Any]]:
    """The most recent messages, newest first — for the operator's keep window. Best-effort."""
    try:
        p = _inbox_path()
        if not p.exists():
            return []
        lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        out: List[Dict[str, Any]] = []
        for ln in reversed(lines[-max(1, min(limit, 200)):]):
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
        return out
    except Exception:
        return []


def _persist(rec: Dict[str, Any]) -> bool:
    try:
        p = _inbox_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def submit(body: Any) -> Dict[str, Any]:
    """Handle a contact submission — persist it to the inbox so it lands on the keep. Returns a
    client-safe result. The message is the payload; the keeper reads it on the keep, not by email."""
    if not isinstance(body, dict):
        return {"ok": False, "error": "expected a JSON object"}
    # honeypot: a hidden field a human never fills; a bot fills everything. Accept silently, drop it.
    if str(body.get("website") or body.get("hp") or "").strip():
        return {"ok": True, "message": "Thank you — your message was received."}

    def _f(k: str) -> str:
        return str(body.get(k) or "").strip()[:_MAX[k]]

    name, email, subject, message = _f("name"), _f("email"), _f("subject"), _f("message")
    if not message:
        return {"ok": False, "error": "a message is required"}
    if email and not _EMAIL_RE.match(email):
        return {"ok": False, "error": "that email address does not look valid"}
    now = time.time()
    rec = {"name": name, "email": email, "subject": subject, "message": message,
           "at": now, "at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))}
    if not _persist(rec):
        return {"ok": False, "error": "could not record your message — please try again"}
    return {"ok": True, "message": "Thank you — your message was received. We read every one."}
