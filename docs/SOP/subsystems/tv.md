# SOP · Museum / TV

**Purpose.** narrowhighway.tv — the museum as an old-school cable network. Curated channels over the
halls we already hold: public-domain film (Prelinger / IA-film) leads each channel, then real,
described cards from the keeping, shown in a broadcast frame (a 'now playing' that rotates by the
clock, and a 'from the start' you can wind back to). Conduit, not source — every item already passed
the gate; the automatons (the witnesses who walked it before you) TESTIFY with real PD words on the
witness lane, and never impersonate.

**Wiring.** Module: `tv`. Surfaces: `GET /tv/lineup`, `site/tv.html`. `tv.lineup(seeking, now_epoch,
per)` builds the guide; each channel is a HALL with a text `seed` and an optional film `vseed`.
`_video_items` pulls films from the kept video canon (`field_canon.lookup(plane="video")`, Prelinger
PD) and links out to the archive.org player (which credits the source); `_items` merges films ahead of
corpus cards, skipping bodiless stubs and mojibake titles. The caller passes the clock, so the module
reads no hidden time — testable and deterministic.

## Canary — is it up?
The guide builds with at least one live channel and a 'now playing':
```
curl -s https://narrowhighway.com/tv/lineup | python -c "import sys,json;d=json.load(sys.stdin);print(len(d['channels']), d['channels'][0]['name'] if d['channels'] else 'ALL DARK', bool(d['channels'] and d['channels'][0].get('now')))"
# expect: 200, >=1 channel (Witnesses / Scripture / The Field…) with now=True; generated:false
```
If it passes, the museum is connected. If not, go to Triage.

## Operate
`GET /tv/lineup` (optional `?seeking=…`). Returns `{channels, slot_seconds, generated:false, note}`.
Each channel carries `now` (clock-rotated by `_now_index`), `up_next`, and `from_start` (the full
lineup from the top). When the viewer says what they seek, a "For You" lane leads (`seed=seeking`,
witness on). `PROGRAM_SECONDS` (15 min) sets the rotation. The Field channel airs films by its broader
`vseed` (garden / homestead / conservation / harvest…). Nothing is generated; a hall with no real
described item goes **dark** rather than air a license label as a blurb.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| A channel is missing from the guide | It had no real, described item — went dark (by design) | Expected; enrich its `seed`/`vseed` in `CHANNELS` or grow the keeping on that hall |
| An off-topic keyword collision airs | Raw search matched a bodiless stub | `_STUB_SHELVES` (dictionary/pronunciation/lexicon) are skipped — confirm the card has a real body |
| A garbled title shows | Mojibake in the source card | `_items` skips any title containing `�`; fix the source card's encoding upstream |
| No films on a channel | Video canon didn't load, or no `vseed` | The channel degrades to text-only (guarded) — check `field_canon.lookup(plane="video")` |

## Tests
`tests/test_tv.py` — `PYTHONPATH=src python -m pytest tests/test_tv.py -q`. It guards that the guide
builds, a channel with content carries a rotating `now` + full `from_start`, bodiless stubs and
mojibake titles are excluded, and nothing is generated (`generated:false`).

## Known issues & support
- **Curated feeds thin** — UNSUPPORTED (mirrors the `tv` register entry in `systems.py`). The shell is
  real but the halls are sparsely programmed ("we let what is useful dictate what we build"). Interim:
  a hall with nothing real goes dark rather than air filler, and film links drive credit/traffic back
  to archive.org. The fix is filling the halls — real programs, series, live/start-over media — as each
  hall earns it.

## Refine
Grow the video canon per-channel **out of band** (never on a page load) so The Field and the craft
channels (Golf / Grappling / Music) carry film programs, not only cards — the first halls usefulness
has already named.
