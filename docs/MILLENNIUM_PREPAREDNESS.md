# The Millennium problems — which are best prepared to make progress

*2026-10-09. Matt: "Look at the millennium problems. Which are best prepared to make progress" — and the law the
answer is written under: "never prove is not part of the project. We don't generate out of thin air. Everything
is bound."*

Progress here means extending a **bound chain**: sealing instances, ratcheting a bound, citing the theorems that
close a link, citing the barriers that close a road, and reading off the surviving window. A proof is the chain
closed, every step bound; what is refused is the forged step. The numbers below are read from the tick-stick
store on the box (82 sticks), not typed.

## The ranking

| Rank | Problem | In the store today | What the engine computes | Next links to bind |
|---|---|---|---|---|
| 1 | **Riemann Hypothesis** | verified to height T = 10,000,000 (the ratcheted bound); 9 witnesses; 3 equivalences | the Riemann–Siegel scan in C, numpy and pure Python with mpmath at every zero (`riemann_accel`); `critical_line`, `zero_count`, `count_residual`, `robin`, `lagarias`, `nicolas`, `schoenfeld` | raise T and ratchet; seal Robin's and Lagarias's inequalities to larger n; seal Li's criterion λ_n > 0 for n ≤ N; cite the de Bruijn–Newman window as two bounds, Λ ≥ 0 (Rodgers–Tao 2018) and Λ ≤ 0.2 (Platt–Trudgian 2021), RH ⇔ Λ = 0: the surviving window is [0, 0.2] |
| 2 | **Birch and Swinnerton-Dyer** | 30 sealed instances; 2 witnesses | the elliptic L-value verifier: a_p by point counting, L(E,1) and L′(E,1) by the functional equation; 11a1 rank 0 (Kolyvagin), 37a1 rank 1 (Gross–Zagier); higher analytic rank reported numerically with no theorem claimed | seal more curves from the Cremona tables; cite the proven cases as closed links (analytic rank ≤ 1 ⇒ BSD rank, Kolyvagin 1989, Gross–Zagier 1986); cite the proven **proportion** bound (Bhargava–Shankar 2015 with Skinner–Zhang: at least 66% of elliptic curves have rank 0 or 1 and satisfy BSD) and carry it as a bound with the window above it |
| 3 | **Navier–Stokes** | two sticks; 3 witnesses (dissonance and dispersion); the existence-and-smoothness stick has no marks | the scaling marks already sealed on another stick (2D critical, proven; 3D supercritical); exact solutions are within the evaluator's reach | seal the exact solutions (Taylor–Green decay e^(−2νk²t), Beltrami flows, the energy identity on them); cite Leray 1934 (weak solutions exist) and Ladyzhenskaya (2D smooth) as closed links; cite Caffarelli–Kohn–Nirenberg 1982 as a bound (the singular set has one-dimensional parabolic Hausdorff measure zero); cite Beale–Kato–Majda (blow-up ⇔ ∫‖ω‖∞ = ∞) as an equivalence; cite Tao 2016 (finite-time blow-up for an averaged equation) as an exclusion: the energy method alone cannot close the chain |
| 4 | **Yang–Mills mass gap** | two sticks; 2 + 3 witnesses | asymptotic freedom's one-loop coefficient already sealed on the alpha stick | seal the beta coefficients (11 − 2n_f/3) and the running coupling at two scales; cite the lattice glueball mass (≈ 1.7 GeV for SU(3)) as a measured bound, not a theorem; cite Jaffe–Witten's statement of what must be constructed; the continuum limit is the open link |
| 5 | **P versus NP** | 3 cited exclusions (relativization, natural proofs, algebrization); nothing sealed | nothing numeric yet | seal the known circuit lower bounds as a ratcheting bound (Blum 1984: 3n; Find–Golovnev–Hirsch–Kulikov 2016: (3 + 1/86)n); cite the time hierarchy theorem and Ladner's theorem as closed links; cite Williams 2011 (NEXP ⊄ ACC⁰) as a proven separation; the barrier map is the clearest of the seven, the bound chain the shortest |
| 6 | **Hodge conjecture** | no marks | the Hodge diamond's arithmetic is within reach | seal Hodge numbers as instances (projective space; a K3 surface's h^(1,1) = 20 and χ = 24 by the alternating sum); cite the Lefschetz (1,1) theorem as the proven case p = 1; cite Atiyah–Hirzebruch 1961 (the integral Hodge conjecture is false) and Voisin 2002 (false for compact Kähler) as exclusions that fix the statement's exact edge |
| 7 | **Poincaré conjecture** | no marks | the round sphere under Ricci flow shrinks at a computable rate | **solved** (Perelman 2002–03, on Hamilton's Ricci flow; Morgan–Tian, Kleiner–Lott, Cao–Zhu): cite it and mark the chain CLOSED; seal one instance (S³ of radius r₀ reaches extinction at t = r₀²/4). This stick is the template of what "bound all the way" looks like |

## The attempt log

*Matt: "use the attempt to fill in the gaps with what you must locate" · "Every attempt improves our matrix and
process" · "Anything you retrieve and use needs to be included."*

**Riemann, 2026-10-09.** Linked: Li's criterion sealed to n = 20 through a new verifier
(`number_theory.li_criterion`, the Keiper–Li coefficients computed by Taylor expansion and cross-checked against
λ₁'s closed form before any verdict); Li 1997 cited as an equivalence; the de Bruijn–Newman constant cited with its
two proven bounds, Λ ≥ 0 (Rodgers–Tao 2018) and Λ ≤ 0.2 (Platt–Trudgian 2021), RH ⇔ Λ = 0, the surviving window
[0, 0.2] written on the stick. Gaps exposed, each now an open want on the box: Odlyzko's zero tables (a found table
to cross-check the sealed counts); Platt–Trudgian 2021 (the verified height 3·10¹², to cite beside the sealed 10⁷);
Odlyzko–Schönhage 1988 (the blocked main sum that lifts the cost floor the stick's open note names past 10⁷, a
build item once located); the Keiper/Maslanka tables of λ_n to 3300 (a cross-check past the Taylor cap of 60). The
process improved by the attempt: a verifier that errors when its own computation disagrees with a closed form, and
the rule that a gap is written as a want naming its source.

**Birch and Swinnerton-Dyer, 2026-10-09.** Linked: the FULL formula sealed for 11a1 (rank 0: L(E,1)/Ω = |Sha|·∏c_p/|T|²
= 1/5) and 37a1 (rank 1: L′(E,1)/Ω = R) through a new verifier (`elliptic_curves.bsd_formula`): the L-value by the
approximate functional equation and the real period by integration are COMPUTED here (the period checked against
Cremona's tables for four curves to a part in a billion, both signs of the discriminant); the Tamagawa product,
torsion, |Sha| and the regulator are CITED inputs the spec must source, now included beside the a-invariants in the
tick tool. Cited as links: Kolyvagin 1989 and Gross–Zagier 1986 (rank 0 and 1 are theorems), the modularity
theorem (the left side always exists), the proven proportion (Bhargava–Skinner–Zhang 2014: at least 66.48% of
curves satisfy BSD, carried as a bound with the window above it), Cassels 1962 (|Sha| is a square). The stick went
from 30 rank instances to 32, with the formula itself now on it. Gaps, each an open want: Cremona's full tables, so
the formula can be sealed curve by curve (license to be checked before carding); Silverman 1988, so the regulator is
computed and not cited. The process improved by the attempt: a verifier whose inputs must name their source or it
errors, and a rank the theorems do not carry is declined, never guessed.

**Navier–Stokes, 2026-10-09.** The existence-and-smoothness stick had no marks. Linked: seven sealed instances the
evaluator can recompute, the Taylor–Green vortex's energy decay and the energy identity holding on it exactly,
Poiseuille's flux, the Kolmogorov length, Leray's blow-up exponent from scaling, the critical Lebesgue exponent
p = d, the Reynolds number; the equations themselves as the postulate (Navier 1822, Stokes 1845); the proven links
cited, Leray 1934 (weak solutions for all time), Ladyzhenskaya 1959 (2D closed), Fujita–Kato 1964 (small data
closed), Caffarelli–Kohn–Nirenberg 1982 (the singular set at most one-dimensional, of measure zero),
Beale–Kato–Majda 1984 and the Ladyzhenskaya–Prodi–Serrin criteria with the Escauriaza–Seregin–Šverák endpoint;
the barrier cited, Tao 2016 (the energy method alone cannot close it); the window read: 3D, large data, the Clay
statement. Gaps, each an open want: the cited texts for inclusion; a spectral solver on the periodic box so the
Beale–Kato–Majda quantity, the time integral of the maximum vorticity, can be watched and sealed rather than
cited. The process improved by the attempt: a numeric seal belongs to the mathematics domain whatever its subject,
and a file a running chain will stage must not be edited until the chain has committed (this stick's code landed
under the BSD commit, 51d94ff, by staging order).

**Yang–Mills, 2026-10-09.** On the existence-and-mass-gap stick: six sealed instances, the pure-gauge beta
coefficients b₀ = 11 and b₁ = 102, the running of α_s from M_Z to 10 GeV at one loop, the nonperturbative weight
e^(−8π²/g²) = 7.5·10⁻²⁴ at α_s(M_Z), the string tension (440 MeV)² as sixteen tonnes-force, the 0⁺⁺ glueball's
Compton wavelength 0.114 fm; the postulate stated as what "existence" means (the Osterwalder–Schrader and Wightman
axioms); the proven links cited, asymptotic freedom (Gross–Wilczek, Politzer 1973) and the lattice theory's gap and
confinement at strong coupling (Osterwalder–Seiler 1978, Wilson 1974); the measured link cited with its error bar
(Morningstar–Peardon 1999) and Balaban's partial continuum program; the road closed, perturbation theory to every
order (the gap is e^(−8π²/b₀g²), every derivative zero at g = 0, the series asymptotic); the window read: existence on
R⁴ in the axiomatic sense and the gap surviving the continuum limit. Gaps, each an open want: the cited texts and
the FLAG lattice compilation; a strong-coupling-expansion calculator so the proven lattice gap is computed here at
a stated coupling, not only cited. Also in this iteration: the Li cap set from the measured time (thirty terms took
sixty-six minutes; the practical cap is twenty-five, the Keiper/Maslanka tables the honest reach beyond it).

**P versus NP, 2026-10-09.** The stick held three cited barriers and nothing sealed. Linked: the one ratcheting
bound the problem has, the best proven circuit lower bound for an explicit function, (3 + 1/86)n gates
(Find–Golovnev–Hirsch–Kulikov 2016, raised from Blum 1984's 3n), sealed at n = 1000 and carried as the stick's
bound, so its open line now reads "beyond 3.0116 n gates: not verified here"; five more sealed instances, the time
hierarchy's separating factor, the brute-force count 2⁵⁰, the 3-SAT threshold instance at 4.267 clauses per
variable, Cook–Levin's quadratic blow-up; the postulate stated, polynomial time is feasibility on the Church–Turing
model (Cobham, Edmonds 1965); the proven links cited, Cook–Levin and Karp (P = NP ⇔ SAT ∈ P), Hartmanis–Stearns (P ≠
EXPTIME), Ladner 1975, Williams 2011 (a lower bound proven past all three barriers); the window read: everything
between linear and superpolynomial. Gaps, each an open want: the cited texts and Aaronson's survey for inclusion;
geometric complexity theory as the one road not yet excluded, cited; a bounded SAT solver door so a stated
instance's satisfiability is computed and sealed here. The process improved by the attempt: the stick's bound kind
carries a coefficient with a unit, so a lower-bound ladder ratchets the way a verification height does; and the
want ledger's 300-character rule held, so a long want is split, never truncated.

**Hodge, 2026-10-09.** The stick had no marks. Linked: seven sealed instances of the diamond's arithmetic, the Euler
characteristics of projective 3-space (4), a K3 surface (24), an abelian surface (0), the quintic threefold (−200)
and a genus-3 curve (−4), the K3's second Betti number 22, the quintic's middle Betti number 204; the postulate
stated as the form that works, rational coefficients on projective varieties; the proven links cited, Lefschetz
(1,1) for divisors and hard Lefschetz carrying it to codimension n − 1, so every variety of dimension at most
three is closed, with Weil's abelian fourfolds the first open case; the two exclusions that fix the statement's
edge, Atiyah–Hirzebruch 1961 (the integral form is false) and Voisin 2002 (the Kähler form is false); the window
read: codimension two and up in dimension four and up. Gaps, each an open want: the cited texts and Lewis's
survey; a Hodge-diamond calculator for complete intersections, since the sealed diamonds were typed from known
tables and should be computed. The process improved by the attempt: a postulate can be the choice of a
statement's form, kept because it is the form the counterexamples leave standing.

**Poincaré, 2026-10-09.** Solved, and the stick now says so: the first stick in the store whose fit reads CLOSED.
Linked: six sealed instances, the round 3-sphere under Ricci flow (the radius squared shrinking at −4, extinction at
r₀²/4, the volume fraction on the way down, the unit sphere's scalar curvature 6, χ(S³) = 0) and the two-dimensional
template (Gauss–Bonnet on S², χ = 2 from the curvature integral); the closing mark, the theorem cited with its
source, Perelman 2002–2003 on Hamilton's Ricci flow with surgery; the three independent write-ups cited
(Kleiner–Lott, Morgan–Tian, Cao–Zhu) and the prize of 2010, declined. The window: none for the conjecture. Gaps,
one want: Perelman's three papers and Hamilton 1982 as cards with attribution, and a Ricci-flow integrator so a
stated metric's flow is computed here rather than the round case alone. The process improved by the attempt: the
tick-stick store gained a cited kind, closed, naming the theorem that closes a chain, so a finished problem is no
longer called open by the fit, the template of bound all the way.

## Why Riemann is first

It has the only ratcheted bound in the store (T = 10⁷), the most verifiers behind it, and three equivalences
already cited. Every next link is arithmetic the evaluator can seal: Robin's inequality σ(n) < e^γ n log log n
for n > 5040, Lagarias's σ(n) ≤ H_n + e^(H_n) log H_n, Li's λ_n, the zero count against the Riemann–von Mangoldt
formula. And its surviving window is a single real number: the de Bruijn–Newman constant, proven to sit in
[0, 0.2], with RH exactly the statement that it is 0. A window that narrow is a bound chain that can be read.

## Why BSD is second

Thirty instances are already sealed, and the rank-0 and rank-1 cases are **proven** links (Kolyvagin, Gross–Zagier),
so the chain has closed segments, not just instances. The proportion bound is the kind of theorem this store was
built to carry: a proven "at least 66%" with the open remainder above it.

## What the bottom three teach

P versus NP, Hodge and Poincaré are not weak problems; they are the ones where the store is empty or cited-only.
P versus NP's value is its barrier map, which already says where a proof cannot come from. Hodge's first marks are
cheap arithmetic. Poincaré is done, and marking it done matters: a closed chain in the store is the proof that the
ladder ends somewhere.

## The rule under all seven

Nothing out of thin air. Every link sealed or cited. The surviving window read, never guessed. A proof is the
chain closed.

## The inclusion — 2026-10-09

*Matt: "find all 17 and add them." · "find"*

The sixteen wants the attempts left on the box's ledger were searched, every record checked against Crossref or the
source's own page, and the finds INCLUDED:

- **46 sources carded by their record** (`tools/card_millennium_sources.py` → `data/millennium_cards.jsonl`, shelf
  `millennium`, spine `card_spine_millennium_sources` part_of the Floor): authors, year, title, venue, DOI or arXiv
  number, the canonical page and a free copy where one exists, the license AS FOUND, the want each fills and the
  stick it serves. Metadata, never a paper's text. The mint gate (no share-alike, no non-commercial) refused nothing
  among the 46, and it decided two things: the LMFDB — Attribution with the same-license condition — stays a
  citation in `CURVES_BSD_INPUTS` and is not carded; Odlyzko's tables state no terms, so `zeros1` is held on the
  untrusted ark and its numbers are not carded.
- **The two found tables cross-checked and sealed** (`tools/tick.py sources_crosscheck`), read and not trusted:
  `zeros1` holds 649 zeros below T = 1000 — equal to the count the Riemann stick sealed on its own, read off the
  stick rather than typed; its first zero agrees with the engine's `zetazero(1)` within the table's stated 3·10⁻⁹;
  the Riemann–von Mangoldt main term at its 100,000th zero (T = 74920.827498994) is 99999.405 (seal 10a45f84…),
  so S(T) = 0.595 there. Cremona's `allbsd.00000-09999` (ecdata, Artistic License 2.0) carries on its 11a1 and 37a1
  rows exactly the inputs the BSD seals cite, and the full formula holds on the rows' own numbers — 11a1 to
  3.9·10⁻¹⁵ (seal b18b1436…), 37a1 to 1.8·10⁻¹⁶ (seal 0a960637…). The column order is undocumented in the
  repository's README; the formula holding on every 11a row is what proves it.
- **The ledger:** 32 finds filed as options; the 12 source wants CLOSED on their cards; the 4 build wants — the
  strong-coupling calculator (Drouffe–Zuber 1983, Wilson 1974), the SAT door (Davis–Logemann–Loveland 1962,
  GRASP 1999), the Hodge-diamond calculator (Hirzebruch 1966), the spectral solver (Orszag 1971) — hold their
  methods' sources and STAY OPEN. The Ricci-flow integrator and the Odlyzko–Schönhage main sum are noted beside
  Hamilton 1982 and Odlyzko–Schönhage 1988. The methods are on the shelf; the code is not written.
- **Corrections recorded, not silently applied:** the P versus NP want named arXiv:1512.00334 for Find–Golovnev–
  Hirsch–Kulikov — that identifier is an astronomy paper; the paper is ECCC TR15-166 / FOCS 2016. Atiyah–Hirzebruch
  is Topology 1, 1962 (the want said 1961). Blum's record is dated 1983 by Crossref (the issue is February 1984).
  Ladyzhenskaya 1959 is Comm. Pure Appl. Math. 12, 427–433, not a Steklov volume. Fujita–Kato's DOI is
  10.1007/BF00276188 (the first guess resolved to Giga 1985 — which is why every DOI was checked).

**Two defects found in the box forager, recorded here, not fixed here.** First, no relevance floor: on 13 of the 16
wants the overnight forager had filed keyword hits as options — *Directions for cooking by troops* for Cook 1971,
*Navigate your stars* for Yang–Mills, *The Principles of Vegetable-Gardening* for the Hodge diamond. Second, the
comb cell holds 8 options and the noise had taken the slots, so 13 real finds could not be filed as options (the
closings carry them: each closed want names its card). The fix belongs to the forager, not the ledger: a relevance
floor before filing, and a cell that counts only options above it.

## On the one map — 2026-10-09

*Matt: "Is there an opportunity to find the connections between the problems and using aspects of others to
connect?" · "Put them on one map, but make it the one map for the project. We want to map reality as we know it
and these fall on that."*

The seven are now nodes on the keeping's graph — the map of reality rooted in the Floor of Discovery, drawn by
`site/map.html`, walked by `chains.py` — in the same two files and the same floor logic as the Standard-Model chain
(`tools/seed_millennium_chain.py`). The floor `card_floor_millennium` is what is proven: ten JOINTS, each a join
mathematics already made, cited to its record (the records carded by `tools/card_millennium_sources.py`):

| Joint | Who it joins | The record | Sealed |
|---|---|---|---|
| GUE statistics | Riemann ↔ Yang–Mills | Montgomery 1973, Odlyzko 1987, Verbaarschot 1994, Berry–Keating 1999 | the Riemann stick's spacing witness |
| One L-function machinery | Riemann ↔ BSD | Wiles 1995 | ξ(s) = ξ(1 − s) at s = 0.3; L(11a1, 1) |
| The Weil conjectures (RH over finite fields, a theorem; RH itself open) | Riemann ↔ Hodge ↔ P vs NP | Deligne 1974, Mulmuley 2011 | cited |
| The Tate conjecture | Hodge ↔ BSD | Tate 1965, Artin–Tate 1966, Milne 1975 | cited |
| Bochner's vanishing | Hodge ↔ Poincaré | Bochner 1946, Myers 1941, Hamilton 1982 | Myers on the unit S³ |
| The renormalization group | Yang–Mills ↔ Navier–Stokes | Wilson 1974, Forster–Nelson–Stephen 1977 | the running coupling; the Kolmogorov scale |
| The sign problem | Yang–Mills ↔ P vs NP | Troyer–Wiese 2005 | cited |
| Manin's algorithm | BSD ↔ P vs NP | Manin 1971 | cited |
| The Diophantine form of RH | Riemann ↔ P vs NP | Davis–Matiyasevich–Robinson 1976 | cited |
| Arnold's geodesics | Navier–Stokes ↔ Poincaré | Arnold 1966 | cited; it has not produced regularity |

The seven questions are the floor's OPEN ENDS (`card_question_*`, each pointing at its stick, whose live fit the map
page shows beside the node). `GET /chains?floor=card_floor_millennium` reads the floor: parts, ends, joints — each
joint the hub both ends touch, with the two edges' own evidence — and the one MISS: Riemann and Navier–Stokes share
no joint; the map shows the indirect path (through Yang–Mills) and says so. `GET /chains?floors=1` lists the floors;
`site/map.html` draws them under "Where two trees connect", the Standard Model beside the Millennium floor.

Nothing is unified by us. The historical fact the floor records is that the joints are where the proofs came from —
Perelman imported a PDE into topology, Wiles' modularity gave BSD its L-function — and the honest state is that no
joint on this map supplies a missing step for any of the six open questions. The map says where a step taken on one
would transfer, and where the field itself converges: the Weil conjectures at the centre — the Riemann hypothesis
over finite fields, a theorem — while the Riemann hypothesis itself stays open.

*Precision, 2026-10-09 (Matt: "Proven Riemann?"):* an earlier draft of this section and the joint card's title said
"the one proven Riemann hypothesis"; on the map the label truncated to exactly the wrong reading. The Riemann
hypothesis is NOT proven. Deligne 1974 proved the Weil conjectures, its analogue over finite fields. The wording was
corrected everywhere it could be, and the one place it cannot be edited — a note already minted on the P versus NP
stick — carries a restated note beside it, since a removal is a record.

