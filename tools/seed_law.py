#!/usr/bin/env python3
"""Law floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_law.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_law'
STICK = 'stick_law_structural_checks_on_public_domain_us_law_sealed'
PILLARS = [{'key': 'rules_and_inference', 'title': 'Rules and inference - law is applied logic', 'body': 'Statutes and precedent are premises; a ruling is an inference. The structural checks are sealed on the law stick.', 'rests': [('card_floor_the_instruments', 'law is deduction over rules - the formal-logic instrument')]}, {'key': 'society', 'title': 'Society - obligation and rights', 'body': 'Law binds a society of minds: duties, rights, consent. It is how a people agree to be governed.', 'rests': [('card_floor_the_mind', 'law governs a society of minds - obligation and rights')]}, {'key': 'incentives', 'title': 'Incentives - deterrence and remedy', 'body': 'Penalty and remedy are incentives; law shapes behaviour the way prices do, by changing the payoffs.', 'rests': [('card_floor_economics', 'deterrence and remedy are incentives - the economics of law')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'law', FLOOR, 'card_spine_law', STICK, 'Law — rules, evidence, and inference', 'Law is a rule system applied to facts: statutes and precedent (the rules), evidence (the facts), and inference (the argument). The structural checks on public-domain US law are sealed on the law stick; this floor places it, resting on the instruments (formal logic - law is deduction over rules), the mind (society and obligation) and economics (incentives and deterrence). No new stick (tools/seed_law.py).', PILLARS, 'the rule of law on the one map, rooted in the Floor of Discovery', ['seed_instruments', 'seed_the_mind', 'seed_economics'])

if __name__ == "__main__":
    raise SystemExit(main())
