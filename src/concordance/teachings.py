"""Phase 3 — the teaching-review workspace (the language tree, the Words in Red).

The Codex's own roadmap: when the grid (the math tree) is intact, turn to the WORDS OF JESUS.
This module is the SCAFFOLDING for that operator-led work — it does NOT do the review. It holds
the work queue (the teachings of Christ) and, for each, names the method. The workspace surface
assembles the frozen anchor (the original Greek + word-parts, via /original + /word_study) and the
existing sites (cards, cross-refs); the OPERATOR records the reading. The engine surfaces and
records; it never writes the reading. Tier 4 (any lens) never overrides Tier 1 (the Word).

The four-part method (per data/codex/TEACHINGS_OF_CHRIST_REVIEW.md), for each teaching:
  1. ORIGINAL GREEK + WORD-PARTS — the frozen anchor (auto-assembled from the scripture engine).
  2. THE TEACHING PLAINLY — what it says (operator).
  3. ITS WISDOM ON EVERY AXIS — the map's axes / domains (operator).
  4. ITS NESTING — to the existing structure, not a parallel one; the join (Col 1:17) is reserved.

Witness content: served on the witness surface (or once the Gate is opened in conversation).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from . import corpus

NOTE = ("God seeded wisdom across all of history; we only GATHER it and make its alignment to the Word "
        "visible. Nothing here is authored or generated — every fragment is FOUND across the body and "
        "ATTRIBUTED to its source. True wisdom always aligns to Scripture, because reality has one Source "
        "(Col 1:17); the concord is discovered, never imposed. Tier 1 (Words in Red) always wins; where a "
        "fragment carries error, the seed is kept and the error refused (the Areopagus method, Acts 17). "
        "The operator curates — keeps what aligns, refuses the idol — but never writes the wisdom.")

# The work queue — the teachings of Christ, grouped. Refs are the anchor; descriptors are factual,
# never interpretive. Sourced from the Codex teaching-review work-map.
_QUEUE: List[Dict[str, Any]] = [
    # ── The Sermon on the Mount (Matthew 5–7) — the spine ──
    {"id": "som_01", "group": "Sermon on the Mount", "title": "The Beatitudes", "ref": "Matthew 5:3-12"},
    {"id": "som_02", "group": "Sermon on the Mount", "title": "Salt and Light", "ref": "Matthew 5:13-16"},
    {"id": "som_03", "group": "Sermon on the Mount", "title": "Christ and the Law", "ref": "Matthew 5:17-20"},
    {"id": "som_04", "group": "Sermon on the Mount", "title": "Anger and reconciliation", "ref": "Matthew 5:21-26"},
    {"id": "som_05", "group": "Sermon on the Mount", "title": "Lust and the heart", "ref": "Matthew 5:27-30"},
    {"id": "som_06", "group": "Sermon on the Mount", "title": "Divorce", "ref": "Matthew 5:31-32"},
    {"id": "som_07", "group": "Sermon on the Mount", "title": "Oaths — let your Yes be Yes", "ref": "Matthew 5:33-37"},
    {"id": "som_08", "group": "Sermon on the Mount", "title": "Turn the other cheek", "ref": "Matthew 5:38-42"},
    {"id": "som_09", "group": "Sermon on the Mount", "title": "Love your enemies", "ref": "Matthew 5:43-48"},
    {"id": "som_10", "group": "Sermon on the Mount", "title": "Giving to the needy", "ref": "Matthew 6:1-4"},
    {"id": "som_11", "group": "Sermon on the Mount", "title": "The Lord's Prayer", "ref": "Matthew 6:5-15"},
    {"id": "som_12", "group": "Sermon on the Mount", "title": "Fasting", "ref": "Matthew 6:16-18"},
    {"id": "som_13", "group": "Sermon on the Mount", "title": "Treasures in heaven", "ref": "Matthew 6:19-24"},
    {"id": "som_14", "group": "Sermon on the Mount", "title": "Do not worry", "ref": "Matthew 6:25-34"},
    {"id": "som_15", "group": "Sermon on the Mount", "title": "Judging others — the plank", "ref": "Matthew 7:1-6"},
    {"id": "som_16", "group": "Sermon on the Mount", "title": "Ask, Seek, Knock — the Golden Rule", "ref": "Matthew 7:7-12"},
    {"id": "som_17", "group": "Sermon on the Mount", "title": "The Narrow Gate", "ref": "Matthew 7:13-14"},
    {"id": "som_18", "group": "Sermon on the Mount", "title": "A tree and its fruit", "ref": "Matthew 7:15-20"},
    {"id": "som_19", "group": "Sermon on the Mount", "title": "I never knew you", "ref": "Matthew 7:21-23"},
    {"id": "som_20", "group": "Sermon on the Mount", "title": "Build on the Rock", "ref": "Matthew 7:24-27"},
    # ── The Great Discourses (John 15 first — the load-bearing one) ──
    {"id": "disc_vine", "group": "The Discourses", "title": "The True Vine", "ref": "John 15:1-17"},
    {"id": "disc_shepherd", "group": "The Discourses", "title": "The Good Shepherd", "ref": "John 10:1-18"},
    {"id": "disc_bread", "group": "The Discourses", "title": "The Bread of Life", "ref": "John 6:35-59"},
    {"id": "disc_paraclete", "group": "The Discourses", "title": "The Farewell — the Paraclete", "ref": "John 14:1-31"},
    {"id": "disc_prayer", "group": "The Discourses", "title": "The High-Priestly Prayer", "ref": "John 17:1-26"},
    {"id": "disc_olivet", "group": "The Discourses", "title": "The Olivet Discourse", "ref": "Matthew 24:1-51"},
    # ── The seven "I AM" (ego eimi) sayings + the ground ──
    {"id": "iam_ground", "group": "The I AM Sayings", "title": "Before Abraham was, I AM", "ref": "John 8:58"},
    {"id": "iam_bread", "group": "The I AM Sayings", "title": "I am the Bread of Life", "ref": "John 6:35"},
    {"id": "iam_light", "group": "The I AM Sayings", "title": "I am the Light of the World", "ref": "John 8:12"},
    {"id": "iam_door", "group": "The I AM Sayings", "title": "I am the Door", "ref": "John 10:9"},
    {"id": "iam_shepherd", "group": "The I AM Sayings", "title": "I am the Good Shepherd", "ref": "John 10:11"},
    {"id": "iam_resurrection", "group": "The I AM Sayings", "title": "I am the Resurrection and the Life", "ref": "John 11:25"},
    {"id": "iam_way", "group": "The I AM Sayings", "title": "I am the Way, the Truth, and the Life", "ref": "John 14:6"},
    {"id": "iam_vine", "group": "The I AM Sayings", "title": "I am the True Vine", "ref": "John 15:1"},
    # ── The parables of Jesus (his own — the genuine gap) ──
    {"id": "par_sower", "group": "The Parables", "title": "The Sower", "ref": "Matthew 13:3-23"},
    {"id": "par_weeds", "group": "The Parables", "title": "The Wheat and the Weeds", "ref": "Matthew 13:24-30"},
    {"id": "par_mustard", "group": "The Parables", "title": "The Mustard Seed", "ref": "Matthew 13:31-32"},
    {"id": "par_leaven", "group": "The Parables", "title": "The Leaven", "ref": "Matthew 13:33"},
    {"id": "par_treasure", "group": "The Parables", "title": "The Treasure and the Pearl", "ref": "Matthew 13:44-46"},
    {"id": "par_dragnet", "group": "The Parables", "title": "The Dragnet", "ref": "Matthew 13:47-50"},
    {"id": "par_lost_sheep", "group": "The Parables", "title": "The Lost Sheep", "ref": "Luke 15:3-7"},
    {"id": "par_prodigal", "group": "The Parables", "title": "The Prodigal Son", "ref": "Luke 15:11-32"},
    {"id": "par_samaritan", "group": "The Parables", "title": "The Good Samaritan", "ref": "Luke 10:25-37"},
    {"id": "par_talents", "group": "The Parables", "title": "The Talents", "ref": "Matthew 25:14-30"},
    {"id": "par_unforgiving", "group": "The Parables", "title": "The Unforgiving Servant", "ref": "Matthew 18:23-35"},
    {"id": "par_rich_fool", "group": "The Parables", "title": "The Rich Fool", "ref": "Luke 12:16-21"},
]

_BY_ID = {t["id"]: t for t in _QUEUE}


def queue() -> Dict[str, Any]:
    """The work queue — every teaching, grouped, with its anchor reference."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for t in _QUEUE:
        groups.setdefault(t["group"], []).append({"id": t["id"], "title": t["title"], "ref": t["ref"]})
    return {"total": len(_QUEUE), "note": NOTE,
            "groups": [{"group": g, "count": len(items), "teachings": items} for g, items in groups.items()]}


