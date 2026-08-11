#!/usr/bin/env python3
"""The off-grid power shelf — keeping the lights (and the radio) on, from public-domain sources.

The disk holds the library and the radio carries the whisper — but both need power when the grid is
down. This is the off-grid electricity reference for the prepared home and the mesh node: how to size
a battery-and-solar system, charge it, invert it to household power, and do it SAFELY. Gathered from
U.S. Department of Energy / NREL public guidance and established electrical fact.

DISCIPLINE:
  • PUBLIC-DOMAIN / factual sources: U.S. DOE / NREL consumer guidance (public domain) and basic
    electrical law (Ohm's law, power = volts × amps). Each card attributed.
  • Gather, don't author: established practice — generated=False.
  • SAFETY: electricity, batteries, and generators kill (shock, fire, hydrogen gas, carbon monoxide).
    Cards say the hazard plainly; the boundary loads first-class.
  • NO ORPHANS: every card is member_of the power SPINE, part_of the Floor of Discovery.

    PYTHONPATH=src python tools/card_power.py     # -> data/power_cards.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_power"
_slug = re.compile(r"[^a-z0-9]+")

DOE = "U.S. Department of Energy / NREL consumer energy guidance (public domain)"
FACT = "Basic electrical law (Ohm's law; power = volts × amps) — public fact"
CDC = "CDC / U.S. government carbon-monoxide safety guidance (public domain)"

CARDS = [
    ("basics", "Volts, amps, watts — the words you need", "basics", FACT,
     "volts amps watts electricity ohm law power watt hours basics understand dc ac 12 volt measure",
     "Three words run everything. VOLTS (V) are the push (like water pressure); AMPS (A) are the flow "
     "(like the current in a pipe); WATTS (W) are the actual power, and Watts = Volts × Amps. Energy "
     "over time is WATT-HOURS (Wh): a 10-watt lamp for 5 hours uses 50 Wh. Ohm's law ties them: Volts "
     "= Amps × Resistance. Battery capacity is often given in AMP-HOURS (Ah) at a voltage — multiply "
     "to get watt-hours (100 Ah × 12 V = 1,200 Wh). Learn these and every spec on a panel, battery, "
     "or inverter makes sense."),
    ("power_budget", "Size the system to your load, not the other way", "plan", DOE,
     "power budget load calculation watt hours per day size system how much solar battery need list appliances",
     "Design from your NEEDS. List each device, its watts, and hours per day: watts × hours = watt-"
     "hours/day. Add them up — that daily total is what your system must supply and your battery must "
     "store (plus a margin for cloudy days and losses, roughly ×1.5). A phone and LED lights and a "
     "radio might be 100–300 Wh/day; a fridge alone can be 1,000+. Cut the load first (LED lights, "
     "efficient fridge, turn things off) — every watt you don't use is a watt you don't have to "
     "generate and store."),
    ("batteries", "Batteries — the store, and how not to wreck it", "battery", DOE,
     "battery lead acid lithium lifepo4 amp hours depth of discharge capacity store off grid deep cycle",
     "The battery is your reservoir. LEAD-ACID (flooded/AGM) is cheap but heavy, and you must not "
     "regularly drain it below ~50% or it dies young — so a 100 Ah lead-acid battery gives ~50 Ah of "
     "usable energy. LITHIUM (LiFePO4) costs more but is lighter, lasts far longer, and can be drained "
     "~80–90%, so you buy less capacity for the same usable energy. Use DEEP-CYCLE batteries, not car "
     "starting batteries. Keep them charged, not sitting empty; keep lead-acid vented (it off-gasses "
     "hydrogen); keep lithium from freezing while charging."),
    ("solar", "Solar panels — free power from the sun", "solar", DOE,
     "solar panel photovoltaic pv watts sun hours tilt orientation sizing charge off grid array how much",
     "A solar panel turns sunlight into DC electricity; its rating (e.g. 100 W) is its output in full "
     "sun. What you actually harvest per day is roughly panel-watts × your daily PEAK SUN HOURS (about "
     "3–6 in most of the US, fewer in winter and cloud) — so a 100 W panel might make 400–500 Wh on a "
     "good day. Face panels toward the equator (south in the northern hemisphere), tilt them roughly "
     "to your latitude, and keep them clean and unshaded — even a little shade on one cell can gut the "
     "output. Size the array to refill your daily budget with margin."),
    ("charge_controller", "The charge controller — protect the battery", "solar", DOE,
     "charge controller mppt pwm solar battery protect overcharge regulate off grid required why need",
     "Never wire a solar panel straight to a battery — a CHARGE CONTROLLER sits between them and "
     "regulates the charge so the panel can't overcharge and destroy the battery. Two kinds: PWM is "
     "cheap and fine for small, matched systems; MPPT is more efficient (harvests 20–30% more, "
     "especially in cold or when panel voltage is higher than battery voltage) and worth it for "
     "larger arrays. Match the controller to your panel's and battery's voltage and current. It also "
     "shows you charge state — your fuel gauge."),
    ("inverter", "The inverter — DC battery to household AC", "output", DOE,
     "inverter dc ac pure sine modified sine watts surge size household 120v appliances off grid convert",
     "Batteries and solar are DC (12/24/48 V); most household devices want AC (120 V in the US). An "
     "INVERTER converts it. Size it to your biggest simultaneous load PLUS surge — motors (fridge, "
     "pump, power tools) draw several times their running watts at startup, so a 500 W fridge may need "
     "a 1,500 W+ inverter. PURE SINE wave is clean power that runs anything, including electronics, "
     "motors, and medical gear; MODIFIED SINE is cheaper but can buzz, run hot, or damage sensitive "
     "devices — buy pure sine if you can. Inverters idle-drain the battery; switch off when not needed."),
    ("wiring_fuses", "Wire thick, fuse close — the safety that prevents fires", "safety", DOE,
     "wire gauge size fuse breaker battery short circuit fire safety dc off grid amps thick connect",
     "Low-voltage DC carries BIG amps, so undersized wire overheats and starts fires. Use wire thick "
     "enough for the current and the run length (thicker for more amps and longer runs), keep "
     "connections tight and clean, and put a correctly-rated FUSE or breaker as close to the battery's "
     "positive terminal as possible on every circuit — a short in the wiring must blow the fuse, not "
     "melt the cable. Protect wires from chafing, water, and rodents. When in doubt, size UP the wire "
     "and DOWN nothing on the fuse. Electricity forgives no shortcut here."),
    ("generator_safety", "Generators — and the invisible killer, carbon monoxide", "safety", CDC,
     "generator carbon monoxide co poisoning safety outdoors never indoors gas fuel ventilation death backup",
     "A fuel generator is a strong backup, but its exhaust contains CARBON MONOXIDE — an invisible, "
     "odorless gas that kills quickly. NEVER run a generator indoors, in a garage, basement, crawlspace, "
     "or near open windows/doors — even with ventilation, even for a minute. Run it OUTSIDE, well away "
     "from the house, exhaust pointed away, and use a battery CO alarm indoors. Let it cool before "
     "refueling (hot engine + gasoline = fire), store fuel safely, and don't back-feed it into house "
     "wiring without a proper transfer switch (it can kill a lineworker). Size it to your real load; "
     "a small quiet inverter generator sips fuel."),
    ("keep_devices_alive", "Keeping phones, radios, and lights alive", "practical", DOE,
     "keep devices charged phone radio lights power bank usb 12 volt low power off grid conserve battery",
     "When power is scarce, discipline stretches it far. Charge small devices from 12 V or USB "
     "directly (a car socket or a small solar/USB panel), skipping the inverter's losses. Keep a "
     "couple of charged POWER BANKS for phones and headlamps. Choose low-draw gear: LED lights, an "
     "efficient handheld radio, a laptop over a desktop. Charge in the day when the sun is making "
     "power; run heavy loads (pump, tools) then too, straight off the panels. Turn the inverter off "
     "when idle. A little power, well managed, keeps a family in light and contact indefinitely."),
    ("hand_power", "Power with no sun and no fuel — hand and micro", "practical", DOE,
     "hand crank power dynamo small solar micro emergency radio flashlight charge no fuel backup last resort",
     "For the worst case — no sun, no fuel — small human and micro power still keep the essentials. A "
     "HAND-CRANK radio/flashlight gives light and news for a minute of cranking. A small folding solar "
     "panel (5–20 W) with a USB output charges phones and headlamps even off-grid. A car alternator, "
     "a bicycle-driven dynamo, or a micro-hydro wheel in a running stream can trickle-charge a "
     "battery. These won't run a house, but they keep a phone, a light, and a radio alive — which is "
     "often what matters most. Redundancy in power is redundancy in safety."),
]

BOUNDARY = (
    "THE OFF-GRID POWER SHELF — what this is, and is not. These cards gather established off-grid "
    "electrical practice from PUBLIC-DOMAIN sources (U.S. DOE / NREL guidance, basic electrical law, "
    "CDC carbon-monoxide safety). Electricity, batteries, and generators are DANGEROUS: they cause "
    "shock, fire, explosive battery gas, and — from any fuel engine — carbon-monoxide poisoning that "
    "kills without warning. This is reference and planning, NOT a wiring course or an electrician. For "
    "permanent house wiring, grid connection, or anything you are unsure of, use a qualified "
    "electrician and obey local code. Never run a generator indoors. Prepared, not fearful (Proverbs "
    "22:3).")


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The off-grid power shelf — keeping the lights and the radio on",
        "body": ("Off-grid electricity for the prepared home and the mesh node: volts/amps/watts, "
                 "sizing a system to your real load, batteries (lead-acid vs lithium), solar panels "
                 "and charge controllers, inverters, safe wiring and fusing, generator and "
                 "carbon-monoxide safety, and stretching scarce power to keep phones, radios, and "
                 "lights alive. From DOE/NREL public guidance and basic electrical fact."),
        "source": {"label": "The off-grid power shelf (curated, public domain)", "url": "",
                   "domain": "energy", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["power", "energy", "off grid", "solar", "battery", "generator", "electricity",
                  "prepper", "field", "spine"],
        "subject": "off-grid power and energy",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "harnessing the created order's energy, a spine of the Floor of Discovery"}],
        "author": "Matt Harris (the off-grid power shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False, "extra": {"license": "public-domain"},
    }
    cards = [spine]
    for slug, title, box, src_label, keywords, body in CARDS:
        cards.append({
            "id": f"card_power_{slug}", "kind": "reference", "title": title,
            "body": f"{body}  — {src_label}.",
            "source": {"label": src_label, "url": "", "domain": "energy", "authority_tier": "reference"},
            "shelf": "energy", "box": box,
            "bands": (["power", "energy", "off grid", box.replace("_", " "), "how to"] + keywords.split())[:24],
            "subject": title,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"off-grid power ({box})"}],
            "author": "Matt Harris (the off-grid power shelf)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"category": box, "source": src_label, "license": "public-domain"},
        })
    cards.append({
        "id": "card_power_boundary", "kind": "reference",
        "title": "The off-grid power shelf — electricity is dangerous; use a pro for house wiring",
        "body": BOUNDARY,
        "source": {"label": "The boundary", "url": "", "domain": "energy", "authority_tier": "reference"},
        "shelf": "energy", "box": "principle",
        "bands": ["boundary", "safety", "electrician", "carbon monoxide", "power", "energy", "code"],
        "subject": "the off-grid power shelf boundary",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": "the boundary of the off-grid power shelf"}],
        "author": "Matt Harris (the off-grid power shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    })
    out = Path("data") / "power_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards) - 1} off-grid power entries (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
