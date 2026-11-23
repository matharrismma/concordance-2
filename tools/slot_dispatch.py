"""A TOOL PER SLOT, AND A LANGUAGE THAT SAYS WHICH TOOL — tested on the keeping.

Matt, 2026-11-23: "You need a tool for each task to render what fits in that slot. You need a
language that communicates what goes where."

Code_Score.py already IS that design, and its demo is the proof:
    zlib -9 on a 39,930-byte triangle list ... 8,410 bytes
    score + zlib ............................ 422 bytes
    the grid generator (GR1) ................. 5 bytes
A 1,682x spread between the general compressor and the right renderer. The language is the 3-byte
tag -- GR1 / SC1 / ZL1 -- and `restore(frame)` dispatches on it while `min(choices, key=len)` holds
a competition and lets the winner take the slot.

WHY THIS RUN EXISTS. Yesterday I measured "remove constant keys" (1.95x) against gzip (14.96x) and
concluded a generator is not a size argument here. The comparison was wrong: constant-key removal is
not a renderer, it is one trick. The real question is whether a COMPETITION OF RENDERERS, dispatched
per class, beats one global compressor. That is what this measures.

FAIRNESS, stated up front. A columnar renderer preserves the DATA, not the byte order of the original
file. Comparing it against gzip-on-raw-bytes would be comparing a lossy-to-bytes method against a
lossless one. So every card is first CANONICALISED to compact JSON with sorted keys, and every
renderer -- gzip included -- must reproduce those canonical bytes exactly. Round trip is asserted for
each renderer on every class; a renderer that cannot rebuild its slot is disqualified, not scored.
"""
import gzip
import io
import json
import itertools
import os
import sys
from collections import defaultdict

# Code_Score.py is the OWNER'S OWN FILE and is deliberately NOT committed to this public repo.
# Point CODE_SCORE_DIR at the directory holding it, e.g.
#     CODE_SCORE_DIR=/path/to/dir python tools/slot_dispatch.py
_CS = os.environ.get("CODE_SCORE_DIR")
if not _CS or not os.path.isfile(os.path.join(_CS, "Code_Score.py")):
    sys.exit("set CODE_SCORE_DIR to the directory containing Code_Score.py "
             "(it is not in this repo on purpose)")
sys.path.insert(0, _CS)
import Code_Score                                    # noqa: E402

PATH = os.path.join("data", "source_cards.jsonl")
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 120000
MIN_CARDS = 500


def canon(d):
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def klass(cid):
    out = []
    for p in cid.split("_"):
        if p.isdigit() or (len(p) > 6 and any(c.isdigit() for c in p)):
            break
        out.append(p)
    return "_".join(out) or cid


def u(n):
    return Code_Score.number(n)


# ---------------------------------------------------------------- renderers
def r_zl1(cards):
    """ZL1 - the baseline: gzip the canonical lines, knows nothing."""
    blob = b"".join(canon(d) + b"\n" for d in cards)
    return b"ZL1" + gzip.compress(blob, 9)


def p_zl1(frame):
    blob = gzip.decompress(frame[3:])
    return [json.loads(l) for l in blob.splitlines()]