_REF_RE = re.compile(r"^(\d?\s?[A-Za-z ]+?)\s+(\d+):(\d+)(?:-(\d+))?$")

# The wisdom seeded across history — the sources scattered through every people and age that,
# gathered, align to the Word. Prefix -> the era, so the SPREAD is visible (a Stoic emperor, a
# rabbi, a church father, a medieval monk, a Puritan tinker, a French skeptic — all concording).
# (prefix, era-label, approximate year — negative = BC) so the SPREAD across history can be mapped.
_WISDOM = [
    ("Confucius", "Chinese · ~500 BC", -500), ("Analects", "Chinese · ~500 BC", -500),
    ("Plato", "Greek · ~380 BC", -380), ("Aristotle", "Greek · ~340 BC", -340),
    ("Cicero", "Roman · ~50 BC", -50), ("Seneca", "Stoic · ~60 AD", 60),
    ("Clement", "Apostolic Father · ~96 AD", 96), ("Didache", "Apostolic · ~1st c.", 90),
    ("Plutarch", "Greek · ~100 AD", 100), ("Epictetus", "Stoic · ~110 AD", 110),
    ("Ignatius", "Apostolic Father · ~110 AD", 110), ("Polycarp", "Apostolic Father · ~150 AD", 150),
    ("Aurelius", "Stoic · Rome, ~170 AD", 170), ("Pirkei Avot", "Jewish (Mishnah) · ~200 AD", 200),
    ("Avot", "Jewish (Mishnah) · ~200 AD", 200), ("Augustine", "Church Father · ~400 AD", 400),
    ("Boethius", "Late antiquity · ~524 AD", 524), ("Imitation of Christ", "Medieval devotion · ~1420", 1420),
    ("Kempis", "Medieval devotion · ~1420", 1420), ("Canons of Dort", "Reformed · 1619", 1619),
    ("La Rochefoucauld", "French moralist · 1665", 1665), ("Rochefoucauld", "French moralist · 1665", 1665),
    ("Pilgrim's Progress", "Puritan · 1678", 1678),
]
_WISDOM_KEYS = [k for k, _, _ in _WISDOM]


