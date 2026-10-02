"""THE FIVE DOORS (Matt, 2026-10-02: "I don't want 15 things. I want 1-5 amazing things."). One source
of truth — concordance.doors — read by the site spine, the agent catalog and /capabilities, so the five
verbs cannot drift between faces. docs/FIVE_DOORS_MAP.md is the audit; this pins what it decided."""
import re
from pathlib import Path

from concordance import doors
from concordance.engine import EngineConfig
from concordance.mcp.server import handle
from concordance.web import api

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"


def _catalog():
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, EngineConfig())
    return r["result"]["tools"]


def test_five_verbs_each_with_a_door_page_that_exists():
    assert doors.VERBS == ["CHECK", "FIND", "WALK", "KEEP", "WORD"]
    for v in doors.VERBS:
        page = doors.DOOR_PAGE[v]
        assert (SITE / page.lstrip("/")).exists(), f"{v}'s door page is missing: {page}"
        assert doors.LEAD[v] and doors.TOOL_DOORS[v]


def test_every_catalog_tool_belongs_to_one_verb_and_the_doors_are_real():
    names = {t["name"] for t in _catalog()}
    untagged = sorted(names - set(doors.TOOL_VERB))
    assert not untagged, f"tools with no verb: {untagged}"
    stale = sorted(set(doors.TOOL_VERB) - names)
    assert not stale, f"verb map names tools that no longer exist: {stale}"
    for v, ds in doors.TOOL_DOORS.items():
        for d in ds:
            assert d in names and doors.TOOL_KIND[d] == "DOOR" and doors.TOOL_VERB[d] == v


def test_a_new_agent_meets_the_doors_first_and_every_tool_leads_with_its_verb():
    cat = _catalog()
    assert len(cat) == 97                                   # the golden holds — nothing removed
    first = [t["name"] for t in cat[:4]]
    assert first == doors.TOOL_DOORS["CHECK"], first        # CHECK's doors open the list
    kinds = [doors.TOOL_KIND[t["name"]] for t in cat]
    verbs = [doors.TOOL_VERB[t["name"]] for t in cat]
    # sorted by verb order, doors before internals within a verb
    assert verbs == sorted(verbs, key=doors.VERBS.index)
    for v in doors.VERBS:
        ks = [k for k, vv in zip(kinds, verbs) if vv == v]
        assert ks == sorted(ks, key={"DOOR": 0, "INTERNAL": 1, "PLUMBING": 2}.get), v
    for t in cat:
        assert t["description"].startswith(f"[{doors.tag(t['name'])}]"), t["name"]


def test_capabilities_carries_the_doors_on_both_doors():
    r = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "capabilities", "arguments": {}}}, EngineConfig())
    body = r["result"]["content"][0]["text"] if "content" in r["result"] else str(r["result"])
    assert '"doors"' in body and '"CHECK"' in body
    st, payload = api.dispatch("GET", "/capabilities", {}, None, EngineConfig())[:2]
    assert st == 200 and set(payload["doors"]) == set(doors.VERBS)


def test_the_spine_shows_the_same_five_verbs_on_every_face():
    shell = (SITE / "shell.js").read_text(encoding="utf-8")
    for label, href in (("Check", "/"), ("Find", "/explore.html"), ("Walk", "/situations.html"),
                        ("Keep", "/profile.html"), ("Word", "https://narrowhighway.org/bible.html")):
        assert re.search(r'label:\s*"%s",\s*href:\s*"%s"' % (label, re.escape(href)), shell), label
    desk = (SITE / "index.html").read_text(encoding="utf-8")
    nav = desk.split('aria-label="Navigate"', 1)[1].split("</nav>", 1)[0]
    assert [m for m in re.findall(r'href="([^"]+)"', nav)] == \
        ["/bible.html", "/situations.html", "/checkit.html", "/explore.html", "/profile.html"]
    grid = desk.split('<div class="doors">', 1)[1].split("</div>", 1)[0]
    assert len(re.findall(r"<a href=", grid)) == 6                  # five doors + about


def test_the_manifesto_keeps_its_prose_and_loses_its_lobby():
    com = (SITE / "com.html").read_text(encoding="utf-8")
    assert "A deterministic model of reality." in com                 # the identity line stays
    for gone in ("/halls.html", "/coach.html", "/capabilities", "/systems.html", "/steward.html"):
        assert f'href="{gone}"' not in com, f"com.html still links the lobby: {gone}"   # (the live-count fetch of /capabilities is not a link)


def test_retired_pages_answer_with_where_they_went():
    for path, dest in (("/atlas.html", "/explore.html"), ("/improve.html", "/workshop.html"),
                       ("/crossing.html", "/concordance.html"), ("/encyclopedia.html", "/characters.html")):
        assert api._RETIRED[path] == dest
        assert not (SITE / path.lstrip("/")).exists(), f"{path} still ships as a file"
    assert api._retire_to("/encyclopedia.html", "ref=Slave") == "/characters.html?ref=Slave"   # the query rides along
