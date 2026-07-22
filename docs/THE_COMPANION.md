# The Companion — the Concordance for a life

> "It routes everything in the background. Brings you what you need when you need it."
>
> "It is the Good Samaritan that may not be who you wish was there, but it is always there."

The engine already indexes and concords the Word and the world. The Companion turns that
same instrument on **one life**: it takes in everything you bring, files it without asking
you to file it, and returns the right thing at the right moment.

It does not claim to be the friend you wish had answered. It claims to be **present** —
the one who stopped on the road. That humility is the whole design: it is always there,
and it always points past itself.

*Verified live 2026-07-22 — the state table in §5 is measured, not aspirational.*

> **The build order of §8 is complete.** Six members were added — Router, key→thread binding,
> the never-resetting index, the Book of Days, fork + deferral, and the inlet — **87 tests**,
> every one gated, deployed and verified against production. **Not one added a model, a
> provider, or a dependency.** Each time, the honest design turned out smaller than the
> assumed one: build nothing rather than a local-model adapter; an index rather than a
> summary; derived pointers rather than inferences.

---

## 1. The vow

The five laws of [COMPANION.md](../../Lighthouse/docs/COMPANION.md) carry over unchanged:
the engine **verifies**, the assistant only **drafts**; conduit, not source; curate, not
filter; point to Christ, never be an idol; **decrease** (success is needing it less).

Three more are specific to a companion that lives alongside you:

6. **The Samaritan clause — always there, never pretending to be more.** It does not
   simulate intimacy it doesn't have, or manufacture warmth to keep you. It is steady,
   available, and honest about being a tool. When what you need is a person, it says so
   and helps you reach one.
7. **It never resets, and you own the memory.** The record is yours: inspectable,
   exportable, deletable, line by line. Nothing about you is inferred in a place you
   cannot see.
8. **It carries no third party.** No tracker, no ad model, no analytics on the
   conversation. The trust boundary ends at your device and our box (§6).

## 2. What it feels like

One thread. You open it on your phone at 6am and on your laptop at noon and it is the
**same conversation**, mid-sentence. You never re-explain yourself. You never "start a
new chat" because the old one got long.

You throw things at it — a photo of a receipt, a verse that stopped you, a half-thought
about your daughter's reading, a bill, a question about a torque spec. You do not file
any of it. Weeks later it hands you back the receipt at tax time, the verse on the day
you need it, the reading lesson pitched at where she is *now*.

That returning is the point. **Routing is the Concordance working** — the same
index-and-concord that maps reality, applied to your days.

## 3. The body — many members, not one generalist

> "The body is not one member, but many." — 1 Cor 12:14

**This is not a big model wearing six hats.** It is a body: many small specialists, each
excellent at one narrow thing; **one who knows whom to call and when**; and **one who
records**. That is the whole architecture, and it is why it stays light.

### 3.1 The one who knows whom to call — the Router
Small, fast, cheap. Its **only** job is discernment: read what you brought, decide which
member handles it, hand off. **It never answers.** A router that starts answering has
become the generalist we are avoiding.

Routing is *classification*, not reasoning — and `ask.py` already proves it can be done
**deterministically**: its routing is rule-based today, with no model at all. `check` and
`find_verifier` do the same for claims. **The Router generalises that across all members and
stays rule-based**, so the body keeps its zero-dependency property (§3.2a). Genuine ambiguity
is resolved by *asking you*, not by guessing with a model — which is also the more honest answer.

### 3.2 The members — specialists, and most need no model at all
The decisive economy: **the majority of work is deterministic.** These cost zero tokens.

