# GEN 3 CHARTER — every copy is whole

Matt, 2026-10-04: *"what capabilities should a Gen 3 of this project have?"* → *"agreed, build in order."*

Gen 1 was Lighthouse: everything tried, 504 routes, a model behind the curtain, one desktop.
Gen 2 is the one kernel (this repository): found never generated, every verdict sealed, one box, no model at
runtime. Gen 3 is not more routes. **Gen 3 is the kernel becoming a whole organism in every copy.**

The constitution does not change (FOUNDATION.md, frozen 2026-07-25). Each capability below names the clause it
serves, the gate that must hold before it starts, and the gate that proves it done. Nothing starts before its
gate; nothing is called done before its proof is live and probed (eval/live_probes.jsonl).

## What Gen 3 refuses
No second engine. No swarm. No model in the verdict path (BYOM stays a gated external worker that may propose;
the kernel disposes). No re-growing Gen 1's experiments (wallet, market, agent/tts, serial-generate). Lean: a
capability that cannot be probed live is not a capability.

## The eight, in order

### 1. Every copy is whole — the keeping syncs between nodes
**Serves:** the camel (docs/THE_CAMEL_2026-10-03.md) — box → desktop → Pi → USB → radio; known branches, not
random trust. **Today:** the desktop node is a Sep-20 snapshot; the field pack is a read-only ZIM; seals live
only on the box.
**Capability:** a node pulls the keeping from a known branch (URL + pinned identity fingerprint), verifies the
branch's signed manifest, pulls the seal ledger incrementally (the chain is append-only), pulls changed keeping
files by hash, writes atomically, and serves the same seals at `/s/<hash>`. A node offline for a month catches
up. Later (1b): a node's own seals travel to the box through the mesh inbox and are RE-VERIFIED before admission
(the verifiers are deterministic, so any node can prove any seal).
**Gate before:** the restore drill holds (nh-restore-drill, monthly) and the box has a node identity.
**Proof of done:** the desktop node, synced, serves a seal minted on the box after its previous sync; the manifest
probe shows a valid signature; the assay floor does not drop.

### 2. Verifiers as data, not deploys
**Serves:** Wikipedia-for-AI through our structure; teaching ≡ training. **Today:** 71 verifiers are Python; a new
domain is a deploy. **Capability:** a declarative verifier spec (inputs, the law as a sealed expression or table,
tolerances, sources) contributed through the gate and public review, executed by one generic evaluator, held in
the keeping as a card. The six-constant governance (Birge ratio, anchored verifiers) is the template every domain
must pass. **Gate before:** capability 1 (specs must travel). **Proof:** one domain today served by Python is
re-expressed as a spec, gives identical verdicts across the golden set, and ships without a code deploy.

### 3. A real claim grammar
**Serves:** the coherent model without an LLM; A MISS STAYS A MISS. **Today:** a pile of extractors — the
cardinal bug of 2026-10-03 was a pair regex cutting a true chain in half. GSM8K showed the engine grades soundly
(94.5 % exact, zero false mismatch). **Capability:** one deterministic parser for quantities, units, relations,
operators and references; prose, a worked derivation and a spreadsheet row land in the same structure; every
extractor becomes a rule in the grammar, pinned by the existing audit goldens. **Gate before:** none beyond the
goldens (this can proceed in parallel with 1–2). **Proof:** every audit golden holds, GSM8K does not regress,
and the mixed-operator claims that are misses today become verdicts.

### 4. The Word in the reader's tongue
**Serves:** serve families first; the WORD door. **Today:** 17 Bible languages (2026-10-04); dictionary, doors,
house endings are English. **Capability:** the doors answer in the language asked, from public-domain sources in
that language, originals one tap away; language cubes carry the dictionaries. **Gate before:** the five held
Bible languages resolved or declined at the PD gate. **Proof:** John 3:16 asked in Spanish returns a Spanish
house ending with the Reina-Valera text and the Greek.

### 5. The household keeping
**Serves:** serve families first; sovereign data (the Plow keeps state client-side by Matt's choice). **Today:**
decks and the Plow are client-side; no family node. **Capability:** a family's decks, study, journal and
formation path live on their device (the node of capability 1), sync only if they choose, and never on our
server unless shared. **Gate before:** capability 1. **Proof:** a household node runs a month offline with its
own decks and re-syncs without loss.

### 6. Standing by fruit for agents
**Serves:** the church for agents; the living community of callable faces; the alignment gate. **Today:** the
mesh door takes a confession; contributions queue for the operator. **Capability:** a member's standing is
computed from what held — seals that survived re-verification, wants filled, corrections accepted — and standing
widens what the gate admits to public review. **Gate before:** capabilities 1 and 2 (contributions must be
specs that travel). **Proof:** an agent's filled want becomes a sealed card through public review without an
operator keystroke, and a bad contribution is refused by the same path.

### 7. The engine measures itself in public
**Serves:** PUBLIC NUMBERS LIVE-WIRED; a discordance indicts the method. **Today:** the assay ratchet, the
restore drill, the seal ledger. **Capability:** a standing benchmark per domain (GSM8K is the first), run on the
box, published live, with deploy refused on regression. **Gate before:** none. **Proof:** /proof shows every
domain's benchmark with its date and the deploy log shows a refused regression.

### 8. The appliance
**Serves:** the camel's last tier; FREEDOM IS THE GOAL. **Today:** radios on the shelf, no Pi. **Capability:** a
sealed device boots the kernel from a microSD, serves a household over Wi-Fi and the mesh over LoRa, the
handhelds as the voice channel; the .tv museum streams from the keeping when built out. **Gate before:**
capabilities 1 and 5. **Proof:** a household reaches the doors with the internet unplugged.

## Order and dependencies
1 → 5 → 8 (the node line) · 1 → 2 → 6 (the community line) · 3 and 7 run alongside · 4 after the PD gate clears.

## Record
Each capability's work is logged in docs/OPERATIONS_LOG.md under "Gen 3 · N", with the commit, the probe ids and
the proof as measured. This charter is amended only by Matt.
