#!/usr/bin/env python3
"""Ecology floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_ecology.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = "card_floor_ecology"
STICK = "stick_ecology_energy_and_number_in_the_living_world"
PILLARS = [
    dict(key="energy_flow", title="Energy flow — the 10 percent rule",
         body="About a tenth of the energy at one trophic level reaches the next (sealed), so food chains are short "
              "and top predators rare - the second law paid at every step.",
         rests=[("card_floor_biology", "trophic levels - who eats whom in the living world"),
                ("card_floor_thermodynamics", "energy is lost as heat up the food chain - the second law")]),
    dict(key="populations", title="Populations — logistic growth",
         body="A population grows fastest at half its carrying capacity (sealed); logistic growth and predator-prey "
              "cycles are the arithmetic of number in the wild.",
         rests=[("card_floor_statistics", "population dynamics and sampling - the statistics of number")]),
    dict(key="habitat", title="Habitat — climate and place",
         body="Where life lives is set by climate, soil and water - earth science. Biomes map onto temperature and "
              "rainfall; change the climate and the ranges move.",
         rests=[("card_floor_earth_science", "biomes track climate and place - habitat is earth science")]),
]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    "ecology", FLOOR, "card_spine_ecology", STICK,
    "Ecology — energy and number in the living world",
    ("Energy drops tenfold each trophic level; populations grow logistically; habitat is set by climate. Three "
     "pillars rest on biology (organisms and the tree of life), statistics (population dynamics) and earth science "
     "(habitat). The accounting of energy and number across the living world. The stick (" + STICK + ") seals the "
     "trophic transfer and the fastest-growth point (tools/seed_ecology.py)."),
    PILLARS, "the living world on the one map, rooted in the Floor of Discovery",
    ["seed_biology", "seed_statistics", "seed_earth_science", "seed_thermodynamics"])

if __name__ == "__main__":
    raise SystemExit(main())
