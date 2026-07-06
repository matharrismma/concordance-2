"""Graph builder guardrails — the map shows only FOUND, PUBLIC connections, each sealed.

Hermetic: builds a tiny fixture corpus and asserts the three views. No network, no disk.
"""
from concordance import corpus, graph


def _note(cid, shelf="codex", tier="scripture", stage="public"):
    return {"id": cid, "kind": "note", "shelf": shelf, "title": cid, "body": cid + " body",
            "box": "", "source": {"authority_tier": tier}, "lifecycle_stage": stage}


def _conn(cid, left, right, rel="see_also", stage="public"):
    return {"id": cid, "kind": "connection", "shelf": "connections", "title": cid,
            "body": "", "lifecycle_stage": stage,
            "extra": {"left_card_id": left, "right_card_id": right, "relationship_kind": rel}}


def _setup(cards):
    corpus._DEFAULT = corpus.Corpus({c["id"]: c for c in cards})
    graph._GRAPH = None


def teardown_function(_fn):
    corpus._DEFAULT = None
    graph._GRAPH = None


def _fixture():
    return [
        _note("n1", "codex"), _note("n2", "codex"),
        _note("n3", "classics"), _note("n4", "classics"),
        _note("priv", "codex", stage="private"),          # must be excluded everywhere
        _conn("c1", "n1", "n2", "cites"),
        _conn("c2", "n1", "n3", "proof_text"),
        _conn("c3", "n3", "n4", "see_also"),
        _conn("cbad", "n1", "missing"),                    # dangling → dropped
        _conn("cpriv", "n1", "priv"),                      # touches private → dropped
        _conn("cq", "n1", "n2", "cites", stage="quarantine"),  # non-public edge → dropped
    ]


def test_overview_counts_and_excludes_private():
    _setup(_fixture())
    ov = graph.overview()
    assert ov["scope"] == "overview"
    assert ov["total_nodes"] == 4          # priv excluded
    assert ov["total_edges"] == 3          # cbad, cpriv, cq dropped
    shelves = {c["shelf"]: c["count"] for c in ov["clusters"]}
    assert shelves == {"codex": 2, "classics": 2}
    # inter-shelf link weights: codex-codex (c1), codex-classics (c2), classics-classics (c3)
    weights = {tuple(sorted((l["source"], l["target"]))): l["weight"] for l in ov["links"]}
    assert weights[("codex", "codex")] == 1
    assert weights[("classics", "codex")] == 1
    assert weights[("classics", "classics")] == 1


def test_connection_cards_are_never_nodes():
    _setup(_fixture())
    sh = graph.shelf_graph("classics")
    ids = {n["id"] for n in sh["nodes"]}
    assert not any(i.startswith("c") and i not in ("classics",) for i in ids if i in ("c1", "c2", "c3"))
    assert ids <= {"n1", "n2", "n3", "n4"}   # only note nodes, never connection cards
    assert "priv" not in ids


def test_neighborhood_has_center_neighbors_and_seals():
    _setup(_fixture())
    nb = graph.neighborhood("n1")
    assert nb is not None and nb["center"] == "n1"
    assert nb["total"] == 2                 # n2 (cites) + n3 (proof_text); priv/missing excluded
    seals = {l["seal"] for l in nb["links"]}
    assert seals == {"c1", "c2"}            # every edge links to its connection-card seal
    kinds = {l["kind"] for l in nb["links"]}
    assert kinds == {"cites", "proof_text"}


def test_neighborhood_none_for_missing_or_private():
    _setup(_fixture())
    assert graph.neighborhood("missing") is None
    assert graph.neighborhood("priv") is None     # private card is not a public node
    assert graph.neighborhood("") is None


def test_shelf_embeds_cross_shelf_neighbors():
    _setup(_fixture())
    sh = graph.shelf_graph("classics")
    ids = {n["id"] for n in sh["nodes"]}
    assert {"n3", "n4"} <= ids              # the shelf members
    assert "n1" in ids                      # pulled in as a neighbor of n3 (c2)
    assert sh["total_in_shelf"] == 2
