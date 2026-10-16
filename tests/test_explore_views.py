"""explore.html is the ONE visualization surface (issue #16, 2026-10-16).

The six single-view static pages (calculations / one_body / spiral / domains / bridges / strategy)
were explore.html's own layouts drawn twice, each by a generator nothing ran. Each is retired to ITS
view, and a view is addressable by URL — so an old bookmark lands on the same picture, carrying
whatever it was asked for."""
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from concordance.web import api

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
EXPLORE = (SITE / "explore.html").read_text(encoding="utf-8")

VIEWS = {
    "/calculations.html": "wheel",
    "/one_body.html": "onebody",
    "/spiral.html": "spiral",
    "/domains.html": "domains",
    "/bridges.html": "bridges",
    "/strategy.html": "strategy",
}


@pytest.mark.parametrize("path,view", sorted(VIEWS.items()))
def test_each_retired_view_lands_on_a_page_that_ships(path, view):
    dest = api._RETIRED[path]
    u = urlparse(dest)
    assert (SITE / u.path.lstrip("/")).is_file(), f"{path} -> {dest}: no such page in site/"
    assert parse_qs(u.query).get("view") == [view], f"{path} -> {dest}: not its own view"
    assert not (SITE / path.lstrip("/")).exists(), f"{path} still ships as a file"


@pytest.mark.parametrize("view", sorted(set(VIEWS.values())))
def test_explore_has_a_tab_and_a_renderer_for_each_view(view):
    assert re.search(rf"data-l={view}[\s>]", EXPLORE), f"no tab for {view}"
    assert f"{view}:render" in EXPLORE, f"no RENDER entry for {view}"   # the dispatch table


def test_explore_reads_the_view_from_its_url():
    """The page defines its own deep-link hook (what test_retired_pages' honours-the-query guard
    looks for), and reads ?view= — the parameter every retired entry sends."""
    assert "NHDeepLink" in EXPLORE
    assert "get('view')" in EXPLORE


def test_the_generator_and_the_page_agree():
    gen = (ROOT / "tools" / "atlas_explore.py").read_text(encoding="utf-8")
    assert "NHDeepLink" in gen and "get('view')" in gen, "explore.html drifted from its generator"


def test_the_query_rides_along_to_the_view():
    assert api._retire_to("/spiral.html", "") == "/explore.html?view=spiral"
    loc = api._retire_to("/strategy.html", "q=Lincoln&shelf=war")
    assert urlparse(loc).path == "/explore.html"
    assert parse_qs(urlparse(loc).query) == {"view": ["strategy"], "q": ["Lincoln"], "shelf": ["war"]}
    # the incoming side wins — a link that names a view means that view
    assert parse_qs(urlparse(api._retire_to("/spiral.html", "view=domains")).query)["view"] == ["domains"]
