#!/usr/bin/env python3
"""Soil science floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_soil_science.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_soil_science'
STICK = 'stick_soil_science_the_living_skin_of_the_land'
PILLARS = [{'key': 'minerals', 'title': 'Minerals and nutrients - the chemistry', 'body': 'Soil holds nutrients by its chemistry (pH, cation exchange); the loam composition sums to 100 (sealed).', 'rests': [('card_floor_chemistry', 'soil nutrients, pH and cation exchange - chemistry')]}, {'key': 'parent_rock', 'title': 'Parent rock - weathering over deep time', 'body': 'Soil is rock weathered over deep time by water, frost and life; the mineral fraction is its ground-up parent.', 'rests': [('card_floor_earth_science', 'soil is weathered parent rock - earth science over deep time')]}, {'key': 'life', 'title': 'Life - microbes, fungi, roots', 'body': 'Soil is alive: microbes and fungi cycle the carbon-to-nitrogen balance (sealed), roots and worms build structure.', 'rests': [('card_floor_biology', 'the soil biota - microbes, fungi, roots')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'soil', FLOOR, 'card_spine_soil_science', STICK, 'Soil science — the living skin of the land', 'Soil is mineral, water, air and organic matter in rough proportion, alive with microbes, holding nutrients by a carbon-to-nitrogen balance. Pillars rest on chemistry (minerals and nutrients), earth science (weathering) and biology (microbes and roots). The stick (stick_soil_science_the_living_skin_of_the_land) seals the loam composition and the C:N ratio (tools/seed_soil_science.py).', PILLARS, 'the living soil on the one map, rooted in the Floor of Discovery', ['seed_chemistry', 'seed_earth_science', 'seed_biology'])

if __name__ == "__main__":
    raise SystemExit(main())
