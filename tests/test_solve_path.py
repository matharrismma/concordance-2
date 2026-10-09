"""THE SOLVE PATH on the one map (Matt, 2026-10-09: "put both doors on the map solve path"). The set path as a floor:
two jaws (exclude from outside, converge from inside) meeting at the answer, with the two doors - get-close and
change-of-domain - as the converge side's steps. Pinned on the seeds alone: the floor's two roots are exclude and
converge; the chain holds all six steps; the jaws meet at the answer (the confluence); the two doors point at their
instruments; exclude points at the barriers; the seed merges idempotently."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="nh-solve-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import card_millennium_sources as M  # noqa: E402
import seed_chains as S3  # noqa: E402
import seed_charts as SC  # noqa: E402
import seed_instruments as SI  # noqa: E402
import seed_millennium_chain as S2  # noqa: E402
import seed_solve_path as SPATH  # noqa: E402
import seed_standard_model_chain as S1  # noqa: E402
from concordance import chains, corpus  # noqa: E402

ALL = (S1, S2, S3, SC, SI, SPATH)


def _graph():
    cards = {}
    for s in ALL:
        for c in s.CARDS:
            cards[c["id"]] = json.loads(json.dumps(c))
    for c in M.cards() + [M.spine_card(1)]:
        cards[c["id"]] = json.loads(json.dumps(c))
    for cid in ("card_builder_james_clerk_maxwell", "card_k_floor_of_discovery", "card_spine_builders"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    ov = Path(TMP) / "o.jsonl"
    edges = []
    for s in ALL:
        edges += getattr(s, "BRIDGES", [])
    ov.write_text("\n".join(json.dumps(e) for e in edges) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, ov)
    return cards


def test_the_seed_validates_and_is_on_the_floors_registry():
    assert SPATH._validate() == []
    assert "card_floor_the_solve_path" in chains.FLOORS


def test_the_two_jaws_meet_at_the_answer():
    g = _graph()
    m = chains.floor_map("card_floor_the_solve_path", get_card=g.get)
    assert {p["id"] for p in m["parts"]} == {"card_solve_exclude", "card_solve_converge"}
    nodes = {n["id"] for n in m["chain"]["nodes"]}
    assert nodes >= {"card_solve_get_close", "card_solve_change_domain", "card_solve_refine", "card_solve_answer"}
    conf = {(c["a"], c["b"]): c["at"] for c in m["confluences"]}
    meet = conf.get(("card_solve_exclude", "card_solve_converge")) or conf.get(("card_solve_converge", "card_solve_exclude"))
    assert meet == "card_solve_answer"                       # the jaws close on the answer


def test_both_doors_are_on_the_path_and_point_at_their_instruments():
    g = _graph()
    m = chains.floor_map("card_floor_the_solve_path", get_card=g.get)
    serves = {s["from"]: s["at"] for s in m["serves"]}
    assert serves.get("card_solve_get_close") == "card_instr_approximation"
    assert serves.get("card_solve_change_domain") == "card_instr_spectral"
    assert serves.get("card_solve_exclude") == "card_floor_p_vs_np"
    # the door steps carry their stick in source.ref so the map can open the live stick
    gc = next(c for c in SPATH.CARDS if c["id"] == "card_solve_get_close")
    cd = next(c for c in SPATH.CARDS if c["id"] == "card_solve_change_domain")
    assert gc["source"]["ref"] == "stick_get_fairly_close_with_a_proven_bound"
    assert cd["source"]["ref"] == "stick_change_of_domain_solve_in_the_eigenbasis_map_back"


def test_it_merges_idempotently(monkeypatch):
    d = Path(tempfile.mkdtemp(prefix="nh-solve-seed-"))
    for s in ALL:
        monkeypatch.setattr(s, "DATA", d)
    monkeypatch.setattr(sys, "argv", ["seed"])
    for s in ALL:
        assert s.main() == 0
    ids = [json.loads(l)["id"] for l in (d / "chain_cards.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(ids) == len(set(ids)) and "card_floor_the_solve_path" in ids
    before = (d / "chain_cards.jsonl").read_bytes()
    assert SPATH.main() == 0 and (d / "chain_cards.jsonl").read_bytes() == before
