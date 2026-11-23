"""THE HELM on the operator's phone — his own devices, his own door.

The push stack was already here and nothing used it: `concordance.push` implements RFC 8291
(aes128gcm payload encryption) and RFC 8292 (VAPID) with no third-party dependency, `site/sw.js`
already carries the `push` and `notificationclick` handlers — and **no page in the site ever called
`pushManager.subscribe`**, so not one device was ever registered. This module and the Helm's phone
section are the missing link.

WHY THE HELM DOES NOT REUSE /push/subscribe. That endpoint is deliberately unauthenticated,
because a mesh node is keyed by its OWN public fingerprint and proves nothing to subscribe itself.
For the operator's panel that would be two holes at once: anyone who guessed the fingerprint could
POST their own device and **receive the operator's alerts**, or POST to /push/unsubscribe and
**silence his phone** (that endpoint "requires no proof at all" — push.py says so in its own
comment). So:

  - the Helm's fingerprint is a RANDOM 32-hex secret generated on the server, persisted beside the
    subscriptions, and NEVER sent to a browser or accepted from a request;
  - the only way to add or remove a device is POST /helm/push, behind `keep.request_is_operator`.

The storage, the crypto and the VAPID identity are push.py's, untouched. This file only decides WHO
may register a device and WHAT is allowed to wake him.

WHAT MAY WAKE HIM — the policy, stated here because the place to argue it is once, not per caller:
only (1) a safety gate failing a pin, (2) the integrity chain disagreeing with itself, and (3) a
lever waiting at the desk. Everything else he pulls. A panel that pushes nine kinds of notification
teaches its owner to ignore it, and then the one that matters arrives inside the noise it taught him
to dismiss. No email, ever. The triggers themselves are not built yet; `notify()` here is the one
door they will use.
"""
from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any, Dict

from .. import push

_FP_FILE = "helm_fp.json"
_TEST_TITLE = "The Helm"
_TEST_BODY = "This device is registered. You will only be woken by a failed safety pin, a chain that disagrees with itself, or a lever waiting at the desk."


def _fp() -> str:
    """The Helm's own subscription key: a server-side secret, made once and kept. Never leaves the
    server, never read from a request — see the module docstring for what that prevents."""
    p: Path = push._dir() / _FP_FILE          # same gitignored dir as the subscriptions
    if p.exists():
        try:
            fp = (json.loads(p.read_text(encoding="utf-8")) or {}).get("fp")
            if fp:
                return str(fp)
        except ValueError:
            pass
    fp = secrets.token_hex(16)                # 32 hex chars — inside push._FP_RE's 8..80
    p.write_text(json.dumps({"fp": fp}), encoding="utf-8")
    return fp


def _available() -> tuple:
    """Push needs the optional `cryptography` extra for VAPID. Say so plainly rather than 500."""
    try:
        push.vapid_keys()
        return True, None
    except ImportError:
        return False, "the signing extra is not installed here (pip install -e .[signing])"
    except Exception as e:                                    # noqa: BLE001 - never break the panel
        return False, "%s: %s" % (type(e).__name__, e)


def status() -> Dict[str, Any]:
    """What the panel needs to draw the phone row. Reveals the VAPID PUBLIC key (that is what it is
    for — the browser needs it as applicationServerKey) and the device COUNT, never the fingerprint
    and never a subscription."""
    ok, why = _available()
    devices = len(push._subs_for(_fp())) if ok else 0
    return {
        "available": ok,
        "unavailable_because": why,
        # the network hop out to the push service is off unless the host turns it on. A device can
        # still be REGISTERED with it off; nothing is delivered until it is on.
        "delivery_enabled": push.enabled(),
        "key": push.public_key_b64() if ok else None,
        "devices": devices,
    }


def subscribe(subscription: Dict[str, Any]) -> Dict[str, Any]:
    ok, why = _available()
    if not ok:
        return {"ok": False, "error": why}
    res = push.subscribe(_fp(), subscription)
    res["delivery_enabled"] = push.enabled()
    return res


def forget() -> Dict[str, Any]:
    """Drop every device. The operator's own panel is the only way to do this, which is the point."""
    ok, why = _available()
    if not ok:
        return {"ok": False, "error": why}
    return push.unsubscribe(_fp())


def notify(title: str, body: str, url: str = "/helm.html") -> Dict[str, Any]:
    """The one door the triggers will use. Best-effort and off by default — with delivery disabled
    this reports sent=0 rather than pretending."""
    ok, why = _available()
    if not ok:
        return {"ok": False, "error": why, "sent": 0}
    return push.notify(_fp(), title, body, url=url)


def test() -> Dict[str, Any]:
    """Prove the whole path to the operator's own phone, because a notification stack that has
    never delivered once is a stack nobody should trust on the day it matters."""
    res = notify(_TEST_TITLE, _TEST_BODY)
    if res.get("ok") and not res.get("sent"):
        res["why_nothing_arrived"] = (
            "no device registered yet" if not res.get("devices")
            else "delivery is off on this host (CONCORDANCE_PUSH_ENABLED is not set)")
    return res


__all__ = ["status", "subscribe", "forget", "notify", "test"]
