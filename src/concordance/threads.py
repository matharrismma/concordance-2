"""Threads — the Deck: a conversation as a continuous, resumable chain.

Matt's keystone: "It needs to be a continuous chain. We should never feel like we started
over. It's one conversation. We pick up whatever thread you pull. Our job is to find the
correct conversation and to keep good notes so we can be accurate. Our card system creates
a deck."

Each exchange (the user's text + the conduit's found/verified/cited response) is appended to
a thread record as an ordered, hash-chained entry — the same content-addressed, tamper-evident
discipline the seal ledger uses, applied to a conversation. A thread is a DECK you pull from:
resume any thread by id, and (F3) search past conversations to find the right one.

CONDUIT, NOT MEMORY-THAT-GENERATES: every kept exchange is the VERBATIM user text plus the
EXACT dict ask.respond() already returned (its note / scripture / verify seal / results).
Nothing is summarized or regenerated — the deck keeps good notes so the engine can be
accurate; it never invents them. A composed/generated turn (if that fork ever opens) must be
stored with generated=True and never presented as a found note.

Sovereign: stdlib only. The store mirrors cas.py's sharded layout; appends are serialized by a
store-level lock (mirroring receipts._LEDGER_LOCK) so concurrent requests cannot fork a thread's
chain. The store is LOCAL/PRIVATE (gitignored) and is NEVER auto-sealed to the public ledger —
any verified answer inside an exchange was already redacted + sealed by receipts.mint at
verify-time, so no PII enters the permanent public chain.

Storage layout:
    <base>/<thread_id[:2]>/<thread_id[2:]>.json
Environment:
    CONCORDANCE_THREADS_DIR — override the store path
    CONCORDANCE_DATA_DIR    — parent for the default path (<data>/threads)
"""
from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import validate

SCHEMA = "concordance/thread/v1"

# thread ids are hex tokens (secrets.token_hex) — validate so a client-held id can never
# escape the store dir (no path traversal) and stays a clean shard key.
_ID_RE = re.compile(r"[a-f0-9]{8,64}\Z")

# Appending is read-then-write (load thread, append exchange, recompute head, write). Serialize
# it within the process so concurrent /ask requests cannot fork a thread's chain — exactly the
# hazard receipts._LEDGER_LOCK guards for the seal ledger (ThreadingHTTPServer is one process).
_THREADS_LOCK = threading.Lock()


def _valid_id(thread_id: Any) -> bool:
    return isinstance(thread_id, str) and bool(_ID_RE.match(thread_id))


def _threads_dir() -> Path:
    env = os.environ.get("CONCORDANCE_THREADS_DIR", "").strip()
    if env:
        return Path(env)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    if data:
        return Path(data) / "threads"
    return Path("data") / "threads"


def _path(base: Path, thread_id: str) -> Path:
    return base / thread_id[:2] / f"{thread_id[2:]}.json"


def _now() -> float:
    return round(time.time(), 3)


def _new_record(thread_id: str, surface: str = "secular") -> Dict[str, Any]:
    now = _now()
    return {"schema": SCHEMA, "thread_id": thread_id,
            "surface": surface if surface in ("secular", "witness") else "secular",
            "created_at": now, "updated_at": now, "title": "", "exchanges": [], "head_hash": ""}


def _exchange_hash(ex: Dict[str, Any]) -> str:
    """Content hash of an exchange, excluding its own hash — the per-thread chain link.
    Uses the ONE canonicalizer (validate.content_hash, ensure_ascii=False) so witness-surface
    Greek/Hebrew hashes identically everywhere, same as the seal floor."""
    return validate.content_hash(ex, exclude=("hash",))


