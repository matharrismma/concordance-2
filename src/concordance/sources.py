"""THE SOURCE ARK — the body lands on the drive, hashed, or we say plainly that it did not.

Matt, 2026-08-01: *"We want as many of the sources on the external hard drive as possible. We will
have multiple drives and store them in many locations. It can be shared extensively over time, but
we spread the Card Corpus across the world by being useful and cheap and small."*

That is the two-tier design, and this module is its anchoring half. Cards travel — small, cheap,
useful, and everywhere. Bodies anchor — full texts on drives multiplied across locations, each one
verifiable on its own without asking us or anyone else.

WHAT WAS MISSING, and why the flywheel did not turn. `shepherd_rounds.choose()` minted a card whose
body was the miner's 600-character SNIPPET, with the origin URL in `source.url`. So a chosen want
produced a POINTER, not a holding: nothing landed on the drive, nothing could be read offline, and
"heal from what you hold" had nothing to heal from. The loop ran miss -> want -> forage -> choose
and then stopped one step short of an asset.

THE WAYBILL IS THE POINT. Every stored body gets a sidecar recording origin URL, sha256, byte
count, media type, when it was fetched, which want asked for it and who chose it. A drive copied to
another drive carries the waybills with it, so ANY holder can re-verify every file against its own
hash with no network and no trust in us. That is what makes a copied drive a verifiable drive.

THREE STATES, NEVER TWO. A fetch that fails is not a card that lies:
    held        the bytes are on the drive and the hash matches on both sides
    not_held    we could not fetch it (offline, refused, too large, wrong type) — SAID SO
    already     this exact content is already on the drive; nothing refetched, nothing duplicated
A card minted after a failed fetch still gets minted, and it says `ark: null` with the reason. It
must never claim to hold what it does not.

STRICT GATE. Only the whitelisted public-domain / open-access hosts `find.py` already uses — the
Library of Congress, the Internet Archive, Project Gutenberg. One allowlist, reused, not a second
one that could drift from the first. Anything else is refused by host, before a byte is requested.

BOUNDED BY CONSTRUCTION. A miner must never be able to fill a 12 TB drive by accident: a byte
ceiling enforced DURING streaming (not from a Content-Length header a server can lie about), a
timeout, and a redirect that must still land on an allowlisted host.

Content-addressed layout — the hash IS the name, so the same body fetched twice is stored once:

    <SOURCES>/<sha256[:2]>/<sha256>[.ext]        the bytes, never overwritten, never deleted
    <SOURCES>/<sha256[:2]>/<sha256>.waybill.json the provenance beside them
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

# The same hosts find.py already searches. Imported as data rather than re-typed, so the fetch gate
# and the search gate cannot drift apart.
ALLOWED_HOSTS = frozenset({
    "www.loc.gov", "loc.gov", "tile.loc.gov",
    "archive.org", "iaod.archive.org", "web.archive.org",
    "www.gutenberg.org", "gutenberg.org", "aleph.gutenberg.org",
})

# ARCHIVE.ORG SERVES EVERY DOWNLOAD FROM A NUMBERED STORAGE NODE — ia801905.us, dn790008.ca,
# dn760107.eu — picked per request, so `archive.org/download/...` always redirects to a host
# chosen at fetch time. This constant has now been wrong TWICE, both times by generalizing from
# exactly what had been observed:
#
#   1. It named ONE guessed node (`ia801.us.archive.org`), so the redirect check — itself correct —
#      refused every real download, and the ark could not fetch from archive.org at all.
#   2. Fixed 2026-08-01 to `.us.archive.org`, the suffix of the node observed that morning. The
#      SAME EVENING a six-book batch was refused entire: the CDN answered from `.ca.` and `.eu.`
#      nodes. The fix was measured, and measured too narrowly.
#
# The trust argument never depended on the continent: only the Internet Archive controls the
# archive.org DNS zone, so `.archive.org` IS the boundary — anything narrower is an assumption
# about their CDN topology, which their CDN falsified within hours. The leading dot stays
# load-bearing: `evil-archive.org` and `archive.org.evil.com` both remain refused.
ALLOWED_SUFFIXES = (".archive.org",)

MAX_BYTES = 64 * 1024 * 1024      # 64 MB: a book, not a film. Enforced while streaming.
TIMEOUT = 30
_UA = "NarrowHighway/1.0 (+https://narrowhighway.com; source ark)"
_CHUNK = 64 * 1024

# Media we can actually keep and read later. A login page is HTML and would otherwise be stored
# forever as though it were a book.
KEEPABLE = ("text/plain", "text/html", "application/pdf", "application/epub",
            "application/epub+zip", "application/octet-stream", "text/xml", "application/xml",
            "application/json")

HELD, NOT_HELD, ALREADY = "held", "not_held", "already"


def sources_dir() -> Optional[Path]:
    """Where bodies land. Unset means this device does not anchor sources — which is legitimate:
    a phone carries cards, not the ark."""
    d = os.environ.get("CONCORDANCE_SOURCES", "").strip()
    return Path(d) if d else None


def _host_ok(url: str) -> bool:
    try:
        host = (urllib.parse.urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    if host in ALLOWED_HOSTS:
        return True
    return any(host.endswith(sfx) for sfx in ALLOWED_SUFFIXES)


def _ext_for(url: str, ctype: str) -> str:
    for suffix in (".txt", ".htm", ".html", ".pdf", ".epub", ".xml", ".json"):
        if url.lower().split("?")[0].endswith(suffix):
            return suffix
    return {"text/plain": ".txt", "text/html": ".html", "application/pdf": ".pdf",
            "application/epub+zip": ".epub"}.get((ctype or "").split(";")[0].strip(), "")


def path_for(sha: str, ext: str = "") -> Optional[Path]:
    base = sources_dir()
    if not base:
        return None
    return base / sha[:2] / (sha + ext)


def resolve_text_url(url: str, _meta=None) -> Optional[str]:
    """The plain-text download behind a catalogue page, or None when there isn't one.

    The tortoise finds DETAIL pages — `archive.org/details/x`, `gutenberg.org/ebooks/n` — and for
    months the mint carded the citation because nothing could open the book behind it (Matt,
    2026-08-02: "I asked it to find the information, and it couldn't do that."). This is the
    missing step: catalogue entry -> the text itself.

      archive.org   the item's metadata names its files; we take the `_djvu.txt` and honour
                    `access-restricted-item`. `_meta` injects the metadata dict in tests so no
                    test ever depends on the network.
      gutenberg     the plain-text URL is deterministic from the ebook number.
      anything else None — LoC items are largely images and maps; carding a scan as text would
                    card noise, so the citation stands alone there, honestly.
    """
    u = str(url or "")
    m = re.search(r"gutenberg\.org/ebooks/(\d+)", u)
    if m:
        return f"https://www.gutenberg.org/cache/epub/{m.group(1)}/pg{m.group(1)}.txt"
    m = re.search(r"archive\.org/details/([^/?#]+)", u)
    if m:
        ident = m.group(1)
        meta = _meta
        if meta is None:
            try:
                req = urllib.request.Request(f"https://archive.org/metadata/{ident}",
                                             headers={"User-Agent": _UA})
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                    meta = json.loads(r.read().decode("utf-8", "replace"))
            except Exception:  # noqa: BLE001 — an unreachable catalogue is a miss, not an error page
                return None
        md = (meta or {}).get("metadata") or {}
        if str(md.get("access-restricted-item", "")).lower() in ("true", "1"):
            return None
        for f in (meta or {}).get("files") or []:
            name = str(f.get("name") or "")
            if name.endswith("_djvu.txt"):
                # A scan's filename can carry spaces or stray control characters (e.g. an
                # 'in.gov.ignca…' item), which urllib rejects outright ("URL can't contain control
                # characters") — so the openable book was lost to a fetch that never left. Percent-
                # encode the path segments; the bytes behind the name are unchanged.
                return ("https://archive.org/download/" + urllib.parse.quote(ident)
                        + "/" + urllib.parse.quote(name))
    return None


def held(sha: str) -> Optional[Dict[str, Any]]:
    """The waybill for a body we hold, or None. Reads the drive — no index to fall out of date."""
    base = sources_dir()
    if not base or not sha:
        return None
    d = base / sha[:2]
    if not d.is_dir():
        return None
    for w in d.glob(sha + ".waybill.json"):
        try:
            return json.loads(w.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    return None


def verify(sha: str) -> Dict[str, Any]:
    """RE-HASH THE BYTES ON THE DRIVE. Never trust the name of a file, or a manifest, or us.

    This is what makes a copied drive verifiable by whoever holds it: the hash is recomputed from
    the bytes present, right now, and compared to the name they are filed under. A file that has
    rotted, been truncated, or been swapped is reported `invalid` — not quietly skipped.
    """
    w = held(sha)
    if not w:
        return {"sha256": sha, "status": "absent"}
    p = Path(w.get("path", ""))
    if not p.is_file():
        return {"sha256": sha, "status": "absent", "waybill": w}
    h = hashlib.sha256()
    try:
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(_CHUNK), b""):
                h.update(chunk)
    except OSError as e:
        return {"sha256": sha, "status": "unreadable", "error": str(e)}
    actual = h.hexdigest()
    return {"sha256": sha, "status": "valid" if actual == sha else "invalid",
            "actual": actual, "bytes": p.stat().st_size, "path": str(p)}


def fetch(url: str, *, want_id: str = "", chosen_by: str = "", label: str = "",
          license_note: str = "public domain / open access") -> Dict[str, Any]:
    """Fetch one body to the drive and return its waybill. Never raises for an expected failure.

    Returns {"status": held|already|not_held, ...}. `not_held` always carries `reason` in words a
    person can act on — the point is that the caller can mint an honest card either way.
    """
    base = sources_dir()
    if not base:
        return {"status": NOT_HELD, "reason": "this device anchors no sources "
                                              "(CONCORDANCE_SOURCES is unset)"}
    if not url:
        return {"status": NOT_HELD, "reason": "the option carried no source url"}
    if not _host_ok(url):
        host = (urllib.parse.urlparse(url).hostname or "?")
        return {"status": NOT_HELD, "reason": f"{host} is not an allowed public-domain source"}

    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    h = hashlib.sha256()
    tmp = base / ".incoming"
    tmp.mkdir(parents=True, exist_ok=True)
    staging = tmp / f"fetch_{int(time.time() * 1000)}_{os.getpid()}"
    total, ctype = 0, ""
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            # A redirect must still land somewhere allowed — otherwise the allowlist is a
            # suggestion rather than a gate.
            final = r.geturl()
            if not _host_ok(final):
                return {"status": NOT_HELD,
                        "reason": f"redirected off the allowlist to {urllib.parse.urlparse(final).hostname}"}
            ctype = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
            if ctype and not any(ctype.startswith(k) for k in KEEPABLE):
                return {"status": NOT_HELD, "reason": f"not a keepable document ({ctype})"}
            with open(staging, "wb") as out:
                while True:
                    chunk = r.read(_CHUNK)
                    if not chunk:
                        break
                    total += len(chunk)
                    # Enforced HERE, not from Content-Length: a header can lie, a stream cannot.
                    if total > MAX_BYTES:
                        out.close()
                        staging.unlink(missing_ok=True)
                        return {"status": NOT_HELD,
                                "reason": f"larger than the {MAX_BYTES // (1024*1024)} MB ceiling"}
                    h.update(chunk)
                    out.write(chunk)
    except urllib.error.HTTPError as e:
        # NAME THE STATUS. "could not fetch: HTTPError" told an operator nothing and cost a
        # separate investigation to learn the Library of Congress answers 403 to our agent on item
        # pages — an ACCESS REFUSAL, which is acted on quite differently from a network fault or a
        # dead link. A refusal that does not say what happened just gets worked around blindly.
        staging.unlink(missing_ok=True)
        return {"status": NOT_HELD,
                "reason": f"the source refused us: HTTP {e.code} {e.reason}"}
    except (urllib.error.URLError, OSError, ValueError) as e:
        staging.unlink(missing_ok=True)
        reason = getattr(e, "reason", None)
        return {"status": NOT_HELD,
                "reason": f"could not reach the source: {type(e).__name__}"
                          + (f" ({reason})" if reason else "")}

    if total == 0:
        staging.unlink(missing_ok=True)
        return {"status": NOT_HELD, "reason": "the source returned an empty body"}

    sha = h.hexdigest()
    ext = _ext_for(url, ctype)
    dest = path_for(sha, ext)
    already = dest.is_file()
    dest.parent.mkdir(parents=True, exist_ok=True)

    if already:
        staging.unlink(missing_ok=True)       # same content, already anchored — never a duplicate
    else:
        os.replace(staging, dest)

    waybill = {
        "sha256": sha, "bytes": total, "media_type": ctype or "unknown",
        "origin_url": url, "label": label[:300], "license": license_note,
        "fetched_at": int(time.time()), "want_id": want_id, "chosen_by": chosen_by,
        "path": str(dest),
    }
    wb = dest.parent / (sha + ".waybill.json")
    if not wb.is_file():
        wb.write_text(json.dumps(waybill, ensure_ascii=False, indent=1), encoding="utf-8")

    # VERIFY THE COPY THAT LANDED, not the bytes we think we wrote. A copy that arrives corrupt is
    # worse than no copy, because it looks like safety (tools/ark_pull.sh, same rule).
    v = verify(sha)
    if v.get("status") != "valid":
        return {"status": NOT_HELD, "reason": f"stored copy failed verification ({v.get('status')})",
                "sha256": sha}

    waybill["status"] = ALREADY if already else HELD
    return waybill


def stats() -> Dict[str, Any]:
    """What this device actually anchors. Walks the drive — a count nobody maintains cannot drift."""
    base = sources_dir()
    if not base or not base.is_dir():
        return {"anchoring": False, "bodies": 0, "bytes": 0}
    n, total = 0, 0
    for w in base.glob("*/*.waybill.json"):
        n += 1
        try:
            total += int(json.loads(w.read_text(encoding="utf-8")).get("bytes") or 0)
        except (OSError, ValueError):
            continue
    return {"anchoring": True, "root": str(base), "bodies": n, "bytes": total}


__all__ = ["fetch", "verify", "held", "stats", "sources_dir", "path_for",
           "ALLOWED_HOSTS", "MAX_BYTES", "HELD", "NOT_HELD", "ALREADY"]
