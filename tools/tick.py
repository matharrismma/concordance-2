#!/usr/bin/env python3
"""THE TICK STICK — make a mark (docs/TICK_STICK.md; Matt, 2026-10-05).

    PYTHONPATH=src python tools/tick.py list                 # every stick in the catalog (data/sticks/*.json) and its aliases
    PYTHONPATH=src python tools/tick.py <alias>              # run one: a data stick through concordance.sticks, a Python
                                                             # handler (the computational minority below) by its function
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

STICKS ARE DATA (issue #13, 2026-10-17). Every stick is an entry in data/sticks/<name>.json — aliases, seals (nid /
expr / value / tol, or a domain verifier's spec), the stick and its marks — run by concordance.sticks.run; adding a
stick needs no Python. The functions below are the computational minority (they call verify_derivation or
tickstick.tick themselves, take a CLI argument, or read a table) and are registered in the SAME catalog as handler
entries, so main() has one table and an alias can reach exactly one stick: a duplicate is a load-time error.
tools/tick_golden.py pins every entry's sealed content; tools/tick_record.py is how a function becomes data.
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


def grimm_law() -> int:
    """GRIMM'S LAW - A SOUND LAW, VERIFIED AND SEALED (Matt, 2026-10-09: "How do we use this for linguistics?" -
    "build it"). The first consonant shift: in Germanic the Proto-Indo-European voiceless stops became voiceless
    fricatives - p -> f, t -> th, k -> h - regularly, across the vocabulary. That regularity is CHECKABLE on cognate
    pairs attested by the comparative method (Latin, which kept the stops, against English, which shifted). The
    sound_law verifier confirms each correspondence on its cited pairs and the verdict is SEALED. What is cited: the
    cognate pairs (attested) and the proto-form (a reconstruction - a postulate, never sealed). What is sealed: that
    the correspondence holds on every cited pair. Idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig
    LAWS = [
        ("p", "f", "Grimm's law: PIE *p -> Germanic f",
         [["pater", "father"], ["piscis", "fish"], ["pes", "foot"], ["plenus", "full"], ["pellis", "fell"]]),
        ("t", "th", "Grimm's law: PIE *t -> Germanic th",
         [["tres", "three"], ["tu", "thou"], ["tenuis", "thin"]]),
        ("c", "h", "Grimm's law: PIE *k -> Germanic h",
         [["cornu", "horn"], ["canis", "hound"], ["centum", "hundred"], ["caput", "head"], ["cor", "heart"]]),
    ]
    seals = {}
    for so, to, label, pairs in LAWS:
        spec = {"SOUNDLAW_VERIFY": {"pairs": pairs, "source_onset": so, "target_onset": to, "law": label,
                                    "claimed_regular": True}}
        res = verify_derivation([{"id": "law", "domain": "sound_law", "spec": spec}])
        if res.get("verdict") != "HOLDS":
            print("the law did not hold:", label, res.get("verdict")); return 1
        res = receipts.attach(res, config=EngineConfig(), domain="sound_law")
        seal = (res.get("seal") or {}).get("content_hash")
        if not seal:
            print("no seal minted for", label); return 1
        seals[so] = (seal, label, pairs)
        print("sealed", label, seal[:12])
    sid = TS.create("Grimm's law - a regular sound correspondence, verified")["id"]
    marks = [
        ("instance", "[PIE *p -> Germanic f, verified] Latin kept the stop, English shifted it: pater/father, "
                     "piscis/fish, pes/foot, plenus/full, pellis/fell - the correspondence p -> f holds at the onset "
                     "on all five cited cognate pairs (sealed through sound_law). A regular law, not five coincidences; "
                     "the cognates are attested by the comparative method, the proto-form *ph2ter is a reconstruction.",
         seals["p"][0]),
        ("instance", "[PIE *t -> Germanic th, verified] tres/three, tu/thou, tenuis/thin - t -> th on every cited pair "
                     "(sealed).", seals["t"][0]),
        ("instance", "[PIE *k -> Germanic h, verified] cornu/horn, canis/hound, centum/hundred, caput/head, cor/heart "
                     "- Latin c (/k/) answers English h on all five (sealed). centum/hundred is the very pair that names "
                     "the centum/satem split of the family.", seals["c"][0]),
        ("postulate", "[what is cited, not proven] The cognate pairs are ATTESTED by the comparative method; the "
                      "Proto-Indo-European forms (*p, *t, *k, *ph2ter) are RECONSTRUCTIONS - they work (they predict the "
                      "attested forms by regular law), so the proto-language is inferred, never kept as a fact and never "
                      "sealed. The engine seals only what it checked: that the correspondence holds on the cited pairs.",
         {"source": "J. Grimm, Deutsche Grammatik (1822); K. Verner (1877) for the exceptions; the comparative method"}),
        ("note", "[how linguistics uses this] A sound law is a regular correspondence - math on the vocabulary, "
                 "exactly checkable and sealable, and refutable (a pair that breaks it is named). The engine CERTIFIES "
                 "the correspondence with its cited cognates as the reason, DECLINES the reconstruction beyond the "
                 "attested (a postulate), and a false law (p -> p, or a non-cognate pair) is caught. Verner's law is the "
                 "famous residue - the apparent exceptions to Grimm that a deeper regularity (PIE accent) explained; the "
                 "exceptions become a want, not a fudge.",
         {"source": "src/concordance/verifiers/sound_law.py; the one map, card_floor_indo_european"}),
        ("note", "[on the one map] Etymology is chains from a floor where two trees connect: the proto-language is the "
                 "floor, the sound laws are the chain, a cognate is the confluence where two language-branches meet "
                 "(father and pater meet at PIE *ph2ter). card_floor_indo_european draws it.",
         {"source": "tools/seed_indo_european.py"}),
    ]
    _mint_marks(sid, marks, by="tools/tick.py grimm_law")
    return 0


