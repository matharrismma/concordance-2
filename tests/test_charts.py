"""THE FUNCTION FOLLOWS THE FORM (Matt, 2026-10-09: "allow the function to follow the form" - "Yes. Go through each
one"). The engine's tick sticks placed ON the one map: a chart card per stick, a cited `charts` edge to the node, and
floor_map collecting each node's charts. Pinned on the seeds alone (no corpus build): every chart lands on a node the
map actually holds, carries a real stick id and a basis, hangs off the charts spine; the Riemann question is charted
by its four sticks, the logarithm floor by e and entropy, and the Weil/L-function joints by the finite-field RH and
Langlands; the chart cards are pointers (a stick in source.ref), never generated."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="nh-chart-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import card_millennium_sources as M  # noqa: E402
import seed_chains as S3  # noqa: E402
import seed_charts as SC  # noqa: E402
import seed_millennium_chain as S2  # noqa: E402
import seed_standard_model_chain as S1  # noqa: E402
from concordance import chains, corpus  # noqa: E402


def _graph():
    cards = {c["id"]: json.loads(json.dumps(c))
             for c in S1.CARDS + S2.CARDS + S3.CARDS + SC.CARDS + M.cards() + [M.spine_card(1)]}
    for cid in ("card_builder_james_clerk_maxwell", "card_k_floor_of_discovery", "card_spine_builders"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(TMP) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S1.BRIDGES + S2.BRIDGES + S3.BRIDGES + SC.BRIDGES) + "\n",
                       encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    return cards


def test_the_seed_validates_and_every_chart_lands_on_a_real_node():
    assert SC._validate() == []
    assert len(SC.CHARTS) == 14
    nodes = SC.known_nodes()
    for c in SC.CHARTS:
        assert c["node"] in nodes, c["key"]
        assert c["stick"].startswith("stick_") and len(c["basis"]) >= 20
    cc = SC.chart_card(SC.CHARTS[0])
    assert cc["generated"] is False and cc["box"] == "chart"
    assert (cc["source"]["ref"] == SC.CHARTS[0]["stick"])        # a pointer to the stick, not a copy
    assert SC.spine_card()["connections"][0] == {"to_card_id": SC.FLOOR, "relationship": "part_of",
                                                 "evidence": SC.spine_card()["connections"][0]["evidence"]}


def test_floor_map_collects_the_charts_on_a_floor_and_its_nodes():
    g = _graph()
    log = chains.floor_map("card_floor_logarithm", get_card=g.get)
    sticks = {c["stick"] for c in log["charts"]}
    assert "stick_e_the_number_of_continuous_growth" in sticks
    assert "stick_entropy_is_never_decreased_only_concentrated_maxwell_s_demon" in sticks
    for c in log["charts"]:
        assert c["evidence"] and c["of"] and c["id"].startswith("card_chart_")


def test_the_riemann_question_is_charted_by_its_four_sticks():
    g = _graph()
    # the question is an end of both the Riemann chain floor and the Millennium floor
    for floor in ("card_floor_riemann", "card_floor_millennium"):
        m = chains.floor_map(floor, get_card=g.get)
        sticks = {c["stick"] for c in m["charts"]}
        assert "stick_the_zeta_function" in sticks, floor
        assert "stick_the_de_bruijn_newman_constant" in sticks, floor
        assert "stick_a_torus_and_the_waveforms_inside_the_prime_numbers_the_zeros" in sticks, floor


def test_the_joints_are_charted_by_the_matching_sticks():
    g = _graph()
    m = chains.floor_map("card_floor_millennium", get_card=g.get)
    at = {c["stick"]: c["of"] for c in m["charts"]}
    assert at.get("stick_finite_field_the_weil_riemann_hypothesis") == "card_joint_weil_conjectures"
    assert at.get("stick_the_langlands_program") == "card_joint_l_functions"


def test_the_standard_model_floor_is_charted_by_its_stick_and_alpha():
    g = _graph()
    m = chains.floor_map("card_floor_standard_model", get_card=g.get)
    sticks = {c["stick"] for c in m["charts"]}
    assert "stick_the_standard_model_chain_where_two_trees_connect" in sticks
    assert "stick_the_fine_structure_constant" in sticks
    # the floor still reads its lineage - the charts do not disturb the chain
    assert [j["at"] for j in m["joints"]] == ["card_builder_steven_weinberg"]


def test_every_chart_card_id_is_unique_and_merges_idempotently(monkeypatch):
    d = Path(tempfile.mkdtemp(prefix="nh-chart-seed-"))
    for s in (S1, S2, S3, SC):
        monkeypatch.setattr(s, "DATA", d)
    monkeypatch.setattr(sys, "argv", ["seed"])
    assert S1.main() == 0 and S2.main() == 0 and S3.main() == 0 and SC.main() == 0
    ids = [json.loads(l)["id"] for l in (d / "chain_cards.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(ids) == len(set(ids))
    assert sum(1 for i in ids if i.startswith("card_chart_")) == 14
    before = (d / "chain_cards.jsonl").read_bytes()
    assert SC.main() == 0 and (d / "chain_cards.jsonl").read_bytes() == before
