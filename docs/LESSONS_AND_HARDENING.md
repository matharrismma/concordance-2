# THE LESSONS, AND WHAT THEY OBLIGATE

Matt, 2026-07-30: *"Use the lessons learned to improve our project."*

One night produced more correction than any night before it. Every lesson below is **measured** —
it has a number, a failing artifact, or a retraction behind it — and each one names the work it
obligates. Lessons without work attached are not lessons; they are sentiment.

The ordering rule for the worklist: **the things that are currently WRONG come before the things
that are merely missing**, and a lesson that has already cost us twice outranks one that has cost us
once.

---

## PART I — what tonight proved

### L1 · A typed name is not authority
`shelves.curate` refused an *empty* steward name and felt like a check. It was not. `steward` is a
string anyone can type, and C1b shipped that to the live box: for that window any passer-by could
have promoted their own drop into the commons or pulled another member's card down. Nothing was —
verified directly on the box — but the exposure was real.
**The tell:** if the only thing between a stranger and the act is a string they choose, there is no
check. Ask what the caller must *hold*, never what they must *say*.

### L2 · Length is never the test — this cost three false findings in one night
1. **246 cards** reported as shipping a placeholder because their titles contained `_xxx`. It is the
   Roman numeral **XXX**. Retracted in the open.
2. **157,130 cards** (29% of the library) flagged as truncated by `[a-z,]$`. They were Scripture
   verses — punctuated with a comma *because the sentence carries into the next verse* — and recipe
   ingredient lines.
3. **105 lexicon cards** flagged for ending in a preposition. `to violently make gain of` is a
   complete BDB gloss.

**The pattern underneath:** the library does not write like prose. It holds verses, glosses,
ingredient lists, Hebrew, and commentary, and every one ends differently. Any rule that assumes one
voice will accuse thousands of cards of a fault they do not have.

### L3 · Judge and act must be separate, or a bad rule eats the library
The assay reports and changes nothing. That is the only reason lesson L2 cost **one measurement**
instead of **157,130 edits**. Any process that both decides and executes will be trusted before it
has earned it.

### L4 · Check the check — the instrument was wrong more often than the system
Tonight: the `_xxx` reading, the truncation rule (×3), the shelf-count expectation in the live probe,
the "no MCP errors" claim (I searched service logs; our own telemetry held both errors), and the
`/card/null` attribution (I implied it was ours; `Sec-Fetch-Site: same-origin` across 765 distinct
pages plus a clean-browser reproduction says it is an extension). **When a measurement indicts the
system, suspect the measurement first.**

### L5 · Correct server-side and wrong in front of the person is not correct
A member withdrew their card, the store recorded it, and the page still showed the card. The tell was
**exactly one write behind** — a cache, not a race. And no JSON response on this server had *ever*
carried `cache-control`. Fixing the header was right and **did not fix it**: the client ignored both
`no-store` on the request and on the response. Freshness had to go in the URL.

### L6 · Test the wire, not the function
That bug passed every one of 989 tests. `api.serve()` had to be split into `build_server()` so a test
could bind port 0 and read real headers. A dispatch-level test passes for exactly as long as the wire
stays silent.

### L7 · An error can be hiding a wrong answer
Telemetry logged `OperationalError: database is locked`. Chasing it found that a shared SQLite
connection under 12 concurrent readers also returned **`fetchone()` → None for a row that exists**.
An outage is loud; a library that quietly denies holding what it holds has failed at the one thing it
is for.

### L8 · Fix the path, not the artifact that looks like the path
Editing `site/robots.txt` did nothing — robots.txt is *generated* in `api.py`. Only the live check
caught it.

### L9 · The gate is the safety net, and it caught me twice
`shelf.html` shipped without the shared home control; the doctrine spine shipped with
`connections: []`, stranding 9 cards in an island that never reaches the Floor. **Both were mine.**
Neither would have been caught by reading the diff.

---

## PART II — what Matt's own documents obligate

Harvested 2026-07-30 from six planning documents plus the Calibre code drop, and carded on the
`doctrine` shelf. Three of them indict something live:

