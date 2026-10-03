# The ark — the scripts that run on the desktop (HARRISMOTORS) against the 12 TB drive

These are COPIES of what runs from `D:\NarrowHighway-Backups\` (the drive is the live location; this
folder is the continuity copy — a known branch). Scheduled on the desktop with Task Scheduler:

| Task | When | Runs | Lands |
|---|---|---|---|
| NarrowHighway Backup | Sat 23:00 | `backup.ps1` — full snapshot of /home/nh streamed over ssh, verified end to end, seals counted | `D:\NarrowHighway-Backups\snapshots\` |
| NarrowHighway Ark Pull | Wed 23:00 | `ark_pull.cmd` → `tools/ark_pull.sh shards` — the nightly data tar + the shards, re-hashed | `D:\NarrowHighway-Backups\hetzner\` |
| NarrowHighway Memory Seal | daily 22:00 | `seal_memory.cmd` → `seal_memory.sh` — the decision memory, tar + sha256, to the ark AND the box | `D:\NarrowHighway-Backups\memory\` + `/home/nh/backups/` |

See docs/THE_CAMEL_2026-10-03.md for the tiers and the rule of known branches. 2026-10-03.
