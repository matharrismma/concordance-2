"""THE COMMONS · C1d — a link, carded, with a waybill. No byte of anyone else's page is kept.

Matt, 2026-07-28: *"Can they drop their favorite videos, quotes, book recommendations. whatever
they enjoy sharing."* And: *"Any link they enjoy. We can curate and evaluate before we make
available."*

So a member drops a URL. We open it in the AIRLOCK, take down what is TRUE ABOUT THE ARTIFACT, and
throw the bytes away. What survives is a waybill:

    url · canonical host · the page's own <title> · content type · byte length · sha256 · fetched_at

Every one of those is a *fact about* the page, not a piece of it — the same distinction
`airlock.ingest` draws for a dragged file (docs: the file "never enters our core"). The card's BODY
is the member's own words about the link. That is the whole rule, and `no_page_bytes_kept()` below
is written so it can be checked rather than promised.

A QUOTE is different and is allowed: a short passage the member typed themselves, attributed, with
the link beside it. That is a citation, not a copy — and it is the MEMBER's act, carrying their name
at the member tier. Capped, and refused without attribution.

**WE DO NOT EMBED.** An iframe or a remote <img> would hand the reader's IP, user-agent, and
referrer to the provider the moment the page painted — and the one thing this library promises is
that nothing records who read what. We cannot make that promise and then quietly place a beacon on
the page. A link drop renders as a card with its waybill and a plain link; the reader decides to
walk through the door. `EMBED_POLICY` states it in the payload so no client has to guess.

THE FETCH IS THE DANGEROUS PART. A member-supplied URL fetched by our server is a server-side
request forgery primitive, so `_safe_target` refuses anything that is not public http(s): no other
scheme, no credentials in the URL, no loopback/private/link-local/multicast/reserved address, no
redirect off those rails, and a hard cap on bytes and time. It resolves the host and checks EVERY
address, because a name that resolves to 127.0.0.1 is the oldest trick here.

THREE STATES, never two. If we cannot reach a link that is our failure, reported as
`SYSTEM_ERROR` with what we tried — never as "the link is bad". A member's link is not falsified by
our outage.

Stdlib only.
"""
from __future__ import annotations

import hashlib
import ipaddress
import re
import socket
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

MAX_BYTES = 512 * 1024          # enough to reach a <title>; we are not archiving
TIMEOUT_S = 8
MAX_REDIRECTS = 3
MAX_QUOTE = 600                 # a citation, not a chapter
USER_AGENT = "NarrowHighway-Airlock/1.0 (+https://narrowhighway.com/llms.txt)"

EMBED_POLICY = ("not embedded on purpose — an iframe would hand your IP and referrer to the "
                "provider, and nothing here records who read what. The link is a door you choose "
                "to walk through.")

# What a waybill is allowed to contain. Anything not on this list is not kept, and the guard below
# is written against the list rather than against a remembered set of fields.
WAYBILL_FIELDS = ("url", "host", "page_title", "content_type", "bytes", "sha256", "fetched_at",
                  "status", "redirected_to")

_TITLE_MAX = 200
_WS = re.compile(r"\s+")


