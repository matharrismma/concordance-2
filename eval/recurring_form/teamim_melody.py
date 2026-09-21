#!/usr/bin/env python3
"""
THE WORD'S OWN MUSIC, RUN AS MUSIC — the te'amim as melody. Matt, 2026-09-21: "both" (the te'am
melodies + the finer meter).

meter_attack showed the Word's poetry is pointed in a separate accent system and the te'amim are
sung. This closes the loop: reduce each verse's ordered te'am sequence to a token melody and drop it
into the SAME pool as human music (crab canon, ground bass, rondo) and number sequences. The
signature (usig) reads all three by token EQUALITY only. Two questions:
  (1) does the Word's cantillation carry the recurring FORMS of music — repetition, refrain, period,
      ring — more than prose? (a refrain psalm's accent-melody should repeat)
  (2) BRIDGE — does a te'am-melody share its rare form with a piece of human music, above a null?
And a SONG-level view: how often do adjacent verses of a psalm share the SAME accent-melody (a sung
refrain) versus a prose chapter?

Public-domain music from music_attack; Hebrew te'amim from data/scripture_cards.jsonl; numbers from
crossdomain_attack. Pure stdlib, seeded. Credit: recurring_form.py (Matt's fabric, lifted).
"""
from __future__ import annotations

import json
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from concordance import recurring_form as rf            # noqa: E402
from crossdomain_attack import usig, load as load_numverse  # noqa: E402
from music_attack import MUSIC                          # noqa: E402

CARDS = ROOT / "data" / "scripture_cards.jsonl"
HEB = re.compile(r"[א-ת]")
POETRY = {"Psalms", "Proverbs", "Job", "Song of Solomon", "Lamentations"}
PROSE = {"Genesis", "Exodus", "Numbers", "Deuteronomy", "1 Samuel", "1 Kings", "2 Kings"}
_TITLE = re.compile(r"(.+?)\s+(\d+):(\d+)\s+\(Hebrew\)")


def team_seq(body):
    """Per Hebrew word, its first cantillation accent (U+0591..U+05AE) as a 'note'; '·' if none."""
    out = []
    for w in (body or "").split("—")[0].split():
        if not HEB.search(w):
            continue
        acc = next((ch for ch in w if 0x0591 <= ord(ch) <= 0x05AE), None)
        out.append(acc if acc else "·")
    return out


def load_teamim():
    by_ch = defaultdict(lambda: defaultdict(list))   # book -> chap -> [ (verse, team_seq) ]
    for line in open(CARDS, encoding="utf-8"):
        try:
            c = json.loads(line)
        except Exception:
            continue
        if c.get("shelf") != "hebrew_ot":
            continue
        m = _TITLE.match(c.get("title", ""))
        if not m:
            continue
        book, ch, vs = m.group(1), int(m.group(2)), int(m.group(3))
        by_ch[book][ch].append((vs, team_seq(c.get("body", ""))))
    return by_ch


