#!/usr/bin/env python3
"""RETIRED 2026-09-24 — do not run. Kept for the record only.

PHOIBLE 2.0 is CC-BY-SA 3.0 (viral copyleft), which the license gate refuses: it is on
`corpus._DISALLOWED_SOURCE`, so its cards were minted but NEVER publicly served. The languages deck is
now seeded LICENSE-CLEAN from Glottolog CC-BY 4.0 via `tools/card_glottolog.py` (family & region; the
phoneme inventories stay out). This seeder will NOT run: re-running it would overwrite
`data/language_cards.jsonl` with the withheld PHOIBLE cards and dark the languages deck on the next
shard rebuild. It is preserved as the documentary record of the PHOIBLE attempt and why it was refused.

(Original intent: PHOIBLE 2.0 + Glottolog — the phonological inventory of 2,177 languages, one card
each. The scattering of Babel, catalogued. Blocked on license, not on merit.)
"""
from __future__ import annotations

import sys


def main() -> int:
    print("RETIRED: card_phoible.py does not run. PHOIBLE is CC-BY-SA 3.0 — refused by the license "
          "gate (corpus._DISALLOWED_SOURCE) and never publicly served. The languages deck is seeded "
          "license-clean from Glottolog CC-BY 4.0 via tools/card_glottolog.py. Re-running this would "
          "overwrite data/language_cards.jsonl with withheld cards and dark the deck.")
    return 2


def _retired_original() -> int:
    """The original PHOIBLE seeder, kept unreachable for the record. Never called."""
    import json
    import os
    import re
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    FLOOR = "card_k_floor_of_discovery"
    SPINE = "card_spine_languages"
    _slug = re.compile(r"[^a-z0-9]+")

    def _sk(*p):
        return _slug.sub("_", "-".join(str(x) for x in p).lower()).strip("_")

    def _base() -> Path:
        b = os.environ.get("CONCORDANCE_LW_BASE", "").strip()
        return Path(b) if b else Path("D:/nh-backup/mirror/repo/lw/00_source")

    src = _base() / "phoible" / "phoible_index.json"
    if not src.exists():
        print(f"phoible index not found: {src}"); return 1
    data = json.loads(src.read_text(encoding="utf-8"))
    langs = data.get("by_glottocode", {})
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    spine = {
        "id": SPINE, "kind": "reference", "title": "The languages of the earth — PHOIBLE",
        "body": ("The phonological inventory of the world's languages: each tongue's family, region, "
                 "and the consonants, vowels and tones it speaks with. The scattering of Babel and the "
                 "gathering of Pentecost, catalogued — a spine of the Floor of Discovery at the scale "
                 "of human language."),
        "source": {"label": "PHOIBLE 2.0 + Glottolog (CC-BY-SA 3.0 / CC-BY 4.0)", "url": "https://phoible.org/",
                   "domain": "linguistics", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["languages", "linguistics", "phoible", "glottolog", "phonology", "spine"],
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
        for gc, v in langs.items():
            name = str(v.get("name") or gc)
            iso = str(v.get("iso") or "")
            fam = str(v.get("family") or "")
            area = str(v.get("macroarea") or "")
            nph, ncon, nvow, ntone = (v.get("n_phonemes"), v.get("n_consonants"),
                                      v.get("n_vowels"), v.get("n_tones"))
            title = f"{name}" + (f" ({iso})" if iso else "") + (f" — {fam}" if fam else "")
            body = (f"{name}" + (f", a language of the {fam} family" if fam else "")
                    + (f" ({area})" if area else "") + "."
                    + (f" {nph} phonemes: {ncon} consonants, {nvow} vowels, {ntone} tones." if nph else "")
                    + (f" ISO 639-3: {iso}." if iso else "") + f" Glottocode {gc}.")
            card = {
                "id": f"card_src_lang_{_sk(gc)}", "kind": "reference", "title": title[:180], "body": body,
                "source": {"label": "PHOIBLE 2.0 + Glottolog (CC-BY-SA 3.0 / CC-BY 4.0)",
                           "url": f"https://phoible.org/languages/{gc}", "domain": "linguistics",
                           "authority_tier": "reference"},
                "shelf": "languages", "box": "source",
                "bands": [name.lower(), iso.lower(), fam.lower(), area.lower(), "language", "linguistics"],
                "subject": name,
                "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                                 "evidence": "a language of the earth"}],
                "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
                "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
                "extra": {"glottocode": gc, "iso": iso, "family": fam, "macroarea": area,
                          "lat": v.get("lat"), "lon": v.get("lon"), "n_phonemes": nph,
                          "n_consonants": ncon, "n_vowels": nvow, "n_tones": ntone,
                          "consonants": (v.get("consonants") or [])[:40], "vowels": (v.get("vowels") or [])[:40]},
            }
            f.write(json.dumps(card, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, out / "language_cards.jsonl")
    print(f"carded {n:,} languages -> data/language_cards.jsonl  (+1 spine)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
