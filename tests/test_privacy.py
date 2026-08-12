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
    # NON-COMMERCIAL is disallowed too (CC-BY-NC* forbids the free-to-all use that is the point)
    assert not corpus.is_public({**pub, "source": {"label": "some source (CC-BY-NC 4.0)"}})
    assert not corpus.is_public({**pub, "extra": {"license": "CC BY-NC-SA 3.0"}})
    assert not corpus.is_public({**pub, "source": {"label": "a dataset (non-commercial use only)"}})
    # OEIS (CC-BY-NC-SA) carries only its SOURCE NAME in the label, never the license string — the
    # live leak found in the pre-launch audit (6,000 cards public). Caught by source name now.
    assert not corpus.is_public({**pub, "shelf": "oeis", "source": {
        "label": "OEIS — On-Line Encyclopedia of Integer Sequences (oeis.org)",
        "url": "https://oeis.org/A000001"}}), "OEIS is CC-BY-NC-SA — it must be withheld"
    # attribution-only and public-domain licenses ARE served (CC-BY is not CC-BY-SA/NC)
    assert corpus.is_public({**pub, "source": {"label": "GeoNames (CC-BY 4.0)"}})
    assert corpus.is_public({**pub, "source": {"label": "STEPBible Strong's (CC-BY, Tyndale House)"}})
    assert corpus.is_public({**pub, "source": {"label": "NNDC nuclide data (public domain)"}})
    assert corpus.is_public({**pub, "extra": {"license": "CC0"}})
    # the new permissive sources serve: ECB reference rates (attribution) + IANA tzdata (PD)
    assert corpus.is_public({**pub, "source": {"label": "European Central Bank — euro foreign "
                                               "exchange reference rates (free to use with attribution to the ECB)"}})
    assert corpus.is_public({**pub, "source": {"label": "IANA Time Zone Database (tzdata) — public domain"}})
    # a generated card is never served publicly; the conduit's generated:false rides through
    assert not corpus.is_public({**pub, "generated": True})
    assert corpus.is_public({**pub, "generated": False})


def test_no_generator_mints_a_disallowed_license():
    """The mint-side mirror of is_public: scan every source_label literal in tools/card_sources.py
    and confirm none carries a share-alike or non-commercial license. The two boundaries (mint and
    serve) must agree — a source clean to mint must be clean to serve. Guards against a future
    generator quietly sourcing a CC-BY-SA/NC dataset (e.g. the CC-BY-SA-3.0 elements.db)."""
    import re
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "tools" / "card_sources.py").read_text(encoding="utf-8")
    bad = [m.group(1) for m in re.finditer(r'source_label="([^"]*)"', src)
           if corpus._is_share_alike({"source": {"label": m.group(1)}})]
    assert not bad, "generator mints a disallowed-license source_label:\n" + "\n".join(bad)


import pytest


