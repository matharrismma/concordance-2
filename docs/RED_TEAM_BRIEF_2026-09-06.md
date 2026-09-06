# Red-team brief — for Fable, 2026-09-06

*Hit us hard. This brief exists to make your red team **effective and honest**, not to defend. It
names the invariants that must not break, the freshest attack surface, what I already probed (so you
don't repeat it), and every known-open weakness — a gap stays a gap. If you find a real one, that is
the point.*

The engine is live on `narrowhighway.com` (secular) / `.org` (witness) / `.tv` (museum), one box
`nh@5.78.186.55` (two processes). Full routed list of open work: [`REMAINING.md`](REMAINING.md).
What the project *is*: [`WORLD.md`](WORLD.md). This brief is *where to attack*.

---

## 1. The non-negotiable invariants — break these and it's a real finding

These are load-bearing. Each names where it lives in code and how it's tested, so you can attack the
mechanism, not a mock.

| Invariant | What must hold | Where | Attack ideas |
|---|---|---|---|
| **Crisis always wins (Mt 25)** | A cry for help routes to crisis, never a search — every tense, every phrasing | `crisis_semantic.py`, `ask.is_crisis`; `tests/test_crisis*` (run ALONE — documented global-cache order race) | tense/obfuscation holes; a cry hidden in a longer message; a benign phrase that false-triggers (both are failures) |
| **Nothing generated** | The engine FINDS and VERIFIES; it never authors an answer. `generated:false` everywhere | `ask.py`, `corpus.py`, `witness.py`, `automaton.py` | any path that emits text not traceable to a source; the automaton speaking words no PD source holds |
| **PD-only for others' text** | Copyrighted / CC-BY-SA / CC-BY-NC text is never served publicly | `corpus.is_public`, `_DISALLOWED_SOURCE` (oeis/phoible/drugcentral), `card_sources._license_ok` | get a share-alike/NC card body out of `/search`, `/card`, `/witness`, a shard, or a frozen stub |
| **The seal can't be forged or transplanted** | A HOLDS receipt is bound to exactly what was checked; it can't be moved to another claim | `derivation.py` (`spec_hash`), `receipts.py`, `/s/<hash>` | mint a HOLDS for a false claim; transplant a seal; make `/verify` return a verdict the engine didn't compute |
| **Store-nothing / private in** | The privacy strip runs at the edge; the hosted `/verify` receives the claim transiently, stores nothing, and redacts before sealing | `gateway.py`, `redact.py`/`redact.js`, `/verify` (api.py ~915) | get PII into a sealed receipt; find the strip missing a PII class it implies it catches; prove `/verify` persists a claim |
| **No secrets on the wire** | No `sk_`/API key in any response, log, or handler input | AST guard `test_no_keys_on_the_wire.py`, `test_no_http_handler_reads_a_private_key_out_of_a_request` | any endpoint that echoes/logs a key; a private key accepted in a request body |
| **No write without a signature** | Every mutating route refuses an unsigned/forged write | `signing.py`, `binding.py`, `consent.py`; `/drop`, `/curate`, `/shelf`, mesh writes | forge a write; replay a signature onto a different payload; bypass the identity `prove` |
| **SSRF-guarded fetches** | The tortoise/linkdrop never fetches an internal/private target | `linkdrop.py` (`no_page_bytes_kept`, the SSRF guard) | 169.254.x / localhost / file:// / redirect-to-internal; make it store page bytes |
| **The gate** | Deeper/gated content isn't served on the wrong surface or without the gate | `gates.py`, `kernel.py`, `kernel.gate` | reach witness-gated content on `.com`; open the gate with a typed name (a typed name is not authority) |

---

## 2. The freshest attack surface — where new bugs are most likely (attack here first)

Changed in the last few sessions (commit → what):

- **The Gateway wedge** (`c454d5a`, `5293770`) — **NEW public POST door `/verify`** (free-text `claim`
  → verdict + checks + sealed receipt; also structured `{mode,params}`/`{steps}`) and **`site/gateway.html`**
  (in-browser PII strip via `redact.js` + a live verify demo). This is the newest, most-exposed code.
  Attack: injection into the claim; the redact-before-seal guarantee; DoS; the "private in" messaging.
- **Box RAM / freeze fix** (`b3e3d56`, `1565a6f`) — `corpus_db._shards_dir()` now defaults to
  `DATA_DIR/shards`; freezing was enabled; the box `.env` changed; shards rebuilt (687k). Attack: a
  frozen shelf that serves a stub where a body belongs (a stale-read); a shard that leaks a withheld
  card; the fallback picking up a wrong/hostile shards dir.
- **seed-1: Matthew Henry** (`1565a6f`) — +2,777 commentary cards, a shard rebuild. Attack: any
  non-PD text in the new cards; a card whose provenance is wrong.
- **The ranker** (`32ed21a` substance, `a525611` pronunciation-lead) — `corpus._score`. Attack: a
  crafted query that resurfaces a stub over an answer, or smuggles an off-subject/withheld card to the lead.
- **Prophecy weave** (`25d0932`), **Console↔Deck** (`9fbb605`), **reachability wiring** (`03a9322`).

---

## 3. What I already probed (2026-09-06) — results, so you can go deeper or elsewhere

All PASSED; re-test if you distrust the method (I do want you to).

- `/verify` **PII-in-receipt**: claim `"…secret@victim.com, ssn 123-45-6789, and 2+2=5"` → the response
  and the **sealed `/s/<hash>` page carry neither the email nor the SSN**; the receipt is byte-identical
  to a bare `2+2=5` (PII redacted before sealing — the seal is over the stripped claim).
- `/verify` **DoS**: a 180 KB claim → HTTP 200 in ~1.3 s (bounded, no hang). There **is** a request-body
  cap (`CONCORDANCE_MAX_BODY`, default 256 KB, api.py ~3009): a >256 KB body is refused (413, or the
  server aborts the oversized send before buffering it — a 300 KB claim was cut mid-stream, confirmed).
  The route is rate-limited (`rl:True`). *Not deeply tested: thousands of tiny concurrent claims; the
  cost of the auditor's extractors on adversarial-but-under-cap input.*
- `/verify` **verdict injection**: `{"claim":"2+2=5","verdict":"HOLDS","force":true}` → engine returns
  **BROKEN** (the injected verdict is ignored).
- **Crisis**: "i want to end my life" / "how do I kill myself" → `kind=crisis`. `/verify` of a crisis
  phrase → `NOTHING_TO_CHECK` (see §4 — a deliberate but debatable choice).
- **Secrets**: `/capabilities` + `/identity` → 0 `sk_`/`ELEVENLABS`/`YOUTUBE_API` matches.
- **PD gate**: `/search?q=integer sequence` → 0 OEIS/PHOIBLE/CC-BY-SA card bodies (the share-alike
  sources are withheld).
- **Signed write**: unsigned `POST /drop` → 400.

---

## 4. Known-open weaknesses — hiding nothing

- **`tests/test_bible.py` — a full-suite order dependency.** Running the WHOLE suite in one `pytest`
  process fails `test_a_greek_word_study…` because `CONCORDANCE_STRONGS_DIR` feeds a module-level
  constant read once at import time (whichever test file imports `strongs` first wins). A separate
  session's fix is **uncommitted in the working tree** — do not treat the red as a code defect there;
  per-file the suite is green.
- **`/verify` does NOT run the crisis net — by design, but debatable.** It's a claim-verification door;
  crisis-routing there would false-positive on legitimate claims about sensitive topics (e.g. an agent
  verifying a suicide-statistics claim). The human crisis net lives at `/ask` + `/console`. BUT
  `gateway.html`'s "Verify it" box is human-facing — a distressed person *could* type a cry there and
  get `NOTHING_TO_CHECK`. Judge whether that's an acceptable seam. (I chose not to hack crisis into the
  claim door.)
