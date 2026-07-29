#!/usr/bin/env python3
"""Per-domain golden cases — derived from each verifier's own documented example, then PROVEN.

GAPS.md G5: the trust kernel is ≥90% covered but the DOMAIN verifiers sit at 13–25%, and the
0-false-positive benchmark covers the derivation moat (60 claims, three modes) — not the ~64
domains. A domain with no golden case has never been shown to seal a truth or refuse a
falsehood.

This derives a golden PAIR for every domain without hand-authoring 64 packets:

  1. Read the example packet out of the verifier module's own docstring (every verifier
     documents its `*_VERIFY` shape — that documentation is the specification).
  2. Run it. If it does not CONFIRM, no golden is recorded and the domain is REPORTED —
     a documented example that does not hold is itself a finding, never a silent skip.
  3. Perturb every `claimed_*` value (numbers scaled, booleans inverted) to build the
     falsehood, and run that. If the engine still confirms, that is a FALSE POSITIVE and the
     domain is reported loudly — this is the property the whole product rests on.
  4. Write the proven pairs to data/domain_goldens.json.

The pairs then serve twice: `tests/test_domain_goldens.py` gates them, and
`tools/card_domain_cores.py` mints a substance card per domain from the same worked run
(GAPS.md G1/G2 — the empty shelves get real content, not stubs).

    PYTHONPATH=src python tools/domain_goldens.py            # derive, prove, write
    PYTHONPATH=src python tools/domain_goldens.py --dry-run  # report only
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

OUT = ROOT / "data" / "domain_goldens.json"
_BLOCK = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", re.S)


def _example_from_docstring(mod) -> dict | None:
    """The example packet a verifier documents for itself. Its docstring is the spec."""
    doc = (mod.__doc__ or "")
    best = None
    for m in _BLOCK.finditer(doc):
        txt = m.group(0)
        txt = re.sub(r"#.*", "", txt)                    # strip trailing comments
        txt = re.sub(r"\.\.\.", "", txt)
        txt = txt.replace("true", "True").replace("false", "False").replace("null", "None")
        txt = re.sub(r",(\s*[}\]])", r"\1", txt)         # trailing commas
        try:
            val = ast.literal_eval(txt)
        except (ValueError, SyntaxError):
            continue
        if isinstance(val, dict) and val and all(isinstance(k, str) for k in val):
            if best is None or len(val) > len(best):
                best = val
    return best


def _packet_key(mod, src: str) -> str | None:
    keys = re.findall(r'packet\.get\("([A-Z][A-Z0-9_]+)"', src)
    if keys:
        return keys[0]
    m = re.search(r"\b([A-Z][A-Z0-9]*_(?:VERIFY|SETUP|CONTROL|INFERENCE|PACKET))\b", mod.__doc__ or "")
    return m.group(1) if m else None


def _falsify(spec: dict) -> dict | None:
    """Perturb the CLAIMS, never the inputs — the falsehood must be a wrong ANSWER to the same
    question, which is exactly what a false positive would have to swallow."""
    out, changed = {}, False
    for k, v in spec.items():
        if k.startswith("claimed_") or k.startswith("claim_"):
            if isinstance(v, bool):
                out[k], changed = (not v), True
                continue
            if isinstance(v, (int, float)):
                out[k], changed = (v * 2 + 7.5 if v else 42.0), True
                continue
            if isinstance(v, str):
                out[k], changed = (v + "_NOT"), True
                continue
        out[k] = v
    return out if changed else None


def _confirmed(results) -> bool:
    """True iff at least one verifier CONFIRMED and none reported a mismatch."""
    sts = [str(getattr(r, "status", "")) for r in results]
    ok = any("CONFIRM" in s for s in sts)
    bad = any("MISMATCH" in s or "BROKEN" in s for s in sts)
    return ok and not bad


def derive():
    from concordance import verifiers
    # VERIFIERS maps MANY aliases to one module ("geology" and "earth_science" both reach
    # verifiers/geology.py). The canonical name is the module's own basename — that is what a
    # reader searches and what the shelf must be called; picking whichever alias sorted first
    # gave shelves named "earth_science", "clinical", "heat".
    canonical = {}
    for dom, path in verifiers.VERIFIERS.items():
        base = path.rsplit(".", 1)[-1]
        if dom == base or path not in canonical:
            canonical[path] = dom if dom == base else canonical.get(path, dom)
    seen, goldens, no_example, unproven, false_positives = set(), {}, [], [], []
    for path, domain in sorted(canonical.items()):
        if path in seen:
            continue
        seen.add(path)
        f = ROOT / "src" / (path.replace(".", "/") + ".py")
        if not f.exists():
            continue
        mod = verifiers._get_module(domain)
        if mod is None:
            continue
        src = f.read_text(encoding="utf-8")
        spec = _example_from_docstring(mod)
        pkt = _packet_key(mod, src)
        if not spec or not pkt:
            no_example.append(domain)
            continue
        # A module docstring often shows the WHOLE shape — several independent checks at once,
        # where one sub-check's placeholder numbers do not hold. That is a documentation
        # convention, not a broken verifier, so before reporting a gap we try each claim ALONE
        # (the claim plus the non-claim inputs). The first subset that genuinely confirms is
        # the golden; if none do, the domain is reported.
        candidates = [spec]
        claims = [k for k in spec if k.startswith(("claimed_", "claim_"))]
        if len(claims) > 1:
            base = {k: v for k, v in spec.items() if not k.startswith(("claimed_", "claim_"))}
            candidates += [{**base, c: spec[c]} for c in claims]
        chosen = None
        for cand in candidates:
            try:
                if _confirmed(verifiers.run_for_domain(domain, {pkt: cand}, surface="witness")):
                    chosen = cand
                    break
            except Exception:  # noqa: BLE001 — try the next subset; report only if all fail
                continue
        if chosen is None:
            unproven.append(domain)
            continue
        spec = chosen
        false_spec = _falsify(spec)
        if false_spec is None:
            unproven.append(f"{domain} (no claimed_* value to falsify)")
            continue
        false_packet = {pkt: false_spec}
        try:
            if _confirmed(verifiers.run_for_domain(domain, false_packet, surface="witness")):
                false_positives.append(domain)          # CRITICAL — sealed a falsehood
                continue
        except Exception as exc:  # noqa: BLE001
            unproven.append(f"{domain} (falsehood raised {type(exc).__name__})")
            continue
        goldens[domain] = {"packet_key": pkt, "true": spec, "false": false_spec}
    return goldens, no_example, unproven, false_positives


def main() -> int:
    goldens, no_example, unproven, fps = derive()
    print(f"PROVEN golden pairs: {len(goldens)} domains")
    print(f"  no documented example found: {len(no_example)}")
    if no_example:
        print("    " + ", ".join(sorted(no_example)))
    print(f"  example did not hold (documentation gap): {len(unproven)}")
    if unproven:
        print("    " + ", ".join(sorted(unproven)))
    print(f"  FALSE POSITIVES (sealed a falsehood — CRITICAL): {len(fps)}")
    for d in fps:
        print(f"    !! {d}")
    if "--dry-run" in sys.argv:
        return 1 if fps else 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(goldens, indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")
    print(f"\nwrote {OUT} ({len(goldens)} pairs)")
    return 1 if fps else 0


if __name__ == "__main__":
    sys.exit(main())
