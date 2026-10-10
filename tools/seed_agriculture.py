#!/usr/bin/env python3
"""Agriculture floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_agriculture.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_agriculture'
STICK = 'stick_agriculture_soil_sun_and_chemistry_into_food'
PILLARS = [{'key': 'the_crop', 'title': 'The crop - photosynthesis and growth', 'body': 'A crop is stored sunlight: 6 CO2 + 6 H2O -> glucose + 6 O2 (glucose molar mass sealed). Rests on biology.', 'rests': [('card_floor_biology', 'the crop is a living organism building sugar from light')]}, {'key': 'fertilizer', 'title': 'Fertilizer - fixing nitrogen', 'body': 'Haber-Bosch makes ammonia (sealed), the synthetic nitrogen that feeds roughly half the world. Rests on chemistry.', 'rests': [('card_floor_chemistry', 'Haber-Bosch and soil chemistry - fertilizer')]}, {'key': 'agroecosystem', 'title': 'The agro-ecosystem - pests and pollinators', 'body': 'A farm is an ecosystem: pests, pollinators, and the 10 percent rule that makes plants cheaper food than meat. Rests on ecology.', 'rests': [('card_floor_ecology', 'the farm as an ecosystem - the 10 percent rule')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'agriculture', FLOOR, 'card_spine_agriculture', STICK, 'Agriculture — soil, sun, and chemistry into food', 'Crops fix carbon by photosynthesis (glucose) and need fixed nitrogen (Haber-Bosch ammonia, feeding half the world). Pillars rest on biology (the crop), chemistry (fertilizer and photosynthesis) and ecology (the agro-ecosystem). The stick (stick_agriculture_soil_sun_and_chemistry_into_food) seals ammonia per mole of nitrogen and the molar mass of glucose (tools/seed_agriculture.py).', PILLARS, 'feeding the world on the one map, rooted in the Floor of Discovery', ['seed_biology', 'seed_chemistry', 'seed_ecology'])

if __name__ == "__main__":
    raise SystemExit(main())
