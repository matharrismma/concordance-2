"""FORAGE - search current theories and white papers across ALL domains (OpenAlex), to see whether a
theory already FITS an open want, or whether a STRUCTURE in one field answers a problem in another.

Found and CITED, never ingested. A paper is a CLAIM to verify, not sealed truth; the keeping stays
public-domain, and these are pointers the operator reads and brings back to the gate. Cross-domain by
construction: OpenAlex indexes every field, and each work carries its CONCEPTS (its domains), so a
structural match from another domain surfaces here with its home fields named. (Matt, 2026-10-11: "We need
a good source of white papers and current theories... cross reference all theories in all domains for a
structural fit.")
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from typing import Any, Dict, List, Optional

_UA = "NarrowHighway/1.0 (+https://narrowhighway.org; forage for open wants)"
_BASE = "https://api.openalex.org/works"


def _get(url: str, timeout: int = 12) -> Dict[str, Any]:
    mail = os.environ.get("OPENALEX_MAILTO", "").strip()
    if mail:
        url += ("&" if "?" in url else "?") + "mailto=" + urllib.parse.quote(mail)
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - fixed https host
        return json.load(r)


def _abstract(inv: Any, cap: int = 420) -> str:
    """OpenAlex stores the abstract as an inverted index {word: [positions]}; rebuild the prose."""
    if not isinstance(inv, dict):
        return ""
    words: List = []
    for w, ps in inv.items():
        for p in ps:
            words.append((p, w))
    words.sort()
    return " ".join(w for _, w in words)[:cap]


def _work(w: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": w.get("display_name"),
        "year": w.get("publication_year"),
        "authors": [(a.get("author") or {}).get("display_name") for a in (w.get("authorships") or [])[:4]],
        "domains": [c.get("display_name") for c in (w.get("concepts") or []) if (c.get("level") or 0) <= 1][:6],
        "cited_by": w.get("cited_by_count"),
        "link": w.get("doi") or w.get("id"),
        "abstract": _abstract(w.get("abstract_inverted_index")),
    }


def search(query: str, limit: int = 8) -> Dict[str, Any]:
    """Candidate theories across ALL domains for a query (or a want). Cited, never verified here."""
    q = (query or "").strip()
    if not q:
        return {"query": q, "count": 0, "candidates": [], "note": "give a query or an open want to forage"}
    limit = max(1, min(int(limit or 8), 25))
    url = _BASE + "?search=" + urllib.parse.quote(q) + "&per-page=" + str(limit)
    try:
        d = _get(url)
    except Exception as e:  # noqa: BLE001 - the forage source may be unreachable; say so, never crash
        return {"query": q, "count": 0, "candidates": [],
                "note": "the forage source could not be reached: " + str(e)[:140]}
    out = [_work(w) for w in (d.get("results") or [])]
    return {"query": q, "source": "OpenAlex (openalex.org) - open catalog of scholarly works, all domains",
            "total": (d.get("meta") or {}).get("count"), "count": len(out), "candidates": out,
            "note": ("Candidate theories, found and CITED across all domains - NOT verified. A paper is a "
                     "claim; the engine seals only what it can check. Each work's 'domains' are its fields. "
                     "Read the source; bring the checkable step to the gate.")}


def structural_fit(structure: str, limit: int = 12) -> Dict[str, Any]:
    """CROSS-REFERENCE ALL DOMAINS for a STRUCTURAL FIT. Search a domain-neutral description of a want's
    structure (e.g. 'a coercive monotone quantity controlling a nonlinear amplification term'); OpenAlex
    returns matches from every field, which we group BY DOMAIN so a fit from another discipline is seen.
    The structure is the agent's to phrase; the verifying is the engine's. Found and cited, never forged."""
    r = search(structure, limit=limit)
    cands = r.get("candidates") or []
    by_domain: Dict[str, int] = Counter()
    for c in cands:
        for dom in (c.get("domains") or []):
            by_domain[dom] += 1
    spread = sorted(by_domain.items(), key=lambda kv: (-kv[1], kv[0]))
    return {"structure": structure, "count": len(cands),
            "domains_touched": [{"domain": d, "hits": n} for d, n in spread],
            "candidates": cands, "source": r.get("source"),
            "note": ("A structure searched across all domains; the candidates are grouped by the fields they "
                     "live in, so a transfer from another discipline surfaces. Candidates to VERIFY, not "
                     "truths: the fit is a lead, confirmed only when the checkable step is sealed at the gate.")}
