#!/usr/bin/env python3
"""The navigation shelf — map, compass, and the sky, from public-domain sources.

Prepper Disk and the offline libraries carry maps; this is how to USE them when the GPS dies. Beside
the field library, it teaches a family to find their way with a paper map, a compass, and the sun and
stars — no battery required. Gathered from the U.S. Army's public-domain land-navigation manual.

DISCIPLINE:
  • PUBLIC-DOMAIN sources: U.S. Army FM 3-25.26 (Map Reading and Land Navigation) and long-established
    celestial navigation fact. Each card attributed.
  • Gather, don't author: established technique — generated=False.
  • NO ORPHANS: every card is member_of the navigation SPINE, part_of the Floor of Discovery.

    PYTHONPATH=src python tools/card_navigation.py     # -> data/navigation_cards.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_navigation"
_slug = re.compile(r"[^a-z0-9]+")

FM = "U.S. Army FM 3-25.26 — Map Reading and Land Navigation (public domain)"
SKY = "Celestial navigation — long-established public fact (astronomy)"

CARDS = [
    ("read_map", "Reading a topographic map", "map", FM,
     "topographic map read scale legend contour lines relief terrain symbols grid north how to",
     "A topographic map shows the shape of the land. The SCALE (e.g. 1:24,000) tells you map-to-ground "
     "distance — 1 unit on the map is 24,000 on the ground. CONTOUR LINES join points of equal "
     "elevation: close together means steep, far apart means gentle, and a closed ring is a hilltop. "
     "The LEGEND decodes the symbols and colors (blue = water, green = vegetation, black = man-made, "
     "brown = contours). Note the map's DATE — terrain lasts, roads and buildings change. Always keep "
     "the map dry and folded to your area."),
    ("grid_coords", "Grid coordinates — read right, then up", "map", FM,
     "grid coordinates map reference easting northing read right up mgrs utm square location point how to",
     "A map grid lets you name any point with numbers. Rule: READ RIGHT, THEN UP. First read the "
     "vertical grid line to the LEFT of your point and go along the bottom (the EASTING), then the "
     "horizontal line BELOW it and go up the side (the NORTHING). More digits = more precise (a "
     "6-figure grid locates you within ~100 m). Give coordinates the same way every time so others "
     "can find the exact spot — a shared grid is how two parties meet on a big map."),
    ("lat_long", "Latitude and longitude", "map", FM,
     "latitude longitude coordinates degrees minutes north south east west gps position equator meridian",
     "Latitude is your distance north or south of the equator (0° at the equator, up to 90° at the "
     "poles); longitude is east or west of the prime meridian through Greenwich (0° to 180°). A "
     "position is written latitude first, then longitude, each with N/S and E/W — e.g. 39.7392° N, "
     "104.9903° W. Degrees split into 60 minutes, minutes into 60 seconds. Most GPS units and maps "
     "can show either lat/long or grid; agree which format your group uses so a shared position "
     "isn't misread."),
    ("compass", "The compass — magnetic north vs true north", "compass", FM,
     "compass magnetic north true grid declination needle bezel baseplate parts how to use orient",
     "A compass needle points to MAGNETIC north, which differs from TRUE (map) north by an angle "
     "called DECLINATION — printed on the map's margin, and different for every region and slowly "
     "changing. To be accurate you must adjust for it (add or subtract the declination as the map "
     "says). Keep the compass FLAT and away from metal, phones, and vehicles, which pull the needle. "
     "Its parts: the magnetized needle, the rotating bezel marked 0–360°, and the baseplate with a "
     "direction-of-travel arrow."),
    ("take_bearing", "Taking and following a bearing", "compass", FM,
     "bearing azimuth take follow compass direction of travel degrees back bearing sight object walk to",
     "A BEARING (azimuth) is a direction in degrees, 0°/360° = north, 90° = east, 180° = south, 270° "
     "= west. To take one to a landmark: point the direction-of-travel arrow at it, turn the bezel "
     "until its needle-outline sits under the needle ('put red in the shed'), and read the number. "
     "To FOLLOW it, hold the compass level in front of you, turn your body until the needle is boxed, "
     "and walk toward a feature on that line — then repeat. A BACK bearing (add or subtract 180°) "
     "points the way you came."),
    ("orient_map", "Orienting the map to the ground", "compass", FM,
     "orient map north align compass terrain association match features ground where am i how to",
     "Orient the map so its top (north) points to real north — then everything on the paper lines up "
     "with the world in front of you. Lay the compass on the map with its edge along a north-south "
     "grid line, then turn the whole map-and-compass together until the needle points north (adjusted "
     "for declination). Now practice TERRAIN ASSOCIATION: match the hills, streams, and bends you see "
     "to the contours and features on the map. Knowing roughly where you are, and reading the ground, "
     "prevents most 'lost'."),
    ("pace_count", "Distance by pace count and dead reckoning", "measure", FM,
     "pace count distance dead reckoning steps 100 meters measure how far traveled navigation estimate",
     "Know how far you've walked by counting paces. On flat ground, count how many of YOUR paces (one "
     "pace = every time the same foot lands) cover 100 m — most adults are 60–70. Then in the field, "
     "count paces and multiply to estimate distance; add paces uphill, on rough ground, and when "
     "tired. DEAD RECKONING is navigating by a known bearing plus a measured distance from a known "
     "start — 'walk 300° for 800 m to the stream junction.' Use a knotted cord or pebbles to keep "
     "count without losing track."),
    ("north_by_sun", "Finding north by the sun", "sky", SKY,
     "north sun shadow stick method east west rises sets noon direction without compass day navigate",
     "The sun rises in the EAST and sets in the WEST (exactly so only near the equinoxes; it drifts "
     "north in summer, south in winter). At solar noon it sits due south in the northern hemisphere "
     "(due north in the southern). The SHADOW-STICK method: push a stick upright, mark the tip of its "
     "shadow, wait 15–20 minutes, mark the new tip — the line from the FIRST mark to the second runs "
     "roughly WEST to EAST, and a line square to it is north–south. An analog watch can also help, "
     "but the shadow stick needs no gear."),
    ("north_by_stars", "Finding north by the stars", "sky", SKY,
     "north star polaris big dipper southern cross night navigate direction stars find hemisphere sky",
     "At night in the NORTHERN hemisphere, find POLARIS, the North Star — it sits over true north and "
     "barely moves. Locate the Big Dipper; the two stars at the end of its 'cup' (the pointer stars) "
     "aim at Polaris, about five times their own spacing away. In the SOUTHERN hemisphere there's no "
     "pole star: find the SOUTHERN CROSS, extend its long axis about 4.5 times its length to an empty "
     "point in the sky, and drop straight down to the horizon — that is due south. Drop a line from "
     "the found pole star to the horizon; that point is north (or south)."),
    ("gps_limits", "GPS — useful, but never your only tool", "tools", FM,
     "gps satellite navigation battery signal limits backup map compass fail spoofing canyon forest trust",
     "GPS is precise and easy — and a single point of failure. It dies with the battery, loses signal "
     "in canyons, thick forest, and buildings, can be jammed or spoofed, and gives you a dot with no "
     "understanding of the terrain. Carry it, but treat the MAP and COMPASS as primary and the GPS as "
     "a check: note your position on the paper map regularly, so when the screen goes dark you already "
     "know where you are. Learn to navigate without it BEFORE you need to. Batteries and satellites "
     "fail; the sky and a printed map do not."),
    ("stay_found", "Staying found — and what to do when you're lost", "principle", FM,
     "lost stop stay found protocol navigate observe plan panic signal wait rescue what to do prevent",
     "The cure for lost is not getting lost: before you set out, study the route, note handrails "
     "(roads, ridges, streams you can follow) and a catching feature (a long road or river you can't "
     "miss) beyond your goal, and check your position often. If you DO become lost, STOP — Stop, "
     "Think, Observe, Plan. Don't wander or push on in fear. If you truly don't know the way and "
     "you're overdue, staying put makes you easier to find; make yourself visible, signal in threes, "
     "and conserve energy. Tell someone your plan and return time before every trip."),
]

BOUNDARY = (
    "THE NAVIGATION SHELF — what this is, and is not. These cards gather established land-navigation "
    "technique from a PUBLIC-DOMAIN source (U.S. Army FM 3-25.26) and long-known celestial fact. It is "
    "reference and preparation — practice with a real map and compass in easy country BEFORE you rely "
    "on it in hard country, and never bet your life on a skill you have only read about. Carry a map "
    "and compass and know your position even when a GPS is working. Tell someone your route and return "
    "time. Prepared, not fearful (Proverbs 22:3).")


def main() -> int:
    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The navigation shelf — map, compass, and the sky",
        "body": ("Finding your way with no battery: reading a topographic map, grid and lat/long "
                 "coordinates, the compass and declination, taking and following a bearing, orienting "
                 "the map, distance by pace count, and finding north by the sun and stars — with GPS "
                 "kept as a check, never the only tool. From the Army's public-domain land-navigation "
                 "manual. Beside the field library."),
        "source": {"label": "The navigation shelf (curated, public domain)", "url": "",
                   "domain": "navigation", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["navigation", "map", "compass", "land nav", "orienteering", "celestial", "off grid",
                  "prepper", "field", "spine"],
        "subject": "land navigation",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "finding the way through the created order, a spine of the Floor of Discovery"}],
        "author": "Matt Harris (the navigation shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False, "extra": {"license": "public-domain"},
    }
    cards = [spine]
    for slug, title, box, src_label, keywords, body in CARDS:
        cards.append({
            "id": f"card_nav_{slug}", "kind": "reference", "title": title,
            "body": f"{body}  — {src_label}.",
            "source": {"label": src_label, "url": "", "domain": "navigation", "authority_tier": "reference"},
            "shelf": "navigation", "box": box,
            "bands": (["navigation", "map", box.replace("_", " "), "how to"] + keywords.split())[:24],
            "subject": title,
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"land navigation ({box})"}],
            "author": "Matt Harris (the navigation shelf)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"category": box, "source": src_label, "license": "public-domain"},
        })
    cards.append({
        "id": "card_nav_boundary", "kind": "reference",
        "title": "The navigation shelf — practice before you rely on it",
        "body": BOUNDARY,
        "source": {"label": "The boundary", "url": "", "domain": "navigation", "authority_tier": "reference"},
        "shelf": "navigation", "box": "principle",
        "bands": ["boundary", "safety", "practice", "navigation", "map", "compass"],
        "subject": "the navigation shelf boundary",
        "connections": [{"to_card_id": SPINE, "relationship": "member_of", "evidence": "the boundary of the navigation shelf"}],
        "author": "Matt Harris (the navigation shelf)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    })
    out = Path("data") / "navigation_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    print(f"carded {len(cards) - 1} navigation entries (+1 spine) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
