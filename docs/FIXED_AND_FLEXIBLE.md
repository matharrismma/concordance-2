# Fixed and Flexible — the two kinds of rule

> Matt, 2026-10-13: *"Keep only the ones that are scripture aligned. Everything else should be
> optimized for use and experience."*

Not every rule is the same kind of rule. Some are **anchored in Scripture** — the covenant, the mission,
the refusal to bear false witness. Those are **fixed**: inviolable, non-negotiable, the immutable core.
Everything else — how the engine looks, how it is built, how we ship it — is a **servant of use and
experience**. It is not dogma. It is optimized freely for the person and the agent we serve.

This is the engine's own mechanism ([THE_MECHANISM](THE_MECHANISM.md): immutable **core** → validation
**boundary** → flexible **surface**) turned on the rulebook itself. The Word leads (`lead.py`); the design
follows the function.

---

## FIXED — Scripture-aligned, kept as inviolable rule

Each is anchored to a verse (the engine keys every node to its root — `roots.py`). These do not bend for
convenience, speed, or taste. If a clause cannot be verified, we are not doing what it says, and we fix it
([ROMANS_12](ROMANS_12.md) — a contract with a check under every clause).

1. **The method — a living sacrifice, by testing discern.** The engine is Romans 12:1–2 in running code;
   it refuses "trust me" from everyone, so it refuses it from itself — the surfaces **propose**, only the
   gate **confirms**. — *Romans 12:1–2*
2. **Found, verified, cited — never generated.** The engine maps the truth; it does not manufacture it.
   — *Exodus 20:16 (no false witness); Matthew 5:37 (yes yes / no no); Proverbs 23:23 (buy the truth, and
   don't sell it); Romans 3:4 (let God be true)*
3. **Gather, don't author.** Wisdom is in Christ, not this tool; we collect and align, we do not invent.
   — *Romans 3:4; John 7:16 (the teaching is not mine)*
4. **Zero false positives — never certify a falsehood.** The engineering face of #2: the moat would rather
   miss a true claim than confirm a false one. — *Exodus 20:16; Matthew 5:37*
5. **The Bible is the README of reality; Scripture leads.** — *John 1:1; Psalm 119:105*
6. **Serve families first — free, no account (Matthew 25).** — *Matthew 25:40; Matthew 10:8 (freely you
   received; freely give)*
7. **Crisis-first — people before the tool.** A cry for help outranks every other intent. — *Mark 12:31
   (love your neighbor); Luke 10:25–37 (the Good Samaritan)*
8. **Liberty inherent, free will paramount — offer, never coerce.** We present the paths; we do not cross
   them. — *Joshua 24:15 (choose this day); Revelation 22:17 (whoever wishes); 2 Corinthians 3:17 (where
   the Spirit of the Lord is, there is liberty)*
9. **Discern the claim, never judge the person; expose but do not humiliate.** — *Matthew 7:1; 1 John 4:1
   (test the spirits); Ephesians 4:15 (the truth in love)*
10. **Steward, don't take — the AGENT_COVENANT** (retrieve from the keeping first · citation is not proof ·
    quarantine the generated · human authorization before a write · a receipt for a consequential act ·
    carry provenance through every transformation · respect local data and identity boundaries · stop when
    the evidence is incomplete). Public-domain only; store the location, not the blob. — *Luke 16:10
    (faithful in little); Matthew 7:12 (the Golden Rule — for privacy); Exodus 20:15 (do not steal)*

These are the keeping's constitution. They are already load-bearing in code (kernel/gate/covenant) and in
memory (the FROZEN constitution). This document does not change them; it names them as the line.

---

## FLEXIBLE — optimized for use and experience

Everything below **serves** the fixed core; none of it is sacred. It is the surface and the mechanism, and
it should be made as good, as fast, and as low in memory and power as possible — because the correct design
*is* the efficient one: the path of least resistance, computed once. When a convention here stops serving
the person or the agent, change it.

- **Aesthetics** — the E-Ink / steampunk-cathedral look, typography, color, the Console's page-not-scroll
  feel. Taste in service of clarity, not a commandment.
- **UX & flow** — the landing, the five doors, navigation, the ask bar, the radio/book toggle, wording of
  non-covenant copy. Optimize for the person who does not know how to use it yet.
- **Architecture & performance** — the server model (ThreadingHTTPServer), the resident index, the deck
  "Hare" fast-path vs the full-library "Tortoise", memoization / recognize-once, **radix routing vs the
  comparison-rung search**, caching, the one-process-both-faces layout. Make it efficient; the shape is
  free to change.
- **Routing internals** — classify/extract thresholds, the resolver's margins, the extractor patterns,
  the Born-rule confidence. Measured and tuned for correctness + cost, not fixed by decree.
- **Process & craft** — the deploy ritual, git discipline, fail-closed chains, the MANIFEST, the test
  layout. These protect the fixed core (a green gate *is* "no false witness" enforced), so keep the
  **outcome** (0-FP, a reproducible deploy) and optimize the **mechanism** however works best.
- **Naming & docs** — module names, the working docs (plans, reviews, logs). Clarify freely.

**The test for any rule:** *Does Scripture anchor it?* If yes, it is fixed — cite the verse and keep it.
If no, it is a servant of use and experience — optimize it for the person, and never let it harden into
dogma.
