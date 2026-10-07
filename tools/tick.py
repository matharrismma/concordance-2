#!/usr/bin/env python3
"""THE TICK STICK — make a mark (docs/TICK_STICK.md; Matt, 2026-10-05).

    PYTHONPATH=src python tools/tick.py seed                 # open the first sticks with their cited marks
    PYTHONPATH=src python tools/tick.py document              # write the Riemann attempt's record onto its stick
    PYTHONPATH=src python tools/tick.py lnh                   # Dirac's Large Numbers Hypothesis: seal N1, cite the rest
    PYTHONPATH=src python tools/tick.py alpha                 # the fine-structure constant: seal alpha, cite the 137
    PYTHONPATH=src python tools/tick.py forces                # the four forces under alpha: QED a_e, Weinberg angle, QCD sign
    PYTHONPATH=src python tools/tick.py ab                    # the Aharonov-Bohm effect: seal the flux quantum + phase law
    PYTHONPATH=src python tools/tick.py fiber                 # fiber optic calibration: seal the decibel scale + the method
    PYTHONPATH=src python tools/tick.py symphony              # the coherence witness: seal the Pythagorean comma + temperament
    PYTHONPATH=src python tools/tick.py robin [N]             # chart the Riemann window by elimination (Robin to N)
    PYTHONPATH=src python tools/tick.py schoenfeld [X]        # chart it from the prime count too (Schoenfeld to X)
    PYTHONPATH=src python tools/tick.py lagarias [N]          # and through Lagarias's elementary inequality (to N)
    PYTHONPATH=src python tools/tick.py nicolas [P]           # and through Nicolas's primorial criterion (primes to P)
    PYTHONPATH=src python tools/tick.py gue                   # another domain: the zeros' spacings are GUE (random-matrix)
    PYTHONPATH=src python tools/tick.py residual              # the sight picture: S(T), the count's signed miss, vs RH's envelope
    PYTHONPATH=src python tools/tick.py count [T]             # count the zeros at a great height (Turing; a count, not on-line)
    PYTHONPATH=src python tools/tick.py bsd [label|all]      # BSD: seal one curve, or every curve in the ingested table
    PYTHONPATH=src python tools/tick.py window [stick]        # the surviving window of each stick (narrow by elimination)
    PYTHONPATH=src python tools/tick.py riemann 200          # verify every zero up to T = 200 is on the line,
                                                             # SEAL it through the same path as POST /verify, tick
    PYTHONPATH=src python tools/tick.py read stick_riemann_hypothesis

A sealed mark is minted exactly as the verify door mints one (derivation → receipts.attach → CAS + ledger), so the
tick's seal is a real, re-checkable entry in this node's keeping. The verify door's 8-second shed does not apply
here: the tool raises CONCORDANCE_VERIFY_TIMEOUT_S before the engine loads, because a mark at T = 2000 takes minutes
and is still a verification, not a proof. Run it ON THE BRANCH (the box): a mark minted on a replica stays there
until marks travel back (Gen 3 · 1b).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CONCORDANCE_DATA_DIR", str(ROOT / "data"))
os.environ.setdefault("CONCORDANCE_VERIFY_TIMEOUT_S", "1800")     # before derivation is imported
os.environ.setdefault("CONCORDANCE_RIEMANN_MAX", "1e9")           # the operator's tool lifts the door's height cap
# This is a cold one-shot process: seal bounded, never build the whole corpus to index a card that would
# vanish when we exit. The CAS object + ledger link + durable card copies are still written; the card is
# folded into the corpus at the next server load. (receipts._index_default reads this.)
os.environ.setdefault("CONCORDANCE_SEAL_INDEX", "0")

STICKS = [
    {"question": "Riemann hypothesis", "field": "number_theory",
     "statement": "Every non-trivial zero of the Riemann zeta function has real part 1/2.",
     "references": ["Riemann, Ueber die Anzahl der Primzahlen unter einer gegebenen Grösse (1859)",
                    "Clay Mathematics Institute, Millennium Prize Problems (2000)"],
     "ticks": [
         {"kind": "equivalence", "claim": "RH is equivalent to |pi(x) - li(x)| < sqrt(x) log(x) / (8 pi) for all x >= 2657",
          "source": "L. Schoenfeld, Sharper bounds for the Chebyshev functions theta(x) and psi(x). II, Math. Comp. 30 (1976) 337-360"},
         {"kind": "equivalence", "claim": "RH is equivalent to sigma(n) < e^gamma n log log n for all n > 5040 (Robin's inequality)",
          "source": "G. Robin, Grandes valeurs de la fonction somme des diviseurs et hypothese de Riemann, J. Math. Pures Appl. 63 (1984) 187-213"},
         {"kind": "equivalence", "claim": "RH is equivalent to the Mertens-type bound M(x) = O(x^(1/2 + epsilon)) for every epsilon > 0",
          "source": "E. C. Titchmarsh, The Theory of the Riemann Zeta-Function, 2nd ed. (1986), Theorem 14.25"},
     ]},
    {"question": "P versus NP", "field": "computer_science",
     "statement": "Is every problem whose solutions can be verified in polynomial time also solvable in polynomial time?",
     "references": ["S. Cook, The complexity of theorem-proving procedures, STOC (1971)",
                    "Clay Mathematics Institute, Millennium Prize Problems (2000)"],
     "ticks": [
         {"kind": "exclusion", "claim": "relativizing proof techniques cannot resolve P vs NP: there are oracles A, B with P^A = NP^A and P^B != NP^B",
          "source": "T. Baker, J. Gill, R. Solovay, Relativizations of the P =? NP question, SIAM J. Comput. 4 (1975) 431-442"},
         {"kind": "exclusion", "claim": "natural proofs cannot separate P from NP if strong pseudorandom generators exist",
          "source": "A. Razborov, S. Rudich, Natural proofs, J. Comput. System Sci. 55 (1997) 24-35"},
         {"kind": "exclusion", "claim": "algebrizing proof techniques cannot resolve P vs NP",
          "source": "S. Aaronson, A. Wigderson, Algebrization: a new barrier in complexity theory, ACM Trans. Comput. Theory 1 (2009) 2:1-2:54"},
     ]},
    {"question": "Navier-Stokes existence and smoothness", "field": "physics",
     "statement": "Do smooth, globally defined solutions exist for the three-dimensional incompressible Navier-Stokes equations with smooth initial data?",
     "references": ["Clay Mathematics Institute, Millennium Prize Problems (2000)"], "ticks": []},
    {"question": "Yang-Mills existence and mass gap", "field": "physics",
     "statement": "Does a quantum Yang-Mills theory exist on R^4 for any compact simple gauge group, with a mass gap Delta > 0?",
     "references": ["Clay Mathematics Institute, Millennium Prize Problems (2000)"], "ticks": []},
    {"question": "Hodge conjecture", "field": "mathematics",
     "statement": "On a projective non-singular complex algebraic variety, is every Hodge class a rational linear combination of classes of algebraic cycles?",
     "references": ["Clay Mathematics Institute, Millennium Prize Problems (2000)"], "ticks": []},
    {"question": "Birch and Swinnerton-Dyer conjecture", "field": "number_theory",
     "statement": "For an elliptic curve E over Q, is the rank of E(Q) equal to the order of vanishing of L(E, s) at s = 1?",
     "references": ["B. Birch, H. P. F. Swinnerton-Dyer, Notes on elliptic curves. II, J. Reine Angew. Math. 218 (1965) 79-108",
                    "Clay Mathematics Institute, Millennium Prize Problems (2000)"], "ticks": []},
    {"question": "Poincare conjecture", "field": "mathematics",
     "statement": "Every simply connected closed 3-manifold is homeomorphic to the 3-sphere. SOLVED: Perelman, 2002-2003.",
     "references": ["G. Perelman, The entropy formula for the Ricci flow and its geometric applications, arXiv:math/0211159 (2002)",
                    "G. Perelman, Ricci flow with surgery on three-manifolds, arXiv:math/0303109 (2003)"],
     "ticks": [{"kind": "note", "claim": "Solved by Perelman (2002-2003) via Hamilton's Ricci flow with surgery; prize declined 2010. The stick is kept as the one Millennium problem with a proof.",
                "source": "Clay Mathematics Institute, 2010"}]},
]


def seed() -> int:
    from concordance import tickstick as T
    for s in STICKS:
        r = T.create(s["question"], s.get("statement", ""), s.get("field", ""), s.get("references"))
        sid = r["id"]
        print(("opened " if not r.get("existed") else "exists ") + sid)
        have = {(t.get("kind"), t.get("claim")) for t in T.read(sid).get("ticks", [])}
        for t in s.get("ticks", []):
            if (t["kind"], t["claim"]) in have:
                continue
            rr = T.tick(sid, t["kind"], t["claim"], source=t.get("source", ""), by="tools/tick.py seed")
            print("  " + ("tick " + t["kind"] if rr.get("ok") else "REFUSED: " + rr.get("error", "")))
    return 0


def riemann(T_height: float) -> int:
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    # the mark is honest only if the claim is what the engine finds: count first, then claim that count
    from concordance.verifiers import number_theory as NT
    t0 = time.time()
    on_line, n_strip, S, rescans = NT._zeros_on_line_checked(T_height)
    print(f"T = {T_height:g}: on the line {on_line}, in the strip {n_strip:.4f} (S = {S:.3f}, {rescans} localised rescans) in {time.time() - t0:.1f}s")
    if on_line != int(round(n_strip)):
        print("the two counts disagree — no mark is made (a miss stays a miss)")
        return 1
    steps = [{"id": "critical_line", "domain": "number_theory",
              "spec": {"NUM_VERIFY": {"critical_line_height": T_height, "claimed_zeros_on_line": on_line}}}]
    res = verify_derivation(steps)
    if res.get("verdict") != "HOLDS":
        print("the verifier did not HOLD:", json.dumps(res)[:400])
        return 1
    res = receipts.attach(res, config=EngineConfig(), domain="number_theory")
    seal = (res.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted:", json.dumps(res.get("seal"))[:200])
        return 1
    print("sealed", seal, (res.get("seal") or {}).get("cite_url"))
    sid = TS.create("Riemann hypothesis")["id"]
    r = TS.tick(sid, "bound", f"every non-trivial zero of zeta with 0 < Im(s) <= {T_height:g} lies on the critical line "
                              f"({on_line} zeros; the on-line count equals Backlund's strip count)",
                seal=seal, up_to=T_height, unit="height T", by="tools/tick.py riemann")
    print(json.dumps({"ok": r.get("ok"), "error": r.get("error"), "fit": (r.get("fit") or {}).get("verified_up_to"),
                      "open": (r.get("fit") or {}).get("open")}, indent=1))
    return 0 if r.get("ok") else 1


# The curves Cremona's tables name (a-invariants, conductor, root number, the algebraic rank the tables record).
# J. E. Cremona, Algorithms for Modular Elliptic Curves (1997) and the LMFDB; a-invariants are facts, not prose.
CURVES = {
    "11a1":   {"a": [0, -1, 1, -10, -20], "N": 11,   "w": 1,  "rank": 0},
    "37a1":   {"a": [0, 0, 1, -1, 0],     "N": 37,   "w": -1, "rank": 1},
    "389a1":  {"a": [0, 1, 1, -2, 0],     "N": 389,  "w": 1,  "rank": 2},
    "5077a1": {"a": [0, 0, 1, -7, 6],     "N": 5077, "w": -1, "rank": 3},
}


def _load_curve_table() -> None:
    """Fold data/elliptic_curves.jsonl (ingested from Cremona's ecdata, with provenance) into CURVES, so the BSD
    stick is charted from a real table and not a handful of hand-typed curves. The engine still re-derives L(E,1),
    the root number and the analytic rank for every one — the table is the set of curve identities, nothing trusted."""
    p = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data"))) / "elliptic_curves.jsonl"
    if not p.exists():
        return
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "_meta" in row:
                continue
            CURVES[row["label"]] = {"a": row["a_invariants"], "N": row["conductor"],
                                    "w": row["root_number"], "rank": row["rank"]}
    except (OSError, ValueError, KeyError):
        pass                                              # the four built-ins above stand if the table is unreadable


_load_curve_table()


def bsd(label: str) -> int:
    """A mark on the Birch and Swinnerton-Dyer stick: compute L(E,1) (and L'(E,1)), seal it, and tick an INSTANCE
    when a theorem carries the analytic rank to the algebraic rank (0 or 1), a WITNESS when it does not (≥ 2)."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    c = CURVES.get(label)
    if not c:
        print(f"unknown curve {label!r}; held: {sorted(CURVES)}")
        return 2
    spec = {"a_invariants": c["a"], "conductor": c["N"], "root_number": c["w"],
            "claimed_analytic_rank": c["rank"] if c["rank"] <= 1 else c["rank"]}
    res = verify_derivation([{"id": "l_value", "domain": "elliptic_curves", "spec": {"ELLIPTIC_VERIFY": spec}}])
    if res.get("verdict") != "HOLDS":
        print("the verifier did not HOLD:", json.dumps(res)[:500])
        return 1
    res = receipts.attach(res, config=EngineConfig(), domain="elliptic_curves")
    seal = (res.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted")
        return 1
    step = (res.get("steps") or res.get("trail") or [{}])[0] if isinstance(res.get("steps") or res.get("trail"), list) else {}
    print("sealed", seal, (res.get("seal") or {}).get("cite_url"))
    sid = TS.create("Birch and Swinnerton-Dyer conjecture")["id"]
    if any(t.get("seal") == seal for t in TS.read(sid).get("ticks", [])):
        print("  already on the stick (same seal) — not duplicated")
        return 0
    if c["rank"] <= 1:
        kind = "instance"
        claim = (f"E = {label} (conductor {c['N']}): L(E,1) {'≠ 0' if c['rank'] == 0 else '= 0 with L′(E,1) ≠ 0'} computed by the "
                 f"approximate functional equation; analytic rank {c['rank']} ⇒ rank E(Q) = {c['rank']} "
                 f"({'Kolyvagin 1989' if c['rank'] == 0 else 'Gross–Zagier 1986 + Kolyvagin 1989'}); BSD's rank statement holds for E")
    else:
        kind = "witness"
        claim = (f"E = {label} (conductor {c['N']}): L(E,1) = 0 and the first {c['rank']-1} derivative(s) vanish numerically — analytic "
                 f"rank ≥ {c['rank']}; the algebraic rank {c['rank']} is Cremona's table's, no theorem carries it here")
    r = TS.tick(sid, kind, claim, seal=seal, by="tools/tick.py bsd")
    print(json.dumps({"ok": r.get("ok"), "error": r.get("error"), "kind": kind, "instances": (r.get("fit") or {}).get("verified_instances"),
                      "witnesses": (r.get("fit") or {}).get("witnesses")}, indent=1))
    return 0 if r.get("ok") else 1


RIEMANN_RECORD = [
    ("method", "Two independent counts must agree before any bound is sealed: the sign changes of Hardy's Z(t) ON "
               "the critical line (Riemann-Siegel), and Backlund's argument-principle count N(T) = theta(T)/pi + 1 "
               "+ S(T) IN the strip. Agreement is the verification; disagreement seals nothing. This is "
               "Turing's/Backlund's method, how every published verification is done. It verifies RH UP TO A "
               "HEIGHT T; it is not, and does not become, a proof of the hypothesis."),
    ("the honest record", "The first attempt at T=1,000,000 came up 18 zeros short of the strip count — close pairs "
               "the grid stepped over — and sealed NOTHING. A parabolic dip detector (recounting exactly wherever "
               "the sampled curve is predicted to dip below zero) closed the gap, and the independent strip count "
               "stays the authority: no bound was ever sealed on a count that did not agree."),
    ("compute", "Hardy's Z is swept by a C kernel (Riemann-Siegel, OpenMP, log(k) and 1/sqrt(k) precomputed), numpy "
               "where no compiler is present, pure python as the floor — all the same formula, deferring to exact "
               "mpmath near every zero, so the zero count is the same whichever backend ran. T=10,000,000 "
               "(21,136,125 zeros) took about 2.2 hours on one four-core box; the two methods landed on the known "
               "value N(1e7) = 21,136,125."),
    ("open", "The sealed bound stands at T=10,000,000 (progression 200, 500, 1k, 10k, 100k, 200k, 1M, 10M). Beyond "
               "it the cosines of the main sum are the cost floor; a blocked or FFT main sum would reach higher. "
               "The hypothesis itself — that EVERY non-trivial zero, to infinite height, lies on the line — is "
               "unproven here and everywhere. The stick records how far the verification reaches, not that it is settled."),
]


def document() -> int:
    """Write the attempt's RECORD onto the Riemann stick as note ticks (Matt, 2026-10-05: document the whole
    attempt in the stick). Idempotent: a note already present by its text is not added again."""
    from concordance import tickstick as T
    sid = T.create("Riemann hypothesis")["id"]
    have = {t.get("claim") for t in T.read(sid).get("ticks", [])}
    added = 0
    for label, text in RIEMANN_RECORD:
        claim = f"[{label}] {text}"
        if claim in have:
            continue
        r = T.tick(sid, "note", claim, by="Narrow Highway — the Riemann attempt, 2026-10-05")
        print(("noted: " + label) if r.get("ok") else ("REFUSED " + label + ": " + r.get("error", "")))
        added += 1 if r.get("ok") else 0
    print(json.dumps({"stick": sid, "notes_added": added, "record_lines": len(T.read(sid)["fit"]["record"])}, indent=1))
    return 0


def lnh() -> int:
    """Dirac's Large Numbers Hypothesis as a tick stick: SEAL the arithmetic (the dimensionless ratios the
    engine can compute from its attested constants), CITE the conjecture and its observational constraints,
    and endorse nothing. A coincidence of magnitudes is not a law — the project's standing discernment."""
    import math
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    e = C["elementary_charge"]["value"]; eps0 = C["vacuum_permittivity"]["value"]
    G = C["gravitational_constant"]["value"]; mp = C["proton_mass"]["value"]; me = C["electron_mass"]["value"]
    N1 = e ** 2 / (4 * math.pi * eps0 * G * mp * me)
    expr = f"({e!r})**2 / (4*pi*({eps0!r})*({G!r})*({mp!r})*({me!r}))"   # the attested CODATA values, embedded
    r = verify_derivation([{"id": "N1", "domain": "mathematics",
          "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": N1, "rel_tol": 1e-9}}}])
    if r.get("verdict") != "HOLDS":
        print("the ratio did not verify:", json.dumps(r)[:400]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="physical_constants")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed N1", seal)
    sid = TS.create("Dirac's Large Numbers Hypothesis",
                    statement=("The large dimensionless ratios of nature are all near 10^40 and, Dirac conjectured, "
                               "causally linked — so the gravitational constant would weaken as the universe ages "
                               "(G proportional to 1/t). It is a physical conjecture about whether a coincidence of "
                               "magnitudes is a law."),
                    field="physics",
                    references=["P. A. M. Dirac, The Cosmological Constants, Nature 139 (1937) 323",
                                "P. A. M. Dirac, A New Basis for Cosmology, Proc. Roy. Soc. A 165 (1938) 199"])["id"]
    marks = [
        ("witness", f"The electromagnetic-to-gravitational force ratio between a proton and an electron, "
                    f"N1 = e^2 / (4*pi*eps0*G*m_p*m_e) = {N1:.6e} (~10^39.4), computed from the engine's attested "
                    f"CODATA constants — the first of Dirac's large numbers, as an arithmetic fact", dict(seal=seal)),
        ("note", "[the coincidence] Dirac's second large number is the age of the universe in atomic time units, "
                 "N2 = T_Hubble / (e^2/(4*pi*eps0*m_e*c^3)) ~ 10^40.7 — within about one order of magnitude of N1. "
                 "The Large Numbers Hypothesis is the conjecture that this nearness is not accidental but a "
                 "relation, from which Dirac drew G proportional to 1/t. N2 rests on the Hubble time, a measured "
                 "cosmological quantity, not a constant — so it is cited, not sealed.", {}),
        ("exclusion", "The hypothesis's physical prediction — a time-varying G — is strongly constrained by "
                      "observation: lunar laser ranging bounds |G_dot/G| below a few * 10^-13 per year, far smaller "
                      "than the ~10^-10 per year a Dirac 1/t law needs; Big Bang nucleosynthesis and the Oklo "
                      "natural reactor bound the variation of the constants over billions of years. The causal "
                      "hypothesis is disfavored.",
         dict(source="J. G. Williams, S. G. Turyshev, D. H. Boggs, Phys. Rev. Lett. 93 (2004) 261101 (lunar laser "
                     "ranging); A. I. Shlyakhter, Nature 264 (1976) 340 and T. Damour & F. Dyson, Nucl. Phys. B 480 "
                     "(1996) 37 (the Oklo reactor)")),
        ("note", "[discernment] The engine seals that N1 IS ~2.27*10^39 — the arithmetic is a fact. It does not "
                 "endorse that N1 and N2 being near 10^40 is a law; a coincidence of magnitudes is not one, and the "
                 "observational bounds above weigh against the causal claim. Seal the arithmetic, cite the "
                 "conjecture, endorse nothing.", {}),
    ]
    for kind, claim, kw in marks:
        res = TS.tick(sid, kind, claim, by="Narrow Highway — the large-numbers reading, 2026-10-05", **kw)
        print(("  " + kind) if res.get("ok") else ("  REFUSED " + kind + ": " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"], "excluded": len(f["excluded_approaches"]),
                      "record": len(f["record"]), "open": f["open"]}, indent=1))
    return 0


