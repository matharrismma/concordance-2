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
