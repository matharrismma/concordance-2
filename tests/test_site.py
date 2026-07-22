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
    for f in ("index.html", "seal.html", "styles.css"):
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


def test_check_page_still_carries_the_demo():
    """The proof-first demo was relocated, not deleted: a blank landing must not cost the
    thing that makes the claim checkable by a stranger."""
    t = (SITE / "check.html").read_text(encoding="utf-8")
    assert "/verify" in t and "/search" in t, "the demo must call the API"
    assert "checkAnything" in t, "the paste-anything demo must still work"


def test_every_page_offers_a_way_home():
    """One identical home control, injected everywhere, so it cannot drift per page."""
    missing = [f.name for f in SITE.glob("*.html")
               if f.name != "index.html" and "nh-home.js" not in f.read_text(encoding="utf-8")]
    assert not missing, f"pages with no way home: {missing}"


def test_seal_page_calls_seal_endpoint():
    t = (SITE / "seal.html").read_text(encoding="utf-8")
    assert "/seal" in t


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
        assert (SITE / href.lstrip("/")).exists(), f"{name!r} points at a missing page: {href}"


def test_the_palette_never_offers_a_page_that_is_not_public():
    """keep.html is the operator's own surface: noindex, and 404 to the world. Listing it would
    hand every visitor a door that opens onto nothing — or worse, onto something private."""
    for href, name in _palette():
        assert "keep.html" not in href, f"{name!r} exposes the operator surface"


def test_the_palette_reaches_every_public_page():
    """Anything shipped in site/ should be findable, or deliberately excluded with a reason
    written in nh-tools.js. Silence is how a page becomes unreachable without anyone noticing."""
    listed = {h.lstrip("/") for h, _n in _palette()}
    # documented exclusions — see the comment above TOOLS in nh-tools.js
    excused = {"index.html", "keep.html", "ask.html", "encyclopedia.html"}
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
