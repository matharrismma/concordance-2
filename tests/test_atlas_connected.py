"""THE ATLAS — one body at the DOMAIN layer, not only the theory floor.

Matt, 2026-09-19: *"Atlas does not look fully connected."* It wasn't. The calculation/bridge
graph the Atlas draws had TWO components: a mass of 59 domains, and an island of three —
formal_logic, philosophy, rhetoric — all resting on the `boolean_logic` form, which reached
nothing else. The theory floor had long been one body (`tests/test_floor_connected.py`); this
is the same ratchet one layer down, over the domains the Atlas actually shows.

The island dissolved when the truth was told about Boolean algebra: propositional logic
(formal_logic / philosophy / rhetoric) is the SAME algebra as digital switching circuits
(computer_science — Shannon 1937) and the algebra of sets (mathematics — Boole; Stone's
representation theorem). Two real verifiers, `computer_science.logic_gate` and
`mathematics.set_algebra`, carry that bridge — so it is a computation the engine runs, not a
line drawn on a map. A future domain added without a real bridge into the body must fail here,
exactly as the floor ratchet forces every new theory to be linked.

Asserts what the Atlas IS (one connected body), not how it is drawn. Runnable with pytest or directly.
"""
from __future__ import annotations

import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))


def _domain_graph():
    """The domain adjacency the Atlas induces: two domains are joined when a real bridge spans
    them — a master equation's domains, a form realized in both, or a theory >= 3 domains rest on.
    Built from the seeders (the source of truth), so it is independent of the generated store."""
    from seed_bridges import MASTER_EQUATIONS, _load_theory
    from seed_calculations import CALCS, CALC_THEORY

    domains = sorted({c[3] for c in CALCS})
    dset = set(domains)
    adj = defaultdict(set)

    def clique(ds):
        ds = [d for d in ds if d in dset]
        for i in range(1, len(ds)):
            adj[ds[0]].add(ds[i])
            adj[ds[i]].add(ds[0])

    # master equations — one formula across a set of domains
    for me in MASTER_EQUATIONS:
        clique(sorted({d for d, _s, _sub in me["rows"]}))
    # form bridges — a canonical form realized in >= 2 domains
    form_dom = defaultdict(set)
    for c in CALCS:
        form_dom[c[4]].add(c[3])
    for form, ds in form_dom.items():
        if len(ds) >= 2:
            clique(sorted(ds))
    # theory hubs — one theory >= 3 domains rest on
    titles, _ = _load_theory()
    slug_dom = {c[0]: c[3] for c in CALCS}
    theory_dom = defaultdict(set)
    for slug, tid in CALC_THEORY.items():
        if slug in slug_dom:
            theory_dom[tid].add(slug_dom[slug])
    for tid, ds in theory_dom.items():
        if len(ds) >= 3 and tid in titles:
            clique(sorted(ds))
    return domains, adj


def _components(domains, adj):
    seen, comps = set(), []
    for n in domains:
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


def test_the_atlas_is_one_body():
    """Every domain the Atlas draws is reachable from every other through a real bridge. A single
    unbridged domain (or a stranded cluster like the old logic/philosophy/rhetoric island) fails
    here — the whole point is that reality is ONE floor, so its map must be one body."""
    domains, adj = _domain_graph()
    comps = _components(domains, adj)
    largest = max((len(c) for c in comps), default=0)
    off = sorted(d for c in comps if len(c) != largest for d in c)
    assert len(comps) == 1, (
        f"the Atlas fractured into {len(comps)} components; off the giant body: {off}. "
        "Bridge them with a REAL isomorphism (a shared form, a spanning equation, a common "
        "theory) — never by drawing an unearned line.")
    assert largest == len(domains), f"only {largest}/{len(domains)} domains connected"


def test_the_boolean_bridge_is_a_computation_not_a_line():
    """The named alignment that closed the island: propositional logic = switching circuits =
    sets. Each leg is a verifier the engine actually runs, and each catches a real falsehood
    rather than rubber-stamping the claim."""
    from concordance.verifiers.computer_science import verify_logic_gate
    from concordance.verifiers.mathematics import verify_set_algebra

    # De Morgan as a gate network (Shannon): a & b  ==  ~(~a | ~b)
    assert verify_logic_gate({"variables": ["a", "b"], "gate_a": "a & b",
                              "gate_b": "~(~a | ~b)", "claimed_equivalent": True}).status == "CONFIRMED"
    # XOR is not OR — a false equivalence is caught, not confirmed
    assert verify_logic_gate({"variables": ["a", "b"], "gate_a": "a ^ b",
                              "gate_b": "a | b", "claimed_equivalent": True}).status == "MISMATCH"
    # De Morgan for sets (Stone): ~(A | B)  ==  ~A & ~B
    assert verify_set_algebra({"variables": ["A", "B"], "set_a": "~(A | B)",
                               "set_b": "~A & ~B", "claimed_equal": True}).status == "CONFIRMED"
    # union is not intersection — caught
    assert verify_set_algebra({"variables": ["A", "B"], "set_a": "A | B",
                               "set_b": "A", "claimed_equal": True}).status == "MISMATCH"


def test_the_reasoning_domains_reach_the_mass():
    """formal_logic / philosophy / rhetoric were the island; assert each still shares the
    boolean_logic form, and that the form now reaches a giant-component domain."""
    from seed_calculations import CALCS
    form_dom = defaultdict(set)
    for c in CALCS:
        form_dom[c[4]].add(c[3])
    bl = form_dom["boolean_logic"]
    for d in ("formal_logic", "philosophy", "rhetoric"):
        assert d in bl, f"{d} lost the boolean_logic form"
    assert {"computer_science", "mathematics"} & bl, "boolean_logic no longer reaches the mass"


if __name__ == "__main__":
    import pytest
    sys.exit(int(pytest.main([__file__, "-q"])))
