#!/usr/bin/env python3
"""Card the languages of the earth — Glottolog + WALS (both CC-BY 4.0): family, region & phonology.

The languages deck was pending BY PRINCIPLE: its intended phonology source (PHOIBLE) is CC-BY-SA 3.0,
which the license gate refuses (viral copyleft; PHOIBLE is on `corpus._DISALLOWED_SOURCE`). That
withholding is the gate working as designed. So instead of circumventing it, we source LICENSE-CLEAN:

  * classification & geography from GLOTTOLOG (CC-BY 4.0) — name, family, macroarea, coordinates, ISO;
  * phonological typology from WALS (CC-BY 4.0) — consonant/vowel inventory size and tone, where WALS
    covers the language. NOT PHOIBLE's per-segment inventories (those need CC-BY-SA, and stay out).

Genesis 11 scattered the tongues; Acts 2 gathered them; here they are catalogued, license-clean. This
REPLACES the withheld PHOIBLE cards (same id scheme). Conduit, not source: each card is real Glottolog
(+ WALS) data, attributed, generated=False, nested under a languages spine → the Floor of Discovery.

Source CSVs, mirrored under <CONCORDANCE_LW_BASE>/:
  * glottolog/languages.csv  (github.com/glottolog/glottolog-cldf, CC-BY 4.0)
  * wals/{languages,values,codes}.csv  (github.com/cldf-datasets/wals, CC-BY 4.0)  — optional

    CONCORDANCE_LW_BASE=/home/nh/Lighthouse/lw/00_source python tools/card_glottolog.py
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_languages"
GLOTTO_LABEL = "Glottolog (CC-BY 4.0)"
BOTH_LABEL = "Glottolog + WALS (CC-BY 4.0)"
_slug = re.compile(r"[^a-z0-9]+")

# WALS phonology chapter (parameters 1A-19A) → the short keys we keep on each card.
WALS_PHON = {
    "1A": "consonant_inventory", "2A": "vowel_inventory", "3A": "consonant_vowel_ratio",
    "6A": "uvular_consonants", "8A": "lateral_consonants", "9A": "velar_nasal",
    "10A": "vowel_nasalization", "12A": "syllable_structure", "13A": "tone",
    "18A": "absent_common_consonants", "19A": "uncommon_consonants",
}


def _sk(*p) -> str:
    return _slug.sub("_", "-".join(str(x) for x in p).lower()).strip("_")


def _base() -> Path:
    b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
    return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")


def _load_wals(base: Path) -> Dict[str, Dict[str, str]]:
    """glottocode -> {phon_key: human label}, from WALS CLDF (CC-BY 4.0). Empty if WALS isn't mirrored."""
    wl = base / "wals"
    f_lang, f_val, f_code = wl / "languages.csv", wl / "values.csv", wl / "codes.csv"
    if not (f_lang.exists() and f_val.exists() and f_code.exists()):
        return {}
    gc_of: Dict[str, str] = {}
    with f_lang.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("Glottocode"):
                gc_of[r.get("ID")] = r["Glottocode"]
    label: Dict[str, str] = {}
    with f_code.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            label[r.get("ID")] = (r.get("Name") or "").strip()
    phon: Dict[str, Dict[str, str]] = {}
    with f_val.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            key = WALS_PHON.get(r.get("Parameter_ID"))
            if not key:
                continue
            gc = gc_of.get(r.get("Language_ID"))
            lbl = label.get(r.get("Code_ID") or "")
            if gc and lbl:
                phon.setdefault(gc, {})[key] = lbl
    return phon


def main() -> int:
    src = _base() / "glottolog" / "languages.csv"
    if not src.exists():
        print(f"glottolog languages.csv not found: {src}"); return 1
    with src.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    name_of = {r.get("Glottocode"): r.get("Name") for r in rows if r.get("Glottocode")}
    wals = _load_wals(_base())
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)

    spine = {
        "id": SPINE, "kind": "reference", "title": "The languages of the earth — Glottolog & WALS",
        "body": ("The world's languages by family and region, with their phonological typology where "
                 "known: each tongue's Glottolog classification and macroarea, and its WALS consonant/"
                 "vowel inventory and tone. The scattering of Babel and the gathering of Pentecost, "
                 "catalogued — a spine of the Floor of Discovery at the scale of human language."),
        "source": {"label": BOTH_LABEL, "url": "https://glottolog.org/",
                   "domain": "linguistics", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["languages", "linguistics", "glottolog", "wals", "phonology", "spine"],
        "subject": "the languages of the earth",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "human language, a spine of the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }
    (out / "language_spine.jsonl").write_text(json.dumps(spine, ensure_ascii=False) + "\n", encoding="utf-8")

    n = enriched = 0
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

            ph = wals.get(gc) or {}
            if ph:
                bits = []
                if ph.get("consonant_inventory"):
                    bits.append(f"{ph['consonant_inventory'].lower()} consonant inventory")
                if ph.get("vowel_inventory"):
                    bits.append(f"{ph['vowel_inventory'].lower()} vowel inventory")
                if ph.get("tone"):
                    bits.append(ph["tone"].lower())
                if bits:
                    body += " Phonology (WALS): " + "; ".join(bits) + "."
                enriched += 1
            src_label = BOTH_LABEL if ph else GLOTTO_LABEL

            bands = [b for b in (name.lower(), iso.lower(), fam.lower(), area.lower(),
                                 "language", "linguistics", ("phonology" if ph else "")) if b]
            extra = {"glottocode": gc, "iso": iso, "family": fam, "isolate": isolate,
                     "macroarea": area, "lat": lat, "lon": lon, "countries": countries}
            if ph:
                extra["phonology"] = ph
            card = {
                "id": f"card_src_lang_{_sk(gc)}", "kind": "reference", "title": title[:180], "body": body,
                "source": {"label": src_label, "url": f"https://glottolog.org/resource/languoid/id/{gc}",
                           "domain": "linguistics", "authority_tier": "reference"},
                "shelf": "languages", "box": "source", "bands": bands, "subject": name,
                "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                                 "evidence": "a language of the earth"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
                "extra": extra,
            }
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, out / "language_cards.jsonl")
    print(f"carded {n:,} languages (Glottolog CC-BY 4.0), {enriched:,} enriched with WALS phonology "
          f"(CC-BY 4.0) -> data/language_cards.jsonl  (+1 spine)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
