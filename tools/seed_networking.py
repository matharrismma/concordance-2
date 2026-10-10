#!/usr/bin/env python3
"""Networking floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_networking.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_networking'
STICK = 'stick_networking_addresses_packets_and_capacity'
PILLARS = [{'key': 'addressing', 'title': 'Addressing - counting in binary', 'body': 'IPv4 is 2^32 addresses, a /24 subnet 2^8 = 256 (both sealed); routing is binary arithmetic on addresses.', 'rests': [('card_floor_computer_science', 'addressing and routing are binary arithmetic - computation')]}, {'key': 'capacity', 'title': "Capacity - Shannon's ceiling", 'body': 'A channel carries at most C = B log2(1+S/N) bits/s (Shannon); no code beats it. Packets and error-correction live under it.', 'rests': [('card_floor_the_instruments', 'the Shannon-Hartley capacity - the information instrument')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'net', FLOOR, 'card_spine_networking', STICK, 'Networking — addresses, packets, and capacity', 'The internet routes packets between addresses (IPv4 has 2^32); a channel has a hard Shannon capacity. Pillars rest on computer science (machines and protocols) and the instruments (the channel capacity). The stick (stick_networking_addresses_packets_and_capacity) seals the IPv4 space and a subnet size (tools/seed_networking.py).', PILLARS, 'the network on the one map, rooted in the Floor of Discovery', ['seed_computer_science', 'seed_instruments'])

if __name__ == "__main__":
    raise SystemExit(main())
