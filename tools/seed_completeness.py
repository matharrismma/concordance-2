#!/usr/bin/env python3
"""COMPLETENESS SETS — the Atlas as a predictor, not only a map.

Some fields have a CLOSED structure: a small set of fundamental quantities whose pairwise
relations form a complete table. When one cell of that table is empty, symmetry does not merely
suggest — it DEMANDS — that something fill it. Leon Chua read the four circuit variables (voltage,
current, charge, flux), saw that five of their six relations were spoken for and the sixth was
empty, and argued in 1971 that a fourth fundamental element MUST exist. HP built the memristor in
2008. The hole in the table was the prediction.

This is the same move as the Atlas's Mendeleev gap-loop, at the grade of a fundamental element:
lay out the complete structure, and the empty cells are predictions. It is a whole CLASS in the
history of science (see PREDICTIONS) — Mendeleev's gallium, Gell-Mann's Omega-minus, Dirac's
positron, Pauli's neutrino, Maxwell's displacement current. Every one: a complete structure, a
hole, a real thing found later.

CONDUIT, NOT SOURCE. Everything here is a CONFIRMED historical prediction — grounded, cited by
date and discoverer, never invented. Having the Atlas emit a NEW prediction (an unfilled cell we
claim must exist) is a further step that must clear the same rigor bar as the master equations'
--check; this file makes no such claim.

    python tools/seed_completeness.py --check    # validate the structure (no hallucination)
    python tools/seed_completeness.py --list
"""
from __future__ import annotations

import argparse
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

# A completeness SET: fundamental quantities + the COMPLETE table of their pairwise relations.
# Each relation carries a status: "definition" (true by construction), "element" (a known law/part),
# or "predicted" (the empty cell that symmetry demanded — with who predicted it and who confirmed it).
SETS: list[dict] = [
    {
        "id": "circuit_variables",
        "title": "The four fundamental circuit elements",
        "domain": "electrical",
        "kind": "gap",
        "finding": ("Two definitions and three known elements filled five edges; the sixth — the "
                    "flux–charge diagonal — was empty. That emptiness was the prediction."),
        "gist": ("Four circuit variables — voltage v, current i, charge q, and magnetic flux φ — "
                 "admit six pairwise relations. Two are definitions (q is the integral of i; φ is the "
                 "integral of v), three are the classic passive elements (resistor, capacitor, inductor), "
                 "and the sixth — linking flux to charge — was EMPTY. Chua argued in 1971 that an element "
                 "must fill it. HP built the memristor in 2008. The hole in the table was the prediction."),
        # the four corners of Chua's square (a diamond: top / right / bottom / left)
        "quantities": [
            {"sym": "v", "name": "voltage", "pos": "top"},
            {"sym": "q", "name": "charge", "pos": "right"},
            {"sym": "i", "name": "current", "pos": "bottom"},
            {"sym": "φ", "name": "flux linkage", "pos": "left"},
        ],
        # the six edges — every pair of {v, q, i, phi}
        "relations": [
            {"pair": ["q", "i"], "name": "charge from current", "formula": "q = ∫ i dt",
             "status": "definition", "note": "charge is the time-integral of current", "calc": "charge_from_current"},
            {"pair": ["φ", "v"], "name": "flux from voltage", "formula": "φ = ∫ v dt",
             "status": "definition", "note": "flux linkage is the time-integral of voltage"},
            {"pair": ["v", "i"], "name": "resistor", "formula": "dv = R·di", "status": "element",
             "element": "Resistor (R)", "since": "Ohm's law, 1827", "calc": "ohms_law"},
            {"pair": ["q", "v"], "name": "capacitor", "formula": "dq = C·dv", "status": "element",
             "element": "Capacitor (C)", "since": "the Leyden jar, 1745"},
            {"pair": ["φ", "i"], "name": "inductor", "formula": "dφ = L·di", "status": "element",
             "element": "Inductor (L)", "since": "Faraday's induction, 1831"},
            {"pair": ["φ", "q"], "name": "memristor", "formula": "dφ = M·dq", "status": "predicted",
             "element": "Memristor (M)",
             "predicted": "Chua, 1971 — from the symmetry of this very table",
             "confirmed": "HP (Strukov, Snider, Stewart & Williams), 2008",
             "note": "memristance M = dφ/dq — a resistance that REMEMBERS the charge that has flowed through it"},
        ],
    },
    {
        "id": "thermodynamic_square",
        "title": "The thermodynamic square — the four potentials",
        "domain": "thermodynamics",
        "kind": "generative",
        "finding": ("The four potentials are the COMPLETE Legendre family of two conjugate pairs — there "
                    "is no fifth. The square's symmetry then FORCES the four Maxwell relations: predicted "
                    "from the structure, confirmed by every measurement ever made."),
        "gist": ("Four state variables in two conjugate pairs — temperature T with entropy S, pressure P "
                 "with volume V — and the four thermodynamic potentials (internal energy U, enthalpy H, "
                 "Helmholtz F, Gibbs G), each a Legendre transform that trades one variable of a pair for its "
                 "partner. Arrange them on a square (Born, 1929): the variables at the corners, the potentials "
                 "on the sides, the conjugate pairs on the diagonals. The equality of each potential's mixed "
                 "second derivatives then yields a Maxwell relation — four in all, and no more."),
        "quantities": [
            {"sym": "S", "name": "entropy", "pos": "top"},
            {"sym": "V", "name": "volume", "pos": "right"},
            {"sym": "T", "name": "temperature", "pos": "bottom"},
            {"sym": "P", "name": "pressure", "pos": "left"},
        ],
        "relations": [
            {"pair": ["S", "V"], "name": "internal energy", "formula": "dU = T dS − P dV",
             "status": "potential", "label": "U", "of": "U(S,V)",
             "maxwell": "(∂T/∂V)ₛ = −(∂P/∂S)ᵥ"},
            {"pair": ["V", "T"], "name": "Helmholtz free energy", "formula": "dF = −S dT − P dV",
             "status": "potential", "label": "F", "of": "F(T,V)",
             "maxwell": "(∂S/∂V)ₜ = (∂P/∂T)ᵥ"},
            {"pair": ["T", "P"], "name": "Gibbs free energy", "formula": "dG = −S dT + V dP",
             "status": "potential", "label": "G", "of": "G(T,P)",
             "maxwell": "(∂S/∂P)ₜ = −(∂V/∂T)ₚ"},
            {"pair": ["P", "S"], "name": "enthalpy", "formula": "dH = T dS + V dP",
             "status": "potential", "label": "H", "of": "H(S,P)",
             "maxwell": "(∂T/∂P)ₛ = (∂V/∂S)ₚ"},
            {"pair": ["S", "T"], "name": "thermal conjugates", "formula": "T·S → heat",
             "status": "conjugate", "label": "◇",
             "note": "temperature and entropy are conjugate — their product carries energy as heat"},
            {"pair": ["V", "P"], "name": "mechanical conjugates", "formula": "P·V → work",
             "status": "conjugate", "label": "◇",
             "note": "pressure and volume are conjugate — their product carries energy as work"},
        ],
    },
]

