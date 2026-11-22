# The Symphony — where music actually touches the keeping

**Status: measured, not built.** 2026-11-22. Sibling to [THE_REVERSAL.md](THE_REVERSAL.md), which
supplies the machinery any of this would ship on.

> *We have a symphony and don't recognize it.*

That is the claim this document tests. It holds, but not where it looks like it should. The parts are
on the **verifier** side. The shelf whose whole subject is that mathematics holds no music at all.

## 1. First the measurement: there is no music in the keeping

Read from the sources the engine itself reads — `cards.jsonl` plus `corpus.EXTRA_CARD_SOURCES`, taken
from `corpus.py` rather than retyped: 70 registered, 69 read, one absent from disk
(`sword_dict_cards.jsonl`):

    933,210 cards · 129 shelves · 1,053,914 edges
      music_theory shelf .................... 6 cards
      acoustics shelf ....................... 4 cards
      edges OUT of those 10 ................. 10   (member_of 7 · part_of 3)
      edges IN  to those 10 ................. 0
    for scale: astronomy 3,850 · physics 6,162 · mathematics 3,979 · chemistry 1,495

Every one of the ten outbound edges is `member_of` or `part_of` — filing plumbing. **Not one
substantive connection, and nothing in the keeping points at music.**

It is worse than thin. Of the ten cards, **nine are `kind=reference`**: seven `card_domchk_*` (one
per verifier *parameter*) and two `card_spine_domain_*` titled "what this engine can check". The
tenth is a single `kind=verified` card recording that the checks were once run:

    card_v_225533310c11   "C -> G = 7 semitones (a perfect fifth) · MIDI 69 = A4 = 440 Hz"

So the engine's entire holding on music is **nine cards describing its own checklist and one receipt
for having used it.** No Pythagoras, no temperament, no Kepler, no Tonnetz, no instrument, no
interval table as *knowledge*. A card titled "Music Theory: semitones" that documents a verifier
*parameter* has nothing to teach the person who asks. This is
[the inversion](REMAINING.md) in miniature: reference bulk where content should be — and the whole
keeping measures the same way, **96.84% of cards and 96.64% of bytes `kind=reference`**
([THE_PRICE_OF_THE_PRIOR.md](THE_PRICE_OF_THE_PRIOR.md) §5). Music is not an unlucky shelf; it is the
engine's own proportions with nothing to hide behind.

