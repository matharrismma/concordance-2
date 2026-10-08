# Our form, measured against the spherical one (2026-10-08)

Matt: "Think of bubbles joined. Each sphere is in its domain. The domains are clustered based on similarity.
Superposition allows the spheres to be in two places at once. Inside the sphere we have a grid and coordinates to
trace the location of each component. They run inside of a form and are connected along axis. Allow the shape to be
in the form of the most efficient vectors. Look at our own form. See if this is more efficient."

This is a reading of one day, not a seal: the whole keeping was streamed once on the desk (no engine, no index), one
token vector built per shelf, and four things measured. Script: `scratchpad/measure_form.py`; raw numbers:
`scratchpad/form_measure.json` (desk only). Live search timings were taken on the box, read-only.

## The names

Matt, the same day: "I've been saying cards and shelves but we arrange them in tensors and domains." So:
a **domain** is a sphere (what the library calls a shelf), and a **tensor** is the arrangement inside it (what the
library calls cards with call numbers). The library names stay on the surface for readers; the form's names are
domains and tensors, and this page uses both.

## What our form is today

| Fact | Measured |
|---|---|
| Cards | 882,022 in 49 files, read in 34 s with no index |
| Shelves (the domains) | 124 |
| Cards on two shelves (superposition) | 0 |
| Grid inside each sphere | the call number `shelf.class.item` and the bands: every card has a coordinate |
| Axes between spheres | the `connections` shelf, 19,633 cards, plus `uses` edges and chains |
| Search | an inverted index, rarest token first, seat never capped; p50 ≈ 110 ms, p95 ≈ 530 ms on 20 live queries; one 0-hit query 1.8 s |
| Resident engine | 1,193 MB; boot 7.4 s (corpus 6.1 s, of which the index build is 4.4 s) |

So the keeping already has the bubble form's parts: spheres (shelves), a grid inside each, axes between them. What it
does not have is superposition (no card belongs to two shelves) and clustering by likeness (shelves are grouped by
provenance: where a card came from, not what it is like).

## 1. Do the domains cluster by likeness?

Yes, and the clusters are recognisable. At cosine distance 0.75 on unit shelf vectors:

- the verifier sciences: geometry, optics, acoustics, electrical, thermodynamics, probability, information theory, linear algebra, law, materials, oceanography and 16 more
- the reference sciences: medicine, history, economics, mathematics, astronomy, physics, biology, chemistry, psychology, sociology, philosophy
- the Scripture family: commentary, connections, lexicon, encyclopedia, topical, classics, strategy, codex, patristics
- the engine's own working shelves: calculations, theories, bridges, the-works, forms, almanac
- the acquired bulk: taxonomy, dictionary, pronunciation, gutenberg, geography

The last cluster is 616,002 cards, 53% of the keeping, and it looks alike to a token vector because it is generic
English. Nearest neighbours confirm the picture: physics sits by mathematics, astronomy, chemistry; hebrew_ot by
sermons, topical, connections; theories by bridges, physics, mathematics.

## 2. Are the shelves the most efficient vectors?

Singular values of the 124-shelf unit matrix: 90% of the energy needs 98 directions, 99% needs 121. The shelf space
is full rank. The domains are already nearly orthogonal, so an SVD basis would be the shelves themselves and a
low-rank compression would throw away real domains, not redundancy. A dense embedding per card would cost more than
the whole engine does now (882,022 × 300 float32 = 1.06 GB against 1.19 GB resident today).

## 3. Would routing a query to its nearest spheres keep our answers?

No. For 29 live queries with 145 top-5 answers from the box:

| Route to | Share of the engine's own answers kept |
|---|---|
| nearest 1 shelf | 12.4% |
| nearest 3 shelves | 27.6% |

The engine's answers come from small cross-cutting shelves (theories 50 of 145, dictionary 20, codex 13, patristics,
calculations, physics), whose centroids are generic. "escape velocity" routes by centroid to hydrology, systems and
the-works; the engine answers from theories and dictionary. "the speed of light" routes to physical_constants and the
engine answers from theories. A shelf is the wrong grain for routing: the rarest-token posting list already lands on
the exact cards across all 124 shelves in about a tenth of a second. Sphere-first search would be slower in quality
for no gain in time.

## 4. Where the weight sits

Tokens by shelf: commentary 9.0 M (30% of all tokens in 51,272 cards), dictionary 3.0 M, gutenberg 3.0 M,
pronunciation 2.1 M, taxonomy 1.7 M. The acquired-bulk cluster is 53% of the cards and 23% of the tokens, and it
answers queries only through headwords and titles. That is exactly the part that should be cold.

## Verdict

The spherical form is not a more efficient way to find. It is a more efficient way to place.

- Keep the inverted index for finding. It is precise where spheres are coarse, and it is already fast.
- Take the bubbles for memory: the acquired-bulk cluster (taxonomy, dictionary, pronunciation, gutenberg, geography)
  as cold spheres, their full text and postings in shards off the heap, only their title index resident. This is the
  memory cut already planned (roughly 400 to 600 MB of the 1,193 MB) and the measurement says which spheres to move
  first and that nothing in search quality depends on them being resident.
- Take superposition as metadata, not as a second index: a weighted dual shelf for cards that straddle domains (the
  theories, bridges and connections shelves answer most queries and belong to several bubbles). It helps browse and
  decks; it does not speed search.
- The grid and the axes already exist (call numbers, connections, chains). Nothing to build there.
- The arrangement inside a sphere is a tensor (Matt, later the same day: "Tensors is what I've been trying to come
  up with"): the indices are the grid's axes (shelf, class, item; token; surface), the components are the cards,
  and the invariants are what every reading in every frame must agree on (counts, norms, seals, a card's
  connections). Measured, the keeping is a sparse card-by-token-by-shelf array with 30.0 M nonzero entries. The
  spherical matrix rotates its components; the invariants are the meaning. That is a description of what we have,
  and it says the same thing as the measurement: keep the sparse form.
- The spherical matrix is the right reading of what scoring does (likeness is a dot product on the unit sphere), and
  the engine already does it sparsely; a dense version would cost more memory than it saves.

Nothing was changed by this reading. The sticks minted the same day (svd, bubbles) carry the arithmetic; this page
carries the measurement.