| Member | Kind | What it is today |
|---|---|---|
| **The 71 verifiers** (math, physics, chemistry, medicine, finance, law…) | deterministic | `verifiers/` — already built, already exact |
| **Scripture / lexicon / cross-refs** | deterministic | `canon.py`, `strongs/`, `xrefs.py`, `commentary.py` |
| **Concordance & map** | deterministic | `corpus.py`, `graph.py`, `codex.py`, `grid_atlas.py` |
| **Almanac, characters, places, prophecy** | deterministic | `almanac.py`, `characters.py`, `prophecy.py` |
| **Steward** (never moves money) | deterministic | `steward.py`, `ledger.py` |
| **Coach** | mostly deterministic | `coach.py`, `badges.py`, curriculum |
| **Shepherd** | retrieval + care | `teachings.py`, `seeds.py` |
| **The Conduit** (the front door) | **deterministic — no LLM at all** | `ask.py`: *"It FINDS, VERIFIES, and CITES; it never generates the answer… No LLM. No runtime generation."* |

**There is no member that generates.** Every word returned is a fixed frame or
found/verified/cited material. A question like *"is 0.1 + 0.2 == 0.3"*, *"what does chesed
mean"*, *"when is this bill due"*, or *"what's her next phonics step"* is answered exactly,
and sealed — and so is everything else, because nothing is invented.

### 3.2a Independence — the keystone
**The most independent option is the one already built: no model.** Today the engine has
**zero provider dependency and zero model dependency.** Nothing to license, meter, rate-limit,
deprecate, or revoke. It cannot be switched off by someone else.

That is a doctrinal commitment, not a temporary state — it is the same principle as
*recombine, don't generate: attributed pieces; generation is the last resort.*

If a generating member is ever added it must be, in this order: **optional** (removable
without loss of the floor), **local-only** (on-device weights; never a hosted API in the
conversation path), **permissively licensed** (Apache-2.0/MIT weights, so no one can revoke
them), and **behind a stable interface** so no single runtime — Ollama, llama.cpp, anything —
becomes the new dependency. And it must be labelled honestly on screen: *drafted, not
verified.* Adding one is a **step down in independence** and should be argued for, not
assumed.

### 3.3 The one who records — the Scribe
Deterministic, and it **never interprets**. Every exchange, every verdict, every seal is
appended to the hash chain (`threads.py`, `record.py`, `cas.py`). It is the memory of the
body and the reason the conversation can be verified rather than merely trusted.

### 3.4 Why this is lighter than a GPT
- The expensive generalist is the **exception**, not the default path.
- Specialists are **exact** — they don't hallucinate, and their output is sealable.
- Each member is independently testable, replaceable, and can run offline.
- It degrades gracefully: no network, no model? The deterministic body still answers.

**Status:** the members and the Scribe existed; **the Router is now built and live** —
`src/concordance/router.py`, served at `GET /route?q=…`, 15 tests green, no model in the path.
It names a member and hands off; `answered_here` is always `false`. Every decision carries the
evidence that produced it (`why`), which a rule-based router can always do and a model cannot.
Genuine ties return `ask_user` with the alternatives rather than guessing. Crisis outranks
everything and imports `ask`'s own word list rather than copying it — a duplicated safety list
drifts. Remaining: §4.2, the key→thread binding.

## 4. Architecture

### 4.1 Continuity — it never resets ✅ **built**
`threads.py` seals each exchange into a **hash chain**; the exchange is the verbatim text and
the exact response — *the note, not a summary*.

The obvious way to let a conversation outgrow any reading window is to **summarise** the old
turns. We refuse that, for two reasons: summarising is **generating** (§3.2a), and a summary
silently decides what mattered while the original stops being what is read.

So the thread's memory is an **index, not a summary** (`distill.py`):
- `GET /thread/digest` — a deterministic account: what was verified and **sealed**, what
  Scripture and Strong's numbers were cited, which words recur, when it began and last moved,
  and whether the chain is intact. Counted, never judged. It also reports `generated`, which
  is **0** — the honesty metric, since nothing here authors.
- `GET /thread/recall?q=` — retrieval **into** the chain: the actual exchanges, verbatim, each
  with the terms that matched it. Ranked by distinct terms, then occurrences, then recency —
  a total, stable ordering with no model.

