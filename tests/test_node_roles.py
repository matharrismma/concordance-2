"""Node roles — reader by default, carrier and node only by written choice, holdings measured.

The invariants that matter: nothing upgrades anyone (absence of a record IS reader), a torn
record fails closed to the tier that owes nothing, and the manifest reports what the disk
actually holds so a role never claims what reality does not back.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import node_roles as R  # noqa: E402


def _tmp_data_dir():
    prior = os.environ.get("CONCORDANCE_DATA_DIR")
    os.environ["CONCORDANCE_DATA_DIR"] = tempfile.mkdtemp(prefix="nh-role-")
    return prior


def _restore(prior):
    if prior is None:
        os.environ.pop("CONCORDANCE_DATA_DIR", None)
    else:
        os.environ["CONCORDANCE_DATA_DIR"] = prior


def test_the_default_is_reader_and_reader_is_the_absence_of_a_record():
    prior = _tmp_data_dir()
    try:
        assert R.current_role() == "reader"
        assert not R._role_path().exists()      # nobody had to opt into owing nothing
    finally:
        _restore(prior)


def test_carrier_and_node_are_written_choices_that_persist():
    prior = _tmp_data_dir()
    try:
        rec = R.choose("carrier")
        assert rec["role"] == "carrier" and rec["chosen_utc"]
        assert R.current_role() == "carrier"
        R.choose("node")
        assert R.current_role() == "node"
        # returning to reader REMOVES the record rather than writing 'reader'
        R.choose("reader")
        assert R.current_role() == "reader" and not R._role_path().exists()
    finally:
        _restore(prior)


def test_an_unknown_role_is_refused_and_a_torn_record_fails_closed_to_reader():
    prior = _tmp_data_dir()
    try:
        try:
            R.choose("admin")
            assert False, "an unknown role was accepted"
        except ValueError:
            pass
        p = R._role_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{torn", encoding="utf-8")
        assert R.current_role() == "reader"     # fail to the tier that owes nothing
        p.write_text(json.dumps({"role": "emperor"}), encoding="utf-8")
        assert R.current_role() == "reader"     # a typed name is not authority
    finally:
        _restore(prior)


def test_every_declared_role_names_what_it_holds_and_serves_and_who_chose_it():
    assert set(R.ROLES) == {"reader", "carrier", "node"}
    for name, decl in R.ROLES.items():
        for field in ("holds", "serves", "chosen_by"):
            assert decl[field].strip(), f"{name}.{field} is empty — an undeclared boundary"
    # serving is a separate consent from holding — the doctrine, pinned
    assert "SEPARATE consent" in R.ROLES["node"]["chosen_by"]


def test_the_manifest_measures_the_disk_and_digests_only_on_request():
    shard_dir = Path(tempfile.mkdtemp(prefix="nh-shards-"))
    payload = b"shard-bytes-" * 100
    (shard_dir / "core.db").write_bytes(payload)
    (shard_dir / "word.db").write_bytes(b"w")
    (shard_dir / ".hidden").write_bytes(b"x")                  # not a holding

    m = R.hold_manifest(shard_dir)
    assert m["held_files"] == 2 and m["held_bytes"] == len(payload) + 1
    assert m["digested"] is False and "sha256" not in m["files"][0]
    assert m["looked_in"] == str(shard_dir)                    # coverage first: where it looked

    m2 = R.hold_manifest(shard_dir, digest=True)
    want = hashlib.sha256(payload).hexdigest()
    got = next(f for f in m2["files"] if f["name"] == "core.db")["sha256"]
    assert got == want                                          # the waybill hash a peer heals from


def test_a_missing_shard_dir_is_reported_as_such_not_as_an_empty_success():
    m = R.hold_manifest(Path(tempfile.mkdtemp()) / "does-not-exist")
    assert m["held_files"] == 0
    assert "no shard directory" in m["looked_in"]


def test_status_flags_a_chosen_carrier_whose_disk_holds_nothing():
    # _shards_dir is patched to "nothing configured" so this measures the FLAGGING LOGIC and not
    # whatever shards happen to sit on the machine running the suite — the developer box holds
    # real shards, the gate box may not, and a test that changes verdict by host is noise.
    prior = _tmp_data_dir()
    orig = R._shards_dir
    R._shards_dir = lambda explicit=None: None
    try:
        assert R.status()["consistent"] is True                # reader is always consistent
        R.choose("carrier")
        st = R.status()
        assert st["role"] == "carrier"
        assert st["consistent"] is False, (
            "a carrier holding zero shard files must be visible as a claim the disk does not back")
    finally:
        R._shards_dir = orig
        _restore(prior)
