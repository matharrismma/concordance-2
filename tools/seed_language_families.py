#!/usr/bin/env python3
"""The world's language families on the one map: a floor per family, branches as the trees.

Matt, 2026-10-11: "map the whole tree" - the language family tree. Indo-European is already a floor
(tools/seed_indo_european.py); this seeds the OTHER major families the same way, on the exact same
pattern - each family a FLOOR, its daughter BRANCHES the trees, the proto-language a RECONSTRUCTION
(a postulate: cited to the comparative method, inferred, never sealed). The families are kept SEPARATE
(no contested macro-families like "Altaic"), exactly as the consensus classification holds them.

What is attested: the branches and their languages (the comparative method; the family classification,
Glottolog). What is a postulate: the proto-language and its reconstructed forms - they work (they predict
the attested reflexes by regular law), so the proto is inferred, never kept as a fact and never sealed.

Rooted to Babel (Genesis 11): "the whole earth was of one language" (11:1), "let us confound their
language" (11:7) - where the one tongue became many. The shared origin of every family below.

This is GATHERING the established consensus (the same status as the IE branches the existing floor
already asserts), cited - not authoring novel relationships. Sound laws are sealed only where cognate
pairs are checkable (Indo-European, via Grimm's law); the other families are cited floors (the
comparative method is the source) with no sealed stick - we decline to seal what we have not checked.

    PYTHONPATH=src python tools/seed_language_families.py [--check]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

GLOBAL_FLOOR = "card_k_floor_of_discovery"
# Babel - where the one language became many (the Console weaves a single verse, so anchor the opening
# verse and the confounding verse alongside the range).
ROOT_REFS = ["Genesis 11:1-9", "Genesis 11:1", "Genesis 11:7"]

# slug, Name, Proto-language, [ (branch_slug, Branch Name, example languages), ... ]
FAMILIES = [
    ("uralic", "Uralic", "Proto-Uralic", [
        ("finnic", "Finnic", "Finnish, Estonian, Karelian"),
        ("ugric", "Ugric", "Hungarian, Khanty, Mansi"),
        ("samic", "Sámi", "the Sámi languages of the far north"),
        ("samoyedic", "Samoyedic", "Nenets, Enets, Nganasan, Selkup"),
    ]),
    ("turkic", "Turkic", "Proto-Turkic", [
        ("oghuz", "Oghuz", "Turkish, Azerbaijani, Turkmen"),
        ("karluk", "Karluk", "Uzbek, Uyghur"),
        ("kipchak", "Kipchak", "Kazakh, Kyrgyz, Tatar"),
        ("siberian_turkic", "Siberian Turkic", "Yakut (Sakha), Tuvan"),
    ]),
    ("mongolic", "Mongolic", "Proto-Mongolic", [
        ("mongolian", "Mongolian", "Khalkha Mongolian (Mongolia), Inner Mongolian"),
        ("peripheral_mongolic", "Peripheral Mongolic", "Buryat, Kalmyk-Oirat, Dagur"),
    ]),
    ("sino_tibetan", "Sino-Tibetan", "Proto-Sino-Tibetan", [
        ("sinitic", "Sinitic", "the Chinese languages: Mandarin, Cantonese, Wu, Min, Hakka"),
        ("tibeto_burman", "Tibeto-Burman", "Burmese, Tibetan (Dzongkha), Karen, Bodo-Garo"),
    ]),
    ("japonic", "Japonic", "Proto-Japonic", [
        ("japanese", "Japanese", "Japanese and its dialects"),
        ("ryukyuan", "Ryukyuan", "Okinawan and the Ryukyuan languages"),
    ]),
    ("koreanic", "Koreanic", "Proto-Koreanic", [
        ("korean", "Korean", "Korean and the Jeju language"),
    ]),
    ("austroasiatic", "Austroasiatic", "Proto-Austroasiatic", [
        ("vietic", "Vietic", "Vietnamese, Mường"),
        ("khmeric", "Khmeric", "Khmer (Cambodian)"),
        ("munda", "Munda", "Santali and the Munda languages of India"),
    ]),
    ("austronesian", "Austronesian", "Proto-Austronesian", [
        ("formosan", "Formosan", "the aboriginal languages of Taiwan - the homeland"),
        ("malayo_polynesian", "Malayo-Polynesian",
         "Malay, Indonesian, Tagalog, Malagasy, Hawaiian, Tahitian, Māori, Fijian"),
    ]),
    ("niger_congo", "Niger-Congo", "Proto-Niger-Congo", [
        ("bantu", "Bantu", "Swahili, Zulu, Xhosa, Shona, Kikongo, Lingala, Luganda, Chichewa, Sesotho, Setswana"),
        ("volta_niger", "Volta-Niger", "Yoruba, Igbo"),
        ("mande", "Mande", "Bambara, Mandinka"),
    ]),
    ("afroasiatic", "Afro-Asiatic", "Proto-Afro-Asiatic", [
        ("semitic", "Semitic", "Arabic, Hebrew, Amharic, Aramaic, Tigrinya, Maltese"),
        ("cushitic", "Cushitic", "Somali, Oromo"),
        ("chadic", "Chadic", "Hausa"),
        ("berber", "Berber", "Tamazight and the Berber languages"),
        ("egyptian", "Egyptian", "Ancient Egyptian and its last stage, Coptic"),
    ]),
    ("kartvelian", "Kartvelian", "Proto-Kartvelian", [
        ("georgian_zan", "Karto-Zan", "Georgian (Kartuli); Mingrelian and Laz"),
        ("svan", "Svan", "Svan"),
    ]),
    ("tupian", "Tupian", "Proto-Tupian", [
        ("tupi_guarani", "Tupí-Guaraní", "Guaraní, Old Tupí, Nheengatu"),
    ]),
]


# COGNATE CONFLUENCES - one etymon descending down several branches and meeting at its proto-form (the
# confluence, exactly as Indo-European's cognates work). Austronesian is the comparative method's showcase:
# the numerals and body-part words are regular across Formosan (the Taiwan homeland) and Malayo-Polynesian.
# (fam, slug, headword, proto, gloss, {branch_slug: attested reflexes}). Reflexes are attested; the proto
# is a reconstruction (a postulate, not sealed). More families' cognates are a continuing want.
COGNATES = [
    ("austronesian", "mata", "mata", "*mata (Proto-Austronesian)", "eye",
     {"formosan": "Amis mata", "malayo_polynesian": "Malay mata, Tagalog mata, Malagasy maso, Hawaiian maka, Māori mata, Fijian mata"}),
    ("austronesian", "lima", "lima", "*lima (Proto-Austronesian)", "five; hand",
     {"formosan": "Amis lima", "malayo_polynesian": "Malay lima, Tagalog lima, Hawaiian lima, Māori rima, Fijian lima, Malagasy dimy"}),
    ("austronesian", "telu", "telu", "*telu (Proto-Austronesian)", "three",
     {"formosan": "Amis tulu", "malayo_polynesian": "Tagalog tatlo, Malagasy telo, Hawaiian kolu, Māori toru, Fijian tolu"}),
]


def _floor_id(fam: str) -> str:
    return f"card_floor_{fam}"


def _branch_id(fam: str, slug: str) -> str:
    return f"card_{fam}_branch_{slug}"


def _cognate_id(fam: str, slug: str) -> str:
    return f"card_{fam}_cognate_{slug}"


def cognate_card(fam, name, slug, head, proto, gloss, reflexes) -> dict:
    refl = "; ".join(f"{b.replace('_', '-')}: {f}" for b, f in reflexes.items())
    return {
        "id": _cognate_id(fam, slug), "kind": "reference",
        "title": f"{head} — a cognate across {name} ({proto})",
        "body": (f"The word for '{gloss}', one etymon descending down several branches of {name} and meeting at the "
                 f"reconstructed {proto}. Reflexes (attested): {refl}. The reflexes are attested by the comparative "
                 f"method; {proto} is a reconstruction (a postulate, not sealed). This cognate is where the branches "
                 f"that carry it connect - a confluence on the {name} floor."),
        "source": _src(name), "shelf": "codex", "box": "cognate",
        "bands": [name.lower(), "cognate", head, "etymology", "linguistics"],
        "subject": head, "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
    }


def _src(name: str) -> dict:
    return {"label": f"the {name} family (the comparative method; the consensus classification, Glottolog)",
            "url": "", "domain": "linguistics", "authority_tier": "reference"}


def floor_card(fam, name, proto) -> dict:
    return {
        "id": _floor_id(fam), "kind": "note",
        "title": f"{name} — a language family: branches descending from {proto}",
        "body": (f"The {name} family as a floor on the one map: its daughter BRANCHES are the trees, descending "
                 f"from {proto} — a RECONSTRUCTION (a postulate: cited to the comparative method, inferred from "
                 f"the regular correspondences among the attested languages, never kept as a fact and never sealed). "
                 f"The branches and their languages are attested; {proto} is reconstructed. The family is held "
                 f"SEPARATE from the others (no contested macro-family). At Babel the one language became many "
                 f"(Genesis 11); this is one of those tongues. Found, never generated (tools/seed_language_families.py)."),
        "source": {"label": f"Narrow Highway — the {name} floor (the comparative method)", "url": "",
                   "domain": "linguistics", "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "floor",
        "bands": ["floor", name.lower(), "language family", "linguistics", "etymology", "one map", "babel"],
        "subject": name, "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
    }


def branch_card(fam, name, slug, bname, langs) -> dict:
    return {
        "id": _branch_id(fam, slug), "kind": "reference",
        "title": f"{bname} — a branch of {name}",
        "body": (f"The {bname} branch of the {name} family: {langs}. A daughter of the reconstructed proto-language; "
                 f"attested by the comparative method. The branch is attested; the proto-form it descends from is a "
                 f"reconstruction (a postulate, not sealed)."),
        "source": _src(name), "shelf": "codex", "box": "branch",
        "bands": [name.lower(), "branch", bname.lower(), "linguistics"],
        "subject": bname, "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
    }


def _edge(a, b, rel, ev) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


_FAM_NAME = {f[0]: f[1] for f in FAMILIES}
_FAM_BRANCHES = {f[0]: {b[0] for b in f[3]} for f in FAMILIES}

CARDS: List[dict] = []
BRIDGES: List[dict] = []
for _fam, _name, _proto, _branches in FAMILIES:
    _fid = _floor_id(_fam)
    CARDS.append(floor_card(_fam, _name, _proto))
    BRIDGES.append(_edge(_fid, GLOBAL_FLOOR, "part_of", f"the {_name} floor rests on the one Floor of Discovery"))
    for _slug, _bname, _langs in _branches:
        CARDS.append(branch_card(_fam, _name, _slug, _bname, _langs))
        BRIDGES.append(_edge(_branch_id(_fam, _slug), _fid, "part_of",
                             f"a branch (tree) of the {_name} family: {_bname}"))

# cognate confluences: each cognate builds_on every branch that carries it, so intersect(branch, branch)
# over `enables` lands on the cognate - where the branches of that family meet (the IE confluence pattern)
for _fam, _slug, _head, _proto, _gloss, _reflexes in COGNATES:
    _name = _FAM_NAME[_fam]
    CARDS.append(cognate_card(_fam, _name, _slug, _head, _proto, _gloss, _reflexes))
    for _b in _reflexes:
        BRIDGES.append(_edge(_cognate_id(_fam, _slug), _branch_id(_fam, _b), "builds_on",
                             f"{_head}: the {_b.replace('_', '-')} reflexes {_reflexes[_b]}"))

FLOOR_IDS = [_floor_id(f[0]) for f in FAMILIES]


def _validate() -> List[str]:
    errs = []
    ids = {c["id"] for c in CARDS}
    if len(ids) != len(CARDS):
        errs.append("duplicate card ids")
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] != GLOBAL_FLOOR:
            errs.append(f"edge target unknown: {e['b']}")
    return errs


def _anchor_floors() -> None:
    from concordance import roots
    for fam, name, _proto, _branches in FAMILIES:
        res = roots.anchor(roots.node_id("floor", _floor_id(fam)), ROOT_REFS, by="proposed",
                           why="at Babel the one language became many (Genesis 11)", data_dir=DATA)
        print(f"  anchor {name}: {'ok' if res.get('ok') else res}")


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        _nbranch = len(CARDS) - len(FAMILIES) - len(COGNATES)
        print(f"[check] {len(FAMILIES)} families, {len(CARDS)} cards "
              f"({len(FAMILIES)} floors + {_nbranch} branches + {len(COGNATES)} cognates), {len(BRIDGES)} edges; "
              f"{'OK' if not errs else 'ERRORS'}")
        print("  floor ids:", ", ".join(FLOOR_IDS))
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed) and "
          f"{DATA/'chain_bridges.jsonl'} ({n['bridges']} edges, {len(BRIDGES)} from this seed)")
    _anchor_floors()
    print("remember: append the floor ids to chains.FLOORS (chains.py) or they stay off the map:")
    print("  " + " ".join(f'"{fid}",' for fid in FLOOR_IDS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
