"""Covenant — identity triangulated by the verses you stand on.

Matt, 2026-07-25: "The best method to know it is me across devices... very protective of privacy...
triangulate by verse. Romans 12:1-2, Matthew 7:7, John 1:1, Psalm 72. We triangulate with 4 verses."

Your identity is not a password a server keeps, nor an email, nor a phone — it is the Word you have
hidden in your heart (Psalm 119:11). Choose four verses. From them, deterministically, we derive an
Ed25519 keypair. The PUBLIC key is your handle (the server may keep it — it is public and reveals
nothing). The PRIVATE key is never stored and never transmitted; it is re-derived, on any device, from
the four verses you know by heart. To prove it is you, you sign a challenge — the verses themselves
never leave your device.

WHY THIS IS PRIVATE + PORTABLE:
  • Cross-device: you carry nothing. The four verses are in your memory; the key re-derives anywhere.
  • Zero PII: the server sees only a public key. No email, no phone, no password, no tracking.
  • Sovereign + offline: stdlib + one vendored crypto lib; canonicalization needs no corpus/network.

THE HONEST SECURITY MODEL (stated plainly, like a seed phrase):
  • Four verses are the SECRET. Anyone who knows your exact four verses can BE you — guard them like a
    seed phrase, and there is no "forgot my verses" recovery: lose them and the identity is gone.
  • Entropy: four verses chosen from ~31,000 give ~50 bits. That is NOT enough on its own against an
    offline attacker who has your public key — so the derivation is deliberately SLOW (PBKDF2-HMAC-
    SHA256, 600k iterations, chosen so the browser and Python derive the same key), making each guess
    cost real time; an optional personal passphrase adds entropy. A memory-hard KDF (scrypt/argon2) is
    a planned hardening. Choose verses that are yours, not the four most-quoted in Christendom.
  • Order does NOT matter (a set, not a sequence) — forgiving to remember; the entropy above is the
    unordered count.
"""
from __future__ import annotations

import hashlib
import re
from typing import List, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

_SALT = b"narrowhighway/covenant/v1"        # domain separation (public, not a secret)
_MIN_VERSES = 4
# PBKDF2-HMAC-SHA256, 600k iterations (OWASP-grade). Chosen so the SAME key derives byte-for-byte in
# the browser (WebCrypto PBKDF2) and in Python (hashlib) — RFC 2898 is identical on both, and needs no
# vendored crypto (CSP-safe, sovereign). Deliberately SLOW so each brute-force guess is expensive;
# a memory-hard KDF (scrypt/argon2) is a planned hardening once a matching client impl is vetted.
_ITERATIONS = 600_000

