"""Chains / floors / connections — walk a lineage of discovery, and find where two chains connect.

A CHAIN is an ordered path through the keeping's connection graph: each link BUILDS_ON the one before
(reciprocally, the floor ENABLES what follows), rooted in a FLOOR — a spine/root card its members are
PART_OF. This module adds the only logic the engine lacked: a traversal BETWEEN cards and the INTERSECTION
of two chains. It walks the existing connection graph (edges live in bridge overlays — see
`corpus._apply_bridges`), so it NEVER duplicates card bodies: it takes ids and returns ids. Size-aware by
construction.

The graph accessor is injected (`get_card`) so the logic is pure and testable without building the corpus;
it defaults to `corpus.get_card`.
"""
from __future__ import annotations

import json
from collections import deque
from typing import Callable, Dict, List, Optional, Set

BUILDS_ON = "builds_on"   # a later work builds on an earlier one (directional)
ENABLES = "enables"       # the reciprocal: an earlier work enables a later one (floor -> forward)
PART_OF = "part_of"
HAS_PART = "has_part"           # the reciprocal of part_of: a floor's parts (what is proven, what the chain stands on)
CONNECTS_AT = "connects_at"     # an open question meets another at a proven or observed hub (lateral, symmetric)
OPEN_END_OF = "open_end_of"     # an open question hangs off a floor (reciprocal has_open_end)
HAS_OPEN_END = "has_open_end"

