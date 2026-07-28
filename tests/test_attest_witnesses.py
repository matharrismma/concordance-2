"""Detached attestation — bind an identity to a record without ever sending a key.

The last shape of the private-key-on-the-wire problem: badges, study bundles and group
contributions sign a content_hash of a record the SERVER builds, and those records carry a server
timestamp, so a client cannot pre-compute the hash and could not pre-sign it. The old answer was to
hand over a private key. This is the two-phase answer: act unsigned → receive the hash → sign THAT
hash locally → submit only the attestation.

Attestations live BESIDE the record rather than inside it, because a CAS record is immutable (fold a
signature in and the hash changes, so it would name a different record). That limitation turns out to
be the better shape: the old embedded-signature design held exactly ONE signature, the issuer's. A
store holds MANY — so several parties can independently bear witness to the same record, which is the
witness gate this project already applies to history (Deuteronomy 19:15) now applied to its own
records. One signature is a claim; two or three begin to establish a matter.

Pinned here: multiple independent witnesses accumulate; the SAME key repeating itself does NOT become
two witnesses; a hash we do not hold is declined rather than stored as a dangling claim; a bad
signature, a signature over a different record, and an attestation carrying a private key are all
refused; and tampering with the STORED file is caught on read and REPORTED rather than quietly
dropped. Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402


@pytest.fixture(autouse=True, scope="module")
def _isolate_data_dir():
    """Writes records and attestations; keep it in a temp dir and restore after (the leak lesson
    from tests/test_scripture.py — a dangling CONCORDANCE_DATA_DIR breaks later files)."""
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp()
    yield
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


def _mods():
    from concordance import attest, cas, identity, signing
    return attest, cas, identity, signing


def test_two_independent_keys_become_two_witnesses():
    attest, cas, identity, signing = _mods()
    A, B = identity.create_identity(), identity.create_identity()
    h = cas.store({"record_type": "test", "claim": "2+2=4", "generated": False})

    r1 = attest.bear_witness(h, signing.sign_seal(h, A["private_key"]))
    assert r1["ok"] is True and r1["witnesses"] == 1
    assert r1["established"] is False, "one signature is a claim, not an established matter"

    r2 = attest.bear_witness(h, signing.sign_seal(h, B["private_key"]))
    assert r2["ok"] is True and r2["witnesses"] == 2 and r2["established"] is True

    w = attest.witnesses(h)
    assert w["witnesses"] == 2 and w["invalid"] == 0 and w["record_held"] is True
    assert len({a["pubkey"] for a in w["attestations"]}) == 2


def test_the_same_key_repeating_itself_is_not_a_second_witness():
    attest, cas, identity, signing = _mods()
    A = identity.create_identity()
    h = cas.store({"record_type": "test", "claim": "one voice twice", "generated": False})
    att = signing.sign_seal(h, A["private_key"])
    assert attest.bear_witness(h, att)["witnesses"] == 1
    again = attest.bear_witness(h, att)
    assert again["ok"] is True and again.get("already") is True
    assert again["witnesses"] == 1, "a key cannot become two witnesses by repeating itself"


def test_a_record_we_do_not_hold_is_declined_not_stored():
    attest, _cas, identity, signing = _mods()
    A = identity.create_identity()
    ghost = "0" * 64
    r = attest.bear_witness(ghost, signing.sign_seal(ghost, A["private_key"]))
    assert r["ok"] is False and "do not have" in r["error"]
    assert attest.witnesses(ghost)["witnesses"] == 0


def test_every_forgery_shape_is_refused():
    attest, cas, identity, signing = _mods()
    A = identity.create_identity()
    h = cas.store({"record_type": "test", "claim": "guard me", "generated": False})
    other = cas.store({"record_type": "test", "claim": "a different record", "generated": False})

    bad_sig = dict(signing.sign_seal(h, A["private_key"]))
    bad_sig["sig"] = "AAAA"
    assert attest.bear_witness(h, bad_sig)["ok"] is False

    # a real signature, but over a DIFFERENT record's hash
    wrong_record = signing.sign_seal(other, A["private_key"])
    r = attest.bear_witness(h, wrong_record)
    assert r["ok"] is False and "does not verify" in r["error"]

    assert attest.bear_witness(h, {"private_key": "x"})["ok"] is False
    assert attest.bear_witness("", {})["ok"] is False
    assert attest.bear_witness(h, "not-a-dict")["ok"] is False  # type: ignore[arg-type]


def test_tampering_with_the_stored_file_is_caught_on_read_and_reported():
    """Storage is not trusted. A reader is owed the fact that something was altered — not a tidier
    list with the bad entry silently removed."""
    attest, cas, identity, signing = _mods()
    A = identity.create_identity()
    h = cas.store({"record_type": "test", "claim": "tamper target", "generated": False})
    attest.bear_witness(h, signing.sign_seal(h, A["private_key"]))

    p = Path(os.environ["CONCORDANCE_DATA_DIR"]) / "attestations" / h[:2] / f"{h}.jsonl"
    entry = json.loads(p.read_text(encoding="utf-8").strip())
    entry["sig"] = entry["sig"][:-4] + "AAAA"
    p.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    w = attest.witnesses(h)
    assert w["witnesses"] == 0, "a tampered signature must not count as a witness"
    assert w["invalid"] == 1, "the tampered entry must be REPORTED, not dropped"
    assert w["attestations"][0]["valid"] is False
    assert w["established"] is False


def test_the_endpoint_and_agent_tools_carry_the_same_rules():
    attest, cas, identity, signing = _mods()
    from concordance import mcp
    from concordance.config import EngineConfig
    from concordance.web.api import dispatch
    cfg = EngineConfig("secular")

    A = identity.create_identity()
    h = cas.store({"record_type": "test", "claim": "over the wire", "generated": False})
    att = signing.sign_seal(h, A["private_key"])

    st, body = dispatch("POST", "/attest", {}, {"content_hash": h, "attestation": att}, cfg)
    assert st == 200 and body["ok"] is True and body["witnesses"] == 1
    st2, seen = dispatch("GET", "/attest", {"hash": h}, None, cfg)
    assert st2 == 200 and seen["witnesses"] == 1
    assert dispatch("POST", "/attest", {}, {"attestation": att}, cfg)[0] == 400

    def call(name, args):
        r = mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": name, "arguments": args}}, cfg, {})
        return json.loads(r["result"]["content"][0]["text"])

    names = {t["name"] for t in mcp.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, cfg, {})["result"]["tools"]}
    assert {"attest_record", "witnesses"} <= names
    B = identity.create_identity()
    r = call("attest_record", {"content_hash": h, "attestation": signing.sign_seal(h, B["private_key"])})
    assert r["ok"] is True and r["witnesses"] == 2
    assert call("witnesses", {"content_hash": h})["established"] is True
    assert "private key" in str(call("attest_record", {"content_hash": h, "attestation": att,
                                                       "private_key": "AAAA"}).get("error", "")).lower()


def test_the_receipt_page_shows_who_bore_witness_without_overclaiming():
    """The attestation store existed but no reader of a receipt could see it — and /s/<hash> is
    exactly where someone lands to CHECK a claim (it is what cite_url points at). A witness nobody
    can see is not a witness.

    The wording is load-bearing: ONE witness must read as a claim, TWO as beginning to be
    established (Deut 19:15) — and the page must never tell the reader the matter is settled."""
    attest, cas, identity, signing = _mods()
    from concordance.web.api import render_seal_html
    rec = {"overall": "PASS",
           "verifier_results": [{"status": "CONFIRMED", "name": "arith", "detail": "2+2=4"}],
           "gate_results": [{"gate": "floor", "status": "PASS"}]}
    h = cas.store(rec)

    _st, html = render_seal_html(h, rec)
    assert "borne witness" not in html, "an empty witness section should not clutter the receipt"

    A, B = identity.create_identity(), identity.create_identity()
    attest.bear_witness(h, signing.sign_seal(h, A["private_key"]))
    _st, html = render_seal_html(h, rec)
    assert "borne witness" in html
    assert "a claim, not yet established" in html, "one signature must not read as established"

    attest.bear_witness(h, signing.sign_seal(h, B["private_key"]))
    _st, html = render_seal_html(h, rec)
    assert "begins to be established" in html and "Deuteronomy 19:15" in html
    assert html.count("nh_") >= 2, "each witness's key should be identifiable"
    # the only mention of "settled" is the refusal to claim it
    assert "do not tell you the matter is settled" in html


def test_a_tampered_attestation_is_shown_as_broken_on_the_receipt():
    """Dropping it silently would leave the reader with a tidier page and less truth."""
    import json
    attest, cas, identity, signing = _mods()
    from concordance.web.api import render_seal_html
    rec = {"overall": "PASS", "verifier_results": [], "gate_results": []}
    h = cas.store(rec)
    A = identity.create_identity()
    attest.bear_witness(h, signing.sign_seal(h, A["private_key"]))
    p = Path(os.environ["CONCORDANCE_DATA_DIR"]) / "attestations" / h[:2] / f"{h}.jsonl"
    e = json.loads(p.read_text(encoding="utf-8").strip())
    e["sig"] = e["sig"][:-4] + "AAAA"
    p.write_text(json.dumps(e) + "\n", encoding="utf-8")

    _st, html = render_seal_html(h, rec)
    assert "borne witness" in html, "a broken attestation must still be reported, not hidden"
    assert "no longer verify" in html
    assert ">✗<" in html


if __name__ == "__main__":
    os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp())
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} attestation tests passed — many witnesses, no key on the wire.")
