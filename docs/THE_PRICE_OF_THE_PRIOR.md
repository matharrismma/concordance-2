# The Price of the Prior — an outside benchmark scores what we only assert

**Status: read, verified, and applied to our own numbers. 2026-11-22.** Nothing here changes the
engine. Source: *tufazip: Learning to Compress a Billion Bytes of Wikipedia*, Tommy He, Tufa Labs,
2026-10-14 (`https://tufalabs.ai/research/tufazip/`). Every figure below was read off that page
directly, not from a summary of it. Our own figures are reproducible: `python tools/keeping_bits.py .`

## 1. What the entry is

He took **#2 on the Large Text Compression Benchmark** (at submission, 2026-09-07) — Matt Mahoney's
benchmark, running 20+ years — and is the best-performing entry ever to use a neural network as its
**sole** predictor. One billion bytes of Wikipedia (`enwik9`) compressed to **105,388,353 bytes**
(105.39 MB), *including the offline-trained weights and the decoder*. That is **0.843 bits per byte**
for everything needed to reconstruct the file.

The final predictor is a 12-layer, 163M-parameter decoder-only Transformer, initialized from a
34M-parameter offline model quantized to **4.33 MB**, with a 4K word vocabulary, a **192-token
context**, a 35M-token replay window and 0.25 replay dropout.

## 2. The mechanism is already our architecture

The encoder and the decoder **start from identical weights and run the same deterministic loop** —
predict, encode or decode, then perform the same training update now that both sides know the token.
The decoder reconstructs the model's training as it reconstructs the text. *The weights learned
online never need to be transferred.* The update must be fully deterministic or the scheme is not
lossless.

Three correspondences, stated as correspondences and not as credit:

- **The receiver re-derives rather than receives.** That is the same move as
  [COHERENT_MODEL.md](COHERENT_MODEL.md) and the kernel: a deterministic procedure both sides can run
  means the artifact does not have to carry the model. He needs it for losslessness; we need it to
  own our own runtime. Same constraint, different reason.
- **The winner is a looped transformer.** The chosen prior, Cycle2, is two blocks repeated six times
  (`ABABABABABAB`), stored once, then copied into twelve independent layers that specialize online.
  Recurrence offline, specialization at use. No document in this repo states that hypothesis, so
  there is nothing here to cite for it; what this page adds is that the shape **won on an outside
  benchmark**, beating nine other layouts including full depth, which cost 20.70 MB to store against
  Cycle2's 4.33.
- **Replay is free because the text is already decoded.** Revisiting earlier text costs computation,
  never archive bytes. The keeping sits outside the loop, which is exactly why it can be read again
  without being shipped again.

## 3. The scoring rule is our doctrine, in bits

The benchmark scores the compressed text **plus the zipped decoder and anything needed to decode**.
So, in his words, better predictions must save more space than an offline model adds. The target is
one inequality:

    transferred model + compressed text and decoder  <  online baseline

The three full `enwik9` runs are the whole argument:

| configuration | payload MB | decoder + weights MB | total MB |
|---|---|---|---|
| Online v1 (no prior) | 105.924 | 0.055 | 105.979 |
| L6 (six-layer prior) | **99.173** | 10.945 | 110.118 |
| C2 (Cycle2 prior) | 100.958 | 4.430 | **105.388** |

**L6 predicted better and lost.** Its payload is 1.785 MB smaller than C2's, and its weight bundle
erased that and more. C2 saved 4.97 MB of payload for 4.38 MB of decoder cost — a net 0.59 MB, or
0.56%, over having no prior at all.

Then the part that bites hardest here. On `enwik8` (100 MB) **not one prior paid for itself**: the
best dense quantized-LoRA estimate was 20.88 MB and the best compact priors 17.58 and 18.96 MB,
against a 15.152 MB online baseline. The same priors won on `enwik9` only because a billion bytes
gives a fixed-size prior **ten times as much text over which to recover its cost**.

