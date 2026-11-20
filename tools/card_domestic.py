#!/usr/bin/env python3
"""The domestic shelf — household health and cottage economy, from two public-domain books.

WHY THIS EXISTS. The keeping already held both of these books — and held nothing of them. The
catalogue carried `card_src_book_74359` and `card_src_book_32863`, each a 164-character stub on the
`gutenberg` shelf whose whole body is a title, a subject list and a link. Measured against the live
keeping, "how do I treat a burn at home" returned a parable about the tongue, and "my child has a
fever and will not eat" returned nursing-school review questions, while `first_aid` held 14 cards,
`sanitation` 11 and `foods` ZERO, against 125,167 on `pronunciation`. The acquisition had happened;
the minting never did.

  • William Buchan, *Domestic Medicine; or, A Treatise on the Prevention and Cure of Diseases by
    Regimen and Simple Medicines*, 12th ed., London 1791 (Project Gutenberg 74359).
  • William Cobbett, *Cottage Economy, to Which is Added The Poor Man's Friend*, New York 1833
    (Project Gutenberg 32863).

DISCIPLINE (load-bearing — this seed GATHERS, it does not author):
  • Every body is VERBATIM from the public-domain text. Nothing here is composed, paraphrased or
    summarised. `generated` is False and it is true. Cuts inside a passage are marked `[...]`;
    italic markers from the source are dropped, which is the only edit made.
  • The SELECTION IS AN ALLOWLIST IN THIS FILE, not a choice made at runtime. A generator that picks
    its own path is a destructive act; the path here is literal, reviewable and diffable.
  • TWO DENYLISTS, enforced in main(), which EXITS NON-ZERO rather than writing a bad shelf:
      HAZARD    — Buchan is 1791. Where he prescribes bleeding, mercury, antimony, opium, blisters,
                  purges or vomits he is DANGEROUS, and none of that is carried. Only the regimen
                  half of the book is drawn on (Chapters IV Air, VIII Cleanliness, IX Infection),
                  which is prevention and nursing care, not treatment.
      PREJUDICE — Cobbett is 1833 and a polemicist. His potato passage disparages the Irish, and he
                  argues paper money, schooling and "happy poverty" at length. None of that is
                  carried either; only the practical instruction and his definition of economy.
  • A BOUNDARY CARD PER BOOK, in the author's own words where he gave them. Buchan wrote that his
    book was "never intended to supercede the use of a physician, but to supply his place in
    situations where medical assistance could not easily be obtained" — which is exactly the claim
    this shelf makes, and the reason the boundary is his sentence and not ours.
  • NO ORPHANS: every card is member_of its spine; every spine is part_of the Floor of Discovery.
  • Shelves are the ones a FACE ACTUALLY READS (`faces.py`): `sanitation` (the Survivalist) and
    `foods` (the Survivalist, the Cook, the Gardener). `household` is named nowhere and is NOT used
    — a card on a shelf no face reads is a card nobody can reach, which is the defect this fixes.

    PYTHONPATH=src python tools/card_domestic.py     # -> data/domestic_cards.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE_HEALTH = "card_spine_domestic_health"
SPINE_ECONOMY = "card_spine_cottage_economy"

# Bands are match terms. `card_firstaid.py` builds them with a bare `keywords.split()`, which puts
# "a", "for" and "of" on the shelf as search terms — and a one-letter band is exactly the kind of
# spurious match that returns Easton's entry on Lot for a child bleeding "a lot". Dropped here.
# The older seeds have the same pattern and are left alone: changing them changes live cards.
_STOP = frozenset(("a", "an", "and", "the", "of", "for", "to", "in", "on", "at", "is", "it", "or",
                   "be", "do", "my", "you", "your", "with", "from", "that", "this", "what", "how",
                   "if", "no", "not", "so", "up", "out", "too", "who", "should", "would", "can"))


def _bands(fixed: list[str], keywords: str, cap: int = 26) -> list[str]:
    """Fixed bands first, then the keyword terms, de-duplicated, no stopwords, no single letters."""
    seen: set[str] = set()
    bands: list[str] = []
    for term in fixed + keywords.split():
        t = term.strip().lower()
        if len(t) < 3 or t in _STOP or t in seen:
            continue
        seen.add(t)
        bands.append(term)
    return bands[:cap]

BUCHAN = ("William Buchan, Domestic Medicine, 12th ed. (London, 1791) — public domain, "
          "Project Gutenberg 74359")
COBBETT = ("William Cobbett, Cottage Economy, to Which is Added The Poor Man's Friend "
           "(New York, 1833) — public domain, Project Gutenberg 32863")

# A body containing any of these means treatment material was pulled in by mistake. Buchan on
# these subjects can kill a reader, so the build fails rather than shipping the shelf.
HAZARD = ("bleed", "blood-letting", "bloodletting", "venesection", "phlebotomy", "mercur",
          "calomel", "antimon", "opium", "laudanum", "blister", "purgative", "emetic",
          "clyster", "leech", "vomit", "dose", "grains of", "drachm", "bolus", "tincture")

# A body containing any of these means polemic or period prejudice was pulled in by mistake.
PREJUDICE = ("irish", "pig too", "paper-money", "paper money", "fanaticism", "blaspheme",
             "happy poverty", "servility", "pauperism", "slavery", "savage", "barbarity",
             "mahometan", "jewish", "jews", "peasants", "negligent", "shameful")

# (slug, shelf, box, title, source, keywords, verbatim body)
CARDS = [
    # ---- Buchan, Chapter IV: OF AIR -------------------------------------------------------
    ("air_free_passage", "sanitation", "air",
     "Air a house daily — open opposite windows, and turn the beds down", BUCHAN,
     "air house ventilate ventilation open windows fresh air stuffy damp musty room beds bedding "
     "airing healthy home draught cross ventilation how to",
     "The various methods which luxury has invented to make houses close and warm, contribute not a "
     "little to render them unwholesome. No house can be wholesome unless the air has a free passage "
     "through it. For which reason houses ought daily to be ventilated, by opening opposite windows, "
     "and admitting a current of fresh air into every room. Beds, instead of being made up as soon "
     "as people rise out of them, ought to be turned down, and exposed to the fresh air from the "
     "open windows through the day. This would expel any noxious vapour, and could not fail to "
     "promote the health of the inhabitants."),

    ("air_stagnates", "sanitation", "air",
     "Where air stagnates it turns unwholesome — choose open air for a dwelling", BUCHAN,
     "stagnant air crowded close dwelling damp basement overcrowding housing poor ventilation "
     "contagious disease choosing a house where to live children sickly",
     "Wherever air stagnates long, it becomes unwholesome. [...] These low dirty habitations are "
     "the very lurking-places of bad air and contagious diseases. Such as live in them seldom enjoy "
     "good health; and their children commonly die young. In the choice of a house, those who have "
     "it in their power ought always to pay the greatest attention to open free air."),

    ("air_small_room_fire", "sanitation", "air",
     "Do not sleep in a small closed room with a fire burning", BUCHAN,
     "sleep small bedroom fire stove closed room suffocation stifled smoke fumes carbon night "
     "danger airless chamber safety heater",
     "Many people who have splendid houses, chuse to sleep in small apartments. This conduct is "
     "very imprudent. A bed-chamber ought always to be well-aired; as it is generally occupied in "
     "the night only, when all doors and windows are shut. If a fire be kept in it, the danger from "
     "a small room becomes still greater. Numbers have been stifled when asleep by a fire in a "
     "small apartment, which is always hurtful."),

    # ---- Buchan, Chapter VIII: OF CLEANLINESS ---------------------------------------------
    ("clean_water_for_nothing", "sanitation", "cleanliness",
     "Cleanliness admits of no excuse where water can be had", BUCHAN,
     "cleanliness wash washing clean clothes change apparel laundry skin perspiration hygiene "
     "poverty no excuse water free soap how to stay clean",
     "The want of cleanliness is a fault which admits of no excuse. Where water can be had for "
     "nothing, it is surely in the power of every person to be clean. The continual discharge from "
     "our bodies by perspiration, renders frequent change of apparel necessary. Changing apparel "
     "greatly promotes the secretion from the skin, so necessary for health. When that matter which "
     "ought to be carried off by perspiration, is either retained in the body, or resorbed from "
     "dirty clothes, it must occasion diseases."),

    ("clean_fevers_begin_in_dirt", "sanitation", "cleanliness",
     "Fevers begin in close dirty houses — cleanliness is a public matter, not a private one",
     BUCHAN,
     "fever infection spread neighbourhood public health dirty house close crowded cleanliness "
     "community outbreak epidemic why disease spreads",
     "One common cause of putrid and malignant fevers, is the want of cleanliness. These fevers "
     "commonly begin among the inhabitants of close dirty houses, who breathe unwholesome air, take "
     "little exercise, and wear dirty clothes. There the infection is generally hatched, which "
     "often spreads far and wide, to the destruction of many. Hence cleanliness may be considered "
     "as an object of public attention. It is not sufficient that I be clean myself, while the want "
     "of it in my neighbour affects my health as well as his own."),

    ("clean_wash_after_the_sick", "sanitation", "cleanliness",
     "Wash after visiting the sick or handling a body, and before you eat", BUCHAN,
     "wash hands handwashing after visiting the sick touching a dead body before eating meals "
     "infection prevention simple precaution caring for the ill funeral",
     "Were every person, for example, after visiting the sick, handling a dead body, or touching "
     "any thing that might convey infection, to wash before he went into company, or sat down to "
     "meat, he would run less hazard either of catching the infection himself, or of communicating "
     "it to others."),

    ("clean_the_sick_need_it_more", "sanitation", "sick_room",
     "The sick need cleanliness more, not less — change the linen", BUCHAN,
     "sick room nursing care caring for a sick person linen sheets bedding change wash fever "
     "patient home care convalescent looking after the ill clean bed",
     "Few things are more unaccountable than that neglect, or rather dread of cleanliness, which "
     "appears among those who have the care of the sick; they think it almost criminal to suffer "
     "any thing that is clean to come near a person in a fever, for example, and would rather allow "
     "him to wallow in all manner of filth, than change the least bit of his linen. If cleanliness "
     "be necessary for persons in health, it is certainly more so for the sick. Many diseases may "
     "be cured by cleanliness alone; most of them might be mitigated by it; and, where it is "
     "neglected, the slightest disorders are often changed into the most malignant. The same "
     "mistaken care which prompted people to prevent the least admission of fresh air to the sick, "
     "seems to have induced them to keep them dirty."),

    ("clean_many_sick_together", "sanitation", "sick_room",
     "Where many sick are gathered, cleanliness matters most of all", BUCHAN,
     "hospital infirmary ward many sick together cleanliness smell infection caught in hospital "
     "shelter crowded sickroom camp clinic risk",
     "In places where great numbers of sick people are collected together, cleanliness ought to be "
     "most religiously observed. The very smell in such places is often sufficient to make one "
     "sick. It is easy to imagine what effect that is likely to have upon the diseased. In an "
     "hospital or infirmary, where cleanliness is neglected, a person in perfect health has a "
     "greater chance to become sick, than a sick person has to get well."),

    ("clean_feet_after_wet", "sanitation", "cleanliness",
     "Bathe the feet in lukewarm water after a day of cold or wet", BUCHAN,
     "cold wet feet soaked chilled lukewarm water bathe feet evening after work prevent colds "
     "chill exposure outdoors simple remedy",
     "Were people careful to bathe their feet and legs in lukewarm water at night, after being "
     "exposed to cold or wet through the day, they would seldom experience the ill effects which "
     "often proceed from these causes."),

    # ---- Buchan, Chapter IX: OF INFECTION -------------------------------------------------
    ("infect_do_not_crowd", "sanitation", "sick_room",
     "Do not crowd a sick room — keep the patient quiet", BUCHAN,
     "sick room visitors crowding quiet rest fever patient keep calm too many people whispering "
     "disturb the sick caring at home what not to do",
     "Were a plan to be laid down for communicating infection, it could not be done more "
     "effectually than by the common method of visiting the sick. Such visitors not only endanger "
     "themselves and their connections, but likewise hurt the sick. By crowding the house, they "
     "render the air unwholesome, and by their private whispers and dismal countenances disturb the "
     "imagination of the patient, and depress his spirits. Persons who are ill, especially in "
     "fevers, ought to be kept as quiet as possible. The sight of strange faces, and every thing "
     "that disturbs the mind, hurts them."),

    ("infect_outlives_the_patient", "sanitation", "infection",
     "Contagion outlives the patient, and lodges in clothes and bedding", BUCHAN,
     "contagion after death clothes blankets bedding retain infection long time funeral wake "
     "crowding corpse burial disinfect wash linen how long infection lasts",
     "The infection does not always die with the patient. Every thing that comes into contact with "
     "his body while alive, receives the contagion, and some of them, as clothes, blankets, &c. "
     "will retain it for a long time."),

    ("infect_separate_sick_and_well", "sanitation", "infection",
     "Keep the well at a distance from the sick", BUCHAN,
     "separate isolate quarantine sick from healthy distance avoid contact infectious disease "
     "household spread protect the family who should nurse",
     "Many diseases are infectious. Every person ought therefore, as far as he can, to avoid all "
     "communication with the diseased. [...] It would tend greatly to prevent the spreading of "
     "infectious diseases, if those in health were kept at a proper distance from the sick."),

    # ---- Cobbett, Cottage Economy ---------------------------------------------------------
    ("economy_is_management", "foods", "economy",
     "Economy means management, not stinginess", COBBETT,
     "economy household management budget money family affairs thrift saving meaning of economy "
     "home finances running a household misers",
     "The word Economy, like a great many others, has, in its application, been very much abused. "
     "It is generally used as if it meant parsimony, stinginess [...] or, at best, "
     "merely the refraining from expending money. [...] ECONOMY means management, and nothing "
     "more; and it is generally applied to the affairs of a house and family, which affairs are an "
     "object of the greatest importance, whether as relating to individuals or to a nation."),

    ("family_food_and_raiment", "foods", "economy",
     "A family must be well supplied with food and clothing", COBBETT,
     "family food clothing raiment necessaries of life wellbeing provide for your family work "
     "wages labour right to live well sufficiency household provision",
     "I lay it down as a maxim, that for a family to be happy, they must be well supplied with food "
     "and raiment. [...] To live well, to enjoy all things that make life pleasant, is the right of "
     "every man who constantly uses his strength judiciously and lawfully."),

    ("bread_bushel_yield", "foods", "bread",
     "What a bushel of wheat yields in bread", COBBETT,
     "bread wheat bushel flour bran pounds yield baking how much bread from wheat household bread "
     "fine flour quartern loaf milling grain measure",
     "As I have before stated, sixty pounds of wheat, that is to say, where the Winchester bushel "
     "weighs sixty pounds, will make sixty-five pounds of bread, besides the leaving of about ten "
     "pounds of bran. This is household bread, made of flour from which the bran only is taken. If "
     "you make fine flour, you take out pollard, as they call it, as well as bran, and then you "
     "have a smaller quantity of bread and a greater quantity of offal; but, even of this finer "
     "bread, bread equal in fineness to the baker's bread, you get from fifty-eight to fifty-nine "
     "pounds out of the bushel of wheat."),

    ("bread_bake_at_home", "foods", "bread",
     "Baking at home beats the baker's shop — the oven costs little to heat", COBBETT,
     "bake bread at home oven fuel cost cheaper than baker home baking loaves family saving flour "
     "wholemeal fine flour wasteful buying bread",
     "But I have hitherto taken a view of the matter the least possibly advantageous to the "
     "home-baked bread. For, ninety-nine times out of a hundred, the fuel for heating the oven "
     "costs very little. The hedgers, the copsers, the woodmen of all descriptions, have fuel for "
     "little or nothing. At any rate, to heat the oven cannot, upon an average, take the country "
     "through, cost the labourer more than 6d. a bushel. Then, again, fine flour need not ever be "
     "used, and ought not to be used. This adds six pounds of bread to the bushel, or nearly "
     "another quartern loaf and a half, making nearly fifteen quartern loaves out of the bushel of "
     "wheat."),
]

BOUNDARY_BUCHAN = (
    "Buchan set this boundary himself, in the book's own advertisement: his Domestic Medicine was "
    "\"never intended to supercede the use of a physician, but to supply his place in situations "
    "where medical assistance could not easily be obtained.\" That is exactly the claim this shelf "
    "makes and the only one it makes. WHAT IS CARRIED HERE: the regimen half of the book — air, "
    "cleanliness, infection and the care of a sick room — which is prevention and nursing, and "
    "which has held up. WHAT IS NOT CARRIED, AND MUST NOT BE SOUGHT HERE: everything the book says "
    "about treating a disease. Buchan wrote in 1791, and on treatment he is not merely dated but "
    "dangerous. Nothing from those chapters is on this shelf, by design, and no amount of searching "
    "will surface it. For an injury or an illness, reach a trained person; where one cannot be "
    "reached, the first-aid shelf carries conservative modern field care from public-domain "
    "military and public-health sources. Prepared, not fearful (Proverbs 22:3)."
)

BOUNDARY_COBBETT = (
    "Cobbett wrote Cottage Economy in 1821 for a labourer's family, and The Poor Man's Friend as a "
    "defence of \"the rights of those who do the work, and fight the battles.\" WHAT IS CARRIED "
    "HERE: his practical instruction and his definition of economy as the management of a "
    "household. WHAT IS NOT CARRIED: his politics and his prejudices. Cobbett argues paper money, "
    "schooling and \"happy poverty\" at length, and his passage on potatoes disparages the Irish. "
    "None of that is on this shelf. The measures are period measures — a Winchester bushel, a "
    "quartern loaf, pence — and are kept as he wrote them rather than converted, because a "
    "converted number is no longer a quotation. Convert before you rely on one."
)


def _check(cards: list[dict]) -> list[str]:
    """Every body is checked against both denylists. Returns the faults; main() refuses on any."""
    faults = []
    for c in cards:
        body = (c.get("body") or "").lower()
        if c["id"].endswith(("boundary_buchan", "boundary_cobbett")):
            continue                      # the boundaries NAME what is excluded, so they are exempt
        for word in HAZARD:
            if word in body:
                faults.append(f"{c['id']}: HAZARD term {word!r} in body")
        for word in PREJUDICE:
            if word in body:
                faults.append(f"{c['id']}: PREJUDICE term {word!r} in body")
        if not c.get("connections"):
            faults.append(f"{c['id']}: orphan — no connection to a spine")
        if c.get("generated") is not False:
            faults.append(f"{c['id']}: generated must be False")
    return faults


def _spine(cid: str, title: str, body: str, shelf_subject: str, src: str, bands: list[str]) -> dict:
    return {
        "id": cid, "kind": "reference", "title": title, "body": body,
        "source": {"label": src, "url": "", "domain": "medicine", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine", "bands": bands, "subject": shelf_subject,
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "the keeping of a household, a spine of the Floor of Discovery"}],
        "author": "Matt Harris (the domestic shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False, "extra": {"license": "public-domain"},
    }


def main() -> int:
    cards = [
        _spine(SPINE_HEALTH,
               "The domestic health shelf — air, cleanliness, infection and the sick room",
               "What a household can do for its own health without a physician in reach: air the "
               "rooms, keep the person and the linen clean, keep the well apart from the sick, and "
               "nurse a sick room quietly and cleanly. Drawn verbatim from the regimen chapters of "
               "Buchan's Domestic Medicine (1791), which is where that book has held up. Its "
               "treatment chapters are excluded by design — see the boundary.",
               "household health, prevention and the care of the sick", BUCHAN,
               ["domestic medicine", "household health", "sanitation", "cleanliness", "air",
                "infection", "sick room", "nursing", "prevention", "buchan", "spine"]),
        _spine(SPINE_ECONOMY,
               "The cottage economy shelf — bread, and the management of a household",
               "The practical economy of a labouring family: what a bushel of wheat yields in "
               "bread, what an oven costs to heat, and what economy actually means. Drawn verbatim "
               "from Cobbett's Cottage Economy (1833). His politics and his prejudices are excluded "
               "by design — see the boundary.",
               "the practical economy of a household", COBBETT,
               ["cottage economy", "household", "bread", "baking", "foods", "thrift", "economy",
                "labourer", "family", "cobbett", "spine"]),
    ]

    for slug, shelf, box, title, src, keywords, body in CARDS:
        spine = SPINE_HEALTH if shelf == "sanitation" else SPINE_ECONOMY
        cards.append({
            "id": f"card_domestic_{slug}", "kind": "reference", "title": title,
            "body": f"{body}  — {src}.",
            "source": {"label": src, "url": "", "domain": "medicine",
                       "authority_tier": "reference"},
            "shelf": shelf, "box": box,
            "bands": _bands(["household", box.replace("_", " ")], keywords),
            "subject": title,
            "connections": [{"to_card_id": spine, "relationship": "member_of",
                             "evidence": f"household keeping ({box})"}],
            "author": "Matt Harris (the domestic shelf)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"category": box, "source": src, "license": "public-domain",
                      "quotation": "verbatim; cuts marked [...]; italic markers dropped"},
        })

    for cid, spine, shelf, title, body in [
        ("card_domestic_boundary_buchan", SPINE_HEALTH, "sanitation",
         "The domestic health shelf — what Buchan is for, and what he must not be used for",
         BOUNDARY_BUCHAN),
        ("card_domestic_boundary_cobbett", SPINE_ECONOMY, "foods",
         "The cottage economy shelf — what Cobbett is for, and what is left out",
         BOUNDARY_COBBETT),
    ]:
        cards.append({
            "id": cid, "kind": "reference", "title": title, "body": body,
            "source": {"label": "The boundary", "url": "", "domain": "medicine",
                       "authority_tier": "reference"},
            "shelf": shelf, "box": "principle",
            "bands": ["boundary", "safety", "limits", "disclaimer", "household", "public domain",
                      "what is excluded", "doctor", "trained help"],
            "subject": "the boundary of the domestic shelf",
            "connections": [{"to_card_id": spine, "relationship": "member_of",
                             "evidence": "the boundary of the shelf"}],
            "author": "Matt Harris (the domestic shelf)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
        })

    faults = _check(cards)
    if faults:
        for f in faults:
            print(f"REFUSED: {f}", file=sys.stderr)
        print(f"REFUSED: {len(faults)} fault(s); nothing written.", file=sys.stderr)
        return 1

    out = Path("data") / "domestic_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n",
                   encoding="utf-8")
    shelves: dict[str, int] = {}
    for c in cards:
        shelves[c["shelf"]] = shelves.get(c["shelf"], 0) + 1
    print(f"carded {len(cards)} domestic entries -> {out}")
    for s, n in sorted(shelves.items()):
        print(f"   {n:>3}  {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
