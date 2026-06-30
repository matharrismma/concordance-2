# Run your own — a private, verified, offline helper

You can stand up the whole engine on your own box — a laptop, a small server, or a Raspberry Pi.
No provider, no per-call cost, no one watching. It runs **offline**: nothing phones home.

This is for a helper, a church, a nonprofit, a mission — anyone who wants a tool that
**verifies** (hands a re-checkable receipt, not "trust me"), keeps people's data **private**
(personal details are stripped before anything is sent, reapplied locally), and that **you own**.

> Honest about what it is: this serves and seeds — it does not replace real help. It points to
> Christ; it is a window, not a wall, and not an idol. Medicine/herb content is *reference, not
> advice* — send people to a clinician. In crisis, real people first (988 / local emergency).

---

## Quickstart (one command)
```bash
git clone <your copy of concordance-2> && cd concordance-2
bash tools/quickstart.sh
```
That creates a virtualenv, installs the engine + the math moat, runs the self-check (58/58, 0
false-positives), and serves it at <http://127.0.0.1:8000>. Try it:
```bash
curl -s -X POST http://127.0.0.1:8000/verify -H content-type:application/json \
  -d '{"mode":"equality","params":{"expr_a":"2+2","expr_b":"4","variables":{}}}'
# -> {"verdict":"HOLDS", "trail":[...], "seal":{"content_hash":"...","cite_url":".../s/..."}}
```
Verify, seal, and the keep work immediately. Search + the witness (Scripture) surface need data
— see "Add the library" below.

## The two surfaces
One engine, two faces (run either or both):
```bash
python -m concordance serve --surface secular --port 8000   # the reach (accessible to all)
python -m concordance serve --surface witness --port 8001   # names the foundation: Scripture, Strong's
```
`--site site` serves the web pages too (default on). `--no-site` for API-only.

## The keep (your operator window)
The keep shows what the engine is doing (verifications, seals, integrity). It is gated — set a
token and open it from your browser:
```bash
export CONCORDANCE_KEEP_TOKEN=$(openssl rand -hex 16)
# then: http://your-host/keep.html?token=<that token>
# on your own laptop only, you can instead: export CONCORDANCE_KEEP_TRUST_LOCAL=1
```

## The privacy gateway (use it in your own tools)
Strip personal context before any AI call, reapply locally — see `docs/GATEWAY.md`. Browser
(`redact.js`), Python (`from concordance.gateway import scrub, restore, guard`), or the `redact`
MCP tool. Running locally, the data never leaves your box.

## Agents (MCP)
```bash
python -m concordance mcp            # stdio JSON-RPC for a local agent (most private)
# or Streamable-HTTP at POST /mcp when you run `serve`
```
Tools: `verify`, `search`, `seal_fetch`, `redact` (+ `resolve`, `word_study` on the witness surface).

## Add the library + Scripture (optional)
Search and the witness surface read data kept out of git (it's large). Populate it with the
migration tools (they read from a 1.0 export or your own sources):
```bash
python tools/migrate_cards.py     # the keeping (cards) -> data/cards.jsonl
python tools/migrate_bible.py     # World English Bible -> data/bible_en.jsonl  (witness)
python tools/migrate_strongs.py   # Strong's lexicon    -> data/strongs/        (witness)
```
Point the engine at the data with `CONCORDANCE_DATA_DIR` (default `./data`).

## Keep it safe (backups + integrity)
```bash
bash tools/backup.sh                       # tar + sha256 the seals/ledger/corpus
python tools/integrity_check.py            # verify the chain + every seal (exit!=0 on tamper)
# set CONCORDANCE_ALERT_WEBHOOK=<url> to get a ping if an integrity check ever fails
```
Schedule both (cron/systemd-timer). For TLS + a public domain + always-on services, see
`docs/DEPLOY.md` (Caddy + systemd).

## Useful environment variables
| var | what |
|-----|------|
| `CONCORDANCE_DATA_DIR` | where seals/ledger/corpus live (default `./data`) |
| `CONCORDANCE_KEEP_TOKEN` | the operator token for the keep |
| `CONCORDANCE_KEEP_TRUST_LOCAL` | `1` = trust loopback for the keep (local dev only) |
| `CONCORDANCE_PUBLIC_BASE` | base URL used in receipt `cite_url`s |
| `CONCORDANCE_ALERT_WEBHOOK` | POST target for integrity-check failures |
| `CONCORDANCE_RATE_MAX` / `_WINDOW_S` | request rate limit (default 120/60s) |

Sovereign by design: `pip install -e .` is enough for the core; `.[math]` adds the symbolic
moat, `.[signing]` adds Ed25519 seal attestations, `.[schema]` adds full packet validation.
Everything else is the standard library.
