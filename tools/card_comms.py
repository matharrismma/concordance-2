#!/usr/bin/env python3
"""The communications shelf — radio & field comms, for the mesh and the off-grid.

Matt, 2026-08-08: LoRa + offline libraries (Prepper Disk / Kiwix / Meshtastic) share our purpose —
keep knowledge and connection alive for the ones the grid leaves behind. The disk carries the
library; the radio carries the whisper. This shelf is the whisper's field reference: how to say it,
what frequency to say it on, and how to be heard — so a family with a $30 radio or a LoRa node can
reach a neighbour when there is no internet at all. It stands beside the field library (survival)
and pairs with the Fellowship Mesh.

DISCIPLINE (load-bearing):
  • Strict PUBLIC-DOMAIN / factual sources only — US-government regulation (FCC Part 97 amateur, Part
    95 GMRS/FRS/MURS/CB, Part 15 ISM), NOAA, and long-established international standards (ITU/ICAO
    phonetics, International Morse, Q-codes). Band edges and channel plans are LAW, and law is public.
    Each card is attributed. No copyrighted band charts (e.g. the ARRL chart) — the underlying
    frequencies-are-regulation are the public fact we card.
  • Gather, don't author: proven, published reference — generated=False, never an invention.
  • Safety + LAW over bravado: transmitting on most of these bands REQUIRES a license, except in a
    genuine life-threatening emergency (any means to call for help is lawful then). The boundary card
    says so plainly and loads first-class.
  • NO ORPHANS: every card is member_of the comms SPINE, which is part_of the Floor of Discovery.

    PYTHONPATH=src python tools/card_comms.py     # -> data/comms_cards.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_comms"
_slug = re.compile(r"[^a-z0-9]+")

# ── public-domain / factual sources ──────────────────────────────────────────
FCC97 = "FCC Part 97 — Amateur Radio Service (U.S. regulation, public domain)"
FCC95 = "FCC Part 95 — Personal Radio Services: GMRS/FRS/MURS/CB (U.S. regulation, public domain)"
FCC15 = "FCC Part 15 — ISM band, unlicensed devices (U.S. regulation, public domain)"
ITU_PHON = "ITU/ICAO/NATO International Radiotelephony Spelling Alphabet (international standard)"
ITU_MORSE = "ITU-R M.1677 International Morse Code (international standard, public domain)"
ITU_Q = "ITU Q-code / operating signals (international standard, long-established)"
NOAA = "NOAA NWS — Weather Radio All Hazards (U.S. government, public domain)"
INTL_DISTRESS = "International distress conventions (ITU / ICAO / IMO, public domain)"
MESH = "FCC Part 15 ISM band (public domain) + Meshtastic open-source project"
FIELD = "U.S. Army field antenna & signaling references (public domain)"

# (slug, title, box, source_label, source_url, keywords, body)
CARDS = [
    # ── how to say it ──────────────────────────────────────────────────────
    ("phonetic_alphabet", "The phonetic alphabet — spell so you're heard", "speech", ITU_PHON, "",
     "phonetic alphabet nato icao spelling alfa bravo charlie letters spell say clearly radio noise",
     "Spell hard words letter by letter so noise can't garble them. A=Alfa B=Bravo C=Charlie D=Delta "
     "E=Echo F=Foxtrot G=Golf H=Hotel I=India J=Juliett K=Kilo L=Lima M=Mike N=November O=Oscar "
     "P=Papa Q=Quebec R=Romeo S=Sierra T=Tango U=Uniform V=Victor W=Whiskey X=X-ray Y=Yankee Z=Zulu. "
     "Numbers are spoken digit by digit; 'niner' for 9 so it isn't heard as 5."),
    ("prowords", "Prowords — the words that carry meaning on the air", "speech", FCC97, "",
     "prowords over out roger wilco say again break affirmative negative copy standby radio procedure how to talk",
     "Plain words with fixed meaning keep a channel clear: OVER (I'm done, your turn), OUT (done, no "
     "reply expected — never 'over and out'), ROGER (received), WILCO (received and will comply), SAY "
     "AGAIN (repeat — not 'repeat', which means fire again), AFFIRMATIVE/NEGATIVE (yes/no), BREAK "
     "(separates parts, or pauses for emergency traffic), STANDBY (wait). Listen before you transmit."),
    ("morse_code", "Morse code — the signal that gets through when voice can't", "code", ITU_MORSE, "",
     "morse code dot dash cw sos distress ...---... telegraph light sound tap flashlight whistle signal",
     "Morse rides through noise and weak signals that swallow voice, and needs only a light, a whistle, "
     "or a tap. SOS is the universal distress call: dot-dot-dot dash-dash-dash dot-dot-dot ( ...---... ), "
     "sent as one unbroken group. E=. T=- A=.- N=-. O=--- S=... I=.. M=--  Learn SOS first; a dash is "
     "three times a dot; letters are spaced by a dot-length of silence, words by a dash-length."),
    ("q_codes", "Q-codes — three letters that ask a whole question", "code", ITU_Q, "",
     "q codes qth qsl qrz qrm qrn qsy qrt qso operating signal shorthand ham radio abbreviation",
     "Q-codes pack a question or statement into three letters (a '?' after asks it): QTH = my location "
     "(QTH? = where are you); QSL = received/acknowledged; QRZ? = who is calling me; QRM = interference "
     "from other stations; QRN = interference from noise/static; QSY = change frequency; QRT = I am "
     "closing down; QSB = your signal is fading. Born in Morse, still used by voice everywhere."),

    # ── the cheap radios most families already have ──────────────────────────
    ("frs_gmrs", "FRS & GMRS — the license-cheap family radios", "channels", FCC95, "",
     "frs gmrs walkie talkie family radio license 22 channels uhf 462 467 mhz bubble pack cheap how to",
     "The 'bubble-pack' walkie-talkies use 22 shared UHF channels (462–467 MHz). FRS is LICENSE-FREE "
     "(up to 2 watts on most channels) — fine for a family within a mile or two. GMRS reaches farther "
     "(up to 50 watts, repeaters, detachable antennas) but needs a $35 FCC license (no test, covers "
     "your whole household for 10 years). Agree a channel and a check-in time before you separate."),
    ("murs", "MURS — five license-free VHF channels", "channels", FCC95, "",
     "murs multi use radio service license free vhf 151 154 mhz 2 watts unlicensed business itinerant",
     "MURS is five VHF channels (151.820, 151.880, 151.940, 154.570, 154.600 MHz), license-free, up to "
     "2 watts. VHF often reaches farther than FRS/GMRS UHF across open ground and hills. Popular for "
     "farms, property, and off-grid groups; some wireless driveway alarms use 154.570/154.600."),
    ("cb_radio", "CB radio — 40 channels, no license, Channel 9 & 19", "channels", FCC95, "",
     "cb radio citizens band 27 mhz 40 channels channel 9 emergency 19 highway truckers license free",
     "Citizens Band (27 MHz, 40 channels) needs no license and reaches a few miles (much more when the "
     "band 'skips' on solar highs). Channel 9 is the traditional emergency/monitoring channel; Channel "
     "19 is the highway/trucker channel for road conditions. AM is standard; SSB radios reach farther. "
     "A good outside antenna matters more than power."),
    ("noaa_weather", "NOAA weather radio — the seven frequencies that warn you", "listen", NOAA, "https://www.weather.gov/nwr/",
     "noaa weather radio nwr all hazards frequency 162 mhz alert warning storm tornado emergency listen",
     "NOAA Weather Radio broadcasts continuous forecasts and emergency alerts on seven VHF frequencies: "
     "162.400, 162.425, 162.450, 162.475, 162.500, 162.525, and 162.550 MHz. A cheap weather radio (or "
     "any scanner/handheld that covers them) with the alert tone will wake you for tornado, flood, and "
     "civil warnings. This is receive-only — no license, just listen."),

    # ── amateur (ham) radio — the long reach ─────────────────────────────────
    ("ham_license", "Getting a ham license — the key to the long-range bands", "amateur", FCC97, "https://www.fcc.gov/wireless/bureau-divisions/mobility-division/amateur-radio-service",
     "ham amateur radio license technician general extra test exam class fcc how to get started reach far",
     "Amateur ('ham') radio reaches from across town to across the world, and is the backbone of "
     "volunteer emergency comms. Three US license classes, each a 35-question multiple-choice exam "
     "(no Morse required anymore): TECHNICIAN (VHF/UHF, local + repeaters + some HF), GENERAL (most HF "
     "— regional/worldwide), EXTRA (all privileges). Study is free online; the exam is ~$15. Get "
     "licensed BEFORE you need it — practice is what makes you useful in an emergency."),
    ("ham_bands", "The common ham bands — where to find people", "amateur", FCC97, "",
     "ham bands frequencies 80 40 20 meters 2m 70cm hf vhf uhf band plan mhz where to listen call",
     "Key US amateur bands (edges are FCC regulation): HF for distance — 80m 3.5–4.0 MHz (regional, "
     "night), 40m 7.0–7.3 MHz (day/night workhorse), 20m 14.0–14.35 MHz (worldwide, daytime). VHF/UHF "
     "for local/line-of-sight — 2m 144–148 MHz and 70cm 420–450 MHz, mostly through repeaters. The 2m "
     "NATIONAL SIMPLEX CALLING frequency is 146.520 MHz — a good place to call directly, no repeater."),
    ("repeaters", "Repeaters — how a hilltop doubles your range", "amateur", FCC97, "",
     "repeater offset ctcss pl tone input output duplex ham vhf uhf how repeaters work range hilltop",
     "A repeater sits high (hilltop, tower) and re-transmits what it hears, so two low handhelds reach "
     "each other across a whole region. Your radio listens on the repeater's OUTPUT and transmits on a "
     "fixed OFFSET (2m: ±600 kHz; 70cm: ±5 MHz). Most require a CTCSS/'PL' sub-audible TONE to open "
     "them. Program the local repeater's output, offset, and tone; find them in RepeaterBook offline."),

    # ── the mesh — LoRa / Meshtastic ─────────────────────────────────────────
    ("lora_meshtastic", "LoRa & Meshtastic — off-grid text that meshes itself", "mesh", MESH, "https://meshtastic.org",
     "lora meshtastic mesh off grid text message 915 mhz ism license free node relay range no internet",
     "LoRa radios send tiny encrypted TEXT + GPS over long range on the license-free US ISM band "
     "(902–928 MHz) — and Meshtastic nodes REBROADCAST each other's messages, forming a self-healing "
     "mesh with no tower or internet. Range: ~500 m in dense city, 15 km+ across open ridgelines, "
     "farther hop by hop. Bandwidth is tiny (text and position only — no voice, photos, or files). A "
     "node is ~$30; pair it to your phone over Bluetooth. This is the whisper layer; the disk carries "
     "the library."),
    ("meshtastic_start", "Meshtastic quick-start — a node on the air in minutes", "mesh", MESH, "https://meshtastic.org/docs/getting-started/",
     "meshtastic setup quick start node channel longfast bluetooth phone app region preset how to config",
     "1) Set your REGION on first boot (US) so it uses the legal frequency. 2) Keep the default preset "
     "'LongFast' (long range, everyone's default) or agree one with your group. 3) Set a private "
     "CHANNEL + PSK so only your people read your traffic (the default channel is public). 4) Pair the "
     "node to the phone app over Bluetooth. 5) Height + a clear view = range; put a node up high to "
     "relay for everyone. Nodes relay even when your phone is off."),

    # ── distress, calling for help, and the plan ─────────────────────────────
    ("distress_signals", "Calling for help — the signals everyone should know", "emergency", INTL_DISTRESS, "",
     "distress signal mayday sos three whistle blasts fires ground to air rescue emergency call help",
     "MAYDAY (spoken three times) is the voice distress call for grave, immediate danger; PAN-PAN "
     "(x3) is urgent but not life-threatening. On Morse or light: SOS ( ...---... ). The universal "
     "'I need help' pattern is THREE of anything — three whistle blasts, three fires in a triangle, "
     "three gunshots — answered by two. Marine VHF Channel 16 (156.800 MHz) and aircraft 121.5 MHz are "
     "the international distress/calling frequencies, monitored by rescue services."),
    ("emergency_frequencies", "The frequencies to know for an emergency", "emergency", INTL_DISTRESS, "",
     "emergency frequencies channel 16 marine 121.5 aviation noaa frs gmrs cb 9 calling monitor distress",
     "Worth writing on the radio: Marine VHF Ch 16 = 156.800 MHz (international distress/hailing, "
     "Coast Guard monitors). Aviation emergency = 121.500 MHz. NOAA weather 162.400–162.550 MHz "
     "(receive alerts). CB Channel 9 (27.065 MHz) traditional emergency. 2m ham calling 146.520 MHz. "
     "GMRS/FRS Channel 1 or a pre-agreed family channel. In a true life-or-death emergency, you may "
     "transmit for help on ANY frequency by ANY means, licensed or not — the law makes that exception."),
    ("comms_plan", "A family comms plan — agree it before you need it", "plan", INTL_DISTRESS, "",
     "communication plan family emergency who what when channel check in time rally point ready.gov prepare",
     "Radios are useless without a plan agreed in advance. Write down: a primary and backup CHANNEL/"
     "frequency; a CHECK-IN TIME (e.g. top of every hour) so batteries last; who calls whom; a code "
     "word for 'I'm safe' and one for 'come get me'; an out-of-area contact everyone reports to; and "
     "physical RALLY POINTS if comms fail entirely. Keep it on paper in every kit. Test it before the "
     "day you depend on it."),

    # ── being heard: antennas, propagation, time ─────────────────────────────
    ("antenna_basics", "Antennas — the cheapest way to double your range", "signal", FIELD, "",
     "antenna half wave quarter wave height line of sight dipole ground plane swr feedline range improve",
     "A better antenna beats more power almost every time. Key ideas: HEIGHT wins for VHF/UHF — they go "
     "line-of-sight, so raising the antenna a few metres can double reach. Length matters: a common "
     "field antenna is a half-wave (length in metres ≈ 143 ÷ frequency-in-MHz) or a quarter-wave over "
     "a ground plane. Keep feedline short and connectors dry. Even a wire thrown over a branch, cut to "
     "length, outperforms a stock 'rubber duck'."),
    ("propagation", "Propagation — why range changes with band and time of day", "signal", FIELD, "",
     "propagation hf vhf uhf line of sight ionosphere skip day night band choice distance skywave ground",
     "Match the band to the distance: VHF/UHF (2m/70cm, GMRS, MURS) travel LINE-OF-SIGHT — great "
     "local, blocked by hills and horizon. HF (80/40/20m) bounces off the ionosphere ('skip') to reach "
     "over the horizon — 80/40m for regional at night, 20m for worldwide by day. If you can't reach "
     "someone, changing band or waiting for day/night often does more than shouting into the mic."),
    ("utc_time", "UTC / Zulu time — why radio runs on one clock", "signal", INTL_DISTRESS, "",
     "utc zulu gmt time radio logging coordinated universal time zone net schedule why radio uses",
     "Radio, aviation, and the military run on UTC (Coordinated Universal Time), spoken 'Zulu' — one "
     "clock for everyone, so a net at '0200Z' means the same instant in every timezone and there's no "
     "confusion across borders or a date line. Learn your offset from UTC (e.g. US Eastern is UTC−5, "
     "or −4 in summer) and log times in Zulu. A cheap watch set to UTC lives in the radio kit."),
    ("power_field", "Powering a radio in the field", "signal", FIELD, "",
     "battery power field radio 12 volt solar charge handheld aa lithium runtime low power off grid keep going",
     "Comms fail when the batteries do, so plan power like water. Handhelds sip current on RECEIVE and "
     "gulp on TRANSMIT — listen more, key up briefly, and turn power DOWN when the other station is "
     "close (low power reaches farther than you'd think and saves the battery). Carry spare cells or a "
     "12V battery + a small solar panel; a 20–50W panel keeps a base station and phone alive. Keep "
     "lithium cells from freezing and from full heat."),
]

BOUNDARY = (
    "THE COMMUNICATIONS SHELF — what this is, and is not. These cards gather established, public field "
    "reference from PUBLIC-DOMAIN sources: FCC Parts 97/95/15 (US radio regulation), NOAA, and "
    "long-standing international standards (ITU/ICAO phonetics, International Morse, Q-codes). LAW "
    "matters here: transmitting on the amateur, GMRS, and most other bands REQUIRES the correct "
    "license, and you must use your callsign and obey band limits — get licensed before you need it, "
    "it is cheap and the study is free. The one exception, written into the rules, is a genuine "
    "life-threatening EMERGENCY: then you may call for help by any means on any frequency. This is "
    "reference and preparation, NOT a substitute for training or for professional rescue when it can "
    "be reached. Listen first; identify yourself; help others. Prepared, not fearful (Proverbs 22:3).")


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The communications shelf — radio & field comms for the mesh and the off-grid",
        "body": ("How to reach a neighbour when there is no internet: the phonetic alphabet and "
                 "prowords, Morse and Q-codes, the license-cheap family radios (FRS/GMRS/MURS/CB), "
                 "amateur radio and repeaters, LoRa/Meshtastic mesh, distress signals and emergency "
                 "frequencies, antennas, propagation, and a family comms plan. The whisper layer beside "
                 "the field library — gathered from public regulation and international standard."),
        "source": {"label": "The communications shelf (curated, public domain)", "url": "",
                   "domain": "communications", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["communications", "radio", "comms", "mesh", "lora", "meshtastic", "ham", "amateur",
                  "emergency", "off grid", "prepper", "field", "spine"],
        "subject": "radio and field communications",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "practical knowledge of reaching one another, a spine of the Floor of Discovery"}],
        "author": "Matt Harris (the communications shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
        "extra": {"license": "public-domain"},
    }
    cards = [spine]
    for slug, title, box, src_label, src_url, keywords, body in CARDS:
        cards.append({
            "id": f"card_comms_{slug}", "kind": "reference", "title": title,
            "body": f"{body}  — {src_label}.",
            "source": {"label": src_label, "url": src_url, "domain": "communications",
                       "authority_tier": "reference"},
            "shelf": "communications", "box": box,
            "bands": (["communications", "radio", box.replace("_", " "), "how to"] + keywords.split())[:24],
            "subject": title,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"field communications ({box.replace('_', ' ')})"}],
            "author": "Matt Harris (the communications shelf)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"category": box, "source": src_label, "license": "public-domain"},
        })
    cards.append({
        "id": "card_comms_boundary", "kind": "reference",
        "title": "The communications shelf — reference, license, and the emergency exception",
        "body": BOUNDARY,
        "source": {"label": "The boundary", "url": "", "domain": "communications", "authority_tier": "reference"},
        "shelf": "communications", "box": "principle",
        "bands": ["boundary", "safety", "license", "law", "emergency", "communications", "radio", "fcc"],
        "subject": "the communications shelf boundary",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": "the boundary of the communications shelf"}],
        "author": "Matt Harris (the communications shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    })
    out = Path("data") / "comms_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards) - 1} communications entries (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