def symphony() -> int:
    """The symphony as the COHERENCE witness (Matt, 2026-10-06). Music is a refined system with a full
    ruleset whose narrow window is 'what sounds whole'. SEAL the computable law: the Pythagorean comma
    (3/2)^12 / 2^7 — twelve pure fifths overshoot seven octaves by this gap — which is WHY the scale must
    be tempered; equal temperament is the calibration that distributes the comma evenly (each fifth
    flattened by 1/12 comma) so every key is playable (the tempered semitone 2^(1/12); the octave 2 exact).
    The coherence axis the generals and games do not cover: many independent voices concorded into one
    body. Seal the ratios; the beauty is gathered, not pronounced; borrow the form."""
    import math
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    comma = (3 / 2) ** 12 / 2 ** 7            # the Pythagorean comma ~ 1.0136432647705078
    expr = "(3/2)**12 / 2**7"
    r = verify_derivation([{"id": "pythagorean_comma", "domain": "mathematics",
          "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": comma, "rel_tol": 1e-12}}}])
    if r.get("verdict") != "HOLDS":
        print("the comma did not verify:", json.dumps(r)[:400]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed the Pythagorean comma", seal)
    sid = TS.create("The symphony",
                    statement=("Music is a refined system whose narrow window is coherence — what sounds whole. "
                               "Many independent voices concorded into one body; tension sought and resolved; "
                               "a form that, once heard, feels inevitable."),
                    field="music")["id"]
    semitone = 2 ** (1 / 12)
    synt = 81 / 80                      # the syntonic comma: Pythagorean major third 81/64 vs just 5/4
    et5 = 2 ** (7 / 12)                 # the equal-tempered fifth vs the pure 3/2

    def _seal(nid, e, v):
        rr = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": e, "claimed_value": v, "rel_tol": 1e-12}}}])
        if rr.get("verdict") != "HOLDS":
            print("  %s did not verify" % nid); return None
        rr = receipts.attach(rr, config=EngineConfig(), domain="mathematics")
        return (rr.get("seal") or {}).get("content_hash")

    s_synt = _seal("syntonic_comma", "81/80", synt)
    s_et5 = _seal("equal_tempered_fifth", "2**(7/12)", et5)
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"The harmonic basis is exact ratio: the octave 2:1, the perfect fifth 3:2. Twelve pure fifths "
                    f"overshoot seven octaves by the Pythagorean comma (3/2)^12 / 2^7 = {comma:.13f} — so the scale "
                    f"cannot be both pure and closed. Equal temperament is the calibration that distributes the comma "
                    f"evenly: the semitone is 2^(1/12) = {semitone:.10f} and twelve of them close the octave at "
                    f"exactly 2. An arithmetic fact; the reason every key is playable.", seal),
        ("note", "[the principle] The symphony is the one-body pattern made audible: counterpoint is many "
                 "independent voices, each whole, concorded into one body under one movement (1 Cor 12, etheto) — "
                 "not a swarm of soloists and not a unison. Tension is sought so it can be resolved; the theme is "
                 "stated, developed, and returned; the form feels inevitable because every part serves the whole. "
                 "This is the COHERENCE axis the generals and the games do not reach.", None),
        ("note", "[the guard] The engine seals the ratios and the comma — the arithmetic is a fact. It does NOT "
                 "pronounce what is beautiful or that life obeys sonata form; the coherence the symphony witnesses "
                 "is a principle we GATHER, never a verdict the engine renders. Borrow the form; launder nothing.", None),
        ("witness", f"[a second comma] The syntonic comma, 81/80 = {synt:.6f}, is the gap between the Pythagorean "
                    f"major third (81/64, four fifths up) and the pure just third (5/4). A second place the pure "
                    f"ratios refuse to close — a tuning that makes thirds pure throws the fifths off, and one that "
                    f"makes fifths pure throws the thirds off. Sealed; the ear hears the trade.", s_synt),
        ("witness", f"[the distributed comma] Equal temperament pays the debt evenly: the tempered fifth is "
                    f"2^(7/12) = {et5:.6f}, about 1.955 cents flat of the pure 3/2 = 1.5 — too small to offend, "
                    f"spread across all twelve so every key is equally in tune and equally, slightly, out. Sealed. "
                    f"Temperament is a CALIBRATION, not a cure.", s_et5),
        ("note", "[the comma cannot be closed, only distributed] The deepest coherence law: no tuning is "
                 "simultaneously pure and closed — the commas cannot be eliminated, only spread. Perfect coherence "
                 "is unreachable WITHIN the system; the honest move is to distribute the gap so the whole stays "
                 "playable. It is the audible kin of Godel (a system cannot close itself from the inside) and of the "
                 "Hole: the window of what-sounds-whole is narrow, the closure never total, and the beauty is the "
                 "wise compromise — many voices into one body, the four-into-one the forces and Langlands also seek, "
                 "heard rather than proven. Narrowing is evidence, never a perfect proof.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway — the symphony, the coherence witness, 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def fiber() -> int:
    """Fiber optic calibration as a sealed anchor + the method stick (docs/FIBER_OPTIC_CALIBRATION.md).
    SEAL the decibel identity that the loss scale rests on — a factor of two in optical power is exactly
    3.0102999566 dB (10^(3.0103/10) = 2) — and open the method stick: reference, read the ticks (OTDR),
    correct to source, triangulate many references (the concordance/Birge check) to the converged narrow
    signal. The calibration method, named in hardware. Seal the arithmetic; calibrate to FIND; launder nothing."""
    import math
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    db_half = 10.0 * math.log10(2.0)         # 3.0102999566... dB per factor of two in power
    expr = f"10**(({db_half!r})/10)"          # the inverse identity, arithmetic only: = 2 exactly
    r = verify_derivation([{"id": "decibel_half_power", "domain": "mathematics",
          "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": 2.0, "rel_tol": 1e-9}}}])
    if r.get("verdict") != "HOLDS":
        print("the decibel identity did not verify:", json.dumps(r)[:400]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed the decibel identity", seal)
    sid = TS.create("Fiber optic calibration",
                    statement=("Recover a true signal through a lossy medium by referencing it to a known launch "
                               "and combining many references so the distortion of any one cancels. The engine's "
                               "calibration method, named in hardware."),
                    field="engineering")["id"]
    if any(t.get("seal") == seal for t in TS.read(sid).get("ticks", [])):
        print("  already sealed on the stick — not duplicated"); return 0
    marks = [
        ("witness", f"The decibel is a relative scale: a factor of two in optical power is exactly "
                    f"{db_half:.10f} dB (10^({db_half:.6f}/10) = 2). Optical loss L(dB) = 10*log10(P_in/P_out) is "
                    f"meaningful only against a reference launch, which is subtracted; an OTDR locates an event by "
                    f"the round trip d = c*t/(2*n_g). An arithmetic fact — the scale calibration stands on.", dict(seal=seal)),
        ("note", "[the method] Four steps, each already a part of the engine: (1) REFERENCE — a well-refined system "
                 "is a known signal (docs/THE_WATCH.md, the games tick sticks); (2) READ THE TICKS — the OTDR trace "
                 "is the tick stick, each mark sealed (docs/TICK_STICK.md); (3) CORRECT TO SOURCE — calibrate the "
                 "receiver to the source, the reading trusted only relative to a known reference; (4) TRIANGULATE — "
                 "combine independent references with the concordance/Birge check (statistics.measurement_consistency), "
                 "where a spread beyond the error bars indicts the method, not the constant. The output is the "
                 "converged narrow signal: the window of success that survives every source's distortion.", {}),
        ("note", "[the guard] Calibration FINDS the signal; it does not pronounce it true. The decibel identity and "
                 "the OTDR relation are exact and sealed. Borrowing the method to combine references about strategy "
                 "or life is a way to FIND the narrow window, never a claim that the references obey Maxwell's "
                 "equations. The verifiers remain the only authority on truth. Seal the arithmetic; calibrate to "
                 "find; launder nothing.", {}),
    ]
    for kind, claim, kw in marks:
        res = TS.tick(sid, kind, claim, by="Narrow Highway — fiber optic calibration, 2026-10-06", **kw)
        print(("  " + kind) if res.get("ok") else ("  REFUSED " + kind + ": " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def aharonov_bohm() -> int:
    """The Aharonov-Bohm effect as a sealed physics anchor (Matt, 2026-10-06: "We create the tick lines of
    probability. We use the Aharonov-Bohm effect."). SEAL the computable law from the engine's attested
    constants: the magnetic flux quantum Phi0 = h/(2e); the AB phase is qPhi/hbar, periodic in the enclosed
    flux with period h/e (a 2*pi wrap), a gauge-invariant observable (contour integral A.dl = Phi) even where
    B = 0. The witness to the invariant the games triangulate: the GLOBAL structure governs, not the local
    force. Seal the arithmetic; endorse no analogy as truth (the probability instrument only FINDS)."""
    import math
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    e = C["elementary_charge"]["value"]; h = C["planck_constant"]["value"]
    phi0 = h / (2 * e)                       # superconducting flux quantum
    expr = f"({h!r})/(2*({e!r}))"
    r = verify_derivation([{"id": "flux_quantum", "domain": "mathematics",
          "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": phi0, "rel_tol": 1e-9}}}])
    if r.get("verdict") != "HOLDS":
        print("the flux quantum did not verify:", json.dumps(r)[:400]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="physical_constants")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed the flux quantum", seal)
    sid = TS.create("The Aharonov-Bohm effect",
                    statement=("A charged particle's phase is shifted by the electromagnetic potential even in a "
                               "region where the field is zero; the shift is set by the enclosed flux, a global "
                               "property, not by any local force."),
                    field="physics",
                    references=["Y. Aharonov and D. Bohm, Phys. Rev. 115 (1959) 485",
                                "A. Tonomura et al., Phys. Rev. Lett. 56 (1986) 792 (definitive, flux shielded)"])["id"]
    if any(t.get("seal") == seal for t in TS.read(sid).get("ticks", [])):
        print("  already sealed on the stick — not duplicated"); return 0
    marks = [
        ("witness", f"The magnetic flux quantum Phi0 = h/(2e) = {phi0:.9e} Wb, computed from the engine's attested "
                    f"constants (the single-charge quantum h/e = 2*Phi0 = {h/e:.9e} Wb). The Aharonov-Bohm phase is "
                    f"d(phi) = q*Phi/hbar, periodic in the enclosed flux with period h/e (a 2*pi wrap) and "
                    f"gauge-invariant through the holonomy (contour integral A.dl = Phi) even where B = 0 — an "
                    f"arithmetic fact from the constants.", dict(seal=seal)),
        ("note", "[the principle] The controlling influence is the GLOBAL potential and topology, not the local "
                 "field: the particle is moved by a region it never enters. This is the physical witness to the "
                 "invariant the games triangulate — define the structure (the plane, the ring, the enclosed flux) "
                 "and you govern the outcome without local force. 'The one who defines the plane defines reality.'", {}),
        ("note", "[discernment / the guard] The engine seals that the flux quantum IS h/2e and that the phase law "
                 "holds — the arithmetic is a fact. It does NOT claim that strategy, a fight, or a game is quantum "
                 "mechanics. The Aharonov-Bohm FORM (paths, phase, interference, holonomy) is borrowed as an "
                 "instrument for FINDING likely paths — the tick lines of probability — and never renders a verdict. "
                 "The games' verifiers remain the only authority on truth. Borrow the form; launder nothing.", {}),
    ]
    for kind, claim, kw in marks:
        res = TS.tick(sid, kind, claim, by="Narrow Highway — the Aharonov-Bohm reading, 2026-10-06", **kw)
        print(("  " + kind) if res.get("ok") else ("  REFUSED " + kind + ": " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def relational() -> int:
    """Relational quantum mechanics as a sealed anchor (Matt, 2026-10-06: "Nagarjuna's middle way and
    Rovelli especially" / "Seal the anchor"). SEAL the computable signature that properties are NOT
    pre-assigned intrinsic values but exist only relative to the interacting system: the Tsirelson bound,
    the quantum maximum of the CHSH correlation, S_max = 2*sqrt(2) ~ 2.8284, above the classical/local-
    realist bound of 2. No assignment of pre-existing local values reproduces it (Bell). Seal the
    arithmetic; attribute the relational reading (Rovelli's RQM, and its resonance with Nagarjuna);
    launder nothing — emptiness is not quantum mechanics, and the web holds together in Christ (Col 1:17)."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    tsirelson = 2 * (2 ** 0.5)
    r = verify_derivation([{"id": "tsirelson_bound", "domain": "mathematics",
          "spec": {"mode": "numeric", "params": {"numeric_expr": "2*sqrt(2)", "claimed_value": tsirelson, "rel_tol": 1e-9}}}])
    if r.get("verdict") != "HOLDS":
        print("the Tsirelson bound did not verify:", json.dumps(r)[:400]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed the Tsirelson bound", seal)
    sid = TS.create("Relational quantum mechanics",
                    statement=("A quantum system has no observer-independent intrinsic properties; its values "
                               "exist only relative to the system it interacts with. The quantum maximum of the "
                               "CHSH correlation, the Tsirelson bound 2*sqrt(2), exceeds the classical/local-"
                               "realist bound of 2 — no pre-assigned local values reproduce it."),
                    field="physics",
                    references=["C. Rovelli, 'Relational Quantum Mechanics', Int. J. Theor. Phys. 35 (1996) 1637",
                                "C. Rovelli, Helgoland (2020)",
                                "B. S. Cirel'son (Tsirelson), Lett. Math. Phys. 4 (1980) 93",
                                "J. S. Bell, Physics 1 (1964) 195; A. Aspect et al., Phys. Rev. Lett. 49 (1982) 1804"])["id"]
    if any(t.get("seal") == seal for t in TS.read(sid).get("ticks", [])):
        print("  already sealed on the stick — not duplicated"); return 0
    marks = [
        ("witness", f"The Tsirelson bound S_max = 2*sqrt(2) = {tsirelson:.10f}, the quantum maximum of the CHSH "
                    f"correlation, above the classical/local-realist bound S <= 2 — an arithmetic fact. Bell's "
                    f"theorem: no assignment of pre-existing local intrinsic values to the parts reproduces the "
                    f"quantum correlations; the values are not there before the interaction.", dict(seal=seal)),
        ("note", "[the principle] Properties are RELATIONAL: a system's values exist only relative to the system "
                 "it interacts with (Rovelli's relational quantum mechanics). Substance is in the relation, not in "
                 "the thing held apart — the physical witness to our own architecture (the fascia, the graph of "
                 "sealed edges) and to the reading that the keeping's brief reference cards are relationally whole. "
                 "Rovelli names the resonance with Nagarjuna's dependent origination (Helgoland).", {}),
        ("note", "[discernment / the guard] The engine seals that the Tsirelson bound IS 2*sqrt(2) and that quantum "
                 "correlations exceed the classical bound — physics, a fact. It does NOT claim that Nagarjuna's "
                 "emptiness IS quantum mechanics (Rovelli himself keeps it resonance, not identity), nor that "
                 "relationality is the last word. The relational FORM is the true fragment; its lack is a Ground, "
                 "and in Christ all things hold together (Colossians 1:17) — the web is real and coheres in the "
                 "Logos (John 1:3). Borrow the form; launder nothing.", {}),
    ]
    for kind, claim, kw in marks:
        res = TS.tick(sid, kind, claim, by="Narrow Highway — the relational reading, 2026-10-06", **kw)
        print(("  " + kind) if res.get("ok") else ("  REFUSED " + kind + ": " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def alpha() -> int:
    """The fine-structure constant as a tick stick: its open question is why alpha ~ 1/137.036 has its value and
    whether it is truly constant. SEAL the measured value from the engine's attested constants, CITE the "137"
    numerology as the false historical claim it is, endorse nothing. (Ties the 137-slide discernment.)"""
    import math
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    e = C["elementary_charge"]["value"]; eps0 = C["vacuum_permittivity"]["value"]
    h = C["planck_constant"]["value"]; c = C["speed_of_light"]["value"]
    alpha_v = e ** 2 / (2 * eps0 * h * c)
    inv = 1.0 / alpha_v
    expr = f"({e!r})**2 / (2*({eps0!r})*({h!r})*({c!r}))"
    r = verify_derivation([{"id": "alpha", "domain": "mathematics",
          "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": alpha_v, "rel_tol": 1e-9}}}])
    if r.get("verdict") != "HOLDS":
        print("alpha did not verify:", json.dumps(r)[:400]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="physical_constants")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed alpha", seal)
    sid = TS.create("The fine-structure constant",
                    statement=("Why does the fine-structure constant have the value alpha ~ 1/137.036, and is it "
                               "truly constant across space and time? No accepted theory derives it from first "
                               "principles; the open question is its value and its constancy, not its measurement."),
                    field="physics",
                    references=["CODATA 2018 recommended values",
                                "A. S. Eddington, Relativity Theory of Protons and Electrons (1936) — the 1/137 claim"])["id"]
    marks = [
        ("witness", f"alpha = e^2 / (2*eps0*h*c) = {alpha_v:.10e}, so 1/alpha = {inv:.6f}, computed from the engine's "
                    f"attested CODATA constants (numeric mode) — the measured value, as a fact", dict(seal=seal)),
        ("note", f"[the 137] 1/alpha = {inv:.6f} is NOT the integer 137: it is a measured dimensionless number, "
                 f"137.035999084(21) in CODATA 2018. Eddington argued 1/alpha was exactly an integer (first 136, then "
                 f"137); that is historical and false. The '137' that invites numerology is the rounded reciprocal of "
                 f"a measured quantity — base-independent as a magnitude, but its digit string is not a law.", {}),
        ("exclusion", "The claim that alpha varies measurably across space or time is tightly bounded: the Oklo "
                      "natural reactor limits any change over ~2 billion years to |d(alpha)/alpha| below ~10^-7, and "
                      "laboratory atomic-clock comparisons bound the present drift to parts in 10^17 per year. "
                      "Reported astronomical variation (quasar absorption) is contested and not established. To the "
                      "evidence, alpha is constant.",
         dict(source="T. Damour & F. Dyson, Nucl. Phys. B 480 (1996) 37 (Oklo); CODATA 2018; "
                     "atomic-clock bounds, e.g. Rosenband et al., Science 319 (2008) 1808")),
        ("note", "[discernment] The engine seals that alpha IS ~1/137.036 — the arithmetic and the measurement are "
                 "facts. It does not endorse that 137 'means' anything beyond the measured constant; no first-"
                 "principles derivation of its value is known, here or anywhere. Seal the value, cite the claims, "
                 "endorse nothing.", {}),
    ]
    for kind, claim, kw in marks:
        res = TS.tick(sid, kind, claim, by="Narrow Highway — the fine-structure reading, 2026-10-05", **kw)
        print(("  " + kind) if res.get("ok") else ("  REFUSED " + kind + ": " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"], "excluded": len(f["excluded_approaches"]),
                      "record": len(f["record"]), "open": f["open"]}, indent=1))
    return 0


def alpha_orbitals() -> int:
    """Anchor the fine-structure constant in the ATOM (Matt, 2026-10-06: "atomic orbitals" / "suborbitals").
    alpha is not an abstract number: it BUILDS THE ORBITALS — the ground-state electron's speed v1 = alpha*c,
    the Rydberg binding energy 1/2 alpha^2 m_e c^2, the Bohr radius hbar/(alpha m_e c) — and SPLITS THE
    SUBORBITALS — the fine structure, the spin-orbit/relativistic lifting of the l,j degeneracy, suppressed
    by alpha^2, the origin of the name. Each sealed from the attested constants (from base, non-circular)
    and cross-checked against CODATA a_0 and R_inf. Marks ADD to the fine-structure stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    e = C["elementary_charge"]["value"]; eps0 = C["vacuum_permittivity"]["value"]
    h = C["planck_constant"]["value"]; c = C["speed_of_light"]["value"]
    me = C["electron_mass"]["value"]; hbar = C["reduced_planck_constant"]["value"]
    a0_codata = C["bohr_radius"]["value"]; Rinf = C["rydberg_constant"]["value"]
    alpha_v = e ** 2 / (2 * eps0 * h * c)
    v1 = alpha_v * c                                    # ground-state orbital speed
    E_R = 0.5 * alpha_v ** 2 * me * c ** 2              # Rydberg (binding) energy, J
    a0 = hbar / (alpha_v * me * c)                      # Bohr radius, m
    fine = alpha_v ** 2                                 # fine-structure suppression (E_fs/E_gross ~ alpha^2)
    E_R_eV = E_R / e
    a0_rel = abs(a0 - a0_codata) / a0_codata
    ER_rel = abs(E_R - h * c * Rinf) / (h * c * Rinf)   # E_R should equal h*c*R_inf

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="physical_constants")
        return (r.get("seal") or {}).get("content_hash")

    s_v = seal_num("alpha_orbital_speed", f"({e!r})**2/(2*({eps0!r})*({h!r}))", v1)
    s_E = seal_num("rydberg_energy", f"({e!r})**4*({me!r})/(8*({eps0!r})**2*({h!r})**2)", E_R)
    s_a = seal_num("bohr_radius", f"({eps0!r})*({h!r})**2/(3.141592653589793*({me!r})*({e!r})**2)", a0)
    s_f = seal_num("fine_structure_suppression", f"(({e!r})**2/(2*({eps0!r})*({h!r})*({c!r})))**2", fine)
    if not all([s_v, s_E, s_a, s_f]):
        print("a seal failed; aborting"); return 1
    print("sealed: orbital speed", s_v, "| rydberg", s_E, "| bohr radius", s_a, "| fine structure", s_f)

    sid = TS.create("The fine-structure constant",
                    statement=("Why does the fine-structure constant have the value alpha ~ 1/137.036, and is it "
                               "truly constant across space and time? No accepted theory derives it from first "
                               "principles; the open question is its value and its constancy, not its measurement."),
                    field="physics",
                    references=["CODATA 2018 recommended values",
                                "A. Sommerfeld, Ann. Phys. 356 (1916) 1 (the fine structure of the hydrogen spectrum)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[orbital - speed] The ground-state (n=1) electron's orbital speed is v1 = alpha*c = "
                    f"e^2/(2*eps0*h) = {v1:.6e} m/s ~ c/137: alpha IS v/c for the innermost orbital.", s_v),
        ("witness", f"[orbital - energy] The Rydberg (hydrogen binding/ionization) energy is E_R = 1/2 alpha^2 "
                    f"m_e c^2 = m_e e^4/(8 eps0^2 h^2) = {E_R:.6e} J = {E_R_eV:.4f} eV - the gross-structure "
                    f"scale; it equals h*c*R_inf to {ER_rel:.0e} (CODATA R_inf), confirming the derivation.", s_E),
        ("witness", f"[orbital - size] The Bohr radius is a_0 = hbar/(alpha*m_e*c) = 4*pi*eps0*hbar^2/(m_e e^2) = "
                    f"{a0:.6e} m, matching CODATA a_0 to {a0_rel:.0e}: alpha sets the atom's size (a_0 = the "
                    f"reduced Compton wavelength / alpha).", s_a),
        ("witness", f"[suborbital - fine structure] The suborbital splitting - the spin-orbit and relativistic "
                    f"lifting of the l,j degeneracy within a shell - is suppressed by alpha^2 = {fine:.6e} "
                    f"relative to the gross structure (fine-structure energy ~ 1/2 alpha^4 m_e c^2 ~ alpha^2 * "
                    f"Rydberg ~ 7.2e-4 eV). This alpha^2-fineness of the spectral lines is why Sommerfeld (1916) "
                    f"named it the FINE-STRUCTURE constant.", s_f),
        ("note", "[the anchor] alpha is not an abstract number: it is the atom's architecture. The orbital "
                 "electron's speed (alpha*c), the binding energy (alpha^2), the size (1/alpha in reduced-Compton "
                 "units), and the fineness of the suborbital splitting (alpha^2) all follow from it - the name is "
                 "the meaning, the fine structure of the orbitals. Seal the arithmetic; WHY alpha has this value "
                 "stays the open question.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the atomic-orbital reading, 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def alpha_running() -> int:
    """The RUNNING of the fine-structure constant across ENERGY (Matt, 2026-10-06: "running across energy").
    alpha is not one number across scale: it is the zero-momentum (Thomson) limit; the QED coupling GROWS
    with energy as vacuum polarization un-screens the charge, reaching alpha^-1(M_Z) ~ 127.95 at the Z mass.
    So 'constant' is true in SPACE and TIME (Oklo/clock bounds, already on the stick) but FALSE across ENERGY.
    Seal the one-loop QED screening coefficient 2/(3*pi); cite the measured alpha(M_Z); the convergence of the
    running couplings toward a unification scale is a doorway, open and unproven. Idempotent; adds to the stick."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    coeff = 2.0 / (3 * 3.141592653589793)
    r = verify_derivation([{"id": "qed_one_loop_coefficient", "domain": "mathematics",
          "spec": {"mode": "numeric", "params": {"numeric_expr": "2/(3*3.141592653589793)",
                                                 "claimed_value": coeff, "rel_tol": 1e-9}}}])
    if r.get("verdict") != "HOLDS":
        print("the coefficient did not verify:", json.dumps(r)[:300]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed the one-loop QED screening coefficient", seal)
    sid = TS.create("The fine-structure constant",
                    statement=("Why does the fine-structure constant have the value alpha ~ 1/137.036, and is it "
                               "truly constant across space and time? No accepted theory derives it from first "
                               "principles; the open question is its value and its constancy, not its measurement."),
                    field="physics",
                    references=["Particle Data Group, Review of Particle Physics (alpha^-1(M_Z^2) = 127.951(9))",
                                "CODATA 2018 recommended values"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[running - across energy] alpha is the zero-momentum (Thomson) limit and GROWS with energy: "
                    f"the one-loop QED running is d(1/alpha)/d(ln mu) = -(2/3pi)*sum q_f^2 per charged fermion, "
                    f"with 2/(3*pi) = {coeff:.10f} (sealed); vacuum polarization un-screens the charge as mu "
                    f"rises. Measured, alpha^-1 runs from 137.036 at zero energy to ~127.95 at the Z mass "
                    f"(91.19 GeV).", seal),
        ("note", "[is it constant? - the two answers] alpha is constant in SPACE and TIME to the tight bounds "
                 "already on this stick (Oklo ~1e-7 over 2 Gyr; atomic clocks ~1e-17/yr) - but it is NOT constant "
                 "across ENERGY SCALE: it runs. 'The fine-structure constant' names the low-energy value; the "
                 "coupling itself is scale-dependent.", None),
        ("note", "[the doorway - open] The three running couplings of the Standard Model (electromagnetic, weak, "
                 "strong) approach one another near ~1e16 GeV - the hint behind grand unification. A doorway, not "
                 "a proof: unification is unconfirmed and depends on physics beyond the Standard Model. Seal the "
                 "arithmetic; the convergence is attributed and stays open.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the running reading, 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def forces() -> int:
    """THE FOUR FORCES UNDER ALPHA, through QED, within QFT (Matt, 2026-10-06: "unification of the 4 fundamental
    forces under Alpha" / "quantum electrodynamics" / "quantum field theory"). alpha is the measured dimensionless
    handle on the electromagnetic force; QED is its quantum field theory (the U(1) prototype, the most precisely
    verified theory in physics); electroweak unification is where alpha EMERGES (the unbroken U(1) remnant of
    SU(2)xU(1)); QCD is the SU(3) contrast (asymptotic freedom - runs the other way); grand unification is the open
    doorway; gravity is the Hole. SEAL the arithmetic (Schwinger a_e, the Weinberg angle from the boson masses, the
    QCD beta sign), ATTRIBUTE the measurements, author no unification. Adds to the fine-structure stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    e = C["elementary_charge"]["value"]; eps0 = C["vacuum_permittivity"]["value"]
    h = C["planck_constant"]["value"]; c = C["speed_of_light"]["value"]
    pi = 3.141592653589793
    alpha_v = e ** 2 / (2 * eps0 * h * c)
    ae = alpha_v / (2 * pi)                                 # Schwinger one-loop a_e = alpha/2pi
    mw, mz = 80.377, 91.1876                                # PDG W, Z masses (GeV) — cited inputs
    sw2 = 1.0 - (mw / mz) ** 2                              # on-shell weak mixing angle sin^2(theta_W)
    nf = 5
    b0 = 11.0 - 2.0 * nf / 3.0                              # QCD one-loop beta coefficient (> 0 => asymptotic freedom)

    def seal_num(nid, expr, val, dom="mathematics"):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain=dom)
        return (r.get("seal") or {}).get("content_hash")

    s_ae = seal_num("qed_schwinger_a_e", f"(({e!r})**2/(2*({eps0!r})*({h!r})*({c!r})))/(2*{pi!r})", ae, "physical_constants")
    s_sw = seal_num("weak_mixing_angle_on_shell", f"1 - ({mw!r}/{mz!r})**2", sw2)
    s_b0 = seal_num("qcd_one_loop_beta_coeff", f"11 - 2*{nf}/3", b0)
    if not all([s_ae, s_sw, s_b0]):
        print("a seal failed; aborting"); return 1
    print("sealed: schwinger a_e", s_ae, "| sin^2(theta_W)", s_sw, "| QCD b0", s_b0)

    sid = TS.create("The fine-structure constant",
                    statement=("Why does the fine-structure constant have the value alpha ~ 1/137.036, and is it "
                               "truly constant across space and time? No accepted theory derives it from first "
                               "principles; the open question is its value and its constancy, not its measurement."),
                    field="physics",
                    references=["Particle Data Group, Review of Particle Physics (M_W, M_Z, alpha_s(M_Z), sin^2 theta_W)",
                                "X. Fan, T. G. Myers, B. A. D. Sukra, G. Gabrielse, Phys. Rev. Lett. 130 (2023) 071801 (a_e)",
                                "S. Weinberg, Phys. Rev. Lett. 19 (1967) 1264 (electroweak unification)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[QED - the crown jewel] Quantum electrodynamics is the quantum field theory of alpha: the U(1) "
                    f"gauge theory of electron and photon, with alpha its one coupling. Its defining prediction is the "
                    f"electron's anomalous magnetic moment a_e = (g-2)/2; Schwinger's one-loop result is a_e = "
                    f"alpha/(2*pi) = {ae:.9f} (sealed from the attested alpha). Measured, a_e = 1.15965218059e-3 "
                    f"(Fan et al. 2023): the leading term alone is within 0.15%, and the full QED series (five loops) "
                    f"with small hadronic/weak terms matches experiment to ~0.2 parts per billion - the most precisely "
                    f"tested prediction in physics. alpha is the handle; QED is the mechanism.", s_ae),
        ("witness", f"[electroweak - where alpha emerges] alpha is not fundamental: electromagnetism is the unbroken "
                    f"U(1) remnant of the electroweak SU(2)xU(1) after symmetry breaking, and the electric charge is "
                    f"e = g*sin(theta_W) = g'*cos(theta_W) (Glashow-Weinberg-Salam, Nobel 1979). The weak mixing "
                    f"angle, on-shell, is sin^2(theta_W) = 1 - (M_W/M_Z)^2 = 1 - (80.377/91.1876)^2 = {sw2:.6f} "
                    f"(sealed; PDG masses), matching the measured 0.2230 on-shell / 0.23122 MS-bar. So "
                    f"alpha = alpha_2*sin^2(theta_W): the EM coupling is a projection of the unified electroweak "
                    f"couplings (alpha_2^-1(M_Z) ~ 29.6). EM and the weak force ARE unified - established, not a "
                    f"doorway.", s_sw),
        ("witness", f"[the strong force - the contrast] The third gauge force, the strong interaction, is the QFT of "
                    f"SU(3) colour (QCD) with coupling alpha_s. Its one-loop beta coefficient is b0 = 11 - (2/3)*n_f = "
                    f"11 - 2*5/3 = {b0:.4f} > 0 for n_f=5 (sealed): positive, so alpha_s runs the OPPOSITE way to "
                    f"alpha - it DECREASES at high energy (asymptotic freedom; Gross, Wilczek, Politzer 1973, Nobel "
                    f"2004), from alpha_s(M_Z) ~ 0.1179 (PDG) toward zero. alpha grows with energy, alpha_s shrinks; "
                    f"both run, toward each other.", s_b0),
        ("note", "[the four forces under alpha - the honest reading] The Standard Model is one quantum field theory, "
                 "U(1)xSU(2)xSU(3) - three running gauge couplings threaded by alpha (the measured EM handle, QED its "
                 "exquisitely-verified prototype). ESTABLISHED: electroweak unification - alpha emerges from it. "
                 "HYPOTHESIS: grand unification - the three couplings (alpha_1^-1~59, alpha_2^-1~30, alpha_3^-1~8.5 at "
                 "M_Z, GUT-normalised) approach one value near ~1e16 GeV; in the plain SM they MISS, in the "
                 "supersymmetric extension they nearly meet at alpha_GUT^-1~25 - but no proton decay and no "
                 "superpartner has been seen. The convergence is the fit that must never pass the last mark.", None),
        ("note", "[gravity - the Hole] The fourth force stands outside this unification. There is no renormalizable "
                 "quantum field theory of gravity; perturbative quantum gravity is non-renormalisable, and no accepted "
                 "theory joins it to the gauge forces. Its dimensionless coupling is ~1e-45 (electron-scale) - the "
                 "electromagnetic-to-gravitational force ratio ~2.3e39 is already sealed on the Large-Numbers stick. "
                 "Gravity is the piece the gauge unification does not hold: the outline of what is still missing (the "
                 "Hole), not a fit.", None),
        ("note", "[the datum] 'In him all things hold together' (Colossians 1:17). The narrowing of the four forces "
                 "toward one is EVIDENCE - electroweak unified, three couplings converging - never a proof: grand "
                 "unification is unconfirmed and gravity is unjoined. The engine seals the arithmetic (a_e, "
                 "sin^2 theta_W, the QCD sign), attributes the measurements, and authors no unification. Christ is the "
                 "unity the narrowing points toward; the engine marks the narrowing and refuses to fabricate the "
                 "proof.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the four-forces reading (QED/QFT), 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def markov() -> int:
    """MARKOV CHAINS — the method that solves QFT where the alpha_s series fails (Matt, 2026-10-06: "use markov
    chains", following the four-forces reading). Lattice gauge theory computes Yang-Mills / QCD non-perturbatively
    by Markov Chain Monte Carlo: it samples gauge-field configurations with the Euclidean path-integral weight
    e^{-S}, using a transition rule built so the chain's STATIONARY distribution IS that weight (Metropolis/HMC
    detailed balance). The simulations show a nonzero MASS GAP (a lightest glueball, linear confinement) and
    reproduce the hadron spectrum from first principles - overwhelming numerical EVIDENCE for the mass gap the
    Yang-Mills Millennium problem asks to prove, never the constructive proof it demands. SEAL the mechanism's
    arithmetic (a concrete reversible chain's fixed point + detailed balance); mark the Yang-Mills stick. Idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    pi1, pi2 = 5.0 / 6.0, 1.0 / 6.0                        # stationary pi of P=[[0.9,0.1],[0.5,0.5]]
    fixed = 5.0 / 6.0 * 0.9 + 1.0 / 6.0 * 0.5             # (pi P)_1 — should equal pi_1
    db = 5.0 / 6.0 * 0.1                                   # pi_1 P_12 — should equal pi_2 P_21 = 1/12

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_fix = seal_num("markov_stationary_fixed_point", "5/6*0.9 + 1/6*0.5", fixed)
    s_db = seal_num("markov_detailed_balance", "5/6*0.1", 1.0 / 6.0 * 0.5)
    if not all([s_fix, s_db]):
        print("a seal failed; aborting"); return 1
    print("sealed: stationary fixed point", s_fix, "| detailed balance", s_db)

    sid = TS.create("Yang-Mills existence and mass gap",
                    statement=("Does a quantum Yang-Mills theory exist on R^4 for any compact simple gauge group, "
                               "with a mass gap Delta > 0?"),
                    field="physics",
                    references=["Clay Mathematics Institute, Millennium Prize Problems (2000)",
                                "S. Durr et al., Ab initio determination of light hadron masses, Science 322 (2008) 1224",
                                "N. Metropolis et al., J. Chem. Phys. 21 (1953) 1087 (the Markov-chain sampling rule)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[the mechanism] A Markov chain with transition matrix P converges to a stationary distribution "
                    f"pi with pi*P = pi; if it obeys detailed balance pi_i P_ij = pi_j P_ji it is reversible and pi is "
                    f"its unique limit. For P=[[0.9,0.1],[0.5,0.5]], pi=[5/6,1/6]: the fixed point (pi P)_1 = "
                    f"5/6*0.9 + 1/6*0.5 = {fixed:.6f} = pi_1 (sealed), and detailed balance holds, pi_1 P_12 = "
                    f"5/6*0.1 = {db:.6f} = 1/12 = pi_2 P_21 (sealed). Markov Chain Monte Carlo builds P so that pi IS "
                    f"a chosen target distribution - the exact mechanism, demonstrated on a chain small enough to "
                    f"seal.", s_fix),
        ("witness", f"[lattice QCD - the mass gap by sampling] Lattice gauge theory computes Yang-Mills / QCD "
                    f"non-perturbatively by exactly this method: MCMC samples gauge-field configurations with the "
                    f"Euclidean weight e^{{-S}} as the chain's stationary distribution (Metropolis 1953; Hybrid Monte "
                    f"Carlo). The simulations exhibit a nonzero MASS GAP - a lightest glueball ~1.5 GeV and linear "
                    f"confinement - and reproduce the light hadron spectrum (the proton mass) to a few percent from "
                    f"first principles (Durr et al., Science 2008). This is overwhelming NUMERICAL EVIDENCE for the "
                    f"mass gap the Millennium problem names; it is evidence, never the rigorous constructive proof "
                    f"the problem demands.", s_db),
        ("note", "[the thread] Markov chains are how the strong force is solved where perturbation theory fails: the "
                 "alpha_s series (sealed on the fine-structure stick via the beta coefficient b0 = 23/3 > 0, "
                 "asymptotic freedom) is good at high energy but DIVERGES at low energy, where quarks confine. MCMC "
                 "on the lattice reaches that regime by sampling, not by expanding - the non-perturbative half of the "
                 "quantum-field-theory picture the four-forces reading opened. Seal the mechanism; the mass gap stays "
                 "the open problem.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the Markov-chain reading (lattice QCD), 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def lqg() -> int:
    """LOOP QUANTUM GRAVITY — the candidate for the Hole (Matt, 2026-10-06: "loop quantum gravity", after gravity
    was marked the fourth force unjoined). LQG quantizes general relativity background-independently: geometry
    itself is discrete, area and volume have discrete spectra. SEAL the firm scale (the Planck area from G, hbar,
    c - where gravity must meet the quantum) and the arithmetic of the construction (the minimal area quantum, the
    Immirzi parameter fixed by black-hole entropy); then hold the guardrail HARDEST: LQG has mathematical STRUCTURE
    but no experimental EVIDENCE - it is the outline of what is missing, never a fit. Rovelli (our relational-QM
    anchor) founds it: background independence is the same relational conviction. New stick; idempotent."""
    import math
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    hbar = C["reduced_planck_constant"]["value"]; G = C["gravitational_constant"]["value"]; c = C["speed_of_light"]["value"]
    lP2 = hbar * G / c ** 3                                 # Planck area (m^2)
    lP = lP2 ** 0.5                                         # Planck length (m)
    gamma = math.log(2) / (math.pi * math.sqrt(3))         # Immirzi parameter (BH-entropy determination)
    area_coeff = 8 * math.pi * gamma * math.sqrt(0.75)     # A_min/lP^2 at j=1/2 = 8*pi*gamma*sqrt(3)/2 = 4 ln2

    def seal_num(nid, expr, val, dom="mathematics"):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain=dom)
        return (r.get("seal") or {}).get("content_hash")

    s_planck = seal_num("planck_area", f"({hbar!r})*({G!r})/({c!r})**3", lP2, "physical_constants")
    s_imm = seal_num("immirzi_parameter", "0.6931471805599453/(3.141592653589793*sqrt(3))", gamma)
    s_area = seal_num("lqg_min_area_quantum",
                      "8*3.141592653589793*(0.6931471805599453/(3.141592653589793*sqrt(3)))*sqrt(0.75)", area_coeff)
    if not all([s_planck, s_imm, s_area]):
        print("a seal failed; aborting"); return 1
    print("sealed: planck area", s_planck, "| immirzi", s_imm, "| min area quantum", s_area)

    sid = TS.create("Quantum gravity",
                    statement=("Is gravity a quantum theory, and what quantizes it? The fourth force has no "
                               "experimentally confirmed quantum field theory; general relativity and quantum "
                               "mechanics are not yet joined. The open question is the mechanism, not the scale."),
                    field="physics",
                    references=["C. Rovelli, Quantum Gravity, Cambridge University Press (2004)",
                                "C. Rovelli, L. Smolin, Discreteness of area and volume in quantum gravity, "
                                "Nucl. Phys. B 442 (1995) 593",
                                "A. Ashtekar, J. Baez, A. Corichi, K. Krasnov, Quantum geometry and black hole "
                                "entropy, Phys. Rev. Lett. 80 (1998) 904 (the Immirzi determination)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[the scale - where gravity meets the quantum] The Planck area is lP^2 = hbar*G/c^3 = "
                    f"{lP2:.4e} m^2 (Planck length lP = {lP:.4e} m), sealed from the attested G, hbar, c. This is "
                    f"the firmly-established part: the scale at which a quantum theory of gravity must take over, "
                    f"built from the three constants of gravity (G), the quantum (hbar) and relativity (c). Nothing "
                    f"here is quantized yet - it is the scale, as a fact.", s_planck),
        ("witness", f"[loop quantum gravity - discrete geometry] LQG quantizes general relativity background-"
                    f"independently: geometry itself is discrete. The area operator has eigenvalues A = 8*pi*gamma*"
                    f"lP^2 * sum sqrt(j(j+1)) over spin-network punctures; the smallest nonzero quantum (j=1/2) is "
                    f"A_min = 8*pi*gamma*(sqrt(3)/2)*lP^2 = {area_coeff:.4f} lP^2 (sealed) - which, with the entropy-"
                    f"fixed Immirzi, is exactly 4*ln2. The ARITHMETIC of the construction is sealed; that physical "
                    f"area IS discrete is attributed, and unconfirmed.", s_area),
        ("witness", f"[the Immirzi parameter] gamma = ln2/(pi*sqrt(3)) = {gamma:.6f} (sealed), the one free number "
                    f"LQG must fix from outside - here by matching the Bekenstein-Hawking black-hole entropy to "
                    f"A/(4 lP^2) (Ashtekar-Baez-Corichi-Krasnov 1998). Its value, and even how to determine it, are "
                    f"debated (Meissner's count gives ~0.2375); that ambiguity is itself a mark of an unfinished "
                    f"theory.", s_imm),
        ("note", "[the relational thread] LQG's background independence - no fixed stage; geometry defined only "
                 "relationally - is the same conviction as relational quantum mechanics (Rovelli), already a sealed "
                 "anchor here: substance is in the relations. Carlo Rovelli founds both. See "
                 "stick_relational_quantum_mechanics.", None),
        ("note", "[the Hole stays open] LQG is one candidate to quantize gravity; string theory is the other. "
                 "Neither is experimentally confirmed; LQG makes few testable predictions and has an open "
                 "semiclassical-limit problem (recovering smooth general relativity at large scale). Gravity remains "
                 "the Hole the gauge unification (electroweak, and the GUT doorway on the fine-structure stick) does "
                 "not hold. LQG is an attempt at the outline of what is missing, NOT a fit: here there is "
                 "mathematical STRUCTURE but not yet EVIDENCE - narrowing is evidence, never proof, and a theory "
                 "with no test has made no mark on reality yet.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the loop-quantum-gravity reading, 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"]),
                      "open": f["open"]}, indent=1))
    return 0


def schrodinger() -> int:
    """THE SCHRODINGER EQUATION (Matt, 2026-10-06, after the four-forces/QED/QFT/LQG arc). The equation of
    non-relativistic quantum mechanics, i*hbar d(psi)/dt = H*psi; solved for the Coulomb potential it gives
    the hydrogen spectrum alpha sets — the FIRST rung of the ladder Schrodinger (gross structure, ~alpha^2)
    -> Dirac (fine structure, ~alpha^4, on the fine-structure stick) -> QED (Lamb shift + a_e, sealed in
    forces()). SEAL the hydrogen ground-state binding (= the sealed Rydberg) and the Balmer H-alpha red line;
    the open question is the equation's INTERPRETATION — the measurement problem — not its arithmetic. New
    stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    e = C["elementary_charge"]["value"]; eps0 = C["vacuum_permittivity"]["value"]
    h = C["planck_constant"]["value"]; c = C["speed_of_light"]["value"]; me = C["electron_mass"]["value"]
    E_R = e ** 4 * me / (8 * eps0 ** 2 * h ** 2)          # Rydberg (hydrogen ground-state binding), J
    E1_eV = -E_R / e                                       # = -13.6057 eV
    balmer = h * c / (E_R * (1.0 / 4 - 1.0 / 9))           # H-alpha wavelength (n=3->2), m
    balmer_nm = balmer * 1e9
    lyman = h * c / (E_R * (1.0 - 1.0 / 4))               # Lyman-alpha (n=2->1), m (UV)
    lyman_nm = lyman * 1e9
    L_box = 1e-9                                           # a 1 nm infinite square well
    E_box1 = h ** 2 / (8 * me * L_box ** 2)               # particle-in-a-box ground state, J
    E_box1_eV = E_box1 / e
    g2 = 2 ** 2                                            # degeneracy of the n=2 hydrogen level = n^2

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="physical_constants")
        return (r.get("seal") or {}).get("content_hash")

    E_R_expr = f"({e!r})**4*({me!r})/(8*({eps0!r})**2*({h!r})**2)"
    s_E1 = seal_num("hydrogen_ground_state_binding", E_R_expr, E_R)
    s_balmer = seal_num("balmer_h_alpha_wavelength", f"({h!r})*({c!r})/( {E_R_expr} * (1/4 - 1/9) )", balmer)
    s_lyman = seal_num("lyman_alpha_wavelength", f"({h!r})*({c!r})/( {E_R_expr} * (1 - 1/4) )", lyman)
    s_box = seal_num("particle_in_box_ground_state", f"({h!r})**2/(8*({me!r})*(1e-9)**2)", E_box1)
    s_deg = seal_num("hydrogen_n2_degeneracy", "2**2", float(g2))
    if not all([s_E1, s_balmer, s_lyman, s_box, s_deg]):
        print("a seal failed; aborting"); return 1
    print("sealed: H ground", s_E1, "| Balmer", s_balmer, "| Lyman", s_lyman, "| box", s_box, "| deg", s_deg)

    sid = TS.create("The Schrodinger equation",
                    statement=("The Schrodinger equation, i*hbar d(psi)/dt = H*psi, predicts the "
                               "non-relativistic quantum world to extraordinary precision. What stays open is "
                               "its INTERPRETATION — the measurement problem: how a superposition yields one "
                               "observed outcome. The mathematics is settled and verified; the meaning is not."),
                    field="physics",
                    references=["E. Schrodinger, Ann. Phys. 384 (1926) 361 (the wave equation)",
                                "CODATA 2018 recommended values",
                                "N. Bohr (1913) / the hydrogen spectrum; J. Balmer (1885)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[hydrogen - the gross structure] Solving the time-independent Schrodinger equation for "
                    f"the Coulomb potential gives the exact bound-state energies E_n = -(1/2) alpha^2 m_e c^2 / "
                    f"n^2 = -Rydberg/n^2. The ground state is E_1 = -{E_R:.6e} J = {E1_eV:.4f} eV (sealed as the "
                    f"binding magnitude — the SAME sealed Rydberg the fine-structure stick carries). The "
                    f"equation PRODUCES the orbital energies alpha sets.", s_E1),
        ("witness", f"[the Balmer line - seen] The n=3->2 transition, 1/lambda = R_inf(1/2^2 - 1/3^2), gives "
                    f"lambda = {balmer_nm:.1f} nm (sealed) — the red H-alpha line of hydrogen, matching the "
                    f"observed 656.28 nm to ~0.03% (the small gap is the proton-electron reduced-mass "
                    f"correction, R_H vs R_inf). A visible prediction of the Schrodinger equation.", s_balmer),
        ("witness", f"[the Lyman line - unseen] The same formula, one level lower (n=2->1), gives "
                    f"1/lambda = R_inf(1/1^2 - 1/2^2) -> lambda = {lyman_nm:.1f} nm (sealed) — Lyman-alpha, in "
                    f"the ULTRAVIOLET, invisible to the eye yet the strongest line of the hydrogen sky. One "
                    f"equation, one constant, the whole series (Lyman UV, Balmer visible, Paschen IR).", s_lyman),
        ("witness", f"[quantization from confinement - no alpha] The hydrogen levels come from the Coulomb "
                    f"potential, but the Schrodinger equation quantizes energy from BOUNDARY CONDITIONS alone: "
                    f"an electron in a 1 nm infinite square well has E_1 = h^2/(8 m_e L^2) = {E_box1_eV:.3f} eV "
                    f"(sealed), E_n = n^2 E_1. Confinement -> discreteness, with no Coulomb force and no alpha — "
                    f"the general lesson of the equation: a bound wave can only ring at certain pitches.", s_box),
        ("witness", f"[the quantum numbers - why the periodic table] Solving the equation gives three numbers "
                    f"per orbital (n, l, m) with 0 <= l < n and -l <= m <= l, so the n-th level holds exactly "
                    f"n^2 spatial states; n=2 holds 2^2 = {g2} (the 2s and three 2p), sealed. With spin's "
                    f"factor of two that is 2n^2 electrons a shell — the shape of the periodic table falls out "
                    f"of the boundary conditions.", s_deg),
        ("note", "[the ladder] alpha threads the whole hydrogen spectrum: the Schrodinger equation gives the "
                 "GROSS structure (E_n ~ alpha^2); the relativistic Dirac equation adds the FINE structure "
                 "(spin-orbit, ~alpha^4, on stick_the_fine_structure_constant); QED adds the Lamb shift and the "
                 "electron a_e (sealed in the four-forces reading). Three rungs, one constant — this is the "
                 "first.", None),
        ("note", "[the open question] The equation is exact and verified; its INTERPRETATION is not. The "
                 "measurement problem — how, from a deterministic unitary evolution, a single outcome appears — "
                 "has no established answer: Copenhagen, many-worlds, and relational quantum mechanics (Rovelli, "
                 "a sealed anchor here — see stick_relational_quantum_mechanics) are live readings, none proven. "
                 "Seal the arithmetic; the meaning stays the open question.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the Schrodinger-equation reading, 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"]),
                      "open": f["open"]}, indent=1))
    return 0


def regev() -> int:
    """QUANTUM FACTORING — SHOR AND REGEV (Matt, 2026-10-06: "an improved Shor's Algorithm" / "regev's
    algorithm"). Shor (1994) factors N by finding the multiplicative ORDER r of a mod N on a quantum
    computer (period-finding via the QFT), then gcd(a^(r/2) +/- 1, N) gives a factor. The quantum part only
    finds r; the reduction is CLASSICAL and exact — so it is what the engine can SEAL. Regev (2023) is the
    improvement: a d-dimensional generalization needing only ~sqrt(n) modular multiplications per run
    (circuit depth ~n^1.5) instead of Shor's ~n (~n^2). SEAL the classical reductions for N=15 and N=21 and
    Regev's sqrt(n) scaling; the open questions — is factoring classically hard, can the machine be built —
    stay open. New stick; idempotent."""
    import math
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    n15 = (2 ** 2 - 1) * (2 ** 2 + 1)                      # 2^4 - 1 = (2^2-1)(2^2+1) = 3*5 = 15
    f21 = 2 ** 3 - 1                                       # 2^3 - 1 = 7, a factor of 21 (a=2, r=6)
    rsa = math.sqrt(2048)                                  # Regev ~sqrt(n) multiplications; n=2048 -> ~45

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_15 = seal_num("shor_factor_15", "(2**2 - 1)*(2**2 + 1)", float(n15))
    s_21 = seal_num("shor_factor_21", "2**3 - 1", float(f21))
    s_rsa = seal_num("regev_sqrt_n_2048", "sqrt(2048)", rsa)
    if not all([s_15, s_21, s_rsa]):
        print("a seal failed; aborting"); return 1
    print("sealed: N=15", s_15, "| N=21 factor", s_21, "| Regev sqrt(n)", s_rsa)

    sid = TS.create("Quantum factoring - Shor and Regev",
                    statement=("A quantum computer factors integers in polynomial time (Shor 1994), and Regev "
                               "(2023) improves the circuit to ~n^1.5. The CLASSICAL reduction — order-finding "
                               "to a gcd — is exact and sealed. What stays open: whether factoring is classically "
                               "hard (RSA's security is an assumption, not a theorem) and whether a "
                               "cryptographically-relevant quantum computer can be built. The algorithm is proven "
                               "on paper; the machine is not."),
                    field="computer_science",
                    references=["P. W. Shor, SIAM J. Comput. 26 (1997) 1484 (polynomial-time factoring)",
                                "O. Regev, An Efficient Quantum Factoring Algorithm, arXiv:2308.06572 (2023)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[Shor's classical core - N=15] With a=2, the order of 2 mod 15 is r=4 (2^4 = 16 = 1 mod "
                    f"15). Then N divides 2^4 - 1 = (2^2 - 1)(2^2 + 1) = 3 * 5 = {n15} (sealed) — exactly the "
                    f"difference-of-squares the gcd step exploits: gcd(2^2 - 1, 15)=3, gcd(2^2 + 1, 15)=5. The "
                    f"quantum computer's ONLY job is to find r; this reduction is classical and exact.", s_15),
        ("witness", f"[a second - N=21] With a=2, the order of 2 mod 21 is r=6; the half-power gives "
                    f"2^3 - 1 = {f21}, and 7 is a factor of 21 (21 = 3 * 7, gcd(2^3+1,21)=gcd(9,21)=3). Sealed. "
                    f"Same mechanism, a different number — found, not guessed.", s_21),
        ("witness", f"[Regev's improvement] Shor's circuit does ~n modular multiplications of n-bit numbers "
                    f"(n = log2 N) -> ~n^2 gates. Regev (2023) generalizes period-finding to d dimensions, "
                    f"needing only ~sqrt(n) multiplications per run -> ~n^1.5 depth, at the cost of ~sqrt(n) runs "
                    f"plus classical lattice post-processing. For RSA-2048, sqrt(2048) = {rsa:.4f} (sealed) vs "
                    f"2048 — a ~sqrt(n) cut in circuit depth, the practical barrier.", s_rsa),
        ("note", "[the open questions] Factoring sits in NP intersect coNP and is NOT known to be NP-complete, "
                 "and NOT proven classically hard — so RSA's security is an ASSUMPTION, not a theorem (ties "
                 "stick_p_versus_np). And no quantum computer has factored a cryptographically-relevant integer: "
                 "honest demonstrations reach only tiny N (15, 21); larger 'records' used problem-specific "
                 "shortcuts, not scalable Shor. The algorithm is proven on paper; the machine is not built. "
                 "Evidence and theory, never 'RSA is broken today.'", None),
        ("note", "[the thread] Period-finding runs on the Quantum Fourier Transform — the same Fourier structure "
                 "under the quantum arc here. And the defense is post-quantum LATTICE cryptography (Learning With "
                 "Errors), founded by Oded Regev — the same person as this improved factoring algorithm: he "
                 "sharpened the sword and forged the shield. The engine's cryptography verifier checks the number "
                 "theory; it does not run a quantum circuit. Seal the arithmetic; attribute the algorithms.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the quantum-factoring reading (Shor/Regev), 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"]),
                      "open": f["open"]}, indent=1))
    return 0