# THE WATCH: complete subsystems are whole on their own, but the PERFORMANCE is in how they mesh.
# A connection is given the same weight as a set, and the same rigor: it carries its EVIDENCE (the
# shared form or method), or it is a forced analogy, which is a broken gear. Between = the two set ids.
CONNECTIONS: list[dict] = [
    {"between": ["circuit_variables", "thermodynamic_square"], "kind": "same method",
     "shared": "prediction from structural completeness — read two ways",
     "evidence": ("Both close a table by symmetry. The circuit square shows the GAP face: an empty cell "
                  "(flux–charge) that demanded the memristor. The thermodynamic square shows the "
                  "GENERATIVE face: a full table whose symmetry FORCES the four Maxwell relations. One "
                  "method, two faces — a hole predicts a thing; a full structure predicts a law.")},
    {"between": ["circuit_variables", "thermodynamic_square"], "kind": "same form",
     "shared": "a complete K₄ on four quantities, drawn as a square with two distinguished diagonals",
     "evidence": ("They are the SAME graph: four fundamental quantities, all six pairwise relations, on a "
                  "square whose two diagonals are the special ones — resistor and memristor for circuits, "
                  "the two conjugate pairs (T–S, P–V) for thermodynamics. The completeness FORM is "
                  "identical though the fields are not; the semantics of the diagonals differ, and that "
                  "difference is itself the finding.")},
]