def _tradition_of(title: str, shelf: str, tier: str):
    """(era-label, year) of a seeded-wisdom source, or (None, None) if the card is not cross-history
    wisdom (i.e. canonical Scripture, a dictionary entry, or plumbing)."""
    for key, era, year in _WISDOM:
        if title.startswith(key) or (" " + key) in title:
            return era, year
    if shelf == "science":
        return "The book of nature (creation)", None
    if tier == "matt" or title.startswith("Devotional") or title.startswith("A parable"):
        return "The lens (M.R. Harris) — Tier 4", 2020
    return None, None  # canonical Scripture / dictionary / other — concords, but not the cross-history witness


def _parse_ref(ref: str):
    m = _REF_RE.match(ref.strip())
    if not m:
        return None
    book, ch, v1, v2 = m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4)
    return book, ch, v1, int(v2) if v2 else v1


def _passage_text(ref: str) -> str:
    """The WEB text of the teaching — the Word's own words become the query that gathers its echoes."""
    parsed = _parse_ref(ref)
    if not parsed:
        return ""
    book, ch, v1, v2 = parsed
    import json
    from pathlib import Path
    import os
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    p = (Path(d) if d else Path("data")) / "bible_en.jsonl"
    if not p.exists():
        return ""
    out: List[str] = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("book") == book and r.get("chapter") == ch and v1 <= (r.get("verse") or 0) <= v2:
                out.append(r.get("text") or "")
    except OSError:
        return ""
    return " ".join(out)


