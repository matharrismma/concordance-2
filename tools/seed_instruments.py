#!/usr/bin/env python3
"""The other joints: every validator and verifier on the one map (Matt, 2026-10-09: "now look for the other joints.
Every validator and verifier.").

After the sticks took their place on the map (tools/seed_charts.py), the engine's INSTRUMENTS - the 89 verifiers and
the gate that validates them - are placed too. The joints among them are FOUND, not invented: the real import graph,
extracted from the verifier files at seed time (re-run after a code change and the map updates; it can never drift
from the code). What that graph shows:

  * a MEASURE spine: si_units -> physical_constants -> scale_base -> the six scale libraries (alpha, grav, rela,
    thermal, molar, planck) -> the domains. Its CONFLUENCES - where several scales meet in one domain - are found,
    not declared: chemistry (alpha + molar + thermal), physics (grav + planck + rela), photonics, thermodynamics,
    astronomy.
  * a LOGIC cluster: _boolean -> mathematics / computer_science / formal_logic.
  * two small islands: number_theory <-> riemann_accel, and linguistics <- scripture.
  * sixty leaf verifiers on `base` alone - no inter-verifier joint. A leaf is not a failure; it is a verifier whose
    check stands by itself (law, medicine, agriculture, ...). Counted, not forced - a miss stays a miss.

Above them, the GATE that validates every verdict: the derivation router (routes a spec to its verifier, reduces to
one moat status), the moat (0 false positives, the hard gate), the seal (content-addressed, hash-chained), the
doorkeeper (committed and intact). And the SERVICE joints to the one map: the instruments that produced a Millennium
seal connect_at the question they instrument (number_theory + riemann_accel -> Riemann; elliptic_curves -> BSD;
physical_constants + alpha_scale -> the fine-structure chart / Yang-Mills; mathematics -> the whole map).

Each instrument card is a stub (its module in source.ref), member_of card_spine_instruments (part_of the Floor); the
code keeps the logic, the card is a cited pointer - map, never launder. MERGE-writes through chains.merge_seed.

    PYTHONPATH=src python tools/seed_instruments.py           # merge into the two shared files
    PYTHONPATH=src python tools/seed_instruments.py --check   # validate, write nothing
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))
VERIFIERS = ROOT / "src" / "concordance" / "verifiers"

FLOOR = "card_floor_the_instruments"
SPINE = "card_spine_instruments"
GLOBAL_FLOOR = "card_k_floor_of_discovery"

# the roots of the instrument trees (the deepest shared floors + each island's root)
# riemann_accel (the Riemann-Siegel acceleration) and number_theory mutually import; the collapsed graph makes
# the acceleration upstream (a tool number_theory builds on), so it is a root of its own tree.
ROOTS = ["si_units", "_boolean", "number_theory", "riemann_accel", "scripture", "elliptic_curves", "approximation"]

# a readable title where the module name is not self-explaining
TITLES = {
    "si_units": "SI units — the base of measure", "_boolean": "Boolean algebra — the base of logic",
    "physical_constants": "The physical constants — one source", "scale_base": "The scale base — the shared mechanism",
    "alpha_scale": "The fine-structure scale (α)", "grav_scale": "The gravitational scale (G)",
    "rela_scale": "The relativistic scale (c)", "thermal_scale": "The thermal scale (k_B)",
    "molar_scale": "The molar scale (N_A)", "planck_scale": "The Planck scale (ħ)",
    "number_theory": "Number theory", "riemann_accel": "The Riemann-Siegel acceleration",
    "elliptic_curves": "Elliptic curves", "mathematics": "Mathematics — the numeric substrate",
    "computer_science": "Computer science", "formal_logic": "Formal logic", "scripture": "Scripture",
    "linguistics": "Linguistics", "approximation": "Get close - a bounded estimate",
}

# the gate: the validators that sit above every verifier (module in source.ref; the edge to what they gate)
VALIDATORS = [
    dict(key="derivation", title="The derivation router", module="src/concordance/derivation.py",
         body="routes a {domain, spec} to its verifier and reduces a domain's results to one moat status "
              "(MISMATCH > ERROR > CONFIRMED); the apex where every verifier's verdict converges",
         builds_on=["mathematics"], role="routes to every verifier"),
    dict(key="the_moat", title="The moat — zero false positives", module="tools/check.py",
         body="the hard gate: the benchmark must hold at 60/60 with 0 false positives, the suite must be whole "
              "(MANIFEST), the integrity core above its coverage floor - exits non-zero on any failure",
         builds_on=["derivation"], role="gates the whole engine"),
    dict(key="the_seal", title="The seal — content-addressed, hash-chained", module="src/concordance/cas.py",
         body="every confirmed verdict is stored by its content hash (cas), minted as a receipt and linked into "
              "the hash chain (ledger) - the seal a stick carries and the site re-fetches",
         builds_on=["derivation"], role="records every verdict"),
    dict(key="the_doorkeeper", title="The doorkeeper — committed and intact", module="src/concordance/candidates.py",
         body="the airlock: a candidate is admitted only once it is committed and intact, so nothing unverified "
              "reaches the keeping",
         builds_on=["the_seal"], role="keeps the door"),
]

# the service joints: an instrument that produced a Millennium seal connects_at the question it instruments
SERVICE = [
    ("number_theory", "card_question_riemann",
     "number_theory checks the zero count, Robin, Schoenfeld, Lagarias, Nicolas and Li criteria - the Riemann "
     "stick's witnesses are its verdicts, sealed"),
    ("riemann_accel", "card_question_riemann",
     "the Riemann-Siegel acceleration is how the zeros are swept fast enough to count to height 10^7"),
    ("elliptic_curves", "card_question_bsd",
     "elliptic_curves computes L(E,1), the root number and the analytic rank, and the full BSD formula - the BSD "
     "stick's instances are its verdicts, sealed"),
    ("physical_constants", "card_chart_fine_structure",
     "the fine-structure constant α = e^2/(2 eps0 h c) is computed from this one attested constant source"),
    ("mathematics", "card_floor_logarithm",
     "mathematics' numeric mode evaluates every expression the whole map seals - including li(1000), log 2, the "
     "law of the wall - the universal instrument"),
    ("approximation", "card_question_p_vs_np",
     "the get-close door: a bounded estimate (anchor + one step, Taylor/Lipschitz error) - the practical response to "
     "the three barriers, which say an exact answer cannot always be found by rule"),
]


def _extract_graph() -> Dict[str, List[str]]:
    """The real import edges among the verifier modules: {module: [modules it imports]}, excluding `base`.
    `A: [B]` means A imports B, i.e. A builds_on B. Read from the files, so it is the code's own graph."""
    edges: Dict[str, List[str]] = {}
    for p in sorted(VERIFIERS.glob("*.py")):
        b = p.stem
        if b in ("__init__",):
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        deps: Set[str] = set()
        for m in re.finditer(r"from \. import ([a-zA-Z0-9_, ]+)", txt):
            for d in m.group(1).split(","):
                d = d.strip().split(" as ")[0].strip()
                if d and d != "base":
                    deps.add(d)
        for m in re.finditer(r"from \.([a-zA-Z0-9_]+) import", txt):
            d = m.group(1)
            if d and d != "base":
                deps.add(d)
        if deps:
            edges[b] = sorted(deps)
    return edges


