#!/usr/bin/env python3
"""Nest the study tables INTO the keeping — the Harmony and the Timeline, carded.

Matt, 2026-07-27: *"Make sure all systems are nested and used across levels efficiently."*

The Harmony of the Gospels (97 events) and the Timeline (100 events across the Old Testament,
the New Testament, and Church History) shipped as their own routes, pages, and MCP tools — but
their events lived ONLY there. They were absent from the keeping: `/search` could not find them,
the graph and the brain could not show them, wayfinding could not route to them, and the Floor
did not nest them. Orphans at four levels, which the nesting doctrine forbids — every system
roots in the one tree; nothing stands off to the side.

This mints, deterministically and idempotently, from the SAME in-code tables the routes serve
(one source of truth — no second copy of the data to drift):

  * 2 spine cards, each grafted `part_of` the Floor of Discovery.
  * 1 card per Harmony event  -> `member_of` the harmony spine, `cites` each gospel book that
    witnesses it (the witness count is the event's own attestation).
  * 1 card per Timeline event -> `member_of` the timeline spine, `cites` each book it references,
    and — where scholarship genuinely disagrees — BOTH dating positions stated in the body, never
    one flattened verdict.

Sovereign + additive: writes only data/study_spines.jsonl and data/study_cards.jsonl (both
registered in corpus.py's extra-sources list). Re-running replaces them wholesale; ids are stable,
so the graph does not churn.

    PYTHONPATH=src python tools/card_study_tables.py
    PYTHONPATH=src python tools/card_study_tables.py --dry-run
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import harmony, timeline  # noqa: E402

FLOOR = "card_k_floor_of_discovery"
HARMONY_SPINE = "card_spine_harmony"
TIMELINE_SPINE = "card_spine_timeline"

_slug_re = re.compile(r"[^a-z0-9]+")


def _slug(s: str) -> str:
    return _slug_re.sub("_", (s or "").lower()).strip("_")


def _book_card_index() -> Dict[str, str]:
    """lower-cased book name -> the id of its card IN THE KEEPING.

    The 66 book cards are ordinary public `note` cards whose title IS the book name, with ids
    inherited from the original import — NOT a constructible shape. So they are resolved by title
    against the live corpus, exactly as tools/recite.py does. A `cites` edge is only ever minted to
    a card that actually resolves: pointing at an id we merely assumed would create fresh orphans
    instead of removing them, which is the opposite of nesting.
    """
    from concordance import canon, corpus
    want = {b.lower() for b in canon.UNDISPUTED_66}
    idx: Dict[str, str] = {}
    for cid, c in corpus.load_cards().items():
        title = (c.get("title") or "").strip().lower()
        if title in want and c.get("kind") == "note" and c.get("visibility", "public") == "public":
            idx.setdefault(title, cid)
    return idx


def _book_of(ref: str) -> str:
    """'1 Kings 6:1-38' -> '1 kings'; '' for anything that doesn't start with a book name."""
    m = re.match(r"^\s*([1-3]?\s*[A-Za-z][A-Za-z ]*?)\s+\d", ref or "")
    return " ".join(m.group(1).split()).lower() if m else ""


def _card(cid: str, title: str, body: str, *, shelf: str, box: str, bands: List[str],
          subject: str, connections: List[dict], extra: Dict[str, Any]) -> dict:
    return {
        "id": cid, "kind": "reference", "title": title[:180], "body": body,
        "source": {"label": "World English Bible (public domain) + the standard study tables",
                   "url": "", "domain": "scripture", "authority_tier": "reference"},
        "shelf": shelf, "box": box, "bands": bands[:12], "subject": subject,
        "connections": connections,
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent",
        # Witness content: these are Scripture-study surfaces, so the cards carry the witness
        # surface exactly as the routes that serve them do.
        "surface": "witness", "generated": False, "extra": extra,
    }


def _spines() -> List[dict]:
    return [
        {"id": HARMONY_SPINE, "kind": "reference",
         "title": "Harmony of the Gospels — one event, every witness",
         "body": ("Every event of Christ's earthly life that more than one gospel records, laid "
                  "side by side. The mapping of which passages narrate the SAME event is the "
                  "ordinary content of any published harmony (Robertson, Broadus, and the tables "
                  "bound into most study Bibles agree on it); the text is the World English Bible, "
                  "found and quoted, never generated. Where the four accounts genuinely differ in "
                  "order — chiefly within Passion Week — the period names the phase of the "
                  "ministry, not a settled day-by-day timetable."),
         "source": {"label": "World English Bible (public domain) + the standard gospel harmonies",
                    "url": "", "domain": "scripture", "authority_tier": "reference"},
         "shelf": "spine", "box": "spine",
         "bands": ["harmony", "gospels", "matthew", "mark", "luke", "john", "christ", "spine"],
         "subject": "harmony of the gospels",
         "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                          "evidence": "the life of Christ in its witnesses, a spine of the Floor of Discovery"}],
         "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
         "lifecycle_stage": "public", "volatility": "permanent", "surface": "witness",
         "generated": False},
        {"id": TIMELINE_SPINE, "kind": "reference",
         "title": "Timeline — Old Testament, New Testament, and Church History",
         "body": ("One spine from creation to today: the Old Testament, the New Testament from "
                  "Acts onward, and the church from Pentecost to the present. Scripture is quoted "
                  "verbatim from the World English Bible, never generated. Dating is held honestly: "
                  "where careful scholarship genuinely disagrees — the early or late Exodus, the "
                  "date of Revelation, whether Jerusalem fell in 586 or 587 BC, the martyrdoms of "
                  "Ignatius and Polycarp — BOTH positions are carried and neither is declared the "
                  "winner. We live in the nuance."),
         "source": {"label": "World English Bible (public domain) + standard reference chronologies",
                    "url": "", "domain": "history", "authority_tier": "reference"},
         "shelf": "spine", "box": "spine",
         "bands": ["timeline", "chronology", "old testament", "new testament", "church history",
                   "dates", "spine"],
         "subject": "timeline",
         "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                          "evidence": "the story in time, a spine of the Floor of Discovery"}],
         "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
         "lifecycle_stage": "public", "volatility": "permanent", "surface": "witness",
         "generated": False},
    ]