def gather(teaching_id: str, limit: int = 14) -> Optional[Dict[str, Any]]:
    """GATHER, do not author. For a teaching, search all of history in the body and surface the wisdom
    that ALIGNS to it — attributed, never generated. The Word's own words drive the search; the concord
    is what the one Source already scattered. The operator curates; the engine only makes it visible."""
    t = _BY_ID.get((teaching_id or "").strip())
    if not t:
        return None
    parsed = _parse_ref(t["ref"])
    book = parsed[0] if parsed else t["ref"].split()[0]
    ch = parsed[1] if parsed else None
    text = _passage_text(t["ref"])
    query = (t["title"] + " " + text).strip() or t["title"]
    hits = corpus.search(query, limit=limit * 12, include_witness=True)
    wisdom: List[Dict[str, Any]] = []          # the cross-history seeded wisdom — the witness
    scripture: List[Dict[str, Any]] = []       # Scripture concording with itself — secondary
    seen = set()
    per_source: Dict[str, int] = {}            # cap each source, so the SPREAD across history shows
    _PER = 3

    def _source_key(title: str, shelf: str, tier: str) -> str:
        for k in _WISDOM_KEYS:
            if title.startswith(k) or (" " + k) in title:
                return k
        if shelf == "science":
            return "_science"
        return "_lens"

    for c in hits:
        if c.get("kind") != "note":
            continue
        title = c.get("title") or ""
        if title in seen:
            continue
        # skip the teaching's OWN passage (that is Step 1, the Word itself)
        if ch is not None and re.match(rf"^{re.escape(book)}\s+{ch}(?:[:\s—]|$)", title):
            continue
        seen.add(title)
        src = c.get("source") or {}
        shelf = c.get("shelf") or ""
        tier = src.get("authority_tier") or ""
        era, year = _tradition_of(title, shelf, tier)
        if era:
            sk = _source_key(title, shelf, tier)
            if per_source.get(sk, 0) >= _PER:      # already have enough from this source — favor breadth
                continue
            if len(wisdom) < limit:
                per_source[sk] = per_source.get(sk, 0) + 1
                wisdom.append({"source": title, "excerpt": (c.get("body") or "")[:340], "id": c.get("id"),
                               "shelf": shelf, "tier": tier, "tradition": era, "year": year,
                               "seal": (src.get("url") if "/s/" in (src.get("url") or "") else "")})
        elif not title.startswith("Easton") and len(scripture) < 8:
            scripture.append({"source": title, "id": c.get("id"),
                              "excerpt": (c.get("body") or "")[:160]})
        if len(wisdom) >= limit and len(scripture) >= 8:
            break
    traditions = sorted({w["tradition"] for w in wisdom})
    return {
        "id": t["id"], "title": t["title"], "ref": t["ref"], "group": t["group"],
        "wisdom": wisdom, "count": len(wisdom), "traditions": traditions,
        "scripture_concord": scripture, "note": NOTE,
        "anchor": {  # Step 1 stays the frozen Word — the Greek word-parts
            "passage": f"/passage?ref={t['ref'].replace(' ', '+')}",
            "original": f"/original?ref={t['ref'].replace(' ', '+')}",
        },
    }


# Backwards-compatible alias — the descriptor IS the gathered wisdom now.
def get(teaching_id: str) -> Optional[Dict[str, Any]]:
    return gather(teaching_id)


__all__ = ["queue", "get", "gather", "NOTE"]