def _columns(cards):
    keys = sorted({k for d in cards for k in d})
    const, vary = {}, []
    for k in keys:
        vals = {json.dumps(d.get(k), ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")) for d in cards}
        if len(vals) == 1 and all(k in d for d in cards):
            const[k] = json.loads(next(iter(vals)))
        else:
            vary.append(k)
    return const, vary


def r_cl1(cards):
    """CL1 - columnar: the class's constant keys ONCE, then each varying key as its own stream,
    so like sits beside like before the entropy coder ever sees it."""
    const, vary = _columns(cards)
    out = bytearray()
    head = json.dumps({"const": const, "vary": vary}, ensure_ascii=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")
    out += u(len(head)) + head + u(len(cards))
    for k in vary:
        col = bytearray()
        for d in cards:
            v = json.dumps(d[k], ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8") if k in d else b""
            col += u(len(v)) + v
        out += u(len(col)) + bytes(col)
    return b"CL1" + gzip.compress(bytes(out), 9)


def p_cl1(frame):
    f = io.BytesIO(gzip.decompress(frame[3:]))
    head = json.loads(f.read(Code_Score.take_number(f)).decode("utf-8"))
    n = Code_Score.take_number(f)
    const, vary = head["const"], head["vary"]
    cols = {}
    for k in vary:
        c = io.BytesIO(f.read(Code_Score.take_number(f)))
        vals = []
        for _ in range(n):
            ln = Code_Score.take_number(c)
            raw = c.read(ln)
            vals.append(None if ln == 0 else json.loads(raw.decode("utf-8")))
        cols[k] = vals
    out = []
    for i in range(n):
        d = dict(const)
        for k in vary:
            if cols[k][i] is not None:
                d[k] = cols[k][i]
        out.append(d)
    return out


def r_sc1(cards):
    """SC1 - Matt's arithmetic-motif encoder on the columnar form, then gzip. The columns put the
    numeric runs next to each other, which is the shape `encode` was built to find."""
    inner = r_cl1(cards)[3:]
    plain = gzip.decompress(inner)
    return b"SC1" + gzip.compress(Code_Score.encode(plain), 9)


def p_sc1(frame):
    plain = Code_Score.decode(gzip.decompress(frame[3:]))
    return p_cl1(b"CL1" + gzip.compress(plain, 1))


RENDERERS = [("ZL1", r_zl1, p_zl1), ("CL1", r_cl1, p_cl1), ("SC1", r_sc1, p_sc1)]


def main():
    by_class = defaultdict(list)
    n = 0
    with open(PATH, encoding="utf-8") as f:
        for line in itertools.islice(f, LIMIT):
            d = json.loads(line)
            by_class[klass(str(d.get("id") or ""))].append(d)
            n += 1
    classes = [(c, v) for c, v in by_class.items() if len(v) >= MIN_CARDS]
    classes.sort(key=lambda kv: -sum(len(canon(d)) for d in kv[1]))
    print("read %d cards from %s; %d classes at or above %d cards\n" % (n, PATH, len(classes), MIN_CARDS))

    print("=" * 100)
    print("A COMPETITION PER SLOT. Every renderer must rebuild the canonical cards exactly.")
    print("=" * 100)
    print("%-22s %7s %10s | %9s %9s %9s | %-4s %7s"
          % ("class", "cards", "canonical", "ZL1", "CL1", "SC1", "win", "vs ZL1"))
    print("-" * 100)
    if not classes:
        print("No class reaches the %d-card floor in this sample, so there is nothing to "
              "score. Below the floor, 'this key is constant' cannot be told from 'there "
              "is only one example' -- the artifact the floor exists to prevent." % MIN_CARDS)
        return
    tot_canon = tot_zl = tot_best = 0
    tags = []
    for c, cards in classes:
        base = sum(len(canon(d)) for d in cards)
        sizes = {}
        for tag, enc, dec in RENDERERS:
            try:
                frame = enc(cards)
                if dec(frame) != cards:          # the only thing that makes a size meaningful
                    sizes[tag] = None
                    continue
                sizes[tag] = len(frame)
            except Exception as e:               # noqa: BLE001 - disqualify, never score
                sizes[tag] = None
                if os.environ.get("SLOT_DEBUG"):
                    print("   ! %s/%s %s: %s" % (c, tag, type(e).__name__, e))
        ok = {k: v for k, v in sizes.items() if v}
        win = min(ok, key=ok.get)
        tot_canon += base
        tot_zl += sizes["ZL1"] or 0
        tot_best += ok[win]
        tags.append(win)
        fmt = lambda t: ("%9d" % sizes[t]) if sizes[t] else "      DISQ"   # noqa: E731
        print("%-22s %7d %10d | %s %s %s | %-4s %6.2fx"
              % (c[:22], len(cards), base, fmt("ZL1"), fmt("CL1"), fmt("SC1"),
                 win, (sizes["ZL1"] or 0) / ok[win]))
    print("-" * 100)
    print("%-22s %7s %10d | %9d %9s %9s | %-4s %6.2fx"
          % ("TOTAL", "", tot_canon, tot_zl, "", "", "mixed", tot_zl / tot_best))
    print("\nONE GLOBAL COMPRESSOR vs PER-SLOT DISPATCH, same canonical bytes:")
    print("   gzip -9, whole sample as one stream ...... %10d" % tot_zl)
    print("   per-class winner + 3-byte tag ............ %10d   = %.2fx better"
          % (tot_best, tot_zl / tot_best))
    print("   canonical source ......................... %10d" % tot_canon)
    print("   dispatch total ratio ..................... %.2fx" % (tot_canon / tot_best))
    print("\nthe language that says what goes where, for these slots: %s" % " ".join(tags))
    if len(set(tags)) == 1:
        print("ALL ONE TAG -- on THIS data the competition has a single winner, so dispatch buys")
        print("the margin above but not yet variety. A slot with a true generator (Matt's GR1, 5")
        print("bytes for a whole mesh) is what makes the registry pay; no card class here is a")
        print("closed-form enumeration, which is the honest limit of this result.")


if __name__ == "__main__":
    main()
