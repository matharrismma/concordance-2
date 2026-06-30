"""Gateway — make the engine's privacy embeddable in anyone's pipeline.

Drop this in front of ANY LLM call (or any external service) so personal context is stripped
before the model sees it and reapplied after — the strip-context-then-reapply pattern, as a
one-liner. Sovereign: stdlib + the deterministic redact layer, runs entirely at YOUR edge —
the data never has to reach us.

    from concordance.gateway import scrub, restore, guard

    clean, mapping = scrub("email me at a@b.com")    # -> ("email me at [EMAIL_1]", {...})
    reply = my_llm(clean)                             # the model never sees the email
    final = restore(reply, mapping)                   # reapply locally

    safe_llm = guard(my_llm)                          # …or wrap it once
    final = safe_llm("email me at a@b.com")           # scrub-in, restore-out, automatically

This is the deterministic layer (emails, SSNs, cards, IPs, URLs). For contextual PII (names,
phones), the browser gateway adds the Rampart model (see site/rampart-ml.js). For a
re-checkable verification receipt, pair with derivation.verify / the /verify endpoint:
verify a claim, hand the user the seal.
"""
from __future__ import annotations

from typing import Callable, Dict, Tuple

from .redact import redact as _redact
from .redact import restore as _restore

__all__ = ["scrub", "restore", "guard"]


def scrub(text: str) -> Tuple[str, Dict[str, str]]:
    """Strip PII to stable placeholders. Returns (clean, mapping); keep the mapping to restore."""
    return _redact(text)


def restore(text: str, mapping: Dict[str, str]) -> str:
    """Reapply the stripped context — placeholders back to their original values."""
    return _restore(text, mapping)


def guard(fn: Callable[..., object]) -> Callable[..., object]:
    """Wrap a text->text callable so its input is scrubbed and its (string) output restored.

    The wrapped fn — an LLM, an API, anything external — never sees the personal context;
    callers get their answer back with the real values reapplied. Non-string outputs pass
    through untouched."""
    def wrapped(text: str, *args, **kwargs):
        clean, mapping = _redact(text)
        out = fn(clean, *args, **kwargs)
        return _restore(out, mapping) if isinstance(out, str) else out
    return wrapped
