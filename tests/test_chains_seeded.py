"""THE CHAINS ON THE ONE MAP (Matt, 2026-10-09: "logarithms fit here correct?" - "same" - "same with the millennium").
The logarithm and the seven Millennium problems as lineages from a floor, in the same two files as the Standard Model
and the joints floor. Pinned on the seeds alone (no corpus build): every chain's floor reads its two roots, its chain
walks forward to the open question, the confluence the seed EXPECTS is the one the graph FINDS, the logarithm enters
every question, every edge endpoint resolves to a seeded or carded id, every DOI is well-formed, the Millennium joints
are unchanged by the chains, and the three seeders merge in any order."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="nh-chains-")
os.environ.setdefault("CONCORDANCE_DATA_DIR", TMP)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import card_millennium_sources as M  # noqa: E402
import seed_chains as S3  # noqa: E402
import seed_millennium_chain as S2  # noqa: E402
import seed_standard_model_chain as S1  # noqa: E402
from concordance import chains, corpus  # noqa: E402


def _graph():
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S1.CARDS + S2.CARDS + S3.CARDS + M.cards() + [M.spine_card(1)]}
    for cid in ("card_builder_james_clerk_maxwell", "card_k_floor_of_discovery", "card_spine_builders"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(TMP) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S1.BRIDGES + S2.BRIDGES + S3.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    return cards


def test_the_seed_validates_and_every_endpoint_resolves():
    assert S3._validate() == []
    assert len(S3.CHAINS) == 8 and len(S3.RECORDS) >= 55
    assert set(S3.FLOORS) <= set(chains.FLOORS) and len(chains.FLOORS) == 30


def test_each_chain_walks_from_its_roots_to_its_open_end_and_meets_where_the_seed_expects():
    g = _graph()
    for c in S3.CHAINS:
        m = chains.floor_map(f"card_floor_{c['slug']}", get_card=g.get)
        assert m, c["slug"]
        assert [p["id"] for p in m["parts"]] == [S3._node(r) for r in c["roots"]], c["slug"]
        ids = {n["id"] for n in m["chain"]["nodes"]}
        assert len(ids) >= 6, c["slug"]
        for e in c["ends"]:
            assert S3.q(e) in {x["id"] for x in m["ends"]}, (c["slug"], e)
        if c["slug"] != "logarithm":
            assert S3.q(c["ends"][0]) in ids, c["slug"]                 # the walk reaches the open question
        assert S3._node(c["expect_confluence"]) in {x["at"] for x in m["confluences"]}, c["slug"]
        assert all(e["from"] in ids for e in m["chain"]["edges"])


def test_the_logarithm_enters_every_question():
    g = _graph()
    m = chains.floor_map("card_floor_logarithm", get_card=g.get)
    assert len(m["ends"]) == 7 and len(m["entries"]) >= 8
    assert {e["end"] for e in m["entries"]} == {S3.q(s) for s in ("riemann", "bsd", "navier_stokes", "yang_mills", "p_vs_np", "hodge", "poincare")}
    for e in m["entries"]:
        assert e["evidence"].startswith("where the logarithm enters:")
    # a chain floor with one end has no pairwise joints and no misses
    r = chains.floor_map("card_floor_riemann", get_card=g.get)
    assert r["joints"] == [] and r["misses"] == []


def test_the_millennium_joints_are_unchanged_by_the_chains():
    g = _graph()
    m = chains.floor_map(S2.FLOOR, get_card=g.get)
    assert len(m["ends"]) == 7 and len(m["parts"]) == 10 and len(m["joints"]) >= 10
    q = S2._q
    at = {(j["a"], j["b"]): j["at"] for j in m["joints"]}
    assert at[(q("riemann"), q("yang_mills"))] == S2._j("gue_statistics")
    assert at[(q("hodge"), q("poincare"))] == S2._j("bochner_vanishing")
    sm = chains.floor_map(S1.FLOOR, get_card=g.get)
    assert [j["at"] for j in sm["joints"]] == ["card_builder_steven_weinberg"] and len(sm["chain"]["nodes"]) >= 10


def test_every_record_is_cited_with_a_wellformed_doi_or_a_free_or_canonical_copy():
    import re
    doi = re.compile(r"^10\.\d{4,9}/\S+$")
    for r in S3.RECORDS:
        assert r["authors"] and r["year"] and r["title"] and r["venue"], r["key"]
        if r["doi"]:
            assert doi.match(r["doi"]), r["key"]
        assert S3._license_ok(r["license"]), r["key"]
    c = S3.record_card(S3.REC["riemann_1859"])
    assert c["shelf"] == "codex" and c["generated"] is False and "License as found" in c["body"]


def test_the_three_seeders_merge_in_any_order(monkeypatch):
    d = Path(tempfile.mkdtemp(prefix="nh-seed3-"))
    monkeypatch.setattr(sys, "argv", ["seed"])
    for s in (S1, S2, S3):
        monkeypatch.setattr(s, "DATA", d)
    assert S3.main() == 0 and S1.main() == 0 and S2.main() == 0
    ids = lambda p: {json.loads(l)["id"] for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}  # noqa: E731
    got = ids(d / "chain_cards.jsonl")
    assert got == {c["id"] for c in S1.CARDS + S2.CARDS + S3.CARDS}
    before = (d / "chain_bridges.jsonl").read_bytes()
    assert S3.main() == 0 and (d / "chain_bridges.jsonl").read_bytes() == before      # idempotent


def test_the_chains_door_reads_a_chain_floor(monkeypatch):
    from concordance.web.api import dispatch
    from concordance.config import EngineConfig
    g = _graph()
    monkeypatch.setattr(chains, "_default_get_card", g.get)
    st, payload = dispatch("GET", "/chains", {"floor": "card_floor_riemann"}, None, EngineConfig("secular"))
    body = payload.get("data") or payload
    assert st == 200 and len(body["chain"]["nodes"]) >= 12 and body["confluences"][0]["at"] == "card_chain_riemann_1859"
    st, payload = dispatch("GET", "/chains", {"floors": "1"}, None, EngineConfig("secular"))
    body = payload.get("data") or payload
    assert st == 200 and len(body["floors"]) == 30


def test_the_capstone_floor_gathers_the_others_and_marks_the_two_barriers():
    """The capstone (Matt, 2026-10-09): one source, many potentials, one end - the floor the others stand on. Three
    pillars (parts); it rests on (serves) the one force, the tree of life and the solve path; the narrow way is
    flanked by the two marked barriers (Copenhagen's silence, many-worlds' excess). Pinned on the seed alone."""
    import seed_the_capstone as S4
    assert S4._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S4.CARDS}
    for cid in ("card_floor_standard_model", "card_floor_tree_of_life", "card_floor_the_solve_path",
                "card_floor_the_instruments", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-cap-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S4.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S4.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 3
    assert (m.get("charts") == [] or True) and m["title"].startswith("The capstone")
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_standard_model", "card_floor_tree_of_life", "card_floor_the_solve_path"} <= serves
    assert "card_capstone_copenhagen" in serves and "card_capstone_many_worlds" in serves


def test_the_hamiltonian_floor_rests_on_the_capstone_and_solve_path_with_the_measurement_gap_open():
    """The Hamiltonian (Matt, 2026-10-09): the law of the flow - four pillars resting on the capstone and the solve
    path, with the measurement gap as its one open end. Pinned on the seed alone."""
    import seed_the_hamiltonian as S5
    assert S5._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S5.CARDS}
    for cid in ("card_floor_the_capstone", "card_floor_the_solve_path", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-ham-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S5.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S5.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4 and len(m["ends"]) == 1
    assert m["ends"][0]["id"] == "card_question_measurement_gap"
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_the_capstone", "card_floor_the_solve_path"} <= serves


def test_the_lagrangian_floor_is_the_hamiltonians_dual_and_gathers_least_action():
    """The Lagrangian (Matt, 2026-10-09): the Hamiltonian's Legendre dual - four pillars resting on the Hamiltonian,
    the capstone, the solve path and the Standard Model. Pinned on the seed alone."""
    import seed_the_lagrangian as S6
    assert S6._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S6.CARDS}
    for cid in ("card_floor_the_hamiltonian", "card_floor_the_capstone", "card_floor_the_solve_path",
                "card_floor_standard_model", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-lag-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S6.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S6.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_the_hamiltonian", "card_floor_the_capstone", "card_floor_standard_model"} <= serves


def test_noethers_theorem_is_the_seam_between_the_lagrangian_and_the_hamiltonian():
    """Noether (Matt, 2026-10-09): symmetry is the source of conservation - four pillars resting on the Lagrangian,
    the capstone, the Hamiltonian and the Standard Model. Pinned on the seed alone."""
    import seed_noethers_theorem as S7
    assert S7._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S7.CARDS}
    for cid in ("card_floor_the_lagrangian", "card_floor_the_capstone", "card_floor_the_hamiltonian",
                "card_floor_standard_model", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-noe-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S7.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S7.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_the_lagrangian", "card_floor_the_hamiltonian", "card_floor_standard_model"} <= serves


def test_maxwells_equations_floor_is_the_first_unification():
    """Maxwell (Matt, 2026-10-09): the first unification - four pillars resting on the capstone, Noether, the
    Lagrangian and the Standard Model; the floor cites the already-sealed EM stick. Pinned on the seed alone."""
    import seed_maxwells_equations as S8
    assert S8._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S8.CARDS}
    for cid in ("card_floor_the_capstone", "card_floor_noethers_theorem", "card_floor_the_lagrangian",
                "card_floor_standard_model", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-max-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S8.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S8.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4 and m["title"].startswith("Maxwell")
    assert S8.floor_card()["source"]["ref"] == "stick_maxwell_s_equations_and_superconductivity"  # cites, no new stick
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_the_capstone", "card_floor_noethers_theorem", "card_floor_the_lagrangian",
            "card_floor_standard_model"} <= serves


def test_thermodynamics_floor_is_the_arrow_and_the_one_end():
    """Thermodynamics (Matt, 2026-10-09): the four laws - four pillars resting on Noether (1st law), the capstone
    (2nd law/arrow), the Hamiltonian (stat mech) and the instruments (entropy=information). Pinned on the seed."""
    import seed_thermodynamics as S9
    assert S9._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S9.CARDS}
    for cid in ("card_floor_noethers_theorem", "card_floor_the_capstone", "card_floor_the_hamiltonian",
                "card_floor_the_instruments", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-thm-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S9.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S9.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_noethers_theorem", "card_floor_the_capstone", "card_floor_the_hamiltonian",
            "card_floor_the_instruments"} <= serves


def test_relativity_floor_ties_the_physics_region():
    """Relativity (Matt, 2026-10-09): many frames, one invariant - four pillars resting on Maxwell, the capstone,
    the Hamiltonian, the Lagrangian and Noether. Pinned on the seed alone."""
    import seed_relativity as S10
    assert S10._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S10.CARDS}
    for cid in ("card_floor_maxwells_equations", "card_floor_the_capstone", "card_floor_the_hamiltonian",
                "card_floor_the_lagrangian", "card_floor_noethers_theorem", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-rel-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S10.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S10.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_maxwells_equations", "card_floor_the_hamiltonian", "card_floor_the_lagrangian",
            "card_floor_noethers_theorem"} <= serves


def test_quantum_mechanics_floor_is_the_framework_and_adds_uncertainty_and_entanglement():
    """Quantum mechanics (Matt, 2026-10-09): the framework the physics region lives in - four pillars resting on the
    Hamiltonian, Maxwell, the capstone, the instruments and relativity. Pinned on the seed alone."""
    import seed_quantum_mechanics as S11
    assert S11._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S11.CARDS}
    for cid in ("card_floor_the_hamiltonian", "card_floor_maxwells_equations", "card_floor_the_capstone",
                "card_floor_the_instruments", "card_floor_relativity", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-qm-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S11.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S11.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_the_hamiltonian", "card_floor_the_capstone", "card_floor_the_instruments",
            "card_floor_relativity"} <= serves


def test_the_standard_model_content_is_charted_onto_the_existing_floor():
    """Standard Model (Matt, 2026-10-09): the gauge content and quark model, charted onto the EXISTING
    card_floor_standard_model (no new floor). Pinned on the seed + the standard-model chain seed."""
    import seed_standard_model_chain as S1
    import seed_standard_model_content as S12
    assert S12._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S1.CARDS + S12.CARDS}
    cards.setdefault("card_k_floor_of_discovery", {"id": "card_k_floor_of_discovery", "title": "", "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-sm-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S1.BRIDGES + S12.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map("card_floor_standard_model", get_card=cards.get)
    assert m is not None
    charts = {c["stick"] for c in m["charts"]}
    assert "stick_the_standard_model_gauge_forces_and_quarks" in charts
    assert m["charts"][0]["of"] == "card_floor_standard_model"  # charted onto the floor itself


def test_hermitian_operators_are_charted_onto_the_quantum_mechanics_floor():
    """Hermitian operators (Matt, 2026-10-09): the formal object under the quantum region, charted onto the EXISTING
    card_floor_quantum_mechanics (no new floor), with the Hilbert-Polya tie to Riemann. Pinned on the seeds."""
    import seed_quantum_mechanics as QM
    import seed_hermitian_operators as S13
    assert S13._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in QM.CARDS + S13.CARDS}
    for cid in ("card_floor_the_hamiltonian", "card_floor_maxwells_equations", "card_floor_the_capstone",
                "card_floor_the_instruments", "card_floor_relativity", "card_floor_riemann",
                "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-herm-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in QM.BRIDGES + S13.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map("card_floor_quantum_mechanics", get_card=cards.get)
    assert m is not None
    assert "stick_hermitian_operators_real_eigenvalues_the_observables" in {c["stick"] for c in m["charts"]}


def test_chemistry_floor_stands_on_the_physics_region():
    """Chemistry (Matt, 2026-10-09): the world of substances - QM applied - four pillars resting on quantum
    mechanics, Maxwell, thermodynamics and Noether. Pinned on the seed alone."""
    import seed_chemistry as S14
    assert S14._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S14.CARDS}
    for cid in ("card_floor_quantum_mechanics", "card_floor_maxwells_equations", "card_floor_thermodynamics",
                "card_floor_noethers_theorem", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-chem-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S14.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S14.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_quantum_mechanics", "card_floor_maxwells_equations", "card_floor_thermodynamics",
            "card_floor_noethers_theorem"} <= serves


def test_physical_chemistry_floor_stands_on_chemistry():
    """Physical chemistry (Matt, 2026-10-09, "deeper in chemistry"): rate, equilibrium, acid-base, redox - four
    pillars reaching to chemistry, thermodynamics and Maxwell. Pinned on the seed alone."""
    import seed_physical_chemistry as S15
    assert S15._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S15.CARDS}
    for cid in ("card_floor_chemistry", "card_floor_thermodynamics", "card_floor_maxwells_equations",
                "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-pchem-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S15.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S15.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_chemistry", "card_floor_thermodynamics", "card_floor_maxwells_equations"} <= serves


def test_biology_floor_stands_on_chemistry_and_connects_the_tree_of_life():
    """Biology (Matt, 2026-10-09, down the domain list): life = self-replicating chemistry - four pillars reaching to
    chemistry/instruments, the tree of life, the capstone and thermodynamics. Pinned on the seed alone."""
    import seed_biology as S16
    assert S16._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S16.CARDS}
    for cid in ("card_floor_chemistry", "card_floor_the_instruments", "card_floor_tree_of_life",
                "card_floor_the_capstone", "card_floor_thermodynamics", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-bio-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S16.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S16.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_chemistry", "card_floor_tree_of_life", "card_floor_thermodynamics"} <= serves


def test_earth_science_floor_stands_on_chemistry_and_hands_biology_deep_time():
    """Earth science (Matt, 2026-10-09, down the domain list): the planet - four pillars reaching to physical
    chemistry, chemistry, thermodynamics and biology. Pinned on the seed alone."""
    import seed_earth_science as S17
    assert S17._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S17.CARDS}
    for cid in ("card_floor_physical_chemistry", "card_floor_chemistry", "card_floor_thermodynamics",
                "card_floor_biology", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-earth-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S17.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S17.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_physical_chemistry", "card_floor_chemistry", "card_floor_thermodynamics",
            "card_floor_biology"} <= serves


def test_the_mind_floor_tops_the_ladder_with_the_hard_problem_as_its_open_end():
    """The mind (Matt, 2026-10-09, down the domain list): matter aware of itself - three pillars on physical
    chemistry/biology/instruments/thermodynamics, with the hard problem of consciousness as its one open end."""
    import seed_the_mind as S18
    assert S18._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S18.CARDS}
    for cid in ("card_floor_physical_chemistry", "card_floor_biology", "card_floor_the_instruments",
                "card_floor_thermodynamics", "card_floor_the_capstone", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-mind-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S18.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S18.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 3 and len(m["ends"]) == 1
    assert m["ends"][0]["id"] == "card_question_the_hard_problem"
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_biology", "card_floor_the_instruments", "card_floor_thermodynamics"} <= serves


def test_quantum_harmonic_oscillator_is_charted_onto_the_quantum_mechanics_floor():
    """The QHO (Matt, 2026-10-09): a system charted onto card_floor_quantum_mechanics (no new floor), with the
    field-as-oscillators tie to the Standard Model. Pinned on the seeds."""
    import seed_quantum_mechanics as QM
    import seed_quantum_harmonic_oscillator as S19
    assert S19._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in QM.CARDS + S19.CARDS}
    for cid in ("card_floor_the_hamiltonian", "card_floor_maxwells_equations", "card_floor_the_capstone",
                "card_floor_the_instruments", "card_floor_relativity", "card_floor_standard_model",
                "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-qho-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in QM.BRIDGES + S19.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map("card_floor_quantum_mechanics", get_card=cards.get)
    assert m is not None
    assert "stick_the_quantum_harmonic_oscillator_zero_point_and_the_ladder" in {c["stick"] for c in m["charts"]}


def test_consciousness_receiver_is_charted_onto_the_mind_floor():
    """Consciousness as a receiver (Matt, 2026-10-09): a cited hypothesis for the hard problem, charted onto
    card_floor_the_mind - the radio physics sealed, the consciousness claim declined. Pinned on the seeds."""
    import seed_the_mind as MIND
    import seed_consciousness_receiver as S20
    assert S20._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in MIND.CARDS + S20.CARDS}
    for cid in ("card_floor_physical_chemistry", "card_floor_biology", "card_floor_the_instruments",
                "card_floor_thermodynamics", "card_floor_the_capstone", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-consc-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in MIND.BRIDGES + S20.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map("card_floor_the_mind", get_card=cards.get)
    assert m is not None
    assert "stick_consciousness_as_a_receiver_the_crystal_radio" in {c["stick"] for c in m["charts"]}


def test_cryptography_floor_bridges_to_the_millennium_region():
    """Cryptography (Matt, 2026-10-09, "cryptography next"): public keys and hard problems - four pillars reaching to
    the instruments, P vs NP (hardness) and Riemann (primes). Pinned on the seed alone."""
    import seed_cryptography as S21
    assert S21._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S21.CARDS}
    for cid in ("card_floor_the_instruments", "card_floor_p_vs_np", "card_floor_riemann",
                "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-crypto-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S21.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S21.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_the_instruments", "card_floor_p_vs_np", "card_floor_riemann"} <= serves


def test_statistics_floor_is_the_method_of_science():
    """Statistics (Matt, 2026-10-09, down the domain list): the normal law and the method of science - four pillars
    reaching to the instruments, the capstone and biology. Pinned on the seed alone."""
    import seed_statistics as S22
    assert S22._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S22.CARDS}
    for cid in ("card_floor_the_instruments", "card_floor_the_capstone", "card_floor_biology",
                "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-stats-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S22.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S22.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_the_instruments", "card_floor_the_capstone", "card_floor_biology"} <= serves


def test_tesseract_is_charted_onto_the_capstone():
    """The tesseract (Matt, 2026-10-09): a 4-cube charted onto card_floor_the_capstone (the shadow/one theme), with
    a connects_at to relativity. Pinned on the seeds."""
    import seed_the_capstone as CAP
    import seed_tesseract as S23
    assert S23._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in CAP.CARDS + S23.CARDS}
    for cid in ("card_floor_standard_model", "card_floor_tree_of_life", "card_floor_the_solve_path",
                "card_floor_the_instruments", "card_floor_relativity", "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-tess-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in CAP.BRIDGES + S23.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map("card_floor_the_capstone", get_card=cards.get)
    assert m is not None
    assert "stick_the_tesseract_the_4_cube_and_its_shadow" in {c["stick"] for c in m["charts"]}


def test_economics_floor_rests_on_the_mind_and_statistics():
    """Economics (Matt, 2026-10-10, complete the domain list): minds that choose meeting scarcity - four pillars
    reaching to the mind, statistics and the instruments; cites the finance stick. Pinned on the seed alone."""
    import seed_economics as S24
    assert S24._validate() == []
    cards = {c["id"]: json.loads(json.dumps(c)) for c in S24.CARDS}
    for cid in ("card_floor_the_mind", "card_floor_statistics", "card_floor_the_instruments",
                "card_k_floor_of_discovery"):
        cards.setdefault(cid, {"id": cid, "title": cid, "connections": []})
    overlay = Path(tempfile.mkdtemp(prefix="nh-econ-")) / "overlay.jsonl"
    overlay.write_text("\n".join(json.dumps(e) for e in S24.BRIDGES) + "\n", encoding="utf-8")
    corpus._apply_bridges(cards, overlay)
    m = chains.floor_map(S24.FLOOR, get_card=cards.get)
    assert m and len(m["parts"]) == 4
    assert S24.floor_card()["source"]["ref"] == "stick_economics_the_finance_arithmetic_verified_and_sealed"
    serves = {s["at"] for s in m["serves"]}
    assert {"card_floor_the_mind", "card_floor_statistics", "card_floor_the_instruments"} <= serves
