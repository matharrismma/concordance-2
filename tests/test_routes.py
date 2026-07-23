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
    "/health", "/identity", "/route", "/bind/challenge", "/thread/digest", "/thread/recall", "/thread/lineage", "/thread/recalled", "/land", "/cards/for-the-group",
    "/search", "/seal", "/resolve", "/word_study",
    "/card", "/cards", "/cards/stats", "/daily", "/grid", "/grid/dimension",
    "/card/connections", "/graph", "/locate", "/library/health", "/growth",
    "/thread", "/threads", "/threads/search", "/thread/verify", "/passage", "/apothecary",
    "/pronounce", "/cross_refs", "/word_occurrences", "/original", "/canon",
    "/commentary", "/journal", "/journal/dates", "/steward", "/tsk",
    "/character", "/characters", "/prophecy",
    "/coach/subjects", "/coach/overview", "/coach/unit", "/coach/next", "/coach/recommend", "/coach/guidance",
    "/identity/fingerprint", "/identity/describe", "/badges", "/study", "/card.html",
    "/groups", "/group", "/seeds", "/almanac",
    "/codex", "/codex/scripture", "/codex/themes", "/codex/connections", "/codex/artifact", "/codex/verify",
    "/teachings",
}
GOLDEN_RATELIMITED = {
    "/verify", "/derivation/verify", "/search", "/mcp", "/ask", "/speak", "/bind", "/book", "/fork", "/defer", "/inlet", "/returns", "/days", "/apothecary/propose", "/pins", "/pins/done",
    "/threads", "/threads/search",
    "/coach/mastery", "/identity/create", "/identity/verify", "/badges",
    "/study", "/study/export", "/study/import",
    "/groups", "/group", "/group/join", "/group/contribute",
    "/audit",   # deliberate addition (the Auditor) — goldens update ONLY with a new route
}


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