# THE FLOORS ON THE ONE MAP (Matt, 2026-10-09: "put them on one map, but make it the one map for the project").
# A registry the map page lists, not a scan of the keeping. Add a floor here when its seed lands.
FLOORS = ("card_floor_standard_model", "card_floor_millennium",
          # the chains (tools/seed_chains.py, 2026-10-09): the logarithm, and the seven problems as lineages
          "card_floor_logarithm", "card_floor_riemann", "card_floor_bsd", "card_floor_navier_stokes",
          "card_floor_yang_mills", "card_floor_p_vs_np", "card_floor_hodge", "card_floor_poincare",
          # the instruments (tools/seed_instruments.py, 2026-10-09): every verifier and validator, found from imports
          "card_floor_the_instruments",
          # the solve path (tools/seed_solve_path.py, 2026-10-09): both doors as the steps of the method
          "card_floor_the_solve_path",
          # linguistics (tools/seed_indo_european.py, 2026-10-09): the Indo-European family, cognates as confluences
          "card_floor_indo_european",
          # genomics (tools/seed_tree_of_life.py, 2026-10-09): the tree of life, homologous genes as confluences
          "card_floor_tree_of_life",
          # the capstone (tools/seed_the_capstone.py, 2026-10-09): one source, many potentials, one end - the reply
          # to Copenhagen; the floor the others stand on, threading between Copenhagen's silence and many-worlds' excess
          "card_floor_the_capstone",
          # the Hamiltonian (tools/seed_the_hamiltonian.py, 2026-10-09): the law of the flow - the energy operator and
          # generator of time evolution; four pillars on the capstone + solve path, the measurement gap its open end
          "card_floor_the_hamiltonian",
          # the Lagrangian (tools/seed_the_lagrangian.py, 2026-10-09): the Hamiltonian's Legendre dual - least action,
          # the path integral; four pillars on the Hamiltonian + capstone + solve path + Standard Model
          "card_floor_the_lagrangian",
          # Noether's theorem (tools/seed_noethers_theorem.py, 2026-10-09): symmetry is the source of conservation -
          # the seam between L and H; four pillars on the Lagrangian + capstone + Hamiltonian + Standard Model
          "card_floor_noethers_theorem",
          # Maxwell's equations (tools/seed_maxwells_equations.py, 2026-10-09): the first unification - electricity,
          # magnetism and light one field; cites stick_maxwell_s_...; pillars on capstone + Noether + Lagrangian + SM
          "card_floor_maxwells_equations",
          # thermodynamics (tools/seed_thermodynamics.py, 2026-10-09): the arrow and the one end - the four laws;
          # pillars on Noether (1st law) + capstone (2nd law/arrow) + Hamiltonian (stat mech) + instruments (entropy=info)
          "card_floor_thermodynamics",
          # relativity (tools/seed_relativity.py, 2026-10-09): many frames, one invariant; ties the physics region -
          # pillars on Maxwell + capstone (special), Hamiltonian (E=mc^2), Lagrangian (GR), Noether (Poincare)
          "card_floor_relativity",
          # quantum mechanics (tools/seed_quantum_mechanics.py, 2026-10-09): the framework the physics region lives in;
          # adds quantization + uncertainty + entanglement; pillars on Hamiltonian + Maxwell + capstone + instruments + relativity
          "card_floor_quantum_mechanics",
          # chemistry (tools/seed_chemistry.py, 2026-10-09): the world of substances - QM applied; the periodic table;
          # pillars on QM (periodic table) + Maxwell (bond) + thermodynamics (Delta G) + Noether (conservation)
          "card_floor_chemistry",
          # physical chemistry (tools/seed_physical_chemistry.py, 2026-10-09): deeper in chemistry - rate, equilibrium,
          # acid-base, redox; stands on chemistry; pillars reach to thermodynamics (Delta G=-RT lnK) and Maxwell (redox)
          "card_floor_physical_chemistry",
          # biology (tools/seed_biology.py, 2026-10-09): life = self-replicating chemistry; the genetic code, evolution,
          # Hardy-Weinberg, metabolism; stands on chemistry + thermodynamics, connects the tree of life into the ladder
          "card_floor_biology",
          # earth science (tools/seed_earth_science.py, 2026-10-09): the planet - radiometric deep time, plate tectonics,
          # minerals; stands on physical chemistry + chemistry + thermodynamics, hands biology its deep time
          "card_floor_earth_science",
          # the mind (tools/seed_the_mind.py, 2026-10-09): matter aware of itself - the neuron, computation, the
          # expensive brain; top of the emergence ladder; open end = the hard problem of consciousness (DECLINED)
          "card_floor_the_mind",
          # cryptography (tools/seed_cryptography.py, 2026-10-09): public keys and hard problems - RSA round-trip,
          # perfect secrecy; rests on the instruments + P vs NP (hardness) + Riemann (primes); bridges to the Millennium
          "card_floor_cryptography",
          # statistics (tools/seed_statistics.py, 2026-10-09): the normal law and the method of science - describe,
          # CLT, infer; rests on the instruments + capstone (CLT=many-into-one) + biology (the empirical method)
          "card_floor_statistics",
          # economics (tools/seed_economics.py, 2026-10-10): minds that choose meeting scarcity - cites the finance
          # stick; pillars on the mind (choice) + statistics (measurement) + instruments (the arithmetic)
          "card_floor_economics",
          # computer science (tools/seed_computer_science.py, 2026-10-10): bits, logic, computability - the byte, the
          # 16 Boolean functions, merge sort; rests on the instruments + P vs NP (complexity) + the mind (computes)
          "card_floor_computer_science",
          # game theory (tools/seed_game_theory.py, 2026-10-10): equilibrium, dilemmas, strategy - matching pennies,
          # the prisoner's dilemma; rests on the solve path (fixed point) + economics + the mind + biology (ESS)
          "card_floor_game_theory",
          # acoustics (tools/seed_acoustics.py, 2026-10-10): sound - the wave, the decibel, harmonics, Doppler; rests
          # on chemistry (medium) + the mind (perception) + quantum mechanics (phonons) + relativity (Doppler)
          "card_floor_acoustics",
          # batch down the list (2026-10-10): medicine (biology+physical chem+statistics), materials science
          # (chemistry+physical chem+quantum), optics (Maxwell+quantum)
          "card_floor_medicine", "card_floor_materials_science", "card_floor_optics",
          # batch 2 (2026-10-10): meteorology, oceanography, ecology, geography, nutrition (earth/life/applied)
          "card_floor_meteorology", "card_floor_oceanography", "card_floor_ecology",
          "card_floor_geography", "card_floor_nutrition",
          # batch 3 (2026-10-10): logistics + law (cite existing sticks), education, agriculture, hydrology
          "card_floor_logistics", "card_floor_law", "card_floor_education",
          "card_floor_agriculture", "card_floor_hydrology",
          # batch 4 (2026-10-10): nuclear physics, quantum computing, networking, soil science, astronomy (cite)
          "card_floor_nuclear_physics", "card_floor_quantum_computing", "card_floor_networking",
          "card_floor_soil_science", "card_floor_astronomy",
          # batch 5 (2026-10-10): metrology (measurement/SI) and the calendar (timekeeping) - the ground under measure
          "card_floor_metrology", "card_floor_the_calendar")


