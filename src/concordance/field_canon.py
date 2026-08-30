"""The canon — the field library's kept map: a subject -> the tried-and-true source that answers it.

Matt, 2026-08-30: "Refine the concept of find. Recraft it to perfectly fit the system instead of
trying to rework the system for find." — and, naming the planes: "This is also how we build feeds
from youtube for .tv." … "Library of Congress."

WHY THIS EXISTS. `find` used to gamble: strip a question to a guess-word, throw it at the outside
catalogues, and keep a result only if a returned *title* happened to share a word. It hit for five
hand-wired subjects and went dark for the rest, so the keeping barely grew (44 bodies, ever). That is
positive-matching over an outside catalogue — the exact opposite of what the engine does everywhere
else: ELIMINATE over a KEPT substrate, be a conduit to primary sources, search once, keep forever.

The canon is that kept substrate for FINDING. It is a curated map from a subject to the ANCHORING
public-domain / openly-licensed source that answers it — Langstroth for bees, a Soap-Maker's manual
for soap — each entry a real, openable source. `find` navigates the canon by elimination FIRST
(deterministic, no gamble); only a subject the canon does not yet hold falls through to the archive
reach, and every reach that WINS is promoted back into the canon, so that subject is never gambled
again. The reach stops being the method and becomes the tortoise's fallback that feeds the canon.

ONE MECHANISM, MANY PLANES ([[everything connects on planes]]). The text plane's sources are books
(Project Gutenberg / Internet Archive / Library of Congress) kept as cards; the VIDEO plane's sources
are openly-licensed programmes (Internet Archive moving-image and the Library of Congress film
collections, both public-domain; YouTube under a Creative-Commons filter where a key is present),
kept as .tv channels. Same canon shape, same search-once, same gate. The Curator's museum is the
video keeping — its automatons testify with real matched words, never impersonate.

HOW IT IS KEPT. Seeded IN CODE (like find's shelf spines: tracked, present on a fresh box, carried
offline) and GROWN at runtime into `data/canon.jsonl` by `promote`. The two are unioned at lookup —
the code seed is the floor, the runtime file the growth. Scoring is pure (no I/O); the only I/O is
reading and appending the runtime file. Nothing here fetches or renders; it only says WHERE the
anchoring source is. The fetch → ark → craft chain and the gate downstream are unchanged, so a canon
source is still born quarantined and still passes the gate before it reaches anyone.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_WORD = re.compile(r"[a-z]{3,}")
# The same content-word floor `find` uses, so a subject reads the same on both sides of the seam.
_STOP = frozenset((
    "the", "a", "an", "of", "to", "in", "is", "are", "was", "were", "do", "does", "did", "how",
    "what", "why", "who", "when", "where", "which", "that", "this", "it", "for", "and", "or", "on",
    "at", "by", "with", "about", "i", "you", "my", "me", "we", "can", "tell", "explain", "mean",
    "means", "old", "new", "so", "if", "be", "from", "into", "there", "here", "your", "our", "want",
    "need", "get", "getting", "some", "any", "best", "way", "ways", "good",
    # generic craft-VERBS are not subjects: 'keeping poultry' and 'keeping bees' both carry 'keeping',
    # which let a bee ask reach the poultry book. The distinctive noun ('bee', 'poultry') carries the
    # subject; the verb is noise. (Real craft-nouns — cure, dry, smoke, tan, forge, preserve — stay.)
    "keep", "keeping", "make", "making", "raise", "raising", "build", "building", "grow", "growing",
    "use", "using", "do", "doing", "start", "starting", "home"))

PLANES = ("text", "video")


def _norm(s: str) -> set:
    """Content tokens, crudely singularised and hyphen-flattened so a subject matches however it is
    phrased: 'honeybees' ~ 'honey-bee' ~ 'bees', 'candles' ~ 'candle'. Deliberately generous — the
    gate downstream is what proves a source, so finding errs toward reaching the right shelf."""
    toks = set()
    for w in _WORD.findall((s or "").lower().replace("-", " ")):
        if w in _STOP:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]                    # bees -> bee, candles -> candle (not 'glass' -> 'glas')
        toks.add(w)
    return toks


def _score(qtoks: set, etoks: set) -> int:
    """How well a query matches a canon entry's terms. A shared content word counts double; a
    compound bridge ('honeybee' contains 'bee') counts once — enough to reach the shelf, never
    enough to drown a direct hit. Zero means no relation: the entry is not returned at all."""
    if not qtoks or not etoks:
        return 0
    direct = len(qtoks & etoks)
    bridge = 0
    for q in qtoks:
        if q in etoks:
            continue
        for e in etoks:
            if len(q) >= 4 and len(e) >= 4 and (q in e or e in q):
                bridge += 1
                break
    return direct * 2 + bridge


# ── the seed: curated, VERIFIED public-domain anchors (the floor) ────────────────────────────
# Each entry names the subject, the match `terms` (generously phrased), the plane, and the openable
# source. Every `url` here was verified against the live catalogue when it was added on TWO bars, not
# one: on-topic AND OPENABLE — sources.resolve_text_url must return a real _djvu.txt (a lending-only
# scan, e.g. a Better-World-Books "bwb_" item, has no public full text and cards NOTHING, so it is
# not an anchor however on-topic its title). A stale url is a lie to the reader ([[a stale read is a
# lie]]), so an unverified subject is simply LEFT OUT and left to the reach + promotion to fill. Text-plane sources
# are books the craft chain can open (a Gutenberg ebook page or an archive.org details page); video
# sources are programme pages the .tv frame airs. This list is the floor, not the ceiling: it is
# meant to grow itself from real family misses via `promote`, not to be hand-stuffed to completeness.
def _ia(ident: str, title: str, year: str) -> Dict[str, Any]:
    """An Internet Archive details page — the shape find's own provider returns, so the craft chain
    opens it unchanged. Every id here was returned live by archive.org's search when it was added."""
    return {"title": title, "url": "https://archive.org/details/" + ident,
            "source": "Internet Archive", "license": "Public domain (verify per item)", "year": year}


