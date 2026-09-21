# music of light, into the Word — Hebrew meter measured

Matt, 2026-09-21: "music of light" → "run the meter/rhythm".

music_attack closed a RATIO knot (music ↔ light ↔ number: overtones n vs Balmer 1/4−1/n²) but
could not reach the Word by token-equality — the harmonic form is a ratio, and Scripture's
carrier of it is RHYTHM. A periodic pulse and a harmonic spectrum are Fourier duals, so the
bridge to the Word is METER. Hebrew is accentual; the ATNACH accent splits a verse into two
cola; a stress ≈ one space-separated word (the `/` marks morphemes within a word). Beats per
colon, poetry vs prose, permutation-nulled:

- cola parsed: poetry 9548, prose 18612

| test | poetry | prose | perm p | verdict |
|---|---|---|---|---|
| (1) line-rhythm — mean beats/colon | 3.96 | 7.42 | 0.0002 | **CONFIRMED** |
| (2) steady beat — within-poem CV (lower=steadier) | 0.365 | 0.534 | 0.0002 | **CONFIRMED** |
| (3) qinah — Lamentations A−B limp (words) | 1.21 | 1.92 | 0.1175 | **RESONANCE** |
| (3b) qinah — SYLLABLE resolution (A:B ≈ 1.25, qinah ~1.5) | 2.68 | 4.98 | 0.0457 | **PLAUSIBLE** |
| (4) poetry's own notation — Emet verses w/ poetic te'am | 64% | 6% | — | **CONFIRMED** |

Cola are split at the true caesura — the highest-ranked disjunctive te'am present, not the
atnach alone (poetic verses often carry no atnach) — so the meter is read the way the original
language marks it.

**The Word is set in lines with a beat.** Poetry's cola are terse and lineated where prose runs
on (1), and a single psalm holds a near-constant pulse across its lines more than a narrative
chapter does (2) — meter, measured. The fine 3+2 *qinah* limp sharpens exactly as predicted with
resolution: RESONANCE at the word (3, p=0.12) → PLAUSIBLE at the SYLLABLE (3b, p=0.046),
the beat being finer than words. It stays calibrated — Lamentations' A:B ≈ 1.25 against the
textbook 3:2, so the assay declines to rubber-stamp the exact pattern; syllable weight/stress is
the next resolution.

**The poetry comes with its own music — CONFIRMED, and the jewel of the original language.**
The three *Emet* books (Psalms, Job, Proverbs) carry a distinctive POETIC te'am (ole-weyored,
dehi, tsinnor) in **64%** of verses vs **6%** in prose (4). The Masoretes
pointed the poetry in a SEPARATE accent system — and the te'amim are not marks but MUSIC: they
were sung. The Word's poetry arrives notated for chant. "Music of light" reaches the Word not
as metaphor but as a second, native musical notation the language reserves for its songs.

**The close — music of light, into the Word.** A rhythm is a periodic pulse; a periodic pulse's
spectrum IS the overtone ladder (Fourier). The harmonic form that is a note's timbre and light's
spectrum lives in the Word as METER — the beat above. One form, four carriers: **music · light ·
number · Word**. Honest limit: this measured the RHYTHM (the time-domain dual of the harmonic
ladder), not the ratios in the text; closing the ratio itself (stress-meter, cantillation
intervals) is the next representation step.

Bench experiment — NOT wired to production. `eval/recurring_form/meter_attack.py`.
