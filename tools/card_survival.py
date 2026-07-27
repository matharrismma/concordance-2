#!/usr/bin/env python3
"""The field library — outdoor, survival, bushcraft, and homestead knowledge, from PD sources.

Matt, 2026-07-26: "Make sure it has the outdoor knowledge and survival built into the main tool …
it's all of the almanac and apothecary along with the farming and survival knowledge from PD
sources … bushcraft, military guides and handbooks, old scout books, or wisdom from older sources
that still applies."

This serves the families and communities that most need us — the off-grid home, the prepared
household, the radio and homestead folk, anyone the world prices out of resilience. It sits beside
the Almanac (facts + weather) and the Apothecary (herbs + remedies) as the practical outdoor body.

DISCIPLINE (load-bearing):
  • Strict PUBLIC DOMAIN sources only — US-government works (the U.S. Army Survival Manual FM 21-76,
    field first-aid manuals, CDC/EPA/Ready.gov guidance, USDA bulletins) and pre-1929 classics
    (the 1911 Boy Scouts Handbook; Nessmuk's & Kephart's woodcraft). Each card is attributed.
  • Gather, don't author: each card carries proven, established field knowledge from a named source
    — generated=False, never an LLM's invention. Curated + git-tracked.
  • Safety over bravado: survival/medical cards are conservative and say plainly when to seek trained
    help; they are reference, NOT a substitute for hands-on training or a doctor. The boundary card
    is loaded first-class into the shelf.
  • NO ORPHANS: every card is member_of the survival SPINE, which is part_of the Floor of Discovery.

    PYTHONPATH=src python tools/card_survival.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_survival"
_slug = re.compile(r"[^a-z0-9]+")

# (slug, title, box, source_label, source_url, keywords, body)
FM2176 = "U.S. Army Survival Manual FM 21-76 (public domain)"
BSA1911 = "Boy Scouts of America Handbook, 1911 (public domain)"
USDA_CAN = "USDA Complete Guide to Home Canning (public domain)"
WOODCRAFT = "Kephart, Camping and Woodcraft (1917) & Nessmuk, Woodcraft (1884) — public domain"
CDC_WATER = "CDC/EPA emergency water guidance (U.S. government, public domain)"
READY = "Ready.gov / FEMA (U.S. government, public domain)"
USDA_BUL = "USDA Farmers' Bulletins (public domain)"

CARDS = [
    ("rule_of_threes", "The rule of threes — what to solve first", "priorities", FM2176, "",
     "survival priorities order first air breathing shelter exposure water food how long can you survive without",
     "A rule of thumb for what kills first, so you spend effort in the right order: roughly 3 minutes "
     "without air, 3 hours without shelter in harsh cold or heat, 3 days without water, 3 weeks without "
     "food. Exposure — not hunger — is the usual killer. Fix breathing and bleeding, then shelter and "
     "warmth, then water, then food. Stop, think, observe, plan before you move."),
    ("purify_water", "Making water safe to drink", "water", CDC_WATER, "https://www.cdc.gov/healthywater/emergency/making-water-safe.html",
     "purify water safe drink boil bleach disinfect clean dirty contaminated giardia treat filter purification bottle container pot how to",
     "Boiling is surest: bring clear water to a ROLLING boil for 1 minute (3 minutes above ~6,500 ft), "
     "let cool. No fire? Use unscented household bleach (5–9% sodium hypochlorite): 2 drops per quart/"
     "liter of clear water (4 drops if cold or cloudy), stir, wait 30 minutes — it should smell faintly "
     "of chlorine. Cloudy water: filter through a clean cloth or let it settle FIRST, then boil or treat. "
     "Purify every wild source, however clean it looks."),
    ("find_water", "Finding water in the wild", "water", FM2176, "",
     "find water wild source spring stream rain dew solar still transpiration bag where to look thirsty",
     "Look downhill and in green valleys, at the base of cliffs, and where animals trail. Rainwater and "
     "morning dew (sponged from grass) are among the safest. Running water above human habitation beats "
     "stagnant. A clear plastic bag tied over a leafy live branch collects clean transpired water in a "
     "day. Avoid water near dead animals or heavy algae. Purify all of it before drinking."),
    ("make_fire", "Making and keeping a fire", "fire", FM2176, "",
     "make build fire start tinder kindling fuel spark friction matches lighter flint steel ferro lens magnifying warmth cook how to",
     "Gather far more than you think: fine dry TINDER (birch bark, dry grass, fatwood shavings, char "
     "cloth), pencil-thin KINDLING, then FUEL wood. Build a small nest, take your spark or flame to the "
     "tinder low and shielded from wind, and feed it from small to large. Keep a dry reserve under cover. "
     "Site it on bare earth or stone, clear of overhanging brush, and never leave it unattended."),
    ("build_shelter", "Building a survival shelter", "shelter", FM2176, "",
     "build shelter survival lean-to debris hut warmth exposure cold insulate ground protection tarp poncho rope cord branches leaves how to",
     "Shelter beats almost everything but breathing — exposure kills fast. Get out of wind and wet, and "
     "INSULATE yourself from the ground (a foot of dry leaves or boughs) — you lose more heat to the cold "
     "earth than to the air. Keep the space SMALL so your body heats it. A leaning ridgepole thatched "
     "with boughs (lean-to), a leaf-packed debris hut, or a snow trench all work. Site away from "
     "flood channels, dead limbs, and avalanche paths."),
    ("hypothermia", "Cold injury: hypothermia and frostbite", "first_aid", FM2176, "",
     "hypothermia cold freezing frostbite shivering confusion warm rewarm treat signs symptoms exposure",
     "Hypothermia signs: hard shivering, then the 'umbles' — stumbles, mumbles, fumbles, grumbles — and "
     "confusion as it worsens. Get the person dry, insulate from the ground, add layers and a windbreak, "
     "give warm sweet drinks if fully awake, and warm the core gradually (not fast heat to the limbs). "
     "Frostbite: hard, waxy, numb skin — do NOT rub; rewarm gently in warm (not hot) water and protect "
     "from refreezing. Seek trained medical help as soon as you can."),
    ("heat_illness", "Heat injury: exhaustion and heat stroke", "first_aid", READY, "https://www.ready.gov/heat",
     "heat illness exhaustion stroke hot sweating dehydration cool shade emergency signs treat summer",
     "Heat exhaustion — heavy sweat, weakness, nausea, cool clammy skin: move to shade, lie down, loosen "
     "clothing, sip water, cool the skin. Heat STROKE — hot skin, confusion, fainting, often little "
     "sweat — is a life-threatening emergency: cool the body aggressively (shade, wet cloths, fanning, "
     "cold packs to neck/armpits/groin) and get emergency help immediately. Prevent both: water, shade, "
     "and rest in the heat of the day."),
    ("stop_bleeding", "Stopping severe bleeding", "first_aid", "U.S. Army First Aid field manual (FM 4-25.11 / FM 21-11), public domain", "",
     "stop severe bleeding wound blood pressure tourniquet first aid injury cut hemorrhage emergency how to",
     "Life-threatening bleeding is minutes to death — act now. Press HARD directly on the wound with a "
     "cloth or your hand and keep pressing; add dressings on top, don't lift to peek. For an arm or leg "
     "bleed you cannot stop, apply a tourniquet 2–3 inches above the wound (not on a joint), tighten "
     "until bleeding stops, and write down the TIME. Treat for shock and get the person to professional "
     "care fast. This is reference — get hands-on first-aid training before you need it."),
    ("treat_shock", "Recognizing and treating shock", "first_aid", "U.S. Army First Aid field manual (public domain)", "",
     "shock first aid pale cold clammy rapid pulse faint injury treat lay down elevate legs warm",
     "After serious injury or blood loss the body can go into shock: pale, cold, clammy skin, fast weak "
     "pulse, rapid breathing, confusion or faintness. Lay the person down, raise the legs about a foot "
     "(unless a head, spine, or leg injury forbids it), keep them warm and calm, control any bleeding, "
     "give nothing to eat or drink, and get emergency help. Reassurance itself steadies them."),
    ("edibility_test", "The universal edibility test — and its warning", "food", FM2176, "",
     "edible wild plants foraging test poison safe to eat forage food unknown plant universal edibility",
     "MANY wild plants are deadly, and no test is foolproof — when in doubt, do without, and never eat "
     "fungi you cannot positively identify. If you must test an unknown plant in true survival, the FM "
     "21-76 procedure is slow and one part at a time: fast 8 hours; test only one plant part; smell it; "
     "rub it on your inner wrist and wait; touch it to the lip, then tongue, then chew a small bit and "
     "hold 15 minutes — any burning, itching, or numbness means stop. Cook when you can. Learn your "
     "region's known edibles from a trusted local guide BEFORE you need them."),
    ("fish_trap", "Catching food: fishing and simple traps", "food", FM2176, "",
     "fishing trapping snare hunting food catch fish improvised hook trap survival protein game how to",
     "Calories from animals usually beat foraging. Improvise hooks from thorns, bone, or wire; set "
     "baited lines and check them often; fish are most active at dawn and dusk near cover. Simple snares "
     "on game trails and at burrow mouths work while you do other tasks — set many. Know and obey local "
     "hunting and fishing law except in genuine life-or-death need; conserve your energy for the traps "
     "that feed you."),
    ("navigate", "Finding direction without a compass", "navigation", FM2176, "",
     "navigate direction without compass sun stars north polaris shadow stick lost wayfinding how to find",
     "The sun rises in the east and sets in the west. Shadow-stick method: mark a stick's shadow tip, "
     "wait ~15 minutes, mark it again — the line from first to second mark runs roughly west-to-east. "
     "At night in the north, find Polaris (the North Star) by following the two 'pointer' stars at the "
     "end of the Big Dipper's cup; Polaris marks true north. Moss on trees is NOT a reliable guide. Pick "
     "a distant landmark and walk to it to keep a straight line."),
    ("signal_rescue", "Signaling for rescue", "signaling", FM2176, "",
     "signal rescue help distress mirror whistle fire smoke ground to air SOS three lost found how to",
     "THREE of anything means distress — three fires in a triangle, three whistle blasts, three flashes. "
     "By day: signal mirror aimed at aircraft (flash toward the sun's reflection), bright smoke (green "
     "boughs on the fire), and large ground symbols — a big 'V' means need assistance, 'X' need medical "
     "help. By night: fire and light. Make signals BIG and high-contrast against their background, and "
     "stay near shelter and water while you wait."),
    ("read_weather", "Reading the weather", "weather", "Traditional weather lore + almanac wisdom (public domain)", "",
     "weather read sky red morning storm coming clouds wind barometer forecast predict rain almanac signs",
     "Older wisdom that still holds a truth: 'Red sky at night, sailor's delight; red sky at morning, "
     "sailors take warning' — a red dawn often means the fair weather has already passed east and wet is "
     "coming. Falling pressure, a wind that shifts (backs) counter-clockwise, and high wispy clouds "
     "thickening and lowering all warn of an approaching front. Rings around sun or moon (thin high "
     "cloud) often precede rain within a day. Watch the sequence, not one sign."),
    ("knots", "The knots worth knowing", "skills", BSA1911, "",
     "knots bowline square reef two half hitches taut line clove hitch rope tie lashing scout how to",
     "A few knots cover most needs. BOWLINE: a fixed loop that won't slip or jam — for rescue and "
     "securing a line. SQUARE (reef) knot: joins two ropes of equal size, for bundles and bandages. TWO "
     "HALF-HITCHES: ties a rope to a post or ring. TAUT-LINE HITCH: an adjustable loop that holds "
     "tension — for tent guy-lines. CLOVE HITCH: a quick start for lashings. Practice them until your "
     "hands know them in the dark."),
    ("camp_hygiene", "Camp sanitation — the silent killer", "health", FM2176, "",
     "sanitation hygiene camp latrine waste disease clean hands water sickness diarrhea health survival",
     "In the field, disease fells more people than the cold or the animals. Site your latrine downhill "
     "and well away (200 ft / 60 m) from any water and from camp; cover waste. Wash hands before eating "
     "and after the latrine — even a rinse and a cloth helps. Purify all drinking water, keep food "
     "covered and cooked, and keep your body and gear dry. Cleanliness is survival, not luxury."),
    ("cutting_tools", "The knife, the axe, and cordage", "skills", WOODCRAFT, "",
     "knife axe baton carve wood cordage rope natural fibers bushcraft woodcraft tools cutting how to",
     "A sharp knife is the woodsman's first tool: cut away from yourself, keep the edge keen, and split "
     "kindling by 'batoning' — tapping the blade's spine through the wood with a stick. Make cordage by "
     "twisting plant fibers (inner bark, nettle, yucca) into a two-ply reverse-wrap. Keep steel dry and "
     "oiled against rust. A dull tool is more dangerous than a sharp one — it slips."),
    ("canning", "Preserving food: safe home canning", "homestead", USDA_CAN, "https://nchfp.uga.edu/how/can_home.html",
     "canning can preserve food jars water bath pressure botulism acid vegetables meat fruit store safely safe homestead how to",
     "Two methods, and choosing wrong can be deadly. HIGH-ACID foods (fruits, jams, pickles, properly "
     "acidified tomatoes) are safe by BOILING-WATER-BATH canning. LOW-ACID foods (vegetables, meats, "
     "beans, soups) MUST be PRESSURE canned — boiling alone will not kill botulism spores. Use tested, "
     "current USDA recipes and processing times, correct headspace and lids, and never improvise the "
     "process. If a jar's seal failed, the lid bulges, or it smells wrong — do not taste it; discard it."),
    ("dry_store", "Drying and root-cellaring the harvest", "homestead", USDA_BUL, "",
     "drying dehydrate food storage root cellar preserve vegetables fruit keep winter store homestead how to",
     "Drying is the oldest, simplest preservation: thin slices in a warm, airy, shaded place or a low "
     "oven/dehydrator until leathery or brittle; store airtight in the dark. A root cellar (cool ~32–40°F, "
     "humid, dark) keeps potatoes, carrots, beets, apples, cabbage, and winter squash for months — keep "
     "fruit and vegetables separate, and cull anything spoiling so 'one bad apple' doesn't spread. Label "
     "everything with the date."),
    ("kitchen_garden", "The kitchen garden", "homestead", USDA_BUL, "",
     "garden vegetables grow plant soil sun spacing frost dates succession water food homestead how to",
     "Grow where there is at least 6 hours of sun and workable, drained soil enriched with compost. "
     "Know your last spring and first fall FROST dates — plant cool crops (peas, greens, roots) early, "
     "warm crops (tomatoes, beans, squash) only after frost. Give plants room to reach full size, water "
     "deeply at the roots in the morning, mulch to hold moisture and stop weeds, and sow a little every "
     "few weeks (succession) for a steady harvest instead of a glut."),
    ("save_seed", "Saving your own seed", "homestead", USDA_BUL, "",
     "seed saving save heirloom open pollinated garden self sufficient store dry harvest homestead how to",
     "Seed you save closes the circle and costs nothing. Save only from OPEN-POLLINATED (heirloom) "
     "plants — hybrids ('F1') won't come true. Let the best, healthiest plants fully ripen; scoop and "
     "dry the seed thoroughly (wet seeds like tomato ferment a few days first, then dry); store bone-dry "
     "in a cool, dark place, labeled with variety and year. Most vegetable seed stays viable several "
     "years."),
    ("compost", "Building soil with compost", "homestead", USDA_BUL, "",
     "compost soil fertility manure greens browns rot pile garden fertilizer homestead how to make",
     "Compost turns scraps into free fertility. Layer 'greens' (kitchen scraps, fresh grass, manure — "
     "nitrogen) with more 'browns' (dry leaves, straw, cardboard — carbon), keep it as damp as a wrung "
     "sponge, and turn it every week or two for air. It heats, shrinks, and in a few months becomes dark, "
     "sweet-smelling crumbly soil. Keep meat, dairy, and pet waste out of the pile."),
    ("keep_chickens", "Keeping a few laying hens", "homestead", "USDA poultry Farmers' Bulletins (public domain)", "",
     "chickens hens eggs poultry coop keep raise feed predators homestead livestock food how to",
     "A few hens give eggs, pest control, and manure. Give each bird room in a dry, draft-free coop with "
     "a roost, nest boxes, and a secure run — predators (raccoons, dogs, hawks) are the main loss, so "
     "hardware cloth and a locked door at dusk matter. Feed a layer ration, offer grit and extra calcium "
     "(crushed shell), and always fresh water. Collect eggs daily. Hens lay best in their first two "
     "years and slow in deep winter without light."),
]

BOUNDARY = (
    "THE FIELD LIBRARY — what this is, and is not. These cards gather established outdoor, survival, "
    "and homestead knowledge from trusted PUBLIC-DOMAIN sources: the U.S. Army Survival Manual (FM "
    "21-76), public-domain military first-aid manuals, CDC/EPA/Ready.gov guidance, the 1911 Boy Scouts "
    "Handbook, the woodcraft classics of Nessmuk and Kephart, and USDA farming bulletins. It is "
    "reference and preparation — NOT a substitute for hands-on training, and never for a doctor or "
    "emergency services when they can be reached. Get trained before you need it; obey local law; when "
    "a life is in danger and help is reachable, call for it. Prepared, not fearful (Proverbs 22:3).")


def _sk(name: str) -> str:
    return _slug.sub("_", name.lower()).strip("_")


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The field library — outdoor, survival, bushcraft & homestead knowledge",
        "body": ("Practical knowledge for the prepared and the off-grid — water, fire, shelter, first "
                 "aid, food, navigation, signaling, weather, and the homestead skills of preserving, "
                 "growing, and keeping. Gathered from public-domain field manuals, scout handbooks, "
                 "woodcraft classics, and USDA bulletins. Stands beside the Almanac and the Apothecary "
                 "as the outdoor body of the keeping."),
        "source": {"label": "The field library (curated, public domain)", "url": "", "domain": "survival",
                   "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["survival", "outdoors", "bushcraft", "prepper", "homestead", "field", "wilderness", "spine"],
        "subject": "outdoor and survival knowledge",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "practical knowledge of the created order, a spine of the Floor of Discovery"}],
        "author": "Matt Harris (the field library)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
        "extra": {"license": "public-domain"},
    }
    cards = [spine]
    for slug, title, box, src_label, src_url, keywords, body in CARDS:
        cards.append({
            "id": f"card_survival_{slug}", "kind": "reference", "title": title,
            "body": f"{body}  — {src_label}.",
            "source": {"label": src_label, "url": src_url, "domain": "survival", "authority_tier": "reference"},
            "shelf": "survival", "box": box,
            "bands": (["survival", box.replace("_", " "), "outdoors", "how to"] + keywords.split())[:24],
            "subject": title,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"field knowledge ({box.replace('_', ' ')})"}],
            "author": "Matt Harris (the field library)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"category": box, "source": src_label, "license": "public-domain"},
        })
    cards.append({
        "id": "card_survival_boundary", "kind": "reference", "title": "The field library — reference, not a substitute for training",
        "body": BOUNDARY,
        "source": {"label": "The boundary", "url": "", "domain": "survival", "authority_tier": "reference"},
        "shelf": "survival", "box": "principle",
        "bands": ["boundary", "safety", "training", "disclaimer", "survival", "first aid", "law"],
        "subject": "the field library boundary",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": "the boundary of the field library"}],
        "author": "Matt Harris (the field library)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    })
    out = Path("data") / "survival_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards) - 1} field-library entries (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