@pytest.mark.parametrize("module,out_file,spine", [
    ("card_comms", "comms_cards.jsonl", "card_spine_comms"),
    ("card_firstaid", "firstaid_cards.jsonl", "card_spine_firstaid"),
    ("card_navigation", "navigation_cards.jsonl", "card_spine_navigation"),
    ("card_power", "power_cards.jsonl", "card_spine_power"),
    ("card_sanitation", "sanitation_cards.jsonl", "card_spine_sanitation"),
    ("card_water", "water_cards.jsonl", "card_spine_water"),
    ("card_food", "food_cards.jsonl", "card_spine_food"),
])
def test_field_shelf_is_clean_public_and_unorphaned(module, out_file, spine, tmp_path, monkeypatch):
    """Every authored field-reference shelf (the practical library that serves the off-grid + mesh —
    communications, first aid, navigation, off-grid power) is PD field reference: every card must be
    PUBLIC, clean-licensed (no share-alike/NC), and member_of its spine (no orphan). Runs the real
    emitter hermetically into a temp dir and proves the OUTPUT, not the code — so a future edit that
    quietly sources a disallowed license, or drops a card's spine link, fails the gate."""
    import importlib
    import json
    import sys
    from pathlib import Path
    monkeypatch.chdir(tmp_path)
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    mod = importlib.import_module(module)
    assert mod.main() == 0
    cards = [json.loads(ln) for ln in
             (tmp_path / "data" / out_file).read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(cards) >= 10 and cards[0]["id"] == spine
    for c in cards:
        assert corpus.is_public(c), f"{c['id']} is not public"
        assert not corpus._is_share_alike(c), f"{c['id']} carries a disallowed license"
        if c["id"] != spine:
            assert any(e.get("to_card_id") == spine for e in c["connections"]), \
                f"{c['id']} is an orphan (not member_of {spine})"


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


def test_pd_decision_ships_only_verifiable_public_domain():
    """The age-PD acquisition gate (store_book._pd_decision) is conservative and auditable: it ships
    a book only when the Archive marks it NOT_IN_COPYRIGHT or it was published before 1929, and it
    REFUSES an in-copyright work or one under a restrictive (CC) license. Strict PD-only, at the
    mint — the handyman/trades shelf must never carry something the copyright has not yet released."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import store_book as sb

    def d(md):
        return sb._pd_decision({"metadata": md})

    assert d({"possible-copyright-status": "NOT_IN_COPYRIGHT", "year": "1955"})[0]  # Archive's PD mark wins
    ok, yr, _ = d({"date": "Boston, 1907"}); assert ok and yr == "1907"             # age basis, year parsed
    assert d({"year": "1928"})[0]                                                   # ceiling year is PD
    assert not d({"year": "1945"})[0]                                               # still in copyright
    assert not d({"possible-copyright-status": "IN_COPYRIGHT", "year": "1900"})[0]  # explicit copyright wins
    assert not d({"licenseurl": "https://creativecommons.org/licenses/by/4.0/", "year": "1850"})[0]  # licensed != PD
    assert not d({})[0]                                                             # no basis -> refused
    assert d({"licenseurl": "https://creativecommons.org/publicdomain/mark/1.0/", "year": "1900"})[0]  # PD mark ok


def test_gen_ark_pd_cards_are_clean_public_and_carry_pd_basis(tmp_path, monkeypatch):
    """gen_ark_pd cards the age-PD trades shelf from docs_pd: every card PUBLIC, clean-licensed,
    member_of card_spine_arkpd, id-namespaced card_src_pd_* (never colliding with the federal
    card_src_fed_*), carrying the PD basis so provenance stays auditable and un-blurred with the
    17-USC-105 federal shelf. Runs the real generator against a hermetic docs_pd, proving OUTPUT."""
    import importlib
    import sqlite3
    import sys
    from pathlib import Path
    ark = tmp_path / "ark"
    (ark / "archive_org").mkdir(parents=True)
    con = sqlite3.connect(str(ark / "archive_org" / "texts.db"))
    con.execute("create table docs_pd (identifier text primary key, title text, query text, "
                "raw_bytes integer, gz blob, stored_at text, url text, sha256 text, "
                "pd_year text, pd_basis text)")
    con.execute("insert into docs_pd values (?,?,?,?,?,?,?,?,?,?)",
                ("audels01", "Audels Carpenters and Builders Guide",
                 "subject:(carpentry) AND mediatype:(texts)", 123456, b"",
                 "2026-08-11T00:00:00Z", "https://archive.org/download/audels01/x_djvu.txt",
                 "abc123", "1923", "public domain by copyright expiry (published 1923, pre-1929)"))
    con.execute("insert into docs_pd values (?,?,?,?,?,?,?,?,?,?)",
                ("farmmanual", "The Farmer's Every-Day Book",
                 "subject:(agriculture) AND mediatype:(texts)", 67890, b"",
                 "2026-08-11T00:00:00Z", "https://archive.org/download/farmmanual/y_djvu.txt",
                 "def456", "1890", "public domain by copyright expiry (published 1890, pre-1929)"))
    con.commit(); con.close()
    monkeypatch.setenv("CONCORDANCE_ARK_BASE", str(ark))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import card_sources
    importlib.reload(card_sources)
    cards = list(card_sources.gen_ark_pd())
    assert len(cards) == 2
    assert all(c["id"].startswith("card_src_pd_") for c in cards)
    for c in cards:
        assert corpus.is_public(c), f"{c['id']} is not public"
        assert not corpus._is_share_alike(c), f"{c['id']} carries a disallowed license"
        assert any(e.get("to_card_id") == "card_spine_arkpd" for e in c["connections"]), \
            f"{c['id']} is not member_of the trades spine"
        assert c["extra"]["pd_basis"], f"{c['id']} lost its PD basis"
    shelves = {c["shelf"] for c in cards}
    assert "practical" in shelves and "agriculture" in shelves  # carpentry->practical, agri->agriculture