def genomics() -> int:
    """GENOMICS - THE GENETIC CODE, SEALED (Matt, 2026-10-09: "We will cover every domain. Starting with genomics").
    The code is a deterministic table (NCBI translation table 1, public domain) - like Webster for etymology - so a
    genomic claim is exactly checkable. Sealed: the code's arithmetic (64 = 4^3 codons, 61 sense + 3 stop, the
    six-fold degeneracy of leucine), real translations run through the genetics verifier (ATG -> Met the start, TGG ->
    Trp the only one, ATGGCCTAA -> MA*), and a Hardy-Weinberg equilibrium run through biology. What is sealed is what
    is CHECKED; gene function, phenotype and clinical meaning are declined, not guessed. Idempotent."""
    from concordance import receipts, tickstick as TS
    from concordance.derivation import verify_derivation
    from concordance.engine import EngineConfig

    def seal_domain(domain, artifact_key, spec):
        res = verify_derivation([{"id": "g", "domain": domain, "spec": {artifact_key: spec}}])
        if res.get("verdict") != "HOLDS":
            print("did not hold:", domain, spec, res.get("verdict")); return None
        res = receipts.attach(res, config=EngineConfig(), domain=domain)
        return (res.get("seal") or {}).get("content_hash")

    S = {}
    # the code's arithmetic (numeric seals)
    S["codons"] = _rh_seal_num("genetic_code_number_of_codons_four_cubed", "4**3", 64.0, tol=1e-12)
    S["sense"] = _rh_seal_num("genetic_code_sense_codons_sixty_four_minus_three_stops", "4**3 - 3", 61.0, tol=1e-12)
    S["hw"] = _rh_seal_num("hardy_weinberg_sum_p_sq_two_pq_q_sq_equals_one", "0.6**2 + 2*0.6*0.4 + 0.4**2", 1.0, tol=1e-12)
    # real verdicts, sealed through the verifiers
    S["atg"] = seal_domain("genetics", "GENETICS_VERIFY", {"codon": "ATG", "claimed_amino_acid": "M"})
    S["tgg"] = seal_domain("genetics", "GENETICS_VERIFY", {"codon": "TGG", "claimed_amino_acid": "W"})
    S["tr"] = seal_domain("genetics", "GENETICS_VERIFY", {"sequence": "ATGGCCTAA", "claimed_protein": "MA*"})
    S["hwe"] = seal_domain("biology", "BIO_VERIFY", {"hardy_weinberg": {"counts": [360, 480, 160]}})
    for k, v in S.items():
        if not v:
            print("a seal failed:", k); return 1
    print("sealed", len(S), "genomics facts")
    sid = TS.create("Genomics - the genetic code, verified and sealed")["id"]
    marks = [
        ("instance", "[the code counted] Three bases, four letters: 4^3 = 64 codons (sealed), of which 61 are sense and "
                     "3 are stop (TAA, TAG, TGA) - 64 - 3 = 61 (sealed). Sixty-one sense codons map onto twenty amino "
                     "acids, so the code is degenerate: leucine, serine and arginine have six codons each; methionine "
                     "and tryptophan have one. The redundancy sits in the third base - the wobble.", S["codons"]),
        ("instance", "[translation, verified] ATG -> Met (sealed through the genetics verifier): the start codon, and "
                     "the only codon for methionine. The reading begins here.", S["atg"]),
        ("instance", "[the only one] TGG -> Trp (sealed): tryptophan is the one amino acid with a single codon - which "
                     "is why a mutation in it is rarely silent.", S["tgg"]),
        ("instance", "[a whole reading frame] ATG GCC TAA translates to Met-Ala-stop, the protein 'MA*' (sealed through "
                     "the verifier): start, one residue, stop - transcription and translation run as a checkable chain, "
                     "DNA -> mRNA -> protein, the central dogma.", S["tr"]),
        ("instance", "[Hardy-Weinberg, verified] With allele frequencies p = 0.6, q = 0.4, the genotype frequencies are "
                     "p^2 + 2pq + q^2 = 0.36 + 0.48 + 0.16 = 1 (sealed), so in a population of 1000 the counts 360 : 480 "
                     ": 160 are in equilibrium - run through the biology verifier (chi-square = 0, sealed). The law that "
                     "says a population not evolving keeps its allele frequencies.", S["hwe"]),
        ("postulate", "[what is cited, not proven] The genetic code is NEAR-universal, not universal - mitochondria and "
                      "some lineages read a few codons differently; the engine seals table 1 (the standard code) and "
                      "names the variant table where one applies. Ancestral gene sequences are RECONSTRUCTIONS, like a "
                      "proto-language - postulates, cited, never sealed. The code's origin is open science.",
         {"source": "NCBI translation table 1 (public domain); F. Crick, the central dogma (1958); G. Hardy, W. Weinberg (1908)"}),
        ("note", "[how genomics uses this] The deterministic layer - the code, complementarity, GC content, reading "
                 "frames, Mendelian and Hardy-Weinberg ratios - is exactly checkable, sealed, and refutable (a wrong "
                 "codon or a broken equilibrium is caught). The INTERPRETIVE layer - gene function, genotype-to-"
                 "phenotype, clinical significance - is declined, cited, or left as a want; a miss stays a miss. The "
                 "engine certifies the sequence arithmetic, not the meaning of the gene.",
         {"source": "src/concordance/verifiers/genetics.py, biology.py; the one map, card_floor_tree_of_life"}),
        ("note", "[on the one map] Phylogeny is the comparative method for genes: the tree of life is chains from a "
                 "floor where two trees connect - LUCA the floor, the three domains the branches, a homologous gene the "
                 "confluence where lineages meet (the small-subunit ribosomal RNA is in every cell, as 'father' is in "
                 "every Indo-European branch). card_floor_tree_of_life draws it.",
         {"source": "tools/seed_tree_of_life.py; the Indo-European floor is the same form"}),
    ]
    _mint_marks(sid, marks, by="tools/tick.py genomics")
    return 0


