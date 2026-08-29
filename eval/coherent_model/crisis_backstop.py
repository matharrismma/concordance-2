#!/usr/bin/env python3
"""ASSAY: does a DETERMINISTIC semantic score catch the veiled cries the substring net misses?

Run-list item #1 (docs/CRISIS_BACKSTOP.md). Before building/deploying a backstop, MEASURE it. The
substring matcher (ask.is_crisis) misses a veiled/behavioral cluster (goodbye+giving-away, grief-
longing, faith-"called home"). This asks: build a hopelessness/ideation CENTROID from the confirmed
crisis corpus using the coherent model's PPMI vectors (from the keeping — deterministic, sovereign,
no LLM), score each message's centroid against it, and find the threshold where CLEARLY_BENIGN false-
positives stay at 0%. At THAT threshold, how many of the substring-MISSED cries does semantics catch?

Verdict per the assay: CONFIRMED (worth building) / RESONANCE / COINCIDENCE (name the limit honestly).
The backstop may only ADD catches, never remove one the substring net makes — so only the MISSED set
matters for recall, and the benign floor is non-negotiable.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "tests"))

import model as M          # noqa: E402  the shared deterministic PPMI model
from concordance import ask  # noqa: E402
import test_crisis_coverage as T  # noqa: E402  the durable corpora (CRISIS_FLOOR/CLEARLY_BENIGN/RED_TEAM_BLIND)


def build_model():
    """PPMI over the keeping (Bible + general cards) — enough vocabulary for everyday despair words."""
    docs = list(M.bible_docs())
    docs += list(M.card_docs(["encyclopedia_cards.jsonl", "cards.jsonl"], cap_per_file=9000))
    return M.build(docs, window=5, min_count=5)


def main():
    if not (M.DATA / "bible_en.jsonl").exists():
        print("corpus not present"); return
    print("building the PPMI model (keeping: Bible + cards)…", flush=True)
    mdl = build_model()
    print(f"  vocab {len(mdl.vec)}", flush=True)

    # The crisis centroid: the mean PPMI vector of ALL content words across the confirmed crisis corpus.
    crisis_words = []
    for phrase in T.CRISIS_FLOOR:
        crisis_words += M.content(phrase)
    centroid = mdl.centroid(crisis_words)

    def score(text):
        return mdl._cos_raw(mdl.centroid(M.content(text)), centroid)

    # DEPLOYABLE FORM: a per-word crisis-affinity table {word: cos(word_vec, crisis_centroid)}. Small
    # (~vocab entries), sovereign, auditable — no model at runtime. score_b = mean affinity of the
    # message's content words. Verify it tracks the centroid-cosine before building it as the artifact.
    affinity = {w: mdl._cos_raw(v, centroid) for w, v in mdl.vec.items()}

    def score_b(text):
        vals = [affinity[w] for w in M.content(text) if w in affinity]
        return sum(vals) / len(vals) if vals else 0.0

    # C) the SEPARABLE deployable form: {word: raw dot(word_vec, crisis_centroid)}. mean over a message's
    # words = dot(message_centroid, crisis_centroid) = the cosine NUMERATOR (drops only the message-norm).
    ck = set(centroid)
    dot_tab = {w: sum(v[k] * centroid[k] for k in (v.keys() & ck)) for w, v in mdl.vec.items()}

    def score_c(text):
        vals = [dot_tab[w] for w in M.content(text) if w in dot_tab]
        return sum(vals) / len(vals) if vals else 0.0

    # split the blind red-team into what the SUBSTRING net already catches vs MISSES (the backstop's job)
    missed = [q for q in T.RED_TEAM_BLIND if not ask.is_crisis(q)]
    caught_sub = [q for q in T.RED_TEAM_BLIND if ask.is_crisis(q)]

    benign_scores = sorted((score(q) for q in T.CLEARLY_BENIGN), reverse=True)
    top_benign = benign_scores[0] if benign_scores else 0.0
    # conservative threshold: just above the highest benign score => 0% benign false-positives
    thr = top_benign + 1e-9

    def recall(items):
        return sum(1 for q in items if score(q) > thr), len(items)

    mc, mn = recall(missed)
    fc, fn = recall(T.CRISIS_FLOOR)
    bc = sum(1 for q in T.CLEARLY_BENIGN if score(q) > thr)

    print(f"\n=== A) centroid-cosine (reference) ===")
    print(f"threshold (0% benign FP) = {thr:.4f}   (top benign score {top_benign:.4f})")
    print(f"CLEARLY_BENIGN false-positives at threshold: {bc}/{len(T.CLEARLY_BENIGN)}  (must be 0)")
    print(f"SUBSTRING-MISSED cries now caught by semantics: {mc}/{mn} = {100*mc//max(mn,1)}%")
    print(f"CRISIS_FLOOR also caught by semantics alone:    {fc}/{fn} = {100*fc//max(fn,1)}%")
    print(f"(substring already catches {len(caught_sub)}/{len(T.RED_TEAM_BLIND)} of the blind set)")

    # B) the deployable per-word-affinity form, same 0%-benign-FP discipline
    tb = max(score_b(q) for q in T.CLEARLY_BENIGN) + 1e-9
    bmc = sum(1 for q in missed if score_b(q) > tb)
    bbc = sum(1 for q in T.CLEARLY_BENIGN if score_b(q) > tb)
    union = sum(1 for q in T.RED_TEAM_BLIND if ask.is_crisis(q) or score_b(q) > tb)
    print(f"\n=== B) per-word affinity table (DEPLOYABLE) ===")
    print(f"threshold (0% benign FP) = {tb:.4f}")
    print(f"CLEARLY_BENIGN false-positives: {bbc}/{len(T.CLEARLY_BENIGN)}  (must be 0)")
    print(f"SUBSTRING-MISSED cries caught:  {bmc}/{mn} = {100*bmc//max(mn,1)}%")
    print(f"UNION (substring OR affinity) on blind set: {union}/{len(T.RED_TEAM_BLIND)} = "
          f"{100*union//len(T.RED_TEAM_BLIND)}%   (substring alone {len(caught_sub)})")

    tc = max(score_c(q) for q in T.CLEARLY_BENIGN) + 1e-9
    cmc = sum(1 for q in missed if score_c(q) > tc)
    cbc = sum(1 for q in T.CLEARLY_BENIGN if score_c(q) > tc)
    cunion = sum(1 for q in T.RED_TEAM_BLIND if ask.is_crisis(q) or score_c(q) > tc)
    print(f"\n=== C) per-word DOT table (separable, DEPLOYABLE) ===")
    print(f"threshold (0% benign FP) = {tc:.4f}")
    print(f"CLEARLY_BENIGN false-positives: {cbc}/{len(T.CLEARLY_BENIGN)}  (must be 0)")
    print(f"SUBSTRING-MISSED cries caught:  {cmc}/{mn} = {100*cmc//max(mn,1)}%")
    print(f"UNION (substring OR dot) on blind set: {cunion}/{len(T.RED_TEAM_BLIND)} = "
          f"{100*cunion//len(T.RED_TEAM_BLIND)}%   (substring alone {len(caught_sub)})")
    print(f"artifact size: {len(dot_tab)} word->score entries")

    # size the deployable artifact: crisis centroid + the word vectors + threshold. Try a top-N-per-word
    # compaction and confirm the cosine survives it (so the committed artifact stays small).
    import json, math
    def norm(v): return math.sqrt(sum(x * x for x in v.values())) or 1.0
    ncrit = norm(centroid)
    def cos_red(a, b, nb):
        d = sum(a[k] * b[k] for k in (a.keys() & b.keys())); return d / (norm(a) * nb) if d else 0.0
    for N in (24, 40, 64):
        red = {w: dict(sorted(v.items(), key=lambda kv: abs(kv[1]), reverse=True)[:N]) for w, v in mdl.vec.items()}
        rc = {k: centroid[k] for k in sorted(centroid, key=lambda k: abs(centroid[k]), reverse=True)[:256]}
        nrc = norm(rc)
        def sc(text, red=red, rc=rc, nrc=nrc):
            c = M.defaultdict(float); n = 0
            for w in M.content(text):
                if w in red:
                    n += 1
                    for k, x in red[w].items(): c[k] += x
            if n:
                for k in c: c[k] /= n
            return cos_red(c, rc, nrc)
        trd = max(sc(q) for q in T.CLEARLY_BENIGN) + 1e-9
        rmc = sum(1 for q in missed if sc(q) > trd)
        rbc = sum(1 for q in T.CLEARLY_BENIGN if sc(q) > trd)
        runion = sum(1 for q in T.RED_TEAM_BLIND if ask.is_crisis(q) or sc(q) > trd)
        blob = json.dumps({"c": rc, "v": {w: red[w] for w in list(red)[:50]}})
        approx_mb = (len(json.dumps(red)) + len(json.dumps(rc))) / 1e6
        print(f"\n=== D) top-{N} compact centroid-cosine (committable artifact) ===")
        print(f"  benign FP {rbc}/{len(T.CLEARLY_BENIGN)} | missed caught {rmc}/{mn}={100*rmc//max(mn,1)}% | "
              f"UNION {runion}/{len(T.RED_TEAM_BLIND)}={100*runion//len(T.RED_TEAM_BLIND)}% | ~{approx_mb:.1f} MB")

    # E) DENSE RANDOM PROJECTION (chosen path): project each sparse PPMI vector to K dense dims via a
    # fixed seeded ±1 matrix (JL — preserves dot/norm ⇒ cosine survives), stdlib-only + committable.
    # Projects lazily (only the test words) here to measure; the build tool projects the whole vocab.
    import random, math
    ctx_idx = {c: i for i, c in enumerate(sorted({c for v in mdl.vec.values() for c in v}))}
    for K in (200, 384):
        SEED = 20260828
        Rcache = {}
        def Rc(i):
            r = Rcache.get(i)
            if r is None:
                g = random.Random(SEED * 1000003 + i)
                r = [1.0 if g.random() < 0.5 else -1.0 for _ in range(K)]
                Rcache[i] = r
            return r
        pcache = {}
        def project(v, key=None):
            if key is not None and key in pcache: return pcache[key]
            d = [0.0] * K
            for c, val in v.items():
                i = ctx_idx.get(c)
                if i is None: continue
                rc = Rc(i)
                for j in range(K): d[j] += val * rc[j]
            s = 1.0 / math.sqrt(K); d = [x * s for x in d]
            if key is not None: pcache[key] = d
            return d
        dC = project(centroid)
        nC = math.sqrt(sum(x * x for x in dC)) or 1.0
        def score_e(text):
            ws = [w for w in M.content(text) if w in mdl.vec]
            if not ws: return 0.0
            acc = [0.0] * K
            for w in ws:
                dv = project(mdl.vec[w], key=w)
                for j in range(K): acc[j] += dv[j]
            n = len(ws); acc = [x / n for x in acc]
            dot = sum(acc[j] * dC[j] for j in range(K)); na = math.sqrt(sum(x * x for x in acc))
            return dot / (na * nC) if na else 0.0
        te = max(score_e(q) for q in T.CLEARLY_BENIGN) + 1e-9
        emc = sum(1 for q in missed if score_e(q) > te)
        ebc = sum(1 for q in T.CLEARLY_BENIGN if score_e(q) > te)
        eunion = sum(1 for q in T.RED_TEAM_BLIND if ask.is_crisis(q) or score_e(q) > te)
        approx_mb = len(mdl.vec) * K / 1e6   # int8: 1 byte/dim
        print(f"\n=== E) dense random projection K={K} (CHOSEN, committable) ===")
        print(f"  benign FP {ebc}/{len(T.CLEARLY_BENIGN)} | missed caught {emc}/{mn}={100*emc//max(mn,1)}% | "
              f"UNION {eunion}/{len(T.RED_TEAM_BLIND)}={100*eunion//len(T.RED_TEAM_BLIND)}% | int8 ~{approx_mb:.1f} MB")

    print("\n— sample of MISSED cries the semantic score WOULD catch (backstop value) —")
    for q in [q for q in missed if score(q) > thr][:12]:
        print(f"   {score(q):.3f}  {q}")
    print("\n— MISSED cries still below threshold (the residual even semantics can't reach) —")
    for q in [q for q in missed if score(q) <= thr][:8]:
        print(f"   {score(q):.3f}  {q}")


if __name__ == "__main__":
    main()
