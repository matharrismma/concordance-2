# THE TICK STICK — inferring an open shape from the marks you can reach

Matt, 2026-10-05: *"We build a tick stick. A tool that allows us to infer closer and closer."*

A joiner fitting a board to a crooked wall does not guess the wall. He lays a stick against it, makes a tick at
every point he can reach, and the shape is inferred from the ticks — exact where there is a tick, honest about
the gap between ticks. Nothing is drawn past the last mark.

The engine does the same for an OPEN QUESTION. A Millennium problem asks for a proof, and this engine does not
author proofs (FOUNDATION.md: found, never generated). What it can do is make marks it can stand behind and say
exactly what they establish:

| tick kind   | what it is                                                        | what it needs                    |
|-------------|-------------------------------------------------------------------|----------------------------------|
| bound       | a sealed verification up to a height / size / count               | the ledger seal (HOLDS), `up_to` |
| instance    | a sealed verification of one case                                 | the ledger seal                  |
| witness     | a sealed computation that exhibits something                      | the ledger seal                  |
| equivalence | a cited theorem: this statement ⇔ that one                        | the source                       |
| exclusion   | a cited barrier: proofs of this kind cannot settle the question   | the source                       |
| note        | a remark by a named author (never counts toward the fit)          | —                                |

**The fit** is computed from the ticks and nothing else: the greatest sealed bound, the sealed instances, the cited
equivalences and exclusions, and the open remainder ("beyond T = 200: not verified here"). A bound only ever goes
further (the ratchet). The fit never says the question is settled.

## The doors

    GET  /sticks                      every stick: question, ticks, verified-up-to, excluded, open
    GET  /stick?id=stick_…            one stick with its ticks and fit
    POST /stick  {question, statement, field, references}
    POST /tick   {stick, kind, claim, seal | source, up_to, unit, by}

A sealed tick is refused unless `seal` is the content hash of a HOLDS verification already in this node's keeping:
verify first through POST /verify (or `tools/tick.py`), then tick. A cited tick is refused without a source.
Sticks live in `data/sticks.jsonl` and ride with the node sync (Gen 3 · 1), so every node holds the same marks.

## The first stick: the Riemann hypothesis

`number_theory.critical_line` counts the zeros of ζ two independent ways and requires them to agree: the zeros
found ON the critical line (sign changes of Hardy's Z(t)) and the zeros IN the strip (Backlund's argument-principle
count N(T) = θ(T)/π + 1 + S(T), with S(T) followed continuously from σ = 2 to ½). When both equal the claim, every
zero up to T lies on the line — verified to that height, re-checkable by anyone, and no more than that. This is the
method of every published verification; ours is small next to the records and entirely sealed.

    PYTHONPATH=src python tools/tick.py riemann 200      # verify to T = 200, seal it, tick the stick

A P versus NP stick carries the barriers as cited exclusions (relativization — Baker, Gill, Solovay 1975; natural
proofs — Razborov, Rudich 1997; algebrization — Aaronson, Wigderson 2009): an attempt that does not pass them is
not an attempt. The stick is the map of the territory, which is what a human attempt needs, and the honest
referee for one.
