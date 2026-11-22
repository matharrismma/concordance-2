# The Reversal — every major has a minor twin

**Status: design, not built.** 2026-11-22.

Greene's unit carries its own Reversal: the section that says when the law does *not* hold. Ours
carries none. Measured on 2026-11-22 across the whole keeping:

    1,478,343 rows · 946,739 cards
    cards carrying any limit / bound / scope / caveat / reversal key ...... 0
    edges that can carry a limit or refutation ........................... 118  (0.011%)
      counterexample_of 82 · limits 34 · bounded_by 1 · falsified_by 1
    member_of ........................................................... 86.2%
    member_of + citation plumbing ....................................... 99.6%

A keeping of 946,739 claims and 118 ways to say "here is where this fails."

## 1. The shape comes from the music, and it closes at three

**Corrected 2026-11-22.** This section first said the music closed at *two*. It does not. Two of
the twins are defined by the chord itself; the third is defined by an axis chosen for the whole
system, and leaving it out would have let an unreproducible reversal in through the front door.

| twin | music | meaning for a card |
|---|---|---|
| **relative** | C major → A minor. Same key signature, **same seven notes**, tonic a minor third below. | **Same evidence, different centre.** Not a counter-claim — the same material read from where the other person stands. |
| **parallel** | C major → C minor. **Same tonic**, different signature. | **Same subject, different conditions.** The boundary: where this claim stops holding. |
| **mirror** | The whole circle reflected about an axis — majors running up the fifths against minors running up the fourths. | **The same claim under an inverted frame.** Meaningless unless the frame is named. |

The first two are checkable from the card alone, through our own `music.interval_semitones`:

    C4 -> A3   claimed -3   CONFIRMED      (relative: a minor third below)
    C4 -> C4   claimed  0   CONFIRMED      (parallel: same tonic)
    G4 -> E4   claimed -3   CONFIRMED
    C4 -> A3   claimed -4   MISMATCH       (negative control — the check can fail)

### The mirror is different: it carries an axis, or it is not a twin at all

Reading the seven rows of the mirror as pairs and placing each root on the circle of fifths
(C=0, each step a fifth):

    Ab maj / Db min    8 + 7 = 3 (mod 12)     +5 semitones
    Eb maj / F# min    9 + 6 = 3              +3
    Bb maj / B  min   10 + 5 = 3              +1
    F  maj / E  min   11 + 4 = 3              -1
    C  maj / A  min    0 + 3 = 3              -3
    G  maj / D  min    1 + 2 = 3              -5
    D  maj / G  min    2 + 1 = 3              -7

**The sum is constant.** A constant sum *is* a reflection — the axis here sits between G and D.
The semitone gaps fall by exactly 2 a step, which is the signature of two sequences running in
opposite directions: fifths and fourths are inverses, so the two sides are one cycle read both
ways. *Two sides of one pattern*, as the source puts it.

The consequence for the field is strict. **Move the axis and every twin changes.** A `mirror`
reversal that does not record its axis cannot be reproduced and therefore cannot be falsified —
it is an opinion wearing a bound's clothes. So:

> A `mirror` reversal MUST name its axis. Without one the row is rejected at load, not warned.

`relative` and `parallel` need no axis because the chord supplies it. That asymmetry is the real
content of the three-way split, and it is why the set could not close at two.

*Source, checked and not checked.* The mirror frames are **Áureo Puerta Carreño's** —
*El Patrón Secreto de la Música* (thesecretpatternofmusic.com, 2017–), a hexagonal space for the
twelve notes, with a book and a research body behind it. The arithmetic above is mine and it holds
exactly; I verified it rather than taking it. Whether this construction is the standard "negative
harmony" of Levy and others I have **not** verified — that reflects in pitch space about a different
axis, and the two are not obviously the same operation.

**The Greene rule applies.** The mathematics is public: the Tonnetz is Euler's, mod-12 reflection is
arithmetic, and anyone can recompute every number here. The *presentation* — his hexagonal star, his
naming, his diagrams — is his work, and we use the mathematics, never the wall. The keeping holds no
card for any of it.

## 2. Where it lives: an overlay, not a field on 946,739 cards

