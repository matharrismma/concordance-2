"""A handle is a claim; a signature makes authorship checkable — and the wire can still sign.

THIS FIXES A REGRESSION I INTRODUCED. Retiring `private_key` from the HTTP layer (commit af52593)
was right, but `groups.contribute` had no sovereign replacement, so after that change a contribution
could not be signed over the wire AT ALL — `signed` was always False. That traded a key-on-the-wire
problem for a loss of provable attribution, which is the kind of quiet damage a passing gate will
not show you. Recorded plainly because a fix that breaks something else is not a fix.

The replacement needs no round trip: the contributor already has the text, so it can compute
`groups.text_hash(text)` itself, sign that locally, and pass the attestation. Nothing secret travels.

Groups are pseudonymous and nothing stops anyone typing any name — so a bare handle is a CLAIM, and
`signed` is what distinguishes a claim from something a reader can check. Both are allowed; only one
is provable, and the record says which.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True, scope="module")
def _isolate_data_dir():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


TEXT = "They received the word with all readiness of mind"


def _setup():
    from concordance import groups, identity, signing
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    cfg = EngineConfig("secular")
    g = dispatch("POST", "/groups", {}, {"name": "Bereans", "topic": "Acts 17"}, cfg)[1]
    gid = g.get("id") or (g.get("group") or {}).get("id")
    return groups, identity, signing, cfg, dispatch, gid


def _signed_flag(resp):
    c = resp.get("contribution") or resp
    return (c.get("extra") or {}).get("signed", c.get("signed"))


def test_the_wire_can_sign_a_contribution_again():
    groups, identity, signing, cfg, dispatch, gid = _setup()
    me = identity.create_identity()
    att = signing.sign_seal(groups.text_hash(TEXT), me["private_key"])
    st, r = dispatch("POST", "/group/contribute", {},
                     {"id": gid, "text": TEXT, "handle": "Berean", "attestation": att}, cfg)
    assert st == 200
    assert _signed_flag(r) is True, "the regression is back: the wire cannot sign a contribution"


def test_the_contributor_can_compute_the_hash_itself_without_asking_us():
    """No round trip — you have the text, so you can derive and check the hash yourself."""
    import hashlib
    groups, _i, _s, _c, _d, _gid = _setup()
    assert groups.text_hash(TEXT) == hashlib.sha256(TEXT.encode("utf-8")).hexdigest()
    # trimming is applied before hashing, so what you sign is exactly what is stored
    assert groups.text_hash("  " + TEXT + "  ") == groups.text_hash(TEXT)


def test_a_signature_cannot_be_transplanted_onto_different_text():
    """Otherwise a signature harvested from one contribution would authenticate any other."""
    groups, identity, signing, cfg, dispatch, gid = _setup()
    me = identity.create_identity()
    att = signing.sign_seal(groups.text_hash(TEXT), me["private_key"])
    st, r = dispatch("POST", "/group/contribute", {},
                     {"id": gid, "text": "a different claim entirely", "handle": "Berean",
                      "attestation": att}, cfg)
    assert (r or {}).get("ok") is False
    assert "does not verify" in str(r.get("error", ""))


def test_an_unsigned_claim_is_still_allowed_and_marked_as_a_claim():
    """Pseudonymous groups mean anyone can type any name. We do not pretend to stop that — we record
    honestly that it was not signed, so a bare handle never reads as established."""
    groups, _i, _s, cfg, dispatch, gid = _setup()
    st, r = dispatch("POST", "/group/contribute", {},
                     {"id": gid, "text": "just a claim", "handle": "Someone Else"}, cfg)
    assert st == 200
    assert _signed_flag(r) is False, "an unsigned contribution must not be recorded as signed"


def test_a_bad_attestation_is_refused_rather_than_downgraded_to_unsigned():
    """Silently storing it as 'unsigned' would hide that someone tried to pass a bad signature."""
    groups, identity, signing, cfg, dispatch, gid = _setup()
    me = identity.create_identity()
    att = dict(signing.sign_seal(groups.text_hash(TEXT), me["private_key"]))
    att["sig"] = "AAAA"
    st, r = dispatch("POST", "/group/contribute", {},
                     {"id": gid, "text": TEXT, "handle": "Berean", "attestation": att}, cfg)
    assert (r or {}).get("ok") is False and "does not verify" in str(r.get("error", ""))


def test_the_agent_tool_offers_attestation_and_never_a_private_key():
    import json
    from concordance import groups, identity, mcp, signing
    from concordance.config import EngineConfig
    cfg = EngineConfig("secular")
    tools = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, cfg, {})["result"]["tools"]
    tool = next(t for t in tools if t["name"] == "group_contribute")
    props = tool["inputSchema"]["properties"]
    assert "attestation" in props, "an agent has no way to prove authorship"
    assert "private_key" not in props

    _g, _i, _s, cfg2, dispatch, gid = _setup()
    me = identity.create_identity()
    att = signing.sign_seal(groups.text_hash(TEXT), me["private_key"])
    r = mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "group_contribute",
                               "arguments": {"id": gid, "text": TEXT, "handle": "AgentBerean",
                                             "attestation": att}}}, cfg2, {})
    body = json.loads(r["result"]["content"][0]["text"])
    assert _signed_flag(body) is True


if __name__ == "__main__":
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — the wire can sign again; a handle alone stays a claim.")
