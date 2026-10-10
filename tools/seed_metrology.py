#!/usr/bin/env python3
"""Metrology floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_metrology.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_metrology'
STICK = 'stick_metrology_measurement_and_the_si'
PILLARS = [{'key': 'base_units', 'title': 'Base units - defined by constants', 'body': 'Seven SI units built from seven fixed constants: the metre from c (sealed), the kilogram from the Planck constant, the second from caesium. Anchored to nature.', 'rests': [('card_floor_the_instruments', 'the 6-constant measure spine defines the units'), ('card_floor_quantum_mechanics', 'the kilogram is fixed by the Planck constant')]}, {'key': 'conversion', 'title': 'Conversion - exact factors and dimensions', 'body': 'Units convert by defined factors (1 inch = 2.54 cm, sealed); dimensional analysis tracks units through a calculation and catches errors.', 'rests': [('card_floor_the_instruments', 'dimensional analysis - a sealed number carries its unit')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'metro', FLOOR, 'card_spine_metrology', STICK, 'Metrology — measurement and the SI', 'Measurement is the ground of every sealed number: the SI defines its units by fixing constants (the metre by c), and every unit converts by exact factors. Pillars rest on the instruments (the 6-constant measure spine) and quantum mechanics (the kilogram by the Planck constant). The stick (stick_metrology_measurement_and_the_si) seals the defined speed of light and the inch (tools/seed_metrology.py).', PILLARS, 'measurement on the one map, rooted in the Floor of Discovery', ['seed_instruments', 'seed_quantum_mechanics'])

if __name__ == "__main__":
    raise SystemExit(main())
