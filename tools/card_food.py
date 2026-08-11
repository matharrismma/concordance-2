#!/usr/bin/env python3
"""The food-growing shelf — raising your own food, from public-domain sources.

The field library (survival) teaches PRESERVING what you have; this shelf teaches GROWING more: a
survival garden, feeding the soil, saving seed, planting by season, and eating from your own ground
through the year. It is the difference between a stored pantry that empties and a garden that renews.
Gathered from USDA public-domain farming bulletins and extension guidance.

DISCIPLINE:
  • PUBLIC-DOMAIN sources: USDA Farmers' Bulletins and US-government agricultural guidance. Attributed.
  • Gather, don't author: established growing practice — generated=False.
  • SAFETY: never eat an unknown wild plant; the foraging card is conservative and the boundary says so.
  • NO ORPHANS: every card is member_of the food SPINE, part_of the Floor of Discovery.

    PYTHONPATH=src python tools/card_food.py     # -> data/food_cards.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_food"
_slug = re.compile(r"[^a-z0-9]+")

USDA = "USDA Farmers' Bulletins & extension guidance (U.S. government, public domain)"

CARDS = [
    ("survival_garden", "A survival garden — grow calories first", "garden", USDA,
     "survival garden grow food calories potatoes beans squash corn greens what to plant reliable staple",
     "In a real food crisis, grow CALORIES, then vitamins. Calorie-dense, storable staples that feed a "
     "family: potatoes (huge calories per square foot), dried beans (protein that stores for years), "
     "winter squash and pumpkins (calories + long keeping), and corn. Add fast, forgiving greens "
     "(kale, chard, lettuce) for vitamins and cabbage/carrots/beets for keeping. Start with a few "
     "reliable crops you'll actually eat, grow them well, and expand. A small, well-tended plot beats "
     "a big neglected one."),
    ("soil", "Feed the soil, not just the plant", "soil", USDA,
     "soil compost organic matter fertility nitrogen phosphorus potassium npk manure health build garden",
     "Healthy soil grows healthy food; poor soil grows failure. Build it with ORGANIC MATTER — "
     "compost, aged manure, leaf mold, cover crops turned in — which feeds soil life, holds water, and "
     "releases nutrients slowly. Plants need mainly NITROGEN (N, leafy growth), PHOSPHORUS (P, roots "
     "and fruit), and POTASSIUM (K, overall vigor), plus minerals. Compost and manure supply most of "
     "it. Test or watch your plants: pale = often nitrogen; test pH (most crops like slightly acidic "
     "to neutral). Never let bare soil erode — mulch or cover it."),
    ("seed_saving", "Saving seed — the harvest that never ends", "seed", USDA,
     "seed saving open pollinated heirloom hybrid f1 save dry store viability collect next year renew garden",
     "Saved seed makes a garden self-renewing and free. Save from OPEN-POLLINATED or HEIRLOOM varieties "
     "— they breed true. Do NOT save from HYBRID (F1) seed: its offspring won't match the parent. Let "
     "the best plants fully mature, collect the seed, DRY it thoroughly (damp seed rots or sprouts), "
     "and store it cool, dark, dry, and labeled with the variety and year. Most vegetable seed stays "
     "viable 2–5 years (some longer) if kept cool and dry. Save from your strongest plants each year "
     "and your seed adapts to your ground."),
    ("season", "Planting by season — frost dates and timing", "season", USDA,
     "planting season frost dates cool warm crops days to maturity succession calendar when to plant timing",
     "Timing decides the harvest. Learn your average LAST spring frost and FIRST fall frost — the span "
     "between is your growing season. COOL-season crops (peas, lettuce, spinach, brassicas, root veg) "
     "tolerate frost and grow in spring and fall; WARM-season crops (tomatoes, beans, squash, corn, "
     "peppers) need warm soil and die at frost — plant them after the last frost. Check each seed's "
     "'days to maturity' so it finishes before the season ends. SUCCESSION-plant quick crops every few "
     "weeks for a steady supply instead of one glut."),
    ("water_mulch", "Watering and mulching the garden", "care", USDA,
     "garden water deep mulch moisture weeds straw leaves conserve drought care how often plants roots",
     "Water DEEP and less often, not shallow and daily — deep watering drives roots down where they "
     "survive dry spells; shallow watering makes weak surface roots. Water in the cool morning to "
     "reduce loss and disease. MULCH heavily (straw, leaves, grass clippings, wood chips) around "
     "plants: it holds soil moisture, smothers weeds, feeds the soil as it breaks down, and keeps "
     "roots cool. Mulch can cut your watering in half — a critical saving when water is precious. Keep "
     "mulch a little back from stems to prevent rot."),
    ("companion_rotation", "Companion planting and crop rotation", "care", USDA,
     "companion planting crop rotation three sisters corn beans squash pest disease soil family garden plan",
     "Don't grow the same crop in the same spot year after year — ROTATE by plant family so pests and "
     "diseases can't build up and so heavy feeders (corn, brassicas) follow soil-builders (beans, "
     "peas, which fix nitrogen). Some plants help each other: the classic THREE SISTERS grows corn "
     "(a pole), beans (climbing the corn, feeding the soil), and squash (shading out weeds) together. "
     "Aromatic herbs and flowers (marigold, basil) can confuse or repel pests. A little planning turns "
     "the garden into a system that defends and feeds itself."),
    ("nutrition_balance", "Growing for nutrition, not just calories", "nutrition", USDA,
     "nutrition balance calories vitamins greens vegetables scurvy deficiency variety grow protein vitamin c",
     "A pile of potatoes keeps you alive but not well — long-term survival needs VITAMINS too. Grow a "
     "spread: staples for calories (potatoes, grains, beans), leafy GREENS and colorful vegetables for "
     "vitamins and minerals, and legumes for protein. Vitamin C (from fresh greens, peppers, tomatoes, "
     "cabbage, sprouts) prevents scurvy — a real risk on an all-stored-food diet. Fresh sprouts and "
     "greens through winter fill the gap when little else grows. Variety on the plate is variety in the "
     "garden."),
    ("root_cellar", "Root cellaring — winter storage without power", "store", USDA,
     "root cellar store winter potatoes carrots squash apples cool humid no power keep harvest months",
     "Many crops keep for months with no electricity if stored right. A ROOT CELLAR (a cool, humid, "
     "dark space — a basement corner, a buried barrel, an insulated pit) holds potatoes, carrots, "
     "beets, turnips, cabbage, and apples through winter. Different crops want different conditions: "
     "roots like cold and humid; onions, garlic, and winter squash like cool and DRY; apples give off "
     "a gas that ripens (and spoils) other produce, so store them apart. Cure potatoes and squash "
     "before storing, keep them from freezing, and check often — remove any that rot."),
    ("sprouting", "Sprouts and microgreens — fresh food in days", "garden", USDA,
     "sprouts microgreens grow indoors fast vitamins winter jar seeds beans no soil small space fresh greens",
     "When the garden is under snow, SPROUTS and MICROGREENS give fresh, vitamin-rich food in days, "
     "indoors, with almost no space or soil. Sprouts: rinse a spoonful of seeds/beans (alfalfa, mung, "
     "lentil, broccoli) in a jar, drain, and rinse twice a day — eat in 3–5 days. Microgreens: sow "
     "seeds thickly on a tray of soil or damp mat, give light, and snip the young shoots in 1–2 weeks. "
     "Both turn stored dry seed into living vitamins — a winter's difference between deficiency and "
     "health. Use seed meant for sprouting/eating, not treated garden seed."),
    ("foraging_safe", "Foraging — only what you certainly know", "forage", USDA,
     "foraging wild edible plants safe identify never unknown poisonous mushroom guide caution universal test",
     "Wild food can supplement the table, but a wrong identification can kill — so the rule is "
     "absolute: NEVER eat a wild plant or mushroom unless you are CERTAIN of it. Learn a few reliable, "
     "unmistakable local edibles from a trusted field guide and, ideally, a knowledgeable person, "
     "before you need them; know the dangerous look-alikes for each. Avoid wild MUSHROOMS entirely "
     "unless expertly identified — many deadly ones resemble edibles. The old 'universal edibility "
     "test' is slow and unreliable; certainty from knowledge is the only safe path. When unsure, don't."),
]

BOUNDARY = (
    "THE FOOD-GROWING SHELF — what this is, and is not. These cards gather established growing practice "
    "from PUBLIC-DOMAIN sources (USDA Farmers' Bulletins and US-government agricultural guidance). "
    "Gardens vary hugely by climate, soil, and season — treat these as starting principles and learn "
    "your own ground and local frost dates. NEVER eat a wild plant or mushroom you cannot identify with "
    "certainty. This is reference, not a substitute for local agricultural extension advice or a "
    "trusted guide. Start small, learn by doing, save your best seed. Prepared, not fearful (Proverbs "
    "22:3).")


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The food-growing shelf — raising your own food",
        "body": ("Growing more, beside the field library's preserving: a survival garden that grows "
                 "calories first, feeding the soil, saving open-pollinated seed, planting by frost "
                 "dates and season, watering deep and mulching, companion planting and rotation, "
                 "balancing calories with vitamins, root-cellaring for winter, and sprouts for fresh "
                 "food in the cold. From USDA public-domain farming guidance."),
        "source": {"label": "The food-growing shelf (curated, public domain)", "url": "",
                   "domain": "agriculture", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["food", "growing", "garden", "agriculture", "seed", "soil", "homestead", "off grid",
                  "prepper", "self reliance", "spine"],
        "subject": "growing food",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "raising food from the created order, a spine of the Floor of Discovery"}],
        "author": "Matt Harris (the food-growing shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False, "extra": {"license": "public-domain"},
    }
    cards = [spine]
    for slug, title, box, src_label, keywords, body in CARDS:
        cards.append({
            "id": f"card_food_{slug}", "kind": "reference", "title": title,
            "body": f"{body}  — {src_label}.",
            "source": {"label": src_label, "url": "", "domain": "agriculture", "authority_tier": "reference"},
            "shelf": "agriculture", "box": box,
            "bands": (["food", "growing", "garden", box.replace("_", " "), "how to"] + keywords.split())[:24],
            "subject": title,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"growing food ({box})"}],
            "author": "Matt Harris (the food-growing shelf)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"category": box, "source": src_label, "license": "public-domain"},
        })
    cards.append({
        "id": "card_food_boundary", "kind": "reference",
        "title": "The food-growing shelf — learn your ground; never eat the unknown",
        "body": BOUNDARY,
        "source": {"label": "The boundary", "url": "", "domain": "agriculture", "authority_tier": "reference"},
        "shelf": "agriculture", "box": "principle",
        "bands": ["boundary", "safety", "foraging", "food", "growing", "garden", "poison"],
        "subject": "the food-growing shelf boundary",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": "the boundary of the food-growing shelf"}],
        "author": "Matt Harris (the food-growing shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    })
    out = Path("data") / "food_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards) - 1} food-growing entries (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