A prior is not good or bad. **It is good or bad per use.** We hold a 326 MB keeping, a ~1.9 GB
resident floor (`keeping-2`) and 95 verifier modules — a large fixed prior — and we cannot currently
state the rate it is used at, because `nh-traffic.timer` is disabled and `data/traffic.json` is stale
(`own-2`). The analogy is not a measurement: he pays in archive bytes, we pay in build time, memory
floor and attention, and those do not convert. What transfers is the *form* of the question, which
this project has never once asked in a number: **for each shelf and each verifier, does it save more
than it costs, at the rate it is actually used?**

## 4. Three measured findings, as warnings for this project

Each of these is his result on his task. None of them is a result about us. All three are directly
against instincts recorded in this repo.

1. **More parameters did not help.** With a fixed 16K vocabulary, 267M gave *larger* payloads than
   188M at both replay windows. On `enwik8` with 4K and a 15M window, gains ran from 14M to 77M, then
   little at 163M and **worse at 336M**. He hypothesizes an optimal model size per fixed document.
   The same shape as our own finding that depth adds no capacity.
2. **Smaller vocabulary won, and domain-specific tokens made it worse.** 4K beat both 8K and 16K, and
   **dedicated XML/wiki tokens made compression worse despite the abundance of markup in the input.**
   That is an independent hit on the instinct to add a specialized shelf or a synonym list because a
   domain "obviously" needs one — the markup was everywhere and the dedicated tokens still lost.
3. **A better predictor can still lose.** §3. Any change must be scored with its cost attached, not
   on the metric it improves.

The discussion section states our own method discipline in his words: hill-climbing one objective
"can improve a score without explaining why a change worked or where it will work again." He reaches
it through Goodhart's law and Tao's Math 2.0; we reached it through a week of ranker measurements
where the metric could not tell the hypothesis from something else and confirmed it anyway. Two
routes, one rule — and ours is the reason [HARNESS.md](HARNESS.md) forbids the builder from grading
its own step.

## 5. Our own keeping, measured by the same accounting

`python tools/keeping_bits.py .` — 69 of 70 registered sources (`sword_dict_cards.jsonl` is absent
from disk), 933,210 cards, 326.3 MB of title+body:

    kind                  cards   %cards         bytes   %bytes  b/card
    reference            903738   96.84%     315378155   96.64%     348
    connection            19906    2.13%       3041374    0.93%     152
    note                   5539    0.59%       5218915    1.60%     942
    receipt                2314    0.25%       2166849    0.66%     936
    principle               847    0.09%        236479    0.07%     279
    verified                510    0.05%        164459    0.05%     322
    bridge                  180    0.02%         76850    0.02%     426
    strategy_case            82    0.01%         22796    0.01%     278
    strategy_counter         41    0.00%         17861    0.01%     435
    strategy_pattern         20    0.00%          4878    0.00%     243
    source                   17    0.00%          6337    0.00%     372
    practical                13    0.00%          7152    0.00%     550
    walk                      3    0.00%           510    0.00%     170

**96.84% of the cards, and 96.64% of the bytes, are `kind=reference`. 510 cards carry a verdict.**
The two denominators agree, which matters: the bulk is not an artifact of counting thin cards.

Then the compression diagnostic — each card compressed alone, versus the kind compressed as one
stream. The ratio is how much of a kind is the same card repeated:

    kind               sample    raw bytes      alone   together    ratio  verdict
    reference            4000      1667760    1083745     367300   2.95x  patterned (1.762 bits/byte)
    connection           4000       407063     326975      52424   6.24x  heavily patterned (1.030)
    note                 4000      3854818    2065599    1500546   1.38x  mostly distinct (3.114)
    receipt              2314      2166849    1141159     237064   4.81x  heavily patterned (0.875)
    principle             847       236479     118932      60531   1.96x  mostly distinct (2.048)
    verified              510       164459     128675      45135   2.85x  patterned (2.196)
    bridge                180        76850      45877      22383   2.05x  patterned (2.330)

