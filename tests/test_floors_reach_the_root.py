"""Every Floor roots in the Floor of Discovery — pinned at the seed AND in the keeping.

The card-graph audit (issue #25, 2026-10-16) found two of the 67 Floors — `card_floor_the_instruments` and
`card_floor_the_solve_path` — stored with `connections: []`: their spines rooted in the Floor of Discovery,
but the Floor cards themselves carried no edge UP, so nothing under them could be walked back to the root.
Every healthy Floor seeder gives its Floor one bridge row `FLOOR -part_of-> card_k_floor_of_discovery`;
these two did not. The fix is in the seeders; this file pins the CLASS so a new Floor cannot be born unrooted:

  1. at the seed — every `tools/seed_*.py` that mints a Floor card gives it an edge up (inline on the card
     or as a bridge row from it) to the Floor of Discovery or to another Floor; runs without the keeping;
  2. in the keeping — every id in `chains.FLOORS` walks up to the root over the upward relationships
     (`roots._to_floor`'s set + rests_on/instance_of); measures the real keeping, skips if it is absent.

`tests/test_nothing_is_isolated.py` pins that no card lacks a connection; this pins that a Floor's
connection goes UP. Runnable with pytest OR directly.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import pytest  # noqa: E402

from concordance import chains  # noqa: E402

GLOBAL_FLOOR = "card_k_floor_of_discovery"
UP = frozenset({"part_of", "open_end_of", "builds_on", "member_of", "enables", "rests_on", "instance_of"})
_FLOOR_LINE = re.compile(r'^FLOOR\s*=\s*["\'](card_floor_[a-z0-9_]+)["\']', re.M)


def _floors() -> set:
    return set(chains.FLOORS) | {GLOBAL_FLOOR}


def _import_seeder(path: Path):
    spec = importlib.util.spec_from_file_location(f"_seed_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        spec.loader.exec_module(mod)   # seeders write only in main(); importing builds CARDS/BRIDGES
    return mod


def _seeders_that_mint_a_floor():
    """(file, floor id, cards, bridges) for every seeder whose CARDS actually contain its FLOOR card.
    Secondary seeders (content under an existing Floor) name a FLOOR but do not mint it — not theirs to root."""
    out, unreadable = [], []
    for f in sorted((ROOT / "tools").glob("seed_*.py")):
        m = _FLOOR_LINE.search(f.read_text(encoding="utf-8"))
        if not m:
            continue
        try:
            mod = _import_seeder(f)
        except (FileNotFoundError, SystemExit) as e:   # needs a data file this checkout lacks
            unreadable.append((f.name, repr(e)))
            continue
        cards = getattr(mod, "CARDS", None)
        bridges = getattr(mod, "BRIDGES", None)
        if cards is None or bridges is None:
            unreadable.append((f.name, "no module-level CARDS/BRIDGES"))
            continue
        if any(c.get("id") == m.group(1) for c in cards):
            out.append((f.name, m.group(1), cards, bridges))
    return out, unreadable


def test_every_seeded_floor_carries_an_edge_up():
    floors = _floors()
    minted, unreadable = _seeders_that_mint_a_floor()
    assert len(minted) >= 40, f"only {len(minted)} Floor seeders imported — the scan is not seeing the tools"
    unrooted = []
    for name, fid, cards, bridges in minted:
        card = next(c for c in cards if c.get("id") == fid)
        inline = any(e.get("relationship") in UP and e.get("to_card_id") in floors
                     for e in (card.get("connections") or []))
        bridge = any(e.get("a") == fid and e.get("relationship") in UP and e.get("b") in floors
                     for e in bridges)
        if not (inline or bridge):
            unrooted.append((name, fid))
    assert not unrooted, (
        f"{len(unrooted)} Floor(s) are born with no edge UP to the Floor of Discovery or another Floor — "
        f"nothing under them can be walked back to the root: {unrooted}. Give the seeder's _bridges() the row "
        f"_edge(FLOOR, GLOBAL_FLOOR, 'part_of', ...) like every other Floor seeder.")
    if unreadable:   # visible, never silent: a seeder this checkout could not import is a seeder not checked
        print(f"  (not checked here, data absent: {[n for n, _ in unreadable]})")


def test_the_two_floors_the_audit_found_are_rooted_at_the_seed():
    """The instances, by name — so the fix cannot be undone by a rewrite of the generic scan."""
    sys.path.insert(0, str(ROOT / "tools"))
    for stem, fid in (("seed_instruments", "card_floor_the_instruments"),
                      ("seed_solve_path", "card_floor_the_solve_path")):
        mod = _import_seeder(ROOT / "tools" / f"{stem}.py")
        ups = [(e["relationship"], e["b"]) for e in mod.BRIDGES
               if e.get("a") == fid and e.get("relationship") in UP and e.get("b") in _floors()]
        assert ("part_of", GLOBAL_FLOOR) in ups, f"{stem}: {fid} has no part_of edge to the root: {ups}"


def _walk_up(cid: str, get_card, floors: set, depth: int = 0, seen=None) -> bool:
    seen = seen if seen is not None else set()
    if cid == GLOBAL_FLOOR:
        return True
    if depth > 6 or cid in seen:
        return False
    seen.add(cid)
    for conn in ((get_card(cid) or {}).get("connections") or []):
        if conn.get("relationship") in UP and _walk_up(conn.get("to_card_id"), get_card, floors, depth + 1, seen):
            return True
    return False


def test_every_floor_in_the_keeping_walks_up_to_the_root():
    """The ratchet over the real keeping: a Floor minted anywhere (a seeder, a stick, by hand) must reach
    the root. Skips, visibly, when the keeping is not present (CI); the box gate runs it on the real one."""
    if not (ROOT / "data" / "cards.jsonl").is_file():
        pytest.skip("the keeping is not present — run on a checkout with data/")
    from conftest import real_cards
    cards = real_cards()
    missing = [f for f in chains.FLOORS if f not in cards]
    unrooted = [f for f in chains.FLOORS if f in cards and not _walk_up(f, cards.get, _floors())]
    assert not unrooted, (
        f"{len(unrooted)} Floor(s) in the keeping cannot be walked up to {GLOBAL_FLOOR}: {unrooted}. "
        f"Re-run that Floor's seeder (idempotent) after giving it the edge up.")
    if missing:
        print(f"  (Floors not in this keeping, so not measured: {missing})")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
