"""TRAINING — the loop where teaching IS training (there is no train/infer wall).

Matt, 2026-09-28: "There is no difference in the model when teaching or training. That is the theory in
practice." This is that identity, made a runnable loop. One OPERATE cycle:

    SELECT a gap the keeping does not hold  (the DEMAND signal — what people keep asking for, unmet)
      → ACQUIRE it  (read a real source, find the instances, verify, BIND as cards — the proven
                     `expand.pull_and_card` / `byom.ingest` path, with all its guards)
      → REINFORCE   (stigmergy — the trail is laid by being travelled)
      → CLOSE       (the want is filled; the gap taught is now learned)

Running the cycle IS training the model — the same act by which the engine TEACHES (finds and binds a
real instance for a learner, the Cubo way). The loop only DRIVES the proven acquire path by demand and
closes the gap; it mints nothing itself, so every write guard already in force holds unchanged:
found-not-generated, verification, the alignment gate, PD provenance, and model-derived cards enter
`public_review` (a human reviews source + quality before they are shared).

GATED OFF by default (CONCORDANCE_TRAINING): `step` is a no-op until a node opts in. The acquire path is
INJECTED (`acquire_fn`), so the loop is pure, offline-testable, and never reaches for the network or the
corpus on its own — the runner wires the real path.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Dict, List, Optional, Tuple

Acquire = Callable[[str], Dict[str, Any]]


def enabled() -> bool:
    return os.environ.get("CONCORDANCE_TRAINING", "").strip().lower() in ("1", "true", "yes", "on")


def _wants():
    from . import wants
    return wants


def next_want(fold_fn: Optional[Callable[[], Dict[str, Dict[str, Any]]]] = None
              ) -> Optional[Tuple[str, Dict[str, Any]]]:
    """The strongest demand: the most-asked OPEN 'missing' want (what people keep seeking and do not
    find). The demand signal IS the teaching pressure — the loop learns what it is most asked to teach."""
    fold = fold_fn or _wants().fold
    try:
        folded = fold() or {}
    except Exception:  # noqa: BLE001 — a bad want store never crashes the loop
        return None
    cand = [(wid, w) for wid, w in folded.items()
            if isinstance(w, dict) and w.get("state") == "open" and w.get("kind") == "missing"
            and str(w.get("query") or "").strip()]
    if not cand:
        return None
    cand.sort(key=lambda kv: (-int(kv[1].get("asks") or 0), str(kv[0])))   # most-asked first, stable
    return cand[0]


def _deposit(card_ids: List[str]) -> None:
    try:
        from . import stigmergy
        stigmergy.deposit([c for c in card_ids if c])
    except Exception:  # noqa: BLE001 — reinforcement is a soft signal; never fatal
        pass


def step(*, acquire_fn: Acquire, want_id: Optional[str] = None,
         fold_fn: Optional[Callable[[], Dict[str, Dict[str, Any]]]] = None,
         close_fn: Optional[Callable[[str, str, str], Dict[str, Any]]] = None,
         deposit_fn: Optional[Callable[[List[str]], None]] = None,
         by: str = "training") -> Dict[str, Any]:
    """One turn of the loop. `acquire_fn(query)` runs the proven read→find→verify→BIND path (wire it to
    `expand.pull_and_card` for a PD source, or `byom.ingest` for a user's model) and returns at least
    `{card_id, kept}`. No-op when gated off. Nothing is minted here — acquire_fn owns the write and its
    guards; this only chooses by demand, reinforces, and closes the gap."""
    if not enabled():
        return {"status": "gated_off"}
    if want_id:
        fold = fold_fn or _wants().fold
        w = (fold() or {}).get(want_id)
        picked: Optional[Tuple[str, Dict[str, Any]]] = (want_id, w) if isinstance(w, dict) else None
    else:
        picked = next_want(fold_fn)
    if not picked:
        return {"status": "no_open_wants"}
    wid, w = picked
    query = str(w.get("query") or "").strip()
    if not query:
        return {"status": "no_open_wants"}
    res = acquire_fn(query) or {}
    card_id = str(res.get("card_id") or "")
    if not card_id:
        # acquire honestly found/kept nothing (rejected, PII, no PD source) — the want stays open
        return {"status": "nothing_kept", "want_id": wid, "query": query, "acquire": res.get("status")}
    (deposit_fn or _deposit)([card_id])
    close = (close_fn or _wants().close_want)(wid, card_id, by) or {}
    return {"status": "learned", "want_id": wid, "query": query, "card_id": card_id,
            "kept": int(res.get("kept") or 0), "trust": res.get("trust"),
            "lifecycle_stage": res.get("lifecycle_stage"), "closed": bool(close.get("ok"))}


def run(*, acquire_fn: Acquire, steps: int = 1, **kw: Any) -> Dict[str, Any]:
    """Drive the loop up to `steps` bounded turns, stopping early when no open want remains. Continuous
    training is just this, run on a cadence: the corpus grows by being used (the keeping is the model)."""
    out: List[Dict[str, Any]] = []
    for _ in range(max(1, int(steps))):
        r = step(acquire_fn=acquire_fn, **kw)
        out.append(r)
        if r.get("status") in ("gated_off", "no_open_wants"):
            break
        kw.pop("want_id", None)                    # after the first, always take the next by demand
    return {"steps": len(out), "learned": sum(1 for r in out if r.get("status") == "learned"),
            "results": out}
