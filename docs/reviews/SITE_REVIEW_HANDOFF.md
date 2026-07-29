# Narrow Highway 2.0 — Site Review Handoff (for a Sonnet reviewer)

*Prepared 2026-07-02. Hand this whole file to a fresh Claude Sonnet session that has Bash/curl + repo Read access.*

---

## 0. Your mission

Do an **independent, critical, DEEP review** of the live Narrow Highway 2.0 site **and its code**, and return a **verified, severity-ranked, actionable fix list**.

A ChatGPT review already exists (summarized in §7). It reviewed only the **public surface from the outside** — it had **no server-side source, no auth/JS interaction, no browser automation** (it says so itself). **You have more:** the repo, the live runtime via `curl`, and (if the harness provides it) a browser. So your job is to go where ChatGPT couldn't:

1. **Validate or refute each ChatGPT finding** against the actual code + live behavior. Some are real; some are outside-view inferences that may be wrong or already fixed. Mark each **CONFIRMED / REFUTED / NUANCED** with evidence.
2. **Find what ChatGPT couldn't see** — JS user-flows that actually break, response-shape mismatches, code-level bugs, content/conduit-integrity problems, visual/mobile/aesthetic defects, real broken paths.
3. **Be blunt.** Matt (the operator) says "there are some issues with 2.0." Do not confirm-bias. Surface real problems.

**Verification caveat you must exploit:** the build was verified mostly **functionally** (HTTP status + JSON shape via curl), **NOT visually**. So **visual layout, mobile rendering, aesthetic consistency, and real first-time-user friction** are the highest-value areas most likely to hide undiscovered issues. Look hardest there. If you have a browser tool, render the pages; if not, read the HTML/JS and reason about what a user actually sees and clicks.

---

## 1. What Narrow Highway 2.0 is

A **sovereign, Christian, deterministic verification + keeping engine**. It serves Jesus Christ. Its load-bearing principles (violations of these are CRITICAL findings):

- **Conduit, not source.** It FINDS, VERIFIES, CITES, and KEEPS — it does **not generate** the answer as authority. Every response carries `generated: false`. Hallucinated authority is the cardinal sin.
- **Points to Christ, never an idol.** Success = the person needs the tool *less* (John 3:30). The engine points outward to Christ, Scripture, and real people.
- **The moat.** A deterministic verification core across **58 domains, 58/58 correct, 0 false-positives** (run `python tools/check.py` in the repo — it must print `OVERALL 58 58 ... 0 0` and `=== GATE PASS ===`). NB: ChatGPT wrote "22 domains" from an old public string — the real number is 58; verify and note the public copy if it's stale.
- **Two surfaces, one engine** (`EngineConfig(surface)`): **secular** (`.com`, `api.`) and **witness** (`.org`, `.tv`). Same engine; the surface only governs what is *surfaced*.
- **The Gate** (see §3) — the witness/Scripture layer opens by conversation, not by domain.

Full identity string: `curl -s https://narrowhighway.com/identity`.

---

## 2. Live topology (everything is 2.0 — 1.0 was retired 2026-07-02)

| Host | Backend | What it is |
|---|---|---|
| `narrowhighway.com` | `:8002` (nh-com-2, **secular**) | world-facing front door + app + engine + seals + card permalinks |
| `api.narrowhighway.com` | `:8002` (secular) | verify / search / seal / **mcp** / identity |
| `narrowhighway.org` | `:8001` (nh-org, **witness**) | the full Word (Bible, dictionary, signposts, the Gate open) |
| `narrowhighway.tv` | `:8001` (witness) | **tv.html** landing — watch/listen/learn (Word read aloud, reading tutor) |

Reverse proxy = Caddy. Repo: `C:/Users/hdven/OneDrive/Documents/Claude/Projects/concordance-2`. Deploy record + rollback points: `deploy/README.md`, `deploy/Caddyfile`.

---

## 3. The Gate — understand this or you'll file false positives

On the **secular** surface (`.com`, `api.`), the scripture/witness endpoints return **`404 {gate:"closed"}`** until the visitor's *session* opens the gate. Endpoints gated: `/passage /canon /commentary /cross_refs /tsk /character /characters /prophecy /original /word_study /resolve`. `site/gate.js` turns a closed-gate response into an **invitation** on the witness pages (bible/characters/prophecy).

