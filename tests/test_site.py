"""Site test — the front door's files exist and call the right endpoints.

Lightweight (no live server — the integrated server is exercised in dev via
`python -m concordance serve`; the dispatcher is covered by test_api). Guards that the
site is present, named, positioned, wired to the API, and honestly links to the witness.
Runnable with `pytest` OR `python tests/test_site.py`.
"""
from __future__ import annotations

import sys
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
SITE = _ROOT / "site"


def test_site_files_exist():
    for f in ("index.html", "proof.html", "styles.css"):
        assert (SITE / f).is_file(), f"missing site file: {f}"


def test_index_named_positioned_and_wired():
    """The landing is now the conversation itself, not a product page — but the principles it
    had to satisfy are unchanged: it names itself, states its positioning, calls the engine,
    and never hides the witness. The interactive demo moved to /check.html (below)."""
    t = (SITE / "index.html").read_text(encoding="utf-8")
    assert "Narrow" in t and "narrowing the possibilities" in t, "name + positioning"
    assert "/ask" in t, "the landing must call the engine — it IS the conversation"
    assert "narrowhighway.org" in t, "honest link to the witness — not hiding"
    assert "narrowhighway.org" in t and "Christ" in t, "surface-aware: name the foundation on .org"


def test_identity_line_is_one_source():
    """THE REFRAME (Matt, 2026-08-06: "Deterministic verification engine. We need to reframe and
    reorganize."). What the engine IS is defined ONCE — branding.IDENTITY_LINE — and surfaced
    verbatim on every face a person reads it on, so the identity can never rot back into the buried,
    per-page paraphrases it was before (it lived in a hidden span and a footer, not a headline).
    The agent-facing descriptors state the SAME identity in machine register — verified here by the
    two load-bearing claims, not the exact wording: it is a *verification* engine, and there is *no
    model in the loop*."""
    import sys as _sys
    _sys.path.insert(0, str(_ROOT / "src"))
    from concordance import branding
    anchor = branding.IDENTITY_LINE
    assert anchor == "A deterministic verification engine.", anchor
    # the long-form identity is BUILT from the line — the single source is internally consistent
    assert branding.SECULAR_IDENTITY.startswith(anchor), "SECULAR_IDENTITY must open with the line"
    # every human-read SECULAR surface carries the exact line — one source, no drift. The .com face
    # is com.html (the surface sort, 2026-09-01): the deterministic-engine identity lives on the secular
    # landing, not the witness desk (index.html), which names the Rock in its own language instead.
    for rel in ("site/com.html", "site/live.html", "site/llms.txt"):
        t = (_ROOT / rel).read_text(encoding="utf-8")
        assert anchor in t, f"{rel} does not surface the identity line verbatim"
    # the agent descriptors say the same thing in machine-register: still a verification engine,
    # still no model in the loop (these two claims are load-bearing; the exact human wording is not)
    for rel in ("docs/registry/server.json", "site/.well-known/mcp.json", "site/connect.html"):
        t = (_ROOT / rel).read_text(encoding="utf-8").lower()
        assert "deterministic verification" in t, f"{rel} lost the engine framing"
        assert "no model in the loop" in t, f"{rel} lost the 'no model in the loop' guarantee"


