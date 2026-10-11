"""THE ROOTS — the Scripture anchor per reality-node: fold/supersede/retract, the two-way lookup,
verified refs, and the coverage gap. The key column of the concordance of reality."""
import json

import pytest

from concordance import roots


def test_anchor_and_lead_round_trip(tmp_path):
    roots.anchor("floor:card_floor_the_capstone", ["Ephesians 2:20", "Psalm 118:22"],
                 why="the cornerstone", by="proposed", verify=False, data_dir=tmp_path)
    r = roots.root_of("floor:card_floor_the_capstone", data_dir=tmp_path)
    assert r and r["refs"] == ["Ephesians 2:20", "Psalm 118:22"]
    assert r["by"] == "proposed" and r["why"] == "the cornerstone"


def test_latest_write_wins_and_retraction(tmp_path):
    roots.anchor("domain:thermodynamics", ["Psalm 102:25-26"], verify=False, data_dir=tmp_path)
    roots.anchor("domain:thermodynamics", ["Romans 8:20-21"], by="operator", verify=False, data_dir=tmp_path)
    r = roots.root_of("domain:thermodynamics", data_dir=tmp_path)
    assert r["refs"] == ["Romans 8:20-21"] and r["by"] == "operator"   # the confirmed anchor supersedes
    roots.anchor("domain:thermodynamics", [], verify=False, data_dir=tmp_path)   # retract
    assert roots.root_of("domain:thermodynamics", data_dir=tmp_path) is None


def test_the_concordance_direction_is_the_inverse(tmp_path):
    roots.anchor("floor:a", ["Genesis 1:1"], verify=False, data_dir=tmp_path)
    roots.anchor("domain:cosmology", ["Genesis 1:1", "Colossians 1:16"], verify=False, data_dir=tmp_path)
    roots.anchor("floor:b", ["John 1:1"], verify=False, data_dir=tmp_path)
    hits = roots.nodes_rooted_at("genesis 1:1", data_dir=tmp_path)      # loose match, case-insensitive
    assert {h["node"] for h in hits} == {"floor:a", "domain:cosmology"}
    assert [h["node"] for h in roots.nodes_rooted_at("John 1:1", data_dir=tmp_path)] == ["floor:b"]


def test_an_anchor_must_be_a_real_verse(tmp_path, monkeypatch):
    import concordance.verifiers.scripture as S
    # a ref that resolves -> kept; one that does not -> refused, nothing written
    monkeypatch.setattr(S, "read_passage",
                        lambda ref, lang=None: {"status": "ok", "verses": [{"verse": 1, "text": "x"}]}
                        if "Genesis" in ref else {"status": "not_found", "verses": []})
    ok = roots.anchor("floor:real", ["Genesis 1:1"], verify=True, data_dir=tmp_path)
    assert ok["ok"] and roots.root_of("floor:real", data_dir=tmp_path)
    bad = roots.anchor("floor:bad", ["Nowhere 9:9"], verify=True, data_dir=tmp_path)
    assert bad["ok"] is False and bad["refused"] == ["Nowhere 9:9"]
    assert roots.root_of("floor:bad", data_dir=tmp_path) is None


def test_no_corpus_stores_as_given(tmp_path, monkeypatch):
    import concordance.verifiers.scripture as S
    monkeypatch.setattr(S, "read_passage", lambda ref, lang=None: {"status": "source_missing", "verses": []})
    r = roots.anchor("floor:x", ["Genesis 1:1"], verify=True, data_dir=tmp_path)
    assert r["ok"] and roots.root_of("floor:x", data_dir=tmp_path)   # verified where the Bible lives, not here


def test_node_id_namespaces_and_rejects_unknown_kind():
    assert roots.node_id("floor", "card_floor_x") == "floor:card_floor_x"
    assert roots.node_id("domain", "thermodynamics") == "domain:thermodynamics"
    with pytest.raises(ValueError):
        roots.node_id("widget", "x")


def test_resolve_direct_then_inherited(tmp_path, monkeypatch):
    import concordance.chains as chains
    monkeypatch.setattr(chains, "FLOORS", ("card_floor_thermodynamics",))
    roots.anchor("floor:card_floor_thermodynamics", ["Romans 8:20-21"], by="proposed", verify=False, data_dir=tmp_path)
    gc = lambda cid: None  # no corpus needed for domain (name-match) or an explicit stick index  # noqa: E731
    # DIRECT — the floor itself
    d = roots.resolve("floor:card_floor_thermodynamics", get_card=gc, stick_index={}, data_dir=tmp_path)
    assert d["via"] == "direct" and d["refs"] == ["Romans 8:20-21"]
    # INHERITED — a domain inherits its floor by name (card_floor_<domain>)
    di = roots.resolve("domain:thermodynamics", get_card=gc, stick_index={}, data_dir=tmp_path)
    assert di and di["via"] == "inherited" and di["by"] == "inherited"
    assert di["through"] == "floor:card_floor_thermodynamics" and di["refs"] == ["Romans 8:20-21"]
    # INHERITED — a charted stick inherits the floor it charts (via the index)
    si = {"stick_entropy": "card_floor_thermodynamics"}
    si_res = roots.resolve("stick:stick_entropy", get_card=gc, stick_index=si, data_dir=tmp_path)
    assert si_res["via"] == "inherited" and si_res["through"] == "floor:card_floor_thermodynamics"


