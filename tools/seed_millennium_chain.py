#!/usr/bin/env python3
"""Seed the Millennium floor on the ONE map (Matt, 2026-10-09: "Put them on one map, but make it the one map for
the project. We want to map reality as we know it and these fall on that.").

The map of reality is the keeping's connection graph, rooted in the Floor of Discovery, drawn by site/map.html and
walked by chains.py. The Standard-Model chain already lives there (tools/seed_standard_model_chain.py). This seeds
the seven Millennium problems onto the same graph, in the same two files, as the same kind of thing:

  * a FLOOR, card_floor_millennium — part_of the one Floor of Discovery. Its PARTS are what is PROVEN or OBSERVED:
    the ten joints where two of the problems meet at one established thing (GUE statistics, the L-function
    machinery, the Weil conjectures (the Riemann hypothesis over finite fields, Deligne 1974 - the hypothesis itself
    stays open), the Tate conjecture, Bochner's vanishing,
    the renormalization group, the sign problem, Manin's algorithm, the Diophantine form of RH, Arnold's geodesics).
  * seven OPEN ENDS, card_question_<problem> — the questions as the Clay Mathematics Institute states them, each
    pointing at its tick stick, where what is sealed, cited and open is read live. They hang off the floor
    (open_end_of) and CONNECT AT the joints (connects_at), with the citation and, where the join is arithmetic, the
    name of the seal, written on the edge itself.
  * the joints CITE the source cards of tools/card_millennium_sources.py (Montgomery 1973, Deligne 1974, …), so
    every claim on the map lands on a record.

Nothing is unified by us. Each joint is a join mathematics already made, found and cited; the sealed ones are
arithmetic the engine recomputed (tools/tick.py millennium_map). The one recorded miss — Riemann and
Navier-Stokes share no joint — is left as a miss, and the map shows the indirect path honestly.

MERGE-WRITES the two shared files (by card id; by edge (a, b, relationship)), so the Standard-Model seed and this
one coexist, in either order, idempotently.

    PYTHONPATH=src python tools/seed_millennium_chain.py           # merge into the two files
    PYTHONPATH=src python tools/seed_millennium_chain.py --check   # validate, write nothing
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

FLOOR = "card_floor_millennium"
GLOBAL_FLOOR = "card_k_floor_of_discovery"
SOURCES_SPINE = "card_spine_millennium_sources"       # tools/card_millennium_sources.py
CLAY = "https://www.claymath.org/millennium-problems/"


def _src(key: str) -> str:
    return f"card_src_mill_{key}"


def _q(slug: str) -> str:
    return f"card_question_{slug}"


def _j(slug: str) -> str:
    return f"card_joint_{slug}"


def _question(slug: str, name: str, stick: str, statement: str, status: str, bands: List[str]) -> dict:
    return {
        "id": _q(slug), "kind": "reference", "title": name,
        "body": (f"{name}. {statement} Its chart is the tick stick {stick}: what is sealed, what is cited and what "
                 f"stays open are read live at /stick?id={stick}. {status}"),
        "source": {"label": "Clay Mathematics Institute, the Millennium Prize Problems (2000)", "url": CLAY,
                   "ref": stick, "domain": "mathematics", "authority_tier": "reference"},
        "shelf": "millennium", "box": "question",
        "bands": ["millennium", "open question", "clay", slug.replace("_", " ")] + bands,
        "subject": name,
        "connections": [{"to_card_id": SOURCES_SPINE, "relationship": "member_of",
                         "evidence": "one of the seven questions the Millennium shelf is about"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def _joint(slug: str, title: str, body: str, bands: List[str]) -> dict:
    return {
        "id": _j(slug), "kind": "note", "title": title, "body": body,
        "source": {"label": "Narrow Highway - the Millennium floor, a joint found in the literature (operator seed)",
                   "url": "", "domain": "mathematics", "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "joint",
        "bands": ["joint", "two trees", "millennium", "floor"] + bands,
        "subject": title,
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


FLOOR_CARD = {
    "id": FLOOR, "kind": "note",
    "title": "The Millennium floor - seven open questions, and where they connect",
    "body": ("The seven Millennium Prize Problems on the one map of reality. The FLOOR is what is proven or observed: "
             "the joints where two of the questions meet at one established thing - the GUE statistics shared by zeta "
             "zeros and the lattice Dirac operator, the one L-function machinery, the Weil conjectures (the Riemann "
             "hypothesis over finite fields, a theorem by Deligne 1974 - the Riemann hypothesis itself stays open), the "
             "Tate conjecture that is Hodge's arithmetic twin and BSD over function fields, "
             "Bochner's vanishing under positive Ricci curvature, the renormalization group, the NP-hard sign problem, "
             "Manin's algorithm under finite Sha, the Diophantine form of RH, Arnold's geodesic flow. The questions "
             "are the OPEN ENDS hanging off that floor; one of them, Poincare, is closed (Perelman 2002-2003). Nothing "
             "is unified here: each joint is a join mathematics already made, found and cited, sealed where it is "
             "arithmetic. Riemann and Navier-Stokes share no joint - recorded as a miss. Historically the joints are "
             "where the proofs came from: Perelman imported a PDE into topology; Wiles' modularity gave BSD its "
             "L-function. A chain begins from a floor; the connections are where two chains become one."),
    "source": {"label": "Narrow Highway - the Millennium floor (operator seed)", "url": CLAY,
               "ref": "docs/MILLENNIUM_PREPAREDNESS.md", "authority_tier": "engine_derived"},
    "shelf": "codex", "box": "floor",
    "bands": ["floor", "millennium", "chain", "two trees", "mathematics", "physics", "computation"],
    "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
    "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
}

# slug, name, stick, the statement as the Institute states it (one sentence), status, bands
QUESTIONS = [
    _question("riemann", "The Riemann hypothesis", "stick_riemann_hypothesis",
              "Every non-trivial zero of the Riemann zeta function has real part one half.",
              "Open.", ["zeta", "primes", "number theory"]),
    _question("bsd", "The Birch and Swinnerton-Dyer conjecture", "stick_birch_and_swinnerton_dyer_conjecture",
              "The rank of the group of rational points of an elliptic curve over Q equals the order of vanishing "
              "of its L-function at s = 1, and the leading coefficient is the product of its arithmetic invariants.",
              "Open for rank two and above; rank zero and one are theorems (Kolyvagin, Gross-Zagier).",
              ["elliptic curves", "L-functions", "number theory"]),
    _question("navier_stokes", "Navier-Stokes existence and smoothness", "stick_navier_stokes_existence_and_smoothness",
              "In three dimensions, smooth globally defined solutions of the Navier-Stokes equations exist for every "
              "smooth initial datum, or a counterexample does.",
              "Open in three dimensions for large data; closed in two (Ladyzhenskaya 1959).",
              ["fluids", "partial differential equations", "analysis"]),
    _question("yang_mills", "Yang-Mills existence and the mass gap", "stick_yang_mills_existence_and_mass_gap",
              "A quantum Yang-Mills theory exists on four-dimensional Euclidean space for every compact simple gauge "
              "group, and has a mass gap greater than zero.",
              "Open on the continuum; the gap is proven on the lattice at strong coupling (Osterwalder-Seiler 1978).",
              ["gauge theory", "quantum field theory", "physics"]),
    _question("p_vs_np", "P versus NP", "stick_p_versus_np",
              "Is every problem whose solution can be checked in polynomial time also solvable in polynomial time?",
              "Open; the three barriers (relativization, natural proofs, algebrization) are cited on the stick.",
              ["complexity", "computation", "algorithms"]),
    _question("hodge", "The Hodge conjecture", "stick_hodge_conjecture",
              "On a projective non-singular algebraic variety over the complex numbers, every Hodge class is a "
              "rational linear combination of classes of algebraic cycles.",
              "Open from dimension four; closed in dimension three and below (Lefschetz, hard Lefschetz).",
              ["algebraic geometry", "cohomology", "cycles"]),
    _question("poincare", "The Poincare conjecture", "stick_poincare_conjecture",
              "Every simply connected closed three-manifold is homeomorphic to the three-sphere.",
              "PROVEN by Grigori Perelman (2002-2003) by Hamilton's Ricci flow with surgery; the prize awarded in "
              "2010 and declined.",
              ["topology", "three-manifolds", "ricci flow"]),
]

# slug, title, body, bands, the questions it joins, the sources it cites, the seal it carries (a derivation id on
# a stick, or "")
JOINTS = [
    dict(slug="gue_statistics",
         title="Zeta zeros and the lattice Dirac operator share GUE statistics",
         body=("The nearest-neighbour spacings of the zeros of zeta follow the Gaussian Unitary Ensemble of random "
               "matrix theory (Montgomery's pair correlation, 1973; Odlyzko's computation, 1987), and so does the "
               "low-lying spectrum of the Dirac operator in lattice gauge theory (chiral random matrix theory, "
               "Verbaarschot 1994). Hilbert and Polya's reading - the zeros as eigenvalues of an operator - is the "
               "same sentence from the other side (Berry-Keating 1999). The Riemann stick sealed the GUE fit on "
               "Odlyzko's first 10,000 zeros."),
         bands=["random matrices", "gue", "spectral"], joins=("riemann", "yang_mills"),
         cites=("montgomery_1973", "odlyzko_1987", "verbaarschot_1994", "berry_keating_1999"),
         seal="the Riemann stick's spacing witness (seal deefbb6d)"),
    dict(slug="l_functions",
         title="One machinery: Euler product, functional equation, critical line",
         body=("Zeta is the simplest L-function; L(E,s) of an elliptic curve is another, given its analytic "
               "continuation by modularity (Wiles 1995). Both have an Euler product, a functional equation about a "
               "centre, and a critical line; the Grand Riemann Hypothesis names both at once. The engine computes both "
               "sides with the same approximate functional equation: xi(s) = xi(1 - s) sealed at s = 0.3, and "
               "L(11a1, 1) sealed on the BSD stick."),
         bands=["L-functions", "modularity", "functional equation"], joins=("riemann", "bsd"),
         cites=("wiles_1995",), seal="xi_functional_equation_at_s_0_3 (Riemann stick) and the 11a1 instance (BSD stick)"),
    dict(slug="weil_conjectures",
         title="The Weil conjectures (Deligne 1974): the Riemann hypothesis over finite fields, a theorem",
         body=("The Weil conjectures are the analogue of the Riemann hypothesis for the zeta functions of varieties "
               "over FINITE FIELDS, and they are a theorem (Deligne 1974): every eigenvalue of Frobenius on the i-th "
               "cohomology has absolute value q^(i/2). The Riemann hypothesis itself - zeta over the rationals - stays "
               "OPEN, and Deligne's proof has not transferred to it. The proof runs on weights - the finite-field shadow "
               "of Hodge theory - and the positivity it establishes is what Mulmuley's geometric complexity theory, the "
               "one road to P versus NP not excluded by a barrier, leans on. A proven analogue at the centre, three open "
               "questions around it."),
         bands=["weil conjectures", "finite fields", "weights"], joins=("riemann", "hodge", "p_vs_np"),
         cites=("deligne_1974", "mulmuley_2011"), seal=""),
    dict(slug="tate_conjecture",
         title="The Tate conjecture: Hodge's arithmetic twin, and BSD over function fields",
         body=("Tate's conjecture (1965) is the Hodge conjecture with Galois representations in place of Hodge "
               "structures. For an elliptic surface over a finite field, the Tate conjecture is equivalent to the "
               "Birch and Swinnerton-Dyer conjecture for its generic fibre (Artin-Tate 1966, Milne 1975), and both to "
               "the finiteness of the Brauer group. One conjecture, three faces."),
         bands=["tate conjecture", "algebraic cycles", "brauer group"], joins=("hodge", "bsd"),
         cites=("tate_1965", "artin_tate_1966", "milne_1975"), seal=""),
    dict(slug="bochner_vanishing",
         title="Positive Ricci curvature kills harmonic one-forms",
         body=("Bochner (1946): a closed manifold with positive Ricci curvature carries no non-zero harmonic one-form, "
               "so its first Betti number is zero - a Hodge-theoretic conclusion from the very hypothesis Hamilton's "
               "1982 Ricci-flow theorem starts from. Myers (1941): under Ric >= (n - 1)k the diameter is at most "
               "pi/sqrt(k), with equality on the round sphere - sealed on the unit three-sphere."),
         bands=["bochner", "myers", "ricci curvature", "harmonic forms"], joins=("hodge", "poincare"),
         cites=("bochner_1946", "myers_1941", "hamilton_1982"),
         seal="myers_diameter_bound_on_the_unit_s3 (Poincare stick)"),
    dict(slug="renormalization_group",
         title="The renormalization group, and the continuum limit as the question",
         body=("Wilson's lattice (1974) and Forster, Nelson and Stephen's randomly stirred fluid (1977) run the same "
               "renormalization group: a coupling that changes with scale, a finite system whose continuum limit is "
               "the whole question. Asymptotic freedom on one side, the Kolmogorov cascade on the other; the Yang-Mills "
               "stick sealed the running coupling and the Navier-Stokes stick sealed the Kolmogorov scale."),
         bands=["renormalization group", "scaling", "continuum limit"], joins=("yang_mills", "navier_stokes"),
         cites=("wilson_1974", "forster_nelson_stephen_1977"),
         seal="the running coupling (Yang-Mills stick) and the Kolmogorov scale (Navier-Stokes stick)"),
    dict(slug="sign_problem",
         title="The lattice sign problem is NP-hard",
         body=("Troyer and Wiese (2005): the fermion sign problem of quantum Monte Carlo - the obstacle to simulating "
               "lattice gauge theory at finite density - is NP-hard. A proof that P = NP would remove it; its hardness "
               "is a statement about computation sitting inside a statement about gauge fields."),
         bands=["sign problem", "np-hard", "lattice"], joins=("yang_mills", "p_vs_np"),
         cites=("troyer_wiese_2005",), seal=""),
    dict(slug="manin_algorithm",
         title="If Sha is finite, the rank is computable",
         body=("Manin (1971): if the Tate-Shafarevich group is finite - part of what BSD asserts - then the rank of an "
               "elliptic curve over Q is effectively computable by descent. Without it, no algorithm is known. A "
               "conjecture in arithmetic that would decide a question in computation."),
         bands=["manin", "descent", "computability"], joins=("bsd", "p_vs_np"),
         cites=("manin_1971",), seal=""),
    dict(slug="diophantine_rh",
         title="The Riemann hypothesis is one Diophantine equation with no solutions",
         body=("Davis, Matiyasevich and Robinson (1976): the Riemann hypothesis is equivalent to a specific polynomial "
               "Diophantine equation having no solutions in the integers. The hypothesis is a Pi-1 statement; its truth "
               "or failure is a fact about one computation that never halts, or does."),
         bands=["diophantine", "hilbert's tenth", "computability"], joins=("riemann", "p_vs_np"),
         cites=("davis_matiyasevich_robinson_1976",), seal=""),
    dict(slug="arnold_geodesics",
         title="Euler flow is geodesic flow on the volume-preserving diffeomorphisms",
         body=("Arnold (1966): the Euler equations of an ideal fluid are the geodesic equations of the group of "
               "volume-preserving diffeomorphisms with the kinetic-energy metric - the fluid as a point moving on an "
               "infinite-dimensional manifold, the same geometric analysis Perelman's proof lives in. It has not "
               "produced regularity for Navier-Stokes; the join is real and the question stays open."),
         bands=["arnold", "geodesic flow", "diffeomorphisms"], joins=("navier_stokes", "poincare"),
         cites=("arnold_1966",), seal=""),
]

# the Clay descriptions the questions cite (source cards that already exist on the shelf)
DESCRIBED_BY = {"navier_stokes": "fefferman_2000", "yang_mills": "jaffe_witten_2000", "hodge": "deligne_2000",
                "poincare": "perelman_2002"}

CARDS: List[dict] = [FLOOR_CARD] + QUESTIONS + [_joint(j["slug"], j["title"], j["body"], j["bands"]) for j in JOINTS]


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


def _bridges() -> List[dict]:
    out = [_edge(FLOOR, GLOBAL_FLOOR, "part_of", "the Millennium floor rests on the one Floor of Discovery")]
    for q in QUESTIONS:
        out.append(_edge(q["id"], FLOOR, "open_end_of", "an open question hanging off the floor of what is proven"))
    for slug, key in DESCRIBED_BY.items():
        out.append(_edge(_q(slug), _src(key), "cites", "the official description, or the proof, the question is read by"))
    for j in JOINTS:
        jid = _j(j["slug"])
        out.append(_edge(jid, FLOOR, "part_of", "a joint that is proven or observed - a part of the floor"))
        ev = j["title"] + ". " + "; ".join(k.replace("_", " ") for k in j["cites"]) + \
            (". Sealed: " + j["seal"] if j["seal"] else ". Cited, not sealed: no arithmetic to recompute")
        for slug in j["joins"]:
            out.append(_edge(_q(slug), jid, "connects_at", ev))
        for key in j["cites"]:
            out.append(_edge(jid, _src(key), "cites", "the record the joint stands on"))
    return out


BRIDGES: List[dict] = _bridges()


def _validate() -> List[str]:
    errs = []
    ids = {c["id"] for c in CARDS}
    for c in CARDS:
        for k in ("id", "kind", "title", "body", "shelf", "connections"):
            if k not in c:
                errs.append(f"{c.get('id')}: missing {k}")
        json.dumps(c)
    if len(ids) != len(CARDS):
        errs.append("duplicate card ids")
    for e in BRIDGES:
        if e["a"] not in ids and not e["a"].startswith("card_src_mill_"):
            errs.append(f"bridge endpoint not seeded: {e['a']}")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    if errs:
        print("VALIDATION:")
        for e in errs:
            print("  " + e)
    if check:
        print(f"[check] {len(CARDS)} cards, {len(BRIDGES)} bridges; {'OK' if not errs else 'ERRORS'}")
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
