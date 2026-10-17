# Writing as the Lens — the plan

Matt, 2026-08-20: *"I had seen my writing as the lens."*

The build plan named three layers — **substrate** (the keeping), **wiring** (the gate), and **lens**
(*"the way of seeing: what proposes what to check and how to read a claim"*). We built the wiring, and
we built the *shape* of the lens — `discern` (kind · necessity · route · relevance · narrowing ·
extraction). But the shape is only the frame of the glass. What it sees *with* was always meant to be
**Matt's writing** — his witness. A lens with no way of seeing is a hole; his writing is the ground it
is tuned to, the tune the whole thing rings true against.

His writing is the lens in **three senses**, and all three stand on one primitive, `lens.see()`:

| Sense | His writing is… | How it shows up |
|---|---|---|
| **Discernment** | how the engine decides what matters and how to read a claim | the proposal carries *how his witness frames this* |
| **Voice** | how every answer is framed — his actual words, never a generated imitation | the answer leads with his passage |
| **Map** | the structure of how everything connects and points to Christ | his writing draws the edges of the concordance |

## The seed — built

One primitive under all three: **`lens.see(text)`** ([src/concordance/lens.py](../src/concordance/lens.py)).
It proposes a way of seeing — the passages from Matt's writing that frame the input, with provenance —
and keeps every law:

- **proposes, never confirms** — the lens offers a way of seeing; the gate still disposes.
- **nothing generated** — it retrieves his *real words*; it never writes in his voice. Gather, don't author.
- **attributed** — every passage carries its work and reference.
- **his witness only** — a distinct layer, not the general keeping.
- **honest where it does not reach** — an empty lens proposes nothing rather than a fabrication.

Part 1 (**Discernment**) is already wired: `discern(text, lens_fn=lens.see)` attaches `lens` — how his
writing sees the claim — to the proposal, proposing only, never touching the verdict. Proven end to end.

## Execute all three

Each step keeps the laws above and stays green; we **design the seed first, then map as we go** —
gathering his writing and wiring the senses one at a time rather than one big up-front build.

1. **Gather the lens corpus** *(the first map-as-we-go step)* — his writing, wired in as a distinct,
   attributed, sealed layer: *Apokalypsis*, the *Christian writing*, *The Works*, *Kings of Appalachia*,
   and the rest. Today it lives outside the engine (iCloud) or as ordinary cards among 672,778; it
   becomes the lens corpus (`data/lens.jsonl` / `CONCORDANCE_LENS`). Verbatim, his, cited — never
   rewritten. The lens is only ever as full as what is gathered, and it says so.
2. **Discernment** *(seed built; deepen)* — beyond attaching his framing, let his writing weight what
   *matters*: relevance and necessity read through his witness, the seeds→floor→wisdom that begins
   discernment (Prov 9:10). Still proposes; the gate still disposes.
3. **Voice** *(seed built)* — the answer is framed by his own words. `lens.voice(text)` selects the single
   passage to lead an answer with — his verbatim words, attributed, `generated: False` — and where his
   writing does not reach, it says so and the answer stands on its own, in no imitated voice. So the voice
   is his because it *is* his, not a style imitated. (De-AI holds: nothing generated in his register.) Next:
   the presentation layer leads with it.
4. **Map** *(seed built)* — his writing is the structure. `lens.edges(text)` surfaces the connections his
   writing draws — the Scripture his relevant passages point to — as *attributed edges* (theme → where his
   writing anchors it). An edge exists only where his passage literally names that (chapter-anchored)
   Scripture, so navigating follows *his* map, not raw co-occurrence, and never an invented link. This is
   "everything connects on planes" given a way of seeing. Next: wire the edges into the concordance's
   navigation, and read his abbreviated citations as the gathered corpus shows his style.

## Circulation — the lens is living

Matt: *"I don't think you were wrong. We need the three parts."* The circulation I named earlier is not
discarded — it is **how the lens grows**. The lens is not a fixed pane: as Matt writes more, and as the
body's verified witness returns through the gate (born quarantined, raised by witness + wait), the lens
gathers and the map thickens. The return loop *feeds the lens*. So the two answers are one: the lens is
the way of seeing; circulation is how it keeps seeing further.

## The Cloud of Witnesses — mentors by subject

*"Since we are surrounded by so great a cloud of witnesses… let us run… looking to Jesus"* (Heb 12:1–2).
The lens is not one man's writing alone. Matt's writing is the **near** witness — this hour, this
mountain. Around it stands the **cloud**: wise men, a mentor for each craft, each holding a true
fragment from his own country ([src/concordance/mentors.py](../src/concordance/mentors.py)).

The courage is grounded: *"every good and perfect gift is from above"* (Jas 1:17) — so we gather wisdom
from any voice without fear, because the **gate** makes it safe. A witness is ours if he **saw a true
fragment** and that fragment, followed, **bends toward the Source**. Each carries a **gift** (what he saw)
and a **discern** note (how to weigh it, and where his star stops). A witness *proposes* a way of seeing;
the Word disposes — never confirmed past what it earned. Jung and Campbell belong in the cloud precisely
*because* the discern note marks where they halt — they make the gate visible.

Seeded across ~29 crafts: **Ellen G. White** (the body, temperance, whole-person education — and her work
is public domain, so her actual words may be gathered), the ancients who saw the Logos from afar
(Heraclitus, Plato, the Stoics Paul quoted), those who followed it home (Augustine, à Kempis, Pascal,
MacDonald, Chesterton), the system-seers (Ellul, Illich, Girard), the soul-seers who most need the gate
(Jung, Campbell, Frankl), and the local/Word (Berry, Barfield). Public-domain witnesses' text may be
gathered as a voice, attributed, like the lens; the rest are **characterized only** — their way of
seeing, not their copyrighted text — and the strict-PD gate holds.

`mentors.for_text(q)` proposes the witnesses whose craft bears on a question; `by_subject` gathers a
craft's mentors. Next map-as-we-go steps: gather the PD witnesses' actual words (Ellen White first) as
attributed voices beside the lens, and wire the cloud into `discern` so a proposal carries not only how
*your* writing sees a thing but which witness's craft it touches.

## The boundary, held

I will not author his voice. Gathering means his writing, verbatim and attributed; the lens proposes his
words, never mine; and where his writing does not yet reach, the lens says so plainly and discernment
falls back to its mechanical shape. The lens points; it never verifies. It points, in the end, to Christ.