def test_every_page_offers_a_way_home():
    """One identical home control, injected everywhere, so it cannot drift per page."""
    # mesh.html is THE HIDDEN discovery surface (the Fellowship Mesh / "The Way"). It must NOT carry
    # the shared home control, because that control injects the nav + Ctrl-K palette — which would
    # advertise a page that is meant to be found only when the agent reveals it (Matthew 7:7). It
    # carries its own minimal brand-home link instead, and the flock is protected by the confession
    # gate, not by nav-hiding alone.
    # live.html is the austere .org "under the hood" ledger — like mesh.html it carries its own
    # minimal home link, not the shared nav/palette control (which would clutter the calm feed).
    # Self-contained surfaces that carry their OWN nav, not the shared home control: the efficiency
    # front door and its confession/lobby (checkit/about/halls — the .com door leads with the working
    # tool, no shared nav by design, per the Domain Sort), the offline instrument apps (golf/grappling),
    # and the operator/sovereign/pastoral surfaces (playbook/plow/profile/situations). Declared here
    # rather than each carrying nh-home.js — the same treatment mesh.html/live.html already get.
    hidden = {"mesh.html", "live.html", "checkit.html", "about.html", "halls.html", "golf.html",
              "grappling.html", "music.html", "provision.html", "wisdom.html", "workshop.html",
              "coach.html", "tv.html", "playbook.html", "plow.html", "profile.html", "situations.html",
              # com.html is the .com secular LANDING (surface sort, 2026-09-01): it IS home and carries
              # its own nav, not the shared desk control. systems.html/prophecy.html are self-contained
              # surfaces reached by direct URL.
              "com.html", "systems.html", "prophecy.html"}
    missing = [f.name for f in SITE.glob("*.html")
               if f.name != "index.html" and f.name not in hidden
               and "nh-home.js" not in f.read_text(encoding="utf-8")]
    assert not missing, f"pages with no way home: {missing}"


def test_cli_entrypoint_importable():
    sys.path.insert(0, str(_ROOT / "src"))
    import concordance.__main__ as m
    assert hasattr(m, "main")


# ── the tools have to actually be reachable ─────────────────────────────────────────────────

def _palette():
    """Every entry in the Ctrl-K list: (href, name)."""
    js = (SITE / "nh-tools.js").read_text(encoding="utf-8")
    return re.findall(r"\{ h: '([^']+)',\s*n: '([^']+)'", js)


def test_every_tool_in_the_palette_exists():
    """A list that points at a page which is not there is worse than no list."""
    for href, name in _palette():
        if href == "/":
            continue
        # a palette entry may be a DEEP link (/corpus.html?section=drawers) — the page has to
        # exist, the query does not name a file
        page = href.split("?")[0].split("#")[0]
        assert (SITE / page.lstrip("/")).exists(), f"{name!r} points at a missing page: {href}"


def test_the_palette_never_offers_a_page_that_is_not_public():
    """keep.html is the operator's own surface: noindex, and 404 to the world. Listing it would
    hand every visitor a door that opens onto nothing — or worse, onto something private."""
    for href, name in _palette():
        assert "keep.html" not in href, f"{name!r} exposes the operator surface"


def test_the_palette_reaches_every_public_page():
    """Anything shipped in site/ should be findable, or deliberately excluded with a reason
    written in nh-tools.js. Silence is how a page becomes unreachable without anyone noticing."""
    listed = {h.lstrip("/") for h, _n in _palette()}
    # documented exclusions — see the comment above TOOLS in nh-tools.js. mesh.html is the HIDDEN
    # discovery surface: never in the palette (the whole point is that it is found, not advertised —
    # Matthew 13:44), served but revealing nothing until the agent opens it and confession is made.
    excused = {"index.html", "keep.html", "ask.html", "encyclopedia.html", "mesh.html", "live.html",
               # self-contained surfaces, reached by direct URL / their own nav, not the palette: the
               # efficiency front door + confession + lobby, the offline instruments, the operator pages
               "checkit.html", "about.html", "halls.html", "golf.html", "grappling.html",
               "coach.html", "tv.html", "music.html", "provision.html", "wisdom.html", "workshop.html", "playbook.html", "plow.html", "profile.html", "situations.html",
               # com.html is the .com bare homepage (served at "/"), like index.html; systems.html is the
               # operator dashboard and prophecy.html a direct-URL surface — reached by URL, not the palette.
               "com.html", "systems.html", "prophecy.html"}
    unreachable = sorted(
        p.name for p in SITE.glob("*.html") if p.name not in listed and p.name not in excused)
    assert not unreachable, f"no way to reach: {unreachable} (list them or excuse them by name)"


def test_the_palette_is_on_every_page_that_has_the_home_control():
    """Reachable from where you are standing, not only from the landing."""
    for p in SITE.glob("*.html"):
        t = p.read_text(encoding="utf-8")
        if "nh-home.js" in t:
            assert "nh-tools.js" in t, f"{p.name} can go home but cannot reach the tools"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} site tests passed — the front door is built, named, and wired.")
