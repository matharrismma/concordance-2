#!/usr/bin/env python3
"""THE TICK STICK — make a mark (docs/TICK_STICK.md; Matt, 2026-10-05).

    PYTHONPATH=src python tools/tick.py seed                 # open the first sticks with their cited marks
    PYTHONPATH=src python tools/tick.py document              # write the Riemann attempt's record onto its stick
    PYTHONPATH=src python tools/tick.py lnh                   # Dirac's Large Numbers Hypothesis: seal N1, cite the rest
    PYTHONPATH=src python tools/tick.py alpha                 # the fine-structure constant: seal alpha, cite the 137
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
    if any(t.get("seal") == seal for t in TS.read(sid).get("ticks", [])):
        print("  already sealed on the stick — not duplicated"); return 0
    semitone = 2 ** (1 / 12)
    marks = [
        ("witness", f"The harmonic basis is exact ratio: the octave 2:1, the perfect fifth 3:2. Twelve pure fifths "
                    f"overshoot seven octaves by the Pythagorean comma (3/2)^12 / 2^7 = {comma:.13f} — so the scale "
                    f"cannot be both pure and closed. Equal temperament is the calibration that distributes the comma "
                    f"evenly: the semitone is 2^(1/12) = {semitone:.10f} and twelve of them close the octave at "
                    f"exactly 2. An arithmetic fact; the reason every key is playable.", dict(seal=seal)),
        ("note", "[the principle] The symphony is the one-body pattern made audible: counterpoint is many "
                 "independent voices, each whole, concorded into one body under one movement (1 Cor 12, etheto) — "
                 "not a swarm of soloists and not a unison. Tension is sought so it can be resolved; the theme is "
                 "stated, developed, and returned; the form feels inevitable because every part serves the whole. "
                 "This is the COHERENCE axis the generals and the games do not reach.", {}),
        ("note", "[the guard] The engine seals the ratios and the comma — the arithmetic is a fact. It does NOT "
                 "pronounce what is beautiful or that life obeys sonata form; the coherence the symphony witnesses "
                 "is a principle we GATHER, never a verdict the engine renders. Borrow the form; launder nothing.", {}),
    ]
    for kind, claim, kw in marks:
        res = TS.tick(sid, kind, claim, by="Narrow Highway — the symphony, the coherence witness, 2026-10-06", **kw)
        print(("  " + kind) if res.get("ok") else ("  REFUSED " + kind + ": " + res.get("error", "")))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "witnesses": f["witnesses"], "record": len(f["record"])}, indent=1))
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