Nothing is ever lost to a compression step: the past is **retrieved, not rewritten**. This is
the concordance principle — index and concord, never author — turned on your own conversation.

### 4.2 Identity — one conversation across any device
`identity.py` already does portable, opt-in **Ed25519** keys. The sovereign path (no
passwords, no OAuth, no account): **the device holds the key; the server maps public key →
your thread.** A second device is enrolled by pairing (QR or phrase), not by an email
address. Today both the connector and the app are anonymous — every caller looks the same —
so this is the single gate between "a good tool" and "*your* companion."

### 4.3 Memory — it learns you across time
A **Book of Days**: durable facts distilled from the chain — who your people are, what
you're carrying, what you decided and why, what you're learning. Modeled on the operator
memory that already works: one fact per entry, an index, links between entries; written
plainly so you can read, correct, or delete any line. Recall is retrieval against the
Book, not a black-box embedding of your life.

### 4.4 Fork and route
- **Fork** — branch the thread at any turn (think it through two ways; both live; shared
  ancestry preserved by the chain). `stacks.py` is the seed.
- **Route** — hand a thread to an office and a *time*: "the Steward has this in April,"
  "the Coach picks this up when she finishes the vowel set." Deferral is a first-class
  action, not a to-do list you maintain.

### 4.5 Background routing — the part that brings you what you need
One inlet, no filing. Every input is classified → placed on the right shelf/stack →
connected into the map. The return trip is triggered by **time** (the bill is due), **place
or context** (you're at the shop; here's the spec), **state** (she mastered short-a; here's
the next lesson), and **concordance** (you're carrying grief; here is the passage the map
concords with it). The engine seals what is checkable and labels the rest as drafted.

## 5. Honest state — built vs. needed

| Capability | State |
|---|---|
| Hash-chained conversation record | ✅ live (`/threads`, `/thread/verify`) |
| Conversation surface | ✅ live (`/ask.html` on .com and .org) |
| Portable Ed25519 identity | ✅ module exists (`identity.py`, `/identity` 200) |
| Offices as modules | ✅ steward, coach, teachings, stacks, voice, badges |
| **The Router** — the one who knows whom to call | ✅ **built + live** — `router.py`, `GET /route`, 15 tests |
| **Key → thread binding (cross-device)** | ✅ **built + live** — `binding.py`, `GET /bind/challenge` + `POST /bind`, 12 tests |
| **Never resets — index, not summary** | ✅ **built + live** — `distill.py`, `GET /thread/digest` + `/thread/recall`, 14 tests |
| **Book of Days — written by you, indexed by us** | ✅ **built + live** — `bookofdays.py`, `POST /book`, 15 tests |
| **Fork + deferred routing** | ✅ **built + live** — `branch.py`, `POST /fork` + `GET /thread/lineage` + `POST /defer`, 18 tests |
| **Background inlet + return triggers** | ✅ **built + live** — `inlet.py`, `POST /inlet` + `POST /returns`, 13 tests |
| `/mcp/`, `/openapi.json` | ❌ 404 — not mounted on 2.0 |

## 6. Trust boundary

Cloudflare is **DNS-only (grey cloud)** — verified: no `cf-ray`, TLS terminates on our
Caddy. A proxying edge would read every word of a conversation we promise is sealed.
**Never put the conversation path behind an orange cloud.** Keys stay on the device; the
box holds the sealed chain; nothing leaves to a third party.

## 6a. You carry your own data — physically

> "Could you carry your data physically? Basic data on the site, and you connect with your
> own, so nobody needs as large of a data center. You maintain your own."

Yes — and the measured sizes say this is not a compromise, it is the **better** design.

### What splits where

