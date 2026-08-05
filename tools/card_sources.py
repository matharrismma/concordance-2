#!/usr/bin/env python3
"""Card the stored sources — the technical, academic corpus that always grows.

Matt: "It was the cards from our stored sources. The Corpus. … Focus on the technical, academic
focused work. We don't have to stop at 100k. It should just always grow."

The hard drive holds a library of real, public-domain reference sources (nuclides, star catalogs,
USDA foods, IANA ports, World Bank indicators, …) — millions of rows. This mints them into cards:
one real, sourced, engine-verifiable seed per fact. Not the speculative "connection assay" cards —
the technical/academic reference layer.

Discipline: gather, don't author (every card is a source row, attributed; generated=False, never
an LLM). Strict open-license only (US-gov public domain, or CC-BY with attribution). NO ORPHANS —
each card is member_of a domain SPINE, and each spine roots (through the created order) in the
Floor of Discovery. Idempotent + additive: re-run to grow; ids are deterministic so nothing dupes.

    CONCORDANCE_LW_BASE=D:/nh-backup/mirror/repo/lw/00_source python tools/card_sources.py
    ... --only nuclides,stars     # a subset
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
CREATED_ORDER = "card_k_spine_created_order"   # nature roots here → the Floor
_slug = re.compile(r"[^a-z0-9]+")


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def _conn(name: str) -> sqlite3.Connection:
    dbs = list(_base().glob(f"{name}/*.db"))
    if not dbs:
        raise FileNotFoundError(f"no db for source {name!r} under {_base()}")
    return sqlite3.connect(f"file:{dbs[0]}?mode=ro", uri=True)


def _sk(*parts) -> str:
    return _slug.sub("_", "-".join(str(p) for p in parts).lower()).strip("_")


def _card(cid, title, body, *, shelf, subject, bands, source_label, spine, domain):
    return {
        "id": cid, "kind": "reference", "title": title[:180], "body": body,
        "source": {"label": source_label, "url": "", "domain": domain, "authority_tier": "reference"},
        "shelf": shelf, "box": "source", "bands": bands, "subject": subject,
        # embedded edge → the domain spine (no orphan; no giant bridge file needed)
        "connections": [{"to_card_id": spine, "relationship": "member_of",
                         "evidence": f"a member of {shelf} in the keeping"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
        "generated": False,
    }


def _spine(cid, title, body, parent, bands):
    return {
        "id": cid, "kind": "reference", "title": title, "body": body,
        "source": {"label": "The Corpus — a spine of the stored sources", "url": "",
                   "domain": "", "authority_tier": "reference"},
        "shelf": "regulation" if False else "spine", "box": "spine", "bands": bands, "subject": title,
        "connections": [{"to_card_id": parent, "relationship": "part_of",
                         "evidence": "a spine of the corpus, rooted in the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


# ── source mappers: each yields cards; SPINES lists the spine seeds ────────────
SPINES = [
    _spine("card_spine_nuclides", "The nuclides — every isotope",
           "Every known nuclide: its protons, neutrons, mass, stability and half-life. A spine of "
           "the created order at the scale of the atom.", CREATED_ORDER,
           ["nuclides", "isotopes", "nuclear physics", "spine", "created order"]),
    _spine("card_spine_stars", "The stars — a catalogue of the heavens",
           "Named and naked-eye stars: position, distance, brightness and spectral type. The "
           "heavens catalogued, a spine of the created order.", CREATED_ORDER,
           ["stars", "astronomy", "catalogue", "spine", "created order"]),
    _spine("card_spine_foods", "Foods and their nourishment",
           "Whole foods and their measured nutrition — a spine of the created order concerned with "
           "the keeping of the body.", CREATED_ORDER,
           ["foods", "nutrition", "USDA", "spine", "created order"]),
    _spine("card_spine_ports", "Network ports & protocols",
           "The IANA registry of service names and port numbers — the agreed doorways of the "
           "networked world.", FLOOR,
           ["networking", "ports", "protocols", "IANA", "spine"]),
    _spine("card_spine_worldbank", "World development indicators",
           "World Bank open indicators — economies measured across countries and years.", FLOOR,
           ["economics", "development", "world bank", "indicators", "spine"]),
    _spine("card_spine_words", "The Dictionary & Thesaurus",
           "Every word: what it means, and the words that stand with it. A dictionary and a "
           "thesaurus in one — so language itself is carried on the ark.", FLOOR,
           ["dictionary", "thesaurus", "words", "language", "wordnet", "spine"]),
    _spine("card_spine_places", "The places of the earth",
           "Named places of the earth — country, coordinates, population. A gazetteer for the ark.",
           FLOOR, ["geography", "places", "gazetteer", "geonames", "spine"]),
    _spine("card_spine_drugs", "The medicines",
           "Medicines and their class, form and route — a pharmacopeia so a caregiver with no "
           "doctor still has the reference.", FLOOR,
           ["medicine", "drugs", "pharmacology", "pharmacopeia", "spine"]),
    _spine("card_spine_federal", "The federal shelf — US government publications",
           "United States federal publications held on the ark — field manuals, farmers' "
           "bulletins, technical reports and surveys, public domain under 17 USC 105. Practical "
           "knowledge a family can use, from sources whose authorship makes them free.", FLOOR,
           ["federal", "government", "public domain", "manuals", "bulletins", "spine"]),
    # The plumb-line: the original tongues. Rooted in the Word (special revelation), not the Floor —
    # everything runs THROUGH Hebrew and Greek. Matt: "Everything through hebrew and greek. We are
    # the tool to bring the Academics and jewish people to Christ through logic and coherence."
    _spine("card_spine_lexicon", "The Original Tongues — Hebrew & Greek",
           "Every word of the Biblical languages: Strong's number, the word itself, its "
           "transliteration and its lexical range. The plumb-line the whole map is measured "
           "against — Scripture in the tongues it was given in.", "card_k_spine_the_word",
           ["hebrew", "greek", "lexicon", "strongs", "original language", "the Word", "spine"]),
]


def gen_nuclides():
    c = _conn("nuclides")
    for (nuc, el, z, n, a, hl, stable, d1, d1p, ab, am) in c.execute(
            "select nuclide,element,z,n,a,half_life_s,is_stable,decay_1,decay_1_pct,abundance,atomic_mass from nuclides"):
        mass_u = ""
        try:
            mass_u = f" Atomic mass {float(am) / 1e6:.6f} u."
        except (TypeError, ValueError):
            pass
        stab = "stable" if stable else (f"half-life {hl} s" if hl else "unstable")
        decay = f" Primary decay: {d1}{(' ' + str(d1p) + '%') if d1p else ''}." if d1 else ""
        ab_s = f" Natural abundance {ab}." if ab else ""
        body = (f"Nuclide {nuc}: {z} protons, {n} neutrons, mass number A={a}. {stab.capitalize()}."
                f"{decay}{ab_s}{mass_u}")
        yield _card(f"card_src_nuclide_{_sk(nuc)}", f"{nuc} — {str(el).lower()}-{a}", body,
                    shelf="nuclear_physics", subject=nuc,  # underscore: the ONE canonical form
                    # (was "nuclear physics" — the only shelf split in the keeping; healed 2026-08-04)
                    bands=[nuc, str(el), "isotope", "nuclide", "nuclear physics"],
                    source_label="NNDC / AME nuclide data (public domain)",
                    spine="card_spine_nuclides", domain="nuclear_physics")


def gen_stars():
    c = _conn("hyg")
    for (proper, bf, con, ra, dec, dist, mag, absmag, spect, lum) in c.execute(
            "select proper,bf,con,ra,dec,dist,mag,absmag,spect,lum from stars "
            "where mag<=6.5 and (proper!='' or bf!='')"):
        name = proper or (f"{bf} {con}".strip() if bf else "")
        if not name:
            continue
        d_s = f" about {dist:.1f} parsecs away" if dist else ""
        l_s = f", ~{lum:g}× the Sun's luminosity" if lum else ""
        body = (f"{name}: a star{(' in ' + con) if con else ''}, apparent magnitude {mag:g}"
                f"{(', spectral type ' + spect) if spect else ''}{d_s}{l_s}.")
        yield _card(f"card_src_star_{_sk(name, con)}", name, body,
                    shelf="astronomy", subject=name,
                    bands=[name, str(con), "star", "astronomy", str(spect)],
                    source_label="HYG stellar database (CC-BY-SA, D. Nash)",
                    spine="card_spine_stars", domain="astronomy")


def gen_ports():
    c = _conn("protocols")
    seen = set()
    for (port, proto, service, desc, ref) in c.execute(
            "select port,protocol,service,description,reference from ports where service!=''"):
        key = (port, proto, service)
        if key in seen:
            continue
        seen.add(key)
        body = (f"Port {port}/{proto} is assigned to {service}"
                f"{(': ' + desc) if desc else ''}.{(' ' + ref) if ref else ''}")
        yield _card(f"card_src_port_{_sk(proto, port, service)}",
                    f"Port {port}/{proto} — {service}", body,
                    shelf="networking", subject=f"{port}/{proto}",
                    bands=[str(port), str(proto), str(service), "port", "networking"],
                    source_label="IANA Service Name and Port Number Registry (public domain)",
                    spine="card_spine_ports", domain="networking")


def gen_worldbank():
    c = _conn("worldbank")
    for (country, iso3, code, indicator, value, year) in c.execute(
            "select country,iso3,code,indicator,value,year from indicators where value is not null"):
        body = (f"{indicator} for {country}: {value:,g} in {year}. World Bank series {code}.")
        yield _card(f"card_src_wb_{_sk(iso3, code, year)}",
                    f"{indicator} — {country} ({year})", body,
                    shelf="economics", subject=f"{indicator} ({country})",
                    bands=[str(country), str(iso3), str(indicator), "world bank", "economics"],
                    source_label="World Bank Open Data (CC-BY 4.0)",
                    spine="card_spine_worldbank", domain="economics")


def gen_foods():
    c = _conn("usda")
    cols = [d[1] for d in c.execute('pragma table_info("foods")')]
    namecol = "description" if "description" in cols else ("name" if "name" in cols else cols[1])
    idcol = "fdc_id" if "fdc_id" in cols else cols[0]
    # energy (1008) + protein (1003) if present, one light lookup per food
    for (fid, name) in c.execute(f'select "{idcol}","{namecol}" from foods'):
        if not name:
            continue
        nut = {}
        for (nid, amt) in c.execute(
                "select nutrient_id,amount from food_nutrients where fdc_id=? and nutrient_id in (1008,1003,1004,1005)", (fid,)):
            nut[nid] = amt
        parts = []
        if 1008 in nut: parts.append(f"{nut[1008]:g} kcal")
        if 1003 in nut: parts.append(f"{nut[1003]:g} g protein")
        if 1004 in nut: parts.append(f"{nut[1004]:g} g fat")
        if 1005 in nut: parts.append(f"{nut[1005]:g} g carbohydrate")
        per = (" Per 100 g: " + ", ".join(parts) + ".") if parts else ""
        body = f"{name} — a food in the USDA FoodData Central reference.{per}"
        yield _card(f"card_src_food_{_sk(fid)}", str(name).title()[:120], body,
                    shelf="nutrition", subject=str(name),
                    bands=[str(name).lower(), "food", "nutrition", "USDA"],
                    source_label="USDA FoodData Central (public domain)",
                    spine="card_spine_foods", domain="nutrition")


def gen_words():
    """The Dictionary & Thesaurus — WordNet: one card per lemma, all senses (definitions) plus
    the words that stand with it (synonyms)."""
    c = _conn("wordnet")
    for (lemma, data) in c.execute("select lemma,data from senses"):
        try:
            senses = json.loads(data)
        except Exception:
            continue
        if not senses:
            continue
        parts, poss = [], set()
        for s in senses[:6]:
            pos, d = s.get("pos", ""), s.get("definition", "")
            poss.add(pos)
            sy = s.get("synonyms") or []
            parts.append(f"({pos}) {d}" + (f" — syn: {', '.join(sy[:6])}" if sy else ""))
        body = f"{lemma}: " + " · ".join(parts)
        yield _card(f"card_src_word_{_sk(lemma)}", str(lemma), body,
                    shelf="dictionary", subject=str(lemma),
                    bands=[str(lemma).lower(), "dictionary", "thesaurus", "word"] + [p for p in poss if p],
                    source_label="WordNet 3.0, Princeton University (WordNet License)",
                    spine="card_spine_words", domain="linguistics")


def gen_places():
    c = _conn("geonames")
    for (gid, name, ascii_, lat, lon, cc, admin1, fcode, pop, tz) in c.execute(
            "select geonameid,name,ascii,lat,lon,cc,admin1,fcode,population,tz from places"):
        if not name:
            continue
        pop_s = f", population {pop:,}" if pop else ""
        body = (f"{name}: a place in {cc}{(', ' + admin1) if admin1 else ''} at "
                f"{lat:.3f}, {lon:.3f}{pop_s}. Feature {fcode}, timezone {tz}.")
        yield _card(f"card_src_place_{_sk(gid)}", str(name), body,
                    shelf="geography", subject=str(name),
                    bands=[str(name).lower(), str(cc), "place", "geography", str(fcode)],
                    source_label="GeoNames (CC-BY 4.0)",
                    spine="card_spine_places", domain="geography")


def gen_drugs():
    c = _conn("openfda_ndc")
    seen = set()
    for (ndc, brand, generic, form, route, ptype, dea, ingr, pharm, labeler) in c.execute(
            "select product_ndc,brand_name,generic_name,dosage_form,route,product_type,"
            "dea_schedule,active_ingredients,pharm_class,labeler_name from drugs where generic_name is not null"):
        key = str(generic or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        body = (f"{generic}: a {ptype or 'drug'}" + (f", {form.lower()}" if form else "") +
                (f" given by the {route.lower()} route" if route else "") + "." +
                (f" Pharmacologic class: {pharm}." if pharm else "") +
                (f" DEA schedule {dea}." if dea else ""))
        bands = [key, "drug", "medicine", "pharmacology"]
        if brand and brand.lower() != key:
            bands.append(brand.lower())
        yield _card(f"card_src_drug_{_sk(key)}", str(generic).title(), body,
                    shelf="medicine", subject=str(generic),
                    bands=bands, source_label="openFDA / FDA NDC Directory (public domain)",
                    spine="card_spine_drugs", domain="medicine")


def gen_lexicon():
    """The plumb-line: every Strong's entry — Hebrew and Greek — with its word, transliteration,
    gloss and lexical range. Everything runs through the original tongues."""
    c = _conn("lexicon_bdbt")
    for (strongs, word, translit, gloss, definition) in c.execute(
            "select strongs,word,translit,gloss,definition from entries"):
        if not strongs:
            continue
        lang = "hebrew" if str(strongs).upper().startswith("H") else "greek"
        body = f"{word} ({translit}), Strong's {strongs}: {gloss}. {definition}"
        yield _card(f"card_src_lex_{_sk(strongs)}",
                    f"{strongs} — {word} ({translit}): {gloss}", body,
                    shelf="lexicon", subject=str(word),
                    bands=[str(strongs).lower(), str(word), str(translit), str(gloss), lang,
                           "lexicon", "original language"],
                    source_label="STEPBible TBESH/TBESG — Extended Strong's lexicon (CC-BY, Tyndale House)",
                    spine="card_spine_lexicon", domain="linguistics")


def gen_federal():
    """The federal shelf of the ark (lever 3, 2026-08-05): US-government publications fetched
    by store_book.py --ia-query into D:/NarrowHighway-Sources/archive_org/texts.db — public
    domain under 17 USC 105, every row carrying its waybill (origin URL + sha256). One stub
    card per held document; the full text is ON the ark, and the card says so."""
    ark = os.environ.get("CONCORDANCE_ARK_BASE", "").strip() or "D:/NarrowHighway-Sources"
    db_path = Path(ark) / "archive_org" / "texts.db"
    if not db_path.exists():
        raise FileNotFoundError(f"ark store not found at {db_path} (set CONCORDANCE_ARK_BASE)")
    shelf_of = [  # stored query fragment -> the shelf its documents truly serve
        ("military-manuals", "practical", "United States military field manuals (PD, 17 USC 105)"),
        ("Department of Agriculture", "agriculture", "USDA publications (PD, 17 USC 105)"),
        ("nasa_techdocs", "science", "NASA technical documents (PD, 17 USC 105)"),
        ("Forest Service", "ecology", "US Forest Service publications (PD, 17 USC 105)"),
        ("Public Health", "medicine", "US Public Health Service publications (PD, 17 USC 105)"),
        ("Geological Survey", "geology", "US Geological Survey publications (PD, 17 USC 105)"),
    ]
    c = sqlite3.connect(str(db_path))
    for ident, title, query, raw, url, sha in c.execute(
            "select identifier, title, query, raw_bytes, url, sha256 from docs order by identifier"):
        shelf, label = "practical", "US federal publication (PD, 17 USC 105)"
        for frag, sh, lb in shelf_of:
            if frag in (query or ""):
                shelf, label = sh, lb
                break
        t = (title or ident).strip() or ident
        body = (f"{t}. A United States federal publication, public domain (17 USC 105). "
                f"The full text ({(raw or 0):,} bytes) is held on the ark; waybill sha256 "
                f"{(sha or '')[:16]}…; origin archive.org/{ident}. A held source: this card "
                f"is the map, and the drive carries the freight.")
        card = _card(f"card_src_fed_{_sk(ident)}", t, body,
                     shelf=shelf, subject=t[:80],
                     bands=[t[:60], "federal", "public domain", shelf, "ark"],
                     source_label=label, spine="card_spine_federal", domain=shelf)
        card["source"]["url"] = url or f"https://archive.org/details/{ident}"
        yield card
    c.close()


GENERATORS = {"nuclides": gen_nuclides, "stars": gen_stars, "ports": gen_ports,
              "worldbank": gen_worldbank, "foods": gen_foods, "words": gen_words,
              "places": gen_places, "drugs": gen_drugs, "lexicon": gen_lexicon,
              "federal": gen_federal}


def main() -> int:
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    # spines are git-tracked content (small); source cards are generated data (large, gitignored)
    (out / "source_spines.jsonl").write_text(
        "\n".join(json.dumps(s, ensure_ascii=False) for s in SPINES) + "\n", encoding="utf-8")

    seen_ids = set()
    n = 0
    per = {}
    failed = []
    tmp = out / "source_cards.jsonl.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        for name, gen in GENERATORS.items():
            if only and name not in only:
                continue
            cnt = 0
            try:
                for card in gen():
                    cid = card["id"]
                    if cid in seen_ids:
                        continue
                    seen_ids.add(cid)
                    f.write(json.dumps(card, ensure_ascii=False) + "\n")
                    cnt += 1
                    n += 1
            except Exception as e:  # a bad source must not sink the rest
                print(f"  !! {name}: {type(e).__name__}: {e}")
                failed.append(name)
            per[name] = cnt
            print(f"  {name:12s} {cnt:>8,} cards")
    # NEVER SHRINK A TRACKED KEEPING SILENTLY (the reference_cards lesson, applied here):
    # a failed generator or an --only subset would quietly rewrite 282k cards smaller.
    dest = out / "source_cards.jsonl"
    if dest.exists():
        old_n = sum(1 for _ in dest.open(encoding="utf-8"))
        if n < old_n:
            print(f"REFUSING to replace: new {n:,} < held {old_n:,} "
                  f"(failed: {', '.join(failed) or 'none'}; only={sorted(only) if only else 'ALL'}) "
                  f"— the keeping stays; pass --shrink-ok to override deliberately")
            if "--shrink-ok" not in sys.argv:
                tmp.unlink()
                return 1
    os.replace(tmp, dest)
    print(f"TOTAL {n:,} technical source cards -> data/source_cards.jsonl  (spines: {len(SPINES)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
