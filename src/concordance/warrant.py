"""THE WARRANT — steward authority with a name, a term, and rotation without a gap.

`docs/LESSONS_AND_HARDENING.md` H1, where two lessons met:

  * **L1 — a typed name is not authority.** `shelves.curate` once took the steward's name on faith,
    and C1b shipped that live. Closing it introduced a token, which fixed the hole and made this one.
  * **L11 — authority sunsets** (The Way v0.2): *"startup authority sunsets into the ordinary
    governance system."* What C1b shipped was **one permanent secret, no expiry, no rotation, and no
    record of who held it** — the exact opposite of the document it was meant to honour.

A warrant, not a password: it says WHO may act and UNTIL WHEN, and several may be live at once so a
rotation never leaves a moment where nobody can act.

    CONCORDANCE_STEWARD_WARRANTS="matt:s3cret-long-enough:2026-12-31, ruth:an0ther-secret:never"
                                  ^name ^secret             ^term ends (ISO date, or `never`)

FOUR THINGS IT REFUSES TO DO:

1. **Never return, log, or record the secret** — only the NAME. `identify()` hands back who acted so
   `curation.jsonl` can say `by_identity: "matt"` and the record stays publishable.
2. **Never treat an ended term as valid**, and say *ended* rather than *wrong* — a steward whose term
   finished is not an impostor and must not be sent hunting for a typo instead of a renewal.
3. **Never invent a date.** An unreadable expiry drops the whole entry rather than defaulting to
   `never`, because the failure mode of a guessed date is an authority that outlives its grant.
4. **Fail closed.** No configuration means no steward, never an open commons.

BACKWARD COMPATIBILITY, SAID OUT LOUD. If no warrants are configured, the older
`CONCORDANCE_KEEP_TOKEN` still works so the live box never loses its steward mid-change — but it
identifies as `legacy-keep-token` with `sunsets: False`, and the act records that. The weakness
becomes visible in the trail instead of hiding in the environment, which is the whole point of L11.

Stdlib only.
"""
from __future__ import annotations

import hmac
import os
import time
from typing import Any, Dict, List, Optional

ENV = "CONCORDANCE_STEWARD_WARRANTS"
LEGACY_ENV = "CONCORDANCE_KEEP_TOKEN"
LEGACY_NAME = "legacy-keep-token"
NEVER = "never"

MIN_SECRET = 12          # a steward secret short enough to guess is not a secret

_UNREADABLE = object()   # distinct from None ("no expiry") — see rule 3 above


def _parse_expiry(s: str):
    """`2026-12-31` → the last second of that day; `never` → None; anything unreadable → sentinel."""
    s = (s or "").strip().lower()
    if s in ("", NEVER):
        return None
    try:
        y, m, d = (int(x) for x in s.split("-"))
        return time.mktime((y, m, d, 23, 59, 59, 0, 0, -1))   # inclusive of the named day
    except (ValueError, TypeError, OverflowError):
        return _UNREADABLE


def warrants(raw: Optional[str] = None) -> List[Dict[str, Any]]:
    """The configured warrants. A malformed entry is DROPPED, never repaired into existence."""
    raw = os.environ.get(ENV, "") if raw is None else raw
    out: List[Dict[str, Any]] = []
    for chunk in (raw or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [p.strip() for p in chunk.split(":")]
        if len(parts) < 2:
            continue
        name, secret = parts[0], parts[1]
        expires = _parse_expiry(parts[2] if len(parts) > 2 else NEVER)
        if not name or len(secret) < MIN_SECRET or expires is _UNREADABLE:
            continue
        out.append({"name": name, "secret": secret, "expires_at": expires})
    return out


def identify(token: str, now: Optional[float] = None) -> Dict[str, Any]:
    """Who is acting? `{ok, name, expires_at, sunsets}` — and never the secret.

    A wrong token and an ended term are DIFFERENT answers, deliberately.
    """
    token = (token or "").strip()
    now = time.time() if now is None else now
    if not token:
        return {"ok": False, "error": "a steward's act needs a warrant — a typed name is not "
                                      "authority"}

    matched = None
    for w in warrants():
        if hmac.compare_digest(token, w["secret"]):
            matched = w
            break

    if matched is None:
        legacy = os.environ.get(LEGACY_ENV, "").strip()
        if legacy and len(legacy) >= MIN_SECRET and hmac.compare_digest(token, legacy):
            return {"ok": True, "name": LEGACY_NAME, "expires_at": None, "sunsets": False,
                    "note": (f"this authority has no end date; set {ENV} to give each steward a "
                             f"name and a term")}
        return {"ok": False, "error": "that is not a steward's warrant"}

    exp = matched["expires_at"]
    if exp is not None and now > exp:
        when = time.strftime("%Y-%m-%d", time.localtime(exp))
        return {"ok": False, "expired": True, "name": matched["name"],
                "error": (f"{matched['name']}'s warrant ended {when}. This is not a bad token — it "
                          f"is a finished term. Renew it in {ENV} to continue.")}

    return {"ok": True, "name": matched["name"], "expires_at": exp, "sunsets": exp is not None}


def roster(now: Optional[float] = None) -> Dict[str, Any]:
    """Who may act, and until when — carrying NO secret, so it is safe to show or log.

    Rotation is simply two live warrants at once: grant the next before the current one ends, and
    there is never a moment when nobody can act.
    """
    now = time.time() if now is None else now
    out = []
    for w in warrants():
        exp = w["expires_at"]
        out.append({"name": w["name"],
                    "expires": (time.strftime("%Y-%m-%d", time.localtime(exp)) if exp else NEVER),
                    "active": exp is None or now <= exp,
                    "sunsets": exp is not None})
    legacy = bool(os.environ.get(LEGACY_ENV, "").strip())
    using_legacy = legacy and not out
    return {
        "ok": True,
        "stewards": out,
        "active": [s["name"] for s in out if s["active"]],
        "expired": [s["name"] for s in out if not s["active"]],
        "legacy_token_in_use": using_legacy,
        "all_sunset": bool(out) and all(s["sunsets"] for s in out),
        "note": ("Rotation is two live warrants at once: grant the next before the current ends. "
                 "Nothing here reveals a secret — only who may act, and until when."),
    }


__all__ = ["identify", "roster", "warrants", "ENV", "LEGACY_ENV", "LEGACY_NAME", "MIN_SECRET"]