`data/reversal_bridges.jsonl`, joining the seven existing `*_bridges.jsonl` overlays (10–906 rows
each) and carried by the machinery `_apply_bridges` already has. Row format is the one
`reference_bridges.jsonl` uses, unchanged:

    {"a": "<card>", "b": "<twin>", "subject": "...",
     "relationship": "reverses_relative" | "reverses_parallel" | "reverses_mirror",
     "axis": "<REQUIRED for reverses_mirror, forbidden otherwise>",
     "evidence": "<the boundary, and what states it>", "a_title": "..."}

Why an overlay and not a card field:

- the card files are **never mutated on disk** — the same reason the two trees are grafted this way;
- it survives regeneration, and data files are never deployed (seeds run on the box, idempotent);
- it is git-tracked and small;
- `_apply_bridges` already attaches **reciprocally**, already applies the **0-FP endpoint test**
  (attach nothing unless both endpoints resolve), and already **counts and warns** on unresolved
  rows instead of skipping silently.

Reciprocal attachment is musically right as well as cheap: A minor's relative major is C major.
The twin relation is symmetric, so the overlay states it once.

## 3. Three states, and the third must be loud

    bounded        a twin is named
    unbounded      no twin found yet       <- 946,739 cards, on day one
    self_bounding  the card is its own twin UNDER A NAMED AXIS — and never alone

On day one every card is `unbounded`. That is the honest reading, and it is not the same as
"always holds": it means **nobody has bounded this**. So the state must be *visible*, not absent.

This is the load-bearing decision. A zero without its denominator is uninterpretable, and a claim
without its limit is the same error wearing different clothes. `house.next_step` on an unbounded
card should say so in the envelope — which turns 946,739 silences into countable **wants**, and
gaps becoming wants is already doctrine. The field's first job is not to be full. It is to make
the emptiness audible.

### The third state was wrong, and the tritone fixed it

This slot first read `universal` — "claimed to hold without limit, requires a signature." That was
an authority claim dressed as a state, and it is exactly how a postulate gets kept as a fact.

The mirror supplies the better one. Under a reflection the axis maps to **itself**, and six
semitones is the *only* interval that is its own inverse (computed, mod 12: `[6]`). So a mirror
has a fixed point, and the keeping needs the matching slot: a card whose reversal is itself — a
claim that holds exactly at its own boundary.

So `self_bounding` replaces `universal`: earned by demonstration, never by authority. The source
frame states the test outright — *only the tritone, the axis, never moves: it splits the octave
exactly in half.* Solving `2x = k (mod 12)` over every axis gives the rule, and it is strict:

    k   fixed points      apart        k   fixed points      apart
    0   C,  F#              6          6   D#, A               6
    2   C#, G               6          8   E,  A#              6
    4   D,  G#              6         10   F,  B               6
    1,3,5,7,9,11  (none)    -

    fixed points per axis: 2 for six axes, 0 for the other six — NEVER exactly one
    distance between a pair: always 6 semitones, every time
    k=4 fixes exactly D and G# — the column the source frame draws

Three rules fall straight out, and together they are the demonstration procedure this document
was missing:

1. **An axis is required.** D is fixed under `k=4` and moves under `k=0`. Being its own twin is
   never absolute — it is held *with respect to a mirror*. The same rule as `reverses_mirror`.
2. **Fixed points come in pairs.** A lone `self_bounding` card is a structural error, not a strong
   claim: if one card is fixed under an axis, exactly one other is too, a tritone away. So the
   overlay is checkable — **count `self_bounding` rows per axis; the count must be 0 or 2.** You
   do not assert self-bounding, you *produce the pair*.
3. **Half of all frames admit none.** Six axes of twelve have no fixed point at all. "Nothing in
   this frame is its own limit" is an ordinary, legitimate state.

### And I had its meaning backwards

The paragraph here previously called `self_bounding` "the honest form of the strongest claim."
That is wrong, and the correction matters more than the slot does.

The tritone is not the most stable interval in the scale — it is the least. The *diabolus in
musica*: belonging to no key, demanding resolution. A fixed point is where a claim and its
reversal **coincide**, which is not maximum certainty but maximum ambiguity. Splitting the octave
exactly in half means standing the same distance from the tonic in both directions — so for a
card, it means **the evidence supports the claim and its denial equally**.

