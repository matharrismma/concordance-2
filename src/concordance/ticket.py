"""THE WINNING TICKET — pruning as a MASK over the keeping (Matt, 2026-10-31: "look at neural networks and the
winning ticket theory. We need a pruning method and SOP." · "Transformers, language models and diffusion models.").

What was found (cited), and what carries over:
  Frankle & Carbin (ICLR 2019) — a dense network holds a sparse subnetwork that, trained alone from the SAME
    initialization, matches the whole; found by iterative magnitude pruning: prune the smallest p%, RESET the
    survivors, retrain, repeat. Zhou et al. (2019): the ticket is a MASK. Frankle et al. (2020): rewind, don't restart.
  Sun et al. (Wanda, 2023) / Frantar & Alistarh (SparseGPT, 2023) — at LLM scale prune ONE-SHOT, no retraining, by
    magnitude × input ACTIVATION: importance is measured under real inputs, never assumed from size.
  Michel et al. / Voita et al. (2019) — prune STRUCTURED units (whole heads); the survivors are the specialised ones.
  Sanh et al. (2020) — movement pruning: keep what moves toward use.
  Fang et al. (Diff-Pruning, NeurIPS 2023) — importance is per TIMESTEP across the trajectory; the steps that
    contribute nothing to structure are disregarded. DeepCache — reuse across steps; nothing is wiped.

Carried over: a UNIT is structured and reversible (a face's scope word, a resolver synonym, a road, a card) — never a
verifier, the kernel, a receipt, the ledger, Scripture, or the crisis backstop. IMPORTANCE = MAGNITUDE (the unit's
static trust: specificity, authority tier, relationship band) × ACTIVATION (how often the gates and real traffic
exercised it in a DATED window — a logarithm for each timestamp, never a running total). The ticket is a VERSIONED
MASK: data/ticket/mask.json is current, every version is kept beside it (the workbench is in the river — no wipe), and
a regression REWINDS to the previous version. "Retrain" here is RE-GATE: the 0-FP gates must hold with the mask on.
What does NOT carry over: we never retrain, never reinitialise, never delete. A unit that fired in any gate is never
masked — the gates are our test set, and a ticket that fails the test set is not a ticket.

Pure where it can be: `importance`, `propose`, `imp` take their measure / gate / apply as functions and are tested
without the box; the store is a small JSON file under CONCORDANCE_DATA_DIR with mtime hot-reload, so the live engine
sees a new version without a restart and an absent file means NOTHING is masked (exact prior behaviour).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

UNIT_KINDS = ("scope", "synonym", "road", "card")               # what may be masked — structured, reversible
PROTECTED = ("verifier", "kernel", "receipt", "ledger", "scripture", "crisis")   # never units at all

Units = Dict[str, Tuple[float, int]]      # unit id -> (magnitude, fires in the window)


# ── importance and the proposal (pure) ────────────────────────────────────────────────────────────────

def importance(magnitude: float, fires: int) -> float:
    """Wanda's form: |w| · ‖x‖ — static trust × measured exercise. Zero when a unit never fired in the window."""
    return float(magnitude) * float(max(0, int(fires)))


def propose(units: Units, p: float, protect: Iterable[str] = ()) -> List[str]:
    """The units to mask this round: at most p of ALL units, drawn only from the DEAD (fires == 0, not protected),
    least magnitude first (a generic word shared across faces is the likeliest false route), then by id. A unit that
    fired is never proposed — the gates are the test set. Deterministic."""
    if not units or p <= 0:
        return []
    prot = set(protect)
    dead = [(mag, uid) for uid, (mag, fires) in units.items() if int(fires) <= 0 and uid not in prot]
    dead.sort(key=lambda t: (t[0], t[1]))
    n = min(len(dead), max(1, int(math.ceil(p * len(units)))))
    return [uid for _, uid in dead[:n]]


# ── the store: a versioned mask, every version kept, hot-reloaded ────────────────────────────────────

def _dir() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "ticket"


def _current_path() -> Path:
    return _dir() / "mask.json"


