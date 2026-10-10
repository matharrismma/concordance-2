#!/usr/bin/env python3
"""Meteorology floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_meteorology.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = "card_floor_meteorology"
STICK = "stick_meteorology_the_atmosphere_as_a_heat_engine"
PILLARS = [
    dict(key="adiabatic", title="Air rising cools — the lapse rate",
         body="A lifted air parcel expands and cools at g/cp ~ 9.75 C/km (sealed), making clouds and storms. The "
              "atmosphere is a Sun-driven heat engine.",
         rests=[("card_floor_thermodynamics", "the adiabatic lapse rate - the atmosphere as a heat engine")]),
    dict(key="circulation", title="Circulation — the rotating planet",
         body="Winds and storms are organized by the Earth's rotation (the Coriolis effect) and the Sun's uneven "
              "heating. The general circulation moves heat from equator to pole.",
         rests=[("card_floor_earth_science", "the Coriolis effect and the general circulation - the rotating planet")]),
    dict(key="forecasting", title="Forecasting — probability and chaos",
         body="Weather is predicted statistically, and chaos limits how far: small errors grow, so forecasts are "
              "probabilities with a horizon of about two weeks.",
         rests=[("card_floor_statistics", "forecasts are probabilities; chaos bounds predictability")]),
]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    "meteorology", FLOOR, "card_spine_meteorology", STICK,
    "Meteorology — the atmosphere as a heat engine",
    ("Air rising cools at the lapse rate; the rotating planet organizes winds; forecasts are probabilities bounded "
     "by chaos. Three pillars rest on thermodynamics (the heat engine), earth science (the rotating planet) and "
     "statistics (forecasting). The stick (" + STICK + ") seals the lapse rate and the molar volume "
     "(tools/seed_meteorology.py)."),
    PILLARS, "the weather on the one map, rooted in the Floor of Discovery",
    ["seed_thermodynamics", "seed_earth_science", "seed_statistics"])

if __name__ == "__main__":
    raise SystemExit(main())
