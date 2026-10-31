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


# ── least-doubt paths: Dijkstra over MEASURED cost (declared relationship + the kernel's authority ladder)

def _card(cid, conns, tier="verified"):
    return {"id": cid, "connections": conns, "source": {"authority_tier": tier}}


def test_least_doubt_prefers_a_longer_proven_path_over_a_short_unverified_one():
    # start -> goal in TWO hops via an 'unspecified' bridge onto a QUARANTINED card, or in THREE hops through
    # verified `enables` lineage. Fewest-hops says the shortcut; least-doubt says the proven lineage.
    g = {
        "start": _card("start", [{"to_card_id": "shady", "relationship": "unspecified", "evidence": ""},
                                 _edge("p1")]),
        "shady": _card("shady", [_edge("goal")], tier="quarantined"),
        "p1":    _card("p1", [_edge("p2")]),
        "p2":    _card("p2", [_edge("goal")]),
        "goal":  _card("goal", []),
    }
    out = chains.shortest("start", "goal", get_card=g.get)
    assert out["path"] == ["start", "p1", "p2", "goal"]       # the proven lineage, not the 2-hop shortcut
    shortcut = chains.edge_cost(g["start"]["connections"][0], g["shady"]) + chains.edge_cost(_edge("goal"), g["goal"])
    assert out["cost"] < shortcut                              # and it is cheaper in doubt, by construction


def test_shortest_returns_cost_and_none_when_unreachable():
    out = chains.shortest("fermi", "electroweak", get_card=_get)
    assert out["path"] == ["fermi", "yang_mills", "parity", "electroweak"] and out["cost"] > 0
    assert chains.shortest("electroweak", "fermi", get_card=_get) is None   # edges are directed
    assert chains.shortest("x", "x", get_card=_get) == {"cost": 0, "path": ["x"]}


def test_intersect_weighted_finds_the_least_doubt_meeting():
    w = chains.intersect_weighted("fermi", "maxwell", get_card=_get)
    assert w and w["at"] == "electroweak" and w["cost"] == w["cost_a"] + w["cost_b"] + w["joint_bits"]
    assert chains.intersect("fermi", "maxwell", get_card=_get) == "electroweak"   # BFS still agrees here
    # a joint is a THIRD card: when b lies on a's own lineage the meeting is still the card beyond, not b itself
    # (live, 2026-10-31: e reached the trig parts directly and the "meeting" came back as the trig card at cost_b 0)
    w = chains.intersect_weighted("fermi", "parity", get_card=_get)
    assert w and w["at"] == "electroweak" and w["cost_b"] > 0


def test_nearest_floor_by_least_doubt():
    g = dict(_CARDS)   # electroweak is a leaf in the fixture; hang a floor off it
    g["electroweak"] = {"id": "electroweak", "connections": [_edge("floor_x", rel="part_of")]}
    g["floor_x"] = _card("floor_x", [])
    nf = chains.nearest_floor("fermi", floors=["floor_x", "floor_never"], get_card=g.get)
    assert nf and nf["floor"] == "floor_x"
    assert chains.nearest_floor("fermi", floors=["floor_never"], get_card=g.get) is None


def test_edge_cost_is_measured_not_guessed():
    verified, cited, shady = _card("v", []), _card("c", [], tier="cited"), _card("q", [], tier="quarantined")
    assert chains.edge_cost(_edge("v"), verified) < chains.edge_cost(_edge("c"), cited) < chains.edge_cost(_edge("q"), shady)
    assert chains.edge_cost({"to_card_id": "v", "relationship": "unspecified"}, verified) > chains.edge_cost(_edge("v", rel="connects_at"), verified) > chains.edge_cost(_edge("v"), verified)


# ── tensors as the TERRAIN beneath the chains: roads (declared edges) are proof; the scaffold's own
# proximity (the floor's 1 - Jaccard metric over an axis's members) fills the gaps where no road was drawn.

def _tcard(cid, shelf, conns=(), tier="verified"):
    return {"id": cid, "shelf": shelf, "connections": list(conns), "source": {"authority_tier": tier}}


def test_terrain_connects_cards_with_no_declared_road():
    # physics and chemistry share scaffold members (physical_substance, conservation_balance) — near on the
    # tensor — but NO chain edge joins these two cards. Roads alone: unreachable. Terrain: reachable.
    g = {"a": _tcard("a", "physics"), "b": _tcard("b", "chemistry")}
    assert chains.shortest("a", "b", get_card=g.get) is None
    out = chains.shortest("a", "b", get_card=g.get, terrain_fn=lambda cid: [x for x in g if x != cid])
    assert out and out["path"] == ["a", "b"] and out["cost"] == chains.tensor_cost("physics", "chemistry")


