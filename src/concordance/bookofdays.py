"""The Book of Days — it learns you across time, and you own every line of it.

"Learning you" normally means *inferring* things about a person and keeping them somewhere
they cannot see. This does the opposite, for the same reason the rest of the engine refuses to
generate: an inference you cannot read is a claim made about you behind your back.

So the Book is **written by you and indexed by us**. Exactly two kinds of entry exist:

  - `note`    — what you recorded, stored **verbatim**. Never rewritten, never "improved".
  - `derived` — a plain pointer taken from `distill.digest()`: a Scripture reference you keep
                returning to, a seal you produced, a word that recurs. It carries
                `derived_from` so you can see precisely what produced it, and it can be
                deleted like anything else. **Nothing is inferred beyond what is already
                countable in your own chain.**

The promises, kept literally:
  - **readable**    — plain JSON, your words, no encoding games.
  - **correctable** — `amend()` keeps the prior text visible in `history`; a correction is a
                      record, not an erasure.
  - **exportable**  — `export()` returns everything in one object, to put on your drive.
  - **deletable**   — `forget()` is a **hard delete**. The entry is removed and its text is
                      gone from the file. No tombstone that quietly keeps the content.

Bound to the key from `binding.py`: only the holder of the drive can read or write it. No
model, no generation — every field here is your text or arithmetic over your own chain.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA = "bookofdays/1"


def _dir() -> Path:
    env = os.environ.get("CONCORDANCE_BOOK_DIR", "").strip()
    if env:
        return Path(env)
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    if data:
        return Path(data) / "bookofdays"
    return Path("data") / "bookofdays"


def _path(owner: str) -> Path:
    return _dir() / f"{owner}.json"


def _now() -> float:
    return round(time.time(), 3)


def _load(owner: str) -> Dict[str, Any]:
    try:
        return json.loads(_path(owner).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"schema": SCHEMA, "owner": owner, "entries": [], "created_at": _now()}


def _save(rec: Dict[str, Any]) -> None:
    p = _path(rec["owner"])
    p.parent.mkdir(parents=True, exist_ok=True)
    rec["updated_at"] = _now()
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")


def write(owner: str, text: str, *, links: Optional[List[str]] = None) -> Dict[str, Any]:
    """Record something in your own words. Stored VERBATIM — never rewritten."""
    text = text if isinstance(text, str) else ""
    if not text.strip():
        return {"ok": False, "error": "nothing to record"}
    rec = _load(owner)
    entry = {"id": secrets.token_hex(6), "at": _now(), "kind": "note",
             "text": text,                      # verbatim, exactly as given
             "links": list(links or []), "history": []}
    rec["entries"].append(entry)
    _save(rec)
    return {"ok": True, "entry": entry}


def derive(owner: str, thread_id: str, *, top: int = 5) -> Dict[str, Any]:
    """Add plainly-derived pointers from a thread's digest. Labelled, sourced, deletable.

    Nothing is inferred: every entry below is something already countable in your own chain.
    """
    from . import distill
    d = distill.digest(thread_id)
    if not d.get("ok"):
        return {"ok": False, "error": d.get("error", "no such thread")}

    rec = _load(owner)
    seen = {(e.get("derived_from") or {}).get("fact") for e in rec["entries"]}
    added: List[Dict[str, Any]] = []

    def _add(fact: str, text: str) -> None:
        if fact in seen:
            return                                   # never duplicate a derived pointer
        entry = {"id": secrets.token_hex(6), "at": _now(), "kind": "derived",
                 "text": text, "links": [],
                 "derived_from": {"thread_id": thread_id, "fact": fact,
                                  "how": "counted in your own chain by distill.digest()"},
                 "history": []}
        rec["entries"].append(entry)
        seen.add(fact)
        added.append(entry)

    for ref, n in (d.get("scripture_refs") or [])[:top]:
        _add(f"ref:{thread_id}:{ref}", f"You returned to {ref} ({n}×) in this conversation.")
    for s, n in (d.get("strongs") or [])[:top]:
        _add(f"strongs:{thread_id}:{s}", f"You studied {s} ({n}×) in this conversation.")
    for seal in (d.get("sealed") or [])[:top]:
        _add(f"seal:{thread_id}:{seal.get('seq')}",
             f"You produced a re-checkable seal: {seal.get('seal')}")

    if added:
        _save(rec)
    return {"ok": True, "added": added, "count": len(added),
            "note": "derived pointers only — nothing inferred beyond what is countable in your chain"}


def entries(owner: str, *, limit: int = 100, kind: str = "") -> Dict[str, Any]:
    """Read your Book. Plain, in the order you wrote it."""
    rec = _load(owner)
    out = rec.get("entries", [])
    if kind:
        out = [e for e in out if e.get("kind") == kind]
    return {"ok": True, "owner": owner, "count": len(out), "entries": out[-max(1, limit):]}


def amend(owner: str, entry_id: str, text: str) -> Dict[str, Any]:
    """Correct an entry. The prior text stays visible in `history` — a record, not an erasure."""
    if not isinstance(text, str) or not text.strip():
        return {"ok": False, "error": "nothing to record"}
    rec = _load(owner)
    for e in rec.get("entries", []):
        if e.get("id") == entry_id:
            e.setdefault("history", []).append({"at": e.get("at"), "text": e.get("text")})
            e["text"] = text
            e["at"] = _now()
            _save(rec)
            return {"ok": True, "entry": e}
    return {"ok": False, "error": "no such entry"}


def forget(owner: str, entry_id: str) -> Dict[str, Any]:
    """Delete an entry — really. Removed from the file, text and corrections and all."""
    rec = _load(owner)
    before = len(rec.get("entries", []))
    rec["entries"] = [e for e in rec.get("entries", []) if e.get("id") != entry_id]
    if len(rec["entries"]) == before:
        return {"ok": False, "error": "no such entry"}
    _save(rec)
    return {"ok": True, "forgotten": entry_id,
            "note": "hard delete — the text is gone from the file, not tombstoned"}


def export(owner: str) -> Dict[str, Any]:
    """Everything, in one object, to carry away on your drive."""
    rec = _load(owner)
    return {"ok": True, "schema": SCHEMA, "owner": owner,
            "entries": rec.get("entries", []),
            "created_at": rec.get("created_at"), "updated_at": rec.get("updated_at"),
            "note": "this is the whole Book — copy it to your drive; we keep no other copy of it"}
