"""Unit-pin the music_theory verifier (A2, 2026-10-06). C to G is a perfect fifth = 7 semitones; MIDI
note 69 (A4) = 440 Hz in equal temperament. Wrong claim caught; missing field NOT_APPLICABLE."""
from __future__ import annotations
from concordance.verifiers import music_theory as MU


def test_interval_semitones():
    assert MU.verify_interval_semitones({"note_a": "C", "note_b": "G", "claimed_semitones": 7}).status == "CONFIRMED"
    assert MU.verify_interval_semitones({"note_a": "C", "note_b": "G", "claimed_semitones": 5}).status == "MISMATCH"
    assert MU.verify_interval_semitones({}).status == "NOT_APPLICABLE"


def test_equal_temperament_freq():
    assert MU.verify_equal_temperament_freq({"midi_note": 69, "claimed_frequency_hz": 440}).status == "CONFIRMED"
    assert MU.verify_equal_temperament_freq({"midi_note": 69, "claimed_frequency_hz": 400}).status == "MISMATCH"
