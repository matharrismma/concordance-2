"""THE COMMONS · C1b — the shelf flow, reached the two ways anyone reaches this project.

C1a proved the shelf as a module. That is not shipped. `PUNCHLIST.md` sets the completion test for
this unit: *"the whole flow works over HTTP and through an agent."* The lesson behind that wording
is the one this project has hit more than any other — correct server-side and unreachable by the
person (or the agent) is not done. So the same journey is walked twice here, once per surface:

    sign on my own machine → stock my shelf → read it → a commons drop waits → a steward acts

and the two surfaces are then checked AGAINST EACH OTHER: a card stocked over HTTP must be visible
to an agent, and vice versa. One store, two doors — if they ever diverge, this fails.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402


STEWARD_TOKEN = "steward-token-for-this-test-only"


@pytest.fixture(autouse=True)
def _isolated():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    prior_tok = os.environ.get("CONCORDANCE_KEEP_TOKEN")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    os.environ["CONCORDANCE_KEEP_TOKEN"] = STEWARD_TOKEN
    yield
    for k, v in (("CONCORDANCE_DATA_DIR", prior), ("CONCORDANCE_KEEP_TOKEN", prior_tok)):
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _key():
    from concordance import signing
    try:
        return signing.generate_keypair()
    except Exception:  # noqa: BLE001 — no cryptography in this build
        pytest.skip("signing unavailable in this build")


# ---------------------------------------------------------------- the HTTP door

def _http(path, method="GET", body=None, query=None):
    """Call a route the way the server calls it, without binding a port. The route table IS the
    contract (tests/test_routes.py pins it); this exercises the handlers behind it."""
    from concordance.config import EngineConfig
    from concordance.web import api
    return api.dispatch(method, path, query or {}, body, EngineConfig("secular"))


def _sign(signable, priv):
    from concordance import signing
    return signing.sign_bytes(base64.urlsafe_b64decode(signable), priv)


def test_a_member_stocks_a_shelf_over_http_and_anyone_can_read_it():
    priv, pub = _key()
    st, sg = _http("/drop/signable", query={"member": pub, "kind": "recipe",
                                            "subject": "Sourdough, cold-proofed",
                                            "body": "Feed the starter twelve hours ahead; the cold "
                                                    "proof is what makes the crumb open.",
                                            "ring": "shelf"})
    assert st == 200 and sg.get("ok"), (st, sg)
    st, r = _http("/drop", "POST", {"fields": sg["fields"], "signature": _sign(sg["signable"], priv),
                                    "display_name": "Matt Harris"})
    assert st == 200 and r.get("ok"), (st, r)

    st, view = _http("/shelf", query={"member": pub})
    assert st == 200 and view["count"] == 1
    card = view["cards"][0]
    assert "Sourdough" in card["title"]
    assert card["source"]["authority_tier"] == "member", "amplified, never verified by us"
    assert "Matt Harris" in card["source"]["label"], "real names, no tracking"


def test_the_commons_waits_for_a_human_over_http():
    priv, pub = _key()
    st, sg = _http("/drop/signable", query={"member": pub, "kind": "writing", "subject": "On work",
                                            "body": "A piece the member wants the whole fellowship "
                                                    "to read, in their own words.",
                                            "ring": "commons"})
    _st, r = _http("/drop", "POST", {"fields": sg["fields"],
                                     "signature": _sign(sg["signable"], priv)})
    assert r["stage"] == "public_review"
    assert _http("/commons")[1]["count"] == 0, "nothing reaches the commons uncurated"

    st, q = _http("/curate/queue")
    assert st == 200 and q["count"] == 1
    # a typed name is not authority — the steward token is
    st, bare = _http("/curate", "POST", {"card_id": r["card_id"], "action": "promoted",
                                         "steward": "matt", "reason": "true, and kindly put"})
    assert st == 403 and "not authorized" in bare.get("error", ""), (st, bare)
    st, act = _http("/curate", "POST", {"card_id": r["card_id"], "action": "promoted",
                                        "steward": "matt", "reason": "true, and kindly put",
                                        "token": STEWARD_TOKEN})
    assert st == 200 and act.get("ok"), (st, act)
    c = _http("/commons")[1]
    assert c["count"] == 1 and c["authority"] == "member"
    assert _http("/curate/queue")[1]["count"] == 0, "a handled item leaves the queue"


def test_a_forged_signature_is_refused_over_http():
    """The same protection as the module, checked at the door — because the door is what is exposed."""
    priv_a, _pub_a = _key()
    _priv_b, pub_b = _key()
    _st, sg = _http("/drop/signable", query={"member": pub_b, "kind": "note", "subject": "not mine",
                                             "body": "Words attributed to someone who never wrote "
                                                     "them, signed by somebody else."})
    st, r = _http("/drop", "POST", {"fields": sg["fields"],
                                    "signature": _sign(sg["signable"], priv_a)})
    # The door answers 400 with the REASON in it, not a bare ok:false — a refusal the caller cannot
    # read is a refusal they will work around.
    assert st == 400, (st, r)
    assert "does not verify" in r.get("error", ""), r
    assert _http("/shelf", query={"member": pub_b})[1]["count"] == 0


def test_reading_a_shelf_is_not_a_write_and_a_stranger_never_sees_private():
    priv, pub = _key()
    _st, sg = _http("/drop/signable", query={"member": pub, "kind": "note", "subject": "for me",
                                             "body": "Something written only for myself, kept and "
                                                     "not shown to anyone.", "ring": "private"})
    _http("/drop", "POST", {"fields": sg["fields"], "signature": _sign(sg["signable"], priv)})
    assert _http("/shelf", query={"member": pub, "viewer": pub})[1]["count"] == 1
    assert _http("/shelf", query={"member": pub})[1]["count"] == 0
    # `viewer` decides what is SERVED and is not kept: nothing anywhere records who looked.
    store = Path(os.environ["CONCORDANCE_DATA_DIR"]) / "shelves"
    written = "\n".join(p.read_text(encoding="utf-8") for p in store.glob("*.jsonl"))
    assert "viewer" not in written, "a read must leave no trace of the reader"


# --------------------------------------------------------------- the agent door

def _mcp(name, args):
    from concordance import mcp as _mcp_mod
    from concordance.config import EngineConfig
    r = _mcp_mod.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": name, "arguments": args}},
                        EngineConfig("secular"), {"gate_open": False})
    assert "error" not in r, r["error"]
    return json.loads(r["result"]["content"][0]["text"])


def test_an_agent_walks_the_same_flow():
    priv, pub = _key()
    sg = _mcp("shelf_signable", {"member": pub, "kind": "field_note",
                                 "subject": "Reading a creek for a crossing",
                                 "body": "Cross at the wide shallow riffle, never the narrow "
                                         "smooth part — smooth means deep and fast."})
    assert sg.get("ok"), sg
    r = _mcp("shelf_drop", {"fields": sg["fields"], "signature": _sign(sg["signable"], priv),
                            "display_name": "Matt Harris"})
    assert r.get("ok"), r
    view = _mcp("shelf_read", {"member": pub})
    assert view["count"] == 1 and "creek" in view["cards"][0]["title"].lower()
    assert _mcp("commons_read", {})["count"] == 0
    assert _mcp("curate_queue", {})["count"] == 0, "a shelf drop needs no steward"


def test_the_shelf_tools_are_on_the_secular_surface():
    """A maker who never opened the Gate still gets a shelf. The Commons is the front door, not a
    reward for confessing — the gate is on the Word, never on the workbench."""
    from concordance import mcp as _mcp_mod
    from concordance.config import EngineConfig
    names = {t["name"] for t in _mcp_mod.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        EngineConfig("secular"), {"gate_open": False})["result"]["tools"]}
    for t in ("shelf_signable", "shelf_drop", "shelf_read", "commons_read",
              "curate_queue", "curate"):
        assert t in names, f"{t} is not reachable without the Gate"


def test_one_store_two_doors():
    """The regression that would matter most: an agent and a browser looking at different shelves."""
    priv, pub = _key()
    sg = _mcp("shelf_signable", {"member": pub, "kind": "build", "subject": "A bench from one board",
                                 "body": "Rip the board in three, laminate the legs, and the whole "
                                         "bench comes out of eight feet of pine."})
    _mcp("shelf_drop", {"fields": sg["fields"], "signature": _sign(sg["signable"], priv)})
    assert _http("/shelf", query={"member": pub})[1]["count"] == 1, "agent wrote, HTTP cannot see it"

    _st, sg2 = _http("/drop/signable", query={"member": pub, "kind": "question",
                                              "subject": "How do you keep pine from denting?",
                                              "body": "Asking the people who actually work with "
                                                      "soft wood every day.", "ring": "commons"})
    _st, r2 = _http("/drop", "POST", {"fields": sg2["fields"],
                                      "signature": _sign(sg2["signable"], priv)})
    q = _mcp("curate_queue", {})
    assert q["count"] == 1 and q["items"][0]["card_id"] == r2["card_id"], \
        "HTTP wrote, the agent cannot see it"
    # the agent door enforces the SAME rule — the authorization lives in the module, not the route
    assert "not authorized" in str(_mcp("curate", {
        "card_id": r2["card_id"], "action": "promoted", "steward": "matt",
        "reason": "a real question from someone doing the work"}).get("error", ""))
    act = _mcp("curate", {"card_id": r2["card_id"], "action": "promoted", "steward": "matt",
                          "reason": "a real question from someone doing the work",
                          "token": STEWARD_TOKEN})
    assert act.get("ok"), act
    assert _http("/commons")[1]["count"] == 1, "the agent's act is invisible over HTTP"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
