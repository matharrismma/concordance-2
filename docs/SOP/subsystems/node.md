# SOP · Node / Sovereignty

**Purpose.** The engine as INFRASTRUCTURE others run — not a site anyone visits, but a self-contained node
you drop on a cheap offline computer (a Pi, an old phone, a solar mini-PC) beside a Meshtastic radio. It
gives a whole LoRa mesh two gifts, free and sovereign, with no account and no internet: a signed Daily Word,
and VERIFIED answers to questions typed into the mesh (crisis-first, byte-budgeted to ~200 bytes, carrying a
`/c/<id>` pull-ref). The AI lives BEHIND the radio; every reply is signed so any node pins the station once
and verifies its broadcasts offline forever.

**Wiring.** Modules: `lighthouse_node` (the composer + station identity) · `node_roles` (reader→carrier→node,
by choice) · `mesh` (the Fellowship Mesh) · `meshtastic_bridge` (the LoRa wire) · `airlock` (drag-a-file
intake, kept nothing). Bootstrap: `tools/cut_field_pack.py` cuts a sealed, runnable pack; the pack's own
`run.py` serves it. Mesh surfaces: `GET /mesh`, `GET /mesh/map`, `POST /mesh/post`, `GET /mesh/signable`.
The wire carries THREE honest states: UNALTERED (id = sha256, no key), SIGNED (signature internally
consistent), AUTHENTIC (signature vs the PINNED key — the strong claim, never laundered from an unpinned key).

## Canary — is it up?
Confirm the pack assembles, the whole chain verifies with no radio, and the mesh door answers:
```
python tools/cut_field_pack.py --check
# expect: "field pack would carry: <N> field cards + <M> Bible verses" — N must be nonzero
PYTHONPATH=src python -m concordance.lighthouse_node
# expect: crisis→988 (no lookup); a verified card rides LoRa authentic=True; a signed daily word authentic=True
PYTHONPATH=src python -m concordance.meshtastic_bridge
# expect: reassembled True · unaltered True · signed True · authentic True
```
The stronger proof a node truly stands up: cut a pack and run it —
`python tools/cut_field_pack.py --out DIR && python DIR/run.py` prints "Field pack OK." and
"crisis routes to real help: True". If these pass, the node builds, serves, and verifies offline.

## Operate
Cut once, carry, serve. `python tools/cut_field_pack.py` writes a sealed pack (self-verifies its own
MANIFEST); `--offline` bundles the `cryptography` wheels so the field node installs with no internet. On the
node: `./run.sh` (Windows `run.cmd`) sets up + self-tests; `./run.sh --serve --dev /dev/ttyUSB0` attaches to
the radio and answers the mesh; `--daily` broadcasts the signed card of the day. The first `--serve` mints
`station_key.json` (kept `0600`, never leaves the device) — publish the station PUBLIC key once so the mesh
pins the lighthouse. Roles: `node_roles.choose('carrier'|'node')` is the ONLY path off reader (reader is the
absence of a choice); `node_roles.status()` reports the chosen role AND what the disk actually holds — a
claimed carrier with an empty shard dir is visibly holding nothing.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| `--serve` → `{ok:False, "meshtastic not installed"}` | the radio library is absent (it is optional) | `pip install meshtastic` on the node; the composer + self-test still work offline without it |
| `--serve` → `{ok:False, "no Meshtastic radio reachable"}` | wrong/absent serial device | Pass the real `--dev` (`/dev/ttyUSB0`, `COM3`); the transport is field-test-pending on real hardware — stated, not hidden |
| A reply verifies `signed` but not `authentic` | the sender is not pinned, or the carried key ≠ the pinned key | Pin the station's public key once; an unpinned valid signature proves integrity, never WHO signed (by design) |
| `cut_field_pack` refuses: "no field cards found" | `CONCORDANCE_FIELD_DATA` / data dir points nowhere with cards | Point it at the repo `data/` (per-shelf `*_cards.jsonl` + `bible_en.jsonl`) |
| `status()` shows `consistent:False` for a carrier/node | role chosen but shard dir empty | `hold_manifest()` names where it looked; put the shard files there, or set the role back to reader |

## Tests
`tests/test_lighthouse_node.py`, `tests/test_mesh.py`, `tests/test_meshtastic_bridge.py`,
`tests/test_node_roles.py`, `tests/test_airlock.py` — run
`PYTHONPATH=src python -m pytest tests/test_lighthouse_node.py tests/test_mesh.py tests/test_meshtastic_bridge.py tests/test_node_roles.py tests/test_airlock.py -q`
(53 pass). They prove crisis-first + honest-miss composing, sign→chunk→reassemble→verify offline, the
confession gate + signed vouches, the 3-state wire, opt-in roles measured against disk, and airlock keeping nothing.

## Known issues & support
- **No off-site backup durability** — unsupported. Every backup currently lives on the same box it backs up;
  a lost box loses its history. The structural answer is `node_roles`: carriers/nodes as CAPACITORS holding
  shard copies close to the people who need them, each file carrying its sha256 waybill so a damaged copy
  heals from any peer holding the same hash. The roles are declared in code, but the SERVING tier (a node
  with a door open) is unshipped. (Mirrors the register in `systems.py`: `supported: False`.)

## Refine
Ship the node-role SERVING tier — a carrier that opens a door to peers — so held shards actually heal each
other off-box. That turns the unsupported backup gap into the capacitor answer already designed in `node_roles`.
