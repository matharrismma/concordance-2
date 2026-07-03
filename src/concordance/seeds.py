"""Seeds of the Word — the Areopagus / logos spermatikos mining pass.

Paul's own method at Athens (Acts 17:16-34): grieved by the idols, he recognized the genuine seeking,
found the altar TO AN UNKNOWN GOD, named the Source ("what you worship in ignorance, this I proclaim"),
MINED the pagan poets *attributed* (17:28, Epimenides & Aratus), turned the seed AGAINST the idol
(17:29), and pointed to Christ and the resurrection (17:30-31) — accepting a mixed harvest (17:32-34).

This module is a curated, ATTRIBUTED keeping of such seeds — NOT a generator. The engine does not
"discern" a seed with an LLM (that would be generation, and a dependency we refuse); it keeps what has
already been identified and vetted, names each source verbatim, and points each toward Christ. Every
seed is rated CONCORDANT — a SIGNPOST, NEVER HOLDS: religious/experiential material is never sealed as
math. The discriminator is Christ (1 John 4:1-3; 1 Thess 5:21). This is mining and refining, never
syncretism: the true ore is kept, the idol is named and refused, and the fragment is a signpost TO the
Gate — never the Gate itself.

Store: the vetted starter seeds live in-code (_SEEDS), where they are reviewed; additional seeds may be
kept in data/seeds/seeds.jsonl (gitignored, same record shape) and are loaded if present.
Env: CONCORDANCE_SEEDS_DIR / CONCORDANCE_DATA_DIR.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

NOTE = ("A signpost, not a proof — CONCORDANT, never HOLDS. Found + attributed; the idol is named and "
        "refused, the Source is named: Jesus Christ (Acts 17:23; 1 John 4:1-3). Not syncretism — the "
        "seed is kept, the error rejected; the fragment points to the Gate, it is never the Gate.")

# Paul's Areopagus sequence — the method every seed is mined by (Acts 17:16-34).
METHOD: List[Dict[str, str]] = [
    {"step": "grieve", "ref": "Acts 17:16", "do": "Be grieved by the idols — mine with sorrow at the counterfeit, never approval of it."},
    {"step": "recognize", "ref": "Acts 17:22-23", "do": "Recognize the genuine seeking; find the altar TO AN UNKNOWN GOD — real reaching for the true God, unnamed."},
    {"step": "name", "ref": "Acts 17:23", "do": "Name the Source: 'What you worship in ignorance, this I proclaim to you.'"},
    {"step": "mine", "ref": "Acts 17:28", "do": "Mine the true fragment, attributed verbatim to its source (Paul quotes Epimenides and Aratus)."},
    {"step": "turn", "ref": "Acts 17:29", "do": "Turn the seed AGAINST the idol — the light corrects the darkness (we are His offspring, so He is not a gold image)."},
    {"step": "point", "ref": "Acts 17:30-31", "do": "Point to Christ and the resurrection — the Gate, and the call to repent."},
    {"step": "release", "ref": "Acts 17:32-34", "do": "Accept the mixed harvest — some mock, some defer, some believe. Faithful proclamation; the yield is God's."},
]

# Vetted starter seeds — those Paul himself and the early fathers (Justin's logos spermatikos, Clement,
# Augustine) actually mined. Rock-solid and defensible; the corpus is meant to grow under curation.
_SEEDS: List[Dict[str, Any]] = [
    {
        "id": "epimenides-in-him-we-live",
        "fragment": "In him we live and move and have our being.",
        "source": "Epimenides of Crete, Cretica (~6th c. BC) — quoted by Paul, Acts 17:28",
        "tradition": "Greek (Cretan)",
        "rating": "CONCORDANT",
        "concordance": [
            {"ref": "Acts 17:28", "text": "For in him we live, move, and have our being."},
            {"ref": "Colossians 1:17", "text": "He is before all things, and in him all things are held together."},
            {"ref": "Psalm 139:7-8", "text": "Where could I go from your Spirit?... If I make my bed in Sheol, behold, you are there!"},
        ],
        "refuse": "Epimenides said it of Zeus (arguing Zeus was not dead). The sentence is true; the name was false. Refuse the idol Zeus — the living God is not a Cretan deity.",
        "turn_to_christ": "The One 'not far,' in whom all things actually subsist, is the Logos in whom all things hold together (Col 1:17) — the unknown god Paul then names: Jesus Christ. (Paul mines Epimenides again in Titus 1:12.)",
    },
    {
        "id": "aratus-his-offspring",
        "fragment": "For we are also his offspring.",
        "source": "Aratus, Phaenomena (~3rd c. BC); also Cleanthes' Hymn to Zeus — quoted by Paul, Acts 17:28",
        "tradition": "Greek (Stoic)",
        "rating": "CONCORDANT",
        "concordance": [
            {"ref": "Acts 17:28-29", "text": "'For we are also his offspring.' Being then the offspring of God, we ought not to think that the Divine Nature is like gold, or silver, or stone."},
            {"ref": "Genesis 1:27", "text": "God created man in his own image."},
            {"ref": "Luke 3:38", "text": "...the son of Adam, the son of God."},
        ],
        "refuse": "Aratus opens 'Let us begin with Zeus' — the kinship was ascribed to Zeus. Keep the truth of our divine origin; refuse the idol; and it is not a warrant for making God into an image (17:29).",
        "turn_to_christ": "We are His offspring by creation (Gen 1:27) — and adopted as sons in the Son (Galatians 4:4-6; Romans 8:14-16). The kinship is real, named and fulfilled in Christ.",
    },
    {
        "id": "plato-the-good-beyond-being",
        "fragment": "The Good is beyond being — the source of being and of knowing, as the sun is the source of light and sight.",
        "source": "Plato, Republic VI (the sun analogy), ~380 BC — mined by Justin Martyr and Augustine (logos spermatikos)",
        "tradition": "Greek (Platonic)",
        "rating": "CONCORDANT",
        "concordance": [
            {"ref": "John 1:9", "text": "The true light that enlightens everyone was coming into the world."},
            {"ref": "1 John 1:5", "text": "God is light, and in him is no darkness at all."},
            {"ref": "James 1:17", "text": "...the Father of lights, with whom can be no variation, nor turning shadow."},
        ],
        "refuse": "Plato's Good is impersonal, and his system carries real error — a demiurge who is not Creator, pre-existent matter, transmigration, and a disdain for the body. Keep the seed of a transcendent source of being and light; refuse the impersonal, dualist frame.",
        "turn_to_christ": "The 'Good beyond being' that gives being and light is a Person — God who IS light (1 John 1:5), and the Logos who is the true Light enlightening everyone (John 1:9), who took a body He did not disdain.",
    },
]

_EXTRA: List[Dict[str, Any]] = []
_MTIME: float = 0.0


def _file() -> Path:
    env = os.environ.get("CONCORDANCE_SEEDS_DIR", "").strip()
    if env:
        return Path(env) / "seeds.jsonl"
    data = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return (Path(data) if data else Path("data")) / "seeds" / "seeds.jsonl"


def _load() -> List[Dict[str, Any]]:
    """The vetted in-code seeds, plus any curated extras from the gitignored JSONL store."""
    global _EXTRA, _MTIME
    p = _file()
    if not p.exists():
        return _SEEDS + _EXTRA
    mtime = p.stat().st_mtime
    if _EXTRA and mtime == _MTIME:
        return _SEEDS + _EXTRA
    out: List[Dict[str, Any]] = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        return _SEEDS + _EXTRA
    _EXTRA, _MTIME = out, mtime
    return _SEEDS + _EXTRA


def _brief(r: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": r.get("id"), "fragment": r.get("fragment"), "source": r.get("source"),
            "tradition": r.get("tradition"), "rating": r.get("rating", "CONCORDANT")}


def method() -> Dict[str, Any]:
    """Paul's Areopagus sequence — how every seed is mined and held."""
    return {"method": "Areopagus (Acts 17:16-34)", "steps": METHOD, "note": NOTE}


