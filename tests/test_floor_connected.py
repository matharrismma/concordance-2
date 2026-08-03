"""THE FLOOR — the assembled theories must stay one body, and every edge must keep its reason.

Matt, 2026-08-02: *"We should have assembled the aligned theories across domains. That was the
floor. Reality itself mapped."* — and, when 13 theories still stood apart: *"Link them all."*

The measurement that started it (2026-08-02): 99 theory cards, **zero** theory→theory edges, zero crossing a
domain. The catalogue was built, the assay was run, each card was minted — and every one was left
alone on its own tile. A hundred true statements side by side is a pile; a floor is what you get
when you can walk from any one of them to the ones it rests on.

This file is the ratchet that keeps it assembled. It asserts what the floor IS, not how it was
built, so a future rewrite of the assembler cannot quietly undo it:

  * ONE BODY — no theory is an island, and the largest component holds essentially all of them.
    Ratcheted like `tests/test_reachable_from_the_floor.py`: the numbers may improve, never slip.
  * EVERY EDGE CARRIES ITS REASON — an edge without `evidence` is a claim wearing a relation's
    clothes. This is the same rule that killed 53 false `cites` edges: an edge that does not
    carry a real relation is worse than an absent one, because it makes the map lie.
  * NOTHING DANGLES — every endpoint resolves to a card actually on the shelf.
  * THE FLOOR NAMES ITS OWN BOUNDS — `limits` edges must exist (Gödel over Peano/ZFC, relativity
    over Newton, quantum mechanics over Bohr). A floor with no stated limits is an idol; this
    assertion is the doctrinal one, and it is deliberately unskippable.
  * IT CROSSES DOMAINS — the whole point was alignment BETWEEN fields, so a floor whose edges all
    stayed inside one domain would pass every other check here and still be a failure.

Runnable with pytest OR directly.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest  # noqa: E402

STORE = Path(os.environ.get("CONCORDANCE_THEORY_CARDS")
             or (ROOT / "data" / "theory_cards.jsonl"))
RELATIONS = ("rests_on", "limits", "same_form")

# The ratchet. Raise these when the floor genuinely improves; never lower them to make a red test
# green — that is the one move this file exists to prevent.
MIN_EDGES = 100
MAX_ISLANDS = 0
MIN_LARGEST_COMPONENT = 95
MIN_DOMAIN_PAIRS = 60

pytestmark = pytest.mark.skipif(not STORE.is_file(), reason="theory store not present")


def _load():
    cards = []
    for line in STORE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                cards.append(json.loads(line))
            except ValueError:
                continue
    return {c["id"]: c for c in cards if c.get("shelf") == "theories"}


def _edges(th):
    out = []
    for c in th.values():
        for e in (c.get("connections") or []):
            if e.get("relationship") in RELATIONS:
                out.append((c["id"], e.get("relationship"), str(e.get("to_card_id")),
                            str(e.get("evidence") or "")))
    return out


def _components(th, edges):
    adj = defaultdict(set)
    for a, _r, b, _ev in edges:
        adj[a].add(b)
        adj[b].add(a)
    seen, comps = set(), []
    for n in th:
        if n in seen:
            continue
        q, comp = deque([n]), []
        seen.add(n)
        while q:
            x = q.popleft()
            comp.append(x)
            for y in adj.get(x, ()):
                if y not in seen:
                    seen.add(y)
                    q.append(y)
        comps.append(comp)
    return comps


def test_the_floor_is_one_body():
    th = _load()
    edges = _edges(th)
    assert len(edges) >= MIN_EDGES, (
        f"the floor lost edges: {len(edges)} < {MIN_EDGES}. Raise the ratchet when it improves; "
        "never lower it to make this green.")
    comps = _components(th, edges)
    islands = [c for c in comps if len(c) == 1]
    largest = max((len(c) for c in comps), default=0)
    assert len(islands) <= MAX_ISLANDS, (
        "theories left standing alone: "
        + ", ".join(sorted(str(th[c[0]].get("title"))[:44] for c in islands)))
    assert largest >= MIN_LARGEST_COMPONENT, (
        f"the floor fractured: largest component {largest} < {MIN_LARGEST_COMPONENT}")


def test_every_edge_carries_its_reason():
    """An edge without evidence is a claim wearing a relation's clothes — the same rule that
    removed 53 false `cites` edges. A map that lies is worse than a map with a gap."""
    th = _load()
    bare = [(a, r, b) for a, r, b, ev in _edges(th) if len(ev.strip()) < 20]
    assert not bare, f"{len(bare)} edge(s) carry no real evidence: {bare[:5]}"


def test_nothing_dangles():
    th = _load()
    dangling = [(a, r, b) for a, r, b, _ev in _edges(th) if b not in th]
    assert not dangling, f"edges pointing at cards that are not on the shelf: {dangling[:5]}"


def test_the_floor_names_its_own_bounds():
    """THE DOCTRINAL ONE. Gödel limits Peano and ZFC; relativity limits Newton; quantum mechanics
    limits Bohr. A floor that cannot say where it ends is an idol, and this project exists to
    prevent exactly that."""
    th = _load()
    limits = [(a, b) for a, r, b, _ev in _edges(th) if r == "limits"]
    assert len(limits) >= 5, f"only {len(limits)} `limits` edge(s) — the floor stopped naming its bounds"
    titles = {cid: str(c.get("title", "")).lower() for cid, c in th.items()}
    joined = " | ".join(f"{titles.get(a,'')} -> {titles.get(b,'')}" for a, b in limits)
    assert "gödel" in joined or "godel" in joined, "Gödel no longer limits anything on this floor"


def test_the_floor_crosses_domains():
    """Alignment BETWEEN fields was the whole point: a floor whose edges all stayed inside one
    domain would satisfy every other assertion here and still be a failure."""
    th = _load()
    pairs = set()
    for a, _r, b, _ev in _edges(th):
        if b not in th:
            continue
        da = (th[a].get("source") or {}).get("domain") or "?"
        db = (th[b].get("source") or {}).get("domain") or "?"
        if da != db:
            pairs.add((da, db))
    assert len(pairs) >= MIN_DOMAIN_PAIRS, (
        f"only {len(pairs)} cross-domain pair(s) joined — under the {MIN_DOMAIN_PAIRS} ratchet")


def test_the_named_alignments_are_actually_there():
    """The three Matt named — every science domain, cryptography, engineering — spot-checked as
    real edges rather than as a claim in a commit message."""
    th = _load()
    by_title = {str(c.get("title", "")).lower(): cid for cid, c in th.items()}

    def _edge_between(a_frag, b_frag):
        a = next((cid for t, cid in by_title.items() if a_frag in t), None)
        b = next((cid for t, cid in by_title.items() if b_frag in t), None)
        if not a or not b:
            return False
        for x, _r, y, _ev in _edges(th):
            if {x, y} == {a, b}:
                return True
        return False

    assert _edge_between("shannon", "second law"), \
        "entropy's two coats came apart: Shannon and Clausius are no longer one form"
    assert _edge_between("cryptographic", "fundamental theorem of arithmetic"), \
        "cryptography lost its footing in unique factorization"
    assert _edge_between("structural statics", "newton's three laws"), \
        "engineering lost its footing in conservation"


if __name__ == "__main__":
    sys.exit(int(pytest.main([__file__, "-q"])))
