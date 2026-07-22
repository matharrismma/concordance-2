"""Distill — a thread's memory is an INDEX, not a summary.

The problem this solves: a conversation that never resets eventually outgrows anything that
reads it in one gulp. The usual fix is to summarise the old turns — but summarising is
*generating*, and generation is the one thing this engine does not do (docs/THE_COMPANION.md
§3.2a). A summary is also lossy in the worst way: it silently decides what mattered, and the
original is no longer what gets read.

So instead of compressing the past, we **index** it:

  - `digest(thread_id)` — a deterministic account of what a thread contains: what was verified
    and sealed, what Scripture it cited, which words recur, when it started and last moved,
    whether the chain is intact. Every number is counted, not judged.
  - `recall(thread_id, query)` — retrieval INTO the chain, returning the actual exchanges,
    verbatim, with the reason each matched.

Nothing is ever lost to a summary: the hash chain remains the truth, and the digest is only a
finding aid over it. This is the same concordance principle the whole engine runs on — index
and concord, never author — turned on your own conversation.

No model. No generation. Every field below is arithmetic over text that already exists.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from . import threads
from .ask import _REF, _STRONGS

# Deliberately small and explicit — a stopword list is an editorial choice, so it is visible
# here rather than hidden in a library.
_STOP = {
    "the", "and", "for", "that", "this", "with", "what", "when", "where", "which", "who", "how",
    "you", "your", "yours", "are", "was", "were", "have", "has", "had", "not", "but", "can",
    "did", "does", "from", "into", "its", "it's", "about", "there", "their", "them", "they",
    "then", "than", "will", "would", "should", "could", "been", "being", "get", "got", "just",
    "like", "more", "most", "some", "any", "all", "one", "two", "out", "off", "own", "why",
    "our", "ours", "his", "her", "hers", "him", "she", "they're", "i'm", "i've", "don't",
}
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]{2,}")


def _text_of(ex: Dict[str, Any]) -> str:
    """Everything readable in an exchange — the user's words and the response's."""
    parts = [str(ex.get("user") or "")]
    resp = ex.get("response")
    if isinstance(resp, dict):
        for k in ("message", "text", "note", "value", "title"):
            v = resp.get(k)
            if isinstance(v, str):
                parts.append(v)
        for k in ("results", "items", "scripture", "sources"):
            v = resp.get(k)
            if isinstance(v, list):
                for item in v[:20]:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict):
                        for kk in ("title", "text", "label", "ref"):
                            if isinstance(item.get(kk), str):
                                parts.append(item[kk])
    return "  ".join(parts)


def _seal_of(ex: Dict[str, Any]) -> Optional[str]:
    """A re-checkable receipt, if this exchange produced one."""
    resp = ex.get("response")
    if not isinstance(resp, dict):
        return None
    seal = resp.get("seal")
    if isinstance(seal, dict):
        return seal.get("cite_url") or seal.get("content_hash")
    return resp.get("cite_url")


def _counts(pairs: List[str], limit: int) -> List[Tuple[str, int]]:
    tally: Dict[str, int] = {}
    for p in pairs:
        tally[p] = tally.get(p, 0) + 1
    # deterministic: by count desc, then alphabetically — never by dict order
    return sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]


def digest(thread_id: str, *, terms: int = 12) -> Dict[str, Any]:
    """A deterministic index of a thread. Counted, never judged; no model, no generation."""
    rec = threads.get(thread_id)
    if not rec:
        return {"ok": False, "error": "no such thread"}
    exs: List[Dict[str, Any]] = rec.get("exchanges", []) or []

    kinds: Dict[str, int] = {}
    sealed: List[Dict[str, Any]] = []
    refs: List[str] = []
    strongs: List[str] = []
    words: List[str] = []
    generated = 0

    for ex in exs:
        k = str(ex.get("kind") or "unknown")
        kinds[k] = kinds.get(k, 0) + 1
        if ex.get("generated"):
            generated += 1
        s = _seal_of(ex)
        if s:
            sealed.append({"seq": ex.get("seq"), "seal": s})
        blob = _text_of(ex)
        refs += [m.group(0).strip() for m in _REF.finditer(blob)]
        strongs += [m.group(1).upper() for m in _STRONGS.finditer(blob)]
        words += [w.lower() for w in _WORD.findall(str(ex.get("user") or ""))]

    # Chain linkage: each exchange must point at the one before it.
    chain_ok = True
    prev = ""
    for ex in exs:
        if ex.get("prev_hash", "") != prev:
            chain_ok = False
            break
        prev = ex.get("hash", "")

    first, last = (exs[0] if exs else None), (exs[-1] if exs else None)
    return {
        "ok": True,
        "thread_id": rec.get("thread_id"),
        "title": rec.get("title") or "",
        "exchanges": len(exs),
        "first_at": (first or {}).get("at"),
        "last_at": (last or {}).get("at"),
        "kinds": dict(sorted(kinds.items())),
        "generated": generated,          # honesty metric: this engine generates nothing, so 0
        "sealed": sealed,                # the re-checkable receipts this thread produced
        "scripture_refs": _counts(refs, 20),
        "strongs": _counts(strongs, 20),
        "recurring_terms": [t for t in _counts([w for w in words if w not in _STOP], terms)],
        "head_hash": rec.get("head_hash", ""),
        "chain_ok": chain_ok,
        "note": "an index, not a summary — nothing was compressed away; recall() returns the exchanges themselves",
    }


def recall(thread_id: str, query: str, *, limit: int = 5) -> Dict[str, Any]:
    """Retrieval INTO the chain: the actual exchanges, verbatim, and why each matched.

    This is what replaces 'summarise the old turns'. The past is retrieved, not rewritten.
    """
    rec = threads.get(thread_id)
    if not rec:
        return {"ok": False, "error": "no such thread"}
    terms = [w.lower() for w in _WORD.findall(query or "") if w.lower() not in _STOP]
    if not terms:
        return {"ok": True, "thread_id": thread_id, "query": query or "", "matches": [],
                "note": "no searchable terms in the query"}

    scored: List[Tuple[int, int, Dict[str, Any]]] = []
    for ex in rec.get("exchanges", []) or []:
        blob = _text_of(ex).lower()
        hits = {t: blob.count(t) for t in terms if t in blob}
        if not hits:
            continue
        # score: distinct terms matched first, then total occurrences — both deterministic
        scored.append((len(hits), sum(hits.values()),
                       {"seq": ex.get("seq"), "at": ex.get("at"), "kind": ex.get("kind"),
                        "user": ex.get("user"), "hash": ex.get("hash"),
                        "matched": sorted(hits)}))
    # ties break by most recent, so the ordering is total and stable
    scored.sort(key=lambda s: (-s[0], -s[1], -(s[2].get("seq") or 0)))
    return {"ok": True, "thread_id": thread_id, "query": query or "",
            "matches": [m for _d, _t, m in scored[:limit]],
            "searched": len(rec.get("exchanges", []) or []),
            "note": "the exchanges themselves, verbatim — nothing summarised"}
