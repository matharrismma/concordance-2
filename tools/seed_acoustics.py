#!/usr/bin/env python3
"""Acoustics on the one map (Matt, 2026-10-10, down the domain list - after game theory).

The physics of sound and hearing, standing between matter and mind. A floor whose pillars rest on the floors
already seeded:
  * THE WAVE - v = f lambda; sound needs a medium. Rests on chemistry (the medium).
  * LOUDNESS - the decibel, a logarithm. Rests on the mind (perception).
  * HARMONICS - pitch, timbre, phonons. Rests on quantum mechanics (phonons).
  * THE DOPPLER EFFECT - the acoustic cousin of the redshift. Rests on relativity.
The stick (stick_acoustics_waves_loudness_and_harmonics) seals the wavelength of concert A, a 30 dB power ratio,
and a third harmonic. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_acoustics.py           # merge
    PYTHONPATH=src python tools/seed_acoustics.py --check   # validate, write nothing
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

FLOOR = "card_floor_acoustics"
SPINE = "card_spine_acoustics"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
STICK = "stick_acoustics_waves_loudness_and_harmonics"

F_CHEM = "card_floor_chemistry"
F_MIND = "card_floor_the_mind"
F_QM = "card_floor_quantum_mechanics"
F_REL = "card_floor_relativity"

PILLARS = [
    dict(key="the_wave", title="The wave — v = f lambda",
         body="Sound is a travelling pressure wave: v = f lambda. Concert A at 440 Hz has wavelength 0.78 m in air "
              "(sealed). Unlike light it needs a MEDIUM - no air, no sound - and its speed is set by the medium's "
              "stiffness and density. Rests on chemistry (the medium).",
         rests=[(F_CHEM, "sound needs a material medium; its speed is set by the medium's stiffness and density")]),
    dict(key="loudness", title="Loudness — the decibel, a logarithm",
         body="The ear spans a trillion-fold range, so loudness is measured in decibels: every 10 dB is a tenfold "
              "power ratio, 30 dB a thousandfold (sealed). Perception compresses huge ranges logarithmically. Rests "
              "on the mind.",
         rests=[(F_MIND, "loudness is logarithmic perception - the decibel, a psychophysical scale")]),
    dict(key="harmonics", title="Harmonics — pitch, timbre, phonons",
         body="Pitch is frequency; a string also rings at integer multiples (the harmonic series), and their mix is "
              "timbre. The third harmonic of 220 Hz is 660 Hz (sealed). Quantized, a sound wave's quanta are "
              "PHONONS. Rests on quantum mechanics.",
         rests=[(F_QM, "phonons - the quanta of lattice vibration, the harmonic oscillator applied to sound")]),
    dict(key="doppler", title="The Doppler effect — the acoustic redshift",
         body="A source moving toward you raises the pitch, away lowers it (the passing siren) - the waves bunch "
              "ahead and stretch behind. It is the acoustic cousin of the relativistic redshift of light. Rests on "
              "relativity.",
         rests=[(F_REL, "the Doppler effect is the acoustic analogue of the redshift - same geometry, different medium")]),
]


def _pid(key: str) -> str:
    return f"card_acoustics_{key}"


def _card(cid: str, kind: str, title: str, body: str, bands: List[str], ref: str = "") -> dict:
    src = {"label": "Narrow Highway — acoustics", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {
        "id": cid, "kind": kind, "title": title, "body": body, "source": src,
        "shelf": "codex", "box": "acoustics", "bands": bands, "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    return _card(
        FLOOR, "note", "Acoustics — waves, loudness, and harmonics",
        ("The physics of sound and hearing, standing between matter and mind. Sound is a pressure wave in a medium "
         "(v = f lambda); loudness is logarithmic (the decibel); pitch is frequency and timbre is the harmonic "
         "series; a moving source shifts pitch (the Doppler effect, the acoustic cousin of the redshift). Four "
         "pillars rest on chemistry (the medium), the mind (perception), quantum mechanics (phonons), and relativity "
         "(Doppler). The stick (" + STICK + ") seals concert A's wavelength, a 30 dB ratio, and a third harmonic "
         "(tools/seed_acoustics.py)."),
        ["floor", "acoustics", "sound", "decibel", "harmonics", "one map"],
        ref=STICK,
    )


def spine_card() -> dict:
    c = _card(SPINE, "reference", "Acoustics — a spine", "The pillars of acoustics.",
              ["acoustics", "spine", "one map"])
    c["shelf"] = "spine"
    c["box"] = "spine"
    c["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "the physics of sound on the one map, rooted in the Floor of Discovery"}]
    return c


CARDS: List[dict] = [floor_card(), spine_card()]
for _p in PILLARS:
    CARDS.append(_card(_pid(_p["key"]), "reference", _p["title"], _p["body"],
                       ["acoustics", "pillar", _p["key"], "one map"]))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    for p in PILLARS:
        out.append(_edge(_pid(p["key"]), FLOOR, "part_of", f"a pillar of acoustics ({p['title'].split(' — ')[0]})"))
        for target, ev in p["rests"]:
            out.append(_edge(_pid(p["key"]), target, "connects_at", ev))
    out.append(_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the physics of sound on the one map"))
    return out


BRIDGES: List[dict] = _bridges()


def known_nodes() -> set:
    ids = {c["id"] for c in CARDS}
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_chemistry as CH
        import seed_the_mind as MIND
        import seed_quantum_mechanics as QM
        import seed_relativity as REL
        ids |= {c["id"] for c in CH.CARDS} | {c["id"] for c in MIND.CARDS}
        ids |= {c["id"] for c in QM.CARDS} | {c["id"] for c in REL.CARDS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs: List[str] = []
    ids = known_nodes()
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] != GLOBAL_FLOOR:
            errs.append(f"edge target unknown: {e['b']} (from {e['a']})")
    if len({c["id"] for c in CARDS}) != len(CARDS):
        errs.append("duplicate card ids")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards ({len(PILLARS)} pillars + floor + spine), "
              f"{len(BRIDGES)} edges; {'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed) and "
          f"{DATA/'chain_bridges.jsonl'} ({n['bridges']} edges, {len(BRIDGES)} from this seed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