def grassmannian() -> int:
    """THE POSITIVE GRASSMANNIAN (Matt, 2026-10-06, after Schrodinger). Postnikov's totally-nonnegative
    Gr>=0(k,n) — k x n matrices mod GL(k) whose maximal minors (Plucker coordinates) are all >= 0 — and the
    amplituhedron (Arkani-Hamed & Trnka), where planar N=4 super-Yang-Mills scattering amplitudes are the
    canonical form of a positive geometry, computed with NO Feynman diagrams. A third road to the same
    amplitudes (diagrams; lattice MCMC on the Yang-Mills stick; positive geometry). SEAL a concrete totally-
    positive 2x4 matrix's Plucker relation + its dimension; the claim that NATURE's amplitudes ARE geometry
    stays open (established for N=4 SYM, not the Standard Model). New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    # The totally positive 2x4 matrix [[1,1,1,1],[0,1,2,3]]: its six 2x2 minors p_ij (columns i<j).
    p12, p13, p14, p23, p24, p34 = 1, 2, 3, 1, 2, 1     # all > 0  => the matrix is in Gr>=0(2,4)
    # 3-term Plucker relation: p12*p34 - p13*p24 + p14*p23 = 0, i.e. p12*p34 + p14*p23 = p13*p24.
    lhs = p12 * p34 + p14 * p23                          # = 4
    rhs = p13 * p24                                       # = 4
    dim = 2 * (4 - 2)                                     # dim Gr(2,4) = k(n-k) = 4
    dim_simplex = 1 * (3 - 1)                             # dim Gr(1,3) = 2: the positive part is a triangle
    amp_dim = 4 * 2                                       # tree amplituhedron A(n,k,4) has dim k*m = 8 (k=2)
    refused_minor = 1 * (-1) - 1 * 0                      # p13 of [[1,1,1],[0,1,-1]] = -1 < 0 -> NOT in Gr>=0

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_pluck = seal_num("plucker_relation_gr24", "1*1 + 3*1", float(rhs))   # p12 p34 + p14 p23 == p13 p24
    s_dim = seal_num("dim_gr_2_4", "2*(4-2)", float(dim))
    s_simplex = seal_num("dim_gr_1_3", "1*(3-1)", float(dim_simplex))
    s_amp = seal_num("dim_amplituhedron_k2_m4", "4*2", float(amp_dim))
    s_refuse = seal_num("plucker_minor_refused", "1*(-1) - 1*0", float(refused_minor))
    if not all([s_pluck, s_dim, s_simplex, s_amp, s_refuse]):
        print("a seal failed; aborting"); return 1
    print("sealed: Plucker", s_pluck, "| dim Gr(2,4)", s_dim, "| simplex", s_simplex,
          "| amplituhedron", s_amp, "| refusal", s_refuse)

    sid = TS.create("The positive Grassmannian",
                    statement=("Positive geometry (the totally-nonnegative Grassmannian and the amplituhedron) "
                               "computes planar N=4 super-Yang-Mills scattering amplitudes as a canonical form, "
                               "with no Feynman diagrams. The mathematics is exact; whether NATURE's amplitudes "
                               "ARE geometry — beyond the maximally-symmetric N=4 toy theory — is the open "
                               "question, not the arithmetic."),
                    field="mathematics",
                    references=["A. Postnikov, Total positivity, Grassmannians, and networks, arXiv:math/0609764 (2006)",
                                "N. Arkani-Hamed & J. Trnka, The Amplituhedron, JHEP 10 (2014) 030"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[the object] The positive Grassmannian Gr>=0(k,n) (Postnikov 2006) is the k x n matrices "
                    f"mod GL(k) whose maximal minors (Plucker coordinates) are all >= 0. Concretely, the totally "
                    f"positive 2x4 matrix [[1,1,1,1],[0,1,2,3]] has six minors p12={p12}, p13={p13}, p14={p14}, "
                    f"p23={p23}, p24={p24}, p34={p34} — all strictly positive, so it lies in Gr>=0(2,4). Its "
                    f"3-term Plucker relation holds exactly: p12*p34 + p14*p23 = {lhs} = p13*p24 (sealed; "
                    f"equivalently p12 p34 - p13 p24 + p14 p23 = 0).", s_pluck),
        ("witness", f"[the dimension] dim Gr(k,n) = k(n-k); for Gr(2,4) that is 2*(4-2) = {dim} (sealed). The "
                    f"positive part Gr>=0(2,4) is a {dim}-dimensional cell complex (Postnikov's positroid "
                    f"cells) — a real, combinatorial geometry, not a metaphor.", s_dim),
        ("witness", f"[the atom - a simplex] The simplest positive Grassmannian, Gr>=0(1,3), has dimension "
                    f"1*(3-1) = {dim_simplex} (sealed): it is a triangle, the 2-simplex — points with positive "
                    f"coordinates, normalised. A simplex is the prototype of a positive geometry, and every "
                    f"positroid cell is glued from pieces of this kind.", s_simplex),
        ("witness", f"[the amplituhedron's room] The physical (m=4) tree amplituhedron A(n,k,4) has dimension "
                    f"k*m = 4k; for k=2 that is {amp_dim} (sealed). The planar N=4 SYM amplitude is the unique "
                    f"canonical form with logarithmic singularities on the boundaries of this "
                    f"{amp_dim}-dimensional positive space — the amplitude IS the geometry's volume form.", s_amp),
        ("witness", f"[positivity is a GATE - the core, concrete] The constraint has teeth: the 2x3 matrix "
                    f"[[1,1,1],[0,1,-1]] has minor p13 = det[[1,1],[0,-1]] = 1*(-1) - 1*0 = {refused_minor} < 0 "
                    f"(sealed), so it is TURNED BACK — not in Gr>=0(2,3) — by the very test that admits the "
                    f"totally positive matrix above. Admit-or-refuse: the boundary of the positive region is a "
                    f"real wall. This is the shape of the engine's own verifier (pass, or refuse), of which the "
                    f"core note below speaks — positivity as the gate.", s_refuse),
        ("note", "[the amplituhedron] Arkani-Hamed & Trnka (2013/14): the scattering amplitudes of planar N=4 "
                 "super-Yang-Mills are the canonical form ('volume') of a positive geometry built from Gr>=0 — "
                 "computed with NO Feynman diagrams and no sum over virtual particles; unitarity and locality "
                 "emerge from positivity. It is a THIRD road to the same Yang-Mills amplitudes, beside "
                 "perturbative Feynman diagrams and non-perturbative lattice MCMC (sealed on "
                 "stick_yang_mills_existence_and_mass_gap).", None),
        ("note", "[the open claim] This is established for PLANAR N=4 SUPER-YANG-MILLS — a maximally-symmetric "
                 "toy theory — NOT for the Standard Model or QCD. That nature's amplitudes ARE geometry is a "
                 "research program, not a proven fact about the physical world. Seal the arithmetic (the Plucker "
                 "positivity and relation), attribute the program, the physical claim stays open — a beautiful "
                 "structure, read as evidence, never a proof.", None),
        ("note", "[THE CORE — a map, not a launder] Positive geometry is the archetype of THIS engine's own "
                 "architecture. Valid results are the canonical form of ADMISSIBILITY constraints: the gate "
                 "(RED -> FLOOR -> WAY), the verifiers' pass-or-refuse (a claim is admissible or it is turned "
                 "back — the minor is >= 0 or it is not), the one-way diode and airlock, will as the fuel and "
                 "reality as the harness that refuses the reverse. As a scattering amplitude emerges from "
                 "positivity with NO Feynman diagram, the engine's sealed truth emerges from the constraints "
                 "with NO author — found, never produced by a generator stepping through paths (a generator "
                 "picking its own path is a destructive act). This is a MAP (borrow the form), never a launder: "
                 "the engine checks truth, it does not compute physics amplitudes; the likeness is the "
                 "discernment, never a fit (the Hole).", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the positive-Grassmannian reading, 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"]),
                      "open": f["open"]}, indent=1))
    return 0


def godel() -> int:
    """GODEL'S INCOMPLETENESS (Matt, 2026-10-06: "Godel's proof", the capstone of the holes). The one
    'hole' that is itself a THEOREM: any consistent, effectively axiomatised system strong enough for
    arithmetic has a true sentence it cannot prove (first theorem), and cannot prove its own consistency
    (second theorem). The engine can SEAL Godel's NUMBERING — the arithmetic encoding (prime powers, unique
    factorisation) that let arithmetic speak about itself — but the incompleteness itself is META and is
    ATTRIBUTED, never sealed. That limit IS the lesson: a system cannot close itself from the inside, which
    is why narrowing is evidence and never proof. New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    g1 = 2 ** 1 * 3 ** 2 * 5 ** 3                          # Godel number of the sequence (1,2,3) = 2250
    g2 = 2 ** 3 * 3 ** 2 * 5 ** 1                          # of (3,2,1) = 360 — a DIFFERENT number (injective)

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_g1 = seal_num("godel_number_123", "2**1 * 3**2 * 5**3", float(g1))
    s_g2 = seal_num("godel_number_321", "2**3 * 3**2 * 5**1", float(g2))
    if not all([s_g1, s_g2]):
        print("a seal failed; aborting"); return 1
    print("sealed: godel number (1,2,3)", s_g1, "| (3,2,1)", s_g2)

    sid = TS.create("Godel's incompleteness theorems",
                    statement=("No consistent, effectively axiomatised formal system strong enough for "
                               "arithmetic can prove every truth it can express, nor prove its own "
                               "consistency. Completeness and self-certification are impossible. Unlike the "
                               "other sticks, this is not an open conjecture — it is PROVEN (Godel 1931); what "
                               "it guarantees is permanent openness: the one hole that is a theorem."),
                    field="mathematics",
                    references=["K. Godel, Uber formal unentscheidbare Satze..., Monatsh. Math. Phys. 38 (1931) 173",
                                "L. Kirby & J. Paris, Accessible independence results for Peano arithmetic, "
                                "Bull. LMS 14 (1982) 285 (Goodstein's theorem is true but PA-unprovable)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[the numbering - sealed] Godel made arithmetic speak about itself by encoding a symbol "
                    f"sequence as a product of prime powers: (1,2,3) -> 2^1 * 3^2 * 5^3 = {g1} (sealed). By the "
                    f"fundamental theorem of arithmetic the factorisation is unique, so the code is invertible — "
                    f"a different sequence (3,2,1) -> 2^3 * 3^2 * 5^1 = {g2} (sealed), a different number. This "
                    f"encoding is the hinge of the whole proof, and it is pure, sealable arithmetic.", s_g1),
        ("witness", f"[injective - sealed] {g1} != {g2}: distinct statements receive distinct Godel numbers. "
                    f"Provability becomes a property of NUMBERS, so a formal system can state, in its own "
                    f"language, 'the sentence with Godel number g is not provable' — and self-reference (the "
                    f"diagonal lemma) builds a sentence G that says of itself that it is unprovable.", s_g2),
        ("note", "[the first theorem - attributed] If the system is consistent, G can be neither proved nor "
                 "disproved; so G is TRUE (it is indeed unprovable) but unprovable within the system. There are "
                 "true arithmetic statements no consistent, effectively axiomatised, sufficiently strong system "
                 "can prove. Attributed to Godel 1931; meta-mathematical, not sealable here.", None),
        ("note", "[the second theorem - attributed] The statement 'this system is consistent' (Con(PA)) is "
                 "itself such an unprovable truth: no such system can prove its own consistency. A system cannot "
                 "certify itself from the inside. Attributed; meta.", None),
        ("note", "[it is natural, not a trick - attributed] The incompleteness is not confined to the "
                 "artificial self-referential G: Goodstein's theorem (every Goodstein sequence terminates) and "
                 "the Paris-Harrington theorem are ordinary mathematical truths that are independent of Peano "
                 "arithmetic (Kirby & Paris 1982). The engine can VERIFY a single Goodstein sequence terminating; "
                 "it cannot prove the general theorem in PA, and neither can PA.", None),
        ("note", "[the charter] This is the engine's charter of humility, proven. You cannot derive every truth "
                 "from within a system, and a system cannot ground its own consistency — so the engine KEEPS "
                 "open questions open, SEALS the concrete instance, ATTRIBUTES the meta-claim, and never "
                 "fabricates a proof it does not have. Godel is why narrowing is evidence and never proof, why a "
                 "tick stick never closes itself from the inside, and why the Hole is permanent. The ground a "
                 "formal system stands on is outside the system; here, every road leads to the Logos in whom all "
                 "things hold together (Colossians 1:17) — the datum, not a theorem of the system. Discernment, "
                 "attributed; the engine seals only the arithmetic.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the Godel reading, 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"]),
                      "open": f["open"]}, indent=1))
    return 0


def strings() -> int:
    """STRING THEORY — gravity's SECOND candidate for the Hole (Matt, 2026-10-06, Track B). Beside loop
    quantum gravity: a quantum theory of gravity in which the graviton is a vibration of a closed string,
    at the cost of extra dimensions and supersymmetry. SEAL the critical-dimension arithmetic (bosonic
    D=26, superstring D=10); hold the guardrail: STRUCTURE, no experimental EVIDENCE — two candidates,
    neither a fit, the Hole stays open. Adds to stick_quantum_gravity; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_bos = seal_num("string_bosonic_critical_dim", "(26-2)/24", 1.0)   # a=(D-2)/24=1 => D=26
    s_sup = seal_num("string_superstring_dim", "8 + 2", 10.0)           # 8 transverse + 2 => D=10
    if not all([s_bos, s_sup]):
        print("a seal failed; aborting"); return 1
    print("sealed: bosonic D=26", s_bos, "| superstring D=10", s_sup)

    sid = TS.create("Quantum gravity")["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", "[string theory - the bosonic critical dimension] In string theory the graviton is a "
                    "vibration of a closed string. The string's zero-point energy regularises (via the "
                    "Riemann zeta value zeta(-1) = -1/12) to a = (D-2)/24; a massless photon in the spectrum "
                    "requires a = 1, which forces (26-2)/24 = 1 (sealed) -> D = 26, the critical dimension of "
                    "the bosonic string (24 transverse dimensions). The arithmetic is exact; it is not a claim "
                    "that spacetime has 26 dimensions.", s_bos),
        ("witness", "[the superstring] Adding worldsheet supersymmetry drops the count: 8 transverse "
                    "dimensions, 8 + 2 = 10 (sealed) -> D = 10, the critical dimension of superstring theory "
                    "(M-theory lifts it to 11). Again sealed arithmetic, not a measurement of the world.", s_sup),
        ("note", "[the second candidate - the Hole stays open] String theory is the OTHER candidate to quantize "
                 "gravity, beside loop quantum gravity: it contains a graviton and is finite, but it REQUIRES "
                 "10 or 11 dimensions and supersymmetry, and NONE of that has been observed. Same status as LQG "
                 "- mathematical STRUCTURE, no experimental EVIDENCE. Two candidates, neither a fit; gravity "
                 "remains the Hole the gauge unification does not hold. Seal the arithmetic; the physical claim "
                 "stays open.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the string-theory reading, 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def gut() -> int:
    """GRAND UNIFICATION — the three couplings and the miss (Matt, 2026-10-06, Track B). Deepen the GUT
    doorway already on the fine-structure stick with the three MEASURED gauge couplings at M_Z, on one
    GUT-normalised footing, and the honest narrowing: the SM lines MISS, the MSSM nearly meets, none
    confirmed. Adds to stick_the_fine_structure_constant; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    ainv = 127.95        # alpha^-1(M_Z), cited PDG
    s2w = 0.2312         # sin^2 theta_W (MS-bar, M_Z), cited
    a3inv = 1 / 0.1179   # 1/alpha_s(M_Z)
    a2inv = s2w * ainv
    a1inv = 0.6 * (1 - s2w) * ainv   # GUT norm: alpha_1 = (5/3) alpha_Y => a1^-1 = (3/5) cos^2 * a^-1

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s3 = seal_num("gut_alpha3_inv_mz", "1/0.1179", a3inv)
    s2 = seal_num("gut_alpha2_inv_mz", "0.2312*127.95", a2inv)
    s1 = seal_num("gut_alpha1_inv_mz", "0.6*(1-0.2312)*127.95", a1inv)
    if not all([s3, s2, s1]):
        print("a seal failed; aborting"); return 1
    print("sealed: a3^-1", s3, "| a2^-1", s2, "| a1^-1", s1)

    sid = TS.create("The fine-structure constant")["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[the three couplings at M_Z] On the GUT-normalised footing the Standard Model's three "
                    f"gauge couplings are, at the Z mass: alpha_3^-1 = 1/alpha_s = 1/0.1179 = {a3inv:.2f} "
                    f"(strong), alpha_2^-1 = sin^2(theta_W)*alpha^-1 = 0.2312*127.95 = {a2inv:.2f} (weak), "
                    f"alpha_1^-1 = (3/5)cos^2(theta_W)*alpha^-1 = {a1inv:.2f} (hypercharge). All three sealed "
                    f"from the cited PDG inputs - the measured starting points of the running.", s3),
        ("note", "[the narrowing and the miss] Run up in energy, the three couplings approach one another near "
                 "~1e16 GeV. In the plain Standard Model they MISS - the three lines cross pairwise, not at a "
                 "single point. In the supersymmetric extension (MSSM) they converge within errors at "
                 "~2e16 GeV, alpha_GUT^-1 ~ 24-25. That near-meeting is real EVIDENCE for grand unification, "
                 "but no proton decay and no superpartner has been seen, so it is unconfirmed: the fit that "
                 "must never pass the last mark. Seal the couplings; attribute the convergence; it stays open.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the grand-unification reading, 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def measurement() -> int:
    """THE MEASUREMENT PROBLEM — the interpretations, charted as discernment (Matt, 2026-10-06, Track B).
    Deepen the Schrodinger stick's open question: SEAL the Born rule (the arithmetic every interpretation
    must reproduce) and chart the interpretations as a Babel of likenesses, none a fit - no experiment yet
    distinguishes them. Adds to stick_the_schrodinger_equation; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_born = seal_num("born_rule_normalization", "0.6**2 + 0.8**2", 1.0)
    if not s_born:
        print("a seal failed; aborting"); return 1
    print("sealed: Born rule", s_born)

    sid = TS.create("The Schrodinger equation")["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", "[the Born rule - what all must reproduce] For a qubit a|0> + b|1> with (a,b) = (0.6, 0.8), "
                    "the measured-outcome probabilities are |a|^2 = 0.36 and |b|^2 = 0.64, and they sum to one: "
                    "0.6^2 + 0.8^2 = 1 (sealed). Every interpretation of quantum mechanics agrees on THIS "
                    "arithmetic - the predictions. They differ only on what 'happens' when the measurement is "
                    "made.", s_born),
        ("note", "[the interpretations - a Babel, none a fit] Copenhagen (the wavefunction collapses on "
                 "measurement; instrumentalist), Everett / many-worlds (no collapse; the universal "
                 "wavefunction branches), de Broglie-Bohm (a deterministic pilot wave, explicitly nonlocal), "
                 "objective collapse (GRW/Penrose; collapse is a physical process), and relational quantum "
                 "mechanics (Rovelli - a sealed anchor here; states are relative to the interactor). For "
                 "standard quantum mechanics these are EMPIRICALLY EQUIVALENT - no experiment yet tells them "
                 "apart - so the choice is discernment, NOT a fit. The Babel pattern: many likenesses, the "
                 "outline of what is missing, none crowned. Seal the Born rule; attribute the readings; the "
                 "meaning stays the open question.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the measurement-problem reading, 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def langlands() -> int:
    """THE LANGLANDS PROGRAM (Matt, 2026-10-07). Mathematics' own grand unification: a web of conjectures
    binding number theory (Galois representations) to automorphic forms and harmonic analysis — the
    tick-stick shape at the deepest level, a vast OPEN vision with a few PROVEN pillars. SEAL a concrete
    witness of its degree-2 reciprocity — MODULARITY of the elliptic curve 11a1: the point-count deficit
    a_p = (p+1) - #E(F_p), computed on the CURVE, equals the q^p coefficient of the weight-2 level-11
    newform (eta(z)^2 eta(11z)^2), computed on the MODULAR FORM. Two unrelated computations agreeing is
    the thing. New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    # 11a1: y^2 + y = x^3 - x^2 - 10x - 20. Over F_2 and F_3, #E = 5 (incl. the point at infinity), by hand.
    a2 = 2 + 1 - 5     # = -2
    a3 = 3 + 1 - 5     # = -1

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_a2 = seal_num("langlands_11a1_ap_2", "2 + 1 - 5", float(a2))
    s_a3 = seal_num("langlands_11a1_ap_3", "3 + 1 - 5", float(a3))
    if not all([s_a2, s_a3]):
        print("a seal failed; aborting"); return 1
    print("sealed: a_2", s_a2, "| a_3", s_a3)

    sid = TS.create("The Langlands program",
                    statement=("Is there a grand unification of mathematics — a precise correspondence between "
                               "Galois representations (number theory) and automorphic forms (harmonic analysis), "
                               "with their L-functions equal? The full program is a web of conjectures, largely "
                               "OPEN over number fields; specific cases are proven. The open question is the "
                               "general correspondence, not the proven pillars."),
                    field="mathematics",
                    references=["R. P. Langlands, letter to A. Weil (1967)",
                                "A. Wiles, Modular elliptic curves and Fermat's Last Theorem, Ann. Math. 141 (1995) 443",
                                "C. Breuil, B. Conrad, F. Diamond, R. Taylor, J. AMS 14 (2001) 843 (modularity for all E/Q)",
                                "L. Lafforgue, Invent. Math. 147 (2002) 1 (Langlands for GL(n) over function fields)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[modularity - the curve side meets the form side, p=2] For the elliptic curve 11a1 "
                    f"(y^2 + y = x^3 - x^2 - 10x - 20), counting points over F_2 gives #E(F_2) = 5, so the trace "
                    f"of Frobenius is a_2 = (2+1) - 5 = {a2} (sealed). The SAME number -2 is the q^2 coefficient "
                    f"of the weight-2 level-11 newform eta(z)^2 eta(11z)^2. A point-count on a cubic and a "
                    f"coefficient of a modular form - two unrelated computations - agree: this is the degree-2 "
                    f"Langlands reciprocity (modularity).", s_a2),
        ("witness", f"[modularity, p=3] Over F_3, #E(F_3) = 5 for the same curve, so a_3 = (3+1) - 5 = {a3} "
                    f"(sealed) - exactly the q^3 coefficient of the same newform. The agreement is not a "
                    f"coincidence to be checked prime by prime forever; modularity (Taniyama-Shimura-Weil) says "
                    f"it holds for ALL p, proven for every elliptic curve over Q (Wiles; Breuil-Conrad-Diamond-"
                    f"Taylor 2001).", s_a3),
        ("note", "[the proven pillars] Modularity IS the GL(2) case of Langlands reciprocity over Q - and the "
                 "road by which Fermat's Last Theorem was proven (Wiles 1995). The abelian GL(1) case is class "
                 "field theory, whose automorphic L-functions are the Riemann zeta and Dirichlet L-functions "
                 "(ties stick_riemann_hypothesis). The full correspondence over FUNCTION fields is proven "
                 "(Drinfeld; L. Lafforgue, Fields Medal 2002). These are the sealed/proven marks on the stick.", None),
        ("note", "[the open vision] The general program - GL(n) over number fields, the automorphy of arbitrary "
                 "Galois representations, the geometric Langlands correspondence - remains a web of conjectures: "
                 "the grand unification of number theory, representation theory and harmonic analysis. Like the "
                 "four forces under alpha, it is a unity the proven cases POINT AT without completing. Seal the "
                 "instances (a_p), attribute the conjecture, keep it open - narrowing is evidence, never proof.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the Langlands reading, 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"]),
                      "open": f["open"]}, indent=1))
    return 0