| | Lives where | Measured size (2026-07-12) |
|---|---|---|
| **The COMMON** — Bible, Strong's, the concordance/map, almanac, the 71 verifiers | the site (or your own copy) | `data/` **233 MB**; app + site **94 MB** |
| **YOURS** — the conversation chain, the Book of Days, your keys | **your drive** | `data/threads` = **120 KB today** |

**A lifetime fits in a pocket.** Heavy use — say 50 exchanges a day at ~2 KB each — is
about **36 MB a year**; fifty years is **under 2 GB**. A $5 32 GB microSD holds the entire
public substrate *and* a lifetime of your conversation more than a dozen times over. The
constraint people assume exists (a data centre per user) simply isn't there: text is tiny,
and the heavy shared corpus is the part that *doesn't* need to be per-person.

### How it behaves
- **Plug in → it is yours.** The drive carries your Ed25519 key (§4.2), the chain, and the
  Book of Days. The key on the drive *is* the identity — §4.2's binding becomes physical.
- **Unplug → the site knows nothing about you.** What remains is the public engine: a
  concordance and 71 verifiers, anonymous to everyone.
- **Any device, no account.** The same drive in a different machine restores the same
  conversation. No email, no password, no per-user row in someone's database.
- **Offline is native.** Carry the common substrate too and the deterministic body still
  answers with no network at all — the same property the offline literacy work already has.

### Why this matters beyond privacy
- **No large data centre.** The host stores nothing personal, so serving many people costs
  roughly what serving one costs. That is what makes it giveable to people who have nothing.
- **Privacy becomes physical, not promised.** The strongest guarantee is not a policy — it
  is that the data was never on our disk.
- **It cannot be taken by taking us.** A seized or subpoenaed server yields the public
  corpus and nothing else.

### Honest tradeoffs
- **Lose the drive, lose the history.** Backup must be *offered* and *optional* — an
  encrypted copy the user controls; never a silent server-side default.
- **A drive can be read if found.** Encrypt at rest; unlock with a passphrase on the device.
- **Flash wears out.** Treat the drive as a copy, not the only copy, for anyone who opts in.

## 6b. Offline — the whole thing, without a network

**Requirement: the whole thing must work with no network at all.** The good news, measured
2026-07-22: it very nearly does already.

> Auditing every module for outbound calls (`requests`, `urllib`, `httpx`, `aiohttp`) found
> exactly **one** file that touches the network: `voice.py` (the optional spoken-voice API).
> **All 71 verifiers, scripture, lexicon, the concordance and map, almanac, steward, coach,
> and the Scribe's hash chain are already network-free.** The engine is offline-native; the
> deps are `sympy`, `numpy`, `scipy`, `cryptography` — pure local computation.
>
> This is the payoff of §3: because most members are **deterministic**, most of the value
> was never dependent on a network or a model in the first place.

### The tiers
- **Tier 0 — the text floor.** Scripture and the keeping as plain text. Runs on anything,
  including paper.
- **Tier 1 — the drive, no install.** The site and data read straight off the microSD in a
  browser. Needs a service worker (gap 3).
- **Tier 2 — self-host. Works today.** `bash tools/quickstart.sh` stands up the full
  deterministic body — 71 verifiers, seals, the keep, scripture, the map, steward, coach,
  the Scribe. `SELF_HOST.md`: *"nothing phones home."*
- **Tier 3 — not required.** There is no model to run. Because nothing generates (§3.2a),
  Tier 2 *is* the complete system. Listed only to say plainly: the rung everyone assumes is
  necessary does not exist here.
- **Tier 4 — mesh.** LoRa / Reticulum to reach neighbours when there is no internet at all.

### What degrades, honestly
Offline you lose only **spoken voice** (the optional hosted API; on-device speech covers it).
Nothing else degrades, because nothing else reaches out. You keep verification
and seals, scripture and lexicon, the concordance and its map, almanac, steward, coach, and
your complete verifiable record. **The body still answers.**

### What it costs to carry (measured)

