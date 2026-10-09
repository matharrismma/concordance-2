"""THE ONE MAP (Matt, 2026-10-09: "Put them on one map, but make it the one map for the project. We want to map
reality as we know it and these fall on that."). The seven Millennium questions and their joints are nodes and edges
of the keeping's connection graph - the same two files, the same floor logic, the same /chains door and map page as
the Standard-Model chain. Pinned here on the seeds alone (no corpus build): the floor reads seven open ends and ten
joints; each pair of questions meets at the hub the literature names, or is recorded as a miss with the indirect path
shown; the Standard-Model floor still meets at Weinberg; the seeder MERGES into the shared files without losing the
other seed; the /chains door lists the floors and 404s an unknown one."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="nh-map-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import card_millennium_sources as M  # noqa: E402
import seed_millennium_chain as S2  # noqa: E402
import seed_standard_model_chain as S1  # noqa: E402
from concordance import chains, corpus  # noqa: E402


def _graph():
    """Both seeds + the source cards, folded through the real corpus._apply_bridges (no corpus build)."""
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S1.CARDS + S2.CARDS + M.cards() + [M.spine_card(1)]}
    for cid in ("card_builder_james_clerk_maxwell", "card_k_floor_of_discovery", "card_spine_builders"):
        cards.setdefault(cid, {"id": cid, "connections": []})
    overlay = Path(TMP) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S1.BRIDGES + S2.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    return cards


def test_the_millennium_floor_reads_seven_ends_and_its_joints():
    g = _graph()
    m = chains.floor_map(S2.FLOOR, get_card=g.get)
    assert m and m["floor"] == S2.FLOOR
    assert len(m["ends"]) == 7 and all(e["stick"].startswith("stick_") for e in m["ends"])
    assert len(m["parts"]) == len(S2.JOINTS) == 10
    at = {(j["a"], j["b"]): j["at"] for j in m["joints"]}
    q = S2._q
    assert at[(q("riemann"), q("yang_mills"))] == S2._j("gue_statistics")
    assert at[(q("riemann"), q("bsd"))] == S2._j("l_functions")
    assert at[(q("bsd"), q("hodge"))] == S2._j("tate_conjecture")
    assert at[(q("hodge"), q("poincare"))] == S2._j("bochner_vanishing")
    assert at[(q("navier_stokes"), q("yang_mills"))] == S2._j("renormalization_group")
    assert at[(q("yang_mills"), q("p_vs_np"))] == S2._j("sign_problem")
    assert at[(q("bsd"), q("p_vs_np"))] == S2._j("manin_algorithm")
    assert at[(q("riemann"), q("p_vs_np"))] in (S2._j("diophantine_rh"), S2._j("weil_conjectures"))
    assert at[(q("navier_stokes"), q("poincare"))] == S2._j("arnold_geodesics")
    # the Weil hub joins three
    weil = [j for j in m["joints"] if j["at"] == S2._j("weil_conjectures")]
    assert {frozenset((j["a"], j["b"])) for j in weil} >= {frozenset((q("riemann"), q("hodge"))), frozenset((q("hodge"), q("p_vs_np")))}
    # every joint carries the edges' own evidence, and names a citation
    for j in m["joints"]:
        assert len(j["evidence"]) == 2 and j["evidence"][0]


def test_a_miss_stays_a_miss_and_the_indirect_path_is_shown():
    g = _graph()
    m = chains.floor_map(S2.FLOOR, get_card=g.get)
    q = S2._q
    miss = [x for x in m["misses"] if {x["a"], x["b"]} == {q("riemann"), q("navier_stokes")}]
    assert len(miss) == 1 and miss[0]["at"] is None
    assert miss[0]["via"] and miss[0]["via"] != S2.FLOOR      # connected only through another node, never the floor


def test_the_standard_model_floor_still_meets_at_weinberg():
    g = _graph()
    m = chains.floor_map(S1.FLOOR, get_card=g.get)
    assert {p["id"] for p in m["parts"]} == {"card_builder_james_clerk_maxwell", "card_builder_enrico_fermi"}
    assert m["ends"] == []
    assert [j["at"] for j in m["joints"]] == ["card_builder_steven_weinberg"]


def test_the_seeder_merges_into_the_shared_files_and_is_idempotent(monkeypatch):
    d = Path(tempfile.mkdtemp(prefix="nh-seed-"))
    monkeypatch.setattr(S1, "DATA", d)
    monkeypatch.setattr(S2, "DATA", d)
    monkeypatch.setattr(sys, "argv", ["seed"])
    assert S1.main() == 0
    n1 = len((d / "chain_cards.jsonl").read_text(encoding="utf-8").splitlines())
    assert S2.main() == 0
    cards = (d / "chain_cards.jsonl").read_text(encoding="utf-8")
    bridges = (d / "chain_bridges.jsonl").read_text(encoding="utf-8")
    assert len(cards.splitlines()) == n1 + len(S2.CARDS)          # the Standard-Model lines kept
    assert "card_floor_standard_model" in cards and S2.FLOOR in cards
    assert S2.main() == 0
    assert (d / "chain_cards.jsonl").read_text(encoding="utf-8") == cards        # the same bytes
    assert (d / "chain_bridges.jsonl").read_text(encoding="utf-8") == bridges
    # and the order of seeds does not matter: millennium first, then the Standard Model, same set of ids
    d2 = Path(tempfile.mkdtemp(prefix="nh-seed2-"))
    monkeypatch.setattr(S1, "DATA", d2)
    monkeypatch.setattr(S2, "DATA", d2)
    assert S2.main() == 0 and S1.main() == 0
    ids = lambda p: {json.loads(l)["id"] for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}  # noqa: E731
    assert ids(d2 / "chain_cards.jsonl") == ids(d / "chain_cards.jsonl")


def test_the_chains_door_lists_the_floors_and_404s_an_unknown_one(monkeypatch):
    from concordance.web.api import dispatch
    from concordance.config import EngineConfig
    g = _graph()
    monkeypatch.setattr(chains, "_default_get_card", g.get)
    st, payload = dispatch("GET", "/chains", {"floors": "1"}, None, EngineConfig("secular"))
    body = payload.get("data") or payload
    assert st == 200 and {f["id"] for f in body["floors"]} == set(chains.FLOORS)
    st, payload = dispatch("GET", "/chains", {"floor": S2.FLOOR}, None, EngineConfig("secular"))
    body = payload.get("data") or payload
    assert st == 200 and len(body["ends"]) == 7 and len(body["joints"]) >= 10
    st, payload = dispatch("GET", "/chains", {"floor": "card_floor_does_not_exist"}, None, EngineConfig("secular"))
    assert st == 404


def test_every_joint_cites_a_carded_source_and_the_edge_names_the_seal_or_says_cited():
    ids = {c["id"] for c in M.cards()}
    for j in S2.JOINTS:
        for key in j["cites"]:
            assert S2._src(key) in ids, key
    ev = {(e["a"], e["b"]): e["evidence"] for e in S2.BRIDGES if e["relationship"] == "connects_at"}
    for (a, b), text in ev.items():
        assert ("Sealed:" in text) or ("Cited, not sealed" in text), (a, b)
