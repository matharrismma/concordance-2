"""The tortoise — when the keeping does not hold it, go find it, surely.

Matt: "If we don't have an answer, we go search like a traditional tool… but we run it through our
tools prior to sharing. It may be slower, but our results meet a standard. We search for primary and
high quality — Library of Congress, and others. We don't claim to be the fastest. We are the surest.
We are the tortoise."

So this is not a web-scraper that hands back whatever a search engine says. It is a slow, sure path:

  1. Ask only PRIMARY / HIGH-QUALITY, openly-licensed sources — never arbitrary copyrighted pages
     (that would break the moat: [[strict PD-only]]). Today: the Library of Congress (primary
     documents, largely public domain) and Wikipedia (a high-quality reference, CC BY-SA — cacheable
     WITH attribution). The provider list is meant to grow (Gutenberg, government archives, OA
     scholarship) — always openly licensed, always attributed.
  2. Run the finding through OUR OWN TOOLS before we vouch for it (the Auditor extracts checkable
     claims and verifies them). We are good at telling what is false — so we frame by falsification:
     anything our checks break is flagged; what survives stands, labeled "not our verified keeping".
  3. Keep what we find. A card is minted (attributed, tiered `web_unverified`, carrying its check
     verdict) so next time the keeping already holds it — the tool fills its own gaps.

Sovereign and offline-first: this only runs when the keeping had no answer AND the network is
reachable; every failure degrades to the honest "I don't have that". Server-side (the query leaves
from the droplet, not the person's browser), bounded by a timeout, never stored beyond the card.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

_UA = "NarrowHighway/1.0 (+https://narrowhighway.com; sovereign verification)"
_TIMEOUT = 10
_WORD = re.compile(r"[a-z]{3,}")
_STOP = frozenset((
    "the", "a", "an", "of", "to", "in", "is", "are", "was", "were", "do", "does", "did", "how",
    "what", "why", "who", "when", "where", "which", "that", "this", "it", "for", "and", "or", "on",
    "at", "by", "with", "about", "i", "you", "my", "me", "we", "can", "tell", "explain", "mean",
    "means", "old", "new", "so", "if", "be", "from", "into", "there", "here"))


def enabled() -> bool:
    return os.environ.get("WEB_FIND_DISABLED", "").strip().lower() not in ("1", "true", "yes")


def _tokens(s: str) -> set:
    return {w for w in _WORD.findall((s or "").lower()) if w not in _STOP}


def _relevant(query: str, *texts: str) -> bool:
    """A finding is kept only if it actually shares a content word with what was asked — so the
    Library of Congress's tangential artifacts (a photo merely titled 'Speed of Light') are not
    passed off as an answer."""
    q = _tokens(query)
    if not q:
        return False
    hay = set()
    for t in texts:
        hay |= _tokens(t)
    return bool(q & hay)


def _get(url: str) -> Optional[str]:
    """Defensive GET — text or None. Never raises into the caller."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:   # noqa: S310 (trusted hosts only)
            return r.read().decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return None


# ── providers: openly-licensed, primary / high-quality only ─────────────────────────────────
def wikipedia(query: str) -> Optional[Dict[str, Any]]:
    """A high-quality reference summary (CC BY-SA 4.0), attributed and cacheable. The plain answer."""
    q = urllib.parse.quote(query)
    # full-text search (not opensearch, which only matches titles) — so a natural-language question
    # like "who invented the telephone" finds the right article
    raw = _get(f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=search"
               f"&srlimit=1&srprop=&srsearch={q}")
    if not raw:
        return None
    try:
        hits = (json.loads(raw).get("query") or {}).get("search") or []
        title = hits[0]["title"] if hits else None
    except (ValueError, KeyError, IndexError):
        return None
    if not title:
        return None
    s = _get("https://en.wikipedia.org/api/rest_v1/page/summary/"
             + urllib.parse.quote(title.replace(" ", "_")))
    if not s:
        return None
    try:
        d = json.loads(s)
    except ValueError:
        return None
    extract = (d.get("extract") or "").strip()
    if not extract or d.get("type") == "disambiguation":
        return None
    page = ((d.get("content_urls") or {}).get("desktop") or {}).get("page") \
        or ("https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")))
    return {"title": d.get("title") or title, "url": page, "extract": extract,
            "source": "Wikipedia", "license": "CC BY-SA 4.0", "tier": "reference"}


