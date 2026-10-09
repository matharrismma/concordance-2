"""THE OTHER JOINTS - every validator and verifier (Matt, 2026-10-09: "now look for the other joints. Every validator
and verifier."). The instruments on the one map, their joints FOUND from the real import graph. Pinned on the seeds
alone (no corpus build): the graph is extracted from the files and matches the known shape (physical_constants is a
floor, chemistry is a confluence); every edge lands on a carded instrument or a real map node; floor_map walks the
measure spine, surfaces the confluences as merges, and the service joints as serves; the leaves are counted, not
carded; the validators sit above; the seed merges idempotently."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="nh-instr-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import card_millennium_sources as M  # noqa: E402
import seed_chains as S3  # noqa: E402
import seed_charts as SC  # noqa: E402
import seed_instruments as SI  # noqa: E402
import seed_millennium_chain as S2  # noqa: E402
import seed_standard_model_chain as S1  # noqa: E402
from concordance import chains, corpus  # noqa: E402

ALL_SEEDS = (S1, S2, S3, SC, SI)


def _graph():
    cards = {}
    for s in ALL_SEEDS:
        for c in s.CARDS:
            cards[c["id"]] = json.loads(json.dumps(c))
    for c in M.cards() + [M.spine_card(1)]:
        cards[c["id"]] = json.loads(json.dumps(c))
    for cid in ("card_builder_james_clerk_maxwell", "card_k_floor_of_discovery", "card_spine_builders"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(TMP) / "overlay.jsonl"
    edges = []
    for s in ALL_SEEDS:
        edges += getattr(s, "BRIDGES", [])
    overlay.write_text("\n".join(json.dumps(e) for e in edges) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    return cards


def test_the_graph_is_extracted_from_the_code_and_has_the_known_shape():
    g = SI.GRAPH
    assert g.get("physical_constants") == ["si_units"]
    assert set(g.get("chemistry", [])) == {"alpha_scale", "molar_scale", "thermal_scale"}      # a confluence
    assert set(g.get("physics", [])) == {"grav_scale", "planck_scale", "rela_scale"}
    assert "scale_base" in g.get("alpha_scale", [])
    # the measure floor is depended on by several; the leaves are the majority
    deps = {d for ds in g.values() for d in ds}
    assert "physical_constants" in deps and "scale_base" in deps and "_boolean" in deps
    assert len(SI.LEAVES) >= 50 and "law" in SI.LEAVES and "medicine" in SI.LEAVES
    assert SI._validate() == []


def test_every_edge_lands_on_a_carded_instrument_or_a_real_map_node():
    ids = {c["id"] for c in SI.CARDS}
    mapids = SI.known_map_nodes() | {SI.GLOBAL_FLOOR}
    for e in SI.BRIDGES:
        assert e["a"] in ids, e["a"]
        assert e["b"] in ids or e["b"] in mapids, e["b"]


def test_floor_map_walks_the_spine_and_finds_the_confluences_as_merges():
    g = _graph()
    m = chains.floor_map("card_floor_the_instruments", get_card=g.get)
    assert m
    nodes = {n["id"] for n in m["chain"]["nodes"]}
    assert "card_instr_physical_constants" in nodes and "card_instr_chemistry" in nodes
    merged = {x["id"] for x in m["merges"]}
    assert "card_instr_chemistry" in merged and "card_instr_physics" in merged
    chem = next(x for x in m["merges"] if x["id"] == "card_instr_chemistry")
    assert len(chem["from"]) == 3            # alpha + molar + thermal


def test_the_service_joints_reach_the_one_map():
    g = _graph()
    m = chains.floor_map("card_floor_the_instruments", get_card=g.get)
    at = {s["from"]: s["at"] for s in m["serves"]}
    assert at.get("card_instr_number_theory") == "card_question_riemann"
    assert at.get("card_instr_elliptic_curves") == "card_question_bsd"
    assert at.get("card_instr_physical_constants") == "card_chart_fine_structure"


def test_the_validators_sit_above_the_verifiers():
    ids = {c["id"] for c in SI.CARDS}
    for v in ("derivation", "the_moat", "the_seal", "the_doorkeeper"):
        assert f"card_instr_{v}" in ids
    # the moat builds on the router; nothing in the verifier graph builds on the moat (it is the apex)
    builds = {(e["a"], e["b"]) for e in SI.BRIDGES if e["relationship"] == "builds_on"}
    assert ("card_instr_the_moat", "card_instr_derivation") in builds
    assert not any(a for (a, b) in builds if b == "card_instr_the_moat")


def test_the_seed_merges_idempotently(monkeypatch):
    d = Path(tempfile.mkdtemp(prefix="nh-instr-seed-"))
    for s in ALL_SEEDS:
        monkeypatch.setattr(s, "DATA", d)
    monkeypatch.setattr(sys, "argv", ["seed"])
    for s in ALL_SEEDS:
        assert s.main() == 0
    ids = [json.loads(l)["id"] for l in (d / "chain_cards.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(ids) == len(set(ids))
    assert sum(1 for i in ids if i.startswith("card_instr_")) == len(SI.JOINED) + len(SI.VALIDATORS)
    before = (d / "chain_cards.jsonl").read_bytes()
    assert SI.main() == 0 and (d / "chain_cards.jsonl").read_bytes() == before
