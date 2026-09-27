"""FLOCK through the real mesh — the ON-path end-to-end. The pure neighborhood is pinned in test_flock;
here we prove map_around actually surfaces it: absent when off, a capped `flock` list + `in_flock` marks
when on, built from real registered, confessed, mutually-linked nodes."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402
from concordance import identity, mesh, signing  # noqa: E402


@pytest.fixture()
def mesh_dir(monkeypatch):
    d = tempfile.mkdtemp(prefix="flock_mesh_")
    monkeypatch.setenv("CONCORDANCE_MESH_DIR", d)
    yield d


def _node(callsign="anon"):
    idn = identity.create_identity()
    r = mesh.register_node(idn["public_key"], callsign, confession="Jesus Christ is Lord and Messiah")
    assert r["ok"], r
    return idn, r["fp"]


def _vouch(a, b):
    for x, y in ((a, b), (b, a)):
        n = "n" + y["id"][-8:]
        sig = signing.sign_bytes(mesh.link_signable(x["id"], y["id"], "link", n), x["private_key"])
        assert mesh.link(x["id"], y["id"], signature=sig, nonce=n)["ok"]


def _star(n_leaves):
    """A center mutually linked to n leaves (each leaf linked only to the center)."""
    cidn, cfp = _node("center")
    leaves = [_node("leaf%d" % i) for i in range(n_leaves)]
    for lidn, _lfp in leaves:
        _vouch(cidn, lidn)
    return cfp, {fp for _idn, fp in leaves}


def test_map_has_no_flock_when_off(mesh_dir, monkeypatch):
    monkeypatch.delenv("CONCORDANCE_FLOCK", raising=False)
    cfp, _leaf_fps = _star(3)
    out = mesh.map_around(cfp)
    assert "flock" not in out                              # inert: the view is unchanged
    assert all("in_flock" not in nd for nd in out["nodes"])


def test_map_surfaces_flock_when_on(mesh_dir, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_FLOCK", "1")
    cfp, leaf_fps = _star(3)
    out = mesh.map_around(cfp)
    assert set(out["flock"]) == leaf_fps                  # only 3 links -> all make the handful
    marked = {nd["fp"] for nd in out["nodes"] if nd.get("in_flock")}
    assert marked == leaf_fps                             # each neighbor marked; the center is not
    center_nd = next(nd for nd in out["nodes"] if nd["fp"] == cfp)
    assert center_nd.get("in_flock") is False


def test_flock_caps_at_seven_through_the_map(mesh_dir, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_FLOCK", "1")
    cfp, leaf_fps = _star(8)
    out = mesh.map_around(cfp)
    assert len(out["flock"]) == 7                         # the starling's handful, enforced end-to-end
    assert len(set(out["flock"])) == 7
    assert set(out["flock"]).issubset(leaf_fps)


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
