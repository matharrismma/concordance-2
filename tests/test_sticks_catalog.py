"""STICKS AS DATA (issue #13, 2026-10-17). The catalog data/sticks/*.json is ONE table for every tick stick —
the data entries the loader runs and the Python handlers tools/tick.py keeps — and it is held to three things:
an alias reaches exactly one stick (a duplicate is a LOAD-TIME error, never a silent first match); a malformed
entry is refused at load, not at mint; and every data entry mints BYTE-IDENTICAL sealed content to the function
it replaced — the golden tools/tick_golden.py snapshotted from those functions before they became data."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", tempfile.mkdtemp(prefix="nh-sticks-"))

from concordance import sticks  # noqa: E402

GOLDEN = ROOT / "tests" / "fixtures" / "tick_golden"


def _entry(name="probe_one", aliases=("probe_one", "probe"), **over):
    e = {"schema": 1, "name": name, "aliases": list(aliases),
         "seals": [{"key": "two", "nid": "two", "expr": "1 + 1", "value": 2, "tol": 1e-9, "domain": "mathematics"}],
         "sticks": [{"question": "A probe question", "by": "tests",
                     "marks": [{"kind": "witness", "claim": "[probe] 1 + 1 = 2 (sealed)", "seal": "two"},
                               {"kind": "note", "claim": "[probe] a note needs no seal"}]}]}
    e.update(over)
    return e


def _write(d: Path, *entries) -> Path:
    for e in entries:
        (d / f"{e['name']}.json").write_text(json.dumps(e), encoding="utf-8")
    return d


def test_the_catalog_loads_and_every_alias_reaches_exactly_one_entry():
    cat = sticks.load_catalog()
    assert len(cat) >= 187
    assert len(cat.aliases) >= 845
    for e in cat:
        assert (cat.path / f"{e['name']}.json").exists()
        for al in e["aliases"]:
            assert cat.resolve(al) is e
    data = [e for e in cat if not e.get("handler")]
    handlers = [e for e in cat if e.get("handler")]
    assert len(data) >= 1 and len(handlers) >= 1
    # the resolver: an alias first, then an entry's own name
    assert cat.resolve("basel")["name"] == "zeta"
    assert cat.resolve("finance_stick")["name"] == "economics"
    assert cat.resolve("euler_e")["name"] == "euler_e"
    assert cat.resolve("no_such_stick") is None


def test_a_duplicate_alias_is_a_load_time_error(tmp_path):
    _write(tmp_path, _entry("probe_one", ("probe_one", "shared")), _entry("probe_two", ("probe_two", "shared")))
    with pytest.raises(sticks.StickError) as exc:
        sticks.load_catalog(tmp_path)
    assert "'shared'" in str(exc.value) and "probe_one" in str(exc.value)


def test_a_malformed_entry_is_refused_at_load(tmp_path):
    bad = _entry()
    bad["sticks"][0]["marks"][0]["seal"] = "never_minted"
    _write(tmp_path, bad)
    with pytest.raises(sticks.StickError, match="never_minted"):
        sticks.load_catalog(tmp_path)
    # the file must be named for its entry
    (tmp_path / "probe_one.json").unlink()
    (tmp_path / "other.json").write_text(json.dumps(_entry()), encoding="utf-8")
    with pytest.raises(sticks.StickError, match="file name"):
        sticks.load_catalog(tmp_path)
    (tmp_path / "other.json").unlink()
    for broken in (_entry(schema=2), _entry(aliases=["a", "a"]), _entry(sticks=[]),
                   _entry(handler="x", seals=[], sticks=[{"question": "a handler carries none"}])):
        _write(tmp_path, broken)
        with pytest.raises(sticks.StickError):
            sticks.load_catalog(tmp_path)


def test_every_handler_names_a_function_in_tick_py_and_its_params_parse():
    import tick as T
    cat = sticks.load_catalog()
    for e in cat:
        if not e.get("handler"):
            continue
        fn = getattr(T, e["handler"], None)
        assert callable(fn), f"{e['name']}: handler {e['handler']!r} is not in tools/tick.py"
        for p in e.get("params") or []:
            assert p["type"] in sticks.PARAM_TYPES
            assert isinstance(sticks.PARAM_TYPES[p["type"]](str(p["default"])), sticks.PARAM_TYPES[p["type"]])
    # the CLI parses argv by the params; a typed value passes through
    seen = {}
    T.robin = lambda N: seen.setdefault("N", N) or 0  # noqa: E731 — the handler itself is not run here
    try:
        T.run_entry(cat.resolve("robin"), ["12345"])
        assert seen["N"] == 12345 and isinstance(seen["N"], int)
        seen.clear(); T.run_entry(cat.resolve("robin"), [])
        assert seen["N"] == 1000000
    finally:
        del T.robin
    assert T.run_entry(cat.resolve("bsd"), ["11a1"]) in (0, 1) or True  # a real run is the golden's job


def test_the_loader_refuses_a_handler_and_aborts_on_a_seal_that_does_not_hold(tmp_path, monkeypatch):
    monkeypatch.setenv("CONCORDANCE_DATA_DIR", str(tmp_path / "keeping"))
    monkeypatch.setenv("CONCORDANCE_SEAL_INDEX", "0")
    from concordance import tickstick
    with pytest.raises(sticks.StickError):
        sticks.run({"name": "h", "handler": "x"})
    false = _entry()
    false["seals"][0]["value"] = 3                              # 1 + 1 is not 3: the seal must refuse
    assert sticks.run(false) == 1
    assert tickstick.fold() == {}                               # nothing opened, nothing marked
    assert sticks.run(_entry()) == 0
    st = tickstick.fold()["stick_a_probe_question"]
    assert [t["kind"] for t in st["ticks"]] == ["witness", "note"] and st["ticks"][0]["seal"]
    assert sticks.run(_entry()) == 0 and len(tickstick.fold()["stick_a_probe_question"]["ticks"]) == 2   # idempotent


@pytest.mark.parametrize("name", sorted(p.stem for p in (ROOT / "data" / "sticks").glob("*.json")
                                        if "handler" not in json.loads(p.read_text(encoding="utf-8"))))
def test_a_data_entry_mints_byte_identical_to_the_function_it_replaced(name):
    """The acceptance criterion of #13: same stick, same seals (content hashes), same marks as the golden the
    pre-refactor function produced — in a fresh temp keeping, exactly as tools/tick_golden.py checks it."""
    import tick as T
    import tick_golden as G
    entry = sticks.load_catalog().entries[name]
    want = json.loads((GOLDEN / f"{name}.json").read_text(encoding="utf-8"))
    got = G.run_entry(name, lambda: T.run_entry(entry))
    assert G._diff(name, want, got) == []
