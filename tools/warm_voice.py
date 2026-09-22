#!/usr/bin/env python3
"""WARM THE VOICE — synthesize the kept, repeated lines ONCE, in the operator's own voice.

Matt, 2026-09-22: "turn this into a strength." The ElevenLabs voice is the ceiling; the content-
addressed cache (voice.py, keyed by voice|model|text) means the paid API is touched AT MOST ONCE per
distinct utterance. So the repeated spoken lines — the cube's rules and its Socratic checks, and the
coach's fixed prompts — are the same words for every learner, forever. Voice them once and they
become a KEPT ASSET: instant, free, and (with the service worker) offline, in the operator's voice.

This walks those lines and calls voice.speak on each. A line already in the cache is a HIT and costs
nothing; only a genuinely new line spends. Idempotent, bounded, honest:

    ELEVENLABS_API_KEY=… ELEVENLABS_VOICE_ID=… PYTHONPATH=src python tools/warm_voice.py --dry-run
    …                                          PYTHONPATH=src python tools/warm_voice.py --limit 40
    …                                          PYTHONPATH=src python tools/warm_voice.py           # all

Runs where the keys and the curriculum live (the box). A dry run needs no key and spends nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

from concordance import voice  # noqa: E402

CURR = Path("data") / "curriculum"

# Fixed lines the coach speaks verbatim, so they are worth voicing once. Kept short and true.
FIXED = [
    "You are not alone. Please reach a real person right now.",
    "That is not in the keeping yet.",
    "Written down.",
    "Yes — that's it.",
    "Not quite. Try once more.",
    "Say it in the words of the cube.",
    "One thing first —",
    "Where next — your choice.",
    "Kept your copy. Now say, for instance, read me the section on, and I'll read that part from your book.",
    "I read the page. Now say, for instance, read me the section on, or ask me about it.",
]


def _clean(s: str) -> str:
    return " ".join(str(s or "").split()).strip()


def curriculum_lines(scope: str):
    """The repeated spoken lines of the cubes. scope='core' = rules + check prompts (clean English,
    highest repeat); scope='all' also adds decodable sentences and examples (the 'hear it' buttons)."""
    lines = []
    for p in sorted(CURR.glob("*_en.json")):
        try:
            units = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(units, list):
            continue
        for u in units:
            if not isinstance(u, dict):
                continue
            if u.get("rule"):
                lines.append(_clean(u["rule"]))
            chk = u.get("check") or {}
            if chk.get("prompt"):
                lines.append(_clean(chk["prompt"]))
            if scope == "all":
                if u.get("decodable_sentence"):
                    lines.append(_clean(u["decodable_sentence"]))
                for ex in (u.get("examples") or []):
                    lines.append(_clean(ex))
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description="Warm the operator's-voice cache with the kept lines.")
    ap.add_argument("--dry-run", action="store_true", help="list what would be voiced; spend nothing")
    ap.add_argument("--limit", type=int, default=0, help="synthesize at most N NEW lines (0 = no cap)")
    ap.add_argument("--scope", choices=("core", "all"), default="core",
                    help="core = rules + checks (default); all = also decodables + examples")
    args = ap.parse_args()

    phrases, seen = [], set()
    for s in FIXED + curriculum_lines(args.scope):
        if s and len(s) <= voice._MAX_CHARS and s not in seen:
            seen.add(s)
            phrases.append(s)

    print(f"warm-voice · scope={args.scope} · {len(phrases)} distinct lines · "
          f"~{sum(len(p) for p in phrases):,} characters")
    if args.dry_run:
        for p in phrases[:8]:
            print("   ·", p[:80])
        print(f"   … ({len(phrases)} total). Dry run — nothing synthesized, nothing spent.")
        return 0
    if not voice.configured():
        print("ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID not set — run where the operator's voice is wired.",
              file=sys.stderr)
        return 2

    hits = misses = fails = 0
    for i, p in enumerate(phrases, 1):
        if args.limit and misses >= args.limit:
            print(f"   reached --limit {args.limit} new lines; stopping.")
            break
        res = voice.speak(p)
        if res is None:
            fails += 1
            continue
        _, state = res
        if state == "hit":
            hits += 1
        else:
            misses += 1
            time.sleep(0.4)   # be a good neighbor to the API on a genuine synthesis
        if i % 25 == 0 or state == "miss":
            print(f"   [{i}/{len(phrases)}] {state:4}  {p[:64]}")
    print(f"\n  done · {hits} already kept · {misses} newly voiced · {fails} unavailable. "
          f"The kept lines now speak instantly and free, in the operator's voice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