*Two things this does NOT mean,* both checked rather than assumed. A `kind=reference` card is not
excluded from retrieval — nothing in `ask.py` filters on that kind (what it drops from how-to answers
is a *shelf* named `reference`, which is not these cards' shelf). And `roots._universe` is the
denominator of **coverage**, counting floor / stick / domain nodes; a reference card not registering
there means music does not count as a *covered domain*, which is a separate matter from whether a
card can be returned. An earlier draft of this section asserted both as one mechanism. It was wrong,
and the point survives without it: the cards can be found and still have nothing in them.

*Verified independently.* `data/shards/core.db` reports exactly `acoustics` 4 and `music_theory` 6,
and no other shard carries a music shelf — so the count is not an artifact of which files I walked.
The edge total 1,053,914 matches the earlier whole-keeping measurement exactly, so this is the same
graph THE_REVERSAL.md measured.

## 2. The symphony is the verifier roster

    95 verifier modules · 457 named checks
    checks whose subject is periodicity / ratio / spectrum / resonance ....... ~17

A first regex said 26; hand-checking cut it to ~17 (`combinations` matched "comb",
`periodic_table.element` matched "period", `wordcraft.homophone` matched "phon"). The raw number is
recorded here because a keyword count that nobody corrects is how the 118-edge miscount happened.

These are the instruments. **Each can already check a piece of music's mathematics under another
domain's name, and no edge joins any two of them.**

| already computable, today | the pair | the shared mathematics |
|---|---|---|
| **harmonic = interval** | `acoustics.harmonic_frequency` · `music.frequency_ratio` | f_n = n·f₀, and every stored interval is f_a/f_b |
| **the log of a ratio** | `neuroscience.weber_fechner` · `acoustics` dB · `music.equal_temperament_freq` | S = k·log(I/I₀) — one law, three units |
| **the octave, in light** | `photonics.second_harmonic` · `music.frequency_ratio` | the same factor 2 |
| **integer period ratios** | `ephemeris.orbital_period` · `astronomy.kepler_third_law` · `music.frequency_ratio` | resonance is consonance |
| **cavity modes** | `photonics.ring_resonator_fsr` | FSR = c/nL *is* a fundamental with its harmonics |
| **lattice sound** | `condensed_matter.phonon_*`, `.debye_temperature`, `.sound_velocity` | the Debye temperature is set by the top phonon frequency |
| **standing-wave condition** | `condensed_matter.bragg` | the same mode condition as a stopped string |
| **period finding** | `quantum_computing.shor_period` | finding a period *is* hearing a pitch |
| **timbre** | `spectral.fourier_convolution`, `riemann_accel`'s NUFFT | the Fourier transform is the definition of timbre |
| **line spectra** | `periodic_table.moseley` | √f linear in Z — the elements' own frequencies |

The third row is the one to look at. The engine says **"second harmonic"** of light and **"octave"**
of sound and never notices that the 2 is the same 2.

## 3. The bridges, computed

Recomputed from first principles, never taken from a source's number. Every figure in this section is
reproducible — `python tools/music_bridges.py` prints all of it, including the refusal in the last
subsection. A number in prose that nobody can re-derive is the thing this repo keeps catching itself
at, so the computation ships beside the claim.

### Every interval is a quotient of two harmonics

    unison      1/1 = h1/h1      fourth       4/3 = h4/h3
    octave      2/1 = h2/h1      major_third  5/4 = h5/h4
    fifth       3/2 = h3/h2      minor_third  6/5 = h6/h5
    major_sixth 5/3 = h5/h3      minor_sixth  8/5 = h8/h5

All 8 of `music._INTERVAL_RATIOS` are f_a/f_b with a,b ≤ 8. `acoustics.harmonic_frequency` computes
f_a and f_b. The music verifier stores the quotient of two numbers the acoustics verifier produces.

### Why the scale has twelve notes — Diophantine, not aesthetic

log₂(3/2) = 0.584962500721, continued fraction **[0; 1, 1, 2, 2, 3, 1, 5, 2]**. Its convergents:

    1/2    denominator  2     err +101.955 cents per fifth
    3/5    denominator  5     err  -18.045          <- the PENTATONIC scale
    7/12   denominator 12     err   +1.955          <- the CHROMATIC scale
    24/41  denominator 41     err   -0.484
    31/53  denominator 53     err   +0.068          <- the 53-tone scale, long known to theorists

The two divisions humanity actually uses, **5 and 12**, are consecutive convergents of one logarithm.
That is a derivation, not a resemblance — and it is computable with what the repo already has.

### The comma is the price, and it is exact

    (3/2)^12 / 2^7 = 531441/524288 = 3^12/2^19 = 23.460010 cents

No stack of pure fifths ever closes an octave: 3^m = 2^(n+m) is impossible by unique factorization,
for **every** m. So something must be tempered, and the bill falls unevenly:

    interval      just      12-TET     diff (cents)
    unison        1.00000   1.00000     +0.0000   exact
    fifth         1.50000   1.49831     -1.9550   subtle
    fourth        1.33333   1.33484     +1.9550   subtle
    major_third   1.25000   1.25992    +13.6863   audible
    minor_third   1.20000   1.18921    -15.6413   audible
    minor_sixth   1.60000   1.58740    -13.6863   audible
    major_sixth   1.66667   1.68179    +15.6413   audible
    octave        2.00000   2.00000     +0.0000   exact

Only the unison and the octave survive exactly. Note the internal check: the 12-TET fifth's error,
±1.9550 cents, **is** the 7/12 convergent residual from the table above. Two independent routes, one
number.

### Orbital resonance is the consonance test

Jupiter's inner moons, periods in days (JPL/IAU, public data):

    Europa  /Io       2.007295   vs 2:1   +0.36%
    Ganymede/Europa   2.014697   vs 2:1   +0.73%

Io : Europa : Ganymede = 1 : 2 : 4. **The Laplace resonance is two stacked octaves.**
`ephemeris.orbital_period` computes the periods; `music.frequency_ratio` tests 2:1; neither knows
the other exists.

### Kepler's *Harmonice Mundi* V, recomputed from ((1+e)/(1−e))²

    Earth    1.0691 vs 16:15   +0.23%        Saturn   1.2439 vs 5:4    -0.49%
    Jupiter  1.2143 vs 6:5     +1.19%        Venus    1.0275 vs 25:24  -1.36%
    Mars     1.4546 vs 3:2     -3.03%        Mercury  2.3035 vs 12:5   -4.02%

The claim holds at Earth and fails at Mercury — a limit that is **computable**, which is why
THE_REVERSAL.md already files this as the worked `reverses_parallel` example. Two honest caveats: any
pass/fail line here (1.5%, say) is **mine and arbitrary**, not Kepler's, so the percentages are the
result and the verdict is not; and Jupiter/Saturn shift in the third decimal with the eccentricity
source — an earlier run of mine gave +1.15% and −0.75%. The orderings do not move.

### One family, two theorems — stated carefully

The comma says a required commensurability has no integer solution. So does the crystallographic
restriction: a periodic lattice admits an n-fold rotation only when 2cos(2π/n) ∈ ℤ, which holds for
n = 1,2,3,4,6 and fails for 5 at 2cos72° = (√5−1)/2 = 0.618034. Five-fold symmetry therefore needs
cut-and-project instead of a lattice — the girih construction.

**These are the same *kind* of argument and not the same theorem.** The comma rests on unique
factorization; the crystal ban on an irrationality. Writing them as one theorem is the overclaim this
section exists to refuse.

## 4. What must be refused, and why

A twin may arrive only three ways — authored, derived, or cited — **never by stem match**
(THE_REVERSAL.md §4). Music is where that rule earns its keep, because everything sounds like music
if you want it to.

- **`sound_law.*`** (`correspondence`, `dissimilation`, `voicing`, `vowel_shift`) — historical
  phonology. "Sound" in a different sense entirely: categorical consonant shifts, not frequency.
  **Refused.** It is the most tempting false bridge in the roster precisely because the name matches.
- **"Architecture is frozen music."** Measured: `architecture.*` is `floor_area_ratio`,
  `occupant_load`, `stair_compliance`, `structural_load`, `window_wall_ratio` — building code, with
  no proportion or ratio check anywhere. The aphorism has **no computable support here** and gets no
  card. A famous sentence is not evidence.
- **Numerology of any kind.** Ratios are checkable; letter-and-number correspondences are not, and
  the engine holds no card for them. The mirror frames of
  *El Patrón Secreto de la Música* (Áureo Puerta Carreño) are used the same way THE_REVERSAL.md uses
  them: the mathematics is public and recomputed, the presentation is his, and we use the
  mathematics, never the wall.

## 5. The gaps, which become wants

- **Astronomy has no Doppler.** `acoustics` computes `f_observed` from source/observer velocity;
  `astronomy` has no redshift or radial-velocity check at all. The single most familiar music↔sky
  bridge is **half-built** — and this is the honest answer to the earlier question of why
  music↔astronomy measured zero edges. Not poetry: a missing check.
- **No cochlea, no tonotopy.** `neuroscience` is `goldman`, `nernst_potential`, `weber_fechner`;
  `biology` has nothing on hearing. Place-frequency mapping is absent.
- **No music corpus for `info_theory.shannon_entropy`.** The check exists; there is nothing to run it
  on, because §1 — there is no music content to measure.
- **No card content whatsoever.** Before any bridge can attach, both endpoints must resolve
  (`_apply_bridges` enforces this, 0-FP). Today the music endpoint is nine self-descriptions. **The
  bridges cannot be built until the shelf holds something to bridge.**

## 6. What to build, in order

1. **Mint the music shelf from public-domain sources** — Helmholtz (*On the Sensations of Tone*,
   1863/1885 tr.), Rayleigh (*Theory of Sound*, 1877), Euler's *Tentamen* and the Tonnetz, Kepler's
   *Harmonice Mundi* (1619). Content cards, not `reference` cards; a `reference` card cannot answer.
   Nothing here is generated: found, cited, sealed.
2. **`data/music_bridges.jsonl`** — the overlay, on the machinery `_apply_bridges` already has
   (reciprocal attach, 0-FP endpoints, warn on unresolved). The table in §2 is its first ten rows.
3. **Close the Doppler gap** — `astronomy.radial_velocity`, the formula `acoustics` already carries.
   One check turns the half-bridge into a bridge.
4. **Wire the derivation** — the §3 continued fraction makes "why twelve notes" a *computed* answer.
   Nothing in the roster computes a convergent today, and `approximation.py` is not a near miss: its
   one check is `approximation.get_close`, a Taylor/Lipschitz *bounded estimate* around an anchor
   point, a different shape entirely. A convergent check would be new work, sitting most naturally
   beside `number_theory`.

Each of these ends in a product line, per doctrine: a family asking *why does a piano have twelve
keys* should get the convergents of log₂(3/2), cited and checked — not a `reference` card that says
"Music Theory: semitones".

## 7. What this document does not establish

- **No card was minted and no bridge was built.** This is a measurement and a design.
- **The ~17 count is a hand-corrected keyword match, not a semantic audit.** Treat it as an estimate
  with a named method, which is why the raw 26 is recorded beside it.
- **I did not measure at box shape.** All figures come from the local checkout.
- The `card_v_225533310c11` receipt shows the four music checks pass. **Nothing here shows any
  cross-domain bridge passing, because none exists to run.** Every row of the §2 table is a claim
  about two formulas being the same, verified by reading them — not by a check the engine ran.
