#!/usr/bin/env python3
"""THE BRIDGES — the cross-domain isomorphisms, made first-class.

Matt, 2026-09-14: "This is really about the bridges." A bridge is one structure
appearing in two or more domains — the universality of the one kernel, seen as a
connection. The spiral showed the first batch (forms that span many domains). This
gathers ALL of them into bridge cards, integrated into the body, and searches four
signatures for more:

  1. FORM bridges      — a canonical form realized in >= 2 domains (the first batch)
  2. THEORY bridges    — a same_form edge THE FLOOR already asserts between two theories
  3. THEORY hubs       — one theory that calculations from >= 3 domains rest on
  4. FORM dualities     — deep form<->form relations (FTC, convolution theorem, log-odds...)

Every bridge carries its evidence; a bridge with none is not drawn — the rule between a
map of reality and apophenia. NON-DESTRUCTIVE: writes data/bridge_cards.jsonl (gitignored,
rebuilt from here). Stdlib only.

    python tools/seed_bridges.py --list      # ranked, grouped by kind
    python tools/seed_bridges.py --check      # validate every member resolves
    python tools/seed_bridges.py --rebuild    # (re)write data/bridge_cards.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
from seed_calculations import CALCS, CALC_THEORY, FORMS  # noqa: E402

STORE = ROOT / "data" / "bridge_cards.jsonl"

# --- FORM DUALITIES: deep form<->form bridges (the search for more) ------------
# Each is a standard, named mathematical relationship — found, not invented.
FORM_DUALITIES: list[tuple[str, str, str, str]] = [
    ("exponential", "logarithmic", "inverse functions",
     "exp and log are inverse functions; a logarithmic scale linearizes exponential growth — the same relation read backwards"),
    ("power_law", "logarithmic", "log-log linearity",
     "a power law y = a x^k is a straight line in log-log coordinates (log y = log a + k log x) — the log is the power law's natural ruler"),
    ("accumulation", "linear_flux", "fundamental theorem of calculus",
     "a flux (a rate) and an accumulation (an integral) are inverse operations — differentiate the accumulation and the flux returns"),
    ("fourier_spectral", "convolution", "convolution theorem",
     "convolution in one domain is multiplication in the other; the Fourier transform turns the hardest operation into the easiest"),
    ("fourier_spectral", "periodic", "one object, two domains",
     "a periodic signal IS its Fourier series; a single sinusoid is one spectral line — periodic and spectral are one object seen twice"),
    ("wave", "fourier_spectral", "superposition of frequencies",
     "every wave is a superposition of pure frequencies; the wave equation is solved in the spectral domain"),
    ("gaussian", "diffusion", "the heat kernel",
     "the fundamental solution of diffusion is a Gaussian widening as sqrt(t): the bell curve and the heat equation are the same spreading"),
    ("gaussian", "stochastic", "Brownian increments",
     "Brownian increments are Gaussian; the central-limit bell curve is the marginal of the Wiener process"),
    ("logistic", "exponential", "growth with a ceiling",
     "logistic growth IS exponential growth with a ceiling — for a small population it is indistinguishable from the exponential"),
    ("eigenvalue", "linear_system", "diagonalization",
     "A x = b and A v = lambda v are the inhomogeneous and spectral faces of one linear operator; solving either is diagonalization"),
    ("variational", "optimization", "point vs function",
     "optimization finds the extremal POINT; the variational form finds the extremal FUNCTION — the calculus of variations over an infinite-dimensional space"),
    ("green_function", "convolution", "impulse response",
     "a Green's function IS an impulse response; the solution is its convolution with the source"),
    ("mobius_conformal", "proportion", "fractional-linear map",
     "a Mobius map w = (az+b)/(cz+d) is a fractional-linear RATIO; the Smith chart folds the impedance plane by one proportion of complex numbers"),
    ("probability_ratio", "logarithmic", "log-odds",
     "Bayes multiplies odds; taking logs turns it into ADDING evidence (log-likelihood) — the log-odds bridge from probability to information"),
    ("recursion", "accumulation", "discretization",
     "a recurrence x_{n+1} = x_n + h f is the discrete shadow of an integral; Euler's method turns accumulation into recursion"),
    ("conservation", "linear_flux", "continuity equation",
     "a conservation law in differential form is the continuity equation: the divergence of a flux equals the rate of change of what is stored"),
    ("trigonometric", "periodic", "circle vs oscillation",
     "sine and cosine are the projection of uniform circular motion; the trigonometric relations and periodic oscillation are the circle seen two ways"),
    ("trigonometric", "fourier_spectral", "harmonic basis",
     "Fourier analysis is trigonometry taken to a basis — any signal as a sum of sines and cosines"),
]


def _load_theory() -> tuple[dict[str, str], list[tuple[str, str, str]]]:
    """(id -> title) and the same_form edges between theory cards."""
    titles, edges = {}, []
    p = ROOT / "data" / "theory_cards.jsonl"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                c = json.loads(line)
            except ValueError:
                continue
            titles[c["id"]] = c.get("title", c["id"])
            for cn in c.get("connections", []):
                if cn.get("relationship") == "same_form" and cn.get("to_card_id"):
                    edges.append((c["id"], cn["to_card_id"], cn.get("evidence", "")))
    return titles, edges


def _calc_ids() -> set[str]:
    ids = set()
    p = ROOT / "data" / "calculation_cards.jsonl"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    ids.add(json.loads(line)["id"])
                except (ValueError, KeyError):
                    pass
    return ids


def _pretty(cid: str) -> str:
    return cid.replace("card_theory_", "").replace("card_form_", "").replace("card_calc_", "").replace("_", " ")


def _card(bid, title, body, kind, members, span, extra=None):
    conns = [{"to_card_id": m, "relationship": "bridges", "evidence": ev} for m, ev in members]
    return {
        "id": bid, "kind": "bridge", "title": title, "body": body,
        "source": {"label": "The Bridges — cross-domain isomorphisms", "url": "", "domain": "mathematics", "authority_tier": "reference"},
        "shelf": "bridges", "box": "bridge", "bands": ["bridge", kind], "subject": title,
        "connections": conns, "author": "engine", "created_at": 0.0, "updated_at": 0.0,
        "visibility": "public", "lifecycle_stage": "public", "volatility": "permanent",
        "surface": "secular", "generated": False,
        "extra": {"bridge_kind": kind, "span": span, **(extra or {})},
    }


def build_bridges():
    """Return (cards, report) — report is a list of (kind, span, title) for --list."""
    titles, edges = _load_theory()
    cards, report = [], []

    # 1) FORM bridges — a form realized in >= 2 domains
    form_dom = defaultdict(dict)  # form -> {domain: representative calc_slug}
    for slug, title, formula, domain, form, note in CALCS:
        form_dom[form].setdefault(domain, slug)
    for form, dmap in form_dom.items():
        if len(dmap) < 2:
            continue
        members = [(f"card_form_{form}", f"the {form} form, shared across {len(dmap)} domains")]
        members += [(f"card_calc_{slug}", f"{domain}: {slug.replace('v_','').replace('_',' ')}")
                    for domain, slug in sorted(dmap.items())]
        doms = ", ".join(sorted(dmap))
        cards.append(_card(
            f"card_bridge_form_{form}", f"Bridge: the {form} form across {len(dmap)} domains",
            f"The canonical form {form} ({FORMS.get(form, ('', ''))[0]}) is the SAME computation in "
            f"{len(dmap)} different domains — {doms}. One calculation, many fields, under a change of variable.",
            "form", members, len(dmap), {"domains": sorted(dmap), "form": form}))
        report.append(("form", len(dmap), f"{form}  ({len(dmap)} domains)"))

    # 2) THEORY bridges — same_form isomorphisms THE FLOOR already asserts
    seen = set()
    for a, b, ev in edges:
        key = frozenset((a, b))
        if key in seen or a not in titles or b not in titles:
            continue
        seen.add(key)
        slug = f"{a.replace('card_theory_','')}__{b.replace('card_theory_','')}"[:80]
        cards.append(_card(
            f"card_bridge_theory_{slug}",
            f"Bridge: {titles[a]}  ↔  {titles[b]}",
            f"{titles[a]} and {titles[b]} are the same form in different domains. {ev}",
            "theory", [(a, ev or "same form"), (b, ev or "same form")], 2,
            {"evidence": ev}))
        report.append(("theory", 2, f"{_pretty(a)[:22]} <-> {_pretty(b)[:22]}"))

    # 3) THEORY hubs — one theory that calcs from >= 3 domains rest on
    theory_dom = defaultdict(set)
    slug_dom = {c[0]: c[3] for c in CALCS}
    for slug, tid in CALC_THEORY.items():
        if slug in slug_dom:
            theory_dom[tid].add(slug_dom[slug])
    for tid, doms in theory_dom.items():
        if len(doms) < 3 or tid not in titles:
            continue
        cards.append(_card(
            f"card_bridge_hub_{tid.replace('card_theory_','')}"[:90],
            f"Hub: {titles[tid]} carries {len(doms)} domains",
            f"Calculations from {len(doms)} different domains ({', '.join(sorted(doms))}) all rest on "
            f"{titles[tid]} — one theory holding up many fields.",
            "hub", [(tid, f"{len(doms)} domains rest on this theory")], len(doms),
            {"domains": sorted(doms)}))
        report.append(("hub", len(doms), f"{_pretty(tid)[:28]} ({len(doms)} domains)"))

    # 4) FORM dualities — deep form<->form bridges (the search for more)
    for fa, fb, kind, ev in FORM_DUALITIES:
        if fa not in FORMS or fb not in FORMS:
            continue
        cards.append(_card(
            f"card_bridge_dual_{fa}__{fb}",
            f"Duality: {fa}  ↔  {fb}  ({kind})",
            f"A deep bridge between two forms — {kind}. {ev}",
            "duality", [(f"card_form_{fa}", ev), (f"card_form_{fb}", ev)], 2,
            {"relation": kind, "forms": [fa, fb]}))
        report.append(("duality", 2, f"{fa} <-> {fb}  ({kind})"))

    return cards, report


def cmd_check() -> int:
    cards, _ = build_bridges()
    known = set(FORMS)  # not used directly; ids checked below
    calc_ids = _calc_ids()
    titles, _ = _load_theory()
    form_ids = {f"card_form_{f}" for f in FORMS}
    resolvable = calc_ids | set(titles) | form_ids
    missing = []
    for c in cards:
        for cn in c["connections"]:
            t = cn["to_card_id"]
            if t not in resolvable:
                missing.append((c["id"], t))
    if missing:
        print(f"unresolved bridge members ({len(missing)}):")
        for b, t in missing[:20]:
            print(f"    {b} -> {t}")
        return 3
    kinds = defaultdict(int)
    for c in cards:
        kinds[c["extra"]["bridge_kind"]] += 1
    print(f"OK: {len(cards)} bridges — " + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items()))
          + "; every member resolves.")
    return 0


def cmd_list() -> int:
    _, report = build_bridges()
    for kind in ("form", "hub", "theory", "duality"):
        rows = sorted([r for r in report if r[0] == kind], key=lambda r: -r[1])
        print(f"\n== {kind.upper()} bridges ({len(rows)}) ==")
        for _k, span, label in rows:
            print(f"   [{span:2}] {label}")
    return 0


def cmd_rebuild() -> int:
    if cmd_check():
        return 3
    cards, _ = build_bridges()
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n", encoding="utf-8")
    kinds = defaultdict(int)
    for c in cards:
        kinds[c["extra"]["bridge_kind"]] += 1
    print(f"wrote {STORE}: {len(cards)} bridges (" + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items())) + ")")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()
    if args.list:
        return cmd_list()
    if args.rebuild:
        return cmd_rebuild()
    return cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
