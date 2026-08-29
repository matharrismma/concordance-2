"""Clean URLs — "2 paths on everything" (Matt, 2026-08-22).

Every page must answer to BOTH its clean address (`/golf`) and its old `.html` address
(`/golf.html`), with no forced redirect — whichever a visitor types is served. And the clean-URL
fallback must never become a traversal or content-type hole: an escaping path returns nothing, and
a missing *extensioned* asset (a stray `.css`) is not retried as `.html`.

Tests resolve_site_file() directly — the pure resolver the static handler delegates to — so the
behaviour is proven in milliseconds without warming the whole corpus-backed server.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance.web.api import resolve_site_file, home_for, redirect_for, MOVED_TO_ORG  # noqa: E402

SITE = (ROOT / "site").resolve()


# ---- Domain Sort Part 2: family/teaching pages 301 to .org on the .com surface ----

def test_family_pages_redirect_to_org_on_secular():
    assert redirect_for("secular", "/bible") == "https://narrowhighway.org/bible"
    assert redirect_for("secular", "/bible.html") == "https://narrowhighway.org/bible.html"
    assert redirect_for("secular", "/read") == "https://narrowhighway.org/read"
    assert redirect_for("secular", "/encyclopedia") == "https://narrowhighway.org/encyclopedia"


def test_verification_pages_stay_on_com():
    for p in ("/checkit", "/", "/proof", "/about", "/connect", "/identity"):
        assert redirect_for("secular", p) is None, p


def test_witness_surface_never_redirects():
    for p in ("/bible", "/read", "/encyclopedia", "/"):
        assert redirect_for("witness", p) is None, p


def test_agent_endpoints_and_ambiguous_pages_do_not_move():
    # JSON agent endpoints (characters/prophecy/... answer application/json) must NOT move; nor the
    # crisis-first page, nor 404-on-org names.
    for p in ("characters", "prophecy", "harmony", "timeline", "backmatter", "places", "narratives",
              "teachings", "seeds", "journal", "steward", "situations", "voices", "corpus",
              "community", "map", "profile", "almanac"):
        assert p not in MOVED_TO_ORG, p


# ---- the Domain Sort flip: .com homepage IS the auditor; .org and /index.html unchanged ----

def test_secular_bare_home_flips_to_checkit():
    assert home_for("secular", SITE, "/") == "/checkit"


def test_flip_is_only_the_bare_root():
    # /index.html still serves the desk; deep paths and clean URLs are untouched
    assert home_for("secular", SITE, "/index.html") == "/index.html"
    assert home_for("secular", SITE, "/golf") == "/golf"
    assert home_for("secular", SITE, "/about") == "/about"


def test_witness_home_is_untouched():
    assert home_for("witness", SITE, "/") == "/"
    assert home_for("witness", SITE, "/index.html") == "/index.html"


def test_clean_path_serves_the_html_twin():
    for name in ("golf", "grappling", "halls"):
        assert resolve_site_file(SITE, "/" + name) == (SITE / (name + ".html")).resolve(), name


def test_explicit_html_still_resolves():
    # the old address must keep working — two paths, both served, no redirect
    for name in ("golf", "grappling", "halls"):
        assert resolve_site_file(SITE, "/" + name + ".html") == (SITE / (name + ".html")).resolve()


def test_root_is_index():
    assert resolve_site_file(SITE, "/") == (SITE / "index.html").resolve()


def test_missing_returns_none():
    assert resolve_site_file(SITE, "/no-such-hall") is None
    assert resolve_site_file(SITE, "/no-such-hall.html") is None


def test_extensioned_miss_is_not_retried_as_html():
    # a stray /x.css must 404, never resolve to x.css.html (content-type safety)
    assert resolve_site_file(SITE, "/definitely-missing.css") is None


def test_traversal_is_blocked():
    for attack in ("/../secret", "/golf/../../api.py", "/../../etc/passwd", "/..%2f..%2fapi.py"):
        assert resolve_site_file(SITE, attack) is None, attack


if __name__ == "__main__":
    import pytest
    sys.exit(int(pytest.main([__file__, "-q"])))
