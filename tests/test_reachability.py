"""Reachability — a capability nobody can reach is not shipped.

GAPS.md G4, measured 2026-07-29: 51 of 140 API routes were referenced by no page at all, and 8
pages (including `mesh.html`, a V1 capstone) were linked from nowhere. Correct server-side and
invisible to the person is the failure this project has hit more than any other — five times in
one night in July, and this was the sixth shape of it.

So reachability becomes a gate, with the same shape as the route goldens: every route is either
REACHED by a page or DECLARED agent-only; every page is either LINKED from another page or
DECLARED deliberately unlisted. Both declarations live here, in the open, with reasons — so the
next person adding a route has to say which it is, and drift fails loudly instead of quietly
burying the work.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

SITE = ROOT / "site"

# Routes that exist for AGENTS and machines, not for a page. Each is reachable through the MCP
# tool surface, llms.txt, or a documented HTTP call — a human page would add nothing.
AGENT_ONLY = {
    # THE CUT of 2026-08-05 (lever 5): these routes' pages were retired — 31 pages earned
    # fewer than 12 human visits in a week while agents kept calling the ROUTES (MCP tools
    # map onto many). The features remain as agent/API surface; humans reach the substance
    # through the desk, the card pages, and search.
    "/apothecary/propose", "/backmatter", "/codex/artifact", "/codex/connections",
    "/codex/scripture", "/codex/themes", "/codex/verify", "/commons", "/curate",
    "/curate/queue", "/curate/signable", "/deck", "/deck/open", "/decks", "/drop", "/drop/signable",
    "/formation", "/formation/help", "/formation/kinds", "/group", "/group/contribute",
    "/group/join", "/groups", "/journal/dates", "/mesh/door", "/mesh/inbox", "/mesh/invite",
    "/mesh/link", "/mesh/map", "/mesh/node", "/mesh/post", "/mesh/redeem", "/narratives",
    "/places", "/push/key", "/push/subscribe", "/shelf", "/steward/budget",
    "/steward/cost-destroyed", "/study", "/study_find", "/teachings", "/thread/verify",
    "/want", "/works/artifact", "/works/verify",
    "/health",
    # The six MCP profile mounts (task #123): an agent's client mounts one plane by URL;
    # a human page linking them would be a door drawn for someone who cannot walk through it.
    # The full /mcp is documented on the connect page; the profiles are documented beside it.
    "/mcp/core", "/mcp/library", "/mcp/sovereign", "/mcp/coach", "/mcp/witness", "/mcp/community",
    # The clock. An agent's own 'today' is its training cutoff — months stale — so this is the
    # correction an AGENT needs; a human reader has a wall clock and a phone. The MCP `now` tool
    # is the primary door; this route is the same reading over plain HTTP for scripts and
    # connectors that speak REST rather than MCP.
    "/now",
    # No page links this and none should: it is an OPERATOR instrument, read by a
    # person deciding an architecture, not a reader looking something up. Declared
    # rather than quietly exempted — an undeclared door is how a registry rots.
    "/health/memory",
    "/capabilities", "/identity/create", "/identity/describe",
    # /activity.json powers the /live.html "under the hood" ledger via fetch()
    # (the AST auditor reads only literal links, not fetch strings) — a data
    # endpoint, not a page a human navigates TO. The human surface is /live.html.
    "/activity.json",
    # /build.json is deployment provenance (red team R-14) — protocol + profiles +
    # tool_catalog_hash a reviewer compares to the repo; a data endpoint, not a page.
    "/build.json",
    "/identity/fingerprint", "/identity/verify", "/attest", "/self-attest",
    "/bind", "/bind/challenge", "/consent", "/consent/signable", "/consent/revoke",
    "/connect/event", "/moderation/signable", "/derivation/verify", "/grid",
    "/grid/dimension", "/locate", "/resolve", "/route", "/path", "/inlet", "/land",
    "/defer", "/fork", "/returns", "/steward/ask", "/mesh/tend", "/mesh/signable",
    "/push/unsubscribe", "/study/export", "/study/import", "/card/connections",
    "/cards/for-the-group", "/decks/predict", "/thread/digest", "/thread/lineage",
    "/thread/recall", "/thread/recalled", "/threads/search", "/word_occurrences",
    "/works/item", "/library/health", "/growth", "/daily", "/pronounce", "/book",
    "/badges", "/archetype", "/archetypes", "/archetypes/match", "/coach/guidance",
    "/chess", "/report", "/block",
    # The open-question pair (Matt, 2026-08-01: "you ask the first person that recalls the cards
    # to verify them"). `/unchecked` is the standing ledger — a Steward instrument, same shape as
    # `/wants`. `/unchecked/answer` IS reader-facing and is NOT quietly exempt: it is linked as a
    # real <a href> from every engine-written card page, which api.render_card_html builds at
    # request time. This checker reads static markup only (site/*.html, site/*.js), so it cannot
    # see a server-rendered link — the limit is in the instrument, not in the door, and saying so
    # here is the point of declaring rather than exempting. tests/test_unchecked_route.py holds
    # the link itself, by rendering the page and asserting the href is in the HTML.
    "/unchecked", "/unchecked/answer",
    "/wants",   # the desiderata ledger — read by the Steward's rounds and the mint; humans reach
                # the WRITE side (/want) from the empty-search offer and the card flag

    # Verification / keeping surfaces no page links, by design: /witness is the Cloud of Witnesses' voice
    # (public-domain, attributed) reached by agents and the discern flow; /context/run is the node-local
    # context loop, gated by CONCORDANCE_SOVEREIGN_NODE (403 on the shared box); /kernel + /kernel/gate run
    # a proposed state-change through the invariant lattice; /playbook/signable + /playbook/submit are the
    # Playbook's signed two-step write. All agent/API surface, not a human page.
    "/witness", "/context/run", "/kernel", "/kernel/gate", "/playbook/signable", "/playbook/submit",

    # THE COMMONS: nothing here is agent-only any more. C1b declared the six shelf routes on this
    # list with a promise that `shelf.html` would land in C1c and they would come off it — C1c
    # landed, and they came off. That is what the declaration was for.
}

# Pages reachable by design without an in-site link: entered by URL, by QR, by an app shell,
# or deliberately quiet. Named so "unlinked" is a decision, never an accident.
UNLISTED_PAGES = {
    "offline.html",       # served by the service worker when the network is gone
    "404.html",
    "keep.html",          # the operator's own surface, noindex — a public list is not its place
    "encyclopedia.html",  # a redirect stub onto characters.html; a second door to one room
    "ask.html",           # the landing's predecessor, kept for old links
    "profile.html",       # the opt-in sovereign keeping (ez-login) — reached by direct URL / the keeping flow, not the public nav
    "golf.html",          # Gate Golf — the founder's N=1 instrument (NarrowFairway), a self-contained offline tool; reached by direct URL / home-screen install, not the public nav
    "playbook.html",      # the Playbook surface — operator/agent authoring, not the public nav
    "plow.html",          # the Plow surface — an operator instrument, not the public nav
}


def _pages():
    return sorted(p for p in SITE.glob("*.html"))


def _all_markup():
    """Pages AND scripts. The first run of this check read only `*.html` and reported 51
    unreachable routes and 8 orphan pages — but most routes are called from scripts, and
    `nh-tools.js` IS a reachability surface (the Everything palette). Measuring the wrong
    surface manufactures findings: check the check first."""
    return "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                     for p in _pages() + sorted(SITE.glob("*.js")))


def _palette():
    """The Everything palette (Ctrl-K) — a page listed there is reachable from every page."""
    js = SITE / "nh-tools.js"
    if not js.exists():
        return set()
    return set(re.findall(r"h: '/([a-z0-9_-]+\.html)", js.read_text(encoding="utf-8")))


def test_every_api_route_is_reachable_or_declared_agent_only():
    from concordance.web import api
    markup = _all_markup()
    unreachable = []
    for r in api.ROUTES:
        path = r["path"]
        if path in AGENT_ONLY or path.startswith("/s/"):
            continue
        # A retired path is unlinked ON PURPOSE — it catches inbound links we do not control and
        # forwards them. Requiring a page to link it would put a tombstone in the navigation.
        if r.get("retired"):
            continue
        if path not in markup:
            unreachable.append(path)
    assert not unreachable, (
        "routes no page can reach — add them to a page, or declare them in AGENT_ONLY with a "
        "reason: " + ", ".join(sorted(unreachable)))


def test_agent_only_declarations_are_real_routes():
    """A stale declaration would silently excuse a route that no longer exists — and worse,
    would let a NEW route inherit an old exemption by name."""
    from concordance.web import api
    live = {r["path"] for r in api.ROUTES}
    stale = sorted(AGENT_ONLY - live)
    assert not stale, f"AGENT_ONLY names routes that no longer exist: {stale}"


def test_every_page_is_linked_or_declared_unlisted():
    markup = _all_markup()
    linked = set(re.findall(r'href="/?([a-z0-9_\-]+\.html)"', markup)) | _palette()
    orphans = [p.name for p in _pages()
               if p.name not in linked and p.name != "index.html"
               and p.name not in UNLISTED_PAGES]
    assert not orphans, (
        "pages linked from nowhere — link them, or declare them in UNLISTED_PAGES with a "
        "reason: " + ", ".join(sorted(orphans)))


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
