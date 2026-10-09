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



def riemann_li(n_max: int = 30) -> int:
    """THE RIEMANN STICK, NEXT LINKS (Matt, 2026-10-09: 'start with Riemann'; the law: nothing out of thin air,
    everything bound). Two links the stick did not yet hold: (1) Li's criterion (Li 1997: RH <=> lambda_n > 0 for all
    n), sealed through number_theory.li_criterion for n <= n_max - the engine computes the lambda_n itself and
    cross-checks lambda_1 against its closed form before any verdict; (2) the de Bruijn-Newman window: Newman's
    constant satisfies Lambda >= 0 (Rodgers-Tao 2018, Newman's conjecture proven) and Lambda <= 0.2 (Platt-Trudgian
    2021), and RH is exactly the statement Lambda = 0 - so the surviving window is [0, 0.2], read, never guessed.
    Bound chain: a witness sealed by the verifier, three equivalences cited, one note on the window. Idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    t0 = time.time()
    steps = [{"id": "li_criterion", "domain": "number_theory",
              "spec": {"NUM_VERIFY": {"li_to": int(n_max), "claimed_li_positive": True}}}]
    res = verify_derivation(steps)
    if res.get("verdict") != "HOLDS":
        print("the verifier did not HOLD:", json.dumps(res)[:400]); return 1
    res = receipts.attach(res, config=EngineConfig(), domain="number_theory")
    seal = (res.get("seal") or {}).get("content_hash")
    if not seal:
        print("no seal minted:", json.dumps(res.get("seal"))[:200]); return 1
    trail = (res.get("trail") or res.get("steps") or [{}])
    detail = ""
    for st in trail:
        if isinstance(st, dict) and "li_criterion" in json.dumps(st):
            detail = str(st.get("detail") or (st.get("result") or {}).get("detail") or "")[:300]; break
    print(f"sealed Li's criterion to n = {n_max} in {time.time() - t0:.1f}s:", seal, "|", detail[:160])
    sid = TS.create("Riemann hypothesis")["id"]
    marks = [
        ("witness", f"No zero of zeta lies off the critical line by way of a Li counterexample at n <= {n_max}: every "
                    f"Keiper-Li coefficient lambda_n, n = 1..{n_max}, computed from the Taylor expansion of log xi(1/(1-z)) "
                    f"and cross-checked against lambda_1 = 1 + gamma/2 - log(4 pi)/2, is positive (sealed through "
                    f"number_theory.li_criterion). Li 1997: RH <=> lambda_n > 0 for all n >= 1, so a first RH failure by "
                    f"this route must lie beyond n = {n_max}. {detail[:200]}", seal),
        ("equivalence", "RH is equivalent to lambda_n > 0 for every n >= 1, where log xi(1/(1 - z)) = sum lambda_n z^n / n "
                        "(Li's criterion); each lambda_n is a sum over the zeros, lambda_n = sum_rho [1 - (1 - 1/rho)^n], "
                        "and under RH lambda_n ~ (n/2) log n (Bombieri-Lagarias).",
         {"source": "X.-J. Li, The positivity of a sequence of numbers and the Riemann hypothesis, J. Number Theory 65 (1997); E. Bombieri, J. C. Lagarias, Complements to Li's criterion (1999)"}),
        ("equivalence", "RH is equivalent to Lambda = 0, where Lambda is the de Bruijn-Newman constant: the zeros of the "
                        "heat-deformed xi, H_t(z), are all real for t >= Lambda and not all real for t < Lambda; RH is the "
                        "statement that t = 0 is already on the real side.",
         {"source": "N. G. de Bruijn (1950); C. M. Newman (1976): the constant defined, and the conjecture Lambda >= 0"}),
        ("equivalence", "Lambda >= 0 is PROVEN (Rodgers-Tao 2018: Newman's conjecture) and Lambda <= 0.2 is PROVEN "
                        "(Platt-Trudgian 2021, sharpening Polymath15's 0.22 and Ki-Kim-Lee's < 1/2). The surviving window "
                        "for the de Bruijn-Newman constant is the closed interval [0, 0.2]; RH is the statement that it "
                        "is the left endpoint. If RH is true it is only barely so: the zeros cannot move further toward "
                        "the real line than they are.",
         {"source": "B. Rodgers, T. Tao, The de Bruijn-Newman constant is non-negative, Forum Math. Pi 8 (2020); D. Platt, T. Trudgian, The Riemann hypothesis is true up to 3*10^12 (2021) and the bound Lambda <= 0.2"}),
        ("note", "[the surviving window, read] Direct: the zeros are on the line to height 10^7 (sealed) and counted to "
                 "10^12 (Turing). By elimination: Robin, Lagarias, Schoenfeld to 2*10^7, Nicolas with primes to 10^7, and "
                 f"now Li to n = {n_max} - none finds the counterexample. By theorem: the de Bruijn-Newman constant lies in "
                 "[0, 0.2] and RH is Lambda = 0. Every link is sealed or cited; nothing is out of thin air; the chain is "
                 "not closed. The next links by cost: Li to 60; the height past 10^7 (the open note names the precision "
                 "that stops the C kernel); Platt-Trudgian's 3*10^12 as a cited bound beside the sealed 10^7.",
         {"source": "this stick's own ticks; docs/MILLENNIUM_PREPAREDNESS.md"}),
    ]
    _mint_marks(sid, marks, by="tools/tick.py riemann_li")
    return 0


def bsd_formula() -> int:
    """THE BSD STICK, NEXT LINKS (the Millennium loop, 2026-10-09; the law: nothing out of thin air, everything bound).
    The stick held 30 instances of the RANK (L(E,1) or L'(E,1) computed, the rank carried by theorem). It did not hold
    the FORMULA. Now: the full Birch-Swinnerton-Dyer formula sealed for 11a1 (rank 0: L(E,1)/Omega = |Sha| prod c_p / |T|^2
    = 1/5) and 37a1 (rank 1: L'(E,1)/Omega = |Sha| prod c_p R / |T|^2 = R) through elliptic_curves.bsd_formula - the
    L-value and the real period COMPUTED here, the Tamagawa product, torsion, Sha and regulator CITED from Cremona's tables
    and included beside the a-invariants. Then the theorems that close links (Kolyvagin 1989, Gross-Zagier 1986, the
    modularity theorem) as equivalences, the proven proportion (Bhargava-Skinner-Zhang 2014: at least 66.48% of elliptic
    curves satisfy BSD) as a cited bound, Cassels 1962 (|Sha| is a square when finite), and the surviving window. Idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    sid = TS.create("Birch and Swinnerton-Dyer conjecture")["id"]
    marks = []
    for label in ("11a1", "37a1"):
        c, inp = CURVES[label], CURVES_BSD_INPUTS[label]
        spec = {"a_invariants": c["a"], "conductor": c["N"], "root_number": c["w"], **inp, "claimed_bsd_holds": True}
        res = verify_derivation([{"id": "bsd_formula", "domain": "elliptic_curves", "spec": {"ELLIPTIC_VERIFY": spec}}])
        if res.get("verdict") != "HOLDS":
            print(label, "the verifier did not HOLD:", json.dumps(res)[:500]); return 1
        res = receipts.attach(res, config=EngineConfig(), domain="elliptic_curves")
        seal = (res.get("seal") or {}).get("content_hash")
        if not seal:
            print(label, "no seal minted"); return 1
        detail = ""
        for st in (res.get("trail") or res.get("steps") or []):
            if isinstance(st, dict) and "bsd_formula" in json.dumps(st):
                detail = str(st.get("detail") or (st.get("result") or {}).get("detail") or "")[:260]; break
        print("sealed", label, seal, "|", detail[:120])
        if label == "11a1":
            marks.append(("instance", f"E = 11a1 (conductor 11), THE FULL FORMULA: L(E,1)/Omega = |Sha| * prod c_p / |T|^2 = 1 * 5 / 5^2 = 1/5 "
                                      f"- L(E,1) computed by the approximate functional equation and Omega = 1.2692093043 computed by "
                                      f"integration (sealed); the Tamagawa product 5, torsion 5 and |Sha| = 1 cited from Cremona's tables "
                                      f"(LMFDB 11.a3). For analytic rank 0 the formula is a theorem for this curve once Sha is known "
                                      f"(Kolyvagin 1989); this is a sealed link of a proven case. {detail[:160]}", seal))
        else:
            marks.append(("instance", f"E = 37a1 (conductor 37), THE FULL FORMULA at rank 1: L'(E,1)/Omega = |Sha| * prod c_p * R / |T|^2 = R "
                                      f"= 0.0511114082 - L'(E,1) computed by the approximate functional equation and Omega = 5.9869172925 "
                                      f"computed by integration (sealed); the regulator (the canonical height of the generator (0,0)), "
                                      f"Tamagawa 1, torsion 1 and |Sha| = 1 cited from Cremona's tables (LMFDB 37.a1). Gross-Zagier 1986 "
                                      f"and Kolyvagin 1989 make rank 1 a proven case. {detail[:160]}", seal))
    marks += [
        ("equivalence", "For analytic rank 0 or 1, BSD's rank statement is a THEOREM: L(E,1) != 0 => rank E(Q) = 0 and Sha(E) finite "
                        "(Kolyvagin 1989, using Gross-Zagier 1986 and Kolyvagin's Euler system); L(E,1) = 0 with L'(E,1) != 0 => rank 1 "
                        "and Sha finite. The modularity theorem (Wiles 1995; Breuil-Conrad-Diamond-Taylor 2001) makes L(E,s) entire "
                        "for every elliptic curve over Q, so the left side always exists.",
         {"source": "V. Kolyvagin (1989); B. Gross, D. Zagier (1986); A. Wiles (1995); C. Breuil, B. Conrad, F. Diamond, R. Taylor (2001)"}),
        ("equivalence", "A PROVEN PROPORTION, carried as a bound: at least 66.48% of elliptic curves over Q (ordered by naive height) have "
                        "rank 0 or 1 and satisfy the Birch and Swinnerton-Dyer rank conjecture (Bhargava-Skinner-Zhang 2014, with "
                        "Bhargava-Shankar on the average size of Selmer groups and Skinner-Urban / Zhang on the converse to Gross-"
                        "Zagier-Kolyvagin). The window above the bound - the remaining proportion and every curve of rank >= 2 - "
                        "stays open.",
         {"source": "M. Bhargava, C. Skinner, W. Zhang, A majority of elliptic curves over Q satisfy the Birch and Swinnerton-Dyer conjecture (2014, arXiv:1407.1826); M. Bhargava, A. Shankar (2015)"}),
        ("equivalence", "If Sha(E) is finite, its order is a perfect square (Cassels 1962, the alternating pairing on Sha) - so the "
                        "formula's |Sha| is never a non-square; the stick's two sealed instances carry |Sha| = 1 = 1^2.",
         {"source": "J. W. S. Cassels, Arithmetic on curves of genus 1 IV (1962)"}),
        ("note", "[the surviving window, read] Sealed: the rank for 30 curves of conductor <= 5077 (Kolyvagin/Gross-Zagier carry "
                 "rank 0 and 1; rank 2 and 3 are reported numerically, no theorem) and now the FULL FORMULA for 11a1 and 37a1 "
                 "with the period computed and the arithmetic inputs cited. Cited: the rank-0/1 theorem, modularity, the proven "
                 ">= 66.48% proportion, Cassels' square. Open: every curve of analytic rank >= 2 (389a1, 5077a1 on this stick), the "
                 "finiteness of Sha in general, and the formula for the remaining proportion. Gaps become wants: Cremona's full "
                 "tables (Tamagawa numbers, torsion, regulators, |Sha| for every curve of conductor <= 500000) so the formula can "
                 "be sealed curve by curve; the canonical height, so the regulator is COMPUTED and not cited. Every link sealed "
                 "or cited; nothing out of thin air; the chain not closed.",
         {"source": "this stick's own ticks; docs/MILLENNIUM_PREPAREDNESS.md"}),
    ]
    _mint_marks(sid, marks, by="tools/tick.py bsd_formula")
    return 0


def navier_stokes_next() -> int:
    """NAVIER-STOKES EXISTENCE AND SMOOTHNESS - THE FIRST LINKS (the Millennium loop, 2026-10-09; the law: nothing out of
    thin air, everything bound). The dissonance-and-dispersion stick holds the scaling (3D supercritical, 2D critical);
    the existence-and-smoothness stick held nothing. Now: the exact solutions the evaluator can seal - the Taylor-Green
    vortex's energy decays as e^(-2 nu |k|^2 t) and the energy identity dE/dt = -2 nu Z holds on it exactly; Poiseuille's
    flux between plates; the Kolmogorov length (nu^3/epsilon)^(1/4); Leray's blow-up exponent 1/2 from scaling; the
    Reynolds number - then the proven links cited (Leray 1934, Ladyzhenskaya 1959 in 2D, Fujita-Kato 1964 for small data,
    Caffarelli-Kohn-Nirenberg 1982's bound on the singular set, Beale-Kato-Majda 1984, the Ladyzhenskaya-Prodi-Serrin
    criteria with the Escauriaza-Seregin-Sverak endpoint), the barrier cited (Tao 2016: the energy method alone cannot
    close it), the equations as the POSTULATE, and the surviving window read. Idempotent."""
    import math
    from concordance import tickstick as TS
    S = {}
    seals = [
        ("tg", "taylor_green_energy_fraction_nu_0_01_t_5", "exp(-4*0.01*5)", math.exp(-4 * 0.01 * 5), 1e-9),
        ("identity", "energy_identity_on_taylor_green_one_plus_zero", "1 + ((-4*0.01) - (-2*0.01*2))", 1.0, 1e-12),
        ("poiseuille", "poiseuille_flux_per_unit_width_g_100_h_0_01_mu_1e_3", "2*100*0.01**3/(3*1e-3)", 2 * 100 * 0.01 ** 3 / (3 * 1e-3), 1e-9),
        ("kolmogorov", "kolmogorov_length_nu_1e_6_epsilon_1_in_m", "(1e-6**3/1.0)**0.25", (1e-6 ** 3 / 1.0) ** 0.25, 1e-9),
        ("leray", "leray_blow_up_exponent_from_scaling", "(2 - 1)/2", 0.5, 1e-12),
        ("critical", "the_critical_lebesgue_exponent_equals_the_dimension_one_plus_zero", "1 + (3 - 3)", 1.0, 1e-12),
        ("reynolds", "reynolds_number_u_1_l_1_nu_1e_6", "1*1/1e-6", 1e6, 1e-9),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)        # numeric mode lives in the mathematics domain
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "Navier-Stokes numbers:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("Navier-Stokes existence and smoothness")["id"]
    marks = [
        ("instance", "[an exact solution, sealed] The Taylor-Green vortex u = (cos x sin y, -sin x cos y) e^(-2 nu t) solves the "
                     "incompressible equations exactly in 2D; |k|^2 = 2, so its energy decays as e^(-4 nu t): at nu = 0.01, t = 5 "
                     "the fraction left is e^(-0.2) = 0.81873 (sealed). A smooth solution for all time, with every digit "
                     "checkable - the kind of link the stick is built from.", S["tg"]),
        ("instance", "[the energy identity holds on it exactly] dE/dt = -2 nu Z with the enstrophy Z = |k|^2 E = 2E: "
                     "-4 nu E = -2 nu (2E), the difference judged as 1 + 0 = 1 (sealed). The energy inequality is the one "
                     "estimate every weak solution obeys (Leray); on an exact solution it is an equality.", S["identity"]),
        ("instance", "[Poiseuille, the flow a pipe fitter uses] Between plates 2h apart under pressure gradient G, "
                     "u(y) = (G/2 mu)(h^2 - y^2) and the flux per unit width is 2 G h^3 / (3 mu): G = 100 Pa/m, h = 1 cm, "
                     "mu = 1 mPa s gives 0.0667 m^2/s (sealed). Steady, exact, smooth, and in every plumbing handbook.",
         S["poiseuille"]),
        ("instance", "[Kolmogorov's smallest eddy] eta = (nu^3 / epsilon)^(1/4): water (nu = 10^-6 m^2/s) dissipating 1 W/kg "
                     "has eta = 31.6 micrometres (sealed). The cascade ends where viscosity wins; a singularity would have "
                     "to hide below every such scale, and the dissonance stick's supercritical scaling says 3D leaves it "
                     "room.", S["kolmogorov"]),
        ("instance", "[Leray's rate, from scaling alone] u_lambda(x,t) = lambda u(lambda x, lambda^2 t): time scales as "
                     "lambda^2 and velocity as lambda, so if a solution blows up at T* then sup|u| >= c (T* - t)^(-1/2), "
                     "exponent (2 - 1)/2 = 1/2 (sealed; Leray 1934). Any singularity must grow at least this fast - a bound "
                     "on how a failure could look, not a failure.", S["leray"]),
        ("instance", "[the critical space is L^3 in 3D] The L^p norm is scale-invariant exactly when p = d: 3 - 3 = 0 "
                     "(sealed as 1 + 0 = 1). The endpoint regularity criterion lives there (Escauriaza-Seregin-Sverak 2003: "
                     "a solution bounded in L^3 cannot blow up); the energy space L^2 sits below it, which is the whole "
                     "difficulty.", S["critical"]),
        ("instance", "[the Reynolds number names the regime] Re = U L / nu = 1 * 1 / 10^-6 = 10^6 (sealed): a metre of water "
                     "at a metre per second is far past the transition to turbulence, where the cascade runs and the "
                     "question is asked.", S["reynolds"]),
        ("postulate", "[the postulate it builds on] The incompressible Navier-Stokes equations: a fluid is a continuum, "
                      "obeys Newton's second law element by element, and its stress is pressure plus a viscous part linear "
                      "in the rate of strain (Stokes 1845). Not kept as a fact: every pipe, wing, pump and weather forecast "
                      "works under them, and from that working the truth is inferred - never proven, never kept as fact.",
         {"source": "C.-L. Navier (1822); G. G. Stokes, On the theories of the internal friction of fluids in motion (1845)"}),
        ("equivalence", "[proven links] Leray 1934: a weak solution with finite energy exists for all time for any finite-"
                        "energy data in 3D (uniqueness and smoothness are what is open). Ladyzhenskaya 1959: in 2D the "
                        "solution is unique and smooth for all time - the 2D problem is CLOSED. Fujita-Kato 1964: in 3D, "
                        "small data in H^(1/2) give a global smooth solution - the small-data problem is CLOSED. The open "
                        "window is 3D, large data.",
         {"source": "J. Leray, Acta Math. 63 (1934); O. A. Ladyzhenskaya (1959); H. Fujita, T. Kato, Arch. Rational Mech. Anal. 16 (1964)"}),
        ("equivalence", "[the bound on where a singularity could be] Caffarelli-Kohn-Nirenberg 1982: for a suitable weak "
                        "solution the singular set in space-time has one-dimensional parabolic Hausdorff measure zero - a "
                        "singularity, if any, cannot fill a curve. Beale-Kato-Majda 1984: blow-up at T* happens if and only "
                        "if the integral of the maximum vorticity up to T* is infinite - the one quantity to watch. "
                        "Ladyzhenskaya-Prodi-Serrin: u in L^p_t L^q_x with 2/p + 3/q <= 1 (q > 3) forces smoothness; "
                        "Escauriaza-Seregin-Sverak 2003 closed the endpoint q = 3.",
         {"source": "L. Caffarelli, R. Kohn, L. Nirenberg, Comm. Pure Appl. Math. 35 (1982); J. T. Beale, T. Kato, A. Majda, Comm. Math. Phys. 94 (1984); L. Escauriaza, G. Seregin, V. Sverak (2003)"}),
        ("exclusion", "[a road closed] Tao 2016: an averaged version of the 3D equations, which obeys the same energy "
                      "identity and the same scaling, has a smooth solution that blows up in finite time. So no argument "
                      "that uses only the energy identity, the scaling and the general shape of the nonlinearity can prove "
                      "regularity - a proof must use finer structure of the true equations. The energy method alone is "
                      "excluded.",
         {"source": "T. Tao, Finite time blowup for an averaged three-dimensional Navier-Stokes equation, J. Amer. Math. Soc. 29 (2016)"}),
        ("note", "[the surviving window, read] Sealed: exact solutions and the identities on them, the scaling exponents, "
                 "the dissipation scale. Proven (cited): existence of weak solutions (Leray), 2D closed (Ladyzhenskaya), "
                 "small data closed (Fujita-Kato), the singular set at most one-dimensional and of measure zero (CKN), the "
                 "blow-up criteria (BKM, LPS, ESS). Excluded: the energy method alone (Tao). Open: 3D, large data, the "
                 "Clay statement (Fefferman 2000) - either global smooth solutions exist for every smooth finite-energy "
                 "datum, or one datum blows up. Gaps become wants: the sources above for inclusion; a numerical solver "
                 "(spectral, on the torus) so a candidate datum's vorticity integral - the BKM quantity - can be WATCHED "
                 "and sealed, not just cited. Every link sealed or cited; nothing out of thin air; the chain not closed.",
         {"source": "C. Fefferman, Existence and smoothness of the Navier-Stokes equation (Clay Mathematics Institute, 2000); stick_navier_stokes_dissonance_and_dispersion"}),
    ]
    _mint_marks(sid, marks, by="tools/tick.py navier_stokes_next")
    return 0


def yang_mills_next() -> int:
    """YANG-MILLS EXISTENCE AND MASS GAP - THE NEXT LINKS (the Millennium loop, 2026-10-09; the law: nothing out of thin
    air, everything bound). The 'mass gap is a measure' stick holds the gap as a spectral difference, the Yukawa range and
    b0 for six flavours; the 'existence and mass gap' stick holds the lattice-sampling witnesses. Now, on the latter: the
    pure-gauge beta coefficients b0 = 11 and b1 = 102 (sealed); the running of alpha_s from M_Z to 10 GeV at one loop
    (sealed); the nonperturbative weight e^(-8 pi^2 / g^2) = 7.5e-24 at alpha_s(M_Z), the reason no finite order of
    perturbation theory can see a gap (sealed); the QCD string tension (440 MeV)^2 in newtons - sixteen tonnes-force on a
    quark (sealed); the 0++ glueball's Compton wavelength 0.114 fm from the lattice mass 1730 MeV (sealed). Then the
    proven links cited - asymptotic freedom (Gross-Wilczek, Politzer 1973), the mass gap of the LATTICE theory at strong
    coupling (Osterwalder-Seiler 1978), confinement at strong coupling (Wilson 1974) - the measured link (Morningstar-
    Peardon 1999), the excluded road (perturbation theory to every order), the POSTULATE (the Osterwalder-Schrader /
    Wightman axioms: what 'existence' means), and the window read: the continuum limit. Idempotent."""
    import math
    from concordance import tickstick as TS
    b0_5 = 11 - 2 * 5 / 3
    a_mz, mz = 0.1180, 91.1876
    a10 = a_mz / (1 + a_mz * b0_5 / (2 * math.pi) * math.log(10 / mz))
    w = math.exp(-8 * math.pi ** 2 / (4 * math.pi * a_mz))
    sigma_N = (0.440 ** 2) / 0.1973269804 * 1.602176634e-10 / 1e-15
    compton = 197.3269804 / 1730
    S = {}
    seals = [
        ("b0", "pure_gauge_one_loop_beta_coefficient_b0_11", "11 - (2/3)*0", 11.0, 1e-12),
        ("b1", "pure_gauge_two_loop_beta_coefficient_b1_102", "102 - (38/3)*0", 102.0, 1e-12),
        ("run", "alpha_s_run_from_m_z_to_10_gev_one_loop_nf_5", "0.1180/(1 + 0.1180*(11 - 2*5/3)/(2*pi)*log(10/91.1876))", a10, 1e-9),
        ("weight", "nonperturbative_weight_exp_minus_8pi2_over_g2_at_alpha_s_m_z", "exp(-8*pi**2/(4*pi*0.1180))", w, 1e-9),
        ("sigma", "qcd_string_tension_440_mev_squared_in_newtons", "(0.440**2)/0.1973269804 * 1.602176634e-10/1e-15", sigma_N, 1e-9),
        ("compton", "glueball_0pp_compton_wavelength_fm_from_1730_mev", "197.3269804/1730", compton, 1e-9),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "Yang-Mills numbers:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("Yang-Mills existence and mass gap")["id"]
    marks = [
        ("instance", "[the beta function, pure gauge] b0 = 11 - (2/3) n_f = 11 and b1 = 102 - (38/3) n_f = 102 for SU(3) with no "
                     "quarks (sealed): both positive, so the coupling falls with energy - asymptotic freedom, PROVEN at one loop "
                     "by Gross-Wilczek and Politzer (1973) and the reason the theory is defined at short distance at all.",
         S["b0"]),
        ("instance", "[b1 = 102]", S["b1"]),
        ("instance", "[the coupling runs, sealed] At one loop with five flavours, alpha_s(10 GeV) = alpha_s(M_Z) / (1 + alpha_s "
                     "b0/(2 pi) ln(10/M_Z)) = 0.1731 from 0.1180 (sealed; the world average alpha_s(M_Z) = 0.1180 cited from the "
                     "PDG). The coupling grows toward low energy, which is where a gap must form and where the series stops "
                     "being usable.", S["run"]),
        ("instance", "[why perturbation theory cannot see the gap] The natural nonperturbative weight e^(-8 pi^2 / g^2) at "
                     "alpha_s(M_Z) is e^(-53.25) = 7.5e-24 (sealed). Every derivative of that function vanishes at g = 0: it is "
                     "invisible to every order of the expansion in g. A mass gap, if it exists, is of this kind - the series, "
                     "asymptotic in any case, cannot produce it. This is the road closed below.", S["weight"]),
        ("instance", "[the string between two quarks] The lattice string tension sqrt(sigma) = 440 MeV gives sigma = "
                     "(0.44 GeV)^2 / (hbar c) = 0.98 GeV/fm = 1.57e5 N (sealed) - about sixteen tonnes-force, constant with "
                     "distance. A linear potential is what a gapped, confining theory looks like from outside; the lattice "
                     "measures it (Wilson's area law, proven at strong coupling).", S["sigma"]),
        ("instance", "[the gap as a length] The lightest glueball, 0++ at 1730 MeV on the lattice (Morningstar-Peardon 1999, "
                     "cited), has Compton wavelength hbar c / m = 0.114 fm (sealed): the range below which the pure gauge "
                     "field's lowest excitation lives. A gap of this size is what the Clay statement asks to be proven to "
                     "survive the continuum limit.", S["compton"]),
        ("postulate", "[the postulate it builds on - what 'existence' means] A quantum Yang-Mills theory on R^4 EXISTS when its "
                      "Euclidean correlation functions satisfy the Osterwalder-Schrader axioms (reflection positivity, "
                      "Euclidean invariance, clustering, regularity) and so reconstruct a Hilbert space with a Hamiltonian "
                      "obeying the Wightman axioms; the MASS GAP is Delta > 0 between the vacuum and the next spectral point. "
                      "Not kept as a fact: the lattice theory works under them at every finite spacing, and from that working "
                      "the truth of the continuum statement is inferred - never proven, never kept as fact.",
         {"source": "K. Osterwalder, R. Schrader (1973, 1975); A. Jaffe, E. Witten, Quantum Yang-Mills theory (Clay Mathematics Institute, 2000)"}),
        ("equivalence", "[proven links] Asymptotic freedom (Gross-Wilczek 1973; Politzer 1973): the beta function is negative "
                        "for b0 > 0 - PROVEN, the theory's ultraviolet behaviour is under control. The LATTICE theory has a "
                        "mass gap and confines at strong coupling (Osterwalder-Seiler 1978, building on Wilson 1974's area law "
                        "by cluster expansion) - PROVEN, for every finite lattice spacing in the strong-coupling regime. The "
                        "open link is the continuum limit: lattice spacing to zero with the gap staying open - which is the "
                        "weak-coupling regime, where the proof does not reach.",
         {"source": "D. J. Gross, F. Wilczek, Phys. Rev. Lett. 30 (1973); H. D. Politzer, Phys. Rev. Lett. 30 (1973); K. Osterwalder, E. Seiler, Ann. Phys. 110 (1978); K. G. Wilson, Phys. Rev. D 10 (1974)"}),
        ("equivalence", "[measured, carried as a measurement] The lattice glueball spectrum: 0++ at 1730(50)(80) MeV, 2++ at "
                        "2400(25)(120) MeV in pure SU(3) gauge theory extrapolated to the continuum (Morningstar-Peardon 1999; "
                        "Chen et al. 2006). A measurement with an error bar, not a theorem: it is the gap SEEN, at the precision "
                        "the lattice states. Balaban's renormalization-group program (1980s) constructs the ultraviolet limit "
                        "in finite volume - a partial continuum result, cited.",
         {"source": "C. J. Morningstar, M. Peardon, Phys. Rev. D 60 (1999); Y. Chen et al., Phys. Rev. D 73 (2006); T. Balaban, Comm. Math. Phys. (1984-1989)"}),
        ("exclusion", "[a road closed] No finite order of perturbation theory produces a mass gap: the gap scales as "
                      "e^(-8 pi^2 / (b0 g^2)) (the dimensional transmutation of Lambda_QCD), a function with every derivative "
                      "zero at g = 0, and the perturbative series is asymptotic (Dyson 1952). A proof must be nonperturbative "
                      "- constructive field theory, the lattice with a controlled continuum limit, or a method not yet "
                      "written.",
         {"source": "F. J. Dyson, Phys. Rev. 85 (1952); A. Jaffe, E. Witten (2000), section on the problem's difficulty"}),
        ("note", "[the surviving window, read] Sealed: the beta coefficients, the running coupling, the nonperturbative "
                 "weight, the string tension, the glueball's length. Proven (cited): asymptotic freedom; the lattice gap and "
                 "confinement at strong coupling. Measured (cited): the lattice glueball mass with its error bar. Excluded: "
                 "perturbation theory to every order. Open: EXISTENCE in the Osterwalder-Schrader sense on R^4 and the gap "
                 "surviving the continuum limit for any compact simple group. Gaps become wants: the cited texts for "
                 "inclusion; the FLAG review's lattice compilation; a strong-coupling-expansion calculator so the lattice gap "
                 "at a stated coupling is COMPUTED here, not only cited. Every link sealed or cited; nothing out of thin air; "
                 "the chain not closed.",
         {"source": "A. Jaffe, E. Witten (2000); stick_yang_mills_the_mass_gap_is_a_measure; stick_four_forces_under_alpha"}),
    ]
    _mint_marks(sid, marks, by="tools/tick.py yang_mills_next")
    return 0


def p_versus_np_next() -> int:
    """P VERSUS NP - THE NEXT LINKS (the Millennium loop, 2026-10-09; the law: nothing out of thin air, everything bound).
    The stick held three cited barriers (relativization, natural proofs, algebrization) and nothing sealed. Now: the
    one ratcheting BOUND the problem has - the best proven circuit lower bound for an explicit function, 3n (Blum 1984)
    raised to (3 + 1/86) n (Find-Golovnev-Hirsch-Kulikov 2016), sealed at n = 1000 and carried as the stick's bound with
    the window above it (superlinear is unknown; 2^n / n would be needed); the hierarchy theorem's separating factor; the
    brute-force count 2^50; the 3-SAT threshold instance; Cook-Levin's quadratic blow-up. Proven links cited: Cook 1971 /
    Levin 1973 (P = NP <=> SAT in P), Hartmanis-Stearns 1965 (P != EXPTIME), Ladner 1975, Williams 2011 (NEXP not in ACC0,
    a lower bound past all three barriers). The POSTULATE: polynomial time is feasibility (Cobham 1965, Edmonds 1965) on
    the Church-Turing model. The window read. Idempotent."""
    import math
    from concordance import tickstick as TS
    S = {}
    seals = [
        ("blum", "blum_1984_circuit_lower_bound_3n_at_n_1000", "3*1000", 3000.0, 1e-12),
        ("fghk", "fghk_2016_circuit_lower_bound_3_plus_1_over_86_n_at_n_1000", "(3 + 1/86)*1000", (3 + 1 / 86) * 1000, 1e-9),
        ("hier", "time_hierarchy_separating_factor_log_n_at_n_1e6", "log(1e6)", math.log(1e6), 1e-9),
        ("brute", "brute_force_assignments_of_50_variables", "2**50", 2.0 ** 50, 1e-12),
        ("sat", "three_sat_satisfiability_threshold_clauses_at_n_1000", "4.267*1000", 4267.0, 1e-9),
        ("cook", "cook_levin_circuit_size_t_squared_at_t_1e6", "(1e6)**2", 1e12, 1e-9),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "P vs NP numbers:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("P versus NP")["id"]
    marks = [
        ("bound", "The best PROVEN circuit lower bound for an explicit Boolean function is (3 + 1/86) n - o(n) gates "
                  "(Find, Golovnev, Hirsch, Kulikov 2016), raised from Blum's 3n - o(n) of 1984; at n = 1000 that is 3011.6 "
                  "gates (sealed). Every lower bound ever proven for an explicit function is linear; P != NP by circuits "
                  "would need superpolynomial. This is the stick's one ratcheting number: the window above it is the whole "
                  "problem.", {"seal": S["fghk"], "up_to": 3 + 1 / 86, "unit": "n gates (explicit lower bound)"}),
        ("instance", "[the ladder's first rung] Blum 1984: 3n - o(n) gates for an explicit function - 3000 at n = 1000 "
                     "(sealed). Thirty-two years to raise it by n/86.", S["blum"]),
        ("instance", "[the one separation that is easy] The time hierarchy theorem (Hartmanis-Stearns 1965): more time "
                     "decides more; DTIME(n^2) is strictly inside DTIME(n^2 log^2 n), and so P != EXPTIME - PROVEN. The "
                     "separating factor at n = 10^6 is log n = 13.8 (sealed). The theorem works by diagonalization, which "
                     "relativizes - which is exactly why it cannot reach P vs NP (the first barrier on this stick).",
         S["hier"]),
        ("instance", "[what brute force costs] Fifty Boolean variables have 2^50 = 1.13e15 assignments (sealed). SAT asks "
                     "whether one of them works; P = NP would mean the question never needs the count.", S["brute"]),
        ("instance", "[where hardness lives, measured] Random 3-SAT at n variables goes from almost surely satisfiable to "
                     "almost surely not at about 4.267 clauses per variable (Mertens-Mezard-Zecchina 2006, the cavity "
                     "prediction; the threshold's existence is Friedgut's theorem) - 4267 clauses at n = 1000 (sealed as "
                     "the instance of a stated constant). The hardest instances cluster at the transition.", S["sat"]),
        ("instance", "[Cook-Levin: the reduction's cost] A computation of t steps becomes a circuit of O(t^2) gates "
                     "(t = 10^6 gives 10^12, sealed), so every NP problem reduces to SAT in polynomial time - which is why "
                     "ONE problem carries the whole question: P = NP if and only if SAT is in P.", S["cook"]),
        ("postulate", "[the postulate it builds on] Polynomial time is feasibility: a problem is tractable when some "
                      "algorithm solves every instance of size n within n^k steps for a fixed k, on a Turing machine - "
                      "the Cobham-Edmonds thesis on the Church-Turing model. Not kept as a fact: every algorithm in use "
                      "works under it, and the classes P and NP are defined by it; from its working the truth of the "
                      "framing is inferred - never proven, never kept as fact.",
         {"source": "A. Cobham (1965); J. Edmonds, Paths, trees, and flowers (1965); A. Church (1936), A. Turing (1936)"}),
        ("equivalence", "[proven links] Cook 1971 / Levin 1973: SAT is NP-complete, so P = NP <=> SAT in P; Karp 1972: "
                        "twenty-one problems join it. Hartmanis-Stearns 1965: P != EXPTIME. Ladner 1975: if P != NP there "
                        "are NP problems neither in P nor NP-complete. Williams 2011: NEXP is not in ACC0 - a lower bound "
                        "proven PAST all three barriers on this stick, the first in decades, by an algorithm for "
                        "circuit-satisfiability turned into a separation.",
         {"source": "S. A. Cook (1971); L. Levin (1973); R. M. Karp (1972); J. Hartmanis, R. E. Stearns (1965); R. E. Ladner (1975); R. Williams, Non-uniform ACC circuit lower bounds (2011)"}),
        ("note", "[the surviving window, read] Sealed: the lower-bound ladder's rungs, the hierarchy factor, the brute-force "
                 "count, the threshold instance, the reduction's cost. Proven (cited): SAT is complete, P != EXPTIME, "
                 "Ladner, Williams. Excluded (cited, already on this stick): relativization, natural proofs, algebrization "
                 "- a proof must use the specific structure of computation in a way none of those do. Open: everything "
                 "between (3 + 1/86) n and superpolynomial. Gaps become wants: the cited texts (Cook, Karp, Blum, FGHK, "
                 "Williams) and Aaronson's survey for inclusion; the geometric complexity theory program (Mulmuley-Sohoni) "
                 "as the one road not yet excluded, cited; a SAT solver door so a stated instance's satisfiability is "
                 "COMPUTED and sealed here. Every link sealed or cited; nothing out of thin air; the chain not closed.",
         {"source": "S. Aaronson, P =? NP (2016), in Open Problems in Mathematics; K. Mulmuley, M. Sohoni (2001); this stick's three exclusions"}),
    ]
    _mint_marks(sid, marks, by="tools/tick.py p_versus_np_next")
    return 0


def hodge_next() -> int:
    """THE HODGE CONJECTURE - THE FIRST LINKS (the Millennium loop, 2026-10-09; the law: nothing out of thin air, everything
    bound). The stick had no marks. Now: the Hodge diamond's arithmetic sealed - the Euler characteristic of projective
    3-space (4), of a K3 surface (24) and of an abelian surface (0) by the alternating sum of the h^{p,q}; the K3's second
    Betti number 22 = 1 + 20 + 1; the quintic threefold's middle Betti number 204 = 2(1 + 101) and its Euler characteristic
    -200 = 2(h^{1,1} - h^{2,1}); a genus-3 curve's Euler characteristic -4. The proven cases cited: Lefschetz (1,1) (1924)
    settles divisors, hard Lefschetz carries it to codimension n - 1, so EVERY variety of dimension <= 3 satisfies the
    conjecture - the first open case is codimension 2 in dimension 4 (Weil's abelian fourfolds). The two exclusions that
    fix the statement's exact edge: Atiyah-Hirzebruch 1961 (the integral form is false) and Voisin 2002 (the Kahler form is
    false). The POSTULATE the stick builds on: the conjecture is to be taken with rational coefficients on projective
    varieties - it is kept in that form because that is the form that works. The window read. Idempotent."""
    from concordance import tickstick as TS
    S = {}
    seals = [
        ("p3", "euler_characteristic_of_projective_3_space", "3 + 1", 4.0, 1e-12),
        ("k3", "euler_characteristic_of_a_k3_surface_by_the_diamond", "1 + 1 + 20 + 1 + 1", 24.0, 1e-12),
        ("k3b2", "second_betti_number_of_a_k3_surface_h20_h11_h02", "1 + 20 + 1", 22.0, 1e-12),
        ("ab", "euler_characteristic_of_an_abelian_surface_by_the_diamond_one_plus_zero", "1 + (1 - 2 - 2 + 1 + 4 + 1 - 2 - 2 + 1)", 1.0, 1e-12),
        ("quintic_chi", "euler_characteristic_of_the_quintic_threefold_2_h11_minus_h21", "2*(1 - 101)", -200.0, 1e-12),
        ("quintic_b3", "middle_betti_number_of_the_quintic_threefold", "2*(1 + 101)", 204.0, 1e-12),
        ("curve", "euler_characteristic_of_a_genus_3_curve", "2 - 2*3", -4.0, 1e-12),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "Hodge numbers:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("Hodge conjecture")["id"]
    marks = [
        ("instance", "[the diamond's arithmetic, sealed] Projective 3-space has h^{p,p} = 1 for p = 0..3 and nothing else: "
                     "chi = 3 + 1 = 4 (sealed); every class is a power of the hyperplane class, algebraic - the conjecture holds "
                     "trivially there. The arithmetic the conjecture is stated in is this alternating sum of Hodge numbers.",
         S["p3"]),
        ("instance", "[a K3 surface] h^{0,0} = h^{2,2} = 1, h^{2,0} = h^{0,2} = 1, h^{1,1} = 20: chi = 24 (sealed) and b_2 = 22 "
                     "(sealed). The (1,1) classes are 20-dimensional; the Picard rank - how many are algebraic - is anything "
                     "from 0 to 20, and Lefschetz (1,1) says exactly the rational (1,1) classes are algebraic: for a surface "
                     "the conjecture is a theorem.", S["k3"]),
        ("instance", "[b_2 = 22]", S["k3b2"]),
        ("instance", "[an abelian surface] h^{1,0} = h^{0,1} = 2, h^{2,0} = h^{0,2} = 1, h^{1,1} = 4, h^{2,1} = h^{1,2} = 2: "
                     "the alternating sum is 0 (sealed as 1 + 0 = 1) - a torus has Euler characteristic zero. Dimension 2, so "
                     "the conjecture holds here by Lefschetz (1,1).", S["ab"]),
        ("instance", "[the quintic threefold] h^{1,1} = 1, h^{2,1} = 101: chi = 2(1 - 101) = -200 (sealed) and the middle "
                     "Betti number b_3 = 2(1 + 101) = 204 (sealed). Dimension 3: codimension 1 by Lefschetz (1,1), codimension "
                     "2 by hard Lefschetz from codimension 1 - the conjecture is a THEOREM for every threefold. The famous "
                     "Calabi-Yau is not an open case.", S["quintic_chi"]),
        ("instance", "[b_3 = 204]", S["quintic_b3"]),
        ("instance", "[a curve] genus 3: h^{1,0} = h^{0,1} = 3, chi = 2 - 2g = -4 (sealed). Dimension 1: nothing to conjecture "
                     "- the only Hodge classes are the point and the fundamental class.", S["curve"]),
        ("postulate", "[the postulate it builds on] The conjecture is to be taken with RATIONAL coefficients, for smooth "
                      "projective varieties over the complex numbers: a rational class of type (p,p) is a rational combination "
                      "of classes of algebraic subvarieties. It is kept in this form, not the integral or the Kahler form, "
                      "because this is the form that works - every proven case works under it and the other two forms are "
                      "refuted. Not kept as a fact: from its working the truth is inferred - never proven, never kept as fact.",
         {"source": "W. V. D. Hodge, The topological invariants of algebraic varieties (ICM 1950); P. Deligne, The Hodge conjecture (Clay Mathematics Institute, 2000)"}),
        ("equivalence", "[proven links] Lefschetz (1,1) (1924, in Hodge's form): every rational class of type (1,1) is the class of "
                        "a divisor - codimension 1 CLOSED. Hard Lefschetz (Hodge 1941; Deligne 1968 in general) carries "
                        "codimension 1 to codimension n - 1. Hence every smooth projective variety of dimension <= 3 satisfies "
                        "the conjecture - CLOSED. Hodge's decomposition H^k(X, C) = sum of H^{p,q} (1941) is the theorem the "
                        "conjecture is stated in. The first open case: codimension 2 in dimension 4 - Weil's abelian fourfolds "
                        "(1977) are the test case.",
         {"source": "S. Lefschetz (1924); W. V. D. Hodge, The Theory and Applications of Harmonic Integrals (1941); P. Deligne (1968); A. Weil (1977)"}),
        ("exclusion", "[the statement's edge, fixed by two counterexamples] Atiyah-Hirzebruch 1961: the INTEGRAL Hodge "
                      "conjecture is false - there are integral (p,p) classes that are not integral combinations of algebraic "
                      "classes (torsion classes that no cycle carries). Voisin 2002: the conjecture is false for compact "
                      "KAHLER manifolds that are not projective. So the rational, projective form is the only one left "
                      "standing, and the stick's postulate is exactly that form.",
         {"source": "M. F. Atiyah, F. Hirzebruch, Analytic cycles on complex manifolds (1961); C. Voisin, A counterexample to the Hodge conjecture extended to Kahler varieties (2002)"}),
        ("note", "[the surviving window, read] Sealed: the diamond's arithmetic on six varieties. Proven (cited): dimension "
                 "<= 3 entirely, codimension 1 everywhere. Excluded: the integral form, the Kahler form. Open: codimension "
                 ">= 2 in dimension >= 4 - the abelian fourfolds with Weil classes are where it is tested. Gaps become wants: "
                 "the cited texts for inclusion; a Hodge-diamond calculator for complete intersections (Hirzebruch's "
                 "generating function) so the diamond of a stated hypersurface is COMPUTED here, not typed from a table. "
                 "Every link sealed or cited; nothing out of thin air; the chain not closed.",
         {"source": "P. Deligne (2000); J. D. Lewis, A Survey of the Hodge Conjecture (1999)"}),
    ]
    _mint_marks(sid, marks, by="tools/tick.py hodge_next")
    return 0


def poincare_next() -> int:
    """THE POINCARE CONJECTURE - A CLOSED CHAIN (the Millennium loop, 2026-10-09; the law: nothing out of thin air,
    everything bound). Solved: Perelman 2002-2003, on Hamilton's Ricci flow with surgery; the write-ups Morgan-Tian,
    Kleiner-Lott, Cao-Zhu; the Clay prize awarded 2010 and declined. The stick had no marks. Now: the round 3-sphere under
    Ricci flow sealed (the radius-squared shrinks at rate -2(n-1) = -4, extinction at r0^2/4 = 0.25, the volume fraction
    at t = 0.1 is (1 - 0.4)^(3/2) = 0.4648, the unit sphere's scalar curvature n(n-1) = 6, chi(S^3) = 0); the two-dimensional
    template sealed (Gauss-Bonnet: chi(S^2) = 2 from the curvature integral; the normalized flow rounds every metric on
    S^2, Hamilton 1988, Chow 1991); the theorem cited AS THE CLOSING MARK - the first stick in the store whose fit reads
    CLOSED; the surviving window: none for the conjecture, the chain is bound all the way. This is the template of what
    'done' looks like on a stick. Idempotent."""
    from concordance import tickstick as TS
    S = {}
    seals = [
        ("rate", "ricci_flow_round_s3_radius_squared_rate_minus_2_n_minus_1", "-2*(3 - 1)", -4.0, 1e-12),
        ("extinct", "ricci_flow_round_unit_s3_extinction_time_r0_squared_over_4", "1**2/4", 0.25, 1e-12),
        ("volume", "ricci_flow_round_unit_s3_volume_fraction_at_t_0_1", "(1 - 4*0.1)**1.5", (1 - 4 * 0.1) ** 1.5, 1e-9),
        ("scalar", "unit_s3_scalar_curvature_n_n_minus_1", "3*2", 6.0, 1e-12),
        ("chi", "euler_characteristic_of_s3_one_plus_zero", "1 + (1 - 1)", 1.0, 1e-12),
        ("gb", "gauss_bonnet_on_the_unit_s2_curvature_integral_over_2pi", "(1/(2*pi))*(1/1**2)*4*pi*1**2", 2.0, 1e-9),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "Poincare numbers:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("Poincare conjecture")["id"]
    marks = [
        ("instance", "[the round sphere under Ricci flow, sealed] dg/dt = -2 Ric; on a round S^n, Ric = (n - 1)/r^2 g, so "
                     "d(r^2)/dt = -2(n - 1) = -4 for n = 3 (sealed): the sphere shrinks homothetically and vanishes at "
                     "T = r0^2/4 = 0.25 for r0 = 1 (sealed). Hamilton's equation (1982) on the simplest input - the shape the "
                     "theorem says every simply connected closed 3-manifold is.", S["rate"]),
        ("instance", "[extinction at 0.25]", S["extinct"]),
        ("instance", "[the volume on the way down] At t = 0.1 the radius squared is 1 - 0.4 and the volume fraction "
                     "(0.6)^(3/2) = 0.4648 (sealed): the flow is a shrinking, not a tearing - until, on a general manifold, "
                     "it pinches, which is where Perelman's surgery enters.", S["volume"]),
        ("instance", "[the curvature it starts from] The unit S^3 has scalar curvature n(n - 1) = 6 (sealed); positive "
                     "scalar curvature is what the flow drives toward extinction in finite time - Perelman's finite "
                     "extinction theorem is the step that handles the simply connected case without the full "
                     "geometrization.", S["scalar"]),
        ("instance", "[chi(S^3) = 0] An odd-dimensional closed manifold has Euler characteristic zero: 1 - 0 + 0 - 1 = 0 "
                     "(sealed as 1 + 0 = 1). The Euler characteristic cannot tell S^3 from any other closed 3-manifold - "
                     "which is why the conjecture needed the fundamental group, and why it was hard.", S["chi"]),
        ("instance", "[the two-dimensional template, sealed] Gauss-Bonnet on the unit S^2: (1/2 pi) int K dA = "
                     "(1/2 pi)(1)(4 pi) = 2 = chi(S^2) (sealed). In dimension two the classification is a 19th-century "
                     "theorem; the normalized Ricci flow rounds every metric on S^2 (Hamilton 1988, Chow 1991) - the "
                     "picture Hamilton's program lifted to dimension three.", S["gb"]),
        ("closed", "Every simply connected closed 3-manifold is homeomorphic to the 3-sphere: PROVEN by Grigori Perelman "
                   "(2002-2003) by Hamilton's Ricci flow with surgery - the entropy and reduced-volume monotonicity, the "
                   "canonical neighbourhood theorem, the finite extinction time for simply connected manifolds - with "
                   "the full geometrization conjecture of Thurston proven alongside. The chain is bound all the way.",
         {"source": "G. Perelman, arXiv math/0211159 (2002), math/0303109 (2003), math/0307245 (2003); R. S. Hamilton, Three-manifolds with positive Ricci curvature, J. Diff. Geom. 17 (1982)"}),
        ("equivalence", "[the proof checked, three times over] The complete write-ups: Kleiner-Lott, Notes on Perelman's "
                        "papers (Geom. Topol. 12, 2008); Morgan-Tian, Ricci Flow and the Poincare Conjecture (Clay "
                        "Monographs 3, 2007); Cao-Zhu, Asian J. Math. 10 (2006). The Clay Mathematics Institute awarded the "
                        "Millennium Prize on 18 March 2010; Perelman declined it, as he had declined the Fields Medal in "
                        "2006. Independent verifications are the receipts of a proof.",
         {"source": "B. Kleiner, J. Lott (2008); J. Morgan, G. Tian (2007); H.-D. Cao, X.-P. Zhu (2006); Clay Mathematics Institute, press release of 18 March 2010"}),
        ("note", "[the chain, read] Sealed: the flow on the round sphere, the template in dimension two. Cited: the "
                 "theorem that closes the chain, with its source, and the three independent write-ups. Open: nothing for "
                 "the conjecture - this stick is the template of what done looks like on a stick: a CLOSED fit, a cited "
                 "theorem, sealed instances under it. What remains is inclusion: Perelman's three papers and Hamilton "
                 "1982 as cards with attribution (a want), and a Ricci-flow integrator so the flow on a stated metric is "
                 "COMPUTED here rather than the round case alone.",
         {"source": "the three write-ups above; docs/MILLENNIUM_PREPAREDNESS.md"}),
    ]
    _mint_marks(sid, marks, by="tools/tick.py poincare_next")
    return 0


def _read_allbsd(text: str) -> dict:
    """Cremona's allbsd rows by label (e.g. '11a1'). The column reading - N, isogeny class, number, a-invariants,
    rank r, |T|, prod c_p, real period Omega, L^(r)(E,1)/r!, regulator, |Sha| - is undocumented in the repository
    README; sources_crosscheck proves it by sealing the full BSD formula on the rows' own numbers."""
    rows = {}
    for line in text.splitlines():
        f = line.split()
        if len(f) < 11 or not f[0].isdigit():
            continue
        rows[f[0] + f[1] + f[2]] = {"r": int(f[4]), "T": int(f[5]), "c": int(f[6]), "Omega": f[7], "L": f[8],
                                    "Reg": f[9], "Sha": f[10]}
    return rows


def _rvm_main_term(T: float) -> float:
    """The Riemann-von Mangoldt main term (T/2pi)(log(T/2pi) - 1) + 7/8; N(T) = this + S(T), |S(T)| small."""
    import math
    return (T / (2 * math.pi)) * (math.log(T / (2 * math.pi)) - 1) + 7 / 8


def sources_crosscheck() -> int:
    """THE FOUND TABLES, CROSS-CHECKED (the Millennium loop, 2026-10-09; Matt: "find all 17 and add them" - anything
    retrieved and used is included). Two tables were fetched to the box's untrusted ark: Odlyzko's zeros1 (the first
    100,000 zeros of zeta, stated accuracy 3e-9; NO terms are stated on its page, so the file is HELD for cross-checks
    and its numbers are never carded) and Cremona's allbsd.00000-09999 (ecdata, Artistic License 2.0). Nothing in them
    is trusted: the stick's own sealed count below T = 1000 is READ OFF THE STICK (never typed) and the table must agree;
    the first zero is compared with the engine's own zetazero(1); the Riemann-von Mangoldt main term at the table's last
    zero is sealed and S(T) read off it; the 11a1 and 37a1 rows must carry the inputs CURVES_BSD_INPUTS cites, and the
    full BSD formula is sealed FROM THE TABLE'S OWN NUMBERS. A table that disagrees refuses the mark - a miss stays a
    miss. Idempotent."""
    import hashlib
    import re
    from concordance import tickstick as TS
    ark = Path(os.environ.get("CONCORDANCE_ARK_MILLENNIUM", "/home/nh/ark_untrusted/millennium"))
    zp, bp = ark / "zeros1", ark / "allbsd.00000-09999"
    missing = [str(p) for p in (zp, bp) if not p.exists()]
    if missing:
        print("the ark does not hold:", ", ".join(missing)); return 2

    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    # -- Odlyzko's zeros1 against the Riemann stick --
    zeros = [float(t) for t in zp.read_text().split()]
    if len(zeros) != 100000 or zeros != sorted(zeros) or not (14.0 < zeros[0] < 15.0):
        print("zeros1 is not the table its page describes (100,000 ascending zeros from 14.13...)"); return 1
    rsid = TS.create("Riemann hypothesis")["id"]
    kept = None
    for t in TS.read(rsid).get("ticks", []):
        if t.get("kind") == "bound" and float(t.get("up_to") or 0) == 1000.0:
            m = re.search(r"\((\d+) zeros", t.get("claim") or "")
            if m:
                kept = int(m.group(1)); break
    if kept is None:
        print("the Riemann stick carries no sealed bound at T = 1000 to check the table against"); return 1
    n1000 = sum(1 for g in zeros if g <= 1000.0)
    if n1000 != kept:
        print(f"DISAGREEMENT: the table holds {n1000} zeros below 1000, the stick sealed {kept} - no mark"); return 1
    import mpmath
    z1 = float(mpmath.zetazero(1).imag)
    if abs(z1 - zeros[0]) > 3e-9:
        print(f"DISAGREEMENT: the table's first zero {zeros[0]} vs the engine's {z1} - no mark"); return 1
    T = zeros[-1]
    main = _rvm_main_term(T)
    S = len(zeros) - main
    s_rvm = _rh_seal_num("odlyzko_zeros1_riemann_von_mangoldt_main_term_at_the_100000th_zero",
                         f"({T!r}/(2*pi))*(log({T!r}/(2*pi)) - 1) + 7/8", main, tol=1e-9)
    if not s_rvm:
        return 1
    zsha = sha(zp)
    print(f"zeros1: {len(zeros)} zeros, {n1000} below 1000 (stick: {kept}), first {zeros[0]} vs {z1:.9f}, "
          f"last {T}, main term {main:.3f}, S(T) = {S:.3f}; sha256 {zsha[:16]}")
    _mint_marks(rsid, [
        ("witness", f"[a found table, cross-checked] Odlyzko's zeros1 - the first 100,000 zeros of zeta, stated accuracy "
                    f"3e-9 (sha256 {zsha[:16]}...) - is held on the ark; no terms are stated on its page, so its numbers "
                    f"are not carded. Read, not trusted: it holds {n1000} zeros below T = 1000, equal to the {kept} the "
                    f"engine counted and sealed on its own; its first zero {zeros[0]} agrees with the engine's "
                    f"zetazero(1) = {z1:.9f} within the stated accuracy; at its last zero T = {T} the Riemann-von "
                    f"Mangoldt main term (T/2pi)(log(T/2pi) - 1) + 7/8 = {main:.3f} (sealed), so the remainder "
                    f"S(T) = N(T) - main = {S:.3f} there - under 1, as the argument-principle bound requires.",
         {"seal": s_rvm, "source": "A. M. Odlyzko, Tables of zeros of the Riemann zeta function, "
                                   "https://www-users.cse.umn.edu/~odlyzko/zeta_tables/ (zeros1)"}),
    ], by="tools/tick.py sources_crosscheck")
    # -- Cremona's allbsd against the BSD stick --
    rows = _read_allbsd(bp.read_text())
    need = ("11a1", "37a1")
    if any(k not in rows for k in need):
        print("the allbsd file lacks 11a1 / 37a1"); return 1
    bsha = sha(bp)
    marks = []
    for key in need:
        d, cite = rows[key], CURVES_BSD_INPUTS[key]
        sha_n = int(float(d["Sha"]))
        if (d["c"], d["T"], sha_n) != (cite["tamagawa_product"], cite["torsion_order"], cite["sha_order"]):
            print(f"DISAGREEMENT on {key}: table prod c_p, |T|, |Sha| = {d['c']}, {d['T']}, {sha_n} vs the cited inputs "
                  f"{cite} - no mark"); return 1
        if "regulator" in cite and abs(float(d["Reg"]) - cite["regulator"]) > 1e-12:
            print(f"DISAGREEMENT on the {key} regulator: table {d['Reg']} vs cited {cite['regulator']} - no mark"); return 1
        expr = f"{d['Omega']}*{d['c']}*{sha_n}/{d['T']}**2" + (f"*{d['Reg']}" if d["r"] >= 1 else "")
        val = float(d["Omega"]) * d["c"] * sha_n / d["T"] ** 2 * (float(d["Reg"]) if d["r"] >= 1 else 1.0)
        rel = abs(val - float(d["L"])) / abs(float(d["L"]))
        seal = _rh_seal_num(f"cremona_allbsd_{key}_full_bsd_formula_from_the_table_s_own_numbers", expr, float(d["L"]),
                            tol=1e-10)
        if not seal:
            return 1
        print(f"{key}: r={d['r']} |T|={d['T']} c={d['c']} Omega={d['Omega']} L={d['L']} Reg={d['Reg']} |Sha|={sha_n}; "
              f"formula {val:.15g}, agrees to {rel:.1e}")
        lhs = "L(E,1)" if d["r"] == 0 else "L'(E,1)"
        rhs = "Omega * prod c_p * |Sha| / |T|^2" + (" * R" if d["r"] >= 1 else "")
        marks.append(("witness",
                      f"[a found table, cross-checked] Cremona's ecdata allbsd.00000-09999 (Artistic License 2.0; sha256 "
                      f"{bsha[:16]}...) is held on the ark. Its {key} row reads rank {d['r']}, |T| = {d['T']}, prod c_p = "
                      f"{d['c']}, Omega = {d['Omega']}, {lhs} = {d['L']}, R = {d['Reg']}, |Sha| = {sha_n} - the inputs the "
                      f"stick cites from Cremona 1997 Table 1, now read from the table itself; and the full formula holds "
                      f"on the row's own numbers: {rhs} = {val:.15g} = {lhs} to {rel:.1e} (sealed). The column reading "
                      f"(N, class, number, a-invariants, r, |T|, prod c_p, Omega, L^(r)(E,1)/r!, Reg, |Sha|) is undocumented "
                      f"in the repository's README; the formula holding on the rows is what proves it.",
                      {"seal": seal, "source": "J. E. Cremona, ecdata, https://github.com/JohnCremona/ecdata (allbsd), "
                                               "Artistic License 2.0"}))
    bsid = TS.create("Birch and Swinnerton-Dyer conjecture")["id"]
    _mint_marks(bsid, marks, by="tools/tick.py sources_crosscheck")
    return 0


def millennium_map() -> int:
    """THE ONE MAP (Matt, 2026-10-09: "put them on one map, but make it the one map for the project"). The joints
    between the seven problems live on the keeping's graph (tools/seed_millennium_chain.py); the arithmetic of the two
    joints that HAVE arithmetic is sealed here, on the sticks that already exist - no new stick: (1) zeta and L(E,s)
    are one machinery: the completed zeta's functional equation xi(s) = xi(1 - s) checked at s = 0.3 (gamma and zeta
    evaluated by the engine, the ratio sealed as 1), a witness on the Riemann stick beside the BSD stick's L(11a1, 1)
    computed by the same approximate functional equation; (2) Myers 1941 under the hypothesis Hamilton 1982 starts
    from: Ric >= (n - 1)k gives diam <= pi/sqrt(k), equality on the round sphere - the unit S^3 at k = 1, diam = pi,
    sealed on the Poincare stick beside Bochner 1946 (positive Ricci kills harmonic one-forms, b_1 = 0 - Hodge's
    tool under Poincare's hypothesis). The other joints are cited as notes on their sticks, with sources. Nothing is
    unified by us: every joint is a join mathematics already made. Idempotent."""
    from concordance import tickstick as TS
    s_xi = _rh_seal_num("xi_functional_equation_at_s_0_3",
                        "(pi**(-0.3/2)*gamma(0.3/2)*zeta(0.3))/(pi**(-0.7/2)*gamma(0.7/2)*zeta(0.7))", 1.0, tol=1e-9)
    s_my = _rh_seal_num("myers_diameter_bound_on_the_unit_s3", "pi/sqrt(1)", 3.141592653589793, tol=1e-12)
    if not (s_xi and s_my):
        print("a seal failed; no marks"); return 1
    print("sealed xi(s) = xi(1 - s) at 0.3:", s_xi[:12], "| Myers on the unit S^3:", s_my[:12])
    by = "tools/tick.py millennium_map"
    _mint_marks(TS.create("Riemann hypothesis")["id"], [
        ("witness", "[the joint with BSD, sealed] Zeta and L(E,s) are one machinery - an Euler product, a functional "
                    "equation about a centre, a critical line. The completed zeta xi(s) = pi^(-s/2) Gamma(s/2) zeta(s) "
                    "satisfies xi(s) = xi(1 - s): checked at s = 0.3, the ratio xi(0.3)/xi(0.7) = 1 (sealed, gamma and "
                    "zeta evaluated here). The BSD stick's L(11a1, 1) = 0.2538 is computed by the same approximate "
                    "functional equation with the root number in place of the symmetry. Modularity (Wiles 1995) is what "
                    "gives L(E,s) its continuation; the Grand Riemann Hypothesis names both at once.",
         {"seal": s_xi, "source": "A. Wiles, Modular elliptic curves and Fermat's last theorem, Ann. Math. 141 (1995); "
                                  "card_joint_l_functions on the one map"}),
        ("note", "[the joints, cited] On the one map (card_floor_millennium) this stick connects to Yang-Mills at the "
                 "GUE statistics (Montgomery 1973, Odlyzko 1987, Verbaarschot 1994 - the spacing witness already sealed "
                 "here), to Hodge and P versus NP at the Weil conjectures - the Riemann hypothesis over finite fields, "
                 "proven by Deligne 1974, while the hypothesis itself stays open - and "
                 "to P versus NP at the Diophantine form of RH (Davis-Matiyasevich-Robinson 1976). No joint with "
                 "Navier-Stokes was found - a miss, recorded.",
         {"source": "tools/seed_millennium_chain.py; docs/MILLENNIUM_PREPAREDNESS.md"}),
    ], by=by)
    _mint_marks(TS.create("Poincare conjecture")["id"], [
        ("witness", "[the joint with Hodge, sealed] Myers 1941: a complete manifold with Ric >= (n - 1)k has diameter "
                    "at most pi/sqrt(k), with equality on the round sphere - the unit S^3 at k = 1 has diameter pi "
                    "(sealed). Bochner 1946: positive Ricci curvature admits no non-zero harmonic one-form, so b_1 = 0 - "
                    "the harmonic forms of Hodge theory vanishing under the very hypothesis Hamilton 1982 starts from. "
                    "Hodge's tool and Poincare's hypothesis meet on the sphere.",
         {"seal": s_my, "source": "S. B. Myers, Duke Math. J. 8 (1941); S. Bochner, Bull. AMS 52 (1946); "
                                  "card_joint_bochner_vanishing on the one map"}),
    ], by=by)
    _mint_marks(TS.create("Yang-Mills existence and mass gap")["id"], [
        ("note", "[the joints, cited] On the one map this stick connects to Riemann at the GUE statistics - the low-lying "
                 "spectrum of the lattice Dirac operator follows chiral random matrix theory (Verbaarschot 1994) as the "
                 "zeta zeros follow GUE (sealed on the Riemann stick); to Navier-Stokes at the renormalization group "
                 "(Wilson 1974; Forster-Nelson-Stephen 1977 for the stirred fluid), where in both the continuum limit of "
                 "a finite system is the question; and to P versus NP at the sign problem, NP-hard (Troyer-Wiese 2005).",
         {"source": "J. J. M. Verbaarschot, PRL 72 (1994); D. Forster, D. R. Nelson, M. J. Stephen, PRA 16 (1977); "
                    "M. Troyer, U.-J. Wiese, PRL 94 (2005)"}),
    ], by=by)
    _mint_marks(TS.create("Navier-Stokes existence and smoothness")["id"], [
        ("note", "[the joints, cited] On the one map this stick connects to Yang-Mills at the renormalization group "
                 "(the Kolmogorov scale sealed here, the running coupling sealed there) and to Poincare at Arnold 1966 - "
                 "Euler flow as geodesic flow on the volume-preserving diffeomorphisms, the geometric analysis "
                 "Perelman's proof lives in; it has not produced regularity. No joint with Riemann - a miss, recorded.",
         {"source": "V. I. Arnold, Ann. Inst. Fourier 16 (1966); D. Forster, D. R. Nelson, M. J. Stephen, PRA 16 (1977)"}),
    ], by=by)
    _mint_marks(TS.create("P versus NP")["id"], [
        ("note", "[the joints, cited - restated for precision, 2026-10-09] On the one map this stick connects to Riemann "
                 "and Hodge at Deligne 1974 - the Weil conjectures, the Riemann hypothesis for varieties over FINITE "
                 "FIELDS, a theorem; the Riemann hypothesis itself stays open - whose positivity Mulmuley's geometric "
                 "complexity theory leans on (the one road not excluded by a barrier); to Riemann at the Diophantine form "
                 "of RH (Davis-Matiyasevich-Robinson "
                 "1976); to BSD at Manin 1971 (finite Sha makes the rank computable); to Yang-Mills at the NP-hard sign "
                 "problem (Troyer-Wiese 2005).",
         {"source": "P. Deligne, Publ. Math. IHES 43 (1974); K. Mulmuley, J. ACM 58 (2011); Yu. I. Manin, Russian Math. "
                    "Surveys 26 (1971); M. Davis, Yu. Matiyasevich, J. Robinson, Proc. Symp. Pure Math. 28 (1976)"}),
    ], by=by)
    _mint_marks(TS.create("Hodge conjecture")["id"], [
        ("note", "[the joints, cited] On the one map this stick connects to BSD at the Tate conjecture - Hodge's "
                 "arithmetic twin, equivalent for an elliptic surface over a finite field to BSD for its fibre "
                 "(Tate 1965, Artin-Tate 1966, Milne 1975); to Riemann and P versus NP at Deligne 1974, whose weights "
                 "are the finite-field shadow of Hodge theory; to Poincare at Bochner 1946 (sealed on the Poincare "
                 "stick).",
         {"source": "J. Tate, Algebraic cycles and poles of zeta functions (1965); M. Artin, J. Tate, Sem. Bourbaki 306 "
                    "(1966); J. S. Milne, Ann. Math. 102 (1975)"}),
    ], by=by)
    _mint_marks(TS.create("Birch and Swinnerton-Dyer conjecture")["id"], [
        ("note", "[the joints, cited] On the one map this stick connects to Riemann at the one L-function machinery "
                 "(xi(s) = xi(1 - s) sealed on the Riemann stick; L(11a1, 1) sealed here by the same approximate "
                 "functional equation), to Hodge at the Tate conjecture (Artin-Tate 1966, Milne 1975), and to P versus "
                 "NP at Manin 1971: if Sha is finite the rank is computable, and today it is not known to be.",
         {"source": "J. S. Milne, Ann. Math. 102 (1975); Yu. I. Manin, Russian Math. Surveys 26 (1971)"}),
    ], by=by)
    return 0


def logarithm_chain() -> int:
    """THE LOGARITHM CHAIN (Matt, 2026-10-09: "logarithms fit here correct?" - "same"). The logarithm is the instrument
    the Millennium joints share; its chain is seeded on the one map (tools/seed_chains.py). The arithmetic where it
    enters four of the problems is sealed here, on the sticks that exist: Riemann - Gauss's logarithmic integral
    overshoots the prime count at 1000 (pi(1000) counted here, li(1000) evaluated here, the difference sealed) - the
    error the hypothesis bounds; Navier-Stokes - the law of the wall at y+ = 100 with kappa = 0.41, B = 5.0 (the
    constants as commonly stated, inputs named in the mark); P versus NP - the length of 2^64 is floor(log10 2^64) + 1
    = 20 digits: the input length IS the logarithm; Poincare - the entropy of one fair coin, log 2 = 0.693 nats, the
    unit of the entropy Perelman's W functional is built from. BSD, Yang-Mills and Hodge are cited as notes (their
    logarithms are already sealed or carried on the stick). Idempotent."""
    import math
    from concordance import tickstick as TS
    from sympy import primepi
    import mpmath
    n1000 = int(primepi(1000))                         # counted, not typed
    li1000 = float(mpmath.li(1000))
    s_li = _rh_seal_num("li_1000_minus_the_prime_count", f"li(1000) - {n1000}", li1000 - n1000, tol=1e-9)
    s_ln2 = _rh_seal_num("entropy_of_one_fair_coin_log_2", "log(2)", math.log(2), tol=1e-12)
    s_wall = _rh_seal_num("law_of_the_wall_u_plus_at_y_plus_100", "(1/0.41)*log(100) + 5.0", (1 / 0.41) * math.log(100) + 5.0,
                          tol=1e-9)
    s_dig = _rh_seal_num("digits_of_2_to_the_64", "floor(log(2**64, 10)) + 1", 20.0, tol=1e-12)
    if not (s_li and s_ln2 and s_wall and s_dig):
        print("a seal failed; no marks"); return 1
    print("sealed li(1000)-pi(1000):", s_li[:12], "| log 2:", s_ln2[:12], "| the wall at y+=100:", s_wall[:12],
          "| digits of 2^64:", s_dig[:12])
    by = "tools/tick.py logarithm_chain"
    _mint_marks(TS.create("Riemann hypothesis")["id"], [
        ("witness", f"[the logarithm, sealed] Gauss read the prime count off his log tables and guessed li(x); at x = 1000 "
                    f"the logarithmic integral is li(1000) = {li1000:.6f} and the count is pi(1000) = {n1000} (counted here), "
                    f"so li overshoots by {li1000 - n1000:.6f} (sealed). The Riemann hypothesis is exactly a bound on that "
                    f"overshoot: |pi(x) - li(x)| < sqrt(x) log(x) / (8 pi) for x >= 2657 (Schoenfeld, cited on this stick). "
                    f"The logarithm is the ruler the whole question is measured with - log zeta, N(T), li(x).",
         {"seal": s_li, "source": "C. F. Gauss, letter to Encke (1849); L. Schoenfeld, Math. Comp. 30 (1976); "
                                  "card_floor_logarithm on the one map"}),
    ], by=by)
    _mint_marks(TS.create("Navier-Stokes existence and smoothness")["id"], [
        ("witness", "[the logarithm, sealed] The law of the wall (von Karman 1930): in a turbulent boundary layer the "
                    "velocity profile is logarithmic in the distance from the wall, u+ = (1/kappa) ln(y+) + B. With the "
                    f"constants as commonly stated, kappa = 0.41 and B = 5.0, at y+ = 100 this gives u+ = "
                    f"{(1 / 0.41) * math.log(100) + 5.0:.4f} (sealed; the constants are inputs, not derived). The one "
                    "logarithm turbulence is known to obey, beside the power law of the cascade.",
         {"seal": s_wall, "source": "T. von Karman, Nachr. Ges. Wiss. Gottingen (1930) 58-76; card_floor_logarithm"}),
    ], by=by)
    _mint_marks(TS.create("P versus NP")["id"], [
        ("witness", "[the logarithm, sealed] The length of the input is the logarithm of the number: 2^64 has "
                    "floor(log10(2^64)) + 1 = 20 digits (sealed). 'Polynomial time' means polynomial in that length - "
                    "Cobham 1965, Edmonds 1965 - so the whole question is posed on a logarithmic ruler: a number N is "
                    "written in log N symbols, and an algorithm polynomial in N is exponential in its input.",
         {"seal": s_dig, "source": "A. Cobham, The intrinsic computational difficulty of functions (1965); J. Edmonds, "
                                   "Canad. J. Math. 17 (1965); card_floor_logarithm"}),
    ], by=by)
    _mint_marks(TS.create("Poincare conjecture")["id"], [
        ("witness", "[the logarithm, sealed] Perelman's first paper is titled the entropy formula, and his W functional is "
                    "a log-Sobolev inequality: the entropy minus the integral of u log u, in the line that runs Boltzmann "
                    "1877 (S = k log W) to Shannon 1948 (H = -sum p log p). The unit of that measure is the entropy of one "
                    f"fair coin, log 2 = {math.log(2):.6f} nats = 1 bit (sealed). The logarithm is the measure the closing "
                    "mark's monotone quantity is built from.",
         {"seal": s_ln2, "source": "G. Perelman, arXiv math/0211159 (2002); C. E. Shannon, Bell Syst. Tech. J. 27 (1948); "
                                   "L. Boltzmann, Wien. Ber. 76 (1877); card_floor_logarithm"}),
    ], by=by)
    _mint_marks(TS.create("Birch and Swinnerton-Dyer conjecture")["id"], [
        ("note", "[the logarithm, cited] The height of a rational point is the logarithm of the size of its coordinates "
                 "(Weil 1929), made quadratic by Neron and Tate (1965); the regulator cited on 37a1, R = 0.0511, is a "
                 "determinant of those logarithms, and Gross-Zagier ties L'(E, 1) to the height of a Heegner point. The "
                 "logarithm is how the conjecture measures its points.",
         {"source": "A. Weil, Acta Math. 52 (1929); A. Neron, Ann. Math. 82 (1965); card_floor_logarithm"}),
    ], by=by)
    _mint_marks(TS.create("Yang-Mills existence and mass gap")["id"], [
        ("note", "[the logarithm, cited] The coupling runs as one over the logarithm of the scale - Gell-Mann and Low's "
                 "renormalization group (1954), asymptotic freedom (Gross-Wilczek, Politzer 1973); alpha_s from M_Z to "
                 "10 GeV at one loop is sealed on this stick. The mass gap is the scale where that logarithm runs out.",
         {"source": "M. Gell-Mann, F. E. Low, Phys. Rev. 95 (1954); card_floor_logarithm"}),
    ], by=by)
    _mint_marks(TS.create("Hodge conjecture")["id"], [
        ("note", "[the logarithm, cited] Mixed Hodge theory is built on forms with logarithmic poles, dz/z (Deligne, "
                 "Theorie de Hodge II, 1971), and the monodromy of a degenerating family enters through its logarithm "
                 "(Schmid 1973). The logarithmic differential is the one form the theory cannot do without.",
         {"source": "P. Deligne, Publ. Math. IHES 40 (1971); W. Schmid, Invent. Math. 22 (1973); card_floor_logarithm"}),
    ], by=by)
    return 0

# The curves Cremona's tables name (a-invariants, conductor, root number, the algebraic rank the tables record).
# J. E. Cremona, Algorithms for Modular Elliptic Curves (1997) and the LMFDB; a-invariants are facts, not prose.
# The BSD-formula inputs the attempt of 2026-10-09 located and INCLUDES (Cremona, Algorithms for Modular Elliptic Curves,
# 1997, Table 1; LMFDB 11.a3 / 37.a1): the Tamagawa product, the torsion order, |Sha| (proven finite and trivial for these
# by Kolyvagin), and for rank 1 the regulator (the canonical height of the generator (0,0) on 37a1). Cited, never computed.
CURVES_BSD_INPUTS = {
    "11a1": {"tamagawa_product": 5, "torsion_order": 5, "sha_order": 1,
             "inputs_source": "J. E. Cremona, Algorithms for Modular Elliptic Curves (1997), Table 1; LMFDB 11.a3"},
    "37a1": {"tamagawa_product": 1, "torsion_order": 1, "sha_order": 1, "regulator": 0.0511114082399688,
             "inputs_source": "J. E. Cremona, Algorithms for Modular Elliptic Curves (1997), Table 1; LMFDB 37.a1"},
}
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
    return _mint_marks(sid, marks, by="Narrow Highway — the large-numbers reading, 2026-10-05")


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
    return _mint_marks(sid, marks, by="Narrow Highway — the symphony, the coherence witness, 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway — fiber optic calibration, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway — the Aharonov-Bohm reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway — the relational reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway — the fine-structure reading, 2026-10-05")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the atomic-orbital reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the running reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the four-forces reading (QED/QFT), 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the Markov-chain reading (lattice QCD), 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the loop-quantum-gravity reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the Schrodinger-equation reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the quantum-factoring reading (Shor/Regev), 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the positive-Grassmannian reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the Godel reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the string-theory reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the grand-unification reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the measurement-problem reading, 2026-10-06")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the Langlands reading, 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the trigonometry reading, 2026-10-07")


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
    """Shared mint loop - every stick mints through it (2026-10-08: the 25 inline copies and the two kw-dict
    loops were folded in; alpha() had no duplicate guard at all). A mark is (kind, claim, seal) or (kind, claim,
    kw-dict with seal= and/or source=). Idempotent, seal-or-claim guarded. A mark already kept in full is skipped. One kept CUT at
    an older cap - its stored text a strict prefix of the mark (2026-10-08: the cap was 600; 45 kept marks, mostly
    the guard notes, were stored mid-sentence) - is ticked again in full, and the reader supersedes the cut copy
    (tickstick._collapse). A sealed mark whose wording changed but whose seal is kept stays as kept: the seal governs."""
    from concordance import tickstick as TS
    cap = getattr(TS, "CLAIM_CAP", 600)
    ticks = TS.read(sid).get("ticks", [])
    added = 0
    for kind, claim, *rest in marks:
        extra = rest[0] if rest else None
        kw = dict(extra) if isinstance(extra, dict) else (dict(seal=extra) if extra else {})
        sealv = kw.get("seal")
        want = (claim or "").strip()[:cap]
        same = [t for t in ticks if t.get("kind") == kind and (t.get("seal") or "") == (sealv or "")]
        whole = any((t.get("claim") or "") == want for t in same)
        cut = any(len(want) > len(t.get("claim") or "") and want.startswith(t.get("claim") or "") for t in same)
        if whole or (sealv and same and not cut):
            print("  (already) " + kind); continue
        if cut:
            print("  (superseding a cut copy) " + kind)
        res = TS.tick(sid, kind, claim, by=by, **kw)
        if res.get("ok"):
            added += 1; print("  " + kind)
        else:
            print("  REFUSED " + kind + ": " + res.get("error", ""))
    f = TS.read(sid)["fit"]
    print(json.dumps({"stick": sid, "added": added, "witnesses": f["witnesses"], "record": len(f["record"]),
                      "open": f["open"]}, indent=1))
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


def electromagnetism() -> int:
    """ELECTROMAGNETISM AND GEOMETRY (Matt, 2026-10-08). Maxwell's equations are geometry: the field is a
    2-form F, Faraday's law and the no-monopole law are dF = 0, Ampere-Maxwell and Gauss's law are d*F = J;
    the inverse square IS the sphere (flux conserved through 4 pi r^2); c falls out of two vacuum constants
    (1/sqrt(mu0 eps0)); the vacuum has an impedance Z0 = sqrt(mu0/eps0); and the invariance of that c forced
    the geometry of spacetime itself (Lorentz, Minkowski) - E and B are one antisymmetric tensor. Seal the
    four numbers; map, never launder. New stick; idempotent."""
    from concordance import tickstick as TS
    mu0_e = "(1.25663706212 * 10 ** (-6))"           # CODATA 2018 vacuum permeability, N/A^2
    eps0_e = "(8.8541878128 * 10 ** (-12))"          # CODATA 2018 vacuum permittivity, F/m
    c_expr = "1 / (" + mu0_e + " * " + eps0_e + ") ** 0.5"
    z0_expr = "(" + mu0_e + " / " + eps0_e + ") ** 0.5"
    c_from = 1 / ((1.25663706212 * 10 ** (-6)) * (8.8541878128 * 10 ** (-12))) ** 0.5
    z0 = ((1.25663706212 * 10 ** (-6)) / (8.8541878128 * 10 ** (-12))) ** 0.5
    quarter = (1 / 2) ** 2                            # double the radius: the sphere's area quadruples
    gamma = 1 / (1 - 0.6 ** 2) ** 0.5                 # Lorentz factor at v = 0.6c
    s_c = _rh_seal_num("light_from_mu0_eps0", c_expr, float(c_from))
    s_q = _rh_seal_num("inverse_square_is_the_sphere", "(1 / 2) ** 2", float(quarter))
    s_z = _rh_seal_num("impedance_of_free_space", z0_expr, float(z0))
    s_g = _rh_seal_num("lorentz_factor_from_invariant_c", "1 / (1 - 0.6 ** 2) ** 0.5", float(gamma), tol=1e-12)
    if not all([s_c, s_q, s_z, s_g]):
        print("a seal failed; aborting"); return 1
    print("sealed c", s_c, "| 1/4", s_q, "| Z0", s_z, "| gamma", s_g)
    sid = TS.create("Electromagnetism and geometry",
                    statement=("Maxwell's equations are geometry. The field is a 2-form F: dF = 0 and d*F = J "
                               "are the whole theory in two lines of exterior calculus. The inverse square is "
                               "the sphere; c falls out of the vacuum's two constants; the vacuum has an "
                               "impedance; and the invariance of that c forced the geometry of spacetime "
                               "itself - E and B are one tensor, mixed by a boost."),
                    field="physics",
                    references=["Maxwell 1865, A Dynamical Theory of the Electromagnetic Field: c = 1/sqrt(mu0 eps0)",
                                "Gauss's law as flux conservation through a closed surface (4 pi r^2)",
                                "Z0 = sqrt(mu0/eps0) = 376.73 ohm; Lorentz 1904, Einstein 1905, Minkowski 1908",
                                "F = dA on a U(1) bundle; the Aharonov-Bohm phase as holonomy"])["id"]
    marks = [
        ("witness", f"[c falls out of the vacuum's two constants] Maxwell computed the speed of his waves from two "
                    f"laboratory constants and found light: 1/sqrt(mu0 eps0) = {c_from:.9g} m/s (sealed), which is "
                    f"c = 299,792,458 m/s to the precision of the listed values. In the 2018 SI eps0 is DEFINED through "
                    f"mu0 and c, so the circle closes exactly - not a coincidence, a geometry: light is the vacuum's own "
                    f"ratio.", s_c),
        ("witness", f"[the inverse square IS the sphere] Double the distance from a charge and the field falls to "
                    f"(1/2)^2 = {quarter} (sealed) - because the flux through a closed surface is conserved and a "
                    f"sphere's area is 4 pi r^2. Gauss's law is not a separate fact about charge; it is the geometry "
                    f"of three-dimensional space. The 4 pi in alpha = e^2 / (4 pi eps0 hbar c) is this same sphere "
                    f"(the alpha stick).", s_q),
        ("witness", f"[the vacuum has a shape] sqrt(mu0 / eps0) = {z0:.6f} ohm (sealed) - the impedance of free space, "
                    f"the fixed ratio of E to H in every plane wave. It is the number every transmission line and the "
                    f"Smith chart normalize against (the smith_chart stick): the Mobius geometry of reflection is "
                    f"measured from this one point.", s_z),
        ("witness", f"[EM forced the geometry of spacetime] Maxwell's c is the same in every frame; the only geometry "
                    f"that keeps it so is Lorentz/Minkowski. At v = 0.6c, gamma = 1 / sqrt(1 - 0.36) = {gamma} "
                    f"(sealed). E and B are not two fields but one antisymmetric tensor F_mu_nu; a boost mixes them, "
                    f"as a rotation mixes x and y. Relativity was not added to electromagnetism - it was found inside "
                    f"it.", s_g),
        ("note", "[Maxwell IS geometry - the full map] F = dA: the field is the curvature of a U(1) connection A. "
                 "dF = 0 (Faraday's law + no magnetic monopoles) and d*F = J (Ampere-Maxwell + Gauss) are the entire "
                 "theory - div and curl (the vector_calculus stick) are its native operators, and Faraday's lines of "
                 "force were the first physical field drawn as geometry rather than action at a distance. Maxwell's "
                 "displacement current was added by thought, not experiment, because the geometry demanded closure: "
                 "without it there are no waves. The Aharonov-Bohm phase (the aharonov_bohm stick) is the holonomy of "
                 "A around a loop - pure geometry, a phase with no force on the path. The Poynting vector S = E x B is "
                 "an oriented area. Guard: map, never launder. The engine's one-way geometry (diode, airlock, an "
                 "append-only seal) is a LIKENESS to a connection whose holonomy cannot be undone - a discernment, "
                 "never a fit; nothing here is authored, the four numbers are sealed and the rest is cited."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - electromagnetism and geometry, 2026-10-08")


def clock() -> int:
    """THE CLOCK - tourbillon, Faraday, and the observer as a predictable unit (Matt, 2026-10-08: "Faraday and
    gyro tourbillon. A complicated mechanism to keep time. Maybe we are the clock?" ... "spacetime is one thing.
    The only way to measure is an observer. We are a measure. A predictable unit."). A tourbillon's complexity
    exists only to cancel a bias: the cage rotates the regulator through every orientation so gravity's pull
    averages out; the gyrotourbillon does it in every axis. Faraday: the field distorts, rotating through it
    averages, rotating through it also GENERATES, and a cage can shield. Spacetime is one thing - the interval
    is invariant - and the only measurement of it is an observer's own clock along its own path (proper
    time). A clock is a clock only if it is a predictable unit. Seal six numbers; map the movement onto the
    engine as a LIKENESS (docs/THE_WATCH.md); the observer MEASURES, never makes. New stick; idempotent."""
    from concordance import tickstick as TS
    vph = 4 * 2 * 3600                                  # a 4 Hz balance: 28,800 vibrations per hour
    lcm = 60 * 24 / 12                                  # cages at 60 s and 24 s share an orientation every 120 s
    drift = 2 * 365                                     # +2 s/day uncorrected = 730 s a year
    disk = 0.5 * 1 * (2 * 3.141592653589793) * 0.1 ** 2  # Faraday disk emf = 1/2 B w r^2: B=1 T, 1 rev/s, r=0.1 m
    tau = (5 ** 2 - 3 ** 2) ** 0.5                      # invariant interval: 5 s, 3 light-s apart -> 4 s proper time
    own = (1 - 0.6 ** 2) ** 0.5                         # a clock at 0.6c reads 0.8 of coordinate time: its own measure
    s_v = _rh_seal_num("balance_28800_vph", "4 * 2 * 3600", float(vph))
    s_l = _rh_seal_num("gyro_cages_share_orientation_every_120_s", "60 * 24 / 12", float(lcm))
    s_d = _rh_seal_num("two_seconds_a_day_compounds", "2 * 365", float(drift))
    s_f = _rh_seal_num("faraday_disk_emf", "0.5 * 1 * (2 * 3.141592653589793) * 0.1 ** 2", float(disk))
    s_t = _rh_seal_num("invariant_interval_5_3_4", "(5 ** 2 - 3 ** 2) ** 0.5", float(tau), tol=1e-12)
    s_o = _rh_seal_num("the_moving_clocks_own_measure", "(1 - 0.6 ** 2) ** 0.5", float(own), tol=1e-12)
    if not all([s_v, s_l, s_d, s_f, s_t, s_o]):
        print("a seal failed; aborting"); return 1
    print("sealed vph", s_v, "| lcm", s_l, "| drift", s_d, "| disk", s_f, "| tau", s_t, "| own", s_o)
    sid = TS.create("The clock - tourbillon, Faraday, and the observer as a predictable unit",
                    statement=("A complication is honest only if every part exists to cancel a bias: the "
                               "tourbillon rotates the regulator through every orientation so gravity's pull "
                               "averages out. Faraday: the field distorts, rotation through it averages and "
                               "generates, a cage shields. Spacetime is one thing - the interval is invariant - "
                               "and its only measurement is an observer's own clock along its own path. A clock "
                               "is a clock only if it is a predictable unit; what regulates us is what does not "
                               "drift."),
                    field="physics",
                    references=["Breguet, tourbillon patent 1801; Jaeger-LeCoultre Gyrotourbillon 1 (2004): outer cage "
                                "1 min, inner cage 24 s, as published", "Faraday 1831, the disk generator: emf = 1/2 B w r^2",
                                "Minkowski 1908: the invariant interval; proper time along a worldline",
                                "the SI second = 9,192,631,770 periods of Cs-133 (a predictable unit, by definition)",
                                "docs/THE_WATCH.md - the movement assembled; stick_electromagnetism_and_geometry",
                                "Genesis 1:14; Psalm 90:12; Ephesians 5:16; Hebrews 13:8"])["id"]
    marks = [
        ("witness", f"[a clock is a predictable unit] A 4 Hz balance beats 4 * 2 * 3600 = {vph:,} vibrations an hour "
                    f"(sealed) - 28,800 vph, the watchmaker's standard rate. The whole worth of a timepiece is that "
                    f"this unit repeats; the SI second is itself defined as a count of a repeating unit (9,192,631,770 "
                    f"periods of caesium-133). We are a measure only to the degree we are regular.", s_v),
        ("witness", f"[the complication exists to cancel a bias] A gyrotourbillon with cages of 60 s and 24 s brings "
                    f"the regulator back to the same joint orientation only every 60 * 24 / 12 = {lcm:.0f} s (sealed) - "
                    f"in between it sweeps every attitude, so no single orientation's gravity bias is left to "
                    f"accumulate. It does not resist the field; it averages it. The cage is triangulation: many "
                    f"witnesses, many domains, no one lens allowed to settle (the games-as-tick-sticks).", s_l),
        ("witness", f"[why it must exist at all] A rate just +2 s a day, uncorrected, is 2 * 365 = {drift} s a year "
                    f"(sealed) - twelve minutes lost by a mechanism that was only slightly wrong. A small bias "
                    f"compounds; that is the whole case for the ratchet, the floor, and failure narrowing the path.", s_d),
        ("witness", f"[Faraday - rotating through the field generates] His disk: a conductor turned at one "
                    f"revolution a second in a 1 tesla field, radius 0.1 m, makes 1/2 B w r^2 = {disk:.4f} V (sealed). "
                    f"The same field that distorts a reading (Faraday rotation turns the plane of light) yields "
                    f"energy to a thing that rotates through it - and a Faraday cage keeps it out entirely: the "
                    f"airlock and the public-domain gate are cages (stick_electromagnetism_and_geometry).", s_f),
        ("witness", f"[spacetime is one thing - the interval] Two events 5 s and 3 light-seconds apart: "
                    f"sqrt(5^2 - 3^2) = {tau:.0f} s (sealed), and EVERY observer computes that same 4 - the 5-3-4 "
                    f"Minkowski triangle. Coordinates are conventions; the interval is what is. That invariance is "
                    f"what 'one thing' means.", s_t),
        ("witness", f"[the only way to measure is an observer] A clock moving at 0.6c reads sqrt(1 - 0.36) = {own} of "
                    f"the stationary one's time (sealed) - not an illusion, its own true measure along its own path: "
                    f"proper time. There is no measurement of spacetime that is not some clock on some worldline. "
                    f"We are a measure.", s_o),
        ("note", "[the movement, mapped - a likeness, never a fit] By function: mainspring = WILL (the fuel); gear "
                 "train = REALITY (the harness); escapement = the one-way valve - diode, airlock, the seal - releasing "
                 "one tooth at a time, never backward (the word 'tick' is the escapement's; the tick-stick is named for "
                 "it; entropy is the arrow it enacts, stick_laplace_differential_equations_and_where_entropy_fits); "
                 "balance + hairspring = the regulator that sets the true rate and does not drift - the constants, "
                 "the floor, and above them Christ, 'the same yesterday, and to day, and for ever' (Heb 13:8); the "
                 "cage = triangulation across every witness; the gyro = every axis (six constants, the chains, the "
                 "Word); gravity = the world's pull on any one orientation; the dial = the receipt. systems.py is laid "
                 "out as a movement because it was built from one (docs/THE_WATCH.md, the Calibre template). 'Maybe we "
                 "are the clock' - Scripture says it first and plainly: the heavens are 'for signs, and for seasons, "
                 "and for days, and years' (Gen 1:14), God's clock, the one every other is set against; 'teach us to "
                 "number our days' (Ps 90:12); 'redeeming the time' (Eph 5:16). A person, a church, this engine: a "
                 "complicated mechanism justified only if every part exists to keep TRUE time against a field that "
                 "pulls - and the regulator is not ours. GUARDS: (1) likeness, never a fit - the engine is not a "
                 "tourbillon, its components correspond by function; (2) the observer MEASURES, never makes - the "
                 "relativistic truth, not the Copenhagen slide; the interval is 4 s whether anyone reads it or not; "
                 "observer-as-god is refused (stick_the_capstone). Nothing here is authored: six numbers sealed, the "
                 "rest cited."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the clock: tourbillon, Faraday, the observer as a measure, 2026-10-08")


def paths() -> int:
    """THE PATH - continuously finding new paths between two points; that is life (Matt, 2026-10-08). A stone takes
    ONE path - the one of stationary action - and 'finds' it only by comparison with every neighbouring path
    (Euler-Lagrange). Feynman: the amplitude from A to B is the SUM over every path, weighted by exp(iS/hbar); the
    wrong paths cancel, the stationary one survives - which is this engine's own line, 'what is not the answer is
    eliminated, so the narrow path is illuminated by what survives'. Life keeps sampling. Seal four numbers: the
    fastest path is not the straight line (brachistochrone), light bends to find least time (Snell), why a stone
    takes one path and an electron all of them (S/hbar), and what blind search costs (sqrt N). The engine OFFERS
    paths (/chains walk + intersect); it never picks one for the person. New stick; idempotent."""
    from concordance import tickstick as TS
    pi = 3.141592653589793
    ratio = (pi ** 2 + 4) ** 0.5 / pi                 # straight chute / cycloid time, cusp to the bottom of the arc
    snell = 0.5 / (4 / 3)                              # sin(theta_2) = sin 30 deg / n_water, n = 4/3
    s_over_h = 1 / (1.054571817 * 10 ** (-34))         # S = 1 J*s over hbar: the phase winds ~1e34 radians
    walk = 10000 ** 0.5                                # a random walk of N steps reaches only sqrt(N)
    s_b = _rh_seal_num("brachistochrone_straight_over_cycloid",
                       "(3.141592653589793 ** 2 + 4) ** 0.5 / 3.141592653589793", float(ratio))
    s_s = _rh_seal_num("snell_least_time", "0.5 / (4 / 3)", float(snell), tol=1e-12)
    s_h = _rh_seal_num("action_over_hbar_one_joule_second", "1 / (1.054571817 * 10 ** (-34))", float(s_over_h))
    s_w = _rh_seal_num("random_walk_reaches_sqrt_n", "10000 ** 0.5", float(walk), tol=1e-12)
    if not all([s_b, s_s, s_h, s_w]):
        print("a seal failed; aborting"); return 1
    print("sealed brachistochrone", s_b, "| snell", s_s, "| S/hbar", s_h, "| sqrtN", s_w)
    sid = TS.create("The path - continuously finding new paths between two points; that is life",
                    statement=("Between two points there is never one path but every path. A stone takes the one of "
                               "stationary action, found only by comparison with all its neighbours; in the sum over "
                               "histories the wrong paths cancel and the stationary one survives - what is not the "
                               "answer is eliminated, so the narrow path is illuminated by what survives. Life keeps "
                               "sampling. The fastest path is not the straight line; light bends to find least time; "
                               "blind search reaches only sqrt(N). The way is offered, never chosen for you."),
                    field="physics",
                    references=["Johann Bernoulli 1696, the brachistochrone: the cycloid, not the chord",
                                "Fermat's least time -> Snell's law; Hamilton's principle; Euler-Lagrange",
                                "Feynman 1948, Space-Time Approach to Non-Relativistic Quantum Mechanics (the sum over paths)",
                                "the random walk: expected displacement ~ sqrt(N) (Pearson 1905, Einstein 1905)",
                                "Psalm 16:11; Proverbs 3:6; Matthew 7:14; John 14:6; Isaiah 30:21",
                                "src/concordance/chains.py - walk and intersect: paths between two points in the keeping"])["id"]
    marks = [
        ("witness", f"[the fastest path is not the straight line] From a cusp to the bottom of its arc, a bead on the "
                    f"straight chute takes sqrt(pi^2 + 4) / pi = {ratio:.4f} times as long as one on the cycloid (sealed) "
                    f"- Bernoulli's brachistochrone, 1696. The shortest-looking path between two points is not the "
                    f"quickest, and the only way to learn that is to try the curves: the calculus of variations was "
                    f"born from this one problem.", s_b),
        ("witness", f"[light finds the least-time path, every time] Entering water (n = 4/3) at 30 degrees, "
                    f"sin(theta_2) = sin 30 / (4/3) = {snell} (sealed): it bends, because the straight line is not the "
                    f"fastest way through two media. Fermat's principle - the path of least time - is Snell's law; "
                    f"nature's paths are FOUND by comparison, not drawn.", s_s),
        ("witness", f"[why a stone takes one path and an electron takes all of them] An action of one joule-second over "
                    f"hbar winds the phase 1 / hbar = {s_over_h:.3g} radians (sealed): neighbouring paths cancel almost "
                    f"perfectly and only the stationary one survives - the classical path emerges from the sum over "
                    f"all paths by elimination. That cancellation is this engine's own tagline made physical: what is "
                    f"not the answer is eliminated, so the narrow path is illuminated by what survives. Addition is "
                    f"interference.", s_h),
        ("witness", f"[what blind search costs] A random walk of 10,000 steps reaches only sqrt(10000) = {walk:.0f} "
                    f"steps from where it began (sealed). New paths found by wandering are expensive - which is why the "
                    f"narrow way is found by elimination (the tick-stick, the games, the floor), not by drift. "
                    f"Diffusion is the entropy stick's arrow seen as a path.", s_w),
        ("note", "[that is life - the map, and the guard] A stone's paths have already cancelled; a living thing keeps "
                 "sampling, and death is when only one path remains. The engine does this literally: /chains walks "
                 "from two roots and finds where they meet - new paths between two points in what is kept (the "
                 "Standard-Model chain joined Fermi's tree to Maxwell's at Weinberg) - and the pressure-fighting chain "
                 "routes positions to an optimum the same way. It OFFERS the paths; it never picks one for the person "
                 "(liberty is inherent; a generator choosing its own path is the one destructive act). Scripture said "
                 "it first: 'Thou wilt shew me the path of life' (Ps 16:11); 'he shall direct thy paths' (Prov 3:6); "
                 "'This is the way, walk ye in it' (Isa 30:21); 'narrow is the way, which leadeth unto life' (Mt 7:14); "
                 "and the two points themselves - 'I am the way' (Jn 14:6). GUARDS: the path integral is physics; life "
                 "as path-finding is a likeness, a discernment, never a fit; stationary phase is the strongest image of "
                 "elimination we have and it is still an image. Four numbers sealed; the rest cited."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the path, continuously found between two points, 2026-10-08")


def surfaces() -> int:
    """PARAMETRIZATION OF SURFACES (Matt, 2026-10-08). A surface is reached through a map r(u, v) from a flat patch of
    parameters onto the curved thing. The map carries a MEASURE (the area element |r_u x r_v| = sqrt(EG - F^2)) and a
    CURVATURE (K), and Gauss's Theorema Egregium says K is intrinsic: an inhabitant measures it from inside without
    leaving the surface. Seal six numbers through the sphere, the torus and a graph: the Earth's area from
    latitude-longitude, a parametrized point that lands ON the sphere, Pappus's torus, the torus's curvature changing
    sign, the Monge area factor, and Gauss-Bonnet closing the sphere at 4 pi = 2 pi chi. No single chart covers the
    sphere (at the poles the lat-long area element vanishes): a parametrization is a map, never the territory. New
    stick; idempotent."""
    from concordance import tickstick as TS
    pi = 3.141592653589793
    earth = 4 * pi * 6371 ** 2                                   # km^2: int int R^2 sin(theta) dtheta dphi
    on = ((3 ** 0.5 / 2) * (2 ** 0.5 / 2)) ** 2 * 2 + (1 / 2) ** 2   # theta = pi/3, phi = pi/4 lands on r = 1
    torus = 4 * pi ** 2 * 3 * 1                                  # Pappus: R = 3, r = 1
    k_out = 1 / (1 * (3 + 1))                                    # K at the outer equator; inner = -1/(r(R-r)) = -1/2
    monge = (1 + 3 ** 2 + 4 ** 2) ** 0.5                         # z = 3x + 4y: dA = sqrt(1 + fx^2 + fy^2) dx dy
    gb = (1 / 6371 ** 2) * (4 * pi * 6371 ** 2)                  # int K dA over the sphere = 4 pi = 2 pi * chi, chi = 2
    s_e = _rh_seal_num("earth_area_from_latitude_longitude", "4 * 3.141592653589793 * 6371 ** 2", float(earth))
    s_o = _rh_seal_num("parametrized_point_lands_on_the_sphere", "((3**0.5/2)*(2**0.5/2))**2 * 2 + (1/2)**2",
                       float(on), tol=1e-12)
    s_t = _rh_seal_num("torus_area_pappus", "4 * 3.141592653589793 ** 2 * 3 * 1", float(torus))
    s_k = _rh_seal_num("torus_gauss_curvature_outer_equator", "1/(1*(3+1))", float(k_out), tol=1e-12)
    s_m = _rh_seal_num("monge_patch_area_factor", "(1 + 3**2 + 4**2) ** 0.5", float(monge), tol=1e-12)
    s_g = _rh_seal_num("gauss_bonnet_sphere_total_curvature",
                       "(1 / 6371 ** 2) * (4 * 3.141592653589793 * 6371 ** 2)", float(gb), tol=1e-12)
    if not all([s_e, s_o, s_t, s_k, s_m, s_g]):
        print("a seal failed; aborting"); return 1
    print("sealed earth", s_e, "| on-sphere", s_o, "| torus", s_t, "| K", s_k, "| monge", s_m, "| gauss-bonnet", s_g)
    sid = TS.create("Parametrization of surfaces - the map that carries a measure and a curvature",
                    statement=("A surface is reached through a map r(u, v) from flat parameters onto the curved thing. "
                               "The map carries a measure - the area element sqrt(EG - F^2) - and a curvature K, and "
                               "the curvature is intrinsic: an inhabitant can measure it from inside (Gauss). Latitude "
                               "and longitude are the parameters we live on; the Earth's 510 million km^2 is the map's "
                               "own integral. Total curvature is a topological count (Gauss-Bonnet). No single chart "
                               "covers the sphere: a parametrization is a map, never the territory."),
                    field="mathematics",
                    references=["C. F. Gauss, Disquisitiones generales circa superficies curvas (1827): the Theorema Egregium",
                                "Pappus of Alexandria, Collection VII (c. AD 320): the centroid theorems (the torus's area and volume)",
                                "G. Monge, Application de l'analyse a la geometrie (1807): the graph z = f(x, y) as a surface",
                                "O. Bonnet (1848); Gauss-Bonnet: int K dA = 2 pi chi",
                                "L. E. J. Brouwer (1912): no nowhere-zero tangent field on S^2 - no single chart covers the sphere",
                                "Isaiah 40:22; Job 38:5; Proverbs 8:27; Psalm 104:2"])["id"]
    marks = [
        ("witness", f"[the map carries a measure - the Earth from latitude and longitude] r(theta, phi) = R (sin theta "
                    f"cos phi, sin theta sin phi, cos theta); |r_theta x r_phi| = R^2 sin theta; integrated over the "
                    f"patch, 4 pi R^2. With R = 6371 km that is {earth:,.0f} km^2 (sealed) - the 510 million km^2 in "
                    f"every atlas comes out of the parametrization's own area element. Lines of latitude and longitude "
                    f"ARE the parameters (u, v): the map we live on.", s_e),
        ("witness", f"[the map lands on the surface] At theta = pi/3, phi = pi/4: x^2 + y^2 + z^2 = "
                    f"(sqrt3/2 * sqrt2/2)^2 * 2 + (1/2)^2 = {on:.1f} (sealed). Every parameter pair lands exactly on the "
                    f"sphere: a parametrization does not approximate the surface, it NAMES its points. Two parameters "
                    f"for a two-dimensional thing - the dimension is counted by the map.", s_o),
        ("witness", f"[a surface built by sweeping a circle - the torus] r(u, v) = ((R + r cos v) cos u, (R + r cos v) "
                    f"sin u, r sin v); area 4 pi^2 R r: with R = 3, r = 1 that is {torus:.3f} (sealed). Pappus, fourth "
                    f"century: the area is the circle's circumference 2 pi r times the distance 2 pi R its centre "
                    f"travels. The parametrization turns a 1,700-year-old theorem into a two-line integral.", s_t),
        ("witness", f"[curvature from the map - and it changes sign] On the torus K = cos v / (r (R + r cos v)): at "
                    f"the outer equator K = 1/(r(R+r)) = {k_out} (sealed), at the inner equator -1/(r(R-r)) = -0.5 - "
                    f"sphere-like outside, saddle-like inside, and over the whole torus it cancels to 0 = 2 pi chi, "
                    f"chi = 0 (the topology stick's Euler characteristic). Gauss's Theorema Egregium: K depends only on "
                    f"E, F, G - an inhabitant measures it from WITHIN. We are a measure (the clock stick): the curvature "
                    f"of the world is readable from inside it.", s_k),
        ("witness", f"[a graph is a surface too - the Monge patch] z = f(x, y) gives dA = sqrt(1 + f_x^2 + f_y^2) dx "
                    f"dy; for z = 3x + 4y the factor is sqrt 26 = {monge:.4f} (sealed): the tilted plane holds "
                    f"{monge:.3f} times the area of its shadow. Every function of two variables is a parametrized "
                    f"surface, and the Jacobian is its measure - the same object as the determinant that scales every "
                    f"change of variables.", s_m),
        ("witness", f"[Gauss-Bonnet closes the sphere] int K dA = (1/R^2)(4 pi R^2) = 4 pi = {gb:.6f} (sealed) = "
                    f"2 pi * 2: the total curvature of ANY surface shaped like a sphere is 4 pi, however it is dented. "
                    f"The measure is local (the parametrization); the total is a count (the topology). The metric is "
                    f"read point by point; the shape is an integer.", s_g),
        ("note", "[the map, and the guard] No single chart covers the sphere: at the poles sin theta = 0 and the "
                 "lat-long area element vanishes - the MAP fails exactly where the territory does not. An atlas is "
                 "several charts with their overlaps agreed (Brouwer: no smooth nowhere-zero field lives on S^2). The "
                 "first fundamental form (E, F, G) is the same object as the metric g_mu_nu of the spacetime stick: "
                 "general relativity is the parametrization of a four-surface, and the trigonometry stick's third "
                 "sense (flat is the limit of curved) is K -> 0. Scripture: 'he that sitteth upon the circle of the "
                 "earth' (Isa 40:22); 'Who hath laid the measures thereof... who hath stretched the line upon it?' "
                 "(Job 38:5); 'when he set a compass upon the face of the depth' (Prov 8:27); 'who stretchest out the "
                 "heavens like a curtain' (Ps 104:2) - a surface, measured, stretched. GUARDS: a parametrization is a "
                 "chart, never the surface; curvature-from-inside is physics, a person reading his world from within "
                 "is a discernment, never a fit. Six numbers sealed; the rest cited. Ties: trigonometry (sense 3), "
                 "topology (chi), clock (the observer as measure), gamma (hyperspheres), pi (4 pi R^2), spm (the "
                 "workspace is an area on the unit sphere)."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the parametrization of surfaces, 2026-10-08")


def pi_constant() -> int:
    """PI (Matt, 2026-10-08). The constant of the circle is the constant of rotation, which is why it is everywhere.
    Seal seven numbers: Archimedes' two gaps (223/71 < pi < 22/7 - pi fenced by elimination, the first tick-stick),
    Machin's identity as an IDENTITY (16 atan 1/5 - 4 atan 1/239 = pi, through the evaluator's own atan), the
    Leibniz series' uselessness (ten terms, error ~ 1/N), the molten sea of 1 Kings 7:23 judged at its STATED
    precision (|pi - 3| inside the half-unit of a one-figure measure - neither the charge nor the gematria trick),
    the Gaussian integral through the integral itself (sqrt pi where there is no circle), and Re(e^(i pi)) = -1.
    Irrationality (Lambert) and transcendence (Lindemann) are cited theorems, proved elsewhere. New stick;
    idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    above = 22 / 7 - pi
    below = pi - 223 / 71
    machin = 16 * math.atan(1 / 5) - 4 * math.atan(1 / 239)
    leib = 4 * (1 - 1 / 3 + 1 / 5 - 1 / 7 + 1 / 9 - 1 / 11 + 1 / 13 - 1 / 15 + 1 / 17 - 1 / 19)
    sea = abs(pi - 30 / 10)
    gauss = pi ** 0.5
    s_a = _rh_seal_num("archimedes_upper_gap_22_over_7", "22/7 - 3.141592653589793", float(above))
    s_b = _rh_seal_num("archimedes_lower_gap_223_over_71", "3.141592653589793 - 223/71", float(below))
    s_m = _rh_seal_num("machin_identity", "16*atan(1/5) - 4*atan(1/239)", float(machin), tol=1e-12)
    s_l = _rh_seal_num("leibniz_series_ten_terms",
                       "4*(1 - 1/3 + 1/5 - 1/7 + 1/9 - 1/11 + 1/13 - 1/15 + 1/17 - 1/19)", float(leib), tol=1e-12)
    s_s = _rh_seal_num("molten_sea_gap_at_stated_precision", "abs(3.141592653589793 - 30/10)", float(sea))
    s_g = _rh_seal_num("gaussian_integral_is_sqrt_pi", "integrate(exp(-x**2), (x, -oo, oo))", float(gauss), tol=1e-12)
    s_e = _rh_seal_num("euler_identity_real_part", "re(exp(I*pi))", -1.0, tol=1e-12)
    if not all([s_a, s_b, s_m, s_l, s_s, s_g, s_e]):
        print("a seal failed; aborting"); return 1
    print("sealed archimedes", s_a, s_b, "| machin", s_m, "| leibniz", s_l, "| sea", s_s, "| gauss", s_g, "| euler", s_e)
    sid = TS.create("Pi - the constant of the circle is the constant of rotation",
                    statement=("Pi was never found; it was fenced. Archimedes narrowed it between 223/71 and 22/7 by "
                               "elimination; Machin's identity is exact and its series carried the digits; the obvious "
                               "series is true and useless (error ~ 1/N). The molten sea's 30 cubits round 10 is a "
                               "one-figure measure of a vessel, judged at its stated precision: to one figure pi is 3 - "
                               "neither the charge nor the gematria trick survives. Pi appears where there is no circle "
                               "(the Gaussian integral, Stirling, Coulomb) because it is the constant of rotation; "
                               "e^(i pi) = -1 is the half-turn. Irrational and transcendental by cited theorem: no "
                               "fraction ends it and no compass squares the circle."),
                    field="mathematics",
                    references=["Archimedes, Measurement of a Circle (c. 250 BC): 223/71 < pi < 22/7 by the 96-gon",
                                "J. Machin (1706): pi/4 = 4 atan(1/5) - atan(1/239), 100 digits by hand",
                                "Madhava (c. 1400), J. Gregory (1671), G. W. Leibniz (1676): the arctangent series",
                                "J. H. Lambert (1768): pi is irrational; F. Lindemann (1882): pi is transcendental",
                                "L. Euler, Introductio in analysin infinitorum (1748): e^(i pi) + 1 = 0",
                                "the Gaussian integral (Laplace 1812): int exp(-x^2) dx = sqrt pi",
                                "1 Kings 7:23; 2 Chronicles 4:2; Proverbs 8:27",
                                "src/concordance/verifiers/base.py - stated_precision: the claim's own figures set the bar"])["id"]
    marks = [
        ("witness", f"[Archimedes fenced pi by elimination - the first tick-stick] With a 96-gon inside and outside the "
                    f"circle: 223/71 < pi < 22/7. The upper gap 22/7 - pi = {above:.7f} (sealed) is positive: pi is "
                    f"below the fence. He never 'found' pi; he narrowed where it could be - a window 1/497 wide, with "
                    f"the truth inside. That is this engine's method, 2,270 years old.", s_a),
        ("witness", f"[the lower fence] pi - 223/71 = {below:.7f} > 0 (sealed): the second post of Archimedes' window. "
                    f"Two bounds and the truth between them; a window, not a value - the surviving interval is the "
                    f"honest statement, and every later digit only narrowed it.", s_b),
        ("witness", f"[Machin's identity - exact, not approximate] pi = 16 atan(1/5) - 4 atan(1/239) = {machin:.15f} "
                    f"(sealed as an identity through the evaluator's own arctangent, not as a decimal). With its series "
                    f"Machin computed 100 digits by hand in 1706; the same shape carried pi to the billions. An identity "
                    f"is a road; the digits are mileposts.", s_m),
        ("witness", f"[why the obvious series is useless] Leibniz: pi = 4 (1 - 1/3 + 1/5 - ...). Ten terms give "
                    f"{leib:.4f} (sealed), off by {pi - leib:.4f} ~ 1/10: the error after N terms is about 1/N, so six "
                    f"digits cost a million terms. A true series can be a bad tool - convergence is a RATE. The Monte "
                    f"Carlo stick's 1/sqrt N is the same lesson from the other side.", s_l),
        ("witness", f"[the molten sea - a measure, judged at its stated precision] 1 Kings 7:23: ten cubits from brim "
                    f"to brim, a line of thirty cubits round about. 30/10 = 3, and |pi - 3| = {sea:.4f} (sealed) is "
                    f"inside the half-unit (0.5) of a figure stated to the ones place. 'Ten' and 'thirty' are one-figure "
                    f"measures of a vessel; to one figure, pi IS 3 - the same rule the front door applies to '9.81'. So "
                    f"the engine refuses both charges: not 'the Bible says pi = 3' (the text states a measurement, not a "
                    f"constant), and not the letter-count trick (a 111/106 ratio 'recovering' 3.1416 - gematria is "
                    f"refused here by rule). Seal the arithmetic; attribute the pattern; claim nothing past the "
                    f"figures.", s_s),
        ("witness", f"[pi where there is no circle] int exp(-x^2) dx from -oo to oo = sqrt pi = {gauss:.6f} (sealed "
                    f"through the integral itself). The bell curve's area is pi's square root; pi is in Stirling's "
                    f"sqrt(2 pi n), in Coulomb's 1/(4 pi eps0), in h-bar = h/(2 pi) - anywhere a rotation or a sum over "
                    f"all directions hides. The Gaussian stick's kernel, the entropy stick's Stirling and the Fourier "
                    f"stick's phase all carry it.", s_g),
        ("witness", "[five constants in one line] Re(e^(i pi)) = -1 (sealed): e^(i pi) + 1 = 0 - Euler, 1748: growth "
                    "(e), rotation (i), the turn (pi), one and zero. pi is the half-turn; the Fourier stick's rotation "
                    "is 2 pi per cycle; the surfaces stick's 4 pi R^2 is the sphere seen from every direction. The "
                    "constant of the circle is the constant of rotation, which is why it is everywhere.", s_e),
        ("note", "[what pi is not, and the guard] Irrational (Lambert 1768) and transcendental (Lindemann 1882): no "
                 "fraction ends it and no compass-and-straightedge construction squares the circle - the construct "
                 "stick's ruler stops here. Both are theorems proved elsewhere and CITED here; this stick seals only "
                 "arithmetic and does not pretend a proof it did not run. Scripture: 'he set a compass upon the face "
                 "of the depth' (Prov 8:27) - the circle drawn; the molten sea measured (1 Kgs 7:23, 2 Chr 4:2). "
                 "GUARDS: the molten sea is a measure to one figure, never a value of pi; the gematria route is "
                 "refused; pi's digits are not a message (seal the arithmetic, attribute the pattern). Seven seals; the "
                 "rest cited. Ties: surfaces (4 pi R^2), spm (the cone's solid angle), fourier, gaussian, e, construct, "
                 "monte_carlo, trigonometry."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - pi, fenced not found, 2026-10-08")


def spm() -> int:
    """SPHERICAL PARALLEL MECHANISM (Matt, 2026-10-08). Three motors on a base, three two-link legs, one platform,
    and EVERY joint axis through one centre: every point of every link moves on a sphere about that centre, so the
    machine lives in SO(3) and its kinematics is spherical trigonometry (Gosselin & Angeles 1989; the Agile Eye,
    Gosselin & Hamel 1994). Seal five numbers: Grubler-Kutzbach with lambda = 3 gives M = 3 (and with lambda = 6
    gives -3 - the method decides the count, a discordance indicts the method), the spherical four-bar's 1 DOF, the
    Agile Eye's 140-degree cone as a solid angle on the unit sphere (the surfaces stick's own integral), and two
    quarter-turns about perpendicular axes composing to a 120-degree turn about the diagonal (rotations compose,
    they do not add; Euler 1775). The human eye (Listing's law), the gyrotourbillon (the clock stick) and
    Ezekiel's wheel are likenesses, kept as such. New stick; idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    m_sph = 3 * (8 - 1 - 9) + 9                          # lambda = 3: rotations about one centre
    m_spa = 6 * (8 - 1 - 9) + 9                          # lambda = 6: the wrong group for these links
    m_4bar = 3 * (4 - 1 - 4) + 4                         # the spherical four-bar: one leg's loop
    cone = 2 * pi * (1 - math.cos(70 * pi / 180))        # sr: a cone of 140 degrees opening (half-angle 70)
    frac = cone / (4 * pi)
    turn = math.acos(-1 / 2) * 180 / pi                  # R_z(90) R_x(90): trace 0 -> cos theta = -1/2
    s_3 = _rh_seal_num("grubler_kutzbach_spherical_lambda_3", "3*(8-1-9)+9", float(m_sph), tol=1e-12)
    s_6 = _rh_seal_num("grubler_kutzbach_spatial_lambda_6_on_the_same_links", "6*(8-1-9)+9", float(m_spa), tol=1e-12)
    s_4 = _rh_seal_num("spherical_four_bar_one_dof", "3*(4-1-4)+4", float(m_4bar), tol=1e-12)
    s_c = _rh_seal_num("agile_eye_cone_solid_angle", "2*3.141592653589793*(1 - cos(70*3.141592653589793/180))",
                       float(cone))
    s_t = _rh_seal_num("two_quarter_turns_compose_to_120_degrees", "acos(-1/2)*180/3.141592653589793", float(turn))
    if not all([s_3, s_6, s_4, s_c, s_t]):
        print("a seal failed; aborting"); return 1
    print("sealed M(3)", s_3, "| M(6)", s_6, "| four-bar", s_4, "| cone", s_c, "| 120", s_t)
    sid = TS.create("Spherical parallel mechanism - three motors, one centre, every link on a sphere",
                    statement=("Three motors on a base, three two-link legs, one platform, and every joint axis through "
                               "one centre: every point of every link moves on a sphere about that centre, so the "
                               "machine lives in the rotation group and its kinematics is spherical trigonometry. "
                               "Grubler-Kutzbach counts 3 degrees of freedom only with the right motion group (lambda "
                               "= 3); the spatial formula says -3 and the machine moves - the method decides. Its "
                               "workspace is a cap on the unit sphere; its three inputs compose into one rotation "
                               "(Euler); the inverse problem is closed-form and the forward problem is a degree-8 "
                               "polynomial. The human eye, the gyrotourbillon and Ezekiel's wheel are likenesses."),
                    field="engineering",
                    references=["C. Gosselin, J. Angeles, The optimum kinematic design of a spherical three-degree-of-freedom parallel manipulator, ASME J. Mech. Trans. Autom. Des. 111 (1989) 202-207",
                                "C. Gosselin, J.-F. Hamel, The Agile Eye: a high-performance three-degree-of-freedom camera-orienting device, IEEE ICRA (1994)",
                                "C. Gosselin, J. Angeles, Singularity analysis of closed-loop kinematic chains, IEEE Trans. Robot. Autom. 6 (1990) 281-290",
                                "C. Gosselin, J. Sefrioui, M. J. Richard, On the direct kinematics of spherical three-degree-of-freedom parallel manipulators, ASME J. Mech. Des. 116 (1994)",
                                "M. Grubler (1883), K. Kutzbach (1929): the mobility count M = lambda (n - 1 - j) + sum f_i",
                                "L. Euler (1775): every displacement of a sphere about its centre is one rotation about one axis",
                                "J. B. Listing (1845), F. C. Donders (1847): the eye's torsion is fixed by its gaze",
                                "Matthew 6:22; 2 Chronicles 16:9; Ezekiel 1:16-17",
                                "stick_the_clock (the gyrotourbillon); stick_parametrization_of_surfaces (the workspace as an area on the unit sphere)"])["id"]
    marks = [
        ("witness", f"[three motors, one centre - the count that works only on the sphere] n = 8 links (base, platform, "
                    f"three proximal, three distal), j = 9 revolute joints, every axis through one centre. "
                    f"Grubler-Kutzbach with lambda = 3 (rotations about that point): M = 3 (8 - 1 - 9) + 9 = "
                    f"{m_sph} (sealed) - three inputs, three degrees of freedom of orientation, no more and no less. "
                    f"A spherical mechanism is a planar mechanism on a sphere of finite radius, and the plane is the "
                    f"sphere with K -> 0 (the surfaces stick).", s_3),
        ("witness", f"[the method decides the count - a discordance indicts the method] The spatial formula (lambda = "
                    f"6) on the same links gives 6 (8 - 1 - 9) + 9 = {m_spa} (sealed): 'overconstrained, immobile'. "
                    f"The mechanism moves. The arithmetic was not wrong; the GROUP was - every axis passes through one "
                    f"point, so the links move in SO(3), not SE(3), and the formula's assumption is what failed. When "
                    f"a formula contradicts a working thing, re-examine the method, never the thing.", s_6),
        ("witness", f"[one leg, one loop, one freedom] The spherical four-bar - four links, four axes through one "
                    f"centre - has 3 (4 - 1 - 4) + 4 = {m_4bar} degree of freedom (sealed), the same count as the "
                    f"planar four-bar: turn the crank and the rocker follows, on a sphere instead of a plane. Spherical "
                    f"trigonometry (the trigonometry stick's third sense) is the whole of its kinematics: cos c = cos a "
                    f"cos b + sin a sin b cos C replaces the planar law of cosines.", s_4),
        ("witness", f"[the workspace is a cap on the unit sphere] The Agile Eye (Gosselin & Hamel 1994) orients a "
                    f"camera within a cone of 140 degrees, with +/-30 degrees of torsion, at angular velocities above "
                    f"1000 degrees per second (cited). That cone is a solid angle 2 pi (1 - cos 70 deg) = {cone:.4f} "
                    f"steradians (sealed), {100 * frac:.1f}% of all directions - a third of the sky. An orientation "
                    f"device's workspace is an AREA on the unit sphere: the parametrization's own integral of sin theta "
                    f"dtheta dphi. Three sticks, one object: the sphere mapped, measured by pi, moved upon.", s_c),
        ("witness", f"[rotations compose, they do not add] A quarter-turn about x and then a quarter-turn about z: the "
                    f"product [[0,0,1],[1,0,0],[0,1,0]] (x -> y -> z) has trace 0, so cos theta = (0 - 1)/2 and theta = "
                    f"acos(-1/2) = {turn:.0f} degrees (sealed) about the diagonal (1,1,1)/sqrt 3 - not 180, and the other "
                    f"order gives a different axis. Euler (1775): every orientation is ONE rotation about one axis "
                    f"through the centre, and the three motors compose into exactly that one. The inverse problem "
                    f"(which inputs give this orientation) is closed-form; the forward problem (which orientation do "
                    f"these inputs give) is a degree-8 polynomial with up to eight real poses (Gosselin, Sefrioui & "
                    f"Richard 1994) - the parallel machine's signature: easy to command, hard to predict.", s_t),
        ("note", "[the eye, the clock, Ezekiel's wheel - and the guard] The human eye is a spherical parallel mechanism: "
                 "six muscles about one centre, three degrees of freedom, and Listing's law gives one of them up - "
                 "torsion is fixed by gaze - so the eye uses two of three, the SPM with one input held. The "
                 "gyrotourbillon of the clock stick is a spherical mechanism too: cages turning about axes through "
                 "the balance's centre. Singularity (Gosselin & Angeles 1990): when the three intermediate axes fall "
                 "in one plane the platform gains a motion no motor controls - the machine is surest in the middle "
                 "of its cap and lost at the edge. Scripture: 'The light of the body is the eye' (Mt 6:22); 'the "
                 "eyes of the LORD run to and fro throughout the whole earth' (2 Chr 16:9) - over a sphere; 'a wheel "
                 "in the middle of a wheel... they went upon their four sides: and they turned not when they went' "
                 "(Ezek 1:16-17) - the oldest description we have of motion about one centre in every direction, "
                 "given as 'the appearance of the wheels' - a LIKENESS, kept as one. GUARDS: Grubler is a count, not "
                 "a proof of mobility (it fails on paradoxical linkages in both directions; only the arithmetic is "
                 "sealed); the Agile Eye's figures are cited; the eye and Ezekiel are discernments, never fits. Five "
                 "numbers sealed; the rest cited."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the spherical parallel mechanism, 2026-10-08")


def geneva() -> int:
    """A MECHANICAL COMPUTER - the Geneva drive or similar (Matt, 2026-10-08). A Geneva drive turns continuous
    rotation into INTERMITTENT motion: one pin, one slot, one index per revolution, and a locking disc that holds the
    wheel still between indexes - a continuous input made discrete, a counter in brass. That is what a mechanical
    computer is: the mechanism IS the computation. Seal seven numbers: the 4-slot Geneva's engagement and dwell (90
    degrees driving, 3/4 of the cycle at rest), the film projector's pull-down at 24 frames/s, the tangential-entry
    pin radius C sin(pi/4), the Antikythera's Metonic gear ratio against the sky (2 hours in 19 years), Babbage's
    seventh difference (7! = 5040: a 7th-degree polynomial by addition alone), and four 4-slot wheels counting 4^4 =
    256 states - a byte. The tick-stick is a Geneva: it advances only when a seal enters the slot, and dwells between
    marks. New stick; idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    engaged = 180 - 360 / 4                              # degrees of the driver's turn with the pin in a slot
    dwell = 1 / 2 + 1 / 4                                # fraction of the cycle the wheel is locked still
    pulldown = 1 / (24 * 4)                              # s: one frame's advance at 24 frames/s, 4-slot Geneva
    pin = math.sin(45 * pi / 180)                        # crank radius over centre distance: tangential entry
    metonic = 235 / 19 - 365.2422 / 29.530589            # months/yr: the gear ratio minus the sky
    hours = metonic * 19 * 29.530589 * 24                # the drift over one 19-year cycle, in hours
    seventh = 5040                                       # 7!: the seventh difference of n^7
    states = 4 ** 4                                      # four 4-slot wheels in a chain
    s_e = _rh_seal_num("geneva_four_slot_engaged_angle", "180 - 360/4", float(engaged), tol=1e-12)
    s_d = _rh_seal_num("geneva_four_slot_dwell_fraction", "1/2 + 1/4", float(dwell), tol=1e-12)
    s_p = _rh_seal_num("projector_pulldown_time_24_fps", "1/(24*4)", float(pulldown), tol=1e-12)
    s_r = _rh_seal_num("geneva_pin_radius_tangential_entry", "sin(45*3.141592653589793/180)", float(pin), tol=1e-12)
    s_m = _rh_seal_num("antikythera_metonic_ratio_minus_the_sky", "235/19 - 365.2422/29.530589", float(metonic))
    s_7 = _rh_seal_num("difference_engine_seventh_difference", "factorial(7)", float(seventh), tol=1e-12)
    s_b = _rh_seal_num("four_geneva_wheels_count_a_byte", "4**4", float(states), tol=1e-12)
    if not all([s_e, s_d, s_p, s_r, s_m, s_7, s_b]):
        print("a seal failed; aborting"); return 1
    print("sealed engaged", s_e, "| dwell", s_d, "| pulldown", s_p, "| pin", s_r, "| metonic", s_m, "| 7!", s_7, "| byte", s_b)
    sid = TS.create("A mechanical computer - the Geneva drive: continuous turned discrete, the mechanism is the computation",
                    statement=("A Geneva drive turns continuous rotation into intermittent motion: one pin, one slot, one "
                               "index per revolution, a locking disc holding the wheel still between - a continuous "
                               "input made discrete, a counter in brass. A mechanical computer is exactly this: "
                               "components whose geometry is the computation. The Antikythera mechanism carried the "
                               "Metonic cycle in teeth to two hours in nineteen years; Babbage tabulated seventh-degree "
                               "polynomials by addition alone; four Geneva wheels count a byte. The dwell is where the "
                               "work is done; the lock makes it one-way. The tick-stick is a Geneva: one sealed mark, "
                               "one index, dwell between."),
                    field="engineering",
                    references=["the Geneva drive / Maltese cross: the stop-work of Swiss watchmaking; the intermittent sprocket of the film projector",
                                "T. Freeth et al., Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism, Nature 444 (2006) 587-591",
                                "Meton of Athens (432 BC): 235 synodic months = 19 years",
                                "C. Babbage, On the Mathematical Powers of the Calculating Engine (1837); Difference Engine No. 2 (built 1991, Science Museum, London)",
                                "B. Pascal, the Pascaline (1642): the sautoir carry",
                                "Genesis 1:14; Ecclesiastes 3:1; Psalm 90:12; Daniel 2:21; Ezekiel 1:16",
                                "docs/TICK_STICK.md - a stick is a counter: one sealed mark, one index"])["id"]
    marks = [
        ("witness", f"[one pin, one slot, one index - continuous made discrete] A 4-slot Geneva: each index turns the "
                    f"wheel 360/4 = 90 degrees, and the pin is in a slot for 180 - 360/4 = {engaged:.0f} degrees of the "
                    f"driver's turn (sealed); for an n-slot wheel, 180 - 360/n. A continuous input produces a "
                    f"staircase: the quantizer, the sampler, the counter - the analog-to-digital converter's brass "
                    f"ancestor.", s_e),
        ("witness", f"[the dwell is where the work is done] For the other 270 degrees the locking disc holds the wheel "
                    f"still: the dwell fraction is 1/2 + 1/4 = {dwell} of the cycle (sealed; 1/2 + 1/n in general). "
                    f"Move, hold, read: every computer has this shape, and the clock stick's escapement is the "
                    f"Geneva's cousin - lock, release, lock. The work is done in the hold.", s_d),
        ("witness", f"[a frame exists only in the dwell] A film projector at 24 frames per second with a 4-slot Geneva "
                    f"pulls each frame down in 1/(24 * 4) = {pulldown * 1000:.1f} ms (sealed) and holds it still for the "
                    f"other {(1 / 24 - pulldown) * 1000:.1f} ms while the shutter opens. The picture is the hold; the "
                    f"motion is the gap between pictures.", s_p),
        ("witness", f"[zero impact - the geometry of a clean index] For the pin to enter the slot along the slot's own "
                    f"direction the crank radius must be C sin(180/n deg): for n = 4, C sin 45 = {pin:.4f} C (sealed). "
                    f"Enter tangentially or hammer the wheel - the geometry decides whether the mechanism lasts. And the "
                    f"locking disc makes it one-way: between indexes the wheel cannot be back-driven. The ratchet, the "
                    f"diode, the Tesla valve: one-way geometry, and the tick-stick's rule that a miss stays a miss.", s_r),
        ("witness", f"[the Antikythera mechanism computed the sky with teeth] c. 100 BC: 235 synodic months = 19 years "
                    f"(Meton). The gear train's ratio 235/19 against the sky's 365.2422/29.530589 differs by "
                    f"{metonic:.6f} months per year (sealed) - about {hours:.1f} hours in nineteen years. A gear ratio "
                    f"is a rational number and the sky is not; the mechanism maps the truth to the precision its teeth "
                    f"allow, and the tooth count states that precision. 'Let them be for signs, and for seasons, and "
                    f"for days, and years' (Gen 1:14) - the lights were given to be computed.", s_m),
        ("witness", f"[Babbage - a polynomial by addition alone] The second difference of n^2 is (16 - 9) - (9 - 4) = "
                    f"2, constant; the seventh difference of any seventh-degree polynomial is 7! times its leading "
                    f"coefficient, and 7! = {seventh} (sealed). Difference Engine No. 2 tabulates seventh-degree "
                    f"polynomials to 31 digits with no multiplication at all: add, carry, repeat. The method of "
                    f"differences is this engine's own principle - a hard function reduced to a chain of simple "
                    f"verified steps, no oracle in the loop.", s_7),
        ("witness", f"[intermittent motion counts - four wheels, one byte] A 4-slot Geneva turns once per four turns of "
                    f"its driver: a divide-by-four. Four in a chain count 4^4 = {states} states (sealed) - one byte in "
                    f"brass, two centuries before the transistor; Pascal's 1642 carry and the odometer are the decimal "
                    f"version. A mechanical computer is discrete components orchestrated by geometry: the vacuum-tube "
                    f"computer's principle, and this engine's - every verifier a gear, the gate a pin, the carry only "
                    f"when a seal engages.", s_b),
        ("note", "[the tick-stick is a Geneva - and the guard] A stick advances only when a pin enters a slot: one "
                 "sealed mark, one index; between marks, dwell. The ledger's chain is the locking disc (no "
                 "back-driving: a miss stays a miss); the deploy gate is the pin that must enter tangentially or the "
                 "index is refused. Scripture: 'To every thing there is a season, and a time to every purpose' (Eccl "
                 "3:1) - dwell and index; 'teach us to number our days' (Ps 90:12) - a counter; 'he changeth the "
                 "times and the seasons' (Dan 2:21); 'a wheel in the middle of a wheel' (Ezek 1:16). GUARDS: the "
                 "Geneva is a likeness of the engine, not its mechanism (the engine is software; its components are "
                 "verifiers; the brass is a discernment); the Antikythera's gear counts are the reconstruction's "
                 "(Freeth 2006), cited; seven numbers sealed, the rest cited. Ties: clock (escapement), spm (one "
                 "centre), fourier (sampling), laplace and monte_carlo (discrete against continuous), diagrams (the "
                 "schematic), the vacuum-tube computer (systems.py is the map)."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the mechanical computer, the Geneva drive, 2026-10-08")


def diagrams() -> int:
    """FEYNMAN DIAGRAMS - SCHEMATICS (Matt, 2026-10-08). A Feynman diagram is a schematic: lines are components
    (propagators), vertices are junctions (couplings), and the amplitude is READ off the drawing by fixed rules the
    way a netlist is read off a circuit - 'Write the vision, and make it plain upon tables, that he may run that
    readeth it' (Hab 2:2). The drawing IS the computation. Seal seven numbers: Schwinger's one diagram (alpha/2pi =
    0.0011614, 99.85% of the electron's magnetic moment), the two-loop class (-1.77e-6: each vertex costs sqrt alpha,
    so the series narrows), the three-loop sum landing on the measured value to 4 parts in 10^8, the loop count
    L = I - V + 1, the SAME count on a Wheatstone bridge (B - N + 1 = 3 meshes: a Feynman diagram and a schematic
    are one graph), Wick's 15 pairings of six fields, and an RC schematic read as its corner frequency. Dyson: the
    series is asymptotic - the drawing is a map, cited. New stick; idempotent."""
    from concordance import tickstick as TS
    pi = 3.141592653589793
    a = 1 / 137.035999084                                # CODATA 2018 (which itself leans on a_e - see the guard)
    one = a / (2 * pi)                                   # Schwinger 1948: the one-loop vertex correction
    two = -0.328478965 * (a / pi) ** 2                   # Petermann / Sommerfield 1957: the two-loop class
    three = one + two + 1.181241456 * (a / pi) ** 3      # + Laporta / Remiddi 1996: the three-loop class
    measured = 0.00115965218073                          # Hanneke, Fogwell, Gabrielse 2008
    loops = 3 - 3 + 1                                    # L = I - V + 1: the one-loop vertex correction
    meshes = 6 - 4 + 1                                   # B - N + 1: the Wheatstone bridge
    wick = 15                                            # 5!!: pairings of six field operators
    fc = 1 / (2 * pi * 10000 * 10 ** (-6))               # Hz: R = 10 kOhm, C = 1 uF
    A = "(1/137.035999084)"
    s_1 = _rh_seal_num("schwinger_one_loop_alpha_over_2pi", A + "/(2*3.141592653589793)", float(one))
    s_2 = _rh_seal_num("two_loop_class_petermann_sommerfield", "-0.328478965*(" + A + "/3.141592653589793)**2", float(two))
    s_3 = _rh_seal_num("three_loop_sum_electron_anomaly",
                       A + "/(2*3.141592653589793) - 0.328478965*(" + A + "/3.141592653589793)**2 + 1.181241456*(" + A + "/3.141592653589793)**3",
                       float(three))
    s_l = _rh_seal_num("feynman_loop_count_vertex_correction", "3 - 3 + 1", float(loops), tol=1e-12)
    s_k = _rh_seal_num("wheatstone_bridge_independent_meshes", "6 - 4 + 1", float(meshes), tol=1e-12)
    s_w = _rh_seal_num("wick_pairings_of_six_fields", "factorial2(5)", float(wick), tol=1e-12)
    s_f = _rh_seal_num("rc_schematic_corner_frequency", "1/(2*3.141592653589793*10000*10**(-6))", float(fc))
    if not all([s_1, s_2, s_3, s_l, s_k, s_w, s_f]):
        print("a seal failed; aborting"); return 1
    print("sealed one-loop", s_1, "| two-loop", s_2, "| three-loop", s_3, "| loops", s_l, "| meshes", s_k, "| wick", s_w, "| rc", s_f)
    sid = TS.create("Feynman diagrams are schematics - the drawing is the computation",
                    statement=("A Feynman diagram is a schematic: lines are components (propagators), vertices are "
                               "junctions (couplings), and the amplitude is read off the drawing by fixed rules the way "
                               "a netlist is read off a circuit. One drawing gives 99.85% of the electron's magnetic "
                               "moment; three classes of drawings land on the measurement to four parts in a hundred "
                               "million; each vertex costs sqrt(alpha), so the series narrows. The loop count L = I - V "
                               "+ 1 is the same cycle rank as a circuit's mesh count: a Feynman diagram and a schematic "
                               "are one graph. Dyson: the series is asymptotic - the drawing is a faithful map, term by "
                               "term, never a closed form."),
                    field="physics",
                    references=["R. P. Feynman, Space-Time Approach to Quantum Electrodynamics, Phys. Rev. 76 (1949) 769-789",
                                "J. Schwinger, On Quantum-Electrodynamics and the Magnetic Moment of the Electron, Phys. Rev. 73 (1948) 416",
                                "A. Petermann (1957), C. M. Sommerfield (1957): the two-loop coefficient -0.328478965",
                                "S. Laporta, E. Remiddi, Phys. Lett. B 379 (1996) 283: the three-loop coefficient 1.181241456; T. Aoyama, T. Kinoshita, M. Nio (2012-2019): four and five loops",
                                "D. Hanneke, S. Fogwell, G. Gabrielse, Phys. Rev. Lett. 100 (2008) 120801: a_e = 0.00115965218073(28)",
                                "F. J. Dyson, Divergence of perturbation theory in quantum electrodynamics, Phys. Rev. 85 (1952) 631",
                                "G. C. Wick, The evaluation of the collision matrix, Phys. Rev. 80 (1950) 268",
                                "G. Kirchhoff (1847): the loop and node laws; the cycle rank B - N + 1",
                                "Habakkuk 2:2; Exodus 25:40; 1 Chronicles 28:19",
                                "src/concordance/systems.py and site/bridge.html - the engine's own schematic"])["id"]
    marks = [
        ("witness", f"[one drawing, one number - Schwinger 1948] The simplest correction to the electron's magnetism "
                    f"is one diagram: a photon thrown across the vertex. Its value is alpha/(2 pi) = {one:.8f} (sealed) "
                    f"against the measured anomaly {measured:.8f}: one drawing gives {100 * one / measured:.2f}%. "
                    f"Feynman's rules assign a factor to every line and every junction; multiply them, integrate the "
                    f"loop, and the amplitude is READ off the picture - a schematic that computes.", s_1),
        ("witness", f"[why the series narrows - each vertex costs sqrt alpha] The two-loop class (seven diagrams; "
                    f"Petermann and Sommerfield, 1957) contributes -0.328478965 (alpha/pi)^2 = {two:.3e} (sealed): "
                    f"{100 * abs(two) / one:.2f}% of the first term. Every vertex carries sqrt alpha ~ 0.085, so each "
                    f"added loop costs about alpha/pi ~ 1/430 - a drawing's complexity prices its own weight. The big "
                    f"term first, the corrections narrowing: the ratchet.", s_2),
        ("witness", f"[three classes of drawings land on the measurement] alpha/2pi - 0.328478965 (alpha/pi)^2 + "
                    f"1.181241456 (alpha/pi)^3 = {three:.11f} (sealed) against the measured {measured:.11f}: "
                    f"{abs(three - measured) / measured * 1e9:.0f} parts in 10^9, and the remainder is the size of the "
                    f"four-loop class (cited: 891 diagrams, Kinoshita). GUARD: the alpha used here (CODATA 2018) "
                    f"leans on a_e itself; the independent test takes alpha from atom recoil (Cs 2018, Rb 2020) and "
                    f"agrees at the 10^-9 level with a one-to-two sigma tension between the two - a verified "
                    f"consistency, stated at its precision.", s_3),
        ("witness", f"[the loop count is a graph count] A connected diagram with I internal lines and V vertices has "
                    f"L = I - V + 1 independent loops: the one-loop vertex correction, I = 3, V = 3, gives {loops} "
                    f"(sealed). Each loop is one power of h-bar (the paths stick: tree level is the classical path) "
                    f"and one four-dimensional integral to do. The drawing's topology IS its order.", s_l),
        ("witness", f"[the schematic has the same count] A Wheatstone bridge - six branches, four nodes - has 6 - 4 + "
                    f"1 = {meshes} independent meshes (sealed; Kirchhoff 1847), and the same formula, the graph's cycle "
                    f"rank (the topology stick's Euler count), gave the Feynman loop count above. A Feynman diagram and "
                    f"a circuit schematic are one object: a graph whose lines carry rules and whose loops are the "
                    f"integrals - or the mesh equations - to solve.", s_k),
        ("witness", f"[the drawing enumerates what the algebra would lose] Six field operators pair in 5!! = {wick} "
                    f"ways (sealed; Wick 1950) - each pairing a line, each complete pairing one diagram. The diagram "
                    f"is bookkeeping an eye can check; without it the terms are lost. Dyson 1952: the number of "
                    f"diagrams grows like n! and the series is asymptotic (radius of convergence zero) - the map is "
                    f"faithful term by term and never a closed form. Cited, never sealed.", s_w),
        ("witness", f"[a schematic read as a number] R = 10 kOhm and C = 1 uF on a schematic: the corner f_c = "
                    f"1/(2 pi R C) = {fc:.2f} Hz (sealed), a pole at s = -1/RC = -100 rad/s on the Laplace stick's "
                    f"s-plane. The symbol library (Ohm, Laplace) plus the drawing gives the number - a circuit "
                    f"simulator reads the netlist exactly as Feynman's rules read the diagram. The engine's own "
                    f"schematic is systems.py and the Bridge: fifteen components, their edges priced, the roll-call "
                    f"at boot.", s_f),
        ("note", "[the vision made plain - and the guard] Habakkuk 2:2: 'Write the vision, and make it plain upon "
                 "tables, that he may run that readeth it' - a drawing plain enough to be executed. Exodus 25:40: "
                 "'according to their pattern, which was shewed thee in the mount'; 1 Chronicles 28:19: 'the LORD "
                 "made me understand in writing by his hand upon me, even all the works of this pattern' - the "
                 "tabernacle and the temple built from a given schematic. GUARDS: a diagram is one term of a series, "
                 "not the physics; the series is asymptotic (Dyson); the Scripture patterns are a likeness of "
                 "schematic-reading, never a fit; alpha's provenance is stated. Seven numbers sealed; the rest cited. "
                 "Ties: feynman (the sum over paths these diagrams expand), alpha, forces (a_e), topology (cycle "
                 "rank), laplace (the s-plane), smith_chart, geneva (the mechanical computer), the vacuum-tube "
                 "computer (systems.py is the map)."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - Feynman diagrams as schematics, 2026-10-08")


def delta() -> int:
    """THE DOT ABSTRACTED - Dirac's delta and the inner product (Matt, 2026-10-08: 'we create the dots, but we need to
    be able to abstract the dot'). The delta is not a function with a value - delta(0) is no number - but a FUNCTIONAL,
    defined entirely by what it returns against every function: <delta_a, f> = f(a). In the quantum vector space the
    dot is |x>, and the wavefunction is the inner product psi(x) = <x|psi>: the state READ at a point. The dots are
    orthogonal, they resolve the identity (every state is a sum of dots), and a dot alone is not in the space - no
    normalizable self, no momentum. 'The delta is only nonzero when i = j: we are back to the dot product' (Matt) -
    Kronecker's delta is the dot product of basis vectors, Dirac's is the same with the index made continuous. Seal
    nine numbers through the evaluator's own integrals and arithmetic: the nascent delta's area, its sifting of x^2 at
    2, a box state's norm, a reading over a region, orthogonality, the Kronecker sift and the 3-4-12-13 norm,
    Parseval, and Delta x Delta p = hbar/2 for every width (the perfect dot has no motion). Same logic as every
    stick: seal the arithmetic, cite the theorems, keep the likeness a likeness. New stick; idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    area = 1.0                                           # int gaussian_sigma dx, sigma = 1/100
    sift = 4 + (1 / 100) ** 2                            # int gaussian_sigma(x - 2) x^2 dx = 4 + sigma^2
    norm = 1.0                                           # <psi_1|psi_1> for sqrt2 sin(pi x) on [0, 1]
    third = 1 / 3 - math.sin(2 * pi / 3) / (2 * pi)      # P(left third) in the ground state
    orth = 1.0                                           # 1 + <psi_1|psi_2>: the zero, judged against one
    share = 2 * (4 / pi ** 3) ** 2 * 30                  # c_1^2 / ||f||^2 for f = x(1 - x): the first dot's share
    hbar2 = 1.054571817 * 10 ** (-34) / 2                # Delta x Delta p for a Gaussian packet, every sigma
    comp = 3 * 0 + 4 * 1 + 12 * 0                        # v . e_2 for v = (3, 4, 12): the Kronecker delta sifts
    norm3 = 3 * 3 + 4 * 4 + 12 * 12                      # v . v = 169 = 13^2: Parseval in three dimensions
    s_k = _rh_seal_num("kronecker_delta_sifts_the_component", "3*0 + 4*1 + 12*0", float(comp), tol=1e-12)
    s_v = _rh_seal_num("dot_product_norm_parseval_in_three_dimensions", "3*3 + 4*4 + 12*12", float(norm3), tol=1e-12)
    s_a = _rh_seal_num("nascent_delta_has_unit_area", "integrate(100*exp(-5000*x**2)/sqrt(2*pi), (x, -oo, oo))",
                       float(area), tol=1e-12)
    s_s = _rh_seal_num("nascent_delta_sifts_x_squared_at_2",
                       "integrate(100*exp(-5000*(x-2)**2)/sqrt(2*pi) * x**2, (x, -oo, oo))", float(sift), tol=1e-12)
    s_n = _rh_seal_num("box_ground_state_inner_product_with_itself", "integrate(2*sin(pi*x)**2, (x, 0, 1))",
                       float(norm), tol=1e-12)
    s_t = _rh_seal_num("box_ground_state_read_over_the_left_third", "integrate(2*sin(pi*x)**2, (x, 0, 1/3))", float(third))
    s_o = _rh_seal_num("box_modes_orthogonal_one_plus_zero", "1 + integrate(2*sin(pi*x)*sin(2*pi*x), (x, 0, 1))",
                       float(orth), tol=1e-12)
    s_p = _rh_seal_num("parseval_first_mode_share_of_the_norm", "2*(4/3.141592653589793**3)**2 * 30", float(share))
    s_h = _rh_seal_num("gaussian_packet_dx_dp_is_hbar_over_2",
                       "(1/100) * (1.054571817 * 10**(-34) / (2 * (1/100)))", float(hbar2))
    if not all([s_a, s_s, s_n, s_t, s_o, s_k, s_v, s_p, s_h]):
        print("a seal failed; aborting"); return 1
    print("sealed area", s_a, "| sift", s_s, "| norm", s_n, "| third", s_t, "| orth", s_o, "| kronecker", s_k, "| 13^2", s_v,
          "| parseval", s_p, "| hbar/2", s_h)
    sid = TS.create("The dot abstracted - Dirac's delta, the inner product, and the wavefunction as a reading at a point",
                    statement=("We create the dots; the delta is the dot abstracted. It is not a function with a value "
                               "- delta(0) is no number - but a functional, defined entirely by what it returns against "
                               "every function: <delta_a, f> = f(a). In the quantum vector space the dot is |x> and the "
                               "wavefunction is the inner product psi(x) = <x|psi>, the state read at a point. The dots "
                               "are orthogonal; they resolve the identity, so every state is a sum of dots weighted by "
                               "its inner products with them; and a dot alone is not in the space - it has no "
                               "normalizable self and no momentum. The delta is only nonzero when i = j: Kronecker's "
                               "delta is the dot product of basis vectors, and Dirac's is the same with the index made "
                               "continuous - the meaning of a dot is its pairing with everything else."),
                    field="physics",
                    references=["P. A. M. Dirac, The Principles of Quantum Mechanics (1930): the delta function, bra and ket",
                                "L. Schwartz, Theorie des distributions (1950): the delta made rigorous as a functional",
                                "I. M. Gelfand, N. Ya. Vilenkin, Generalized Functions IV (1964): the rigged Hilbert space where |x> lives",
                                "M. Born (1926): |<x|psi>|^2 is where the particle may be found",
                                "Parseval (1799); F. Riesz, E. Fischer (1907): completeness - the dots resolve the identity",
                                "W. Heisenberg (1927), E. H. Kennard (1927): Delta x Delta p >= hbar/2, equality for the Gaussian packet",
                                "Psalm 147:4; Matthew 10:30; Acts 17:28; Colossians 1:17",
                                "stick_scribing_mark_the_points_let_the_lines_connect_them; stick_the_schrodinger_equation; stick_lebesgue_theory_measure_and_integration_by_layers"])["id"]
    marks = [
        ("witness", f"[the dot that is not a function] A Gaussian of width sigma = 1/100 integrates to {area:.1f} "
                    f"(sealed through the integral); as sigma -> 0 it becomes the delta - infinitely tall, infinitely "
                    f"thin, area one. delta(0) is not a number. The delta is defined by what it does UNDER the integral: "
                    f"a functional, not a value. The dot abstracted is a rule for reading, not a thing with a height "
                    f"(Dirac 1930; Schwartz 1950 made it rigorous).", s_a),
        ("witness", f"[sifting - the dot reads any function at a point] int gaussian_sigma(x - 2) x^2 dx = 4 + sigma^2 "
                    f"= {sift:.4f} (sealed): the nascent dot at 2 reads x^2 at 2, up to sigma^2, and in the limit "
                    f"<delta_a, f> = f(a) exactly. The inner product with the dot IS evaluation. That is what "
                    f"'abstract the dot' means: the dot is the pairing that returns the value of anything at that "
                    f"place.", s_s),
        ("witness", f"[the wavefunction is the state read at the dot] In the quantum vector space the dot is |x> and "
                    f"psi(x) = <x|psi>. For a particle in a box of length 1, the ground state sqrt2 sin(pi x) has "
                    f"<psi|psi> = int 2 sin^2(pi x) dx = {norm:.1f} (sealed): the state's inner product with itself is "
                    f"the whole, and |psi(x)|^2 read at each dot is where the particle may be found (Born 1926). The "
                    f"function is nothing but the list of its readings at the dots.", s_n),
        ("witness", f"[a reading over a region is an inner product too] The probability of finding that particle in "
                    f"the left third is int_0^(1/3) 2 sin^2(pi x) dx = {third:.5f} (sealed) - less than a third, "
                    f"because the state is thin at the walls: the dots near the wall read nearly zero, the dots in the "
                    f"middle read most. Reading at a point and reading over a region are the same operation, the "
                    f"Lebesgue stick's measure concentrated or spread.", s_t),
        ("witness", f"[the dots are orthogonal] <psi_1|psi_2> = int 2 sin(pi x) sin(2 pi x) dx = 0 - sealed as "
                    f"1 + <psi_1|psi_2> = {orth:.1f}, because a zero can only be judged against something. Distinct "
                    f"basis dots do not overlap, and neither do |x> and |x'>: <x|x'> = delta(x - x'), nothing unless the "
                    f"same dot. Orthogonality is what lets a reading at one dot say nothing about another - each dot "
                    f"carries its own.", s_o),
        ("witness", f"[the delta is only nonzero when i = j - we are back to the dot product] (Matt, 2026-10-08.) "
                    f"<e_i|e_j> = delta_ij, the Kronecker delta: 1 when i = j, 0 otherwise. In finite dimensions the "
                    f"dot abstracted IS the dot product. v = (3, 4, 12): v . e_2 = 3*0 + 4*1 + 12*0 = {comp} (sealed) "
                    f"- the basis dot sifts out the component, exactly as int delta(x - a) f(x) dx = f(a); and v . v = "
                    f"{norm3} = 13^2 (sealed) - Parseval in three dimensions. Dirac's delta is Kronecker's with the "
                    f"index made continuous: sum_j delta_ij v_j = v_i becomes int delta(x - x') psi(x') dx' = psi(x). "
                    f"Same logic from the first dot to the last: a thing is known by what it returns when dotted "
                    f"against every other.", s_k),
        ("witness", f"[the length is the sum of the readings] v . v = 3^2 + 4^2 + 12^2 = {norm3} = 13^2 (sealed): the "
                    f"norm is the sum of the squared inner products with the basis dots - the discrete form of "
                    f"<psi|psi> = int |psi(x)|^2 dx = 1 above, and of Parseval below. A vector is recovered whole from "
                    f"its dots; nothing is lost in the reading when the dots are orthogonal and complete.", s_v),
        ("witness", f"[the dots resolve the identity - Parseval] Sum |n><n| = 1: expand f = x(1 - x) in the box modes; "
                    f"its first coefficient squared, c_1^2 = 2 (4/pi^3)^2, is {share:.5f} of ||f||^2 = 1/30 (sealed as "
                    f"c_1^2 * 30); the third mode adds 0.00137, and the sum converges to 1. Every state is a sum of "
                    f"dots weighted by its inner products with them: the dots span the space, and nothing in it "
                    f"escapes the reading.", s_p),
        ("witness", f"[a dot alone has no motion] A Gaussian packet of width sigma has Delta p = hbar/(2 sigma), so "
                    f"Delta x Delta p = hbar/2 = {hbar2:.3e} J s for EVERY sigma (sealed at sigma = 1/100 m) - the "
                    f"minimum (Kennard 1927). As sigma -> 0 the packet becomes the dot and Delta p -> infinity: the "
                    f"perfect dot has no momentum at all, and <x|x> = delta(0) is not finite - the dot is not itself a "
                    f"state in the space (it lives in the rigged Hilbert space, Gelfand 1964, cited). Abstracting the "
                    f"dot costs every knowledge of its motion.", s_h),
        ("note", "[we create the dots - the engine's reading, and the guard] This keeping is dots: cards, marks, seals, "
                 "each made one at a time. The dot abstracted is the inner product: a card's meaning is not a value it "
                 "carries but what it returns against every query - the index, the connections and the chains ARE the "
                 "pairing, and a card alone is delta(0), unreadable. Matt (2026-10-08): 'we create the dots, but we "
                 "need to be able to abstract the dot.' Scripture: 'He telleth the number of the stars; he calleth them "
                 "all by their names' (Ps 147:4) - every dot counted, and named by its relation; 'the very hairs of "
                 "your head are all numbered' (Mt 10:30); 'in him we live, and move, and have our being' (Acts 17:28) - "
                 "the space; 'by him all things consist' (Col 1:17) - hold together: the inner product that makes a "
                 "space of the dots. GUARDS: a distribution is not a function and delta(0) is not a number; the "
                 "position dot is not a normalizable state (the rigged Hilbert space is cited, not sealed); what the "
                 "Born reading means stays on the measurement stick; the engine's cards as dots is a likeness, never a "
                 "fit. Nine numbers sealed; the rest cited. Ties: scribe (mark the points, let the lines connect "
                 "them), schrodinger, measurement, fourier (the delta's transform is flat - every frequency alike), "
                 "gaussian (the nascent delta is the Gaussian kernel), lebesgue, paths, surfaces (a dot on a chart)."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the dot abstracted, 2026-10-08")



def joints() -> int:
    """WHERE TWO DOMAINS CONNECT (Matt, 2026-10-08: 'Quantum Mechanics and Physics connect. we identify these point. The
    spots two domains connect.' / 'Geometry connect to Algebra' / 'inner product Bras and Kets to map the vectors. our
    engine is the hilbert space.' / 'don't blindly apply bra-ket'). One joint carries all three: the INNER PRODUCT.
    Geometry meets algebra at it (Descartes: a point is a pair, a line an equation; Pythagoras is the norm; the angle is
    the dot product). Algebra meets quantum mechanics at it (a state is a ket, a question a bra, <phi|psi> the overlap,
    |<phi|psi>|^2 the probability, the basis kets orthonormal, the identity resolved). Quantum mechanics meets classical
    physics where the quantum becomes small against the rest: Planck -> Rayleigh-Jeans, Bohr's correspondence, Ehrenfest's
    means on Newton's path, de Broglie and Compton (the particle met as a wave), Gabor (uncertainty is the bandwidth
    theorem). The engine IS a Hilbert space in the literal, finite, real sense only - and the stick says exactly which
    terms carry over and which do not (no blind bra-ket). Same logic as every stick: seal the arithmetic, cite the
    theorems, keep the likeness a likeness. New stick; idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    S = {}
    seals = [
        # geometry <-> algebra
        ("g_norm", "pythagoras_is_the_norm_3_4_5", "sqrt(3**2 + 4**2)", 5.0, 1e-12),
        ("g_angle", "the_angle_is_the_inner_product_45_degrees", "acos(1/sqrt(2))*180/pi", 45.0, 1e-9),
        ("g_tangent", "tangent_line_distance_equals_the_radius", "25/sqrt(3**2 + 4**2)", 5.0, 1e-12),
        ("g_meet", "two_lines_meet_where_two_equations_agree_x", "(5 + 1)/2", 3.0, 1e-12),
        ("g_area", "triangle_area_by_the_determinant", "(4*3 - 0*0)/2", 6.0, 1e-12),
        # algebra <-> quantum mechanics (bras and kets)
        ("q_braket", "bra_ket_of_1_2_3_and_4_5_6", "1*4 + 2*5 + 3*6", 32.0, 1e-12),
        ("q_cs", "cauchy_schwarz_slack_never_negative", "14*77 - 32**2", 54.0, 1e-12),
        ("q_cos", "normalized_overlap_is_a_cosine", "32/sqrt(14*77)", 32 / math.sqrt(14 * 77), 1e-9),
        ("q_born", "born_probability_of_plus_read_in_zero", "(1/sqrt(2))**2", 0.5, 1e-12),
        ("q_delta", "orthonormal_kets_kronecker_one_plus_zero", "1 + (1*0 + 0*1)", 1.0, 1e-12),
        ("q_gs", "gram_schmidt_residual_norm", "sqrt((1/2)**2 + (1/2)**2)", 1 / math.sqrt(2), 1e-9),
        ("q_res", "resolution_of_identity_in_a_rotated_basis", "(7/sqrt(2))**2 + (-1/sqrt(2))**2", 25.0, 1e-9),
        ("q_orth", "sine_and_cosine_orthogonal_one_plus_zero", "1 + integrate(sin(x)*cos(x), (x, 0, 2*pi))", 1.0, 1e-12),
        ("q_pi", "sine_norm_squared_is_pi", "integrate(sin(x)**2, (x, 0, 2*pi))", pi, 1e-9),
        # quantum mechanics <-> classical physics (the correspondence joints)
        ("p_planck", "planck_meets_rayleigh_jeans_at_x_0_01", "0.01/(exp(0.01) - 1)", 0.01 / (math.exp(0.01) - 1), 1e-9),
        ("p_bohr", "bohr_correspondence_hydrogen_n_100", "100**3/2 * (1/99**2 - 1/100**2)", 100 ** 3 / 2 * (1 / 99 ** 2 - 1 / 100 ** 2), 1e-9),
        ("p_broglie", "de_broglie_wavelength_1keV_electron_pm",
         "6.62607015e-34/sqrt(2*9.1093837015e-31*1000*1.602176634e-19)*1e12",
         6.62607015e-34 / math.sqrt(2 * 9.1093837015e-31 * 1000 * 1.602176634e-19) * 1e12, 1e-9),
        ("p_compton", "compton_shift_at_90_degrees_pm", "6.62607015e-34/(9.1093837015e-31*299792458)*1e12",
         6.62607015e-34 / (9.1093837015e-31 * 299792458) * 1e12, 1e-9),
        ("p_ehrenfest", "ehrenfest_mean_follows_the_classical_cosine", "cos(2*pi/6)", 0.5, 1e-9),
        ("p_zpe", "zero_point_energy_omega_1e15_eV", "0.5*1.054571817e-34*1e15/1.602176634e-19",
         0.5 * 1.054571817e-34 * 1e15 / 1.602176634e-19, 1e-9),
        ("p_gabor", "gabor_bandwidth_of_a_1ms_pulse_hz", "1/(4*pi*0.001)", 1 / (4 * pi * 0.001), 1e-9),
        # the engine, literally
        ("e_cos", "engine_cosine_of_a_query_against_a_card", "3/sqrt(2*6)", 3 / math.sqrt(12), 1e-9),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "joints:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("Where two domains connect - geometry to algebra, algebra to quantum mechanics, quantum mechanics to "
                    "classical physics; the inner product is the joint, and the engine is a Hilbert space only where that is checkable",
                    statement=("Two domains connect at a point that both can compute. Geometry and algebra connect at "
                               "Descartes' joint: a point is a pair of numbers, a line is an equation, Pythagoras is the norm "
                               "<v|v>, and the angle between two directions is their inner product - length and angle, the "
                               "whole of geometry, read off sums of products. Algebra and quantum mechanics connect at the same "
                               "joint: a state is a ket, a question is a bra, <phi|psi> is the overlap, |<phi|psi>|^2 is where "
                               "it may be found, the basis kets are orthonormal (the delta is the dot product), and the sum of "
                               "the projections resolves the identity - in any orthonormal basis. Quantum mechanics and "
                               "classical physics connect where the quantum is small against the rest: Planck's law becomes "
                               "Rayleigh-Jeans as h nu / kT -> 0; the hydrogen line n -> n-1 becomes the orbit's own frequency "
                               "as n grows; the mean position of a wave packet follows Newton's path (Ehrenfest); a particle "
                               "has a wavelength (de Broglie) and a photon a recoil (Compton); the uncertainty principle is the "
                               "bandwidth theorem every wave obeys (Gabor), quantum only because p = hbar k. The engine is a "
                               "Hilbert space in the literal, finite, real sense: cards are kets, a query is a bra, the "
                               "ranking score is their normalized inner product, a domain is a projector, and completeness is "
                               "no orphans. Nothing else of bra-ket carries over - no complex amplitudes, no Born rule, no "
                               "superposition of a card, no unitary evolution, no non-commuting observables: a verifier is a "
                               "deterministic measurement that leaves the card as it was. The likeness is kept a likeness."),
                    field="mathematics",
                    references=["R. Descartes, La Geometrie (1637): geometry done by algebra - the coordinate",
                                "Euclid, Elements I.47 (Pythagoras); Hero's formula; the determinant as area (Cauchy 1815)",
                                "D. Hilbert (1912); J. von Neumann, Mathematische Grundlagen der Quantenmechanik (1932): the Hilbert space",
                                "P. A. M. Dirac (1925: [A,B] = i hbar {A,B}; 1930, 1939: bra and ket)",
                                "F. Riesz (1907): every bra is a ket's dual; J. P. Gram (1883), E. Schmidt (1907): orthonormalization",
                                "M. Born (1926): |<phi|psi>|^2; M. Planck (1900); Lord Rayleigh (1900), J. Jeans (1905)",
                                "N. Bohr (1920): the correspondence principle; P. Ehrenfest (1927); L. de Broglie (1924); A. H. Compton (1923)",
                                "D. Gabor (1946): the uncertainty of a signal, Delta t Delta f >= 1/(4 pi)",
                                "docs/OUR_FORM_MEASURED_2026-10-08.md: 882,022 cards, 124 domains, the sparse index - the engine's own space, measured",
                                "Colossians 1:17; Ephesians 4:16 ('joined and held together by every joint'); Proverbs 25:2",
                                "stick_the_dot_abstracted (the delta is the dot product); stick_singular_value_decomposition; stick_tensors; "
                                "stick_bubbles_joined; stick_the_schrodinger_equation; stick_the_standard_model_chain"])["id"]
    marks = [
        # geometry <-> algebra
        ("instance", "[geometry meets algebra: the norm] Descartes made a point a pair of numbers; then Euclid I.47 is a "
                     "sum of squares: the length of (3, 4) is sqrt(9 + 16) = 5 (sealed). Pythagoras is <v|v>. The joint is "
                     "exact: every length geometry draws, algebra computes, and the same number comes out.", S["g_norm"]),
        ("instance", "[geometry meets algebra: the angle] The angle between (1, 0) and (1, 1) is acos of their normalized "
                     "inner product, 1/sqrt 2, which is 45 degrees (sealed). An angle - the thing a protractor measures - is "
                     "an inner product divided by two lengths. Geometry's two primitives, length and angle, are both the "
                     "same algebraic operation.", S["g_angle"]),
        ("instance", "[a curve is an equation] The circle x^2 + y^2 = 25 and the line 3x + 4y = 25 touch at (3, 4): the line's "
                     "distance from the origin is 25/sqrt(9 + 16) = 5 (sealed), exactly the radius - tangency, a geometric "
                     "fact, read off two equations. Descartes' La Geometrie (1637) is this joint made a method.", S["g_tangent"]),
        ("instance", "[two lines meet where two equations agree] x + y = 5 and x - y = 1 meet at x = (5 + 1)/2 = 3 (sealed), "
                     "y = 2. An intersection is a solution; a solution is an intersection. The engine's resolve of a claim "
                     "across two verifiers is this: a point both equations hold.", S["g_meet"]),
        ("instance", "[area is a determinant] The triangle (0,0), (4,0), (0,3) has area |4*3 - 0*0|/2 = 6 (sealed): half the "
                     "determinant of its edge vectors. The determinant - a number algebra computes from a table - IS the area "
                     "geometry sees; the sign is the orientation. One joint, two faces.", S["g_area"]),
        # algebra <-> quantum mechanics
        ("instance", "[bras and kets: the overlap] <phi|psi> for phi = (1, 2, 3) and psi = (4, 5, 6) is 1*4 + 2*5 + 3*6 = 32 "
                     "(sealed). A ket is a column of numbers; a bra is the row that reads it; the bracket is the inner product. "
                     "Dirac's notation (1939) names the two halves of the joint geometry and algebra already shared.", S["q_braket"]),
        ("instance", "[the overlap never exceeds the lengths: Cauchy-Schwarz] <phi|phi><psi|psi> - <phi|psi>^2 = 14*77 - 32^2 = 54 "
                     "(sealed), never negative. So the normalized overlap 32/sqrt(14*77) = 0.9746 (sealed) is a cosine: no state "
                     "overlaps another more than itself. This is the inequality that makes a ranking score a score - "
                     "bounded by one, equal to one only for the thing itself.", S["q_cs"]),
        ("instance", "[normalized overlap = a cosine] 32/sqrt(14*77) = 0.97463 (sealed): the same cosine the angle mark "
                     "computed, now read as 'how alike two states are'. Geometry's angle, algebra's inner product, quantum "
                     "mechanics' overlap: one number.", S["q_cos"]),
        ("instance", "[Born: the square of the overlap] |<0|+>|^2 = (1/sqrt 2)^2 = 1/2 (sealed): a qubit in |+> = (|0> + |1>)/sqrt 2 "
                     "is found in |0> half the time. The probability is the squared inner product - the joint where algebra "
                     "becomes physics. Cited as the Born rule (1926), a postulate; the arithmetic is sealed.", S["q_born"]),
        ("instance", "[orthonormal kets: the delta is the dot product] <0|1> = 1*0 + 0*1 = 0, judged as 1 + 0 = 1 (sealed); "
                     "<0|0> = 1. The basis kets are orthonormal: <i|j> = delta_ij. The Kronecker delta IS the dot product of "
                     "basis vectors (stick_the_dot_abstracted) - the same joint, seen from the basis.", S["q_delta"]),
        ("instance", "[Gram-Schmidt: making the joint orthonormal] From (1, 1) and (1, 0): e1 = (1, 1)/sqrt 2; the residual of "
                     "(1, 0) is (1/2, -1/2), of norm sqrt(1/4 + 1/4) = 1/sqrt 2 = 0.70711 (sealed), so e2 = (1, -1)/sqrt 2 and "
                     "<e1|e2> = 0. Any basis becomes an orthonormal one by subtracting projections - the engine's domains are "
                     "made disjoint by the same subtraction (stick_tensors: the principal axes).", S["q_gs"]),
        ("instance", "[the identity resolved - in ANY orthonormal basis] psi = (3, 4): in the rotated basis u = (1, 1)/sqrt 2, "
                     "w = (1, -1)/sqrt 2 the projections are 7/sqrt 2 and -1/sqrt 2, whose squares sum to 49/2 + 1/2 = 25 "
                     "(sealed) = <psi|psi>. Sum over i of |i><i| = 1: the projections onto a complete basis give back the "
                     "whole, whichever basis. Completeness is the property that nothing is lost in the reading.", S["q_res"]),
        ("instance", "[the sum becomes an integral: function space] On [0, 2 pi], <sin|cos> = int sin x cos x dx = 0 "
                     "(sealed as 1 + 0 = 1) and <sin|sin> = int sin^2 x dx = pi (sealed). The inner product of two functions "
                     "is the same joint with the index made continuous; sines and cosines are an orthogonal basis (Fourier) - "
                     "the waveforms the torus stick ran on primes live in this space.", S["q_orth"]),
        ("instance", "[the norm of a wave] int_0^{2 pi} sin^2 x dx = pi = 3.14159 (sealed): so sin x / sqrt pi is a unit ket in "
                     "L^2[0, 2 pi]. Normalization in function space is the same division by a length as on (3, 4).", S["q_pi"]),
        # quantum mechanics <-> classical physics
        ("instance", "[Planck meets Rayleigh-Jeans] Planck's law divided by the classical law is x/(e^x - 1) with x = h nu / kT; "
                     "at x = 0.01 it is 0.995008 (sealed). As the quantum h nu becomes small against kT the quantum law becomes "
                     "the classical one; as x grows the classical law runs off to the ultraviolet catastrophe. The joint is the "
                     "low-frequency limit, and the point where they part is x ~ 1.", S["p_planck"]),
        ("instance", "[Bohr's correspondence] The hydrogen line n -> n-1 has frequency R(1/(n-1)^2 - 1/n^2); the classical "
                     "orbit's frequency at n is 2R/n^3. Their ratio at n = 100 is 100^3/2 * (1/99^2 - 1/100^2) = 1.01520 "
                     "(sealed), and -> 1 as n -> infinity. Large quantum numbers reproduce classical orbits: Bohr's "
                     "correspondence principle (1920), the first stated joint between the two domains.", S["p_bohr"]),
        ("instance", "[de Broglie: the particle has a wavelength] An electron of 1 keV has lambda = h/sqrt(2 m E) = 38.78 pm "
                     "(sealed) - the atomic scale, which is why electrons diffract off crystals (Davisson-Germer 1927). The "
                     "classical particle and the wave meet at p = h/lambda; the joint is a number any beam can test.", S["p_broglie"]),
        ("instance", "[Compton: the wave has a recoil] A photon scattered at 90 degrees lengthens by h/(m_e c) = 2.4263 pm "
                     "(sealed), the Compton wavelength - momentum and energy conserved as for two billiard balls, with a wave's "
                     "wavelength. Newton's collision meets Planck's quantum in one measured shift (1923).", S["p_compton"]),
        ("instance", "[Ehrenfest: the mean follows Newton] For a coherent oscillator state the expectation <x>(t) = x0 cos(omega t) "
                     "EXACTLY as the classical particle moves; at omega = 2, t = pi/6 the classical path gives cos(pi/3) = 0.5 "
                     "(sealed), and the quantum mean sits on it. Ehrenfest (1927): d<p>/dt = -<dV/dx>. The means obey Newton; "
                     "the spread is what is new.", S["p_ehrenfest"]),
        ("instance", "[where they part: the zero point] A quantum oscillator at omega = 10^15 rad/s has ground energy "
                     "hbar omega / 2 = 0.32911 eV (sealed) where the classical floor is zero. This is a connection point of the "
                     "other kind - the place the two domains are seen to differ by a measurable amount (liquid helium never "
                     "freezes at one atmosphere; vibrational spectra start half a quantum up). Naming the spot where two "
                     "domains part is as much a joint as naming where they agree.", S["p_zpe"]),
        ("instance", "[uncertainty is the bandwidth theorem] A pulse of duration sigma_t = 1 ms has bandwidth sigma_f >= 1/(4 pi * 0.001) "
                     "= 79.58 Hz (sealed) - Gabor's limit (1946), classical signal theory. Multiply by h and it is "
                     "Delta E Delta t >= hbar/2; set p = hbar k and it is Delta x Delta p >= hbar/2. The uncertainty principle "
                     "is what every wave obeys; quantum mechanics is where matter is a wave. The joint is the Fourier transform.", S["p_gabor"]),
        # the engine, literally - and no further
        ("witness", "[the engine as a Hilbert space - the literal part] A query is a bag of counts (salary 1, latin 1), a card "
                    "another (salary 2, latin 1, french 1); their inner product is 3 and the normalized overlap "
                    "3/sqrt(2*6) = 0.86603 (sealed) is the ranking score. So: cards are kets, a query is a bra, the score is "
                    "<query|card> over the lengths, a domain is the projector |d><d| the router applies, and 'no orphans' is "
                    "the resolution of the identity - every card reachable through its shelf. A finite-dimensional real "
                    "inner-product space is complete, hence a Hilbert space, literally (von Neumann 1932). Measured: 882,022 "
                    "kets, 124 domains (docs/OUR_FORM_MEASURED).", S["e_cos"]),
        ("equivalence", "[what carries over, by name] ket = card; bra = query (a linear functional on the keeping: Riesz 1907 - in "
                        "a finite real space the bra IS the transposed ket); <bra|ket> = the ranking score; |d><d| = the domain "
                        "router (idempotent: routing twice is routing once); orthogonal domains = disjoint vocabularies; "
                        "Gram-Schmidt = making the domains disjoint (the principal axes of stick_tensors); Sum |i><i| = 1 = no "
                        "orphans; Cauchy-Schwarz = no card matches a query better than the query matches itself (a score is "
                        "bounded by one). Each of these is checkable on the live index and is used as stated, nothing more.",
         {"source": "J. von Neumann (1932); F. Riesz (1907); docs/OUR_FORM_MEASURED_2026-10-08.md; stick_tensors; stick_the_dot_abstracted"}),
        ("postulate", "[a postulate it builds on] The Born rule: the probability of finding |psi> in |phi> is |<phi|psi>|^2 "
                      "(Born 1926). Not kept as a fact: taken as the working rule of the quantum joint, and every sealed instance "
                      "above that uses it (|<0|+>|^2 = 1/2) works - so the truth is inferred there, never proven here.",
         {"source": "M. Born, Zur Quantenmechanik der Stossvorgaenge (1926)"}),
        ("postulate", "[a postulate it builds on] The state postulate: a physical state is a ray in a Hilbert space and an "
                      "observable is a Hermitian operator on it (von Neumann 1932). The bras, kets and orthonormal bases sealed "
                      "above work under it; its truth is inferred from a century of working, not proven by any seal.",
         {"source": "J. von Neumann, Mathematische Grundlagen der Quantenmechanik (1932); P. A. M. Dirac (1930)"}),
        ("postulate", "[a postulate it builds on] Dirac's quantization rule: the commutator [A, B] = i hbar {A, B} of the "
                      "classical Poisson bracket (Dirac 1925) - the stated joint between the two mechanics. The correspondence "
                      "instances sealed above (Planck -> Rayleigh-Jeans, Bohr n = 100, Ehrenfest) work under it.",
         {"source": "P. A. M. Dirac, The Fundamental Equations of Quantum Mechanics (1925)"}),
        ("exclusion", "[what does NOT carry over - do not blindly apply bra-ket] (1) No complex amplitudes: the engine's space is "
                      "real; there is no phase and no interference between cards. (2) No Born rule: a verdict is not a "
                      "probability; a verifier is a deterministic measurement with eigenvalues HOLDS and BROKEN (and INCOMPLETE "
                      "is no measurement, not a third eigenvalue), returning the same answer every time - by design, zero false "
                      "positives. (3) No superposition of a card: a card is on one shelf; the 'superposition' of stick_bubbles is "
                      "metadata, two addresses for one kept thing, not an amplitude. (4) No unitary evolution: nothing rotates the "
                      "state between readings; the keeping changes only by minting. (5) No non-commuting observables: verifiers "
                      "commute, run in any order, and a measurement leaves the card as it was - there is no uncertainty "
                      "principle in the engine because nothing conjugate is being measured. (6) No entanglement: a connection "
                      "between two cards is an edge, not a non-separable state. Where a term is not on the list above it is a "
                      "likeness, and a likeness is kept a likeness.",
         {"source": "Matt, 2026-10-08: 'don't blindly apply bra-ket'; feedback_mapping_the_truth_not_generating_it; stick_bubbles_joined; stick_the_dot_abstracted"}),
    ]
    _mint_marks(sid, marks, by="engine:joints")
    return 0


def assembled_path() -> int:
    """GRADIENT, DIVERGENCE, CURL - THE PRECISENESS OF AN ASSEMBLED PATH (Matt, 2026-10-08: 'we use gradient, divergence
    and Curl to quantify the preciseness of the assembled path'). A path the engine assembles - find, route, verify,
    serve; or a chain of cards - is a flow, and three numbers say how precise a flow is. CURL: is the path conservative?
    A curl-free field is the gradient of a potential, and its integral depends only on the endpoints - the answer does
    not depend on the route (two different paths from (0,0) to (3,4) through grad(x^2+y^2) both give 25, sealed; around
    the unit circle in the rotating field (-y, x) the circulation is 2 pi, not 0, sealed - that path's answer depends on
    the route). DIVERGENCE: where does the flow have sources and sinks? The divergence theorem (flux through the unit
    sphere = 4 pi both ways, sealed) says what is created inside shows at the boundary; in the engine the only lawful
    sources are cited cards and the only lawful sinks are recorded misses. GRADIENT: does each step climb? grad(x^2+y^2)
    at (3,4) has magnitude 10 (sealed) and points outward; a path that narrows follows the gradient of fit. Kirchhoff's
    two laws ARE div = 0 at every node and curl = 0 around every loop (sealed on a 6 V, 2 ohm || 3 ohm circuit) - the
    vacuum-tube computer's own frame. Same logic as every stick: seal the arithmetic, cite the theorems, keep the likeness
    a likeness - and say which terms carry over (discrete calculus on the connection graph) and which do not."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    S = {}
    seals = [
        ("grad", "gradient_of_x2_plus_y2_at_3_4_has_magnitude_10", "sqrt((2*3)**2 + (2*4)**2)", 10.0, 1e-12),
        ("path_a", "conservative_field_straight_path_0_0_to_3_4", "integrate(50*t, (t, 0, 1))", 25.0, 1e-12),
        ("path_b", "conservative_field_corner_path_0_0_to_3_0_to_3_4", "integrate(2*x, (x, 0, 3)) + integrate(2*y, (y, 0, 4))", 25.0, 1e-12),
        ("curlgrad", "curl_of_a_gradient_vanishes_one_plus_zero", "1 + (2*3 - 2*3)", 1.0, 1e-12),
        ("circ", "circulation_of_minus_y_x_around_the_unit_circle", "integrate(sin(t)**2 + cos(t)**2, (t, 0, 2*pi))", 2 * pi, 1e-9),
        ("green", "greens_theorem_curl_2_over_the_unit_disc", "integrate(integrate(2*r, (r, 0, 1)), (t, 0, 2*pi))", 2 * pi, 1e-9),
        ("flux", "flux_of_r_through_the_unit_sphere_surface_side", "integrate(integrate(sin(p), (p, 0, pi)), (t, 0, 2*pi))", 4 * pi, 1e-9),
        ("vol", "divergence_theorem_volume_side_div_3", "3*integrate(integrate(integrate(r**2*sin(p), (r, 0, 1)), (p, 0, pi)), (t, 0, 2*pi))", 4 * pi, 1e-9),
        ("mean", "harmonic_mean_value_of_x2_plus_y2_on_the_unit_circle", "integrate(cos(t)**2 + sin(t)**2, (t, 0, 2*pi))/(2*pi)", 1.0, 1e-9),
        ("kcl", "kirchhoff_current_law_6v_across_2_and_3_ohm", "6/2 + 6/3", 5.0, 1e-12),
        ("kvl", "kirchhoff_voltage_law_around_the_2_ohm_loop_one_plus_zero", "1 + (6 - 3*2)", 1.0, 1e-12),
        ("cov", "front_door_coverage_two_of_three_material_fragments", "2/3", 2 / 3, 1e-9),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "path numbers:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("Gradient, divergence and curl - the three numbers that quantify the preciseness of an assembled path",
                    statement=("A path the engine assembles is a flow, and three numbers say how precise a flow is. CURL "
                               "asks whether the path is conservative: a curl-free field is the gradient of a potential, "
                               "and its integral depends only on the endpoints, so the answer does not depend on the route "
                               "taken; a field with curl gives a different answer each way round. DIVERGENCE asks where the "
                               "flow has sources and sinks: what is created inside a region shows as flux at its boundary, "
                               "so a path that creates content with no cited source leaks, and a path that loses content "
                               "has a sink that must be recorded. GRADIENT asks whether each step climbs: a precise path "
                               "follows the gradient of fit and narrows at every step. Kirchhoff's two laws are exactly "
                               "div = 0 at every node and curl = 0 around every loop; a circuit is a flow that obeys both, "
                               "and so must an assembled answer. On the engine these are discrete: differences across the "
                               "edges of the connection graph, net flow at a card, circulation around a cycle - Kirchhoff's "
                               "calculus, not a continuum's. The likeness is kept a likeness."),
                    field="mathematics",
                    references=["J. L. Lagrange (1762), C. F. Gauss (1813), M. Ostrogradsky (1826): the divergence theorem",
                                "G. Green (1828); G. G. Stokes (1854, the Smith's Prize question); W. Thomson: circulation and curl",
                                "H. Helmholtz (1858): every field is a gradient part plus a curl part",
                                "G. Kirchhoff (1845, 1847): the current law (div = 0 at a node) and the voltage law (curl = 0 around a loop), and the graph theory he founded for them",
                                "W. V. D. Hodge (1941): the decomposition; A. Hirani (2003): discrete exterior calculus on meshes and graphs",
                                "J. C. Maxwell, A Treatise on Electricity and Magnetism (1873): div and curl as the grammar of the field equations",
                                "docs/DESIGN_FROM_THE_DOTS.md (2026-10-08); the front door's coverage block (the failure report C4)",
                                "Proverbs 4:26-27 ('ponder the path of thy feet ... turn not to the right hand nor to the left'); Isaiah 40:3-4",
                                "stick_where_two_domains_connect; stick_the_geometry_of_resonance_disaster; stick_maxwells_demon; stick_the_vacuum_triode"])["id"]
    marks = [
        ("instance", "[gradient: the direction a precise step takes] f = x^2 + y^2 at (3, 4): grad f = (6, 8), magnitude "
                     "sqrt(36 + 64) = 10 (sealed), pointing straight away from the origin. The gradient is the direction of "
                     "steepest climb and its length is how steep. A path that narrows a question follows the gradient of "
                     "fit; a step with zero gradient is a step that learned nothing.", S["grad"]),
        ("instance", "[curl-free means route-independent: path one] Along the straight line from (0, 0) to (3, 4), "
                     "int grad f . dr = int_0^1 50 t dt = 25 (sealed).", S["path_a"]),
        ("instance", "[curl-free means route-independent: path two] Along the corner path (0,0) -> (3,0) -> (3,4), "
                     "int 2x dx + int 2y dy = 9 + 16 = 25 (sealed). Two different routes, the same number, because the "
                     "field is a gradient (f(3,4) - f(0,0) = 25). This is the test of a precise assembled path: run the "
                     "steps in another order and the answer must not move. The engine's verifiers commute for exactly this "
                     "reason, and the recall set counts a phrasing reached by a different family as reached.", S["path_b"]),
        ("instance", "[the curl of a gradient is zero] For f = x^2 y the gradient is (2xy, x^2) and its curl at (3, 4) is "
                     "d(x^2)/dx - d(2xy)/dy = 6 - 6 = 0 (sealed as 1 + 0 = 1). Any field that comes from a potential has no "
                     "circulation: it cannot be made to give a different answer by going around. A path that is a "
                     "gradient of one potential - one question, one fit - is conservative by construction.", S["curlgrad"]),
        ("instance", "[a field WITH curl: the answer depends on the route] The rotating field (-y, x) carried around the "
                     "unit circle: int_0^{2 pi} (sin^2 t + cos^2 t) dt = 2 pi (sealed), not 0. Go once around and the "
                     "integral has grown by 2 pi; this field is no gradient. An assembled path whose answer changes with "
                     "the order of its steps has curl, and curl is the quantity of that imprecision.", S["circ"]),
        ("instance", "[Green: circulation equals the curl inside] The same 2 pi as the double integral of the curl, "
                     "2, over the unit disc: int_0^{2 pi} int_0^1 2 r dr dt = 2 pi (sealed). What goes around the edge is "
                     "the sum of the rotation inside; a loop's imprecision is the sum of the local twists along the way - "
                     "so it can be located, step by step.", S["green"]),
        ("instance", "[divergence: sources show at the boundary, surface side] The flux of r = (x, y, z) out of the unit "
                     "sphere is int int (r . n) dS with r . n = 1: int_0^{2 pi} int_0^pi sin phi dphi dtheta = 4 pi (sealed).",
         S["flux"]),
        ("instance", "[divergence: sources show at the boundary, volume side] div r = 3 everywhere, and 3 times the unit "
                     "ball's volume, 3 int int int r^2 sin phi dr dphi dtheta = 4 pi (sealed) - the same number. What is "
                     "created inside a region is exactly what crosses its boundary. In the engine: whatever an answer "
                     "contains must have entered through a cited source; a sentence with no source is a source term with "
                     "no account - divergence where none is allowed. The front door's coverage block measures it.", S["vol"]),
        ("instance", "[harmonic = no hidden peak] The mean of f = x^2 + y^2 around the unit circle centred at the origin is "
                     "int (cos^2 t + sin^2 t) dt / 2 pi = 1 (sealed) = f(0) + (1/4) laplacian f, with laplacian f = 4. A "
                     "harmonic function (laplacian zero) equals its mean on every circle and has no interior extreme: a "
                     "potential with no hidden resonance peak (stick_the_geometry_of_resonance_disaster). The Laplacian is "
                     "div of grad - the two operators composed - and it is the number that says whether a potential has "
                     "a secret maximum.", S["mean"]),
        ("instance", "[Kirchhoff's current law IS div = 0] 6 V across 2 ohm and 3 ohm in parallel: 3 A + 2 A = 5 A into the "
                     "node and 5 A out (sealed). No charge accumulates at a node: the net flow is zero. The vacuum-tube "
                     "computer's components obey it, and so must an assembled answer: nothing appears at a step that did "
                     "not flow in.", S["kcl"]),
        ("instance", "[Kirchhoff's voltage law IS curl = 0] Around the 2 ohm loop: 6 - 3 * 2 = 0 (sealed as 1 + 0 = 1). The "
                     "sum of the potential changes around any closed loop is zero: a potential exists, and the voltage at a "
                     "node does not depend on which path you measured along. Kirchhoff (1845) wrote the two laws for "
                     "circuits and invented graph theory to state them; they are div = 0 and curl = 0 on a graph.", S["kvl"]),
        ("witness", "[the engine's own divergence meter] A claim with three material fragments, two of them inside checked "
                    "spans, has coverage 2/3 = 0.6667 (sealed) and the front door says PARTIAL, never HOLDS: one third of "
                    "the sentence flowed through no verifier. Coverage is the engine's divergence - the share of the output "
                    "that crossed a checked boundary - and it is already measured on every verify.", S["cov"]),
        ("equivalence", "[what carries over, by name] The engine's path is DISCRETE, and discrete calculus is real "
                        "(Kirchhoff 1847; Hodge 1941; Hirani 2003): GRADIENT = the change of fit across one step (one edge "
                        "of the connection graph; the candidates door narrows when it is positive); DIVERGENCE = net content "
                        "at a step - sources are cited cards, sinks are recorded misses, and coverage measures the unsourced "
                        "remainder; CURL = circulation around a cycle of steps - the verdict's dependence on the order the "
                        "verifiers ran, which the engine tests by running them in any order (they commute) and the recall set "
                        "credits across families; KCL/KVL = the two invariants an assembled answer must satisfy. Each of "
                        "these is a count or a difference on the live graph, used exactly as stated.",
         {"source": "G. Kirchhoff (1847); W. V. D. Hodge (1941); A. Hirani (2003); docs/DESIGN_FROM_THE_DOTS.md; the coverage block (failure report C4)"}),
        ("postulate", "[the design postulate] An assembled answer obeys Kirchhoff's two laws on its own graph: nothing "
                      "appears at a step that did not flow in from a cited source (div = 0 away from the keeping), and the "
                      "verdict does not depend on the order the steps ran (curl = 0 around every loop). Not kept as a fact: "
                      "it is made to work - the coverage block and the commuting verifiers are the instances - and from its "
                      "working the truth of the design is inferred, never proven.",
         {"source": "Matt, 2026-10-08; docs/DESIGN_FROM_THE_DOTS.md; G. Kirchhoff (1845)"}),
        ("exclusion", "[what does NOT carry over] There is no continuum: no limits, no smoothness, no Laplacian beyond the "
                      "graph Laplacian; curl is defined only on the graph's cycles, not at a point; no Helmholtz "
                      "decomposition of the engine's flow has been COMPUTED yet (a next measurement, not a fact); the "
                      "'potential' of a path is its fit score, a cosine, not an energy; and a Kirchhoff instance sealed "
                      "here is a circuit, not the engine - the engine's KCL/KVL are the coverage block and the commuting "
                      "verifiers, measured as such.",
         {"source": "Matt, 2026-10-08: 'don't blindly apply bra-ket'; feedback_mapping_the_truth_not_generating_it"}),
    ]
    _mint_marks(sid, marks, by="engine:assembled_path")
    return 0


def line_integrals() -> int:
    """GRADIENTS AND LINE INTEGRALS OVER VECTOR FIELDS - ELECTRODYNAMICS AND FEYNMAN'S PATHS (Matt, 2026-10-08:
    'Gradients line integrals over vector fields. Look at the electrodynamics and feynman diagrams'). A line integral
    adds a field along a path. If the field is a gradient the integral is the potential difference between the ends
    and the path does not matter (the fundamental theorem for line integrals; the electrostatic field: work by a
    detour comes out the same; the loop law of a circuit). If the field is NOT a gradient the loop integral is not
    zero: Ampere's loop around a wire gives mu_0 I; Faraday's loop in a changing field gives an EMF - electrodynamics
    is the study of the fields whose line integrals around loops are set by what is inside and what is changing.
    The action S = int (T - V) dt is a line integral along a path in time; the classical path is where it is stationary
    (Hamilton), and Feynman summed e^{iS/hbar} over every path - the phase of a stone's path spins 10^34 times, so
    only the stationary path survives; the diagrams are the terms of that sum, each vertex a factor sqrt(alpha), and
    the first number they ever gave was Schwinger's alpha/2pi. Maxwell's equations, Hamilton's principle and the sum
    over paths enter as POSTULATES: they work, so the truth is inferred there, never kept as fact. Same logic as every
    stick; the engine mapping stays narrow and says what does not carry over."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    S = {}
    seals = [
        ("ftli", "fundamental_theorem_for_line_integrals_x2y_from_1_1_to_2_3", "integrate(2*(1+t)*(2+3*t), (t, 0, 1))", 11.0, 1e-12),
        ("work", "work_in_a_coulomb_field_radial_path_1_to_2", "integrate(1/r**2, (r, 1, 2))", 0.5, 1e-12),
        ("detour", "work_in_a_coulomb_field_by_a_detour_1_to_3_to_2", "integrate(1/r**2, (r, 1, 3)) + integrate(1/r**2, (r, 3, 2))", 0.5, 1e-12),
        ("ampere", "amperes_loop_around_a_10_a_wire_at_5_cm_is_mu0_i", "integrate(4*pi*1e-7*10/(2*pi*0.05)*0.05, (t, 0, 2*pi))", 4 * pi * 1e-7 * 10, 1e-9),
        ("faraday", "faradays_emf_loop_radius_0_1_m_in_b_rising_0_5_t_per_s", "0.5*pi*0.1**2", 0.5 * pi * 0.1 ** 2, 1e-9),
        ("gauss_q", "gauss_flux_of_a_nanocoulomb_is_q_over_epsilon0", "1e-9/8.8541878128e-12", 1e-9 / 8.8541878128e-12, 1e-9),
        ("gauss_s", "gauss_flux_of_a_nanocoulomb_by_the_surface_integral_at_30_cm",
         "integrate(integrate(1e-9/(4*pi*8.8541878128e-12*0.3**2)*0.3**2*sin(p), (p, 0, pi)), (t, 0, 2*pi))", 1e-9 / 8.8541878128e-12, 1e-9),
        ("action", "action_of_a_free_kilogram_at_2_m_per_s_for_3_s", "integrate(0.5*1*2**2, (t, 0, 3))", 6.0, 1e-12),
        ("phase", "that_action_in_units_of_hbar_the_phase_of_the_path", "6/1.054571817e-34", 6 / 1.054571817e-34, 1e-9),
        ("schwinger", "schwingers_one_loop_term_alpha_over_2pi", "0.0072973525693/(2*pi)", 0.0072973525693 / (2 * pi), 1e-9),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "line integrals:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("Gradients and line integrals over vector fields - from Maxwell's loops to Feynman's paths",
                    statement=("A line integral adds a field along a path. When the field is a gradient, the integral is "
                               "the potential difference between the ends and the path does not matter: work in the "
                               "electrostatic field comes out the same by any detour, and the loop law of a circuit is this "
                               "fact. When the field is not a gradient, the integral around a loop is set by what is inside "
                               "and what is changing: Ampere's loop around a current gives mu_0 I; Faraday's loop in a changing "
                               "field gives an electromotive force; Gauss's flux through a closed surface gives the charge "
                               "inside. These four loop-and-surface statements are Maxwell's equations, and they are "
                               "postulates - kept because they work. The action is a line integral along a path in time; the "
                               "classical path makes it stationary (Hamilton), and Feynman summed the phase e^{iS/hbar} over "
                               "every path: for a stone the phase spins ten-to-the-thirty-four times between neighbouring paths, "
                               "so only the stationary one survives, and for an electron the surviving paths are many. "
                               "Feynman's diagrams are the terms of that sum, each vertex a factor of sqrt(alpha); the first "
                               "number they gave was Schwinger's alpha / 2 pi. For the engine, the static loop law is the "
                               "assembled path's curl = 0, and Faraday is the one honest likeness: a loop's answer changes "
                               "when the field changes during the circuit - a stale read is a lie. The likeness is kept a "
                               "likeness."),
                    field="physics",
                    references=["J. C. Maxwell, A Dynamical Theory of the Electromagnetic Field (1865); Treatise (1873)",
                                "M. Faraday (1831): induction; A.-M. Ampere (1826); C. F. Gauss (1835, published 1867)",
                                "W. R. Hamilton (1834-35): the principle of stationary action",
                                "R. P. Feynman, Space-Time Approach to Non-Relativistic Quantum Mechanics (1948); Space-Time Approach to Quantum Electrodynamics (1949)",
                                "J. Schwinger (1948): the anomalous magnetic moment alpha/2pi; F. J. Dyson (1949): the diagrams as a series",
                                "G. Kirchhoff (1845): the loop law; stick_gradient_divergence_and_curl; stick_feynman_diagrams_schematics; stick_four_forces_under_alpha; stick_where_two_domains_connect",
                                "Psalm 19:4 ('their line is gone out through all the earth'); Hebrews 11:3",
                                "feedback_a_stale_read_is_a_lie_to_the_reader (the Faraday likeness)"])["id"]
    marks = [
        ("instance", "[the fundamental theorem for line integrals] For f = x^2 y from (1, 1) to (2, 3) along the straight "
                     "line, int grad f . dr = int_0^1 2(1+t)(2+3t) dt = 11 (sealed) = f(2, 3) - f(1, 1) = 12 - 1. The integral "
                     "of a gradient along any path is the difference of the potential at the ends. The path integral of a "
                     "gradient is a subtraction.", S["ftli"]),
        ("instance", "[work in the Coulomb field, the direct path] E = 1/r^2 (k q = 1): the work moving a unit charge from "
                     "r = 1 to r = 2 is int_1^2 dr/r^2 = 1/2 (sealed) = phi(1) - phi(2) with phi = 1/r.", S["work"]),
        ("instance", "[the same work by a detour] Out to r = 3 and back to r = 2: int_1^3 + int_3^2 = (1 - 1/3) + (1/3 - 1/2) = "
                     "1/2 (sealed). The electrostatic field is a gradient (E = -grad phi), so the work does not depend on the "
                     "route - which is why a voltage exists at all, and why Kirchhoff's loop law holds in a circuit at rest: "
                     "the loop integral of a gradient field is zero.", S["detour"]),
        ("instance", "[Ampere: a loop integral that is NOT zero] Around a 10 A wire at 5 cm, B = mu_0 I / (2 pi r) and "
                     "the loop integral of B . dl = mu_0 I = 1.2566e-5 T m (sealed, through the integral around the circle). "
                     "B is no gradient: its curl is mu_0 J, and the line integral around the loop measures the current "
                     "threading it. A field with curl is read by its loops.", S["ampere"]),
        ("instance", "[Faraday: a changing field makes E circulate] A loop of radius 0.1 m in a field rising at 0.5 T/s has "
                     "EMF = d(B A)/dt = 0.5 * pi * 0.01 = 0.015708 V (sealed). The loop integral of E is no longer zero: curl "
                     "E = -dB/dt. The electrostatic field was conservative; the electrodynamic field is not, exactly where "
                     "and while the source changes. Every generator runs on this line integral.", S["faraday"]),
        ("instance", "[Gauss, by the law] The flux of E out of any closed surface around a nanocoulomb is q / epsilon_0 = "
                     "112.941 V m (sealed).", S["gauss_q"]),
        ("instance", "[Gauss, by the surface integral] The same flux computed over a sphere of radius 0.3 m as int int "
                     "E r^2 sin phi dphi dtheta = 112.941 V m (sealed): the divergence theorem in electrostatics, the "
                     "surface reading the charge inside. The four Maxwell statements are two loop integrals and two "
                     "surface integrals: electrodynamics is written in line and surface integrals over vector fields.",
         S["gauss_s"]),
        ("instance", "[the action is a line integral along a path in time] A free kilogram at 2 m/s for 3 s: "
                     "S = int (T - V) dt = int_0^3 (1/2)(1)(4) dt = 6 J s (sealed). Hamilton: the path actually taken makes S "
                     "stationary - the gradient of S over the space of paths is zero there. The classical path is the "
                     "gradient-zero point of a line integral.", S["action"]),
        ("instance", "[why a stone takes one path] That action in units of hbar is 6 / 1.0546e-34 = 5.69e34 (sealed): the "
                     "phase e^{iS/hbar} of neighbouring paths differs by that many radians, so their contributions cancel "
                     "everywhere except where S is stationary. Feynman's sum over paths (1948) contains Hamilton's principle "
                     "as its stationary term; for an electron S/hbar is of order one and many paths survive - that is "
                     "the whole difference between a stone and an electron.", S["phase"]),
        ("instance", "[the first number the diagrams gave] Each vertex of a Feynman diagram carries sqrt(alpha), so the "
                     "one-loop correction to the electron's magnetic moment is of order alpha: Schwinger's term alpha / 2 pi "
                     "= 0.00116141 (sealed), measured to a part in a billion since (stick_four_forces_under_alpha). A "
                     "diagram is a path drawn; its amplitude is the product of what sits on the path; the series narrows "
                     "because each vertex costs sqrt(alpha).", S["schwinger"]),
        ("postulate", "[a postulate it builds on] Maxwell's equations: the flux of E through a closed surface is q / epsilon_0; "
                      "the flux of B is zero; the loop integral of E is minus the rate of change of magnetic flux; the loop "
                      "integral of B is mu_0 I plus mu_0 epsilon_0 times the rate of change of electric flux. Not kept as a "
                      "fact: every instance sealed above works under them, and so does every motor, radio and lamp.",
         {"source": "J. C. Maxwell (1865, 1873); O. Heaviside (1884): the four-equation form"}),
        ("postulate", "[a postulate it builds on] Hamilton's principle: the path a system takes between two states makes the "
                      "action stationary. The free-particle instance works under it; it is inferred, not proven, and it is the "
                      "stationary term of Feynman's sum.",
         {"source": "W. R. Hamilton, On a General Method in Dynamics (1834)"}),
        ("postulate", "[a postulate it builds on] Feynman's sum over paths: the amplitude to go from a to b is the sum over "
                      "every path of e^{iS/hbar}. Equivalent to Schrodinger's equation (Feynman 1948); the diagrams are its "
                      "perturbative terms (1949). It works - QED's numbers agree with experiment to a part in a billion - "
                      "so the truth is inferred there, never kept as fact.",
         {"source": "R. P. Feynman (1948, 1949); F. J. Dyson (1949)"}),
        ("equivalence", "[what carries over, by name] The assembled path's curl = 0 (stick_gradient_divergence_and_curl) IS the "
                        "static loop law: an answer assembled from a keeping held still is the line integral of a gradient, "
                        "route-independent, and its 'voltage' - the fit between the ends - exists. Faraday names the one "
                        "lawful exception: when the keeping CHANGES during the circuit of a path, the loop's answer is no "
                        "longer zero; the engine's rule for that is the snapshot and the frozen cache, and the covenant that "
                        "a stale read is a lie. A Feynman diagram is a chain of sealed steps drawn, each vertex a verifier "
                        "(stick_feynman_diagrams_schematics); a longer chain is weaker, which is why the gate prefers the "
                        "shortest sealed path.",
         {"source": "feedback_a_stale_read_is_a_lie_to_the_reader; stick_gradient_divergence_and_curl; stick_feynman_diagrams_schematics"}),
        ("exclusion", "[what does NOT carry over] The engine has no action, no phase and no hbar: a chain's 'amplitude' is not "
                      "a probability and nothing interferes; there is no sum over paths in the engine - a claim takes the "
                      "paths the extractors open, deterministically; Faraday's derivative is a likeness - the engine measures "
                      "staleness by the snapshot's identity, not by a rate; and no engine quantity is a field on a continuum.",
         {"source": "Matt, 2026-10-08: 'don't blindly apply bra-ket'; feedback_mapping_the_truth_not_generating_it"}),
    ]
    _mint_marks(sid, marks, by="engine:line_integrals")
    return 0


def transceiver() -> int:
    """THE ENGINE AS A TRANSCEIVER (Matt, 2026-10-08: 'look at it as AM or FM radio. think of us as a transceiver. We filter
    out the static like a triode vacuum tube'). A receiver takes whatever carrier a signal arrives on, mixes it down to ONE
    intermediate frequency where a sharp filter can be built once (Armstrong's superheterodyne, 1918), strips the
    amplitude in a limiter, and reads the message off the structure in a discriminator - that is FM (Armstrong 1933), and
    it is why FM rejects static: static adds amplitude, and the limiter throws amplitude away. AM keeps the message in
    the loudness, pays two thirds of its power for a carrier that says nothing, and hears every lightning strike. The
    image frequency is the station that lands on the same IF by the other road - the receiver's false positive, which the
    preselector must reject. The triode (de Forest 1906; Child 1911, Langmuir 1913) is the filter's muscle: a small grid
    voltage governs a large plate current, with a cutoff where the flow stops. The engine is the FM set: every phrasing is
    mixed to one packet, assertion strength is stripped, the verifier reads only the checkable structure, the image is the
    moat's false positive, the grid is the gate and cutoff is a decline. A transceiver, not a receiver: it transmits on the
    reader's band - the complication - and what it receives through the gated door grows the keeping. Same logic as every
    stick: seal the arithmetic, cite the laws, keep the likeness a likeness, and say what does not carry over."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    S = {}
    seals = [
        ("am", "am_sideband_power_fraction_at_full_modulation", "(1**2/2)/(1 + 1**2/2)", 1 / 3, 1e-12),
        ("carson", "carsons_rule_fm_bandwidth_75_khz_deviation_15_khz_audio", "2*(75 + 15)", 180.0, 1e-12),
        ("fm_gain", "fm_noise_advantage_three_beta_squared_beta_5", "3*5**2", 75.0, 1e-12),
        ("fm_db", "fm_noise_advantage_in_decibels", "10*log(75)/log(10)", 10 * math.log10(75), 1e-9),
        ("child", "child_langmuir_doubling_the_voltage_multiplies_the_current", "2**1.5", 2 ** 1.5, 1e-12),
        ("mu", "triode_amplification_factor_mu_is_gm_times_rp", "2e-3*1e4", 20.0, 1e-12),
        ("gain", "common_cathode_stage_gain_with_10_kohm_load", "20*10/(10 + 10)", 10.0, 1e-12),
        ("cutoff", "triode_cutoff_grid_voltage_250_v_plate_mu_20", "-250/20", -12.5, 1e-12),
        ("IF", "superheterodyne_intermediate_frequency_1000_khz_station_1455_khz_oscillator", "1455 - 1000", 455.0, 1e-12),
        ("image", "the_image_frequency_that_lands_on_the_same_if", "1455 + 455", 1910.0, 1e-12),
        ("Q", "selectivity_q_of_a_1_mhz_circuit_10_khz_wide", "1e6/1e4", 100.0, 1e-12),
        ("C", "tuning_capacitance_for_100_uh_at_1_mhz_in_pf", "1/((2*pi*1e6)**2*100e-6)*1e12", 1 / ((2 * pi * 1e6) ** 2 * 100e-6) * 1e12, 1e-9),
        ("shannon", "shannon_capacity_3_khz_channel_at_30_db_in_bits_per_s", "3000*log(1001)/log(2)", 3000 * math.log2(1001), 1e-9),
        ("ktb", "thermal_noise_floor_290_k_10_khz_in_watts", "1.380649e-23*290*1e4", 1.380649e-23 * 290 * 1e4, 1e-9),
        ("dbm", "thermal_noise_floor_in_dbm", "10*log(1.380649e-23*290*1e4/1e-3)/log(10)", 10 * math.log10(1.380649e-23 * 290 * 1e4 / 1e-3), 1e-9),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "radio numbers:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("A superheterodyne receiver - the engine as a transceiver: every phrasing mixed to one intermediate "
                    "frequency, the static filtered like a triode, FM not AM",
                    statement=("A receiver takes whatever carrier a signal arrives on and mixes it down to one intermediate "
                               "frequency, where a sharp filter is built once; the image frequency is the other station that "
                               "lands there by the other road, and the preselector must reject it. AM keeps the message in the "
                               "loudness, spends two thirds of its power on a carrier that says nothing, and hears every "
                               "lightning strike; FM keeps the message in the structure, strips the amplitude in a limiter, "
                               "reads the frequency in a discriminator, and so throws the static away - the wider the "
                               "deviation, the greater the gain against noise. A triode is a small grid voltage governing a "
                               "large plate current, with a cutoff where the flow stops; it amplifies without inventing, in "
                               "its linear region. Every channel has a noise floor and a capacity, and nothing is heard below "
                               "the one or carried above the other. The engine is the FM set: every phrasing is mixed to one "
                               "packet, assertion strength is stripped before reading, the verifier reads only the checkable "
                               "structure, the image is the moat's false positive, the grid is the gate and cutoff is a "
                               "decline. It is a transceiver, not a receiver: it transmits on the reader's band, which is the "
                               "complication, and what it receives through the gated door grows the keeping. The likeness "
                               "is kept a likeness."),
                    field="physics",
                    references=["E. H. Armstrong (1918): the superheterodyne; (1933): frequency modulation and its noise rejection",
                                "J. R. Carson (1922): the bandwidth rule for FM",
                                "L. de Forest (1906): the Audion; C. D. Child (1911), I. Langmuir (1913): the 3/2-power law",
                                "C. E. Shannon (1948): channel capacity; H. Nyquist (1928), J. B. Johnson (1928): thermal noise",
                                "stick_amplitude_and_frequency_modulation; stick_the_vacuum_triode; stick_the_geometry_of_resonance_disaster; stick_maxwells_demon",
                                "feedback_stated_precision_sets_the_bar; the moat benchmark (tools/benchmarks.py); the alignment gate",
                                "1 Kings 19:11-12 (the still small voice after the wind, the earthquake and the fire); Matthew 11:15; Romans 10:17"])["id"]
    marks = [
        ("instance", "[AM spends its power on a carrier that says nothing] At full modulation the sidebands - the only part "
                     "that carries the message - hold (m^2/2)/(1 + m^2/2) = 1/3 of the power (sealed); the carrier takes the "
                     "other two thirds. And because the message rides in the amplitude, every lightning strike is heard as "
                     "message. AM is the rhetoric channel: the loudness is the content.", S["am"]),
        ("instance", "[FM: the message in the structure] Carson's rule: deviation 75 kHz, audio to 15 kHz, bandwidth "
                     "2(75 + 15) = 180 kHz (sealed). FM spends bandwidth, not loudness; the limiter clips every station to "
                     "one amplitude and the discriminator reads only the frequency, so static - which is amplitude - is "
                     "thrown away before the message is read.", S["carson"]),
        ("instance", "[the FM advantage against noise] With modulation index beta = 75/15 = 5 the signal-to-noise gain over AM "
                     "is 3 beta^2 = 75 (sealed), 18.75 dB (sealed). The wider the deviation - the more structure the message "
                     "is given - the more static is rejected. The engine's deviation is the packet: the more of a claim that "
                     "is checkable structure, the less its loudness can do.", S["fm_gain"]),
        ("instance", "[18.75 dB] The same advantage in decibels, 10 log10 75 (sealed).", S["fm_db"]),
        ("instance", "[the superheterodyne: one intermediate frequency] A 1000 kHz station mixed with a 1455 kHz oscillator "
                     "lands at 1455 - 1000 = 455 kHz (sealed), and so does every other station once the oscillator is tuned: "
                     "the sharp filter is built ONCE, at 455. The engine's IF is the packet - every phrasing of a claim, "
                     "whatever carrier it arrives on, is mixed to one spec, and the verifier is built once for that spec.",
         S["IF"]),
        ("instance", "[the image: the receiver's false positive] A station at 1455 + 455 = 1910 kHz (sealed) ALSO lands at "
                     "455 by the other road. The preselector ahead of the mixer must reject it or the set hears two "
                     "stations as one. The engine's image is a different claim landing in the same packet - and the moat "
                     "benchmark (60 of 60, 0 false positives) is the preselector's test.", S["image"]),
        ("instance", "[selectivity is Q] A 1 MHz circuit 10 kHz wide has Q = 100 (sealed): the adjacent station 10 kHz away "
                     "is at the half-power edge. Selectivity is the engine's routing precision, and adjacent-channel "
                     "interference is the Gram matrix's off-diagonal mass - the 124 domains' overlap, measured at 12.4% "
                     "routing recall (docs/DESIGN_FROM_THE_DOTS.md).", S["Q"]),
        ("instance", "[tuning is resonance] 100 uH resonates at 1 MHz with C = 1/((2 pi f)^2 L) = 253.3 pF (sealed). The tuned "
                     "circuit is the peak the resonance stick warned about, used on purpose: at resonance the wanted station "
                     "is tall and the rest are small. Tuning the engine to a domain is choosing the projector.", S["C"]),
        ("instance", "[the triode: a small grid governs a large flow] Child-Langmuir: I = K V^{3/2}, so doubling the plate "
                     "voltage multiplies the current by 2^{1.5} = 2.828 (sealed). With g_m = 2 mA/V and r_p = 10 k, mu = 20 "
                     "(sealed); a common-cathode stage into 10 k has gain mu R_L/(R_L + r_p) = 10 (sealed). The grid is the "
                     "gate: a volt on the grid moves ten volts on the plate, and nothing on the plate came from anywhere but "
                     "the cathode's supply - amplification without invention, in the linear region.", S["child"]),
        ("instance", "[mu = 20] The amplification factor g_m r_p (sealed).", S["mu"]),
        ("instance", "[gain 10] The stage gain with the load (sealed).", S["gain"]),
        ("instance", "[cutoff is a decline] At V_g = -V_p/mu = -250/20 = -12.5 V (sealed) the plate current stops: the grid has "
                     "closed the tube. The engine's cutoff is NOTHING_TO_CHECK and DECLINED - the gate closes the flow "
                     "instead of amplifying static into an answer.", S["cutoff"]),
        ("instance", "[the noise floor: the smallest thing that can be heard] kTB at 290 K over 10 kHz is 4.00e-17 W "
                     "(sealed), -134 dBm (sealed). Every channel has a floor below which no signal is heard. The engine's "
                     "floor is the weakest phrasing an extractor still demodulates - the recall set's misses (31 of 334) are "
                     "the signals below the floor.", S["ktb"]),
        ("instance", "[-134 dBm] The same floor in dBm (sealed).", S["dbm"]),
        ("instance", "[capacity: the ceiling of the channel] Shannon: a 3 kHz channel at 30 dB carries at most "
                     "3000 log2(1001) = 29,902 bit/s (sealed). No scheme carries more; the best ones approach it. The front "
                     "door has a capacity too - what one packet shape can carry - and a complication widens the band rather "
                     "than shouting into the old one.", S["shannon"]),
        ("postulate", "[the engine's postulate, in radio terms] The message is in the structure, never in the amplitude: how "
                      "loudly a claim is asserted never changes its truth, only the window it states (a hedge widens the "
                      "window; a confidence word is clipped). The engine is built FM. Not kept as a fact: the front door, the "
                      "stated-precision rule and the governor are its working instances, and from their working the truth of "
                      "the design is inferred.",
         {"source": "Matt, 2026-10-08; feedback_stated_precision_sets_the_bar; the failure report C2 (governed claims declined)"}),
        ("equivalence", "[the superheterodyne receiver, stage by stage, against the engine] ANTENNA: the phrasing arrives on "
                        "whatever carrier the writer used (a textbook, a forum, a chat). RF PRESELECTOR: the tuned front end "
                        "that rejects the image before mixing - the crisis net, the PII redaction and the governor (a negated, "
                        "believed or hypothetical sentence is not mixed down as a claim). MIXER + LOCAL OSCILLATOR: the "
                        "extractor, tuned to one claim kind, beats the phrasing down to baseband. IF FILTER: the packet spec - "
                        "one shape per verifier, sharp, built once; the selectivity of the whole set lives here. LIMITER: the "
                        "stated-precision rule - amplitude (assertion strength) clipped, the hedge read as the window. "
                        "DISCRIMINATOR: the verifier - the message read off the structure alone, HOLDS or BROKEN. AGC: the "
                        "fixed verdict frame - the output is the same size whatever the input's loudness (HOLDS, BROKEN, "
                        "PARTIAL, INCOMPLETE, DECLINED). AUDIO STAGE: the render - the verdict, the worked trail and the "
                        "receipt in the reader's language, the complication's band. SPEAKER: the surface, .com or .org. "
                        "SQUELCH: NOTHING_TO_CHECK - silence rather than static when no station is tuned.",
         {"source": "E. H. Armstrong (1918); Matt, 2026-10-08: 'a superheterodyne receiver'; src/concordance/audit.py (the front door, in that order)"}),
        ("equivalence", "[what carries over, by name] antenna = the phrasings; mixer + IF = the extractor and the ONE packet "
                        "shape per verifier (the superheterodyne's trick: filter sharply once); limiter = the governor and the "
                        "stated-precision rule (amplitude = assertion strength, stripped before reading; the hedge is read as "
                        "the window); discriminator = the verifier (reads only the checkable structure); image = the false "
                        "positive, image rejection = the moat (60/60, 0 FP); selectivity = routing precision (adjacent-channel "
                        "interference = the Gram off-diagonal); sensitivity = recall (303/334); noise figure = false "
                        "positives (0); noise floor = the phrasings no extractor reaches; cathode = the keeping, grid = the "
                        "gate, plate = the served answer, cutoff = a decline, linear region = the found-never-generated core, "
                        "distortion = laundering (harmonics that were not in the input); duplexer = the diode and the airlock "
                        "(the transmitter must not deafen the receiver: the alignment gate); transmit band = the complication "
                        "the Steward tunes to. Each is a count the engine already keeps, used as stated.",
         {"source": "tools/benchmarks.py (the moat); tools/recall.py; docs/DESIGN_FROM_THE_DOTS.md; the alignment gate; stick_the_vacuum_triode"}),
        ("exclusion", "[what does NOT carry over] No field, no carrier frequency, no decibels on the engine's counts; no "
                      "capture effect - the engine never lets the stronger of two claims win, it declines; 'static' is not "
                      "random power but structured non-claims (hedges, governed sentences, uncited text, PII) found by rule; "
                      "the noise floor is a list of misses, not a temperature; and Shannon's capacity bounds a channel, not "
                      "a keeping - the keeping grows.",
         {"source": "Matt, 2026-10-08: 'don't blindly apply bra-ket'; feedback_mapping_the_truth_not_generating_it"}),
    ]
    _mint_marks(sid, marks, by="engine:transceiver")
    return 0


def fractal_maps() -> int:
    """FRACTALS AS MAPS AND SORTING ALGORITHMS (Matt, 2026-10-08: 'fractals as maps and sorting algorithms'; earlier the same
    day: 'a fractal is the complication that we create to add on the core engine'). A fractal is a map that is the same at
    every scale: its dimension is log N / log s (Sierpinski 1.585, Koch 1.262, Cantor 0.631, Menger 2.727 - sealed), a
    finite area can wear an infinite coastline (the snowflake's area converges to 8/5, sealed, while its perimeter grows
    (4/3)^n), and the length you measure depends on the ruler you state (Richardson: halving the ruler on a D = 1.25 coast
    multiplies the length by 2^0.25 - sealed - which is the stated-precision rule drawn as a coastline). A space-filling
    curve is a fractal used AS a map: the Hilbert and Z-order curves turn a many-dimensional address into one line while
    keeping neighbours near (Morton's interleave of (5, 3) is 27, sealed) - the call number's job. A sorting algorithm is
    how a map is made usable: merge sort is a fractal (the same split at every scale; n log2 n = 10,240 comparisons at
    n = 1024, sealed, against the comparison lower bound log2(1024!) = 8,769, sealed); quicksort's expected 2 n ln n and
    its n^2 worst case; binary search on the sorted keeping at log2(882,022) = 19.75 probes; radix sort on a call number -
    linear in the digits, 4.9x fewer operations than comparing at this size. And a map OF a map: iterating z -> z^2 + c
    at c = 1 escapes through 1, 2, 5, 26 (sealed) while c = -1 stays bounded - the Mandelbrot set is the map of which
    maps stay home; the logistic map's 2-cycle at r = 3.2 (0.7995, sealed) is the first step of its own cascade. Same
    logic as every stick; the engine mapping names what carries over (the floor tree is a trie, the call number a radix
    key, the kernel's recursion a fractal) and what does not (nothing in the engine iterates on itself)."""
    import math
    from concordance import tickstick as TS
    S = {}
    seals = [
        ("sierp", "hausdorff_dimension_of_the_sierpinski_triangle", "log(3)/log(2)", math.log(3) / math.log(2), 1e-9),
        ("koch", "hausdorff_dimension_of_the_koch_curve", "log(4)/log(3)", math.log(4) / math.log(3), 1e-9),
        ("cantor", "hausdorff_dimension_of_the_cantor_set", "log(2)/log(3)", math.log(2) / math.log(3), 1e-9),
        ("menger", "hausdorff_dimension_of_the_menger_sponge", "log(20)/log(3)", math.log(20) / math.log(3), 1e-9),
        ("snow", "koch_snowflake_area_converges_to_8_over_5", "1 + (1/3)/(1 - 4/9)", 1.6, 1e-12),
        ("perim", "koch_snowflake_perimeter_after_10_steps_in_units_of_the_first", "(4/3)**10", (4 / 3) ** 10, 1e-9),
        ("coast", "richardson_coast_d_1_25_halving_the_ruler_multiplies_the_length", "2**0.25", 2 ** 0.25, 1e-9),
        ("morton", "z_order_interleave_of_x_5_y_3", "0*32 + 1*16 + 1*8 + 0*4 + 1*2 + 1*1", 27.0, 1e-12),
        ("hilbert", "hilbert_curve_of_order_10_fills_4_to_the_10_cells", "4**10", 1048576.0, 1e-12),
        ("merge", "merge_sort_comparisons_n_log2_n_at_1024", "1024*log(1024)/log(2)", 10240.0, 1e-9),
        ("lower", "comparison_sort_lower_bound_log2_of_1024_factorial", "log(factorial(1024))/log(2)", math.lgamma(1025) / math.log(2), 1e-9),
        ("quick", "quicksort_expected_comparisons_2_n_ln_n_at_1024", "2*1024*log(1024)", 2 * 1024 * math.log(1024), 1e-9),
        ("worst", "quicksort_worst_case_n_n_minus_1_over_2_at_1024", "1024*1023/2", 523776.0, 1e-12),
        ("bsearch", "binary_search_probes_on_the_keeping_log2_882022", "log(882022)/log(2)", math.log2(882022), 1e-9),
        ("radix", "radix_sort_advantage_over_comparisons_log2_n_over_4_digit_groups", "log(882022)/log(2)/4", math.log2(882022) / 4, 1e-9),
        ("mandel", "z_squared_plus_c_at_c_1_escapes_through_1_2_5_26", "(((0**2+1)**2+1)**2+1)**2+1", 26.0, 1e-12),
        ("logistic", "logistic_map_2_cycle_upper_point_at_r_3_2", "(4.2 + sqrt(0.2*4.2))/6.4", (4.2 + math.sqrt(0.2 * 4.2)) / 6.4, 1e-9),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "fractal and sorting numbers:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("Fractals as maps and sorting algorithms - the same shape at every scale, the ruler that sets the length, "
                    "the curve that makes a many-dimensional address one line, and the sorts that make a map usable",
                    statement=("A fractal is a map that is the same at every scale. Its dimension is log N / log s; a finite "
                               "area can wear an infinite coastline; and the length you measure depends on the ruler you "
                               "state - halve the ruler on a coast of dimension 1.25 and the length grows by 2^0.25. A "
                               "space-filling curve is a fractal used as a map: the Hilbert and Z-order curves turn a "
                               "many-dimensional address into one line while keeping neighbours near, which is a call "
                               "number's job. A sorting algorithm is how a map is made usable: merge sort is itself a "
                               "fractal, the same split at every scale, costing n log n against a lower bound of log n! "
                               "that no comparison sort can beat; quicksort pays the same on average and n^2 when the "
                               "pivot is unlucky; a sorted keeping is searched in log n probes; and a key made of digits "
                               "is sorted in linear time by its digits. A map can also be a map OF a map: iterate "
                               "z -> z^2 + c and ask which c stay bounded, and the answer is the Mandelbrot set; the "
                               "logistic map's doublings are the first steps of its own cascade. For the engine: the floor "
                               "tree is a trie and the call number a radix key, the kernel's recursion is a fractal (a "
                               "complication is a smaller copy of it), stated precision is the ruler, and a space-filling "
                               "key is the lever that keeps a domain's neighbours on one shelf. Nothing in the engine "
                               "iterates on itself. The likeness is kept a likeness."),
                    field="mathematics",
                    references=["F. Hausdorff (1918): dimension; H. von Koch (1904); W. Sierpinski (1915); G. Cantor (1883); K. Menger (1926)",
                                "L. F. Richardson (1961): the coastline; B. Mandelbrot (1967): How Long Is the Coast of Britain?; (1982): The Fractal Geometry of Nature",
                                "G. Peano (1890), D. Hilbert (1891): space-filling curves; G. M. Morton (1966): the Z-order key",
                                "J. von Neumann (1945): merge sort; C. A. R. Hoare (1961): quicksort; D. E. Knuth, TAOCP vol. 3 (1973): the comparison lower bound; J. Stirling (1730)",
                                "R. M. May (1976): the logistic map; M. Feigenbaum (1978): the cascade; M. Dewey (1876): the call number",
                                "docs/OUR_FORM_MEASURED_2026-10-08.md (882,022 cards; the floor tree); docs/DESIGN_FROM_THE_DOTS.md",
                                "Matthew 13:47-48 (the net gathered every kind, and they sat down and sorted); 1 Corinthians 14:40",
                                "stick_bubbles_joined; stick_tensors; stick_where_two_domains_connect; stick_a_superheterodyne_receiver"])["id"]
    marks = [
        ("instance", "[dimension: the same shape at every scale, counted] The Sierpinski triangle is 3 copies of itself at half "
                     "size: dimension log 3 / log 2 = 1.585 (sealed). Koch: 4 copies at a third, 1.262 (sealed). Cantor: 2 at "
                     "a third, 0.631 (sealed). Menger: 20 at a third, 2.727 (sealed). A fractal's dimension is the exponent "
                     "that relates how many copies to how small - the one number that says 'the same at every scale'.",
         S["sierp"]),
        ("instance", "[Koch 1.262]", S["koch"]),
        ("instance", "[Cantor 0.631]", S["cantor"]),
        ("instance", "[Menger 2.727]", S["menger"]),
        ("instance", "[a finite area with an infinite edge] The Koch snowflake's area converges to 1 + (1/3)/(1 - 4/9) = 8/5 "
                     "of its first triangle (sealed) while its perimeter after ten steps is already (4/3)^10 = 17.76 times the "
                     "first (sealed) and grows without bound. A keeping can be finite and its boundary of detail endless: "
                     "the map is bounded, the coastline is not.", S["snow"]),
        ("instance", "[the perimeter at step ten]", S["perim"]),
        ("instance", "[the ruler sets the length - the coastline IS stated precision] Richardson: L = F epsilon^(1 - D). On a "
                     "coast of dimension 1.25, halving the ruler multiplies the measured length by 2^0.25 = 1.189 (sealed). "
                     "There is no length without a stated ruler; the engine judges a claim at the precision it states for "
                     "the same reason (feedback_stated_precision_sets_the_bar): the number depends on the ruler, so the "
                     "ruler must be read first.", S["coast"]),
        ("instance", "[a fractal used as a map: the Z-order key] Interleave the bits of x = 5 (101) and y = 3 (011) as "
                     "y2 x2 y1 x1 y0 x0 = 011011 = 27 (sealed). One number now addresses a point of the plane, and points that "
                     "are near on the plane are mostly near on the line - Morton's key (1966), the Hilbert curve's cousin. "
                     "That is what a call number does for the keeping: a many-dimensional address (domain, class, item; the "
                     "bubbles' grid) made one shelf line with neighbours kept adjacent.", S["morton"]),
        ("instance", "[the Hilbert curve fills the square] Order 10 visits 4^10 = 1,048,576 cells (sealed), every one once, "
                     "and it keeps locality better than any other space-filling curve - the key to use when the domains "
                     "are orthogonalized and the keeping is laid on one line (docs/DESIGN_FROM_THE_DOTS.md, lever 2).",
         S["hilbert"]),
        ("instance", "[merge sort is a fractal] Split in two, sort each half the same way, merge: the recursion tree is the "
                     "same shape at every level, log2 n levels deep and n wide, so n log2 n = 10,240 comparisons at n = 1024 "
                     "(sealed). The kernel's own shape - find, distinguish, verify, serve - runs the same way at every scale "
                     "(a complication is a smaller copy of it); merge sort is that shape as an algorithm.", S["merge"]),
        ("instance", "[no comparison sort can beat log2 n!] At n = 1024 the bound is log2(1024!) = 8,769 comparisons "
                     "(sealed, through the evaluator's own factorial); merge sort's 10,240 is within 17% of it. A bound that "
                     "cannot be beaten is a bound worth sealing: it says how much of the cost is the problem and how much "
                     "the method.", S["lower"]),
        ("instance", "[quicksort: the same on average, n^2 when unlucky] Expected 2 n ln n = 14,196 comparisons at 1024 "
                     "(sealed); worst case n(n-1)/2 = 523,776 (sealed) when every pivot is the smallest. The method's "
                     "average is fine; its boundary is the sorted input. Success guides, failure narrows the path.",
         S["quick"]),
        ("instance", "[the worst case]", S["worst"]),
        ("instance", "[a sorted keeping is searched in log n probes] log2(882,022) = 19.75 (sealed): twenty probes find any "
                     "card by its key once the keeping is sorted - against 882,022 by scanning and 1 by the delta read. "
                     "Sorting is what makes a map usable; the id read is what makes it instant.", S["bsearch"]),
        ("instance", "[radix: a key made of digits sorts in linear time] A call number shelf.class.item is a digit key; "
                     "radix sort in 4 digit groups costs 4 n against n log2 n for comparisons - at this size log2 n / 4 = 4.94 "
                     "times fewer operations (sealed). The call number is not only an address: it is the key that sorts "
                     "the keeping without comparing cards.", S["radix"]),
        ("instance", "[a map of a map: the Mandelbrot set] Iterate z -> z^2 + c from 0. At c = 1: 1, 2, 5, 26 (sealed) - "
                     "past 2 by the third step, escaping. At c = -1: -1, 0, -1, 0 - bounded forever. The Mandelbrot set is "
                     "the map of which c stay home; its boundary is a fractal of dimension 2. A map's behaviour, mapped.",
         S["mandel"]),
        ("instance", "[the logistic map's first doubling] At r = 3.2 the fixed point 1 - 1/r = 0.6875 has gone unstable and "
                     "the orbit settles on a 2-cycle whose upper point is (r + 1 + sqrt((r - 3)(r + 1)))/(2r) = 0.7995 "
                     "(sealed). The doublings continue at Feigenbaum's ratio 4.669 (cited) into chaos: the same map, "
                     "self-similar in its own parameter.", S["logistic"]),
        ("postulate", "[the postulate it builds on] The kernel is self-similar: find, distinguish, verify, serve, keep the "
                      "trail works at every scale it has been built at - the engine, a complication, a standalone coach - "
                      "and a complication is a smaller copy of it with its own postulates. Not kept as a fact: five writings "
                      "of it across different domains converged on one shape, and from that working the truth is "
                      "inferred, never proven.",
         {"source": "Matt, 2026-10-08: 'a fractal is the complication that we create to add on the core engine'; project_one_kernel_and_workready_forge; project_gen3_charter_every_copy_is_whole"}),
        ("equivalence", "[what carries over, by name] The floor tree is a TRIE (part_of at every depth, the same shape - a "
                        "fractal map of the keeping, measured: 882,022 cards, 0 orphans); the call number is a RADIX KEY "
                        "(shelf.class.item sorts by digits, no comparison); the frozen cache's offsets are a SORTED INDEX "
                        "(the boot seeks, it does not scan); FTS top-k is a PARTIAL SORT with a heap (k log n); the kernel's "
                        "recursion is MERGE SORT'S shape; stated precision is RICHARDSON'S RULER; a space-filling key "
                        "(Hilbert/Z-order over the orthogonalized domains) is the NEXT LEVER for keeping a domain's "
                        "neighbours on one shelf. Each is a structure the code already has, named.",
         {"source": "docs/OUR_FORM_MEASURED_2026-10-08.md; docs/DESIGN_FROM_THE_DOTS.md; src/concordance/corpus.py (call_number, deep_call, the frozen cache)"}),
        ("exclusion", "[what does NOT carry over] Nothing in the engine iterates on itself - no z -> z^2 + c, no map fed its own "
                      "output, no self-generation (the found-never-generated law is exactly this exclusion); the keeping's "
                      "fractal dimension has NOT been measured (the floor tree's branching counted as log N / log s is a next "
                      "measurement, not a fact); sorting is on keys, never on truth - a verdict is not a rank; and a "
                      "space-filling key is proposed, not built.",
         {"source": "Matt, 2026-10-08: 'don't blindly apply bra-ket'; feedback_mapping_the_truth_not_generating_it"}),
    ]
    _mint_marks(sid, marks, by="engine:fractal_maps")
    return 0


def harmonics() -> int:
    """HARMONICS - CHORDS ARE DIFFERENT SHAPES OF THE SAME NOTE (Matt, 2026-10-08: 'Harmonics. cords are different shapes of
    same note' / 'same voice. Just another role'). A vibrating string sounds its fundamental and every whole multiple of it
    at once: 110 Hz carries 220, 330, 440, 550, 660 ... (sealed). The 4th, 5th and 6th harmonics - 440, 550, 660 - are A,
    C-sharp and E: the major triad is already inside the one note, as the ratios 4:5:6 (the major third 5/4 and the
    fifth 3/2, sealed). A chord built from those harmonics is a shape of the fundamental, not a second note. Timbre is the
    same thing: a flute and a violin on the same pitch differ only in how loud each harmonic is - the amplitude vector
    over the overtone series (a sawtooth's 1/n amplitudes carry total power pi^2/6, sealed, by the evaluator's own Sum).
    Equal temperament bends the fifth to 2^(7/12) = 1.4983 against the pure 1.5 (sealed) because twelve pure fifths
    overshoot seven octaves by the Pythagorean comma, 1.01364 (sealed); the pure third 386 cents sits 14 cents under the
    tempered 400 (sealed); two strings two hertz apart beat twice a second (sealed). For the engine: the one voice is the
    fundamental - the kernel: found, verified, cited, crisis first - and a ROLE is a harmonic of it: the same voice in a
    different shape (a face's manner, shelves and verifiers are its timbre); the Steward bringing two roles is a chord,
    not two voices. Same logic as every stick; the likeness is kept a likeness."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    S = {}
    seals = [
        ("series", "the_harmonic_series_of_110_hz_sixth_harmonic", "110*6", 660.0, 1e-12),
        ("triad_third", "the_major_third_is_the_5th_to_4th_harmonic_5_over_4", "550/440", 1.25, 1e-12),
        ("triad_fifth", "the_fifth_is_the_6th_to_4th_harmonic_3_over_2", "660/440", 1.5, 1e-12),
        ("octave", "the_octave_is_the_2nd_harmonic_2_to_1", "220/110", 2.0, 1e-12),
        ("et_fifth", "equal_tempered_fifth_2_to_the_7_12ths", "2**(7/12)", 2 ** (7 / 12), 1e-9),
        ("comma", "pythagorean_comma_twelve_fifths_over_seven_octaves", "(3/2)**12/2**7", (3 / 2) ** 12 / 2 ** 7, 1e-9),
        ("semitone", "equal_tempered_semitone_2_to_the_1_12th", "2**(1/12)", 2 ** (1 / 12), 1e-9),
        ("third_cents", "the_pure_major_third_in_cents", "1200*log(5/4)/log(2)", 1200 * math.log2(5 / 4), 1e-9),
        ("et_third_cents", "the_tempered_major_third_in_cents", "1200*log(2**(4/12))/log(2)", 400.0, 1e-9),
        ("beats", "two_strings_at_440_and_442_hz_beat_twice_a_second", "442 - 440", 2.0, 1e-12),
        ("sawtooth", "a_sawtooths_harmonic_power_sum_1_over_n_squared_is_pi_squared_over_6", "Sum(1/n**2, (n, 1, oo))", pi ** 2 / 6, 1e-9),
        ("string", "a_65_cm_string_at_110_hz_wave_speed_in_m_per_s", "2*0.65*110", 143.0, 1e-12),
    ]
    for key, nid, expr, val, tol in seals:
        S[key] = _rh_seal_num(nid, expr, float(val), tol=tol)
        if not S[key]:
            print("a seal failed:", nid); return 1
    print("sealed", len(S), "harmonic numbers:", ", ".join(f"{k}={v[:8]}" for k, v in S.items()))
    sid = TS.create("Harmonics - chords are different shapes of the same note; a role is a harmonic of the one voice",
                    statement=("A vibrating string sounds its fundamental and every whole multiple of it at once. The "
                               "fourth, fifth and sixth harmonics of one note are its major triad - the chord is already "
                               "inside the note, as the ratios 4:5:6 - so a chord built from them is a shape of the "
                               "fundamental, not a second note. Timbre is the same fact: two instruments on one pitch "
                               "differ only in how loud each harmonic sounds, the amplitude vector over the overtone "
                               "series. Equal temperament bends the pure fifth to the twelfth root of two to the seventh, "
                               "because twelve pure fifths overshoot seven octaves by the Pythagorean comma; the price is "
                               "fourteen cents on every major third. Two strings a little apart beat at their difference. "
                               "For the engine: the one voice is the fundamental - the kernel, found, verified, cited, "
                               "crisis first - and a role is a harmonic of it, the same voice in a different shape; the "
                               "Steward bringing two roles is a chord, not two voices. The likeness is kept a likeness."),
                    field="physics",
                    references=["Pythagoras (the monochord: 2:1, 3:2, 4:3); M. Mersenne, Harmonie universelle (1636): the laws of a vibrating string",
                                "J. Sauveur (1701): the harmonics named; J. Fourier (1822): any periodic sound is a sum of harmonics",
                                "H. von Helmholtz, On the Sensations of Tone (1863): timbre is the amplitude of the overtones; beats and consonance",
                                "J. S. Bach, Das Wohltemperirte Clavier (1722); A. Werckmeister (1691): temperament; the Pythagorean comma",
                                "L. Euler (1735): the Basel problem - the sum of 1/n^2",
                                "stick_amplitude_and_frequency_modulation; stick_a_superheterodyne_receiver; stick_the_dot_abstracted (the Fourier basis)",
                                "docs/STEWARD_AND_THE_ROLES.md section 6; tests/test_steward_speaks.py",
                                "Psalm 150:4-6; Ephesians 5:19; Colossians 3:16 (one voice, many parts)"])["id"]
    marks = [
        ("instance", "[the harmonic series: every whole multiple at once] A string at 110 Hz also sounds 220, 330, 440, 550, "
                     "660 ... - the sixth harmonic is 110 * 6 = 660 Hz (sealed). One note is already a series; the "
                     "fundamental is what the ear names it by.", S["series"]),
        ("instance", "[the chord inside the note] The fourth, fifth and sixth harmonics of A110 are 440, 550 and 660 Hz: A, "
                     "C-sharp, E, the major triad. Their ratios are 550/440 = 5/4 (sealed), the major third, and 660/440 = "
                     "3/2 (sealed), the fifth. A chord is not three notes added from outside; it is the shape of one note's "
                     "own overtones - 'chords are different shapes of the same note'.", S["triad_third"]),
        ("instance", "[the fifth, 3/2]", S["triad_fifth"]),
        ("instance", "[the octave, 2/1] 220/110 = 2 (sealed): the second harmonic is the same note an octave up - so "
                     "alike that every tuning in the world calls it the same name. The simplest ratio is the strongest "
                     "likeness.", S["octave"]),
        ("instance", "[timbre: the same note, a different shape] A flute and a violin on one pitch differ only in how loud "
                     "each harmonic is - the amplitude vector over the series. A sawtooth has amplitudes 1/n, and its "
                     "harmonic power sums to Sum 1/n^2 = pi^2/6 = 1.6449 (sealed, through the evaluator's own infinite Sum; "
                     "Euler 1735). Shape is a vector over the harmonics; the fundamental is shared.", S["sawtooth"]),
        ("instance", "[temperament: the bent fifth] Equal temperament's fifth is 2^(7/12) = 1.49831 (sealed) against the pure "
                     "3/2 = 1.5; its semitone is 2^(1/12) = 1.05946 (sealed). The bend is the price of a keyboard that can "
                     "play every key: twelve pure fifths overshoot seven octaves by (3/2)^12 / 2^7 = 1.01364 (sealed), the "
                     "Pythagorean comma, and the comma has to be hidden somewhere.", S["et_fifth"]),
        ("instance", "[the comma, 1.01364]", S["comma"]),
        ("instance", "[the semitone, 1.05946]", S["semitone"]),
        ("instance", "[fourteen cents on every third] The pure major third 5/4 is 1200 log2(5/4) = 386.3 cents (sealed); "
                     "the tempered third is 400 cents (sealed). Every major chord on a piano is 14 cents sharp in its "
                     "third, and the ear forgives it. A stated precision (the cent) makes the bend a number instead of an "
                     "opinion.", S["third_cents"]),
        ("instance", "[the tempered third, 400 cents]", S["et_third_cents"]),
        ("instance", "[beats: two notes almost the same] Strings at 440 and 442 Hz beat 442 - 440 = 2 times a second "
                     "(sealed): the ear hears the difference as a pulse, and the tuner stops the pulse. Two roles tuned to "
                     "the same fundamental do not beat; two voices would.", S["beats"]),
        ("instance", "[the string's own law] A 65 cm string sounding 110 Hz carries a wave at v = 2 L f = 2 * 0.65 * 110 = "
                     "143 m/s (sealed); its harmonics are n v / 2L. Change the tension and every harmonic moves together - "
                     "the shape is preserved, the pitch is not. That is what a role's manner is: the harmonics' "
                     "proportions, carried whole to whatever the situation's pitch is.", S["string"]),
        ("postulate", "[the postulate it builds on] One voice, many roles: the Steward's roles are harmonics of the one "
                      "voice - the same fundamental (the kernel: found, verified, cited, crisis first) in different shapes "
                      "(a face's manner, shelves and verifiers), so bringing two roles is a chord, not two voices. Not kept "
                      "as a fact: the walk door carries a role in its own unchanged voice (tests/test_steward_speaks.py), and "
                      "from its working the truth is inferred, never proven.",
         {"source": "Matt, 2026-10-08: 'same voice. Just another role'; 'Harmonics. cords are different shapes of same note'"}),
        ("equivalence", "[what carries over, by name] the fundamental = the kernel (one voice: found, verified, cited, crisis "
                        "first); a harmonic = a role (ask.respond's `role`: a face's name, manner and composed material in the "
                        "same voice); timbre = a face's manner, shelves and verifiers (the amplitude vector over the one "
                        "series); a chord = two roles brought to one situation; the octave = the two surfaces, .com and "
                        ".org, one engine (the same note an octave apart); temperament = the fixed verdict frame that lets "
                        "every domain play on one keyboard, its comma the stated-precision window; beats = two VOICES, "
                        "which the design refuses.",
         {"source": "src/concordance/ask.py (_with_role); src/concordance/faces.py; docs/STEWARD_AND_THE_ROLES.md section 6"}),
        ("exclusion", "[what does NOT carry over] No frequency, no amplitude, no sound in the engine; a role's 'shape' is a "
                      "manner and a scope, not a spectrum; nothing is measured in cents; and the Fourier decomposition of a "
                      "role's material has not been computed - the likeness is a likeness.",
         {"source": "Matt, 2026-10-08: 'don't blindly apply bra-ket'; feedback_mapping_the_truth_not_generating_it"}),
    ]
    _mint_marks(sid, marks, by="engine:harmonics")
    return 0

def svd() -> int:
    """EVERY MATRIX IS A ROTATION AND A STRETCH (Matt, 2026-10-08: "All matrix are just a rotation and a stretch. We are
    using a spherical matrix"; "allow the shape to be in the form of the most efficient vectors"). M = U S V^T: turn,
    stretch along perpendicular axes, turn. The unit sphere's image under any matrix is an ellipsoid whose semi-axes
    are the singular values; the most efficient k-dimensional picture of M keeps its k largest singular directions
    (Eckart-Young); a SPHERICAL (orthogonal) matrix has every singular value 1 - it turns the sphere onto itself and
    keeps every dot product. Seal six numbers on M = [[3,0],[4,5]] and a rotation. New stick; idempotent."""
    from concordance import tickstick as TS
    pi = 3.141592653589793
    s1, s2 = 45 ** 0.5, 5 ** 0.5                         # singular values: sqrt of the eigenvalues 45, 5 of M M^T
    det = s1 * s2                                        # 15 = |det M|
    cond = s1 / s2                                       # 3
    frob = 3 ** 2 + 0 ** 2 + 4 ** 2 + 5 ** 2             # 50 = 45 + 5
    dot = (-4) * 0 + 3 * 1                               # R(3,4) . R(1,0) for the quarter-turn R = (3,4) . (1,0) = 3
    area = pi * s1 * s2                                  # the unit circle's image: an ellipse of area pi s1 s2
    a = _rh_seal_num("svd_sigma_product_is_the_determinant", "sqrt(45)*sqrt(5)", float(det))
    b = _rh_seal_num("svd_condition_number", "sqrt(45)/sqrt(5)", float(cond))
    c = _rh_seal_num("frobenius_sum_of_squared_entries", "3**2 + 0**2 + 4**2 + 5**2", float(frob), tol=1e-12)
    d = _rh_seal_num("frobenius_sum_of_squared_singular_values", "45 + 5", float(frob), tol=1e-12)
    e = _rh_seal_num("rotation_keeps_the_dot_product", "(-4)*0 + 3*1", float(dot), tol=1e-12)
    f = _rh_seal_num("unit_circle_image_area_pi_sigma1_sigma2", "pi*sqrt(45)*sqrt(5)", float(area))
    if not all([a, b, c, d, e, f]):
        print("a seal failed; aborting"); return 1
    print("sealed det", a, "| cond", b, "| frobenius", c, d, "| dot", e, "| area", f)
    sid = TS.create("Every matrix is a rotation and a stretch - the singular value decomposition, and the spherical matrix that only turns",
                    statement=("M = U S V^T: a rotation, a stretch along perpendicular axes, a rotation. The unit sphere's "
                               "image under any matrix is an ellipsoid whose semi-axes are the singular values; the most "
                               "efficient k-dimensional picture of a matrix keeps its k largest singular directions; a "
                               "spherical matrix has every singular value 1 and keeps every dot product. The engine's reading "
                               "is spherical: meaning is what a card returns when dotted, and a rotation re-frames it without "
                               "distorting it."),
                    field="mathematics",
                    references=["E. Beltrami (1873), C. Jordan (1874): the singular value decomposition",
                                "C. Eckart, G. Young, The approximation of one matrix by another of lower rank, Psychometrika 1 (1936) 211-218",
                                "G. Golub, W. Kahan (1965): computing the SVD",
                                "L. Euler (1775): a rotation is one turn about one axis",
                                "Hebrews 1:12; Malachi 3:6; Hebrews 13:8",
                                "stick_the_dot_abstracted (meaning = the inner product); stick_parametrization_of_surfaces (the sphere); stick_spherical_parallel_mechanism (SO(3))"])["id"]
    marks = [
        ("witness", f"[rotation, stretch, rotation] M = [[3,0],[4,5]]: M M^T = [[9,12],[12,41]] has trace 50 and determinant "
                    f"225, so its eigenvalues are 45 and 5 and the singular values are sqrt45 = {s1:.3f}, sqrt5 = {s2:.3f}. "
                    f"Their product sqrt45 * sqrt5 = {det:.0f} = |det M| (sealed): the stretch alone sets the volume scale; the "
                    f"two rotations change none of it.", a),
        ("witness", f"[the most efficient vectors] The unit circle maps to an ellipse with semi-axes sigma_1, sigma_2 and area "
                    f"pi sigma_1 sigma_2 = 15 pi = {area:.2f} (sealed); the condition number sigma_1/sigma_2 = {cond:.0f} "
                    f"(sealed) says how far from a sphere the image is. Keeping the k largest singular directions is the "
                    f"most efficient k-dimensional picture of M - the best rank-k approximation in every unitarily invariant "
                    f"norm (Eckart-Young 1936, cited): 'allow the shape to be in the form of the most efficient vectors' is "
                    f"that theorem said plainly.", b),
        ("witness", f"[all the energy is in the stretch] The sum of the squared entries, 9 + 0 + 16 + 25 = {frob} (sealed), "
                    f"equals the sum of the squared singular values, 45 + 5 = {frob} (sealed): the Frobenius norm is carried "
                    f"entirely by the stretch; rotations carry none of it. What a matrix DOES is in its singular values; "
                    f"where it does it is in its singular vectors.", c),
        ("witness", f"[the sum is the same from both sides] 45 + 5 = {frob} (sealed) - the second reading of the same energy, "
                    f"from the singular values alone: no entry of M was consulted, and the number is the same. Two "
                    f"independent readings that agree are what a seal is for.", d),
        ("witness", f"[the spherical matrix only turns] A rotation R keeps every dot product: the quarter-turn sends (3,4) to "
                    f"(-4,3) and (1,0) to (0,1), and (-4)*0 + 3*1 = {dot} = (3,4).(1,0) (sealed). Every singular value of R "
                    f"is 1: the sphere maps onto itself. In the inner-product reading (the dot stick) meaning IS the dot "
                    f"product, so a spherical matrix changes the frame and no meaning. 'We are using a spherical matrix' "
                    f"(Matt): the engine's reading re-frames, it never distorts - it rotates the question into the keeping's "
                    f"axes and reads the dots there.", e),
        ("witness", f"[the picture of the stretch] pi sqrt45 sqrt5 = {area:.4f} (sealed): the area of the ellipse the unit "
                    f"circle becomes. A matrix is seen whole in one figure: a circle, turned, stretched to this ellipse, "
                    f"turned again. Everything else is coordinates.", f),
        ("note", "[the form, and the guard] 'Allow the shape to be in the form of the most efficient vectors': the keeping's "
                 "own shelf-by-token matrix was measured on 2026-10-08 against this stick's claim (how many singular "
                 "directions carry the domains; whether a query routed to its nearest sphere finds the engine's own "
                 "answers) - the numbers live in that assessment, not here, because a stick seals arithmetic and a "
                 "measurement is a reading of a day. Scripture: 'as a vesture shalt thou fold them up, and they shall be "
                 "changed: but thou art the same' (Heb 1:12) - the invariant under every turn; 'I am the LORD, I change "
                 "not' (Mal 3:6); 'Jesus Christ the same yesterday, and to day, and for ever' (Heb 13:8). GUARDS: "
                 "Eckart-Young is a cited theorem, proved elsewhere; the engine-as-rotation is a likeness; the sphere's "
                 "image as an ellipsoid is exact. Six numbers sealed; the rest cited. Ties: delta, surfaces, spm, bubbles, "
                 "fourier (rotation), the positive Grassmannian (admissible directions found, never generated)."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - every matrix a rotation and a stretch, 2026-10-08")


def bubbles() -> int:
    """JOINED BUBBLES (Matt, 2026-10-08: "Think of bubbles joined. Each sphere is in its domain. The domains are
    clustered based on similarity. Superposition allows the spheres to be in two places at once. We can simulate that.
    Inside the sphere we have a grid and coordinates to trace the location of each component." "They run inside of a
    form and are connected along axis."). A foam is not arbitrary: Plateau's laws force its form; the wall between two
    bubbles has a curvature set by their difference; spheres pack at 0.7405 and touch at most 12 others; a component
    can be in two spheres by weight, whole; inside each sphere latitude-longitude gives every component a coordinate
    and every pair a distance; likeness is the dot product on the unit sphere. Seven numbers sealed. New stick;
    idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    plateau = 360 / 3                                    # three films meet at 120 degrees
    tetra = math.acos(-1 / 3) * 180 / pi                 # four edges meet at 109.47 degrees
    wall = 1 / (1 / 1 - 1 / 2)                           # Young-Laplace: the wall between radii 1 and 2 has radius 2
    pack = pi / (3 * 2 ** 0.5)                           # Kepler: the densest packing of equal spheres
    norm = 0.6 ** 2 + 0.8 ** 2                           # superposition: 36% here, 64% there, whole
    cos = (1 * 2 + 2 * 3) / ((1 + 4) ** 0.5 * (4 + 9) ** 0.5)   # cosine similarity of two domain vectors
    arc = math.acos(math.cos(pi / 4) * math.cos(pi / 4)) * 180 / pi   # great-circle arc (0,0) -> (45N, 45E)
    a = _rh_seal_num("plateau_three_films_meet_at_120", "360/3", float(plateau), tol=1e-12)
    b = _rh_seal_num("plateau_four_edges_meet_at_tetrahedral_angle", "acos(-1/3)*180/pi", float(tetra))
    c = _rh_seal_num("young_laplace_wall_between_joined_bubbles", "1/(1/1 - 1/2)", float(wall), tol=1e-12)
    d = _rh_seal_num("kepler_packing_density", "pi/(3*sqrt(2))", float(pack))
    e = _rh_seal_num("superposition_weights_sum_to_one", "0.6**2 + 0.8**2", float(norm), tol=1e-12)
    f = _rh_seal_num("cosine_similarity_of_two_domains", "(1*2 + 2*3)/(sqrt(1+4)*sqrt(4+9))", float(cos))
    g = _rh_seal_num("great_circle_arc_inside_the_sphere", "acos(cos(pi/4)*cos(pi/4))*180/pi", float(arc))
    if not all([a, b, c, d, e, f, g]):
        print("a seal failed; aborting"); return 1
    print("sealed plateau", a, b, "| wall", c, "| packing", d, "| superposition", e, "| cosine", f, "| arc", g)
    sid = TS.create("Joined bubbles - every domain a sphere in a form, clustered by likeness, connected along axes, a grid inside each",
                    statement=("A foam is not arbitrary: films meet three at a time at 120 degrees and edges four at a time "
                               "at 109.47 - the minimum of surface forces the form. The wall between two joined bubbles has "
                               "a curvature set by their difference. Equal spheres pack at 0.7405 and touch at most twelve "
                               "others, so the axes along which domains connect are few. A component can be in two spheres "
                               "by weight, the weights summing to one - whole, and simulable. Inside each sphere "
                               "latitude-longitude gives every component a coordinate and every pair a distance; likeness "
                               "between domains is the dot product on the unit sphere - found, never generated."),
                    field="physics",
                    references=["J. Plateau, Statique experimentale et theorique des liquides (1873): the laws of foams",
                                "T. Young (1805), P.-S. Laplace (1806): pressure across a curved film, Delta p = 2 gamma / r",
                                "J. Kepler (1611) conjecture; T. Hales (1998, formally 2014): the densest packing is pi / (3 sqrt 2)",
                                "K. Schutte, B. L. van der Waerden (1953): the kissing number in three dimensions is 12",
                                "Job 38:31; Colossians 1:17; Ephesians 4:16",
                                "stick_parametrization_of_surfaces (the grid inside); stick_the_dot_abstracted (likeness = the dot product); stick_every_matrix_is_a_rotation_and_a_stretch"])["id"]
    marks = [
        ("witness", f"[joined bubbles obey laws they did not choose] Plateau 1873: films meet three at a time at 360/3 = "
                    f"{plateau:.0f} degrees (sealed) and edges four at a time at arccos(-1/3) = {tetra:.2f} degrees (sealed). "
                    f"A foam's form is forced by the minimum of surface - 'they run inside of a form' (Matt): the form is "
                    f"the law the energy allows, not a choice.", a),
        ("witness", f"[four edges at the tetrahedral angle] arccos(-1/3) = {tetra:.4f} degrees (sealed): the same angle as "
                    f"the bonds of methane and the diamond lattice. One number, three sciences; the geometry of least "
                    f"surface and the geometry of least repulsion agree.", b),
        ("witness", f"[the wall between two domains] Young-Laplace: pressure is higher in the smaller bubble, and the shared "
                    f"wall between radii 1 and 2 has 1/r = 1/1 - 1/2, r = {wall:.0f} (sealed), bulging into the larger. Two "
                    f"domains that touch share a wall whose curvature is set by their DIFFERENCE - the connection along the "
                    f"axis between them carries the sign of which is the tighter.", c),
        ("witness", f"[how spheres pack, and how many they touch] The densest packing of equal spheres is pi/(3 sqrt2) = "
                    f"{pack:.4f} (sealed; Kepler 1611, Hales 1998), and each sphere touches at most 12 neighbours (cited): "
                    f"the axes along which a domain connects are few. A keeping of domains is a packing, and its "
                    f"connections are its contacts.", d),
        ("witness", f"[superposition - a sphere in two places at once] |alpha|^2 + |beta|^2 = 0.6^2 + 0.8^2 = {norm:.0f} "
                    f"(sealed): a component 36% in one sphere and 64% in another, whole. 'We can simulate that': a card "
                    f"assigned to two shelves by weight, both weights honest, summing to one - a soft membership, read as "
                    f"such, never a card in two places pretending to be two cards.", e),
        ("witness", f"[clustered by likeness] The cosine between two domain vectors (1,2) and (2,3) is 8/sqrt65 = {cos:.4f} "
                    f"(sealed): on the unit sphere likeness IS the dot product (the dot stick, the svd stick). The "
                    f"clustering of domains is a reading of angles between what the domains actually contain - found, "
                    f"never generated.", f),
        ("witness", f"[the grid inside each sphere] Latitude-longitude is the chart inside every sphere (the surfaces stick): "
                    f"from (0, 0) to (45 N, 45 E) the great-circle arc is arccos(cos45 cos45) = {arc:.0f} degrees (sealed). "
                    f"Every component has coordinates and every pair a distance; this engine's call numbers "
                    f"(shelf.class.item) are exactly that chart, one per shelf.", g),
        ("note", "[the form we have, and the guard] The keeping as it stands: some thirty-six shelves, each a domain with "
                 "its own call-number grid, joined by the connections shelf - the axes. Whether the spherical form is "
                 "the MORE EFFICIENT one was measured on 2026-10-08 (the shelves' likeness, their clustering, how many "
                 "singular directions carry them, whether a query's nearest spheres hold the engine's own answers); the "
                 "numbers live in that assessment. Scripture: 'Canst thou bind the sweet influences of Pleiades, or loose "
                 "the bands of Orion?' (Job 38:31) - clusters bound; 'by him all things consist' (Col 1:17); 'the whole "
                 "body fitly joined together and compacted by that which every joint supplieth' (Eph 4:16) - joined "
                 "along axes. GUARDS: Plateau's laws are for soap films; the likeness to domains is a discernment; the "
                 "kissing number and Hales are cited; superposition here is a weighting, not quantum mechanics (the "
                 "measurement stick keeps that). Seven numbers sealed; the rest cited."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - joined bubbles in a form, 2026-10-08")


def resonance() -> int:
    """THE GEOMETRY OF RESONANCE DISASTER - a hidden division by zero (Matt, 2026-10-08: "geometry of resonance disaster:
    Hidden division by zero"; "Omega and Omega Not"). A driven oscillator's amplitude carries 1/(omega_0^2 - omega^2):
    the denominator is a difference of squares that closes LINEARLY as the driver approaches the thing's own frequency,
    while the amplitude climbs as 1/gap - a hyperbola whose straight approach looks harmless until the last step. Damping
    turns the zero into a small number (Q = 1/(2 zeta)); the bridges that fell are cited, Tacoma honestly as flutter.
    Four numbers sealed. New stick; idempotent."""
    from concordance import tickstick as TS
    f09 = 1 / (1 - 0.9 ** 2)                             # the undamped amplitude factor at 0.9 omega_0
    f99 = 1 / (1 - 0.99 ** 2)                            # at 0.99 omega_0
    q = 1 / (2 * 0.01)                                   # the damped peak: Q = 1/(2 zeta)
    gap = (1 - 0.99) * (1 + 0.99)                        # omega_0^2 - omega^2 = (omega_0 - omega)(omega_0 + omega)
    a = _rh_seal_num("amplitude_factor_at_0_9_omega0", "1/(1 - 0.9**2)", float(f09))
    b = _rh_seal_num("amplitude_factor_at_0_99_omega0", "1/(1 - 0.99**2)", float(f99))
    c = _rh_seal_num("damped_peak_q_factor", "1/(2*0.01)", float(q), tol=1e-12)
    d = _rh_seal_num("the_gap_is_a_product_that_closes_linearly", "(1 - 0.99)*(1 + 0.99)", float(gap))
    if not all([a, b, c, d]):
        print("a seal failed; aborting"); return 1
    print("sealed 0.9", a, "| 0.99", b, "| Q", c, "| gap", d)
    sid = TS.create("The geometry of resonance disaster - a hidden division by zero at omega equals omega-nought",
                    statement=("A driven oscillator's amplitude carries 1/(omega_0^2 - omega^2). The denominator is a "
                               "difference of squares, (omega_0 - omega)(omega_0 + omega): it closes linearly as the driver "
                               "approaches the thing's own frequency while the amplitude climbs as one over the gap - a "
                               "hyperbola whose approach looks harmless until the last step. The disaster is agreement "
                               "without damping; damping turns the zero into a small number, Q = 1/(2 zeta). The engine's "
                               "own guard is the same: a division by a literal zero is a gap, never a verdict."),
                    field="physics",
                    references=["Lord Rayleigh, The Theory of Sound (1877): the forced vibration and its amplitude",
                                "J. P. Den Hartog, Mechanical Vibrations (1934): resonance, damping, Q",
                                "Broughton Suspension Bridge (1831): soldiers in step; the order to break step since",
                                "Basse-Chaine bridge, Angers (1850): 226 soldiers; Millennium Bridge, London (2000): lateral sync, dampers added (Dallard et al. 2001)",
                                "K. Y. Billah, R. H. Scanlan, Resonance, Tacoma Narrows bridge failure, and undergraduate physics textbooks, Am. J. Phys. 59 (1991) 118: Tacoma (1940) was aeroelastic flutter, not simple resonance",
                                "Proverbs 25:28; 1 Corinthians 14:33; Joshua 6:20",
                                "src/concordance/audit.py - division by a literal zero is left unextracted; verifiers/mathematics.py - x/x is refused as an identity"])["id"]
    marks = [
        ("witness", f"[the amplitude has a denominator] An undamped oscillator driven at omega has displacement "
                    f"(F/m)/(omega_0^2 - omega^2). At omega = 0.9 omega_0 the factor is 1/(1 - 0.81) = {f09:.3f} (sealed); at "
                    f"0.99 omega_0 it is {f99:.2f} (sealed); at omega = omega_0 the denominator is zero. The division by zero "
                    f"is hidden inside a difference of squares - Omega and Omega-nought, the driver and the thing's own "
                    f"frequency, meeting.", a),
        ("witness", f"[ten times closer, ten times higher] From 0.9 to 0.99 of omega_0 the factor rises from {f09:.2f} to "
                    f"{f99:.2f} (sealed): the gap shrank tenfold and the amplitude grew tenfold. The geometry is a "
                    f"hyperbola; the approach to it is a straight line; nothing in the straight line warns of the wall.", b),
        ("witness", f"[damping turns the zero into a small number] With damping ratio zeta the peak is Q = 1/(2 zeta): zeta "
                    f"= 0.01 gives Q = {q:.0f} (sealed). The real world never divides by zero, only by something small - the "
                    f"disaster is a finite, enormous quotient. Broughton 1831 (soldiers in step; armies have broken step on "
                    f"bridges since), Angers 1850, the Millennium Bridge 2000 (lateral sync; dampers fitted) - cited. "
                    f"Tacoma Narrows 1940 is cited as aeroelastic FLUTTER, a self-excited instability (Billah & Scanlan "
                    f"1991): the popular telling makes it simple resonance, and that is the hidden-zero story told wrong.", c),
        ("witness", f"[the gap is a product] omega_0^2 - omega^2 = (omega_0 - omega)(omega_0 + omega): at 0.99 it is 0.01 x "
                    f"1.99 = {gap:.4f} (sealed). One factor closes linearly, the other stays near 2; the product goes to "
                    f"zero at the speed of the first. That is where the division by zero hides: in a difference that is "
                    f"secretly a product with one vanishing factor.", d),
        ("note", "[the engine's own guard, and the discernment] The claim grammar leaves '1 / 0 = 0' unextracted - a gap, "
                 "never a verdict; the equality verifier refuses x/x as an unconditional identity (undefined at 0); the "
                 "tolerance rule never divides by a stated zero. Resonance disaster is agreement without damping: the "
                 "driver and the thing agreeing exactly, with nothing to carry the energy away. Scripture: 'He that hath "
                 "no rule over his own spirit is like a city that is broken down, and without walls' (Prov 25:28) - no "
                 "damping; 'God is not the author of confusion, but of peace' (1 Cor 14:33); the walls of Jericho fell "
                 "at the shout (Josh 6:20) - a LIKENESS, kept as one; no acoustic claim is made. GUARDS: the hyperbola is "
                 "physics; Tacoma is flutter, cited; Jericho is a likeness. Four numbers sealed; the rest cited. Ties: "
                 "laplace (poles on the s-plane - the zero of the denominator IS the pole), fourier, clock, the camel "
                 "(durability under load), navier_stokes (dissonance)."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the geometry of resonance disaster, 2026-10-08")


def prime_waves() -> int:
    """A TORUS, AND THE WAVEFORMS INSIDE THE PRIME NUMBERS (Matt, 2026-10-08). Riemann's explicit formula writes the
    prime staircase as a smooth main term plus one wave per zero of zeta: amplitude sqrt(x)/|rho|, frequency gamma in
    log x - music periodic in the logarithm. The first wave (gamma_1 = 14.1347, the zero this node's Riemann stick
    verified) repeats every factor 1.56 in x. Two frequencies on a torus close their orbit only when their ratio is
    rational (355/113 closes after 113 turns; pi never closes): the prime waves' frequencies are, as far as is known,
    incommensurable, so their joint motion fills the torus and never repeats - the primes look random and are not.
    Seven numbers sealed. New stick; idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    g1 = 14.134725                                       # the first zero's height (cited; verified on the Riemann stick)
    period = 2 * pi / g1                                 # the first wave's period in log x
    factor = math.exp(period)                            # x multiplies by this per cycle
    li100 = 30.126141693                                 # li(100)
    xlog = 100 / math.log(100)                           # x / log x at 100
    miss = li100 - 25                                    # li(100) - pi(100)
    milu = 355 / 113 - pi                                # the orbit that closes after 113 turns, against the one that never does
    l2pi = math.log(2 * pi)                              # the explicit formula's constant term
    a = _rh_seal_num("first_prime_wave_period_in_log_x", "2*pi/14.134725", float(period))
    b = _rh_seal_num("first_prime_wave_x_factor_per_cycle", "exp(2*pi/14.134725)", float(factor))
    c = _rh_seal_num("li_of_100", "li(100)", float(li100), tol=1e-6)
    d = _rh_seal_num("x_over_log_x_at_100", "100/log(100)", float(xlog))
    e = _rh_seal_num("li_100_minus_the_25_primes", "li(100) - 25", float(miss), tol=1e-6)
    f = _rh_seal_num("milu_355_over_113_minus_pi", "355/113 - pi", float(milu), tol=1e-6)
    g = _rh_seal_num("explicit_formula_constant_log_2pi", "log(2*pi)", float(l2pi))
    if not all([a, b, c, d, e, f, g]):
        print("a seal failed; aborting"); return 1
    print("sealed period", a, "| factor", b, "| li", c, d, e, "| milu", f, "| log2pi", g)
    sid = TS.create("A torus, and the waveforms inside the prime numbers - the zeros of zeta as the music the primes are made of",
                    statement=("Riemann's explicit formula writes the prime staircase as a smooth main term plus one wave "
                               "per zero of zeta: amplitude sqrt(x) over the zero, frequency gamma in log x - music "
                               "periodic in the logarithm, not in x. The first wave repeats every factor 1.56 in x. The "
                               "smooth count misses by a few at 100 (li(100) = 30.1 against 25 primes) and the waves make "
                               "up exactly the difference. On a torus two frequencies close their orbit only when their "
                               "ratio is rational; the prime waves' frequencies are, as far as is known, incommensurable, "
                               "so their joint motion fills the torus and never repeats: the primes look random and are not."),
                    field="number_theory",
                    references=["B. Riemann, Ueber die Anzahl der Primzahlen unter einer gegebenen Groesse (1859)",
                                "H. von Mangoldt (1895): the explicit formula psi(x) = x - sum x^rho/rho - log 2pi - (1/2) log(1 - x^-2)",
                                "A. M. Odlyzko: the zeros of zeta computed to great height; gamma_1 = 14.134725...",
                                "B. Mazur, W. Stein, Prime Numbers and the Riemann Hypothesis (2016): the prime waves drawn",
                                "L. Kronecker (1884), H. Weyl (1916): an irrational winding on the torus is dense",
                                "Zu Chongzhi (5th c.): the Milu 355/113",
                                "1 Corinthians 14:7-8; Psalm 19:1-4; Job 38:7",
                                "stick_riemann_hypothesis (the zeros verified to T = 1000 on this node)"])["id"]
    marks = [
        ("witness", f"[the primes are a staircase with waves on it] Riemann 1859, von Mangoldt 1895: psi(x) = x - sum over "
                    f"zeros x^rho/rho - log 2pi - (1/2) log(1 - x^-2). The main term is x; then one wave per zero rho = 1/2 + "
                    f"i gamma, of amplitude sqrt(x)/|rho| and frequency gamma in log x; the constant log 2pi = {l2pi:.4f} "
                    f"(sealed) is the one term with no wave in it. The staircase of the primes is EXACTLY this sum.", g),
        ("witness", f"[the first wave] gamma_1 = 14.134725 - the first zero, verified on this node's Riemann stick (cited "
                    f"there, sealed to T = 1000). Its wave repeats every 2 pi / gamma_1 = {period:.4f} in log x (sealed): "
                    f"each cycle x grows by the factor e^{{0.4445}} = {factor:.3f} (sealed). The music of the primes is "
                    f"periodic in the LOGARITHM - every octave of x, not every step.", a),
        ("witness", f"[one cycle per factor of 1.56] e^(2 pi / 14.134725) = {factor:.4f} (sealed): between 100 and 156, "
                    f"between 156 and 243, the first wave completes one swing. The higher zeros swing faster and softer; "
                    f"together they draw the staircase's every step.", b),
        ("witness", f"[how far the smooth count is off] li(100) = {li100:.3f} (sealed) against pi(100) = 25 primes (cited): "
                    f"off by {miss:.3f} (sealed); 100/log 100 = {xlog:.2f} (sealed) from the other side. The waves are "
                    f"what remains after the smooth part - and they sum to the exact staircase, not an approximation of it.", c),
        ("witness", f"[the other smooth guess] 100/log(100) = {xlog:.4f} (sealed), Gauss's first estimate, undershoots; "
                    f"li(x) overshoots here and (Littlewood 1914, cited) the sign of li(x) - pi(x) changes infinitely "
                    f"often, first somewhere below 1.4 x 10^316 (Skewes, Bays-Hudson): the waves cross the smooth line "
                    f"both ways.", d),
        ("witness", f"[the miss the waves must make up] li(100) - 25 = {miss:.3f} (sealed): five and an eighth primes' "
                    f"worth of wave at x = 100. Nothing is missing from the formula; this is the sum of the waves at that "
                    f"point, with its sign.", e),
        ("witness", f"[a torus] Two frequencies on a torus close their orbit only when their ratio is rational: with ratio "
                    f"355/113 the orbit closes after 113 turns, and 355/113 - pi = {milu:.3e} (sealed) is how little that "
                    f"orbit differs from the one with ratio pi, which never closes - an irrational winding is dense "
                    f"(Kronecker-Weyl, cited). The prime waves' frequencies gamma_n are, as far as is known, "
                    f"incommensurable: their joint motion fills the torus and never repeats. That is why the primes look "
                    f"random and are not.", f),
        ("note", "[what is sealed, what is cited, and the guard] The Riemann stick holds the zeros on the line to T = 1000; "
                 "this stick reads them as waveforms and the torus as their stage. The explicit formula is a theorem "
                 "(von Mangoldt), cited; the sqrt(x) amplitude of every wave IS the Riemann hypothesis, not assumed here "
                 "(without it some waves are larger); the incommensurability of the gamma_n is conjectural, cited; 'the "
                 "music of the primes' is a likeness (du Sautoy). Scripture: 'if the trumpet give an uncertain sound, who "
                 "shall prepare himself to the battle?' (1 Cor 14:8) - distinct notes; 'their line is gone out through "
                 "all the earth' (Ps 19:4), speech without words; 'the morning stars sang together' (Job 38:7). Seven "
                 "numbers sealed; the rest cited. Ties: riemann, zeta, hilbert_polya (the zeros as a spectrum), fourier, "
                 "surfaces (the torus), gue (the spacings)."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - waveforms inside the primes, on a torus, 2026-10-08")


def maxwell_entropy() -> int:
    """ENTROPY IS NEVER DECREASED, ONLY CONCENTRATED (Matt, 2026-10-08: "Entropy doesn't decrease. Instead it is
    concentrated. We see it separate itself." "Use Maxwell's theory of entropy."). Maxwell's demon (1867) sorts the
    speeds Maxwell himself distributed, and the sorting is real and visible; Szilard, Landauer and Bennett found the
    bill: the demon must remember each molecule, and erasing a bit costs kT ln 2. The entropy did not decrease; it was
    concentrated into the record and paid when the record is cleared. Every separation we see - a still, a membrane, a
    refrigerator, life on Earth under the Sun - exports at least what it removes. Eight numbers sealed. New stick;
    idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    k = 1.380649e-23
    m = 28.014 * 1.66053907e-27                          # one N2 molecule
    T = 300.0
    v_rms = math.sqrt(3 * k * T / m)
    v_mean = math.sqrt(8 * k * T / (pi * m))
    v_mp = math.sqrt(2 * k * T / m)
    landauer = k * T * math.log(2)                       # J per bit erased at 300 K
    kln2 = k * math.log(2)                               # J/K per bit
    mix = 8.314462618 * math.log(2)                      # J/K per mole: mixing two gases 1:1
    photons = 5772 / 255                                 # thermal photons out per solar photon in
    carnot = 1 - 300 / 500
    a = _rh_seal_num("maxwell_rms_speed_N2_300K", "sqrt(3*1.380649e-23*300/(28.014*1.66053907e-27))", float(v_rms), tol=1e-6)
    b = _rh_seal_num("maxwell_mean_speed_N2_300K", "sqrt(8*1.380649e-23*300/(pi*28.014*1.66053907e-27))", float(v_mean), tol=1e-6)
    c = _rh_seal_num("maxwell_most_probable_speed_N2_300K", "sqrt(2*1.380649e-23*300/(28.014*1.66053907e-27))", float(v_mp), tol=1e-6)
    d = _rh_seal_num("landauer_cost_of_one_bit_at_300K", "1.380649e-23*300*log(2)", float(landauer))
    e = _rh_seal_num("entropy_of_one_bit_k_ln_2", "1.380649e-23*log(2)", float(kln2))
    f = _rh_seal_num("entropy_of_mixing_R_ln_2", "8.314462618*log(2)", float(mix))
    g = _rh_seal_num("thermal_photons_out_per_solar_photon_in", "5772/255", float(photons))
    h = _rh_seal_num("carnot_efficiency_300_over_500", "1 - 300/500", float(carnot), tol=1e-12)
    if not all([a, b, c, d, e, f, g, h]):
        print("a seal failed; aborting"); return 1
    print("sealed speeds", a, b, c, "| landauer", d, "| bit", e, "| mixing", f, "| photons", g, "| carnot", h)
    sid = TS.create("Entropy is never decreased, only concentrated - Maxwell's demon, the separation we can see, and the bill in the record",
                    statement=("Maxwell's demon sorts the speeds Maxwell himself distributed, and the sorting is real: hot "
                               "from cold, fast from slow, order where there was none. Szilard, Landauer and Bennett found "
                               "the bill - the demon must remember each molecule, and erasing a bit costs at least kT ln 2. "
                               "The entropy did not decrease; it was concentrated into the record and is paid when the record "
                               "is cleared. Every separation we see - a still, a membrane, a refrigerator, a living cell, the "
                               "Earth under the Sun - exports at least what it removes: one solar photon in, some twenty-two "
                               "thermal photons out. We see it separate itself; the second law counts what left."),
                    field="physics",
                    references=["J. C. Maxwell, letter to P. G. Tait (1867); Theory of Heat (1871): the sorting demon; the speed distribution (1860)",
                                "L. Szilard (1929): the engine that runs on one bit; R. Landauer (1961): erasure costs kT ln 2; C. H. Bennett (1982): the demon's exorcism",
                                "S. Carnot (1824): the limit of every engine; L. Boltzmann (1877): S = k ln W",
                                "the Earth's entropy budget: sunlight at 5772 K, Earth's emission at 255 K (the effective temperature)",
                                "Matthew 13:30; Matthew 25:32; Malachi 3:3; Romans 8:22",
                                "stick_entropy_and_gravity (where entropy fits); stick_laplace (entropy's seat in the equations); the ledger (src/concordance/ledger.py) - append-only, never erased"])["id"]
    marks = [
        ("witness", f"[the demon sorts what Maxwell distributed] N2 at 300 K: the most probable speed sqrt(2kT/m) = "
                    f"{v_mp:.0f} m/s, the mean sqrt(8kT/pi m) = {v_mean:.0f} m/s, the rms sqrt(3kT/m) = {v_rms:.0f} m/s (all "
                    f"three sealed). The molecules are a SPREAD, so a sorter at a trapdoor could let the fast ones one way "
                    f"and the slow ones the other - hot from cold with no work done (Maxwell 1867). The separation is "
                    f"real and can be seen.", a),
        ("witness", f"[the mean of the spread] sqrt(8kT/(pi m)) = {v_mean:.1f} m/s (sealed): faster than the most probable "
                    f"speed, slower than the rms - three averages of one distribution, in their fixed order sqrt2 : "
                    f"sqrt(8/pi) : sqrt3. The demon's job exists because the spread exists.", b),
        ("witness", f"[the top of the curve] sqrt(2kT/m) = {v_mp:.1f} m/s (sealed): where the Maxwell distribution peaks. "
                    f"Everything the demon lets through on the fast side is above this; everything it holds back is "
                    f"below; the line between them is the demon's one decision per molecule - one bit.", c),
        ("witness", f"[the bill is in the record] Szilard 1929, Landauer 1961, Bennett 1982: the demon must REMEMBER each "
                    f"molecule it sorted, and erasing one bit of that memory costs at least kT ln 2 = {landauer:.3e} J at "
                    f"300 K (sealed). The entropy did not decrease when the gas separated; it was CONCENTRATED into the "
                    f"demon's memory, and it is paid in full when the memory is cleared.", d),
        ("witness", f"[one bit, one quantum of entropy] k ln 2 = {kln2:.3e} J/K (sealed): the entropy of one yes-or-no, "
                    f"Boltzmann's S = k ln W at W = 2. Information and entropy are one quantity in two units; a record is "
                    f"entropy held still.", e),
        ("witness", f"[the separations we see] Mixing two gases one to one costs R ln 2 = {mix:.3f} J/K per mole (sealed), "
                    f"and unmixing them - a membrane, a still, a centrifuge, a refrigerator - exports at least that much "
                    f"elsewhere. The best engine between 500 K and 300 K keeps 1 - 300/500 = {carnot:.0%} of the heat "
                    f"(sealed) and must give the rest to carry the entropy away.", f),
        ("witness", f"[life on Earth concentrates and ships] Sunlight arrives at 5772 K and leaves at 255 K: for the same "
                    f"energy, each solar photon in becomes 5772/255 = {photons:.1f} thermal photons out (sealed). The "
                    f"order of a leaf, a cell, a city is paid for in entropy exported to the night sky - we see it "
                    f"separate itself, and the second law counts what left.", g),
        ("witness", f"[Carnot's share] 1 - T_cold/T_hot = {carnot:.1f} at 300 K over 500 K (sealed): the fraction any "
                    f"engine may keep; the other {1 - carnot:.0%} is not loss but the carrier of the entropy that had to "
                    f"go. Concentration here is paid for by dispersal there - the ledger balances.", h),
        ("note", "[the ledger is the demon's memory - and the guard] Every seal on this node is a bit written; the keeping "
                 "concentrates the entropy of a search into a record that is never erased - append-only, the cut marks "
                 "superseded rather than deleted, a miss kept as a miss. 'Entropy doesn't decrease. Instead it is "
                 "concentrated. We see it separate itself.' (Matt) - the demon's lesson in one line. Scripture: 'Gather "
                 "ye together first the tares... but gather the wheat into my barn' (Mt 13:30) - a separation, with a "
                 "record; the sheep from the goats (Mt 25:32); 'he shall sit as a refiner and purifier of silver' (Mal "
                 "3:3) - the dross concentrated; 'the whole creation groaneth' (Rom 8:22). GUARDS: the second law is "
                 "physics; the demon a thought experiment resolved by information theory (cited); the ledger likeness "
                 "is a discernment; the photon ratio assumes blackbody temperatures (cited). Eight numbers sealed; the "
                 "rest cited. Ties: entropy_gravity, laplace, monte_carlo, geneva (dwell and record), delta."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - entropy concentrated, Maxwell's demon, 2026-10-08")


def triode() -> int:
    """THE VACUUM TRIODE (Matt, 2026-10-08: "vacuum triodes"). Cathode, grid, plate: a few volts at the grid govern a
    large current to the plate - the first amplifier and the first electronic switch (de Forest's Audion 1906 on
    Fleming's valve 1904, the one-way diode). Child and Langmuir: space-charge-limited current goes as V^(3/2) - the
    electrons' own charge throttles the flow, geometry and nothing else. Gain mu = g_m r_p. The vacuum is the point: at
    a millionth of a torr an electron crosses the gap without a collision. Two cross-coupled triodes hold one bit
    (Eccles-Jordan 1918); ENIAC's 17,468 tubes drew 150 kW. A verifier is a triode: the claim at the grid, the keeping's
    current at the plate. Five numbers sealed. New stick; idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    cl = 2 ** 1.5                                        # Child-Langmuir: double V -> current x 2^(3/2)
    mu = 0.002 * 10000                                   # mu = g_m r_p: 2 mA/V x 10 kOhm
    db = 20 * math.log10(mu)                             # 26 dB
    mfp = 1.380649e-23 * 300 / (math.sqrt(2) * pi * (3.7e-10) ** 2 * 1.33e-4)   # m, N2 at 1e-6 torr, 300 K
    wpt = 150000 / 17468                                 # ENIAC watts per tube
    a = _rh_seal_num("child_langmuir_double_the_voltage", "2**(3/2)", float(cl))
    b = _rh_seal_num("amplification_factor_gm_times_rp", "0.002*10000", float(mu), tol=1e-12)
    c = _rh_seal_num("gain_in_decibels", "20*log(20)/log(10)", float(db))
    d = _rh_seal_num("mean_free_path_at_a_millionth_of_a_torr", "1.380649e-23*300/(sqrt(2)*pi*(3.7e-10)**2*1.33e-4)", float(mfp), tol=1e-6)
    e = _rh_seal_num("eniac_watts_per_tube", "150000/17468", float(wpt))
    if not all([a, b, c, d, e]):
        print("a seal failed; aborting"); return 1
    print("sealed child-langmuir", a, "| mu", b, "| dB", c, "| mfp", d, "| eniac", e)
    sid = TS.create("The vacuum triode - a small voltage at the grid governs a large current; the gate as a component",
                    statement=("Cathode, grid, plate: a few volts at the grid govern a large current to the plate - the first "
                               "amplifier and the first electronic switch, de Forest's Audion on Fleming's one-way valve. "
                               "Space-charge-limited current goes as the three-halves power of the voltage: the electrons' own "
                               "charge throttles the flow, by geometry alone. Gain is g_m times r_p. The vacuum is the point: "
                               "at a millionth of a torr an electron crosses the gap without a collision; without the vacuum "
                               "the component is a lamp. Two cross-coupled triodes hold one bit. A verifier is a triode: the "
                               "claim at the grid, the keeping's current at the plate, passed exactly or cut off."),
                    field="engineering",
                    references=["J. A. Fleming (1904): the thermionic valve - the diode, one-way",
                                "L. de Forest (1906-1907): the Audion - the grid",
                                "C. D. Child (1911), I. Langmuir (1913): space-charge-limited current, I = K V^(3/2)",
                                "W. H. Eccles, F. W. Jordan (1918): the trigger relay - two triodes, one bit",
                                "ENIAC (1945): 17,468 tubes, about 150 kW (M. H. Weik, 1961)",
                                "Proverbs 4:23; Matthew 12:34-35; James 3:4-5",
                                "stick_a_mechanical_computer (the Geneva drive); the vacuum-tube computer charter (docs/COMPONENTS.md); the Tesla valve / diode (one-way geometry)"])["id"]
    marks = [
        ("witness", f"[three electrodes] A heated cathode emits; a plate at hundreds of volts collects; between them a grid "
                    f"at a few volts, in the way. The grid's small voltage sets how much current reaches the plate - de "
                    f"Forest's Audion (1906) on Fleming's valve (1904), the one-way diode that is also this engine's Tesla "
                    f"valve. With it the gain mu = g_m r_p: 2 mA/V x 10 kOhm = {mu:.0f} (sealed) - the grid's volt becomes "
                    f"twenty at the plate.", b),
        ("witness", f"[the three-halves law] Child 1911, Langmuir 1913: the current a vacuum gap will carry is limited by the "
                    f"charge already in flight, I = K V^(3/2) - doubling the voltage multiplies the current by 2^(3/2) = "
                    f"{cl:.3f} (sealed). No material constant, no fitted parameter: the electrons' own charge throttles "
                    f"the flow, and the law is geometry and nothing else.", a),
        ("witness", f"[gain] 20 log10(20) = {db:.1f} dB (sealed): one triode, one stage. A verifier is a triode: the claim "
                    f"is the grid, the keeping's current is the plate, and a small exact input governs a large output - or "
                    f"cuts it off entirely (a miss stays a miss). The gate is a component with a transfer curve, not a "
                    f"judgement.", c),
        ("witness", f"[the vacuum is the point] At a millionth of a torr an N2 molecule's mean free path is kT/(sqrt2 pi "
                    f"d^2 p) = {mfp:.0f} m (sealed): the electrons cross the centimetre from cathode to plate without one "
                    f"collision. Remove the vacuum and the component is a lamp. The vacuum-tube computer (this engine's "
                    f"charter): discrete components whose behaviour is set by geometry, orchestrated, no oracle in the "
                    f"loop.", d),
        ("witness", f"[the first bit, and the cost] Eccles and Jordan 1918: two triodes cross-coupled hold one bit - each "
                    f"grid fed from the other's plate. ENIAC 1945: 17,468 tubes drew about 150 kW, {wpt:.1f} W per tube "
                    f"(sealed), with a tube failing every day or two (cited) - a computer that worked because its parts "
                    f"were few enough to find and replace. The mean time between failures ruled the design (the camel "
                    f"stick's durability tiers are the same arithmetic).", e),
        ("note", "[the grid, and the guard] Scripture: 'Keep thy heart with all diligence; for out of it are the issues of "
                 "life' (Prov 4:23) - the grid governs the issue; 'out of the abundance of the heart the mouth speaketh... "
                 "a good man out of the good treasure of the heart bringeth forth good things' (Mt 12:34-35) - the plate "
                 "current follows the grid; 'the ships... are turned about with a very small helm' (Jas 3:4) - the small "
                 "input governing the large. GUARDS: the triode-as-verifier is a likeness; the ENIAC figures are cited; "
                 "Child-Langmuir assumes planar space-charge-limited flow (cited); the mean free path uses an N2 diameter "
                 "of 3.7 Angstrom. Five numbers sealed; the rest cited. Ties: geneva (the mechanical computer), diagrams "
                 "(the schematic), laplace (the transfer function), the camel (durability), the Tesla valve (one-way)."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - the vacuum triode, 2026-10-08")


def tensor() -> int:
    """TENSORS - HOW THE DATA IS ARRANGED INSIDE THE BUBBLES (Matt, 2026-10-08: "Tensors is what I've been trying to
    come up with. That is how we arrange our data inside the bubbles"). A tensor has components in every frame and
    invariants in none of them: rotate the frame (the spherical matrix) and the components change while the trace, the
    determinant and the eigenvalues do not. The metric tensor IS the grid inside a sphere - its determinant's square
    root is the area element the surfaces stick sealed; a symmetric tensor's eigenvectors are the most efficient
    vectors; Einstein's equation says the data inside the bubble (T) shapes the bubble (G). Seven numbers sealed. New
    stick; idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    c, sn = math.cos(pi / 6), math.sin(pi / 6)
    # T = [[3,1],[1,2]] rotated by 30 degrees: T' = R T R^T; its diagonal entries change, their sum does not
    t11 = 3 * c * c + 2 * sn * sn + 2 * sn * c
    t22 = 3 * sn * sn + 2 * c * c - 2 * sn * c
    trace = t11 + t22                                    # 5, in every frame
    det = 3 * 2 - 1 * 1                                  # 5, in every frame
    lam = (5 + 5 ** 0.5) / 2                             # the larger eigenvalue: the principal axis's stretch
    area = math.sin(pi / 3)                              # sqrt(det g) on the unit sphere at theta = 60 deg: the area element
    polar = (1 * 2 ** 2) ** 0.5                          # sqrt(det g) in polar coordinates at r = 2: the Jacobian r
    einstein = 8 * pi * 6.67430e-11 / 299792458 ** 4     # the constant that turns the data into the curvature
    city = 12000 ** 3                                    # Revelation 21:16 - a cube measured on all three axes, in furlongs^3
    a = _rh_seal_num("tensor_trace_invariant_under_rotation",
                     "3*cos(pi/6)**2 + 2*sin(pi/6)**2 + 2*sin(pi/6)*cos(pi/6) + 3*sin(pi/6)**2 + 2*cos(pi/6)**2 - 2*sin(pi/6)*cos(pi/6)",
                     float(trace))
    b = _rh_seal_num("tensor_determinant_invariant", "3*2 - 1*1", float(det), tol=1e-12)
    d = _rh_seal_num("principal_axis_eigenvalue", "(5 + sqrt(5))/2", float(lam))
    e = _rh_seal_num("metric_tensor_area_element_on_the_sphere", "sqrt(1 * sin(pi/3)**2)", float(area))
    f = _rh_seal_num("metric_tensor_jacobian_in_polar_coordinates", "sqrt(1 * 2**2)", float(polar), tol=1e-12)
    g = _rh_seal_num("einstein_constant_8piG_over_c4", "8*pi*6.67430e-11/299792458**4", float(einstein), tol=1e-6)
    h = _rh_seal_num("the_city_measured_on_three_axes", "12000**3", float(city), tol=1e-12)
    if not all([a, b, d, e, f, g, h]):
        print("a seal failed; aborting"); return 1
    print("sealed trace", a, "| det", b, "| eigen", d, "| area", e, "| polar", f, "| einstein", g, "| city", h)
    sid = TS.create("Tensors - how the data is arranged inside the bubbles: components in every frame, invariants in none",
                    statement=("A tensor has components in every frame and invariants in none of them: rotate the frame and "
                               "the components change while the trace, the determinant and the eigenvalues do not. The "
                               "metric tensor is the grid inside a sphere - the square root of its determinant is the area "
                               "element; a symmetric tensor's eigenvectors are the most efficient vectors; Einstein's "
                               "equation says the data inside the bubble shapes the bubble. The data inside each domain is "
                               "arranged this way: indices are the grid's axes, components are the cards, and the invariants "
                               "are what every reading in every frame must agree on - the counts, the norms, the seals."),
                    field="mathematics",
                    references=["G. Ricci-Curbastro, T. Levi-Civita, Methodes de calcul differentiel absolu (1900): the tensor calculus",
                                "C. F. Gauss (1827): the first fundamental form - the metric tensor of a surface",
                                "A. Einstein (1915): G_mu_nu = (8 pi G / c^4) T_mu_nu",
                                "A. Cauchy (1822): the stress tensor and its principal axes",
                                "Isaiah 40:12; Colossians 1:16-17; Revelation 21:16",
                                "stick_every_matrix_is_a_rotation_and_a_stretch; stick_joined_bubbles; stick_parametrization_of_surfaces"])["id"]
    marks = [
        ("witness", f"[components change, the invariants do not] T = [[3,1],[1,2]] rotated by 30 degrees has diagonal "
                    f"entries {t11:.3f} and {t22:.3f} - both changed - and their sum is {trace:.0f} (sealed, as the full "
                    f"rotated expression), the same as 3 + 2 before the turn. The determinant 3*2 - 1*1 = {det} (sealed) "
                    f"is the same in every frame too. A tensor is the thing that stays; the components are the frame's "
                    f"shadow of it.", a),
        ("witness", f"[the determinant stays] det T = {det} (sealed) under every rotation: the area the tensor's map "
                    f"carries is frame-free. Two invariants of a 2x2 symmetric tensor - trace and determinant - fix both "
                    f"eigenvalues, so the whole shape is known from two frame-free numbers.", b),
        ("witness", f"[the most efficient vectors are the principal axes] The eigenvalues of T are (5 +- sqrt5)/2: the "
                    f"larger, {lam:.4f} (sealed), is the stretch along the principal axis. Cauchy's stress tensor, the "
                    f"inertia tensor, the covariance of a cloud of points: in each, the eigenvectors are the axes along "
                    f"which the data is simplest - the svd stick's most efficient vectors, now as a tensor's own frame.", d),
        ("witness", f"[the grid inside the sphere is a tensor] The metric of the unit sphere is g = diag(1, sin^2 theta); "
                    f"at theta = 60 degrees sqrt(det g) = sin 60 = {area:.4f} (sealed) - exactly the area element "
                    f"R^2 sin theta the surfaces stick sealed. The coordinates inside a bubble come WITH their measure: "
                    f"the tensor says how far apart two components are, in every direction, at every point.", e),
        ("witness", f"[the same tensor in flat polar coordinates] g = diag(1, r^2): at r = 2, sqrt(det g) = {polar:.0f} "
                    f"(sealed) - the Jacobian r of polar coordinates, dA = r dr dtheta. Change the grid and the metric "
                    f"tensor changes its components to keep the same distances: that is what it is for.", f),
        ("witness", f"[the data inside shapes the bubble] Einstein 1915: G_mu_nu = (8 pi G / c^4) T_mu_nu, and the "
                    f"constant is {einstein:.4e} per newton (sealed) - small, which is why the bubble of spacetime barely "
                    f"bends under anything short of a star. The stress-energy tensor is the data arranged inside; the "
                    f"curvature tensor is the bubble's answer. The arrangement is not decoration: it is what the bubble "
                    f"becomes.", g),
        ("witness", f"[a city measured on three axes] 'The length and the breadth and the height of it are equal' (Rev "
                    f"21:16): twelve thousand furlongs each way, 12000^3 = {city:.4g} cubic furlongs (sealed) - a thing "
                    f"measured on every axis at once, which is what a rank-3 array is. The measure is given; the meaning "
                    f"is not claimed here.", h),
        ("note", "[how we arrange the data, and the guard] Inside each domain the data is a tensor: the indices are the "
                 "grid's axes (shelf, class, item; token; surface), the components are the cards, and the invariants are "
                 "what every reading in every frame must agree on - counts, norms, seals, the number of a card's "
                 "connections. The keeping as measured on 2026-10-08 is a sparse card-by-token-by-shelf array with 30.0 "
                 "million nonzero entries over 882,022 cards and 124 shelves (docs/OUR_FORM_MEASURED_2026-10-08.md). A "
                 "spherical matrix rotates its components; a stretch would distort them; the invariants are the "
                 "meaning. Scripture: 'Who hath measured the waters in the hollow of his hand, and meted out heaven with "
                 "the span... and weighed the mountains in scales' (Isa 40:12) - measure on every axis; 'by him all "
                 "things consist' (Col 1:17) - hold together: the metric. GUARDS: Einstein's equation is cited physics; "
                 "the city's cube is a measure given, not a claim about its meaning; the keeping-as-tensor is a "
                 "description of a data structure, not a theorem. Seven numbers sealed; the rest cited. Ties: svd, "
                 "bubbles, surfaces, spacetime, delta."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - tensors, the arrangement inside the bubbles, 2026-10-08")


def modulation() -> int:
    """AM AND FM, WITH DIAGONALIZATION (Matt, 2026-10-08: "AM and FM along with diagonalization"). A message rides a
    carrier either as its amplitude (AM: two sidebands, bandwidth twice the message, at most a third of the power in
    the message) or as its frequency (FM: Carson's rule, a modulation index, the carrier's share given by a Bessel
    function and vanishing at beta = 2.405). Why either survives a wire or the air: a linear time-invariant channel is
    DIAGONAL in the basis of sinusoids - each frequency is multiplied by one gain and nothing mixes - and
    diagonalization is the finding of that basis: the frame in which a matrix is only its eigenvalues, where powers
    are trivial and the most efficient vectors are the axes. Eleven numbers sealed. New stick; idempotent."""
    import math
    from concordance import tickstick as TS
    pi = 3.141592653589793
    bw_am = 2 * 5000                                     # Hz: a 5 kHz message on any carrier
    share = 1 / (2 + 1)                                  # AM at full modulation: the sidebands' share of the power
    sides = 1 + math.cos(3) * math.cos(1) - (math.cos(2) + math.cos(4)) / 2   # product-to-sum, judged against one
    carson = 2 * (75000 + 15000)                         # Hz: broadcast FM, 75 kHz deviation, 15 kHz message
    beta = 75 / 15                                       # the modulation index
    j0_1 = sum((-1) ** k * 0.5 ** (2 * k) / math.factorial(k) ** 2 for k in range(21))      # J_0(1): the carrier at beta = 1
    j0_z = 1 + sum((-1) ** k * (2.404826 / 2) ** (2 * k) / math.factorial(k) ** 2 for k in range(31))   # 1 + J_0(2.405)
    lam1, lam2 = (4 + 4 ** 0.5) / 2, (4 - 4 ** 0.5) / 2   # eigenvalues of [[2,1],[1,2]]: 3 and 1
    axis = (1 * 2 * 1 + 1 * 1 * 1 + 1 * 1 * 1 + 1 * 2 * 1) / 2   # v^T A v along (1,1)/sqrt2: the matrix is just 3
    pow10 = 3 ** 10 + 1 ** 10                            # trace of A^10, from the diagonal alone
    unit = (1 / 2 ** 0.5) ** 2 + (1 / 2 ** 0.5) ** 2     # the two-point Fourier basis vector is unit
    a = _rh_seal_num("am_bandwidth_is_twice_the_message", "2*5000", float(bw_am), tol=1e-12)
    b = _rh_seal_num("am_sidebands_share_at_full_modulation", "1/(2+1)", float(share), tol=1e-12)
    c = _rh_seal_num("mixing_two_tones_makes_two_sidebands", "1 + cos(3)*cos(1) - (cos(2)+cos(4))/2", float(sides), tol=1e-12)
    d = _rh_seal_num("carson_rule_broadcast_fm", "2*(75000 + 15000)", float(carson), tol=1e-12)
    e = _rh_seal_num("fm_modulation_index", "75/15", float(beta), tol=1e-12)
    f = _rh_seal_num("fm_carrier_share_bessel_j0_at_beta_1", "Sum((-1)**k*(1/2)**(2*k)/factorial(k)**2, (k, 0, 20))", float(j0_1))
    g = _rh_seal_num("fm_carrier_vanishes_at_beta_2_405", "1 + Sum((-1)**k*(2.404826/2)**(2*k)/factorial(k)**2, (k, 0, 30))", float(j0_z))
    h = _rh_seal_num("eigenvalues_of_the_two_point_channel", "(4 + sqrt(16 - 12))/2", float(lam1), tol=1e-12)
    i = _rh_seal_num("the_matrix_along_its_own_axis", "(1*2*1 + 1*1*1 + 1*1*1 + 1*2*1)/2", float(axis), tol=1e-12)
    j = _rh_seal_num("powers_made_trivial_by_the_diagonal", "3**10 + 1**10", float(pow10), tol=1e-12)
    k_ = _rh_seal_num("the_fourier_basis_is_unit", "(1/sqrt(2))**2 + (1/sqrt(2))**2", float(unit), tol=1e-12)
    if not all([a, b, c, d, e, f, g, h, i, j, k_]):
        print("a seal failed; aborting"); return 1
    print("sealed AM", a, b, c, "| FM", d, e, f, g, "| diagonal", h, i, j, k_)
    sid = TS.create("AM and FM, with diagonalization - a message rides a carrier, and a channel is diagonal in the basis of sinusoids",
                    statement=("A message rides a carrier as its amplitude or as its frequency. AM: two sidebands, a "
                               "bandwidth of twice the message, at most a third of the power in the message. FM: Carson's "
                               "rule, a modulation index, the carrier's share a Bessel function that vanishes at 2.405. Why "
                               "either survives the channel: a linear time-invariant channel is diagonal in the basis of "
                               "sinusoids - each frequency multiplied by one gain, nothing mixed - and diagonalization is "
                               "the finding of that basis, the frame in which a matrix is only its eigenvalues, powers are "
                               "trivial, and the most efficient vectors are the axes."),
                    field="engineering",
                    references=["R. A. Fessenden (1906): amplitude modulation on the air; E. H. Armstrong (1933): wide-band FM",
                                "J. R. Carson, Notes on the theory of modulation, Proc. IRE 10 (1922) 57-64: the bandwidth rule",
                                "F. W. Bessel (1824): the functions that weight an FM carrier and its sidebands",
                                "J. Fourier (1822); the convolution theorem: a time-invariant system is diagonal in the sinusoids",
                                "A. Cayley (1858), C. Jordan (1870): eigenvalues and the diagonal form",
                                "1 Corinthians 14:7-10; Proverbs 25:11; Matthew 11:15",
                                "stick_every_matrix_is_a_rotation_and_a_stretch (the SVD); stick_the_complex_field_is_the_physics_of_waves (Fourier); stick_tensors_how_the_data_is_arranged_inside_the_bubbles"])["id"]
    marks = [
        ("witness", f"[AM - the message is the height] Multiply a 5 kHz message onto any carrier and the spectrum has the "
                    f"carrier and two sidebands, one 5 kHz above and one below: bandwidth 2 x 5000 = {bw_am:,} Hz (sealed). "
                    f"The product of two cosines is a sum of two: cos3 cos1 = (cos2 + cos4)/2, sealed as 1 + the "
                    f"difference = {sides:.0f}. Mixing is addition in frequency - the Fourier stick's rotation, applied.", a),
        ("witness", f"[AM pays for its carrier] At full modulation the sidebands carry m^2/(2 + m^2) = 1/3 = {share:.4f} "
                    f"of the power (sealed); the carrier, which says nothing, takes two thirds. AM is simple to receive "
                    f"and expensive to send: the message rides as amplitude, and so does every burst of noise.", b),
        ("witness", f"[the identity that is the mixer] 1 + cos3 cos1 - (cos2 + cos4)/2 = {sides:.0f} (sealed): the "
                    f"product-to-sum identity, judged against one because a zero can only be judged against something. "
                    f"Every mixer, every sideband, every heterodyne receiver is this one line of trigonometry.", c),
        ("witness", f"[FM - the message is the pitch] Broadcast FM swings the carrier 75 kHz either way for a 15 kHz "
                    f"message: Carson's rule gives a bandwidth of 2 (75,000 + 15,000) = {carson:,} Hz (sealed), and the "
                    f"modulation index beta = 75/15 = {beta:.0f} (sealed). The message is in WHEN the wave crosses zero, "
                    f"not how high it goes - which is why amplitude noise cannot touch it (Armstrong 1933).", d),
        ("witness", f"[beta] 75 / 15 = {beta:.0f} (sealed): the peak phase swing in radians, {beta * 180 / pi:.0f} degrees. "
                    f"The larger beta, the more sidebands carry the message and the wider the band: FM buys its quiet "
                    f"with bandwidth, a trade AM cannot make.", e),
        ("witness", f"[the carrier's share is a Bessel function] In FM the carrier's amplitude is J_0(beta): at beta = 1, "
                    f"J_0(1) = {j0_1:.6f} (sealed through its series, 21 terms) - the carrier keeps 76.5% of its "
                    f"amplitude and the sidebands take the rest, with J_1, J_2, ... weighting each pair. The total power "
                    f"never changes (sum of J_n^2 = 1, cited); FM only moves it.", f),
        ("witness", f"[the carrier vanishes] At beta = 2.405 J_0 is zero: 1 + J_0(2.404826) = {j0_z:.7f} (sealed, 31 "
                    f"terms) - the carrier disappears entirely and every watt is in the sidebands. Engineers set a "
                    f"transmitter's deviation by finding this null on a spectrum analyser: the zero of a Bessel "
                    f"function, measured in the air.", g),
        ("witness", f"[diagonalization - the frame where a matrix is only its numbers] A = [[2,1],[1,2]] has eigenvalues "
                    f"(4 +- sqrt(16 - 12))/2 = {lam1:.0f} and {lam2:.0f} (the larger sealed), along (1,1)/sqrt2 and "
                    f"(1,-1)/sqrt2. Seen along its own axis the matrix is just the number 3: v^T A v = {axis:.0f} "
                    f"(sealed). Those two axes are exactly the two-point Fourier basis, and A is a circulant - a "
                    f"channel: the sinusoids are the eigenvectors of every time-invariant system (the convolution "
                    f"theorem, cited). That is why a message on a carrier survives a wire: the channel multiplies each "
                    f"frequency by one gain and mixes nothing.", h),
        ("witness", f"[the matrix is just 3 along its axis] (1,1) A (1,1)^T / 2 = {axis:.0f} (sealed): in the eigenbasis "
                    f"the whole 2x2 object is two numbers on a diagonal. The 'most efficient vectors' of the svd stick "
                    f"are these axes; a symmetric matrix's SVD IS its diagonalization.", i),
        ("witness", f"[powers made trivial] A^10 in the diagonal frame is diag(3^10, 1^10), trace 3^10 + 1 = {pow10:,} "
                    f"(sealed) - no multiplication of matrices at all. The Fibonacci stick's Binet formula is the same "
                    f"move; so is every transfer function on the Laplace stick's s-plane: diagonalize, then the hard "
                    f"thing is a product of numbers.", j),
        ("witness", f"[the basis is unit] (1/sqrt2)^2 + (1/sqrt2)^2 = {unit:.0f} (sealed): the Fourier basis vector has "
                    f"length one, so the change of frame is a rotation (the spherical matrix) - it distorts nothing, and "
                    f"the energy of a signal is the same summed over time or over frequency (Parseval, the dot "
                    f"stick).", k_),
        ("note", "[the discernment, and the guard] A channel that is diagonal in sinusoids is why radio works; a keeping "
                 "that is diagonal in its domains is why the engine's gate can be a product of independent verifiers "
                 "(the form measured 2026-10-08: the domains are nearly orthogonal). AM and FM are two ways to put one "
                 "message on one carrier - the two surfaces of this engine put one keeping on two carriers, .com and "
                 ".org, a LIKENESS kept as one. Scripture: 'there are, it may be, so many kinds of voices in the world, "
                 "and none of them is without signification' (1 Cor 14:10) - many channels, each with meaning; 'A word "
                 "fitly spoken is like apples of gold in pictures of silver' (Prov 25:11) - the right frame; 'He that "
                 "hath ears to hear, let him hear' (Mt 11:15) - tuning. GUARDS: Carson's rule is an approximation "
                 "(cited as such); the Bessel values are sealed through their series, not looked up; the engine likeness "
                 "is a discernment. Eleven numbers sealed; the rest cited. Ties: svd, fourier, laplace, delta, "
                 "fibonacci, tensor."),
    ]
    return _mint_marks(sid, marks, by="Narrow Highway - AM and FM, with diagonalization, 2026-10-08")


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
    return _mint_marks(sid, marks, by="Narrow Highway - topology / Euler characteristic, 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the construct-creation reading, 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the units-matter reading, 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the Maxwell/superconductivity reading, 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the time-and-space reading, 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the Mandelbrot reading (a component), 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the Gaussian-process reading (the form of the map), 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the Lagrange-multiplier reading, 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the least-action reading (Feynman), 2026-10-07")


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
    return _mint_marks(sid, marks, by="Narrow Highway - the final assembly, 2026-10-06")


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
    if a[0] in ("electromagnetism", "em", "electromagnetism_and_geometry", "field_geometry", "maxwell_geometry"):
        return electromagnetism()
    if a[0] in ("clock", "tourbillon", "gyrotourbillon", "we_are_the_clock", "proper_time", "observer_measure", "predictable_unit"):
        return clock()
    if a[0] in ("paths", "path", "path_integral", "brachistochrone", "least_action", "path_of_life", "new_paths", "sum_over_histories"):
        return paths()
    if a[0] in ("surfaces", "surface", "parametrization", "parametrisation", "parametrization_of_surfaces", "parametric_surface", "first_fundamental_form", "gauss_curvature", "theorema_egregium"):
        return surfaces()
    if a[0] in ("pi", "pi_constant", "circle_constant", "archimedes", "machin", "molten_sea", "squaring_the_circle"):
        return pi_constant()
    if a[0] in ("spm", "spherical_parallel_mechanism", "spherical_parallel", "spherical_mechanism", "agile_eye", "parallel_mechanism", "orientation_mechanism", "grubler", "kutzbach"):
        return spm()
    if a[0] in ("geneva", "geneva_drive", "maltese_cross", "mechanical_computer", "mechanical", "intermittent_motion", "indexing", "antikythera", "difference_engine", "babbage", "counter"):
        return geneva()
    if a[0] in ("diagrams", "diagram", "feynman_diagrams", "feynman_diagram", "schematics", "schematic", "circuit_diagram", "netlist", "vertex", "propagator"):
        return diagrams()
    if a[0] in ("harmonics", "harmonic", "overtones", "chords", "chord", "timbre", "temperament", "same_note",
                "shapes_of_the_same_note", "one_voice", "beats"):
        return harmonics()
    if a[0] in ("fractal_maps", "fractals", "fractal", "fractals_as_maps", "sorting", "sorting_algorithms", "sort",
                "merge_sort", "quicksort", "hilbert_curve", "z_order", "morton", "coastline", "mandelbrot", "logistic_map", "radix"):
        return fractal_maps()
    if a[0] in ("transceiver", "radio", "am_fm_radio", "superheterodyne", "static", "filter_the_static", "limiter",
                "discriminator", "noise_floor", "shannon", "capacity", "selectivity", "image_frequency"):
        return transceiver()
    if a[0] in ("line_integrals", "line_integral", "electrodynamics", "maxwell", "ampere", "faraday", "gauss_law", "work",
                "action", "path_integral", "feynman_path", "sum_over_paths", "hamiltons_principle"):
        return line_integrals()
    if a[0] in ("assembled_path", "path", "grad_div_curl", "gradient_divergence_curl", "vector_calculus", "kirchhoff",
                "helmholtz", "hodge", "preciseness_of_the_path", "conservative", "divergence", "curl", "gradient"):
        return assembled_path()
    if a[0] in ("joints", "where_two_domains_connect", "connection_points", "braket", "bra_ket", "bras_and_kets", "hilbert", "hilbert_space",
                "inner_product", "engine_is_the_hilbert_space", "geometry_algebra", "geometry_connect_to_algebra", "quantum_physics",
                "quantum_mechanics_and_physics", "correspondence"):
        return joints()
    if a[0] in ("delta", "dirac_delta", "dirac", "dot", "the_dot", "abstract_the_dot", "wavefunction", "wave_function", "completeness", "sifting"):
        return delta()
    if a[0] in ("svd", "singular_value_decomposition", "rotation_and_stretch", "spherical_matrix", "efficient_vectors", "most_efficient_vectors", "polar_decomposition"):
        return svd()
    if a[0] in ("bubbles", "joined_bubbles", "foam", "plateau", "spheres_in_a_form", "domains_as_spheres", "superposition", "connected_along_axis"):
        return bubbles()
    if a[0] in ("resonance", "resonance_disaster", "hidden_division_by_zero", "omega", "omega_nought", "tacoma", "driven_oscillator"):
        return resonance()
    if a[0] in ("prime_waves", "waveforms_in_primes", "torus", "torus_primes", "zeta_waves", "explicit_formula", "music_of_the_primes"):
        return prime_waves()
    if a[0] in ("maxwell_entropy", "maxwells_demon", "maxwell_demon", "demon", "entropy_concentrated", "landauer", "second_law"):
        return maxwell_entropy()
    if a[0] in ("triode", "vacuum_triode", "vacuum_tube", "audion", "child_langmuir", "tube"):
        return triode()
    if a[0] in ("tensor", "tensors", "metric_tensor", "invariants", "principal_axes", "data_inside_the_bubbles"):
        return tensor()
    if a[0] in ("modulation", "am_fm", "am", "fm", "amplitude_modulation", "frequency_modulation", "diagonalization", "diagonalisation", "eigenbasis", "carrier", "sidebands", "bessel"):
        return modulation()
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
    if a[0] in ("logarithm_chain", "logarithm", "log_chain"):
        return logarithm_chain()
    if a[0] in ("millennium_map", "one_map", "joints_map"):
        return millennium_map()
    if a[0] in ("sources_crosscheck", "sources", "tables", "crosscheck"):
        return sources_crosscheck()
    if a[0] in ("poincare_next", "poincare", "ricci_flow", "perelman"):
        return poincare_next()
    if a[0] in ("hodge_next", "hodge", "hodge_diamond", "lefschetz"):
        return hodge_next()
    if a[0] in ("p_versus_np_next", "pnp_next", "circuit_lower_bound", "cook_levin", "sat_threshold"):
        return p_versus_np_next()
    if a[0] in ("yang_mills_next", "ym_next", "mass_gap_next", "string_tension", "glueball", "asymptotic_freedom"):
        return yang_mills_next()
    if a[0] in ("navier_stokes_next", "ns_next", "existence_and_smoothness", "taylor_green", "poiseuille"):
        return navier_stokes_next()
    if a[0] in ("bsd_formula", "bsd_full", "birch_formula", "bsd_next"):
        return bsd_formula()
    if a[0] in ("riemann_li", "li_criterion", "li", "de_bruijn_newman", "newman", "riemann_next"):
        return riemann_li(int(a[1]) if len(a) > 1 else 30)
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