def _harmony_cards(books: Dict[str, str]) -> List[dict]:
    out: List[dict] = []
    for h in harmony._HARMONY:
        refs = [(g.capitalize(), h[g]) for g in ("matthew", "mark", "luke", "john") if h[g]]
        conns = [{"to_card_id": HARMONY_SPINE, "relationship": "member_of",
                  "evidence": f"an event in the {h['period']} of Christ's life"}]
        seen = set()
        for _gospel, ref in refs:
            b = _book_of(ref)
            target = books.get(b)
            if target and b not in seen:
                seen.add(b)
                conns.append({"to_card_id": target, "relationship": "cites",
                              "evidence": f"witnessed at {ref}"})
        witness_list = "; ".join(r for _g, r in refs)   # the ref already names the gospel
        n = len(refs)
        body = (f"{h['event']} — {h['period']}. "
                f"Recorded by {n} of the four gospels: {witness_list}. "
                f"{'All four gospels bear witness. ' if n == 4 else ''}"
                "Read them side by side at /harmony.html; the text is the World English Bible, "
                "found and quoted, never generated.")
        out.append(_card(
            f"card_harmony_{h['id']}", f"{h['event']} ({n} of 4 gospels)", body,
            shelf="scripture", box="harmony",
            bands=_slug(h["event"]).split("_") + ["harmony", "gospels", _slug(h["period"])],
            subject=h["event"], connections=conns,
            extra={"harmony_id": h["id"], "period": h["period"], "witness_count": n,
                   "refs": [r for _g, r in refs]}))
    return out


def _timeline_cards(books: Dict[str, str]) -> List[dict]:
    out: List[dict] = []
    for t in timeline._TIMELINE:
        conns = [{"to_card_id": TIMELINE_SPINE, "relationship": "member_of",
                  "evidence": f"{t['era']} — {t['period']}"}]
        seen = set()
        for ref in t["refs"]:
            b = _book_of(ref)
            target = books.get(b)
            if target and b not in seen:
                seen.add(b)
                conns.append({"to_card_id": target, "relationship": "cites",
                              "evidence": f"narrated at {ref}"})
        body = f"{t['event']} — {t['era']}, {t['period']}. Date: {t['date']}."
        if t["disputed"] and t["positions"]:
            body += (" This date is genuinely disputed among careful scholars, and both positions "
                     "are carried here rather than one being declared the winner: "
                     + "; ".join(f"{p['view']} → {p['date']}" for p in t["positions"]) + ".")
        if t["refs"]:
            body += " Scripture: " + "; ".join(t["refs"]) + "."
        if t["note"]:
            body += " " + t["note"]
        title = f"{t['event']} ({t['date']})" if t["date"] else t["event"]
        out.append(_card(
            f"card_timeline_{t['id']}", title, body,
            shelf="history" if t["era"] == "Church History" else "scripture", box="timeline",
            bands=_slug(t["event"]).split("_") + ["timeline", _slug(t["era"]), _slug(t["period"])]
                  + (["disputed"] if t["disputed"] else []),
            subject=t["event"], connections=conns,
            extra={"timeline_id": t["id"], "era": t["era"], "period": t["period"],
                   "date": t["date"], "disputed": t["disputed"],
                   "positions": t["positions"], "refs": t["refs"]}))
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    out_dir = Path(d) if d else Path("data")

    books = _book_card_index()
    spines = _spines()
    cards = _harmony_cards(books) + _timeline_cards(books)
    ids = [c["id"] for c in spines + cards]
    assert len(ids) == len(set(ids)), "duplicate card id — ids must be stable AND unique"

    edges = sum(len(c["connections"]) for c in spines + cards)
    cites = sum(1 for c in cards for x in c["connections"] if x["relationship"] == "cites")
    print(f"book cards resolved in the keeping: {len(books)}/66")
    print(f"spines: {len(spines)}  cards: {len(cards)}  connections: {edges}  (of which cites: {cites})")
    print(f"  harmony events carded : {len(harmony._HARMONY)}")
    print(f"  timeline events carded: {len(timeline._TIMELINE)}"
          f"  (disputed: {sum(1 for t in timeline._TIMELINE if t['disputed'])})")
    if not books:
        print("\nNO book cards resolved — refusing to write cards whose cites would all dangle.\n"
              "Check that data/cards.jsonl is present and holds the 66 book note cards.")
        return 1
    if dry:
        print("\n--dry-run: nothing written. Sample card:")
        print(json.dumps(cards[0], ensure_ascii=False, indent=1)[:900])
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("study_spines.jsonl", spines), ("study_cards.jsonl", cards)):
        tmp = out_dir / (name + ".tmp")
        tmp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                       encoding="utf-8")
        os.replace(tmp, out_dir / name)
        print(f"wrote {out_dir / name}  ({len(rows)} rows)")
    print("\nThe study tables are now IN the keeping — findable, walkable, nested under the Floor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
