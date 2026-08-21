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


def test_own_view_reports_your_walk_so_the_page_can_offer_confession(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    r = community.for_member("nh_me", viewer_fp="nh_me")
    assert r["own"] is True and r["walk"]["confessed"] is False and r["walk"]["stage"] == "seeker"


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


def test_a_confessor_sees_that_believers_belong_but_not_yet_their_shelf(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("the well", creator_id="nh_member", handle="a pilgrim")
    try:
        me = identity.create_identity()
    except Exception:  # noqa: BLE001 — needs cryptography for a real key
        return
    mesh.register_node(me["public_key"], confession="Jesus Christ is Lord and Messiah")
    r = community.for_member("nh_member", viewer_fp=me["id"])
    assert r.get("gated") is not True and r["belongs"] == 1   # served — the gate opened for a confessor
    assert r["viewer_stage"] == "confessor"
    assert "shelf" not in r and "reach" in r                  # reach is staged — the shelf opens at 'joined'


def test_the_shelf_opens_to_a_joined_viewer_connected_to_the_member(tmp_path, monkeypatch):
    # Reach widens with the walk AND requires a real connection: a 'joined' viewer who is within the
    # member's mutual-link neighborhood sees the shelf — the offers and needs. (Walk + neighborhood are
    # faked here to test the ladder threshold in isolation.)
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("the well", creator_id="nh_member", handle="a pilgrim")
    monkeypatch.setattr(community, "_walk", lambda fp: {"confessed": True, "stage": "joined"})
    monkeypatch.setattr(mesh, "_bfs", lambda fp, hops: {"nh_viewer": 0, "nh_member": 1})   # connected
    r = community.for_member("nh_member", viewer_fp="nh_viewer")
    assert r["viewer_stage"] == "joined" and "shelf" in r     # connected + joined -> the offers/needs open


def test_a_self_promoted_stranger_cannot_reach_the_shelf(tmp_path, monkeypatch):
    # The Sybil defense: even a JOINED viewer sees a member's shelf ONLY if actually connected to them. A
    # self-promoted attacker's neighborhood is only its own puppets, so a real member it never linked to
    # stays closed — belonging is visible, the sensitive offers/needs are not.
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("the well", creator_id="nh_member", handle="a pilgrim")
    monkeypatch.setattr(community, "_walk", lambda fp: {"confessed": True, "stage": "joined"})
    monkeypatch.setattr(mesh, "_bfs", lambda fp, hops: {"nh_sybil": 0})   # circle = only itself/puppets
    r = community.for_member("nh_member", viewer_fp="nh_sybil")
    assert "shelf" not in r and "reach" in r                  # not connected -> offers/needs stay closed
    assert r["belongs"] == 1                                  # basic belonging is still visible


def test_fruit_is_counted_but_alone_does_not_promote_you_must_also_be_known(tmp_path, monkeypatch):
    # Promotion by fruit: writing/reflecting/serving is counted as fruit — but reach is not handed out for
    # fruit alone; you must also be VOUCHED (known by believers). So a lone confessor who has borne fruit
    # is still a confessor until others vouch for them. Guards against self-promotion by spamming words.
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    try:
        me = identity.create_identity()
    except Exception:  # noqa: BLE001 — needs cryptography for a real key
        return
    mesh.register_node(me["public_key"], confession="Jesus Christ is Lord and Messiah")
    fp = me["id"]
    assert community._fruit(fp) == 0
    # an UNSIGNED post (anyone can attribute one to any fingerprint) must NEVER count as fruit —
    # otherwise reach could be inflated by impersonation. Only authenticated service counts.
    mesh.post_message(fp, "an unsigned word anyone could forge")
    assert community._fruit(fp) == 0
    # a SIGNED post — authenticated writing/reflecting — counts
    mesh.post_message(fp, "a reflection I truly share", private_key=me["private_key"])
    w = community._walk(fp)
    assert w["fruit"] >= 1
    assert w["stage"] == "confessor" and w["vouched"] == 0   # fruit alone does not promote — not yet known


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
