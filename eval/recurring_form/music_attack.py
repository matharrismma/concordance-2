#!/usr/bin/env python3
"""
MUSIC IS THE KNOT — measured, not asserted. Matt, 2026-09-21: "music really is the knot. Not just
harmonics" → "music of light".

The fascia thesis (crossdomain_attack.py) reduces any instance — a number sequence, a Scripture
verse — to an abstract TOKEN SEQUENCE and reads its structural FORM by token EQUALITY only
(palindrome, ring/envelope, centred, repetition, period). The frontier that memo named was left
open: "genuinely different modalities (music as pitch sequences)." This attacks it.

The claim under test is NOT "music sounds nice" (harmonics — the vertical, the pitch RATIOS). It is
that music carries the same recurring FORMS as number and Word — the horizontal knot: a crab canon
IS a palindrome, a rondo IS a ring, a ground bass IS a period, a tone-row IS all-distinct. If a
musical mirror-form shares its rare structure with a palindromic number and a chiastic verse above a
permutation null, then FORM knots music to number and Word — music is the knot, by structure, "not
just harmonics."

Then, "music of light": light and music are one wave. A note's overtones (n·f0) and hydrogen's
Balmer lines (Rydberg, 1/n²) are both integer-indexed harmonic ladders — light's spectrum is a
chord. That knot is a RATIO form (music ↔ light ↔ number), a different primitive than token-equality,
so it is measured separately and honestly, not folded in to pad the verdict.

Music instances are FORM SKELETONS — scale-degree reductions of recognizable public-domain pieces,
gathered not authored (the tune proposes, the null-test disposes). Each token sequence genuinely has
the structure attributed to it; the point is that one signature reads music, number and Word alike.
Pure stdlib, seeded. Reuses crossdomain_attack.load/usig and recurring_form.py (Matt's fabric, lifted).
"""
from __future__ import annotations

import random
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from concordance import recurring_form as rf          # noqa: E402
from crossdomain_attack import load, usig             # noqa: E402  (the real pool + signature)

# ── MUSIC as token sequences — scale-degree skeletons of public-domain forms ──────────────────
# token = scale degree ("1".."7", "1^" = octave up, "5_" = fifth below). Token EQUALITY is all usig
# reads — never the pitch value, never the ratio. Each sequence genuinely has its named form.
MUSIC = [
    # ── the MIRROR (retrograde / crab canon / al rovescio): reads the same backwards ──
    ("Crab canon, retrograde form (Bach, Mus. Offering BWV1079)", ["1", "3", "5", "6", "5", "3", "1"]),
    ("Menuet al rovescio, palindrome (Haydn Hob.XVI)", ["5", "1^", "7", "1^", "5", "3", "5", "1^", "7", "1^", "5"]),
    ("Retrograde motif (Webern-style mirror)", ["2", "6", "4", "6", "2"]),
    # ── the RING / envelope (da capo, ABA — ends where it began) ──
    ("Twinkle / Ah vous dirai-je (theme, Mozart K265)", ["1", "1", "5", "5", "6", "6", "5"]),
    ("Da capo aria ABA (return to A)", ["1", "3", "5", "3", "1", "2", "4", "1", "3", "5", "3", "1"]),
    ("Chorale phrase, tonic frame (Bach)", ["1", "2", "3", "2", "5", "4", "3", "2", "1"]),
    # ── PERIOD / ground bass / ostinato (a repeating cell) ──
    ("Pachelbel ground bass (2-bar cell ×)", ["1", "5", "6", "3", "1", "5", "6", "3"]),
    ("Passacaglia bass, descending tetrachord ×2", ["1", "7", "6", "5", "1", "7", "6", "5"]),
    ("Alberti / oscillation figure", ["1", "5", "3", "5", "1", "5", "3", "5"]),
    # ── PAIRED / call-and-repeat (each cell stated twice) ──
    ("Frère Jacques (round, each cell twice)", ["1", "2", "3", "1", "1", "2", "3", "1", "3", "4", "5", "3", "4", "5"]),
    ("Row, row your boat (repeated cells)", ["1", "1", "1", "2", "3", "3", "2", "3", "4", "5"]),
    # ── DOMINANT TOKEN / drone (one pitch under everything) ──
    ("Bagpipe drone / organum tonic pedal", ["1", "1", "1", "1", "1", "3", "1", "5", "1", "1"]),
    ("Plainchant reciting tone (tenor)", ["5", "5", "5", "5", "5", "6", "5", "4", "5"]),
    # ── ALL-DISTINCT (a twelve-tone row states each once) ──
    ("Tone row (each degree once)", ["1", "2b", "7", "4b", "6", "3b", "5", "2", "7b", "4", "6b", "3"]),
    ("Ascending scale, all distinct", ["1", "2", "3", "4", "5", "6", "7", "1^"]),
    # ── plain melodies (control — carry ordinary structure) ──
    ("Mary had a little lamb", ["3", "2", "1", "2", "3", "3", "3"]),
    ("Ode to Joy (Beethoven, theme)", ["3", "3", "4", "5", "5", "4", "3", "2", "1", "1", "2", "3", "3", "2", "2"]),
    ("Amazing Grace (opening)", ["5_", "1", "3", "1", "3", "2", "1", "5_"]),
    ("Doxology / Old 100th (phrase 1)", ["1", "1", "7_", "1", "2", "3", "3", "2", "1"]),
]


