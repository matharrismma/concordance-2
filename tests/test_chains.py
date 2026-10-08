"""chains.walk / chains.intersect — the discovery-chain traversal, proven on a synthetic graph.

Models the Standard-Model case in miniature: a weak chain (Fermi -> Yang-Mills -> parity -> electroweak)
and an electromagnetic chain (Maxwell -> QED -> electroweak) that CONNECT at the electroweak node. The
traversal takes ids and returns ids (no bodies), and is injected with a fixture accessor so it needs no
corpus build.
"""
from concordance import chains


def _edge(to, rel="enables"):
    return {"to_card_id": to, "relationship": rel, "evidence": "builds on the prior work"}


# a tiny two-tree graph that meets at 'electroweak'
_CARDS = {
    "floor_sm":     {"id": "floor_sm", "connections": [_edge("fermi"), _edge("maxwell")]},
    "fermi":        {"id": "fermi", "connections": [_edge("yang_mills")]},
    "yang_mills":   {"id": "yang_mills", "connections": [_edge("parity")]},
    "parity":       {"id": "parity", "connections": [_edge("electroweak")]},
    "maxwell":      {"id": "maxwell", "connections": [_edge("qed")]},
    "qed":          {"id": "qed", "connections": [_edge("electroweak")]},
    "electroweak":  {"id": "electroweak", "connections": []},
}


def _get(cid):
    return _CARDS.get(cid)


def test_walk_follows_the_lineage_forward():
    assert chains.walk("fermi", get_card=_get) == ["fermi", "yang_mills", "parity", "electroweak"]
    assert chains.walk("maxwell", get_card=_get) == ["maxwell", "qed", "electroweak"]


def test_walk_terminates_on_a_cycle():
    cyc = {"a": {"id": "a", "connections": [_edge("b")]},
           "b": {"id": "b", "connections": [_edge("a")]}}
    out = chains.walk("a", get_card=cyc.get)
    assert out == ["a", "b"]            # visits each once, no infinite loop


def test_walk_stops_at_a_missing_or_leaf_node():
    assert chains.walk("electroweak", get_card=_get) == ["electroweak"]   # leaf
    assert chains.walk("ghost", get_card=_get) == ["ghost"]               # unknown id -> just itself


def test_intersect_finds_where_two_chains_connect():
    # the weak chain and the EM chain meet at electroweak
    assert chains.intersect("fermi", "maxwell", get_card=_get) == "electroweak"
    # symmetric
    assert chains.intersect("maxwell", "fermi", get_card=_get) == "electroweak"


def test_intersect_returns_none_for_disjoint_chains():
    disjoint = {"x": {"id": "x", "connections": [_edge("y")]},
                "y": {"id": "y", "connections": []},
                "p": {"id": "p", "connections": [_edge("q")]},
                "q": {"id": "q", "connections": []}}
    assert chains.intersect("x", "p", get_card=disjoint.get) is None


def test_chain_shape_for_a_reader():
    c = chains.chain("fermi", get_card=_get)
    assert c["floor"] == "fermi" and c["length"] == 4 and c["steps"][-1] == "electroweak"


def test_standard_model_seed_real_data():
    """The real seed files (data/chain_cards.jsonl + data/chain_bridges.jsonl) fold through the real
    corpus._apply_bridges and produce the expected lineage + connection — no full corpus build."""
    import json
    from pathlib import Path
    from concordance import corpus
    root = Path(__file__).resolve().parents[1]
    seed = root / "data" / "chain_cards.jsonl"
    overlay = root / "data" / "chain_bridges.jsonl"
    if not seed.exists() or not overlay.exists():
        import pytest
        pytest.skip("chain seed not generated (run tools/seed_standard_model_chain.py)")
    cards = {}
    for ln in seed.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            c = json.loads(ln)
            cards[c["id"]] = c
    # stubs for the live cards the bridges reference (present in the full corpus)
    for cid in ("card_builder_james_clerk_maxwell", "card_k_floor_of_discovery", "card_spine_builders"):
        cards.setdefault(cid, {"id": cid, "connections": []})
    corpus._apply_bridges(cards, overlay)
    get = cards.get
    # the weak lineage walks forward from Fermi and includes Yang
    w = chains.walk("card_builder_enrico_fermi", get_card=get)
    assert w[0] == "card_builder_enrico_fermi" and "card_builder_chen_ning_yang" in w
    # the two trees CONNECT at Weinberg (electroweak unification), over the forward 'enables' edges
    conn = chains.intersect("card_builder_enrico_fermi", "card_builder_james_clerk_maxwell",
                            rels={chains.ENABLES}, get_card=get)
    assert conn == "card_builder_steven_weinberg", conn
    # each root hangs under this path's floor
    fermi = cards["card_builder_enrico_fermi"]
    assert any(e.get("to_card_id") == "card_floor_standard_model" and e.get("relationship") == "part_of"
               for e in fermi["connections"])


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("ALL PASS")


def test_chains_door_404s_an_unknown_card_and_is_rate_limited():
    """Review 2026-10-08: a lineage of a card that does not exist is not a lineage (was a 200 with length 1),
    and the door is read-rate-limited like every sibling route."""
    from concordance.web.api import dispatch, ROUTES
    from concordance.config import EngineConfig
    st, payload = dispatch("GET", "/chains", {"root": "card_does_not_exist_xyz"}, None, EngineConfig("secular"))
    assert st == 404 and "no card" in payload.get("error", "")
    st, _ = dispatch("GET", "/chains", {"a": "card_does_not_exist_xyz", "b": "also_missing"}, None, EngineConfig("secular"))
    assert st == 404
    route = next(r for r in ROUTES if r["path"] == "/chains")
    assert route.get("rl") == "read"
