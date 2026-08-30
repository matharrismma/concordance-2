"""The field-library canon — find recrafted to fit the system (Matt, 2026-08-30: "Refine the concept
of find. Recraft it to perfectly fit the system instead of trying to rework the system for find.").

Not the scripture canon (that is test_canonical / test_canon_original). This is find's kept map of a
subject -> the tried-and-true public-domain source that answers it, navigated by elimination FIRST,
grown by promotion (search once, keep forever), with provider health/rotation and credit.

Proves: (1) the canon resolves a family subject generously and best-first, respects the plane, and
misses honestly; (2) promotion keeps a reach win and never re-promotes a canon hit; (3) find_and_check
is CANON-FIRST — a family subject resolves even with the whole network dark; (4) providers rotate a
source that fails us more than once and re-probe after cooldown; (5) reach skips paused/benched and
honours a monkeypatch (never the real network behind a test's back); (6) credit reaches the reader
with an easy way back. Network is never touched — providers are stubbed. Runs with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-canon-"))

from concordance import field_canon as canon, find, providers  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

SEC = EngineConfig("secular")
_LOC, _IA, _GUT = find.library_of_congress, find.internet_archive, find.project_gutenberg


def _fresh() -> str:
    """A clean data dir per test, so canon.jsonl and provider_health.json never leak between tests."""
    d = tempfile.mkdtemp(prefix="nh-canon-")
    os.environ["CONCORDANCE_DATA_DIR"] = d
    return d


def _enable() -> None:
    os.environ.pop("WEB_FIND_DISABLED", None)


def _restore() -> None:
    find.library_of_congress, find.internet_archive, find.project_gutenberg = _LOC, _IA, _GUT
    os.environ["WEB_FIND_DISABLED"] = "1"


# ── the canon: elimination over a kept map ───────────────────────────────────────────────────
def test_canon_resolves_family_subjects_generously():
    _fresh()
    cases = {
        "how do i keep honeybees": "everystepinbeek00douggoog",
        "raise chickens for eggs": "openairpoultryho00wood",
        "forge a knife": "forgepracticehea00bacorich",
        "bandage a bleeding wound": "americannational00lync",
        "dry apples for the winter": "dehydratingfoods00andr",
        "make cheese at home": "cheesemakingbook00samm",
    }
    for q, ident in cases.items():
        docs = canon.lookup(q, plane="text", limit=1)
        assert docs, f"canon should hold {q!r}"
        assert ident in docs[0]["url"], f"{q!r} -> {docs[0]['url']} (wanted {ident})"


def test_canon_respects_plane_and_misses_honestly():
    _fresh()
    assert canon.lookup("keep honeybees", plane="video") == []      # a text book is not a video
    assert canon.lookup("quantum chromodynamics amortization schedule") == []   # not a field subject
    assert canon.holds("first aid") and not canon.holds("first aid", plane="video")


def test_promotion_search_once_keep_forever():
    _fresh()
    doc = {"title": "Soap-Making Manual", "url": "https://archive.org/details/soapmakingmanual",
           "source": "Internet Archive", "license": "Public domain", "year": "1922",
           "provider_id": "internet_archive"}
    assert canon.lookup("how do i make soap") == []                 # dark before
    assert canon.promote("soap making", doc, plane="text", terms="soap lye tallow")
    assert canon.lookup("how do i make soap")[0]["url"].endswith("soapmakingmanual")  # kept
    assert not canon.promote("soap making", doc, plane="text")      # dedups by url
    assert not canon.promote("bees", canon.lookup("bees")[0])       # a canon hit is never re-promoted


# ── find_and_check: canon FIRST, even with the network dark ───────────────────────────────────
def test_find_and_check_is_canon_first_with_network_dark():
    _fresh()
    _enable()
    find.internet_archive = lambda q, limit=3, practical=None: []
    find.library_of_congress = lambda q, limit=3, practical=None: []
    find.project_gutenberg = lambda q, limit=3, practical=None: []
    try:
        r = find.find_and_check("how do i keep honeybees", SEC)
        assert r is not None, "canon must answer though every provider is empty"
        assert any("everystepinbeek00douggoog" in (d.get("url") or "") for d in r["documents"])
        assert r["documents"][0].get("credit"), "credit must reach the reader"
        cards = [json.loads(x) for x in find._store_path().read_text(encoding="utf-8").splitlines()
                 if x.strip()]
        assert any("everystepinbeek00douggoog" in json.dumps(c) for c in cards), "the canon source is kept"
    finally:
        _restore()


# ── providers: rotation + credit ─────────────────────────────────────────────────────────────
def test_provider_rotation_two_strikes_then_cooldown():
    _fresh()
    providers.record("internet_archive", False, now=1000)
    assert not providers.benched("internet_archive", now=1001)      # one failure is forgiven
    providers.record("internet_archive", False, now=1002)
    assert providers.benched("internet_archive", now=1003)          # more than once -> benched
    assert all(p["id"] != "internet_archive" for p in providers.active("text", now=1003))
    later = 1002 + providers.COOLDOWN_SECONDS + 1
    assert not providers.benched("internet_archive", now=later)     # checked back after cooldown
    providers.record("internet_archive", True, now=later + 1)
    assert not providers.benched("internet_archive", now=later + 2)  # a success clears the slate


def test_gutenberg_is_cut_by_policy():
    _fresh()
    assert all(p["id"] != "project_gutenberg" for p in providers.active("text"))


def test_reach_skips_paused_and_honours_monkeypatch():
    _fresh()
    _enable()
    seen = []
    find.internet_archive = lambda q, limit=3, practical=None: (seen.append("ia") or [])
    find.project_gutenberg = lambda q, limit=3, practical=None: (seen.append("gut") or [])
    find.library_of_congress = lambda q, limit=3, practical=None: (seen.append("loc") or [])
    try:
        find.reach("beekeeping", plane="text")
        assert "ia" in seen and "loc" in seen        # active sources reached (monkeypatch honoured)
        assert "gut" not in seen                      # gutenberg is paused -> never called
    finally:
        _restore()


def test_credit_names_the_source_with_a_way_back():
    _fresh()
    c = providers.credit({"provider_id": "internet_archive", "url": "https://archive.org/details/x"})
    assert c["name"] == "Internet Archive" and c["home"] and c["url"].endswith("/x")
    line = providers.line({"source": "Library of Congress", "url": "https://www.loc.gov/item/y"})
    assert "Library of Congress" in line and "loc.gov/item/y" in line   # resolved by name, way back present


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} field-canon tests passed — find recrafted: canon-first, rotate, credit, keep.")
