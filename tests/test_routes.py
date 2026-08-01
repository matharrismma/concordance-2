"""Route registry — single source of truth, locked and drift-guarded.

api.ROUTES is the ONE place a route's metadata lives; _API_GET_PATHS and RATELIMITED are
derived from it. This test (1) LOCKS the derivation to the historical hand-maintained values
(so the refactor changed nothing the server sees), and (2) GUARDS against drift — every
(method, path) that dispatch() actually handles must be registered, and every registered
non-serve path must be handled. Adding a route without registering it (the old triplication
bug that made a new GET API path fall through to the site handler) now fails here.

Runnable with pytest OR `python tests/test_routes.py`.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from concordance.web import api  # noqa: E402

# The historical hand-maintained values, verbatim — the behavior the server had before the
# registry refactor. The derived sets must equal these exactly.
GOLDEN_API_GET = {
    "/health",
    # An operator door, added 2026-08-01 to settle whether the freeze design rests on a
    # true belief: it reports where the resident corpus actually spends its memory
    # (cards vs token index), from the live process, sampled and labelled as an estimate.
    "/health/memory",
    "/identity", "/route", "/bind/challenge", "/thread/digest", "/thread/recall", "/thread/lineage", "/thread/recalled", "/land", "/cards/for-the-group",
    "/search", "/seal", "/resolve", "/word_study",
    "/card", "/cards", "/cards/stats", "/daily", "/grid", "/grid/dimension",
    "/card/connections", "/graph", "/floor", "/locate", "/library/health", "/growth",
    "/thread", "/threads", "/threads/search", "/thread/verify", "/passage", "/apothecary",
    "/pronounce", "/cross_refs", "/word_occurrences", "/original", "/canon",
    "/commentary", "/journal", "/journal/dates", "/steward", "/tsk",
    "/character", "/characters", "/prophecy",
    "/coach/subjects", "/coach/overview", "/coach/journey", "/coach/unit", "/coach/next", "/coach/recommend", "/coach/guidance",
    "/identity/fingerprint", "/identity/describe", "/badges", "/study", "/card.html",
    "/groups", "/group", "/seeds", "/almanac",
    "/codex", "/codex/scripture", "/codex/themes", "/codex/connections", "/codex/artifact", "/codex/verify",
    "/works", "/works/item", "/works/artifact", "/works/verify",
    "/decks", "/decks/predict", "/deck",
    "/archetypes", "/archetypes/match", "/archetype",
    "/mesh", "/mesh/map", "/mesh/inbox", "/mesh/door",
    "/formation", "/formation/kinds", "/formation/help",
    "/push/key",
    "/teachings",
    "/path",   # deliberate addition (wayfinding — the floorplan of the keeping)
    "/harmony",   # deliberate addition (Harmony of the Gospels — every gospel witness, side by side)
    "/timeline",  # deliberate addition (OT/NT/Church History — one spine, creation to today)
    "/backmatter",  # deliberate addition (back-matter tables: weights, names, parables, miracles, intros, topics)
    "/places",    # deliberate addition (the Atlas: real biblical place coordinates, honest uncertainty)
    "/consent", "/consent/signable", "/consent/revoke",  # the human-authorized write path (worklist item 2)
    "/drop/signable",
    "/drop",
    "/shelf",
    "/commons",
    "/curate/queue",
    "/curate/signable",
    "/curate",
    "/moderation/signable",
    "/report", "/block",  # the moderation floor (worklist item 4)
    "/connect/event",  # the calendar pilot — the one on-behalf write, behind the consent lock
    "/narratives",  # deliberate addition (storyboards: common narratives charted in the Bible; movements mix and match)
    "/study_find",  # deliberate addition (the quick-find index across the whole reference section)
    "/capabilities",  # deliberate addition (the live capability statement — restored from 1.0)
    "/mesh/signable",  # deliberate addition (the bytes to sign, so a key never crosses the wire)
    "/attest",  # deliberate addition (bear witness to a record you hold; GET lists the witnesses)
    "/wants",   # deliberate addition (the WANT LIST — the library grows by its misses; 2026-08-01)
}
# /search moved OUT of this set on 2026-07-31 and into GOLDEN_READ_LIMITED — a read and a write
# are not the same risk, and the one client the shared cap refused most was ClaudeBot.
GOLDEN_RATELIMITED = {
    "/verify", "/derivation/verify", "/mcp", "/ask", "/speak", "/bind", "/book", "/fork", "/defer", "/inlet", "/returns", "/days", "/apothecary/propose", "/pins", "/pins/done",
    "/threads", "/threads/search",
    "/coach/mastery", "/identity/create", "/identity/verify", "/badges",
    "/study", "/study/export", "/study/import",
    "/groups", "/group", "/group/join", "/group/contribute",
    "/mesh/node", "/mesh/link", "/mesh/post", "/mesh/tend",
    "/mesh/invite", "/mesh/redeem", "/mesh/door", "/formation/help",
    "/push/subscribe", "/push/unsubscribe",
    "/consent/signable", "/consent", "/consent/revoke",  # the human-authorized write path (worklist item 2)
    "/drop/signable",
    "/drop",
    "/curate/signable",
    "/curate",
    "/moderation/signable",
    "/report", "/block",  # the moderation floor (worklist item 4)
    "/connect/event",  # the calendar pilot — the one on-behalf write, behind the consent lock
    "/audit",   # deliberate addition (the Auditor) — goldens update ONLY with a new route
    "/chess",   # deliberate addition (the chess verifier) — game theory, applied and sealable
    "/attest",  # deliberate addition — a write, so rate-limited like every other write
    "/want",    # deliberate addition — opening a want is a write (the hive's return-point)
}


GOLDEN_READ_LIMITED = {"/search"}


def test_the_read_bucket_is_separate_and_larger():
    """Every 429 this server has ever served was on /search, and 75 of them refused ClaudeBot
    mid-crawl — 3,368 searches from the audience we built the surface for. The cap is not removed
    (an unbounded FTS on a 7 GB box is a real exposure); it is separated, so a write cannot spend
    a reader's budget and a reader cannot spend a writer's."""
    from concordance import ratelimit
    assert set(api.READ_LIMITED) == GOLDEN_READ_LIMITED
    assert not (set(api.READ_LIMITED) & set(api.RATELIMITED)), "a path in both buckets"
    assert ratelimit.from_env(read=True).max > ratelimit.from_env().max, (
        "the read bucket must be larger than the write bucket, or the split bought nothing")


def test_derived_sets_match_history():
    assert set(api._API_GET_PATHS) == GOLDEN_API_GET, (
        f"_API_GET_PATHS drifted: missing={GOLDEN_API_GET - set(api._API_GET_PATHS)} "
        f"extra={set(api._API_GET_PATHS) - GOLDEN_API_GET}")
    assert set(api.RATELIMITED) == GOLDEN_RATELIMITED, (
        f"RATELIMITED drifted: missing={GOLDEN_RATELIMITED - set(api.RATELIMITED)} "
        f"extra={set(api.RATELIMITED) - GOLDEN_RATELIMITED}")


def test_no_duplicate_paths():
    paths = [r["path"] for r in api.ROUTES]
    dupes = {p for p in paths if paths.count(p) > 1}
    assert not dupes, f"duplicate ROUTES entries: {dupes}"


def _dispatch_paths():
    """AST-extract every (method, path) that dispatch() handles — the ground truth."""
    src = (ROOT / "src" / "concordance" / "web" / "api.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    disp = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "dispatch")
    out = set()
    for node in ast.walk(disp):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        if isinstance(left, ast.Name) and left.id == "path":
            comp = node.comparators[0]
            if isinstance(comp, ast.Constant):
                out.add(comp.value)
            elif isinstance(comp, (ast.Tuple, ast.List)):
                out.update(e.value for e in comp.elts if isinstance(e, ast.Constant))
    return out


def test_every_dispatched_path_is_registered():
    registered = {r["path"] for r in api.ROUTES}
    dispatched = _dispatch_paths()
    missing = dispatched - registered
    assert not missing, f"dispatch() handles unregistered paths (add to ROUTES): {sorted(missing)}"


def test_registered_nonserve_paths_are_dispatched():
    dispatched = _dispatch_paths()
    for r in api.ROUTES:
        if r.get("serve"):
            continue  # handled in serve()'s Handler, not dispatch()
        assert r["path"] in dispatched, f"registered path not handled by dispatch(): {r['path']}"


def _mcp_handler_names():
    """AST-extract every tool name _call_tool() handles (`if name == "x"` / `name in (...)`)."""
    src = (ROOT / "src" / "concordance" / "mcp" / "server.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_call_tool")
    out = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == "name":
            comp = node.comparators[0]
            if isinstance(comp, ast.Constant):
                out.add(comp.value)
            elif isinstance(comp, (ast.Tuple, ast.List, ast.Set)):
                out.update(e.value for e in comp.elts if isinstance(e, ast.Constant))
    return out


def test_mcp_schema_handler_parity():
    """Every advertised MCP tool (schema) must have a _call_tool handler, and vice versa —
    the MCP half of the old triplication (a tool declared in the schema list but not handled,
    or handled but never advertised)."""
    from concordance.config import EngineConfig
    from concordance.mcp import server as mcp
    # union of tools advertised on both surfaces
    schema_names = set()
    for surface in ("secular", "witness"):
        schema_names |= {t["name"] for t in mcp._tools_for(EngineConfig(surface))}
    handler_names = _mcp_handler_names()
    unhandled = schema_names - handler_names
    unadvertised = handler_names - schema_names
    assert not unhandled, f"MCP tools advertised but not handled: {sorted(unhandled)}"
    assert not unadvertised, f"MCP tools handled but not advertised: {sorted(unadvertised)}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} route-registry tests passed — single source of truth, no drift.")
