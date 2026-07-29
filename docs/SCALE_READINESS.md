# ON TRACK, AND READY TO SCALE? — measured 2026-07-29

Matt: "Ensure we are on track and ready to scale. The goal is 1M cards covering all topics."

Every number here came from a command run against the live box or the live corpus tonight.
Where something is not ready, it says so.

---

## 1 · ON TRACK — the gap program, closed or closing

| gap | state | evidence |
|---|---|---|
| **G5** domain verifiers unproven | **CLOSED** | 48 domains now carry a golden pair, each derived from the verifier's own documented example, run, and kept only if it held. **0 false positives.** Gated by `tests/test_domain_goldens.py` |
| **G2** sciences verified but unstocked | **CLOSED for proven domains** | 48 shelves stocked; shelves holding exactly one card: **33 → 20** |
| **G1** half the keeping is a pointer | **discipline set + 171 substance cards** | avg body 565 chars, real math + verdict + refused falsehood. Stub/body must be reported separately from here on |
| **G4** reachability | **CLOSED (and my measurement corrected)** | only `mesh.html` was genuinely lost; now in the palette. Routes declared agent-only by name; stale declarations fail the gate |
| **G6** box ≠ repo | **guard built; drift found** | `tools/verify_deploy.py` runs at the end of every deploy. First run found `airlock.py` **never deployed**, `web/keep.py` stale, 3 dead files from a July 25–26 refactor |
| **G3/G7** wings + doctrine-ahead-of-code | open, tasks #102–#104 | named, not hidden |
| **G8** seeker surface narrow | open | 12 questions; practical/relational asks still fall through |

---

## 2 · READY TO SCALE — the corpus dimension (the 1M question)

**Measured tonight, not projected from theory:**

| configuration | cards | RSS per process | per-card cost |
|---|---:|---:|---:|
| today (4 shelves frozen) | 496,730 | ~1,980 MB | 4.08 KB |
| **maximal freeze (24 shelves)** | 496,730 | **985 MB** | **2.03 KB** |
| **projected at 1,000,000** | 1,000,000 | **1,984 MB** | 2.03 KB |

**Verdict: the 1M goal fits — with the freeze widened.** Two processes at one million cards
would hold ~3.97 GB of the box's 7.75 GB, leaving ~49% headroom. Without widening it, the wall
arrives around 700k cards.

**And it costs the reader nothing:** the probe battery is **33/33 under maximal freeze**, and
IDF was already proven identical frozen vs resident. The mechanism is deployed, gated, and
measured — widening it is a config change plus a staggered restart.

*Recommended next action:* widen `CONCORDANCE_FREEZE_SHELVES` from 4 shelves to all 24. It
halves memory today and buys the entire runway to 1M.

## 3 · READY TO SCALE — the traffic dimension

| endpoint | warm latency |
|---|---:|
| `/health` | 10 ms |
| `/card/card_isbe_aaron` (full 1915 article from mmap) | **8 ms** |
| `/passage?ref=John 3:16` | 22 ms |
| `/search?q=faith` | 52 ms |

20 concurrent searches completed in **1,353 ms** — roughly **15 heavy searches/second** on 4
cores. Load average is 0.06; the box is nearly idle at present traffic.

**The ceiling is the serving model, not the machine.** Each surface is one Python process
(`ThreadingHTTPServer`), so the GIL caps a single surface's throughput. The box has 4 cores and
runs 2 processes.

*Scale path when needed (not yet):* run 2+ workers per surface behind the existing reverse
proxy. That is only possible **because** the freeze cut per-process memory — two workers per
surface at 1M cards would be ~7.9 GB and would NOT fit today, but ~4 GB with maximal freeze at
today's corpus does.

## 4 · OPERATIONAL RESILIENCE — better than expected, with one real hole

**In place and running:**
- Daily data backups with SHA-256 sidecars, 14 days retained; weekly full tarballs, 7 weeks.
- **Hourly integrity check**, currently reporting `ledger 307/307 verified, 752 CAS records all
  re-verified`. The trust kernel is being re-proven every hour on the live box.
- Both services `enabled` (survive reboot) with `Restart=on-failure`.
- Disk: 19 GB of 75 GB used — 54 GB free. Shards are 965 MB. No pressure.
- Swap barely touched (88 MB of 2,047) since the freeze landed.

**The hole: every backup lives on the box it backs up.** 2.7 GB of tarballs sit on the same
droplet — if the droplet is lost, the backups are lost with it. Nothing in `tools/backup.sh`
copies them anywhere else.

*This is exactly what the distributed corpus (task #103) answers structurally* — a node that
holds shards **is** an offsite backup, and the whole keeping is 965 MB. Until that ships, the
cheap interim is a pull of the newest daily tarball to Matt's HD on a schedule.

---

## 5 · THE HONEST SUMMARY

**On track:** yes. Five of eight gaps are closed or materially closed within hours of being
named, each with a gate so it cannot silently reopen.

**Ready to scale to 1M cards:** yes — the measurement says 1,984 MB per process at one million,
inside a 7.7 GB box, and search quality is unchanged under the freeze that makes it possible.
The freeze must be widened first; that is a one-line config change on proven machinery.

**Ready to scale traffic:** yes for any realistic near-term load (idle at 0.06 with 15 heavy
searches/sec available), with a known and unblocked path to more workers.

**Not ready:** offsite durability. One box holds the library and its own backups. That is the
single point of failure, and the answer is already designed (node roles) and queued.

**Not claimed:** that 1M cards will be *good* cards. The million must be counted in substance,
not stubs — 46% of the keeping is still a pointer, and the honest number to publish is both.
