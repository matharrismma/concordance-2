#!/usr/bin/env python3
"""Education floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_education.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_education'
STICK = 'stick_education_how_a_mind_learns_and_is_taught'
PILLARS = [{'key': 'learning', 'title': 'Learning - memory and the forgetting curve', 'body': 'Retention fades as e^(-t/S); spaced repetition and recall flatten it (1/e sealed). Learning is neural change.', 'rests': [('card_floor_the_mind', 'learning is neural change; memory is storage and recall')]}, {'key': 'assessment', 'title': 'Assessment - measuring learning', 'body': 'Tests, item response and readability (Flesch, sealed) measure what was learned and how hard the text is.', 'rests': [('card_floor_statistics', 'assessment and readability are statistics')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'education', FLOOR, 'card_spine_education', STICK, 'Education — how a mind learns and is taught', 'Memory fades on a forgetting curve, beaten by spaced repetition and the testing effect; text has a measurable reading level. Pillars rest on the mind (learning and memory) and statistics (assessment). Teaching is training. The stick (stick_education_how_a_mind_learns_and_is_taught) seals the 1/e retention and a Flesch reading-ease score (tools/seed_education.py).', PILLARS, 'the teaching of minds on the one map, rooted in the Floor of Discovery', ['seed_the_mind', 'seed_statistics'])

if __name__ == "__main__":
    raise SystemExit(main())