_SEED: List[Dict[str, Any]] = [
    # Ten verified public-domain anchors for the subjects families reach for first — each id returned
    # live by archive.org on 2026-08-30. The floor, not the ceiling: soap, canning, bread, sewing,
    # tanning and the rest are left DARK on purpose, for the reach + promotion to fill from real asks.
    {"subject": "beekeeping", "plane": "text", "kind": "practical",
     "terms": "bee bees beekeeping honeybee honeybees beehive hive honey apiary apiculture langstroth",
     "source": _ia("everystepinbeek00douggoog", "Every Step in Beekeeping: A Book for Amateurs", "1921")},
    {"subject": "keeping poultry", "plane": "text", "kind": "practical",
     "terms": "poultry chicken chickens hen hens fowl egg eggs coop henhouse",
     "source": _ia("openairpoultryho00wood", "Open-air poultry houses for all climates", "1912")},
    {"subject": "blacksmithing", "plane": "text", "kind": "practical",
     "terms": "blacksmith blacksmithing forge forging anvil ironwork steel metalwork",
     "source": _ia("forgepracticehea00bacorich", "Forge-practice and heat treatment of steel", "1919")},
    {"subject": "carpentry", "plane": "text", "kind": "practical",
     "terms": "carpentry carpenter joinery woodworking woodwork cabinetmaking framing",
     "source": _ia("cassellscarpentr00hasl", "Cassell's carpentry and joinery", "1907")},
    {"subject": "cheese making", "plane": "text", "kind": "practical",
     "terms": "cheese cheesemaking curd rennet dairy",
     "source": _ia("cheesemakingbook00samm", "Cheese making: a book for practical cheesemakers", "1918")},
    {"subject": "curing and smoking meat", "plane": "text", "kind": "practical",
     "terms": "meat curing cure sausage smoking smoke butcher butchering pork ham bacon salting",
     "source": _ia("secretsofmeatcur00bhelrich", "Secrets of meat curing and sausage making", "1922")},
    {"subject": "vegetable gardening", "plane": "text", "kind": "practical",
     "terms": "garden gardening vegetable vegetables planting soil crops victory horticulture",
     "source": _ia("VictoryGardenLeadersHandbook", "Victory Garden Leader's Handbook", "1943")},
    {"subject": "herbal remedies", "plane": "text", "kind": "practical",
     "terms": "herb herbs herbal remedy remedies medicinal medicine plants simples",
     "source": _ia("meyer-1934-natures-remedies", "Nature's Remedies", "1934")},
    {"subject": "drying and preserving food", "plane": "text", "kind": "practical",
     "terms": "dry drying dehydrate dehydrating preserve preserving food fruit fruits vegetables",
     "source": _ia("dehydratingfoods00andr", "Dehydrating foods: fruits, vegetables", "1920")},
    {"subject": "first aid", "plane": "text", "kind": "practical",
     "terms": "first aid injury injuries wound wounds bleeding emergency bandage bandaging rescue",
     "source": _ia("americannational00lync", "American National Red Cross text-book on First Aid", "1908")},
]


