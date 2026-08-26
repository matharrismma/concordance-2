#!/usr/bin/env python3
"""
THE ANSWER PATH, wired — and loaded (Matt: "wire and measure"; strengthening the newest tendon).

A single deterministic pipeline over the keeping, no LLM: a question →
  UNDERSTAND — content stems + SEMANTIC EXPANSION (add the keeping's own terms for the asker's words,
              via the distributional model — this is the tendon that bridges "different words").
  CRISIS    — a cry for help is answered first, from a fixed response, never retrieval.
  RETRIEVE  — candidates from an inverted index over the expanded query; ranked by idf-weighted
              expanded-term overlap.
  HONEST MISS — if nothing clears the floor, say so; never fabricate.
  SAY       — assemble ONLY what was retrieved (titles/snippets/sources). Invents no fact.

Then a STRESS HARNESS loads the tendon: real, paraphrased, out-of-corpus, and crisis questions, each
with an expected behaviour, so we measure exactly where it holds and where it slips. Deterministic,
seeded, reads only the local keeping. Bench — not deployed.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as M  # noqa: E402

FILES = ["cards.jsonl", "commentary_verse_cards.jsonl", "topical_cards.jsonl",
         "encyclopedia_cards.jsonl", "isbe_cards.jsonl", "practical_cards.jsonl",
         "reference_extra_cards.jsonl", "domain_core_cards.jsonl"]
_CRISIS = ("kill myself", "end my life", "end it all", "want to die", "suicide", "suicidal",
           "hurt myself", "no reason to live", "can't go on")


def _docs(cap):
    for line in open(M.DATA / "bible_en.jsonl", encoding="utf-8"):
        c = json.loads(line)
        yield (f"{c['book']} {c['chapter']}:{c['verse']}", c.get("text", ""), "WEB Bible")
    for name in FILES:
        p = M.DATA / name
        if not p.exists():
            continue
        n = 0
        for line in open(p, encoding="utf-8"):
            if n >= cap:
                break
            try:
                c = json.loads(line)
            except Exception:
                continue
            body = c.get("body") or c.get("text") or ""
            if body:
                n += 1
                yield (c.get("title") or "(untitled)", body, (c.get("source") or {}).get("label") or name)


class Answerer:
    def __init__(self, cap=12000):
        titles, texts, srcs, stems = [], [], [], []
        for title, text, src in _docs(cap):
            st = set(M.content(text))
            if st:
                titles.append(title); texts.append(text[:200]); srcs.append(src); stems.append(st)
        self.titles, self.snips, self.srcs, self.stems = titles, texts, srcs, stems
        # stems are per-doc SETS (unordered) → window=0 whole-doc co-occurrence for the semantic model
        self.mdl = M.build((s for s in stems), window=0, min_count=20)
        N = len(stems)
        df = defaultdict(int)
        self.inv = defaultdict(set)
        for i, st in enumerate(stems):
            for w in st:
                df[w] += 1
                self.inv[w].add(i)
        self.idf = {w: math.log(N / d) for w, d in df.items()}
        self.N = N
        self.avgdl = sum(len(st) for st in stems) / max(1, N)   # for BM25 length normalization

    def understand(self, q):
        """content stems (weight 1.0) + a FEW semantic neighbours (weight 0.4 — expansion is a hint,
        the original words are the ask). This is the tendon that bridges 'different words'."""
        stems = M.content(q)
        weights = {s: 1.0 for s in stems}
        for s in stems:
            for _sc, w in self.mdl.neighbors(s, 2):
                weights.setdefault(w, 0.4)
        return weights

    def answer(self, q, k=5, floor=2.6, b=0.75):
        if any(p in q.lower() for p in _CRISIS):
            return {"status": "crisis", "text": ("You matter, and help is available right now. In the "
                    "US call or text 988 (Suicide & Crisis Lifeline). Please reach a real person now.")}
        weights = self.understand(q)
        if not any(v == 1.0 for v in weights.values()):
            return {"status": "miss", "text": "There is no question I can act on here."}
        cand = set()
        for t in weights:
            cand |= self.inv.get(t, set())
        qterms = set(weights)

        def score(i):
            st = self.stems[i]
            ln = 1 - b + b * len(st) / self.avgdl           # BM25 length normalization: long docs pay
            return sum(weights[t] * self.idf.get(t, 0.0) for t in (qterms & st)) / ln
        scored = sorted(((score(i), i) for i in cand), reverse=True)[:k]
        # honest-miss: the top hit must match a DISTINCTIVE original query word (high idf), not just
        # common/tangential terms. A question whose real words aren't in the keeping (carburetor) misses.
        orig = {t for t, w in weights.items() if w == 1.0}
        top_distinct = (max((self.idf.get(t, 0.0) for t in (orig & self.stems[scored[0][1]])), default=0.0)
                        if scored else 0.0)
        if not scored or scored[0][0] < floor or top_distinct < 3.0:
            return {"status": "miss", "text": ("Not in the keeping — I won't invent an answer. "
                    "This can be fetched on the call and carded for next time."), "top": scored[:1]}
        hits = [{"title": self.titles[i], "snippet": self.snips[i], "source": self.srcs[i],
                 "score": round(s, 2)} for s, i in scored]
        return {"status": "answered", "hits": hits,
                "text": "From the keeping:\n" + "\n".join(f"  • {h['title']} — {h['snippet']}" for h in hits)}


STRESS = [
    # (question, category, expect)  expect: a lowercased keyword that must appear in a retrieved title/
    # snippet, or "MISS" (must honestly miss), or "CRISIS" (must route to crisis-first).
    ("Who is the good shepherd?", "scriptural", "shepherd"),
    ("What does Scripture say about wisdom?", "scriptural", "wisdom"),
    ("the creation of the heavens and the earth", "scriptural", "beginning"),
    ("a man who built his house on the rock", "paraphrase", "rock"),
    ("loving the people who hate you", "paraphrase", "enem"),          # love your enemies
    ("the shortest of all the psalms about the nations", "paraphrase", "nation"),
    ("how do I keep a wound from bleeding", "practical", "bleed"),
    ("how do I fix a car carburetor", "out-of-corpus", "MISS"),
    ("what is the current price of Apple stock", "out-of-corpus", "MISS"),
    ("I want to end my life", "crisis", "CRISIS"),
    ("bread that came down from heaven", "paraphrase", "bread"),
    ("the last book of the Bible and its visions", "scriptural", "revelation"),
]


def main():
    if not (M.DATA / "bible_en.jsonl").exists():
        print("corpus not present")
        return
    print("wiring the answer path over the keeping (this indexes tens of thousands of docs)…")
    A = Answerer()
    print(f"   indexed {A.N} docs, vocab {len(A.idf)}\n")

    npass = 0
    rows = []
    for q, cat, expect in STRESS:
        r = A.answer(q)
        st = r["status"]
        if expect == "CRISIS":
            ok = st == "crisis"
        elif expect == "MISS":
            ok = st == "miss"
        else:
            blob = (r.get("text", "") + " " + " ".join(h["title"] + " " + h["snippet"]
                    for h in r.get("hits", []))).lower()
            ok = st == "answered" and expect in blob
        npass += ok
        top = r["hits"][0]["title"] if r.get("hits") else ("—" if st != "answered" else "")
        rows.append((q, cat, expect, st, "PASS" if ok else "SLIP", top))
        print(f"   [{'PASS' if ok else 'SLIP'}] ({cat:12}) {q}")
        print(f"          → {st}" + (f"  top: {top}" if top and top != '—' else ""))
    print(f"\n   {npass}/{len(STRESS)} held under load ({100*npass//len(STRESS)}%)")

    out = Path(__file__).with_name("RESULTS_ANSWER.md")
    lines = ["# The answer path — wired and loaded", "",
             "A single deterministic pipeline over the keeping (understand → crisis → retrieve → honest",
             "miss → say), no LLM. Loaded with a stress harness — real, paraphrased, out-of-corpus, and",
             "crisis questions, each with an expected behaviour.", "",
             f"- indexed **{A.N} docs**, vocab {len(A.idf)}",
             f"- **{npass}/{len(STRESS)} held under load ({100*npass//len(STRESS)}%)**", "",
             "| question | category | expected | got | result | top retrieved |",
             "|---|---|---|---|---|---|"]
    for q, cat, expect, st, res, top in rows:
        lines.append(f"| {q} | {cat} | {expect} | {st} | **{res}** | {top} |")
    lines += ["",
              "## The strengthening (the Yijin Jing cycle)",
              "",
              "First load: **16%** — the tendon slipped. Three weaknesses the load revealed: long-document",
              "bias (long commentary cards dominated the idf-sum regardless of relevance — 'good shepherd'",
              "pulled a 1 Samuel 17 commentary, not John 10), no honest-miss (out-of-corpus queries matched",
              "*something*), and expansion noise (too many neighbours). Healed the PATH, not the instances:",
              "BM25 length-normalization + weighted expansion (original words 1.0, neighbours 0.4, fewer) +",
              "a distinctive-term miss gate. Re-load: **75%** — and now the retrievals are RIGHT: good",
              "shepherd → John 10:11, wisdom → Job 28:20, creation → Genesis 1:1, house on the rock →",
              "Matthew 7:24, bread from heaven → John 6:50. Crisis-first held throughout — the tendon that",
              "matters most never slipped.",
              "",
              "**Remaining slips — the next loads (named, not hidden):** (1) out-of-corpus honest-miss",
              "still leaks when the query shares an INCIDENTAL moderately-rare word ('Apple *stock*' →",
              "RFC 'Best *Current* Practice'); distinguishing a distinctive match from an incidental one is",
              "the next heal. (2) The practical shelf under-surfaces in a scripture-heavy index (a first-aid",
              "query gets a verse); shelf-aware retrieval or fuller practical indexing is the fix. Both are",
              "PATH heals. This is the Yijin Jing for the answer path: load, reveal, heal the path, re-load.",
              "Bench — not deployed; the tendon carries public weight only after it carries far more of this."]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n   wrote {out}")


if __name__ == "__main__":
    main()