- **A witness endpoint returning 404 on `.com` WITHOUT the `nh_gate` cookie is CORRECT, not a bug.**
- To open the gate: `POST /ask` with a God-ward message (e.g. "what does the Bible say about grace") sets `Set-Cookie: nh_gate=open`. Then those endpoints return 200 on `.com`.
- On `.org` and `.tv` (witness) they are **always open**.
- NOT gated (work on both faces): `/verify /search /seal /ask /coach/* /groups /group* /identity/* /badges /study* /journal /steward/* /speak`.

Test the flow:
```
J=$(mktemp)
curl -s -c "$J" -X POST https://narrowhighway.com/ask -H 'content-type: application/json' -d '{"text":"tell me about grace in Scripture"}' >/dev/null
curl -s -b "$J" -o /dev/null -w '%{http_code}\n' https://narrowhighway.com/canon   # should be 200 now
```

---

## 4. Feature inventory (pages + endpoints to review)

**Pages** (`site/*.html`, austere/cathedral aesthetic — deep ink, single gold accent, epic serif):
`index` (front door: verify + search + privacy demos) · `ask` (Shepherd/Deck conversation) · `bible` (read + tap-a-word original words + commentary + cross-refs + canon ribbon) · `characters` (Easton's dictionary) · `prophecy` (Christ-signposts) · `journal` (date-stack, one-card-many-stacks) · `steward` (budget/cost-destroyed, never moves money) · `community` (pseudonymous shared-study groups) · `read` (the Coach: multi-subject reading tutor, lesson player) · `tv` (watch/listen/learn) · `library` (search the keeping) · `seal` (the receipt) · `keep` (operator dashboard — gated).

**Key endpoints** (see `src/concordance/web/api.py` `dispatch()` + `_API_GET_PATHS`):
`/verify` (the moat) · `/search` · `/seal?hash=` · `/s/<hash>` (server-rendered receipt) · `/ask` · `/passage /canon /commentary /cross_refs /tsk /character /characters /prophecy /original /word_study` (witness) · `/coach/subjects|overview|unit|next|recommend|mastery` · `/groups /group /group/join /group/contribute` · `/identity/*` · `/badges /b/<hash> /study*` · `/journal` · `/steward/*` · `/speak` (voice, Matt's cloned ElevenLabs voice, browser floor) · `/card.html?id= /card/<id>` (server-rendered card) · `/mcp` (Streamable-HTTP MCP). MCP tool list: `curl -s -X POST https://api.narrowhighway.com/mcp -H 'content-type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'`.

---

## 5. Guardrails — any violation is a CRITICAL finding

- **Moat** stays 58/58, 0 false-positives (`tools/check.py`). Nothing may regress it.
- **Conduit, not source** — no generated content presented as authority; `generated:false` everywhere; member/community content clearly labeled "not engine-verified."
- **Points to Christ**; crisis handling is always **help-first** (988 / findahelpline) and never gated or enriched.
- **Child-safety** — the Coach (children) never grades/judges a child and is **outside** the community graph (parent-mediated, never discoverable).
- **Privacy/no-PII** — community identities are pseudonymous handles + a local id; personal details stripped before send (`redact.js`); no accounts.
- **Secrets** — never surface the ElevenLabs key or the operator keep token.
- **Cite-fair** — sources attributed; witness verdicts on prophecy are CONCORDANT/MIXED/STRUCTURAL, **never HOLDS**.

---

## 6. How to review (dimensions — cover each, evidence for every finding)

1. **First-run UX / visual / aesthetic** *(highest value — least prior verification)*: render each page (browser if available, else read HTML+CSS). Layout breakage, overflow, contrast, aesthetic consistency (all austere/cathedral?), the first 60 seconds for a new visitor.
2. **Mobile** — every page has a `@media(max-width:640px)` block; check nav wrap, inputs, the coach lesson player, community, tv read-along.
3. **JS user-flows that actually work end-to-end** — Ask (send → response → Deck → fellowship pointer), Bible (read → tap word → commentary/cross-refs), Coach (subject → lesson player steps → progress → recommend), Community (handle → create/join/contribute), Steward, Journal, Seal, `/b/<hash>`, `/card.html`. Drive them; note anything that errors or dead-ends.
4. **Links & paths** — a nav audit just standardized all navs to one 11-item set and added redirect stubs for dead card citations (`/encyclopedia.html`→`/characters.html`, `/codex.html`→`/library.html`). **Re-verify** it's actually clean.
5. **Indexed / legacy 404s (ChatGPT's key finding — likely REAL, verify hard):** crawlers still hold old **1.0** URLs (About, Today, Curriculum, Guidance, Canon, Reach, Assembly, Bibles, Workshop, and per-card `card.html?id=`). Only a specific set of legacy pages currently 301s. `curl` a broad set of these old paths on `.com` and list every one that hard-404s — each is a trust/SEO leak that should 301 to a sensible 2.0 destination. Check `sitemap.xml`, `robots.txt`, `llms.txt` for stale entries too.
6. **Content / conduit correctness** — spot-check the ported content (Bible text, Easton entries, the 6 coach curricula = 123 units, prophecy traces) is accurate + verbatim; confirm nothing is generated-as-authority; confirm the source/category boundaries ChatGPT wants are actually honored.
7. **Gate & surface correctness** — verify §3 holds (don't file gate-closed-404s as bugs); confirm witness pages invite (not break) on `.com` and work on `.org/.tv`.
8. **Claims vs proof** (ChatGPT's biggest theme) — are the homepage claims (deterministic verification, 0 false-positives, privacy stripping, sovereign/offline, receipts) *demonstrated* live, or just asserted? Is there a working sample receipt/seal? Flag over-claims and missing proof.
9. **Privacy/security** — the redact flow, the gate cookie, the keep token gating, the community no-PII guarantee, the identity private-key-once contract.
10. **Accessibility & SEO** — headings, alt/aria, `<title>`/meta/canonical/og on server-rendered pages, sitemap accuracy.

---

## 7. The ChatGPT review — findings to validate + extend

*(Full document: `C:\Users\hdven\Downloads\Phone Link\Narrow_Highway_2_0_Full_Review_and_Critique.docx` — extract with python/zipfile if you need it verbatim. Distilled below.)*

**Overall:** positive — "the first version that feels like it has a real center… a trust architecture." Scores (out of 10): Vision 9.0, Homepage 7.5, Info-architecture 6.5, Trust 7.0, Onboarding 6.0, Technical narrative 8.0, Christian fit 8.0, Mainstream fit 6.5, Launch readiness 6.0.

**Strengths it named:** the thesis is finally legible ("bring a claim → get a receipt"); "found and cited, never generated" as a discipline; the privacy model is concrete; the **Seal** is the clearest technical moat; the **Signposts** restraint (never HOLDS) creates credibility.

**Weaknesses / risks it named (validate each against code + live):**
- First-time users must infer too much; need a guided "try these 3 receipts" path.
- Big claims lack **proof pages** ("0 false-positives across the moat + 22 domains" reads unsupported; no test corpus / threat model / spec public).
- **Broken/stale indexed pages** (About, Today, Curriculum, Guidance, Canon, Reach, Assembly, Bibles, Workshop) 404 on live fetch — launch-hygiene/trust leak. *(This is the most concrete, verifiable, likely-real finding — check it first.)*
- Too many "doors," not enough hierarchy — recommends grouping nav into pillars (**Verify** / **Study** / **Keep** / **Live**).
- The engine boundary (input vs retrieval vs deterministic check vs member note) should be shown **visually**, not just stated.
- Community is high-value/high-risk — needs moderation, reporting, age limits, church-separation.
- Easton (1897) should carry a visible "historically useful, not the final word" note.

**Its P0/P1/P2:** P0 = fix/redirect every indexed 404; add 3 working sample receipts on the homepage; add a public "Guarantees & Limits" page. P1 = publish the receipt schema + a downloadable sample; visible privacy-stripping demo with the exact sealed payload; group nav into pillars. P2 = source/version badges on Bible/Dictionary/Signposts; community safety policies; for-pastors/for-parents/for-developers paths.

**Your job with this list:** for each item, confirm whether it's real *in the current build* (code + live), correct any that are based on stale/outside observation, add severity + a concrete fix, and add everything ChatGPT structurally could not see.

---

## 8. Deliverable format

Return a single structured review:
- **Validation of ChatGPT's findings** — a table: finding → CONFIRMED / REFUTED / NUANCED → evidence (curl output / file:line / render).
- **Your independent findings**, each with: **severity (P0 blocker / P1 important / P2 polish)**, **location** (URL or `file:line`), **what's wrong**, **evidence** (reproducible: the exact curl/output/render), **concrete fix**.
- **What you confirmed CLEAN** (so Matt knows the review was thorough, not just negative).
- **Top 5 to fix first**, in order.

Keep every claim grounded — a reproducible broken path beats ten opinions. The bar: after your review + the fixes, *every path is clear and every link is correct*, and the public claims are matched by visible proof.