def _default_get_card(card_id: str) -> Optional[dict]:
    from . import corpus
    return corpus.get_card(card_id)


def _neighbors(card: Optional[dict], rels: Optional[Set[str]]) -> List[str]:
    """The ids this card points to, optionally filtered to edges whose relationship is in `rels`
    (None = any relationship). Order-preserving."""
    out: List[str] = []
    for c in ((card or {}).get("connections") or []):
        if not isinstance(c, dict):
            continue
        if rels is None or c.get("relationship") in rels:
            t = c.get("to_card_id")
            if t:
                out.append(t)
    return out


def walk(start: str, rel: str = ENABLES, *, get_card: Callable = _default_get_card,
         max_steps: int = 128) -> List[str]:
    """The ordered lineage from `start`, following edges labelled `rel` (default 'enables' = from the
    floor forward). Linear: at each node take the first `rel` edge not yet visited; stop at a leaf, a
    cycle, or `max_steps`. Returns the ordered card ids — ids only, bounded, no bodies."""
    path: List[str] = []
    seen: Set[str] = set()
    cur: Optional[str] = start
    rels = {rel}
    while cur and cur not in seen and len(path) < max_steps:
        path.append(cur)
        seen.add(cur)
        nxt = [n for n in _neighbors(get_card(cur), rels) if n not in seen]
        cur = nxt[0] if nxt else None
    return path


def intersect(a_start: str, b_start: str, *, rels: Optional[Set[str]] = None,
              get_card: Callable = _default_get_card, max_nodes: int = 512) -> Optional[str]:
    """The NEAREST card reached by both chains — where the two lineages connect. Breadth-first from
    each start over edges whose relationship is in `rels` (None = any); returns the first shared node,
    or None. Bidirectional BFS, so the result is the closest meeting point, not just any shared node."""
    if a_start == b_start:
        return a_start
    seen_a: Set[str] = {a_start}
    seen_b: Set[str] = {b_start}
    qa: deque = deque([a_start])
    qb: deque = deque([b_start])
    visited = 0
    while (qa or qb) and visited < max_nodes:
        if qa:
            cid = qa.popleft()
            visited += 1
            for n in _neighbors(get_card(cid), rels):
                if n in seen_b:
                    return n
                if n not in seen_a:
                    seen_a.add(n)
                    qa.append(n)
        if qb:
            cid = qb.popleft()
            visited += 1
            for n in _neighbors(get_card(cid), rels):
                if n in seen_a:
                    return n
                if n not in seen_b:
                    seen_b.add(n)
                    qb.append(n)
    return None