# The class the memristor belongs to: great predictions made from the completeness of a structure.
# Each is a CONFIRMED historical result (field, the structure, the empty cell, what filled it, the years).
PREDICTIONS: list[dict] = [
    {"field": "chemistry", "structure": "the periodic table",
     "hole": "gaps between known elements in atomic weight and valence",
     "predicted": "gallium, scandium & germanium — each with its properties",
     "by": "Mendeleev", "year": 1869, "confirmed": "1875–1886"},
    {"field": "electrical", "structure": "the four circuit variables (this table)",
     "hole": "the flux–charge relation",
     "predicted": "the memristor, the fourth fundamental element",
     "by": "Chua", "year": 1971, "confirmed": "2008 (HP)"},
    {"field": "particle physics", "structure": "the SU(3) 'eightfold way' baryon decuplet",
     "hole": "the tenth, empty slot",
     "predicted": "the Ω⁻ baryon, mass and all",
     "by": "Gell-Mann", "year": 1962, "confirmed": "1964"},
    {"field": "quantum physics", "structure": "the Dirac equation",
     "hole": "the negative-energy solutions its symmetry required",
     "predicted": "the positron — antimatter",
     "by": "Dirac", "year": 1928, "confirmed": "1932 (Anderson)"},
    {"field": "nuclear physics", "structure": "the energy–momentum–spin ledger of beta decay",
     "hole": "energy and angular momentum that did not balance",
     "predicted": "the neutrino",
     "by": "Pauli", "year": 1930, "confirmed": "1956 (Cowan–Reines)"},
    {"field": "electromagnetism", "structure": "Maxwell's equations and charge conservation",
     "hole": "an inconsistency in Ampère's law",
     "predicted": "the displacement current — and with it, electromagnetic waves",
     "by": "Maxwell", "year": 1865, "confirmed": "1887 (Hertz)"},
]

_VALID_STATUS = {"definition", "element", "predicted", "potential", "conjugate"}


def _pairs_of(quantities: list[dict]) -> set:
    syms = [q["sym"] for q in quantities]
    return {frozenset((a, b)) for i, a in enumerate(syms) for b in syms[i + 1:]}


def check() -> int:
    """Validate: each set's relations cover EVERY pair exactly once, statuses are valid, and a
    predicted cell carries both who predicted it and who confirmed it (no bare claim)."""
    errs: list[str] = []
    for s in SETS:
        want = _pairs_of(s["quantities"])
        seen = []
        for r in s["relations"]:
            if r["status"] not in _VALID_STATUS:
                errs.append(f"{s['id']}: relation {r['name']!r} has bad status {r['status']!r}")
            fs = frozenset(r["pair"])
            if fs not in want:
                errs.append(f"{s['id']}: relation {r['name']!r} pairs unknown quantities {r['pair']}")
            seen.append(fs)
            if r["status"] == "predicted" and not (r.get("predicted") and r.get("confirmed")):
                errs.append(f"{s['id']}: predicted cell {r['name']!r} must cite who predicted AND who confirmed it")
        if set(seen) != want:
            missing = want - set(seen)
            extra = [tuple(x) for x in seen if seen.count(x) > 1]
            errs.append(f"{s['id']}: relation table is not the COMPLETE set of pairs "
                        f"(missing={[tuple(m) for m in missing]}, duplicated={extra})")
    for p in PREDICTIONS:
        for k in ("field", "structure", "hole", "predicted", "by", "year", "confirmed"):
            if not p.get(k):
                errs.append(f"prediction by {p.get('by','?')} missing {k!r}")
    # the watch: a connection is held to the same bar as a set — real endpoints and its own evidence,
    # or it is a forced analogy, which is a broken gear.
    ids = {s["id"] for s in SETS}
    for c in CONNECTIONS:
        for sid in c.get("between", []):
            if sid not in ids:
                errs.append(f"connection references unknown set {sid!r}")
        if len(c.get("between", [])) != 2:
            errs.append(f"connection {c.get('between')} must join exactly two sets")
        if not (c.get("shared") and c.get("evidence")):
            errs.append(f"connection {c.get('between')} lacks a shared form AND evidence (a forced analogy is a broken gear)")
    if errs:
        print("FAIL:")
        for e in errs:
            print("   ", e)
        return 1
    npred = sum(1 for s in SETS for r in s["relations"] if r["status"] == "predicted")
    print(f"OK: {len(SETS)} completeness set(s), every relation table complete; {npred} predicted-then-"
          f"confirmed cell(s); {len(CONNECTIONS)} evidenced connection(s); {len(PREDICTIONS)} historical "
          f"predictions, all confirmed.")
    return 0


def _list() -> int:
    for s in SETS:
        print(f"\n{s['title']}  [{s['domain']}]")
        for r in s["relations"]:
            tag = {"definition": "def ", "element": "elem", "predicted": "PRED"}[r["status"]]
            extra = r.get("element", "") or ""
            print(f"  {tag}  {'–'.join(r['pair']):9s} {r['formula']:14s} {extra}")
    print(f"\nThe class ({len(PREDICTIONS)} confirmed predictions from structure):")
    for p in PREDICTIONS:
        print(f"  {p['by']:10s} {p['year']}  {p['predicted']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        return _list()
    return check()


if __name__ == "__main__":
    sys.exit(main())