def test_a_placement_files_a_node_under_a_floor_for_inheritance(tmp_path, monkeypatch):
    import concordance.chains as chains
    monkeypatch.setattr(chains, "FLOORS", ("card_floor_acoustics", "card_floor_biology"))
    # a filing must point at a real floor
    bad = roots.place("stick:stick_x", "card_floor_nonsense", verify=True, data_dir=tmp_path)
    assert bad["ok"] is False
    roots.place("stick:stick_acoustics_waves", "card_floor_acoustics", why="acoustics", by="proposed",
                verify=True, data_dir=tmp_path)
    assert roots.placements_fold(tmp_path)["stick:stick_acoustics_waves"]["floor"] == "card_floor_acoustics"
    # an uncharted stick with no direct anchor and no chart inherits through its FILING once the floor is anchored
    roots.anchor("floor:card_floor_acoustics", ["Psalm 150:3-5"], verify=False, data_dir=tmp_path)
    r = roots.resolve("stick:stick_acoustics_waves", get_card=lambda cid: None, stick_index={}, data_dir=tmp_path)
    assert r["via"] == "inherited" and r["through"] == "floor:card_floor_acoustics" and r["refs"] == ["Psalm 150:3-5"]
    # retract the filing -> back to a want
    roots.place("stick:stick_acoustics_waves", "", verify=False, data_dir=tmp_path)
    assert roots.resolve("stick:stick_acoustics_waves", get_card=lambda cid: None, stick_index={}, data_dir=tmp_path) is None


def test_an_unconnected_node_stays_a_want(tmp_path, monkeypatch):
    import concordance.chains as chains
    monkeypatch.setattr(chains, "FLOORS", ("card_floor_thermodynamics",))
    roots.anchor("floor:card_floor_thermodynamics", ["Romans 8:20-21"], verify=False, data_dir=tmp_path)
    gc = lambda cid: None  # noqa: E731
    # a domain with no matching floor, and a stick not in the index, reach nothing
    assert roots.resolve("domain:underwater_basket_weaving", get_card=gc, stick_index={}, data_dir=tmp_path) is None
    assert roots.resolve("stick:stick_uncharted", get_card=gc, stick_index={}, data_dir=tmp_path) is None


def test_resolved_coverage_counts_inheritance(tmp_path, monkeypatch):
    import concordance.chains as chains
    import concordance.tickstick as tickstick
    monkeypatch.setattr(chains, "FLOORS", ("card_floor_thermodynamics", "card_floor_riemann"))
    monkeypatch.setattr(tickstick, "listing",
                        lambda data_dir=None: {"sticks": [{"id": "stick_entropy"}, {"id": "stick_uncharted"}]})
    monkeypatch.setattr(roots, "stick_floor_index", lambda get_card=None: {"stick_entropy": "card_floor_thermodynamics"})
    (tmp_path / "domain_goldens.json").write_text('{"thermodynamics": {}, "astrology": {}}', encoding="utf-8")
    roots.anchor("floor:card_floor_thermodynamics", ["Romans 8:20-21"], verify=False, data_dir=tmp_path)
    cov = roots.resolved_coverage(get_card=lambda cid: None, data_dir=tmp_path)
    # floors: 1 direct (thermo), 1 open (riemann); domains: thermodynamics inherits, astrology unconnected;
    # sticks: stick_entropy inherits, stick_uncharted unconnected
    assert cov["direct"] == 1 and cov["inherited"] == 2
    assert cov["by_kind"]["domain"]["inherited"] == 1 and cov["by_kind"]["domain"]["unconnected"] == 1
    assert cov["by_kind"]["stick"]["inherited"] == 1 and cov["by_kind"]["stick"]["unconnected"] == 1
    assert cov["unconnected"] == 2   # astrology + stick_uncharted reach no floor at all


def test_coverage_measures_the_gap_by_kind(tmp_path, monkeypatch):
    import concordance.chains as chains
    import concordance.tickstick as tickstick
    monkeypatch.setattr(chains, "FLOORS", ("card_floor_a", "card_floor_b"))
    monkeypatch.setattr(tickstick, "listing", lambda data_dir=None: {"sticks": [{"id": "s1"}, {"id": "s2"}, {"id": "s3"}]})
    (tmp_path / "domain_goldens.json").write_text(json.dumps({"d1": {}, "d2": {}}), encoding="utf-8")
    roots.anchor("floor:card_floor_a", ["Genesis 1:1"], by="operator", verify=False, data_dir=tmp_path)
    roots.anchor("domain:d1", ["Proverbs 16:33"], by="proposed", verify=False, data_dir=tmp_path)
    cov = roots.coverage(data_dir=tmp_path)
    assert cov["total_nodes"] == 2 + 3 + 2 and cov["anchored"] == 2
    assert cov["by_kind"]["floor"] == {"total": 2, "anchored": 1, "open": ["floor:card_floor_b"]}
    assert cov["by_kind"]["stick"]["anchored"] == 0 and cov["by_kind"]["stick"]["total"] == 3
    assert cov["kept_by"] == {"operator": 1, "proposed": 1, "other": 0}
