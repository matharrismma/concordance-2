#!/usr/bin/env python3
"""Geography floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_geography.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = "card_floor_geography"
STICK = "stick_geography_the_measured_earth"
PILLARS = [
    dict(key="coordinates", title="Coordinates — the grid on the globe",
         body="A degree of latitude is about 111 km (sealed), a minute of arc a nautical mile; latitude and "
              "longitude turn the globe into addressable space.",
         rests=[("card_floor_earth_science", "the coordinate grid on the planet"),
                ("card_floor_the_instruments", "coordinates and distance are geometry - the measure spine")]),
    dict(key="projection", title="Projection — the flat map must distort",
         body="Longitude is time (15 degrees per hour, sealed), and any flat map of a sphere must distort area or "
              "angle - a sphere has no flat image (Gauss). Every projection is a choice of what to preserve.",
         rests=[("card_floor_the_instruments", "map projection is geometry - no isometry from sphere to plane")]),
]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    "geography", FLOOR, "card_spine_geography", STICK,
    "Geography — the measured Earth",
    ("A degree of latitude is 111 km; longitude is time (15 degrees per hour); and any flat map of a sphere must "
     "distort. Two pillars rest on earth science (the planet) and the instruments (coordinates and projection are "
     "geometry). The science of WHERE. The stick (" + STICK + ") seals the kilometres per degree and the degrees "
     "per hour (tools/seed_geography.py)."),
    PILLARS, "the measured Earth on the one map, rooted in the Floor of Discovery",
    ["seed_earth_science", "seed_instruments"])

if __name__ == "__main__":
    raise SystemExit(main())
