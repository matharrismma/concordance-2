#!/usr/bin/env python3
"""The sanitation shelf — hygiene, waste, and disease prevention, from public-domain sources.

In a disaster or off-grid, the disease that follows BAD SANITATION kills more people than the event
itself — and it is almost entirely preventable with a few simple disciplines. This shelf teaches
them: wash hands, keep human waste away from people, water, and food, and break the routes disease
travels. It fills the gap the field library (survival) only touches, and stands beside the first-aid
shelf. Gathered from WHO, CDC, and US-military field-hygiene guidance — public domain.

DISCIPLINE:
  • PUBLIC-DOMAIN sources: WHO public health guidance, CDC / Ready.gov, and US Army field sanitation
    (FM 4-25.12 / PMBOK-adjacent field hygiene). Each card attributed.
  • Gather, don't author: established public-health practice — generated=False.
  • SAFETY: an outbreak or serious illness needs medical help and local health authority; the
    boundary card says so.
  • NO ORPHANS: every card is member_of the sanitation SPINE, part_of the Floor of Discovery.

    PYTHONPATH=src python tools/card_sanitation.py     # -> data/sanitation_cards.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_sanitation"
_slug = re.compile(r"[^a-z0-9]+")

WHO = "World Health Organization public health / WASH guidance (public reference)"
CDC = "CDC / Ready.gov emergency sanitation guidance (U.S. government, public domain)"
ARMY = "U.S. Army field sanitation & hygiene (FM 4-25.12, public domain)"

CARDS = [
    ("why", "Why sanitation is a life-or-death skill", "principle", WHO,
     "sanitation disease prevention disaster fecal oral route diarrhea cholera kills why important hygiene",
     "After a disaster or off-grid, dirty water and human waste spread diarrhea, cholera, typhoid, and "
     "hepatitis — and these kill more people, especially children, than the event itself. Almost all "
     "of it travels the FECAL-ORAL route: waste gets onto hands, into water, or onto food, and into a "
     "mouth. Break that route and you prevent most of it. Three disciplines do the heavy lifting: wash "
     "hands, keep human waste far from people/water/food, and keep drinking water clean. Sanitation "
     "isn't fussiness — it's survival."),
    ("handwashing", "Handwashing — the single most protective act", "hygiene", CDC,
     "handwashing wash hands soap water when how ash sand sanitizer tippy tap disease prevent germs",
     "Washing hands with soap breaks the disease chain more than anything else. Wash: after using the "
     "toilet or handling waste/diapers, before preparing or eating food, after tending the sick, and "
     "after handling animals. Wet, lather all surfaces for ~20 seconds (backs, between fingers, "
     "nails), rinse, air- or clean-cloth-dry. No soap? Ash or clean sand plus water scrubs nearly as "
     "well. Set up a hands-free 'tippy-tap' (a jug tipped by a foot-cord) by every latrine so water "
     "and soap are always there — convenience is what makes it happen."),
    ("human_waste", "Human waste — catholes, latrines, and bucket toilets", "waste", ARMY,
     "human waste latrine cathole pit toilet bucket dispose feces sanitation dig cover site how to",
     "Contain human waste so it can't reach people, water, or food. ON THE MOVE: a CATHOLE — dig 15–20 "
     "cm deep, at least 60 m (200 ft) from any water, use it, and cover it. FOR A CAMP OR STAY: a "
     "LATRINE — a deep, narrow pit with a cover/lid, sited DOWNHILL and 30 m+ from wells and water, "
     "away from the kitchen, with a screen for dignity; sprinkle soil, ash, or lime after each use to "
     "cut smell and flies. FOR A HOME with no plumbing: a lined BUCKET TOILET — after each use cover "
     "with sawdust, ash, peat, or soil, seal the lid, and dispose of or compost it properly."),
    ("waste_water_separation", "Keep waste downhill and far from your water", "waste", WHO,
     "latrine well water separation distance downhill 30 meters contaminate drinking source protect groundwater",
     "The commonest deadly mistake is putting waste near water. Site every latrine, animal pen, and "
     "waste pit DOWNHILL and at least 30 m (about 100 ft) from any well, spring, or water you drink — "
     "more in sandy or fractured ground where water moves fast. Never relieve yourself, wash, or "
     "bathe UPSTREAM of a drinking source. Protect a well with a raised lip and cover so surface "
     "runoff can't pour in. When you must choose a campsite, place the kitchen and water UPHILL, and "
     "the latrine and greywater DOWNHILL and downwind."),
    ("greywater", "Greywater — where the dishwater and wash water go", "waste", WHO,
     "greywater dishwater laundry wash water soak pit drain standing pooling mosquito disposal disperse",
     "Used water from washing dishes, clothes, and bodies (greywater) shouldn't pool — standing water "
     "breeds mosquitoes and smells. Strain out food scraps first (they draw flies and rodents), then "
     "let greywater soak away in a SOAK PIT (a hole filled with rocks/gravel) or spread it over "
     "ground away from the water source and the kitchen. Keep it away from the drinking supply. "
     "Biodegradable soap makes reuse on non-food plants possible. Never let wash water collect in "
     "open containers where children play or mosquitoes breed."),
    ("garbage", "Garbage and food waste — burn, bury, or compost", "waste", CDC,
     "garbage trash food waste disposal burn bury compost rodents flies pests smell camp home manage",
     "Waste that sits draws rats, flies, and disease. Separate it: burnable trash (burn cleanly, not "
     "plastics near people), organic food scraps (compost or bury deep, away from the kitchen), and "
     "anything that can't be burned or composted (bury or store sealed for later disposal). Keep food "
     "scraps and garbage in a covered container and deal with them daily — an open scrap heap by the "
     "kitchen is a rodent invitation and a fly nursery. A managed compost pile turns the organic waste "
     "into soil for the garden — waste becomes provision."),
    ("water_borne", "Water-borne disease — treat the water, wash the hands", "disease", WHO,
     "water borne disease cholera diarrhea typhoid treat water boil clean wash hands prevent outbreak sick",
     "Diarrheal disease (cholera, dysentery, typhoid) spreads through water and hands fouled by waste, "
     "and it kills fast by dehydration. Prevent it: make ALL drinking and cooking water safe (boil, "
     "filter, or chlorinate — see the field library), wash hands with soap, keep waste far from water, "
     "and keep flies off food. If someone gets watery diarrhea, rehydrate them immediately (the "
     "salt-and-sugar ORS drink) while you treat the cause and, in a serious or spreading case, seek "
     "medical help. Clean water plus clean hands stops most outbreaks before they start."),
    ("vectors", "Mosquitoes, flies, and rodents — cut the disease carriers", "disease", CDC,
     "mosquito fly rodent vector disease malaria dengue standing water nets drain screen food cover pest control",
     "Insects and rodents carry disease from waste to you. MOSQUITOES (malaria, dengue) breed in "
     "standing water — drain, cover, or empty every container, gutter, and puddle weekly; sleep under "
     "a net; cover skin at dusk. FLIES walk from latrines and garbage onto food — cover latrines and "
     "food, screen the kitchen, and clear waste daily. RODENTS spread disease and eat your stores — "
     "keep food in sealed hard containers, clear scraps, block their entry, and remove nesting clutter. "
     "Cut the carrier and you cut the disease."),
    ("sick_care", "Caring for the sick without catching it", "disease", WHO,
     "care sick isolate infection control hand washing waste disposal protect caregiver contagious quarantine home",
     "When you must nurse a contagious person at home: keep them in a separate, ventilated space if "
     "you can; have ONE caregiver who washes hands before and after every contact; give the patient "
     "their own cup, plate, and cloths; and dispose of their waste, vomit, and soiled cloths safely "
     "(bury or bag and seal, then wash hands). Keep the sick well hydrated and warm, and keep the "
     "healthy — especially children and the elderly — away. Disinfect surfaces the patient touches. "
     "If the illness is severe, spreading, or you don't know what it is, get medical help."),
    ("food_safety", "Keeping food from making you sick", "food", CDC,
     "food safety clean cook thoroughly store cool cross contamination spoiled when in doubt throw out prepare",
     "Off-grid food poisoning is dangerous when help is far. Four rules: CLEAN — wash hands, "
     "surfaces, and produce with safe water. SEPARATE — keep raw meat away from other food and use "
     "different boards/knives. COOK thoroughly — heat destroys most germs; reheat leftovers hot all "
     "through. CHILL / STORE — without a fridge, eat cooked food promptly, keep stores cool, dry, and "
     "sealed, and preserve the rest (drying, salting, canning — see the field library). When food "
     "smells wrong, is slimy, or you're unsure, throw it out — it isn't worth a night of vomiting far "
     "from care."),
]

BOUNDARY = (
    "THE SANITATION SHELF — what this is, and is not. These cards gather established public-health and "
    "field-hygiene practice from PUBLIC-DOMAIN sources: WHO WASH guidance, CDC / Ready.gov, and US Army "
    "field sanitation (FM 4-25.12). It is reference and preparation for keeping a household or camp "
    "healthy when services fail — NOT a substitute for professional public-health advice, and never "
    "for medical care in a serious or spreading illness. Obey local health authorities and boil-water "
    "notices. When disease spreads or someone is seriously ill, get help. Wash your hands. Prepared, "
    "not fearful (Proverbs 22:3).")


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The sanitation shelf — hygiene, waste, and disease prevention",
        "body": ("How to keep a household or camp healthy when the plumbing and services fail: "
                 "handwashing, human-waste disposal (catholes, latrines, bucket toilets), keeping "
                 "waste far from water, greywater and garbage, and breaking the routes of water-borne "
                 "and insect-borne disease. The disciplines that prevent the illness which follows a "
                 "disaster. From WHO, CDC, and Army field-hygiene sources. Beside the field library "
                 "and the first-aid shelf."),
        "source": {"label": "The sanitation shelf (curated, public domain)", "url": "",
                   "domain": "medicine", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["sanitation", "hygiene", "waste", "disease", "public health", "latrine", "handwashing",
                  "off grid", "prepper", "field", "spine"],
        "subject": "sanitation and hygiene",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "keeping the body and camp healthy, a spine of the Floor of Discovery"}],
        "author": "Matt Harris (the sanitation shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False, "extra": {"license": "public-domain"},
    }
    cards = [spine]
    for slug, title, box, src_label, keywords, body in CARDS:
        cards.append({
            "id": f"card_sanitation_{slug}", "kind": "reference", "title": title,
            "body": f"{body}  — {src_label}.",
            "source": {"label": src_label, "url": "", "domain": "medicine", "authority_tier": "reference"},
            "shelf": "sanitation", "box": box,
            "bands": (["sanitation", "hygiene", box.replace("_", " "), "off grid", "how to"] + keywords.split())[:24],
            "subject": title,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"sanitation and hygiene ({box})"}],
            "author": "Matt Harris (the sanitation shelf)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"category": box, "source": src_label, "license": "public-domain"},
        })
    cards.append({
        "id": "card_sanitation_boundary", "kind": "reference",
        "title": "The sanitation shelf — reference, not a substitute for a health authority",
        "body": BOUNDARY,
        "source": {"label": "The boundary", "url": "", "domain": "medicine", "authority_tier": "reference"},
        "shelf": "sanitation", "box": "principle",
        "bands": ["boundary", "safety", "public health", "sanitation", "hygiene", "disease"],
        "subject": "the sanitation shelf boundary",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": "the boundary of the sanitation shelf"}],
        "author": "Matt Harris (the sanitation shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    })
    out = Path("data") / "sanitation_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards) - 1} sanitation entries (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