def test_a_declared_road_beats_terrain_proximity():
    # a -> b by a proven `enables` road AND terrain-adjacent (same axis): the road (1) must win over the
    # lateral terrain step (2) — proof is cheaper than proximity, by construction.
    g = {"a": _tcard("a", "physics", [_edge("b")]), "b": _tcard("b", "physics")}
    out = chains.shortest("a", "b", get_card=g.get, terrain_fn=lambda cid: ["b"])
    assert out["cost"] == 1


def test_tensor_cost_is_the_floors_metric():
    # the number is RECOMPUTED from the grid, never pinned by hand (the retag passes add members to an axis;
    # a guessed constant here lied once already — physics/chemistry share 4 of 5, not 2 of 4)
    from concordance import grid
    a, b = grid.AXIS_DIMENSIONS["physics"], grid.AXIS_DIMENSIONS["chemistry"]
    expect = 2 + int(round(4 * (1 - len(a & b) / len(a | b))))
    assert chains.tensor_cost("physics", "physics") == 2                     # a lateral step within one axis
    assert chains.tensor_cost("physics", "chemistry") == expect              # the floor's 1 - Jaccard, scaled
    assert 2 < expect <= 6                                                   # an adjacent axis is dearer than lateral, cheaper than 'unspecified'(5)+auth
    assert chains.tensor_cost("physics", None) is None                       # no coordinates -> no terrain
    assert chains._card_axis({"shelf": "scripture"}) == "scripture_anchors"  # the Word sits on the grid (an alias)
    assert chains._card_axis({"shelf": "storyboards"}) is None               # a shelf with no axis has no terrain
    assert chains.tensor_cost("mathematics", "nutrition") is None            # no shared member -> no terrain between them


def test_everything_on_axes_the_ladder():
    """Matt, 2026-10-31: 'everything should be on axes'. Each rung, finest first, measured against the keeping."""
    ax = chains._card_axis
    # (1) source.domain leads — finer than the shelf (a 'calculations' card whose sealed domain is optics)
    assert ax({"shelf": "calculations", "source": {"domain": "optics"}}) == "optics"
    assert ax({"shelf": "history", "source": {"domain": "scripture"}}) == "scripture_anchors"
    # (2) the confessional tier names its ground when the domain does not (a church father on the classics shelf)
    assert ax({"shelf": "classics", "source": {"authority_tier": "father"}}) == "theology_doctrine"
    assert ax({"shelf": "classics", "source": {"authority_tier": "external_aligned"}}) == "philosophy"
    # (3) the shelf, through the keeping's wider vocabulary
    assert ax({"shelf": "trades", "source": {"domain": "trades"}}) == "construction"
    assert ax({"shelf": "dictionary", "source": {"domain": "linguistics"}}) == "linguistics"
    assert ax({"shelf": "rfcs"}) == "networking" and ax({"shelf": "hebrew_ot"}) == "scripture_anchors"
    # (4) a kind with no shelf at all (Easton's entries)
    assert ax({"kind": "easton", "category": "person"}) == "scripture_anchors"
    # (5) a cross-domain protocol's first axis; a receipt's sealed record
    assert ax({"kind": "protocol", "domains": ["theology_doctrine", "scripture"]}) == "theology_doctrine"
    assert ax({"kind": "receipt", "shelf": "seals",
               "extra": {"record": {"axis_coords": {"axis": "mathematics", "dimensions": ["reasoning"]}}}}) == "mathematics"
    assert ax({"kind": "receipt", "shelf": "seals",
               "extra": {"record": {"verifier_results": [{"name": "b", "data": {"domain": "chemistry"}}]}}}) == "chemistry"
    # (6) a connection card stands where its endpoint stands — one hop, never recursing
    g = {"p": {"id": "p", "shelf": "physics"},
         "c": {"id": "c", "kind": "connection", "shelf": "connections", "connections": [_edge("p")]},
         "cc": {"id": "cc", "kind": "connection", "shelf": "connections", "connections": [_edge("c")]}}
    assert ax(g["c"], g.get) == "physics"
    assert ax(g["cc"], g.get) is None                                        # two hops away: not inferred
    assert ax(g["c"]) is None                                                # no get_card -> no endpoint rung
    # containment is not subject: a literature card `part_of` its shelf-head spine (a META axis) stays an honest None
    g["spine"] = {"id": "spine", "shelf": "spine", "kind": "reference"}
    g["book"] = {"id": "book", "shelf": "gutenberg", "source": {"domain": "literature"},
                 "connections": [_edge("spine", rel="part_of")]}
    assert ax(g["spine"]) == "layer_zero_grounding"                          # the spine itself IS on the engine's ground
    assert ax(g["book"], g.get) is None                                      # but nothing inherits that ground
    # an honest gap: a subject with no axis yet is None, never forced onto a neighbour
    assert ax({"shelf": "gutenberg", "source": {"domain": "literature"}}) is None
    # codex is a MIXED shelf: the tiers place its theology; its engine-derived charts (e, the logarithm) stay None
    assert ax({"shelf": "codex", "source": {"authority_tier": "scripture"}}) == "scripture_anchors"
    assert ax({"shelf": "codex", "source": {"authority_tier": "engine_derived"}}) is None


