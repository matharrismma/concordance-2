#!/usr/bin/env python3
"""Quantum computing floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_quantum_computing.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_quantum_computing'
STICK = 'stick_quantum_computing_qubits_and_superposition'
PILLARS = [{'key': 'superposition', 'title': 'Superposition - the exponential state space', 'body': 'n qubits carry 2^n amplitudes at once (sealed); the resource is superposition and entanglement.', 'rests': [('card_floor_quantum_mechanics', 'superposition and entanglement are the quantum resource')]}, {'key': 'computation', 'title': 'Computation - interference and complexity', 'body': 'The speedup is making wrong answers interfere away (Grover sqrt-N, sealed; Shor); still computation, class BQP.', 'rests': [('card_floor_computer_science', 'quantum computation - a complexity class of its own')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'qc', FLOOR, 'card_spine_quantum_computing', STICK, 'Quantum computing — qubits and superposition', "A qubit is a superposition of 0 and 1, so n qubits hold 2^n amplitudes; the power is interference (Grover, Shor). Pillars rest on quantum mechanics (superposition, entanglement) and computer science (computation). The stick (stick_quantum_computing_qubits_and_superposition) seals the 10-qubit state space and Grover's speedup (tools/seed_quantum_computing.py).", PILLARS, 'quantum computation on the one map, rooted in the Floor of Discovery', ['seed_quantum_mechanics', 'seed_computer_science'])

if __name__ == "__main__":
    raise SystemExit(main())