def floor_map(floor: str, *, get_card: Optional[Callable] = None, max_nodes: int = 512) -> Optional[Dict]:
    """A floor as the one map reads it. Its PARTS (what is proven - part_of the floor: a chain's roots, or a joints
    floor's joints); its OPEN ENDS (the questions hanging off it); THE CHAIN - everything reachable forward from the
    parts over `enables`, with its edges, bounded; the CONFLUENCES - where two parts' trees meet (intersect over
    `enables`), found, never declared; the JOINTS - for a floor with two or more ends, the hub each pair touches
    directly (a shared connects_at neighbour, with the two edges' own evidence), else the nearest node both reach,
    else a recorded MISS; and the ENTRIES - for each end, the chain's own links it connects_at (where this chain
    enters the question). A floor with no ends reports its confluences as its joints (the Standard Model: Fermi and
    Maxwell meet at Weinberg). Ids, titles and the edges' evidence only; no bodies."""
    get_card = get_card or _default_get_card          # resolved at call time, never bound at import
    fc = get_card(floor)
    if fc is None:
        return None

    def node(cid: str) -> Dict:
        c = get_card(cid) or {}
        return {"id": cid, "title": c.get("title") or cid, "stick": str((c.get("source") or {}).get("ref") or "")}

    def hubs(cid: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for c in ((get_card(cid) or {}).get("connections") or []):
            if isinstance(c, dict) and c.get("relationship") == CONNECTS_AT and c.get("to_card_id"):
                out.setdefault(c["to_card_id"], c.get("evidence") or "")
        return out

    parts = _neighbors(fc, {HAS_PART})
    ends = _neighbors(fc, {HAS_OPEN_END})
    # the chain: breadth-first forward from the roots over `enables`, bounded
    chain_ids: List[str] = []
    chain_edges: List[Dict] = []
    queue = list(parts)
    seen: Set[str] = set(parts)
    while queue and len(chain_ids) < 96:
        cid = queue.pop(0)
        chain_ids.append(cid)
        for n in _neighbors(get_card(cid), {ENABLES}):
            chain_edges.append({"from": cid, "to": n})
            if n not in seen:
                seen.add(n)
                queue.append(n)
    reach = set(chain_ids)
    part_set = set(parts)
    confluences: List[Dict] = []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            via = intersect(parts[i], parts[j], rels={ENABLES}, get_card=get_card, max_nodes=max_nodes)
            if via and via != floor:
                confluences.append({"a": parts[i], "b": parts[j], "at": via, "title": node(via)["title"]})
    joints: List[Dict] = []
    misses: List[Dict] = []
    if ends:
        for i in range(len(ends)):
            for j in range(i + 1, len(ends)):
                a, b = ends[i], ends[j]
                ha, hb = hubs(a), hubs(b)
                # a joint counts on THIS floor only at a hub of this floor - one of its parts or a link of its
                # chain - so the logarithm floor does not repeat the joints floor's hubs
                shared = [h for h in ha if h in hb and (h in reach or h in part_set)]
                if shared:
                    for h in shared:
                        joints.append({"a": a, "b": b, "at": h, "via": None, "evidence": [ha[h], hb[h]]})
                    continue
                via = intersect(a, b, rels={CONNECTS_AT}, get_card=get_card, max_nodes=max_nodes)
                misses.append({"a": a, "b": b, "at": None, "via": (via if via != floor else None), "evidence": []})
    else:
        met = {(c["a"], c["b"]) for c in confluences}
        joints = [{"a": c["a"], "b": c["b"], "at": c["at"], "via": None, "evidence": [c["title"], ""]} for c in confluences]
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                if (parts[i], parts[j]) not in met:
                    misses.append({"a": parts[i], "b": parts[j], "at": None, "via": None, "evidence": []})
    # where this floor's CHAIN enters an open end: a link of the lineage (never a part - a joints floor's parts are
    # its joints, already reported above)
    entries = [{"end": e, "at": h, "evidence": ev} for e in ends for h, ev in hubs(e).items()
               if h in reach and h not in part_set]
    # MERGES - where several instruments meet: a chain node two or more others build on (in-degree in the chain,
    # found from the real edges). The generalization of "where two trees connect" to the whole import graph.
    indeg: Dict[str, List[str]] = {}
    for e in chain_edges:
        indeg.setdefault(e["to"], []).append(e["from"])
    merges = [{"id": n, "title": node(n)["title"], "from": [node(f)["title"] for f in indeg[n]]}
              for n in chain_ids if len(indeg.get(n, [])) >= 2]
    # SERVES - a chain node that connects_at a node OUTSIDE this floor's chain (an instrument serving the one map)
    serves: List[Dict] = []
    for cid in chain_ids:
        for c in ((get_card(cid) or {}).get("connections") or []):
            if isinstance(c, dict) and c.get("relationship") == CONNECTS_AT and c.get("to_card_id") \
                    and c["to_card_id"] not in reach:
                serves.append({"from": cid, "from_title": node(cid)["title"], "at": c["to_card_id"],
                               "at_title": node(c["to_card_id"])["title"], "evidence": c.get("evidence") or ""})
    # the sticks charted onto this floor and its nodes (2026-10-09: the function following the form) - each a
    # chart card whose source.ref is a tick stick, reached by the reciprocal `charted_by` edge
    charts: List[Dict] = []
    seen_ch: Set[str] = set()
    for owner in [floor] + parts + ends + sorted({j["at"] for j in joints}):
        oc = get_card(owner)
        for c in ((oc or {}).get("connections") or []):
            if isinstance(c, dict) and c.get("relationship") == "charted_by" and c.get("to_card_id"):
                ch = c["to_card_id"]
                if ch in seen_ch:
                    continue
                seen_ch.add(ch)
                cc = get_card(ch) or {}
                charts.append({"id": ch, "title": cc.get("title") or ch,
                               "stick": str((cc.get("source") or {}).get("ref") or ""),
                               "of": owner, "of_title": (oc or {}).get("title") or owner,
                               "evidence": c.get("evidence") or ""})
    hub_ids = sorted({j["at"] for j in joints})
    return {"floor": floor, "charts": charts, "title": fc.get("title") or floor,
            "parts": [node(p) for p in parts], "ends": [node(e) for e in ends],
            "hubs": [node(h) for h in hub_ids], "joints": joints, "misses": misses,
            "confluences": confluences, "entries": entries, "merges": merges, "serves": serves,
            "chain": {"nodes": [node(c) for c in chain_ids], "edges": chain_edges}}


def _read_jsonl(p) -> List[dict]:
    if not p.exists():
        return []
    out: List[dict] = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return out


def merge_seed(data_dir, cards: List[dict], bridges: List[dict], drop_edges=()) -> Dict[str, int]:
    """THE ONE MAP has one pair of files - data/chain_cards.jsonl and data/chain_bridges.jsonl - and more than one
    seed writes them (the Standard Model, the Millennium floor, the next). Each seed MERGES: by card id and by edge
    (a, b, relationship), its own rows replacing older copies, every other seed's rows kept in order. Idempotent,
    order-independent, the same bytes on every platform."""
    from pathlib import Path
    d = Path(data_dir)
    d.mkdir(parents=True, exist_ok=True)
    cp, bp = d / "chain_cards.jsonl", d / "chain_bridges.jsonl"
    mine = {c["id"]: c for c in cards}
    out_c = [mine.pop(c["id"]) if c.get("id") in mine else c for c in _read_jsonl(cp)] + list(mine.values())

    def key(e):
        return (e.get("a"), e.get("b"), e.get("relationship"))

    mine_b = {key(e): e for e in bridges}
    gone = {tuple(k) for k in drop_edges}                 # edges this seed RETIRES (corpus._apply_bridges keeps
    old_b = [e for e in _read_jsonl(bp) if key(e) not in gone]   # one edge per ordered pair, so a stale one would shadow)
    out_b = [mine_b.pop(key(e)) if key(e) in mine_b else e for e in old_b] + list(mine_b.values())
    nl = "\n"
    cp.write_text(nl.join(json.dumps(c, ensure_ascii=False) for c in out_c) + nl, encoding="utf-8", newline=nl)
    bp.write_text(nl.join(json.dumps(e, ensure_ascii=False) for e in out_b) + nl, encoding="utf-8", newline=nl)
    return {"cards": len(out_c), "bridges": len(out_b), "mine_cards": len(cards), "mine_bridges": len(bridges)}


def chain(root: str, *, rel: str = ENABLES, get_card: Callable = _default_get_card) -> Dict:
    """A chain's shape for a reader: its floor (the root), its ordered steps, and its length. Ids only."""
    steps = walk(root, rel, get_card=get_card)
    return {"floor": root, "rel": rel, "steps": steps, "length": len(steps)}
