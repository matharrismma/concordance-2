# THE CONSOLE — an audio-native coach & scribe

Matt, 2026-08-27: *"I see this as a coach and a scribe. Someone to write down everything important and
manage your daily schedule... a platform that can take and receive audio inputs and perform tasks
including dictation and making multiple copies... accept anything — drag an image, a screenshot, a PDF
— sort and form it into a usable, storable artifact; we don't need the image, we need the image
location... a tool for the disabled that everyone will want."*

## The north star

**A tool for the disabled that everyone will want.** The curb-cut effect: designed for the blind, the
deaf, the hands-busy, the low-literacy, the off-grid — and *because* it is, effortless enough that
everyone prefers it. Accessibility is the feature, never the compromise. This governs every choice
below: if a faculty can't be driven by voice alone AND read as text alone, it isn't done.

## What it is

One console you drive by **voice** (or keyboard, or touch — never only one). You speak; it hears,
acts, and speaks back. It is a **coach** (answers, guides, keeps the day) and a **scribe** (writes down
what matters, verbatim, and makes copies). It accepts **anything** and turns it into a light, located
artifact. It serves Christ: conduit, not source — it speaks found and verified words, and it never
generates the facts it keeps.

## The look — a simple book, a whole library, E-Ink first

Matt: *"It should act as a book on screen — a book you can add notes into — and the book acts as a whole
library. The tent in Harry Potter: normal outside, vast inside. The tools should appear very simple.
Optimized for E-Ink."*

- **A book, not an app.** The surface is a page: a title, a few lines, a place to speak or write a note
  in the margin. Turn the page; don't scroll. Calm, uncluttered, unintimidating — the curb-cut again.
- **Vast inside.** That simple book *is* the whole library — the keeping, your records, your artifacts —
  reached by asking, not by menus. Simple to look at; endless to go into.
- **E-Ink first, and this governs the CSS:** pure high-contrast (black on paper-white, or its inverse),
  **no animation or motion** (reduced-motion is the default, not an option), **page-turns not scrolling**,
  large legible **serif** body type, generous margins, no color needed to convey meaning, static renders
  that settle in one frame. It must be readable in direct sun and sip power — the off-grid field device.
- **Audio and E-Ink complete each other:** the page rests, static and low-power, while the voice carries
  the moment. You listen while you read; you speak while the page holds still.

## The faculties (each on infrastructure already here)

| Faculty | What you say / do | Where it goes | Built on |
|---|---|---|---|
| **Ears** | speak | transcribed at the edge | Web Speech API (sovereign) — *to build* |
| **Voice** | it answers aloud | floor (edge, offline, free) or ceiling (your ElevenLabs voice) | `voice.py`, `speak.js`, `/speak` |
| **Coach** | "what does the keeping say about…" | verified answer, spoken, a connection woven in | `ask.respond`, `corpus.connections` |
| **Scribe** | "note that…", "write this down" | your record, VERBATIM, never rewritten | `bookofdays.write` |
| **Schedule** | "put on my calendar…" | the calendar YOU named (.ics / CalDAV), consent-gated | the `/connect/event` pilot |
| **Copies** | "make N copies", "send this to…" | many light copies / distribution | `wants.py`, the waybill |
| **Intake** | drop a photo / screenshot / PDF / anything | a **located artifact** (see below) | cards + waybill |

## The intake principle — the location, not the blob

Drop anything in. The console extracts the **usable** form — the text (OCR for an image, the text layer
for a PDF), the metadata, a title — and forms a small **artifact card**:

    { title, kind, extracted_text, source_location (a path/URL/drive waybill), sha256?, at }

It stores the **card** (small, searchable, sovereign) and **points** to where the heavy source lives —
never the blob itself. The source follows by the tortoise (a drive, a later sync) if it is ever needed
in full. This is the two-tier distribution already in the architecture, applied to what comes *in*:
*"we don't need the image, we need the image location."*

## Delivery — answer now, source follows (LoRa-ready)

Every reply is a **small** payload: `{ headline, spoken, caption, source_waybill, connections, kind }`.
Small enough to cross a LoRa link. The **answer** (a few bytes of text) arrives immediately and is
spoken **at the edge** by the sovereign floor — so audio needs no bandwidth, only the text does. The
full **source document** is delivered later by the tortoise (minutes on the web, 24–48h over mesh).
Immediate spoken answer + deferred source = the hare and the tortoise, in audio, over any pipe.

## Crisis-first, always

The one hardened matcher (`ask.is_crisis`) runs before any routing. A cry is met with real help spoken
plainly — 988, a real person — before dictation, before a schedule, before anything. Mt 25.

## Sovereignty & privacy

- **Floor before ceiling.** Everything works on the edge with no key, no network (browser speech in and
  out). Your ElevenLabs voice is an enhancement, never a single point of failure.
- **Store nothing you needn't.** Intake keeps the location + the extracted text, not the blob. Writes to
  your record are yours (signed by your covenant key, or kept edge-local); no account.
- **The key is the operator's.** `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` live on the box, never in
  the browser, never in this repo.

## Build order (each a complete, deployed increment)

1. **Spine** — `console.py`: crisis-first → intent → dispatch (ask · dictate · intake), small payload out;
   `/console` route. Deterministic router, no LLM.
2. **The room** — `console.html`: audio-native, ADA (captions + transcript + keyboard + ARIA-live +
   reduced-motion), drop-anything intake, old-radio majesty. Speech in (Web Speech API), voice out (NHSpeak).
3. **Schedule + copies** — wire the calendar pilot and copy/distribution faculties.
4. **The tortoise & LoRa** — the deferred-source delivery and the mesh path.

Status: design locked; building the spine.
