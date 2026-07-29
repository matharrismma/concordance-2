#!/usr/bin/env python3
"""The practical stores, carded — herbs, the almanac, the lessons. Pass 1 of the practical seam.

Seeding loop (Matt, 2026-07-29): alternate PRACTICAL and ACADEMIC seams. The commentaries were
the academic pass; this is the practical one, and it follows the same rule that made that pass
work — card the substance we ALREADY HOLD but nobody can find.

Three stores, none of which had a single card in the keeping:

  * data/herbs/monographs.jsonl  — 12 monographs, ~2,900 chars each: parts used, traditional
    uses, EVIDENCE VERDICTS, preparations, safety notes, growing. The apothecary shelf held 0.
  * data/almanac/resealed.jsonl  — 41 sealed entries: a situation, the wisdom, a verdict, and
    a re-checkable seal. The almanac shelf held 0.
  * data/curriculum/*.json       — the coach's lesson units (McGuffey, Aesop, Pilgrim's,
    founding documents, reading, Spanish), each with its rule, examples and checks.

THE MEDICINE FLOOR IS KEPT (project rule, not a preference): an herb card carries traditional
use as TRADITION and evidence verdicts as the source recorded them. Dosage lines are quoted as
preparation, never rendered as our prescription, and every card says plainly that it is not
medical advice. We carry the tradition honestly; we never upgrade it.

    PYTHONPATH=src python tools/card_practical_stores.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

FLOOR = "card_k_floor_of_discovery"
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
NOT_ADVICE = ("This is a record of what has been used and what has been checked — not medical "
              "advice, and not a prescription. Talk to someone qualified before you act on it.")


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")[:60]


def _card(cid, title, body, shelf, box, bands, spine, subject, evidence, surface="secular"):
    return {"id": cid, "kind": "reference", "title": title[:180], "body": body,
            "source": {"label": evidence, "url": "", "authority_tier": "reference"},
            "shelf": shelf, "box": box, "bands": bands, "subject": subject,
            "connections": [{"to_card_id": spine, "relationship": "member_of",
                             "evidence": f"a member of the {shelf} shelf"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": surface,
            "generated": False}


def _spine(cid, title, body, shelf_bands, subject):
    return {"id": cid, "kind": "reference", "title": title, "body": body,
            "source": {"label": "The keeping's own practical stores", "url": "",
                       "authority_tier": "reference"},
            "shelf": "spine", "box": "spine", "bands": shelf_bands, "subject": subject,
            "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                             "evidence": "a practical wing of the Floor of Discovery"}],
            "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
            "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular",
            "generated": False}


def herbs():
    p = DATA / "herbs" / "monographs.jsonl"
    if not p.exists():
        return []
    out, n = [], 0
    for ln in p.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        h = json.loads(ln)
        name = h.get("name") or h.get("id")
        parts = [f"{name} ({h.get('scientific_name','')})".strip()]
        if h.get("summary"):
            parts += ["", h["summary"]]
        for label, key in (("PARTS USED", "parts_used"), ("TRADITIONAL USE", "traditional_uses"),
                           ("PREPARATION (as recorded, not prescribed)", "preparations"),
                           ("SAFETY", "safety_notes"), ("GROWING", "growing")):
            vals = h.get(key) or []
            if isinstance(vals, str):
                vals = [vals]
            if vals:
                parts += ["", label] + [f"  · {v}" for v in vals]
        ev = h.get("evidence_verdicts") or []
        if ev:
            parts += ["", "WHAT HAS BEEN CHECKED"]
            for e in ev:
                parts.append(f"  · {e.get('claim','')} — {e.get('verdict','')}"
                             + (f" ({e.get('note','')})" if e.get("note") else ""))
        parts += ["", NOT_ADVICE]
        out.append(_card(f"card_herb_{_slug(h.get('id') or name)}", f"{name} — the apothecary",
                         "\n".join(parts), "apothecary", "monograph",
                         ["apothecary", "herb", _slug(name), "traditional", "safety"],
                         "card_spine_apothecary", name,
                         "Apothecary monograph — tradition recorded, evidence marked as found"))
        n += 1
    if n:
        out.append(_spine("card_spine_apothecary", "The Apothecary",
                          f"{n} plant monographs: what the plant is, what it has traditionally "
                          f"been used for, what has actually been checked, how it is prepared, "
                          f"what it can do to you, and how to grow it. Tradition is carried as "
                          f"tradition; a checked claim carries its verdict. {NOT_ADVICE}",
                          ["apothecary", "herbs", "practical", "spine"], "The Apothecary"))
    return out


def almanac():
    p = DATA / "almanac" / "resealed.jsonl"
    if not p.exists():
        return []
    out, n = [], 0
    for ln in p.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        a = json.loads(ln)
        title = a.get("title") or a.get("id")
        body = [f"SITUATION\n  {a.get('situation','')}".rstrip(),
                f"\nWHAT HOLDS\n  {a.get('wisdom','')}".rstrip()]
        if a.get("orig_verdict"):
            body.append(f"\nVERDICT\n  {a['orig_verdict']}")
        seal = (a.get("seal") or {})
        if isinstance(seal, dict) and seal.get("cite_url"):
            body.append(f"\nRE-CHECKABLE SEAL\n  {seal['cite_url']}")
        body.append("\nVerified before it was kept — the almanac holds nothing it could not check.")
        out.append(_card(f"card_alm_{_slug(a.get('id') or title)}", f"Almanac: {title}",
                         "\n".join(body), "almanac", a.get("category") or "entry",
                         ["almanac", "practical", _slug(a.get("category") or "entry")],
                         "card_spine_almanac", title,
                         "The Almanac — verified-only practical wisdom (sealed)"))
        n += 1
    if n:
        out.append(_spine("card_spine_almanac", "The Almanac",
                          f"{n} entries of practical wisdom that PASSED a check before being "
                          f"kept. Each names the situation, what holds, and the seal you can "
                          f"re-fetch. Where a saying could not be verified, it is not here — "
                          f"the almanac's whole discipline is that absence.",
                          ["almanac", "practical", "verified", "spine"], "The Almanac"))
    return out


def lessons():
    root = DATA / "curriculum"
    if not root.exists():
        return []
    out, n, skipped = [], 0, []
    for f in sorted(root.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        units = data if isinstance(data, list) else data.get("units") or []
        track = f.stem
        for u in units:
            if not isinstance(u, dict):
                continue
            title = u.get("title") or u.get("id")
            body = []
            for label, key in (("RULE", "rule"), ("EXAMPLES", "examples"),
                               ("PRACTISE", "decodable_sentence"), ("CHECK", "checks"),
                               ("TEXT", "text"), ("NOTE", "note")):
                v = u.get(key)
                if isinstance(v, list):
                    v = "\n".join(f"  · {x}" for x in v)
                elif v:
                    v = f"  {v}"
                if v:
                    body.append(f"{label}\n{v}")
            if not body:
                continue
            joined = "\n\n".join(body)
            if len(joined) < 120:
                # A unit whose whole content is a word list is a pointer, not a lesson. This
                # seam exists to add SUBSTANCE, so it is skipped — and counted, never silently
                # dropped (no silent caps).
                skipped.append(u.get("id") or title)
                continue
            out.append(_card(f"card_lesson_{_slug(track)}_{_slug(u.get('id') or title)}",
                             f"Lesson: {title}", "\n\n".join(body), "curriculum", track,
                             ["curriculum", "lesson", track, "coach"],
                             "card_spine_curriculum", str(title),
                             "The coach's own curriculum — authored units, verbatim"))
            n += 1
    if skipped:
        print(f"  curriculum: {len(skipped)} unit(s) too thin to be substance, skipped: "
              + ", ".join(str(x) for x in skipped[:5]))
    if n:
        out.append(_spine("card_spine_curriculum", "The Curriculum",
                          f"{n} lesson units the coach teaches from — the rule, the examples, "
                          f"the sentence to practise, the check. Carried as cards so a parent "
                          f"can find the lesson without walking the tutor.",
                          ["curriculum", "coach", "lessons", "practical", "spine"],
                          "The Curriculum"))
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    cards = herbs() + almanac() + lessons()
    if not cards:
        print("no practical stores found on this machine")
        return 0
    from collections import Counter
    by = Counter(c["shelf"] for c in cards)
    bodies = [len(c["body"]) for c in cards]
    print(f"practical cards: {len(cards)}  {dict(by)}")
    print(f"average body: {sum(bodies)//len(bodies):,} chars")
    thin = [c["id"] for c in cards if len(c["body"]) < 120]
    print(f"stubs (must be 0): {len(thin)}" + (f" {thin[:3]}" if thin else ""))
    if dry:
        print("--dry-run: nothing written.")
        return 0
    out = DATA / "practical_cards.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
