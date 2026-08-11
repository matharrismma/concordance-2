#!/usr/bin/env python3
"""The first-aid shelf — field medicine for when help is far, from public-domain sources.

Beside the field library (survival) and the apothecary, this is the "keep a person alive until
help comes" reference for the off-grid home and the mesh community. Conservative by design: it
teaches the few things that save lives (stop bleeding, keep breathing, treat for shock, rehydrate)
and says plainly, on every card and in the boundary, that it is REFERENCE — never a substitute for
training or for professional care when it can be reached. Get certified before you need it.

DISCIPLINE (load-bearing):
  • Strict PUBLIC-DOMAIN sources: US Army First Aid (FM 4-25.11 / FM 21-11), CDC / Ready.gov, and
    WHO public guidance (e.g. the oral-rehydration ratio). Each card is attributed.
  • Gather, don't author: established, non-controversial field first aid — generated=False.
  • SAFETY FIRST: nothing heroic or contested. When a step is dangerous or a myth, the card says
    "do NOT". Every card points to trained help; the boundary card loads first-class.
  • NO ORPHANS: every card is member_of the first-aid SPINE, part_of the Floor of Discovery.

    PYTHONPATH=src python tools/card_firstaid.py     # -> data/firstaid_cards.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_firstaid"
_slug = re.compile(r"[^a-z0-9]+")

FM = "U.S. Army First Aid manual FM 4-25.11 / FM 21-11 (public domain)"
CDC = "CDC / Ready.gov emergency first-aid guidance (U.S. government, public domain)"
WHO = "World Health Organization public guidance (oral rehydration) — public health reference"
REDCROSS = "Established first-aid practice; get certified (American Red Cross / AHA training)"

# (slug, title, box, source_label, keywords, body)
CARDS = [
    ("primary_check", "First check — scene, response, breathing", "assess", FM,
     "first aid primary survey scene safe responsive breathing abc airway circulation call help emergency what to do first",
     "Before you touch anyone: make the SCENE safe (traffic, fire, wire, water) — a second casualty "
     "helps no one. Then check the person: are they RESPONSIVE (tap and shout)? Are they BREATHING "
     "normally? Is there severe BLEEDING? Send someone to call for help immediately and, if you have "
     "it, to bring the kit and an AED. Treat the biggest threat first — bleeding and breathing kill "
     "fastest. Do not move a person with a possible spine injury unless they are in danger."),
    ("bleeding", "Stop severe bleeding — pressure, then more pressure", "life", FM,
     "bleeding hemorrhage stop control direct pressure wound dressing tourniquet blood loss severe limb",
     "Severe bleeding can kill in minutes — act now. Press HARD directly on the wound with a clean "
     "cloth or gloved hand and DO NOT lift to peek; add more cloth on top if it soaks through and "
     "keep pressing. Raise the wound above the heart if you can. For life-threatening bleeding from "
     "an arm or leg that pressure won't stop, apply a TOURNIQUET 5–8 cm above the wound (not on a "
     "joint), tighten until bleeding stops, and write the TIME on it — then get help fast. A "
     "tourniquet is a last resort, but a life beats a limb."),
    ("cpr", "When someone isn't breathing — CPR", "life", REDCROSS,
     "cpr not breathing cardiac arrest chest compressions rescue breathing aed heart stopped collapse unresponsive",
     "If an adult is unresponsive and NOT breathing normally, they need CPR now, and someone must "
     "call emergency services and find an AED. Push HARD and FAST in the CENTER of the chest — about "
     "5 cm deep, 100–120 pushes a minute (the beat of 'Stayin' Alive') — and let the chest come all "
     "the way back up between pushes. Keep going until they breathe, help takes over, or you cannot "
     "continue. This is a reminder, not a course: get certified (Red Cross / AHA) — hands-on practice "
     "is what makes it work."),
    ("choking", "Choking — back blows and abdominal thrusts", "life", FM,
     "choking heimlich abdominal thrusts back blows cannot breathe airway blocked adult conscious food",
     "If a choking person can still cough or speak, encourage them to cough — don't interfere. If "
     "they CAN'T breathe, cough, or speak: give 5 firm BACK BLOWS between the shoulder blades with "
     "the heel of your hand, then 5 ABDOMINAL THRUSTS (stand behind, fist just above the navel, pull "
     "sharply in and up). Alternate 5 and 5 until the object clears or they go unconscious — then "
     "start CPR and call for help. For a baby, use back blows and chest thrusts, never abdominal "
     "thrusts."),
    ("shock", "Treat for shock — the quiet killer after injury", "life", FM,
     "shock pale cold clammy weak fast pulse faint injury bleeding keep warm lie down legs raised treat",
     "Shock — the body failing to circulate enough blood — can follow any serious injury, bleeding, "
     "or burn, and can kill even after you've stopped the obvious wound. Signs: pale, cold, clammy "
     "skin; fast weak pulse; rapid breathing; confusion or faintness. Lay the person down, raise the "
     "legs about 30 cm (unless that worsens an injury), keep them WARM with a blanket, loosen tight "
     "clothing, reassure them, and give NOTHING by mouth. Treat the cause (stop bleeding) and get "
     "help — shock needs a hospital."),
    ("wounds", "Wounds and infection — clean, cover, watch", "wound", CDC,
     "wound cut clean cover bandage infection redness swelling pus fever red streak antiseptic dress heal",
     "For a wound that isn't life-threatening bleeding: wash your hands, rinse the wound with clean "
     "(drinkable) water to flush out dirt, and cover it with a clean dressing. Change the dressing "
     "when wet or dirty. Watch for INFECTION over the next days — spreading redness, swelling, "
     "warmth, pus, increasing pain, fever, or a red streak toward the heart — which needs medical "
     "care and often antibiotics. Deep, dirty, animal-bite, or puncture wounds and anything you can't "
     "clean need professional care and a tetanus check."),
    ("burns", "Burns — cool water, not ice or butter", "wound", CDC,
     "burn cool running water blister cover do not ice butter chemical electrical severe first aid treat",
     "Cool a burn under COOL (not ice-cold) running water for 10–20 minutes as soon as possible — "
     "this is the single most helpful thing. Remove rings and tight items before swelling. Cover "
     "loosely with a clean, non-stick dressing or cling film. Do NOT use ice, butter, oil, or "
     "toothpaste, and do NOT pop blisters. Get medical help for burns that are large (bigger than the "
     "person's palm), deep/white/charred, on the face, hands, feet, or genitals, or caused by "
     "chemicals or electricity. Give sips of water and treat for shock."),
    ("fractures", "Broken bones — splint, don't straighten", "injury", FM,
     "fracture broken bone splint immobilize sprain dislocation support above below joint circulation move",
     "Suspect a fracture with severe pain, swelling, deformity, or inability to use a limb. SPLINT it "
     "the way you find it — do not try to straighten or push a bone back. Support the limb, then "
     "immobilize with a rigid splint padded and tied ABOVE and BELOW the injury (a stick, board, or "
     "rolled magazine works). Check that fingers/toes beyond the splint stay warm and pink — loosen "
     "if they go cold, pale, or numb. For an open fracture (bone through skin), cover the wound first "
     "and control bleeding. Get to definitive care."),
    ("sprains", "Sprains and strains — RICE", "injury", REDCROSS,
     "sprain strain rice rest ice compression elevation ankle joint swelling twist minor injury",
     "For a twisted ankle, pulled muscle, or minor joint injury with no deformity: RICE. REST it "
     "(stop using it). ICE for 15–20 minutes every couple of hours for the first day (a cloth "
     "between ice and skin). COMPRESS with an elastic bandage snug but not cutting off circulation. "
     "ELEVATE above the heart to reduce swelling. If it can't bear weight, is badly deformed, or "
     "isn't improving in a few days, treat it as a possible fracture and seek care."),
    ("rehydration", "Dehydration — the salt-and-sugar rehydration drink", "illness", WHO,
     "dehydration rehydration ors oral rehydration salt sugar diarrhea vomiting water fluids fever heat drink recipe",
     "Dehydration from diarrhea, vomiting, or heat kills, especially the young and old, and it's "
     "cheaply reversed. Oral rehydration solution (the WHO recipe): in 1 liter of CLEAN water, "
     "dissolve about 6 level teaspoons of sugar and half a level teaspoon of salt — it should taste "
     "no saltier than tears. Give small, frequent sips. Signs to rehydrate: dry mouth, little/dark "
     "urine, sunken eyes, weakness, dizziness. Keep giving fluids even while treating the cause. "
     "Severe dehydration (can't drink, very drowsy) needs medical care."),
    ("anaphylaxis", "Severe allergic reaction — a true emergency", "life", CDC,
     "allergic reaction anaphylaxis epipen epinephrine swelling throat breathing hives sting food bee emergency",
     "A severe allergic reaction (anaphylaxis) can kill in minutes and is a true emergency. Signs "
     "after a sting, food, or medicine: swelling of the face, lips, tongue, or throat; trouble "
     "breathing or a tight throat; widespread hives; dizziness or collapse. If the person has an "
     "EPINEPHRINE auto-injector (EpiPen), help them use it in the outer thigh RIGHT AWAY — and call "
     "emergency services. A second dose may be needed after 5–15 minutes. Lay them flat with legs "
     "raised (sit up if breathing is hard). Do not wait to see if it passes."),
    ("snakebite", "Snakebite — stay calm, don't cut or suck", "illness", CDC,
     "snakebite snake bite venom calm immobilize do not cut suck tourniquet ice hospital antivenom first aid",
     "For a venomous snakebite: keep the person CALM and STILL — movement spreads venom. Move them "
     "away from the snake; don't try to catch it (a photo from a distance is enough). Remove rings "
     "and tight clothing near the bite before swelling. Keep the bitten limb below or at heart level "
     "and immobilize it like a fracture. Get to a hospital for antivenom as fast as possible. Do NOT "
     "cut the wound, suck out venom, apply ice, use a tourniquet, or give alcohol — these old "
     "'remedies' cause harm. Note the time and mark the swelling's edge."),
    ("kit", "A simple first-aid kit — what to keep", "kit", CDC,
     "first aid kit supplies bandages gauze tape gloves tourniquet scissors what to stock prepare home vehicle",
     "Keep a kit in the home, the vehicle, and each go-bag. Essentials: gloves; several sizes of "
     "adhesive bandages; sterile gauze pads and a roll; medical tape; an elastic (compression) "
     "bandage; a triangular bandage/sling; blunt scissors and tweezers; antiseptic wipes and antibiotic "
     "ointment; a tourniquet and a trauma dressing for severe bleeding; a space blanket for shock/warmth; "
     "pain/fever reducer and rehydration salts; a CPR face shield; and a small manual. Check it twice a "
     "year and replace what's used or expired. Knowing how to use it matters more than the contents."),
]

BOUNDARY = (
    "THE FIRST-AID SHELF — what this is, and is not. These cards gather established, conservative field "
    "first aid from PUBLIC-DOMAIN sources: the U.S. Army First Aid manual (FM 4-25.11 / FM 21-11), CDC "
    "and Ready.gov guidance, and WHO public health references. It is REFERENCE for when trained help is "
    "far — NEVER a substitute for a first-aid course, and never for a doctor, medic, or emergency "
    "services when they can be reached. Get certified (Red Cross / AHA) BEFORE the day you need it; "
    "hands-on practice is what saves a life. When a life is in danger and help is reachable, call for it "
    "first. Do no harm; comfort always. Prepared, not fearful (Proverbs 22:3).")


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The first-aid shelf — field medicine for when help is far",
        "body": ("The few things that save a life until help comes: check breathing, stop severe "
                 "bleeding, treat for shock, restart a stopped heart, clear a choking airway, cool a "
                 "burn, splint a break, rehydrate, and recognize a true emergency. Conservative field "
                 "first aid from public-domain military and public-health sources. Stands beside the "
                 "field library and the apothecary."),
        "source": {"label": "The first-aid shelf (curated, public domain)", "url": "",
                   "domain": "medicine", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["first aid", "medicine", "field medicine", "emergency", "life saving", "prepper",
                  "off grid", "survival", "spine"],
        "subject": "field first aid and medicine",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "practical care of the body, a spine of the Floor of Discovery"}],
        "author": "Matt Harris (the first-aid shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False, "extra": {"license": "public-domain"},
    }
    cards = [spine]
    for slug, title, box, src_label, keywords, body in CARDS:
        cards.append({
            "id": f"card_firstaid_{slug}", "kind": "reference", "title": title,
            "body": f"{body}  — {src_label}.",
            "source": {"label": src_label, "url": "", "domain": "medicine", "authority_tier": "reference"},
            "shelf": "first_aid", "box": box,
            "bands": (["first aid", "medicine", box.replace("_", " "), "emergency", "how to"] + keywords.split())[:24],
            "subject": title,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"field first aid ({box})"}],
            "author": "Matt Harris (the first-aid shelf)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"category": box, "source": src_label, "license": "public-domain"},
        })
    cards.append({
        "id": "card_firstaid_boundary", "kind": "reference",
        "title": "The first-aid shelf — reference, not a substitute for training or a doctor",
        "body": BOUNDARY,
        "source": {"label": "The boundary", "url": "", "domain": "medicine", "authority_tier": "reference"},
        "shelf": "first_aid", "box": "principle",
        "bands": ["boundary", "safety", "training", "disclaimer", "first aid", "medicine", "doctor"],
        "subject": "the first-aid shelf boundary",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": "the boundary of the first-aid shelf"}],
        "author": "Matt Harris (the first-aid shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    })
    out = Path("data") / "firstaid_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards) - 1} first-aid entries (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
