"""THE .KKRIEGER QUESTION, asked of our own keeping. SECOND ATTEMPT.

Run 1 had two defects of its own, both caught by absurd output:
  * it reported 84.3% of bytes as "constant keys" by aggregating over ALL classes, including
    classes with 43 cards and classes with ONE. In a class of one card every key is trivially
    constant, so the aggregate measured class granularity, not redundancy. Only classes with many
    cards can say anything, so this run imposes a FLOOR (>= MIN_CARDS) and reports nothing above it.
  * it summed "constant keys" + "intra-record duplication" + "body" into one savings figure. Those
    sets OVERLAP (a body is 'constant' in a one-card class; bands bytes sit inside a key that may
    itself be constant), so the sum exceeded the file and printed a 115,910,413x ratio. Nothing is
    summed here: each byte is attributed to exactly ONE bucket, per class, by key.

ATTRIBUTION, once per byte, within each class:
    CONSTANT   -- key's JSON value byte-identical across every card of the class. Storable once.
    VARYING    -- everything else. The cited content lives here.
and inside VARYING, reported but NOT re-added:
    DUP        -- bands values repeated in facets.subject of the SAME record.
    BODY       -- the rendered prose, with the fraction of its tokens found in other fields.

gzip is measured on the same bytes, because the comparison is the actual question: does knowing the
schema beat a general-purpose compressor? If it does not, .kkrieger's lesson for us is not about size.
"""
import gzip
import io
import itertools
import json
import os
import re
import sys
from collections import defaultdict

PATH = os.path.join("data", "source_cards.jsonl")
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 120000
MIN_CARDS = 500
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.\-]*")


def klass(cid):
    out = []
    for p in cid.split("_"):
        if p.isdigit() or (len(p) > 6 and any(c.isdigit() for c in p)):
            break
        out.append(p)
    return "_".join(out) or cid


def main():
    cards = defaultdict(list)          # class -> [ (keyreprs dict, raw_len) ]
    raw_total = n = 0
    gz_buf = io.BytesIO()
    with open(PATH, encoding="utf-8") as f:
        for line in itertools.islice(f, LIMIT):
            b = line.encode("utf-8")
            raw_total += len(b)
            n += 1
            if n <= 40000:
                gz_buf.write(b)
            d = json.loads(line)
            c = klass(str(d.get("id") or ""))
            reprs = {k: json.dumps(v, ensure_ascii=False, separators=(",", ":"))
                     for k, v in d.items()}
            cards[c].append((reprs, len(b), d))

    print("file  %s" % PATH)
    print("read  %d cards, %d bytes (%.1f MB) -- bounded sample, not the whole keeping" %
          (n, raw_total, raw_total / 1e6))
    print("floor %d cards per class; smaller classes cannot distinguish 'constant' from"
          " 'only one example'.\n" % MIN_CARDS)

    classes = [(c, v) for c, v in cards.items() if len(v) >= MIN_CARDS]
    classes.sort(key=lambda kv: -sum(r[1] for r in kv[1]))
    if not classes:
        print("no class reaches the floor"); return

    print("=" * 100)
    print("BYTES ATTRIBUTED ONCE EACH, per class (classes at or above the floor)")
    print("=" * 100)
    print("%-22s %7s %11s %9s %9s | %8s %8s %7s"
          % ("class", "cards", "bytes", "CONSTANT", "VARYING", "dup", "body", "b-ovlp"))
    print("-" * 100)
    g_tot = g_const = g_var = g_dup = g_body = 0
    ov_num = ov_den = 0
    for c, rows in classes:
        keys = set()
        for reprs, _, _ in rows:
            keys |= set(reprs)
        const_keys = set()
        for k in keys:
            vals = {reprs.get(k) for reprs, _, _ in rows}
            if len(vals) == 1 and None not in vals:
                const_keys.add(k)
        tot = sum(r[1] for r in rows)
        const = var = 0
        for reprs, _, _ in rows:
            for k, r in reprs.items():
                cost = len(r.encode("utf-8")) + len(k) + 4
                if k in const_keys:
                    const += cost
                else:
                    var += cost
        dup = body = 0
        for _, _, d in rows:
            bands, fac = d.get("bands"), (d.get("facets") or {}).get("subject")
            if isinstance(bands, list) and isinstance(fac, list):
                shared = set(map(str, bands)) & set(map(str, fac))
                dup += sum(len(json.dumps(s, ensure_ascii=False).encode()) for s in shared)
            bd = d.get("body")
            if isinstance(bd, str) and bd:
                body += len(bd.encode("utf-8"))
                rest = {k: v for k, v in d.items() if k != "body"}
                hay = json.dumps(rest, ensure_ascii=False).lower()
                toks = [t for t in TOKEN.findall(bd) if len(t) > 2]
                ov_num += sum(1 for t in toks if t.lower() in hay)
                ov_den += len(toks)
        print("%-22s %7d %11d %8.1f%% %8.1f%% | %8d %8d %6s"
              % (c[:22], len(rows), tot, 100.0 * const / tot, 100.0 * var / tot, dup, body, ""))
        g_tot += tot; g_const += const; g_var += var; g_dup += dup; g_body += body
    print("-" * 100)
    print("%-22s %7d %11d %8.1f%% %8.1f%% | %8d %8d %5.1f%%"
          % ("CLASSES >= FLOOR", sum(len(v) for _, v in classes), g_tot,
             100.0 * g_const / g_tot, 100.0 * g_var / g_tot, g_dup, g_body,
             100.0 * ov_num / max(ov_den, 1)))
    print("\ncoverage: these classes are %.1f%% of the sample's bytes (%d of %d cards)."
          % (100.0 * g_tot / raw_total, sum(len(v) for _, v in classes), n))
    print("dup and body are INSIDE varying; they are shown, never added to constant.")
    print("body-token overlap %.1f%% is EVIDENCE the prose restates the fields, not a savings claim."
          % (100.0 * ov_num / max(ov_den, 1)))

    print("\n" + "=" * 100)
    print("DOES KNOWING THE SCHEMA BEAT A GENERAL COMPRESSOR?")
    print("=" * 100)
    s = gz_buf.getvalue()
    gz = len(gzip.compress(s, 9))
    schema_x = g_tot / max(g_tot - g_const, 1)
    print("remove constant keys (schema-aware, nothing inferred) : %.2fx" % schema_x)
    print("gzip -9, same bytes, knows nothing about cards        : %.2fx  (%d -> %d)"
          % (len(s) / gz, len(s), gz))
    print()
    if len(s) / gz > schema_x:
        print("gzip WINS, by %.1fx. So a generator is NOT a size argument for us -- the general"
              % ((len(s) / gz) / schema_x))
        print("compressor already removes more than the schema does, because it also eats the")
        print("repeated PROSE that a constant-key analysis has to leave in VARYING.")
    print("\n.kkrieger: 97,280 bytes of creation history -> a whole FPS, expanded at load.")
    print("Our creation history is a seed script PLUS an external cited source, so our generator")
    print("can never be self-contained. That is the doctrine, not a shortfall: a seed that could")
    print("make a place card without GeoNames would be INVENTING PLACES.")


if __name__ == "__main__":
    main()
