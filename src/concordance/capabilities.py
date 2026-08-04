"""The live capability statement — every public number, computed, with its definition attached.

Restores to 2.0 a capability 1.0 had and the rewrite dropped (`GET /capabilities`, 1.0 commit
18c3d5f) — along with Matt's standing rule from the day it was built (2026-06-10): *"do NOT hardcode
capability counts in page copy — they drift and break trust (the moat is TRUST)."* With no live
source to read, the pages drifted again exactly as predicted: a 2026-07-27 review found "71
verifiers", "~60 domains", and "64 checks" all claimed on one site.

The audit's finding was NOT that anyone lied. **Every one of those numbers is true of something:**

    61   distinct secular verifier MODULES          -> read as "~60 domains"
    64   distinct modules incl. witness (61 + 3)    -> read as "64 verification"
    122  domain NAMES the router accepts (aliases)  -> "mathematics" and "math" are one module
    64   verifier .py files on disk                 -> excludes __init__.py and base.py

So the fix is not to force the numbers into agreement — that would trade one wrong claim for
another. The fix is to compute each number from the running engine and **carry its definition with
it**, so a reader (human, agent, or robot) can never mistake which thing was counted. Honest on both
ends: we say what we have, and we say exactly what we mean by it.

Nothing here is hand-maintained and nothing is cached: every field is derived at call time from the
live registries (`verifiers.VERIFIERS`, the MCP tool lists, `web.api.ROUTES`, `corpus.stats()`, the
study tables). If a capability is added or removed, this statement changes with it or it is a bug.

Satisfies the frozen contract's worklist item 3 — "One capabilities manifest; all public counts
derive from it" — and its §5 DONE line "counts derive from one canonical manifest (no
hand-maintained public numbers)".
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

MISSION = ("Narrow Highway gives humans and agents a governed way to find, check, use, and preserve "
           "information without losing its source, authority, or history.")

NOTE = ("A conduit, not a source: the engine FINDS and VERIFIES; it does not generate the answer. "
        "Every count below is computed from the running engine at the moment you asked, and carries "
        "the definition of what was counted — so no number here can drift from what the code "
        "actually does, and none can be misread as a bigger claim than it is.")


def _verifiers() -> Dict[str, Any]:
    from . import verifiers as V

    def by_module(reg: Dict[str, Any]) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for name, mod in reg.items():
            out.setdefault(getattr(mod, "__name__", str(mod)), []).append(name)
        return out

    sec, wit = by_module(V.VERIFIERS), by_module(V.WITNESS_VERIFIERS)
    files = [p.name for p in sorted((Path(__file__).parent / "verifiers").glob("*.py"))
             if p.name not in ("__init__.py", "base.py")]
    return {
        "secular_modules": {
            "count": len(sec),
            "means": "distinct verifier modules reachable on the secular surface",
        },
        "witness_modules": {
            "count": len(wit),
            "means": ("distinct verifier modules added on the witness surface (theology/doctrine, "
                      "scripture, witness) — surfaced only there"),
        },
        "distinct_modules_total": {
            "count": len(set(sec) | set(wit)),
            "means": "distinct verifier modules in total, secular + witness, counted once each",
        },
        "domain_names_accepted": {
            "count": len(V.VERIFIERS) + len(V.WITNESS_VERIFIERS),
            "means": ("domain NAMES the router accepts, including aliases — several names route to "
                      "one module ('mathematics' and 'math' are the same verifier), so this is "
                      "always larger than the module count and is NOT a count of capabilities"),
        },
        "verifier_files_on_disk": {
            "count": len(files),
            "means": "verifier source files, excluding the package __init__ and the shared base",
        },
        "cross_cutting": {
            "count": len(V.CROSS_CUTTING_VERIFIERS),
            "means": "verifiers that run on every packet regardless of domain",
        },
    }


def _tools(surface: str) -> Dict[str, Any]:
    from .config import EngineConfig
    from .mcp import server as _srv
    names = sorted(t["name"] for t in _srv._tools_for(EngineConfig(surface)))
    return {"count": len(names), "names": names,
            "means": f"MCP tools an agent can call on the {surface} surface"}


def _routes() -> Dict[str, Any]:
    from .web import api
    api_gets = sorted(api._API_GET_PATHS)
    return {
        "api_get_paths": {"count": len(api_gets), "paths": api_gets,
                          "means": "JSON GET endpoints served by the engine (not static files)"},
        "rate_limited": {"count": len(api.RATELIMITED),
                         "means": "endpoints behind the rate limiter"},
        "registered_routes": {"count": len(api.ROUTES),
                              "means": "entries in the single route registry ROUTES"},
    }


def _substrate() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        from . import corpus
        st = corpus.stats() or {}
        out["cards"] = {"count": st.get("total") or st.get("cards"),
                        "means": "cards in the keeping (the shared corpus, both surfaces)"}
        # The profile mounts (task #123): the capability statement is where a reader learns the
        # narrow doors exist — a boundary nobody can discover is a boundary that does not reach
        # the reader.
        try:
            from .mcp.server import PROFILES
            out["mcp_profiles"] = {
                "count": len(PROFILES),
                "names": sorted(PROFILES),
                "means": ("mounts at /mcp/<name>, each serving one plane of the tool catalog "
                          "(every tool lives in exactly one); /mcp serves the full catalog for "
                          "existing clients; community is off unless the host enables it")}
        except Exception:                                      # noqa: BLE001 — never break the statement
            pass
        # G1 (docs/GAPS.md): a count claimed alone lets the million be hit without a sentence of
        # substance. So the headline never travels without its split — measured once per process
        # (ops memoizes; walking 548k bodies per request would knock reading into proving).
        from . import ops
        sub = ops.substance_of_the_keeping()
        out["cards_substance"] = {
            "count": sub["substance_cards"],
            "means": sub["means"]["substance_cards"]}
        out["cards_stubs"] = {
            "count": sub["stub_cards"],
            "means": sub["means"]["stub_cards"] + f" — stub_ratio {sub['stub_ratio']}"}
        if sub.get("frozen_cards"):
            out["cards_frozen"] = {
                "count": sub["frozen_cards"],
                "means": sub["means"]["frozen_cards"]}
        if st.get("shelves"):
            out["shelves"] = {"count": len(st["shelves"]), "means": "shelves the cards sit on"}
    except Exception as e:  # noqa: BLE001 — a substrate we cannot read is reported, never guessed
        out["cards"] = {"count": None, "unavailable": str(e)[:120]}
    try:
        from . import harmony, timeline
        out["harmony_events"] = {
            "count": len(harmony._HARMONY),
            "means": "events of Christ's life in the Harmony, each citing every gospel that records it"}
        out["timeline_events"] = {
            "count": len(timeline._TIMELINE),
            "means": "events on the Timeline across the Old Testament, New Testament, and Church History"}
        out["timeline_events_disputed"] = {
            "count": sum(1 for t in timeline._TIMELINE if t["disputed"]),
            "means": ("Timeline events whose date is genuinely disputed among scholars — these carry "
                      "BOTH positions and declare no winner")}
    except Exception as e:  # noqa: BLE001
        out["harmony_events"] = {"count": None, "unavailable": str(e)[:120]}
    return out


def statement(surface: str = "secular") -> Dict[str, Any]:
    """The whole live capability statement for a surface. Computed now; never cached, never hardcoded."""
    surface = "witness" if str(surface).lower() == "witness" else "secular"
    return {
        "mission": MISSION,
        "surface": surface,
        "note": NOTE,
        "verifiers": _verifiers(),
        "tools": _tools(surface),
        "routes": _routes(),
        "substrate": _substrate(),
        "boundaries": {
            "generated": False,
            "means": ("nothing in the keeping is generated by a model; text is found and attributed, "
                      "and generated material is quarantined, never cited as a source"),
            "authority_is_never_silently_upgraded": True,
            "declines_when_it_cannot_verify": True,
            "no_account_required": True,
            "parity": ("every study surface a human reads as a page is a tool an agent can call over "
                       "the same data, under the same gate, with the same refusals"),
        },
        "how_to_read_this": ("Each count carries a 'means' line. Compare like with like: "
                             "'domain_names_accepted' counts router aliases, NOT capabilities; "
                             "'distinct_modules_total' is the honest answer to 'how many verifiers'."),
    }


__all__ = ["statement", "MISSION", "NOTE"]
