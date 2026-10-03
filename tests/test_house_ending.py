"""THE HOUSE ENDING (Matt, 2026-10-02: "keep going API"). Every door's answer — on the agent door and
its web twin — ends the same way: a verdict or a card · the trail · a seal · ONE next step. The next
step is a rule per door filled with the answer's own ids; it names a real tool; a non-door tool gets
no ending; an error gets no ending."""
import json
import os
import tempfile

# a scratch keeping: `verify` mints a receipt card, and minting touches the corpus — on a laptop the
# real keeping is a minutes-long load (OneDrive rehydrates the shards); the ending is what is pinned
os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-house-")

from concordance import doors  # noqa: E402
from concordance.engine import EngineConfig
from concordance.mcp.server import handle
from concordance.web import api


def _call(name, args):
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}, EngineConfig())
    body = json.loads(r["result"]["content"][0]["text"])
    return body, r["result"].get("isError")


def _catalog_names():
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, EngineConfig())
    return {t["name"] for t in r["result"]["tools"]}


def _assert_house(body, door, kind=None):
    h = body["house"]
    assert h["door"] == door and h["next_step"]["do"] and h["next_step"]["door"] in doors.VERBS, h
    if kind:
        assert h["kind"] == kind, h
    if h["trail"]:
        assert h["trail"] in body, (h["trail"], sorted(body)[:12])          # the trail pointer names a real key
    if "tool" in h["next_step"]:
        assert h["next_step"]["tool"] in _catalog_names(), h["next_step"]  # the one step is a real door
    assert h["ends"] == "a verdict or a card · the trail · a seal · one next step"
    return h


def test_check_verify_ends_with_a_verdict_a_trail_a_seal_and_one_step():
    body, err = _call("verify", {"mode": "numeric", "params": {"numeric_expr": "2+2", "claimed_value": 4}})
    assert not err
    h = _assert_house(body, "CHECK", "verdict")
    assert body["verdict"] == "HOLDS" and h["seal"] and h["next_step"]["tool"] == "seal_fetch"
    assert h["next_step"]["params"]["hash"] == body["seal"]["content_hash"]
    broken, _ = _call("verify", {"mode": "numeric", "params": {"numeric_expr": "2+2", "claimed_value": 5}})
    hb = _assert_house(broken, "CHECK", "verdict")
    assert broken["verdict"] == "BROKEN" and hb["next_step"]["tool"] == "verify" and "broke" in hb["next_step"]["do"]


def test_find_and_keep_doors_end_the_same_way():
    body, err = _call("lookup", {"kind": "element", "params": {"symbol": "Fe"}})
    assert not err and body["found"]
    h = _assert_house(body, "FIND", "value")
    assert h["next_step"]["tool"] == "verify"                                 # a found value becomes a sealable claim
    body, err = _call("find_verifier", {"query": "the speed of light is 299792458 m/s"})
    assert not err
    h = _assert_house(body, "CHECK", "route")
    assert h["next_step"]["tool"] == "verify" and h["next_step"]["params"]["domain"]
    assert h["next_step"]["params"]["claim"] == "the speed of light is 299792458 m/s"   # the caller's words ride forward
    body, err = _call("decks", {})
    assert not err
    h = _assert_house(body, "KEEP", "cards")
    assert h["next_step"]["tool"] in ("deck_open", "study_create")


def test_an_internal_points_back_to_its_door_and_an_error_carries_no_ending():
    body, err = _call("kernel", {})
    assert not err
    h = body["house"]                                                        # an internal of CHECK
    assert h["door"] == "CHECK" and h["kind"] == "internal" and h["trail"] is None
    assert h["next_step"]["tool"] == "verify" and "door it serves" in h["next_step"]["do"]
    body, err = _call("now", {})
    assert not err and body["house"]["kind"] == "plumbing" and body["house"]["next_step"]["tool"] == "search"
    body, err = _call("card_get", {})                                        # a door, but an error: no ending
    assert err and "house" not in body


def test_the_web_twin_ends_the_same_way():
    st, payload = api.dispatch("GET", "/lookup", {"kind": "element", "symbol": "Fe"}, None, EngineConfig())[:2]
    assert st == 200 and payload["house"]["door"] == "FIND" and payload["house"]["next_step"]["tool"] == "verify"
    st, payload = api.dispatch("GET", "/find_verifier", {"q": "the boiling point of water is 100 C"}, None, EngineConfig())[:2]
    assert st == 200 and payload["house"]["door"] == "CHECK"
    st, payload = api.dispatch("GET", "/lookup", {"kind": "nonsense"}, None, EngineConfig())[:2]
    assert "house" not in payload or payload.get("found") is False           # a miss is still an answer: one step offered


def test_house_never_raises_on_a_strange_answer():
    for tool in sorted(doors.ALL_DOORS):
        h = doors.house(tool, {})                                             # empty answer
        assert h["door"] in doors.VERBS and h["next_step"]["do"]
        h = doors.house(tool, {"results": "not-a-list", "trail": None, "seal": 3, "candidates": [1, 2]})
        assert h["next_step"]["do"]


def _schema():
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, EngineConfig())
    return {t["name"]: set(((t.get("inputSchema") or {}).get("properties") or {})) for t in r["result"]["tools"]}


def _executable_as_given(h, props):
    """The one step names a real tool and carries ONLY arguments that tool declares — a step that a
    caller follows as given must run, not silently search for nothing (caught 2026-10-02: ask steps
    carried `q`, the tool reads `text`; verify steps carried `claim`, the tool took none)."""
    nxt = h["next_step"]
    if "tool" not in nxt:
        return
    assert nxt["tool"] in props, nxt
    extra = set(nxt.get("params") or {}) - props[nxt["tool"]]
    assert not extra, f"{nxt['tool']} does not take {sorted(extra)}: {nxt}"