What it says:

- **`connection` at 6.24x and `receipt` at 4.81x are near-template** — which is correct and not a
  defect. They are machine-minted plumbing; 19,906 connection cards carry roughly 3,200 cards' worth
  of distinct text. It is independent support for `keeping-3`: the graph is filing, and filing
  compresses.
- **`note` is the densest thing in the keeping** at 3.114 bits/byte and 1.38x — 5,539 cards that are
  almost entirely distinct content, 942 bytes each.
- **My prediction was wrong, and this is the finding.** I expected the reference bulk to nearly
  vanish under compression if it were template. It came in at **2.95x** — real redundancy, but not
  annihilation. Reference cards are thin and repetitive **and they do carry distinct content.** The
  honest statement is not "the bulk is empty"; it is that the engine is 96.8% dictionary-shaped on
  both denominators while 510 cards carry a verdict.

## 6. What this does not establish

- **1.762 bits/byte is not comparable to 0.843.** Ours is zlib — a weak compressor — on card text;
  his is a 163M Transformer on Wikipedia. Different compressor, different data. The figures here are
  comparable **only to each other**, which is the entire point of holding one compressor fixed across
  kinds. Any cross-reading of the two numbers is an error.
- **This does not reconcile with `keeping-1`'s ~67%, and it should not.** That item measures
  *stocking* — whether a card's body answers — while this is a census of `kind`. A `reference` card
  with a real body is still an answer. Two different questions; both numbers stand.
- **We cannot adopt the method.** Mahoney's thesis licenses a learned generative predictor, and this
  engine refuses generation at runtime — [COHERENT_MODEL.md](COHERENT_MODEL.md), "meaning without an
  LLM". What we take is the accounting, not the predictor. Worth
  recording in his favour: he notes that putting knowledge into hardcoded code — cmix v21 mixes 2,077
  predictors — is, from the compression view, a legitimate way to represent it. Our verifiers are
  exactly that kind of representation.
- **The sample is the first 4,000 cards of a kind, not a random draw**, so a kind whose later files
  differ in character could move. `receipt`, `verified` and the strategy kinds are measured whole.
- **Not measured at box shape.** Local checkout only.

## 7. What to do with it

1. **Give the keeping one honest number that includes the cost of the prior.** Per shelf: bytes held,
   resident cost, and times answered. A shelf that has never answered is a prior that has not paid.
   `tools/keeping_bits.py` is only the first half — the cost side. The usage side is blocked on
   `own-2` (the traffic timer is off), which makes that item larger than it looks: without it,
   no shelf and no verifier in this engine can be priced at all.
2. **Score the next ranker change with its cost attached.** §3 is the rule in one line: a change that
   predicts better and costs more is a worse system. Write the cost column into the residual report.
3. **Stop adding specialized vocabulary on the assumption it must help.** §4.2 is an outside,
   measured hit on that instinct. Where we do add one, measure against not having it.
4. **Mint the `note` kind deliberately.** It is the only kind in the keeping that is mostly distinct
   content at scale, and there are 5,539 of them against 903,738 reference cards. Whatever process
   produces notes is the process that produces answers.

## 8. .kkrieger, and why a generator is not our size argument

**2026-11-23.** Matt: *"Kkreiger game design."* `.kkrieger` (.theprodukkt, a Farbrausch spin-off,
2004) is a complete first-person shooter in **97,280 bytes** — a Guinness record for fewest bytes for
an FPS. It stores no textures and no meshes, only *their creation history*: a generator graph authored
in `.werkkzeug`, packed with Fabian Giesen's `kkrunchy` (released 2014, BSD/public domain), expanded
into memory at startup. The notorious load time **is** the decompression.

That is §1–§3's accounting in a shipped artifact, so it is worth asking the question directly: of the
bytes this keeping holds, how many are the cited fact and how many are its expansion?
`tools/creation_history.py` answers it.

### The measurement, and it refutes the obvious move

