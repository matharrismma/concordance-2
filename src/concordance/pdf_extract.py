"""Extract the usable TEXT from a PDF — sovereign first, robust when a library is present.

The engine has zero required dependencies. So the floor is a small **stdlib** extractor (zlib to inflate
the content streams, then pull the text-showing string operands) that handles the common case: a PDF
whose pages carry a real text layer in standard encoding. The optional ceiling: if `pypdf` happens to be
installed, use it for the hard cases (odd fonts, kerning arrays) — lazy, never required.

What it does NOT do: OCR a scanned/image-only PDF (no text layer to read), or decode custom CID/CMap
fonts. Those return little or nothing — honestly. The intake keeps the LOCATION regardless; the extracted
text is the usable form when there is one. Never raises: on any trouble it returns "".
"""
from __future__ import annotations

import re
import zlib
from typing import List

_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\n?endstream", re.DOTALL)
_LIT = re.compile(rb"\((?:[^()\\]|\\.)*\)", re.DOTALL)          # PDF literal string (...)
_NEWLINE_OPS = re.compile(rb"\b(?:Td|TD|T\*|BT|ET)\b")          # rough line boundaries


def _decode_literal(body: bytes) -> bytes:
    """Decode a PDF literal string body (the bytes between the parens), handling PDF escapes."""
    out = bytearray()
    i, n = 0, len(body)
    esc = {110: 10, 114: 13, 116: 9, 98: 8, 102: 12, 40: 40, 41: 41, 92: 92}
    while i < n:
        ch = body[i]
        if ch == 92 and i + 1 < n:                              # backslash escape
            nxt = body[i + 1]
            if nxt in esc:
                out.append(esc[nxt]); i += 2; continue
            if 48 <= nxt <= 55:                                 # octal \ddd
                j, dig = i + 1, b""
                while j < n and len(dig) < 3 and 48 <= body[j] <= 55:
                    dig += body[j:j + 1]; j += 1
                out.append(int(dig, 8) & 0xFF); i = j; continue
            i += 2; continue                                    # line-continuation / unknown escape
        out.append(ch); i += 1
    return bytes(out)


def _inflate(raw: bytes) -> bytes:
    for wbits in (15, -15, 47):
        try:
            return zlib.decompress(raw, wbits)
        except Exception:  # noqa: BLE001 — a stream that won't inflate is used as-is
            continue
    return raw


def _stdlib_text(pdf: bytes, max_chars: int) -> str:
    parts: List[str] = []
    total = 0
    for m in _STREAM.finditer(pdf):
        data = _inflate(m.group(1))
        # only mine streams that actually look like content (contain text operators)
        if b"Tj" not in data and b"TJ" not in data:
            continue
        for sm in _LIT.finditer(data):
            s = _decode_literal(sm.group(0)[1:-1])
            if s:
                parts.append(s.decode("latin-1", "replace"))
                total += len(s)
        parts.append("\n")
        if total > max_chars:
            break
    text = " ".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text).strip()
    return text[:max_chars]


def _pypdf_text(pdf: bytes, max_chars: int) -> str:
    import io
    import pypdf  # optional, lazy — absent on the sovereign box, present in dev
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    out, total = [], 0
    for page in reader.pages:
        t = page.extract_text() or ""
        out.append(t)
        total += len(t)
        if total > max_chars:
            break
    return "\n".join(out).strip()[:max_chars]


def _looks_like_text(s: str) -> bool:
    """Guard the stdlib floor: a PDF with embedded/CID fonts yields GLYPH CODES, not letters — high-
    entropy garbage. Only accept output that reads as real text (mostly letters/spaces, some real words),
    else return nothing. Garbage in the artifact is worse than an honest empty."""
    if len(s) < 16:
        return False
    letters = sum(ch.isalpha() or ch.isspace() for ch in s)
    words = re.findall(r"[A-Za-z]{2,}", s)
    # The RATIO is the real discriminator: glyph-code garbage is dense with punctuation/digits, so it
    # falls well below 0.82; real text (even a short line) is almost all letters and spaces.
    return (letters / len(s)) >= 0.82 and len(words) >= 4


def text(pdf_bytes: bytes, max_chars: int = 20000) -> str:
    """The usable text of a PDF, capped. Optional pypdf if present, else the stdlib floor (only when it
    reads as real text — never glyph garbage). Returns "" honestly when there is no readable text (a
    scanned/image PDF, or an encoding the floor can't read). Never raises."""
    if not pdf_bytes or pdf_bytes[:4] != b"%PDF":
        return ""
    try:
        t = _pypdf_text(pdf_bytes, max_chars)
        if t and len(t.strip()) >= 16:
            return t
    except Exception:  # noqa: BLE001 — fall through to the sovereign floor
        pass
    try:
        t = _stdlib_text(pdf_bytes, max_chars)
        return t if _looks_like_text(t) else ""
    except Exception:  # noqa: BLE001 — extraction must never crash intake
        return ""