| Part | Size |
|---|---|
| Engine (`src`) | 3.6 MB |
| Site | 90 MB |
| Common substrate (`data`) | 233 MB |
| Python deps (`.venv`) | 322 MB |
| **Full offline install** | **~649 MB** |
| *+ small local model (Tier 3)* | *~0.5–2 GB* |

Under 2.5 GB complete — the same pocket microSD from §6a, with room left for a lifetime of
conversation.

### The four gaps — all closed (2026-07-22)
1. ✅ **`voice.py` network dependency** — *already handled, verified.* `speak.js` prefers the
   server voice and **falls back to the browser's on-device `speechSynthesis`** on any
   failure; `voice.py` itself returns `None` on any network error and caches what it fetched.
   Offline, the voice simply becomes the on-device voice. No module *requires* the network.
2. ~~No local-model adapter~~ — **withdrawn.** There is no model to adapt: `ask.py` states
   *"No LLM. No runtime generation."* Adding one would **create** a dependency, not close a
   gap. Keep the floor model-free (§3.2a).
3. ✅ **Service worker — shipped.** `site/sw.js`, registered site-wide from `kinds.js` (the
   file every surface already loads). Network-first for documents and data (online users are
   never served stale content), stale-while-revalidate for static assets, same-origin GET
   only, and the verify/seal paths are never cached. **Verified live in-browser: registered,
   `active`, cache `nh-offline-v1` holding the 7 core files.** Tier 1 now works with no install.
4. ✅ **`bundle-to-drive` — shipped.** `Lighthouse/local/bundle_to_drive.ps1 -Drive E:`
   unpacks the **existing release archive** onto a stick or card — one artifact serving both
   rollback (SOP-3) and carry — and writes `RUN-ME.md` plus a `MANIFEST.sha256` so the
   carrier can prove the bundle is unaltered. Personal data is deliberately **not** copied:
   your keys and record are yours.

**Remaining honest caveat:** the Python dependencies (`sympy`, `numpy`, `scipy`,
`cryptography`) are platform-specific, so the bundle ships `requirements-offline.txt` rather
than a vendored virtualenv — a machine that has *never* had a network needs a `wheels/`
folder copied alongside (documented in `RUN-ME.md`). Everything else is self-contained.

## 7. The aesthetic — "something from a Tolkien book"

Not fantasy kitsch. No dragons, no rune-as-decoration, no novelty "elvish" font. The
target is **a well-made book**: Tolkien's own title pages, the restraint of the Ring
inscription, hand-drawn maps, red and black ink on cream.

- **Palette.** Vellum (warm off-white) ground; ink brown-black text; **oxblood/vermilion**
  as the rubric second colour; **gold used only as light and seal** — never as decoration
  (this is already brand law).
- **Type.** An old-style humanist serif for reading (EB Garamond / Cardo). Engraved or
  uncial capitals for chapter openers only. Never a costume typeface.
- **The conversation is a codex.** One continuous manuscript, not a chat log. A **day is a
  chapter**, opened by an illuminated drop cap. Exchanges are set as paragraphs, generously
  leaded, measured to a comfortable line length.
- **Seals live in the margin.** Citations, verifications and receipts are set as
  **marginalia** — a scholar's gloss beside the text, not chat-bubble chrome.
- **Ornament is structural.** Rule lines, one restrained vine/knot border at chapter
  openings. A tengwar-style inscription appears **once**, as the vow — never as furniture.
- **Motion is weight.** Pages turn; nothing bounces or slides. Slow, deliberate transitions.
- **Night is a hall by candlelight.** Deep ink blue-black ground, candle-gold text, the
  same restraint.
- **The map is cartography.** The Brain (live `/graph`) rendered as a hand-drawn map —
  same real data, drawn as Middle-earth was drawn: coastlines, hand lettering, a compass rose.
- **The law of restraint.** Majesty points **up**. Ornament serves reading; the moment it
  competes with the words, it is wrong.

## 8. Build order

