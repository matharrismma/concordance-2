"""Redact — strip personal context to stable placeholders, then reapply. Sovereign.

The same shape as the National Design Studio's Rampart (CC BY 4.0): strip personal context
to stable placeholders BEFORE text is stored or sent, reapply it after. The context is
stripped and reapplied — never laundered, never lost; the original stays with the user, the
placeholder stands in everywhere else.

This is the DETERMINISTIC layer — the regex half Rampart runs first, at ~100% recall on the
checksummable / structured classes: emails, US SSNs, credit cards (Luhn-checked), IPv4
addresses, URLs. Stdlib only, zero dependencies, fully offline. The contextual ML layer
(names, free-form phone numbers) is a future opt-in (Rampart's 14.7 MB ONNX model); this
layer stands on its own and never leaves the engine.

    clean, mapping = redact("write me at a@b.com")   # -> ("write me at [EMAIL_1]", {...})
    restore(clean, mapping) == "write me at a@b.com"

Placeholders are STABLE within a text (the same value → the same token), so structure and
relationships survive the strip. A sealed record stores the redacted form; the PII never
enters the ledger. `mapping` is held by the caller (the user's side) for reveal — it is not
sealed.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

PLACEHOLDER_RE = re.compile(r"\[([A-Z]+)_(\d+)\]")


def _luhn_ok(digits: str) -> bool:
    ds = [int(c) for c in digits if c.isdigit()]
    if not (13 <= len(ds) <= 19):
        return False
    total, parity = 0, len(ds) % 2
    for i, d in enumerate(ds):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _ipv4_ok(text: str) -> bool:
    parts = text.split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


# (label, pattern, validator|None) — ORDER IS PRIORITY (first match on a span wins).
# URL before EMAIL/IP (a URL can contain both); SSN before CARD (xxx-xx-xxxx is not a card).
_RULES: List[Tuple[str, "re.Pattern[str]", object]] = [
    ("URL", re.compile(r"\bhttps?://[^\s<>\")]+", re.I), None),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), None),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), None),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b"), _luhn_ok),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), _ipv4_ok),
]


def redact(text: str) -> Tuple[str, Dict[str, str]]:
    """Strip PII to stable placeholders. Returns (clean_text, {placeholder: original})."""
    if not text or not isinstance(text, str):
        return text, {}

    spans: List[Tuple[int, int, str, str]] = []  # (start, end, label, value)
    for label, pattern, validator in _RULES:
        for m in pattern.finditer(text):
            if validator is None or validator(m.group(0)):
                spans.append((m.start(), m.end(), label, m.group(0)))

    # Resolve overlaps: sort by start, then by earliest rule priority isn't needed since we
    # keep the first non-overlapping span encountered in (start, -length) order.
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    chosen: List[Tuple[int, int, str, str]] = []
    last_end = -1
    for start, end, label, value in spans:
        if start >= last_end:
            chosen.append((start, end, label, value))
            last_end = end

    mapping: Dict[str, str] = {}
    value_to_token: Dict[Tuple[str, str], str] = {}
    counters: Dict[str, int] = {}
    out: List[str] = []
    cursor = 0
    for start, end, label, value in chosen:
        token = value_to_token.get((label, value))
        if token is None:
            counters[label] = counters.get(label, 0) + 1
            token = f"[{label}_{counters[label]}]"
            value_to_token[(label, value)] = token
            mapping[token] = value
        out.append(text[cursor:start])
        out.append(token)
        cursor = end
    out.append(text[cursor:])
    return "".join(out), mapping


def restore(text: str, mapping: Dict[str, str]) -> str:
    """Reapply the stripped context: replace each placeholder with its original value."""
    if not text or not mapping:
        return text
    return PLACEHOLDER_RE.sub(lambda m: mapping.get(m.group(0), m.group(0)), text)


def has_pii(text: str) -> bool:
    """True if redact() would strip anything — a cheap pre-check."""
    _, mapping = redact(text)
    return bool(mapping)
