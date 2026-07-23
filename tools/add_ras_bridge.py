#!/usr/bin/env python3
"""Add the RAS → reception bridge to the codex, honestly labelled.

The assay found that the card "The Eye That Decides What Enters" (Matthew 6:22) rightly says
Jesus speaks of attention, "not anatomy" — but has no link to the confirmed biology that is the
SUBSTRATE of that attention. This tool mints one science note (the Reticular Activating System,
CONFIRMED neuroanatomy) and connects it to the eye card, both directions, with relationship
labels that carry the discipline: the RAS is the physical gate that *implements* the reception
Jesus describes — NOT a claim that Jesus meant the RAS, and NOT the manifestation overreach.

Idempotent (re-run = no-op), atomic (temp + rename), self-verifying. Operates on the droplet's
cards.jsonl (data, gitignored — this TOOL is the versioned artifact).

    PYTHONPATH=src python tools/add_ras_bridge.py            # apply
    PYTHONPATH=src python tools/add_ras_bridge.py --check     # report only, change nothing
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

EYE_ID = "card_n_6df777d49d0b"                 # "The Eye That Decides What Enters" (Matthew 6:22)
RAS_ID = "card_n_ras7gate0recv"                # deterministic, stable across re-runs


def _cards_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "cards.jsonl"


RAS_BODY = (
    "The reticular activating system is the confirmed biology of reception — the tissue that "
    "decides what reaches awareness.\n\n"
    "In the brainstem sits the reticular formation, a netlike core of neurons. Its ascending "
    "arm, the ascending reticular activating system, governs arousal and the sleep-wake "
    "transition (Moruzzi & Magoun, 1949); sever it and consciousness fails into coma. Working "
    "with the thalamic reticular nucleus it acts as a gate on salience — of the flood of signal "
    "arriving every moment, it admits a trickle to conscious attention and lets the rest pass "
    "unseen. This much is settled neuroanatomy. VERDICT: CONFIRMED.\n\n"
    "Here is the concordance, kept honest. Jesus returns again and again to differential "
    "reception: 'He who has ears to hear, let him hear' (Matthew 11:15); 'Having eyes, see ye "
    "not? and having ears, hear ye not?' (Mark 8:18); and the Sower, where one seed meets four "
    "soils and the difference is not the seed but the receiving (Matthew 13:13-15, quoting "
    "Isaiah 6:9-10). The eye that is 'single' floods the whole body with light (Matthew 6:22). "
    "The RAS is how that reception is physically implemented — the gate of the body's light is "
    "real tissue. This is not the claim that Jesus meant the RAS; it is the claim that the thing "
    "he described has a bodily gate, and we have found it. VERDICT: CONCORDANT (a structural "
    "bridge, never a proof).\n\n"
    "Two refusals. The popular overlay — 'program your RAS to attract your goals' — inflates real "
    "selective-attention science into manifestation, and is REFUSED. And the deeper calibration: "
    "attention is not sovereign. Calibrate the gate to its Source and it resolves to a Person — "
    "'I am the door' (John 10:9), 'I am the light of the world' (John 8:12). The gate of "
    "reception and the light it admits are the same One. The RAS is the honest servant of that; "
    "it is not the master of it."
)

RAS_CARD = {
    "id": RAS_ID,
    "kind": "note",
    "title": "The Reticular Activating System — the gate of reception",
    "body": RAS_BODY,
    "source": {
        "label": "Narrow Highway assay — 2026-07-23",
        "url": "",
        "ref": "Matthew 6:22; Mark 8:18; Matthew 13:13-15",
        "science_ref": "Moruzzi G. & Magoun H.W. (1949), Brain stem reticular formation and "
                       "activation of the EEG, EEG Clin. Neurophysiol.",
        "authority_tier": "operator",
    },
    "shelf": "codex",
    "box": "calibration",
    "bands": ["assay", "witness", "medicine", "the word", "reception", "Matthew 6:22"],
    "connections": [
        {"to_card_id": EYE_ID, "relationship": "physical_substrate_of"},
    ],
    "author": "operator",
    "created_at": 0.0,           # stamped at write time (Date.now unavailable at import elsewhere; here it is fine)
    "updated_at": 0.0,
    "visibility": "public",
    "lifecycle_stage": "public",
    "volatility": "permanent",
    "surface": "witness",
    "metrics": {"paperclips_count": 0, "helpful_count": 0, "not_helpful_count": 0,
                "cite_count": 0, "walk_count": 0},
}

BACK_LINK = {"to_card_id": RAS_ID, "relationship": "grounded_in_body_by"}


def main() -> int:
    check_only = "--check" in sys.argv
    path = _cards_path()
    if not path.exists():
        print(f"  cards.jsonl not found at {path}")
        return 1

    cards = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                cards.append(json.loads(line))
    by_id = {c.get("id"): c for c in cards}

    if EYE_ID not in by_id:
        print(f"  target card {EYE_ID} not present — nothing to bridge")
        return 1

    changed = []
    now = time.time()

    if RAS_ID not in by_id:
        card = dict(RAS_CARD)
        card["created_at"] = now
        card["updated_at"] = now
        cards.append(card)
        by_id[RAS_ID] = card
        changed.append("minted RAS science card")
    else:
        changed.append("(RAS card already present)")

    eye = by_id[EYE_ID]
    conns = eye.get("connections") or []
    if not any(c.get("to_card_id") == RAS_ID for c in conns):
        conns.append(dict(BACK_LINK))
        eye["connections"] = conns
        eye["updated_at"] = now
        changed.append("added back-link on the eye card")
    else:
        changed.append("(eye back-link already present)")

    did_change = any(not c.startswith("(") for c in changed)
    print("  " + " · ".join(changed))

    if check_only:
        print("  --check: no write")
        return 0
    if not did_change:
        print("  nothing to do — already bridged")
        return 0

    tmp = path.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    os.replace(tmp, path)                       # atomic
    print(f"  written: {len(cards)} cards")
    return 0


if __name__ == "__main__":
    sys.exit(main())