def list_seeds(tradition: str = "") -> Dict[str, Any]:
    """Brief of every kept seed; optionally filtered by tradition."""
    t = (tradition or "").strip().lower()
    items = [_brief(r) for r in _load() if not t or t in str(r.get("tradition", "")).lower()]
    return {"total": len(items), "note": NOTE, "method": "Areopagus (Acts 17)", "seeds": items}


def get(seed_id: str) -> Optional[Dict[str, Any]]:
    """One full seed: the fragment (attributed), what it concords with, the idol refused, the turn to Christ."""
    key = (seed_id or "").strip().lower()
    for r in _load():
        if str(r.get("id", "")).lower() == key:
            out = dict(r)
            out["rating"] = r.get("rating", "CONCORDANT")
            out["note"] = NOTE
            return out
    return None


def search(q: str, limit: int = 20) -> Dict[str, Any]:
    """Find seeds by fragment / source / tradition / the Christ-pointing."""
    needle = (q or "").strip().lower()
    out = []
    for r in _load():
        hay = " ".join([r.get("fragment", ""), r.get("source", ""), r.get("tradition", ""),
                        r.get("turn_to_christ", "")]).lower()
        if not needle or needle in hay:
            out.append(_brief(r))
        if len(out) >= max(1, int(limit)):
            break
    return {"query": q, "total": len(out), "note": NOTE, "seeds": out}


__all__ = ["list_seeds", "get", "search", "method", "METHOD", "NOTE"]