### L10 · A gate closes against a number, an OWNER, and a FALLBACK  *(Prism v2.3)*
`tools/check.py` closes against numbers — coverage floors, 0 false positives, a real exit code — and
names **no owner and no fallback**. The punch list has completion tests but does not say who answers
for each, or what happens when one cannot close.

### L11 · Authority sunsets  *(The Way v0.2)*
*"Startup authority sunsets into the ordinary governance system."* Our steward token is **one
permanent secret, no expiry, no rotation, and no record of who holds it** — the precise opposite.

### L12 · WAIT is a first-class result, and a refusal names its gate  *(Calibre engine.py)*
`Result.PASS_ / WAIT / FAIL` with `Block.LAW | WAIT | WITNESS | MUTUAL | PROOF | ALIGN`. Every
refusal says *which* gate stopped it, and `WAIT` is an outcome rather than a failure. Our three
states are HOLDS / BROKEN / SYSTEM_ERROR and name no gate. `Block.WAIT` is also the **GOD gate** —
the one of four we never built.

### L13 · A stated degradation order  *(Humanoid Robot v0.2)*
Shards freeze and unfreeze and `core` can never be frozen — that *is* a degradation order, and it is
written nowhere. A system that has not decided what it sheds will shed whatever fails first.

---

## PART III — THE WORKLIST

One unit at a time, finished before the next is started. Done means **gated, deployed, verified live,
and committed** — never "the code exists". Each names its own completion test.

| # | unit | from | done when |
|---|---|---|---|
| **H1** | **Steward authority that sunsets** — token carries issued-at + expiry, supports rotation without downtime, and every act records WHICH steward identity acted (never the secret). Expired token refuses with a reason. | L1, L11 | a token past its expiry cannot promote; rotation works with both old and new valid during overlap; `curation.jsonl` names the identity; gated + live |
| **H2** | **WAIT, and every refusal names its gate** — add `WAIT` beside HOLDS/BROKEN/SYSTEM_ERROR, and a `blocked_at` naming which gate stopped it. Completes the four-gate set with the GOD (time-window) gate. | L12 | a caller can tell WHY it was refused and WHICH gate did it; WAIT never renders as failure anywhere; gated + live |
| **H3** | **One shared `getJSON` with freshness built in** — eight pages carry their own copy and only `shelf.html` busts the cache. Any page that reads after a write can show a stale answer. | L5 | one helper, used by every page; a read-after-write probe on `community.html` and `mesh.html` measured, not assumed |
| **H4** | **The gate names an owner and a fallback** — each gate in `check.py` and each punch-list item carries who answers for it and what happens if it cannot close. | L10 | no gate closes without all three; a failing gate prints its fallback |
| **H5** | **The degradation order, written and checked** — declare what is shed first when memory, disk, or network is short, and test that `core` is genuinely last. | L13 | the order is a document AND an assertion; freezing everything still answers from `core` |
| **H6** | **Apply the assay's named repairs** — 2,124 titles to render readably (`Meditations 4.38`, not `§aur_04_xxxviii`), 21 cross-references to turn into edges, 5,405 refills to review. | L2, L3 | titles render for a reader; the count drops and is re-measured by `tools/assay_cards.py` |
| **H7** | **Wire-level tests for the guarantees that live in headers** — extend `build_server()` coverage past `cache-control` to the other promises the wire alone can prove. | L6 | each header-borne guarantee has a test that binds a real socket |

### Standing rules this adds
1. **No rule that judges may also act** in the same pass. Report, read, then apply. *(L3)*
2. **No rule about card quality may use length as its test.** *(L2)*
3. **When a measurement indicts the system, check the measurement first** — and say so in the
   report, with what was measured and how. *(L4)*
4. **A guarantee that lives in a header gets a test that binds a socket.** *(L6)*
5. **Every refusal names what was needed** — the rule broken, in words a caller can act on. *(L12)*

---

*The gate stays the arbiter. Nothing on this list is done because it was written here; it is done
when the gate passes, the box serves it, and the commit says what was measured.*
