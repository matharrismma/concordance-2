"""Recall — cards land, earn their usefulness, and are landed on instead of searched again.

*"Cards land, and they can be upgraded by usefulness. We need a clear method to identify the
personal cards and the cards that will benefit the group. We only search once. After that we
land on a card first."*

Named `recall`, not `keep`: "the keep" is already the operator's gate and dashboard, and "the
keeping" is already the corpus. This is the third thing — what a person's own conversation
leaves behind that is worth recalling later.

Four rules, all deterministic. No model, nothing inferred:

**1. Cards land.** An exchange promotes only its durable artifacts — a sealed receipt, a verse
reached for, a word studied. The phrasing and the small talk are not promoted; they stay in the
chain verbatim (nothing is deleted), they simply are not worth recalling. *We cannot recall
everything; we recall what is important.*

**2. Scope is decided by content, never by assertion.** A card is **communal** only if its text
contains *nothing but public identifiers* — a scripture reference, a Strong's number, a seal
hash — which is machine-checkable, so the claim is verified rather than trusted. Anything
carrying a person's own words is **personal**, and personal never becomes communal by any path.
`classify()` is deliberately conservative: what it cannot prove public, it calls personal. That
error costs a shareable card; the opposite error would leak somebody's life.

**3. Usefulness is earned, and counted across people.** A card is upgraded when it is landed on
again — and the signal that matters is **distinct conversations**, not raw hits. One
conversation returning proves it useful *to them*; several different conversations landing on
the same card is the only honest evidence it would **benefit the group**.

**4. We search once.** When a card lands it is indexed under the artifact it names. Next time
that verse or word comes up the index answers first and no search runs. The card is the door;
the search was only how the door got built.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from . import distill, stacks, threads
from .ask import _REF, _STRONGS

_STACK = "thread"          # a conversation's stack of landed cards
_INDEX = "landing"         # artifact key -> the card to land on

COMMUNAL, PERSONAL = "communal", "personal"

# Tiers a card EARNS. Never asserted — always counted.
KEPT, USEFUL, SHARED = "kept", "useful", "shared"
_USEFUL_AT, _SHARED_AT = 2, 3      # distinct conversations

_SEAL = re.compile(r"https?://\S+/s/[0-9a-f]{8,}", re.I)
_PUBLIC_SHAPES = (_REF, _STRONGS, _SEAL)
_OUR_WORDS = re.compile(
    r"\b(reached for|studied|in this conversation|a sealed|re-?checkable|receipt|times?)\b", re.I)


# ── scope: decided by content, checkable by anyone ─────────────────────

def classify(text: str, kind: str = "") -> str:
    """COMMUNAL only if the text carries public identifiers and nothing personal."""
    t = (text or "").strip()
    if not t or kind not in ("seal", "scripture", "word"):
        return PERSONAL                       # only the three artifact kinds can be communal
    if not any(rx.search(t) for rx in _PUBLIC_SHAPES):
        return PERSONAL                       # names nothing public -> not shareable
    rest = t
    for rx in _PUBLIC_SHAPES:
        rest = rx.sub(" ", rest)
    rest = _OUR_WORDS.sub(" ", rest)          # strip the frame we generated around it
    if re.search(r"[@#$]|\b\d{3,}\b", rest):  # a stray detail crept in -> treat as personal
        return PERSONAL
    return COMMUNAL


def is_communal(card: Dict[str, Any]) -> bool:
    """Re-check a stored card from its own text — never trust the stored label."""
    return classify(card.get("text", ""), card.get("kind", "")) == COMMUNAL


# ── landing: search once, then land ────────────────────────────────────

def artifact_keys(text: str) -> List[str]:
    """The public artifacts a piece of text names — the keys a card can be landed on."""
    keys = []
    for m in _STRONGS.finditer(text or ""):
        keys.append("strongs:" + m.group(1).upper())
    for m in _REF.finditer(text or ""):
        keys.append("ref:" + m.group(0).strip())
    return keys


def land(query: str, *, thread_id: str = "") -> Dict[str, Any]:
    """Already hold a card for what is being asked? Land on it — do not search again."""
    hits, seen = [], set()
    for key in artifact_keys(query):
        for brief in (stacks.get_stack(_INDEX, key) or {}).get("cards", []):
            cid = brief.get("id")
            if not cid or cid in seen:
                continue
            card = stacks.get_card(cid)
            if not card:
                continue
            seen.add(cid)
            up = note_use(cid, thread_id) if thread_id else {}
            hits.append({"id": cid, "kind": card.get("kind"), "text": card.get("text"),
                         "scope": up.get("scope") or (COMMUNAL if is_communal(card) else PERSONAL),
                         "tier": up.get("tier") or card.get("tier_earned", KEPT),
                         "conversations": up.get("conversations",
                                                 len(set(card.get("threads_seen") or []))),
                         "landed_on": key})
    return {"ok": True, "landed": bool(hits), "count": len(hits), "cards": hits,
            "note": ("landed on a card already held — no search was run" if hits
                     else "nothing held for this yet — search, and what lands is indexed")}


# ── usefulness: earned across distinct conversations ───────────────────

def _tier_for(threads_seen: List[str], scope: str) -> str:
    n = len(set(threads_seen or []))
    if n >= _SHARED_AT and scope == COMMUNAL:
        return SHARED          # several different conversations -> it would benefit the group
    if n >= _USEFUL_AT:
        return USEFUL          # returned to -> useful to them
    return KEPT


def note_use(card_id: str, thread_id: str) -> Dict[str, Any]:
    """Record that a conversation landed here, and upgrade the card if it has earned it."""
    card = stacks.get_card(card_id, bump=False)
    if not card:
        return {"ok": False, "error": "no such card"}
    seen = list(card.get("threads_seen") or [])
    if thread_id and thread_id not in seen:
        seen.append(thread_id)
    scope = COMMUNAL if is_communal(card) else PERSONAL
    tier = _tier_for(seen, scope)
    stacks.update_card(card_id, {"threads_seen": seen, "scope": scope, "tier_earned": tier})
    return {"ok": True, "id": card_id, "scope": scope, "tier": tier,
            "conversations": len(set(seen))}


def for_the_group(min_conversations: int = _SHARED_AT) -> Dict[str, Any]:
    """Cards that have EARNED a place in the shared keeping: communal, and proven useful across
    several different conversations. Candidates only — nothing is published automatically, and a
    personal card can never appear here."""
    out, seen = [], set()
    for key in stacks.stack_keys(_INDEX):
        for brief in (stacks.get_stack(_INDEX, key) or {}).get("cards", []):
            cid = brief.get("id")
            if not cid or cid in seen:
                continue
            card = stacks.get_card(cid, bump=False)
            if not card or not is_communal(card):
                continue
            seen.add(cid)
            n = len(set(card.get("threads_seen") or []))
            if n >= min_conversations:
                out.append({"id": cid, "kind": card.get("kind"), "text": card.get("text"),
                            "conversations": n, "tier": card.get("tier_earned", KEPT)})
    out.sort(key=lambda c: (-c["conversations"], c["id"]))
    return {"ok": True, "count": len(out), "candidates": out,
            "note": "communal and proven across conversations — candidates, never auto-published"}


# ── landing what an exchange left behind ───────────────────────────────

def _existing_keys(thread_id: str) -> set:
    keys = set()
    for brief in (stacks.get_stack(_STACK, thread_id) or {}).get("cards", []) or []:
        card = stacks.get_card(brief.get("id"), bump=False) if isinstance(brief, dict) else None
        if card and card.get("keep_key"):
            keys.add(card["keep_key"])
    return keys


def remember(thread_id: str) -> Dict[str, Any]:
    """Promote what is worth recalling into cards, index them for landing. Idempotent."""
    if not threads.get(thread_id):
        return {"ok": False, "error": "no such thread"}
    d = distill.digest(thread_id)
    if not d.get("ok"):
        return {"ok": False, "error": d.get("error", "cannot read that conversation")}

    have = _existing_keys(thread_id)
    kept: List[Dict[str, Any]] = []

    def _put(key: str, kind: str, text: str, topics: List[str], extra: Dict[str, Any]) -> None:
        if key in have:
            return
        # Already carded by someone else? Then this conversation LANDS on it rather than
        # minting a second card — one card, many stacks, and the use is counted.
        existing = (stacks.get_stack(_INDEX, key) or {}).get("cards", [])
        if existing:
            cid = existing[0].get("id")
            stacks.add_to_stack(_STACK, thread_id, cid)
            up = note_use(cid, thread_id)
            have.add(key)
            kept.append({"id": cid, "kind": kind, "text": text,
                         "scope": up.get("scope"), "tier": up.get("tier"), "landed": True})
            return
        scope = classify(text, kind)
        card = stacks.put_card(text, kind=kind, topics=topics, source="conversation",
                               extra=dict(extra, keep_key=key, thread_id=thread_id,
                                          scope=scope, tier_earned=KEPT, threads_seen=[thread_id]))
        stacks.add_to_stack(_STACK, thread_id, card["id"])
        stacks.add_to_stack(_INDEX, key, card["id"])      # search once; land here next time
        have.add(key)
        kept.append({"id": card["id"], "kind": kind, "text": text, "scope": scope,
                     "tier": KEPT, "landed": False})

    for s in (d.get("sealed") or []):
        seal = str(s.get("seal") or "")
        if seal:
            _put(f"seal:{seal}", "seal", f"A sealed, re-checkable receipt: {seal}",
                 ["sealed"], {"seal": seal, "seq": s.get("seq")})
    for ref, _n in (d.get("scripture_refs") or []):
        _put(f"ref:{ref}", "scripture", f"{ref} — reached for in this conversation.",
             ["scripture", ref], {"ref": ref})
    for word, _n in (d.get("strongs") or []):
        _put(f"strongs:{word}", "word", f"{word} — studied in this conversation.",
             ["word-study", word], {"strongs": word})

    return {"ok": True, "thread_id": thread_id, "kept": kept, "count": len(kept),
            "note": "the chain keeps everything; cards keep what is worth recalling"}


def recalled(thread_id: str) -> Dict[str, Any]:
    """What this conversation left behind, with the scope and tier each card has earned."""
    out = []
    for brief in (stacks.get_stack(_STACK, thread_id) or {}).get("cards", []) or []:
        card = stacks.get_card(brief.get("id"), bump=False)
        if card:
            out.append({"id": card.get("id"), "kind": card.get("kind"), "text": card.get("text"),
                        "scope": COMMUNAL if is_communal(card) else PERSONAL,
                        "tier": card.get("tier_earned", KEPT),
                        "conversations": len(set(card.get("threads_seen") or []))})
    return {"ok": True, "thread_id": thread_id, "count": len(out), "kept": out}
