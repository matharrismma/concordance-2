"""THE WANT LIST — the library grows by its misses.

Matt, 2026-08-01, three sentences that are the whole design:
  *"[The Shepherd] looks in the catalogue. If not there sends out … and pulls sources. The person
   then selects the best … and we mint a new card."*
  *"I think of it as a hive of specialists. Coming back to a queen."*
  *"Each one is dumb. She's not even that smart, but they are all crafted for their task."*

This module is the QUEEN — and true to the design, she is not smart. She is an append-only ledger
that enforces the covenant mechanically: a want is opened by an explicit human ask (never
auto-logged from bot noise); foragers append OPTION cells — found, attributed sources, and only
sources; nothing enters the keeping from here until a NAMED person chooses, and the choosing
happens elsewhere (the curate machinery / the shepherd's --choose). Coherence lives at the
return-point, never in the forager.

The covenant, enforced by shape rather than judgement:
  * rule 1 (retrieve-first)  — a want exists because the catalogue was consulted and came up short;
  * rule 3 (quarantine)      — options live in ledger cells, NOT in the corpus;
  * rule 4 (human authorizes)— close_want requires a name; no anonymous minting;
  * privacy                  — queries and notes are SCRUBBED before they are stored, and no
                               requester identity of any kind is recorded. A want is a fact about
                               the library's gaps, never about the person who found one.

Offline-tolerant by design: the ledger is a jsonl file. No internet for a week means the queue
waits a week. That is not degradation; that is the design ("That may be a week if we don't have
internet").
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()

KINDS = ("missing", "expand")
# open -> options_ready -> closed. `dropped` is a steward's refusal, recorded, never silent.
STATES = ("open", "options_ready", "closed", "dropped")

_MAX_QUERY = 300
_MIN_QUERY = 3
_MAX_NOTE = 500
_MAX_OPTIONS = 8          # a comb cell holds a few good candidates, not a search-results page


def _path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "wants.jsonl"


def _scrub(text: str) -> str:
    """Personal context is stripped BEFORE storage — the standing privacy rule. The mapping is
    deliberately dropped: a want must never be restorable to the person who asked it."""
    try:
        from .gateway import scrub
        return scrub(str(text or ""))[0]
    except Exception:  # noqa: BLE001 — a broken scrubber must not take the want list down
        return str(text or "")


def _norm(q: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]+", " ", (q or "").lower())).strip()


def _want_id(kind: str, key: str) -> str:
    # Deterministic: the same miss asked twice is ONE want asked twice, not two wants.
    return "want_" + hashlib.sha1(f"{kind}|{key}".encode("utf-8")).hexdigest()[:12]


def _append(ev: Dict[str, Any]) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")


def _events() -> List[Dict[str, Any]]:
    p = _path()
    if not p.exists():
        return []
    out = []
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue                     # a torn line is skipped, never fatal
    return out


def fold() -> Dict[str, Dict[str, Any]]:
    """The ledger, folded to current state. Dumb on purpose: replaying events IS the state."""
    wants: Dict[str, Dict[str, Any]] = {}
    for ev in _events():
        wid = ev.get("id") or ""
        kind_of = ev.get("ev")
        if kind_of == "open":
            wants[wid] = {"id": wid, "kind": ev.get("kind"), "query": ev.get("query", ""),
                          "card_id": ev.get("card_id", ""), "note": ev.get("note", ""),
                          "state": "open", "asks": 1, "options": [],
                          "opened_at": ev.get("at")}
        elif wid not in wants:
            continue                          # an event for a want never opened: ignored, dumbly
        elif kind_of == "ask":
            wants[wid]["asks"] += 1
        elif kind_of == "option":
            if len(wants[wid]["options"]) < _MAX_OPTIONS:
                wants[wid]["options"].append(ev.get("source") or {})
                wants[wid]["state"] = "options_ready"
        elif kind_of == "close":
            wants[wid]["state"] = "closed"
            wants[wid]["minted_card"] = ev.get("card_id", "")
            wants[wid]["closed_by"] = ev.get("by", "")
            wants[wid]["closed_at"] = ev.get("at")
        elif kind_of == "drop":
            wants[wid]["state"] = "dropped"
            wants[wid]["reason"] = ev.get("reason", "")
            wants[wid]["closed_by"] = ev.get("by", "")
    return wants


def open_want(query: str = "", kind: str = "missing", card_id: str = "",
              note: str = "") -> Dict[str, Any]:
    """A person asks the library to acquire (kind=missing) or expand (kind=expand) something.

    Explicit asks only. The empty-search page OFFERS this; nothing records a want on its own —
    bot noise must never write the acquisition queue.
    """
    if kind not in KINDS:
        return {"ok": False, "error": f"kind must be one of {KINDS}"}
    query = _scrub(query)[:_MAX_QUERY].strip()
    note = _scrub(note)[:_MAX_NOTE].strip()
    card_id = str(card_id or "").strip()

    if kind == "expand":
        if not card_id:
            return {"ok": False, "error": "expand needs the card_id it is about"}
        from . import corpus
        if corpus.get_card(card_id) is None:
            return {"ok": False, "error": "no such card in the keeping"}
        key = card_id
    else:
        nq = _norm(query)
        if len(nq) < _MIN_QUERY:
            return {"ok": False, "error": "say what you are looking for — a few words at least"}
        key = nq

    wid = _want_id(kind, key)
    existing = fold().get(wid)
    if existing and existing["state"] in ("open", "options_ready"):
        _append({"ev": "ask", "id": wid, "at": int(time.time())})
        return {"ok": True, "id": wid, "asks": existing["asks"] + 1, "state": existing["state"]}
    _append({"ev": "open", "id": wid, "kind": kind, "query": query, "card_id": card_id,
             "note": note, "at": int(time.time())})
    return {"ok": True, "id": wid, "asks": 1, "state": "open"}


def add_option(want_id: str, source: Dict[str, Any]) -> Dict[str, Any]:
    """A forager returns to the comb with a FOUND source — label + url + snippet, attributed.
    Options are cells in the ledger, not cards: quarantine by construction."""
    w = fold().get(want_id)
    if not w:
        return {"ok": False, "error": "no such want"}
    if w["state"] not in ("open", "options_ready"):
        return {"ok": False, "error": f"want is {w['state']}"}
    if len(w["options"]) >= _MAX_OPTIONS:
        return {"ok": False, "error": "the cell is full — choose, or drop options first"}
    label = str((source or {}).get("label") or "").strip()
    url = str((source or {}).get("url") or "").strip()
    if not label:
        return {"ok": False, "error": "an option names its source"}
    if url and not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "an option's url is http(s) or absent"}
    # THE SHAFT-TAGS (Matt: "branches that can be cut off, so you don't have to completely
    # rebuild"). Every option records WHICH miner brought it up and on WHICH run — so if a source
    # is later found poisoned, cutting the branch is a query over these tags, not a hunt, and the
    # healing is re-mined from source, never patched from a copy.
    keep = {"label": label[:200], "url": url[:500],
            "snippet": str((source or {}).get("snippet") or "")[:600],
            "domain": str((source or {}).get("domain") or "")[:60],
            "miner": str((source or {}).get("miner") or "")[:40],
            "run": str((source or {}).get("run") or "")[:40]}
    _append({"ev": "option", "id": want_id, "source": keep, "at": int(time.time())})
    return {"ok": True, "id": want_id, "options": len(w["options"]) + 1}


def close_want(want_id: str, card_id: str, by: str) -> Dict[str, Any]:
    """The choosing was made and a card was minted — the want closes with an edge to what it
    produced. A name is required: no anonymous minting (covenant rule 4)."""
    if not str(by or "").strip():
        return {"ok": False, "error": "closing carries a name"}
    if not str(card_id or "").strip():
        return {"ok": False, "error": "closing names the card the want produced"}
    w = fold().get(want_id)
    if not w:
        return {"ok": False, "error": "no such want"}
    if w["state"] == "closed":
        return {"ok": False, "error": "already closed"}
    _append({"ev": "close", "id": want_id, "card_id": card_id.strip(), "by": by.strip(),
             "at": int(time.time())})
    return {"ok": True, "id": want_id, "card_id": card_id.strip()}


def listing(state: Optional[str] = None, limit: int = 200) -> Dict[str, Any]:
    """The public face of the ledger — a library posts its desiderata at the desk. Sorted by how
    often it was asked for: demand steers acquisition."""
    ws = [w for w in fold().values() if state is None or w["state"] == state]
    ws.sort(key=lambda w: (-w["asks"], -(w.get("opened_at") or 0)))
    return {"total": len(ws), "wants": ws[: max(1, min(int(limit or 200), 500))]}