Sampled 120,000 cards / 115.9 MB of `data/source_cards.jsonl`. Every byte is attributed to exactly
one bucket per class, and a **floor of 500 cards per class** applies — below it, "this key is
constant" cannot be told from "there is only one example," which is the artifact that made a first
pass report 84.3%.

| class | cards | bytes | constant keys | varying |
|---|---|---|---|---|
| `card_src_food` | 7,793 | 8,852,001 | 40.8% | 54.0% |
| `card_src_port_tcp` | 5,914 | 5,185,019 | 55.5% | 37.4% |
| `card_src_port_udp` | 5,524 | 4,838,630 | 55.6% | 37.3% |
| `card_src_star` | 1,722 | 1,589,160 | 50.5% | 42.8% |
| **classes ≥ floor** | **20,953** | **20,464,810** | **48.8%** | **45.0%** |

Roughly half of a reference card is a key whose value is byte-identical across its whole class —
`kind`, `box`, `author`, `visibility`, `lifecycle_stage`, `volatility`, `surface`, `generated`,
`created_at`, `updated_at`, plus a `source` block and a `connections` block repeated verbatim per
card (989,711 B and 919,574 B respectively, in `card_src_food` alone).

**And removing all of it loses to `gzip`:**

    remove every constant key (schema-aware, nothing inferred) .... 1.95x
    gzip -9, same bytes, knows nothing about cards ................ 14.96x   (38,949,908 -> 2,602,870)

**gzip wins by 7.7x.** So *procedural generation is not a size argument for this keeping.* A
general-purpose compressor already removes more than schema knowledge does, because it also eats the
repeated **prose** that a constant-key analysis has to leave in `varying`. If the goal is bytes, the
answer is to compress the files, not to build a generator.

Two further reasons the .kkrieger trade does not transfer:

1. **We have no uniformity to exploit.** Only four classes in 120,000 cards reach 500 members, and
   together they are just **17.7%** of the sampled bytes. The reference bulk is not a few vast
   uniform tables; it is very many small ones. Procedural compression pays off on uniformity.
2. **Our generator can never be self-contained, by doctrine.** `.kkrieger`'s 97,280 bytes need
   nothing external, because a procedural rock has no ground truth — *the generator IS the truth.*
   Our 82 `seed_*.py` files are **864,613 bytes** against ~326 MB of cards, but that is a
   code-to-data ratio, **not** a compression ratio: the seeds read USDA, GeoNames, IANA, NNDC,
   Gutenberg. A seed that could produce a place card without GeoNames would be **inventing places**.
   Quoting 377x here would be a category error.

### What does transfer: the generator is the authored artifact

The lesson is architectural, not spatial. For `.kkrieger` the werkkzeug graph is the source of truth
and every texture is derived and disposable. The same is already true here — seeds are tracked, cards
are built from them — but it has never been **priced**. If the 326 MB is a rebuildable cache, then
what must be reviewed, backed up and trusted is the seed plus the cited source, and the card store is
a build output. That reframes `own-2` and the shelf-cost work in §7: the cost side of a shelf is not
only its resident bytes but its **rebuild** cost, which this document has not measured and which
running the seeds casually would be the wrong way to find out.

### One finding with a product consequence: the prose is a rendering, and nothing says so

**`generated` is false on 40,000 of 40,000 sampled cards** — not one carries `true`. The flag means
what `airlock.py:26` says it means: the facts are not authored here. But the `body` **is** machine
rendered from the fields by a template, and nothing on the card marks it as ours rather than the
source's. The evidence:

- **57.8%** of body tokens already appear in the same record's other fields.
- The templates show through: *"Port 1/tcp is assigned to tcpmux: TCP Port Service Multiplexer."*,
  a nuclide reading *"1 protons"*, and a star whose name joined badly into **"Tau Phe Phe"**.

So a card's `body` is our sentence about a cited row, carrying no marker distinguishing it from a
quotation of that row. An agent reading `body` can reasonably take it as source text. That is a
narrower and more fixable thing than it sounds — it is a provenance label on the prose, not a change
to any fact — and it sits squarely under the covenant's *distinguish citation from proof* and
*carry provenance through every transformation*.

