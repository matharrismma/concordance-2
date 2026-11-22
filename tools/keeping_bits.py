#!/usr/bin/env python3
"""How many BITS is each kind of card worth? The accounting behind docs/THE_PRICE_OF_THE_PRIOR.md.

The Large Text Compression Benchmark scores the compressed text PLUS the decoder and any offline
weights, so a prior must save more than it costs. Applied to a keeping, that rule yields two numbers
per card kind and one diagnostic:

    count / bytes            how much of the keeping this kind IS
    compress each card ALONE its own internal redundancy
    compress the kind TOGETHER   plus the redundancy BETWEEN cards
    ratio = alone / together     how much of the shelf is THE SAME CARD REPEATED

A kind whose cards compress far better together than alone is TEMPLATE: it carries one card's worth
of information wearing many cards' clothes. A kind near 1.0x carries distinct content per card. That
is a measurement of the inversion (docs/REMAINING.md), not an opinion about it.

zlib is a weak compressor and these bits/byte figures are NOT comparable to a neural compressor's on
a different corpus. They are comparable to EACH OTHER, which is the whole point: the comparison is
kind against kind, inside one keeping, with one compressor held fixed.

Reads the sources the engine reads -- cards.jsonl plus corpus.EXTRA_CARD_SOURCES, taken from
corpus.py rather than retyped. It does not boot the engine, build an index, or walk the corpus.
WRITES NOTHING.

    python tools/keeping_bits.py .
"""
import collections
import json
import re
import sys
import zlib
from pathlib import Path

CAP_PER_KIND = 4000          # cards per kind kept for the compression test, for a bounded run
MAXTEXT = 24 * 1024 * 1024   # and a byte ceiling on that sample
MIN_SAMPLE = 20              # below this a ratio is noise, so the kind is counted but not rated


def sources(root: Path):
    """The registered source list, read out of corpus.py so it cannot drift from the engine."""
    src = (root / "src" / "concordance" / "corpus.py").read_text(encoding="utf-8", errors="replace")
    i = src.index("EXTRA_CARD_SOURCES = (")
    j = src.index("\n)", i)
    return ["cards.jsonl"] + re.findall(r'"([a-z_0-9]+\.jsonl)"', src[i:j])


def main(root: Path):
    data = root / "data"
    names = sources(root)

    count = collections.Counter()
    nbytes = collections.Counter()
    sample = collections.defaultdict(list)
    sample_bytes = collections.Counter()
    missing = []

    for name in names:
        p = data / name
        if not p.exists():
            missing.append(name)
            continue
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line or line[0] != "{":
                    continue
                try:
                    c = json.loads(line)
                except Exception:
                    continue
                if not c.get("id"):
                    continue
                kind = c.get("kind") or "(none)"
                text = (c.get("title") or "") + "\n" + (c.get("body") or "")
                blob = text.encode("utf-8", "replace")
                count[kind] += 1
                nbytes[kind] += len(blob)
                if len(sample[kind]) < CAP_PER_KIND and sample_bytes[kind] < MAXTEXT:
                    sample[kind].append(blob)
                    sample_bytes[kind] += len(blob)

    cards = sum(count.values())
    total = sum(nbytes.values())
    print("sources read  : %d of %d (missing: %s)"
          % (len(names) - len(missing), len(names), ", ".join(missing) or "none"))
    print("cards         : %d" % cards)
    print("title+body    : %.1f MB" % (total / 1e6))
    print()

    print("%-17s %9s %8s %13s %8s %7s" %
          ("kind", "cards", "%cards", "bytes", "%bytes", "b/card"))
    print("-" * 67)
    for kind, n in count.most_common():
        b = nbytes[kind]
        print("%-17s %9d %7.2f%% %13d %7.2f%% %7d"
              % (kind, n, 100.0 * n / cards, b, 100.0 * b / total, b // max(1, n)))
    print()

    print("%-17s %7s %12s %10s %10s %8s  %s" %
          ("kind", "sample", "raw bytes", "alone", "together", "ratio", "verdict"))
    print("-" * 99)
    for kind, _ in count.most_common():
        blobs = sample.get(kind) or []
        if len(blobs) < MIN_SAMPLE:
            continue
        raw = sum(len(b) for b in blobs)
        if raw == 0:
            continue
        alone = sum(len(zlib.compress(b, 9)) for b in blobs)   # each card on its own
        together = len(zlib.compress(b"\n".join(blobs), 9))    # the kind as one stream
        if together == 0:
            continue
        ratio = alone / together
        verdict = ("TEMPLATE" if ratio >= 8 else
                   "heavily patterned" if ratio >= 4 else
                   "patterned" if ratio >= 2 else "mostly distinct")
        print("%-17s %7d %12d %10d %10d %6.2fx  %s (%.3f bits/byte together)"
              % (kind, len(blobs), raw, alone, together, ratio, verdict,
                 8.0 * together / raw))
    print()
    print("READING: 'alone' sums each card compressed by itself; 'together' compresses the kind as")
    print("one stream. A high ratio means the kind's real information content is a small fraction of")
    print("its card count. The sample is the FIRST %d cards of a kind, not a random draw." % CAP_PER_KIND)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
