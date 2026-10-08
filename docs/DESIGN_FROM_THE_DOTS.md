# Design from the dots — what is linear in the engine, what is not, and the levers that follow

*2026-10-08. Matt: "How do we use what we have learned to shape the design of the project? The closer we map the
dots and can map them to linear functions, the more precisely we should be able to design our engine."*

The thesis holds, and it holds for a reason that can be stated: a linear step has a known bound, a known null
space and a known sensitivity. A bound makes a threshold principled. A null space says exactly what the step
cannot see, so a miss stays a miss. A sensitivity says how a small error in the input moves the output, which
is what "precision" means in an engine. A step that is not linear has none of those for free. So the design rule
is: **map every finding step to a linear function on an explicit vector space, put every judging step at the
boundary as a deterministic measurement, and make each linear step's bound, basis and completeness a test.**

## 1. What this week taught, as design facts

| Lesson | Where it was learned | The linear fact |
|---|---|---|
| The delta is the dot product | the delta stick; the pronunciation and etymology lookups | An exact lookup by id is the delta functional, the cheapest and most precise read there is. Ranking (the inner product) surfaced "encyclopedias" above "encyclopedia"; the direct id read fixed it. |
| The score is an inner product | the joints stick (sealed: 3/√12 = 0.866 for a query against a card) | The ranking score is bilinear in query counts × card counts, normalized to a cosine, bounded by one (Cauchy–Schwarz). A threshold on it is a threshold on an angle. |
| Routing is a projector | the joints stick; the form measurement | The domain router is |d⟩⟨d|: idempotent, so routing twice is routing once. Its precision is the orthogonality of the domains. |
| The domains are not orthogonal | docs/OUR_FORM_MEASURED: routing recall 12.4% at k=1, 27.6% at k=3 | The Gram matrix of the 124 domain vocabularies has large off-diagonals. That one number is the engine's routing error. |
| The space is nearly full rank | OUR_FORM_MEASURED: 98 of 124 directions carry 90% of the energy | Domains are real directions, not redundant ones. The basis is worth orthogonalizing rather than collapsing. |
| Completeness is "no orphans" | the joints stick (Σ projections = ‖ψ‖² in any basis); 0 multi-shelf cards | Σ|i⟩⟨i| = 1 is an invariant the floor tree already states: every card reachable through its shelf, every shelf through the floor. |
| A verifier is a measurement, not a function of the space | the joints stick's exclusions; the recall gate incident | Verifiers are deterministic, idempotent, commuting, and do not disturb the card. They must never build or rank the space (a verifier that started the corpus build inside its 8 s budget shed every row). |
| Any linear map is a rotation and a stretch | the SVD stick; the frozen cache | The singular values say which directions carry signal. Shedding by spectrum (keep 98 of 124) is design; shedding by guess is not. |
| A complication must not weigh down the base | Matt, 2026-10-08 | In linear terms: a complication is a block of the Gram matrix with its own basis vectors; removable without changing the other blocks' projectors. "Without weighing down the base tool" is block-diagonality. |

## 2. The two halves of the engine

**The linear core (finding):** the token counts, the cosine score, the domain projectors, the delta reads, the
semantic index, the call numbers. Every step here is a linear functional or a projection on one explicit space:
the keeping as a real, finite inner-product space of 882,022 kets in 124 directions. This is where "the closer
we map the dots to linear functions" buys precision, because every step has a bound, a basis and a null space
we can measure.

**The measured boundary (judging):** the verifiers, the discern gate, the crisis net, the kernel, the extractors.
Deliberately not linear. Their precision comes from determinism and the zero-false-positive covenant, not from
linearity. The design error to avoid is mixing the halves: a verifier inside ranking, or ranking inside a
verifier.

## 3. The levers, in order

1. **Delta before inner product.** Every shelf whose cards have a deterministic address (`card_src_<shelf>_<slug>`)
   is read by id first and ranked only as a fallback. Done for pronunciation and etymology; extend to the
   dictionary, elements, places, nuclides, and every found-fact table. Precision: exact. Cost: O(1).