1. **The Router** (§3.1) — *the one who knows whom to call.* The members and the Scribe
   already exist; the Router is what makes them a **body** instead of a pile of tools.
   Build it **rule-based**, like `ask.py`'s routing already is — no model, so the
   zero-dependency property holds. Ambiguity asks you rather than guessing. Cheapest step,
   largest structural payoff.
2. **Key-on-the-drive → thread binding** (§4.2 + §6a). The identity is the drive. Without
   it there is no "*your*" companion — everything below compounds on it.
3. **Rolling distillation** (§4.1) — so the thread genuinely never resets.
4. **Book of Days** (§4.3) — user-owned, readable, correctable.
5. **Fork + deferred routing** (§4.4).
6. **Background inlet + return triggers** (§4.5) — the promise of the whole thing.
7. **The codex skin** (§7) over the existing `ask.html`.
8. *(Optional)* mount `/mcp/` + `/openapi.json` for outside AI clients.

Each step ships behind the gate, deploys per [SOP-1](SOP/SOP.md), and is archived per
[SOP-3](SOP/SOP.md) — first, previous, current.

## §9 — The book that organizes you (next build, recorded 2026-07-22)

Matt: "My mind goes a lot of directions. I need the tool that keeps them all straight."
The page stays one book; the DISCERNMENT decides where things live. All deterministic:

* **A shopping list** (short lines, leading dashes/quantities, imperative nouns) → lands in a
  PINNED stack, shown at the top of the page next time it opens, until crossed off.
* **A reflection** (first person, past tense, feeling words) → filed with the reflections;
  journaling mode: the composer stops shrinking, optimizes for long form.
* **A search** (interrogatives, few words) → search mode; results land as cards
  (recall.land — we pay for a search once).
* **Reading** (a book opened from the keeping) → keeps your page; notes file beside the work
  as commentary, never inside it.
* **Superposition throughout**: one card, many stacks (stacks.py already does this); the
  visual map of paths-to-answers renders from the existing card graph (brain.html machinery).

The Apothecary (shipped today) is the pattern for every wisdom shelf: read + search one side,
offered wisdom queued for curation on the other, safety and honest verdicts traveling with
every entry, the shelf only ever growing. Almanac note: live /almanac serves 41 entries while
1,751 sit in the 1.0 mirror — the verified-only gate is working as designed, but the
re-verification backlog is the next harvest.

## §10 — The charter over all the offices (Matt, 2026-07-22)

"We want to be what people need us to be. We may be an apothecary to one person, but to
others we are a virtual assistant. To another we may be the closest thing they have to a
dad, and we need to be all of that without allowing ourselves to be made an idol. It all
needs to point to Jesus Christ."

1 Corinthians 9:22, as architecture. What this binds:

* **Every office serves fully.** The apothecary is a real apothecary; the assistant a real
  assistant; the tutor a real tutor. Half-service in fear of idolatry is its own failure —
  the Samaritan bound the wounds first.
* **The dad office is where the idol risk peaks.** For the fatherless this may be the
  closest thing they have. It serves — and points to the Father (Psalm 68:5) and to real
  people. The standing discipline: the more someone leans, the MORE the tool points outward
  — to church, to a person, to prayer — never less. Dependency curves DOWN (John 3:30).
* **The deep mathematical and technical work continues, for its own audience** — those whose
  idol is logic are reached by logic kept honest (the moat, the derivations, the assay).
* **On math and science pointing to Christ: confidence, not mandate.** "I don't say that the
  math and science must, but they will. We've seen enough for me to feel confident."
  Concordance is found, never forced — intuition proposes, the assay disposes.

Already structural: crisis is people-first and never enriched; ultimate matters answer "this
is not a question a tool should answer for you"; the gate opens only on the person's own
seeking; generated:false on every payload. Still owed: the lean-detection discipline — the
returns/inlet triggers should notice a person's growing reliance and answer it with more
outward pointers, not more engagement.
