#!/usr/bin/env python3
"""Card Matt's authored deck — The Lighthouse Field Kit v1 — into the corpus as a real DECK.

Matt (2026-07-25): "I have some cards that can serve as part of the project… it would be cool to
build a card game into the project." The Field Kit is a hand-authored deck of 30 Scripture PROTOCOL
cards (FK1-00…29) — the Sermon on the Mount (0-12) and the Epistles (13-29) — each carrying an anchor
Scripture, a trading-card RARITY (legendary/epic/rare/common), and authored practice fields: source,
floor, spice, common_drift, practice_7day, prompt, axes, related_protocols, and poker-card art.

Conduit, not source: each card is Matt's own authored teaching, GATHERED and attributed (generated
=False). Nested under a fieldkit spine → the Word (the deck is Scripture practice, so it roots in the
Logos, not merely the Floor). Git-tracked (authored content belongs on github). Re-runnable:

    PYTHONPATH=src CONCORDANCE_FIELDKIT_SRC=<path to v1_cards.jsonl> python tools/card_fieldkit.py

The source path defaults to Matt's Lighthouse copy; override with the env var on any machine.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

WORD = "card_k_spine_the_word"           # the deck is Scripture practice → rooted in the Logos
SPINE = "card_spine_fieldkit"
_DEFAULT_SRC = "C:/Users/hdven/OneDrive/Documents/Claude/Projects/Lighthouse/data/fieldkit/v1_cards.jsonl"
_slug = re.compile(r"[^a-z0-9]+")


def _sk(*p):
    return _slug.sub("_", "-".join(str(x) for x in p).lower()).strip("_")


def _clean(s: str) -> str:
    """The source file is cp1252 — the en-dashes in refs (Matthew 5–7) arrive as U+FFFD when a caller
    read it as utf-8. Normalize any stray replacement char to an en-dash so refs read true."""
    return (str(s or "").replace("�", "–").replace("", "–")).strip()


def _load(path: Path):
    """Read the deck, decoding cp1252 (the file's real encoding) so the em/en dashes survive."""
    raw = path.read_bytes()
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    return [json.loads(ln) for ln in text.splitlines() if ln.strip()]


def _body(c: dict) -> str:
    ref = _clean(c.get("scripture"))
    label = _clean(c.get("scripture_label"))
    parts = [f"{_clean(c.get('title'))} — anchor: {ref}" + (f" ({label})" if label else "") + "."]
    if c.get("source"):
        parts.append(f"Source: {_clean(c['source'])}")
    if c.get("floor"):
        parts.append(f"Floor: {_clean(c['floor'])}")
    if c.get("spice"):
        parts.append(f"Spice: {_clean(c['spice'])}")
    if c.get("common_drift"):
        parts.append(f"Common drift: {_clean(c['common_drift'])}")
    if c.get("practice_7day"):
        parts.append(f"Practice (7 day): {_clean(c['practice_7day'])}")
    if c.get("prompt"):
        parts.append(f"Prompt: {_clean(c['prompt'])}")
    return "  ".join(parts)


def main() -> int:
    src = Path(os.environ.get("CONCORDANCE_FIELDKIT_SRC", "").strip() or _DEFAULT_SRC)
    if not src.exists():
        print(f"Field Kit source not found: {src}  (set CONCORDANCE_FIELDKIT_SRC)")
        return 1
    rows = _load(src)
    spine = {
        "id": SPINE, "kind": "reference",
        "title": "The Lighthouse Field Kit — a deck of Scripture protocol cards",
        "body": ("An authored deck: 30 protocol cards drawn from the Sermon on the Mount and the "
                 "Epistles. Each names an anchor Scripture, the floor that keeps it honest, the common "
                 "drift, and a seven-day practice. Hearing plus DOING builds on rock (Matthew 7:24). "
                 "The cards help obedience; they never define truth."),
        "source": {"label": "The Lighthouse Field Kit v1", "url": "", "domain": "", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine", "bands": ["fieldkit", "deck", "protocol", "practice", "spine"],
        "subject": "the field kit", "connections": [{"to_card_id": WORD, "relationship": "part_of",
                    "evidence": "a deck of Scripture practice, rooted in the Word"}],
        "author": "Matt Harris (Lighthouse Field Kit)", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
    }
    cards = [spine]
    for c in rows:
        fid = str(c.get("id") or f"FK1-{int(c.get('number', 0)):02d}")
        rarity = str(c.get("rarity") or "common")
        axes = [str(a) for a in (c.get("axes") or [])]
        cards.append({
            "id": f"card_fk_{_sk(fid)}", "kind": "reference",
            "title": _clean(c.get("title"))[:180], "body": _body(c),
            "source": {"label": "The Lighthouse Field Kit v1 (authored deck)", "url": "",
                       "domain": "fieldkit", "authority_tier": "reference"},
            "shelf": "fieldkit", "box": "protocol",
            "bands": ["fieldkit", "protocol", "practice", rarity] + axes,
            "subject": _clean(c.get("title")),
            "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                             "evidence": f"a Field Kit protocol card ({rarity})"}],
            "author": "Matt Harris (Lighthouse Field Kit)", "created_at": 0.0, "updated_at": 0.0,
            "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False,
            "extra": {"rarity": rarity, "number": c.get("number"),
                      "scripture": _clean(c.get("scripture")), "scripture_label": _clean(c.get("scripture_label")),
                      "axes": axes, "related_protocols": [str(p) for p in (c.get("related_protocols") or [])],
                      "practice_7day": _clean(c.get("practice_7day")), "prompt": _clean(c.get("prompt")),
                      "floor": _clean(c.get("floor")), "spice": _clean(c.get("spice")),
                      "common_drift": _clean(c.get("common_drift")), "source_line": _clean(c.get("source")),
                      "front_image": c.get("front_image"), "back_image": c.get("back_image"),
                      "fieldkit_id": fid},
        })
    out = Path("data") / "fieldkit_cards.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    from collections import Counter
    by = Counter(c["extra"]["rarity"] for c in cards[1:])
    print(f"carded {len(cards)-1} Field Kit cards (+1 spine) -> {out}  | rarity: {dict(by)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
