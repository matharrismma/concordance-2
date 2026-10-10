#!/usr/bin/env python3
"""Nuclear physics floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_nuclear_physics.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_nuclear_physics'
STICK = 'stick_nuclear_physics_binding_decay_and_the_strong_force'
PILLARS = [{'key': 'strong_force', 'title': 'The strong force - what binds the nucleus', 'body': 'Protons repel electrically; the strong force (the residue of the gluon force) binds them, strong but short-ranged.', 'rests': [('card_floor_standard_model', 'the strong force is the residue of the gluon force - the Standard Model')]}, {'key': 'mass_energy', 'title': 'Mass is energy - the binding', 'body': 'A nucleus weighs less than its parts; the mass defect is the binding energy (931.5 MeV/amu, sealed).', 'rests': [('card_floor_relativity', 'E = mc^2 - the mass defect is binding energy')]}, {'key': 'decay', 'title': 'Decay - the half-life and tunnelling', 'body': 'Unstable nuclei decay exponentially (sealed); alpha decay is quantum tunnelling through the barrier.', 'rests': [('card_floor_quantum_mechanics', 'alpha decay is quantum tunnelling; decay is probabilistic')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'nuclear', FLOOR, 'card_spine_nuclear_physics', STICK, 'Nuclear physics — binding, decay, and the strong force', 'The nucleus is held by the strong force against electric repulsion; mass converts to binding energy at 931.5 MeV/amu; unstable nuclei decay on a half-life. Pillars rest on the Standard Model (the strong force), relativity (E=mc^2) and quantum mechanics (tunnelling). The stick (stick_nuclear_physics_binding_decay_and_the_strong_force) seals the amu-to-MeV and a decay fraction (tools/seed_nuclear_physics.py).', PILLARS, 'the nucleus on the one map, rooted in the Floor of Discovery', ['seed_standard_model_chain', 'seed_relativity', 'seed_quantum_mechanics'])

if __name__ == "__main__":
    raise SystemExit(main())
