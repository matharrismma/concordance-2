"""Recall — the record of a conversation, stored as cards, as it comes.

Named `recall`, not `keep`: "the keep" is already the operator's gate and dashboard,
and "the keeping" is already the corpus. This is the third thing — what a person's own
conversation leaves behind that is worth recalling later.

*"We keep the record. Storing cards for them as they come. We can't recall everything, but we
recall everything that is important."*

The second half of that is the whole design. A companion that stored every utterance would
have a transcript, not a memory — and a transcript is exactly what nobody can find anything
in. So this keeps the **durable artifacts** an exchange produced and lets the chatter go:

  - **seals**     — a re-checkable receipt. The most important thing this engine makes.
  - **scripture** — a reference the person actually reached for.
  - **words**     — a Strong's number they studied.
  - **found**     — a card from the keeping that was cited back to them.

What is deliberately NOT kept: the phrasing, the small talk, the half-thought that went
nowhere. It is still in the chain (nothing is deleted, `threads.py` holds it verbatim) — it
simply is not promoted to a card. **The chain is the record; the cards are what is worth
recalling.**

Each card lives ONCE (`stacks.py`'s superposition model) and is referenced from the
conversation's stack, so the same verse kept twice is one card in two places, never a copy.
Idempotent by construction: keeping the same conversation twice adds nothing.

Deterministic — counted from the person's own chain by `distill.digest()`. Nothing generated,
nothing inferred.
"""
from __future__ import annotations

from typing import Any, Dict, List

from . import distill, stacks, threads

_STACK = "thread"          # a conversation's stack of kept cards


def _existing_keys(thread_id: str) -> set:
    """What has already been kept from this conversation — so keeping twice is a no-op."""
    keys = set()
    for brief in (stacks.get_stack(_STACK, thread_id) or {}).get("cards", []) or []:
        card = stacks.get_card(brief.get("id"), bump=False) if isinstance(brief, dict) else None
        if card and card.get("keep_key"):
            keys.add(card["keep_key"])
    return keys


def remember(thread_id: str) -> Dict[str, Any]:
    """Promote what is worth recalling from this conversation into cards. Idempotent."""
    if not threads.get(thread_id):
        return {"ok": False, "error": "no such thread"}
    d = distill.digest(thread_id)
    if not d.get("ok"):
        return {"ok": False, "error": d.get("error", "cannot read that conversation")}

    have = _existing_keys(thread_id)
    kept: List[Dict[str, Any]] = []

    def _put(key: str, kind: str, text: str, topics: List[str], extra: Dict[str, Any]) -> None:
        if key in have:
            return                                   # already recalled — never duplicated
        card = stacks.put_card(text, kind=kind, topics=topics, source="conversation",
                               extra=dict(extra, keep_key=key, thread_id=thread_id))
        stacks.add_to_stack(_STACK, thread_id, card["id"])
        have.add(key)
        kept.append({"id": card["id"], "kind": kind, "text": text})

    # A sealed receipt is the most important thing an exchange can leave behind.
    for s in (d.get("sealed") or []):
        seal = str(s.get("seal") or "")
        if seal:
            _put(f"seal:{seal}", "seal", f"A sealed, re-checkable receipt: {seal}",
                 ["sealed"], {"seal": seal, "seq": s.get("seq")})

    for ref, n in (d.get("scripture_refs") or []):
        _put(f"ref:{ref}", "scripture", f"{ref} — reached for in this conversation ({n}×).",
             ["scripture", ref], {"ref": ref, "times": n})

    for word, n in (d.get("strongs") or []):
        _put(f"strongs:{word}", "word", f"{word} — studied in this conversation ({n}×).",
             ["word-study", word], {"strongs": word, "times": n})

    return {"ok": True, "thread_id": thread_id, "kept": kept, "count": len(kept),
            "note": "the chain keeps everything; cards keep what is worth recalling"}


def recalled(thread_id: str) -> Dict[str, Any]:
    """What has been recalled from this conversation."""
    st = stacks.get_stack(_STACK, thread_id) or {}
    out = []
    for brief in st.get("cards", []) or []:
        cid = brief.get("id") if isinstance(brief, dict) else brief
        card = stacks.get_card(cid, bump=False)
        if card:
            out.append({"id": card.get("id"), "kind": card.get("kind"),
                        "text": card.get("text"), "topics": card.get("topics") or []})
    return {"ok": True, "thread_id": thread_id, "count": len(out), "kept": out}
