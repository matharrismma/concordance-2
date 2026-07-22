"""The Apothecary — living with the land, the old way, kept honestly.

Herb monographs revived verbatim from 1.0: traditional uses, preparations, growing
instructions, safety notes, and evidence verdicts. The practical application of knowledge
hard fought — we are always relearning, so this shelf only ever grows.

Three disciplines:

* **Found, never generated.** Every monograph is data on disk. Search ranks; it never writes.
* **Safety and evidence travel with every entry.** A remedy without its cautions and its
  honest verdict (SUPPORTED / MIXED / TRADITIONAL) is not knowledge, it is a rumor.
* **Anyone may offer wisdom; nobody publishes it but the keeper.** Proposals land in a queue
  on disk and never surface anywhere until curated by hand. The same rule as
  `recall.for_the_group`: a candidate list, not an action.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_WORD = re.compile(r"[A-Za-z][A-Za-z'-]{1,}")


def _data_dir() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base)


def _monographs_path() -> Path:
    """CONCORDANCE_HERBS overrides (tests point it at the repo data); else the data dir.
    Resolved at call time — under one pytest process the shared data-dir env belongs to
    whichever test file imported last, so nothing here may be captured at import."""
    env = os.environ.get("CONCORDANCE_HERBS", "").strip()
    if env:
        return Path(env)
    return _data_dir() / "herbs" / "monographs.jsonl"


def _load() -> List[Dict[str, Any]]:
    path = _monographs_path()
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _brief(h: Dict[str, Any]) -> Dict[str, Any]:
    """The list row: enough to choose by, never enough to misuse by — safety comes with it."""
    return {"id": h.get("id"), "name": h.get("name"),
            "scientific_name": h.get("scientific_name"),
            "summary": h.get("summary", ""),
            "traditional_uses": (h.get("traditional_uses") or [])[:3],
            "safety_notes": (h.get("safety_notes") or [])[:1]}


def browse() -> Dict[str, Any]:
    herbs = _load()
    return {"ok": True, "total": len(herbs),
            "herbs": [_brief(h) for h in sorted(herbs, key=lambda x: x.get("name", ""))],
            "note": ("Traditional knowledge with its evidence verdicts and safety notes — "
                     "found and kept, never generated. Not medical advice.")}


def get(herb_id: str) -> Dict[str, Any]:
    for h in _load():
        if h.get("id") == herb_id:
            return {"ok": True, "herb": h}
    return {"ok": False, "error": "no such monograph"}


def search(q: str, limit: int = 8) -> Dict[str, Any]:
    """Rank by where the words land: name outranks use, use outranks the long text.
    Deterministic — same query, same order, every time."""
    # the ways people name the same trouble — folded to the monographs' own words
    folds = {"anxious": "anxiety", "worried": "anxiety", "worry": "anxiety",
             "sleepless": "sleep", "insomnia": "sleep", "stressed": "anxiety",
             "sick": "nausea", "queasy": "nausea", "stomachache": "digestion",
             "cough": "throat", "grow": "planting", "garden": "planting"}
    terms = [folds.get(w.lower(), w.lower()) for w in _WORD.findall(q or "")]
    if not terms:
        return {"ok": True, "query": q or "", "results": []}
    def wordset(text: str) -> set:
        return {w.lower() for w in _WORD.findall(text)}

    def hit(term: str, words: set) -> bool:
        # a person searches "sleeping"; the monograph says "sleep". Stems meet in the middle —
        # either word may extend the other, requiring 4 shared letters so "tea" != "teaching".
        if term in words:
            return True
        return any((len(w) >= 4 and term.startswith(w)) or (len(term) >= 4 and w.startswith(term))
                   for w in words)

    scored = []
    for h in _load():
        name = wordset(h.get("name", "") + " " + h.get("scientific_name", "") + " "
                       + " ".join(h.get("common_names") or []))
        uses = wordset(" ".join((h.get("traditional_uses") or [])
                                + [v.get("claim", "") for v in (h.get("evidence_verdicts") or [])]))
        body = wordset(" ".join([h.get("summary", ""), h.get("growing", "")]
                                + (h.get("preparations") or []) + (h.get("safety_notes") or [])))
        score = sum(12 for t in terms if hit(t, name)) \
            + sum(4 for t in terms if hit(t, uses)) \
            + sum(1 for t in terms if hit(t, body))
        if score:
            scored.append((score, h.get("name", ""), h))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return {"ok": True, "query": q,
            "results": [_brief(h) for _s, _n, h in scored[:limit]]}


def propose(text: str, name: str = "", kind: str = "") -> Dict[str, Any]:
    """Offer wisdom to the shelf. It is WRITTEN, never published: the queue is a file the
    keeper reads, and nothing in it surfaces on any endpoint until curated by hand."""
    body = (text or "").strip()
    if not body:
        return {"ok": False, "error": "nothing offered"}
    if len(body) > 8000:
        return {"ok": False, "error": "too long — offer it in pieces"}
    qdir = _data_dir() / "apothecary_proposals"
    qdir.mkdir(parents=True, exist_ok=True)
    entry = {"at": time.time(), "name": (name or "").strip()[:80],
             "kind": (kind or "").strip()[:40] or "remedy", "text": body}
    with open(qdir / "proposals.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"ok": True,
            "note": ("Received, with thanks. Offered wisdom goes to the keeper for curation — "
                     "what has stood the test of time joins the shelf; nothing publishes "
                     "itself.")}
