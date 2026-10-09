#!/usr/bin/env python3
"""Seed the CHAINS on the one map: the logarithm, and the seven Millennium problems, each as a lineage from a floor.

Matt, 2026-10-09: "logarithms fit here correct?" → "same" → "same with the millennium." The same form as the
Standard-Model chain (tools/seed_standard_model_chain.py) and the Millennium floor of joints
(tools/seed_millennium_chain.py), on the same graph, in the same two files:

  * a FLOOR per chain (card_floor_<slug>), part_of the one Floor of Discovery. Its PARTS are the chain's ROOTS - the
    two trees it began from (the Riemann chain: Euler's product and Legendre's count; the Navier-Stokes chain: Euler's
    ideal fluid and Navier's viscous one; ...).
  * the LINKS: records (card_chain_<key>) - each a work, cited by its record (authors, year, title, venue, DOI, a
    free copy where one exists, the license as found; the old ones public domain). A later work BUILDS_ON an earlier
    one, so the lineage walks forward from a root over `enables`.
  * the CONFLUENCE is FOUND, never declared: chains.intersect(root_a, root_b) over `enables` - Riemann 1859 is where
    the analytic and the arithmetic trees of the prime count become one; Stokes 1845 where the ideal and the viscous
    fluid do; Cook 1971 where computability and Boolean circuits do. The seed names the confluence it expects, and the
    pin checks the graph finds the same one.
  * the OPEN END: the Millennium question card (tools/seed_millennium_chain.py) hangs off its chain's floor
    (open_end_of) and BUILDS_ON the latest links, so the walk from the root ends at the question. The logarithm
    chain's open ends are all seven questions, and WHERE IT ENTERS each is an edge (connects_at) from the question to
    the link that carries the log into it - the explicit formula into Riemann, the height into BSD, the running
    coupling into Yang-Mills, the law of the wall into Navier-Stokes, the input length into P versus NP, the log pole
    into Hodge, the entropy into Poincare.

Records already carded by tools/card_millennium_sources.py (card_src_mill_*), the builders (card_builder_*) and
the questions (card_question_*) are REUSED by id, never recreated. Nothing is unified by us; a chain is success
building on success, found and cited. MERGE-writes through chains.merge_seed; idempotent.

    PYTHONPATH=src python tools/seed_chains.py           # merge into the two files
    PYTHONPATH=src python tools/seed_chains.py --check   # validate, write nothing
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DATA = Path(os.environ.get("CONCORDANCE_DATA_DIR", str(ROOT / "data")))

GLOBAL_FLOOR = "card_k_floor_of_discovery"
_DISALLOWED_LICENSE = ("cc-by-sa", "cc by-sa", "share-alike", "sharealike", "cc-by-nc", "cc by-nc", "non-commercial",
                       "noncommercial")

L_PD = "public domain (the author died more than a century ago, or the work was published before 1930)"
L_SPRINGER = "Springer TDM license — publisher's copyright, cited"
L_AMS = "AMS — publisher's copyright; free back-volume access on ams.org — cited"
L_APS = "APS default license — publisher's copyright, cited"
L_WILEY = "Wiley terms and conditions — publisher's copyright, cited"
L_CUP = "Cambridge University Press — publisher's copyright, cited"
L_ELSEVIER_OPEN = "Elsevier open archive user license — free to read"
L_ELSEVIER_TDM = "Elsevier TDM user license — publisher's copyright, cited"
L_DEGRUYTER = "De Gruyter — publisher's copyright, cited"
L_SIAM = "SIAM — publisher's copyright, cited"
L_ACM = "ACM copyright policy — publisher's copyright, cited"
L_NUMDAM = "free to read on Numdam — cited"
L_ARXIV = "arXiv.org non-exclusive license to distribute — free to read, cited"
L_EUCLID = "open access on Project Euclid — cited"
L_IOP = "IOP / Turpion — publisher's copyright, cited"
L_ROYAL = "Royal Society — publisher's copyright, cited"
L_BELL = "Bell System Technical Journal (Nokia Bell Labs archive) — cited"
L_RECORD = "cited by its record"


def _R(key, authors, year, title, venue, *, doi="", url="", free="", license=L_RECORD, domain="mathematics",
       what="") -> dict:
    """A link of a chain: a work, cited by its record."""
    return dict(key=key, authors=authors, year=year, title=title, venue=venue, doi=doi, url=url, free=free,
                license=license, domain=domain, what=what)


# ── THE RECORDS (one registry; a record may belong to several chains) ───────────────────────────────────────
RECORDS: List[dict] = [
    # the logarithm
    _R("napier_1614", "J. Napier", "1614", "Mirifici logarithmorum canonis descriptio", "Edinburgh, 1614",
       url="https://archive.org/details/mirificilogarith00napi", free="https://archive.org/details/mirificilogarith00napi",
       license=L_PD, what="the first table of logarithms, and the word"),
    _R("briggs_1624", "H. Briggs", "1624", "Arithmetica logarithmica", "London, 1624", license=L_PD,
       url="https://archive.org/details/arithmeticalogar00brig",
       what="base-ten logarithms, thirty thousand of them to fourteen places - the digits of a number as its logarithm"),
    _R("saint_vincent_1647", "G. de Saint-Vincent", "1647", "Opus geometricum quadraturae circuli et sectionum coni",
       "Antwerp, 1647", license=L_PD,
       what="the area under the hyperbola grows by equal amounts as x grows geometrically - the logarithm as an area "
            "(read as such by de Sarasa, 1649)"),
    _R("mercator_1668", "N. Mercator", "1668", "Logarithmotechnia", "London, 1668", license=L_PD,
       what="log(1 + x) = x - x^2/2 + x^3/3 - ... : the logarithm as a series"),
    _R("euler_1748", "L. Euler", "1748", "Introductio in analysin infinitorum (E101-E102)", "Lausanne, 1748",
       url="https://scholarlycommons.pacific.edu/euler-works/101/", free="https://scholarlycommons.pacific.edu/euler-works/101/",
       license=L_PD, what="e, and the exponential and the logarithm as inverse functions: the table-logarithm of Napier "
                          "and the hyperbola-logarithm of Saint-Vincent are one function"),
    _R("euler_1737", "L. Euler", "1737", "Variae observationes circa series infinitas (E72)",
       "Comm. Acad. Sci. Petrop. 9 (1737, publ. 1744) 160–188", url="https://scholarlycommons.pacific.edu/euler-works/72/",
       free="https://scholarlycommons.pacific.edu/euler-works/72/", license=L_PD,
       what="the Euler product over the primes; its logarithm turns the product into a sum, and the sum of 1/p diverges "
            "like log log x"),
    _R("boltzmann_1877", "L. Boltzmann", "1877",
       "Über die Beziehung zwischen dem zweiten Hauptsatze der mechanischen Wärmetheorie und der Wahrscheinlichkeitsrechnung",
       "Sitzungsber. Kais. Akad. Wiss. Wien, Math.-Naturwiss. Cl. 76 (1877) 373–435", license=L_PD, domain="physics",
       what="entropy as the logarithm of the number of microstates, S = k log W"),
    _R("shannon_1948", "C. E. Shannon", "1948", "A mathematical theory of communication",
       "Bell Syst. Tech. J. 27 (1948) 379–423", doi="10.1002/j.1538-7305.1948.tb01338.x",
       url="https://doi.org/10.1002/j.1538-7305.1948.tb01338.x", license=L_BELL, domain="computer_science",
       what="information as -sum p log p: the logarithm as the measure of a choice"),
    _R("gell_mann_low_1954", "M. Gell-Mann, F. E. Low", "1954", "Quantum electrodynamics at small distances",
       "Phys. Rev. 95 (1954) 1300–1312", doi="10.1103/PhysRev.95.1300", url="https://doi.org/10.1103/PhysRev.95.1300",
       license=L_APS, domain="physics", what="the renormalization group: a coupling that runs with the logarithm of the scale"),
    _R("karman_1930", "T. von Kármán", "1930", "Mechanische Ähnlichkeit und Turbulenz",
       "Nachr. Ges. Wiss. Göttingen, Math.-Phys. Kl. (1930) 58–76", license=L_RECORD, domain="physics",
       what="the law of the wall: the turbulent velocity profile is logarithmic in the distance from the wall"),
    _R("cobham_1965", "A. Cobham", "1965", "The intrinsic computational difficulty of functions",
       "Logic, Methodology and Philosophy of Science (Proc. 1964 Congress), North-Holland, 1965, 24–30",
       license=L_RECORD, domain="computer_science",
       what="feasible = polynomial in the LENGTH of the input, and the length of a number is its logarithm"),
    _R("deligne_1971", "P. Deligne", "1971", "Théorie de Hodge, II", "Publ. Math. IHÉS 40 (1971) 5–57",
       doi="10.1007/BF02684692", url="https://doi.org/10.1007/BF02684692",
       free="http://www.numdam.org/item/PMIHES_1971__40__5_0/", license=L_NUMDAM,
       what="mixed Hodge structures on the complement of a divisor, built on forms with logarithmic poles, dz/z"),
    _R("neron_1965", "A. Néron", "1965", "Quasi-fonctions et hauteurs sur les variétés abéliennes",
       "Ann. Math. 82 (1965) 249–331", doi="10.2307/1970644", url="https://doi.org/10.2307/1970644", license=L_RECORD,
       what="the canonical (Néron-Tate) height: the logarithm of the size of a point, made quadratic"),
    # Riemann
    _R("legendre_1798", "A.-M. Legendre", "1798", "Essai sur la théorie des nombres", "Paris, 1798 (2nd ed. 1808)",
       license=L_PD, what="the first published guess at the prime count: pi(x) is about x / (log x - 1.08366)"),
    _R("gauss_1849", "C. F. Gauss", "1849", "Letter to Encke, 24 December 1849 (the count made in 1792–93)",
       "Werke II, 444–447", license=L_PD,
       what="the logarithmic integral li(x) as the count of primes - read off the log tables he counted primes in"),
    _R("dirichlet_1837", "P. G. L. Dirichlet", "1837",
       "Beweis des Satzes, dass jede unbegrenzte arithmetische Progression ... unendlich viele Primzahlen enthält",
       "Abh. Königl. Preuss. Akad. Wiss. (1837) 45–81", license=L_PD,
       what="L-functions: Euler's product carried into arithmetic progressions"),
    _R("chebyshev_1852", "P. L. Chebyshev", "1852", "Mémoire sur les nombres premiers",
       "J. Math. Pures Appl. 17 (1852) 366–390", license=L_PD,
       what="pi(x) is between 0.92 and 1.11 times x / log x; Bertrand's postulate proven"),
    _R("riemann_1859", "B. Riemann", "1859", "Über die Anzahl der Primzahlen unter einer gegebenen Grösse",
       "Monatsber. Berliner Akad. (1859) 671–680", license=L_PD,
       url="https://www.claymath.org/collections/riemanns-1859-manuscript/",
       free="https://www.claymath.org/collections/riemanns-1859-manuscript/",
       what="zeta continued to the plane, the functional equation, the explicit formula through log zeta, and the hypothesis"),
    _R("hadamard_1896", "J. Hadamard", "1896",
       "Sur la distribution des zéros de la fonction zeta(s) et ses conséquences arithmétiques",
       "Bull. Soc. Math. France 24 (1896) 199–220", doi="10.24033/bsmf.545", url="https://doi.org/10.24033/bsmf.545",
       free="http://www.numdam.org/item/BSMF_1896__24__199_0/", license=L_NUMDAM,
       what="the prime number theorem: no zero on the line Re s = 1"),
    _R("vallee_poussin_1896", "C.-J. de la Vallée Poussin", "1896",
       "Recherches analytiques sur la théorie des nombres premiers", "Ann. Soc. Sci. Bruxelles 20 (1896) 183–256",
       license=L_PD, what="the prime number theorem, independently, with the first zero-free region"),
    _R("von_mangoldt_1905", "H. von Mangoldt", "1905", "Zur Verteilung der Nullstellen der Riemannschen Funktion xi(t)",
       "Math. Ann. 60 (1905) 1–19", doi="10.1007/BF01447494", url="https://doi.org/10.1007/BF01447494", license=L_SPRINGER,
       what="N(T) = (T/2pi) log(T/2pi) - T/2pi + O(log T): Riemann's count of the zeros proven"),
    _R("hardy_1914", "G. H. Hardy", "1914", "Sur les zéros de la fonction zeta(s) de Riemann",
       "C. R. Acad. Sci. Paris 158 (1914) 1012–1014", license=L_PD,
       what="infinitely many zeros lie on the critical line"),
    _R("selberg_1942", "A. Selberg", "1942", "On the zeros of Riemann's zeta-function",
       "Skr. Norske Vid.-Akad. Oslo I (1942) no. 10, 1–59", license=L_RECORD,
       what="a positive proportion of the zeros lie on the line"),
    _R("turing_1953", "A. M. Turing", "1953", "Some calculations of the Riemann zeta-function",
       "Proc. London Math. Soc. (3) 3 (1953) 99–117", doi="10.1112/plms/s3-3.1.99", url="https://doi.org/10.1112/plms/s3-3.1.99",
       license=L_WILEY, what="Turing's method: the count of zeros below T checked by the argument, so a computation can certify"),
    _R("levinson_1974", "N. Levinson", "1974", "More than one third of zeros of Riemann's zeta-function are on sigma = 1/2",
       "Adv. Math. 13 (1974) 383–436", doi="10.1016/0001-8708(74)90074-7", url="https://doi.org/10.1016/0001-8708(74)90074-7",
       license=L_ELSEVIER_OPEN, what="at least one third of the zeros are on the line"),
    _R("conrey_1989", "J. B. Conrey", "1989", "More than two fifths of the zeros of the Riemann zeta function are on the critical line",
       "J. reine angew. Math. 399 (1989) 1–26", doi="10.1515/crll.1989.399.1", url="https://doi.org/10.1515/crll.1989.399.1",
       license=L_DEGRUYTER, what="at least two fifths of the zeros are on the line"),
    # Birch and Swinnerton-Dyer
    _R("poincare_1901", "H. Poincaré", "1901", "Sur les propriétés arithmétiques des courbes algébriques",
       "J. Math. Pures Appl. (5) 7 (1901) 161–233", license=L_PD,
       what="the rational points of a cubic as a group, and the question of its rank"),
    _R("mordell_1922", "L. J. Mordell", "1922",
       "On the rational solutions of the indeterminate equations of the third and fourth degrees",
       "Proc. Cambridge Philos. Soc. 21 (1922) 179–192", license=L_PD,
       what="the group of rational points is finitely generated"),
    _R("weil_1929", "A. Weil", "1929", "L'arithmétique sur les courbes algébriques", "Acta Math. 52 (1929) 281–315",
       doi="10.1007/BF02592688", url="https://doi.org/10.1007/BF02592688", license=L_RECORD,
       what="Mordell's theorem for every abelian variety, by heights - the logarithm of the size of a point"),
    _R("hasse_1936", "H. Hasse", "1936", "Zur Theorie der abstrakten elliptischen Funktionenkörper I–III",
       "J. reine angew. Math. 175 (1936) 55–62, 69–88, 193–208", license=L_RECORD,
       what="the Riemann hypothesis for elliptic curves over finite fields: |a_p| <= 2 sqrt(p)"),
    _R("weil_1949", "A. Weil", "1949", "Numbers of solutions of equations in finite fields",
       "Bull. Amer. Math. Soc. 55 (1949) 497–508", doi="10.1090/S0002-9904-1949-09219-4",
       url="https://doi.org/10.1090/S0002-9904-1949-09219-4",
       free="https://www.ams.org/journals/bull/1949-55-05/S0002-9904-1949-09219-4/", license=L_AMS,
       what="the Weil conjectures stated; the local factors that become the L-function of a curve"),
    _R("cassels_1962", "J. W. S. Cassels", "1962", "Arithmetic on curves of genus 1. IV. Proof of the Hauptvermutung",
       "J. reine angew. Math. 211 (1962) 95–112", doi="10.1515/crll.1962.211.95", url="https://doi.org/10.1515/crll.1962.211.95",
       license=L_DEGRUYTER, what="the alternating pairing on Sha: if finite, its order is a square"),
    _R("birch_swinnerton_dyer_1965", "B. J. Birch, H. P. F. Swinnerton-Dyer", "1965", "Notes on elliptic curves. II",
       "J. reine angew. Math. 218 (1965) 79–108", doi="10.1515/crll.1965.218.79", url="https://doi.org/10.1515/crll.1965.218.79",
       license=L_DEGRUYTER, what="the conjecture: the rank is the order of vanishing of L(E, s) at s = 1, from EDSAC computations"),
    _R("coates_wiles_1977", "J. Coates, A. Wiles", "1977", "On the conjecture of Birch and Swinnerton-Dyer",
       "Invent. Math. 39 (1977) 223–251", doi="10.1007/BF01402975", url="https://doi.org/10.1007/BF01402975", license=L_SPRINGER,
       what="for curves with complex multiplication, L(E, 1) != 0 forces rank zero - the first theorem toward the conjecture"),
    _R("gross_zagier_1986", "B. Gross, D. Zagier", "1986", "Heegner points and derivatives of L-series",
       "Invent. Math. 84 (1986) 225–320", doi="10.1007/BF01388809", url="https://doi.org/10.1007/BF01388809", license=L_SPRINGER,
       what="L'(E, 1) is the height of a Heegner point: analytic rank one gives a point of infinite order"),
    _R("kolyvagin_1989", "V. A. Kolyvagin", "1989", "Finiteness of E(Q) and Sha(E, Q) for a subclass of Weil curves",
       "Math. USSR Izv. 32 (1989) 523–541", doi="10.1070/IM1989v032n03ABEH000779",
       url="https://doi.org/10.1070/IM1989v032n03ABEH000779", license=L_IOP,
       what="Euler systems: analytic rank zero or one gives the algebraic rank and finite Sha - the theorem for ranks 0 and 1"),
    _R("bhargava_skinner_zhang_2014", "M. Bhargava, C. Skinner, W. Zhang", "2014",
       "A majority of elliptic curves over Q satisfy the Birch and Swinnerton-Dyer conjecture", "arXiv (2014)",
       url="https://arxiv.org/abs/1407.1826", free="https://arxiv.org/abs/1407.1826", license=L_ARXIV,
       what="at least 66.48% of elliptic curves over Q, ordered by height, satisfy the conjecture"),
    # Navier-Stokes
    _R("euler_1757", "L. Euler", "1757", "Principes généraux du mouvement des fluides (E226)",
       "Mém. Acad. Sci. Berlin 11 (1757) 274–315", url="https://scholarlycommons.pacific.edu/euler-works/226/",
       free="https://scholarlycommons.pacific.edu/euler-works/226/", license=L_PD, domain="physics",
       what="the equations of an ideal fluid"),
    _R("navier_1822", "C.-L. Navier", "1822", "Mémoire sur les lois du mouvement des fluides",
       "Mém. Acad. R. Sci. Inst. France 6 (1823, read 1822) 389–440", license=L_PD, domain="physics",
       what="viscosity added to Euler's equations, from a molecular argument"),
    _R("stokes_1845", "G. G. Stokes", "1845", "On the theories of the internal friction of fluids in motion, and of the "
       "equilibrium and motion of elastic solids", "Trans. Cambridge Philos. Soc. 8 (1845) 287–319", license=L_PD,
       domain="physics", what="the Navier-Stokes equations as written today, derived from the stress of a continuum"),
    _R("reynolds_1883", "O. Reynolds", "1883", "An experimental investigation of the circumstances which determine "
       "whether the motion of water shall be direct or sinuous", "Philos. Trans. R. Soc. 174 (1883) 935–982",
       doi="10.1098/rstl.1883.0029", url="https://doi.org/10.1098/rstl.1883.0029", license=L_PD, domain="physics",
       what="the Reynolds number: the one dimensionless ratio that decides laminar from turbulent"),
    _R("kolmogorov_1941", "A. N. Kolmogorov", "1941", "The local structure of turbulence in incompressible viscous fluid "
       "for very large Reynolds numbers", "Dokl. Akad. Nauk SSSR 30 (1941) 301–305", license=L_RECORD, domain="physics",
       what="the inertial-range scaling and the dissipation scale eta = (nu^3/epsilon)^(1/4)"),
    _R("hopf_1951", "E. Hopf", "1951", "Über die Anfangswertaufgabe für die hydrodynamischen Grundgleichungen",
       "Math. Nachr. 4 (1951) 213–231", doi="10.1002/mana.3210040121", url="https://doi.org/10.1002/mana.3210040121",
       license=L_WILEY, what="weak solutions for all time on a bounded domain - Leray's theorem carried to domains"),
    # Yang-Mills
    _R("weyl_1929", "H. Weyl", "1929", "Elektron und Gravitation. I", "Z. Phys. 56 (1929) 330–352",
       doi="10.1007/BF01339504", url="https://doi.org/10.1007/BF01339504", license=L_SPRINGER, domain="physics",
       what="gauge invariance as the principle that gives the electromagnetic field"),
    _R("yang_mills_1954", "C. N. Yang, R. L. Mills", "1954", "Conservation of isotopic spin and isotopic gauge invariance",
       "Phys. Rev. 96 (1954) 191–195", doi="10.1103/PhysRev.96.191", url="https://doi.org/10.1103/PhysRev.96.191",
       license=L_APS, domain="physics", what="non-abelian gauge theory: the field equations the problem is about"),
    _R("wightman_1956", "A. S. Wightman", "1956", "Quantum field theory in terms of vacuum expectation values",
       "Phys. Rev. 101 (1956) 860–866", doi="10.1103/PhysRev.101.860", url="https://doi.org/10.1103/PhysRev.101.860",
       license=L_APS, domain="physics", what="the axioms: what it means for a quantum field theory to exist"),
    _R("osterwalder_schrader_1973", "K. Osterwalder, R. Schrader", "1973", "Axioms for Euclidean Green's functions",
       "Comm. Math. Phys. 31 (1973) 83–112", doi="10.1007/BF01645738", url="https://doi.org/10.1007/BF01645738",
       free="https://projecteuclid.org/euclid.cmp/1103858969", license=L_EUCLID, domain="physics",
       what="the Euclidean axioms, equivalent to Wightman's: the lattice's continuum limit has a target"),
    # P versus NP
    _R("turing_1936", "A. M. Turing", "1936", "On computable numbers, with an application to the Entscheidungsproblem",
       "Proc. London Math. Soc. (2) 42 (1937) 230–265", doi="10.1112/plms/s2-42.1.230",
       url="https://doi.org/10.1112/plms/s2-42.1.230", license=L_WILEY, domain="computer_science",
       what="the machine: what computation is"),
    _R("shannon_1949", "C. E. Shannon", "1949", "The synthesis of two-terminal switching circuits",
       "Bell Syst. Tech. J. 28 (1949) 59–98", doi="10.1002/j.1538-7305.1949.tb03624.x",
       url="https://doi.org/10.1002/j.1538-7305.1949.tb03624.x", license=L_BELL, domain="computer_science",
       what="circuit complexity: almost every Boolean function needs about 2^n / n gates"),
    _R("hartmanis_stearns_1965", "J. Hartmanis, R. E. Stearns", "1965", "On the computational complexity of algorithms",
       "Trans. Amer. Math. Soc. 117 (1965) 285–306", doi="10.1090/S0002-9947-1965-0170805-7",
       url="https://doi.org/10.1090/S0002-9947-1965-0170805-7",
       free="https://www.ams.org/journals/tran/1965-117-00/S0002-9947-1965-0170805-7/", license=L_AMS,
       domain="computer_science", what="time as a resource: the hierarchy of complexity classes"),
    _R("edmonds_1965", "J. Edmonds", "1965", "Paths, trees, and flowers", "Canad. J. Math. 17 (1965) 449–467",
       doi="10.4153/CJM-1965-045-4", url="https://doi.org/10.4153/CJM-1965-045-4", license=L_CUP, domain="computer_science",
       what="a 'good' algorithm is a polynomial-time one: the class P named by its intent"),
    _R("baker_gill_solovay_1975", "T. Baker, J. Gill, R. Solovay", "1975", "Relativizations of the P =? NP question",
       "SIAM J. Comput. 4 (1975) 431–442", doi="10.1137/0204037", url="https://doi.org/10.1137/0204037", license=L_SIAM,
       domain="computer_science", what="the first barrier: no relativizing proof can settle the question"),
    _R("razborov_rudich_1997", "A. A. Razborov, S. Rudich", "1997", "Natural proofs",
       "J. Comput. System Sci. 55 (1997) 24–35", doi="10.1006/jcss.1997.1494", url="https://doi.org/10.1006/jcss.1997.1494",
       license=L_ELSEVIER_OPEN, domain="computer_science", what="the second barrier: natural proofs cannot, if one-way functions exist"),
    _R("aaronson_wigderson_2009", "S. Aaronson, A. Wigderson", "2009", "Algebrization: a new barrier in complexity theory",
       "ACM Trans. Comput. Theory 1 (2009) 2:1–54", doi="10.1145/1490270.1490272", url="https://doi.org/10.1145/1490270.1490272",
       license=L_ACM, domain="computer_science", what="the third barrier: algebrizing proofs cannot"),
    # Hodge
    _R("riemann_1857", "B. Riemann", "1857", "Theorie der Abel'schen Functionen", "J. reine angew. Math. 54 (1857) 115–155",
       license=L_PD, what="the periods of integrals on a curve: the transcendental side of algebraic geometry"),
    _R("lefschetz_1924", "S. Lefschetz", "1924", "L'analysis situs et la géométrie algébrique", "Gauthier-Villars, Paris, 1924",
       license=L_PD, what="the topology of an algebraic variety, and the (1,1) theorem: the conjecture is true for divisors"),
    _R("de_rham_1931", "G. de Rham", "1931", "Sur l'analysis situs des variétés à n dimensions",
       "J. Math. Pures Appl. (9) 10 (1931) 115–200", license=L_PD,
       what="cohomology by differential forms: the bridge between forms and topology"),
    _R("hodge_1941", "W. V. D. Hodge", "1941", "The Theory and Applications of Harmonic Integrals",
       "Cambridge University Press, 1941", license=L_CUP,
       what="every cohomology class has a unique harmonic form; the (p, q) decomposition the conjecture is stated in"),
    _R("griffiths_1968", "P. A. Griffiths", "1968", "Periods of integrals on algebraic manifolds, I",
       "Amer. J. Math. 90 (1968) 568–626", doi="10.2307/2373545", url="https://doi.org/10.2307/2373545", license=L_RECORD,
       what="variation of Hodge structure: how the decomposition moves in a family"),
    # Poincare
    _R("poincare_1904", "H. Poincaré", "1904", "Cinquième complément à l'analysis situs",
       "Rend. Circ. Mat. Palermo 18 (1904) 45–110", doi="10.1007/BF03014091", url="https://doi.org/10.1007/BF03014091",
       license=L_PD, what="the homology sphere that is not a sphere, and the question: is a simply connected closed "
                          "3-manifold the sphere?"),
    _R("eells_sampson_1964", "J. Eells, J. H. Sampson", "1964", "Harmonic mappings of Riemannian manifolds",
       "Amer. J. Math. 86 (1964) 109–160", doi="10.2307/2373037", url="https://doi.org/10.2307/2373037", license=L_RECORD,
       what="the heat-flow method: deform a map toward a harmonic one - the template of the Ricci flow"),
    _R("thurston_1982", "W. P. Thurston", "1982", "Three dimensional manifolds, Kleinian groups and hyperbolic geometry",
       "Bull. Amer. Math. Soc. 6 (1982) 357–381", doi="10.1090/S0273-0979-1982-15003-0",
       url="https://doi.org/10.1090/S0273-0979-1982-15003-0",
       free="https://www.ams.org/journals/bull/1982-06-03/S0273-0979-1982-15003-0/", license=L_AMS,
       what="the geometrization conjecture: every closed 3-manifold is cut into eight geometries - Poincaré is a corollary"),
    _R("hamilton_1995", "R. S. Hamilton", "1995", "The formation of singularities in the Ricci flow",
       "Surveys in Differential Geometry 2 (1995) 7–136", doi="10.4310/SDG.1993.v2.n1.a2",
       url="https://doi.org/10.4310/SDG.1993.v2.n1.a2", license=L_RECORD,
       what="the program: run the flow, understand the singularities, cut, continue - what Perelman completed"),
]

REC: Dict[str, dict] = {r["key"]: r for r in RECORDS}
assert len(REC) == len(RECORDS), "duplicate record keys"


def rid(key: str) -> str:
    return f"card_chain_{key}"


def src(key: str) -> str:
    return f"card_src_mill_{key}"      # tools/card_millennium_sources.py


def q(slug: str) -> str:
    return f"card_question_{slug}"     # tools/seed_millennium_chain.py


MAXWELL = "card_builder_james_clerk_maxwell"

# ── THE CHAINS ──────────────────────────────────────────────────────────────────────────────────────────────
# slug, title, body, roots (part_of the floor), edges (later builds_on earlier), the open end(s), the confluence the
# seed expects the graph to FIND (intersect of the first two roots over enables), the log's entries (end -> link).
CHAINS: List[dict] = [
    dict(slug="logarithm",
         title="The logarithm - the instrument the joints share",
         body=("Two trees: Napier's table (1614) and Saint-Vincent's hyperbola (1647) - a number's logarithm as a tabulated "
               "count, and as an area. They become one function in Euler's Introductio (1748): e, and exp and log as "
               "inverses. From there the logarithm enters each of the seven questions as the instrument that turns a "
               "product into a sum (log zeta, Euler 1737 and Riemann 1859), a size into a count (the height of a point, "
               "Weil 1929 and Néron 1965), a scale into a step (the running coupling, Gell-Mann-Low 1954), a profile into a "
               "line (the law of the wall, von Kármán 1930), a number into its length (Cobham 1965), a pole into a form "
               "(Deligne 1971), a count of states into an entropy (Boltzmann 1877, Shannon 1948, Perelman 2002). Found, "
               "cited; sealed where it is arithmetic (tools/tick.py logarithm_chain)."),
         bands=["logarithm", "napier", "euler", "entropy", "instrument"],
         roots=["napier_1614", "saint_vincent_1647"],
         edges=[("briggs_1624", "napier_1614"), ("mercator_1668", "saint_vincent_1647"),
                ("euler_1748", "briggs_1624"), ("euler_1748", "mercator_1668"),
                ("euler_1737", "mercator_1668"), ("riemann_1859", "euler_1737"), ("von_mangoldt_1905", "riemann_1859"),
                ("boltzmann_1877", "euler_1748"), ("shannon_1948", "boltzmann_1877"),
                ("gell_mann_low_1954", "euler_1748"), ("karman_1930", "euler_1748"), ("cobham_1965", "briggs_1624"),
                ("deligne_1971", "euler_1748"), ("weil_1929", "euler_1748"), ("neron_1965", "weil_1929"),
                (src("perelman_2002"), "shannon_1948"), (src("gross_wilczek_1973"), "gell_mann_low_1954"),
                (src("silverman_1988"), "neron_1965")],
         ends=["riemann", "bsd", "navier_stokes", "yang_mills", "p_vs_np", "hodge", "poincare"],
         expect_confluence="euler_1748",
         entries=[("riemann", "riemann_1859", "the explicit formula runs through log zeta - the product over the primes "
                   "turned into a sum (sealed on the stick: Li's coefficients from log xi)"),
                  ("riemann", "von_mangoldt_1905", "the zero count is (T/2pi) log(T/2pi) - sealed on the stick at the "
                   "100,000th zero"),
                  ("bsd", "neron_1965", "the height of a rational point is the logarithm of its size; the regulator "
                   "sealed on 37a1 is a determinant of those logs"),
                  ("yang_mills", src("gross_wilczek_1973"), "the coupling runs as one over the logarithm of the scale - "
                   "sealed on the stick (alpha_s at 10 GeV)"),
                  ("navier_stokes", "karman_1930", "the law of the wall: the turbulent profile is logarithmic in the "
                   "distance from the wall (sealed: u+ at y+ = 100)"),
                  ("p_vs_np", "cobham_1965", "the length of the input is the logarithm of the number; polynomial means "
                   "polynomial in that log (sealed: the digits of 2^64)"),
                  ("hodge", "deligne_1971", "mixed Hodge theory is built on forms with logarithmic poles, dz/z"),
                  ("poincare", src("perelman_2002"), "the entropy formula: Perelman's W functional is a log-Sobolev "
                   "inequality, the entropy minus the integral of u log u (sealed: the entropy of one fair coin, log 2)")]),
    dict(slug="riemann",
         title="The Riemann chain - from Euler's product and Legendre's count to the critical line",
         body=("Two trees. The analytic: Euler's product over the primes (1737), Dirichlet's L-functions (1837). The "
               "arithmetic: Legendre's guess at the prime count (1798), Gauss's logarithmic integral (counted 1792, "
               "written 1849), Chebyshev's bounds (1852). They become one in Riemann's eight pages of 1859: zeta on the "
               "whole plane, the explicit formula, the hypothesis. Then the prime number theorem (Hadamard, de la Vallée "
               "Poussin, 1896), the zero count (von Mangoldt 1905), zeros on the line - infinitely many (Hardy 1914), a "
               "positive proportion (Selberg 1942), a third (Levinson 1974), two fifths (Conrey 1989) - and the "
               "computations: Turing's method (1953), Odlyzko's tables (1987), Platt and Trudgian to 3·10^12 (2021). "
               "The open end stands on the last links."),
         bands=["riemann", "primes", "zeta", "prime number theorem"],
         roots=["euler_1737", "legendre_1798"],
         edges=[("dirichlet_1837", "euler_1737"), ("gauss_1849", "legendre_1798"), ("chebyshev_1852", "legendre_1798"),
                ("riemann_1859", "dirichlet_1837"), ("riemann_1859", "gauss_1849"), ("riemann_1859", "chebyshev_1852"),
                ("hadamard_1896", "riemann_1859"), ("vallee_poussin_1896", "riemann_1859"),
                ("von_mangoldt_1905", "riemann_1859"), ("hardy_1914", "riemann_1859"), ("selberg_1942", "hardy_1914"),
                ("levinson_1974", "selberg_1942"), ("conrey_1989", "levinson_1974"), ("turing_1953", "von_mangoldt_1905"),
                (src("odlyzko_1987"), "turing_1953"), (src("platt_trudgian_2021"), src("odlyzko_1987")),
                (q("riemann"), "conrey_1989"), (q("riemann"), src("platt_trudgian_2021"))],
         ends=["riemann"], expect_confluence="riemann_1859", entries=[]),
    dict(slug="bsd",
         title="The Birch and Swinnerton-Dyer chain - from the group of rational points to the L-function",
         body=("Two trees. The arithmetic: Poincaré's group law on the rational points (1901), Mordell's finite generation "
               "(1922), Weil's heights (1929), the canonical height (Néron 1965). The analytic: Hasse's Riemann hypothesis "
               "for a curve over a finite field (1936), Weil's conjectures and the local factors (1949), modularity "
               "(Wiles 1995). They become one in the conjecture itself (Birch and Swinnerton-Dyer 1965): the rank is the "
               "order of vanishing of L(E, s). Then Cassels' pairing on Sha (1962), Coates-Wiles (1977), Gross-Zagier "
               "(1986), Kolyvagin (1989) - ranks zero and one are theorems - and a majority of curves (2014). The open "
               "end is rank two and above."),
         bands=["elliptic curves", "L-functions", "heights", "rank"],
         roots=["poincare_1901", "hasse_1936"],
         edges=[("mordell_1922", "poincare_1901"), ("weil_1929", "mordell_1922"), ("neron_1965", "weil_1929"),
                ("weil_1949", "hasse_1936"), (src("wiles_1995"), "weil_1949"), ("cassels_1962", "weil_1929"),
                ("birch_swinnerton_dyer_1965", "neron_1965"), ("birch_swinnerton_dyer_1965", "weil_1949"),
                ("coates_wiles_1977", "birch_swinnerton_dyer_1965"), ("gross_zagier_1986", "birch_swinnerton_dyer_1965"),
                ("kolyvagin_1989", "gross_zagier_1986"), ("bhargava_skinner_zhang_2014", "kolyvagin_1989"),
                ("bhargava_skinner_zhang_2014", src("wiles_1995")), (src("silverman_1988"), "neron_1965"),
                (q("bsd"), "kolyvagin_1989"), (q("bsd"), "bhargava_skinner_zhang_2014"), (q("bsd"), "cassels_1962")],
         ends=["bsd"], expect_confluence="birch_swinnerton_dyer_1965", entries=[]),
    dict(slug="navier_stokes",
         title="The Navier-Stokes chain - from the ideal fluid and the viscous one to the regularity question",
         body=("Two trees. Euler's ideal fluid (1757) and Navier's viscous correction (1822) become one in Stokes' "
               "derivation from the stress of a continuum (1845): the equations as written today. Then Reynolds' number "
               "(1883), Leray's weak solutions for all time (1934), Kolmogorov's scaling (1941), Hopf on domains (1951), "
               "Ladyzhenskaya closing two dimensions (1959), Fujita-Kato's strong solutions (1964), partial regularity "
               "(Caffarelli-Kohn-Nirenberg 1982), the blow-up criterion (Beale-Kato-Majda 1984), Tao's averaged blow-up "
               "(2016). The open end: three dimensions, large data."),
         bands=["fluids", "navier-stokes", "turbulence", "regularity"],
         roots=["euler_1757", "navier_1822"],
         edges=[("stokes_1845", "euler_1757"), ("stokes_1845", "navier_1822"), ("reynolds_1883", "stokes_1845"),
                (src("leray_1934"), "stokes_1845"), ("kolmogorov_1941", "reynolds_1883"), ("hopf_1951", src("leray_1934")),
                (src("ladyzhenskaya_1959"), "hopf_1951"), (src("fujita_kato_1964"), src("leray_1934")),
                (src("caffarelli_kohn_nirenberg_1982"), src("leray_1934")), (src("beale_kato_majda_1984"), "stokes_1845"),
                (src("tao_2016"), src("leray_1934")), ("karman_1930", "reynolds_1883"),
                (q("navier_stokes"), src("caffarelli_kohn_nirenberg_1982")), (q("navier_stokes"), src("beale_kato_majda_1984")),
                (q("navier_stokes"), src("tao_2016"))],
         ends=["navier_stokes"], expect_confluence="stokes_1845", entries=[]),
    dict(slug="yang_mills",
         title="The Yang-Mills chain - from the gauge field and the axioms to the mass gap",
         body=("Two trees. The gauge field: Maxwell, Weyl's gauge principle (1929), Yang and Mills' non-abelian field "
               "(1954). The axioms: Wightman's (1956) and Osterwalder-Schrader's Euclidean ones (1973) - what it means for "
               "the theory to exist. They become one in the problem as Jaffe and Witten state it (2000). Along the gauge "
               "tree: asymptotic freedom (Gross-Wilczek, Politzer 1973), Wilson's lattice (1974), the gap proven at strong "
               "coupling (Osterwalder-Seiler 1978), the glueball spectrum measured (Morningstar-Peardon 1999). The open "
               "end: existence on R^4 and the continuum limit."),
         bands=["gauge theory", "yang-mills", "mass gap", "lattice"],
         roots=[MAXWELL, "wightman_1956"],
         edges=[("weyl_1929", MAXWELL), ("yang_mills_1954", "weyl_1929"), ("osterwalder_schrader_1973", "wightman_1956"),
                (src("jaffe_witten_2000"), "yang_mills_1954"), (src("jaffe_witten_2000"), "osterwalder_schrader_1973"),
                (src("gross_wilczek_1973"), "yang_mills_1954"), (src("politzer_1973"), "yang_mills_1954"),
                (src("wilson_1974"), "yang_mills_1954"), (src("osterwalder_seiler_1978"), src("wilson_1974")),
                (src("osterwalder_seiler_1978"), "osterwalder_schrader_1973"),
                (src("morningstar_peardon_1999"), src("wilson_1974")), (src("flag_2021"), src("morningstar_peardon_1999")),
                (q("yang_mills"), src("jaffe_witten_2000")), (q("yang_mills"), src("osterwalder_seiler_1978")),
                (q("yang_mills"), src("morningstar_peardon_1999"))],
         ends=["yang_mills"], expect_confluence=src("jaffe_witten_2000"), entries=[]),
    dict(slug="p_vs_np",
         title="The P versus NP chain - from the machine and the circuit to the three barriers",
         body=("Two trees. Computability: Turing's machine (1936), time as a resource (Hartmanis-Stearns 1965), feasible "
               "as polynomial in the input's length (Cobham 1965, Edmonds 1965). Circuits: Shannon's count of gates "
               "(1949). They become one in Cook's theorem (1971): satisfiability is NP-complete. Then Karp's twenty-one "
               "(1972), the three barriers - relativization (1975), natural proofs (1997), algebrization (2009) - the "
               "circuit lower bounds (Blum 1984, Find-Golovnev-Hirsch-Kulikov 2016), the separation past the barriers "
               "(Williams 2011), the road not excluded (Mulmuley-Sohoni 2001). The open end stands on the last three."),
         bands=["complexity", "p vs np", "circuits", "barriers"],
         roots=["turing_1936", "shannon_1949"],
         edges=[("hartmanis_stearns_1965", "turing_1936"), ("cobham_1965", "turing_1936"), ("edmonds_1965", "turing_1936"),
                (src("cook_1971"), "hartmanis_stearns_1965"), (src("cook_1971"), "cobham_1965"), (src("cook_1971"), "shannon_1949"),
                (src("karp_1972"), src("cook_1971")), ("baker_gill_solovay_1975", src("cook_1971")),
                ("razborov_rudich_1997", "baker_gill_solovay_1975"), ("aaronson_wigderson_2009", "razborov_rudich_1997"),
                (src("blum_1984"), "shannon_1949"), (src("fghk_2016"), src("blum_1984")),
                (src("williams_2011"), "aaronson_wigderson_2009"), (src("mulmuley_sohoni_2001"), src("karp_1972")),
                (src("davis_logemann_loveland_1962"), "turing_1936"),
                (q("p_vs_np"), src("williams_2011")), (q("p_vs_np"), src("fghk_2016")), (q("p_vs_np"), src("mulmuley_sohoni_2001"))],
         ends=["p_vs_np"], expect_confluence=src("cook_1971"), entries=[]),
    dict(slug="hodge",
         title="The Hodge chain - from periods and topology to the classes that are not cycles",
         body=("Two trees. The transcendental: Riemann's periods (1857). The topological: Lefschetz's analysis situs of "
               "a variety and the (1,1) theorem (1924), de Rham's forms (1931). They become one in Hodge's harmonic "
               "integrals (1941): every class has a harmonic form, and the (p, q) decomposition. Then the conjecture as "
               "stated (Hodge 1950), the integral form refuted (Atiyah-Hirzebruch 1962), variations of Hodge structure "
               "(Griffiths 1968), mixed Hodge theory (Deligne 1971), the Kähler form refuted (Voisin 2002), the "
               "statement as the Clay Institute keeps it (Deligne 2000). The open end: the rational projective case from "
               "dimension four."),
         bands=["hodge", "algebraic cycles", "harmonic forms", "periods"],
         roots=["riemann_1857", "lefschetz_1924"],
         edges=[("de_rham_1931", "lefschetz_1924"), ("hodge_1941", "riemann_1857"), ("hodge_1941", "de_rham_1931"),
                (src("hodge_1950"), "hodge_1941"), (src("atiyah_hirzebruch_1962"), src("hodge_1950")),
                ("griffiths_1968", "hodge_1941"), ("deligne_1971", "hodge_1941"), (src("voisin_2002"), src("hodge_1950")),
                (src("deligne_2000"), src("hodge_1950")), (src("lewis_1999"), src("hodge_1950")),
                (q("hodge"), src("deligne_2000")), (q("hodge"), src("voisin_2002")), (q("hodge"), src("atiyah_hirzebruch_1962"))],
         ends=["hodge"], expect_confluence="hodge_1941", entries=[]),
    dict(slug="poincare",
         title="The Poincare chain - from the homology sphere and the heat flow to the closed question",
         body=("Two trees. Topology: Poincaré's homology sphere and the question (1904), Thurston's geometrization "
               "(1982). Geometric analysis: the heat-flow method of Eells and Sampson (1964), Hamilton's Ricci flow "
               "(1982). They become one in Hamilton's program for the singularities (1995), which Perelman completed "
               "(2002-2003); the write-ups of Kleiner-Lott, Morgan-Tian and Cao-Zhu are the receipts. The end is CLOSED."),
         bands=["poincare", "ricci flow", "geometrization", "three-manifolds"],
         roots=["poincare_1904", "eells_sampson_1964"],
         edges=[("thurston_1982", "poincare_1904"), (src("hamilton_1982"), "eells_sampson_1964"),
                ("hamilton_1995", src("hamilton_1982")), ("hamilton_1995", "thurston_1982"),
                (src("perelman_2002"), "hamilton_1995"), (src("perelman_2003a"), src("perelman_2002")),
                (src("perelman_2003b"), src("perelman_2003a")), (src("kleiner_lott_2008"), src("perelman_2003b")),
                (src("morgan_tian_2007"), src("perelman_2003b")), (src("cao_zhu_2006"), src("perelman_2003b")),
                (q("poincare"), src("kleiner_lott_2008")), (q("poincare"), src("cao_zhu_2006"))],
         ends=["poincare"], expect_confluence="hamilton_1995", entries=[]),
]


def _license_ok(label: str) -> bool:
    t = (label or "").lower()
    return not any(m in t for m in _DISALLOWED_LICENSE)


def record_card(r: dict) -> dict:
    if not _license_ok(r["license"]):
        raise ValueError(f"refusing to mint {r['key']!r} under a disallowed license: {r['license']!r}")
    parts = [f"{r['authors']} ({r['year']}). {r['title']}. {r['venue']}."]
    if r["doi"]:
        parts.append(f"DOI {r['doi']}.")
    if r["url"]:
        parts.append(f"Canonical: {r['url']}.")
    parts.append(f"Free copy: {r['free']}." if r["free"] else "Cited by its record.")
    parts.append(f"License as found: {r['license']}.")
    if r["what"]:
        parts.append(f"What it gave the chain: {r['what']}.")
    first = r["authors"].split(",")[0].split()[-1]
    return {
        "id": rid(r["key"]), "kind": "reference", "title": f"{first} {r['year'][:4]} — {r['title']}"[:180],
        "body": " ".join(parts),
        "source": {"label": f"{r['authors']} ({r['year']}), {r['venue'][:120]}", "url": r["url"], "domain": r["domain"],
                   "authority_tier": "reference"},
        "shelf": "codex", "box": "chain",
        "bands": ["chain", "record", r["year"][:4], first.lower(), r["domain"].replace("_", " ")],
        "subject": r["title"][:160],
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def floor_card(c: dict) -> dict:
    return {
        "id": f"card_floor_{c['slug']}", "kind": "note", "title": c["title"], "body": c["body"],
        "source": {"label": "Narrow Highway - a chain on the one map (operator seed)", "url": "",
                   "ref": "docs/MILLENNIUM_PREPAREDNESS.md", "authority_tier": "engine_derived"},
        "shelf": "codex", "box": "floor", "bands": ["floor", "chain", "two trees"] + c["bands"],
        "subject": c["title"],
        "connections": [], "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def _node(x: str) -> str:
    """A record key -> its card id; an id (card_src_mill_*, card_builder_*, card_question_*) passes through."""
    return x if x.startswith("card_") else rid(x)


def _edge(a: str, b: str, rel: str, ev: str) -> dict:
    return {"a": a, "b": b, "relationship": rel, "evidence": ev}


CARDS: List[dict] = [record_card(r) for r in RECORDS] + [floor_card(c) for c in CHAINS]


def _bridges() -> List[dict]:
    out: List[dict] = []
    for c in CHAINS:
        floor = f"card_floor_{c['slug']}"
        out.append(_edge(floor, GLOBAL_FLOOR, "part_of", f"the {c['slug'].replace('_', ' ')} chain rests on the one Floor of Discovery"))
        for r in c["roots"]:
            out.append(_edge(_node(r), floor, "part_of", "a root of this chain - one of the two trees it began from"))
        for later, earlier in c["edges"]:
            lw = REC.get(later, {}).get("what") if not later.startswith("card_") else ""
            out.append(_edge(_node(later), _node(earlier), "builds_on", (lw or "a later work standing on an earlier one")[:300]))
        for e in c["ends"]:
            out.append(_edge(q(e), floor, "open_end_of", "the open question this chain reaches"))
        for e, link, ev in c["entries"]:
            out.append(_edge(q(e), _node(link), "connects_at", f"where the logarithm enters: {ev}"))
    return out


BRIDGES: List[dict] = _bridges()
FLOORS: List[str] = [f"card_floor_{c['slug']}" for c in CHAINS]


def known_ids(extra=()) -> set:
    ids = {c["id"] for c in CARDS} | {GLOBAL_FLOOR, MAXWELL} | set(extra)
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import card_millennium_sources as M
        import seed_millennium_chain as S2
        ids |= {M.card_id(s["key"]) for s in M.SOURCES} | {c["id"] for c in S2.CARDS}
    except Exception as e:  # pragma: no cover - the check reports it
        print("could not load the sibling seeds:", e)
    return ids


def _validate() -> List[str]:
    errs = []
    ids = known_ids()
    for e in BRIDGES:
        for end in ("a", "b"):
            if e[end] not in ids:
                errs.append(f"edge endpoint unknown: {e[end]} ({e['relationship']})")
    doi = re.compile(r"^10\.\d{4,9}/\S+$")
    for r in RECORDS:
        if r["doi"] and not doi.match(r["doi"]):
            errs.append(f"malformed DOI on {r['key']}: {r['doi']}")
    for c in CHAINS:
        if _node(c["expect_confluence"]) not in ids:
            errs.append(f"{c['slug']}: expected confluence unknown")
    return errs


def main() -> int:
    check = "--check" in sys.argv[1:]
    errs = _validate()
    for e in errs:
        print("  VALIDATION:", e)
    if check:
        print(f"[check] {len(CARDS)} cards ({len(RECORDS)} records + {len(CHAINS)} floors), {len(BRIDGES)} bridges; "
              f"{'OK' if not errs else 'ERRORS'}")
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
