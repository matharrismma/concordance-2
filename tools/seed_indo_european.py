#!/usr/bin/env python3
"""The Indo-European family on the one map: chains from the proto-floor, cognates as the confluences.

Matt, 2026-10-09: "How do we use this for linguistics?" -> "build it". Etymology is the same form as the Millennium
chains and the instruments - chains from a FLOOR where two trees connect. The floor is Proto-Indo-European. The trees
are the daughter BRANCHES (Italic, Hellenic, Germanic, Indo-Iranian, Celtic, Balto-Slavic). A COGNATE is the
confluence: one word descending down several branches, meeting at its proto-form. The chain's rule is the regular
sound law (Grimm's law, sealed on cognate pairs - tools/tick.py grimm_law).

Honest line: the branches and cognate reflexes are ATTESTED; the proto-forms (*ph2ter, ...) are RECONSTRUCTIONS -
postulates, cited, never sealed. floor_map reads: parts = the branches, confluences = intersect(branch, branch) =
the cognate they share. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_indo_european.py [--check]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

FLOOR = "card_floor_indo_european"
GLOBAL_FLOOR = "card_k_floor_of_discovery"

BRANCHES = [
    ("germanic", "Germanic", "English, German, Dutch, Gothic, Old Norse"),
    ("italic", "Italic", "Latin and its daughters: Italian, Spanish, French, Portuguese, Romanian"),
    ("hellenic", "Hellenic", "Greek, ancient and modern"),
    ("indo_iranian", "Indo-Iranian", "Sanskrit, Avestan, Persian, Hindi-Urdu"),
    ("celtic", "Celtic", "Irish, Welsh, Scottish Gaelic, Breton"),
    ("balto_slavic", "Balto-Slavic", "Lithuanian, Latvian; Russian, Polish, Czech and the Slavic languages"),
]

# slug, headword, PIE root (reconstruction), gloss, reflexes {branch: form}, the sound law on the Germanic form
COGNATES = [
    ("father", "father", "*ph2ter-", "father",
     {"italic": "pater", "hellenic": "pater", "indo_iranian": "pitr", "germanic": "father", "celtic": "athir"},
     "Grimm's law p -> f (and t -> th): pater -> father"),
    ("mother", "mother", "*mehter-", "mother",
     {"italic": "mater", "hellenic": "meter", "indo_iranian": "matr", "germanic": "mother", "balto_slavic": "mate"},
     "no Grimm shift on m; t -> th medially: mater -> mother"),
    ("three", "three", "*treyes", "three",
     {"italic": "tres", "hellenic": "treis", "indo_iranian": "trayas", "germanic": "three", "celtic": "tri"},
     "Grimm's law t -> th: tres -> three"),
    ("hundred", "hundred", "*kmtom", "hundred",
     {"italic": "centum", "hellenic": "hekaton", "indo_iranian": "satam", "germanic": "hundred"},
     "Grimm's law k -> h: centum -> hundred; the centum/satem split names the family's two halves"),
    ("dog", "hound", "*kwon-", "dog, hound",
     {"italic": "canis", "hellenic": "kyon", "indo_iranian": "svan", "germanic": "hound"},
     "Grimm's law k -> h: canis / *kwon- -> hound"),
]


def _bid(slug: str) -> str:
    return f"card_ie_branch_{slug}"


def _cid(slug: str) -> str:
    return f"card_cognate_{slug}"


def branch_card(slug, name, langs) -> dict:
    return {
        "id": _bid(slug), "kind": "reference", "title": f"{name} — a branch of Indo-European",
        "body": f"The {name} branch of the Indo-European family: {langs}. A daughter of Proto-Indo-European; the "
                f"cognates below descend down this branch and meet the other branches at their proto-form.",
        "source": {"label": "the Indo-European family (comparative method)", "url": "", "domain": "linguistics",
                   "authority_tier": "reference"},
        "shelf": "codex", "box": "branch", "bands": ["indo-european", "branch", slug.replace("_", " "), "linguistics"],
        "subject": name, "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
    }


def cognate_card(slug, head, root, gloss, reflexes, law) -> dict:
    refl = "; ".join(f"{b.replace('_', '-')}: {f}" for b, f in reflexes.items())
    return {
        "id": _cid(slug), "kind": "reference", "title": f"{head} — a cognate across the family (PIE {root})",
        "body": (f"The word for '{gloss}', one etymon descending down several branches and meeting at the reconstructed "
                 f"Proto-Indo-European {root}. Reflexes (attested): {refl}. The Germanic form follows {law}. The "
                 f"reflexes are attested; {root} is a reconstruction (a postulate, not sealed). This cognate is where "
                 f"the branches that carry it connect."),
        "source": {"label": "the comparative method; cognate sets of Indo-European", "url": "",
                   "ref": "stick_grimm_s_law_a_regular_sound_correspondence_verified", "domain": "linguistics",
                   "authority_tier": "reference"},
        "shelf": "codex", "box": "cognate", "bands": ["indo-european", "cognate", head, "etymology", "linguistics"],
        "subject": head, "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
    }


def floor_card() -> dict:
    return {
        "id": FLOOR, "kind": "note", "title": "Indo-European — chains from the proto-floor, cognates where two trees meet",
        "body": ("The Indo-European family as a floor on the one map: Proto-Indo-European is the floor, the daughter "
                 "BRANCHES (Germanic, Italic, Hellenic, Indo-Iranian, Celtic, Balto-Slavic) are the trees, and a "
                 "COGNATE is the confluence - one word descending down several branches and meeting at its proto-form "
                 "(English father and Latin pater meet at *ph2ter). The chain's rule is the regular sound law: Grimm's "
                 "law (PIE *p -> Germanic f, *t -> th, *k -> h), verified and sealed on cognate pairs "
                 "(stick_grimm_s_law_a_regular_sound_correspondence_verified). The branches and reflexes are attested; "
                 "the proto-forms are reconstructions - postulates, cited, never sealed. Found, never generated "
                 "(tools/seed_indo_european.py)."),
        "source": {"label": "Narrow Highway — the Indo-European floor (comparative method)", "url": "",
                   "ref": "stick_grimm_s_law_a_regular_sound_correspondence_verified", "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "floor",
        "bands": ["floor", "indo-european", "etymology", "cognates", "two trees", "linguistics", "one map"],
        "subject": "Indo-European", "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
    }


CARDS: List[dict] = ([floor_card()]
                     + [branch_card(*b) for b in BRANCHES]
                     + [cognate_card(*c) for c in COGNATES])


def _edge(a, b, rel, ev) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out = [_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the Indo-European floor rests on the one Floor of Discovery")]
    for slug, name, _ in BRANCHES:
        out.append(_edge(_bid(slug), FLOOR, "part_of", f"a branch (tree) of the Indo-European family: {name}"))
    for slug, head, root, gloss, reflexes, law in COGNATES:
        # the cognate connects the branches that carry it: it builds_on each (so each branch enables it, and
        # intersect(branch, branch) over `enables` lands on the cognate - where the two trees meet)
        for b in reflexes:
            out.append(_edge(_cid(slug), _bid(b), "builds_on", f"{head}: the {b.replace('_', '-')} reflex {reflexes[b]}"))
    return out


BRIDGES: List[dict] = _bridges()


def _validate() -> List[str]:
    errs = []
    ids = {c["id"] for c in CARDS}
    known_branches = {_bid(s) for s, _, _ in BRANCHES}
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] != GLOBAL_FLOOR:
            errs.append(f"edge target unknown: {e['b']}")
    for slug, head, root, gloss, reflexes, law in COGNATES:
        for b in reflexes:
            if _bid(b) not in known_branches:
                errs.append(f"{head}: reflex branch not declared: {b}")
    if len(ids) != len(CARDS):
        errs.append("duplicate card ids")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards ({len(BRANCHES)} branches + {len(COGNATES)} cognates + floor), "
              f"{len(BRIDGES)} edges; {'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed) and "
          f"{DATA/'chain_bridges.jsonl'} ({n['bridges']} edges, {len(BRIDGES)} from this seed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