# The 66, in canonical order — canonical name → accepted forms (lower-cased, spaces removed on lookup).
# The book's ORDINAL (its 1-based position) is what the derivation uses, so "Rom"/"Romans"/"romans" all
# canonicalize identically and the identity never depends on how a name was spelled or abbreviated.
_BOOKS: List[tuple] = [
    ("Genesis", ["gen", "ge", "gn"]), ("Exodus", ["ex", "exo", "exod"]),
    ("Leviticus", ["lev", "le", "lv"]), ("Numbers", ["num", "nu", "nm", "nb"]),
    ("Deuteronomy", ["deut", "dt", "de"]), ("Joshua", ["josh", "jos", "jsh"]),
    ("Judges", ["judg", "jdg", "jg", "jdgs"]), ("Ruth", ["rth", "ru"]),
    ("1 Samuel", ["1sam", "1sa", "1sm", "1s"]), ("2 Samuel", ["2sam", "2sa", "2sm", "2s"]),
    ("1 Kings", ["1kings", "1kgs", "1ki", "1kg"]), ("2 Kings", ["2kings", "2kgs", "2ki", "2kg"]),
    ("1 Chronicles", ["1chron", "1chr", "1ch"]), ("2 Chronicles", ["2chron", "2chr", "2ch"]),
    ("Ezra", ["ezr", "ez"]), ("Nehemiah", ["neh", "ne"]), ("Esther", ["esth", "est", "es"]),
    ("Job", ["jb"]), ("Psalms", ["psalm", "ps", "psa", "psm", "pss"]),
    ("Proverbs", ["prov", "pro", "prv", "pr"]), ("Ecclesiastes", ["eccl", "ecc", "ec", "qoh"]),
    ("Song of Solomon", ["song", "songofsongs", "sos", "so", "canticles", "cant"]),
    ("Isaiah", ["isa", "is"]), ("Jeremiah", ["jer", "je", "jr"]),
    ("Lamentations", ["lam", "la"]), ("Ezekiel", ["ezek", "eze", "ezk"]),
    ("Daniel", ["dan", "da", "dn"]), ("Hosea", ["hos", "ho"]), ("Joel", ["joe", "jl"]),
    ("Amos", ["am", "amo"]), ("Obadiah", ["obad", "ob"]), ("Jonah", ["jon", "jnh"]),
    ("Micah", ["mic", "mc"]), ("Nahum", ["nah", "na"]), ("Habakkuk", ["hab", "hb"]),
    ("Zephaniah", ["zeph", "zep", "zp"]), ("Haggai", ["hag", "hg"]),
    ("Zechariah", ["zech", "zec", "zc"]), ("Malachi", ["mal", "ml"]),
    ("Matthew", ["matt", "mt", "mat"]), ("Mark", ["mrk", "mk", "mr"]),
    ("Luke", ["luk", "lk"]), ("John", ["jn", "jhn", "joh"]), ("Acts", ["act", "ac"]),
    ("Romans", ["rom", "ro", "rm"]), ("1 Corinthians", ["1cor", "1co", "1c"]),
    ("2 Corinthians", ["2cor", "2co", "2c"]), ("Galatians", ["gal", "ga"]),
    ("Ephesians", ["eph", "ephes"]), ("Philippians", ["phil", "php", "pp"]),
    ("Colossians", ["col", "co"]), ("1 Thessalonians", ["1thess", "1thes", "1th"]),
    ("2 Thessalonians", ["2thess", "2thes", "2th"]), ("1 Timothy", ["1tim", "1ti", "1tm"]),
    ("2 Timothy", ["2tim", "2ti", "2tm"]), ("Titus", ["tit", "ti"]),
    ("Philemon", ["philem", "phm", "pm"]), ("Hebrews", ["heb", "hb"]),
    ("James", ["jas", "jm", "ja"]), ("1 Peter", ["1pet", "1pe", "1pt", "1p"]),
    ("2 Peter", ["2pet", "2pe", "2pt", "2p"]), ("1 John", ["1john", "1jn", "1jo", "1j"]),
    ("2 John", ["2john", "2jn", "2jo", "2j"]), ("3 John", ["3john", "3jn", "3jo", "3j"]),
    ("Jude", ["jud", "jd"]), ("Revelation", ["rev", "re", "rv", "apocalypse", "apoc"]),
]


def _build_alias() -> dict:
    m = {}
    for i, (name, aliases) in enumerate(_BOOKS, start=1):
        forms = [name.lower().replace(" ", "")] + [a.lower().replace(" ", "") for a in aliases]
        for f in forms:
            m[f] = i
    return m


_ALIAS = _build_alias()
_REF = re.compile(r"^\s*([0-9]?\s*[A-Za-z][A-Za-z ]*?)\s*"          # book (opt. leading number)
                  r"(\d{1,3})\s*(?:[:.\s]\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?)?\s*$")


def canonical(ref: str) -> str:
    """A verse reference in a bulletproof canonical token: '<booknum> <chap>[:<v1>[-<v2>]]'. Book
    name/abbreviation and separators are normalized so every spelling of the same verse agrees.
    Raises ValueError on anything not a recognizable reference in the 66 (including a non-string
    input — a malformed client body must fail this contract the SAME way, never a raw TypeError)."""
    if not isinstance(ref, str):
        raise ValueError(f"not a verse reference: {ref!r}")
    m = _REF.match(ref or "")
    if not m:
        raise ValueError(f"not a verse reference: {ref!r}")
    book_raw, chap, v1, v2 = m.group(1), m.group(2), m.group(3), m.group(4)
    num = _ALIAS.get(re.sub(r"\s+", "", book_raw.lower()))
    if num is None:
        raise ValueError(f"unknown book: {book_raw!r}")
    out = f"{num} {int(chap)}"
    if v1:
        out += f":{int(v1)}"
        if v2:
            out += f"-{int(v2)}"
    return out


