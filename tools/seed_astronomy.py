#!/usr/bin/env python3
"""Astronomy floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_astronomy.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_astronomy'
STICK = 'stick_astronomy_orbits_and_distances_verified_and_sealed'
PILLARS = [{'key': 'orbits', 'title': 'Orbits - Kepler, Newton, Einstein', 'body': "Planets obey Kepler's laws and Newton's gravity (sealed on the astronomy stick); near a mass, general relativity corrects them (Mercury's precession).", 'rests': [('card_floor_relativity', 'orbits and precession - gravity as geometry')]}, {'key': 'distances', 'title': 'Distances - the ladder of starlight', 'body': 'Parallax, Cepheids and supernovae measure cosmic distance, all read from LIGHT - a Maxwell wave carrying a spectrum and a redshift.', 'rests': [('card_floor_maxwells_equations', 'the distance ladder is read from starlight - electromagnetism')]}, {'key': 'measurement', 'title': 'Measurement - the astronomical instruments', 'body': "Telescopes and the parallax arithmetic turn the sky into data; the engine's astronomy verifier seals the orbital and distance arithmetic.", 'rests': [('card_floor_the_instruments', 'the astronomy verifier - orbits and distances measured')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'astro', FLOOR, 'card_spine_astronomy', STICK, 'Astronomy — orbits, distances, and the cosmos', 'Orbits obey Kepler and Newton; distances climb the ladder (parallax, standard candles); the cosmos is governed by general relativity. The orbital arithmetic is already sealed on the astronomy stick; this floor places it, resting on relativity (gravity as geometry, cosmology), Maxwell (starlight and spectroscopy) and the instruments (the measurement). No new stick (tools/seed_astronomy.py).', PILLARS, 'the heavens on the one map, rooted in the Floor of Discovery', ['seed_relativity', 'seed_maxwells_equations', 'seed_instruments'])

if __name__ == "__main__":
    raise SystemExit(main())
