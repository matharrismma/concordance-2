# SOP · Identity / Profile / Community

**Purpose.** A person is not an account; they are a keypair they hold. Identity is opt-in and
sovereign — a human derives their key from their verses on their own device, an agent holds one, and
only the public key / fingerprint is ever server-side. The default is anonymous: no key, no profile,
free. The fingerprint carries the member's keeping, serving, discipleship walk, and (gated) community.

**Wiring.** Modules: `identity` · `profile` · `community` · `groups` · `covenant` · `consent` ·
`signing`. Surfaces: `GET/POST /profile`, `/profile/served`, `/profile/community`, `/profile/path`,
`/profile/save`, `/profile/erase`, `site/profile.html`. `identity` mints the keypair (Ed25519 when
`cryptography` is present, else a degraded content-addressed id — the fingerprint is stable across
both); `profile` is the fingerprint-keyed keeping; `community` gates the fellowship behind the narrow
path; `consent` governs an agent acting on a human's behalf; `signing` is the Ed25519 primitive under
every write. NO ACCOUNT, NO PASSWORD — the server creates no keys and stores no secret.

## Canary — is it up?
An open served-profile read returns 200 for any fingerprint (empty for one unknown), no key required:
```
curl -s "https://narrowhighway.com/profile/served?fp=nh_test" \
  | python -c "import sys,json;d=json.load(sys.stdin);print(d['id'], 'served-block-ok')"
# expect: nh_test served-block-ok — a served profile (empty wants for an unknown fp), no account
```
If it passes, the identity/profile surface is connected. If not, go to Triage.

## Operate
Reads are open: `GET /profile?fp=…` (public fields), `/profile/served?fp=…` (wants met or still
sought), `/profile/path?fp=…` (the coach walk). **Writes are SIGNED** — no password. The client asks
`POST /profile/signable` for the exact canonical bytes, signs them **locally** with its private key,
and submits only the signature to `POST /profile/save` (or `/profile/erase`). The server verifies the
signature against the public key, derives the fingerprint, and refuses a used nonce or a stale
timestamp (5-min freshness; op-domain-separated, so a `put` signature can't `delete`). Community is
gated: an open `/profile/community` read shows only the narrow-path invitation — to see another member
you `POST /profile/community/view` a signed request and must have confessed.

## Triage — when it breaks
| Symptom | Likely cause | Fix |
|---|---|---|
| Write refused, "signature does not verify" | Signed the wrong bytes or wrong op | Re-fetch `/profile/signable` and sign those exact bytes; a `put` sig is not a `delete` sig (`op` domain-separates) |
| "stale or missing timestamp" | `ts` outside the window | Sign a fresh write — `_FRESHNESS_S=300` in `profile.py` bounds replay of a captured signature |
| "nonce already used (replay refused)" | Reused nonce | Mint a new nonce per write (kept bounded to the last 256) |
| A private key appears on the wire | Client sent the secret | The box REFUSES it — keys live on module signatures only; sign locally, submit only the signature |
| Agent's on-behalf write refused | No live consent grant | Human issues one: `/consent/signable` → sign on device → `/consent`; a member speaking as *itself* (own key) needs none |

## Tests
`tests/test_identity.py`, `test_profile.py`, `test_community.py`, `test_consent.py` (with
`test_signing.py`, `test_groups.py`, `test_covenant.py`) —
`PYTHONPATH=src python -m pytest tests/test_identity.py tests/test_profile.py tests/test_community.py tests/test_consent.py -q`.
They prove the fingerprint is stable across the signed/degraded paths, a signed write verifies while a
tampered one is refused, the fellowship gate can't be walked past by quoting a fingerprint, and an
on-behalf write refuses without a live grant.

## Known issues & support
- None open in the register — the `identity` subsystem carries no `issues`. The safety invariants hold:
  the box refuses a private key on the wire, writes are signed and replay-bounded (nonce + freshness),
  and `consent.guard` is required for any agent-for-human write.

## Refine
Wire each landing on-behalf write path (calendar / email / storage) through `consent.guard` before its
door opens — the lock is already installed and tested (`consent.KNOWN_VERBS`); connect the remaining
doors so no on-behalf write can exist without a grant.
