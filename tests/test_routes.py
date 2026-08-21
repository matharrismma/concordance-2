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

import os  # noqa: E402

from concordance.web import api  # noqa: E402
from concordance.config import EngineConfig  # noqa: E402

# The historical hand-maintained values, verbatim — the behavior the server had before the
# registry refactor. The derived sets must equal these exactly.
GOLDEN_API_GET = {
    "/health",
    # An operator door, added 2026-08-01 to settle whether the freeze design rests on a
    # true belief: it reports where the resident corpus actually spends its memory
    # (cards vs token index), from the live process, sampled and labelled as an estimate.
    "/health/memory",
    # The clock, added 2026-08-04 at Matt's direction: "the actual date and time always
    # current for the time zone you are in." An agent's own 'today' is its training cutoff.
    "/now",
    "/identity", "/profile", "/profile/served", "/profile/community", "/profile/path", "/route", "/bind/challenge", "/thread/digest", "/thread/recall", "/thread/lineage", "/thread/recalled", "/land", "/cards/for-the-group",
    "/search", "/seal", "/resolve", "/word_study",
    "/card", "/cards", "/cards/stats", "/daily", "/witness", "/grid", "/grid/dimension",
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
    "/decks", "/decks/predict", "/deck", "/deck/open",
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
    "/contact",  # deliberate addition — the public contact form (a JSON write, rate-limited)
    "/connect/event",  # the calendar pilot — the one on-behalf write, behind the consent lock
    "/narratives",  # deliberate addition (storyboards: common narratives charted in the Bible; movements mix and match)
    "/study_find",  # deliberate addition (the quick-find index across the whole reference section)
    "/capabilities",  # deliberate addition (the live capability statement — restored from 1.0)
    "/kernel",  # the gate kernel doctrine — the five moves + covenant, published where agents read (task #152, 2026-08-15)
    "/kernel/gate",  # POST an api:True route (like /drop/report) — run one proposed state-change through the kernel (task #152)
    "/playbook",  # the Playbook — the Body's testimony ledger, "Canon commands, Playbook remembers" (task #153, 2026-08-15)
    "/playbook/signable", "/playbook/submit",  # the two-step signed write (bytes-to-sign, then submit)
    "/plow",  # The Plow — a STATELESS personal-formation engine; the walk lives on the device (task #155, 2026-08-15)
    "/activity.json",  # the .org "under the hood" feed (recent public seals + counts, 2026-08-05)
    "/build.json",  # deployment provenance: protocol + profiles + tool_catalog_hash (red team R-14, 2026-08-06)
    "/mesh/signable",  # deliberate addition (the bytes to sign, so a key never crosses the wire)
    "/attest",  # deliberate addition (bear witness to a record you hold; GET lists the witnesses)
    "/wants",   # deliberate addition (the WANT LIST — the library grows by its misses; 2026-08-01)
    # deliberate addition 2026-08-01 — what the engine writes goes in wearing its open question,
    # and the first reader to recall it is asked to close it. `/unchecked` publishes the standing
    # list; `/unchecked/answer` is the door the ask on every such card points at.
    "/unchecked", "/unchecked/answer",
}
# /search moved OUT of this set on 2026-07-31 and into GOLDEN_READ_LIMITED — a read and a write
# are not the same risk, and the one client the shared cap refused most was ClaudeBot.
GOLDEN_RATELIMITED = {
    "/unchecked/answer",   # deliberate addition 2026-08-01 — anyone may answer, so it is rate-limited
    "/verify", "/derivation/verify", "/mcp",
    # the six profile mounts (task #123) — same engine, narrow doors; goldens updated as a decision
    "/mcp/core", "/mcp/library", "/mcp/sovereign", "/mcp/coach", "/mcp/witness", "/mcp/community", "/ask", "/speak", "/bind", "/book", "/fork", "/defer", "/inlet", "/returns", "/days", "/apothecary/propose", "/pins", "/pins/done",
    "/threads", "/threads/search",
    "/coach/mastery", "/identity/create", "/identity/verify", "/badges",
    "/profile/signable", "/profile/save", "/profile/erase",  # the optional sovereign profile (signed writes)
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
    "/contact",  # deliberate addition — the public contact form (a JSON write, rate-limited)
    "/connect/event",  # the calendar pilot — the one on-behalf write, behind the consent lock
    "/audit",   # deliberate addition (the Auditor) — goldens update ONLY with a new route
    "/context/run",  # the context loop — node-local, gated by CONCORDANCE_SOVEREIGN_NODE (off on the shared server)
    "/chess",   # deliberate addition (the chess verifier) — game theory, applied and sealable
    "/attest",  # deliberate addition — a write, so rate-limited like every other write
    "/want",    # deliberate addition — opening a want is a write (the hive's return-point)
    "/kernel/gate",  # run one proposed state-change through the kernel — rate-limited like every POST (task #152)
    "/playbook/signable", "/playbook/submit",  # the Playbook two-step signed write — rate-limited like every write (task #153)
    "/plow",  # The Plow POST computes a transition — rate-limited like every POST (task #155)
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


def test_context_run_is_off_on_the_shared_server_by_default():
    """The context loop is node-local. On the shared server (flag unset) it MUST refuse, so a caller's
    private text never reaches our box — invariant #2, enforced at the door. Fast: it refuses before
    the engine is ever touched."""
    old = os.environ.pop("CONCORDANCE_SOVEREIGN_NODE", None)
    try:
        status, payload = api.dispatch("POST", "/context/run", {},
                                       {"text": "my mom said 2 + 2 = 4"}, EngineConfig(), False)
        assert status == 403 and "sovereign node" in str(payload).lower()
    finally:
        if old is not None:
            os.environ["CONCORDANCE_SOVEREIGN_NODE"] = old


def test_profile_routes_are_sovereign_signed_writes():
    """GET is a read by fingerprint; a save is a SIGNED write (only the key's owner); a forged
    signature is refused. The server creates no keys and stores no password."""
    import tempfile
    from concordance import identity, signing
    from concordance import profile as _profile
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    try:
        try:
            me = identity.derive_identity("teach us to number our days that we may gain a heart of wisdom")
        except RuntimeError:
            return  # needs cryptography for a real key
        s, p = api.dispatch("GET", "/profile", {"fp": me["id"]}, None, EngineConfig(), False)
        assert s == 200 and p["profile"] == {}                      # anonymous until you save
        patch = {"shelf": ["woodcraft-and-camping"], "display_name": "a pilgrim"}
        sig = signing.sign_bytes(_profile.signable(me["public_key"], patch, "n1"), me["private_key"])
        s, p = api.dispatch("POST", "/profile/save", {},
                            {"public_key": me["public_key"], "patch": patch, "nonce": "n1", "signature": sig},
                            EngineConfig(), False)
        assert s == 200 and p["profile"]["display_name"] == "a pilgrim"
        forger = identity.create_identity()
        fsig = signing.sign_bytes(_profile.signable(me["public_key"], {"x": 1}, "n2"), forger["private_key"])
        s, _ = api.dispatch("POST", "/profile/save", {},
                            {"public_key": me["public_key"], "patch": {"x": 1}, "nonce": "n2", "signature": fsig},
                            EngineConfig(), False)
        assert s == 403                                             # forged signature refused
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_DATA_DIR", None)
        else:
            os.environ["CONCORDANCE_DATA_DIR"] = prior


def test_witness_route_serves_attributed_pd_words_and_holds_the_gate():
    """GET /witness returns the cloud's VERBATIM, attributed words for a query — public (the commons),
    proposes-not-confirms — and never voices a non-public-domain passage, even if it is in the file."""
    import json
    import tempfile
    prior = os.environ.get("CONCORDANCE_WITNESSES")
    d = tempfile.mkdtemp()
    p = Path(d) / "witnesses.jsonl"
    p.write_text(
        json.dumps({"text": "a lamp trimmed and burning is tended before the dark comes",
                    "witness": "TEST-WITNESS", "work": "TEST-WORK", "ref": "ch.1", "id": "w1",
                    "source": "test://pd", "public_domain": True}) + "\n" +
        json.dumps({"text": "a copyrighted lamp passage that must never be voiced here",
                    "witness": "TEST-LIVING", "work": "X", "ref": "1", "id": "c1",
                    "source": "test://c", "public_domain": False}) + "\n",
        encoding="utf-8")
    os.environ["CONCORDANCE_WITNESSES"] = str(p)
    try:
        s, _ = api.dispatch("GET", "/witness", {}, None, EngineConfig(), False)
        assert s == 400                                             # q required
        s, payload = api.dispatch("GET", "/witness", {"q": "how do I tend a lamp"}, None, EngineConfig(), False)
        assert s == 200 and payload["proposes"] is True and payload["confirms"] is False
        seeing = payload["seeing"]
        assert seeing and seeing[0]["witness"] == "TEST-WITNESS"    # verbatim, attributed
        assert all(x["witness"] != "TEST-LIVING" for x in seeing)   # the PD gate holds at the route
    finally:
        if prior is None:
            os.environ.pop("CONCORDANCE_WITNESSES", None)
        else:
            os.environ["CONCORDANCE_WITNESSES"] = prior


def test_context_run_opens_and_validates_when_enabled():
    """With the flag set (a sovereign node), the door opens and validates the body — still fast: an
    empty body is 400 before the verifier loads."""
    old = os.environ.get("CONCORDANCE_SOVEREIGN_NODE")
    os.environ["CONCORDANCE_SOVEREIGN_NODE"] = "1"
    try:
        status, _ = api.dispatch("POST", "/context/run", {}, {}, EngineConfig(), False)
        assert status == 400                              # enabled, but text required
    finally:
        if old is None:
            os.environ.pop("CONCORDANCE_SOVEREIGN_NODE", None)
        else:
            os.environ["CONCORDANCE_SOVEREIGN_NODE"] = old


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


def test_activity_json_is_public_and_leaks_nothing():
    """The .org 'under the hood' feed (2026-08-05). Every seal it lists is ALREADY public at
    /s/<hash>, so the stream leaks nothing new — but the payload must carry ONLY the whitelisted
    fields, never a body, claim text, operator datum, IP, or token. Public on BOTH surfaces (the
    record of the work is not witness-only), and each row's hash is a real re-checkable address."""
    import json as _json
    from concordance.web.api import dispatch
    from concordance.config import EngineConfig
    for surface in ("secular", "witness"):
        st, payload = dispatch("GET", "/activity.json", {}, None, EngineConfig(surface))
        assert st == 200, surface
        assert set(payload.keys()) <= {"surface", "recent", "totals", "note"}
        for row in payload["recent"]:
            assert set(row.keys()) == {"hash", "short", "verdict", "domain", "kind", "when"}, row
        # the whole payload, serialized, must contain none of these forbidden tokens
        blob = _json.dumps(payload).lower()
        for forbidden in ("\"body\"", "raw_text", "claim_text", "\"ip\"", "token",
                          "private", "passphrase", "operator", "x-keep-token"):
            assert forbidden not in blob, f"activity.json leaked {forbidden!r}"


def test_build_json_is_deployment_provenance_and_leaks_nothing():
    """The build-provenance endpoint (red team R-14, 2026-08-06). It ties the SERVED contract to a
    tool_catalog_hash a reviewer can compare against the repo, so a claimed fix can be confirmed in
    production. It carries protocol/profile metadata ONLY — never a body, key, or personal datum,
    and the catalog hash is stable and deterministic (sorted name:effect over all profiles)."""
    import json as _json
    from concordance.web.api import dispatch
    from concordance.config import EngineConfig
    for surface in ("secular", "witness"):
        st, payload = dispatch("GET", "/build.json", {}, None, EngineConfig(surface))
        assert st == 200, surface
        assert set(payload.keys()) <= {"surface", "package_version", "protocol", "profiles",
                                       "tool_catalog_hash", "note", "unavailable"}
        assert "unavailable" not in payload, payload
        assert len(payload["tool_catalog_hash"]) == 64  # sha256 hex
        assert isinstance(payload["profiles"], dict) and payload["profiles"]
        # metadata only — no bodies, keys, or personal data may ride along
        blob = _json.dumps(payload).lower()
        for forbidden in ("raw_text", "claim_text", "\"ip\"", "private_key", "passphrase",
                          "x-keep-token", "signature"):
            assert forbidden not in blob, f"build.json leaked {forbidden!r}"
    # the hash is deterministic across calls (same code => same catalog)
    a = dispatch("GET", "/build.json", {}, None, EngineConfig("secular"))[1]["tool_catalog_hash"]
    b = dispatch("GET", "/build.json", {}, None, EngineConfig("secular"))[1]["tool_catalog_hash"]
    assert a == b
