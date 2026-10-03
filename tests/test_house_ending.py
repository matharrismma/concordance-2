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
