"""Shared helper for the compact down-the-list floor seeds (Matt, 2026-10-10). Not a stick; a builder.
A seed calls build(...) with its floor id, stick ref, and pillars [(key,title,body,[(target,ev)...])]."""
from __future__ import annotations
import json, os, sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
GLOBAL_FLOOR = "card_k_floor_of_discovery"


def _card(box, cid, kind, title, body, bands, ref=""):
    src = {"label": f"Narrow Highway — {box}", "url": "", "authority_tier": "engine_derived"}
    if ref:
        src["ref"] = ref
    return {"id": cid, "kind": kind, "title": title, "body": body, "source": src, "shelf": "codex", "box": box,
            "bands": bands, "subject": title, "connections": [], "author": "engine", "created_at": 0.0,
            "updated_at": 0.0, "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
            "surface": "secular", "generated": False}


def make(box, floor, spine, stick, floor_title, floor_body, pillars, root_evidence, sibling_mods):
    """Return (CARDS, BRIDGES, known_nodes, validate, main) for a floor seed. pillars: list of
    dict(key,title,body,rests=[(target,ev)...])."""
    def pid(k): return f"card_{box}_{k}"
    fc = _card(box, floor, "note", floor_title, floor_body, ["floor", box, "one map"], ref=stick)
    sc = _card(box, spine, "reference", f"{floor_title.split(' — ')[0]} — a spine", "The pillars.", [box, "spine", "one map"])
    sc["shelf"] = "spine"; sc["box"] = "spine"
    sc["connections"] = [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of", "evidence": root_evidence}]
    CARDS = [fc, sc] + [_card(box, pid(p["key"]), "reference", p["title"], p["body"], [box, "pillar", p["key"], "one map"]) for p in pillars]
    BR = []
    for p in pillars:
        BR.append({"a": pid(p["key"]), "b": floor, "relationship": "part_of", "evidence": f"a pillar ({p['title'].split(' — ')[0]})"})
        for t, ev in p["rests"]:
            BR.append({"a": pid(p["key"]), "b": t, "relationship": "connects_at", "evidence": ev})
    BR.append({"a": floor, "b": GLOBAL_FLOOR, "relationship": "part_of", "evidence": root_evidence})

    def known_nodes():
        ids = {c["id"] for c in CARDS}
        try:
            sys.path.insert(0, str(ROOT / "tools"))
            for m in sibling_mods:
                mod = __import__(m)
                ids |= {c["id"] for c in mod.CARDS}
        except Exception as e:
            print("could not load siblings:", e)
        return ids

    def validate():
        errs = []; ids = known_nodes()
        for e in BR:
            if e["a"] not in ids: errs.append(f"edge source not carded: {e['a']}")
            if e["b"] not in ids and e["b"] != GLOBAL_FLOOR: errs.append(f"edge target unknown: {e['b']}")
        if len({c['id'] for c in CARDS}) != len(CARDS): errs.append("duplicate card ids")
        return errs

    def main():
        DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))
        check = "--check" in sys.argv[1:]
        errs = validate()
        for e in errs: print("  VALIDATION:", e)
        if check:
            print(f"[check] {len(CARDS)} cards, {len(BR)} edges; {'OK' if not errs else 'ERRORS'}")
            return 1 if errs else 0
        if errs: return 1
        from concordance.chains import merge_seed
        n = merge_seed(DATA, CARDS, BR)
        print(f"merged ({n['cards']} cards, {len(CARDS)} from this seed; {n['bridges']} edges, {len(BR)} from this seed)")
        return 0
    return CARDS, BR, known_nodes, validate, main
