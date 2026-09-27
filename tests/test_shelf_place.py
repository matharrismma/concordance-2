"""PLACE — a member points the catalogue at content THEY host; we keep the small high-value card, never
the file. Pins: the ownership+license attestation is signed by the member's key; the commons ring is
license-gated (PD/CC0/CC-BY only); a placement is kept as a member-tier card pointing at the member's
storage, and we never hold the file. All local (temp shelf store, a real keypair, waybill stubbed)."""
from __future__ import annotations

import base64
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402


@pytest.fixture()
def member_env(monkeypatch):
    tmp = Path(tempfile.mkdtemp())
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp))
    # The pointer safety (linkdrop._public_only) does live DNS and requires a PUBLIC-resolvable host —
    # correct in production (a public-commons pointer can't aim at a private/unresolvable address; a
    # truly-local desktop folder is a MESH-plane concern, not a public URL). Stub it here so the tests
    # are hermetic (no network), and exercise the placement logic itself.
    from concordance import linkdrop
    monkeypatch.setattr(linkdrop, "_public_ip", lambda host: (True, ""))
    from concordance import signing
    priv, pub = signing.generate_keypair()
    return priv, pub, tmp


def _sign(signable_b64: str, priv: str) -> str:
    from concordance import signing
    return signing.sign_bytes(base64.urlsafe_b64decode(signable_b64), priv)


_OFFLINE = lambda u: {"ok": False, "state": "OFFLINE"}   # a private file is unreachable; the card STILL lands


def test_place_keeps_a_card_pointing_at_the_members_storage(member_env):
    from concordance import shelves
    priv, pub, _ = member_env
    s = shelves.signable_place(pub, title="My field notes on grafting", curation="Ten years of grafting logs.",
                               url="https://drive.google.com/file/d/abc123/view", storage="drive",
                               license="CC-BY 4.0", ring="commons")
    assert s["ok"], s
    out = shelves.place(s["fields"], _sign(s["signable"], priv), display_name="Sam", waybill_fn=_OFFLINE)
    assert out["ok"] and out["ring"] == "commons"
    assert out["stage"] == "public_review"           # commons waits for a steward
    assert out["storage"] == "drive" and out["reach"] == "OFFLINE"
    # the card is KEPT (ours); the file is NOT — the card points at the member's storage
    drops = [__import__("json").loads(l) for l in
             (Path(os.environ["CONCORDANCE_DATA_DIR"]) / "shelves" / "drops.jsonl").read_text().splitlines() if l.strip()]
    card = next(c for c in drops if c["id"] == out["card_id"])
    assert card["source"]["url"] == "https://drive.google.com/file/d/abc123/view"
    assert card["source"]["authority_tier"] == "member" and card["extra"]["placed"] is True
    assert card["extra"]["license"] == "CC-BY 4.0" and card["extra"]["storage"] == "drive"
    assert "grafting" in card["body"].lower()        # the small high-value part is kept


def test_a_self_hosted_folder_is_a_valid_backend(member_env):
    from concordance import shelves
    priv, pub, _ = member_env
    s = shelves.signable_place(pub, title="Sermons archive", curation="My whole sermon archive.",
                               url="https://my-server.example.org/share/sermons", storage="server",
                               license="CC0", ring="shelf")
    assert s["ok"]
    out = shelves.place(s["fields"], _sign(s["signable"], priv), waybill_fn=_OFFLINE)
    assert out["ok"] and out["ring"] == "shelf" and out["stage"] == "private"   # shelf ring withheld from public


def test_commons_amplifies_only_shareable_licenses(member_env):
    """Share-alike/NC content the member owns may sit on their shelf ring, but the commons won't amplify it."""
    from concordance import shelves
    priv, pub, _ = member_env
    s = shelves.signable_place(pub, title="A book", curation="worth reading", url="https://dropbox.com/s/x/book.pdf",
                               storage="dropbox", license="CC-BY-SA 4.0", ring="commons")
    assert s["ok"]
    out = shelves.place(s["fields"], _sign(s["signable"], priv), waybill_fn=_OFFLINE)
    assert out["ok"] is False and out.get("code") == "LICENSE_RING"


def test_signable_place_requires_pointer_license_and_curation(member_env):
    from concordance import shelves
    _, pub, _ = member_env
    assert shelves.signable_place(pub, "t", "why", "", "url", "CC0")["ok"] is False          # no pointer
    assert shelves.signable_place(pub, "t", "why", "https://x.org/f", "url", "")["ok"] is False  # no license
    assert shelves.signable_place(pub, "t", "", "https://x.org/f", "url", "CC0")["ok"] is False   # no curation


def test_a_placed_card_presents_a_borrow_block(member_env):
    """The borrow side (polish): a placed card tells a borrower the terms (license), where it's hosted,
    and that we keep the card, not the file."""
    import json
    from concordance import shelves, present
    priv, pub, _ = member_env
    s = shelves.signable_place(pub, "My grafting notes", "worth borrowing",
                               "https://drive.google.com/file/d/xyz/view", "drive", "CC-BY 4.0", ring="shelf")
    out = shelves.place(s["fields"], _sign(s["signable"], priv), display_name="Sam", waybill_fn=_OFFLINE)
    card = next(json.loads(l) for l in
                (Path(os.environ["CONCORDANCE_DATA_DIR"]) / "shelves" / "drops.jsonl").read_text().splitlines()
                if l.strip() and json.loads(l).get("id") == out["card_id"])
    presented = present.attach([card])
    blob = json.dumps(presented)
    assert "borrow" in blob and "CC-BY 4.0" in blob and "drive" in blob
    assert "https://drive.google.com/file/d/xyz/view" in blob   # the borrower can open it at the source


def test_public_shelf_shows_how_to_connect_and_borrow(member_env):
    """Connect/mesh: a public reader who finds a shelf learns how much waits behind a link, and how to
    connect — the mesh is the connector; the file stays the member's."""
    from concordance import shelves, mesh
    priv, pub, _ = member_env
    s = shelves.signable_place(pub, "Homestead logs", "my whole homestead archive",
                               "https://drive.google.com/d/hs", "drive", "CC0", ring="shelf")
    shelves.place(s["fields"], _sign(s["signable"], priv), display_name="Sam", waybill_fn=_OFFLINE)
    r0 = shelves.shelf_of(pub, viewer=None, access="public")
    assert r0["connect"] is not None
    assert r0["connect"]["borrowable_on_connect"] == 1        # one shelf-ring card waits behind a link
    assert r0["connect"]["on_mesh"] is False and "not on the mesh" in r0["connect"]["how"].lower()
    reg = mesh.register_node(pub, callsign="SAM")
    if reg.get("ok"):
        r1 = shelves.shelf_of(pub, viewer=None, access="public")
        assert r1["connect"]["on_mesh"] is True and "linked" in r1["connect"]["how"].lower()


def test_a_forged_signature_is_refused(member_env):
    from concordance import shelves
    priv, pub, _ = member_env
    s = shelves.signable_place(pub, "t", "why", "https://x.org/f", "url", "CC0", ring="shelf")
    other_priv, _ = __import__("concordance.signing", fromlist=["x"]).generate_keypair()
    out = shelves.place(s["fields"], _sign(s["signable"], other_priv), waybill_fn=_OFFLINE)   # wrong key
    assert out["ok"] is False and "verify" in out["error"].lower()


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
