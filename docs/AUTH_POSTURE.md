# Authentication Posture — stated, not implied (2026-08-04)

Task #127 (assessment F-02). The reviewer found "authentication ambiguity." The ambiguity ends
here; the posture is a DECISION, recorded:

**The read surface is deliberately anonymous-open.** Search, cards, Scripture, verification,
seals, the clock — no account, no key, no tracking. This is the mission, not an oversight: the
library serves families and machines that cannot or will not carry credentials (SERVE FAMILIES
FIRST; no sign-in by design; identity is opt-in Ed25519, born on the device).

**Writes pass the consent lock, not a login.** Anything that preserves or publishes
(`attest_record`, shelves, groups, the calendar pilot) requires a signed grant or consent
record — authorization by cryptographic consent, scoped and expiring, never by session cookie.
Private keys never cross the wire; the live box refuses any request carrying one.

**Rate limits are the abuse boundary** on the open surface (separate read/write buckets;
`/search` learned this the hard way when the shared cap refused ClaudeBot mid-crawl).

**Hosted multi-tenant deployment would require explicit client authentication** — that is a
future decision with its own threat model (assessment §5.4), and nothing in the current posture
should be mistaken for it. Until then: reads are open, writes are consented, and this file is
the statement the reviewer asked for.