### What this does not establish

- **No RAM or load-time figure for `.kkrieger` is quoted here.** The widely repeated numbers trace to
  forum posts; the one "512 MB minimum" is a quoted beta spec, not a developer measurement. The
  decode cost is qualitatively certain (generation at startup) and **not** quantified in any source
  I could stand behind.
- **The sample is 120,000 cards of one file**, not the keeping. `source_cards.jsonl` is 406 MB of a
  1,418.8 MB jsonl total, and that total is far above the 326.3 MB across the 70 *registered*
  sources — unregistered files remain a known hazard.
- **Our own rebuild cost is unmeasured**, as said above.
- **Nothing was changed.** No card, no stick, no seal. `tools/creation_history.py` only reads.

## 9. Lekktor, a tool per slot, and the law that has to be there first

**2026-11-23.** Matt: *"Lekktor … It's a video game design. We can learn from game design. You need a
tool for each task to render what fits in that slot. You need a language that communicates what goes
where."* With `Code_Score.py` attached — which already **is** that design.

### The design, and its own proof

`Code_Score.py` holds three renderers and a three-byte language that says which one owns a slot:
`GR1` a grid generator, `SC1` an arithmetic-motif encoder, `ZL1` plain zlib. `restore(frame)`
dispatches on the tag; `min(choices, key=len)` runs a competition and the winner takes the slot. Its
demo, run here:

    zlib -9 on a 39,930-byte triangle list ......... 8,410 bytes
    score + zlib .................................... 422 bytes
    the grid generator (GR1) .......................... 5 bytes

**1,682x between the general compressor and the right tool.** And `grid_recipe` shows the other half
of the idea: regenerate the canonical mesh, then store only the rows that deviate — one changed
triangle costs 23 bytes, not a new file. Generate the reference; keep the margin.

§8 compared gzip against *constant-key removal* and concluded a generator was not a size argument
here. That comparison was wrong — constant-key removal is one trick, not a renderer. So the
competition was run properly.

### The competition, on real card classes

`tools/slot_dispatch.py`, 120,000 cards of `source_cards.jsonl`. Every card is canonicalised to
compact sorted-key JSON first, so gzip and the columnar renderer are judged on identical bytes, and
**every renderer must rebuild its slot exactly or it is disqualified rather than scored.**

| class | cards | canonical | ZL1 | CL1 columnar | SC1 motif | winner |
|---|---|---|---|---|---|---|
| `card_src_food` | 7,793 | 8,392,214 | **535,354** | 691,920 | 691,920 | ZL1 |
| `card_src_port_tcp` | 5,914 | 4,824,265 | **341,838** | 365,488 | 355,351 | ZL1 |
| `card_src_port_udp` | 5,524 | 4,501,666 | **316,469** | 341,754 | 332,623 | ZL1 |
| `card_src_star` | 1,722 | 1,484,118 | 93,723 | **80,878** | 80,878 | CL1 |

    one global gzip ................. 1,287,384
    per-slot winner + tag ........... 1,274,539   = 1.01x better

**Per-slot dispatch buys 1%.** The columnar renderer wins exactly one class. And the motif encoder,
run directly on 2.8 MB of raw card bytes, finds **zero** motifs — not one arithmetic progression of
length three, with a clean round trip. It beat the columnar form only on the two *port* classes, the
only ones holding a near-dense integer sequence.

### Why: a generator exists only where there is a law

This does not refute the design. It locates where it pays. `GR1` reaches 5 bytes because a 32×32
triangle mesh **is fully determined by one integer**. Nothing in these card classes is determined by
anything: *"Port 5/tcp is assigned to rje"* is a decision someone made at IANA, and a star's
magnitude is a measurement. **The content is contingent, so there is no generator, because there is
no law** — and that is precisely why it must be stored and cited rather than produced. gzip wins
because gzip is the right renderer for contingent text.