So a `self_bounding` card is the most *unresolved* card in the keeping, not the most certain. It
should rank **low** on a claim query, or surface carrying its state — the exact opposite of what
the old `universal` flag would have done. It is the formal shape of the covenant's own last
clause: *stop when the evidence is incomplete.*

## 4. What may fill it, and what may not

Never generated. There is no model at runtime, and *emulating is not generating: record and rules,
halt where the record is silent.* A twin may arrive only three ways:

1. **authored** — a person writes it, signed;
2. **derived** — a verifier computed a failing case (`counterexample_of` is the existing edge);
3. **cited** — a source states the limit, and the citation is the evidence.

Never by stem match. The keeping already shows why: a Sun Tzu card carries
`instance_of -> reciprocity` on the evidence `"names the move: benefits"` — one keyword, inside a
phrase the source itself calls pointless. A reversal minted that way would be worse than none,
because it would *look* like a bound and hold nothing.

The existing 118 limiting edges migrate **into** this field rather than living beside it. Two ways
to say one thing is how `same_form_as` happened.

## 5. The two cards that prove the shape

**Relative — Machiavelli.** *Inspire fear in such a way that, if he does not win love, he avoids
hatred* — and the boundary is naming: abstain from his citizens' property and their women. That is
one observation read from two tonics, with the point where the centre shifts stated outright. Our
card filed that limit as two keyword patterns (`"endure"` → outlive_the_founder, `"inspire"` →
win_the_narrative), neither of which is what the sentence says. With the field it is one
`reverses_relative` edge whose evidence is the boundary itself.

**Parallel — Kepler.** The planetary harmonies of *Harmonice Mundi* V, recomputed from
((1+e)/(1−e))²:

    Earth     1.0691  vs 16:15  +0.23%        Mars      1.4546  vs 3:2   -3.03%
    Saturn    1.2407  vs 5:4    -0.75%        Mercury   2.3035  vs 12:5  -4.02%
    Jupiter   1.2137  vs 6:5    +1.15%        Venus     1.0275  vs 25:24 -1.36%

Same subject, different conditions: the claim holds at Earth and fails at Mercury. That is a
`reverses_parallel` whose evidence is **computable**, so a verifier can mint it and re-check it.
The strongest kind of twin, because it cannot rot without the check going red.

## 6. Why the field can never be filled, and why that is correct

Twelve perfect fifths overshoot seven octaves by 531441/524288 — about 23 cents. You cannot have
pure fifths and pure octaves at once; something must be tempered. The same holds here: you cannot
have a keeping where every card is bounded *and* every card stays simple. Cards will remain
`unbounded` forever.

The field's purpose is not to eliminate that. It is to turn it into **a tuning error you can read**
instead of silence you can mistake for truth. Everything is bound; proof is a chain of bound steps;
a postulate works, so the truth is inferred — never kept as fact.

## 7. Cost to build

| piece | change |
|---|---|
| `data/reversal_bridges.jsonl` | new overlay, starts near-empty, grows by hand and by verifier |
| loader | a sibling of `_apply_bridges` (reciprocal attach, 0-FP endpoints, warn on unresolved) |
| envelope | one line in `house` — the change that makes 946,739 silences audible |
| vocabulary | +3 relationships, and the `same_form`/`same_form_as`/`shares_form_with` dedupe must land with it, or the design inherits the rot |
| axis rule | `reverses_mirror` without an `axis` is **rejected at load**, not warned — an unreproducible twin is worse than none |
| pair rule | `self_bounding` rows per axis must number **0 or 2, never 1** — a lone fixed point is a structural error and fails the load |
| migration | fold the existing 118 limiting edges in; no card file is rewritten |

**Open, and not decided here.** The pair rule makes `self_bounding` *falsifiable* without yet
making it *derivable*: it catches a bad claim but does not tell you how to reflect a card in the
first place. Reflection is defined for a pitch and still undefined for a proposition, so the pair
count is a check on the overlay, not a construction. Also open: whether an axis is declared
per-shelf or per-row; and whether an unbounded card should be *rankable* at all on a claim query,
or should always surface with its state attached.
