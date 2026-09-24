#!/usr/bin/env python3
"""Card the languages of the earth — Glottolog (CC-BY 4.0): family & region.

The languages deck was pending BY PRINCIPLE: its intended phonology source (PHOIBLE, CC-BY-SA 3.0) is
refused by the license gate — viral copyleft may not be publicly redistributed here, and PHOIBLE is on
`corpus._DISALLOWED_SOURCE`. Glottolog's OWN languoid data is CC-BY 4.0 (attribution only), which the
gate ALLOWS. So we card the world's languages BY FAMILY AND REGION from Glottolog directly — name,
family, macroarea, coordinates, ISO 639-3 — WITHOUT PHOIBLE's phoneme inventories (those stay out).
Genesis 11 scattered the tongues; Acts 2 gathered them; here they are catalogued, license-clean.

This REPLACES the withheld PHOIBLE cards (same id scheme, overwriting data/language_cards.jsonl) so the
languages shelf has one served source. Conduit, not source: each card is a real Glottolog languoid,
attributed, generated=False, nested under a languages spine → the Floor of Discovery. Re-runnable.

Source CSV: Glottolog CLDF `cldf/languages.csv` (github.com/glottolog/glottolog-cldf, CC-BY 4.0),
mirrored under <CONCORDANCE_LW_BASE>/glottolog/languages.csv.

    CONCORDANCE_LW_BASE=/home/nh/Lighthouse/lw/00_source python tools/card_glottolog.py
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_languages"
SRC_LABEL = "Glottolog (CC-BY 4.0)"
_slug = re.compile(r"[^a-z0-9]+")


def _sk(*p) -> str:
    return _slug.sub("_", "-".join(str(x) for x in p).lower()).strip("_")


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def main() -> int:
    src = _base() / "glottolog" / "languages.csv"
    if not src.exists():
        print(f"glottolog languages.csv not found: {src}"); return 1
    with src.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    name_of = {r.get("Glottocode"): r.get("Name") for r in rows if r.get("Glottocode")}
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)

    spine = {
        "id": SPINE, "kind": "reference", "title": "The languages of the earth — Glottolog",
        "body": ("The world's languages by family and region: each tongue's Glottolog classification, "
                 "its macroarea, and where it is spoken. The scattering of Babel and the gathering of "
                 "Pentecost, catalogued — a spine of the Floor of Discovery at the scale of human language."),
        "source": {"label": SRC_LABEL, "url": "https://glottolog.org/",
                   "domain": "linguistics", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["languages", "linguistics", "glottolog", "spine"],
        "subject": "the languages of the earth",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "human language, a spine of the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    (out / "language_spine.jsonl").write_text(json.dumps(spine, ensure_ascii=False) + "\n", encoding="utf-8")

    n = 0
    tmp = out / "language_cards.jsonl.tmp"
    with tmp.open("w", encoding="utf-8") as f:
        for r in rows:
            if (r.get("Level") or "").strip() != "language":
                continue
            gc = (r.get("Glottocode") or "").strip()
            if not gc:
                continue
            name = (r.get("Name") or gc).strip()
            iso = (r.get("ISO639P3code") or "").strip()
            fam_id = (r.get("Family_ID") or "").strip()
            fam = (name_of.get(fam_id) or "").strip() if fam_id else ""
            isolate = (r.get("Is_Isolate") or "").strip().lower() in ("true", "1", "yes")
            area = (r.get("Macroarea") or "").strip()
            lat, lon = r.get("Latitude") or "", r.get("Longitude") or ""
            countries = (r.get("Countries") or "").strip()
            fam_phrase = (f", a language of the {fam} family" if fam else
                          (", a language isolate" if isolate else ""))
            title = (f"{name}" + (f" ({iso})" if iso else "")
                     + (f" — {fam}" if fam else (" — isolate" if isolate else "")))
            body = (f"{name}{fam_phrase}" + (f", spoken in {area}" if area else "") + "."
                    + (f" ISO 639-3: {iso}." if iso else "") + f" Glottocode {gc}.")
            bands = [b for b in (name.lower(), iso.lower(), fam.lower(), area.lower(),
                                 "language", "linguistics") if b]
            card = {
                "id": f"card_src_lang_{_sk(gc)}", "kind": "reference", "title": title[:180], "body": body,
                "source": {"label": SRC_LABEL, "url": f"https://glottolog.org/resource/languoid/id/{gc}",
                           "domain": "linguistics", "authority_tier": "reference"},
                "shelf": "languages", "box": "source", "bands": bands, "subject": name,
                "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                                 "evidence": "a language of the earth"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
                "extra": {"glottocode": gc, "iso": iso, "family": fam, "isolate": isolate,
                          "macroarea": area, "lat": lat, "lon": lon, "countries": countries},
            }
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, out / "language_cards.jsonl")
    print(f"carded {n:,} languages (Glottolog CC-BY 4.0) -> data/language_cards.jsonl  (+1 spine)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
