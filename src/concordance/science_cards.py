"""Every verifier produces a card — so the science and math join the one keeping.

The disconnect Matt named: the 70+ deterministic verifiers COMPUTE verdicts and seal them, but
the seal was not a card, so the science/math never entered the graph the Scripture and tradition
live in. The two trees stood side by side, ungrafted. This closes the seam at the one choke point
every verification passes through (`receipts.attach`): when a claim is sealed, its worked result
becomes a durable, searchable, connectable card.

Disciplines:

* **Pay once.** The card id is deterministic from the domain + the normalized claim, so the same
  fact verified a hundred times is one card — the memoized, re-checkable result.
* **Reveal, never invent.** The card body is the engine's own worked trail and its seal cite_url;
  nothing is generated. It carries `generated: false` in spirit — it is found and computed.
* **Off to the side.** Minting can never break or slow the seal it rides on: any failure is
  swallowed, and the value gate skips bare arithmetic so the graph is not flooded with "2+2=4".
* **It joins the graph.** The card lands on its domain's shelf and enters the live corpus index,
  so a search finds it immediately and the growth engine can bridge it to Scripture where it
  genuinely touches (as the RAS→reception bridge did by hand).

Persisted append-only to `verified_cards.jsonl` (a second corpus source), never rewriting the
25k-line cards.jsonl on the hot path.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
_MINTED: Optional[set] = None            # lazily loaded set of existing verified-card ids
_ALPHA = re.compile(r"[A-Za-z]{3,}")     # a named concept — not bare arithmetic
# verdicts that are a real result worth keeping; the rest (incomplete, nothing-to-check, errors)
# are not facts and do not earn a card
_REAL_VERDICTS = {"HOLDS", "CONFIRMED", "BROKEN", "TRUE", "FALSE", "VALID", "INVALID"}
# engine boilerplate that is NOT a stated claim — a bare equality carries only this
_BOILER = re.compile(r"(both sides reduce|simplifies to|holds only off|no applicable|"
                     r"reduce to the same|evaluates to)", re.I)


def _store_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "verified_cards.jsonl"


def _claim_text(result: Dict[str, Any]) -> str:
    """The STATED claim behind a verification — the trail's own claim fields only. Engine
    boilerplate (a bare equality's 'both sides reduce to...') is not a claim, so a card is
    earned only when a real claim was made."""
    parts: List[str] = []
    for step in (result.get("trail") or []):
        c = (step.get("claim") or "").strip()
        if c and not _BOILER.search(c):
            parts.append(c)
    return " · ".join(parts)[:400]


def _is_substantive(claim: str) -> bool:
    """A named concept earns a card; bare arithmetic ('2+2=4') does not flood the graph."""
    return bool(_ALPHA.search(claim))


def card_for(result: Dict[str, Any], domain: str, seal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build the card for a sealed verification — or None if it is too trivial to keep.
    Deterministic id (pay once); body is the worked trail + the seal; never generated."""
    verdict = str(result.get("verdict") or "").upper()
    if verdict not in _REAL_VERDICTS:                 # incomplete / nothing-to-check / error
        return None
    claim = _claim_text(result)
    if not claim or not _is_substantive(claim) or _BOILER.search(claim):
        return None
    dom = (domain or "mathematics").strip() or "mathematics"
    key = dom + "|" + " ".join(claim.lower().split())
    cid = "card_v_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    lines = [f"Verdict: {verdict}."]
    for step in (result.get("trail") or [])[:8]:
        d = (step.get("detail") or step.get("claim") or "").strip()
        if d:
            lines.append("• " + d)
    cite = (seal or {}).get("cite_url") or ""
    if cite:
        lines.append(f"Sealed and independently re-checkable: {cite}")
    # a scripture the claim itself names (e.g. scripture_anchors / theology verifiers) — the
    # growth engine will bridge this science card to the Word through it
    from . import growth as _growth
    refs = sorted(_growth.refs_in_text(claim))
    return {
        "id": cid, "kind": "verified",
        "title": claim[:80],
        "body": "\n".join(lines),
        "source": {"label": f"Verified by the engine — {dom}", "url": cite,
                   "ref": refs[0] if refs else "", "domain": dom, "authority_tier": "engine"},
        "shelf": dom, "box": "verified",
        "bands": ["verified", dom, verdict] + refs[:3],
        # born nested — every verified seed hangs from the created order, never an orphan on the floor
        "connections": [{"to_card_id": "card_k_spine_created_order", "relationship": "part_of",
                         "evidence": f"a verified seed of the created order ({dom})"}],
        "author": "engine", "created_at": time.time(), "updated_at": time.time(),
        "visibility": "public", "lifecycle_stage": "public", "volatility": "durable",
        "surface": "secular", "generated": False,
    }


def _load_minted() -> set:
    global _MINTED
    if _MINTED is None:
        ids = set()
        p = _store_path()
        if p.exists():
            for ln in p.read_text(encoding="utf-8").splitlines():
                ln = ln.strip()
                if ln:
                    try:
                        ids.add(json.loads(ln).get("id"))
                    except ValueError:
                        continue
        _MINTED = ids
    return _MINTED


def mint(result: Dict[str, Any], domain: str, seal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Persist the verification as a card if new, and add it to the live corpus so it is found
    immediately. Idempotent (pay once). Best-effort — returns None on skip or any failure."""
    try:
        card = card_for(result, domain, seal)
        if not card:
            return None
        with _LOCK:
            minted = _load_minted()
            if card["id"] in minted:
                return None                      # already kept — pay once
            p = _store_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(card, ensure_ascii=False) + "\n")
            minted.add(card["id"])
        try:
            from . import corpus as _corpus
            _corpus.add_to_default(card)         # searchable now, no restart
        except Exception:  # noqa: BLE001
            pass
        return card
    except Exception:  # noqa: BLE001
        return None
