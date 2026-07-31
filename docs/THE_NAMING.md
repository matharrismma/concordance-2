# THE NAMING — the job defines the name, and the name is a traditional noun

Matt, 2026-07-31: *"Look at all of the pages and tools. We let the job define the name. Use
traditional nouns to describe them."*

A traditional noun is a name a library, a workshop, or a parish would already recognise — catalogue,
almanac, atlas, journal, steward, rule. It earns its keep twice: a reader knows what a thing is
before opening it, and **two pages cannot quietly do the same job under different invented names**,
which is exactly what this survey found.

Surveyed all 45 pages by TITLE and HEADLINE — what each says its job is.

---

## I · FOUR COLLISIONS, found by naming rather than by counting

### 1. Two pages, one job — and almost the same sentence
| page | headline |
|---|---|
| `guarantees.html` | "What we prove — and what we **don't**." |
| `proof.html` | "What we prove — and what we **won't**" |

Two files, one job, differing by a contraction. Neither knows about the other. **One survives.**

### 2. Three front doors to one act
| page | headline |
|---|---|
| `check.html` | "Check anything with numbers in it." |
| `audit.html` | "Paste anything. Get a receipt." |
| `reason.html` | "Verify an argument. Or a function." |

All three are *give the engine something and get a verdict*. Three doors into one room, and a person
arriving has to guess which. **One survives; the differences become inputs, not addresses.**

### 3. A name collision that will cost someone real time
| page | title | job |
|---|---|---|
| `keep.html` | **The Keep** | the OPERATOR console — token-gated, not public |
| `library.html` | **The Keeping** | the public card browser |

One letter apart; opposite audiences. A misdirected link here sends a reader at an operator console
or an operator at a card list. **Rename one.**

### 4. A page wearing another page's name
`mesh.html` is titled **"The Gate"**, but the Gate is the Ask/Seek/Knock threshold in `ask.html`.
Mesh's actual job is *find the fellowship near you*. The title belongs to a different concept.

### Also doing overlapping work
`catalog.html` (Card Catalog) vs `library.html` (browse the keeping) · `days.html` (Your days) vs
`journal.html` (Your journal) · `places.html` (Atlas — biblical places) vs `map.html` (the card
graph): two different maps, and only one may be called Atlas.

---

## II · THE JOBS, AND THEIR TRADITIONAL NOUNS

Where a name is already right, it is left alone — most of them are.

| job, in plain words | traditional noun | today |
|---|---|---|
| browse the whole collection; the compiled body | **the Corpus** | `library` + `catalog` + `codex` + `works` |
| a reference question answered from the collection | **the Reference Desk** | `ask` |
| give it a claim, get a verdict and a receipt | **the Proof House** *(where a thing is proved before it is trusted)* | `check` + `audit` + `reason` |
| what we will and will not claim | **the Warrant** *(what our word is good for)* | `guarantees` + `proof` |
| word-by-word reference on names and terms | **the Dictionary** ✓ | `characters` |
| facts worked and re-checkable | **the Almanac** ✓ | `almanac` |
| the places of Scripture | **the Atlas** ✓ | `places` |
| your own dated record | **the Journal** ✓ | `journal` + `days` |
| your household money, never moved | **the Steward** ✓ | `steward` |
| name what you reach for; receive a practice | **the Rule** *(a rule of life — the oldest name for exactly this)* | `walk` |
| how the world reached toward Christ | **the Signposts** ✓ | `prophecy` |
| your own shelf in a library of shelves | **the Shelf** ✓ | `shelf` |
| read the Scripture | **the Word** ✓ | `bible` |
| learn to read | **the Primer** *(the traditional name for a first reader)* | `read` |
| find the fellowship near you | **the Fellowship** | `mesh` (mis-titled "The Gate") |
| study together | **the Study** | `community` |
| the operator's own console | **the Keep** ✓ — and only this one | `keep` |

---

## III · WHAT THIS DOES TO THE COUNT

Naming does the cutting that counting could not justify:

- `guarantees` + `proof` → **the Warrant** — −1
- `check` + `audit` + `reason` → **the Proof House** — −2
- `library` + `catalog` + `codex` + `works` → **the Corpus** — −3
- `journal` + `days` → **the Journal** — −1

**−7 pages from four merges**, each one a *duplicate job* rather than a judgement about traffic.
That is the difference between consolidating and pruning: nothing of value is lost, because in every
case two files were already doing one job.

---

## IV · THE CORPUS — first, since it was already asked for

`library` + `catalog` + `codex` + `works` → **the Corpus**: the whole body, browsable.

Its parts, each a section rather than a page:
- **the shelves** — browse and search the keeping (`library`'s job, `/cards/stats`)
- **the manuscript** — the compiled, cross-indexed body with its authority spine (`/codex`, 4 spine
  levels · 6 scripture · 5 themes)
- **the worked volume** — 66 sealed demonstrations, each re-checkable (`/works`)

Evidence it was always one thing: `codex.html` already contains
`if (ref) location.replace('/library.html?q=' + ref)` — it forwards into the library on any
reference. The system has been saying so for a while.

**Method:** build `corpus.html`; 301 `library` · `catalog` · `codex` · `works` onto it so no link or
citation dies; archive the four to the ark with hashes; then remove. Net **−3 pages**.

---

## V · TOOLS ARE A SEPARATE SURFACE, AND NAMED BY THE SAME RULE

79 MCP tools; 40 sit in 13 families. The same rule applies — *the job names the tool* — with one
constraint pages do not have: **a tool's description is the documentation an agent reads**, and
agents are 35% of our traffic. So a family collapses only when its members **share a subject and
differ by verb** (`coach_next`, `coach_overview` → `coach(action=…)`), never across subjects to make
a number look tidier.

Named separately, and after the pages, because a tool surface rewards precision where a page surface
rewards familiarity.

---

*Nothing here is done because it is written here. Each merge is gated, deployed, verified live, and
committed on its own, and every retired page is archived before it is removed.*