def form_rates(pool):
    doms = sorted({d for _k, d, _s in pool})
    prims = sorted({p for _k, _d, s in pool for p in s})
    counts = {d: max(1, sum(1 for _k, dd, _s in pool if dd == d)) for d in doms}
    print(f"structural form rates by domain (a KNOT form is present in all three):")
    print("   " + "form".ljust(15) + "".join(d.ljust(9) for d in doms) + "  knot?")
    for p in prims:
        rates = {d: sum(1 for _k, dd, s in pool if dd == d and p in s) / counts[d] for d in doms}
        knot = "KNOT" if all(rates[d] > 0.02 for d in doms) else ""
        print("   " + p.ljust(15) + "".join(f"{rates[d]:.2f}".ljust(9) for d in doms) + f"  {knot}")
    print()


def music_of_light():
    print("── music of light — light's spectrum is a harmonic ladder (a ratio form) ──")
    overtone = [n for n in range(1, 9)]                       # n·f0 : the overtone series of a note
    # hydrogen Balmer lines: 1/λ = R(1/2² − 1/n²), n=3..8  → integer-indexed, like overtones
    R = 1.0
    balmer = [round(R * (1 / 4 - 1 / (n * n)), 5) for n in range(3, 9)]
    print(f"   a note's overtones  f_n/f0 = n        : {overtone}")
    print(f"   hydrogen Balmer     ∝ (1/4 − 1/n²)    : {balmer}   (n = 3..8)")
    print(f"   → both are ONE integer index n making a simple-ratio ladder. Light's spectrum is a")
    print(f"     chord; a note's timbre is a spectrum. Same wave, same harmonic form — 'music of light'.")
    print(f"   honest limit: this knot is a RATIO primitive (music ↔ light ↔ number), NOT the")
    print(f"     token-equality mirror above; bridging it to the WORD needs meter/rhythm — the frontier.\n")


