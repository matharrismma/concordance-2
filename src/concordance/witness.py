"""Witness — the CLOUD OF WITNESSES' actual words. Public-domain witnesses voiced beside the lens.

`mentors.py` NAMES the cloud — each wise man's SUBJECT, GIFT (the true fragment he saw), and DISCERN note
(how to weigh it). This holds their VERBATIM WORDS, but only where their work is PUBLIC DOMAIN: the FAR
witnesses' own voices around the NEAR witness (Matt's writing, `lens.py`). *"Since we are surrounded by so
great a cloud of witnesses… let us run… looking to Jesus"* (Heb 12:1–2) — the cloud surrounds; Christ is
the finish.

The strict-PD gate is STRUCTURAL here, applied at the moment of voicing, not only at the door: a passage is
voiced only if it is marked public domain. A copyrighted witness is characterized in `mentors.py` (his way
of seeing), never voiced here (his text) — the same line the lens and the license-guard hold. Every passage
is his VERBATIM words, attributed to witness + work + reference, and carries its SOURCE and the provenance
that earned its PD standing (published pre-1929, or author's death + life+70 elapsed). It proposes a way of
seeing; the gate and the Word dispose — never confirmed past what it earned. Nothing is generated: the voice
is the witness's because it IS his, gathered verbatim, never imitated.

The corpus is PLUGGABLE and living, gathered by `tools/gather_witness.py` (Ellen G. White first). Today a
seed — an empty or small corpus — and the layer honestly voices nothing where a witness is not yet gathered;
tomorrow the cloud. Unlike the lens (Matt's private writing, never published), a PD witness's text MAY be
published, because it is already the commons. Stdlib only, offline.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

_STOP = {"the", "a", "an", "to", "of", "and", "or", "is", "it", "in", "on", "for", "with", "that",
         "this", "as", "at", "by", "be", "are", "was", "were", "he", "she", "they", "we", "you", "i",
         "his", "her", "their", "our", "my", "me", "not", "no", "but", "so", "if", "than", "then"}


def _tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(w) > 2 and w not in _STOP}


def _corpus_path() -> str:
    """Where the witness corpus lives — PD witnesses' gathered words. Overridable as the cloud grows."""
    return os.environ.get("CONCORDANCE_WITNESSES", "").strip() or "data/witnesses.jsonl"


def _is_pd(row: Dict[str, Any]) -> bool:
    """The strict-PD gate, structural: a passage is voiced ONLY if it is truly public domain. Fail-closed —
    anything not explicitly marked public domain is held back to characterization, never voiced."""
    return row.get("public_domain") is True


# Load-once cache, keyed by (path, mtime). The cloud grows from a seed (279 passages) toward whole works
# (the fathers, reformers, founders — tens of thousands of paragraphs); re-reading and re-parsing the
# whole file on EVERY /witness call was fine at the seed and a real cost at scale. The file changes only
# when the gatherer appends, so cache the parsed rows and re-read only when the mtime moves.
_CACHE: Dict[str, Any] = {"path": None, "mtime": None, "rows": None}


def load(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load the witness corpus, admitting ONLY public-domain passages with real text. A non-PD or textless
    row is dropped at the door — the gate holds before anything can be voiced. Returns [] if not yet
    gathered: an honest empty cloud, never a fabricated one. Cached by (path, mtime)."""
    p = path or _corpus_path()
    try:
        mtime = os.path.getmtime(p) if os.path.exists(p) else None
    except OSError:
        mtime = None
    if _CACHE["path"] == p and _CACHE["mtime"] == mtime and _CACHE["rows"] is not None:
        return _CACHE["rows"]
    out: List[Dict[str, Any]] = []
    if mtime is not None:
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                if _is_pd(row) and str(row.get("text") or "").strip():
                    out.append(row)
    _CACHE.update(path=p, mtime=mtime, rows=out)
    return out


def _framed(row: Dict[str, Any]) -> Dict[str, Any]:
    return {"text": row.get("text"), "witness": row.get("witness"), "work": row.get("work"),
            "ref": row.get("ref"), "id": row.get("id"), "source": row.get("source")}


def _body(corpus: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """The passages available to voice — the gate applied even to an injected corpus (defense in depth)."""
    src = corpus if corpus is not None else load()
    return [p for p in src if _is_pd(p) and str(p.get("text") or "").strip()]


def see(text: str, *, witness: Optional[str] = None, corpus: Optional[List[Dict[str, Any]]] = None,
        k: int = 3) -> Dict[str, Any]:
    """Propose the WITNESS PASSAGES that most frame `text` — their VERBATIM words, attributed, optionally
    scoped to one witness. Ranked by shared subject words. Only public-domain text is ever voiced; the
    result is honestly empty where the cloud does not yet reach. Proposes; never confirms."""
    q = _tokens(text)
    want = (witness or "").strip().lower()
    body = [p for p in _body(corpus) if not want or want in str(p.get("witness") or "").lower()]
    scored = []
    for i, p in enumerate(body):
        overlap = len(q & _tokens((p.get("text") or "") + " " + (p.get("work") or "")
                                  + " " + (p.get("witness") or "")))
        if overlap:
            scored.append((overlap, -i, p))
    scored.sort(key=lambda x: (-x[0], x[1]))
    seeing = [_framed(p) for _o, _i, p in scored[:max(1, int(k))]]
    return {
        "seeing": seeing,                       # the witnesses' verbatim words that frame this
        "proposes": True, "confirms": False,    # the cloud proposes; the gate and the Word dispose
        "gathered": len(body),                  # how much of the cloud can yet be seen through (scoped)
        "note": ("the cloud proposes how these witnesses frame this — their verbatim words, attributed, "
                 "public-domain, never a verdict" if seeing else
                 "no witness gathered reaches this yet — the cloud is still being gathered (map as we go)"),
    }


def voice(text: str, *, witness: Optional[str] = None,
          corpus: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """VOICE — frame the answer with a witness's OWN words. Selects the single public-domain passage that
    most frames `text` (optionally from one witness) and returns it verbatim, attributed with its source.
    Nothing is generated: the witness's voice is his because it IS his, never imitated. Honest empty where
    the cloud does not reach. Proposes; never confirms."""
    seen = see(text, witness=witness, corpus=corpus, k=1)
    top = seen["seeing"][0] if seen["seeing"] else None
    return {
        "frame": (top["text"] if top else None),          # the witness's verbatim words to lead with — or None
        "witness": (top["witness"] if top else None),
        "work": (top["work"] if top else None),
        "ref": (top["ref"] if top else None),
        "id": (top["id"] if top else None),
        "source": (top["source"] if top else None),
        "verbatim": bool(top), "generated": False,         # gathered, never authored in a witness's register
        "proposes": True, "confirms": False,
        "gathered": seen["gathered"],
        "note": ("a witness's own words frame this — verbatim, attributed, public-domain, never imitated"
                 if top else
                 "no gathered witness reaches this yet — the answer stands on its own, in no imitated voice"),
    }


def witnesses(*, corpus: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """The witnesses whose actual words have been gathered into the cloud (public-domain only), sorted."""
    return sorted({str(p.get("witness") or "").strip() for p in _body(corpus) if p.get("witness")})


def available(witness: Optional[str] = None) -> bool:
    """True if any public-domain witness words (optionally a given witness's) have been gathered yet."""
    ws = witnesses()
    if not ws:
        return False
    want = (witness or "").strip().lower()
    return (not want) or any(want in w.lower() for w in ws)


__all__ = ["see", "voice", "load", "witnesses", "available"]
