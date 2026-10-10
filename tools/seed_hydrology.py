#!/usr/bin/env python3
"""Hydrology floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_hydrology.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_hydrology'
STICK = 'stick_hydrology_the_water_cycle_and_the_flow_of_rivers'
PILLARS = [{'key': 'flow', 'title': 'Flow - discharge and the continuity equation', 'body': 'Q = v A governs every river and flood (sealed); conservation of mass is the continuity equation. Rests on earth science.', 'rests': [('card_floor_earth_science', 'rivers and basins - the flow of water over the land')]}, {'key': 'the_solvent', 'title': 'Water the solvent', 'body': 'Water carries salts, nutrients and life; its chemistry makes it the universal solvent. Rests on chemistry.', 'rests': [('card_floor_chemistry', 'water the universal solvent - the chemistry of the cycle')]}, {'key': 'the_cycle', 'title': 'The cycle - precipitation and runoff', 'body': 'Evaporation, precipitation and runoff keep the 2.5 percent fresh water moving (sealed). Rests on meteorology.', 'rests': [('card_floor_meteorology', 'precipitation - where the water cycle touches the sky')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'hydrology', FLOOR, 'card_spine_hydrology', STICK, 'Hydrology — the water cycle and the flow of rivers', 'River discharge is velocity times cross-section (Q = v A); only 2.5 percent of Earth water is fresh. Pillars rest on earth science (basins and the cycle), chemistry (water the solvent) and meteorology (precipitation). The stick (stick_hydrology_the_water_cycle_and_the_flow_of_rivers) seals a discharge and the freshwater percentage (tools/seed_hydrology.py).', PILLARS, 'water in motion on the one map, rooted in the Floor of Discovery', ['seed_earth_science', 'seed_chemistry', 'seed_meteorology'])

if __name__ == "__main__":
    raise SystemExit(main())
