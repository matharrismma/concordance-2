"""No private key crosses the wire — asserted over the HTTP layer as a whole.

Contract §3: keys "are born on the device… the server holds only public keys and verifies signed
challenges." §5's DONE line: "no private key ever crosses the wire." That line was being read
narrowly — the server never RETURNS one — while FIVE handlers happily read `private_key` out of a
request body: /mesh/post, /mesh/door, /badges, /study/export, /group/contribute. Inbound is still
on the wire.

Retirement was safe by the time it happened, and the order mattered: the browser had to be able to
sign first (site/nh-keys.js, commit 4a86cf8) or removing the parameter would have broken real users
to satisfy a checklist. A grep of site/ confirmed no client ever actually SENT one.

THE DISTINCTION THIS TEST ENCODES: a private key as a LOCAL LIBRARY argument is legitimate — someone
running the engine on their own box may hand their own key to mesh.post_message(), and nothing
travels. A private key as a WIRE parameter is not. So the module signatures keep `private_key` and
the HTTP layer must never source one from a request. The guard is written over the whole file by AST,
not against the five known handlers, so a sixth cannot be added quietly.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import ast
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

API = ROOT / "src" / "concordance" / "web" / "api.py"


@pytest.fixture(autouse=True, scope="module")
def _isolate_data_dir():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


def test_no_http_handler_reads_a_private_key_out_of_a_request():
    """AST, not grep: find every `body.get("private_key")` / `query.get("private_key")` style read
    anywhere in the HTTP layer. Comments mentioning the retired parameter are fine; CODE is not."""
    tree = ast.parse(API.read_text(encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not (isinstance(fn, ast.Attribute) and fn.attr == "get"):
            continue
        src = fn.value
        if not (isinstance(src, ast.Name) and src.id in ("body", "query", "headers")):
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                    and "private" in arg.value.lower() and "key" in arg.value.lower():
                offenders.append(f"{src.id}.get({arg.value!r}) at line {node.lineno}")
    assert offenders == [], (
        "the HTTP layer reads a private key from a request — a secret in a request body is a secret "
        f"on the wire (contract §3): {offenders}")


def test_a_private_key_sent_anyway_simply_does_nothing():
    """The private key is inert: the HTTP layer ignores it (the AST guard above proves no handler
    reads it), so it is never used to sign. Under the signed-posts policy (2026-08-21) the resulting
    unsigned normal post is then refused — so a leaked key buys nothing, not even an unsigned post.
    Silently signing on the sender's behalf would be the failure; it does not happen."""
    from concordance import identity, mesh
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch

    cfg = EngineConfig("secular")
    me = identity.create_identity()
    fp = mesh.register_node(me["public_key"], "alpha",
                            confession="Jesus Christ is Lord and Messiah")["fp"]

    st, r = dispatch("POST", "/mesh/post", {},
                     {"fp": fp, "text": "sneaking a key", "kind": "word",
                      "private_key": me["private_key"]}, cfg)
    assert st == 200
    assert r.get("signed") is not True, "a private key in the body was used to sign — it must be inert"
    assert r["ok"] is False and "signed" in r.get("error", ""), \
        "the leaked key is ignored and the unsigned post refused — it must buy nothing"


def test_the_sovereign_path_still_works_and_unsigned_is_refused_except_a_cry_for_help():
    import base64
    from concordance import identity, mesh, signing
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch

    cfg = EngineConfig("secular")
    me = identity.create_identity()
    fp = mesh.register_node(me["public_key"], "beta",
                            confession="Jesus Christ is Lord and Messiah")["fp"]

    text = "signed on my own machine"
    s = mesh.signable_message(fp, text, kind="word")
    sig = signing.sign_bytes(base64.urlsafe_b64decode(s["canonical_b64u"] + "=="),
                             me["private_key"])
    st, r = dispatch("POST", "/mesh/post", {},
                     {"fp": fp, "text": text, "kind": "word", "nonce": s["nonce"],
                      "created_at": s["created_at"], "signature": sig}, cfg)
    assert st == 200 and r["ok"] is True and r["signed"] is True
    assert r["id"] == s["would_be_id"]

    # a NORMAL unsigned post is refused (policy 2026-08-21): otherwise anyone could post in any node's
    # name (impersonation), and everyone who can post already holds a key — so no one is turned away.
    st2, r2 = dispatch("POST", "/mesh/post", {},
                       {"fp": fp, "text": "no key, no signature", "kind": "word"}, cfg)
    assert st2 == 200 and r2["ok"] is False and "signed" in r2.get("error", "")

    # THE ONE EXCEPTION — crisis-first: a cry for help is heard even unsigned, delivered signed=False.
    st3, r3 = dispatch("POST", "/mesh/post", {},
                       {"fp": fp, "text": "I want to kill myself", "kind": "word"}, cfg)
    assert st3 == 200 and r3["ok"] is True and r3["signed"] is False and "crisis" in r3


def test_modules_may_still_take_a_key_locally():
    """The legitimate case, protected on purpose: on YOUR machine, with nothing travelling, handing
    your own key to the library is fine. If this ever fails, the retirement went too far."""
    import inspect
    from concordance import badges, groups, mesh
    for fn in (mesh.post_message, mesh.leave_on_door, badges.issue_badge,
               badges.study_export, groups.contribute):
        assert "private_key" in inspect.signature(fn).parameters, \
            f"{fn.__name__} lost its local private_key parameter — local signing is legitimate"


def test_the_server_still_refuses_to_mint_an_identity():
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    st, b = dispatch("POST", "/identity/create", {}, {}, EngineConfig("secular"))
    assert st == 400
    assert "on your device" in str(b.get("error", "")), "the refusal message is the teaching"
    assert "private_key" not in b


if __name__ == "__main__":
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed — no key on the wire; local signing still allowed.")