def _write(rec: Dict[str, Any]) -> None:
    base = _threads_dir()
    p = _path(base, rec["thread_id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(validate.canonical_json_bytes(rec))  # same canonical form as the seal floor


def new_thread(surface: str = "secular", title: str = "") -> Dict[str, Any]:
    """Mint a fresh, empty deck and persist it. Returns the record (with its thread_id)."""
    rec = _new_record(secrets.token_hex(16), surface)
    if title:
        rec["title"] = str(title)[:80]
    _write(rec)
    return rec


def get(thread_id: str) -> Optional[Dict[str, Any]]:
    """Load a deck by id, or None if absent/unreadable/invalid-id."""
    if not _valid_id(thread_id):
        return None
    p = _path(_threads_dir(), thread_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def append(thread_id: str, user_text: str, response: Any, *,
           surface: str = "secular", generated: bool = False) -> Dict[str, Any]:
    """Append an exchange to a deck (creating it if a valid client-held id is unknown to this
    box — so a browser-held id always keeps working). Returns the new exchange.

    The exchange is the VERBATIM user text + the EXACT response dict — the note, not a summary.
    Raises ValueError on an invalid thread_id (never touches the filesystem with it)."""
    if not _valid_id(thread_id):
        raise ValueError("invalid thread_id")
    with _THREADS_LOCK:
        rec = get(thread_id) or _new_record(thread_id, surface)
        exchanges = rec.get("exchanges", [])
        kind = ""
        if isinstance(response, dict):
            kind = str(response.get("kind", ""))
            generated = bool(response.get("generated", generated))
        ex = {
            "seq": len(exchanges),
            "at": _now(),
            "kind": kind,
            "user": user_text or "",
            "response": response if isinstance(response, dict) else {"value": response},
            "generated": bool(generated),
            "prev_hash": rec.get("head_hash", ""),
        }
        ex["hash"] = _exchange_hash(ex)
        exchanges.append(ex)
        rec["exchanges"] = exchanges
        rec["head_hash"] = ex["hash"]
        rec["updated_at"] = ex["at"]
        if not rec.get("title") and (user_text or "").strip():
            rec["title"] = user_text.strip()[:80]
        _write(rec)
        return ex


def list_threads(limit: int = 50) -> List[Dict[str, Any]]:
    """Recent decks, newest first — briefs for a 'your conversations' list."""
    base = _threads_dir()
    out: List[Dict[str, Any]] = []
    if not base.exists():
        return out
    for prefix in base.iterdir():
        if not prefix.is_dir() or len(prefix.name) != 2:
            continue
        for f in prefix.glob("*.json"):
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            out.append({"thread_id": rec.get("thread_id"),
                        "title": rec.get("title") or "(untitled)",
                        "updated_at": rec.get("updated_at", 0),
                        "created_at": rec.get("created_at", 0),
                        "exchanges": len(rec.get("exchanges", [])),
                        "surface": rec.get("surface")})
    out.sort(key=lambda r: r.get("updated_at", 0), reverse=True)
    return out[:max(1, int(limit))]


def verify_thread(thread_id: str) -> Tuple[bool, str]:
    """Walk a deck's chain: each exchange's prev_hash must match the prior link and its hash
    must recompute — the conversation's own 'hands a receipt' proof (nothing was edited)."""
    rec = get(thread_id)
    if rec is None:
        return False, f"not found: {thread_id}"
    prev = ""
    exchanges = rec.get("exchanges", [])
    for i, ex in enumerate(exchanges):
        if ex.get("prev_hash", "") != prev:
            return False, f"chain broken at seq {i}: prev_hash does not match prior link"
        if ex.get("hash", "") != _exchange_hash(ex):
            return False, f"tamper at seq {i}: exchange hash does not recompute"
        prev = ex.get("hash", "")
    if rec.get("head_hash", "") != prev:
        return False, "head_hash does not match the last exchange"
    return True, f"ok ({len(exchanges)} exchanges)"


def delete(thread_id: str) -> bool:
    """Forget a deck entirely (right-to-be-forgotten). Returns True if it existed."""
    if not _valid_id(thread_id):
        return False
    p = _path(_threads_dir(), thread_id)
    if not p.exists():
        return False
    p.unlink()
    return True


def prune(max_age_days: Optional[float] = None, keep_per_surface: Optional[int] = None) -> int:
    """Deck hygiene: drop decks older than max_age_days and/or keep only the newest
    keep_per_surface per surface. Returns the number removed. (Operator/retention policy.)"""
    removed = 0
    if max_age_days is not None:
        cutoff = time.time() - float(max_age_days) * 86400.0
        for t in list_threads(limit=10 ** 9):
            if t.get("updated_at", 0) < cutoff and delete(t["thread_id"]):
                removed += 1
    if keep_per_surface is not None:
        from collections import defaultdict
        by_surface: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
        for t in list_threads(limit=10 ** 9):
            by_surface[t.get("surface")].append(t)
        for ts in by_surface.values():
            ts.sort(key=lambda r: r.get("updated_at", 0), reverse=True)
            for t in ts[max(0, int(keep_per_surface)):]:
                if delete(t["thread_id"]):
                    removed += 1
    return removed


# ── exchange-cards: the deck as searchable cards (feeds F3's threads-Corpus) ──────────────

def _exchange_card(rec: Dict[str, Any], ex: Dict[str, Any]) -> Dict[str, Any]:
    """Shape one exchange as a corpus-style card so corpus.Corpus can rank it unchanged —
    the same IDF ranker already trusted for the keeping now finds past conversations too."""
    tid = rec.get("thread_id")
    return {"id": f"ex_{tid}_{ex.get('seq')}", "kind": "exchange", "shelf": "threads",
            "title": (ex.get("user") or "")[:80] or "(exchange)",
            "body": ex.get("user") or "",
            "bands": [tid, ex.get("kind") or ""],
            "surface": rec.get("surface") or "secular",
            "thread_id": tid, "seq": ex.get("seq"), "at": ex.get("at")}


def all_cards() -> Dict[str, Dict[str, Any]]:
    """Every exchange across every deck, as id -> card. Built for corpus.Corpus(...) search."""
    cards: Dict[str, Dict[str, Any]] = {}
    base = _threads_dir()
    if not base.exists():
        return cards
    for prefix in base.iterdir():
        if not prefix.is_dir() or len(prefix.name) != 2:
            continue
        for f in prefix.glob("*.json"):
            try:
                rec = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for ex in rec.get("exchanges", []):
                c = _exchange_card(rec, ex)
                cards[c["id"]] = c
    return cards


# ── search across past conversations (F3) ─────────────────────────────────────────────────

_WORD = re.compile(r"[a-z0-9][a-z0-9']+")


def search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Find the right PAST CONVERSATION to pull. A personal deck is small (unlike the ~11k-card
    keeping), so distinctiveness-IDF is the wrong tool — it returns nothing until you have many
    threads. This is a direct token-overlap + substring match over exchanges, robust from the
    very FIRST conversation, deduped to threads and ranked. O(exchanges) per call — cheap on a
    Pi/LoRa base station; revisit with an index only if a single deck ever grows huge."""
    q = (query or "").strip().lower()
    if not q:
        return []
    qtokens = set(_WORD.findall(q))
    best: Dict[str, Dict[str, Any]] = {}
    for c in all_cards().values():
        text = (c.get("body") or "").lower()
        score = len(qtokens & set(_WORD.findall(text))) * 2
        if q in text:
            score += 3  # a phrase/substring hit beats scattered token overlap
        if score <= 0:
            continue
        tid = c.get("thread_id")
        if tid and (tid not in best or score > best[tid]["_score"]):
            best[tid] = {"_score": score, "match": (c.get("body") or c.get("title") or "")[:120]}
    out: List[Dict[str, Any]] = []
    for tid, info in sorted(best.items(), key=lambda kv: -kv[1]["_score"]):
        rec = get(tid)
        if rec is None:
            continue
        out.append({"thread_id": tid, "title": rec.get("title") or "(untitled)",
                    "updated_at": rec.get("updated_at", 0), "surface": rec.get("surface"),
                    "exchanges": len(rec.get("exchanges", [])), "match": info["match"]})
        if len(out) >= max(1, int(limit)):
            break
    return out


__all__ = ["new_thread", "get", "append", "list_threads", "verify_thread",
           "delete", "prune", "all_cards", "search", "SCHEMA"]