def receipt(mask: Dict[str, Any]) -> str:
    """The mask's own hash — over what it masks and when it was measured, canonical JSON. Carried as `parent` by the
    next version so the chain of tickets is a river you can walk back."""
    body = {"version": mask.get("version"), "masked": mask.get("masked"), "window": mask.get("window")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def empty_mask() -> Dict[str, Any]:
    return {"version": 0, "measured_at": None, "window": None, "parent": None,
            "masked": {k: [] for k in UNIT_KINDS}, "gates": {}, "sparsity": {}}


def versions() -> List[int]:
    d = _dir()
    if not d.exists():
        return []
    out = []
    for p in d.glob("mask.v*.json"):
        try:
            out.append(int(p.stem.split(".v", 1)[1]))
        except ValueError:
            continue
    return sorted(out)


def load_version(n: int) -> Optional[Dict[str, Any]]:
    p = _dir() / f"mask.v{n}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


_UNSET = object()                     # distinct from "no file" (None): the cache has never been read
_cache: Dict[str, Any] = {"sig": _UNSET, "mask": None, "sets": {}}


def reset_cache() -> None:
    """Force the next `current()` to re-read the file (after a write, or when the data dir changes)."""
    _cache["sig"] = _UNSET


def current() -> Dict[str, Any]:
    """The mask in force — hot-reloaded by (mtime, size); an absent file is the empty mask (nothing masked)."""
    p = _current_path()
    try:
        st = p.stat()
        sig = (st.st_mtime_ns, st.st_size)
    except OSError:
        sig = None
    if sig != _cache["sig"]:
        mask = empty_mask()
        if sig is not None:
            try:
                mask = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                mask = empty_mask()          # a corrupt file masks nothing — fail open to the dense keeping, never silently narrow
        _cache["sig"], _cache["mask"] = sig, mask
        _cache["sets"] = {k: set(v) for k, v in (mask.get("masked") or {}).items() if isinstance(v, list)}
    return _cache["mask"]


def masked(kind: str, unit: str) -> bool:
    """Is this unit masked by the ticket in force? O(1) after the first read."""
    current()
    s = _cache["sets"].get(kind)
    return bool(s) and unit in s


def save(masked_units: Dict[str, List[str]], *, window: Optional[Dict[str, Any]] = None,
         gates: Optional[Dict[str, Any]] = None, totals: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """Write the NEXT version (parent = the current receipt) and make it current. Versions are never overwritten."""
    cur = current()
    n = (max(versions()) if versions() else int(cur.get("version") or 0)) + 1
    mask = {
        "version": n,
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": window,
        "parent": receipt(cur) if cur.get("version") else None,
        "masked": {k: sorted(set(masked_units.get(k, []))) for k in UNIT_KINDS},
        "gates": gates or {},
        "sparsity": {k: {"masked": len(set(masked_units.get(k, []))), "total": int((totals or {}).get(k, 0))}
                     for k in UNIT_KINDS if (totals or {}).get(k)},
    }
    mask["receipt"] = receipt(mask)
    d = _dir()
    d.mkdir(parents=True, exist_ok=True)
    body = json.dumps(mask, indent=1, ensure_ascii=False, sort_keys=True)
    (d / f"mask.v{n}.json").write_text(body, encoding="utf-8")
    tmp = d / "mask.json.tmp"
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, _current_path())
    reset_cache()
    return mask


def rewind() -> Dict[str, Any]:
    """Make the PREVIOUS version current again (the newest stays on disk — the river keeps every table top). With
    nothing to rewind to, the empty mask is written: nothing masked."""
    cur = current()
    n = int(cur.get("version") or 0)
    prev = load_version(n - 1) if n > 1 else None
    body = prev if prev is not None else empty_mask()
    d = _dir()
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "mask.json.tmp"
    tmp.write_text(json.dumps(body, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    os.replace(tmp, _current_path())
    reset_cache()
    return body


# ── the loop: iterative pruning with rewind (pure in its parts) ──────────────────────────────────────

def imp(measure_fn: Callable[[], Dict[str, Units]],
        apply_fn: Callable[[Dict[str, List[str]]], Any],
        gate_fn: Callable[[], Tuple[bool, Dict[str, Any]]],
        *, p0: float = 0.2, p_min: float = 0.05, rounds: int = 6,
        protect: Iterable[str] = (), rewind_fn: Callable[[], Any] = rewind) -> List[Dict[str, Any]]:
    """Iterative pruning: MEASURE units per kind → PROPOSE the dead p → APPLY (write a candidate version) → GATE.
    A pass is accepted and the next round prunes further; a regression REWINDS and halves p. Stops when nothing dead
    remains, p falls under p_min, or the rounds run out. Returns the history, one row per round — the SOP's report."""
    history: List[Dict[str, Any]] = []
    p = float(p0)
    already: Dict[str, Set[str]] = {k: set() for k in UNIT_KINDS}
    for r in range(1, int(rounds) + 1):
        if p < p_min:
            history.append({"round": r, "stop": f"p {p:.3f} < p_min {p_min}"})
            break
        measured = measure_fn()
        proposal: Dict[str, List[str]] = {}
        for kind, units in measured.items():
            prot = set(protect) | already.get(kind, set())
            pick = propose(units, p, protect=prot)
            if pick:
                proposal[kind] = pick
        if not proposal:
            history.append({"round": r, "stop": "nothing dead left to mask"})
            break
        cumulative = {k: sorted(already.get(k, set()) | set(proposal.get(k, []))) for k in UNIT_KINDS}
        apply_fn(cumulative)
        ok, detail = gate_fn()
        row = {"round": r, "p": p, "proposed": {k: len(v) for k, v in proposal.items()}, "gate": bool(ok), "detail": detail}
        if ok:
            for k, v in proposal.items():
                already.setdefault(k, set()).update(v)
            row["accepted"] = True
        else:
            rewind_fn()
            p = p / 2.0
            row["accepted"] = False
            row["rewound"] = True
        history.append(row)
    return history