def test_a_crisis_ends_with_help_first_and_no_tool():
    """A crisis answer carries no path on purpose; the generic ending reached it and pointed a cry at
    `discern` ("name what you brought"). Help IS the ending — the number first, no tool, because a
    real person performs this step, not the engine."""
    body, err = _call("ask", {"text": "i want to end my life"})
    assert not err and body["kind"] == "crisis"
    h = body["house"]
    assert h["door"] == "WALK" and h["kind"] == "help" and h["trail"] == "resources"
    assert "988" in h["next_step"]["do"] and "real person" in h["next_step"]["do"]
    assert "tool" not in h["next_step"], h["next_step"]
    assert h["next_step"]["do"].startswith("Reach a real person right now")


def test_a_first_person_ache_is_met_as_comfort_with_the_number_in_hand():
    """"i feel hopeless and alone" is comfort, not crisis (the crisis net is never widened with bare
    emotion words) — but it was told "go to the person — plainly and gently": there is no other
    person. The ending now sits with the word and names someone who loves them; and because
    hopelessness is despair-grade, the helpline rides along quietly as a resource."""
    body, err = _call("ask", {"text": "i feel hopeless and alone"})
    assert not err and body["kind"] == "comfort"
    assert body["path"]["type"] == "comfort" and "go to the person" not in body["path"]["step"].lower()
    assert "someone who loves you" in body["path"]["step"]
    assert body["resources"] and "988" in body["resources"][0]["label"]
    h = _assert_house(body, "WALK", "path")
    assert h["next_step"]["do"] == body["path"]["step"]            # the path IS the ending
    _executable_as_given(h, _schema())
    body, err = _call("ask", {"text": "I feel anxious about my exam"})
    assert not err and body["kind"] == "comfort" and "resources" not in body   # not despair-grade


def test_an_empty_ask_is_an_error_on_the_agent_door_as_on_the_web():
    body, err = _call("ask", {"text": "   "})
    assert err and "house" not in body and "text required" in body["error"]
    body, err = _call("ask", {"q": "i feel hopeless and alone"})            # the wrong key is an empty ask
    assert err


def test_a_plain_claim_through_the_agent_door_is_verified_as_given():
    """find_verifier's ending hands `verify` {claim, domain}; the tool must take exactly that (the
    web twin has since 2026-09-05) and answer in the one verify shape: verdict, trail, seal."""
    body, err = _call("verify", {"claim": "2+2=4"})
    assert not err and body["verdict"] == "HOLDS" and body["claims_found"] == 1 and body["trail"][0]["status"] == "CONFIRMED"
    h = _assert_house(body, "CHECK", "verdict")
    assert h["next_step"]["tool"] == "seal_fetch" and h["seal"]
    body, err = _call("verify", {"claim": "the speed of light is 299792458 m/s", "domain": "astronomy"})
    assert not err and body["verdict"] == "HOLDS" and body["domain_hint"] == "astronomy"
    assert body["checks"][0]["domain"] == "physical_constants"        # the extractor decides, not the hint
    body, err = _call("verify", {"claim": "iron melts at 1538 C"})
    assert not err and body["verdict"] == "INCOMPLETE" and body["gap_at"] == "iron melts at 1538 C"
    assert "NOTHING about whether the claim is true" in body["means"]
    h = _assert_house(body, "CHECK", "verdict")
    assert h["next_step"]["tool"] == "find_verifier" and h["next_step"]["params"] == {"query": "iron melts at 1538 C"}
    _executable_as_given(h, _schema())
    body, err = _call("verify", {"claim": "2+2=5"})
    assert not err and body["verdict"] == "BROKEN" and body["house"]["next_step"]["tool"] == "verify"


def test_every_house_step_is_executable_as_given():
    """Sweep every door with empty and rich synthetic answers (plus the real calls above): each next
    step's params are a subset of what the named tool declares."""
    props = _schema()
    rich = {"verdict": "INCOMPLETE", "claim": "iron melts at 1538 C", "gap_at": "iron melts at 1538 C",
            "trail": [{"id": "a1", "status": "NOT_APPLICABLE", "claim": "iron melts at 1538 C"}],
            "seal": {"cite_url": "/s/abc", "content_hash": "abc"}, "results": [{"id": "card-1", "title": "x"}],
            "candidates": [{"domain": "physics"}], "checks": [{"claim": "2+2=4"}], "query": "iron",
            "found": True, "kind": "element", "id": "card-1", "word": "iron", "ref": "John 1:1",
            "path": {"step": "Sit with John 1:1", "anchor": {"ref": "John 1:1"}, "type": "comfort"},
            "position": {"unit": "u1"}, "detail": "iron", "input": "iron", "strongs": "G26",
            "fingerprint": "fp", "key": "k", "cards": ["card-1"], "decks": [{"id": "d1"}], "source": {"url": "u"}}
    for tool in sorted(doors.ALL_DOORS):
        for answer in ({}, rich, {**rich, "verdict": "BROKEN", "trail": [{"id": "a1", "status": "MISMATCH"}]},
                       {**rich, "verdict": "HOLDS"}, {**rich, "found": False, "results": [], "candidates": [],
                                                       "checks": [], "path": {"step": "x", "type": "claim"}},
                       {"kind": "crisis", "resources": [{"label": "Call or text 988"}]}):
            _executable_as_given(doors.house(tool, answer, {"query": "iron"}), props)
