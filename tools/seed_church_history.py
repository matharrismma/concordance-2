#!/usr/bin/env python3
"""The Church through history on the one map: the descent of the traditions from the apostolic root.

Matt, 2026-10-11: he sent the "Church Denominations History" tree (33 AD -> today) alongside the
language family tree and said "map the whole tree." It is the SAME form as Indo-European
(tools/seed_indo_european.py): a FLOOR where trees descend. Here the floor is the one Church; the
root is the Early Biblical Church at Pentecost (Acts 2); the branches are the traditions already
gathered in data/church_cards.jsonl (card_churches.py); the edges are the DATABLE schisms and
reformations (the East-West Schism of 1054, the Reformation of 1517, the English Reformation of
1534 ...) - each a cited historical event, never a sealed theorem.

Honest line, kept from card_churches.py: we CALIBRATE, we do not judge. The descent is gathered
church history (attested events and confession years), cited and attributed; this seed mints no
verdict on any tradition or believer. The reflexes (the traditions, their confessions) are
attested; the lineage is the sourced event. floor_map reads: parts = the traditions, the chain =
the descent. MERGE-writes through chains.merge_seed; the floor is rooted to Acts 2 / Ephesians 4.

The traditions themselves are carded by tools/card_churches.py (data/church_cards.jsonl) and are
REUSED here by id - this seed adds only the floor, the apostolic root, and the descent edges.

    PYTHONPATH=src python tools/seed_church_history.py [--check]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

FLOOR = "card_floor_church_history"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_churches"           # the churches spine (card_churches.py), already rooted to the Word
APOSTOLIC = "card_church_apostolic"     # the Early Biblical Church (this seed mints it)

# The traditions already gathered in data/church_cards.jsonl (ids verified on the box, 2026-10-11).
EO = "card_church_eastern_orthodoxy"
RC = "card_church_roman_catholicism"
LU = "card_church_lutheran"
RE = "card_church_reformed_presbyterian"
AN = "card_church_anglican"
BA = "card_church_baptist"
ME = "card_church_methodist_wesleyan"
PE = "card_church_pentecostal_charismatic"
AB = "card_church_anabaptist"
CO = "card_church_congregational_free_church"
SD = "card_church_seventh_day_adventist"
RM = "card_church_restoration_movement_churches_of_christ_disciples"
EV = "card_church_evangelical_interdenominational"
CR = "card_church_the_ecumenical_creeds_the_shared_ground"
# Two ancient apostolic traditions that PREDATE the East–West split and are NOT in card_churches.jsonl — this
# seed mints them so the floor does not erase them: the Church of the East (distinct after Ephesus, 431) and
# Oriental Orthodoxy (distinct after Chalcedon, 451, which it did not receive).
COE = "card_church_of_the_east"
OO = "card_church_oriental_orthodoxy"

# the traditions carried by this floor (reused by id; must exist in data/church_cards.jsonl)
TRADITIONS = [EO, RC, LU, RE, AN, BA, ME, PE, AB, CO, SD, RM, EV, CR]

# THE DESCENT — (child, parent, the datable event that is the lineage). child builds_on parent (so the
# parent ENABLES the child, and floor_map's chain walks the whole tree forward from the apostolic root).
# Each evidence string is an attested historical event or confession year; cited, never sealed. Only the
# root is a direct part of the floor; every tradition hangs in the chain below it. A node with two or more
# parents is a MERGE (where streams meet) - Evangelicalism is exactly that.
DESCENT = [
    (CR, APOSTOLIC, "the Nicene Creed (325/381) — the confession the traditions broadly hold in common, the center that holds (Ephesians 4:4-6); the Apostles' Creed in the West; Chalcedon (451) received by the Chalcedonian churches (East and West), the point at which Oriental Orthodoxy diverged — so not universal"),
    # the first ENDURING divisions, before the East–West split: Ephesus (431) and Chalcedon (451)
    (COE, APOSTOLIC, "the ancient Church of the East (East-Syriac, called 'Nestorian') — distinct after the Council of Ephesus, AD 431, over the Christology of Nestorius; the first enduring division"),
    (OO, APOSTOLIC, "Oriental Orthodoxy (Miaphysite) — Coptic, Syriac, Armenian, Ethiopian, Eritrean, Malankara — distinct after the Council of Chalcedon, AD 451, which it did not receive"),
    (EO, APOSTOLIC, "the Chalcedonian Church of the first millennium; the East after the East–West (Great) Schism, AD 1054 — the first great division between the Greek East and the Latin West"),
    (RC, APOSTOLIC, "the Chalcedonian Church of the first millennium; the West (Rome) after the East–West (Great) Schism, AD 1054"),
    (LU, RC, "the Reformation: Luther's Ninety-Five Theses (1517); the Augsburg Confession (1530)"),
    (RE, RC, "the Reformation in Switzerland: Zwingli and Calvin (1520s–1540s); the Westminster Confession (1646)"),
    (AN, RC, "the English Reformation: the Act of Supremacy (1534); the Thirty-Nine Articles (1571)"),
    (AB, RE, "the Radical Reformation out of the Swiss/Zwinglian Reformed movement in Zurich — the first believer's baptism (Grebel, Manz, Blaurock, 1525); the Schleitheim Confession (1527)"),
    (CO, AN, "the English Separatists / Independents out of the Church of England: the Savoy Declaration (1658)"),
    (BA, CO, "the English Separatist stream: the first Baptist congregation (Smyth and Helwys, 1609); the 1689 Confession"),
    (ME, AN, "the Wesleyan revival within the Church of England (1738); the Methodist separation (1784)"),
    (PE, ME, "the Holiness / Methodist stream: the Azusa Street revival (1906)"),
    # the Restoration Movement is a MERGE of the Reformed/Presbyterian and Baptist streams (its own two roots)
    (RM, RE, "the Stone–Campbell Restoration Movement — its Presbyterian/Reformed root (Barton Stone, Cane Ridge 1801; the Campbells' Seceder-Presbyterian background): the Declaration and Address (1809)"),
    (RM, BA, "the Stone–Campbell Restoration Movement — believer's baptism and early Baptist association: the Declaration and Address (1809)"),
    # Seventh-day Adventism out of the Millerite revival — a merge of the Baptist and Methodist streams
    (SD, BA, "the Millerite Adventist revival (1840s) — William Miller a Baptist; organized 1863"),
    (SD, ME, "the Millerite Adventist revival (1840s) — drawing Methodists as well; organized 1863"),
    # Evangelicalism is the MERGE of the Protestant streams - a trans-denominational renewal (the Lausanne
    # Covenant, 1974, principally drafted by John Stott, an Anglican)
    (EV, LU, "a trans-denominational renewal confessing the gospel across the Protestant streams (Lausanne, 1974)"),
    (EV, RE, "a trans-denominational renewal confessing the gospel across the Protestant streams (Lausanne, 1974)"),
    (EV, AN, "a trans-denominational renewal across the Protestant streams (Lausanne, 1974; the Covenant drafted by John Stott, an Anglican)"),
    (EV, BA, "a trans-denominational renewal confessing the gospel across the Protestant streams (Lausanne, 1974)"),
    (EV, ME, "a trans-denominational renewal confessing the gospel across the Protestant streams (Lausanne, 1974)"),
    (EV, PE, "a trans-denominational renewal confessing the gospel across the Protestant streams (Lausanne, 1974)"),
]

# Edges retired when the model was cleaned (2026-10-11): the first run made every tradition a flat part
# of the floor (which made every ancestor/descendant pair a spurious "confluence") and put the creeds and
# Evangelicalism on connects_at joints. The clean model: one root part, a builds_on descent, Evangelicalism
# a merge. These stale edges are dropped so a re-run fully reconciles.
DROP = ([(t, FLOOR, "part_of") for t in TRADITIONS]
        + [(CR, x, "connects_at") for x in (EO, RC, LU, RE, AN)]
        + [(EV, x, "connects_at") for x in (LU, RE, BA, ME, PE)]
        # the first run descended the Anabaptists from Rome; the accurate parent is the Swiss/Reformed stream
        # they broke from (Zurich, 1525), so the old edge is retired and replaced by (AB, RE) in the descent.
        + [(AB, RC, "builds_on")])


def apostolic_card() -> dict:
    return {
        "id": APOSTOLIC, "kind": "reference",
        "title": "The Early Biblical Church — the apostolic root (c. AD 33)",
        "body": ("The one Church as it began: the apostles and the first disciples at Pentecost, when the "
                 "Holy Spirit was poured out and about three thousand were added in a day (Acts 2). The root "
                 "every tradition below descends from — one body, one Spirit, one Lord, one faith, one "
                 "baptism (Ephesians 4:4-6). The root every tradition below descends from; the branches that "
                 "follow are its visible, datable divisions — the first enduring ones at the Councils of Ephesus "
                 "(431) and Chalcedon (451), then the great East–West Schism (1054) and the Reformation — "
                 "gathered and cited, never judged."),
        "source": {"label": "The apostolic Church — Acts of the Apostles", "url": "",
                   "domain": "theology", "authority_tier": "reference"},
        "shelf": "churches", "box": "tradition",
        "bands": ["church", "apostolic", "pentecost", "early church", "root"],
        "subject": "the apostolic Church",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": "the root of the one Church, from which the traditions descend"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": {"confession": "the apostles' preaching (Acts 2:42); the gospel (1 Corinthians 15:3-4)",
                  "emphasis": "the risen Christ, the Spirit poured out, the breaking of bread and the prayers",
                  "era": "c. AD 33", "scripture": "Acts 2:1-4; Acts 2:42; Ephesians 4:4-6"},
    }


def floor_card() -> dict:
    return {
        "id": FLOOR, "kind": "note",
        "title": "The Church through history — the descent of the traditions from the apostolic root",
        "body": ("The one Church as a floor on the one map: the Early Biblical Church (Acts 2) is the root, and "
                 "the traditions are the trees that descend from it by DATABLE events — the first enduring "
                 "divisions at the Councils of Ephesus (431, the Church of the East) and Chalcedon (451, the "
                 "Oriental Orthodox), then the great East–West Schism (1054), the Reformation (1517), the English "
                 "Reformation (1534), and on. The branches and their confessions are attested; each lineage is a "
                 "cited historical event, never a sealed theorem and never a verdict on a tradition or a believer. "
                 "The Nicene Creed (325/381) is the ground most traditions confess in common (the center that "
                 "holds, Ephesians 4:4-6); Chalcedon is not universal (the Oriental Orthodox do not receive it). "
                 "We calibrate, we do not judge. Found, never generated (tools/seed_church_history.py)."),
        "source": {"label": "Narrow Highway — the Church-history floor (gathered church history)", "url": "",
                   "ref": SPINE, "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "floor",
        "bands": ["floor", "church", "denominations", "traditions", "church history", "two trees",
                  "theology", "one map"],
        "subject": "the Church through history", "connections": [], "author": "engine",
        "created_at": 0.0, "updated_at": 0.0, "visibility": "public", "lifecycle_stage": "public",
        "volatility": "permanent", "surface": "secular", "generated": False,
    }


def _ancient_card(cid, title, body, confession, emphasis, era, scripture, bands) -> dict:
    return {
        "id": cid, "kind": "reference", "title": title, "body": body,
        "source": {"label": "An ancient apostolic tradition — its own confession", "url": "",
                   "domain": "theology", "authority_tier": "reference"},
        "shelf": "churches", "box": "tradition",
        "bands": ["church", "tradition", "ancient", "apostolic"] + list(bands),
        "subject": title.split(" — ")[0],
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": "an ancient apostolic tradition of the one Church"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
        "extra": {"confession": confession, "emphasis": emphasis, "era": era, "scripture": scripture},
    }


def church_of_the_east_card() -> dict:
    return _ancient_card(
        COE, "The Church of the East — the East-Syriac tradition (distinct after AD 431)",
        ("The ancient Church of the East (East-Syriac; historically called 'Nestorian', a name it disputes), which "
         "spread along the Silk Road to Persia, India and China. It became distinct after the Council of Ephesus "
         "(AD 431) over the Christology associated with Nestorius. It confesses the Nicene faith; today it endures as "
         "the Assyrian Church of the East and the Ancient Church of the East. An apostolic tradition the map must not "
         "erase — gathered and cited, never judged."),
        "the Nicene Creed; the Christology of the Church of the East (two qnome in one prosopon)",
        "endurance under persecution; the gospel carried to the ends of the known earth",
        "distinct after AD 431 (Council of Ephesus)", "Acts 1:8; Matthew 28:19; John 1:14",
        ["church of the east", "assyrian", "east syriac", "nestorian", "ephesus 431"])


def oriental_orthodoxy_card() -> dict:
    return _ancient_card(
        OO, "Oriental Orthodoxy — the non-Chalcedonian (Miaphysite) churches (distinct after AD 451)",
        ("The Oriental Orthodox communion — Coptic, Syriac, Armenian Apostolic, Ethiopian, Eritrean and Malankara "
         "(Indian) churches (~60 million today). It holds the first three ecumenical councils (Nicaea, Constantinople, "
         "Ephesus) and the Nicene Creed, but did NOT receive the Council of Chalcedon (AD 451); it confesses one united "
         "nature of the incarnate Word (Miaphysite), distinguishing itself from both Nestorianism and Eutychianism. An "
         "ancient apostolic communion — gathered and cited, never judged; recent dialogues have narrowed the historic "
         "Christological difference with the Chalcedonian churches to largely terminological."),
        "the first three ecumenical councils; the Nicene Creed; Miaphysite Christology (St Cyril of Alexandria)",
        "the unbroken ancient liturgy and asceticism; faithfulness through centuries under Islamic and other rule",
        "distinct after AD 451 (Council of Chalcedon)", "John 1:14; Colossians 2:9; Philippians 2:6-7",
        ["oriental orthodox", "miaphysite", "coptic", "armenian", "syriac", "ethiopian", "chalcedon 451"])


CARDS: List[dict] = [floor_card(), apostolic_card(), church_of_the_east_card(), oriental_orthodoxy_card()]


def _edge(a, b, rel, ev) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out = [_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the Church-history floor rests on the one Floor of Discovery")]
    # only the apostolic root is a direct part of the floor; the traditions descend from it in the chain
    out.append(_edge(APOSTOLIC, FLOOR, "part_of", "the apostolic root of the Church"))
    # the descent: child builds_on parent (the datable lineage) -> parent enables child -> the chain
    for child, parent, ev in DESCENT:
        out.append(_edge(child, parent, "builds_on", ev))
    return out


BRIDGES: List[dict] = _bridges()

# every external tradition id this floor reuses must exist in data/church_cards.jsonl (verified 2026-10-11)
_EXTERNAL = set(TRADITIONS)


def _validate() -> List[str]:
    errs = []
    ids = {c["id"] for c in CARDS}
    known = ids | _EXTERNAL | {GLOBAL_FLOOR}
    for e in BRIDGES:
        if e["a"] not in known:
            errs.append(f"edge source unknown: {e['a']}")
        if e["b"] not in known:
            errs.append(f"edge target unknown: {e['b']}")
    if len(ids) != len(CARDS):
        errs.append("duplicate card ids")
    # the descent is a DAG rooted at the apostolic card: every node must reach the root up some parent path
    parents: dict = {}
    for child, par, _ in DESCENT:
        parents.setdefault(child, []).append(par)
    for start in parents:
        stack, seen, reached = [start], set(), False
        while stack:
            cur = stack.pop()
            if cur == APOSTOLIC:
                reached = True
                break
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(parents.get(cur, []))
        if not reached:
            errs.append(f"{start} does not descend to the apostolic root")
    # every tradition reused must be carried on the floor (named in DESCENT) so none is orphaned
    on_floor = {c for c, _, _ in DESCENT}
    for t in TRADITIONS:
        if t not in on_floor:
            errs.append(f"tradition not placed in the descent: {t}")
    return errs


def _anchor_floor() -> None:
    """Root the floor to Scripture: Pentecost (the church born) and the one body. We anchor both the
    ranges AND their opening verses, because the Console weaves a single verse at a time - so a reader
    landing on Acts 2:1 or Ephesians 4:4 still sees the floor surface (until roots matches verse ranges
    by overlap, which is the general fix)."""
    from concordance import roots
    refs = ["Acts 2:1-4", "Acts 2:1", "Ephesians 4:4-6", "Ephesians 4:4"]
    res = roots.anchor(roots.node_id("floor", FLOOR), refs, by="proposed",
                       why="the Church born at Pentecost; one body, one Spirit, one Lord", data_dir=DATA)
    print(f"  roots.anchor({FLOOR}) -> {res}")


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards (floor + apostolic root), {len(TRADITIONS)} traditions reused, "
              f"{len(DESCENT)} descent edges, {len(BRIDGES)} bridges, {len(DROP)} stale edges dropped; "
              f"{'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES, drop_edges=DROP)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed) and "
          f"{DATA/'chain_bridges.jsonl'} ({n['bridges']} edges, {len(BRIDGES)} from this seed)")
    _anchor_floor()
    print("remember: append \"card_floor_church_history\" to chains.FLOORS (chains.py) or it stays off the map.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