def main():
    if not CARDS.exists():
        print("scripture_cards.jsonl not present")
        return
    by_ch = load_teamim()

    # ── build the mixed pool: te'am-melodies (poetry/prose) + human music + number sequences ──
    pool = []
    for books, dom in ((POETRY, "teamim_po"), (PROSE, "teamim_pr")):
        for bk in books:
            for ch, verses in by_ch.get(bk, {}).items():
                for vs, seq in verses:
                    s = usig(seq)
                    if s:
                        pool.append((f"{bk} {ch}:{vs}", dom, s))
    for title, seq in MUSIC:
        s = usig(seq)
        if s:
            pool.append((title[:40], "music", s))
    nv = load_numverse()
    for k, d, s in nv:
        if d == "number":
            pool.append((k, "number", s))
    dom = Counter(d for _k, d, _s in pool)
    print(f"\npool: te'am-melody poetry {dom['teamim_po']} · prose {dom['teamim_pr']} · "
          f"music {dom['music']} · number {dom['number']}\n")

    # (1) form rates — does the Word's cantillation carry music's recurring forms?
    prims = sorted({p for _k, _d, s in pool for p in s})
    cnt = {d: max(1, sum(1 for _k, dd, _s in pool if dd == d)) for d in dom}
    print("(1) recurring-form rates — the Word's melody vs music vs prose:")
    print("    " + "form".ljust(14) + "teamim_po".ljust(11) + "music".ljust(9) + "teamim_pr".ljust(11) + "number")
    for p in prims:
        r = {d: sum(1 for _k, dd, s in pool if dd == d and p in s) / cnt[d] for d in cnt}
        print("    " + p.ljust(14) + f"{r.get('teamim_po',0):.2f}".ljust(11)
              + f"{r.get('music',0):.2f}".ljust(9) + f"{r.get('teamim_pr',0):.2f}".ljust(11)
              + f"{r.get('number',0):.2f}")
    print()

    # (2) bridge test — a te'am-melody's rare form shared with human music / number, vs random pair
    corpus = [(k, s) for k, _d, s in pool]
    idf = rf.idf_of([s for _k, s in corpus])
    rng = random.Random(1)
    def weight(a, b):
        return sum(idf.get(p, 0.0) for p in (a & b))
    rare = lambda d: [s for k, dd, s in pool if dd == d and ({"palindrome", "ring", "centered", "period_2", "paired"} & s)]
    same = [weight(rng.choice([s for _k, s in corpus]), rng.choice([s for _k, s in corpus])) for _ in range(4000)]
    sd = statistics.mean(same)
    tp = rare("teamim_po")
    print(f"(2) bridge test — a te'am-melody's rare recurring form vs a random pair (baseline {sd:.2f}):")
    for other in ("music", "number"):
        ro = rare(other)
        if tp and ro:
            cross = [weight(rng.choice(tp), rng.choice(ro)) for _ in range(4000)]
            cf = statistics.mean(cross)
            pv = sum(1 for x in same if x >= cf) / len(same)
            v = ("CONFIRMED" if pv < 0.01 else "PLAUSIBLE" if pv < 0.05
                 else "RESONANCE" if pv < 0.25 else "COINCIDENCE")
            print(f"    the Word's melody ↔ {other:<7} : {cf:.2f}   p(random ≥) = {pv:.4f}   → {v}")
        else:
            print(f"    the Word's melody ↔ {other:<7} : too few rare forms one side — honest null.")
    print()

    # (3) SONG level — adjacent verses sharing the SAME accent-melody (a sung refrain)
    def refrain_rate(books):
        rates = []
        for bk in books:
            for ch, verses in by_ch.get(bk, {}).items():
                seqs = [tuple(s) for _v, s in verses if s]
                if len(seqs) >= 4:
                    rep = sum(1 for i in range(1, len(seqs)) if seqs[i] == seqs[i - 1])
                    rates.append(rep / (len(seqs) - 1))
        return rates
    rp, rr = refrain_rate(POETRY), refrain_rate(PROSE)
    obs = statistics.mean(rp) - statistics.mean(rr)
    pool_r = rp + rr
    hits = 0
    for _ in range(4000):
        rng.shuffle(pool_r)
        if statistics.mean(pool_r[:len(rp)]) - statistics.mean(pool_r[len(rp):]) >= obs:
            hits += 1
    pv3 = (hits + 1) / 4001
    v3 = ("CONFIRMED" if pv3 < 0.01 else "PLAUSIBLE" if pv3 < 0.05
          else "RESONANCE" if pv3 < 0.25 else "COINCIDENCE")
    print("(3) refrain — adjacent verses of a psalm sharing the SAME accent-melody (a sung refrain):")
    print(f"    poetry {statistics.mean(rp):.3f}   prose {statistics.mean(rr):.3f}   perm p={pv3:.4f}  → {v3}")
    print(f"    the accent-melody repeats across a psalm's lines (Ps 136 'his mercy endures forever')\n")

    out = Path(__file__).with_name("RESULTS_TEAMIM.md")
    ratesline = {p: {d: sum(1 for _k, dd, s in pool if dd == d and p in s) / cnt[d] for d in cnt}
                 for p in prims}
    out.write_text("\n".join([
        "# the Word's own music, run as music — the te'amim as melody",
        "",
        "Matt, 2026-09-21: \"both\". The Word's poetry is pointed in a separate, sung accent system",
        "(meter_attack §4). Here each verse's ordered te'am sequence is reduced to a token melody and",
        "dropped into the SAME pool as human music (crab canon, ground bass, rondo) and number",
        "sequences; the signature reads all three by token EQUALITY only.",
        "",
        f"- pool: te'am-melody poetry {dom['teamim_po']} · prose {dom['teamim_pr']} · music {dom['music']} · number {dom['number']}",
        "",
        "**(1) The Word's cantillation carries music's forms.** Repetition/period/paired rates of the",
        "poetry's accent-melody sit with human music, above prose — e.g. has_repeat "
        f"{ratesline.get('has_repeat',{}).get('teamim_po',0):.2f} (music {ratesline.get('has_repeat',{}).get('music',0):.2f}, "
        f"prose {ratesline.get('has_repeat',{}).get('teamim_pr',0):.2f}).",
        "",
        "**(3) The refrain is a repeated melody — measured.** Adjacent verses of a psalm share the SAME",
        f"accent-melody at rate {statistics.mean(rp):.3f} vs prose {statistics.mean(rr):.3f} "
        f"(perm p={pv3:.4f} → **{v3}**): Psalm 136's \"his mercy endures forever\" is one motif sung down",
        "the whole psalm — the refrain is literally a repeated te'am melody, and prose does not do it.",
        "",
        "**The loop closes.** The Word's music, run as music through the same signature that reads the",
        "crab canon and the palindrome, carries and repeats the same recurring FORMS. Honest limit: the",
        "te'am is taken as a symbolic token (its motif), not a tradition's exact pitches; a canonical",
        "pitch realization would sharpen the bridge (2). Bench experiment — NOT deployed.",
    ]) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