def _material(verses: List[str], passphrase: str = "") -> bytes:
    """The canonical, order-independent secret string built from the verse-set (+ optional
    passphrase). A SET, not a sequence: sorted so order does not matter; de-duplicated."""
    if not isinstance(verses, (list, tuple)):
        raise ValueError("verses must be a list")
    canon = sorted({canonical(v) for v in verses})
    if len(canon) < _MIN_VERSES:
        raise ValueError(f"need at least {_MIN_VERSES} distinct verses (got {len(canon)})")
    return ("\n".join(canon) + "\x00" + (passphrase or "")).encode("utf-8")


def _seed(verses: List[str], passphrase: str = "") -> bytes:
    return hashlib.pbkdf2_hmac("sha256", _material(verses, passphrase), _SALT, _ITERATIONS, dklen=32)


def derive(verses: List[str], passphrase: str = "") -> Ed25519PrivateKey:
    """The private key for this verse-set — re-derived on any device, never stored."""
    return Ed25519PrivateKey.from_private_bytes(_seed(verses, passphrase))


def public_id(verses: List[str], passphrase: str = "") -> str:
    """The public identity handle (hex) — safe to store/share; reveals nothing about the verses."""
    pub = derive(verses, passphrase).public_key()
    return pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def sign(verses: List[str], message: str, passphrase: str = "") -> str:
    """Prove it is you: sign a (server-issued) challenge. The verses never leave the device."""
    return derive(verses, passphrase).sign((message or "").encode("utf-8")).hex()


def strength(verses: List[str], passphrase: str = "") -> dict:
    """A non-secret, structural assessment of a verse-set's brute-force resistance — so a surface can
    NUDGE toward a stronger identity without touching the derivation (the key is byte-identical either
    way; this only advises). Entropy rises with the number of DISTINCT BOOKS the verses span (the book
    ordinal is what the derivation mixes in, so four verses from one book add little) and with an
    optional passphrase. Never raises and never reveals the verses — only counts and a plain hint.

    This is the honest, frozen-design-respecting form of "entropy hardening": four verses give ~50
    bits (stated plainly in the module docstring), which is why the KDF is deliberately slow; a
    memory-hard KDF remains a future, client-coordinated migration. Until then, the strongest lever a
    user actually controls is verse DIVERSITY + a passphrase, and this makes that legible."""
    try:
        canon = sorted({canonical(v) for v in verses})
    except (ValueError, TypeError):
        return {"ok": False, "level": "invalid",
                "note": "not four recognizable verse references in the 66 books"}
    books = {c.split(" ", 1)[0] for c in canon}
    has_pass = bool((passphrase or "").strip())
    enough = len(canon) >= _MIN_VERSES
    strong = enough and (len(books) >= 3 or has_pass)
    tips = []
    if len(books) < 3:
        tips.append("choose verses from different books — the book adds entropy")
    if not has_pass:
        tips.append("add a personal passphrase only you know")
    return {
        "ok": enough,
        "level": "strong" if strong else ("weak" if enough else "incomplete"),
        "distinct_verses": len(canon),
        "distinct_books": len(books),
        "has_passphrase": has_pass,
        "note": ("a strong, hard-to-guess verse-set" if strong
                 else ("choose four distinct verses" if not enough
                       else "guessable — " + "; ".join(tips))),
    }


def verify(public_hex: str, message: str, signature_hex: str) -> bool:
    """Server side: does this signature prove the holder of `public_hex`? No secret is held here.
    Never raises — a malformed/wrong-type field from a client body is exactly the kind of input
    this boundary function must fail closed on, not crash on (bytes.fromhex raises TypeError, not
    ValueError, for a non-str/bytes argument — e.g. a JSON body field that came through as null)."""
    try:
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex))
        pub.verify(bytes.fromhex(signature_hex), (message or "").encode("utf-8"))
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False