2. **Orthogonalize the domain basis.** Compute the Gram matrix of the 124 domain vocabularies; remove the common
   mode (tokens shared by most domains) and Gram–Schmidt the rest, or take the principal axes from the SVD of the
   domain–token matrix; re-measure routing recall. The target is a number: from 12.4% to above 60% at k=1. This is
   the single largest precision gain available, and it is an experiment off the production box (memory-bound).
3. **Make completeness a gate line.** The floor-reachability test exists; make its count (0 orphans, every shelf
   rooted) a line of the deploy gate beside benchmarks, assay, front door and recall, so Σ|i⟩⟨i| = 1 is proven on
   every deploy, not assumed.
4. **Set thresholds from the bound.** The front door's "found" column and the semantic index's cutoffs are angles
   on a cosine bounded by one. State each threshold as an angle, test it against the misses it creates, and never
   tune it by hand.
5. **Keep measurement at the boundary.** The rule landed today: a verifier that reads a shelf asks whether the
   corpus is loaded and declines otherwise; it never builds. Generalize: no verifier calls search; no ranking calls
   a verifier.
6. **Shed by spectrum.** The frozen cache keeps the derived linear structure across boots; the semantic index keeps
   the directions carrying the energy. When the box is short of memory, the singular values say what to freeze.
7. **Build complications as blocks.** Each complication gets its own basis (its shelves, its vocabulary, its
   phrasings), its own projector, and a test that the base's routing recall is unchanged with the block removed.

## 4. What stays nonlinear on purpose

Verdicts. Gates. The crisis net. Discernment. The extractors, which are patterns, and the kernel, which is a
covenant. These are not made more precise by linear design; they are made precise by being deterministic, pinned,
and ratcheted. The joints stick keeps the list of what bra-ket does not say about the engine: no amplitudes, no
Born rule, no superposition of a card, no evolution, no non-commuting observables, no entanglement.

## 5. Quantifying an assembled path: gradient, divergence, curl

*Matt: "we use gradient, divergence and Curl to quantify the preciseness of the assembled path."*

A path the engine assembles (find → route → verify → serve, or a chain of cards) is a flow on the connection
graph, and three discrete numbers say how precise it is. Each one already has an engine measurement behind it;
the stick `assembled_path` seals the calculus and names what carries over.

| Operator | The question it asks of a path | Zero means | The engine's measurement today | The invariant (Kirchhoff) |
|---|---|---|---|---|
| **Curl** | Does the answer depend on the route? | conservative: the same verdict whichever order the steps ran | verifiers commute; the recall set credits a phrasing reached by a different family; a chain's intersection is route-free | the voltage law, curl = 0 around every loop |
| **Divergence** | Where does the path create or lose content? | every token of the output entered through a cited source; every loss is a recorded miss | the coverage block (PARTIAL when material text lies outside checked spans) is the divergence meter; "a miss stays a miss" is the sink rule | the current law, div = 0 at every node |
| **Gradient** | Does each step climb the fit? | a step that learned nothing | the candidates door narrows; the Wisdom Engine's front-load → recall → narrow → parable is descent on ambiguity | the potential exists only when curl = 0 |

Two design consequences follow. First, a path is precise when it is **conservative** (curl 0) and **sourced**
(divergence 0 away from cited cards) and **monotone** (positive gradient at every step), and each of the three is
a count on the live graph, not a metaphor. Second, the Laplacian, div of grad, is the number that says whether a
potential has a hidden peak: a harmonic fit has no interior extreme, which is the condition the resonance stick
named as "no hidden division by zero".

What does not carry over: no continuum, no smoothness, curl only on cycles, and no Helmholtz decomposition of
the engine's flow has been computed yet. That is the second measurement below.

## 6. The next measurements

Lever 2 is the one with a number attached and nothing built yet. The measurement is one script over the existing
form measurement: the Gram matrix of the domain vocabularies, its off-diagonal mass, the common-mode tokens, and
routing recall before and after orthogonalization, run off the production box. That number decides whether the
domain basis is rebuilt.

The second is the Hodge decomposition of the engine's flow: take the live verify paths (the order in which the
verifiers and doors actually ran for a sample of claims), build the graph, and split the flow into its gradient
part, its curl part and its harmonic part. The curl mass is the engine's route-dependence, measured once instead
of argued; the divergence at each node is the unsourced content, which should be zero everywhere but the keeping's
cited cards and the recorded misses.