def library_of_congress(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Primary documents from the Library of Congress — largely public domain. Not an 'answer';
    the original sources to go deeper, attributed and linked."""
    q = urllib.parse.quote(query)
    raw = _get(f"https://www.loc.gov/search/?q={q}&fo=json&c={max(1, limit)}&at=results")
    if not raw:
        return []
    try:
        results = json.loads(raw).get("results") or []
    except ValueError:
        return []
    out = []
    for x in results[:limit]:
        title = (x.get("title") or "").strip()
        url = x.get("id") or x.get("url") or ""
        if not title or not url or not _relevant(query, title, " ".join(x.get("subject") or [])):
            continue
        fmt = x.get("original_format") or x.get("type") or []
        out.append({"title": title[:140], "url": url,
                    "format": (fmt[0] if isinstance(fmt, list) and fmt else str(fmt)),
                    "source": "Library of Congress", "license": "Public domain (mostly) — verify per item",
                    "tier": "primary"})
    return out


# ── the tortoise: find, check, keep ─────────────────────────────────────────────────────────
def _store_path():
    from pathlib import Path
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "web_cache.jsonl"


def _mint(query: str, answer: Dict[str, Any], checks: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Keep the finding so the keeping holds it next time — clearly tiered as web-sourced and
    UNVERIFIED (never masquerading as the verified keeping), carrying its check verdict."""
    try:
        url = answer.get("url") or ""
        cid = "card_web_" + hashlib.sha256((answer.get("source", "") + "|" + url).encode()).hexdigest()[:12]
        verdict = (checks or {}).get("verdict") or "UNCHECKED"
        broken = (checks or {}).get("broken_or_unchecked", 0)
        body = (answer.get("extract", "") + "\n\nSource: " + answer.get("source", "") + " — "
                + url + " (" + answer.get("license", "") + "). Open source, NOT the verified "
                "keeping. Our checks: " + verdict
                + (f" — {broken} claim(s) our tools could not confirm." if broken else "."))
        card = {"id": cid, "kind": "web", "title": answer.get("title", "")[:100], "body": body,
                "source": {"label": answer.get("source", "") + " (open web)", "url": url,
                           "license": answer.get("license", ""), "authority_tier": "web_unverified",
                           "checked": verdict},
                "shelf": "web", "box": "web_cache",
                "bands": ["web", "unverified", answer.get("source", "").lower()] + sorted(_tokens(query))[:6],
                "connections": [], "author": "web", "created_at": time.time(), "updated_at": time.time(),
                "visibility": "public", "lifecycle_stage": "public", "volatility": "cached",
                "surface": "secular", "generated": False, "verified": False}
        p = _store_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        existing = set()
        if p.exists():
            for ln in p.read_text(encoding="utf-8").splitlines():
                ln = ln.strip()
                if ln:
                    try:
                        existing.add(json.loads(ln).get("id"))
                    except ValueError:
                        pass
        if cid not in existing:
            with open(p, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(card, ensure_ascii=False) + "\n")
            try:
                from . import corpus as _c
                _c.add_to_default(card)
            except Exception:  # noqa: BLE001
                pass
        return card
    except Exception:  # noqa: BLE001
        return None


def find_and_check(query: str, config) -> Optional[Dict[str, Any]]:
    """The slow, sure path. Returns a framed answer (or None if nothing high-quality was found or
    the network was unreachable). Never raises."""
    if not enabled():
        return None
    try:
        answer = wikipedia(query)
        if answer and not _relevant(query, answer.get("title", ""), answer.get("extract", "")):
            answer = None
        docs = library_of_congress(query)
        if not answer and not docs:
            return None

        checks = {"verdict": "NOTHING_TO_CHECK"}
        framed = ""
        if answer:
            try:
                from . import audit as _audit
                checks = _audit.audit(answer["extract"], config, seal=False)
            except Exception:  # noqa: BLE001
                checks = {"verdict": "NOTHING_TO_CHECK", "results": []}
            broken = [r for r in (checks.get("results") or []) if r.get("status") != "CONFIRMED"]
            held = [r for r in (checks.get("results") or []) if r.get("status") == "CONFIRMED"]
            # we are good at telling what is false — so we lead with it
            if broken:
                framed = ("⚠ Our checks flag part of this as false or unconfirmed: "
                          + "; ".join((b.get("claim") or "")[:80] for b in broken[:2]))
            elif held:
                framed = (f"We checked {len(held)} claim(s) in this and they hold "
                          "(survived our verification — not the same as proven beyond all doubt).")
            else:
                framed = ("We could not independently check the specifics — treat it as an open "
                          "source, not our verified keeping.")
            _mint(query, answer, checks)

        return {
            "source_note": ("The keeping doesn't hold a verified answer for that. So we do the slow, "
                            "sure thing — search primary and high-quality sources, and run what we "
                            "find through our own checks. We are the tortoise, not the hare."),
            "answer": answer, "framed": framed, "checks_verdict": checks.get("verdict"),
            "documents": docs,
        }
    except Exception:  # noqa: BLE001
        return None