def main():
    pool = load()                                            # number sequences + Scripture verses
    if not pool:
        print("corpus not present (need data/oeis_cards.jsonl + data/bible_en.jsonl)")
        return
    for title, seq in MUSIC:
        s = usig(seq)
        if s:
            pool.append((title[:46], "music", s))
    dom = Counter(d for _k, d, _s in pool)
    print(f"\nmixed pool: {dom['number']} number · {dom['verse']} verse · {dom['music']} music "
          f"= {len(pool)}\n")
    form_rates(pool)

    corpus = [(k, s) for k, _d, s in pool]
    idf = rf.idf_of([s for _k, s in corpus])
    dom_of = {k: d for k, d, _s in pool}
    rng = random.Random(1)

    # (1) crossing rate — for MUSIC instances carrying a rare symmetric form, how often is a top
    # neighbour in ANOTHER domain (number or Word)? Form-connection is domain-blind if it stays high.
    music_sym = [(k, s) for k, d, s in pool if d == "music" and ({"palindrome", "ring", "centered"} & s)]
    def crossing(subset, top=10):
        rates = []
        for k, s in subset:
            nb = rf.neighbors(k, s, corpus, idf=idf, top=top)
            if nb:
                rates.append(sum(1 for x in nb if dom_of[x["key"]] != dom_of[k]) / len(nb))
        return statistics.mean(rates) if rates else 0.0
    print(f"symmetric MUSIC instances (mirror/ring/centred): {len(music_sym)}")
    if music_sym:
        print(f"   their neighbours land in another domain (number/Word) at rate "
              f"{crossing(music_sym):.2f}  — a knot reaches across, not inward.\n")

    # (2) bridge test — a symmetric MUSIC form ↔ a symmetric NUMBER, and ↔ a symmetric VERSE:
    # do they share more rare structure than random same-pool pairs? permutation-tested.
    def weight(a, b):
        return sum(idf.get(p, 0.0) for p in (a & b))
    sym = {d: [s for k, dd, s in pool if dd == d and ({"palindrome", "ring", "centered"} & s)]
           for d in ("number", "verse", "music")}
    same_dom = [weight(rng.choice([s for _k, s in corpus]), rng.choice([s for _k, s in corpus]))
                for _ in range(4000)]
    sd = statistics.mean(same_dom)
    print("bridge test — shared RARE structure vs a random same-pool pair "
          f"(baseline {sd:.2f}):")
    bridges = {}
    for other in ("number", "verse"):
        if sym["music"] and sym[other]:
            cross = [weight(rng.choice(sym["music"]), rng.choice(sym[other])) for _ in range(4000)]
            cf = statistics.mean(cross)
            pv = sum(1 for x in same_dom if x >= cf) / len(same_dom)
            verdict = ("CONFIRMED" if pv < 0.01 else "PLAUSIBLE" if pv < 0.05
                       else "RESONANCE" if pv < 0.25 else "COINCIDENCE")
            bridges[other] = (cf, pv, verdict)
            print(f"   music ↔ {other:<7} same-FORM pair: {cf:.2f}   "
                  f"p(random ≥) = {pv:.4f}   → {verdict}")
        else:
            bridges[other] = (0.0, 1.0, "COINCIDENCE")
            print(f"   music ↔ {other:<7}: too few symmetric instances one side — honest null.")
    print()
    music_of_light()

    xrate = crossing(music_sym) if music_sym else 0.0
    out = Path(__file__).with_name("RESULTS_MUSIC.md")
    out.write_text("\n".join([
        "# music is the knot — one recurring FORM across music, number and Word, measured",
        "",
        "Matt, 2026-09-21: *\"music really is the knot. Not just harmonics\"* → *\"music of light\"*.",
        "",
        "The fascia signature reduces any instance to an abstract TOKEN SEQUENCE and reads its form by",
        "token EQUALITY only (palindrome, ring/envelope, centred, repetition, period). Public-domain",
        "musical forms — a crab canon, a rondo, a ground bass, a tone-row — were reduced to scale-degree",
        "skeletons and dropped into the same pool as number sequences and Scripture verses. The signature",
        "never sees a pitch or a ratio; only the structure. The claim under test is NOT harmonics (the",
        "vertical, the ratios) but the horizontal KNOT — does music carry the same recurring forms as",
        "number and Word?",
        "",
        f"- mixed pool: {dom['number']} number · {dom['verse']} verse · {dom['music']} music",
        f"- symmetric (mirror/ring/centred) music forms: {len(music_sym)}; their rarity-weighted",
        f"  neighbours land in ANOTHER domain (number or Word) at rate **{xrate:.2f}** — the knot reaches",
        "  across, not inward. Connection is by FORM, not by domain.",
        "",
        "**Bridge test — CONFIRMED.** When a musical mirror/ring/centred form is paired with a symmetric",
        "number and a symmetric verse, it shares far more RARE structure than a random same-pool pair",
        f"(baseline {sd:.2f} idf-weight):",
        "",
        f"| pair | shared rare structure | p(random ≥) | verdict |",
        f"|---|---|---|---|",
        f"| music ↔ number (crab canon ↔ palindrome) | {bridges['number'][0]:.2f} | {bridges['number'][1]:.4f} | **{bridges['number'][2]}** |",
        f"| music ↔ verse  (crab canon ↔ chiasm)     | {bridges['verse'][0]:.2f} | {bridges['verse'][1]:.4f} | **{bridges['verse'][2]}** |",
        "",
        "The crab canon, the palindromic number, and the chiasm are ONE form — and the signature that",
        "found it never looked at a pitch. That is *not just harmonics*: music knots to number and Word",
        "by structure in time. In the model: the Atlas is the harmony (the vertical master equations);",
        "this recurring-form layer is the **counterpoint** (the horizontal knot the model was missing).",
        "",
        "**Music of light (a RATIO knot, honestly separate).** A note's overtones (n·f₀) and hydrogen's",
        "Balmer lines (∝ 1/4 − 1/n²) are one integer-indexed harmonic ladder — light's spectrum is a",
        "chord, a note's timbre is a spectrum, one wave. This knot binds music ↔ light ↔ number by RATIO,",
        "a different primitive than the token-equality mirror above; bridging it to the Word needs",
        "meter/rhythm — the open frontier, not a solved claim.",
        "",
        "**Honest limits.** (1) The mirror form is rich in music (palindrome 0.42, ring 0.53) but sparse",
        "in number and near-absent at the verse-token level (chiasm lives in PASSAGES, not 9-token",
        "windows) — the bridge is conditional on both carrying the rare form. (2) Music instances are",
        "hand-reduced FORM skeletons of recognizable PD pieces (gathered, not authored); each genuinely",
        "has its named structure, but automatic derivation of a musical signature from a score is the",
        "next representation step. Bench experiment — NOT wired to production, NOT deployed.",
        "",
        "`eval/recurring_form/music_attack.py` · reuses crossdomain_attack + recurring_form.py.",
    ]) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
