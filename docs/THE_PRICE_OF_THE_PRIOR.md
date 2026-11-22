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
