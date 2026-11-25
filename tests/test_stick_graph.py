"""WHERE THE STICKS POINT (2026-11-25): the stick names a stick's statement, references and marks carry, read as
edges - resolved on this node ("found"), through the dead-link table ("crossing", the old name kept visible), or left
dead (a want). Drawn on site/map.html from GET /sticks/graph."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from concordance import stick_graph as G, tickstick as TS
from concordance.engine import EngineConfig
from concordance.web import api


def _keeping():
    keep = Path(tempfile.mkdtemp(prefix="nh-stick-graph-"))
    a = TS.create("The zeta function", "the function", data_dir=keep)["id"]
    b = TS.create("The Hilbert-Polya conjecture", "an operator", data_dir=keep)["id"]
    c = TS.create("A stick that names nobody", "alone", data_dir=keep)["id"]
    d = TS.create("The symmetry", "names others", ["stick_the_zeta_function"], data_dir=keep)["id"]
    TS.tick(a, "note", "the classical zeta has no known operator - stick_hilbert_polya (an old name)", data_dir=keep)
    TS.tick(a, "note", "ties stick_the_hilbert_polya_conjecture and stick_no_such_stick_anywhere", data_dir=keep)
    TS.tick(d, "note", "the symmetry, again: stick_the_zeta_function", data_dir=keep)
    return keep, a, b, c, d


def test_names_become_edges_found_through_an_alias_or_dead():
    keep, a, b, c, d = _keeping()
    g = G.graph(keep)
    edges = {(l["source"], l["target"], l["kind"]) for l in g["links"]}
    assert (a, b, "crossing") in edges or (a, b, "found") in edges      # the old name and the real one: ONE edge
    assert sum(1 for l in g["links"] if (l["source"], l["target"]) == (a, b)) == 1
    assert (d, a, "found") in edges                                       # named twice, drawn once
    assert {n["id"] for n in g["nodes"]} == {a, b, d}                     # the lone stick is counted, not drawn
    assert g["counts"]["unlinked"] == 1 and g["counts"]["sticks"] == 4
    assert g["dead"] == [{"id": "stick_no_such_stick_anywhere", "named_by": [a]}]


def test_an_alias_only_link_is_marked_as_one():
    keep = Path(tempfile.mkdtemp(prefix="nh-stick-graph-"))
    a = TS.create("The zeta function", data_dir=keep)["id"]
    TS.create("The Hilbert-Polya conjecture", data_dir=keep)
    TS.tick(a, "note", "no known operator - stick_hilbert_polya", data_dir=keep)
    (link,) = G.graph(keep)["links"]
    assert link["kind"] == "crossing" and link["via"] == "stick_hilbert_polya"
    assert link["target"] == "stick_the_hilbert_polya_conjecture"


def test_get_sticks_graph_serves_it(monkeypatch):
    keep, a, b, c, d = _keeping()
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(keep))
    st, body = api.dispatch("GET", "/sticks/graph", {}, None, EngineConfig())[:2]
    assert st == 200 and body["counts"]["linked"] == 3 and body["nodes"] and body["links"]


def test_the_map_draws_it():
    html = (Path(__file__).resolve().parent.parent / "site" / "map.html").read_text(encoding="utf-8")
    assert 'id="stickCanvas"' in html and '"/sticks/graph"' in html and "NHGraph.View" in html


def _chain_keeping():
    """A keeping with a small chain map: a floor, a joint two questions meet at, a chart of one question, and a stick
    that only names its floor."""
    import json
    keep = Path(tempfile.mkdtemp(prefix="nh-stick-graph-chain-"))
    s1 = TS.create("First question", data_dir=keep)["id"]
    s2 = TS.create("Second question", data_dir=keep)["id"]
    s3 = TS.create("A chart of the first", data_dir=keep)["id"]
    s4 = TS.create("A stick under the floor only", data_dir=keep)["id"]
    s5 = TS.create("A third question at the same joint", data_dir=keep)["id"]
    TS.tick(s4, "note", "this sits on card_floor_x and names nothing else", data_dir=keep)
    cards = [
        {"id": "card_floor_x", "title": "Floor X", "connections": []},
        {"id": "card_joint_j", "title": "Joint J", "connections": []},
        {"id": "card_question_one", "title": "Q1", "source": {"ref": s1}, "connections": []},
        {"id": "card_question_two", "title": "Q2", "source": {"ref": s2}, "connections": []},
        {"id": "card_question_three", "title": "Q3", "source": {"ref": s5}, "connections": []},
        {"id": "card_chart_one", "title": "chart", "source": {"ref": s3}, "connections": []},
    ]
    bridges = [
        {"a": "card_floor_x", "b": "card_k_floor_of_discovery", "relationship": "part_of"},
        {"a": "card_joint_j", "b": "card_floor_x", "relationship": "part_of"},
        {"a": "card_question_one", "b": "card_floor_x", "relationship": "open_end_of"},
        {"a": "card_question_two", "b": "card_floor_x", "relationship": "open_end_of"},
        {"a": "card_question_three", "b": "card_floor_x", "relationship": "open_end_of"},
        {"a": "card_question_one", "b": "card_joint_j", "relationship": "connects_at"},
        {"a": "card_question_two", "b": "card_joint_j", "relationship": "connects_at"},
        {"a": "card_question_three", "b": "card_joint_j", "relationship": "connects_at"},
        {"a": "card_chart_one", "b": "card_question_one", "relationship": "charts"},
    ]
    (keep / "chain_cards.jsonl").write_text("\n".join(json.dumps(c) for c in cards) + "\n", encoding="utf-8")
    (keep / "chain_bridges.jsonl").write_text("\n".join(json.dumps(b) for b in bridges) + "\n", encoding="utf-8")
    return keep, s1, s2, s3, s4, s5


def test_the_chain_map_gives_floors_joints_and_charts_never_a_clique():
    keep, s1, s2, s3, s4, s5 = _chain_keeping()
    g = G.graph(keep)
    e = {(l["source"], l["target"]): l["kind"] for l in g["links"]}
    for s in (s1, s2, s5):                                       # three questions at one joint: three lines to it
        assert e.get((s, "card_joint_j")) == "joint" or e.get(("card_joint_j", s)) == "joint", s
        assert e.get((s, "card_floor_x")) == "nested"
    pairs = {frozenset((l["source"], l["target"])) for l in g["links"]}
    assert frozenset((s1, s2)) not in pairs and frozenset((s2, s5)) not in pairs   # a shared joint is not a found link
    assert frozenset((s3, s1)) in pairs                          # the chart charts the first question's card
    assert e.get((s4, "card_floor_x")) == "nested"               # a stick that names its floor sits under it
    assert e.get(("card_floor_x", "card_k_floor_of_discovery")) == "nested"
    kinds = {n["id"]: n["kind"] for n in g["nodes"]}
    assert kinds["card_floor_x"] == "floor" and kinds["card_joint_j"] == "joint" and kinds["card_k_floor_of_discovery"] == "root"
    assert g["counts"]["components"] == 1 and g["alone"] == [] and g["counts"]["linked"] == 5


def test_an_id_that_really_ends_in_an_underscore_is_read_whole():
    keep = Path(tempfile.mkdtemp(prefix="nh-stick-graph-us-"))
    long_q = "Every matrix is a rotation and a stretch - the singular value decomposition of every linear map"
    a = TS.create(long_q, data_dir=keep)["id"]
    assert a.endswith("_")                                       # the slug really is cut on a word boundary
    b = TS.create("The Jacobian conjecture", data_dir=keep)["id"]
    TS.tick(b, "note", f"near a point F is its Jacobian matrix, a rotation and a stretch ({a})", data_dir=keep)
    g = G.graph(keep)
    assert {(l["source"], l["target"]) for l in g["links"]} in ({(a, b)}, {(b, a)}) and g["dead"] == []
