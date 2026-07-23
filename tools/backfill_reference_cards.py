#!/usr/bin/env python3
"""Backfill: the deep reference work the verifiers already hold becomes cards, in git.

Matt: "We should have an extremely comprehensive depth of cards in each area, and we have done
the work. They just aren't getting connected. The content should be on the github at the least."

Right. Each verifier carries real, in-repo reference data — the periodic table (118 elements),
the physical constants — that was never carded, so it lived in the code but not in the graph.
This emits a card per fact into `data/reference_cards.jsonl`, a GIT-TRACKED source (the content
on github, as asked), which the corpus loads alongside Scripture and the tradition.

Facts, not verifications — so there is no "false" here; elimination (BROKEN narrows the way)
is already carded by science_cards.py at the seal. This is the true-depth half.

Idempotent (deterministic ids), deterministic order. Extensible: add an emitter for each further
dataset (nuclides, stars, species, units, RFCs, ports…) and this cards them too.

    python tools/backfill_reference_cards.py            # write reference_cards.jsonl
    python tools/backfill_reference_cards.py --check     # count only, write nothing
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _out_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "reference_cards.jsonl"


def _card(cid, title, body, shelf, domain, bands):
    return {"id": cid, "kind": "reference", "title": title, "body": body,
            "source": {"label": f"Verified reference — {domain}", "url": "",
                       "domain": domain, "authority_tier": "reference"},
            "shelf": shelf, "box": "reference", "bands": bands, "connections": [],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False}


def _elements():
    from concordance.verifiers import periodic_table as pt
    out = []
    for z, sym, name, mass in pt._ELEMENTS:
        title = f"{name.capitalize()} ({sym}) — element {z}"
        body = (f"Atomic number {z}. Symbol {sym}. Standard atomic weight {mass}. "
                f"The {name} atom carries {z} proton{'s' if z != 1 else ''} in its nucleus; "
                f"its place in the periodic table is fixed by that count. Verified reference data.")
        out.append(_card(f"card_ref_el_{z:03d}", title, body, "chemistry", "chemistry",
                         ["reference", "chemistry", "periodic table", sym, name]))
    return out


def _constants():
    from concordance.verifiers import physical_constants as pc
    out = []
    for key, d in pc._CONSTANTS.items():
        name = key.replace("_", " ")
        val, unit = d.get("value"), d.get("unit", "")
        exact = "exact by definition" if d.get("exact") else "measured"
        note = (" — " + d["note"]) if d.get("note") else ""
        title = f"{name.capitalize()} = {val} {unit}".strip()
        body = f"The {name} is {val} {unit} ({exact}){note}. Verified physical constant."
        out.append(_card("card_ref_pc_" + key, title, body, "physics", "physical_constants",
                         ["reference", "physics", "constant", name]))
    return out


def _crops():
    """Each crop, with the soil-pH range and botanical family the agriculture verifier holds.
    Source: Cooperative Extension soil-pH crop guides + basic taxonomy (public domain)."""
    from concordance.verifiers import agriculture as ag
    ph, fam = ag._CROP_PH, ag._CROP_FAMILY
    names = sorted(set(ph) | set(fam))
    out = []
    for crop in names:
        disp = crop.replace("_", " ")
        facts = []
        if crop in ph:
            lo, hi = ph[crop]
            facts.append(f"prefers soil pH {lo}–{hi}")
        if crop in fam:
            facts.append(f"botanical family {fam[crop]} (rotate so it does not follow the same family)")
        if not facts:
            continue
        body = f"{disp.capitalize()}: " + "; ".join(facts) + ". Verified agronomy reference."
        out.append(_card(f"card_ref_crop_{crop}", f"{disp.capitalize()} — growing reference",
                         body, "agriculture", "agriculture",
                         ["reference", "agriculture", "crop", disp] +
                         ([fam[crop]] if crop in fam else [])))
    return out


def _nutrients():
    """Each nutrient, with its Recommended Dietary Allowance across life stages.
    Source: the nutrition verifier's RDA table (USDA/NIH Dietary Reference Intakes)."""
    import re as _re
    from concordance.verifiers import nutrition as nu

    def _stage(s):                                  # "adult_female_19_50" -> "adult female 19–50"
        s = _re.sub(r"_(\d+)_(\d+)", r" \1–\2", s)
        s = _re.sub(r"_(\d+)plus", r" \1+", s)
        return s.replace("_", " ")

    out = []
    for key, stages in nu._RDA_TABLE.items():
        name = key.replace("_", " ")
        unit = {"vitamin_c": "mg/day", "vitamin_d": "IU/day",
                "iron": "mg/day", "calcium": "mg/day"}.get(key, "per day")
        parts = ", ".join(f"{_stage(stage)} {val} {unit}"
                          for stage, val in stages.items())
        body = (f"{name.capitalize()} — recommended dietary allowance by life stage: {parts}. "
                f"Verified nutrition reference.")
        out.append(_card(f"card_ref_rda_{key}", f"{name.capitalize()} — recommended daily allowance",
                         body, "nutrition", "nutrition",
                         ["reference", "nutrition", "RDA", name]))
    return out


EMITTERS = [("periodic table", _elements), ("physical constants", _constants),
            ("crops", _crops), ("nutrients", _nutrients)]


def main() -> int:
    check = "--check" in sys.argv
    cards, per = [], {}
    for label, fn in EMITTERS:
        try:
            got = fn()
        except Exception as e:  # noqa: BLE001
            print(f"  {label}: FAILED — {e}")
            got = []
        per[label] = len(got)
        cards.extend(got)
    # dedup by id (deterministic), stable order
    seen, uniq = set(), []
    for c in sorted(cards, key=lambda x: x["id"]):
        if c["id"] not in seen:
            seen.add(c["id"])
            uniq.append(c)
    print("  emitters: " + " · ".join(f"{k} {v}" for k, v in per.items()))
    print(f"  total reference cards: {len(uniq)}")
    if check:
        print("  --check: nothing written")
        return 0
    p = _out_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for c in uniq:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    os.replace(tmp, p)                              # atomic
    print(f"  written: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