def _all_modules() -> List[str]:
    return sorted(p.stem for p in VERIFIERS.glob("*.py") if p.stem not in ("__init__",))


GRAPH = _extract_graph()
ALL_MODS = _all_modules()
# every module that has an inter-verifier joint (as a source or a target) + the standalone servers
JOINED: Set[str] = set(GRAPH) | {d for ds in GRAPH.values() for d in ds} | {s[0] for s in SERVICE}
LEAVES = [m for m in ALL_MODS if m not in JOINED]


def _title(mod: str) -> str:
    return TITLES.get(mod) or (mod.replace("_", " ").strip().capitalize())


def instr_card(mod: str) -> dict:
    deps = GRAPH.get(mod, [])
    served = [q for m, q, _ in SERVICE if m == mod]
    body = f"The {_title(mod)} verifier (src/concordance/verifiers/{mod}.py)."
    if deps:
        body += " Builds on: " + ", ".join(_title(d) for d in deps) + "."
    else:
        body += " Stands on the verifier base alone (no inter-verifier joint)." if mod not in {r for r in ROOTS} else ""
    if served:
        body += " On the one map it instruments: " + ", ".join(served) + "."
    body += " Found from the code's own imports, never invented; the module keeps the logic, this card is a pointer."
    return {
        "id": f"card_instr_{mod.strip('_')}", "kind": "reference", "title": _title(mod)[:180], "body": body,
        "source": {"label": f"verifier: {mod}", "url": "", "ref": f"src/concordance/verifiers/{mod}.py",
                   "domain": "mathematics", "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "instrument", "bands": ["instrument", "verifier", "one map", mod.strip("_")],
        "subject": _title(mod),
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def validator_card(v: dict) -> dict:
    return {
        "id": f"card_instr_{v['key']}", "kind": "reference", "title": v["title"][:180],
        "body": f"{v['title']} ({v['module']}): {v['body']}. A validator of the gate - it {v['role']}. "
                f"Found, never invented; the module keeps the logic, this card is a pointer.",
        "source": {"label": f"validator: {v['key']}", "url": "", "ref": v["module"], "domain": "mathematics",
                   "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "instrument", "bands": ["instrument", "validator", "gate", "one map", v["key"]],
        "subject": v["title"],
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card() -> dict:
    conf = ", ".join(sorted(m for m in GRAPH if len(GRAPH[m]) >= 2))
    return {
        "id": FLOOR, "kind": "note", "title": "The instruments — every verifier and validator, and where they join",
        "body": ("The engine's checking instruments on the one map: the 89 verifiers and the gate that validates them, "
                 "joined by their real import graph (read from the code at seed time, so it cannot drift). A MEASURE "
                 "spine runs si_units -> physical_constants -> scale_base -> the six scale libraries -> the domains, and "
                 "its confluences - where several scales meet in one domain - are found, not declared: "
                 f"{conf}. A LOGIC cluster runs _boolean -> mathematics / computer_science / formal_logic. Two small "
                 "islands: number_theory <-> riemann_accel, and linguistics <- scripture. "
                 f"{len(LEAVES)} leaf verifiers stand on the base alone - no inter-verifier joint, counted not forced "
                 "(a miss stays a miss). Above them the gate: the derivation router, the moat, the seal, the doorkeeper. "
                 "The instruments that produced a Millennium seal connect to the question they instrument."),
        "source": {"label": "Narrow Highway - the instruments on the one map (found from the import graph)", "url": "",
                   "ref": "src/concordance/verifiers/", "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "floor",
        "bands": ["floor", "instruments", "verifiers", "validators", "gate", "two trees", "one map"],
        "subject": "The instruments",
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def spine_card() -> dict:
    return {
        "id": SPINE, "kind": "reference", "title": "The instruments — a spine of the one map",
        "body": "Every verifier and validator placed on the one map hangs here; the spine roots in the Floor of Discovery.",
        "source": {"label": "The instruments - a spine", "url": "", "domain": "mathematics", "authority_tier": "reference"},
        "shelf": "spine", "box": "spine", "bands": ["instruments", "verifiers", "spine", "one map"],
        "subject": "The instruments",
        "connections": [{"to_card_id": GLOBAL_FLOOR, "relationship": "part_of",
                         "evidence": "a spine of the one map, rooted in the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def _iid(mod: str) -> str:
    return f"card_instr_{mod.strip('_')}"


CARDS: List[dict] = [floor_card(), spine_card()]
_carded: Set[str] = set()
for _m in sorted(JOINED):
    CARDS.append(instr_card(_m))
    _carded.add(_m)
for _v in VALIDATORS:
    CARDS.append(validator_card(_v))


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out: List[dict] = []
    # the roots are parts of the floor; every other instrument is member_of the spine
    for m in sorted(JOINED):
        if m in ROOTS:
            out.append(_edge(_iid(m), FLOOR, "part_of", f"a root of the instrument trees ({_title(m)})"))
        else:
            out.append(_edge(_iid(m), SPINE, "member_of", "an instrument on the one map"))
    for v in VALIDATORS:
        out.append(_edge(f"card_instr_{v['key']}", SPINE, "member_of", "a validator of the gate"))
    # the real import graph: A imports B  =>  A builds_on B (reciprocal: B enables A, so the chain walks forward)
    for a, ds in GRAPH.items():
        for b in ds:
            out.append(_edge(_iid(a), _iid(b), "builds_on", f"{_title(a)} imports {_title(b)}"))
    # the gate above the verifiers (operational, not an import - labelled as such)
    for v in VALIDATORS:
        for b in v["builds_on"]:
            bid = f"card_instr_{b}" if b in {x["key"] for x in VALIDATORS} else _iid(b)
            out.append(_edge(f"card_instr_{v['key']}", bid, "builds_on", f"the gate: {v['title']} {v['role']}"))
    # the service joints to the one map
    for mod, node, ev in SERVICE:
        out.append(_edge(_iid(mod), node, "connects_at", f"instruments the map: {ev}"))
    return out


BRIDGES: List[dict] = _bridges()


def known_map_nodes() -> Set[str]:
    ids: Set[str] = set()
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import seed_charts as SC
        import seed_chains as S3
        import seed_millennium_chain as S2
        ids |= {c["id"] for c in S2.CARDS} | {c["id"] for c in S3.CARDS} | {c["id"] for c in SC.CARDS}
    except Exception as e:  # pragma: no cover
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs = []
    mapids = known_map_nodes()
    ids = {c["id"] for c in CARDS}
    if len(ids) != len(CARDS):
        errs.append("duplicate card ids")
    for mod, node, _ in SERVICE:
        if node not in mapids:
            errs.append(f"service node not on the map: {node}")
        if _iid(mod) not in ids:
            errs.append(f"service source not carded: {mod}")
    for e in BRIDGES:
        if e["a"] not in ids:
            errs.append(f"edge source not carded: {e['a']}")
        if e["b"] not in ids and e["b"] not in mapids and e["b"] != GLOBAL_FLOOR:
            errs.append(f"edge target unknown: {e['b']}")
    # the extraction must match what we expect of the code (a guard against a silent parse change)
    if "physical_constants" not in {d for ds in GRAPH.values() for d in ds}:
        errs.append("extraction found no physical_constants dependents - the graph parse changed")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards ({len(JOINED)} verifiers + {len(VALIDATORS)} validators + floor + spine), "
              f"{len(BRIDGES)} edges; {len(LEAVES)} leaves; confluences "
              f"{sorted(m for m in GRAPH if len(GRAPH[m]) >= 2)}; {'OK' if not errs else 'ERRORS'}")
        return 1 if errs else 0
    if errs:
        return 1
    from concordance.chains import merge_seed
    n = merge_seed(DATA, CARDS, BRIDGES)
    print(f"merged {DATA/'chain_cards.jsonl'} ({n['cards']} cards, {len(CARDS)} from this seed) and "
          f"{DATA/'chain_bridges.jsonl'} ({n['bridges']} edges, {len(BRIDGES)} from this seed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
