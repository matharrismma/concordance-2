# THE TICK STICK — inferring an open shape from the marks you can reach

Matt, 2026-10-05: *"We build a tick stick. A tool that allows us to infer closer and closer."*

A joiner fitting a board to a crooked wall does not guess the wall. He lays a stick against it, makes a tick at
every point he can reach, and the shape is inferred from the ticks — exact where there is a tick, honest about
the gap between ticks. Nothing is drawn past the last mark.

The engine does the same for an OPEN QUESTION. A Millennium problem asks for a proof, and this engine does not
author proofs (FOUNDATION.md: found, never generated). What it can do is make marks it can stand behind and say
exactly what they establish:

| tick kind   | what it is                                                        | what it needs                    |
|-------------|-------------------------------------------------------------------|----------------------------------|
| bound       | a sealed verification up to a height / size / count               | the ledger seal (HOLDS), `up_to` |
| instance    | a sealed verification of one case                                 | the ledger seal                  |
| witness     | a sealed computation that exhibits something                      | the ledger seal                  |
| equivalence | a cited theorem: this statement ⇔ that one                        | the source                       |
| exclusion   | a cited barrier: proofs of this kind cannot settle the question   | the source                       |
| note        | a remark by a named author (never counts toward the fit)          | —                                |

**The fit** is computed from the ticks and nothing else: the greatest sealed bound, the sealed instances, the cited
equivalences and exclusions, and the open remainder ("beyond T = 200: not verified here"). A bound only ever goes
further (the ratchet). The fit never says the question is settled.

## The doors

    GET  /sticks                      every stick: question, ticks, verified-up-to, excluded, open
    GET  /stick?id=stick_…            one stick with its ticks and fit
    POST /stick  {question, statement, field, references}
    POST /tick   {stick, kind, claim, seal | source, up_to, unit, by}

A sealed tick is refused unless `seal` is the content hash of a HOLDS verification already in this node's keeping:
verify first through POST /verify (or `tools/tick.py`), then tick. A cited tick is refused without a source.
Sticks live in `data/sticks.jsonl` and ride with the node sync (Gen 3 · 1), so every node holds the same marks.

A claim is kept whole up to 2,000 characters (`tickstick.CLAIM_CAP`; it was 600 until 2026-10-08, and 45 kept marks -
the guard notes, mostly - were stored cut mid-sentence). The file is append-only, so a mark kept cut at the old cap
stays in it; the reading supersedes it by a later tick of the same kind and seal whose text begins with the whole cut
text, collapses an exact duplicate onto its first copy, and reports how many it superseded (`superseded`). Every
stick in `tools/tick.py` mints through `_mint_marks`, which skips a mark already kept in full and ticks a cut one
again in full - so re-running a stick is the repair.

## The first stick: the Riemann hypothesis

`number_theory.critical_line` counts the zeros of ζ two independent ways and requires them to agree: the zeros
found ON the critical line (sign changes of Hardy's Z(t)) and the zeros IN the strip (Backlund's argument-principle
count N(T) = θ(T)/π + 1 + S(T), with S(T) followed continuously from σ = 2 to ½). When both equal the claim, every
zero up to T lies on the line — verified to that height, re-checkable by anyone, and no more than that. This is the
method of every published verification; ours is small next to the records and entirely sealed.

    PYTHONPATH=src python tools/tick.py riemann 200      # verify to T = 200, seal it, tick the stick

A P versus NP stick carries the barriers as cited exclusions (relativization — Baker, Gill, Solovay 1975; natural
proofs — Razborov, Rudich 1997; algebrization — Aaronson, Wigderson 2009): an attempt that does not pass them is
not an attempt. The stick is the map of the territory, which is what a human attempt needs, and the honest
referee for one.

## Narrowing by elimination — the program

Matt, 2026-10-05: *"We narrow the window and rerun again. We keep narrowing until we basically solve. We do this
for all of the Millennium problems."* And: *"We are looking at what it is not."*

The stick does not try to prove a Millennium problem — the engine finds, checks, and seals; it does not author
proofs, and these questions are open. What it does is chart, by elimination, the window where the question could
still fail, and push that window with every rerun:

1. **Each tool eliminates a region.** A sealed bound ("no zero off the critical line below height T"), a sealed
   witness from another tool ("no Robin counterexample below N", "no Schoenfeld prime-count violation below X"), a
   cited barrier ("relativizing proofs cannot settle P vs NP") — each rules out somewhere a failure could hide. The
   Riemann stick now carries five independent eliminations: the two zero counts directly (to height 10^7); the
   divisor sum (Robin 1984, and Lagarias 2002, its elementary exception-free form `sigma(n) <= H_n + e^H_n ln H_n`);
   the prime count (Schoenfeld 1976, `|pi(x) - li(x)| < sqrt(x) ln x / (8 pi)` for x >= 2657, exact to x = 2·10^7);
   and the primorials (Nicolas 1983, `N_k/(phi(N_k) ln ln N_k) > e^gamma`). A counterexample would have to evade
   every one at once.

   **An answer in another domain.** `statistics.gue_spacing` takes Odlyzko's published zeros, unfolds them to unit
   mean density, and shows their nearest-neighbour spacings follow the Gaussian Unitary Ensemble of random matrix
   theory (Montgomery-Odlyzko): variance far below the Poisson value 1.0, with strong level repulsion. That is
   evidence from mathematical physics for the Hilbert-Polya spectral picture — the zeros behave like the spectrum
   of a random Hermitian operator. It is evidence, not a proof, and says nothing about on-line-ness.

   **The sight picture.** `number_theory.count_residual` reads the same zeros and looks at the signed residual of
   the count, `S(T) = N(T) - (theta(T)/pi + 1)` — where the smooth prediction *missed*. RH (Selberg) requires the
   misses to balance at zero, with a spread of order `sqrt((1/2 pi^2) ln ln T)`, never walking off the `ln T`
   envelope. They do: mean within 0.001 of zero, spread 0.4 against a Selberg scale of 0.34, no `|S|` above 1.3
   where `ln T` is 9.2. This is the early-warning mark — were the residual ever to drift or its spread to outrun
   the envelope, the miss would be seen marching toward the edge long before any inequality broke. Evidence, not
   a proof.

   **A count is not a verification.** The stick also carries a WITNESS of the zero *count* at a great height —
   `number_theory.zero_count` (Turing's method, cross-checked against the Riemann-von Mangoldt term within
   Backlund's bound on S(T)): 3,945,951,430,271 zeros up to T = 10^12. It is marked as exactly what it is — the
   count in the strip, far beyond the on-line sweep's reach of 10^7, and NOT a claim that those zeros lie on the
   line. It extends the stick's reach; it does not narrow the on-line window.

   **Birch-Swinnerton-Dyer narrows curve by curve.** `elliptic_curves.l_value` re-derives L(E,1), the root number
   (cutoff-independence) and the analytic rank, and Kolyvagin / Gross-Zagier carry analytic rank 0 or 1 to the
   algebraic rank. The curves come from an ingested table (`data/elliptic_curves.jsonl`, John Cremona's ecdata,
   conductor coprime to 6) — 30 sealed INSTANCES (rank 0 and 1) plus the rank-2 (389a1) and rank-3 (5077a1)
   WITNESSES. BSD is verified for each of these curves; every curve added narrows the stick. `tools/tick.py bsd all`
   seals the whole table, skipping any curve already sealed.

2. **The fit reports the surviving window** (`fit.window`): what every elimination leaves standing. A failure, if
   one exists, must evade all of them at once.
3. **Rerun to push the frontier.** The next pass extends an elimination (a larger N, a higher height) or registers
   a new tool. Each pass that finds no counterexample narrows the surviving window. The verifiers run through the
   engine (POST /verify, the nightly benchmark), not by hand.

**The honest ceiling.** Narrowing is evidence, never a proof. "Basically solve" means driving the window as far as
the tools allow and stating exactly what remains. And it only narrows numerically where there IS a numeric
counterexample-window: Riemann (zero height, Robin's inequality, and more) and Birch–Swinnerton-Dyer (curve by
curve). For P vs NP, the Hodge conjecture, Yang–Mills, and Navier–Stokes there is no numeric window to shrink —
their marks are the cited proof-barriers, which say which proofs cannot settle them, not how far a search has
reached. `fit.window.narrows_numerically` says which kind a stick is. Poincaré is kept as the one that is solved.
