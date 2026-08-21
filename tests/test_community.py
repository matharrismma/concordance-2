"""Community — a member's fellowship, gathered by fingerprint (the belonging bridge).

The same key that opens a member's keeping is their membership: groups and shelves key off the identity
fingerprint, so a member belongs without a second account. Reads only; anonymity floor (handles, not ids).
"""
from concordance import community, groups


def test_groups_of_finds_a_members_groups(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    g = groups.create_group("beekeeping", creator_id="nh_alice", handle="alice")
    gid = g["id"]
    groups.join_group(gid, member_id="nh_bob", handle="bob")
    assert len(groups.groups_of("nh_alice")) == 1        # founder belongs
    assert len(groups.groups_of("nh_bob")) == 1          # joiner belongs
    assert groups.groups_of("nh_carol") == []            # a stranger belongs to nothing


def test_community_gathers_a_members_fellowship(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("digging wells", creator_id="nh_dave", handle="dave")
    r = community.for_member("nh_dave")
    assert r["belongs"] == 1 and len(r["groups"]) == 1 and "shelf" in r


def test_a_member_with_no_fellowship_is_empty_not_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    r = community.for_member("nh_nobody_here")
    assert r["belongs"] == 0 and r["groups"] == []       # belonging is opt-in, absence is honest


def test_only_handles_are_surfaced_never_the_fingerprint(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path))
    groups.create_group("the anonymity floor", creator_id="nh_secret_fp", handle="a pilgrim")
    grp = community.for_member("nh_secret_fp")["groups"][0]
    blob = str(grp)
    assert "a pilgrim" in blob and "nh_secret_fp" not in blob   # the id never leaves the server
