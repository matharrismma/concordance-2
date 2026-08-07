"""Privacy regression — non-public cards must NEVER surface on any corpus read path.

This guards the fix for the live leak where private/public_review cards (the operator's
unpublished work) were served on the public .com because the corpus filters used a denylist
(archived/quarantine only) instead of the is_public allowlist. Hermetic; no network/disk.
"""
from concordance import corpus, graph

NONPUBLIC = ("private", "public_review", "archived", "quarantine")


def _card(cid, stage="public", shelf="codex", title=None):
    return {"id": cid, "kind": "note", "shelf": shelf, "title": title or cid,
            "body": f"{cid} distinctive body text", "lifecycle_stage": stage,
            "source": {"authority_tier": "scripture"}}


def _setup(cards):
    corpus._DEFAULT = corpus.Corpus({c["id"]: c for c in cards})
    graph._GRAPH = None


def teardown_function(_fn):
    corpus._DEFAULT = None
    graph._GRAPH = None


def _fixture():
    return [
        _card("pub1", "public", title="Alpha public"),
        _card("feat1", "featured", title="Beta featured"),
        _card("priv1", "private", shelf="animation", title="Gamma secret storyboard"),
        _card("rev1", "public_review", title="Delta pending review"),
        _card("arch1", "archived", title="Epsilon archived"),
        _card("quar1", "quarantine", title="Zeta quarantined"),
    ]


def _fixture_with_retracted():
    fx = _fixture()
    r = _card("retr1", "public", title="Eta retracted")  # public stage BUT retracted
    r["retracted"] = True
    fx.append(r)
    return fx


def test_is_public_is_an_allowlist():
    assert corpus.is_public({"lifecycle_stage": "public"})
    assert corpus.is_public({"lifecycle_stage": "featured"})
    assert corpus.is_public({})  # unset defaults to public
    for s in NONPUBLIC:
        assert not corpus.is_public({"lifecycle_stage": s}), s
    assert not corpus.is_public({"lifecycle_stage": "public", "retracted": True})
    assert not corpus.is_public("not a dict")


def test_share_alike_and_generated_are_withheld():
    """LICENSE + conduit guards (red team 2026-08-06, Matt: "drop what could get us in trouble").
    Share-alike (CC-BY-SA) content is a legal issue to REDISTRIBUTE — its copyleft could pull the
    whole corpus under SA — so it is withheld from every public read path even at stage `public`.
    PD / CC0 / CC-BY (attribution-only) stay, credited by each card's source label. And a generated
    card never serves publicly (the conduit contract). Both guards sit ON TOP of the stage allowlist."""
    pub = {"lifecycle_stage": "public"}
    # share-alike, whether the marker rides on the source label or extra.license
    assert not corpus.is_public({**pub, "source": {"label": "HYG stellar database (CC-BY-SA, D. Nash)"}})
    assert not corpus.is_public({**pub, "source": {"label": "PHOIBLE 2.0 + Glottolog (CC-BY-SA 3.0 / CC-BY 4.0)"}})
    assert not corpus.is_public({**pub, "extra": {"license": "CC-BY-SA 4.0"}})
    assert not corpus.is_public({**pub, "source": {"label": "something (Share-Alike)"}})
    # attribution-only and public-domain licenses ARE served (CC-BY is not CC-BY-SA)
    assert corpus.is_public({**pub, "source": {"label": "GeoNames (CC-BY 4.0)"}})
    assert corpus.is_public({**pub, "source": {"label": "STEPBible Strong's (CC-BY, Tyndale House)"}})
    assert corpus.is_public({**pub, "source": {"label": "NNDC nuclide data (public domain)"}})
    assert corpus.is_public({**pub, "extra": {"license": "CC0"}})
    # a generated card is never served publicly; the conduit's generated:false rides through
    assert not corpus.is_public({**pub, "generated": True})
    assert corpus.is_public({**pub, "generated": False})


def test_a_frozen_stub_still_withholds_share_alike():
    """A frozen-shelf STUB drops `source`/`extra` to save memory, so is_public() cannot read the
    license off it — it carries a precomputed `share_alike` bool instead, honoured first. Found LIVE
    (2026-08-06): without this, /search (which runs over stubs) served CC-BY-SA HYG star cards that
    card_get correctly withheld — the guard reached full cards but not the stub the index is built on."""
    stub_sa = {"id": "card_src_star_x", "lifecycle_stage": "public", "shelf": "astronomy",
               "generated": False, "share_alike": True}          # a stub of an HYG (CC-BY-SA) card
    assert corpus.is_public(stub_sa) is False
    stub_ok = {"id": "y", "lifecycle_stage": "public", "shelf": "astronomy",
               "generated": False, "share_alike": False}          # a stub of an ordinary card
    assert corpus.is_public(stub_ok) is True
    # the precomputed flag wins over an (absent) label — a stub never has a source to scan
    assert corpus._is_share_alike({"share_alike": True}) is True
    assert corpus._is_share_alike({"share_alike": False, "source": {"label": "x (CC-BY-SA)"}}) is False


def test_get_card_hides_nonpublic():
    _setup(_fixture_with_retracted())
    assert corpus.get_card("pub1") is not None
    assert corpus.get_card("feat1") is not None
    for cid in ("priv1", "rev1", "arch1", "quar1", "retr1"):
        assert corpus.get_card(cid) is None, cid


def test_search_never_surfaces_nonpublic():
    _setup(_fixture())
    # distinctive tokens from the non-public titles/bodies must return nothing non-public
    for tok in ("secret", "storyboard", "pending", "Delta", "quarantined", "Epsilon", "priv1", "rev1"):
        for h in corpus.search(tok, limit=20):
            assert (h.get("lifecycle_stage") or "public") in ("public", "featured"), (tok, h.get("id"))


def test_browse_returns_only_public():
    _setup(_fixture())
    ids = {c["id"] for c in corpus.browse(limit=100)["cards"]}
    assert ids == {"pub1", "feat1"}


def test_daily_never_returns_nonpublic():
    _setup(_fixture())
    for i in range(80):
        d = corpus.daily(seed=f"seed-{i}")
        if d is not None:
            assert (d.get("lifecycle_stage") or "public") in ("public", "featured")


def test_locate_and_connections_hide_nonpublic():
    _setup(_fixture())
    # exact-id locate must not reveal a private card
    for cid in ("priv1", "rev1", "arch1"):
        matches = corpus.locate(cid)["matches"]
        assert all(m["id"] != cid for m in matches), cid
    # connections on a non-public id must be None (as if it doesn't exist)
    assert corpus.connections("priv1") is None
    assert corpus.connections("rev1") is None


def test_stats_and_health_count_public_only():
    _setup(_fixture())
    assert corpus.stats()["total"] == 2       # pub1 + feat1 only
    assert corpus.health()["total"] == 2


def test_graph_shares_the_same_predicate():
    # graph.is_public must be corpus.is_public (one source of truth)
    assert graph._is_public({"lifecycle_stage": "private"}) is False
    assert graph._is_public({"lifecycle_stage": "public"}) is True
    _setup(_fixture())
    assert graph.neighborhood("priv1") is None