Which means the registry already exists in this engine, and the language that says what goes where is
`kind`:

- **cards** carry contingent facts → store, cite, compress. The slot's renderer is an entropy coder.
- **sticks** carry lawful facts → store the **expression** and regenerate the value. A stick's
  `expr` + `value` *is* `GR1`: `schumann_ideal` keeps `299792458*sqrt(2)/(2*pi*6371000)` and the
  number falls out of it. That is a generator with a citation attached.

So the useful question Matt's design raises is not "compress the cards better" but **"which card
content is actually lawful, and therefore belongs in a stick?"** One hint, weak but present: the
single class where the structure-aware renderer won is `card_src_star`, the class with the most
internal mathematical relation among its fields.

### Lekktor is the tool we need most and cannot run

Lekktor is the third tool in that chain and the only **subtractive** one: per the GitHub blog on
`fr_public`, a tool for profiling, finding and removing dead-code sections, by Giesen and Ohlerich.
Its internals are not documented in any source reached here, and none is invented.

Its requirement is the whole point: **you must run the thing and watch what executes.** This repo has
a long list of findings that are precisely Lekktor's input — nine dead shelves, 96.8% of cards
`reference` against 3.82% that help a family, boost arms that fix 0 of 15, a 9.0x exact-title boost
that fired once in 76,010 candidates, twenty always-deny kernel gates that changed nothing, five test
files that never ran under a green gate.

Every one of those was found by hand. **The instrument that would find them automatically is off:**
the traffic timer (`own-2`). §7 named it as blocking shelf pricing; it also blocks the entire
subtractive half of this toolchain. That raises `own-2` from an accounting gap to the prerequisite
for the only tool here that makes things smaller by removing what reality never asked for.

### What this does not establish

- **1.01x is a result about four classes**, 17.7% of the sampled bytes, in one file.
- **No generator was written for any card class.** The claim that none exists is an argument from
  contingency plus a measured absence of motifs — not a proof that no renderer could do better.
- **Lekktor's mechanism is uncited** beyond "profiling, finding and removing dead code".
- **Nothing was changed.** `tools/slot_dispatch.py` and `Code_Score.py` (the owner's file, kept outside this repo) only read; no card,
  stick or seal was touched.

## 10. How .kkrieger handles text and shapes — read from its source

**2026-11-23.** Matt: *"Look at KKreigers handling of text and shapes."* Read directly from
`farbrausch/fr_public/werkkzeug3_kkrieger` (BSD), not from summaries — none of the searches reached a
write-up, and the code answers it exactly.

### Text: name the font, render at load, cache only where it is checked

`Bitmap_Text` (`genbitmap.cpp:1952`) is one of 31 texture operators. Its parameters include
`sChar *text, sChar *font` — **the font is a name, not data.** It calls `sSystem->FontBegin`, which
(`_start.cpp:5653`) asks Windows GDI for it: `CreateFont`, then `GetCharABCWidths` for each glyph's
metrics, then `ExtTextOut` to draw. **Not one glyph is stored in the 96 KB.** Four mechanics:

1. **Render big, then reduce.** `const sInt alias = 4;` sits beside a commented-out `alias = 2`. The
   string is drawn at 4x in each axis and each output pixel is the mean of a 4x4 block (`>>4`).
2. **An atlas, built once.** In "page" mode the operator renders all 256 characters into one texture
   and records each letter's position and ABC widths in `kenv->Letters[page]`, so any later string
   is drawn from the atlas by metrics.
3. **The editor caches; the release regenerates.** The cached path is compiled only under
   `#if !sINTRO`. It stores coverage at **3 bits per pixel** (`*data++ = fade>>5`, expanded back by
   bit replication on read).
4. **The cache checks itself before it is trusted.** The blob carries a format tag (`data[0] = 3`),
   the page flag and the bitmap's dimensions, and it is used **only if all of them still match** —
   otherwise it is ignored and re-rendered.

### Shapes: primitives, operators, and one register that says what goes where

`genmesh.cpp` defines 48 operators: primitives (`Cube`, `Cylinder`, `Sphere`, `Torus`, `Grid`,
`SingleVert`), modifiers (`Extrude`, `Bevel`, `Subdivide`, `Bend`, `Displace`, `Perlin`,
`Multiply`), and a **selection family** — `SelectCube`, `SelectSphere`, `SelectAngle`,
`SelectRandom`, `SelectGrow`, `SelectFace`, `SelectAll`, `SelectLogic`.

**The selection is a 32-bit mask on every face.** Selectors *write* a bit (`dmask`, `dmode`);
operators *read* one and act only there — `Mesh_Subdivide(…, sInt mask, …)`,
`Mesh_Bevel(…, sInt mask, …)` — and `Mesh_Extrude(…, sInt smask, sInt dmask, …)` reads a source
mask and writes what it creates into a destination mask for the next operator. `SelectLogic` combines
two masks into a third. **One register, 32 slots, written once by an explicit operator and read by
explicit operators** — so two spellings of the same selection can never disagree.

Two more structural facts:

- **Two languages joined by one converter.** The editor's `genmesh` (48 operators) is converted by
  `Mesh_ToMin` into the runtime's `genminmesh` (34 operators, adding bones, animation baking and
  `Compress`). A rich language to author in, a minimal one to ship, one conversion between them.