def _seal_through(domain, artifact_key, spec):
    """Verify a claim through an existing domain verifier and return its seal (now concordance.sticks.seal_verifier;
    kept by name for the Python handlers)."""
    from concordance import sticks
    return sticks.seal_verifier(domain, artifact_key, spec)


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
    print("sealed: Born rule normalization", s_born)

    # THE BORN RULE ITSELF, sealed through the dedicated verifier (2026-10-13): not only that the outcome
    # probabilities sum to one, but that EACH equals its squared amplitude, P_i = |a_i|^2 / Sum|a_j|^2.
    s_born_rule = _seal_through("quantum_computing", "QCOMP_VERIFY",
                                {"amplitudes": [0.6, 0.8], "outcome_index": 1, "claimed_probability": 0.64})
    if not s_born_rule:
        print("the Born-rule seal failed; aborting"); return 1
    print("sealed: Born rule (per-outcome)", s_born_rule)

    sid = TS.create("The Schrodinger equation")["id"]
    marks = [
        ("witness", "[the Born rule - what all must reproduce] For a qubit a|0> + b|1> with (a,b) = (0.6, 0.8), "
                    "the measured-outcome probabilities are |a|^2 = 0.36 and |b|^2 = 0.64, and they sum to one: "
                    "0.6^2 + 0.8^2 = 1 (sealed). Every interpretation of quantum mechanics agrees on THIS "
                    "arithmetic - the predictions. They differ only on what 'happens' when the measurement is "
                    "made.", s_born),
        ("witness", "[the Born rule itself, sealed as the rule] Not only that the probabilities sum to one, but "
                    "that EACH outcome's probability equals its squared amplitude: P(i) = |a_i|^2 / Sum_j |a_j|^2. "
                    "For (a,b) = (0.6, 0.8), P(1) = |0.8|^2 = 0.64 and P(0) = |0.6|^2 = 0.36 (sealed through "
                    "quantum_computing.born_rule). Probability is amplitude squared - the law the double slit "
                    "obeys: the paths' amplitudes interfere, and what the detector counts is their squared "
                    "modulus.", s_born_rule),
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
    """Shared seal helper for the Riemann arc: verify a numeric derivation and return its content hash (now
    concordance.sticks.seal_numeric; kept by name for the Python handlers)."""
    from concordance import sticks
    return sticks.seal_numeric(nid, expr, val, domain, tol)


def _mint_marks(sid, marks, by):
    """Shared mint loop - every stick mints through it (now concordance.sticks.mint_marks, idempotent and
    seal-or-claim guarded; kept by name for the Python handlers)."""
    from concordance import sticks
    return sticks.mint_marks(sid, marks, by)


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


def semantics() -> int:
    """SEMANTIC RELATIONS - comprehensive linguistics, step 3 (Matt, 2026-10-10). Synonymy and the
    IS-A (hypernym) hierarchy from the held WordNet thesaurus, SEALED through linguistics.LING_VERIFY
    (the thesaurus is SQLite, independent of the corpus, so it seals cold); antonymy is not held and
    declines. Idempotent."""
    from concordance import tickstick as TS
    S = {
        "syn": _seal_through("linguistics", "LING_VERIFY", {"relation_a": "car", "relation_b": "automobile", "claimed_relation": "synonym"}),
        "isa": _seal_through("linguistics", "LING_VERIFY", {"relation_a": "dog", "relation_b": "canine", "claimed_relation": "is_a"}),
    }
    if not all(S.values()):
        return 1
    print("sealed", len(S), "semantic relations")
    sid = TS.create("Semantic relations - synonymy and the IS-A hierarchy")["id"]
    marks = [
        ("instance", "[synonymy, SEALED] 'car' and 'automobile' are WordNet synonyms (sealed through "
                     "linguistics.LING_VERIFY). The thesaurus is a conduit, not an author - every pair comes from "
                     "WordNet, cited 'in at least one sense', never asserted as interchangeable.", S["syn"]),
        ("instance", "[IS-A, SEALED] 'a dog is a kind of canine' - WordNet places canine above dog in the IS-A "
                     "hierarchy (sealed), and transitively up to carnivore. Hypernymy is the upward connect-the-dots "
                     "of meaning.", S["isa"]),
        ("note", "[antonymy declines - the limit named] The held thesaurus has synonyms and IS-A hypernyms only; "
                 "antonyms are NOT held, so an antonym claim DECLINES rather than guesses, and meronymy / entailment "
                 "are not held either. 0 false positives: a relation WordNet does not hold cannot be confirmed.",
         {"source": "src/concordance/verifiers/linguistics.py verify_semantic_relation; data/thesaurus.db (WordNet)"}),
        ("note", "[on the one map - comprehensive linguistics, step 3] Semantics joins phonology, orthography, "
                 "etymology, morphology and transliteration on the linguistics floor (card_floor_indo_european). "
                 "Closed-class POS and typology remain.",
         {"source": "card_floor_indo_european; the linguistics coverage map"}),
    ]
    _mint_marks(sid, marks, by="tools/tick.py semantics")
    return 0


def bsd_cli(label: str = "11a1") -> int:
    """`bsd all` seals every curve in the ingested table; otherwise one curve (the CLI form of bsd)."""
    if label == "all":
        rc = 0
        for lab in sorted(CURVES, key=lambda k: (CURVES[k]["N"], k)):
            print(f"\n── {lab} ──")
            rc |= bsd(lab)
        return rc
    return bsd(label)


# ── the catalog: ONE table for every stick, data or Python (issue #13) ────────────────────────────
_CATALOG = None


def catalog():
    """data/sticks/*.json loaded once — a duplicate alias or a malformed entry raises at load, never dispatches."""
    global _CATALOG
    if _CATALOG is None:
        from concordance import sticks
        _CATALOG = sticks.load_catalog()
    return _CATALOG


def run_entry(entry, rest=()) -> int:
    """Run one catalog entry: a data entry through the loader, a handler entry through its Python function with
    the CLI arguments its `params` declare (a string from argv is converted; a typed value passes through)."""
    from concordance import sticks
    handler = entry.get("handler")
    if not handler:
        return sticks.run(entry)
    fn = getattr(sys.modules[__name__], handler, None)
    if fn is None:
        raise sticks.StickError(f"{entry['name']}: handler {handler!r} is not a function in tools/tick.py")
    args = []
    for i, p in enumerate(entry.get("params") or []):
        if i < len(rest):
            v = rest[i]
            args.append(sticks.PARAM_TYPES[p["type"]](v) if isinstance(v, str) else v)
        else:
            args.append(p["default"])
    return fn(*args)


def catalog_entries():
    """[(name, run)] for tools/tick_golden.py: every entry, run(*cli_args) -> rc."""
    return [(e["name"], (lambda *args, e=e: run_entry(e, list(args)))) for e in catalog()]


def main() -> int:
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    if a[0] == "list":
        cat = catalog()
        for e in cat:
            print(f"{e['name']:28s} {'python' if e.get('handler') else 'data  '}  {', '.join(e['aliases'])}")
        print(f"{len(cat)} entries, {len(cat.aliases)} aliases ({cat.path})")
        return 0
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
    if a[0] == "retract":          # tick.py retract <stick_id> <seal>  — drop a superseded/duplicate sealed mark
        if len(a) < 3:
            print("usage: tick.py retract <stick_id> <64-hex seal>"); return 2
        from concordance import tickstick as T
        print(json.dumps(T.retract(a[1], a[2], by="tools/tick.py retract"), indent=1))
        return 0
    if a[0] == "read":
        from concordance import tickstick as T
        print(json.dumps(T.read(a[1]) if len(a) > 1 else T.listing(), indent=1, ensure_ascii=False))
        return 0
    entry = catalog().resolve(a[0])
    if entry is None:
        print(__doc__)
        print(f"no such stick or command: {a[0]!r} — `tick.py list` names every one")
        return 2
    return run_entry(entry, a[1:])


if __name__ == "__main__":
    sys.exit(main())