def _prep(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Precompute the match tokens for an entry (terms + subject), once, at load."""
    e = dict(entry)
    e["_toks"] = _norm((entry.get("terms") or "") + " " + (entry.get("subject") or ""))
    return e


_SEED_PREP = [_prep(e) for e in _SEED]


# ── the runtime growth: data/canon.jsonl (promotions) ────────────────────────────────────────
def _runtime_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "canon.jsonl"


def _load_runtime() -> List[Dict[str, Any]]:
    p = _runtime_path()
    out: List[Dict[str, Any]] = []
    try:
        if not p.exists():
            return out
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                out.append(_prep(json.loads(ln)))
            except ValueError:
                continue
    except OSError:
        return out
    return out


def _as_doc(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Shape a canon entry as a provider `doc` — the same shape `find`'s providers return, so a canon
    hit drops into the existing candidate/craft chain with no new plumbing. Marked `via='canon'` for
    provenance and so a promotion never re-promotes a source already in the canon."""
    src = dict(entry.get("source") or {})
    src.setdefault("tier", "primary")
    src["via"] = "canon"
    src["_subject"] = entry.get("subject", "")
    src["_plane"] = entry.get("plane", "text")
    return src


def lookup(query: str, plane: str = "text", limit: int = 3) -> List[Dict[str, Any]]:
    """The anchoring source(s) the canon holds for this subject on this plane, best first — or an
    empty list if the canon does not yet hold it (then the reach runs). Pure but for the runtime
    read; deterministic; never raises into the caller."""
    try:
        qtoks = _norm(query)
        if not qtoks:
            return []
        scored: List[tuple] = []
        for e in _SEED_PREP + _load_runtime():
            if (e.get("plane") or "text") != plane:
                continue
            s = _score(qtoks, e.get("_toks") or set())
            if s > 0:
                scored.append((s, e))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [_as_doc(e) for _, e in scored[: max(1, limit)]]
    except Exception:  # noqa: BLE001 — a finding aid must never crash the answer path
        return []


def holds(query: str, plane: str = "text") -> bool:
    """Whether the canon already anchors this subject (used to decide if the reach is even needed)."""
    return bool(lookup(query, plane=plane, limit=1))


def promote(subject: str, doc: Dict[str, Any], plane: str = "text",
            terms: str = "") -> bool:
    """Keep a source the reach WON so the subject is never gambled again — search once, keep forever.
    Appends one entry to the runtime canon, de-duplicated by url. A source already IN the canon (a
    canon hit that was carded) is not re-promoted. Returns True if it actually grew the canon."""
    try:
        url = (doc or {}).get("url") or ""
        if not url or (doc or {}).get("via") == "canon":
            return False
        subj = (subject or "").strip()
        if not subj:
            return False
        p = _runtime_path()
        seen = set()
        if p.exists():
            for ln in p.read_text(encoding="utf-8").splitlines():
                if ln.strip():
                    try:
                        seen.add((json.loads(ln).get("source") or {}).get("url"))
                    except ValueError:
                        pass
        if url in seen:
            return False
        entry = {
            "subject": subj,
            "terms": (terms or subj).strip(),
            "plane": plane if plane in PLANES else "text",
            "kind": doc.get("kind") or ("practical" if plane == "text" else "program"),
            "source": {k: v for k, v in doc.items() if not str(k).startswith("_")},
            "promoted_at": time.time(),
        }
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except Exception:  # noqa: BLE001
        return False


__all__ = ["lookup", "holds", "promote", "PLANES"]
