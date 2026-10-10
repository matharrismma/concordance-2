#!/usr/bin/env python3
"""Logistics floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_logistics.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_logistics'
STICK = 'stick_logistics_the_optimization_core_verified_and_sealed'
PILLARS = [{'key': 'flow', 'title': 'Flow - shortest paths and schedules', 'body': 'Routing, scheduling and inventory minimize cost subject to constraints; the arithmetic is sealed on the logistics stick.', 'rests': [('card_floor_economics', 'cost, scarcity and value - the economics of moving goods')]}, {'key': 'hardness', 'title': 'Hardness - routing is NP', 'body': "The travelling salesman and vehicle routing are NP-hard; good heuristics get close - the solve path's get-close door.", 'rests': [('card_floor_computer_science', 'optimization and NP-hardness - the algorithms of logistics')]}, {'key': 'strategy', 'title': 'Strategy - competition and cooperation', 'body': 'Supply chains are strategic: competitors, suppliers and shocks. Game theory governs the equilibria.', 'rests': [('card_floor_game_theory', 'supply chains are strategic - competition and cooperation')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'logistics', FLOOR, 'card_spine_logistics', STICK, 'Logistics — moving things at least cost', 'Getting goods from here to there at least cost: shortest paths, scheduling, inventory, the travelling salesman. The optimization arithmetic is already sealed on the logistics stick; this floor places it, resting on economics (cost and scarcity), computer science (the algorithms and the NP-hardness of routing) and game theory (competition and cooperation). No new stick (tools/seed_logistics.py).', PILLARS, 'moving things at least cost on the one map, rooted in the Floor of Discovery', ['seed_economics', 'seed_computer_science', 'seed_game_theory'])

if __name__ == "__main__":
    raise SystemExit(main())