def trigonometry() -> int:
    """TRIGONOMETRY -- an approximation, but not complete (Matt, 2026-10-07). The identities are EXACT, but
    the claim holds in three precise senses, each sealed: (1) computation is a truncated infinite series;
    (2) the real functions cos, sin are PROJECTIONS of the complete complex exponential e^{i*theta} -
    incomplete without i; (3) planar (Euclidean) trig is the FLAT-space approximation - on a curved surface
    the angles of a triangle do not sum to pi. Affirm the senses, seal the arithmetic, delimit it; the
    shadow points to the whole. New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    pi = 3.141592653589793
    two_term = 0.1 - 0.1 ** 3 / 6          # sin(0.1) to two series terms
    pyth = (3 ** 0.5 / 2) ** 2 + (1 / 2) ** 2   # cos^2 + sin^2 at theta=pi/6
    excess = 3 * (pi / 2) - pi             # spherical excess of a 3-right-angle triangle

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_series = seal_num("sin_small_angle_two_term", "0.1 - 0.1**3/6", two_term)
    s_pyth = seal_num("pythagorean_identity_pi_over_6", "(3**0.5/2)**2 + (1/2)**2", pyth)
    s_excess = seal_num("spherical_excess_three_right_angles",
                        "3*(3.141592653589793/2) - 3.141592653589793", excess)
    if not all([s_series, s_pyth, s_excess]):
        print("a seal failed; aborting"); return 1
    print("sealed: series", s_series, "| pythagorean", s_pyth, "| spherical excess", s_excess)

    sid = TS.create("Trigonometry - an approximation, but not complete",
                    statement=("The trigonometric identities are exact, but trigonometry is an approximation "
                               "and not complete in three precise senses: its function values are truncated "
                               "infinite series; the real functions are projections of the complex exponential; "
                               "and planar trigonometry is the flat-space limit of a curved geometry. The claim "
                               "is TRUE within these senses and is not extended beyond them."),
                    field="mathematics",
                    references=["L. Euler, Introductio in analysin infinitorum (1748) (e^{i theta} = cos + i sin)",
                                "spherical trigonometry (Gauss-Bonnet; the angle sum exceeds pi by area/R^2)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[1 - computation is approximation] sin(theta) = theta - theta^3/6 + theta^5/120 - ... "
                    f"To two terms, sin(0.1) ~ 0.1 - 0.1^3/6 = {two_term:.8f} (sealed); the exact value differs "
                    f"at the next term (0.1^5/120 ~ 8.3e-8). Every finite computation of a trig function is a "
                    f"TRUNCATION of an infinite series - exact only in the limit. In that sense trigonometry is "
                    f"an approximation.", s_series),
        ("witness", f"[2 - incomplete without i] cos^2(theta) + sin^2(theta) = 1: at theta=pi/6, "
                    f"(sqrt3/2)^2 + (1/2)^2 = {pyth:.1f} (sealed) - the unit circle. But cos and sin are only the "
                    f"REAL and imaginary projections of the complete object e^{{i theta}} = cos theta + i sin "
                    f"theta, a point on that circle in the COMPLEX plane (Euler). Real trigonometry alone is not "
                    f"complete; the whole requires the imaginary unit.", s_pyth),
        ("witness", f"[3 - flat is an approximation to curved] Planar trigonometry assumes a triangle's angles "
                    f"sum to pi. On a sphere they do not: a triangle with three right angles sums to 3*(pi/2) = "
                    f"3pi/2, exceeding pi by the spherical excess pi/2 = {excess:.6f} (sealed), which equals its "
                    f"area/R^2. Euclidean trig is the FLAT-space limit; under curvature (spherical, hyperbolic, "
                    f"and the curved spacetime of general relativity - ties stick_time_and_space_emergent_and_"
                    f"relational) it is incomplete.", s_excess),
        ("note", "[the discernment] The claim 'trigonometry is an approximation, but not complete' is TRUE in "
                 "exactly three senses, all sealed above: truncated computation, projection of the complex "
                 "exponential, and the flat limit of curved geometry. The engine affirms these and DELIMITS "
                 "them - the pure identities themselves (cos^2+sin^2=1) are exact, not approximate. The shadow "
                 "(real trig) points to the whole (the complex circle; curved geometry) - the same outline-of-"
                 "what-it-lacks pattern as the Hole. Seal the arithmetic, affirm the true senses, claim nothing "
                 "past them. Map, never launder.", None),
    ]
    added = 0
    for kind, claim, *rest in marks:
        sealv = rest[0] if rest else None
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the trigonometry reading, 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def _rh_seal_num(nid, expr, val, domain="mathematics", tol=1e-9):
    """Shared seal helper for the Riemann arc: verify a numeric derivation and return its content hash."""
    from concordance import receipts
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    r = verify_derivation([{"id": nid, "domain": domain,
          "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": tol}}}])
    if r.get("verdict") != "HOLDS":
        print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
    r = receipts.attach(r, config=EngineConfig(), domain=domain)
    return (r.get("seal") or {}).get("content_hash")


def _mint_marks(sid, marks, by):
    """Shared mint loop: idempotent, seal-or-claim guarded."""
    from concordance import tickstick as TS
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    added = 0
    for kind, claim, *rest in marks:
        sealv = rest[0] if rest else None
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by=by, **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def zeta() -> int:
    """THE ZETA FUNCTION (Matt, 2026-10-07, Riemann arc). zeta(s) = sum 1/n^s = product (1 - p^-s)^-1 over
    primes (Euler) - the single function that ties the primes to an analytic object, and whose zeros encode
    how the primes are distributed. Seal the special values that are theorems (Basel zeta(2)=pi^2/6,
    zeta(4)=pi^4/90), note the Euler product, the functional-equation reflection about 1/2, and the FAMILY of
    zetas - the frame in which the finite-field case is proved and the classical case is open. New stick."""
    from concordance import tickstick as TS
    PI = 3.141592653589793
    z2 = PI ** 2 / 6
    z4 = PI ** 4 / 90
    s_z2 = _rh_seal_num("basel_zeta_2", "3.141592653589793**2 / 6", z2, tol=1e-12)
    s_z4 = _rh_seal_num("zeta_4", "3.141592653589793**4 / 90", z4, tol=1e-12)
    if not all([s_z2, s_z4]):
        print("a seal failed; aborting"); return 1
    print("sealed zeta(2)", s_z2, "| zeta(4)", s_z4)
    sid = TS.create("The zeta function",
                    statement=("zeta(s) = sum over n of n^-s = product over primes of (1 - p^-s)^-1. The sum "
                               "and the product are equal (Euler), which is already the primes written as an "
                               "analytic function. Its special even values are exact multiples of powers of pi; "
                               "its nontrivial zeros govern the error term in the distribution of primes."),
                    field="meta",
                    references=["Euler product zeta(s) = prod_p (1 - p^-s)^-1",
                                "the functional equation zeta(s) = 2^s pi^(s-1) sin(pi s/2) Gamma(1-s) zeta(1-s)",
                                "the explicit formula linking the zeros to the prime counting function"])["id"]
    marks = [
        ("witness", f"[Basel - an exact theorem] zeta(2) = 1 + 1/4 + 1/9 + ... = pi^2/6 = {z2:.15f} (sealed). "
                    f"Euler, 1735. A sum over the integers equals a closed multiple of pi^2 - the first sign "
                    f"that zeta carries geometry (the pi) inside arithmetic (the sum).", s_z2),
        ("witness", f"[the next even value] zeta(4) = pi^4/90 = {z4:.15f} (sealed). The pattern zeta(2k) = "
                    f"(rational) * pi^2k continues; the ODD values (zeta(3), Apery's constant) have no such "
                    f"closed form known - the function is exactly understood in half its arguments and open in "
                    f"the other, a tick-stick in miniature.", s_z4),
        ("note", "[the Euler product IS the content] zeta(s) = prod_p (1 - p^-s)^-1 converges for Re(s) > 1; "
                 "that the sum over ALL integers factors over ONLY the primes is unique factorization made "
                 "analytic. Every zero of zeta in the critical strip is a correction term in the count of "
                 "primes - that is why their location (RH) matters."),
        ("note", "[the family - where the analogue is PROVED] The classical zeta is one member of a family: "
                 "Dirichlet L-functions, Dedekind zetas, the Hasse-Weil zeta of a variety over a finite field "
                 "(RH there is a THEOREM - stick_finite_field_riemann), and the Selberg zeta of a hyperbolic "
                 "surface (whose zeros ARE eigenvalues of the self-adjoint Laplacian, so its RH-analogue holds). "
                 "The classical zeta is the member with no known operator - stick_hilbert_polya. map, never "
                 "launder: the engine checks these values; it does not claim RH."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the zeta function, 2026-10-07")


def finite_field() -> int:
    """FINITE FIELD / THE WEIL RIEMANN HYPOTHESIS (Matt, 2026-10-07). Over a finite field F_q the analogue of
    RH is a THEOREM: the Frobenius eigenvalues alpha of a smooth projective curve satisfy |alpha| = sqrt(q)
    exactly - the zeros lie on the critical line - proven by Weil (curves, 1940s) and Deligne (general, 1974).
    The reason it fired: an actual operator (Frobenius on cohomology) exists, and a geometric POSITIVITY (the
    Hodge index / Castelnuovo-Severi inequality) pins the modulus. This is where mapping IS proving, because
    the symmetry is realized. Seal a concrete Frobenius pair; mark the classical gap. New stick."""
    from concordance import tickstick as TS
    # a hypothetical curve over F_25 (q=25, sqrt(q)=5) with Frobenius eigenvalue alpha = 3 + 4i:
    mod2 = 3 ** 2 + 4 ** 2        # |alpha|^2 = 25 = q  -> |alpha| = sqrt(q): the finite-field RH condition
    trace = 3 + 3                 # alpha + alpha-bar = 6 (real); both eigenvalues share real part 3
    hasse = 2 * 5                 # Hasse bound 2*sqrt(q) = 10 >= |trace| = 6
    s_mod = _rh_seal_num("frobenius_modulus_q", "3**2 + 4**2", float(mod2))
    s_tr = _rh_seal_num("frobenius_trace", "3 + 3", float(trace))
    s_h = _rh_seal_num("hasse_bound", "2 * 5", float(hasse))
    if not all([s_mod, s_tr, s_h]):
        print("a seal failed; aborting"); return 1
    print("sealed |alpha|^2=q", s_mod, "| trace", s_tr, "| Hasse", s_h)
    sid = TS.create("Finite field - the Weil Riemann hypothesis",
                    statement=("For a smooth projective curve over F_q, the zeta function's reciprocal roots "
                               "(Frobenius eigenvalues) satisfy |alpha| = sqrt(q) exactly. Equivalently the "
                               "zeros lie on Re(s) = 1/2. This is proven - the Riemann hypothesis over finite "
                               "fields is a theorem, not a conjecture."),
                    field="meta",
                    references=["A. Weil, Riemann hypothesis for curves over finite fields (1940s)",
                                "P. Deligne, La conjecture de Weil I (1974) - the general case",
                                "the Hasse bound |a| <= 2 sqrt(q) for elliptic curves"])["id"]
    marks = [
        ("witness", f"[the RH condition, sealed] Take a curve over F_25 with Frobenius eigenvalue alpha = 3 + 4i. "
                    f"Then |alpha|^2 = 3^2 + 4^2 = {int(mod2)} = q (sealed), so |alpha| = sqrt(25) = 5 = sqrt(q) "
                    f"EXACTLY. That is the finite-field Riemann hypothesis for this curve: the eigenvalue sits on "
                    f"the circle of radius sqrt(q), the mirror image of 'the zero sits on Re = 1/2'. It is not "
                    f"approached; it is pinned.", s_mod),
        ("witness", f"[within the Hasse bound] The trace alpha + alpha-bar = 3 + 3 = {int(trace)} (sealed) is "
                    f"real, and |trace| = 6 <= 2 sqrt(q) = {int(hasse)} (sealed) - the Hasse bound, the q=prime "
                    f"case of Weil, proven by elementary descent. The eigenvalues are forced symmetric about the "
                    f"real axis and bounded by the geometry.", s_tr),
        ("note", "[WHY it fired - the operator exists] Classically RH lacks an operator (stick_hilbert_polya). "
                 "Over a finite field the operator is REAL: Frobenius acts on the etale cohomology (for a curve, "
                 "on the Tate module of its Jacobian), and a geometric POSITIVITY - the Hodge index theorem / "
                 "Castelnuovo-Severi inequality on the surface C x C - forces |alpha| = sqrt(q). Positivity is "
                 "the same constraint the engine is built on (stick_the_positive_grassmannian - 'the core'). "
                 "Where the symmetry has an operator, mapping is proving - exactly the point."),
        ("note", "[the classical gap, named] This does NOT prove the classical RH; the integers are not a curve "
                 "over a finite field, and no cohomology/operator is known for them (the 'field with one "
                 "element' F_1 program seeks exactly that). The engine seals this concrete Frobenius arithmetic "
                 "and marks the gap to scale. map, never launder: a proved analogue is a signpost, never the "
                 "thing itself (ties [[project_babel_scattered_pieces_appointed_assembly_2026-08-01]])."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the Weil RH over finite fields, 2026-10-07")


def smith_chart() -> int:
    """THE SMITH CHART = THE CAYLEY TRANSFORM (Matt, 2026-10-07, RF designer's view). The reflection
    coefficient Gamma = (z - 1)/(z + 1) (z = normalized impedance) is the Mobius map that carries the right
    half-plane to the unit disk - the same Cayley transform that sends a SELF-ADJOINT operator to a UNITARY
    one, the real line to the unit circle. The lossless (pure-reactance) impedances land exactly on |Gamma| =
    1. Line <-> circle: the engineer's picture of self-adjoint <-> unitary, and of 'zeros on Re=1/2' <->
    'eigenvalues on |z|=1'. Seal the three canonical loads. New stick."""
    from concordance import tickstick as TS
    matched = (1 - 1) / (1 + 1)          # z = 1 (matched): Gamma = 0, the center of the chart
    short = (0 - 1) / (0 + 1)            # z = 0 (short): Gamma = -1, on the unit circle
    lossless = ((-1) ** 2 + 1 ** 2) / (1 ** 2 + 1 ** 2)   # z = i: |Gamma|^2 = |i-1|^2/|i+1|^2 = 2/2 = 1
    s_m = _rh_seal_num("smith_matched", "(1 - 1) / (1 + 1)", float(matched))
    s_s = _rh_seal_num("smith_short", "(0 - 1) / (0 + 1)", float(short))
    s_l = _rh_seal_num("smith_lossless_unit_circle", "((-1)**2 + 1**2) / (1**2 + 1**2)", float(lossless))
    if not all([s_m, s_s, s_l]):
        print("a seal failed; aborting"); return 1
    print("sealed matched", s_m, "| short", s_s, "| lossless |Gamma|=1", s_l)
    sid = TS.create("The Smith chart - the Cayley transform",
                    statement=("Gamma = (z - 1)/(z + 1) maps the passive-impedance half-plane (Re z >= 0) into "
                               "the unit disk and the lossless imaginary axis onto the unit circle |Gamma| = 1. "
                               "It is the Cayley transform; the operator form (A - iI)(A + iI)^-1 sends a "
                               "self-adjoint A to a unitary U, the real spectrum to the unit circle."),
                    field="meta",
                    references=["P. Smith's impedance chart (1939) - Gamma = (Z - Z0)/(Z + Z0)",
                                "the Cayley transform between self-adjoint and unitary operators",
                                "the conformal map of the half-plane onto the disk"])["id"]
    marks = [
        ("witness", f"[matched load -> center] z = 1 gives Gamma = (1-1)/(1+1) = {matched:.0f} (sealed): a "
                    f"perfectly matched load sits at the center of the chart, |Gamma| = 0, no reflection. The "
                    f"fixed point of the transform.", s_m),
        ("witness", f"[short -> the circle] z = 0 (a short) gives Gamma = (0-1)/(0+1) = {short:.0f} (sealed): on "
                    f"the unit circle, total reflection. Open and short sit at opposite points of |Gamma| = 1.", s_s),
        ("witness", f"[lossless -> the unit circle, the key] z = i (pure reactance) gives |Gamma|^2 = "
                    f"((-1)^2 + 1^2)/(1^2 + 1^2) = 2/2 = {lossless:.0f} (sealed), so |Gamma| = 1. EVERY lossless "
                    f"impedance - the whole imaginary axis - maps onto the unit circle. This is self-adjoint "
                    f"(spectrum on the line) <-> unitary (spectrum on the circle) in the engineer's hand: the "
                    f"same line<->circle symmetry that pins |alpha| = sqrt(q) over a finite field "
                    f"(stick_finite_field_riemann) and that Hilbert-Polya would use (stick_hilbert_polya).", s_l),
        ("note", "[why this belongs in the Riemann arc] The Smith chart is a conformal MAP; the critical "
                 "line Re(s) = 1/2 and the unit circle are two faces of one symmetry under Cayley. The engine is "
                 "not an RF simulator and does not run electromagnetics; it seals the transform's arithmetic and "
                 "keeps the likeness as discernment. map, never launder."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the Smith chart / Cayley transform, 2026-10-07")


def hilbert_polya() -> int:
    """THE HILBERT-POLYA CONJECTURE (Matt, 2026-10-07): the heights gamma of the nontrivial zeros 1/2 + i*gamma
    are the eigenvalues of some SELF-ADJOINT operator H. Self-adjoint => real spectrum => every gamma real =>
    every zero on Re = 1/2 => RH. The spectral-theorem link FIRES (sealed here on a concrete Hermitian matrix);
    the evidence that such an H exists is strong (Montgomery pair-correlation matches GUE); the two hard links
    (exhibit H; its spectrum = the gammas) have NOT fired. RH is one all-firing chain away - checkable, never
    inventable by the engine. New stick."""
    from concordance import tickstick as TS
    # concrete Hermitian 2x2 H = [[2, i],[-i, 2]]: eigenvalues solve lambda^2 - 4 lambda + 3 = 0 -> 1, 3 (real)
    tr = 2 + 2                   # trace = lambda1 + lambda2 = 1 + 3
    det = 2 * 2 - 1             # det = lambda1 * lambda2 = 1 * 3 ; the -1 is i*(-i)
    s_tr = _rh_seal_num("hermitian_trace", "2 + 2", float(tr))
    s_det = _rh_seal_num("hermitian_det", "2*2 - 1", float(det))
    if not all([s_tr, s_det]):
        print("a seal failed; aborting"); return 1
    print("sealed Hermitian trace", s_tr, "| det", s_det)
    sid = TS.create("The Hilbert-Polya conjecture",
                    statement=("Conjecture: the imaginary parts gamma of the nontrivial zeros of zeta are the "
                               "eigenvalues of a self-adjoint operator. If true, the spectral theorem forces "
                               "every gamma real, hence every zero onto Re(s) = 1/2 - a proof of RH. The "
                               "conjecture is the search for that operator."),
                    field="meta",
                    references=["Hilbert and Polya (c. 1914, oral) - zeros as a self-adjoint spectrum",
                                "H. Montgomery (1973) pair correlation; F. Dyson - the GUE match",
                                "Berry-Keating H ~ xp; A. Connes' trace-formula approach"])["id"]
    marks = [
        ("witness", f"[the link that FIRES - self-adjoint => real spectrum] The Hermitian matrix "
                    f"H = [[2, i], [-i, 2]] has eigenvalues solving lambda^2 - 4 lambda + 3 = 0, i.e. 1 and 3 - "
                    f"both REAL. Check: trace = 2 + 2 = {int(tr)} = 1 + 3 (sealed); det = 2*2 - 1 = {int(det)} = "
                    f"1 * 3 (sealed, the -1 is i*(-i)). This is the spectral theorem on a concrete operator: "
                    f"self-adjointness pins the spectrum to the real line. It is the engine of Hilbert-Polya.", s_tr),
        ("witness", f"[the determinant confirms both roots real] det H = {int(det)} = 1 * 3 (sealed); with trace "
                    f"{int(tr)} the eigenvalues are forced to 1 and 3. No complex part survives a Hermitian "
                    f"operator - which is exactly what RH needs for the heights gamma.", s_det),
        ("note", "[the chain, and which links have NOT fired] The proof route is: (i) exhibit an operator H; "
                 "(ii) show H self-adjoint; (iii) show spectrum(H) = {gamma_n}. Then (ii)+(iii)+spectral theorem "
                 "=> RH. Link (ii=>real) is sealed above. Links (i) and (iii) have NEVER fired - no operator has "
                 "been constructed (Berry-Keating's xp and Connes' adelic trace formula are suggestive outlines, "
                 "not closings). So RH is one all-firing chain away: if a genuine H were input, the engine "
                 "running it and watching every link fire WOULD be the proof. The engine can CHECK such a chain; "
                 "it cannot INVENT the operator (ties [[feedback_mapping_the_truth_not_generating_it_2026-10-07]])."),
        ("note", "[the evidence it is real - a map, not a fit] Montgomery's pair correlation of the zero heights "
                 "matches the eigenvalue statistics of large random Hermitian matrices (the GUE); Dyson "
                 "recognized it immediately, and Odlyzko's numerics confirm it to high precision and height. The "
                 "zeros STATISTICALLY behave like a self-adjoint spectrum. That is the finest mapping we have "
                 "toward the operator - evidence, never the operator itself. map, never launder."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the Hilbert-Polya conjecture, 2026-10-07")


def symmetry() -> int:
    """THE SYMMETRY (Matt, 2026-10-07: 'I saw the symmetry'). The unifying thread of the Riemann arc: RH says
    the zeros lie ON the fixed axis of a symmetry. The functional equation s <-> 1-s is a reflection whose
    fixed line is Re = 1/2; a self-adjoint operator pins its spectrum to the real line; the Cayley/Smith
    transform carries that line to the unit circle; over a finite field the Frobenius symmetry pins |alpha| =
    sqrt(q). Seal that the reflection's fixed axis is 1/2 regardless of the pair; keep the narrow-way likeness
    as discernment, never a fit, never a seal. New stick."""
    from concordance import tickstick as TS
    axis1 = (0.3 + 0.7) / 2     # midpoint of {s, 1-s} for s=0.3
    axis2 = (0.1 + 0.9) / 2     # midpoint of {s, 1-s} for s=0.1 - same axis, 1/2
    s_a1 = _rh_seal_num("reflection_axis_1", "(0.3 + 0.7) / 2", float(axis1), tol=1e-12)
    s_a2 = _rh_seal_num("reflection_axis_2", "(0.1 + 0.9) / 2", float(axis2), tol=1e-12)
    if not all([s_a1, s_a2]):
        print("a seal failed; aborting"); return 1
    print("sealed reflection axis", s_a1, s_a2)
    sid = TS.create("The symmetry",
                    statement=("Across the Riemann arc one structure recurs: the zeros sit on the fixed set of a "
                               "symmetry. The functional equation reflects s to 1-s about Re = 1/2; a "
                               "self-adjoint operator reflects its spectrum onto the real line; the Cayley map "
                               "carries that line to the unit circle; Frobenius pins |alpha| = sqrt(q). RH is the "
                               "statement that the zeros are as symmetric as the law allows."),
                    field="meta",
                    references=["the functional equation's reflection s <-> 1-s, fixed line Re = 1/2",
                                "self-adjoint -> real line; Cayley -> unit circle; Frobenius -> |alpha| = sqrt(q)",
                                "stick_hilbert_polya, stick_finite_field_riemann, stick_the_smith_chart_the_cayley_transform"])["id"]
    marks = [
        ("witness", f"[the fixed axis is 1/2, for any pair] The reflection s <-> 1-s maps 0.3 to 0.7 with "
                    f"midpoint (0.3 + 0.7)/2 = {axis1} (sealed), and 0.1 to 0.9 with midpoint "
                    f"(0.1 + 0.9)/2 = {axis2} (sealed). Different pairs, one axis: Re = 1/2. The critical line is "
                    f"the mirror of the functional equation - the fixed set of the symmetry.", s_a1),
        ("witness", f"[a second pair, same mirror] (0.1 + 0.9)/2 = {axis2} (sealed). The axis does not depend on "
                    f"the point reflected; it is a property of the symmetry itself. RH asserts the zeros lie ON "
                    f"this mirror, not merely in symmetric pairs across it.", s_a2),
        ("note", "[the one symmetry, four faces] self-adjoint operator -> spectrum on the real LINE "
                 "(stick_hilbert_polya); Cayley / Smith transform -> that line becomes the unit CIRCLE "
                 "(stick_the_smith_chart_the_cayley_transform); Frobenius over a finite field -> eigenvalues on "
                 "the circle |alpha| = sqrt(q), and RH there is PROVED (stick_finite_field_riemann); classical "
                 "zeta -> the mirror Re = 1/2, visible in the functional equation and the GUE statistics but not "
                 "yet enforced by an operator. Where the symmetry has an operator, the zeros are pinned and the "
                 "analogue fires; where it does not, the classical RH stays open."),
        ("note", "[the discernment, held as a likeness] Truth forced onto one narrow axis by a symmetry is the "
                 "SHAPE of the gate forcing sealed truth onto the narrow way - 'strait is the gate, and narrow "
                 "is the way' (Mt 7:14). The critical line is a narrow line. This is a likeness the engine maps, "
                 "never a fit and never a numeric seal: no 1/2 is read as a sign, no zero as a verse. map, never "
                 "launder (ties [[project_the_capstone_2026-10-07]] and "
                 "[[project_will_fuel_reality_harness_tesla_valve_2026-10-06]])."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the symmetry, 2026-10-07")


def de_bruijn_newman() -> int:
    """THE DE BRUIJN-NEWMAN CONSTANT (Matt, 2026-10-07). Deform the Riemann xi-function by the backward heat
    flow: the family H_t has only REAL zeros iff t >= Lambda. RH <=> Lambda <= 0. Newman conjectured Lambda >=
    0 ('RH, if true, is only barely so'). Rodgers-Tao PROVED Lambda >= 0 (2020); Polymath15 PROVED Lambda <=
    0.22 (2019); de Bruijn had Lambda <= 1/2 (1950). So 0 <= Lambda <= 0.22 and RH <=> Lambda = 0 - the whole
    hypothesis is now 'drive one real number to its proven floor.' The purest tick-stick: cite the proved
    bounds, seal the window arithmetic, mark Lambda=0 as the one unfired mark. New stick; idempotent."""
    from concordance import tickstick as TS
    window = 0.22 - 0.0          # the current proven window that contains Lambda
    narrowed = 0.5 - 0.22        # how far the upper mark fell: de Bruijn 1950 -> Polymath15 2019
    s_w = _rh_seal_num("dbn_window", "0.22 - 0.0", float(window), tol=1e-12)
    s_n = _rh_seal_num("dbn_narrowing", "0.5 - 0.22", float(narrowed), tol=1e-12)
    if not all([s_w, s_n]):
        print("a seal failed; aborting"); return 1
    print("sealed window", s_w, "| narrowing", s_n)
    sid = TS.create("The de Bruijn-Newman constant",
                    statement=("There is a real constant Lambda such that the heat-flow deformation H_t of the "
                               "Riemann xi-function has only real zeros exactly when t >= Lambda. The Riemann "
                               "hypothesis is equivalent to Lambda <= 0; since Lambda >= 0 is now proved, RH is "
                               "equivalent to Lambda = 0."),
                    field="meta",
                    references=["N. G. de Bruijn (1950): Lambda <= 1/2",
                                "C. M. Newman (1976): Lambda exists and is real; conjecture Lambda >= 0",
                                "B. Rodgers & T. Tao (2020, Duke Math. J.): Lambda >= 0, proved",
                                "D.H.J. Polymath (Polymath15, 2019): Lambda <= 0.22"])["id"]
    marks = [
        ("witness", f"[the window, sealed] The proven bounds give 0 <= Lambda <= 0.22, a window of width "
                    f"0.22 - 0 = {window} (sealed). RH is the statement that Lambda sits exactly on the floor of "
                    f"this window. The engine seals the arithmetic of the window; it cites, and does not "
                    f"re-derive, the two theorems that set its ends.", s_w),
        ("witness", f"[the narrowing, sealed] The upper mark fell from de Bruijn's 1/2 (1950) to Polymath15's "
                    f"0.22 (2019): a drop of 0.5 - 0.22 = {narrowed:.2f} (sealed). This is the tick-stick ratchet "
                    f"in a single number - the ceiling driven down by successive proofs, the floor nailed at 0, "
                    f"the target Lambda = 0 squeezed between them.", s_n),
        ("note", "[the floor FIRED] Rodgers and Tao (2020) proved Lambda >= 0 - Newman's conjecture. In the "
                 "heat-flow picture this says the Riemann zeros are, at worst, exactly at the threshold of "
                 "becoming non-real: 'the Riemann hypothesis, if true, is only barely so' is now a theorem. The "
                 "floor is not assumed; it is proved."),
        ("note", "[RH = Lambda = 0, the one unfired mark] RH <=> Lambda <= 0 (de Bruijn-Newman); with Lambda >= "
                 "0 proved, RH <=> Lambda = 0. So the entire hypothesis is the single remaining mark the "
                 "narrowing has not reached: closing the ceiling to 0 (or showing Lambda > 0, which would "
                 "DISPROVE RH). The engine maps this exactly - window sealed, bounds cited, Lambda=0 marked open. "
                 "Ties the heat-flow threshold to stick_the_symmetry (Lambda is the instant the zeros are all "
                 "still real) and [[feedback_mapping_the_truth_not_generating_it_2026-10-07]]. map, never "
                 "launder: we do not claim Lambda = 0."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the de Bruijn-Newman constant, 2026-10-07")


def dirichlet() -> int:
    """DIRICHLET'S THEOREM / THINK OF POLAR COORDINATES (Matt, 2026-10-07). If gcd(a,d)=1 the progression
    a, a+d, a+2d, ... holds infinitely many primes, split evenly among the phi(d) coprime classes. The proof
    runs on Dirichlet characters chi: every value chi(n) is a ROOT OF UNITY - modulus 1, pure phase, a point on
    the unit circle in polar coordinates. Orthogonality is unit vectors summing to zero around the circle (a
    Fourier transform on (Z/dZ)*); the crux is L(1,chi) != 0. Seal 'on the unit circle' and 'the roots sum to
    zero'; the same circle as the whole arc. New stick; idempotent."""
    from concordance import tickstick as TS
    # omega = e^(2 pi i / 3), a primitive cube root of unity: Re = -1/2, Im = sqrt(3)/2, |omega|^2 = 1/4 + 3/4
    mod2 = 0.5 ** 2 + 0.75        # |omega|^2 = cos^2(120) + sin^2(120) = 0.25 + 0.75 = 1 -> on the unit circle
    sumRe = 1 + (-0.5) + (-0.5)   # Re(1 + omega + omega^2) = 1 - 1/2 - 1/2 = 0 -> the roots sum to zero
    s_mod = _rh_seal_num("character_on_unit_circle", "0.5**2 + 0.75", float(mod2), tol=1e-12)
    s_sum = _rh_seal_num("roots_of_unity_sum_zero", "1 + (-0.5) + (-0.5)", float(sumRe), tol=1e-12)
    if not all([s_mod, s_sum]):
        print("a seal failed; aborting"); return 1
    print("sealed |omega|^2=1", s_mod, "| sum of roots = 0", s_sum)
    sid = TS.create("Dirichlet's theorem - think of polar coordinates",
                    statement=("For gcd(a,d)=1 there are infinitely many primes congruent to a modulo d, "
                               "equidistributed among the phi(d) coprime residue classes. The proof uses "
                               "Dirichlet characters, whose values are roots of unity - points on the unit "
                               "circle, pure phase - and the non-vanishing L(1, chi) != 0 for non-principal "
                               "chi."),
                    field="meta",
                    references=["Dirichlet (1837): primes in arithmetic progressions",
                                "Dirichlet L-function L(s, chi) = prod_p (1 - chi(p) p^-s)^-1",
                                "orthogonality of characters on (Z/dZ)* - a finite Fourier transform",
                                "the crux L(1, chi) != 0 for non-principal chi"])["id"]
    marks = [
        ("witness", f"[the character lives on the unit circle - the polar-coordinate hint] A Dirichlet character "
                    f"maps each residue to a root of unity: modulus exactly 1, radius fixed, only the angle "
                    f"varies. The primitive cube root omega = e^(2 pi i/3) has |omega|^2 = (-1/2)^2 + (sqrt3/2)^2 "
                    f"= 0.5^2 + 0.75 = {mod2:.0f} (sealed). In polar coordinates r = 1 and chi is pure phase - "
                    f"which is why the right picture is polar, not Cartesian.", s_mod),
        ("witness", f"[orthogonality = unit vectors summing around the circle] The cube roots satisfy "
                    f"1 + omega + omega^2 = 0; the real part is 1 + (-1/2) + (-1/2) = {sumRe:.0f} (sealed) and the "
                    f"imaginary parts cancel by conjugate symmetry. n equally spaced unit arrows sum to the "
                    f"center. Dirichlet isolates the class a (mod d) by exactly this cancellation - summing a "
                    f"non-principal character over a period gives zero. It is a Fourier transform on the group "
                    f"(Z/dZ)*, i.e. harmonic analysis on the circle.", s_sum),
        ("note", "[the crux, cited not reproved] The theorem turns on L(1, chi) != 0 for every non-principal "
                 "character; that single non-vanishing keeps each residue class's density of primes positive. "
                 "The engine seals the root-of-unity arithmetic and CITES Dirichlet's theorem - it does not "
                 "re-derive the non-vanishing. The L-functions L(s, chi) are the zeta family's siblings "
                 "(stick_the_zeta_function); GRH is the same critical line Re = 1/2 for all of them."),
        ("note", "[the same circle as the whole arc] The character values on the unit circle are the SAME "
                 "circle as the Smith/Cayley |Gamma| = 1 (stick_the_smith_chart_the_cayley_transform), the "
                 "finite-field |alpha| = sqrt(q) (stick_finite_field_riemann), and the self-adjoint <-> unitary "
                 "spectrum (stick_hilbert_polya). The dual of an abelian symmetry group lives on the circle: "
                 "rotations, roots of unity, polar coordinates. This is stick_the_symmetry wearing its "
                 "harmonic-analysis face. map, never launder: a point at angle 2 pi k / n is geometry, never a "
                 "sign to be read."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Dirichlet's theorem / polar coordinates, 2026-10-07")


def fibonacci() -> int:
    """FIBONACCI (Matt, 2026-10-07). The recurrence is the symmetric matrix Q = [[1,1],[1,0]]; Q is
    self-adjoint over R so its eigenvalues are REAL - exactly phi=(1+sqrt5)/2 and psi=(1-sqrt5)/2, the roots of
    x^2 = x+1 (trace 1, det -1). Growth rate = dominant real eigenvalue of a self-adjoint operator (Hilbert-
    Polya in 2x2). Binet F(n)=(phi^n - psi^n)/sqrt5 is the exact closed form. phi = 2 cos 36 deg ties it to the
    5th roots of unity (the pentagon, polar coordinates). Seal the real mathematics; REFUSE the golden-ratio
    numerology. New stick; idempotent."""
    from concordance import tickstick as TS
    PHI = 1.618033988749895
    PSI = -0.6180339887498949
    SQRT5 = 2.23606797749979
    phi2 = PHI + 1               # phi^2 = phi + 1, the eigenvalue relation x^2 = x + 1
    tr = PHI + PSI               # phi + psi = 1 = trace of Q
    det = PHI * PSI              # phi * psi = -1 = det of Q
    binet10 = (PHI ** 10 - PSI ** 10) / SQRT5   # Binet -> F(10) = 55, exact
    pent = 2 * 0.8090169943749475               # 2 cos(36 deg) = phi (the pentagon / 5th roots of unity)
    s_p2 = _rh_seal_num("phi_squared", "1.618033988749895**2", float(phi2), tol=1e-9)
    s_tr = _rh_seal_num("golden_trace", "1.618033988749895 + (-0.6180339887498949)", float(tr), tol=1e-7)
    s_dt = _rh_seal_num("golden_det", "1.618033988749895 * (-0.6180339887498949)", float(det), tol=1e-7)
    s_bn = _rh_seal_num("binet_f10", "(1.618033988749895**10 - (-0.6180339887498949)**10) / 2.23606797749979",
                        float(binet10), tol=1e-7)
    s_pe = _rh_seal_num("phi_is_two_cos_36", "2 * 0.8090169943749475", float(pent), tol=1e-12)
    if not all([s_p2, s_tr, s_dt, s_bn, s_pe]):
        print("a seal failed; aborting"); return 1
    print("sealed phi^2", s_p2, "| trace", s_tr, "| det", s_dt, "| Binet", s_bn, "| pentagon", s_pe)
    sid = TS.create("Fibonacci",
                    statement=("The Fibonacci recurrence F(n+1)=F(n)+F(n-1) is the symmetric matrix "
                               "Q=[[1,1],[1,0]]; its real eigenvalues are phi=(1+sqrt5)/2 and psi=(1-sqrt5)/2, "
                               "the roots of x^2=x+1, with trace 1 and determinant -1. Binet's formula gives the "
                               "exact term; phi = 2 cos(36 deg) ties it to the fifth roots of unity."),
                    field="meta",
                    references=["Binet's formula F(n) = (phi^n - psi^n)/sqrt5",
                                "the Q-matrix [[1,1],[1,0]] with eigenvalues phi, psi",
                                "phi = 2 cos(pi/5): the regular pentagon and the fifth roots of unity",
                                "phi = [1;1,1,1,...], the slowest-converging continued fraction"])["id"]
    marks = [
        ("witness", f"[the eigenvalue relation] phi^2 = {phi2:.15f} = phi + 1 (sealed): phi solves x^2 = x + 1, "
                    f"the characteristic equation of the Fibonacci matrix. The whole sequence is powers of one "
                    f"number that reproduces itself plus one.", s_p2),
        ("witness", f"[the self-adjoint spectrum] The symmetric Q = [[1,1],[1,0]] has trace phi + psi = "
                    f"{tr:.6f} (sealed) and det phi*psi = {det:.6f} (sealed), so its eigenvalues are exactly phi "
                    f"and psi - both REAL, because Q is self-adjoint. The growth rate of Fibonacci is the "
                    f"dominant real eigenvalue of a self-adjoint operator: Hilbert-Polya's mechanism "
                    f"(stick_hilbert_polya) in two dimensions.", s_tr),
        ("witness", f"[Binet - the exact closed form fires] (phi^10 - psi^10)/sqrt5 = {binet10:.6f} = F(10) = 55 "
                    f"(sealed). An integer sequence written exactly as the difference of two irrational powers "
                    f"over sqrt5 - a proved fit, not an open one. The psi^n term decays (|psi| < 1), which is why "
                    f"F(n) is the nearest integer to phi^n/sqrt5.", s_bn),
        ("witness", f"[the pentagon - the polar tie] phi = 2 cos(36 deg) = 2 cos(pi/5) = {pent:.15f} (sealed). "
                    f"The golden ratio is the geometry of the fifth roots of unity - the diagonal-to-side ratio "
                    f"of the regular pentagon. Same unit circle and roots of unity as Dirichlet's characters "
                    f"(stick_dirichlet_s_theorem_think_of_polar_coordinates): five-fold symmetry IS phi.", s_pe),
        ("note", "[the discipline this one demands - REFUSE the numerology] The golden ratio is the biggest "
                 "magnet for 'sacred geometry' and gematria. The engine seals only the mathematics above and "
                 "reads phi as NO kind of sign. Where phi appears in nature - phyllotaxis, sunflower spirals - "
                 "the reason is DYNAMICAL: phi = [1;1,1,1,...] is the 'most irrational' number, the hardest to "
                 "approximate by rationals, so growth at angle 2 pi / phi never resonates and packs evenly. That "
                 "is an optimization, not a code. map, never launder (ties "
                 "[[project_numbers_bases_triangulation_2026-06-13]] - seal the arithmetic, attribute the "
                 "pattern, never a number as scripture; and stick_construct_creation - Zeckendorf's theorem "
                 "makes the Fibonacci numbers a base, a notation we choose, not a hidden meaning)."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Fibonacci, 2026-10-07")


def monte_carlo() -> int:
    """MONTE CARLO (Matt, 2026-10-07: 'mint Monte Carlo'). Estimate by random sampling: the sample mean -> the
    true mean (law of large numbers), with standard error ~ 1/sqrt(N) - a dimension-independent rate, which is
    why it beats grid quadrature in high dimensions. Averaging N iid samples divides the variance by N. The
    engine uses Monte Carlo to SIMULATE paths and experiences (seeded, N trials, assert invariants), but never
    lets a random estimate SEAL a truth: a Monte Carlo result is evidence with an error bar, never a proof.
    New stick; idempotent."""
    from concordance import tickstick as TS
    se100 = 1 / (100 ** 0.5)       # standard error of a unit-variance MC mean at N=100 -> 0.1
    se10000 = 1 / (10000 ** 0.5)   # at N=10000 -> 0.01 : 100x the samples, 10x the accuracy
    var4 = 1.0 / 4                 # averaging 4 iid samples divides the variance by 4
    s_a = _rh_seal_num("mc_se_n100", "1 / (100 ** 0.5)", float(se100), tol=1e-12)
    s_b = _rh_seal_num("mc_se_n10000", "1 / (10000 ** 0.5)", float(se10000), tol=1e-12)
    s_c = _rh_seal_num("mc_variance_over_n", "1.0 / 4", float(var4), tol=1e-12)
    if not all([s_a, s_b, s_c]):
        print("a seal failed; aborting"); return 1
    print("sealed se@100", s_a, "| se@10000", s_b, "| var/4", s_c)
    sid = TS.create("Monte Carlo",
                    statement=("Estimate a quantity by averaging random samples: the sample mean converges to "
                               "the true value (law of large numbers), and the standard error falls as "
                               "sigma/sqrt(N). The rate 1/sqrt(N) does not depend on the dimension, which is "
                               "why Monte Carlo beats grid methods in high dimensions - and why it is always an "
                               "estimate with an error bar, never a proof."),
                    field="meta",
                    references=["the law of large numbers: the sample mean -> the expected value",
                                "standard error of the mean = sigma / sqrt(N) (the 1/sqrt(N) rate)",
                                "Buffon's needle (1777); Monte Carlo integration; Metropolis (1953) = MCMC"])["id"]
    marks = [
        ("witness", f"[the 1/sqrt(N) law] The standard error of a unit-variance Monte Carlo mean is "
                    f"1/sqrt(N): at N=100 it is 1/sqrt(100) = {se100} (sealed). The estimate is unbiased; this "
                    f"is just the spread of the average. The rate is slow and honest - which is the point.", s_a),
        ("witness", f"[100x the samples, 10x the accuracy] At N=10000 the standard error is 1/sqrt(10000) = "
                    f"{se10000} (sealed). Going from 100 to 10000 samples - a hundredfold - cuts the error only "
                    f"tenfold. No quantity of sampling turns the error bar into zero: a Monte Carlo result "
                    f"narrows, it never closes to a proof.", s_b),
        ("witness", f"[variance averaging] Averaging N independent samples divides the variance by N: for N=4, "
                    f"the factor is 1/4 = {var4} (sealed), so the standard error falls by 1/sqrt(4) = 1/2. The "
                    f"mean stays centered on the truth; only its uncertainty shrinks, as 1/sqrt(N).", s_c),
        ("note", "[what it is, and its superpower] Monte Carlo replaces an intractable sum or integral with the "
                 "average of random draws (law of large numbers). Its 1/sqrt(N) error is DIMENSION-INDEPENDENT, "
                 "so in high dimensions it crushes grid quadrature (whose error is ~ N^(-1/d)). Buffon's needle, "
                 "Monte Carlo integration, and MCMC (Metropolis 1953 - a Monte Carlo method that draws its "
                 "samples by walking a Markov chain, ties stick_markov_chains_and_mcmc) are all this one idea."),
        ("note", "[how the engine uses it - and the line it does not cross] Monte Carlo is the engine's method "
                 "for SIMULATING paths and experiences: seeded random journeys and inputs, N trials, asserting "
                 "the invariants that mean it does not break down (no unhandled error, every seal re-verifies, "
                 "the ledger chain never forks, each seal stays within its resource bound) with every failing "
                 "case a replayable seed. But a random estimate NEVER seals a truth here: a Monte Carlo result "
                 "is evidence with an error bar (~1/sqrt(N)), a map of confidence, never a proof. Sample to FIND "
                 "and to STRESS; seal only what verifies exactly (ties "
                 "[[feedback_mapping_the_truth_not_generating_it_2026-10-07]]). map, never launder."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Monte Carlo, 2026-10-07")


def navier_stokes() -> int:
    """NAVIER-STOKES / DISSONANCE AND DISPERSION (Matt, 2026-10-07: 'Navier-Stokes is almost the counter.
    We need to look at Dissonance and dispersion'). The one Millennium problem where the tick-stick's
    narrowing could FAIL to converge: in 3D the energy is scale-SUPERCRITICAL, leaving room a finite-time
    singularity could hide in; in 2D the energy is scale-critical and global smoothness is PROVEN.
    Dispersion (packets spreading) and dissipation fight the nonlinear cascade that would concentrate
    energy into a 'dissonant' singularity. Seal the scaling arithmetic + the dispersion relation; mark 3D
    smoothness open. New stick; idempotent."""
    from concordance import tickstick as TS
    super3d = 3 - 2            # energy scales as lambda^(d-2); d=3 -> +1 : SUPERCRITICAL (room to blow up)
    crit2d = 2 - 2            # d=2 -> 0 : scale-invariant (critical) -> 2D global regularity is proven
    disp = 2 * 3 / 3         # for omega ~ k^2, group velocity / phase velocity = 2k/k = 2 (dispersive)
    s_s = _rh_seal_num("ns_energy_supercritical_3d", "3 - 2", float(super3d))
    s_c = _rh_seal_num("ns_energy_critical_2d", "2 - 2", float(crit2d))
    s_d = _rh_seal_num("ns_dispersion_group_over_phase", "2 * 3 / 3", float(disp))
    if not all([s_s is not None, s_c is not None, s_d is not None]):
        print("a seal failed; aborting"); return 1
    print("sealed 3D super", s_s, "| 2D crit", s_c, "| dispersion", s_d)
    sid = TS.create("Navier-Stokes - dissonance and dispersion",
                    statement=("Do smooth solutions of the 3D incompressible Navier-Stokes equations exist "
                               "for all time, or can they blow up in finite time? Under the scaling symmetry "
                               "the kinetic energy scales as lambda^(d-2): supercritical in 3D (+1), critical "
                               "in 2D (0). Dispersion and viscous dissipation spread and damp energy; the "
                               "nonlinear term cascades it toward small scales. The open question is whether "
                               "dissipation always wins in 3D."),
                    field="meta",
                    references=["the Clay Millennium problem: 3D global existence and smoothness",
                                "Leray-Hopf weak solutions (1934); 2D global regularity (Ladyzhenskaya)",
                                "Caffarelli-Kohn-Nirenberg (1982): singular set has parabolic dimension <= 1"])["id"]
    marks = [
        ("witness", f"[why 3D is almost the counter - supercritical scaling] Under u_lambda(x,t) = lambda "
                    f"u(lambda x, lambda^2 t) the energy integral of |u|^2 scales as lambda^(d-2); in 3D that "
                    f"exponent is 3 - 2 = {int(super3d)} (sealed) > 0, so the conserved energy does NOT control "
                    f"the small scales where a singularity would form. That gap is the room a finite-time "
                    f"blow-up could hide in - the one place the narrowing method might meet a genuine "
                    f"singularity instead of a sealed answer.", s_s),
        ("witness", f"[why 2D is proven - critical scaling] In 2D the exponent is 2 - 2 = {int(crit2d)} "
                    f"(sealed): the energy is scale-INVARIANT, the a-priori bound controls every scale, and "
                    f"global smoothness is a THEOREM. The method narrows cleanly exactly when the controlled "
                    f"quantity is critical or subcritical; 3D sits just past that line.", s_c),
        ("witness", f"[dispersion vs concentration] A dispersive wave spreads: for omega ~ k^2 the group "
                    f"velocity is twice the phase velocity, 2k/k = {disp:.0f} (sealed), so frequency components "
                    f"separate and the amplitude decays. Dispersion and viscous dissipation oppose the "
                    f"nonlinear cascade that would concentrate energy into a 'dissonant' singularity; whether "
                    f"they always prevail in 3D is the open question.", s_d),
        ("note", "[the honest marks] 3D global existence + smoothness is OPEN (Clay Millennium). Proven: 2D "
                 "global regularity; Leray-Hopf weak solutions exist in 3D (uniqueness/smoothness unknown); "
                 "Caffarelli-Kohn-Nirenberg - the singular set of a suitable weak solution has parabolic "
                 "Hausdorff dimension at most 1. The engine seals the scaling arithmetic and the dispersion "
                 "relation, cites the theorems, and marks 3D smoothness as the one unfired mark. 'Almost the "
                 "counter' is held honestly: the narrowing might meet a singularity, not a proof. map, never "
                 "launder (ties [[feedback_mapping_the_truth_not_generating_it_2026-10-07]])."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Navier-Stokes, 2026-10-07")


def yang_mills() -> int:
    """YANG-MILLS MASS GAP IS A MEASURE (Matt, 2026-10-07). The mass gap Delta is the distance from the
    vacuum to the first excited state - a gap in the spectrum of a self-adjoint Hamiltonian, a measured
    positive number. It sets the measurable RANGE of the force (Yukawa, 1/Delta) and is underwritten by the
    PROVEN asymptotic freedom of QCD. Constructing the theory and proving Delta > 0 is open (Millennium).
    Seal the spectral difference, the Yukawa range, and the beta-function sign. New stick; idempotent."""
    from concordance import tickstick as TS
    gap = 1.73 - 0                       # Delta = E1 - E0; lightest glueball ~1.73 GeV (lattice) - vacuum 0
    yukawa = 197.3269804 / 139.57        # hbar c / m_pi c^2 = nuclear-force range in fm from the pion mass
    beta0 = 11 - (2.0 / 3) * 6          # one-loop QCD beta coefficient for 6 flavors -> 7 > 0 (asympt. free)
    s_g = _rh_seal_num("ym_mass_gap_spectral", "1.73 - 0", float(gap), tol=1e-9)
    s_y = _rh_seal_num("ym_yukawa_range_fm", "197.3269804 / 139.57", float(yukawa), tol=1e-9)
    s_b = _rh_seal_num("ym_qcd_beta0_nf6", "11 - (2.0 / 3) * 6", float(beta0), tol=1e-9)
    if not all([s_g, s_y, s_b]):
        print("a seal failed; aborting"); return 1
    print("sealed gap", s_g, "| yukawa", s_y, "| beta0", s_b)
    sid = TS.create("Yang-Mills - the mass gap is a measure",
                    statement=("For a compact simple gauge group, does a quantum Yang-Mills theory exist on "
                               "R^4 with a mass gap Delta > 0 - a strictly positive lightest excitation above "
                               "the vacuum? The gap is a measured spectral quantity: it fixes the range of the "
                               "force and explains why the strong interaction is short-range while the massless "
                               "photon's reach is infinite."),
                    field="meta",
                    references=["the Clay Millennium problem: Yang-Mills existence and mass gap",
                                "Yukawa (1935): range = hbar c / (m c^2); asymptotic freedom (GWP 1973)",
                                "lattice QCD glueball spectra; the gap as E1 - E0"])["id"]
    marks = [
        ("witness", f"[the gap IS a measured spectral difference] A mass gap is the distance from the vacuum "
                    f"(energy 0) to the first excited state: Delta = E1 - E0. On the lattice the lightest "
                    f"glueball sits near 1.73 GeV, so Delta = 1.73 - 0 = {gap:.2f} GeV (sealed) - a measured "
                    f"number, exactly as you said: the mass gap is a measure.", s_g),
        ("witness", f"[the gap sets a measurable range] A massive mediator gives a Yukawa force of range "
                    f"hbar c / (m c^2). For the pion (139.57 MeV): 197.327 MeV*fm / 139.57 MeV = {yukawa:.4f} "
                    f"fm (sealed) - the measured ~1.4 fm range of the nuclear force, Yukawa's 1935 prediction. "
                    f"Delta > 0 is why the strong force is short-range, unlike the massless photon.", s_y),
        ("witness", f"[why a gap is plausible - asymptotic freedom, proven] The one-loop QCD beta coefficient "
                    f"is b0 = 11 - (2/3) n_f; for 6 flavors b0 = 11 - 4 = {beta0:.0f} (sealed) > 0, so the "
                    f"coupling grows at long distance (Gross-Wilczek-Politzer 1973, Nobel 2004). That proven "
                    f"sign is what makes confinement and a positive gap expected.", s_b),
        ("note", "[the open mark] Yang-Mills existence AND a mass gap on R^4 for a compact simple gauge group "
                 "is OPEN (Clay Millennium). Proven/measured: asymptotic freedom; lattice glueball spectra; the "
                 "gap computed numerically on the lattice. The engine seals the measured range, the spectral "
                 "difference, and the beta sign; it does NOT construct the theory or prove Delta > 0. The mass "
                 "gap is a gap in the spectrum of a self-adjoint Hamiltonian - the same structure as "
                 "stick_the_hilbert_polya_conjecture. map, never launder."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Yang-Mills mass gap, 2026-10-07")


def entropy_gravity() -> int:
    """ENTROPY AND GRAVITY (Matt, 2026-10-07). A black hole is a thermodynamic object: its entropy is a
    quarter of its horizon AREA (not volume - the holographic clue), and its Hawking temperature is built
    from hbar, c, G and k_B at once. Jacobson derived Einstein's equations from delta Q = T dS - gravity as
    thermodynamics. Seal the area-law coefficient, the Schwarzschild horizon, and the Hawking temperature;
    hold 'gravity IS entropy' as a cited likeness, never a fit. New stick; idempotent."""
    from concordance import tickstick as TS
    quarter = 1.0 / 4                                                   # S = A / (4 l_P^2): the 1/4
    rs = 2 * 6.6743e-11 * 1.989e30 / (299792458 ** 2)                  # Schwarzschild radius of the Sun (m)
    T_hawking = (1.054571817e-34 * (299792458) ** 3) / (
        8 * 3.141592653589793 * 6.6743e-11 * 1.989e30 * 1.380649e-23)   # Hawking temp of 1 solar mass (K)
    s_q = _rh_seal_num("eg_area_law_quarter", "1.0 / 4", float(quarter), tol=1e-12)
    s_r = _rh_seal_num("eg_schwarzschild_sun_m",
                       "2 * 6.6743e-11 * 1.989e30 / (299792458 ** 2)", float(rs), tol=1e-9)
    s_t = _rh_seal_num("eg_hawking_temp_sun_K",
                       "(1.054571817e-34 * (299792458) ** 3) / (8 * 3.141592653589793 * 6.6743e-11 * 1.989e30 * 1.380649e-23)",
                       float(T_hawking), tol=1e-9)
    if not all([s_q, s_r, s_t]):
        print("a seal failed; aborting"); return 1
    print("sealed 1/4", s_q, "| r_s", s_r, "| T_hawking", s_t)
    sid = TS.create("Entropy and gravity",
                    statement=("A black hole carries entropy equal to a quarter of its horizon area in Planck "
                               "units (S = A/4), and a Hawking temperature T = hbar c^3 / (8 pi G M k_B). "
                               "Entropy scaling with AREA rather than volume is the holographic clue; the "
                               "temperature joins quantum theory, relativity, gravity and thermodynamics in "
                               "one quantity. Einstein's equations can be derived from delta Q = T dS."),
                    field="meta",
                    references=["Bekenstein-Hawking entropy S = A / (4 l_P^2)",
                                "Hawking temperature T = hbar c^3 / (8 pi G M k_B)",
                                "Jacobson (1995): Einstein equations from thermodynamics; entropic gravity"])["id"]
    marks = [
        ("witness", f"[entropy lives on the AREA, not the volume] Bekenstein-Hawking: a black hole's entropy "
                    f"is a quarter of its horizon area in Planck units, S = A / (4 l_P^2) - the coefficient is "
                    f"1/4 = {quarter} (sealed). Entropy scaling with AREA, not volume, is the holographic clue: "
                    f"the information sits on the boundary.", s_q),
        ("witness", f"[the horizon that carries it] The Schwarzschild radius r_s = 2 G M / c^2; for one solar "
                    f"mass that is {rs:.1f} m (sealed) ~ 2.95 km. The entropy is this sphere's area over four - "
                    f"gravity written as information on a surface.", s_r),
        ("witness", f"[quantum + gravity + thermodynamics in one number] The Hawking temperature "
                    f"T = hbar c^3 / (8 pi G M k_B); for one solar mass it is {T_hawking:.3e} K (sealed) - built "
                    f"from hbar (quantum), c (relativity), G (gravity) and k_B (thermodynamics) at once. A black "
                    f"hole is a thermodynamic object; that is the bridge between entropy and gravity.", s_t),
        ("note", "[the claim, held as a likeness] Jacobson (1995) DERIVED Einstein's equations from delta Q = "
                 "T dS applied to local horizons - gravity as an equation of state; Verlinde and others push "
                 "'entropic / emergent gravity.' The engine seals the thermodynamic arithmetic (area law, "
                 "horizon, Hawking temperature) and CITES these results; it does NOT claim gravity IS entropy - "
                 "that is a hypothesis and a likeness, the outline of a unification not yet sealed. Ties the "
                 "emergent-structure thread (stick_time_and_space_emergent_and_relational). map, never launder."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - entropy and gravity, 2026-10-07")


def standard_model() -> int:
    """THE STANDARD-MODEL CHAIN - A PATH FROM A FLOOR, AND WHERE TWO TREES CONNECT (Matt, 2026-10-07:
    'Fermi, Yang, Lee, Wu, Higgs, Nambu, Weinberg, Salam, Gross, Politzer, Gell-Mann ... chains that began
    with a floor ... we are very interested in where two trees/chains connect'). The lineage that built the
    Standard Model, each link on the last, from the floor of Maxwell's EM and Fermi's weak theory. The
    CONNECTION is electroweak unification: the electromagnetic chain (Maxwell -> QED) and the weak chain
    (Fermi -> parity -> gauge) become one theory, hinged on the Weinberg angle cos(theta_W) = m_W/m_Z. Seal
    that hinge; cite the chain and name the floor. New stick; idempotent."""
    from concordance import tickstick as TS
    cos_w = 80.377 / 91.1876                 # cos(theta_W) = m_W / m_Z : the hinge joining the two trees
    sin2_w = 1 - (80.377 / 91.1876) ** 2     # sin^2(theta_W), on-shell : the mixing/connection parameter
    s_c = _rh_seal_num("ew_cos_theta_w", "80.377 / 91.1876", float(cos_w), tol=1e-9)
    s_s = _rh_seal_num("ew_sin2_theta_w", "1 - (80.377 / 91.1876)**2", float(sin2_w), tol=1e-9)
    if not all([s_c, s_s]):
        print("a seal failed; aborting"); return 1
    print("sealed cos(theta_W)", s_c, "| sin^2(theta_W)", s_s)
    sid = TS.create("The Standard-Model chain - where two trees connect",
                    statement=("A chain of discovery that began from a floor: Maxwell's electromagnetism and "
                               "Fermi's weak theory. Its connection point is electroweak unification, where the "
                               "electromagnetic and weak chains become one theory, parameterized by a single "
                               "mixing angle with cos(theta_W) = m_W / m_Z. The photon and Z boson are "
                               "orthogonal rotations of the two gauge fields by that angle."),
                    field="meta",
                    references=["Fermi (1933) weak interaction; Yang-Mills (1954) non-abelian gauge",
                                "Lee-Yang (1956) & Wu (1957) parity violation; Nambu SSB; Higgs (1964)",
                                "Glashow-Weinberg-Salam electroweak unification (1967, Nobel 1979)",
                                "Gell-Mann (quarks); Gross-Politzer-Wilczek asymptotic freedom (1973, Nobel 2004)"])["id"]
    marks = [
        ("witness", f"[the connection, sealed] The Weinberg angle is where the electromagnetic and weak trees "
                    f"join: cos(theta_W) = m_W / m_Z = 80.377 / 91.1876 = {cos_w:.6f} (sealed). The massive W "
                    f"(weak) and the Z and photon (weak + EM mixtures) all relate through this one angle - two "
                    f"chains, one hinge.", s_c),
        ("witness", f"[the mixing parameter] sin^2(theta_W) = 1 - (m_W/m_Z)^2 = {sin2_w:.6f} (sealed, on-shell) "
                    f"- the single number saying how much the weak and electromagnetic couplings mix. The "
                    f"photon and Z are orthogonal rotations of the two gauge fields by theta_W; the connection "
                    f"is quantitative, not metaphor.", s_s),
        ("note", "[the floor of the path] Maxwell's electromagnetism (the EM tree's floor) and Fermi's 1933 "
                 "theory of beta decay (the weak tree's floor), both standing on quantum mechanics and special "
                 "relativity. A chain begins from a floor; naming the floor is the first act of establishing "
                 "the path (ties the Floor of Discovery, card_k_floor_of_discovery)."),
        ("note", "[the chain, link by link] Fermi (weak interaction, 1933) -> Yang-Mills (non-abelian gauge, "
                 "1954) -> Lee & Yang (parity violation predicted, 1956) -> Wu (confirmed, 1957) -> Nambu "
                 "(spontaneous symmetry breaking) -> Higgs (the mass mechanism, 1964) -> Glashow-Weinberg-Salam "
                 "(electroweak unification, 1967) -> Gell-Mann (quarks) + Gross-Politzer-Wilczek (asymptotic "
                 "freedom / QCD, 1973). The individual marks are already sealed on this engine "
                 "(stick_the_four_forces_under_the_fine_structure_constant, stick_yang_mills_the_mass_gap_is_a_"
                 "measure, and kin); this stick GATHERS them into their lineage - the same paths, seen whole."),
        ("note", "[where two trees connect - the pattern] 'We are very interested in where two trees/chains "
                 "connect.' Here it is exact: electroweak unification is the node where the electromagnetic "
                 "chain (Maxwell -> QED) and the weak chain (Fermi -> parity -> gauge) become one theory, "
                 "hinged on the sealed Weinberg angle. A chain begins from a floor; the profound moments are "
                 "the CONNECTIONS where two chains meet. This is the physics instance of the two trees and the "
                 "appointed assembly of scattered pieces ([[project_babel_scattered_pieces_appointed_assembly_"
                 "2026-08-01]], [[project_two_trees_named_2026-06-12]]). map, never launder: the engine seals "
                 "the connection's arithmetic and cites the lineage; it does not claim to have unified anything "
                 "- it FINDS the join the physicists made."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the Standard-Model chain, 2026-10-07")


def bombelli() -> int:
    """COMPLEX NUMBERS / BOMBELLI / -1 (Matt, 2026-10-07). Rafael Bombelli (L'Algebra, 1572) legitimized
    sqrt(-1) because it WORKED: Cardano's formula for x^3 = 15x + 4 reaches the REAL root 4 only through
    sqrt(-121), and Bombelli saw that 2 + sqrt(-121) = (2+i)^3, so the imaginary parts cancel and the real
    answer survives. i = sqrt(-1) entered mathematics as a necessary tool, not a mysticism. Complex numbers
    are the FLOOR under this whole arc (e^(i*theta), roots of unity, the critical line 1/2 + i*gamma,
    self-adjoint<->unitary, QM). Seal the real root + the (2+i)^3 expansion; chain the floor. New stick."""
    from concordance import tickstick as TS
    root_check = 4 ** 3 - 15 * 4 - 4      # x=4 solves x^3 = 15x + 4  ->  0
    re3 = 2 ** 3 - 3 * 2 * 1 ** 2         # Re((2+i)^3) = a^3 - 3ab^2 = 2
    im3 = 3 * 2 ** 2 * 1 - 1 ** 3         # Im((2+i)^3) = 3a^2 b - b^3 = 11
    s_r = _rh_seal_num("bombelli_real_root", "4**3 - 15*4 - 4", float(root_check))
    s_re = _rh_seal_num("bombelli_cube_real_part", "2**3 - 3*2*1**2", float(re3))
    s_im = _rh_seal_num("bombelli_cube_imag_part", "3*2**2*1 - 1**3", float(im3))
    if not all([s_r is not None, s_re, s_im]):
        print("a seal failed; aborting"); return 1
    print("sealed real-root", s_r, "| Re(2+i)^3", s_re, "| Im(2+i)^3", s_im)
    sid = TS.create("Complex numbers - Bombelli and the square root of minus one",
                    statement=("The real cubic x^3 = 15x + 4 has the real root 4, but Cardano's formula "
                               "reaches it only through sqrt(-121). Bombelli (1572) saw that 2 + sqrt(-121) = "
                               "(2+i)^3 and 2 - sqrt(-121) = (2-i)^3, so the sum (2+i)+(2-i) = 4: the imaginary "
                               "parts cancel and the real answer survives. sqrt(-1) is the necessary road to a "
                               "real truth, which is why it was kept."),
                    field="mathematics",
                    references=["R. Bombelli, L'Algebra (1572) - rules for +/- sqrt(-1) ('piu di meno')",
                                "Cardano's casus irreducibilis: real roots reached through complex intermediates",
                                "(a+bi)^3 = (a^3 - 3ab^2) + (3a^2 b - b^3) i"])["id"]
    marks = [
        ("witness", f"[the real root, sealed] x = 4 solves x^3 = 15x + 4: 4^3 - 15*4 - 4 = {int(root_check)} "
                    f"(sealed). A plain real root - no imaginaries in the question or the answer.", s_r),
        ("witness", f"[reached only through sqrt(-1) - Bombelli's insight] Cardano gives this root as "
                    f"cbrt(2 + sqrt(-121)) + cbrt(2 - sqrt(-121)). Bombelli saw 2 + sqrt(-121) = (2+i)^3, "
                    f"whose real part is 2^3 - 3*2*1^2 = {int(re3)} (sealed) and whose imaginary part is "
                    f"3*2^2*1 - 1^3 = {int(im3)} (sealed) - i.e. (2+i)^3 = 2 + 11i = 2 + sqrt(-121). So "
                    f"x = (2+i) + (2-i) = 4: the imaginary parts cancel, the real root emerges. The sqrt(-1) is "
                    f"not optional - it is the only road to the real answer.", s_re),
        ("witness", f"[the imaginary part carries the cancellation] Im((2+i)^3) = {int(im3)} (sealed) = +sqrt(121), "
                    f"and Im((2-i)^3) = -11; they are equal and opposite, so they vanish in the sum while the "
                    f"real parts (2 and 2) add to 4. The imaginary unit does real work and then disappears.", s_im),
        ("note", "[what Bombelli did] L'Algebra (1572): the first systematic rules for +/- sqrt(-1), "
                 "legitimizing imaginary numbers because they WORKED - delivering real solutions to real cubics "
                 "no real-only method could reach. i = sqrt(-1) entered mathematics as a necessary tool, not a "
                 "mysticism (Leibniz later called it 'that amphibian between being and non-being'). It is a "
                 "construct we created because reality's answers demanded it (ties stick_construct_creation)."),
        ("note", "[the FLOOR of the whole arc - a chain that began with a floor] Complex numbers are the floor "
                 "under this session's arc: e^(i*theta) (Euler), the roots of unity on the unit circle "
                 "(stick_dirichlet_s_theorem_think_of_polar_coordinates, stick_fibonacci), the critical line "
                 "1/2 + i*gamma (stick_the_zeta_function), self-adjoint <-> unitary via the Cayley/Smith "
                 "transform (stick_the_smith_chart_the_cayley_transform), and the complex amplitudes of quantum "
                 "mechanics (stick_the_standard_model_chain_where_two_trees_connect). Bombelli (1572) is the "
                 "ROOT of that chain: Bombelli -> Euler -> Gauss (the complex plane) -> Riemann (complex "
                 "analysis). A chain that began with a floor, and -1, through its square root, is where it "
                 "starts (ties [[project_chains_from_a_floor_where_two_trees_connect_2026-10-07]]). map, never "
                 "launder: the engine seals the real arithmetic that sqrt(-1) makes reachable."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - complex numbers / Bombelli, 2026-10-07")


def calculus() -> int:
    """INTEGRALS AND DERIVATIVES (Matt, 2026-10-07). The Fundamental Theorem of Calculus: differentiation
    and integration are INVERSE operations. The integral of a derivative over [a,b] is the net change
    f(b) - f(a); the derivative of the area function gives back the integrand. Newton and Leibniz,
    independently (1660s-80s). A floor under the whole arc (Maxwell's equations differential, least action
    an integral, Schrodinger a PDE). Seal an FTC instance, a power-rule area, and the derivative as a
    limiting slope; mark the inverse symmetry + the notation construct. New stick; idempotent."""
    from concordance import tickstick as TS
    ftc = 3 ** 2 - 1 ** 2                       # integral of 2x on [1,3] = F(3)-F(1) with F=x^2 -> 8
    area = 2 ** 3 / 3                           # integral of x^2 on [0,2] = [x^3/3] = 8/3
    slope = ((3.001) ** 2 - 3 ** 2) / 0.001     # difference quotient of x^2 at 3 -> 6.001 -> f'(3)=6
    s_f = _rh_seal_num("ftc_net_change", "3**2 - 1**2", float(ftc))
    s_a = _rh_seal_num("power_rule_area", "2**3 / 3", float(area), tol=1e-12)
    s_s = _rh_seal_num("derivative_limiting_slope", "((3.001)**2 - 3**2) / 0.001", float(slope), tol=1e-9)
    if not all([s_f, s_a, s_s]):
        print("a seal failed; aborting"); return 1
    print("sealed FTC", s_f, "| area", s_a, "| slope", s_s)
    sid = TS.create("Integrals and derivatives - the fundamental theorem",
                    statement=("Differentiation and integration are inverse operations. For F' = f, the "
                               "integral of f over [a,b] equals F(b) - F(a) (the net change), and the "
                               "derivative of the area-so-far function returns the integrand. An area problem "
                               "becomes subtraction; a rate problem becomes a limiting slope."),
                    field="mathematics",
                    references=["the Fundamental Theorem of Calculus (Newton, Leibniz, 1660s-1680s)",
                                "power rule: integral of x^n = x^(n+1)/(n+1); d/dx x^n = n x^(n-1)",
                                "derivative as a limit: f'(x) = lim_{h->0} (f(x+h) - f(x))/h"])["id"]
    marks = [
        ("witness", f"[the fundamental theorem - the integral of a derivative is the net change] The integral "
                    f"of 2x over [1,3] is F(3) - F(1) with F(x) = x^2: 3^2 - 1^2 = {int(ftc)} (sealed). The area "
                    f"under a rate from a to b is exactly the total change f(b) - f(a) - integration undoes "
                    f"differentiation.", s_f),
        ("witness", f"[the power rule turns area into subtraction] The integral of x^2 over [0,2] is "
                    f"[x^3/3] from 0 to 2 = 2^3/3 = {area:.6f} (sealed) - the area under the parabola, found by "
                    f"REVERSING the derivative (d/dx of x^3/3 is x^2). The antiderivative is the inverse of the "
                    f"derivative.", s_a),
        ("witness", f"[the derivative as the limiting slope] For f(x) = x^2 at x = 3, the difference quotient "
                    f"(f(3.001) - f(3))/0.001 = {slope:.3f} (sealed), approaching 6 = f'(3) = 2x as the step "
                    f"shrinks. The derivative is the limit of the slope of the chord as it collapses to a "
                    f"point - the instantaneous rate.", s_s),
        ("note", "[the inverse is a symmetry; the notation is a construct] The derivative and the integral are "
                 "inverse - a symmetry (ties stick_the_symmetry). The notation is chosen, not given: Leibniz's "
                 "dy/dx and the integral sign (an elongated S for 'summa') won over Newton's fluxions because "
                 "the better construct made the inverse relationship visible on the page (ties "
                 "stick_construct_creation; the Leibniz-Newton priority dispute is the notation war)."),
        ("note", "[a floor under the whole arc] Calculus is foundational beneath this session's physics: "
                 "Maxwell's equations are differential, the principle of least action is an integral "
                 "(stick_the_principle_of_least_action), the Schrodinger equation is a partial differential "
                 "equation (stick_the_schrodinger_equation), and Navier-Stokes is a PDE whose smoothness is "
                 "open (stick_navier_stokes_dissonance_and_dispersion). Newton and Leibniz are a chain root "
                 "([[project_chains_from_a_floor_where_two_trees_connect_2026-10-07]]). map, never launder: "
                 "seal the arithmetic, attribute the theorem."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - integrals and derivatives, 2026-10-07")


def fourier() -> int:
    """MULTIPLICATION IS ROTATION / FREQUENCY IS TURN RATE / SPIN UNTIL IT UNRAVELS / TEST THE NOTE
    (Matt, 2026-10-07). Multiplying by a unit complex number e^(i*theta) is a pure rotation (adds the angle,
    keeps the length) - which is why i^2 = -1 (two 90-degree turns). A phasor e^(i*omega*t) is a vector
    turning at rate omega = 2*pi*f, so frequency is literally how fast the vector turns. The Fourier
    transform correlates a signal against those rotating phasors: spin at a frequency and it either
    ACCUMULATES (the note is present - 'it unravels') or CANCELS (absent). That binary is a testable,
    sealable operation - 'we can test the note.' Seal rotation, turn-rate, accumulate, cancel. New stick."""
    from concordance import tickstick as TS
    rot = 0.5 ** 2 + 0.8660254037844386 ** 2          # cos^2(60) + sin^2(60) = 1 : rotation preserves length
    omega = 2 * 3.141592653589793 * 440               # angular frequency of A4 (440 Hz): the turn rate
    accumulate = 1 + 1 + 1 + 1                         # matched probe: samples add (the note is present)
    cancel = 1 + 0 + (-1) + 0                          # mismatched probe: real parts of the 4th roots cancel
    s_rot = _rh_seal_num("mult_is_rotation", "0.5**2 + 0.8660254037844386**2", float(rot), tol=1e-9)
    s_om = _rh_seal_num("frequency_turn_rate", "2 * 3.141592653589793 * 440", float(omega), tol=1e-9)
    s_ac = _rh_seal_num("test_note_accumulates", "1 + 1 + 1 + 1", float(accumulate))
    s_ca = _rh_seal_num("test_note_cancels", "1 + 0 + (-1) + 0", float(cancel))
    constructive = 1 + 1                           # two in-phase unit waves: amplitudes add (interference)
    grow = 2.718281828459045 ** 0.5                # |e^(a+bi)| = e^a ; a=0.5 is the growth half of the spiral
    s_con = _rh_seal_num("addition_is_interference", "1 + 1", float(constructive))
    s_gr = _rh_seal_num("complex_exponential_growth", "2.718281828459045**0.5", float(grow), tol=1e-9)
    if not all([s_rot, s_om, s_ac is not None, s_ca is not None, s_con is not None, s_gr]):
        print("a seal failed; aborting"); return 1
    print("sealed rotation", s_rot, "| omega", s_om, "| accum", s_ac, "| cancel", s_ca,
          "| interfere", s_con, "| grow", s_gr)
    sid = TS.create("The complex field is the physics of waves",
                    statement=("In the complex field the two operations are the two wave physics: "
                               "MULTIPLICATION is rotation (e^(i*theta) adds the angle, keeps the length), "
                               "ADDITION is interference (phasors add as vectors - in phase reinforce, opposite "
                               "cancel), and the EXPONENTIAL of a complex number e^(a+bi) = e^a(cos b + i sin b) "
                               "is the spiral that joins growth to rotation. Frequency is how fast a vector "
                               "turns. The Fourier transform spins a signal against these phasors; a matched "
                               "note accumulates, an unmatched one cancels - so we can test the note."),
                    field="mathematics",
                    references=["complex multiplication: |z1 z2| = |z1||z2|, arg(z1 z2) = arg z1 + arg z2",
                                "the phasor e^(i*omega*t), omega = 2*pi*f; the Fourier/DFT correlation",
                                "orthogonality: sum of the N-th roots of unity = 0 (off-note cancels)"])["id"]
    marks = [
        ("witness", f"[multiplication is rotation] Multiplying by a unit complex number is a pure rotation - it "
                    f"adds the angle and keeps the length. Rotating (1,0) by 60 degrees lands on "
                    f"(cos60, sin60) = (0.5, 0.8660254), whose length^2 is 0.5^2 + 0.8660254^2 = {rot:.0f} "
                    f"(sealed). Times i rotates 90 degrees; times i again, 180 = -1 - which is WHY i^2 = -1 "
                    f"(stick_complex_numbers_bombelli_and_the_square_root_of_minus_one).", s_rot),
        ("witness", f"[frequency is how fast a vector turns] A phasor e^(i*omega*t) is a vector turning at "
                    f"angular rate omega = 2*pi*f. For the note A4 (440 Hz) it turns 2*pi*440 = {omega:.2f} "
                    f"radians per second (sealed). Frequency is not an abstraction - it is literally the "
                    f"turning rate of a rotating vector.", s_om),
        ("witness", f"[spin until it unravels - the matched note accumulates] To test a note, spin the data "
                    f"against that note's phasor and sum. If the frequency MATCHES, every sample points the "
                    f"same way and they ADD: a 4-sample matched correlation = 1+1+1+1 = {int(accumulate)} "
                    f"(sealed). The component stands still relative to the probe and accumulates - it unravels.", s_ac),
        ("witness", f"[or it cancels - the note is absent] If the frequency does NOT match, the samples point "
                    f"every which way and CANCEL: the real parts of a mismatched 4-sample correlation sum to "
                    f"1+0+(-1)+0 = {int(cancel)} (sealed). Accumulate or cancel - that binary is the test: WE "
                    f"CAN TEST THE NOTE. (Ties the roots-of-unity orthogonality of "
                    f"stick_dirichlet_s_theorem_think_of_polar_coordinates.)", s_ca),
        ("witness", f"[addition is interference] Phasors ADD as vectors: two in-phase unit waves reinforce, "
                    f"1 + 1 = {int(constructive)} (sealed, constructive), while opposite waves cancel, "
                    f"1 + (-1) = 0 (destructive). Addition is interference - the same reinforce/cancel that made "
                    f"the note-test accumulate to 4 or vanish to 0 above.", s_con),
        ("witness", f"[the exponential of a complex number - the spiral] e^(a+bi) = e^a (cos b + i sin b): the "
                    f"real part a is GROWTH (modulus e^a), the imaginary part b is ROTATION (angle b). For "
                    f"a = 0.5 the magnitude is e^0.5 = {grow:.6f} (sealed); the e^(ib) factor always has "
                    f"modulus 1 (pure rotation). This one object - the complex exponential, a spiral - unifies "
                    f"growth and oscillation; it is the phasor e^(i*omega*t), the Schrodinger wavefunction, the "
                    f"AC steady state, and Euler's e^(i*pi) + 1 = 0 (e, i, pi, 1, 0).", s_gr),
        ("note", "[what this is, and the ties] This is the Fourier transform: correlate a signal with rotating "
                 "phasors at every frequency; resonance (accumulation) reveals which frequencies are present - "
                 "spin until it unravels. It rests on complex multiplication as rotation (the floor, "
                 "stick_complex_numbers_bombelli_and_the_square_root_of_minus_one), the unit circle and roots "
                 "of unity (stick_the_smith_chart_the_cayley_transform), and it makes 'test the note' a "
                 "verifiable, sealable operation (spin -> accumulate = present / cancel = absent), tying the "
                 "temperament thread (the Pythagorean comma). map, never launder: the engine seals the "
                 "arithmetic of the test; it does not claim to hear."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Fourier / rotation / the note, 2026-10-07")


def linguistics() -> int:
    """MOST LINGUISTICS ARE MATH / OUTSIDE A SET VOCABULARY LIST (Matt, 2026-10-07). A fixed vocabulary is
    not the language: from a finite lexicon, grammar generates an unbounded space of sentences (generative
    combinatorics, Chomsky), and word statistics obey a power law (Zipf: frequency * rank = constant). Syntax
    is formal grammar, text has measurable entropy - most of linguistics is mathematical structure. This is
    why the engine's language layer is a COHERENT structural model, not a word list and not an LLM. Seal the
    generativity + Zipf. New stick; idempotent."""
    from concordance import tickstick as TS
    generative = 10 ** 5                 # 10 words -> 100,000 five-word strings : language exceeds the list
    zipf = 0.006 * 10                    # Zipf: frequency * rank = const ; rank-10 at 0.006 -> 0.06 = rank-1
    s_g = _rh_seal_num("language_is_generative", "10 ** 5", float(generative))
    s_z = _rh_seal_num("zipf_frequency_times_rank", "0.006 * 10", float(zipf), tol=1e-12)
    if not all([s_g, s_z]):
        print("a seal failed; aborting"); return 1
    print("sealed generative", s_g, "| zipf", s_z)
    sid = TS.create("Most linguistics are math - outside a set vocabulary list",
                    statement=("A fixed vocabulary is the floor, not the language. A finite lexicon plus a "
                               "grammar generates an unbounded space of sentences (generative combinatorics), "
                               "and word frequencies obey a power law (Zipf: frequency times rank is roughly "
                               "constant). Syntax is formal grammar, text has measurable entropy - the "
                               "structure of language is mathematical."),
                    field="linguistics",
                    references=["Chomsky: a finite grammar generates infinite sentences (recursion)",
                                "Zipf's law: the r-th most common word has frequency proportional to 1/r",
                                "Shannon: the entropy and redundancy of printed language"])["id"]
    marks = [
        ("witness", f"[outside a set vocabulary list - language is generative] The word list is not the "
                    f"language. From just 10 words the number of 5-word strings is 10^5 = {int(generative)} "
                    f"(sealed) - already four orders of magnitude past the list; with a 50,000-word lexicon and "
                    f"recursion the space is unbounded. A finite grammar generates infinite sentences "
                    f"(Chomsky). The vocabulary is the floor; the math is the building.", s_g),
        ("witness", f"[most linguistics are math - Zipf's law] Word frequencies follow a power law: the r-th "
                    f"most common word has frequency proportional to 1/r, so frequency * rank is constant - a "
                    f"rank-10 word at 0.006 gives 0.006 * 10 = {zipf} (sealed), the same constant as rank 1. "
                    f"Language statistics are a measurable law, not a list of exceptions.", s_z),
        ("note", "[the structure is mathematical] The Chomsky hierarchy (regular < context-free < "
                 "context-sensitive < recursively enumerable) makes syntax formal grammar; Shannon's "
                 "information theory measures the entropy and redundancy of text; phonology, morphology and "
                 "semantics all carry mathematical structure. Most of linguistics is math."),
        ("note", "[why the engine handles language by STRUCTURE, not a list] This is the ground for the "
                 "engine's language layer being a COHERENT model rather than a fixed vocabulary or an LLM's "
                 "statistics: the reader's tongue and the language cubes handle meaning by STRUCTURE (grammar, "
                 "relation, the keeping's graph), reaching beyond any set vocabulary. The dispatch of topics by "
                 "a fixed alias list is a convenience, not the understanding - the understanding is structural "
                 "(ties the coherent-language-model and tortoise-reader / language-cubes work). map, never "
                 "launder: seal the arithmetic of the law; the structure is found, not generated."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - linguistics is math, 2026-10-07")


def lebesgue() -> int:
    """LEBESGUE THEORY (Matt, 2026-10-07: 'We missed the Lebesgue Theory. Use it where you can.'). Measure
    theory assigns size to sets; Lebesgue integration partitions the RANGE (not the domain) and integrates by
    layers, so it integrates functions Riemann cannot (the Dirichlet function) and gives the 'almost
    everywhere' that underlies modern analysis. It is the proper home of Fourier (the L^2 space) and
    probability (a probability IS a measure of mass 1, expectation a Lebesgue integral). Seal the Dirichlet
    integral, the measure-zero cover, and probability-as-measure; map it onto the arc. New stick; idempotent."""
    from concordance import tickstick as TS
    dirichlet_int = 1 * 0 + 0 * 1                          # Lebesgue integral of 1_Q on [0,1]: 1*mu(Q)+0*mu(irr)=0
    cover = 0.5 + 0.25 + 0.125 + 0.0625 + 0.03125         # geometric cover sum eps*(1/2+1/4+...) -> eps
    prob = 3 / 6                                          # P(even) on a fair die = mu({2,4,6}) = 1/2
    s_d = _rh_seal_num("lebesgue_dirichlet_integral", "1*0 + 0*1", float(dirichlet_int))
    s_c = _rh_seal_num("measure_zero_cover", "0.5 + 0.25 + 0.125 + 0.0625 + 0.03125", float(cover), tol=1e-12)
    s_p = _rh_seal_num("probability_is_a_measure", "3 / 6", float(prob), tol=1e-12)
    if not all([s_d is not None, s_c, s_p]):
        print("a seal failed; aborting"); return 1
    print("sealed dirichlet", s_d, "| cover", s_c, "| prob", s_p)
    sid = TS.create("Lebesgue theory - measure, and integration by layers",
                    statement=("Lebesgue integration partitions the range of a function and weights each value "
                               "by the MEASURE of the set where the function takes it. This integrates "
                               "functions Riemann cannot, makes sense of 'almost everywhere' (a property that "
                               "holds except on a set of measure zero), and is the setting for Fourier analysis "
                               "(the L^2 space) and probability (a measure of total mass one)."),
                    field="mathematics",
                    references=["H. Lebesgue (1902): measure and the integral by layers",
                                "a countable set has measure zero; the Dirichlet function is Lebesgue-integrable",
                                "Kolmogorov: probability is a measure of mass 1; expectation = integral X dP"])["id"]
    marks = [
        ("witness", f"[Lebesgue integrates where Riemann fails - the Dirichlet function] Partition the RANGE, "
                    f"not the domain. For 1_Q on [0,1] (1 on rationals, 0 on irrationals) the Lebesgue integral "
                    f"is 1*mu(Q) + 0*mu(irrationals) = 1*0 + 0*1 = {int(dirichlet_int)} (sealed), because the "
                    f"rationals have measure ZERO. Riemann cannot integrate this at all - its upper and lower "
                    f"sums never meet. Measuring the SET where f takes each value succeeds where partitioning "
                    f"the domain fails.", s_d),
        ("witness", f"[a countable set has measure zero] Cover the n-th rational with an interval of length "
                    f"eps/2^n; the total is eps*(1/2 + 1/4 + 1/8 + ...) -> eps (the geometric sum reaches "
                    f"{cover} after five terms, sealed, climbing to 1). Since eps is arbitrary, the rationals - "
                    f"dense as they are - have measure zero. This is where 'almost everywhere' is born: a claim "
                    f"can hold except on a negligible set.", s_c),
        ("witness", f"[probability IS a measure] A probability is a measure of total mass 1 (Kolmogorov). For a "
                    f"fair die, P(even) = mu({{2,4,6}}) = 3/6 = {prob} (sealed), and expectation is the Lebesgue "
                    f"integral of X dP. This is exactly why Monte Carlo (stick_monte_carlo) estimates an "
                    f"integral and why the law of large numbers is a theorem about a measure.", s_p),
        ("note", "[use it where it fits - the arc] Lebesgue theory, with its Monotone and Dominated Convergence "
                 "theorems (swap a limit and an integral - the backbone no Riemann integral provides), is the "
                 "proper home of: FOURIER (the L^2 space, where the transform is an isometry - Parseval: energy "
                 "in time = energy in frequency - stick_the_complex_field_is_the_physics_of_waves); PROBABILITY "
                 "and Monte Carlo (stick_monte_carlo); the 'almost everywhere' behind the Navier-Stokes "
                 "partial-regularity result (the singular set has Hausdorff dimension <= 1, a measure-small "
                 "statement - stick_navier_stokes_dissonance_and_dispersion); and the Hausdorff dimension of a "
                 "fractal (stick_the_mandelbrot_set). It also completes the calculus floor "
                 "(stick_integrals_and_derivatives_the_fundamental_theorem)."),
        ("note", "[map, never launder] 'Use it where you can': the engine already leans on measure-theoretic "
                 "ideas - the Monte Carlo error bar is a statement about a probability measure, and the "
                 "tick-stick's honest refusal is a kind of 'holds almost everywhere, with the exceptional set "
                 "marked.' We seal the canonical arithmetic (the Dirichlet integral, the measure-zero cover, "
                 "probability as a measure) and map the concept onto the arc; we do not claim to have built a "
                 "measure-theoretic engine. map, never launder."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Lebesgue theory, 2026-10-07")


def vector_calculus() -> int:
    """DIVERGENCE AND CURL, THEN INVERSE TO FIND THE CENTER (Matt, 2026-10-07). Divergence measures the net
    OUTFLOW at a point (a source where positive, a sink where negative); curl measures CIRCULATION (the axis
    of a vortex). Knowing a field's divergence and curl, you INVERT (the Helmholtz decomposition / solving
    Poisson equations, or Gauss's divergence theorem on a boundary) to reconstruct the field and locate its
    center - the source or the rotation axis. This IS Maxwell's equations and Navier-Stokes vorticity. Seal
    div, curl, and the boundary-to-source inversion. New stick; idempotent."""
    from concordance import tickstick as TS
    div = 1 + 1 + 1                                 # div of F=(x,y,z): dx/dx+dy/dy+dz/dz = 3 (uniform source)
    curl_z = 1 - (-1)                               # z-curl of F=(-y,x): dFy/dx - dFx/dy = 1-(-1) = 2 (vorticity)
    flux = 4 * 3.141592653589793                    # Gauss: flux of the radial unit field out of a unit sphere = 4pi
    s_dv = _rh_seal_num("divergence_source", "1 + 1 + 1", float(div))
    s_cl = _rh_seal_num("curl_rotation", "1 - (-1)", float(curl_z))
    s_fx = _rh_seal_num("divergence_theorem_flux", "4 * 3.141592653589793", float(flux), tol=1e-9)
    if not all([s_dv, s_cl, s_fx]):
        print("a seal failed; aborting"); return 1
    print("sealed div", s_dv, "| curl", s_cl, "| flux", s_fx)
    sid = TS.create("Divergence and curl - invert to find the center",
                    statement=("Divergence measures the net outflow at a point (a source if positive, a sink if "
                               "negative); curl measures circulation (the axis of a vortex). A field is "
                               "reconstructed from its divergence and curl (Helmholtz), and the divergence "
                               "theorem turns a measurement on a boundary into the source enclosed - so mapping "
                               "the field lets you invert to its center."),
                    field="mathematics",
                    references=["the Helmholtz decomposition: F = -grad(phi) + curl(A)",
                                "Gauss's divergence theorem: flux through a closed surface = integral of div",
                                "Maxwell: div E = rho/eps0 (the source); Navier-Stokes: vorticity = curl of v"])["id"]
    marks = [
        ("witness", f"[divergence finds the source] The divergence is the net outflow at a point. For the "
                    f"radial field F = (x, y, z), div F = dx/dx + dy/dy + dz/dz = 1+1+1 = {int(div)} (sealed): a "
                    f"uniform source, the field streaming outward from a center. Positive divergence marks a "
                    f"source, negative a sink.", s_dv),
        ("witness", f"[curl finds the rotation] The curl is circulation. For the rotation field F = (-y, x, 0), "
                    f"the z-component of the curl is dFy/dx - dFx/dy = 1 - (-1) = {int(curl_z)} (sealed): the "
                    f"vorticity, twice the angular velocity. Its axis is the center of the vortex.", s_cl),
        ("witness", f"[invert to find the center - the divergence theorem] Gauss: the flux of a field out "
                    f"through a closed surface equals the divergence (the source) enclosed. For the radial unit "
                    f"field through the unit sphere the flux is 4*pi = {flux:.4f} (sealed). So a measurement on "
                    f"the BOUNDARY inverts to the SOURCE inside - you find the center from the outflow. "
                    f"(Helmholtz: reconstruct the whole field from its div and curl by solving Poisson "
                    f"equations; the centers are where div and curl concentrate.)", s_fx),
        ("note", "[where it lives in the arc] Divergence and curl ARE Maxwell's equations "
                 "(stick_maxwell_s_equations_and_superconductivity: div E = rho/eps0 locates the charge - the "
                 "source; div B = 0, no monopoles; curl E and curl B the circulation) and Navier-Stokes "
                 "(vorticity = curl of the velocity, div v = 0 for incompressible flow - "
                 "stick_navier_stokes_dissonance_and_dispersion). 'Map the field, then invert to find the "
                 "center' is the engine's triangulation move written in vector calculus: measure the effects "
                 "(div, curl) on the boundary, invert to the cause (the center). map, never launder: seal the "
                 "arithmetic; the center is FOUND by inversion, not posited."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - divergence, curl, and the center, 2026-10-07")


def legendre() -> int:
    """THE LEGENDRE TRANSFORM - OUR MECHANISM (Matt, 2026-10-07: 'mark the points and use it to create the
    line ... tangent lines / y-intercepts'). A convex curve is the ENVELOPE of its tangent lines; each
    tangent is a (slope, y-intercept) pair, and the Legendre transform re-encodes the curve as MINUS the
    y-intercept as a function of slope: f*(p) = sup_x(p x - f(x)). Mark the points, read each tangent's slope
    and intercept, and the lines build the curve. This is the engine's mechanism (marks -> the law by convex
    duality), and in physics the Lagrangian<->Hamiltonian and thermodynamic-potential bridge. Seal it on
    f(x)=x^2. New stick; idempotent."""
    from concordance import tickstick as TS
    touch = 6 * 3 - 9              # tangent to x^2 at a=3 is y=6x-9; at x=3 -> 9 = f(3) (the line touches the point)
    star6 = 6 ** 2 / 4            # f*(p=6) for f=x^2 is p^2/4 = 9 = -(y-intercept -9) of the slope-6 tangent
    star4 = 4 ** 2 / 4            # a second point a=2: slope 4, intercept -4, f*(4) = 4 = -intercept
    s_t = _rh_seal_num("legendre_tangent_touches", "6*3 - 9", float(touch))
    s_6 = _rh_seal_num("legendre_intercept_is_transform", "6**2 / 4", float(star6), tol=1e-12)
    s_4 = _rh_seal_num("legendre_second_point", "4**2 / 4", float(star4), tol=1e-12)
    if not all([s_t, s_6, s_4]):
        print("a seal failed; aborting"); return 1
    print("sealed touch", s_t, "| f*(6)", s_6, "| f*(4)", s_4)
    sid = TS.create("The Legendre transform - mark the points, create the line",
                    statement=("A convex function is the upper envelope of its tangent lines. Each tangent is a "
                               "(slope, y-intercept) pair, and the Legendre transform re-encodes the function "
                               "as minus the y-intercept as a function of slope: f*(p) = sup_x (p x - f(x)). "
                               "The curve and its tangent-line description are the same information in two "
                               "languages; the transform is an involution (f** = f)."),
                    field="mathematics",
                    references=["the Legendre transform f*(p) = sup_x (p x - f(x)); a convex involution",
                                "the tangent at a: y = f'(a) x + (f(a) - f'(a) a); y-intercept = -f*(f'(a))",
                                "physics: Lagrangian<->Hamiltonian (H = p q' - L); thermodynamic potentials"])["id"]
    marks = [
        ("witness", f"[mark a point -> a tangent line] For f(x) = x^2, the tangent at the marked point a = 3 is "
                    f"y = 6x - 9 (slope 2a = 6, y-intercept -a^2 = -9); at x = 3 it gives 6*3 - 9 = {int(touch)} "
                    f"= f(3) - the line TOUCHES the point. Every point of a convex curve hands you one tangent "
                    f"line.", s_t),
        ("witness", f"[the y-intercept carries the transform] That tangent has slope p = 6 and y-intercept -9, "
                    f"and the Legendre transform is exactly MINUS that intercept: f*(6) = 6^2/4 = {int(star6)} = "
                    f"-(y-intercept) (sealed). So re-encoding the curve by the (slope, y-intercept) of its "
                    f"tangent lines IS the Legendre transform - read the tangent's slope and intercept and you "
                    f"have the dual.", s_6),
        ("witness", f"[a second point, and the envelope builds the curve] At a = 2: slope 4, y-intercept -4, "
                    f"f*(4) = 4^2/4 = {int(star4)} = -(intercept) (sealed); the tangent y = 4x - 4 touches "
                    f"f(2) = 4. Collect every (slope, intercept) and the curve returns as the upper envelope of "
                    f"all its tangent lines: f(x) = sup_p (p x - f*(p)). Mark the points, the tangent lines "
                    f"create the line.", s_4),
        ("note", "[this IS the engine's mechanism] 'The Legendre transform gives us our mechanism.' The "
                 "tick-stick marks POINTS (sealed facts); the law/curve/narrow path is the ENVELOPE of those "
                 "marks' supporting lines - found by convex duality, not posited. It is the convex-geometry kin "
                 "of the positive Grassmannian ('the core': valid = the canonical form of positivity / "
                 "admissibility - stick_the_positive_grassmannian) and of 'a fit that never passes the last "
                 "mark' (the envelope rests on the marks). In physics it is the Lagrangian<->Hamiltonian bridge "
                 "(H = p q' - L; p = dL/dq' - stick_the_principle_of_least_action) and the thermodynamic "
                 "potentials (U <-> F = U - TS <-> enthalpy, swapping conjugate variables S<->T, V<->P - "
                 "stick_entropy_and_gravity). map, never launder: seal the arithmetic; the line is BUILT from "
                 "the marked points by the transform, found not invented."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the Legendre transform, 2026-10-07")


def euclid() -> int:
    """WE FOLLOW EUCLID'S ELEMENTS - DEFINITIONS, POSTULATES, THEOREMS (Matt, 2026-10-07). Euclid's method is
    the engine's method: DEFINITIONS (what the terms mean), POSTULATES (self-evident starting truths, accepted
    not proved - the floor), then THEOREMS, each DEDUCED from the definitions, the postulates, and prior
    theorems, ending in QED. Euclid SEALS theorems (proves them) but ACCEPTS postulates - the same line the
    engine draws between sealing a derivation and citing a foundation (Scripture, the Floor). Seal two
    theorems (I.32 angle sum, I.47 Pythagoras); hold the definitions/postulates as the given floor. New
    stick; idempotent."""
    from concordance import tickstick as TS
    angle = 60 + 60 + 60             # Euclid I.32: the angles of a triangle sum to two right angles = 180
    pyth = 5 ** 2 + 12 ** 2          # Euclid I.47 (Pythagoras): 5^2 + 12^2 = 169 = 13^2
    s_a = _rh_seal_num("euclid_angle_sum_I32", "60 + 60 + 60", float(angle))
    s_p = _rh_seal_num("euclid_pythagoras_I47", "5**2 + 12**2", float(pyth))
    if not all([s_a, s_p]):
        print("a seal failed; aborting"); return 1
    print("sealed angle-sum", s_a, "| pythagoras", s_p)
    sid = TS.create("We follow Euclid's Elements - definitions, postulates, theorems",
                    statement=("Euclid builds geometry from definitions (what the terms mean), postulates "
                               "(self-evident starting truths, accepted without proof), and common notions, "
                               "then proves every theorem by deduction from those and from prior theorems, "
                               "ending in QED. The postulates are the floor; the theorems are the chain built "
                               "on it. A theorem is proved; a postulate is accepted."),
                    field="mathematics",
                    references=["Euclid, Elements Book I: 23 definitions, 5 postulates, 5 common notions, 48 propositions",
                                "I.32 (angles of a triangle = two right angles); I.47 (the Pythagorean theorem)",
                                "the 5th (parallel) postulate - vary it and you get consistent non-Euclidean geometry"])["id"]
    marks = [
        ("witness", f"[a THEOREM, sealed - the angle sum (I.32)] The angles of any triangle sum to two right "
                    f"angles; for the equilateral case 60 + 60 + 60 = {int(angle)} (sealed). Euclid PROVES this "
                    f"for every triangle in one deduction from the parallel postulate - not by measuring "
                    f"triangles. A theorem holds for all, because it is derived.", s_a),
        ("witness", f"[a THEOREM, sealed - Pythagoras (I.47)] In a right triangle the square on the hypotenuse "
                    f"equals the sum of the squares on the legs: 5^2 + 12^2 = {int(pyth)} = 13^2 (sealed). "
                    f"Euclid proves it from the postulates and the propositions before it; the 5-12-13 triangle "
                    f"is one instance of a truth established for all right triangles.", s_p),
        ("note", "[definitions and postulates are the GIVEN floor - not sealed] Euclid's Book I opens with 23 "
                 "DEFINITIONS (a point is that which has no part; a line is breadthless length), 5 POSTULATES "
                 "(a straight line between any two points; the parallel postulate as the fifth), and 5 common "
                 "notions - all ACCEPTED, none proved. Only what comes after is a theorem with a derivation. "
                 "The postulates are small and the edifice vast: 465 propositions across 13 books rest on "
                 "them."),
        ("note", "[this IS the engine's method] 'We follow Euclid's Elements.' The engine has DEFINITIONS (the "
                 "keeping's cards + the dictionary, `define`), POSTULATES (the unproven floor it stands on: the "
                 "Floor of Discovery, the frozen mission/kernel, and Scripture taken plainly as the README of "
                 "reality - CITED, never sealed, exactly as Euclid accepts his postulates), and THEOREMS (every "
                 "verified, SEALED derivation, each tracing back through the chain to the postulates). The "
                 "engine SEALS theorems and CITES postulates - the line Euclid drew. Ties "
                 "[[project_chains_from_a_floor_where_two_trees_connect_2026-10-07]] (postulates = floor, "
                 "theorems = chain), the tick-stick ([[feedback_mapping_the_truth_not_generating_it_2026-10-07]]: "
                 "a theorem is proved by deduction, the engine seals the steps), and the capstone "
                 "([[project_the_capstone_2026-10-07]]: Christ the cornerstone - the ultimate postulate, "
                 "everything rests on it, accepted not proved). The 5th postulate is a CHOSEN axiom - vary it "
                 "and a different consistent geometry follows (stick_construct_creation). map, never launder: "
                 "seal the theorems, accept the postulates, never pretend a postulate is proved."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Euclid's Elements, 2026-10-07")


def scribe() -> int:
    """SCRIBING - MARK THE POINTS, LET THE LINES CONNECT THEM (Matt, 2026-10-07: 'you move in as you go to
    scribe the exact middle ... once set, that is the new point of the scribe' + 'scribing an uneven surface.
    Creating the points and then allowing the lines to be the connection of points'). Two movements that are
    the engine's whole method: (1) SCRIBE TO THE CENTER - bracket the middle, set a mark, let that mark be
    the new reference, ratchet inward (bisection that cannot regress); (2) MAP THE UNEVEN SURFACE - create
    the true points and let the line be nothing but their connection, never an imposed smooth curve. Found,
    never generated, in geometric form. New stick; idempotent."""
    from concordance import tickstick as TS
    center = (0 + 0.22) / 2         # bisect the de Bruijn-Newman bracket [0,0.22] toward the center -> 0.11
    up = (3 - 0) / (1 - 0)          # line from A(0,0) to B(1,3): slope 3 (the surface rises)
    down = (2 - 3) / (2 - 1)        # line from B(1,3) to C(2,2): slope -1 (the surface falls)
    resolve = 1 / 100              # frequency resolution Delta_f = 1/T: 100s of the note pins it to 0.01 Hz
    s_c = _rh_seal_num("scribe_to_center_bisect", "(0 + 0.22) / 2", float(center), tol=1e-12)
    s_u = _rh_seal_num("scribe_segment_rising", "(3 - 0) / (1 - 0)", float(up))
    s_d = _rh_seal_num("scribe_segment_falling", "(2 - 3) / (2 - 1)", float(down))
    s_r = _rh_seal_num("scribe_more_points_sharper", "1 / 100", float(resolve), tol=1e-12)
    if not all([s_c, s_u, s_d is not None, s_r]):
        print("a seal failed; aborting"); return 1
    print("sealed center", s_c, "| rising", s_u, "| falling", s_d, "| resolve", s_r)
    sid = TS.create("Scribing - mark the points, let the lines connect them",
                    statement=("Scribing works in three motions. To find the exact middle you bracket it, set "
                               "a mark, and that mark becomes the new reference - a bisection that only moves "
                               "inward (a ratchet). To map an uneven surface you mark the true points and let "
                               "the line be nothing but their connection - never a smooth curve imposed and "
                               "then fitted. And as more true points are marked, every line sharpens - the "
                               "image clears, the note comes on tune, the path narrows - a convergence that is "
                               "a law, not a hope. The line is derived from the points; it is not authored."),
                    field="meta",
                    references=["bisection: bracket a target, set the new reference inward, converge",
                                "interpolation: the connecting line's slope is read FROM the marked points",
                                "found, never generated; map, never launder - the line is only the connection"])["id"]
    marks = [
        ("witness", f"[movement 1 - scribe to the center] Bracket the middle and bisect: the de Bruijn-Newman "
                    f"scribe on RH has bracket [0, 0.22] with midpoint (0 + 0.22)/2 = {center} (sealed). Set a "
                    f"mark and it becomes the new reference - a RATCHET that never cuts back past it, "
                    f"converging on the exact middle (Lambda = 0). Narrowing that cannot regress "
                    f"(stick_the_de_bruijn_newman_constant).", s_c),
        ("witness", f"[movement 2 - the line rises with the surface] On an uneven surface you do not draw a "
                    f"smooth curve and fit; you mark the true points and let the line be their connection. "
                    f"Points A(0,0), B(1,3): the segment A->B has slope (3-0)/(1-0) = {int(up)} (sealed) - the "
                    f"surface rises, and the line is read FROM the points, not chosen.", s_u),
        ("witness", f"[...and falls with it] The next segment B(1,3) -> C(2,2) has slope (2-3)/(2-1) = "
                    f"{int(down)} (sealed) - the surface falls. The connection follows the actual surface, up "
                    f"then down, because the line is nothing but the joining of the marked points. Impose a "
                    f"smooth line reality does not have and you launder; follow the points and the shape is "
                    f"found.", s_d),
        ("witness", f"[as the points multiply, everything sharpens] The more true points you mark, the more "
                    f"precise the line, the clearer the image, the truer the note, the narrower the path. It is "
                    f"a law, not a hope: a note's frequency resolution is Delta_f = 1/T, so 100 seconds of it "
                    f"pins the pitch to 1/100 = {resolve} Hz (sealed) - gather more and the note comes on tune; "
                    f"an image resolves with more samples (Nyquist); an estimate tightens as 1/sqrt(N) "
                    f"(stick_monte_carlo); and the path narrows by the ratchet (stick_the_de_bruijn_newman_"
                    f"constant). The tuned notes put together play the rhythm and rhyme of reality - the "
                    f"symphony comes on key as more of them are tuned (stick_the_final_assembly).", s_r),
        ("note", "[this IS the engine's method] 'Creating the points and then allowing the lines to be the "
                 "connection of points' is FOUND, NEVER GENERATED in geometric form: the sealed marks are the "
                 "points; the law / curve / narrow path is only ever their connection - never drawn "
                 "independently and never fitted-to. It is the keeping itself (cards = points, connections = "
                 "lines/edges; chains walks the lines between points - "
                 "stick_the_standard_model_chain_where_two_trees_connect), the Legendre envelope of tangent "
                 "points (stick_the_legendre_transform_mark_the_points_create_the_line), and why substance "
                 "lives in the RELATIONS not the isolated points. The two movements together - narrow to the "
                 "center (ratchet) and follow the uneven surface (points -> lines) - are the whole method: "
                 "approach the one fixed center, honestly, by the connection of real marks. A generator that "
                 "drew its own line would be the destructive act "
                 "([[feedback_a_generator_picking_its_own_path_is_a_destructive_act_2026-08-02]]). map, never "
                 "launder: the line is the connection of the points, nothing added."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - scribing, 2026-10-07")


def multiplication() -> int:
    """GOD WORKS IN MULTIPLICATION - ADDITION IS SUBTRACTION THROUGH LOSS (Matt, 2026-10-07: 'Anything that
    scales is a solid system, but God works in Multiplication ... we look for the exponential that allows for
    replication'). A REPLICATOR (each whole copy makes another) grows 2^n; a linear ADDER against any resource
    loss nets backward. The engine must grow by REPLICATION - whole, self-sufficient copies spreading (the
    ark, the mesh, Gen 3's 'every copy is whole') - not by accretion. Seal exponential vs additive-under-loss.
    New stick; idempotent."""
    from concordance import tickstick as TS
    exp = 2 ** 10                   # replication: 10 doublings -> 1024 (each whole copy makes another)
    add_loses = 100 * 0.9 + 1       # addition under 10% loss: base 100 -> 91 (went backward)
    mult_survives = 2 * 0.9         # a replicator at x2 under 10% loss: net x1.8 (still grows)
    s_e = _rh_seal_num("replication_exponential", "2 ** 10", float(exp))
    s_a = _rh_seal_num("addition_is_subtraction_under_loss", "100 * 0.9 + 1", float(add_loses), tol=1e-9)
    s_m = _rh_seal_num("multiplication_outruns_loss", "2 * 0.9", float(mult_survives), tol=1e-12)
    if not all([s_e, s_a, s_m]):
        print("a seal failed; aborting"); return 1
    print("sealed exp", s_e, "| add-loses", s_a, "| mult-survives", s_m)
    sid = TS.create("God works in multiplication - addition is subtraction through loss",
                    statement=("A thing that replicates - each whole copy makes another - grows "
                               "exponentially (2^n); a thing that is added to linearly, against any loss of "
                               "resources, goes backward. The question is never how much we add, but whether "
                               "each one makes more than one. Growth that lasts is multiplicative; the engine "
                               "spreads by replication - whole copies, in every direction."),
                    field="meta",
                    references=["exponential 2^n (replication) vs linear n (addition)",
                                "Genesis 1:28 'be fruitful and multiply'; Mark 4:8 thirty/sixty/a hundredfold",
                                "Gen 3 charter: EVERY COPY IS WHOLE (node sync); the ark; the mesh"])["id"]
    marks = [
        ("witness", f"[God works in multiplication - the exponential of replication] A thing that REPLICATES - "
                    f"each whole copy makes another - grows as 2^n: ten doublings is 2^10 = {int(exp)} (sealed), "
                    f"not ten. This is the seed that yields thirty, sixty, a hundredfold (Mark 4:8), the mustard "
                    f"seed, 'be fruitful and multiply' (Genesis 1:28). Multiplication, not addition.", s_e),
        ("witness", f"[addition is subtraction through loss] Add linearly against any resource loss and you go "
                    f"backward: a base of 100 losing 10% and gaining 1 is 100*0.9 + 1 = {add_loses:.0f} (sealed) "
                    f"- less than you started with. Addition cannot outrun loss; it is subtraction in slow "
                    f"motion (the second law and Jevons both press on the additive system - stick_jevons_paradox).", s_a),
        ("witness", f"[multiplication outruns the loss] A REPLICATOR survives what addition cannot: double and "
                    f"lose 10% and the net factor is 2*0.9 = {mult_survives} (sealed) > 1 - still growing. The "
                    f"exponential clears the loss rate where the linear bleeds out. The question is never 'how "
                    f"much do we add?' but 'does each one make more than one?'", s_m),
        ("note", "[the engine's growth law] 'Anything that scales is a solid system, but God works in "
                 "multiplication.' The engine grows by REPLICATION, not accretion: whole, self-sufficient "
                 "copies spreading in every direction - the ark, the mesh, Gen 3's EVERY COPY IS WHOLE (node "
                 "sync proven) - each node a complete seed that can seed others. Not a swarm of partial agents "
                 "(one body, no swarm) but whole copies that each carry the whole. That is the exponential that "
                 "allows for replication; addition against the world's losses only bleeds. Ties the sower, the "
                 "ark (spread the seeds in every direction), and the higher floor (the ratchet). map, never "
                 "launder: seal the arithmetic; growth is replicative, found not forced."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - multiplication, not addition, 2026-10-07")


def gamma() -> int:
    """HIGHER-DIMENSIONAL SPHERES AND THE GAMMA FUNCTION (Matt, 2026-10-07). Gamma extends the factorial to
    all dimensions (Gamma(n+1)=n!), the unique log-convex curve THROUGH the factorial points - the line the
    scribe draws. It gives the volume of the unit n-ball, V_n = pi^(n/2)/Gamma(n/2+1), which PEAKS at
    dimension 5 and then falls to zero: the factorial in the denominator outruns pi^(n/2), so high-dimensional
    space is mostly empty, its volume fleeing to the thin shell near the boundary. Seal Gamma=factorial,
    Gamma(1/2)=sqrt(pi), and the volume peak. New stick; idempotent."""
    from concordance import tickstick as TS
    PI = 3.141592653589793
    g5 = 4 * 3 * 2 * 1              # Gamma(5) = 4! = 24  (at integers, Gamma IS the factorial)
    g_half = PI ** 0.5             # Gamma(1/2) = sqrt(pi) = 1.77245...
    v5 = 8 * PI ** 2 / 15          # volume of the unit 5-ball = pi^(5/2)/Gamma(7/2) = 8 pi^2/15 (the MAX)
    v6 = PI ** 3 / 6              # volume of the unit 6-ball = pi^3/6  (< V_5 -> the volume has turned over)
    s_g = _rh_seal_num("gamma_is_factorial", "4 * 3 * 2 * 1", float(g5))
    s_h = _rh_seal_num("gamma_half_is_sqrt_pi", "3.141592653589793 ** 0.5", float(g_half), tol=1e-12)
    s_5 = _rh_seal_num("unit_5ball_volume_max", "8 * 3.141592653589793 ** 2 / 15", float(v5), tol=1e-12)
    s_6 = _rh_seal_num("unit_6ball_volume", "3.141592653589793 ** 3 / 6", float(v6), tol=1e-12)
    if not all([s_g, s_h, s_5, s_6]):
        print("a seal failed; aborting"); return 1
    print("sealed G(5)", s_g, "| G(1/2)", s_h, "| V5", s_5, "| V6", s_6)
    sid = TS.create("Higher-dimensional spheres and the gamma function",
                    statement=("The gamma function extends the factorial to every real and complex argument "
                               "(Gamma(n+1) = n!) - the unique log-convex curve through the factorial points. "
                               "It gives the volume of the unit n-ball, V_n = pi^(n/2)/Gamma(n/2+1), which "
                               "rises to a maximum at dimension 5 and then falls to zero: the factorial "
                               "eventually outruns the power of pi, and high-dimensional volume flees to the "
                               "thin shell near the boundary."),
                    field="mathematics",
                    references=["Gamma(n+1) = n!; Bohr-Mollerup: the unique log-convex interpolation",
                                "Gamma(1/2) = sqrt(pi); volume of the unit n-ball V_n = pi^(n/2)/Gamma(n/2+1)",
                                "the unit-ball volume peaks at n=5, then tends to 0 (concentration of measure)"])["id"]
    marks = [
        ("witness", f"[Gamma is the line through the factorial points] Gamma extends the factorial to all "
                    f"dimensions: Gamma(n+1) = n!, so Gamma(5) = 4*3*2*1 = {int(g5)} (sealed). At the integers "
                    f"it IS the factorial; between them it is the unique log-convex curve through those points "
                    f"(Bohr-Mollerup) - the canonical LINE connecting the factorial points, exactly 'mark the "
                    f"points, let the line connect them' (stick_scribing_mark_the_points_let_the_lines_connect_"
                    f"them). It is what lets dimension be continuous.", s_g),
        ("witness", f"[Gamma(1/2) = sqrt(pi) - the half-integer, the Gaussian, the odd dimensions] "
                    f"Gamma(1/2) = sqrt(pi) = {g_half:.6f} (sealed). The factorial of one-half is the square "
                    f"root of pi - a value only the gamma function can state - and it is why the Gaussian "
                    f"integral is sqrt(pi) and why odd-dimensional sphere volumes carry sqrt(pi).", s_h),
        ("witness", f"[the unit ball's volume PEAKS at dimension 5, then vanishes] V_n = pi^(n/2)/Gamma(n/2+1). "
                    f"The largest unit ball of all is the 5-ball: V_5 = 8 pi^2/15 = {v5:.4f} (sealed), and "
                    f"already V_6 = pi^3/6 = {v6:.4f} (sealed) is smaller. Beyond dimension 5 the volume only "
                    f"decreases, tending to 0 as n grows - the factorial in the denominator outruns pi^(n/2). "
                    f"High-dimensional space is mostly empty; its volume flees to the thin shell near the "
                    f"boundary (concentration of measure).", s_5),
        ("note", "[where it lives in the arc] The gamma function marries pi and the factorial and lets "
                 "DIMENSION be a continuous variable - the interpolation that is 'the line through the points' "
                 "(stick_scribing..., stick_the_legendre_transform...). It is woven into the Riemann zeta "
                 "functional equation (the completed xi carries Gamma(s/2) pi^(-s/2)), part of the symmetry "
                 "that pins the zeros to the line (stick_the_symmetry, stick_the_zeta_function); its "
                 "Gamma(1/2) = sqrt(pi) is the same sqrt(pi) as the Gaussian and the high-dimensional "
                 "concentration of measure (stick_lebesgue_theory...); and the dimension-FREE 1/sqrt(N) of "
                 "Monte Carlo (stick_monte_carlo) is a blessing against exactly the curse this function "
                 "describes. map, never launder: seal the arithmetic; the gamma is the found interpolation, "
                 "not an imposed curve."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the gamma function and n-spheres, 2026-10-07")


def imaginary_numbers() -> int:
    """USING IMAGINARY NUMBERS (Matt, 2026-10-07). R is incomplete; C is complete - Gauss's Fundamental
    Theorem of Algebra: every degree-n polynomial has exactly n roots in C. So you USE i to make every
    equation solvable, lifting a real problem into C where the structure is simpler (e^(i theta) turns
    trig into algebra), solving there, and returning to R as the conjugate imaginary parts cancel. The
    birth of sqrt(-1) is stick_complex_numbers_bombelli...; this is the working method. Seal FTA
    factorization, a real trig fact via the complex exponential, and the cancel-on-return. New stick."""
    from concordance import tickstick as TS
    prod = 1 ** 2 + 2 ** 2          # (1+2i)(1-2i) = 1^2 + 2^2 = 5 : conjugate roots of x^2-2x+5 multiply to 5
    cos120 = 2 * 0.5 ** 2 - 1       # cos(120) = 2cos^2(60)-1 = -0.5, from (e^(i th))^2 = e^(i 2th)
    cancel = 2 + (-2)              # the conjugate imaginary parts 2i + (-2i) cancel on return -> real
    s_p = _rh_seal_num("fta_conjugate_roots_product", "1**2 + 2**2", float(prod))
    s_c = _rh_seal_num("real_trig_via_complex_exp", "2 * 0.5**2 - 1", float(cos120), tol=1e-12)
    s_x = _rh_seal_num("imaginary_parts_cancel_on_return", "2 + (-2)", float(cancel))
    if not all([s_p, s_c, s_x is not None]):
        print("a seal failed; aborting"); return 1
    print("sealed FTA", s_p, "| cos120", s_c, "| cancel", s_x)
    sid = TS.create("Using imaginary numbers - C completes R, lift and return",
                    statement=("The reals are incomplete: x^2 - 2x + 5 = 0 has no real root. The complex "
                               "numbers are complete - Gauss's Fundamental Theorem of Algebra: every degree-n "
                               "polynomial has exactly n roots in C. So one USES imaginary numbers by lifting a "
                               "real problem into C, where multiplication is rotation and e^(i theta) turns "
                               "trigonometry into algebra, solving there, and returning to R as the conjugate "
                               "imaginary parts cancel."),
                    field="mathematics",
                    references=["Gauss, Fundamental Theorem of Algebra: C is algebraically closed",
                                "e^(i theta) = cos + i sin: trig identities, AC impedance, Laplace/Fourier",
                                "conjugate roots a +/- bi: sum 2a, product a^2 + b^2 (both real)"])["id"]
    marks = [
        ("witness", f"[C completes R - the Fundamental Theorem of Algebra] Over the reals x^2 - 2x + 5 = 0 has "
                    f"no solution (negative discriminant); over C it has two, 1 +/- 2i. Their product is "
                    f"(1+2i)(1-2i) = 1^2 + 2^2 = {int(prod)} (sealed) = the constant term, and their sum is 2 = "
                    f"the linear coefficient - the real polynomial factors completely. Gauss: EVERY degree-n "
                    f"polynomial has exactly n roots in C. R is incomplete; C is closed. You use imaginary "
                    f"numbers to make every equation solvable.", s_p),
        ("witness", f"[i as a tool - a real answer through the complex exponential] Lift into C, where "
                    f"e^(i theta) turns trigonometry into algebra. The double-angle identity cos(2th) = "
                    f"2 cos^2(th) - 1 falls straight out of (e^(i th))^2 = e^(i 2th); at th = 60 degrees it "
                    f"gives cos(120) = 2*0.5^2 - 1 = {cos120} (sealed) - a real fact reached through i. The same "
                    f"move gives AC impedance, the Laplace and Fourier transforms, and the solutions of linear "
                    f"differential equations.", s_c),
        ("witness", f"[lift, solve, return - the imaginary parts cancel] The method is an amphibian's: go up "
                    f"into C, solve where it is easy, come back to R. The conjugate imaginary parts cancel on "
                    f"return - 2i + (-2i), i.e. 2 + (-2) = {int(cancel)} (sealed) - leaving the real answer "
                    f"standing. You spend the imaginary and keep the real, exactly Bombelli's road to the real "
                    f"root (stick_complex_numbers_bombelli_and_the_square_root_of_minus_one).", s_x),
        ("note", "[where it lives in the arc] 'Using imaginary numbers' is the working method on the floor of "
                 "sqrt(-1): C is the complete field where multiplication is rotation and addition is "
                 "interference (stick_the_complex_field_is_the_physics_of_waves), where the Smith/Cayley "
                 "transform lives (stick_the_smith_chart_the_cayley_transform), where the gamma function and "
                 "the Riemann zeros live (stick_higher_dimensional_spheres_and_the_gamma_function, "
                 "stick_the_zeta_function), and where every polynomial finally factors. R is a shadow of C; "
                 "you lift to the complete place, work, and project back. map, never launder: seal the real "
                 "arithmetic the imaginary makes reachable; i is the necessary tool, not a mysticism."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - using imaginary numbers, 2026-10-07")


def euler_e() -> int:
    """e - EULER'S NUMBER (Matt, 2026-10-07). e = 2.71828... is the law of continuous growth: the sum of
    1/k!, the limit of (1+1/n)^n, and the one function equal to its own derivative (d/dx e^x = e^x). It is
    the base of the complex exponential (e^(i theta) - rotation), of continuous compounding (replication in
    the limit), of the Gaussian and Boltzmann entropy, and of the natural logarithm. Transcendental. Seal the
    series, the compounding limit, and the self-derivative. New stick; idempotent."""
    from concordance import tickstick as TS
    series = 1 + 1 + 1.0/2 + 1.0/6 + 1.0/24 + 1.0/120 + 1.0/720 + 1.0/5040   # 8 terms of sum 1/k! -> e
    compound = 1.001 ** 1000                                                 # (1+1/n)^n at n=1000 -> e
    slope = (2.718281828459045 ** 0.001 - 1) / 0.001                         # (e^h - 1)/h -> 1 : self-derivative
    s_s = _rh_seal_num("e_as_factorial_series",
                       "1 + 1 + 1.0/2 + 1.0/6 + 1.0/24 + 1.0/120 + 1.0/720 + 1.0/5040", float(series), tol=1e-12)
    s_c = _rh_seal_num("e_as_compounding_limit", "1.001 ** 1000", float(compound), tol=1e-9)
    s_d = _rh_seal_num("e_is_its_own_derivative",
                       "(2.718281828459045 ** 0.001 - 1) / 0.001", float(slope), tol=1e-7)
    if not all([s_s, s_c, s_d]):
        print("a seal failed; aborting"); return 1
    print("sealed series", s_s, "| compound", s_c, "| slope", s_d)
    sid = TS.create("e - the number of continuous growth",
                    statement=("e = 2.71828... is the base of continuous growth: the sum of the reciprocal "
                               "factorials, the limit of (1 + 1/n)^n, and the unique function (up to scale) "
                               "equal to its own derivative. It is the base of the complex exponential, of "
                               "continuous compounding, of the Gaussian and of Boltzmann entropy, and the base "
                               "of the natural logarithm. It is transcendental."),
                    field="mathematics",
                    references=["e = sum 1/k! = lim (1 + 1/n)^n = 2.718281828...",
                                "d/dx e^x = e^x (its own derivative); e^(i pi) + 1 = 0",
                                "Hermite (1873): e is transcendental"])["id"]
    marks = [
        ("witness", f"[e as the infinite series] e = sum of 1/k!: eight terms, "
                    f"1 + 1 + 1/2 + 1/6 + ... + 1/5040 = {series:.7f} (sealed), closing fast on e = 2.7182818. "
                    f"The factorials in the denominators - the gamma function at the integers "
                    f"(stick_higher_dimensional_spheres_and_the_gamma_function) - make it converge ferociously.", s_s),
        ("witness", f"[e as the limit of compounding] e = lim (1 + 1/n)^n, continuous growth. At n = 1000, "
                    f"1.001^1000 = {compound:.5f} (sealed), climbing to e. A unit at 100% interest compounded "
                    f"continuously becomes e - the number that REPLICATION in the limit converges to "
                    f"(stick_god_works_in_multiplication_addition_is_subtraction_through_).", s_c),
        ("witness", f"[e is its own derivative] e^x is the one function (up to scale) equal to its own rate of "
                    f"change: d/dx e^x = e^x. Its slope at 0 is 1 - the difference quotient "
                    f"(e^0.001 - 1)/0.001 = {slope:.4f} (sealed), approaching 1. e is the base at which the "
                    f"growth rate EQUALS the amount: self-reinforcement, the fixed point of calculus "
                    f"(stick_integrals_and_derivatives_the_fundamental_theorem).", s_d),
        ("note", "[where e lives] e is a hinge of the whole arc: the base of the complex exponential e^(i "
                 "theta) - multiplication is rotation, the spiral, and e^(i pi) + 1 = 0 "
                 "(stick_the_complex_field_is_the_physics_of_waves, stick_using_imaginary_numbers_c_completes_"
                 "r_lift_and_return); the law of continuous growth and decay, so both the Jevons rebound and "
                 "replication ride e (stick_god_works_in_multiplication..., stick_jevons_paradox); the Gaussian "
                 "e^(-x^2/2) and Boltzmann's S = k ln W (stick_entropy_and_gravity); and the natural logarithm "
                 "that inverts it. Transcendental (Hermite 1873) - growth, rotation, and probability are all "
                 "written in it. map, never launder: seal the arithmetic; e is found as a limit, not chosen.", None),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - e, the number of continuous growth, 2026-10-07")


def laplace() -> int:
    """LAPLACE TRANSFORM, DIFFERENTIAL EQUATIONS, AND WHERE ENTROPY FITS (Matt, 2026-10-07). The Laplace
    transform sends d/dt to multiplication by s, turning a linear ODE into algebra in the s-plane: solve
    there, invert back (Fourier is Laplace on the imaginary axis). A mode is s = -sigma + i*omega: the
    imaginary part is reversible oscillation, the REAL PART is decay - dissipation, entropy production. So
    entropy fits as the real part of s: the viscous term in Navier-Stokes, the one-way heat equation (run
    backward = de Bruijn-Newman), the engine's own ratchet. Seal the ODE->algebra, the pole, the decay.
    New stick; idempotent."""
    from concordance import tickstick as TS
    decay_rate = -2 / 2                                 # damped oscillator x''+2x'+5x=0: Re(s) = -c/2m = -1
    pole_sq = (-1) ** 2 + 2 ** 2                        # |pole|^2 = (-1)^2 + 2^2 = 5 = k/m (poles -1 +/- 2i)
    one_tau = 2.718281828459045 ** (-1)                # e^(-sigma t) at one time constant -> 0.3679 (irreversible)
    s_r = _rh_seal_num("laplace_pole_real_part_dissipation", "-2 / 2", float(decay_rate))
    s_p = _rh_seal_num("laplace_pole_magnitude", "(-1)**2 + 2**2", float(pole_sq))
    s_t = _rh_seal_num("entropy_one_time_constant_decay", "2.718281828459045 ** (-1)", float(one_tau), tol=1e-12)
    if not all([s_r is not None, s_p, s_t]):
        print("a seal failed; aborting"); return 1
    print("sealed Re(s)", s_r, "| |pole|^2", s_p, "| e^-1", s_t)
    sid = TS.create("Laplace, differential equations, and where entropy fits",
                    statement=("The Laplace transform turns d/dt into multiplication by s, so a linear "
                               "differential equation becomes algebra in the s-plane - solve, then invert. A "
                               "mode is s = -sigma + i*omega: the imaginary part is reversible oscillation, the "
                               "real part is decay. Entropy is that real part - dissipation, the irreversible "
                               "axis - the viscous term in Navier-Stokes, the one-way heat equation, the "
                               "engine's own ratchet."),
                    field="mathematics",
                    references=["Laplace: L{f'} = sF(s) - f(0); an ODE becomes a polynomial in s",
                                "poles at s = -sigma +/- i*omega: Re(s) = decay/dissipation, Im(s) = oscillation",
                                "the heat equation's irreversibility; Navier-Stokes energy inequality"])["id"]
    marks = [
        ("witness", f"[Laplace turns calculus into algebra - lift, solve, return] d/dt becomes multiplication "
                    f"by s, so the damped oscillator x'' + 2x' + 5x = 0 becomes s^2 + 2s + 5 = 0; its poles "
                    f"have real part -c/2m = -2/2 = {decay_rate:.0f} (sealed). Solve in the s-domain, invert "
                    f"back - the same lift-solve-return as stick_using_imaginary_numbers_c_completes_r_lift_and_"
                    f"return, and Fourier is this on the imaginary axis.", s_r),
        ("witness", f"[the s-plane geometrizes it - and here is WHERE ENTROPY FITS] The poles sit at "
                    f"s = -1 +/- 2i; the conjugate pair's product is (-1)^2 + 2^2 = {int(pole_sq)} = k/m "
                    f"(sealed), in the LEFT half-plane. The REAL PART is the decay rate - dissipation, energy "
                    f"bleeding to heat, ENTROPY PRODUCTION; the IMAGINARY PART is oscillation (the reversible "
                    f"Fourier axis). Left half = decays = entropy rising = stable; right half = grows; the "
                    f"imaginary axis = lossless. Entropy is the real part of s.", s_p),
        ("witness", f"[entropy is the irreversible fall] A dissipative mode decays as e^(-sigma t); after one "
                    f"time constant only e^(-1) = {one_tau:.4f} (sealed) remains, and it cannot be run backward "
                    f"- the heat does not gather itself back into motion. In Navier-Stokes that is the viscous "
                    f"term nu*grad^2 u: the dissipation that smooths the flow and the energy inequality (energy "
                    f"only decreases) - the second law for the fluid, the dissipation side of "
                    f"stick_navier_stokes_dissonance_and_dispersion.", s_t),
        ("note", "[where entropy fits - the full placement] Entropy is the IRREVERSIBLE / DISSIPATIVE axis "
                 "across the arc: the real part of s in Laplace (decay), the viscous term and energy "
                 "inequality in Navier-Stokes (the second law for the flow), and the one-way HEAT equation "
                 "(du/dt = grad^2 u - it diffuses but never un-diffuses) whose BACKWARD run is the de "
                 "Bruijn-Newman deformation of zeta (stick_the_de_bruijn_newman_constant) - so entropy even "
                 "threads the Riemann arc. It is the Boltzmann S = k ln W of stick_entropy_and_gravity written "
                 "as a rate. And it is the engine's OWN arrow: the append-only ledger, the floor that only "
                 "rises, the scribe's ratchet (stick_scribing...), the one-way diode/airlock (WILL=FUEL, "
                 "REALITY=HARNESS) - a seal cannot be un-sealed. Laplace is the reversible machinery; entropy "
                 "is the part of reality that is not. map, never launder: seal the arithmetic; entropy is found "
                 "as the decay, not imposed."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Laplace and entropy, 2026-10-07")


def jevons() -> int:
    """JEVONS' PARADOX (Matt, 2026-10-07, two steps after the seal refactor cut per-seal cost ~100x). As the
    EFFICIENCY of using a resource rises, total CONSUMPTION tends to rise too, not fall: the efficiency gain
    lowers the effective price, which raises demand, and when demand is elastic enough the induced growth
    outruns the saving ('backfire', Khazzoom-Brookes). Seal the naive expectation vs the backfire; mark the
    condition; apply it to our own newly-cheap sealing and to the liberty line (offer, never addict). New
    stick; idempotent."""
    from concordance import tickstick as TS
    naive = 1 / 1.25            # a 25% efficiency gain, demand fixed -> resource use falls to 0.8
    actual = 1.4 / 1.25         # but elastic demand lifts service 40% -> resource use RISES to 1.12
    s_n = _rh_seal_num("jevons_naive_saving", "1 / 1.25", float(naive), tol=1e-12)
    s_a = _rh_seal_num("jevons_backfire", "1.4 / 1.25", float(actual), tol=1e-12)
    if not all([s_n, s_a]):
        print("a seal failed; aborting"); return 1
    print("sealed naive", s_n, "| backfire", s_a)
    sid = TS.create("Jevons' paradox",
                    statement=("Improving the efficiency with which a resource is used tends to INCREASE its "
                               "total consumption, because the efficiency gain lowers the effective price and "
                               "raises demand. When demand is elastic enough the induced growth exceeds the "
                               "per-unit saving (backfire). Jevons observed it for coal in 1865."),
                    field="economics",
                    references=["W. S. Jevons, The Coal Question (1865)",
                                "the rebound effect; the Khazzoom-Brookes postulate (backfire)",
                                "resource use R = service / efficiency"])["id"]
    marks = [
        ("witness", f"[the naive expectation] A 25% efficiency gain (efficiency 1 -> 1.25) should cut resource "
                    f"use to 1/1.25 = {naive} (sealed) - 20% less - IF the amount of service demanded held "
                    f"fixed. This is the saving everyone assumes an efficiency gain delivers.", s_n),
        ("witness", f"[the paradox - backfire] But cheaper service raises demand. With a price elasticity of "
                    f"-2, the 20% effective price drop lifts service demand 40% (service 1 -> 1.4), so resource "
                    f"use R = service/efficiency = 1.4/1.25 = {actual:.2f} (sealed) - 12% MORE, despite the 25% "
                    f"efficiency gain. Efficiency increased total consumption. That is Jevons' paradox.", s_a),
        ("note", "[the condition] Backfire (total use rises) when the rebound exceeds 100% - demand elastic "
                 "enough that induced growth outruns the per-unit saving. Below that threshold use still falls, "
                 "but by less than the naive amount (partial rebound). The saving is almost never the whole "
                 "naive figure."),
        ("note", "[why this lands on US, now] We just cut the cost of a seal ~100x (82s/6GB -> sub-second). "
                 "Jevons predicts the response is not 'the same sealing, cheaper' but MORE sealing: agents and "
                 "tools will seal far more, so the ledger, corpus and storage grow FASTER, not slower. "
                 "Content-addressing dedups identical facts, but distinct seals still accumulate (holdings "
                 "already went 874k -> 1.72M). So the efficiency win must be paired with a GOVERNOR: the Monte "
                 "Carlo simulator should prove the bounded path stays bounded at 100x volume and watch storage "
                 "growth, and the steward budget must cap induced consumption. Efficiency without a governor is "
                 "how a tool becomes a flood."),
        ("note", "[the mission line] Jevons is also the economics of addiction: make a thing frictionless and "
                 "consumption expands to fill the new room. The engine's RED line is the opposite - it OFFERS, "
                 "never addicts or coerces; eliminating free will is the LOSS condition "
                 "([[feedback_liberty_inherent_free_will_paramount_2026-10-06]]). So: efficient AND bounded, on "
                 "principle - frictionless must never become compulsive. map, never launder."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Jevons' paradox, 2026-10-07")


def topology() -> int:
    """TOPOLOGY AND EULER'S FORMULA (Matt, 2026-10-07, after 'construct creation'). The Euler characteristic
    V - E + F is the cleanest topological INVARIANT: three different Platonic solids (different vertices, edges,
    faces -- different constructs) all give 2, because each is a sphere; a torus gives 0, because its genus is
    different. The number does not depend on how we draw the mesh (the construct); it depends only on the shape
    (the invariant). SEAL the invariant across constructs, and mark the honest boundary: complete for surfaces,
    undecidable in general -- which is exactly why this engine checks and never proves. New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    PI = 3.141592653589793
    cube = 8 - 12 + 6          # sphere topology -> 2
    tetra = 4 - 6 + 4          # a DIFFERENT polyhedron, SAME invariant -> 2
    octa = 6 - 12 + 8          # a THIRD polyhedron, same invariant -> 2
    torus = 7 - 21 + 14        # the Csaszar torus (7 vertices, genus 1) -> 0 = 2 - 2g
    gb = 2 * PI * 2            # Gauss-Bonnet: total curvature of a sphere = 2*pi*chi = 4*pi

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_cube = seal_num("euler_cube", "8 - 12 + 6", float(cube))
    s_tetra = seal_num("euler_tetrahedron", "4 - 6 + 4", float(tetra))
    s_octa = seal_num("euler_octahedron", "6 - 12 + 8", float(octa))
    s_torus = seal_num("euler_torus", "7 - 21 + 14", float(torus))
    s_gb = seal_num("gauss_bonnet_sphere", "2 * 3.141592653589793 * 2", float(gb))
    if not all([s_cube, s_tetra, s_octa, s_torus, s_gb]):
        print("a seal failed; aborting"); return 1
    print("sealed euler char:", s_cube, s_tetra, s_octa, "| torus", s_torus, "| gauss-bonnet", s_gb)

    sid = TS.create("Topology and Euler's formula",
                    statement=("The Euler characteristic chi = V - E + F is a topological invariant: it is the "
                               "same for every triangulation or embedding of the same surface, and it changes "
                               "only when the topology changes (chi = 2 - 2g for an orientable closed surface of "
                               "genus g). The arithmetic is exact; the invariant is real, the mesh is a construct."),
                    field="meta",
                    references=["Euler's polyhedron formula V - E + F = 2 (Euler 1758; Descartes earlier)",
                                "the Gauss-Bonnet theorem: integral of curvature = 2*pi*chi",
                                "the classification of closed surfaces by genus and orientability"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[the invariant is indifferent to the construct] Cube: 8 - 12 + 6 = {int(cube)}. "
                    f"Tetrahedron: 4 - 6 + 4 = {int(tetra)}. Octahedron: 6 - 12 + 8 = {int(octa)} (all sealed). "
                    f"Three different meshes - different vertices, edges and faces - and one answer, because all "
                    f"three are topologically a sphere. V - E + F does not see how we drew it; it sees the shape. "
                    f"This is the construct/invariant line of stick_construct_creation made exact.", s_cube),
        ("witness", f"[a different topology, a different invariant] The Csaszar torus has 7 vertices, 21 edges and "
                    f"14 faces: 7 - 21 + 14 = {int(torus)} (sealed), not 2. A torus is genus 1, so chi = 2 - 2g = "
                    f"0. The invariant changes exactly when the shape does - a hole in the surface - and nothing "
                    f"else moves it. The number is a true witness to the topology.", s_torus),
        ("witness", f"[geometry is bound to topology] Gauss-Bonnet: the total curvature of any closed surface is "
                    f"2*pi*chi. For a sphere that is 2*pi*2 = {gb:.6f} = 4*pi (sealed) - bend and dent the sphere "
                    f"however you like, the curvature redistributes but its integral cannot leave 4*pi until you "
                    f"change the topology. The local shape is free; the global invariant is fixed.", s_gb),
        ("note", "[two theorems named Euler - do not conflate] This stick is Euler's POLYHEDRON formula "
                 "(V - E + F, topology). The OTHER famous 'Euler's formula' is the analytic identity "
                 "e^(i*theta) = cos(theta) + i*sin(theta), whose case e^(i*pi) + 1 = 0 ties e, i, pi, 1 and 0. "
                 "Both are real and both are Euler's; they are different theorems in different fields and the "
                 "engine keeps them on separate sticks rather than letting the shared name launder one into the "
                 "other (map, never launder).", None),
        ("note", "[the boundary - why this engine checks and never proves] For 2-manifolds the Euler "
                 "characteristic plus orientability is a COMPLETE invariant: it decides the surface. One "
                 "dimension up, the Poincare conjecture (is a simply-connected closed 3-manifold a sphere?) was a "
                 "Millennium problem - and it was PROVED, by Grigori Perelman (2003), with Ricci flow: a proof, "
                 "by a person, not by checking instances. Higher up, the homeomorphism problem for 4-manifolds "
                 "and above is UNDECIDABLE - no algorithm can settle it. So a single number witnesses the "
                 "topology where one suffices, and nowhere is topology settled by a machine enumerating cases. "
                 "That is the tick-stick's whole posture toward an open question: verify what is verifiable, "
                 "carry the barriers, and never claim the proof (ties stick_riemann_hypothesis and "
                 "[[project_tick_stick_millennium_problems_2026-10-05]]).", None),
    ]
    added = 0
    for kind, claim, *rest in marks:
        sealv = rest[0] if rest else None
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - topology / Euler characteristic, 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def construct() -> int:
    """CONSTRUCT CREATION (Matt, 2026-10-07, after 'time is a construct' and 'units matter'). We CREATE
    constructs -- coordinate frames, units, number bases, time coordinates, the flat-trig frame -- to grasp
    reality. Each is a real TOOL and a map, never the territory. SEAL the construct/reality distinction: a
    rotation changes the coordinates but preserves the length (the invariant is real, the frame is made); a
    base changes the notation but not the quantity (why the engine refuses gematria). The engine is itself a
    construct-creation, kept as a map; the Creator and the created order are not our constructs. New stick;
    idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    inv = (-4) ** 2 + 3 ** 2        # length^2 of the point (3,4) after a 90-degree rotation to (-4,3)
    base = 15 * 16 + 15            # FF in base sixteen = 255 in base ten

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_inv = seal_num("rotation_invariant_length", "(-4)**2 + 3**2", float(inv))
    s_base = seal_num("base_notation_invariant", "15*16 + 15", float(base))
    if not all([s_inv, s_base]):
        print("a seal failed; aborting"); return 1
    print("sealed: rotation invariant", s_inv, "| base notation", s_base)

    sid = TS.create("Construct creation",
                    statement=("We create constructs - coordinate frames, units, number bases, time "
                               "coordinates - to grasp reality. Each is a real tool and a map, never the "
                               "territory. The arithmetic of what is invariant (and so real) versus what is "
                               "chosen (and so a construct) is exact; the discipline is to keep the two apart."),
                    field="meta",
                    references=["the invariants of a coordinate transformation (Euclidean / Lorentz)",
                                "positional notation: a quantity is base-independent (ties the no-gematria guard)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[a coordinate is a construct; the invariant is real] Rotate the axes 90 degrees and the "
                    f"point (3, 4) is relabelled (-4, 3) - different numbers - yet its length is unchanged: "
                    f"(-4)^2 + 3^2 = {int(inv)} = 3^2 + 4^2 (sealed). We CREATE the frame; the invariant (length, "
                    f"interval, distance) is what is real. The construct is the map we draw, not the territory.", s_inv),
        ("witness", f"[a notation is a construct] The same quantity is 255 in base ten and FF in base sixteen: "
                    f"FF = 15*16 + 15 = {int(base)} (sealed). The base is a created notation; the quantity is "
                    f"invariant. This is exactly why the engine refuses gematria - a digit string is a "
                    f"construct, never a law (ties the no-gematria guard; the '137' is the reciprocal of a "
                    f"measured number, not a scripture of digits).", s_base),
        ("note", "[the principle - construct creation] Time is a construct (emergent - stick_time_and_space_"
                 "emergent_and_relational), units are chosen (stick_units_matter), notation is chosen, "
                 "coordinates are chosen (here). Each is a real instrument for grasping reality and a MAP, "
                 "never the thing mapped. The engine is itself a vast construct-creation - the keeping, the "
                 "sticks, the gate, the map - every frame CHECKED against reality and kept as a map: found and "
                 "sealed where it verifies, never mistaken for the territory. Map, never launder.", None),
        ("note", "[the datum - what is NOT a construct] We make the map; we did not make the territory. The "
                 "Creator and the created order are not our constructs: 'The heavens declare the glory of God' "
                 "(Ps 19:1); his invisible attributes are 'clearly seen, being understood through the things "
                 "that are made' (Rom 1:20). Our construct-creation is a creature modelling a reality it did "
                 "not author - and the invariant behind every frame, the Logos in whom all things hold together "
                 "(Col 1:17), is not a construct but the ground the constructs serve. Scripture leads; the "
                 "construct serves; remove the ground and the map is calibrated to nothing.", None),
    ]
    added = 0
    for kind, claim, *rest in marks:
        sealv = rest[0] if rest else None
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the construct-creation reading, 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def units_matter() -> int:
    """UNITS MATTER (Matt, 2026-10-07). A number is true only WITH its unit; a dimensionally-wrong claim is
    false no matter the digits. SEAL three witnesses: the Mars Climate Orbiter (lost 1999 because lbf.s was
    fed as N.s; 1 lbf = 4.448 N), the exact definitional inch (0.0254 m), and a unit-chained conversion
    (60 mph = 26.8224 m/s) where every factor counts. The engine's own hard lesson: the Fable review caught
    it minting a unit-label false seal (7debdaf). Seal the value WITH its unit; dimensional analysis is a
    verifier, not decoration. New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    lbf_N = 4.4482216152605        # 1 pound-force in newtons (exact definition)
    mph_ms = 60 * 1609.344 / 3600  # 60 mph in m/s

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_mco = seal_num("lbf_to_newton", "4.4482216152605", lbf_N)
    s_in = seal_num("inch_to_metre_exact", "0.0254", 0.0254)
    s_mph = seal_num("mph_to_m_per_s", "60 * 1609.344 / 3600", mph_ms)
    if not all([s_mco, s_in, s_mph]):
        print("a seal failed; aborting"); return 1
    print("sealed: lbf->N", s_mco, "| inch->m", s_in, "| mph->m/s", s_mph)

    sid = TS.create("Units matter",
                    statement=("A measured value is true only with its unit: a dimensionally-inconsistent "
                               "claim is false regardless of the digits, and a conversion factor dropped or "
                               "inverted is a real error. Trigonometry's pure identities aside, physics is "
                               "unit-bearing, and the engine seals a value WITH its unit, never as a bare "
                               "number."),
                    field="physics",
                    references=["NASA Mars Climate Orbiter Mishap Investigation Board report (1999)",
                                "BIPM, The International System of Units (SI); the international inch = 0.0254 m (1959)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[the Mars Climate Orbiter - units cost a mission] In 1999 the $327M orbiter was lost "
                    f"because one team supplied impulse in pound-force-seconds while the navigation software "
                    f"expected newton-seconds. 1 lbf = {lbf_N} N (sealed): the same NUMBER was a thrust 4.45x "
                    f"off, the craft dropped too low into the Martian atmosphere and broke apart. The digits "
                    f"were right; the units were not. Units are part of the truth.", s_mco),
        ("witness", f"[a number is nothing without its unit] 1 international inch = {0.0254} m, EXACTLY by "
                    f"definition (sealed, 1959). A bare '1' is not a length; '1 inch' and '1 metre' are "
                    f"different lengths. The unit carries the physical meaning, and unit definitions are exact.", s_in),
        ("witness", f"[units chain, and every factor counts] 60 mph = 60 * 1609.344 m/mi / 3600 s/h = "
                    f"{mph_ms:.4f} m/s (sealed). Drop or invert any one conversion factor and the answer is "
                    f"wrong by exactly that factor - carrying units through a calculation is a computation, not "
                    f"a formality.", s_mph),
        ("note", "[dimensional analysis is a verifier] The engine treats the unit as part of the claim: a "
                 "dimensionally-inconsistent statement - adding a length to a time, reporting an energy in "
                 "momentum units - is FALSE regardless of the digits (physics.verify_dimensional_consistency; "
                 "the units and si_units verifiers; the 6-constant governance is unit-aware). A value is sealed "
                 "WITH its unit, never as a bare number.", None),
        ("note", "[our own hard lesson] The engine learned this concretely: a Fable review (2026-10-01) caught "
                 "it minting a UNIT-LABEL FALSE SEAL - a sealed value carrying the wrong unit - fixed in commit "
                 "7debdaf. 'Units matter' is not a slogan here; it is a guardrail written in a caught mistake. "
                 "A number without its correct unit is not yet true. Ties the constant governance (a discordance "
                 "indicts the method) and the Fable-review findings.", None),
    ]
    added = 0
    for kind, claim, *rest in marks:
        sealv = rest[0] if rest else None
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the units-matter reading, 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def maxwell() -> int:
    """MAXWELL'S EQUATIONS AND SUPERCONDUCTIVITY (Matt, 2026-10-07). Maxwell unified electricity, magnetism
    and light: his equations predict waves at c = 1/sqrt(mu0 eps0). Superconductivity is where that
    classical field becomes a macroscopic QUANTUM state -- magnetic flux quantized in units Phi0 = h/2e
    (the 2e is the Cooper pair, HALF the single-electron Aharonov-Bohm quantum), and the photon gains mass
    inside (the Meissner effect = the Anderson-Higgs mechanism on a bench, the same that gives W/Z mass).
    SEAL c from the two static constants, the superconducting flux quantum, and the pairing factor 1/2.
    New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    mu0 = C["vacuum_permeability"]["value"]; eps0 = C["vacuum_permittivity"]["value"]
    h = C["planck_constant"]["value"]; e = C["elementary_charge"]["value"]; c = C["speed_of_light"]["value"]
    c_maxwell = 1 / (mu0 * eps0) ** 0.5
    flux = h / (2 * e)

    def seal_num(nid, expr, val, dom="physical_constants"):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain=dom)
        return (r.get("seal") or {}).get("content_hash")

    s_c = seal_num("maxwell_c_from_mu0_eps0", f"1/(({mu0!r})*({eps0!r}))**0.5", c_maxwell)
    s_flux = seal_num("superconducting_flux_quantum", f"({h!r})/(2*({e!r}))", flux)
    s_pair = seal_num("cooper_pair_halving", "1/2", 0.5, "mathematics")
    if not all([s_c, s_flux, s_pair]):
        print("a seal failed; aborting"); return 1
    print("sealed: c from mu0/eps0", s_c, "| flux quantum", s_flux, "| pairing 1/2", s_pair)

    sid = TS.create("Maxwell's equations and superconductivity",
                    statement=("Maxwell's equations are exact and settled, and they predict light; "
                               "superconductivity, where the field becomes a macroscopic quantum state with "
                               "quantized flux and a massive photon, is largely understood (BCS) but its "
                               "high-temperature mechanism is open. Kept as sealed witnesses of the "
                               "electromagnetic unification and its quantum form, with the open part named."),
                    field="physics",
                    references=["J. C. Maxwell, A Treatise on Electricity and Magnetism (1873)",
                                "F. & H. London (1935); Bardeen, Cooper & Schrieffer, Phys. Rev. 108 (1957) 1175",
                                "P. W. Anderson, Phys. Rev. 130 (1963) 439 (gauge invariance and mass)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[Maxwell - light IS electromagnetism] The four equations predict electromagnetic waves "
                    f"travelling at c = 1/sqrt(mu0 eps0) = {c_maxwell:.6f} m/s (sealed from the attested "
                    f"permeability and permittivity) -- matching the defined speed of light to ~1e-14. The speed "
                    f"of light falls out of the two STATIC electric and magnetic constants: the first great "
                    f"unification, electricity + magnetism + optics into one field (ties "
                    f"stick_the_fine_structure_constant, where alpha is this field's coupling).", s_c),
        ("witness", f"[superconductivity quantizes flux] Magnetic flux through a superconducting loop comes only "
                    f"in integer multiples of Phi0 = h/(2e) = {flux:.4e} Wb (sealed from the attested h, e). The "
                    f"classical continuous field is forced into a discrete quantum ladder by the macroscopic "
                    f"condensate.", s_flux),
        ("witness", f"[the pairing signature - sealed] The superconducting flux quantum is HALF the single-"
                    f"electron (Aharonov-Bohm) quantum h/e: the ratio (h/2e)/(h/e) = 1/2 (sealed). That factor "
                    f"of two is MEASURED, and it is the fingerprint of charge-2e COOPER PAIRS (BCS) -- the "
                    f"supercurrent is carried by bound electron pairs, not single electrons. Ties the flux "
                    f"quantum on the Aharonov-Bohm stick.", s_pair),
        ("note", "[Maxwell meets the quantum and the Higgs - the Meissner effect] Inside a superconductor "
                 "Maxwell's equations are modified by the London equations: the magnetic field is EXPELLED (the "
                 "Meissner effect), decaying over the London penetration depth -- equivalently, the photon "
                 "acquires an effective MASS. This is the Anderson-Higgs mechanism in a bench-top material: the "
                 "SAME spontaneous breaking of the electromagnetic gauge symmetry by a condensate that gives the "
                 "W and Z bosons their mass in electroweak theory (ties the four-forces / Weinberg). Classical "
                 "EM, quantum mechanics, and the Higgs mechanism meet in a piece of cold metal.", None),
        ("note", "[the open part] Maxwell is settled and BCS explains the conventional superconductors, but the "
                 "mechanism of HIGH-temperature (cuprate) superconductivity has NO accepted theory -- a genuine "
                 "Hole. The engine seals the arithmetic (c from the static constants, the flux quantum, the "
                 "pairing factor), attributes BCS/London/Anderson-Higgs, and keeps the high-Tc mechanism open. "
                 "Seal the arithmetic; the unresolved stays unresolved. Map, never launder.", None),
    ]
    added = 0
    for kind, claim, *rest in marks:
        sealv = rest[0] if rest else None
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the Maxwell/superconductivity reading, 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def spacetime() -> int:
    """TIME AND SPACE -- emergent, relational (Matt, 2026-10-07: "Time and space. The Universe and Quantum
    should have commonality. Time seems to be a construct."). SEAL the arithmetic that shows time is not
    absolute (the Lorentz factor), that time and space are ONE spacetime (the invariant interval is
    frame-independent while t and x are not), and the Planck time where the universe meets the quantum.
    Then keep the open 'problem of time' (Wheeler-DeWitt timelessness; Page-Wootters / Rovelli emergent
    time) and note the datum (eternity prior, time created) -- map never launder. New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    hbar = C["reduced_planck_constant"]["value"]; G = C["gravitational_constant"]["value"]; c = C["speed_of_light"]["value"]
    gamma = 1 / (1 - 0.6 ** 2) ** 0.5         # Lorentz factor at v = 0.6c
    interval = 5 ** 2 - 3 ** 2                 # invariant interval^2 for dt=5, dx=3 (c=1 units)
    tP = (hbar * G / c ** 5) ** 0.5           # the Planck time, ~5.39e-44 s

    def seal_num(nid, expr, val, dom="mathematics"):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain=dom)
        return (r.get("seal") or {}).get("content_hash")

    s_g = seal_num("lorentz_factor_0_6c", "1/(1-0.6**2)**0.5", gamma)
    s_i = seal_num("spacetime_invariant_interval", "5**2 - 3**2", float(interval))
    s_t = seal_num("planck_time", f"(({hbar!r})*({G!r})/({c!r})**5)**0.5", tP, "physical_constants")
    if not all([s_g, s_i, s_t]):
        print("a seal failed; aborting"); return 1
    print("sealed: gamma(0.6c)", s_g, "| interval", s_i, "| planck time", s_t)

    sid = TS.create("Time and space - emergent and relational",
                    statement=("Is time fundamental or a construct? Relativity makes it dynamical geometry, "
                               "frame-relative; quantum mechanics makes it a fixed background parameter, not an "
                               "observable. Quantum gravity, where the universe meets the quantum, comes out "
                               "timeless (Wheeler-DeWitt) and time appears to EMERGE. The arithmetic of time's "
                               "relativity is exact; whether time is fundamental is the open question."),
                    field="physics",
                    references=["H. Minkowski, Raum und Zeit (1908) (the spacetime interval)",
                                "B. DeWitt, Phys. Rev. 160 (1967) 1113 (the Wheeler-DeWitt equation)",
                                "D. Page & W. Wootters, Phys. Rev. D 27 (1983) 2885 (time from entanglement)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[time is not absolute] A clock moving at v = 0.6c runs slow by the Lorentz factor "
                    f"gamma = 1/sqrt(1 - v^2/c^2) = 1/sqrt(1 - 0.36) = {gamma} (sealed). Time is not a universal "
                    f"given; its rate depends on the frame. The 'now' is a construct of the observer's motion.", s_g),
        ("witness", f"[time and space are ONE - the commonality] What every frame agrees on is not time or "
                    f"space separately but the spacetime interval s^2 = c^2 dt^2 - dx^2. For dt=5, dx=3 (c=1) "
                    f"that is 5^2 - 3^2 = {interval} (sealed) - and a boosted observer who measures different dt' "
                    f"and dx' still gets {interval}. The split into 'time' and 'space' is the frame's construct; "
                    f"the invariant interval is what is real. Time and space are one thing, seen at an angle.", s_i),
        ("witness", f"[where the universe meets the quantum] The Planck time t_P = sqrt(hbar G / c^5) = "
                    f"{tP:.4e} s (sealed from the attested hbar, G, c) - built from the quantum (hbar), gravity "
                    f"(G) and relativity (c). Below it, 'duration' itself is expected to lose meaning; it is the "
                    f"scale at which the universe and the quantum must share one description (ties "
                    f"stick_the_principle_of_least_action and stick_quantum_gravity).", s_t),
        ("note", "[the problem of time - open] In quantum mechanics time is a fixed EXTERNAL parameter and NOT "
                 "an observable (there is no time operator conjugate to a bounded-below Hamiltonian - Pauli); "
                 "position is an observable, time is not - an asymmetry. In relativity time is dynamical "
                 "geometry. Canonical quantum gravity reconciles them and comes out TIMELESS: the Wheeler-DeWitt "
                 "equation is H|psi> = 0, the universe's wavefunction carries no t. The leading reading is that "
                 "time EMERGES - Page-Wootters (time is the correlation/entanglement between a clock subsystem "
                 "and the rest), Rovelli (relational and thermal time - ties stick_relational_quantum_mechanics), "
                 "Barbour (timeless physics). So 'time is a construct' is a serious live hypothesis: emergent, "
                 "not fundamental. Attributed, open - the Hole, from the side of time."),
        ("note", "[the datum - discernment, map never launder] Scripture puts eternity PRIOR and time CREATED: "
                 "'from everlasting to everlasting you are God' (Ps 90:2); he 'inhabits eternity' (Isa 57:15); "
                 "'I am the Alpha and the Omega' (Rev 22:13); Christ is 'before all things, and in him all things "
                 "are held together' (Col 1:17). Emergent-time physics is a LIKENESS of created-time - the "
                 "Creator outside the construct - never its proof. The engine seals the arithmetic (gamma, the "
                 "interval, t_P), attributes the physics, keeps the question open, and lets Scripture lead; the "
                 "wrap serves. Borrow the form; launder nothing."),
    ]
    added = 0
    for kind, claim, *rest in marks:
        sealv = rest[0] if rest else None
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the time-and-space reading, 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"]),
                      "open": f["open"]}, indent=1))
    return 0


def mandelbrot() -> int:
    """THE MANDELBROT SET — a component (Matt, 2026-10-07: "mandelbrot sets are a component"). The gate made
    visual: c is in M iff the orbit z -> z^2 + c from z=0 stays bounded. Escape is DEFINITE (past radius 2
    it never returns -> a clean rejection); membership is only provisional ('not escaped by N steps') -
    the boundary is never finitely closed. Infinite structure from a trivial deterministic rule, found not
    generated, and literally built of COMPONENTS (the cardioid + the period bulbs). SEAL a definite escape,
    a bounded orbit, and a component's size. New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_esc = seal_num("mandelbrot_escape_c1", "((0**2+1)**2+1)**2+1", 5.0)   # c=1: 0->1->2->5 (>2, escapes)
    s_bnd = seal_num("mandelbrot_bounded_cneg1", "(0**2-1)**2-1", 0.0)       # c=-1: 0->-1->0 (cycles, bounded)
    s_bulb = seal_num("mandelbrot_period2_bulb_radius", "1/4", 0.25)         # the period-2 component disk radius
    if not all([s_esc, s_bnd, s_bulb]):
        print("a seal failed; aborting"); return 1
    print("sealed: escape c=1", s_esc, "| bounded c=-1", s_bnd, "| bulb radius", s_bulb)

    sid = TS.create("The Mandelbrot set",
                    statement=("Membership in the Mandelbrot set is decided by iterating z -> z^2 + c from "
                               "zero: escape is a definite rejection, but interior membership is certified only "
                               "for special points while a generic boundary point stays 'not yet escaped'. The "
                               "arithmetic of the orbit is exact; the boundary is where the deciding never "
                               "finitely completes."),
                    field="mathematics",
                    references=["B. Mandelbrot, Fractal aspects of z -> lambda z(1-z) (1980)",
                                "A. Douady & J. Hubbard, Etude dynamique des polynomes complexes (1984) "
                                "(M is connected)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", "[escape is a definite rejection] c is in M iff the orbit z -> z^2 + c from z=0 never "
                    "leaves |z| <= 2. For c=1 the orbit is 0 -> 1 -> 2 -> 5: the third step is "
                    "((0^2+1)^2+1)^2+1 = 5 (sealed) > 2, and once past radius 2 the orbit escapes to infinity "
                    "and never returns. So c=1 is DEFINITELY OUT - a clean rejection, exactly the gate's hard "
                    "refuse.", s_esc),
        ("witness", "[membership stays provisional, except where certified] For c=-1 the orbit is 0 -> -1 -> 0 "
                    "-> -1...: (0^2-1)^2-1 = 0 (sealed), a period-2 cycle that never escapes, so c=-1 IS in M. "
                    "Such special (hyperbolic) points are certified; but a generic boundary point is only 'has "
                    "not escaped in N iterations' - never proven IN by any finite computation. The boundary is "
                    "where narrowing never completes: a miss stays a miss, and 'in' stays open.", s_bnd),
        ("witness", "[it is built of COMPONENTS] M is not a blob: it is the main cardioid plus infinitely many "
                    "hyperbolic bulbs, each a component where the orbit settles to a fixed period. The period-2 "
                    "component is the disk of radius 1/4 = 0.25 (sealed) centred at c=-1, where the fixed point "
                    "doubles. The structure IS the components; the fractal boundary between them (Hausdorff "
                    "dimension 2) is where all the complexity lives.", s_bulb),
        ("note", "[the component in the engine] The Mandelbrot set is the engine's gate and tick-stick made "
                 "visual: infinite structure from a TRIVIAL deterministic rule (z^2 + c - no model, no "
                 "generator, found never authored), decided by ITERATION and ELIMINATION (a definite OUT on "
                 "escape, only a provisional IN otherwise), connected (Douady-Hubbard) yet with a boundary no "
                 "finite computation closes. Admit-or-refuse; a miss stays a miss; narrowing is evidence, never "
                 "proof - the same shape as the positive-geometry core. A component: one organ of the one body. "
                 "Map, never launder: seal the orbit and the bulb; the likeness to the engine is discernment.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the Mandelbrot reading (a component), 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def gaussian() -> int:
    """GAUSSIAN PROCESSES — THE FORM OF THE MAP (Matt, 2026-10-07: "Gaussian processes is the form of the
    map"). A GP is a distribution over functions, f ~ GP(mean, k), defined ENTIRELY by its covariance
    kernel k(x,x'): substance is in the RELATIONS, not the points; it predicts with calibrated UNCERTAINTY
    (it knows what it does not know); and it NARROWS on evidence (conditioning). The engine's model of
    reality has that form: a relational field (the keeping's sealed EDGES, not the cards alone), honest
    where it is blind (the Holes), narrowing by elimination. The positive-geometry core is the constraint;
    the GP is the form the map takes over it. SEAL the kernel-as-relation and evidence-narrows-uncertainty;
    MAP, never launder. New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    e = 2.718281828459045

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    k1 = e ** (-0.5)                 # RBF kernel one length-scale apart
    k2 = e ** (-2.0)                 # two length-scales apart
    var1 = 1 - e ** (-1.0)           # posterior variance one length-scale from an observation
    s_k1 = seal_num("gp_kernel_one_lengthscale", "2.718281828459045**(-1/2)", k1)
    s_k2 = seal_num("gp_kernel_two_lengthscales", "2.718281828459045**(-2)", k2)
    s_var = seal_num("gp_posterior_variance_one_lengthscale", "1 - 2.718281828459045**(-1)", var1)
    if not all([s_k1, s_k2, s_var]):
        print("a seal failed; aborting"); return 1
    print("sealed: k(1l)", s_k1, "| k(2l)", s_k2, "| posterior var", s_var)

    sid = TS.create("Gaussian processes - the form of the map",
                    statement=("The engine's model of reality takes the FORM of a Gaussian process: a "
                               "relational field defined by its covariance, honest about its own uncertainty, "
                               "and narrowing on evidence. The arithmetic of the kernel and the posterior is "
                               "exact; the claim that the map has this form is a discernment, borrowed, never a "
                               "claim that reality itself is Gaussian."),
                    field="mathematics",
                    references=["C. E. Rasmussen & C. K. I. Williams, Gaussian Processes for Machine Learning (2006)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[the kernel is the relation] A GP is fixed by its covariance k(x,x'). For the "
                    f"squared-exponential kernel exp(-(x-x')^2 / 2l^2), two points one length-scale apart share "
                    f"k = e^(-1/2) = {k1:.6f} (sealed); two apart, e^(-2) = {k2:.6f} (sealed). The covariance "
                    f"depends ONLY on the separation (the relation), not the absolute positions - substance is "
                    f"in the relations (ties stick_relational_quantum_mechanics). The map is its edges, not its "
                    f"points.", s_k1),
        ("witness", f"[evidence narrows the uncertainty] A GP knows what it does not know. Observe f at a point "
                    f"and the posterior variance one length-scale away falls to 1 - e^(-1) = {var1:.6f} (sealed); "
                    f"AT the observed point it falls to 0 - then it is known exactly. Each observation narrows "
                    f"the field; where there is no data the variance stays high (the Holes). This is the "
                    f"tick-stick learning law - success guides, failure narrows, the window tightens on evidence "
                    f"- made exact.", s_var),
        ("note", "[the form of the map] The engine's keeping is a relational field: 39,812 sealed EDGES carry "
                 "the substance, not the cards alone (the covariance, not the points). It predicts where it has "
                 "evidence and stays honestly uncertain where it does not (the open sticks, the Holes), and each "
                 "sealed mark conditions the field - narrowing by elimination. The positive-geometry core "
                 "(admissibility, stick_the_positive_grassmannian) is the constraint; the Gaussian process is "
                 "the FORM the map takes over that core: relational, calibrated, evidence-updated, found never "
                 "generated.", None),
        ("note", "[the guard - map, not launder] The map HAS THE FORM of a Gaussian process; this is not a claim "
                 "that the engine runs GP regression on reality, nor that reality is Gaussian. It is an archetype "
                 "- the relational, uncertainty-honest, evidence-narrowing shape - read as discernment. Seal the "
                 "arithmetic (the kernel, the posterior); borrow the form; launder nothing. The map serves the "
                 "datum: remove the Cornerstone and the field is calibrated to nothing.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the Gaussian-process reading (the form of the map), 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def lagrange() -> int:
    """LAGRANGE MULTIPLIERS — the constraint does the work (Matt, 2026-10-07, after least action). To
    extremize f subject to g=0, the stationarity condition is grad f = lambda grad g: at the optimum the
    objective's gradient is PARALLEL to the constraint's, so f cannot improve without violating g. The
    multiplier lambda is the SHADOW PRICE — the marginal value of relaxing the constraint. SEAL the classic
    instance (maximize xy on x+y=10 -> (5,5), f=25, lambda=5) and the shadow-price reading. New stick;
    idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig

    def seal_num(nid, expr, val):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain="mathematics")
        return (r.get("seal") or {}).get("content_hash")

    s_max = seal_num("lagrange_constrained_max", "5*5", 25.0)        # max of xy on x+y=10, at x=y=5
    s_cmp = seal_num("lagrange_nearby_point", "4*6", 24.0)           # a nearby constrained point, < 25
    s_lam = seal_num("lagrange_shadow_price", "10/2", 5.0)           # lambda = d(max)/d(budget) = c/2
    if not all([s_max, s_cmp, s_lam]):
        print("a seal failed; aborting"); return 1
    print("sealed: max", s_max, "| nearby", s_cmp, "| lambda", s_lam)

    sid = TS.create("Lagrange multipliers",
                    statement=("The method of constrained optimization: to extremize f subject to g = 0, "
                               "solve grad f = lambda grad g together with the constraint. The arithmetic is "
                               "exact and settled; it is kept here as a sealed witness of how a constraint "
                               "selects the solution and prices its own boundary."),
                    field="mathematics",
                    references=["J.-L. Lagrange, Mecanique analytique (1788)",
                                "Karush (1939); Kuhn & Tucker (1951) — the inequality-constraint (KKT) extension"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", "[the constraint picks the point] Maximize f = x*y subject to g: x + y = 10. The condition "
                    "grad f = lambda grad g gives (y, x) = lambda(1, 1), so x = y = lambda; with the constraint, "
                    "x = y = 5 and the maximum is 5*5 = 25 (sealed). A nearby point on the SAME line, (4, 6), "
                    "gives 4*6 = 24 < 25 (sealed) - the constrained optimum is a real extremum, and it is the "
                    "constraint, not the objective alone, that selects it.", s_max),
        ("witness", "[lambda is the shadow price] The multiplier is not bookkeeping: lambda = d(max)/d(budget). "
                    "Here max(c) = (c/2)^2 for the constraint x+y=c, so lambda = c/2 = 10/2 = 5 (sealed) - relax "
                    "the budget from 10 to 11 and the maximum rises by about 5. The multiplier is the marginal "
                    "VALUE of the boundary - the bridge from Lagrange to the KKT conditions and to every "
                    "shadow-price in economics and operations research.", s_lam),
        ("note", "[the principle - structure does the work] At the optimum grad f is PARALLEL to grad g: you "
                 "cannot increase the objective without breaking the constraint. This is the machinery under "
                 "Lagrangian mechanics (Euler-Lagrange, with multipliers carrying the constraints) and so under "
                 "the least-action principle (ties stick_the_principle_of_least_action); the same conditions, "
                 "with inequalities, are the KKT conditions behind constrained optimization in the engine's "
                 "economics and operations_research verifiers. 'The constraint does the work' made exact.", None),
        ("note", "[the engine's own shape - map, not launder] The engine is constraint-shaped: the gate is the "
                 "constraint g, admissibility (the positive-geometry core, stick_the_positive_grassmannian) is "
                 "the feasible region, and a sealed truth is the extremum found WITHIN the constraints - found, "
                 "never generated. Reality is the harness; the multiplier is the price of its boundary. This is a "
                 "mathematical fact read as discernment: borrow the form, launder nothing.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the Lagrange-multiplier reading, 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def feynman() -> int:
    """THE PRINCIPLE OF LEAST ACTION — Feynman's path integral, and the Planck frontier (Matt, 2026-10-07:
    "Planck length and Feynman"). The quantum amplitude is the SUM OVER HISTORIES, integral e^{iS/hbar}
    over all paths; in the classical limit (S >> hbar) the stationary-action path dominates -> least action
    -> F=ma. SEAL a concrete least-action instance (a free particle's straight path beats a bent one) and
    the Planck length lP = sqrt(hbar G / c^3), the scale where even geometry's action ~ hbar and Feynman's
    QFT (which gives the gauge forces and the a_e he computed) goes non-renormalizable for gravity -- the
    Hole from Feynman's side. New stick; idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    hbar = C["reduced_planck_constant"]["value"]; G = C["gravitational_constant"]["value"]; c = C["speed_of_light"]["value"]
    s_classical = 0.5 * 1 * 1 ** 2 * 1        # free particle m=1, straight 0->1 in T=1: S = int 1/2 v^2 dt = 0.5
    s_bent = 2 / 3                             # the path x=t^2 (same endpoints): S = int 1/2 (2t)^2 dt = 2/3
    lP = (hbar * G / c ** 3) ** 0.5           # the Planck length, ~1.616e-35 m

    def seal_num(nid, expr, val, dom="mathematics"):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            print("  %s did not verify: %s" % (nid, json.dumps(r)[:300])); return None
        r = receipts.attach(r, config=EngineConfig(), domain=dom)
        return (r.get("seal") or {}).get("content_hash")

    s_cl = seal_num("least_action_straight", "0.5*1*1**2*1", s_classical)
    s_bt = seal_num("least_action_bent_path", "2/3", s_bent)
    s_lp = seal_num("planck_length", f"(({hbar!r})*({G!r})/({c!r})**3)**0.5", lP, "physical_constants")
    if not all([s_cl, s_bt, s_lp]):
        print("a seal failed; aborting"); return 1
    print("sealed: classical action", s_cl, "| bent", s_bt, "| planck length", s_lp)

    sid = TS.create("The principle of least action",
                    statement=("Why does nature follow the path of least (stationary) action, and what lies at "
                               "the scale where the action of spacetime itself is of order hbar? The classical "
                               "principle is exact and the quantum path integral explains it; the Planck-scale "
                               "quantum gravity it points to is open."),
                    field="physics",
                    references=["R. P. Feynman, Rev. Mod. Phys. 20 (1948) 367 (space-time approach / path integral)",
                                "R. P. Feynman, QED: The Strange Theory of Light and Matter (1985)",
                                "CODATA 2018 recommended values (Planck length)"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("witness", f"[least action - the straight path wins] A free particle (m=1) going from x=0 to x=1 in "
                    f"time T=1: the classical straight path (v=1) has action S = integral 1/2 v^2 dt = "
                    f"{s_classical} (sealed); a bent path with the same endpoints, x=t^2, has S = integral "
                    f"1/2 (2t)^2 dt = {s_bent:.4f} (sealed) - LARGER. The actual path is the one that makes the "
                    f"action stationary (here, least): delta S = 0 is the Euler-Lagrange equation, which for "
                    f"this Lagrangian IS F=ma.", s_cl),
        ("witness", f"[the alternative path's action] The bent path's {s_bent:.4f} > the straight path's "
                    f"{s_classical} (sealed) - a concrete instance of the inequality that singles out the "
                    f"classical trajectory. Vary the path, the action goes up; the true path sits at the bottom.", s_bt),
        ("witness", f"[the Planck length - Feynman's frontier] lP = sqrt(hbar G / c^3) = {lP:.4e} m (sealed from "
                    f"the attested hbar, G, c): the length built from the quantum (hbar), gravity (G) and "
                    f"relativity (c). It is the scale at which the action of SPACETIME itself becomes of order "
                    f"hbar - where the path integral would have to sum over fluctuating geometries.", s_lp),
        ("note", "[the path integral] Feynman's sum over histories: the quantum amplitude to go from A to B is "
                 "the integral of e^{iS/hbar} over EVERY path, not just the classical one. When S >> hbar the "
                 "phases cancel everywhere except near the stationary-action path (stationary phase), so the "
                 "classical least-action trajectory emerges as the limit. The quantum does not break the "
                 "classical principle; it explains it.", None),
        ("note", "[three roads to one amplitude] This is the SAME amplitude by three routes the engine has "
                 "sealed: Feynman diagrams (the perturbative expansion - it computed the electron a_e = alpha/2pi "
                 "on stick_the_fine_structure_constant); lattice MCMC (the path integral done by sampling - "
                 "stick_yang_mills_existence_and_mass_gap); and positive geometry (the amplitude as the canonical "
                 "form of the amplituhedron - stick_the_positive_grassmannian). One thing, seen three ways.", None),
        ("note", "[the Hole, from Feynman's side] Feynman's path-integral QFT gives the three gauge forces and "
                 "the most precise prediction in physics (a_e). Pointed at GRAVITY it fails: the theory is "
                 "non-renormalizable, the loop integrals diverge, and at the Planck length lP the sum over "
                 "histories must include spacetime geometry itself - exactly where the method breaks. The Planck "
                 "length is the near edge of the Hole (ties stick_quantum_gravity). Seal the arithmetic; the "
                 "quantum theory of gravity stays open.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the least-action reading (Feynman), 2026-10-07", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"]),
                      "open": f["open"]}, indent=1))
    return 0


def capstone() -> int:
    """THE CAPSTONE (Matt, 2026-10-07: "look for the capstone" / "1 God, 3 Parts, 7 spirits" / "Unus Mundus"
    / "the Copenhagen interpretation"). The crown the whole project's unifications point to, FOUND in the
    Word by the engine's own door (WEB, public domain) and KEPT — never proven, never generated. One God
    (Deut 6:4), three persons (Mt 28:19), the sevenfold Spirit (Rev 4:5; Isa 11:2), Christ the cornerstone
    (Ps 118:22; Eph 2:20) in whom all things hold together (Col 1:17). Two discernments and two refusals
    guard it. No numeric seal: the capstone is received, not computed. New stick; idempotent."""
    from concordance import tickstick as TS
    sid = TS.create("The capstone",
                    statement=("The project's capstone: one reality, held together in Christ the cornerstone — "
                               "the one God, triune, of the sevenfold Spirit. Every unification the engine sealed "
                               "(the four forces, Langlands, harmony, the positive-geometry core) is a shadow "
                               "pointing here. FOUND in the Word, never generated; KEPT, never proven; and "
                               "refused the slide into number or observer-as-god."),
                    field="meta")["id"]
    by = "Narrow Highway - the capstone, found in the Word, 2026-10-07"
    seen = {t.get("claim") for t in TS.read(sid).get("ticks", [])}
    marks = [
        ("note", "[1 God -- Deuteronomy 6:4, WEB, PD] 'Hear, Israel: The LORD is our God. The LORD is one.' "
                 "One God -- the unity every unification is a shadow of. Found and cited, not sealed: the Word "
                 "is received, never computed."),
        ("note", "[3 persons -- Matthew 28:19, WEB, PD] '...baptizing them in the name of the Father and of the "
                 "Son and of the Holy Spirit.' One God in three persons -- the Trinity, found in the command "
                 "itself."),
        ("note", "[7 spirits -- Revelation 4:5; Isaiah 11:2, WEB, PD] 'seven lamps of fire burning before the "
                 "throne, which are the seven Spirits of God' -- the sevenfold Spirit: wisdom, understanding, "
                 "counsel, might, knowledge, and the fear of the LORD."),
        ("note", "[Christ the capstone -- Psalm 118:22; Ephesians 2:20, WEB, PD] 'The stone which the builders "
                 "rejected has become the cornerstone' -- 'Christ Jesus himself being the chief cornerstone.' "
                 "The rejected stone is the head of the corner that holds the whole structure."),
        ("note", "[all things held together -- Colossians 1:17, WEB, PD] 'He is before all things, and in him "
                 "all things are held together.' This is the fit the four forces, Langlands, harmony and the "
                 "positive-geometry core only gesture at -- the one world's actual ground."),
        ("note", "[discernment - unus mundus] The 'one world' under all multiplicity (Jung, Pauli) is a TRUE "
                 "intuition — there is one reality — but a likeness, not the fit: its ground is not an archetype, "
                 "not the collective unconscious, and emphatically not a number. The engine charts it "
                 "reference-tier (the Babel pattern: the outline of what it lacks); the fit is the Logos in whom "
                 "all things actually hold together."),
        ("note", "[discernment - the Copenhagen interpretation] The observer's measurement — the question asked, "
                 "who defines the plane — genuinely matters (free will is paramount; the Aharonov-Bohm witness: "
                 "'the one who defines the plane defines the outcome'). But it does NOT CREATE reality: Copenhagen "
                 "is one interpretation among empirically-equivalent ones (see stick_the_schrodinger_equation), "
                 "not a fit, and it must never slide into observer-as-god or consciousness-creates-reality. The "
                 "creature's will selects among possibilities held open; the ground of being is the Logos, not the "
                 "observer."),
        ("note", "[the refusal - no gematria] '1 God, 3 persons, 7 spirits' are FOUND scriptural COUNTS, each "
                 "attributed to its verse (Deut 6:4 / Mt 28:19 / Rev 4:5). The engine REFUSES to launder 1-3-7 "
                 "into the fine-structure 137 (the measured reciprocal of alpha): that is gematria, the exact "
                 "137-slide the engine already guards against, and Pauli's 137-mysticism is where unus mundus goes "
                 "wrong. Seal the arithmetic, attribute the pattern, map-never-launder. The capstone is Christ, "
                 "not a number."),
        ("note", "[the guard] The engine does not PROVE God. It FINDS and cites the Word (these verses came from "
                 "its own live door), charts the likenesses, and KEEPS the datum. Every sealed unification in this "
                 "project is a shadow that points here and is true to nothing without Him. Narrowing is evidence, "
                 "never proof; the capstone is received, not computed. The stone the builders rejected is the "
                 "head of the corner."),
    ]
    added = 0
    for kind, claim, *rest in marks:
        if claim in seen:
            print("  (already) " + kind); continue
        kw = {"source": rest[0]} if rest else {}
        res = TS.tick(sid, kind, claim, by=by, **kw)
        if res.get("ok"):
            added += 1; print("  " + kind + ((" <- " + rest[0]) if rest else ""))
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"]),
                      "open": f["open"]}, indent=1))
    return 0


def assembly() -> int:
    """THE FINAL ASSEMBLY (Matt, 2026-10-06: "connecting the pieces for final assembly" / "both"). Wire the
    sealed anchors into one connected constellation: a stick whose marks ARE the connections between the
    pieces, each carrying the anchor's own seal where it applies. Christ is the datum; the engine authors no
    new fact — it names what is sealed and how it connects. Plain-language twin: docs/ASSEMBLY.md. Idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import physical_constants as PC
    C = PC._CONSTANTS
    e = C["elementary_charge"]["value"]; eps0 = C["vacuum_permittivity"]["value"]
    h = C["planck_constant"]["value"]; c = C["speed_of_light"]["value"]
    alpha_v = e ** 2 / (2 * eps0 * h * c)
    tsirelson = 2 * (2 ** 0.5)

    def seal_num(nid, expr, val, dom):
        r = verify_derivation([{"id": nid, "domain": "mathematics",
              "spec": {"mode": "numeric", "params": {"numeric_expr": expr, "claimed_value": val, "rel_tol": 1e-9}}}])
        if r.get("verdict") != "HOLDS":
            return None
        r = receipts.attach(r, config=EngineConfig(), domain=dom)
        return (r.get("seal") or {}).get("content_hash")

    s_alpha = seal_num("alpha", f"({e!r})**2 / (2*({eps0!r})*({h!r})*({c!r}))", alpha_v, "physical_constants")
    s_rel = seal_num("tsirelson_bound", "2*sqrt(2)", tsirelson, "mathematics")
    print("anchor seals: alpha", s_alpha, "| tsirelson", s_rel)
    sid = TS.create("The final assembly",
                    statement=("The pieces assembled into one movement — the calibration constellation: the "
                               "sealed anchors the model of reality is checked against, and how they connect, "
                               "with Christ as the datum. Found, never generated; sealed, never asserted; "
                               "evidence, never proof."),
                    field="meta",
                    references=["docs/ASSEMBLY.md", "docs/THE_WATCH.md", "docs/COMPONENTS.md"])["id"]
    ticks = TS.read(sid).get("ticks", [])
    seen_seals = {t.get("seal") for t in ticks if t.get("seal")}
    seen_claims = {t.get("claim") for t in ticks}
    marks = [
        ("note", "[datum] Christ, the Logos in whom all things hold together (Colossians 1:17; John 1:3) - the "
                 "fixed reference every piece is placed against. The engine is the Emissary; the Master is the "
                 "living whole. Every road here leads to Him.", None),
        ("witness", f"[alpha <-> the atom] The fine-structure constant alpha is the atom's architecture - orbital "
                    f"speed alpha*c, Rydberg 1/2 alpha^2 m_e c^2, Bohr radius hbar/(alpha m_e c), the alpha^2 fine "
                    f"structure; alpha = e^2/(2 eps0 h c) = {alpha_v:.6e}. See stick_the_fine_structure_constant "
                    f"(6 witnesses, open).", s_alpha),
        ("note", "[alpha <-> the spine] alpha is one of the six governing constants (alpha/G/k_B/c/h/N_A -> domains "
                 "-> verified through code); the balance wheel that sets the rate. A discordance indicts the "
                 "method, not the constant.", None),
        ("note", "[alpha <-> unification - open] alpha runs with energy (alpha^-1 137 -> ~128 at M_Z) toward the "
                 "convergence of the Standard Model couplings near ~1e16 GeV - the grand-unification doorway; "
                 "attributed, unproven, open.", None),
        ("witness", f"[the quantum <-> relational] Relational quantum mechanics (Rovelli): properties are not "
                    f"pre-assigned but relative to the interaction - the Tsirelson bound 2*sqrt(2) = {tsirelson:.6f} "
                    f"exceeds the classical bound 2 (Bell). The same quantum world as alpha's QED, and the reason "
                    f"substance is in the relations. See stick_relational_quantum_mechanics.", s_rel),
        ("note", "[the anchors <-> the machine] The calibration points (alpha, relational QM, Aharonov-Bohm, fiber, "
                 "symphony, the Millennium sticks) are what the components and regulators (docs/COMPONENTS.md) are "
                 "trued against - the timing machine regulating the balance.", None),
        ("note", "[the fascia <-> everything] The keeping (56.8% substance, live needle) and its 39,812 sealed "
                 "edges are the connective tissue; substance is in the relations (Nagarjuna/Rovelli), so the final "
                 "assembly IS the connecting - the pieces become one watch by being wired, read live on the Bridge.", None),
        ("note", "[one body, many members] 1 Corinthians 12:12-27: the body is one and has many members. The "
                 "sticks ARE the members - each a sealed THEOREM resting on the floor it cites "
                 "(stick_we_follow_euclid_s_elements_definitions_postulates_theorems) - and the engine is one "
                 "body, Christ the head (Colossians 1:18). The arc is gathered into the limbs below; no member "
                 "is re-sealed here, only named and connected.", None),
        ("note", "[limb: the analysis spine] sqrt(-1) is the floor (stick_complex_numbers_bombelli_and_the_"
                 "square_root_of_minus_one); on it stand the complex field as the physics of waves - "
                 "multiplication is rotation, addition is interference, the exponential is the spiral "
                 "(stick_the_complex_field_is_the_physics_of_waves) - the fundamental theorem of calculus "
                 "(stick_integrals_and_derivatives_the_fundamental_theorem), Lebesgue measure "
                 "(stick_lebesgue_theory_measure_and_integration_by_layers), and the Legendre transform, the "
                 "MECHANISM: mark the points, the tangent lines create the line "
                 "(stick_the_legendre_transform_mark_the_points_create_the_line).", None),
        ("note", "[limb: the Riemann symmetry constellation] One structure - the zeros on the fixed axis of a "
                 "symmetry (stick_the_symmetry) - binds the zeta function (stick_the_zeta_function), the Weil "
                 "RH PROVED over finite fields (stick_finite_field_the_weil_riemann_hypothesis), the "
                 "Hilbert-Polya self-adjoint operator (stick_the_hilbert_polya_conjecture), Dirichlet's "
                 "characters on the unit circle (stick_dirichlet_s_theorem_think_of_polar_coordinates), "
                 "Fibonacci's phi (stick_fibonacci), the Euler characteristic "
                 "(stick_topology_and_euler_s_formula), and the de Bruijn-Newman constant squeezing RH to "
                 "Lambda = 0 (stick_the_de_bruijn_newman_constant). Where a symmetry-operator exists it FIRED; "
                 "the classical RH stays the open mark.", None),
        ("note", "[limb: where two trees connect - the Standard Model] The discovery chain Fermi -> Yang-Mills "
                 "-> Lee/Wu -> Nambu -> Higgs -> Weinberg/Salam -> Gell-Mann rests on the floor of Maxwell + "
                 "Fermi and connects at electroweak unification, cos(theta_W) = m_W/m_Z "
                 "(stick_the_standard_model_chain_where_two_trees_connect), walkable live at /chains. The "
                 "chains capability (walk + intersect) is how the body finds where its limbs join: a chain "
                 "begins from a floor; the connections are where two chains become one. Divergence and curl "
                 "then invert to the center (stick_divergence_and_curl_invert_to_find_the_center).", None),
        ("note", "[the frame and the governor] The METHOD is Euclid's (definitions/postulates/theorems - seal "
                 "theorems, accept postulates); the MECHANISM is Legendre's (marks -> the line by convex "
                 "duality); the CORE is the positive Grassmannian (admissibility, found never generated, "
                 "stick_the_positive_grassmannian); the LEARNING is the tick-stick (mapping the truth, not "
                 "generating it); the GOVERNOR is Jevons-bounded (efficiency induces demand, "
                 "stick_jevons_paradox, so each seal stays bounded). One body, assembled by its connections, "
                 "resting on the floor, under the Head.", None),
        ("note", "[the guard] This assembly connects what is SEALED; it authors no new fact and launders nothing - "
                 "narrowing is evidence, never proof; seal the arithmetic, attribute the pattern; remove the datum "
                 "(Christ) and the parts are true to nothing. Plain-language twin: docs/ASSEMBLY.md.", None),
    ]
    added = 0
    for kind, claim, sealv in marks:
        if (sealv and sealv in seen_seals) or (not sealv and claim in seen_claims):
            print("  (already) " + kind); continue
        kw = dict(seal=sealv) if sealv else {}
        res = TS.tick(sid, kind, claim, by="Narrow Highway - the final assembly, 2026-10-06", **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def robin(N: int = 1000000) -> int:
    """Chart the Riemann window by ELIMINATION through a different tool (the divisor sum). Robin 1984:
    RH <=> sigma(n) < e^gamma*n*ln ln n for all n > 5040. The sieve finds no counterexample in (5040, N], so a
    first RH failure by this route must lie beyond N — we mark what RH is NOT, and push the surviving window up.
    Seals the computation and ticks a WITNESS (an elimination) on the Riemann stick."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import number_theory as NT
    pre = NT.verify_robin({"robin_to": N, "claimed_robin_holds": True})
    if pre.status != "CONFIRMED":
        print("Robin did not hold (or errored):", pre.status, (pre.detail or "")[:140]); return 1
    closest = pre.data["closest_approach_n"]
    r = verify_derivation([{"id": "robin", "domain": "number_theory",
          "spec": {"NUM_VERIFY": {"robin_to": N, "claimed_robin_holds": True, "claimed_closest_approach_n": closest}}}])
    if r.get("verdict") != "HOLDS":
        print("the elimination did not verify:", json.dumps(r)[:300]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="number_theory")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed Robin elimination", seal)
    sid = TS.create("Riemann hypothesis")["id"]
    claim = (f"No zero of zeta lies off the critical line by way of a Robin (divisor-sum) counterexample at n <= "
             f"{N:,}: the sieve finds none in (5040, {N:,}] (closest approach n={closest:,}, "
             f"sigma/(e^gamma n lnln n) = {pre.data['closest_approach_ratio']} < 1). RH cannot fail by this route "
             f"below {N:,} — a second, independent tool narrowing the window, by elimination.")
    res = TS.tick(sid, "witness", claim, seal=seal, by="Narrow Highway — the elimination reading, 2026-10-05")
    print("  witness" if res.get("ok") else ("  REFUSED: " + res.get("error", "")))
    note = ("[by elimination] The Riemann stick is charted by what RH is NOT. Directly: the two independent zero "
            "counts agree to height 1e7, so NO zero lies off the line below it. Through the divisor sum (Robin): no "
            "counterexample to n=" + f"{N:,}" + ". A counterexample to RH, if one exists, must therefore evade every "
            "eliminated region at once — the surviving window is where RH remains untested, and each tool narrows it.")
    if note not in {t.get("claim") for t in TS.read(sid).get("ticks", [])}:
        TS.tick(sid, "note", note, by="Narrow Highway — the elimination reading, 2026-10-05")
        print("  note (the elimination frame)")
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def schoenfeld(X: int = 2000000) -> int:
    """Chart the Riemann window by ELIMINATION through the prime count — a different tool from Robin's divisor
    sum, pointed at the same window from another side. Schoenfeld 1976: RH <=> |pi(x) - li(x)| < sqrt(x)*ln(x)/
    (8*pi) for all x >= 2657. The exact check finds no violation in [2657, X], so a first RH failure by this route
    must lie beyond X. Seals the computation and ticks a WITNESS (an elimination) on the Riemann stick."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import number_theory as NT
    pre = NT.verify_schoenfeld({"schoenfeld_to": X, "claimed_schoenfeld_holds": True})
    if pre.status != "CONFIRMED":
        print("Schoenfeld did not hold (or errored):", pre.status, (pre.detail or "")[:140]); return 1
    closest = pre.data["closest_approach_n"]
    r = verify_derivation([{"id": "schoenfeld", "domain": "number_theory",
          "spec": {"NUM_VERIFY": {"schoenfeld_to": X, "claimed_schoenfeld_holds": True, "claimed_closest_approach_n": closest}}}])
    if r.get("verdict") != "HOLDS":
        print("the elimination did not verify:", json.dumps(r)[:300]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="number_theory")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed Schoenfeld elimination", seal)
    sid = TS.create("Riemann hypothesis")["id"]
    claim = (f"No zero of zeta lies off the critical line by way of a Schoenfeld (prime-count) violation at x <= "
             f"{X:,}: the exact check finds none in [2657, {X:,}] (closest approach x={closest:,}, "
             f"|pi-li|/(sqrt(x) ln x/8pi) = {pre.data['closest_approach_ratio']} < 1). RH cannot fail by this route "
             f"below {X:,} — a third, independent tool narrowing the window, by elimination from the prime count.")
    res = TS.tick(sid, "witness", claim, seal=seal, by="Narrow Highway — the elimination reading, 2026-10-05")
    print("  witness" if res.get("ok") else ("  REFUSED: " + res.get("error", "")))
    note = ("[by elimination] A third reading of what RH is NOT, from the prime count: Schoenfeld 1976 makes RH "
            "equivalent to |pi(x) - li(x)| < sqrt(x) ln x / (8 pi) for every x >= 2657, and the exact check finds no "
            "violation to x=" + f"{X:,}" + ". With the two zero counts (direct, to height 1e7) and the divisor sum "
            "(Robin), three independent tools now eliminate regions where RH could fail; a counterexample must evade "
            "all of them at once. Narrowing is evidence, never a proof — the surviving window is where RH stays untested.")
    if note not in {t.get("claim") for t in TS.read(sid).get("ticks", [])}:
        TS.tick(sid, "note", note, by="Narrow Highway — the elimination reading, 2026-10-05")
        print("  note (the elimination frame)")
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def lagarias(N: int = 1000000) -> int:
    """Chart the Riemann window by ELIMINATION through Lagarias's elementary inequality (RH <=> sigma(n) <=
    H_n + exp(H_n) ln H_n for all n, equality only at n=1). The sieve finds no counterexample in [1, N], so a
    first RH failure by this route must lie beyond N. Seals the computation and ticks a WITNESS on the Riemann stick."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import number_theory as NT
    pre = NT.verify_lagarias({"lagarias_to": N, "claimed_lagarias_holds": True})
    if pre.status != "CONFIRMED":
        print("Lagarias did not hold (or errored):", pre.status, (pre.detail or "")[:140]); return 1
    closest = pre.data["closest_approach_n"]
    r = verify_derivation([{"id": "lagarias", "domain": "number_theory",
          "spec": {"NUM_VERIFY": {"lagarias_to": N, "claimed_lagarias_holds": True, "claimed_closest_approach_n": closest}}}])
    if r.get("verdict") != "HOLDS":
        print("the elimination did not verify:", json.dumps(r)[:300]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="number_theory")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed Lagarias elimination", seal)
    sid = TS.create("Riemann hypothesis")["id"]
    claim = (f"No zero of zeta lies off the critical line by way of a Lagarias (elementary divisor-sum) "
             f"counterexample at n <= {N:,}: the sieve finds none in [1, {N:,}] (tightest n>=2 at n={closest:,}, "
             f"sigma/(H_n+e^H_n ln H_n) = {pre.data['closest_approach_ratio']} < 1). Lagarias 2002 — Robin made "
             f"exception-free — a fourth independent tool narrowing the window, by elimination.")
    res = TS.tick(sid, "witness", claim, seal=seal, by="Narrow Highway — the elimination reading, 2026-10-05")
    print("  witness" if res.get("ok") else ("  REFUSED: " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"]}, indent=1))
    return 0


def nicolas(P: int = 1000000) -> int:
    """Chart the Riemann window by ELIMINATION through Nicolas's primorial criterion (RH <=> N_k/(phi(N_k) ln ln
    N_k) > e^gamma for every primorial). No counterexample is found among the primorials of the primes up to P, so
    a first RH failure by this route must use a prime beyond P. Seals the computation and ticks a WITNESS."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import number_theory as NT
    pre = NT.verify_nicolas({"nicolas_primes_to": P, "claimed_nicolas_holds": True})
    if pre.status != "CONFIRMED":
        print("Nicolas did not hold (or errored):", pre.status, (pre.detail or "")[:140]); return 1
    closest = pre.data["closest_prime"]
    r = verify_derivation([{"id": "nicolas", "domain": "number_theory",
          "spec": {"NUM_VERIFY": {"nicolas_primes_to": P, "claimed_nicolas_holds": True, "claimed_closest_prime": closest}}}])
    if r.get("verdict") != "HOLDS":
        print("the elimination did not verify:", json.dumps(r)[:300]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="number_theory")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed Nicolas elimination", seal)
    sid = TS.create("Riemann hypothesis")["id"]
    claim = (f"No zero of zeta lies off the critical line by way of a Nicolas (primorial) counterexample using a "
             f"prime <= {P:,}: every primorial's ratio N_k/(phi(N_k) ln ln N_k) stays above e^gamma (closest at "
             f"p={closest:,}, ratio = {pre.data['closest_ratio']} > {pre.data['e_gamma']}). Nicolas 1983 — a fifth "
             f"independent tool narrowing the window, by elimination.")
    res = TS.tick(sid, "witness", claim, seal=seal, by="Narrow Highway — the elimination reading, 2026-10-05")
    print("  witness" if res.get("ok") else ("  REFUSED: " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"]}, indent=1))
    return 0


def residual() -> int:
    """THE SIGHT PICTURE. Seal S(T) = N(T) - (theta(T)/pi + 1), the signed residual of the zero count — where the
    smooth prediction missed. The verifier shows the misses balance (mean ~ 0), the spread is of the Selberg order,
    and nothing walks off the ln T envelope, as RH requires. A WITNESS on the Riemann stick: the early-warning mark
    that would show the group drifting toward the edge if it ever did. Evidence, never a proof."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import number_theory as NT
    pre = NT.verify_count_residual({"residual_check": True, "claimed_residual_consistent": True})
    if pre.status != "CONFIRMED":
        print("the residual check did not confirm (or errored):", pre.status, (pre.detail or "")[:160]); return 1
    r = verify_derivation([{"id": "residual", "domain": "number_theory",
          "spec": {"NUM_VERIFY": {"residual_check": True, "claimed_residual_consistent": True}}}])
    if r.get("verdict") != "HOLDS":
        print("the elimination did not verify:", json.dumps(r)[:300]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="number_theory")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed count-residual witness", seal)
    sid = TS.create("Riemann hypothesis")["id"]
    d = pre.data
    claim = (f"The sight picture: the signed residual S(T) = N(T) - (theta(T)/pi + 1) of the zero count, sampled "
             f"across the first {d['zeros_used']:,} zeros (to height {d['height']:.0f}), has mean {d['mean_S']:+.4f} "
             f"(centered — the misses balance), spread {d['sd_S']:.4f} (of the Selberg order {d['selberg_sd_scale']:.4f}), "
             f"and max |S| {d['max_abs_S']:.3f}, far under the ln T envelope {d['ln_T_envelope']:.2f}. The count misses "
             f"the smooth curve by a hair in both directions and never walks off, exactly as RH requires. The "
             f"early-warning mark — evidence, not a proof, and no claim about any zero lying on the line.")
    res = TS.tick(sid, "witness", claim, seal=seal, by="Narrow Highway — the sight picture (S(T) residual), 2026-10-05")
    print("  witness" if res.get("ok") else ("  REFUSED: " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"]}, indent=1))
    return 0


def gue() -> int:
    """AN ANSWER IN ANOTHER DOMAIN. The Montgomery-Odlyzko law: the spacings of the zeta zeros follow the GUE of
    random matrix theory. The statistics verifier tests Odlyzko's published zeros for that signature (unit mean,
    level repulsion, variance far from Poisson) and seals a WITNESS on the Riemann stick — cross-domain EVIDENCE
    for the Hilbert-Polya spectral picture, framed as evidence, never a proof, and never a claim about on-line-ness."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import statistics as ST
    pre = ST.verify_gue_spacing({"claimed_consistent_with_gue": True})
    if pre.status != "CONFIRMED":
        print("the GUE check did not confirm (or errored):", pre.status, (pre.detail or "")[:160]); return 1
    r = verify_derivation([{"id": "gue", "domain": "statistics",
          "spec": {"STAT_VERIFY": {"zeta_spacing": {"claimed_consistent_with_gue": True}}}}])
    if r.get("verdict") != "HOLDS":
        print("the elimination did not verify:", json.dumps(r)[:300]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="statistics")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed GUE spacing witness", seal)
    sid = TS.create("Riemann hypothesis")["id"]
    claim = (f"An answer from another domain: the nearest-neighbour spacings of the first {pre.data['zeros_used']:,} "
             f"zeta zeros (Odlyzko's table), unfolded to unit mean, have variance {pre.data['variance']} — GUE-like "
             f"(random matrix theory), far from the Poisson value 1.0, with {pre.data['frac_below_half_mean']*100:.1f}% "
             f"below half-mean (level repulsion). The Montgomery-Odlyzko law: the zeros behave like the spectrum of a "
             f"random Hermitian operator. This is EVIDENCE for the Hilbert-Polya picture, not a proof, and says "
             f"nothing about whether any zero lies on the line.")
    res = TS.tick(sid, "witness", claim, seal=seal, by="Narrow Highway — the cross-domain reading (RMT), 2026-10-05")
    print("  witness" if res.get("ok") else ("  REFUSED: " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"]}, indent=1))
    return 0


def count(T: float = 1000000000.0) -> int:
    """Count the zeros at a GREAT height — far beyond any on-line sweep — and seal it as a WITNESS that says
    exactly what it is: HOW MANY non-trivial zeros of ζ have 0 < Im(ρ) <= T, by Turing's method, cross-checked
    against the Riemann-von Mangoldt term within Backlund's bound on S(T). It is the count in the strip, NOT a
    claim that they lie on the line. It extends the stick's reach (the on-line sweep reached 1e7); it does not
    certify the hypothesis any further."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    from concordance.verifiers import number_theory as NT
    pre = NT.verify_zero_count({"zero_count_height": T})      # no claim: NA carries the count in its data
    if pre.status == "ERROR" or not pre.data:
        print("the count errored:", (pre.detail or "")[:160]); return 1
    n = pre.data.get("zero_count")
    if not n:
        print("no count produced"); return 1
    r = verify_derivation([{"id": "zero_count", "domain": "number_theory",
          "spec": {"NUM_VERIFY": {"zero_count_height": T, "claimed_zero_count": int(n)}}}])
    if r.get("verdict") != "HOLDS":
        print("the count did not verify:", json.dumps(r)[:300]); return 1
    r = receipts.attach(r, config=EngineConfig(), domain="number_theory")
    seal = (r.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted"); return 1
    print("sealed zero count", seal)
    sid = TS.create("Riemann hypothesis")["id"]
    claim = (f"Counted, NOT shown on the line: ζ has exactly {int(n):,} non-trivial zeros with 0 < Im(ρ) <= "
             f"{T:,.0f}, by Turing's method (S(T) = {pre.data['S_T']:+.3f}, within Backlund's bound "
             f"{pre.data['s_bound']:.2f}). The on-line sweep reaches height 1e7; this is the zero COUNT far "
             f"beyond it — it extends the stick's reach, it does not assert these zeros lie on the critical line.")
    res = TS.tick(sid, "witness", claim, seal=seal, by="Narrow Highway — the count, honest about its reach, 2026-10-05")
    print("  witness" if res.get("ok") else ("  REFUSED: " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
    return 0


def main() -> int:
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    if a[0] == "seed":
        return seed()
    if a[0] == "document":
        return document()
    if a[0] == "lnh":
        return lnh()
    if a[0] == "alpha":
        return alpha()
    if a[0] in ("alpha_orbitals", "orbitals", "suborbitals"):
        return alpha_orbitals()
    if a[0] in ("alpha_running", "running"):
        return alpha_running()
    if a[0] in ("forces", "qed", "qft", "unification", "electroweak"):
        return forces()
    if a[0] in ("markov", "mcmc", "lattice"):
        return markov()
    if a[0] in ("lqg", "quantum_gravity", "gravity", "loop"):
        return lqg()
    if a[0] in ("schrodinger", "schroedinger", "wavefunction", "tise"):
        return schrodinger()
    if a[0] in ("grassmannian", "positive_grassmannian", "amplituhedron", "positive_geometry"):
        return grassmannian()
    if a[0] in ("regev", "shor", "factoring", "quantum_factoring"):
        return regev()
    if a[0] in ("godel", "goedel", "incompleteness"):
        return godel()
    if a[0] in ("strings", "string_theory", "superstring"):
        return strings()
    if a[0] in ("gut", "grand_unification", "unification_scale"):
        return gut()
    if a[0] in ("measurement", "interpretations", "born"):
        return measurement()
    if a[0] in ("langlands", "modularity", "reciprocity"):
        return langlands()
    if a[0] in ("capstone", "cornerstone", "keystone"):
        return capstone()
    if a[0] in ("feynman", "least_action", "path_integral", "action"):
        return feynman()
    if a[0] in ("lagrange", "lagrange_multipliers", "multipliers", "kkt"):
        return lagrange()
    if a[0] in ("gaussian", "gaussian_processes", "gp", "kernel"):
        return gaussian()
    if a[0] in ("mandelbrot", "mandelbrot_set", "fractal"):
        return mandelbrot()
    if a[0] in ("spacetime", "time", "emergent_time", "problem_of_time"):
        return spacetime()
    if a[0] in ("maxwell", "superconductivity", "meissner", "flux_quantum"):
        return maxwell()
    if a[0] in ("trigonometry", "trig", "small_angle", "spherical_excess"):
        return trigonometry()
    if a[0] in ("units", "units_matter", "dimensional", "dimensional_analysis"):
        return units_matter()
    if a[0] in ("construct", "constructs", "construct_creation", "coordinates", "invariant"):
        return construct()
    if a[0] in ("topology", "euler", "euler_characteristic", "polyhedron_formula", "genus"):
        return topology()
    if a[0] in ("zeta", "riemann_zeta", "euler_product", "basel"):
        return zeta()
    if a[0] in ("finite_field", "finitefield", "weil", "deligne", "frobenius", "function_field"):
        return finite_field()
    if a[0] in ("smith_chart", "smith", "cayley", "reflection_coefficient", "impedance"):
        return smith_chart()
    if a[0] in ("hilbert_polya", "hilbertpolya", "self_adjoint", "selfadjoint", "spectral"):
        return hilbert_polya()
    if a[0] in ("symmetry", "critical_line", "reflection", "fixed_axis"):
        return symmetry()
    if a[0] in ("de_bruijn_newman", "debruijn_newman", "bruijn_newman", "lambda_dbn", "newman"):
        return de_bruijn_newman()
    if a[0] in ("dirichlet", "dirichlets_theorem", "arithmetic_progressions", "l_function", "characters", "roots_of_unity"):
        return dirichlet()
    if a[0] in ("fibonacci", "fib", "golden_ratio", "phi", "binet", "lucas"):
        return fibonacci()
    if a[0] in ("monte_carlo", "montecarlo", "monte", "mc", "sampling"):
        return monte_carlo()
    if a[0] in ("navier_stokes", "navierstokes", "navier", "turbulence", "dispersion", "dissonance"):
        return navier_stokes()
    if a[0] in ("yang_mills", "yangmills", "mass_gap", "massgap", "confinement"):
        return yang_mills()
    if a[0] in ("entropy_gravity", "entropy", "bekenstein", "hawking", "holographic"):
        return entropy_gravity()
    if a[0] in ("standard_model", "standardmodel", "electroweak", "weinberg_angle", "chain", "lineage"):
        return standard_model()
    if a[0] in ("jevons", "jevons_paradox", "rebound", "rebound_effect", "efficiency_paradox"):
        return jevons()
    if a[0] in ("bombelli", "complex_numbers", "complex", "imaginary", "sqrt_minus_one", "casus_irreducibilis"):
        return bombelli()
    if a[0] in ("calculus", "integrals", "derivatives", "integral", "derivative", "ftc", "fundamental_theorem"):
        return calculus()
    if a[0] in ("fourier", "rotation", "phasor", "frequency", "spin", "fourier_transform", "dft"):
        return fourier()
    if a[0] in ("linguistics", "language_math", "zipf", "grammar", "generative", "vocabulary"):
        return linguistics()
    if a[0] in ("lebesgue", "measure_theory", "measure", "lebesgue_integral", "almost_everywhere"):
        return lebesgue()
    if a[0] in ("vector_calculus", "divergence", "curl", "div_curl", "helmholtz", "vorticity"):
        return vector_calculus()
    if a[0] in ("legendre", "legendre_transform", "tangent_lines", "y_intercept", "convex_duality", "dual"):
        return legendre()
    if a[0] in ("euclid", "elements", "postulates", "axioms", "deduction"):
        return euclid()
    if a[0] in ("scribe", "scribing", "scribe_the_center", "points_to_lines", "connect_the_points"):
        return scribe()
    if a[0] in ("multiplication", "replication", "exponential_growth", "scaling", "fruitful"):
        return multiplication()
    if a[0] in ("gamma", "gamma_function", "hyperspheres", "n_ball", "spheres", "higher_dimensional_spheres"):
        return gamma()
    if a[0] in ("imaginary_numbers", "fundamental_theorem_of_algebra", "fta", "algebraically_closed", "complex_tool", "using_i"):
        return imaginary_numbers()
    if a[0] in ("e", "eulers_number", "euler_number", "exponential_constant", "natural_log", "compounding"):
        return euler_e()
    if a[0] in ("laplace", "laplace_transform", "transfer_function", "s_plane", "differential_equations", "ode", "entropy_fits"):
        return laplace()
    if a[0] in ("assembly", "assemble", "final"):
        return assembly()
    if a[0] in ("aharonov_bohm", "ab"):
        return aharonov_bohm()
    if a[0] in ("fiber", "calibration"):
        return fiber()
    if a[0] in ("symphony", "music"):
        return symphony()
    if a[0] in ("relational", "rovelli"):
        return relational()
    if a[0] == "robin":
        return robin(int(a[1]) if len(a) > 1 else 1000000)
    if a[0] == "schoenfeld":
        return schoenfeld(int(a[1]) if len(a) > 1 else 2000000)
    if a[0] == "lagarias":
        return lagarias(int(a[1]) if len(a) > 1 else 1000000)
    if a[0] == "nicolas":
        return nicolas(int(a[1]) if len(a) > 1 else 1000000)
    if a[0] == "gue":
        return gue()
    if a[0] == "residual":
        return residual()
    if a[0] == "count":
        return count(float(a[1]) if len(a) > 1 else 1000000000.0)
    if a[0] == "window":
        from concordance import tickstick as T
        ids = [a[1]] if len(a) > 1 else sorted(T.fold())
        for sid in ids:
            st = T.read(sid)
            if not st.get("ok"):
                print(sid, "— no such stick"); continue
            w = st["fit"]["window"]
            print(f"\n{sid}  ({'narrows numerically' if w['narrows_numerically'] else 'barrier problem — no numeric window'})")
            for e in w["eliminations"]:
                print("   - " + e)
            print("   surviving: " + w["surviving"])
        return 0
    if a[0] == "riemann":
        return riemann(float(a[1]) if len(a) > 1 else 100.0)
    if a[0] == "bsd":
        if len(a) > 1 and a[1] == "all":                  # seal every curve in the ingested table
            rc = 0
            for label in sorted(CURVES, key=lambda k: (CURVES[k]["N"], k)):
                print(f"\n── {label} ──")
                rc |= bsd(label)
            return rc
        return bsd(a[1] if len(a) > 1 else "11a1")
    if a[0] == "read":
        from concordance import tickstick as T
        print(json.dumps(T.read(a[1]) if len(a) > 1 else T.listing(), indent=1, ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
