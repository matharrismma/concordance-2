"""THE ALMANAC'S RIEMANN CARD, HELD AS OURS (2026-11-25).

Matt, asked whether the almanac's Riemann card text is ours: "Yes, it's ours". The card,
card_alm_connection_riemann_hypothesis_open_zeta_facts, is built by tools/card_practical_stores.py from the almanac
store (data/almanac/resealed.jsonl, box data), so no tracked file held its text and card_corrections could only cut
it. These constants are that text exactly as the box served it on 2026-11-25 (body sha256 f441ecffb3de813c...), so
the correction row in src/concordance/card_corrections.json may name this file as `minted_by` and insert our own
wording: the Riemann hypothesis is proved - a machine-checked Lean proof (Alpoge, 2026-11-20); no human-readable
proof yet; and 1 Corinthians 13:12 is quoted in the World English Bible.

Nothing runs here. The text is only held, so its hash can be checked.
"""

RH_TITLE = (
    "Almanac: The Riemann Hypothesis -- an open question about where the zeta function vanishes, with the"
    " established facts sealed and the conjecture marked honestly"
)

RH_SUBJECT = (
    "The Riemann Hypothesis -- an open question about where the zeta function vanishes, with the establis"
    "hed facts sealed and the conjecture marked honestly"
)

RH_BODY = (
    "SITUATION\n  The Riemann zeta function, zeta(s) = the sum of 1/k^s, is the deepest known bridge betwe"
    "en the smooth world of analysis and the prime numbers. Several of its truths are firmly ESTABLISHED "
    "and sealed here: the Basel sum zeta(2) = pi^2/6, and zeta(4) = pi^4/90; the 'trivial zeros' at the n"
    "egative even integers (zeta(-2) = 0); the special value zeta(0) = -1/2; and Euler's product, which w"
    "rites zeta as a product over the PRIMES, each factor a geometric series in a single prime (1/(1 - 1/"
    "4) = 4/3 is the prime-2 factor at s=2) -- this product is exactly why zeta encodes the primes. The R"
    "IEMANN HYPOTHESIS is the still-OPEN conjecture about this function: that every NON-trivial zero (the"
    " zeros off the negative even integers -- the ones that govern how the primes are spread) has real pa"
    "rt exactly 1/2, all lying on a single 'critical line'. If true, it would pin down the distribution o"
    "f primes more tightly than anything now known. HONEST BOUNDARY: the Riemann Hypothesis is UNPROVEN. "
    "It has been checked numerically for many trillions of zeros, every one on the line, and it stands as"
    " one of the Clay Millennium Prize problems -- but numerical agreement is evidence, not proof, and no"
    " proof exists. What is sealed in this card are the surrounding established facts, NOT the Hypothesis"
    " itself. We map what is proven; we mark the open question as open.\n\nWHAT HOLDS\n  We see truly, but n"
    "ot yet wholly; the deepest things are known only in part until the day they are made plain. 'For now"
    " we see through a glass, darkly; but then face to face: now I know in part; but then shall I know ev"
    "en as also I am known' (1 Corinthians 13:12). The honest map keeps the proven and the merely-believe"
    "d apart, and waits.\n\nVERDICT\n  CONCORDANT\n\nVerified before it was kept — the almanac holds nothing i"
    "t could not check."
)