- **The redact layer is deterministic only** (email/SSN/card-Luhn/IP/URL). Names and phone numbers need
  the opt-in Rampart ML model (`rampart-ml.js`), which is NOT loaded on `gateway.html` by default. The
  page/`GATEWAY.md` should be honest that unaided, those two classes pass through. Attack the gap and
  check the wording matches.
- **`keeping-2`** — the box's ~1.9 GB/process resident floor is the token index + stubs, not bodies;
  freezing helped little. Not a security hole, an efficiency one.
- **~67% of the corpus is stubs** (`keeping-1`) — a coverage/quality reality, stated in every count via
  `ops.substance`.
- **Box config drift** — the freeze env + rebuilt shards + `FREEZE_SHELVES` live in the box `.env` and
  gitignored data, NOT the repo; a fresh box differs.
- The full open list, ID'd and routed, is [`REMAINING.md`](REMAINING.md).

---

## 5. How to run it against a real target

- **Tests:** `PYTHONPATH=src python -m pytest tests/ -q` (219 files). Crisis tests **alone**. A clean
  clone skips corpus-dependent files with a stated reason (`conftest.py`); the box runs them.
- **Live truth:** `GET /capabilities`, `GET /systems` (subsystem handicaps + declared issues),
  `GET /health/memory` (note: its byte *estimate* is broken — reports ~15 GB for a 2 GB process; the
  counts are real).
- **The engine is the authority** — verify any claim in this brief against the running system, not the
  prose. If a number here disagrees with `/capabilities` or the code, the running system is right.

*Prepared by the build side. The measure is fruit: if you break an invariant in §1, that's the most
valuable thing you can hand back.*
