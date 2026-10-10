#!/usr/bin/env python3
"""Oceanography floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_oceanography.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = "card_floor_oceanography"
STICK = "stick_oceanography_the_salt_sea_in_motion"
PILLARS = [
    dict(key="pressure", title="The weight of water — pressure with depth",
         body="Pressure rises about one atmosphere per 10 m (10 atm at 100 m, sealed); the deep sea crushes, and "
              "depth is read as pressure.",
         rests=[("card_floor_earth_science", "pressure with depth in the ocean basins")]),
    dict(key="salinity", title="The salt sea — salinity and density",
         body="Seawater is about 3.5 percent salt (sealed), mostly sodium chloride; salinity and temperature set "
              "density, which drives circulation.",
         rests=[("card_floor_chemistry", "dissolved salts - the chemistry of seawater")]),
    dict(key="circulation", title="Circulation — the thermohaline conveyor",
         body="Density differences drive the deep thermohaline circulation, a heat engine that moves the planet's "
              "heat and buffers its climate.",
         rests=[("card_floor_thermodynamics", "the thermohaline circulation - a density-driven heat engine")]),
]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    "oceanography", FLOOR, "card_spine_oceanography", STICK,
    "Oceanography — the salt sea in motion",
    ("Pressure rises with depth; seawater is 3.5 percent salt; density differences drive the thermohaline conveyor. "
     "Three pillars rest on earth science (the basins), chemistry (dissolved salts) and thermodynamics (currents). "
     "The sea covers 71 percent of the planet. The stick (" + STICK + ") seals the gauge pressure at 100 m and the "
     "salinity fraction (tools/seed_oceanography.py)."),
    PILLARS, "the sea on the one map, rooted in the Floor of Discovery",
    ["seed_earth_science", "seed_chemistry", "seed_thermodynamics"])

if __name__ == "__main__":
    raise SystemExit(main())
