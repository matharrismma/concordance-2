"""Community — a member's fellowship, GATED by the narrow path.

Your own keeping is always yours; seeing ANOTHER member requires confession (Romans 10:9), read from the
shared mesh identity. An unconfessed viewer is shown the invitation, never the member. Cross-member views
are SIGNED so the gate cannot be walked past by merely quoting a fingerprint. Reads only; anonymity floor.
"""
from concordance import community, groups, identity, mesh, signing


def test_groups_of_finds_a_members_groups(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    g = groups.create_group("beekeeping", creator_id="nh_alice", handle="alice")
    groups.join_group(g["id"], member_id="nh_bob", handle="bob")
    assert len(groups.groups_of("nh_alice")) == 1        # founder belongs
    assert len(groups.groups_of("nh_bob")) == 1          # joiner belongs
    assert groups.groups_of("nh_carol") == []            # a stranger belongs to nothing


def test_your_own_fellowship_is_always_yours(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("digging wells", creator_id="nh_dave", handle="dave")
    r = community.for_member("nh_dave", viewer_fp="nh_dave")   # your own — no confession needed to see yourself
    assert r["own"] is True and r["belongs"] == 1 and len(r["groups"]) == 1 and "shelf" in r


def test_an_unconfessed_viewer_sees_the_invitation_not_the_member(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("the fellowship", creator_id="nh_member", handle="a pilgrim")
    r = community.for_member("nh_member", viewer_fp="nh_a_stranger")
    assert r.get("gated") is True and "groups" not in r       # no member data — only the way in
    assert r["confession"] and "confess" in r["why"].lower()  # an invitation, not a rejection


def test_a_stranger_with_no_viewer_at_all_is_also_gated(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("the fellowship", creator_id="nh_member", handle="a pilgrim")
    assert community.for_member("nh_member")["gated"] is True  # an open read never reveals a member


def test_a_confessor_may_see_another_member(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("the well", creator_id="nh_member", handle="a pilgrim")
    try:
        me = identity.create_identity()
    except Exception:  # noqa: BLE001 — needs cryptography for a real key
        return
    mesh.register_node(me["public_key"], confession="Jesus Christ is Lord and Messiah")
    r = community.for_member("nh_member", viewer_fp=me["id"])
    assert r.get("gated") is not True and r["belongs"] == 1   # served — the gate opened for a confessor
    assert r["viewer_stage"] in ("confessor", "joined", "community")


def test_a_member_with_no_fellowship_is_empty_not_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    r = community.for_member("nh_nobody", viewer_fp="nh_nobody")   # own, empty
    assert r["belongs"] == 0 and r["groups"] == []                # belonging is opt-in, absence is honest


def test_only_handles_are_surfaced_never_the_fingerprint(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("the anonymity floor", creator_id="nh_secret_fp", handle="a pilgrim")
    grp = community.for_member("nh_secret_fp", viewer_fp="nh_secret_fp")["groups"][0]
    blob = str(grp)
    assert "a pilgrim" in blob and "nh_secret_fp" not in blob   # the id never leaves the server


def test_signed_view_gate_holds_and_a_forgery_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("the body", creator_id="nh_target", handle="a pilgrim")
    try:
        me = identity.derive_identity("teach us to number our days that we may gain a heart of wisdom")
    except RuntimeError:
        return  # needs cryptography for a real key
    # a valid signature, but not yet confessed -> the invitation, never the member
    sig = signing.sign_bytes(community.signable_view(me["public_key"], "nh_target", "n1"), me["private_key"])
    r = community.view(me["public_key"], "nh_target", "n1", sig)
    assert r.get("gated") is True and "groups" not in r
    # confess with the same key -> the gate opens, the member is seen
    mesh.register_node(me["public_key"], confession="Jesus is Lord and the Christ")
    sig2 = signing.sign_bytes(community.signable_view(me["public_key"], "nh_target", "n2"), me["private_key"])
    r2 = community.view(me["public_key"], "nh_target", "n2", sig2)
    assert r2["ok"] is True and r2.get("gated") is not True and r2["belongs"] == 1
    assert r2["viewer"] == me["id"]                            # fingerprint derived from the key, never input
    # a forged signature is refused outright — the gate cannot be walked past
    forger = identity.create_identity()
    bad = signing.sign_bytes(community.signable_view(me["public_key"], "nh_target", "n3"), forger["private_key"])
    r3 = community.view(me["public_key"], "nh_target", "n3", bad)
    assert r3["ok"] is False and "verify" in r3["error"]
