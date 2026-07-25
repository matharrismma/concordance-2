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
                    shelf="nuclear physics", subject=nuc,
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


GENERATORS = {"nuclides": gen_nuclides, "stars": gen_stars, "ports": gen_ports,
              "worldbank": gen_worldbank, "foods": gen_foods}


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
            per[name] = cnt
            print(f"  {name:12s} {cnt:>8,} cards")
    os.replace(tmp, out / "source_cards.jsonl")
    print(f"TOTAL {n:,} technical source cards -> data/source_cards.jsonl  (spines: {len(SPINES)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
