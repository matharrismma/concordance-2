"""THE RECEIVER — the engine as one complete system, stage by stage (Matt, 2026-10-08).

"look at it as AM or FM radio. think of us as a transceiver. We filter out the static like a triode vacuum tube"
→ "a superheterodyne receiver" → "Keep the names as close to current tech and our current, but the receiver is a
complete system. We will be complete when we have all components that function correctly. the sum is greater
than the parts."

So: every stage of a superheterodyne receiver, named in current radio terms, bound to the component the code
already has under the name the code already uses, with the PROOF that it functions — read from the deploy gate's
own artifacts (never typed in): the domain benchmarks and the moat, the live assay, the front door, the recall set,
the launch roll-call; or, where a stage has no gate line yet, the pins on disk. COMPLETE = every stage proven AND
the whole proven end to end by the four gate lines — the sum is greater than the parts, so the whole has its own
proof and is never inferred from the stages. Pure over files; no corpus; cheap per request. Feeds GET /systems and
site/systems.html. The likeness (stick_a_superheterodyne_receiver) is kept a likeness: a stage's name is a map to
the component, and the component's proof is the only thing that moves a lamp.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent.parent


def _data_dir() -> Path:
    d = os.environ.get("CONCORDANCE_DATA_DIR", "").strip()
    return Path(d) if d else (ROOT / "data")


def _load(data: Path, name: str) -> Optional[Dict[str, Any]]:
    p = data / name
    if not p.exists():
        return None
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
        return v if isinstance(v, dict) else None
    except (OSError, ValueError):
        return None


# ── the proofs: each reads one gate artifact and answers (ok, what it read) ──────────────────────────────
def _p_recall(data: Path):
    d = _load(data, "recall.json")
    if not d:
        return None, "no recall.json — the recall gate has not run here"
    ok = d.get("false_positives", 1) == 0 and not d.get("regressed", False)
    return ok, f"reached {d.get('reached')}/{d.get('phrasings')} over {d.get('families')} families, {d.get('false_positives')} false positives, floor {d.get('floor')}"


def _p_moat(data: Path):
    d = _load(data, "benchmarks.json")
    m = (d or {}).get("moat") or {}
    if not m:
        return None, "no benchmarks.json moat — the benchmark gate has not run here"
    ok = m.get("correct") == m.get("cases") and m.get("false_positives", 1) == 0
    return ok, f"the moat: {m.get('correct')}/{m.get('cases')} correct, {m.get('false_positives')} false positives"


def _p_frontdoor(data: Path):
    d = _load(data, "frontdoor.json")
    if not d:
        return None, "no frontdoor.json — the front-door gate has not run here"
    ok = d.get("false_positives", 1) == 0 and not d.get("regressed", False)
    return ok, f"reached {d.get('reached')}/{d.get('claims')}, correct {d.get('correct')}, found {d.get('found')}, {d.get('false_positives')} false positives"


def _p_specs(data: Path):
    d = _load(data, "benchmarks.json")
    s = (d or {}).get("specs") or {}
    if not s:
        return None, "no benchmarks.json specs — the benchmark gate has not run here"
    refused = s.get("refused")
    n_ref = len(refused) if isinstance(refused, list) else int(refused or 0)
    ok = int(s.get("checks") or 0) > 0 and n_ref == 0
    return ok, f"{s.get('checks')} admitted spec checks, {n_ref} refused"


def _p_domains(data: Path):
    d = _load(data, "benchmarks.json")
    dm = (d or {}).get("domains") or {}
    if not dm:
        return None, "no benchmarks.json domains — the benchmark gate has not run here"
    ok = dm.get("ok") == dm.get("count") and dm.get("false_positives", 1) == 0
    return ok, f"domains {dm.get('ok')}/{dm.get('count')} ok (sealed {dm.get('sealed_truths')}, refused {dm.get('refused_falsehoods')}, {dm.get('false_positives')} false positives)"


def _p_assay(data: Path):
    d = _load(data, "benchmarks.json")
    a = (d or {}).get("assay") or {}
    if not a:
        return None, "no live assay in benchmarks.json — the assay has not run here"
    reg = a.get("regressed")
    n_reg = len(reg) if isinstance(reg, list) else int(reg or 0)
    ok = n_reg == 0 and int(a.get("passed") or 0) > 0
    return ok, f"live assay {a.get('passed')}/{a.get('probes')} passed, floor {a.get('floor')}, {n_reg} regressed"


def _p_boot(data: Path):
    d = _load(data, "boot_checkin.json")
    if not d:
        return None, "no boot_checkin.json — no launch roll-call recorded here"
    ok = d.get("ready") == d.get("total") and int(d.get("total") or 0) > 0
    return ok, f"launch roll-call {d.get('ready')}/{d.get('total')} checked in at {d.get('at')}"


def _p_keeping(data: Path):
    d = _load(data, "boot_checkin.json")
    if not d:
        return None, "no boot_checkin.json — no launch roll-call recorded here"
    # the roll-call records the heavy singletons as a list: {"label": "corpus (default_corpus)", "ms", "rss_kb", "ok", ...}
    singles = d.get("singletons")
    if not isinstance(singles, list):
        return None, "the roll-call recorded no singletons"
    corpus = [x for x in singles if isinstance(x, dict) and "corpus" in str(x.get("label") or "").lower()]
    if not corpus:
        return False, "the keeping is not among the roll-call's singletons"
    c = corpus[0]
    ok = bool(c.get("ok"))
    return ok, (f"the keeping at boot: {c.get('label')} in {c.get('ms')} ms, {round((c.get('rss_kb') or 0) / 1024)} MB resident"
                + ("" if ok else f" — failed: {c.get('error')}"))


def _p_squelch(data: Path):
    d = _load(data, "recall.json")
    rows = (d or {}).get("rows")
    if not isinstance(rows, list):
        return None, "no recall rows — the recall gate has not run here"
    un = [r for r in rows if not r.get("reached")]
    silent = [r for r in un if (r.get("verdict") or "NOTHING_TO_CHECK") == "NOTHING_TO_CHECK"]
    ok = len(silent) == len(un)
    return ok, f"{len(silent)}/{len(un)} unreached phrasings answered NOTHING_TO_CHECK — silence, not static"


def _pinned(*tests: str) -> Callable[[Path], Any]:
    def run(_data: Path):
        have = [t for t in tests if (ROOT / "tests" / t).exists()]
        ok = len(have) == len(tests)
        return ok, f"pinned by {', '.join(tests)}" + ("" if ok else f" — missing {', '.join(t for t in tests if t not in have)}")
    return run


# ── the stages, in signal order: radio name → the component under its own name → the proof ──────────────
STAGES: List[Dict[str, Any]] = [
    {"stage": "antenna", "tech": "the carrier the signal arrives on",
     "component": "the phrasings — the recall set in the registers people write (textbook, forum, chat)",
     "modules": ["audit"], "proof": "gated: the recall gate (data/recall.json)", "check": _p_recall},
    {"stage": "preselector", "tech": "the tuned front end that rejects the image before mixing",
     "component": "the crisis net, PII redaction and the governor (a negated, believed or hypothetical sentence is never mixed down as a claim)",
     "modules": ["crisis", "redact", "audit"], "proof": "gated: the moat (data/benchmarks.json)", "check": _p_moat},
    {"stage": "mixer + local oscillator", "tech": "beats the signal down to baseband, tuned to one station",
     "component": "the extractors and slot-fillers — every phrasing of a claim kind to one packet",
     "modules": ["audit", "slotfill"], "proof": "gated: the front door (data/frontdoor.json)", "check": _p_frontdoor},
    {"stage": "IF filter", "tech": "one intermediate frequency; the sharp filter built once",
     "component": "the packet specs — one shape per verifier, admitted by their own goldens",
     "modules": ["verifiers", "derivation"], "proof": "gated: the admitted specs (data/benchmarks.json)", "check": _p_specs},
    {"stage": "limiter", "tech": "amplitude clipped before the message is read",
     "component": "stated precision and the governor — assertion strength stripped, the hedge read as the window",
     "modules": ["verifiers.base", "audit"], "proof": "pinned: the stated-precision and failure-report tests",
     "check": _pinned("test_stated_precision.py", "test_failure_report_2026_10_08.py")},
    {"stage": "discriminator", "tech": "reads the message off the structure alone",
     "component": "the domain verifiers — HOLDS or BROKEN from the checkable content, never the loudness",
     "modules": ["verifiers"], "proof": "gated: the domain benchmarks (data/benchmarks.json)", "check": _p_domains},
    {"stage": "AGC", "tech": "the output the same size whatever the input's loudness",
     "component": "the fixed verdict frame — HOLDS, BROKEN, PARTIAL, INCOMPLETE, DECLINED, NOTHING_TO_CHECK",
     "modules": ["audit", "web.api"], "proof": "pinned: the API and claim-grammar tests",
     "check": _pinned("test_api.py", "test_claim_grammar.py")},
    {"stage": "audio stage", "tech": "the message rendered for the listener",
     "component": "the receipt and the worked trail — /verify, the MCP verify door, the lead door",
     "modules": ["receipts", "mcp.server", "lead"], "proof": "gated: the live assay through the served API", "check": _p_assay},
    {"stage": "speaker", "tech": "the surface the listener hears",
     "component": "the two faces, .com and .org, one engine (api.serve_many)",
     "modules": ["web.api"], "proof": "boot: the launch roll-call, every subsystem checked in", "check": _p_boot},
    {"stage": "squelch", "tech": "silence rather than static when no station is tuned",
     "component": "NOTHING_TO_CHECK — a phrasing no extractor reaches is answered with silence, never a guess",
     "modules": ["audit"], "proof": "gated: the unreached recall rows (data/recall.json)", "check": _p_squelch},
    {"stage": "duplexer", "tech": "transmit and receive on one antenna without deafening the receiver",
     "component": "the airlock, the diode and the alignment gate — what comes in through the door is gated before it joins the keeping",
     "modules": ["airlock"], "proof": "pinned: the alignment and no-LLM-in-the-loop tests",
     "check": _pinned("test_alignment.py", "test_no_llm_in_the_loop.py")},
    {"stage": "power supply (cathode)", "tech": "the source of every electron the tube moves",
     "component": "the keeping — the corpus and the frozen cache; nothing on the plate came from anywhere else",
     "modules": ["corpus", "frozen_cache"], "proof": "boot: the keeping loaded at the launch roll-call", "check": _p_keeping},
]

WHOLE: List[Dict[str, Any]] = [
    {"gate": "benchmarks — domains", "check": _p_domains},
    {"gate": "benchmarks — the moat", "check": _p_moat},
    {"gate": "the live assay", "check": _p_assay},
    {"gate": "the front door", "check": _p_frontdoor},
    {"gate": "the recall set", "check": _p_recall},
]


def _run(check: Callable[[Path], Any], data: Path) -> Dict[str, Any]:
    try:
        ok, read = check(data)
    except Exception as e:  # noqa: BLE001 — a proof that cannot be read is unproven, never a lamp lit
        ok, read = None, f"could not read the proof: {type(e).__name__}"
    status = "proven" if ok else ("failing" if ok is False else "unproven")
    return {"ok": bool(ok), "status": status, "read": read}


def status(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    """The receiver, stage by stage, and whether it is complete. Pure over the gate artifacts on disk."""
    data = Path(data_dir) if data_dir else _data_dir()
    stages = []
    for s in STAGES:
        r = _run(s["check"], data)
        stages.append({"stage": s["stage"], "tech": s["tech"], "component": s["component"], "modules": s["modules"],
                       "proof": s["proof"], **r})
    whole = [{"gate": w["gate"], **_run(w["check"], data)} for w in WHOLE]
    proven = [s["stage"] for s in stages if s["ok"]]
    missing = [s["stage"] for s in stages if not s["ok"]]
    whole_ok = all(w["ok"] for w in whole)
    complete = not missing and whole_ok
    return {
        "stages": stages,
        "proven": len(proven), "total": len(stages), "missing": missing,
        "whole": {"ok": whole_ok, "gates": whole,
                  "note": "the sum is greater than the parts: the whole is proven end to end by the deploy gate's own "
                          "lines, never inferred from the stages"},
        "complete": complete,
        "read": (f"complete — {len(stages)}/{len(stages)} stages proven and the whole proven end to end" if complete else
                 f"incomplete — {len(proven)}/{len(stages)} stages proven" + (f"; not yet: {', '.join(missing)}" if missing else "")
                 + ("" if whole_ok else "; the whole is not proven end to end here")),
        "model": {
            "names": "each stage keeps its current radio name and is bound to the component under the name the code already uses",
            "proof": "gated = read from a deploy-gate artifact (never typed in); pinned = the tests on disk; boot = the launch roll-call",
            "complete": "every stage proven AND the whole proven by the gate lines — all components present and functioning correctly",
        },
    }
