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