class _TitleGrab(HTMLParser):
    """Read ONLY the <title>. Not a parser for content — a parser for one fact about the page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in = False
        self.title = ""
        self.done = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title" and not self.done:
            self._in = True

    def handle_endtag(self, tag):
        if tag.lower() == "title" and self._in:
            self._in = False
            self.done = True

    def handle_data(self, data):
        if self._in and len(self.title) < _TITLE_MAX * 2:
            self.title += data


def _public_ip(host: str) -> Tuple[bool, str]:
    """Every address the name resolves to must be public. One private answer refuses the whole
    host — a round-robin that sometimes points inside is still a way inside."""
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as exc:
        return False, f"cannot resolve {host}: {exc}"
    if not infos:
        return False, f"cannot resolve {host}"
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr.split("%")[0])
        except ValueError:
            return False, f"unreadable address for {host}"
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
                or ip.is_reserved or ip.is_unspecified):
            return False, (f"{host} resolves to {ip}, which is not on the public internet — a link "
                           f"drop may not be used to reach inside the machine that fetches it")
    return True, ""


def _safe_target(url: str) -> Tuple[Optional[str], str]:
    """The normalised, fetchable URL — or a refusal with its reason."""
    raw = (url or "").strip()
    if not raw:
        return None, "a link drop needs a link"
    if len(raw) > 2000:
        return None, "that link is too long to be a link"
    p = urlparse(raw)
    if p.scheme.lower() not in ("http", "https"):
        return None, "only http and https links can be carried — no other scheme is fetched here"
    if p.username or p.password:
        return None, "a link with credentials in it is never fetched; strip them and try again"
    if not p.hostname:
        return None, "that link has no host"
    ok, why = _public_ip(p.hostname)
    if not ok:
        return None, why
    # drop the fragment: it is the reader's business, not part of the artifact
    return urlunparse((p.scheme, p.netloc, p.path or "/", p.params, p.query, "")), ""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects OURSELVES so each hop is re-checked against `_safe_target`. urllib would
    happily follow a 302 into 127.0.0.1, which is the whole attack."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise _Redirect(newurl)


class _Redirect(Exception):
    def __init__(self, to: str) -> None:
        super().__init__(to)
        self.to = to


def _open(target: str) -> Tuple[Optional[bytes], Dict[str, Any], str]:
    """Fetch at most MAX_BYTES, re-checking every redirect hop. Returns (body, meta, error)."""
    opener = urllib.request.build_opener(_NoRedirect)
    seen: List[str] = []
    cur = target
    for _hop in range(MAX_REDIRECTS + 1):
        req = urllib.request.Request(cur, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "text/html,*/*;q=0.5"})
        try:
            with opener.open(req, timeout=TIMEOUT_S) as r:
                body = r.read(MAX_BYTES + 1)
                return (body[:MAX_BYTES],
                        {"status": int(getattr(r, "status", 200) or 200),
                         "content_type": (r.headers.get("content-type") or "").split(";")[0].strip(),
                         "final_url": cur, "hops": seen}, "")
        except _Redirect as red:
            nxt, why = _safe_target(red.to)
            if not nxt:
                return None, {}, f"that link redirects somewhere we will not follow: {why}"
            seen.append(nxt)
            cur = nxt
        except urllib.error.HTTPError as exc:
            # A 4xx/5xx is a fact about the link, and we still record what we saw.
            return b"", {"status": int(exc.code), "content_type": "", "final_url": cur,
                         "hops": seen}, ""
        except (urllib.error.URLError, socket.timeout, OSError) as exc:
            return None, {}, f"could not reach it: {exc}"
    return None, {}, "too many redirects"


def waybill(url: str) -> Dict[str, Any]:
    """Open a link in the airlock, write down what is true ABOUT it, and discard the bytes.

    Returns `{ok, waybill, note}` — or, when the reach fails, `{ok: False, state: "SYSTEM_ERROR"}`
    which is a fact about US. A link we cannot fetch is not thereby a bad link; three states, never
    two ([[our failure is not their falsehood]]).
    """
    target, why = _safe_target(url)
    if not target:
        return {"ok": False, "state": "REFUSED", "error": why}
    body, meta, err = _open(target)
    if body is None:
        return {"ok": False, "state": "SYSTEM_ERROR", "error": err,
                "tried": target,
                "note": ("We could not reach it. That is a fact about us, not about the link — "
                         "nothing here says the page is bad.")}
    page_title = ""
    ctype = meta.get("content_type") or ""
    if body and ("html" in ctype.lower() or not ctype):
        g = _TitleGrab()
        try:
            g.feed(body.decode("utf-8", "replace"))
        except Exception:  # noqa: BLE001 — a page we cannot parse still has a waybill
            pass
        page_title = _WS.sub(" ", g.title).strip()[:_TITLE_MAX]
    wb = {
        "url": target,
        "host": (urlparse(target).hostname or "").lower(),
        "page_title": page_title,
        "content_type": ctype,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest() if body else "",
        "fetched_at": int(time.time()),
        "status": int(meta.get("status") or 0),
        "redirected_to": meta.get("final_url") if meta.get("final_url") != target else "",
    }
    del body  # say it out loud: the page does not outlive this call
    return {"ok": True, "waybill": wb, "embed": EMBED_POLICY,
            "note": ("Opened in the airlock and let go. What is kept is the address, the page's own "
                     "title, its size and fingerprint, and when we looked — facts about it, never "
                     "a copy of it.")}


def no_page_bytes_kept(wb: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """The invariant, checkable. A waybill may hold ONLY the declared fields — so a later hand
    cannot add `excerpt` or `description` or `text` and quietly turn a pointer into a copy.

    `page_title` is the one string that came from the page. It is the artifact's NAME, which is how
    a library has always referred to a work it does not own; a card with no title is unusable. It
    is capped and single-line, so it cannot become a smuggled body."""
    extra = [k for k in (wb or {}) if k not in WAYBILL_FIELDS]
    if extra:
        return False, [f"a waybill must not carry {sorted(extra)} — those are the page, not facts "
                       f"about it"]
    t = str((wb or {}).get("page_title") or "")
    if len(t) > _TITLE_MAX:
        return False, [f"page_title is {len(t)} chars — a title, not a passage"]
    if "\n" in t:
        return False, ["page_title spans lines — that is content, not a title"]
    return True, []


def quote_ok(quote: str, attribution: str) -> Tuple[bool, str]:
    """A member's own citation: short, attributed, and typed by them. Refused without a name to
    credit, because an unattributed quote is how a copy pretends to be a note."""
    q = (quote or "").strip()
    if not q:
        return True, ""                      # a link drop needs no quote
    if len(q) > MAX_QUOTE:
        return False, (f"a quote here is capped at {MAX_QUOTE} characters — cite the line that "
                       f"matters and link the rest")
    if not (attribution or "").strip():
        return False, ("a quote needs someone to credit — say whose words these are, or write it "
                       "in your own")
    return True, ""


__all__ = ["waybill", "no_page_bytes_kept", "quote_ok", "WAYBILL_FIELDS", "EMBED_POLICY",
           "MAX_QUOTE", "MAX_BYTES"]
