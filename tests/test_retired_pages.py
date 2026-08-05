"""A retired page must say where its content WENT — and the destination must honour what it was
asked for.

Two 1.0 pages on narrowhighway.tv were answering 404: /daily.html (70 requests) and /hymns.html
(63), every one with an empty referrer — bookmarks, crawlers and old indexes still asking. A 404
says "no such thing ever existed", which is false, and the reader leaves with nothing.

The second half of this test is the one that matters. /canon.html already 301s to /bible.html
having DROPPED its `?ref=` — so 2,124 card citations land on a generic Bible page, plausibly and
wrongly, and nothing reports it. A redirect that carries a query parameter to a page which ignores
query parameters is that same failure. Every destination page here is checked for a control that
actually reads the URL, so the class of bug cannot come back through a new redirect.

Runs over a REAL socket: the redirect is emitted by the request handler, so a dispatch-level test
would pass while the wire stayed silent.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import http.client
import os
import re
import sys
import tempfile
import threading
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

SITE = ROOT / "site"


@pytest.fixture(scope="module")
def server():
    from concordance.web import api
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    httpd = api.build_server(host="127.0.0.1", port=0, surface="secular",
                            site_dir=str(SITE), warm=False)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield ("127.0.0.1", httpd.server_address[1])
    httpd.shutdown()


def _raw_get(addr, path):
    """No redirect-following — the status and Location ARE the thing under test."""
    conn = http.client.HTTPConnection(addr[0], addr[1], timeout=30)
    try:
        conn.request("GET", path)
        r = conn.getresponse()
        r.read()
        return r.status, {k.lower(): v for k, v in r.getheaders()}
    finally:
        conn.close()


CARD = {"id": "card_test_daily", "title": "A card for today", "body": "worked and kept",
        "kind": "reference", "shelf": "test", "source": {"label": "test", "url": ""}}


def _with_a_daily_card(fn):
    """The tests run against an empty temp keeping, so the daily card is supplied. What is under
    test is the wire — the status, the Location, and the freshness — not the corpus."""
    from concordance import corpus
    old_daily, old_get = corpus.daily, corpus.get_card
    corpus.daily = lambda seed=None: dict(CARD)
    corpus.get_card = lambda cid: dict(CARD) if cid == CARD["id"] else old_get(cid)
    try:
        return fn()
    finally:
        corpus.daily, corpus.get_card = old_daily, old_get


def test_daily_html_goes_to_todays_card(server):
    """302, never 301: today's card is a different card tomorrow, and a permanent redirect would
    sit in browser caches pointing at one frozen day forever."""
    def check():
        status, h = _raw_get(server, "/daily.html")
        assert status == 302, f"expected a temporary redirect, got {status}"
        loc = h.get("location", "")
        assert loc == "/card/" + CARD["id"], f"daily.html must land on today's permalink, got {loc!r}"
        assert "no-store" in h.get("cache-control", ""), "a computed redirect must not be cached"
        status2, _ = _raw_get(server, loc)          # and the destination must actually answer
        assert status2 == 200, f"daily.html redirects to {loc} which answers {status2}"
    _with_a_daily_card(check)


def test_daily_html_says_which_side_failed_when_the_keeping_is_empty(server):
    """With nothing to send, the answer names OUR lack — never 'no such page', which would blame
    the reader's URL for our empty shelf.

    The empty keeping is FORCED here rather than assumed. An earlier version of this test relied
    on the fixture's temp data dir being empty; it passed alone and failed in the full run, where
    another test had already warmed the corpus. A test that asserts a fact about its environment
    is testing the environment.
    """
    from concordance import corpus
    old = corpus.daily
    corpus.daily = lambda seed=None: None
    try:
        status, _ = _raw_get(server, "/daily.html")
    finally:
        corpus.daily = old
    assert status == 404


def test_hymns_html_goes_to_the_hymn_shelf(server):
    status, h = _raw_get(server, "/hymns.html")
    assert status == 301, f"expected a permanent redirect, got {status}"
    assert h.get("location") == "/?q=hymns"


def test_the_four_pages_of_the_corpus_still_answer(server):
    """library · catalog · codex · works were four pages doing one job. Each is a section of the
    Corpus now, and each old address still resolves to its own section."""
    for path, dest in (("/library.html", "/"), ("/catalog.html", "/"),
                       ("/codex.html", "/"), ("/works.html", "/proof.html")):
        status, h = _raw_get(server, path)
        assert status == 301, f"{path} answers {status}"
        assert h.get("location", "") == dest, f"{path} -> {h.get('location')}"


def test_a_retired_page_carries_what_it_was_asked_for(server):
    """The /canon.html failure, refused at the source: a redirect that drops the query lands the
    reader on a plausible page with the reference thrown away."""
    status, h = _raw_get(server, "/library.html?q=Aaron&shelf=hymns")
    assert status == 301
    loc = h.get("location", "")
    assert "q=Aaron" in loc and "shelf=hymns" in loc, f"the query was dropped: {loc}"
    # and the incoming side wins over the destination's own default
    status, h = _raw_get(server, "/codex.html?section=drawers")
    assert h.get("location", "").count("section=") == 1, "merged query has a duplicated key"
    assert "section=drawers" in h.get("location", ""), "the link's own query was dropped"


def test_no_retired_page_points_at_another_retired_page(server):
    """A chain through a page that is itself gone is a hop nobody can follow twice. Every
    destination has to be the real one."""
    from concordance.web import api
    for src, dest in api._RETIRED.items():
        head = dest.split("?")[0]
        assert head not in api._RETIRED, f"{src} -> {dest}, which is itself retired"


def test_no_retired_page_still_404s(server):
    from concordance.web import api
    for path in api._RETIRED:
        status, _ = _raw_get(server, path)
        assert status in (301, 302), f"{path} answers {status} — a retired page is not a 404"


# --- the guard that matters: a destination must honour what it was sent ------------------------

def _page_honours_params(page: str) -> bool:
    """A page honours a deep link if it defines its own hook, or if it loads the shared adopter
    AND has a control the adopter can find."""
    fp = SITE / (page or "index.html")          # "/" is the desk
    if not fp.is_file():
        return False
    html = fp.read_text(encoding="utf-8", errors="replace")
    if "NHDeepLink" in html:
        return True
    if "nh-home.js" not in html:
        return False
    return bool(re.search(r'id=["\'](q|search)["\']|data-deeplink|type=["\']search["\']', html))


def test_every_redirect_target_honours_its_query(server):
    """The /canon.html failure, made impossible to repeat: if we send a reader to a URL carrying a
    parameter, the page there has to read it."""
    from concordance.web import api
    broken = []
    for src, dest in api._RETIRED.items():
        u = urlparse(dest)
        if not u.query:
            continue
        page = u.path.lstrip("/")
        if not _page_honours_params(page):
            broken.append(f"{src} -> {dest} ({page} ignores the URL)")
    assert not broken, ("a redirect carries a parameter to a page that drops it — the reader lands "
                        "somewhere plausible and wrong: " + "; ".join(broken))


def test_the_shared_adopter_is_on_the_pages_that_are_cited():
    """The dictionary is the destination of 2,619 card citations and the library of the hymn
    redirect. Both must read the URL, or every one of those links silently shows the unfiltered
    page."""
    for page in ("characters.html", "index.html"):
        assert _page_honours_params(page), f"{page} does not honour a deep link"


def test_the_shell_scripts_are_not_served_stale():
    """The adopter shipped, the redirect worked, and the page still did nothing — the service
    worker had handed the browser yesterday's nh-home.js from stale-while-revalidate, and the new
    one only took effect on the NEXT load. A reader following a citation gets one shot; the bytes
    that decide whether it resolves cannot be one load behind."""
    sw = (SITE / "sw.js").read_text(encoding="utf-8")
    assert "SHELL" in sw, "sw.js does not distinguish the shell scripts"
    m = re.search(r"const SHELL = \[(.*?)\]", sw, re.S)
    assert m, "SHELL list not found"
    listed = set(re.findall(r"'/([\w.-]+)'", m.group(1)))
    assert "nh-home.js" in listed, "the shared shell is still stale-while-revalidate"
    assert re.search(r"isDoc \|\| isData \|\| isShell", sw), "the shell is not network-first"


def test_the_adopter_waits_for_the_option_it_needs():
    """The shelf dropdown is filled from /cards/stats AFTER load. Setting a value on an empty
    <select> is discarded silently by the browser — so the adopter must wait for its own option,
    not merely for the element."""
    js = (SITE / "nh-home.js").read_text(encoding="utf-8")
    assert "NHDeepLink" in js, "the shared adopter is missing from the shared shell"
    assert re.search(r"o\.value === shelf", js), "the adopter does not wait for its own option"


if __name__ == "__main__":
    import concordance.web.api as _api  # noqa: F401
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    from concordance.web import api as _a
    httpd = _a.build_server(host="127.0.0.1", port=0, surface="secular",
                            site_dir=str(SITE), warm=False)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    addr = ("127.0.0.1", httpd.server_address[1])
    fns = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for name, fn in fns:
        fn(addr) if fn.__code__.co_argcount else fn()
        print(f"  ok  {name}")
    httpd.shutdown()
    print(f"\n{len(fns)} retired-page tests passed — no page 404s, and every destination reads "
          f"what it was sent.")