- **`meshcoder_unused.cpp`.** A complete mesh compressor — 8-bit coordinate quantization, a
  connectivity traversal, halfedge reconstruction — kept in the tree with `_unused` in its name. **No
  comment records why.** The plausible reason, that a build which stores no meshes has nothing to
  code, is inference and is labelled as such.

### What transfers here

**1. Render at use, and provenance becomes automatic.** §8 found that a card's `body` is prose
rendered from the record's own fields, stored with nothing marking it as ours rather than the
source's. `Bitmap_Text` never ships its output: it keeps the inputs and renders at load. If a body
were rendered at answer time from the fields, **the renderer could stamp its own output** — this
sentence, from that row, by that template — where a stored string cannot know it was ever rendered.
That closes the §8 gap structurally rather than by labelling 903,738 cards.

**2. One register, not six spellings.** Measured on 60,000 cards of `source_cards.jsonl`:

    shelf <-> source.domain <-> call.head     each fixes the other two on every card: ONE dimension
    kind, box, surface                         constant on all 60,000: zero information here
    bands == facets.subject                    identical sets on 47.7% of cards
    subject already inside bands               63.0%

Six addressing fields carry **one** varying dimension, spelled three ways. Werkkzeug is the inverse —
one field holding 32. **Ours agree today on all 60,000 cards; the risk is structural, not current:**
nothing stops a seed writing one spelling and not the others, and retrieval keyed on one would then
disagree silently with display keyed on another.

**3. A cache that validates its key before use.** The text blob refuses itself if its format,
page or size no longer match. Our record holds the opposite case — a warm `_search_cache` that let
one question borrow the previous question's hits.

**4. We already made the editor/runtime cut.** `genmesh` → `Mesh_ToMin` → `genminmesh` is the same
shape as the keeping engine and the lean `Concordance-V3` verifier core, with `test_boundary.py`
pinning the line between them.

### What does not transfer

**"Name it, don't ship it" is refused as a content policy.** .kkrieger can name Arial because it
targets Windows and has nothing to protect. This engine serves families offline with no account; the
keeping has to carry what it cites, or a family off the network gets a name instead of a fact. The
idea survives in one place already: a stick names a computation in its `expr` and lets the evaluator
supply it — which is exactly right for a law and exactly wrong for a contingent fact (§9).

### What this does not establish

- **The 60,000-card measurement covers one file**, and there only six shelf values appear.
- **No render-at-use path was built or measured** — its cost at answer time is unknown.
- **Nothing was changed.** The source was read through the GitHub API into the terminal, not saved.
