# The Lighthouse Node — the engine as infrastructure, behind a radio

**Not a site you visit. A node you run.** Drop it on a cheap offline computer (a Raspberry Pi, an old
phone, a solar mini-PC) beside a [Meshtastic](https://meshtastic.org) radio and it gives a whole LoRa
mesh two gifts — free, sovereign, no account, no internet:

- **The Daily Word** — a signed verse / card of the day, broadcast to every node in range.
- **Answers** — a question typed into the mesh comes back as a **verified** card: crisis-first,
  budgeted to the ~200-byte LoRa payload, carrying a `/c/<id>` pull-ref the reader can open later when
  they have signal.

## Why a node and not another web page

The engine's two real superpowers — **it proves what it says**, and **it works when the internet
doesn't** — are invisible on the open web, where everything claims to be trustworthy and everything
works online. They are only *felt* off the grid. This is the engine standing in the one place the giants
can't follow: the valley with no bars, the storm with the power out, the mission field, the campground.

**The AI lives *behind* the radio, never on it.** A Meshtastic board is a microcontroller (kilobytes of
RAM, ~200 bytes per message) — you cannot run the engine on it. So the engine runs on the node beside it
and answers the mesh. That's not a limitation to hide; it's the honest architecture.

## Run it in five minutes

No radio and no corpus needed to see it work — the whole chain (compose → sign → chunk → reassemble →
verify offline) runs in memory:

```bash
python -m concordance.lighthouse_node          # self-test: crisis + a verified answer + the daily word
```

Answer one question from your local corpus, or print the card of the day:

```bash
python -m concordance.lighthouse_node --ask "how do i stop bad bleeding"
python -m concordance.lighthouse_node --daily
```

Then add the radio. Install the Meshtastic Python library and plug in your board:

```bash
pip install meshtastic
python -m concordance.lighthouse_node --serve --dev /dev/ttyUSB0
```

On start it prints the **station public key** — publish that once so the mesh can *pin* your lighthouse
and verify its broadcasts offline forever.

## How a reader trusts what the mesh hands them

Every reply is signed with the station's Ed25519 key. Any node verifies it **offline**, in three honest
states (never collapsed into a false yes/no):

| State | Means |
|---|---|
| **UNALTERED** | the body's `nhm1:` content hash still matches — it was not tampered with (no key needed) |
| **SIGNED** | the Ed25519 signature checks against the carried key — not altered after signing |
| **AUTHENTIC** | SIGNED **and** the key is the one you *pinned* for this lighthouse |

A valid signature from an *unpinned* station is SIGNED but never AUTHENTIC — it proves the body wasn't
altered, not *who* sent it. Pin the station key once and you get the strong claim.

## What the node will and won't do

- **Crisis first.** A cry for help is answered with real-person help (988, findahelpline.com, "tell a
  friend, a pastor, a doctor") *immediately* — it never depends on a lookup succeeding.
- **Verified keeping, or an honest miss.** A checkable question is answered from a card that carries its
  own re-checkable ref. If nothing in the corpus is genuinely relevant, the node says so — **a gap stays
  a gap.** It never fabricates an answer. No model, no oracle, no outbound call.
- **Sovereign.** It depends on none of our servers. Your node, your corpus slice, your key.

## Status — honest

- **Proven** (`python -m concordance.lighthouse_node`, plus `tests/test_lighthouse_node.py` and
  `tests/test_meshtastic_bridge.py`): the composer, the byte-budgeting, the signing, the chunking, and
  the offline verification — the full chain, in memory.
- **Field-test-pending:** the `serve()` transport is written to the Meshtastic `SerialInterface` + pubsub
  API but has not yet been run on a real radio. If you field-test it on your board, that is the last mile.

## Build on it

The wire format is the Fellowship Mesh's own (`nhm1:` content id + Ed25519), framed by
`concordance.meshtastic_bridge` (`to_wire` / `chunk` / `dechunk` / `verify_wire`). Any project can carry,
relay, or verify a Lighthouse broadcast without our code — the format is the contract, not our servers.
