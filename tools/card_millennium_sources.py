#!/usr/bin/env python3
"""Card the Millennium sources — the papers, tables and problem descriptions the seven sticks cite.

Matt, 2026-10-09: "find all 17 and add them." / "find" — and the standing rule of the Millennium loop:
"Anything you retrieve and use needs to be included."

The seven Millennium sticks (tools/tick.py: riemann, bsd_formula, navier_stokes_next, yang_mills_next,
p_versus_np_next, hodge_next, poincare_next) cite their links by name. Each attempt opened WANTS for the texts
behind those names. This tool cards what the search located: one reference card per source — the bibliographic
record (authors, year, title, venue, DOI / arXiv number), the canonical page and the free copy where one exists,
the LICENSE AS FOUND (Crossref's license field, the publisher's statement, or "no terms stated"), the want it
fills and the stick it serves. The cards carry METADATA, never the papers' text: a paper is cited by its record,
not copied. Two found TABLES (Odlyzko's zeros, Cremona's ecdata) are held on the box's untrusted ark and
cross-checked by tools/tick.py sources_crosscheck; the Odlyzko numbers are not carded (no terms stated), the
Cremona rows used are quoted under the Artistic License 2.0 with attribution.

Discipline: gather, don't author — every field below was read from the source's own record (Crossref, arXiv,
the publisher's or author's page) and nothing is generated. The license gate of tools/card_sources.py is
mirrored here: share-alike and non-commercial are refused at the mint (the LMFDB, cited as a cross-reference by
CURVES_BSD_INPUTS, is NOT carded for that reason — see the Cremona card). Corrections are recorded, never
silently applied: the FGHK want named arXiv:1512.00334, which is an astronomy paper; the paper is ECCC TR15-166.

Idempotent; deterministic ids; the same bytes on every platform.

    CONCORDANCE_DATA_DIR=... python tools/card_millennium_sources.py [--dry-run]

Writes <CONCORDANCE_DATA_DIR or data>/millennium_cards.jsonl: 1 spine (part_of the Floor) + the cards.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

FLOOR = "card_k_floor_of_discovery"
SPINE = "card_spine_millennium_sources"
_slug = re.compile(r"[^a-z0-9]+")

# The mint-side license gate, mirrored from tools/card_sources.py (red team 2026-08-06): PD / CC0 / CC-BY with
# attribution, a publisher's record cited by its metadata — never share-alike, never non-commercial.
_DISALLOWED_LICENSE = ("cc-by-sa", "cc by-sa", "share-alike", "sharealike",
                       "cc-by-nc", "cc by-nc", "non-commercial", "noncommercial")

STICKS = {
    "riemann": ("stick_riemann_hypothesis", "Riemann hypothesis"),
    "bsd": ("stick_birch_and_swinnerton_dyer_conjecture", "Birch and Swinnerton-Dyer"),
    "navier_stokes": ("stick_navier_stokes_existence_and_smoothness", "Navier-Stokes"),
    "yang_mills": ("stick_yang_mills_existence_and_mass_gap", "Yang-Mills"),
    "p_vs_np": ("stick_p_versus_np", "P versus NP"),
    "hodge": ("stick_hodge_conjecture", "Hodge"),
    "poincare": ("stick_poincare_conjecture", "Poincare"),
}
DOMAIN = {"riemann": "mathematics", "bsd": "mathematics", "navier_stokes": "mathematics", "yang_mills": "physics",
          "p_vs_np": "computer_science", "hodge": "mathematics", "poincare": "mathematics"}

# The wants the attempts opened on the box (data/wants.jsonl, 2026-10-09). A SOURCE want closes when its texts are
# carded; a BUILD want (a calculator, a door) only receives its method's source as an option and stays open.
WANTS = {
    "riemann_tables": "want_1b2955cde1bd", "riemann_platt": "want_eb1f183b8f7c",
    "riemann_os": "want_cafab309bf42", "riemann_li": "want_779aa6668137",
    "bsd_tables": "want_bb4f38c140c7", "bsd_heights": "want_03781a9b3ac3",
    "ns_sources": "want_a42700904af4",
    "ns_build": "want_ecc2f1c3c14c",
    "ym_sources": "want_cc6c3322438e", "ym_build": "want_d0092fd4da32",
    "pnp_sources": "want_54d4b9cd0f1a", "pnp_barriers": "want_855712e97c3a", "pnp_build": "want_9dbba8ee0e18",
    "hodge_sources": "want_740fff9d8b2e", "hodge_build": "want_e8ea86cae2e6",
    "poincare_sources": "want_96d3c27cb7a8",
}
BUILD_WANTS = {"want_d0092fd4da32", "want_9dbba8ee0e18", "want_e8ea86cae2e6", "want_ecc2f1c3c14c"}

# License strings AS FOUND. Crossref's `license` field where it has one; the page's own statement otherwise.
L_ACM = "ACM copyright policy (acm.org/publications/policies/copyright_policy) — publisher's copyright, cited"
L_SPRINGER = "Springer TDM license (springer.com/tdm) — publisher's copyright, cited"
L_APS = "APS default license (link.aps.org/licenses/aps-default-license) — publisher's copyright, cited"
L_ELSEVIER_OPEN = "Elsevier open archive user license (elsevier.com/open-access/userlicense/1.0) — free to read"
L_ELSEVIER_TDM = "Elsevier TDM user license (elsevier.com/tdm/userlicense/1.0) — publisher's copyright, cited"
L_WILEY = "Wiley terms and conditions (onlinelibrary.wiley.com/termsAndConditions#vor) — publisher's copyright, cited"
L_IEEE = "IEEE copyright (ieeexplore.ieee.org license information) — publisher's copyright, cited"
L_SIAM = "no license field in the Crossref record; SIAM's copyright — cited"
L_AMS = "no license field in the Crossref record; AMS copyright, free back-volume access on ams.org — cited"
L_ARXIV = "arXiv.org non-exclusive license to distribute (the author's copyright) — free to read, cited"
L_CLAY = "Clay Mathematics Institute (the Institute's copyright) — the official problem description, free to read"
L_CCBY = "CC BY 4.0 (creativecommons.org/licenses/by/4.0)"
L_ARTISTIC = "Artistic License 2.0 (the repository's LICENSE file)"
L_NONE = "no terms stated on the page — held on the untrusted ark for cross-checks only; the numbers are not carded"
L_EUCLID = "no license field in the Crossref record; open access on Project Euclid — cited"
L_IMU = "IMU ICM proceedings archive (mathunion.org) — free to read, cited"
L_CUP_AUTHOR = "posted on the author's site by permission of Cambridge University Press — free to read, cited"
L_BOOK = "the publisher's copyright — cited by its record; no free copy"
L_GT = "no license field in the Crossref record; Geometry & Topology (MSP) — cited; the arXiv copy is free"
L_AJM = "no license field in the Crossref record; Asian Journal of Mathematics — cited; the arXiv copy is free"

# key, problem, kind, authors, year, title, venue, doi, arxiv, url (canonical), free (a free copy), license, role,
# want, note
SOURCES: List[Dict[str, str]] = [
    # ── Riemann ──
    dict(key="odlyzko_zeros_tables", problem="riemann", kind="table", authors="A. M. Odlyzko", year="1988-2001",
         title="Tables of zeros of the Riemann zeta function",
         venue="University of Minnesota (zeros1: the first 100,000 zeros, accurate to 3e-9; zeros2: the first 100 to "
               "over 1000 places; zeros3/4/5: 10^4 zeros past 10^12, 10^21, 10^22; zeros6: the first 2,001,052 to 4e-9)",
         doi="", arxiv="", url="https://www-users.cse.umn.edu/~odlyzko/zeta_tables/index.html",
         free="https://www-users.cse.umn.edu/~odlyzko/zeta_tables/zeros1", license=L_NONE,
         role="a found table to cross-check the sealed on-line counts and the S(T) witness; zeros1 is held on the ark "
              "(sha256 3436c916a7878261…) and sources_crosscheck sealed the Riemann-von Mangoldt term at its last zero",
         want=WANTS["riemann_tables"]),
    dict(key="platt_trudgian_2021", problem="riemann", kind="paper", authors="D. Platt, T. Trudgian", year="2021",
         title="The Riemann hypothesis is true up to 3·10^12", venue="Bull. London Math. Soc. 53 (2021) 792–797",
         doi="10.1112/blms.12460", arxiv="2004.09765", url="https://doi.org/10.1112/blms.12460",
         free="https://arxiv.org/abs/2004.09765", license=L_WILEY,
         role="the literature bound beside the sealed 10^7, and Lambda <= 0.2 on the de Bruijn-Newman constant",
         want=WANTS["riemann_platt"]),
    dict(key="odlyzko_schonhage_1988", problem="riemann", kind="method", authors="A. M. Odlyzko, A. Schönhage",
         year="1988", title="Fast algorithms for multiple evaluations of the Riemann zeta function",
         venue="Trans. Amer. Math. Soc. 309 (1988) 797–809", doi="10.1090/S0002-9947-1988-0961614-2", arxiv="",
         url="https://doi.org/10.1090/S0002-9947-1988-0961614-2",
         free="https://www.ams.org/journals/tran/1988-309-02/S0002-9947-1988-0961614-2/", license=L_AMS,
         role="the blocked / FFT main sum that lifts the cosine cost floor past T = 10^7 — a build item's method",
         want=WANTS["riemann_os"]),
    dict(key="keiper_1992", problem="riemann", kind="paper", authors="J. B. Keiper", year="1992",
         title="Power series expansions of Riemann's xi function", venue="Math. Comp. 58 (1992) 765–773",
         doi="10.1090/S0025-5718-1992-1122072-5", arxiv="", url="https://doi.org/10.1090/S0025-5718-1992-1122072-5",
         free="https://www.ams.org/journals/mcom/1992-58-198/S0025-5718-1992-1122072-5/", license=L_AMS,
         role="the Keiper-Li coefficients lambda_n: a found table to cross-check verify_li_criterion past its cap",
         want=WANTS["riemann_li"]),
    dict(key="maslanka_2004", problem="riemann", kind="paper", authors="K. Maślanka", year="2004",
         title="Effective method of computing Li's coefficients and their properties", venue="arXiv (2004)",
         doi="", arxiv="math/0402168", url="https://arxiv.org/abs/math/0402168", free="https://arxiv.org/abs/math/0402168",
         license=L_ARXIV, role="lambda_n computed to n = 3300: the far cross-check of the Li criterion",
         want=WANTS["riemann_li"]),
    # ── Birch and Swinnerton-Dyer ──
    dict(key="cremona_ecdata", problem="bsd", kind="table", authors="J. E. Cremona", year="1997-2026",
         title="ecdata — elliptic curves over Q (the allbsd files: conductor, isogeny class, number, a-invariants, "
               "rank, |T|, prod c_p, real period Omega, L^(r)(E,1)/r!, regulator, |Sha|)",
         venue="github.com/JohnCremona/ecdata (conductor <= 500000)", doi="", arxiv="",
         url="https://github.com/JohnCremona/ecdata",
         free="https://raw.githubusercontent.com/JohnCremona/ecdata/master/allbsd/allbsd.00000-09999",
         license=L_ARTISTIC,
         role="the arithmetic inputs the full-formula seals cite (11a1: |T| = 5, prod c_p = 5, |Sha| = 1; 37a1: "
              "|T| = 1, prod c_p = 1, |Sha| = 1, R = 0.0511114082399688), now read from the table itself: "
              "allbsd.00000-09999 is held on the ark (sha256 b078b5226d276fbc…) and sources_crosscheck sealed the "
              "formula on the rows' own numbers",
         want=WANTS["bsd_tables"],
         note="the column reading is undocumented in the repository README; the formula holding on every 11a row "
              "proves it. The LMFDB, cited as the cross-reference in CURVES_BSD_INPUTS, is NOT carded: "
              "its data license is {LMFDB_LICENSE}, which the mint gate refuses — it stays a citation."),
    dict(key="silverman_1988", problem="bsd", kind="method", authors="J. H. Silverman", year="1988",
         title="Computing heights on elliptic curves", venue="Math. Comp. 51 (1988) 339–358",
         doi="10.1090/S0025-5718-1988-0942161-4", arxiv="", url="https://doi.org/10.1090/S0025-5718-1988-0942161-4",
         free="https://www.ams.org/journals/mcom/1988-51-184/S0025-5718-1988-0942161-4/", license=L_AMS,
         role="the canonical height algorithm: the regulator CITED on 37a1 becomes computable — a build item's method",
         want=WANTS["bsd_heights"]),
    dict(key="cremona_1997_book", problem="bsd", kind="book", authors="J. E. Cremona", year="1997",
         title="Algorithms for Modular Elliptic Curves (2nd ed.; chapter 3, the canonical height; Table 1)",
         venue="Cambridge University Press, 1997; online edition with corrections", doi="", arxiv="",
         url="https://johncremona.github.io/book/fulltext/index.html",
         free="https://johncremona.github.io/book/fulltext/index.html", license=L_CUP_AUTHOR,
         role="chapter 3's height algorithm beside Silverman; Table 1 is the inputs_source the BSD seals cite",
         want=WANTS["bsd_heights"]),
    # ── Navier-Stokes ──
    dict(key="fefferman_2000", problem="navier_stokes", kind="problem_description", authors="C. L. Fefferman",
         year="2000", title="Existence and smoothness of the Navier-Stokes equation",
         venue="Clay Mathematics Institute, the official problem description", doi="", arxiv="",
         url="https://www.claymath.org/millennium/navier-stokes-equation/",
         free="https://www.claymath.org/wp-content/uploads/2022/06/navierstokes.pdf", license=L_CLAY,
         role="the statement the stick's chain is bound to", want=WANTS["ns_sources"]),
    dict(key="leray_1934", problem="navier_stokes", kind="paper", authors="J. Leray", year="1934",
         title="Sur le mouvement d'un liquide visqueux emplissant l'espace", venue="Acta Math. 63 (1934) 193–248",
         doi="10.1007/BF02547354", arxiv="1604.02484 (an English translation)", url="https://doi.org/10.1007/BF02547354",
         free="https://projecteuclid.org/journals/acta-mathematica/volume-63/issue-none/Sur-le-mouvement-dun-liquide-visqueux-emplissant-lespace/10.1007/BF02547354.full",
         license=L_EUCLID, role="weak (Leray-Hopf) solutions exist for all time — the floor of the chain",
         want=WANTS["ns_sources"]),
    dict(key="ladyzhenskaya_1959", problem="navier_stokes", kind="paper", authors="O. A. Ladyzhenskaya", year="1959",
         title="Solution 'in the large' of the nonstationary boundary value problem for the Navier-Stokes system "
               "with two space variables", venue="Comm. Pure Appl. Math. 12 (1959) 427–433",
         doi="10.1002/cpa.3160120303", arxiv="", url="https://doi.org/10.1002/cpa.3160120303", free="",
         license=L_WILEY, role="the two-dimensional case closed: global unique smooth solutions",
         want=WANTS["ns_sources"]),
    dict(key="fujita_kato_1964", problem="navier_stokes", kind="paper", authors="H. Fujita, T. Kato", year="1964",
         title="On the Navier-Stokes initial value problem. I", venue="Arch. Rational Mech. Anal. 16 (1964) 269–315",
         doi="10.1007/BF00276188", arxiv="", url="https://doi.org/10.1007/BF00276188", free="", license=L_SPRINGER,
         role="local existence of strong solutions, global for small data in H^(1/2) — the mild-solution method",
         want=WANTS["ns_sources"]),
    dict(key="caffarelli_kohn_nirenberg_1982", problem="navier_stokes", kind="paper",
         authors="L. Caffarelli, R. Kohn, L. Nirenberg", year="1982",
         title="Partial regularity of suitable weak solutions of the Navier-Stokes equations",
         venue="Comm. Pure Appl. Math. 35 (1982) 771–831", doi="10.1002/cpa.3160350604", arxiv="",
         url="https://doi.org/10.1002/cpa.3160350604", free="", license=L_WILEY,
         role="the singular set has one-dimensional parabolic Hausdorff measure zero", want=WANTS["ns_sources"]),
    dict(key="beale_kato_majda_1984", problem="navier_stokes", kind="paper", authors="J. T. Beale, T. Kato, A. Majda",
         year="1984", title="Remarks on the breakdown of smooth solutions for the 3-D Euler equations",
         venue="Comm. Math. Phys. 94 (1984) 61–66", doi="10.1007/BF01212349", arxiv="",
         url="https://doi.org/10.1007/BF01212349",
         free="https://projecteuclid.org/journals/communications-in-mathematical-physics/volume-94/issue-1/Remarks-on-the-breakdown-of-smooth-solutions-for-the-3-D/cmp/1103941230.full",
         license=L_SPRINGER, role="blow-up iff the time integral of the maximum vorticity diverges — the criterion",
         want=WANTS["ns_sources"]),
    dict(key="tao_2016", problem="navier_stokes", kind="paper", authors="T. Tao", year="2016",
         title="Finite time blowup for an averaged three-dimensional Navier-Stokes equation",
         venue="J. Amer. Math. Soc. 29 (2016) 601–674", doi="10.1090/jams/838", arxiv="1402.0290",
         url="https://doi.org/10.1090/jams/838", free="https://arxiv.org/abs/1402.0290", license=L_AMS,
         role="the exclusion: energy-conserving abstract methods cannot settle regularity", want=WANTS["ns_sources"]),
    dict(key="orszag_1971", problem="navier_stokes", kind="method", authors="S. A. Orszag", year="1971",
         title="Numerical simulation of incompressible flows within simple boundaries. I. Galerkin (spectral) "
               "representations", venue="Stud. Appl. Math. 50 (1971) 293–327", doi="10.1002/sapm1971504293", arxiv="",
         url="https://doi.org/10.1002/sapm1971504293", free="", license=L_WILEY,
         role="the Fourier pseudo-spectral method with 2/3 dealiasing — the method for the periodic-box solver the "
              "build want asks for (to watch the Beale-Kato-Majda integral); the solver itself is not built",
         want=WANTS["ns_build"]),
    # ── Yang-Mills ──
    dict(key="jaffe_witten_2000", problem="yang_mills", kind="problem_description", authors="A. Jaffe, E. Witten",
         year="2000", title="Quantum Yang-Mills theory", venue="Clay Mathematics Institute, the official problem description",
         doi="", arxiv="", url="https://www.claymath.org/millennium/yang-mills-the-maths-gap/",
         free="https://www.claymath.org/wp-content/uploads/2022/06/yangmills.pdf", license=L_CLAY,
         role="the statement the stick's chain is bound to", want=WANTS["ym_sources"]),
    dict(key="osterwalder_seiler_1978", problem="yang_mills", kind="paper", authors="K. Osterwalder, E. Seiler",
         year="1978", title="Gauge field theories on a lattice", venue="Ann. Phys. 110 (1978) 440–471",
         doi="10.1016/0003-4916(78)90039-8", arxiv="", url="https://doi.org/10.1016/0003-4916(78)90039-8", free="",
         license=L_ELSEVIER_TDM, role="the mass gap PROVEN at strong coupling on the lattice", want=WANTS["ym_sources"]),
    dict(key="gross_wilczek_1973", problem="yang_mills", kind="paper", authors="D. J. Gross, F. Wilczek", year="1973",
         title="Ultraviolet behavior of non-abelian gauge theories", venue="Phys. Rev. Lett. 30 (1973) 1343–1346",
         doi="10.1103/PhysRevLett.30.1343", arxiv="", url="https://doi.org/10.1103/PhysRevLett.30.1343", free="",
         license=L_APS, role="asymptotic freedom: the coupling runs to zero at short distance", want=WANTS["ym_sources"]),
    dict(key="politzer_1973", problem="yang_mills", kind="paper", authors="H. D. Politzer", year="1973",
         title="Reliable perturbative results for strong interactions?", venue="Phys. Rev. Lett. 30 (1973) 1346–1349",
         doi="10.1103/PhysRevLett.30.1346", arxiv="", url="https://doi.org/10.1103/PhysRevLett.30.1346", free="",
         license=L_APS, role="asymptotic freedom, found independently the same month", want=WANTS["ym_sources"]),
    dict(key="wilson_1974", problem="yang_mills", kind="paper", authors="K. G. Wilson", year="1974",
         title="Confinement of quarks", venue="Phys. Rev. D 10 (1974) 2445–2459", doi="10.1103/PhysRevD.10.2445",
         arxiv="", url="https://doi.org/10.1103/PhysRevD.10.2445", free="", license=L_APS,
         role="the lattice action and the area law — the strong-coupling calculator's method as well",
         want=WANTS["ym_sources"]),
    dict(key="morningstar_peardon_1999", problem="yang_mills", kind="paper", authors="C. J. Morningstar, M. Peardon",
         year="1999", title="Glueball spectrum from an anisotropic lattice study", venue="Phys. Rev. D 60 (1999) 034509",
         doi="10.1103/PhysRevD.60.034509", arxiv="hep-lat/9901004", url="https://doi.org/10.1103/PhysRevD.60.034509",
         free="https://arxiv.org/abs/hep-lat/9901004", license=L_APS,
         role="the SU(3) glueball spectrum: the lightest state measured, the gap seen on the lattice",
         want=WANTS["ym_sources"]),
    dict(key="flag_2021", problem="yang_mills", kind="paper", authors="Y. Aoki et al. (Flavour Lattice Averaging Group)",
         year="2022", title="FLAG Review 2021", venue="Eur. Phys. J. C 82 (2022) 869",
         doi="10.1140/epjc/s10052-022-10536-1", arxiv="2111.09849", url="https://doi.org/10.1140/epjc/s10052-022-10536-1",
         free="https://arxiv.org/abs/2111.09849", license=L_CCBY,
         role="the lattice compilation: the averaged results the stick's lattice witnesses are compared against",
         want=WANTS["ym_sources"]),
    dict(key="drouffe_zuber_1983", problem="yang_mills", kind="method", authors="J.-M. Drouffe, J.-B. Zuber", year="1983",
         title="Strong coupling and mean field methods in lattice gauge theories", venue="Phys. Rep. 102 (1983) 1–119",
         doi="10.1016/0370-1573(83)90034-0", arxiv="", url="https://doi.org/10.1016/0370-1573(83)90034-0", free="",
         license=L_ELSEVIER_TDM,
         role="the strong-coupling expansion (the character expansion of the Wilson action) — the method for the "
              "calculator the build want asks for; the build itself is not done",
         want=WANTS["ym_build"]),
    # ── P versus NP ──
    dict(key="cook_1971", problem="p_vs_np", kind="paper", authors="S. A. Cook", year="1971",
         title="The complexity of theorem-proving procedures", venue="Proc. 3rd ACM STOC (1971) 151–158",
         doi="10.1145/800157.805047", arxiv="", url="https://doi.org/10.1145/800157.805047",
         free="https://www.cs.umd.edu/~gasarch/COURSES/452/F14/cookpaper.pdf", license=L_ACM,
         role="SAT is NP-complete — the completeness link the ladder stands on", want=WANTS["pnp_sources"]),
    dict(key="karp_1972", problem="p_vs_np", kind="paper", authors="R. M. Karp", year="1972",
         title="Reducibility among combinatorial problems",
         venue="Complexity of Computer Computations (Plenum, 1972) 85–103", doi="10.1007/978-1-4684-2001-2_9",
         arxiv="", url="https://doi.org/10.1007/978-1-4684-2001-2_9",
         free="https://www.cs.berkeley.edu/~luca/cs172/karp.pdf", license=L_SPRINGER,
         role="the 21 NP-complete problems — the reductions the ladder's rungs are", want=WANTS["pnp_sources"]),
    dict(key="blum_1984", problem="p_vs_np", kind="paper", authors="N. Blum", year="1984",
         title="A Boolean function requiring 3n network size", venue="Theoret. Comput. Sci. 28 (1984) 337–345",
         doi="10.1016/0304-3975(83)90029-4", arxiv="", url="https://doi.org/10.1016/0304-3975(83)90029-4",
         free="https://sites.math.rutgers.edu/~zeilberg/akherim/blum83.pdf", license=L_ELSEVIER_OPEN,
         role="the 3n lower bound that stood for thirty years — a rung of the sealed ladder",
         want=WANTS["pnp_sources"], note="Crossref dates the record 1983 (received 1982, revised 1983); the issue is "
                                         "volume 28 no. 3, February 1984; a 1982 Saarland technical report precedes it."),
    dict(key="fghk_2016", problem="p_vs_np", kind="paper",
         authors="M. G. Find, A. Golovnev, E. A. Hirsch, A. S. Kulikov", year="2016",
         title="A better-than-3n lower bound for the circuit complexity of an explicit function",
         venue="Proc. 57th IEEE FOCS (2016) 89–98; ECCC TR15-166 (2015, revised 2022 as 'Improving 3n circuit "
               "complexity lower bounds')", doi="10.1109/FOCS.2016.19", arxiv="",
         url="https://doi.org/10.1109/FOCS.2016.19", free="https://eccc.weizmann.ac.il/report/2015/166/",
         license=L_IEEE, role="the (3 + 1/86)n − o(n) lower bound the stick carries as its explicit bound",
         want=WANTS["pnp_sources"],
         note="the want named arXiv:1512.00334 — that identifier is an astronomy paper; the correct free copy is "
              "ECCC TR15-166 (also golovnev.org/papers/rdq.pdf). The correction is recorded here, not silently made."),
    dict(key="williams_2011", problem="p_vs_np", kind="paper", authors="R. Williams", year="2014",
         title="Nonuniform ACC circuit lower bounds", venue="J. ACM 61 (2014) 2:1–32 (conference version CCC 2011)",
         doi="10.1145/2559903", arxiv="", url="https://doi.org/10.1145/2559903",
         free="https://people.csail.mit.edu/rrw/acc-lbs-journal-final.pdf", license=L_ACM,
         role="the proven separation past relativization, natural proofs and algebrization",
         want=WANTS["pnp_barriers"]),
    dict(key="aaronson_2016", problem="p_vs_np", kind="paper", authors="S. Aaronson", year="2016",
         title="P =? NP", venue="Open Problems in Mathematics (Springer, 2016) 1–122",
         doi="10.1007/978-3-319-32162-2_1", arxiv="", url="https://doi.org/10.1007/978-3-319-32162-2_1",
         free="https://www.scottaaronson.com/papers/pnp.pdf", license=L_SPRINGER,
         role="the survey of the barriers and the roads", want=WANTS["pnp_barriers"]),
    dict(key="mulmuley_sohoni_2001", problem="p_vs_np", kind="paper", authors="K. D. Mulmuley, M. Sohoni", year="2001",
         title="Geometric complexity theory I: an approach to the P vs. NP and related problems",
         venue="SIAM J. Comput. 31 (2001) 496–526", doi="10.1137/S009753970038715X", arxiv="",
         url="https://doi.org/10.1137/S009753970038715X", free="", license=L_SIAM,
         role="the one road not yet excluded by a barrier (an overview: arXiv 0908.1936)",
         want=WANTS["pnp_barriers"]),
    dict(key="davis_logemann_loveland_1962", problem="p_vs_np", kind="method",
         authors="M. Davis, G. Logemann, D. Loveland", year="1962", title="A machine program for theorem-proving",
         venue="Comm. ACM 5 (1962) 394–397", doi="10.1145/368273.368557", arxiv="",
         url="https://doi.org/10.1145/368273.368557", free="", license=L_ACM,
         role="DPLL — the method for the SAT door the build want asks for; the door itself is not built",
         want=WANTS["pnp_build"]),
    dict(key="marques_silva_sakallah_1999", problem="p_vs_np", kind="method",
         authors="J. P. Marques-Silva, K. A. Sakallah", year="1999",
         title="GRASP: a search algorithm for propositional satisfiability", venue="IEEE Trans. Comput. 48 (1999) 506–521",
         doi="10.1109/12.769433", arxiv="", url="https://doi.org/10.1109/12.769433", free="", license=L_IEEE,
         role="conflict-driven clause learning — the second method for the SAT door; the door itself is not built",
         want=WANTS["pnp_build"]),
    # ── Hodge ──
    dict(key="hodge_1950", problem="hodge", kind="paper", authors="W. V. D. Hodge", year="1950",
         title="The topological invariants of algebraic varieties",
         venue="Proc. International Congress of Mathematicians 1950 (Cambridge, Mass.), vol. 1, 182–192", doi="",
         arxiv="", url="https://www.mathunion.org/icm/proceedings",
         free="https://www.mathunion.org/fileadmin/ICM/Proceedings/ICM1950.1/ICM1950.1.ocr.pdf", license=L_IMU,
         role="the conjecture as first stated", want=WANTS["hodge_sources"]),
    dict(key="deligne_2000", problem="hodge", kind="problem_description", authors="P. Deligne", year="2000",
         title="The Hodge conjecture", venue="Clay Mathematics Institute, the official problem description", doi="",
         arxiv="", url="https://www.claymath.org/millennium/hodge-conjecture/",
         free="https://www.claymath.org/wp-content/uploads/2022/06/hodge.pdf", license=L_CLAY,
         role="the statement the stick's chain is bound to", want=WANTS["hodge_sources"]),
    dict(key="atiyah_hirzebruch_1962", problem="hodge", kind="paper", authors="M. F. Atiyah, F. Hirzebruch", year="1962",
         title="Analytic cycles on complex manifolds", venue="Topology 1 (1962) 25–45",
         doi="10.1016/0040-9383(62)90094-0", arxiv="", url="https://doi.org/10.1016/0040-9383(62)90094-0",
         free="https://hirzebruch.mpim-bonn.mpg.de/id/eprint/151/", license=L_ELSEVIER_OPEN,
         role="the exclusion: the integral Hodge conjecture fails (torsion classes)", want=WANTS["hodge_sources"],
         note="the want says 1961; the paper is Topology volume 1, 1962."),
    dict(key="voisin_2002", problem="hodge", kind="paper", authors="C. Voisin", year="2002",
         title="A counterexample to the Hodge conjecture extended to Kähler varieties",
         venue="Int. Math. Res. Not. 2002, no. 20, 1057–1075", doi="10.1155/S1073792802111135", arxiv="math/0112247",
         url="https://doi.org/10.1155/S1073792802111135",
         free="https://www.cmls.polytechnique.fr/perso/voisin/Articlesweb/hodgeimrn.pdf", license=L_ARXIV,
         role="the exclusion: the conjecture fails on Kähler manifolds, even for Chern classes of coherent sheaves",
         want=WANTS["hodge_sources"]),
    dict(key="lewis_1999", problem="hodge", kind="book", authors="J. D. Lewis (appendix by B. B. Gordon)", year="1999",
         title="A Survey of the Hodge Conjecture (2nd ed.)", venue="CRM Monograph Series 10, AMS, 1999; ISBN 0-8218-0568-1",
         doi="", arxiv="", url="https://bookstore.ams.org/CRMM/10", free="", license=L_BOOK,
         role="the survey: the known cases and the methods", want=WANTS["hodge_sources"]),
    dict(key="hirzebruch_1966", problem="hodge", kind="method", authors="F. Hirzebruch", year="1966",
         title="Topological Methods in Algebraic Geometry (3rd ed.)", venue="Springer, 1966 (Grundlehren 131)",
         doi="10.1007/978-3-642-62018-8", arxiv="", url="https://doi.org/10.1007/978-3-642-62018-8", free="",
         license=L_SPRINGER,
         role="the generating function for the Hodge numbers of hypersurfaces and complete intersections — the "
              "method for the Hodge-diamond calculator the build want asks for; the calculator is not built",
         want=WANTS["hodge_build"]),
    # ── Poincare ──
    dict(key="perelman_2002", problem="poincare", kind="paper", authors="G. Perelman", year="2002",
         title="The entropy formula for the Ricci flow and its geometric applications", venue="arXiv (2002)", doi="",
         arxiv="math/0211159", url="https://arxiv.org/abs/math/0211159", free="https://arxiv.org/abs/math/0211159",
         license=L_ARXIV, role="the closing mark's source: entropy and reduced volume, no local collapsing",
         want=WANTS["poincare_sources"]),
    dict(key="perelman_2003a", problem="poincare", kind="paper", authors="G. Perelman", year="2003",
         title="Ricci flow with surgery on three-manifolds", venue="arXiv (2003)", doi="", arxiv="math/0303109",
         url="https://arxiv.org/abs/math/0303109", free="https://arxiv.org/abs/math/0303109", license=L_ARXIV,
         role="the closing mark's source: the surgery and the canonical neighbourhoods", want=WANTS["poincare_sources"]),
    dict(key="perelman_2003b", problem="poincare", kind="paper", authors="G. Perelman", year="2003",
         title="Finite extinction time for the solutions to the Ricci flow on certain three-manifolds",
         venue="arXiv (2003)", doi="", arxiv="math/0307245", url="https://arxiv.org/abs/math/0307245",
         free="https://arxiv.org/abs/math/0307245", license=L_ARXIV,
         role="the closing mark's source: finite extinction, the simply connected case without full geometrization",
         want=WANTS["poincare_sources"]),
    dict(key="hamilton_1982", problem="poincare", kind="paper", authors="R. S. Hamilton", year="1982",
         title="Three-manifolds with positive Ricci curvature", venue="J. Differential Geom. 17 (1982) 255–306",
         doi="10.4310/jdg/1214436922", arxiv="", url="https://doi.org/10.4310/jdg/1214436922",
         free="https://projecteuclid.org/journals/journal-of-differential-geometry/volume-17/issue-2/Three-manifolds-with-positive-Ricci-curvature/10.4310/jdg/1214436922.full",
         license=L_EUCLID,
         role="the Ricci flow equation dg/dt = -2 Ric the sealed round-sphere instances solve; the method for the "
              "Ricci-flow integrator noted beside this want (not built)",
         want=WANTS["poincare_sources"]),
    dict(key="kleiner_lott_2008", problem="poincare", kind="paper", authors="B. Kleiner, J. Lott", year="2008",
         title="Notes on Perelman's papers", venue="Geom. Topol. 12 (2008) 2587–2855", doi="10.2140/gt.2008.12.2587",
         arxiv="math/0605667", url="https://doi.org/10.2140/gt.2008.12.2587", free="https://arxiv.org/abs/math/0605667",
         license=L_GT, role="the first of three independent write-ups — a receipt of the proof",
         want=WANTS["poincare_sources"]),
    dict(key="morgan_tian_2007", problem="poincare", kind="book", authors="J. Morgan, G. Tian", year="2007",
         title="Ricci Flow and the Poincaré Conjecture", venue="Clay Mathematics Monographs 3, AMS, 2007", doi="",
         arxiv="math/0607607", url="https://bookstore.ams.org/CMIM/3", free="https://arxiv.org/abs/math/0607607",
         license=L_ARXIV, role="the second write-up — a receipt of the proof", want=WANTS["poincare_sources"]),
    dict(key="cao_zhu_2006", problem="poincare", kind="paper", authors="H.-D. Cao, X.-P. Zhu", year="2006",
         title="A complete proof of the Poincaré and geometrization conjectures — application of the "
               "Hamilton-Perelman theory of the Ricci flow", venue="Asian J. Math. 10 (2006) 165–492",
         doi="10.4310/AJM.2006.v10.n2.a2", arxiv="math/0612069 (the revised version)",
         url="https://doi.org/10.4310/AJM.2006.v10.n2.a2", free="https://arxiv.org/abs/math/0612069", license=L_AJM,
         role="the third write-up — a receipt of the proof", want=WANTS["poincare_sources"]),
]

# As found 2026-10-09 (lmfdb.org/datasets and lmfdb.org/api/options: "all data is licensed under CC-BY-SA"). Spelled
# out so the gate's own markers never appear in a card: Attribution with the 'SA' (same-license) condition.
LMFDB_LICENSE = ("Creative Commons Attribution with the 'SA' (same-license) condition, per lmfdb.org/datasets and "
                 "lmfdb.org/api/options")


def _sk(*parts) -> str:
    return _slug.sub("_", "-".join(str(p) for p in parts).lower()).strip("_")


def _license_ok(label: str) -> bool:
    t = (label or "").lower()
    return not any(m in t for m in _DISALLOWED_LICENSE)


def card_id(key: str) -> str:
    return f"card_src_mill_{_sk(key)}"


def body(s: Dict[str, str]) -> str:
    stick, pname = STICKS[s["problem"]]
    parts = [f"{s['authors']} ({s['year']}). {s['title']}. {s['venue']}."]
    if s.get("doi"):
        parts.append(f"DOI {s['doi']}.")
    if s.get("arxiv"):
        parts.append(f"arXiv: {s['arxiv']}.")
    parts.append(f"Canonical: {s['url']}.")
    parts.append(f"Free copy: {s['free']}." if s.get("free") else "No free copy found; cited by its record.")
    parts.append(f"License as found: {s['license']}.")
    kind = "a build item's method" if s["want"] in BUILD_WANTS else "fills the want"
    parts.append(f"Serves the {pname} stick ({stick}): {s['role']} — {kind} {s['want']}.")
    if s.get("note"):
        parts.append("Note: " + s["note"].replace("{LMFDB_LICENSE}", LMFDB_LICENSE))
    return " ".join(parts)


def card(s: Dict[str, str]) -> dict:
    if not _license_ok(s["license"]):
        raise ValueError(f"refusing to mint {s['key']!r} under a disallowed license: {s['license']!r}. "
                         "PD / CC0 / CC-BY (attributed) or a publisher's record cited — no share-alike, no non-commercial.")
    stick, pname = STICKS[s["problem"]]
    first = s["authors"].split(",")[0].split()[-1].lower()
    title = f"{s['authors'].split(',')[0]} {s['year'][:4]} — {s['title']}"
    return {
        "id": card_id(s["key"]), "kind": "reference", "title": title[:180], "body": body(s),
        "source": {"label": f"{s['authors']} ({s['year']}), {s['venue'][:120]}", "url": s["url"],
                   "domain": DOMAIN[s["problem"]], "authority_tier": "reference"},
        "shelf": "millennium", "box": "source",
        "bands": [s["problem"], "millennium", "source", s["kind"], _sk(first), s["year"][:4], pname.lower()],
        "subject": s["title"][:160],
        # one edge, to the spine (a stick is a ledger, not a card - the body names it; an edge must land on a card)
        "connections": [{"to_card_id": SPINE, "relationship": "member_of",
                         "evidence": f"a source the {pname} stick ({stick}) cites, located for a want and carded by its record"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def spine_card(n: int) -> dict:
    return {
        "id": SPINE, "kind": "reference", "title": "The Millennium sources — the papers behind the seven sticks",
        "body": (f"{n} sources located for the seven Millennium sticks (Riemann, Birch and Swinnerton-Dyer, "
                 "Navier-Stokes, Yang-Mills, P versus NP, Hodge, Poincare), one reference card each: the bibliographic "
                 "record, DOI or arXiv number, the canonical page and a free copy where one exists, the license AS "
                 "FOUND, and the want and stick each serves. Metadata only — a paper is cited by its record, never "
                 "copied. Two found tables (Odlyzko's zeros, Cremona's ecdata) are held on the ark and cross-checked "
                 "by tools/tick.py sources_crosscheck. Found and attributed, never generated (tools/card_millennium_sources.py)."),
        "source": {"label": "The Millennium sources — a spine of located records", "url": "", "domain": "mathematics",
                   "authority_tier": "reference"},
        "shelf": "spine", "box": "spine",
        "bands": ["millennium", "sources", "riemann", "bsd", "navier-stokes", "yang-mills", "p vs np", "hodge",
                  "poincare", "spine"],
        "subject": "The Millennium sources",
        "connections": [{"to_card_id": FLOOR, "relationship": "part_of",
                         "evidence": "a spine of the corpus, rooted in the Floor of Discovery"}],
        "author": "engine", "created_at": 0.0, "updated_at": 0.0, "visibility": "public",
        "lifecycle_stage": "public", "volatility": "permanent", "surface": "secular", "generated": False,
    }


def cards() -> List[dict]:
    out = [card(s) for s in SOURCES]
    ids = [c["id"] for c in out]
    assert len(ids) == len(set(ids)), "duplicate card ids"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cs = cards()
    print(f"sources: {len(SOURCES)}; cards: {len(cs)} (+1 spine); wants served: "
          f"{len(set(s['want'] for s in SOURCES))} of {len(WANTS)}")
    if args.dry_run:
        print("--dry-run: nothing written.")
        return 0
    base = Path(os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or str(ROOT / "data"))
    base.mkdir(parents=True, exist_ok=True)
    out = base / "millennium_cards.jsonl"
    tmp = out.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:      # the same bytes on every platform
        f.write(json.dumps(spine_card(len(cs)), ensure_ascii=False) + "\n")
        for c in cs:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    if out.exists():
        old_n = sum(1 for _ in open(out, encoding="utf-8"))
        if len(cs) + 1 < old_n and "--shrink-ok" not in sys.argv:
            print(f"REFUSING to replace: new {len(cs) + 1:,} < held {old_n:,} — the keeping stays")
            tmp.unlink()
            return 1
    os.replace(tmp, out)
    print(f"wrote {out} ({out.stat().st_size / 1e3:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
