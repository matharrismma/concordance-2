#!/usr/bin/env python3
"""The calendar floor on the one map (Matt, 2026-10-10, down the list). Uses tools/_seedlib.py.
    PYTHONPATH=src python tools/seed_calendar.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_the_calendar'
STICK = 'stick_the_calendar_keeping_time_by_sun_and_number'
PILLARS = [{'key': 'the_day', 'title': 'The day - one rotation', 'body': 'A day is one turn of the Earth, 24 x 60 x 60 = 86400 seconds (sealed); the base-60 division is Babylonian, the second now an SI unit.', 'rests': [('card_floor_astronomy', 'the day is one rotation of the Earth'), ('card_floor_metrology', 'the second is the SI base unit of time')]}, {'key': 'the_year', 'title': 'The year - one orbit and the leap rule', 'body': 'A tropical year is 365.2422 days; the Gregorian leap rule averages 365.2425 (sealed), 97 leap days per 400 years - number chasing the sun.', 'rests': [('card_floor_astronomy', 'the year is one orbit of the Earth around the Sun')]}]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'cal', FLOOR, 'card_spine_the_calendar', STICK, 'The calendar — keeping time by sun and number', 'The day is one rotation (86400 s), the year one orbit (~365.2422 days); the Gregorian calendar approximates it as 365.2425 by a leap rule. Pillars rest on astronomy (the orbit and rotation) and metrology (the second). The stick (stick_the_calendar_keeping_time_by_sun_and_number) seals the seconds in a day and the Gregorian mean year (tools/seed_calendar.py).', PILLARS, 'the keeping of time on the one map, rooted in the Floor of Discovery', ['seed_astronomy', 'seed_metrology'])

if __name__ == "__main__":
    raise SystemExit(main())
