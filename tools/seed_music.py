#!/usr/bin/env python3
"""Music floor on the one map (Matt, 2026-10-10: "did you complete music?" - the orphaned
music-theory stick, placed). Uses tools/_seedlib.py. Cites the existing sealed stick; no new stick.
    PYTHONPATH=src python tools/seed_music.py [--check]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _seedlib as L

FLOOR = 'card_floor_music'
STICK = 'stick_music_theory_intervals_and_tuning_verified_and_sealed'
PILLARS = [
    {'key': 'intervals', 'title': 'Intervals — the harmonic series in small ratios',
     'body': "The octave is the ratio 2:1, the perfect fifth 3:2, the fourth 4:3 — the consonant intervals are "
             "the low harmonics of a vibrating string or air column, sealed on the music-theory stick. A chord is "
             "stacked ratios.",
     'rests': [('card_floor_acoustics', 'intervals are ratios of the harmonic series - the physics of sound')]},
    {'key': 'tuning', 'title': 'Tuning — equal temperament and the comma',
     'body': "Twelve-tone equal temperament sets every semitone at the irrational ratio 2^(1/12); it is a deliberate "
             "compromise that spreads the Pythagorean comma evenly so every key is playable. A tuning is a CHOICE, "
             "not a law of nature.",
     'rests': [('card_floor_acoustics', 'a tuning divides the octave of frequency - waves'),
               ('card_floor_metrology', 'pitch is a frequency in hertz, built on the SI second')]},
    {'key': 'pitch', 'title': 'Pitch — A440 and the measured reference',
     'body': "Concert pitch fixes A above middle C at 440 Hz (MIDI note 69), sealed; the ensemble tunes to it under "
             "f = 440 * 2^((n-69)/12). Pitch is a measured frequency, and the interval arithmetic is sealed through "
             "the engine's music verifier.",
     'rests': [('card_floor_metrology', 'A440 is a reference frequency - measurement'),
               ('card_floor_the_instruments', 'the music verifier seals the interval and tuning arithmetic')]},
]
CARDS, BRIDGES, known_nodes, _validate, main = L.make(
    'music', FLOOR, 'card_spine_music', STICK, 'Music — interval, tuning, and the harmonic series',
    "Music is number made audible: the consonant intervals are small whole-number frequency ratios (octave 2:1, "
    "fifth 3:2, fourth 4:3), and a scale is a tuning that divides the octave — equal temperament by the irrational "
    "2^(1/12), paying the Pythagorean comma evenly so every key is playable. The interval and tuning arithmetic is "
    "already sealed on the music-theory stick, through the engine's music verifier; this floor places music on the "
    "map, resting on acoustics (the wave and the harmonic series), metrology (A440, pitch in hertz) and the "
    "instruments (the verifier). Taste — whether a chord is beautiful — is declined; the engine seals the ratios, "
    "not the beauty. No new stick (tools/seed_music.py).",
    PILLARS, 'music on the one map, rooted in the Floor of Discovery',
    ['seed_acoustics', 'seed_metrology', 'seed_instruments'])

if __name__ == "__main__":
    raise SystemExit(main())