def test_terrain_never_loses_a_road():
    """2026-10-31, live: with terrain on, e -> Euler's identity came back UNREACHABLE under the node bound — the
    terrain widened the frontier and the bound cut the road off. Information added must never lose a path."""
    g = {"a": _tcard("a", "physics", [_edge("b")]), "b": _tcard("b", "physics", [_edge("goal")]),
         "goal": _tcard("goal", "chemistry")}
    for i in range(40):                                       # a crowd of cheap lateral neighbours on a's axis
        g[f"n{i}"] = _tcard(f"n{i}", "physics", [_edge(f"n{(i + 1) % 40}")])
    crowd = lambda cid: [f"n{i}" for i in range(40)]
    roads = chains.shortest("a", "goal", get_card=g.get, max_nodes=6)
    both = chains.shortest("a", "goal", get_card=g.get, max_nodes=6, terrain_fn=crowd)
    assert roads and roads["cost"] == 2
    assert both and both["cost"] <= roads["cost"]           # terrain can only lower doubt, never lose the road
    # meetings too: `goal` is a sink, so roads alone have no THIRD card where a and goal meet; the terrain may
    # supply one (a lateral neighbour both can reach) — it adds, it never removes, and it never names a start
    assert chains.intersect_weighted("a", "goal", get_card=g.get, max_nodes=6) is None
    w = chains.intersect_weighted("a", "goal", get_card=g.get, max_nodes=60, terrain_fn=crowd)
    assert w is None or w["at"] not in ("a", "goal")


def test_a_hub_costs_the_bits_it_takes_to_leave_it():
    """Measured 2026-10-31: the keeping's cards carry a median of 1 road (p99 = 3); a card with more than 4 exits is
    a hub, and leaving it — or meeting at it — costs log2(d/4) bits. Live case: the floor of discovery, which
    every work paves, won every meeting by fewest hops."""
    g = {"a": _card("a", [_edge("hub"), _edge("l1")]), "goal": _card("goal", [])}
    g["hub"] = _card("hub", [_edge(f"x{i}") for i in range(99)] + [_edge("goal")])   # 100 exits -> ~5 bits
    for i in range(99):
        g[f"x{i}"] = _card(f"x{i}", [])
    g["l1"], g["l2"], g["l3"] = _card("l1", [_edge("l2")]), _card("l2", [_edge("l3")]), _card("l3", [_edge("goal")])
    assert chains._hub_bits(g["hub"]) == 5 and chains._hub_bits(g["l1"]) == 0 and chains._hub_bits(g["a"]) == 0
    out = chains.shortest("a", "goal", get_card=g.get)
    assert out["path"] == ["a", "l1", "l2", "l3", "goal"]        # 4 proven steps (4) beat 2 steps through the hub (2 + 5)
    # a meeting at a hub is dearer than a meeting at a specific joint by the hub's bits
    g["b"] = _card("b", [_edge("hub"), _edge("l3")])
    w = chains.intersect_weighted("a", "b", get_card=g.get)
    assert w["at"] == "l3" and w["joint_bits"] == 0


def test_the_keepings_road_vocabulary_is_priced_from_the_evidence():
    """Measured histogram (2026-10-31): the labels the keeping actually uses, banded by the claim each makes.
    An inverse the loader grafts is priced as its forward."""
    cost = lambda rel: chains._REL_COST.get(rel, chains._REL_COST_DEFAULT)
    assert cost("comments_on") == cost("proof_text") == cost("charts") == 1            # the text itself / sealed
    assert cost("cites") == cost("speaks_to") == cost("paves") == 2                   # declared and checkable
    assert cost("bridges") == cost("same_form") == cost("see_also") == 3              # "RESONANCE, not proof"
    assert cost("member_of") == 5 and cost("never_seen_label") == 5                   # containment / unasserted
    assert cost("charted_by") == cost("charts") and cost("paved_by") == cost("paves") and cost("has_open_end") == cost("open_end_of")


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
