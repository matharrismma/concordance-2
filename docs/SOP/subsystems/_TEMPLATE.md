# SOP · <Subsystem Name>

> One standard operating procedure per subsystem. It exists so that when a portion is out, anyone —
> Matt, an agent, a future context — can see what it does, confirm it's up, and fix it without
> re-deriving the system. Grounded in the real code: every command here runs. Keep it to one screen.
> Presence of this file drops the subsystem's SOP stroke to 0 on the Systems Handicap.

**Purpose.** What this subsystem does for the person or the agent — one plain sentence.

**Wiring.** Modules: `mod_a` · `mod_b`. Surfaces: `GET /x`, `site/x.html`. Where it sits in the flow.

## Canary — is it up?
The single check that confirms it functions end-to-end, with the expected result. Prefer a real probe:
```
curl -s https://narrowhighway.com/<endpoint> | ...     # expect: <what proves it works>
```
If the canary passes, the subsystem is connected. If not, go to Triage.

## Operate
How it's invoked in normal use — the entry point, the key parameters, what a good result looks like.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| <what you'd see> | <the real cause> | <the concrete fix, a command or a file> |

## Tests
`tests/test_<mod>.py` — run `PYTHONPATH=src python -m pytest tests/test_<mod>.py -q`. What they guard.

## Known issues & support
- **<issue>** — <the fallback or plan that keeps it supported>. (Mirror the issue register in `systems.py`.)

## Refine
The one process-improvement step queued for this subsystem — the next thing that lowers its handicap.
