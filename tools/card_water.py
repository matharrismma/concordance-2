#!/usr/bin/env python3
"""The water shelf — the household water SYSTEM, from public-domain sources.

The field library (survival) teaches how to FIND and PURIFY water in an emergency; this shelf is the
standing SUPPLY: how much to store, how to store it safely, how to harvest rainwater and protect a
well, what the filter types actually remove, and how to make a household plan so the tap never runs
dry. Gathered from EPA, CDC/Ready.gov, and FEMA public guidance.

DISCIPLINE:
  • PUBLIC-DOMAIN sources: EPA drinking-water guidance, CDC / Ready.gov / FEMA emergency water. Each
    card attributed. (For emergency FINDING and PURIFYING, see the field library — not repeated here.)
  • Gather, don't author: established public guidance — generated=False.
  • SAFETY: unsafe water kills; when in doubt, treat it. The boundary card says so.
  • NO ORPHANS: every card is member_of the water SPINE, part_of the Floor of Discovery.

    PYTHONPATH=src python tools/card_water.py     # -> data/water_cards.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_water"
_slug = re.compile(r"[^a-z0-9]+")

EPA = "U.S. EPA drinking-water guidance (public domain)"
FEMA = "FEMA / Ready.gov emergency water guidance (U.S. government, public domain)"
CDC = "CDC water safety & storage guidance (U.S. government, public domain)"

CARDS = [
    ("how_much", "How much water to store — a gallon a day, and more", "store", FEMA,
     "how much water store per person per day gallon supply two weeks emergency ration drinking hygiene",
     "Store at least 1 US gallon (about 4 liters) per person PER DAY — roughly half for drinking, half "
     "for cooking and hygiene — and more in hot weather, for children, nursing mothers, the sick, and "
     "pets. Keep a minimum of two weeks' supply where you can; three days is the bare emergency floor. "
     "For a family of four, two weeks is 56+ gallons. Water is heavy (a gallon is ~3.8 kg / 8.3 lb), so "
     "spread storage across manageable containers, and know your refill sources before you need them."),
    ("storing", "Storing water so it stays safe", "store", CDC,
     "store water safely container food grade clean dark cool rotate bleach how long keep milk jug avoid",
     "Use clean, FOOD-GRADE containers (commercial water jugs, or well-scrubbed food buckets) — never "
     "old milk or juice jugs, whose sugars and proteins can't be fully cleaned and will grow bacteria. "
     "Fill with safe tap or treated water, seal tightly, label with the date, and keep in a cool, DARK "
     "place away from fuel, chemicals, and direct sun. Rotate/refresh commercially bottled water by its "
     "date and home-stored water every 6–12 months. If storing longer, add a few drops of unscented "
     "bleach per gallon, or re-treat before drinking."),
    ("rainwater", "Harvesting rainwater", "harvest", EPA,
     "rainwater harvesting collect roof barrel gutter first flush screen mosquito catchment treat storage",
     "A roof is a large water catcher: ~600 gallons per inch of rain on a 1,000 sq ft roof. Channel "
     "gutters into a covered BARREL or tank. Use a FIRST-FLUSH diverter (or just discard the first few "
     "minutes) so the dirtiest runoff — bird droppings, dust, roof grit — doesn't enter your store. "
     "SCREEN every opening against mosquitoes and debris, and keep the tank covered and dark to stop "
     "algae. Treat harvested water before drinking (filter + disinfect); untreated, it's fine for the "
     "garden, animals, flushing, and washing. Check local rules — a few places restrict collection."),
    ("wells", "Protecting a well or spring", "source", EPA,
     "well spring protect cap cover surface runoff contamination hand pump test treat groundwater safe",
     "A well or spring is a lasting source if you keep surface filth out of it. Cap and cover it, build "
     "the ground up so rain runs AWAY from it, and keep livestock, latrines, and fuel well uphill and "
     "at least 30 m (100 ft) distant. After a flood, or if the water changes color, smell, or taste, "
     "assume it's contaminated: disinfect the well and treat the water until you can test it. A manual "
     "HAND PUMP or a bucket-and-rope keeps a well working with no power. Know your water table depth "
     "and whether the source runs dry in drought."),
    ("filters", "Filters — what each kind actually removes", "treat", EPA,
     "water filter ceramic carbon hollow fiber sand biosand removes bacteria protozoa virus chemical sediment",
     "Not all filters do the same job. SEDIMENT/cloth filters remove dirt and grit only. CERAMIC and "
     "HOLLOW-FIBER (0.1–0.2 micron) filters remove bacteria and protozoa (giardia, crypto) but usually "
     "NOT viruses. ACTIVATED CARBON improves taste and removes many chemicals but not germs. A "
     "SAND/BIOSAND filter removes a lot with no cartridges. The safe rule: FILTER to clear the water "
     "and remove particles and most germs, THEN DISINFECT (boil, chlorine, or UV) to kill viruses and "
     "anything left. Filter plus disinfect covers what either alone misses."),
    ("clarify", "Making cloudy water clear before you treat it", "treat", CDC,
     "cloudy muddy water clear settle filter cloth sand sediment turbid before boil disinfect pretreat",
     "Disinfection (chlorine especially) works poorly on cloudy water — the particles shield germs and "
     "soak up the chlorine. So CLARIFY first: let muddy water SETTLE for an hour or more and pour off "
     "the clear top, and/or pour it through a clean cloth, a sand filter, or a coffee filter to strip "
     "the sediment. Only then boil or chlorinate. This one step makes emergency treatment actually "
     "work, and it's easy to skip when you're thirsty and in a hurry."),
    ("uses", "Matching water quality to the use", "plan", FEMA,
     "water uses potable drinking washing irrigation greywater conserve dont waste treated non drinking priority",
     "Treated drinking water is precious — don't spend it where lesser water will do. Reserve the "
     "cleanest, treated water for DRINKING, cooking, and medical use. Use untreated or lightly-treated "
     "water (rainwater, greywater) for washing, flushing, cleaning, animals, and the garden. Catch and "
     "reuse where you can — a basin under the tap, dishwater to non-food plants. In a shortage, "
     "prioritize drinking and hygiene of hands and food over everything else; you can go dirty far "
     "longer than you can go thirsty."),
    ("plan", "A household water plan", "plan", FEMA,
     "water plan household primary backup source storage treatment rotation how much prepare family ready",
     "Write it down before the tap fails. Name your PRIMARY source and at least one BACKUP (stored "
     "supply, rainwater, a well, a nearby stream). State how much you STORE (a gallon per person per "
     "day × your target days) and where. State your TREATMENT method and keep the supplies (bleach, "
     "filter, fuel to boil) on hand. Set a ROTATION reminder so stored water stays fresh. Teach every "
     "member where the water is and how to treat it. A plan on paper, tested once, beats improvising "
     "thirsty in the dark."),
    ("solar_still", "Last-resort water — the solar still", "emergency", FEMA,
     "solar still condensation water sun plastic sheet hole ground evaporate salt sea contaminated last resort",
     "When all water is salty, contaminated, or absent, a SOLAR STILL can wring a little clean water "
     "from the ground or from foul water using the sun. Dig a hole, set a clean container in the "
     "center, place any moisture source (damp soil, non-poisonous plants, even seawater) around it, "
     "cover the hole with a plastic sheet weighted with a stone over the container so the low point "
     "drips in, and seal the edges with soil. Sun evaporates water; it condenses on the plastic and "
     "drips down clean. Yield is small (often under a liter a day), so it's a supplement or last "
     "resort — but it turns bad water and dry ground into safe drops."),
]

BOUNDARY = (
    "THE WATER SHELF — what this is, and is not. These cards gather established water-supply and safety "
    "guidance from PUBLIC-DOMAIN sources (U.S. EPA, CDC, FEMA / Ready.gov). Unsafe water kills quickly, "
    "so when in doubt, TREAT it (see the field library for finding and purifying in an emergency). This "
    "is reference and preparation — NOT a substitute for a certified water test, a public boil-water "
    "notice, or professional advice on a well or a contamination event. Obey local water authorities. "
    "Prepared, not fearful (Proverbs 22:3).")


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The water shelf — the household water system",
        "body": ("The standing water supply, beside the field library's emergency finding and "
                 "purifying: how much water to store (a gallon per person per day), storing it "
                 "safely, harvesting rainwater, protecting a well, what filter types actually remove "
                 "(filter THEN disinfect), matching water quality to its use, and a household water "
                 "plan. From EPA, CDC, and FEMA public guidance."),
        "source": {"label": "The water shelf (curated, public domain)", "url": "",
                   "domain": "survival", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["water", "supply", "storage", "rainwater", "well", "filter", "purify", "off grid",
                  "prepper", "field", "spine"],
        "subject": "the household water supply",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "the water of life for the body, a spine of the Floor of Discovery"}],
        "author": "Matt Harris (the water shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False, "extra": {"license": "public-domain"},
    }
    cards = [spine]
    for slug, title, box, src_label, keywords, body in CARDS:
        cards.append({
            "id": f"card_water_{slug}", "kind": "reference", "title": title,
            "body": f"{body}  — {src_label}.",
            "source": {"label": src_label, "url": "", "domain": "survival", "authority_tier": "reference"},
            "shelf": "water", "box": box,
            "bands": (["water", "supply", box.replace("_", " "), "off grid", "how to"] + keywords.split())[:24],
            "subject": title,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"the water supply ({box})"}],
            "author": "Matt Harris (the water shelf)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"category": box, "source": src_label, "license": "public-domain"},
        })
    cards.append({
        "id": "card_water_boundary", "kind": "reference",
        "title": "The water shelf — when in doubt, treat it",
        "body": BOUNDARY,
        "source": {"label": "The boundary", "url": "", "domain": "survival", "authority_tier": "reference"},
        "shelf": "water", "box": "principle",
        "bands": ["boundary", "safety", "water", "treat", "test", "supply"],
        "subject": "the water shelf boundary",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": "the boundary of the water shelf"}],
        "author": "Matt Harris (the water shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    })
    out = Path("data") / "water_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards) - 1} water entries (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
