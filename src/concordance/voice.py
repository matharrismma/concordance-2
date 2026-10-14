"""VOICE — the spoken floor, the spoken ceiling, and the words it speaks.

Two concerns, one voice:

SYNTHESIS (the floor and the ceiling):
  FLOOR (always, sovereign, offline, free): the browser's own speech (site/speak.js → NHSpeak). No key,
  no network, no dependency — a word can always be spoken.
  CEILING (optional): when ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are present, `/speak` returns audio
  in the operator's own cloned voice. If the key is absent or the upstream call fails, speak() returns
  None and the caller falls back to the floor — the ceiling never becomes a single point of failure.
  Content-addressed cache (save-once-use-forever): audio for a given (voice, model, text) is synthesized
  once and reused, so the paid API is called at most once per distinct utterance. Cache lives under
  data/audio/ (gitignored). Conduit, not source: it voices FOUND words; it never generates them.

SELECTION (whose words — the house shepherd, composition layer #4, 2026-10-14):
  The connective tissue that meets a person and draws the thread should sound like Matt shepherding — so
  it is composed from his OWN writing, a verbatim unit SELECTED to fit the moment, never generated, and
  his cloned voice (above) speaks it. see() is the house tier; the public-domain witness cloud
  (witness.py) stands beside it. Source: data/voice_lines.jsonl (his Christian writing, built by
  tools/seed_voice.py). illustrate() reaches his NARRATIVE (the books, data/voice_book_lines.jsonl) for a
  STORY surface, where his narrative voice belongs. His personal content — box-side data like
  witnesses.jsonl, never committed, never treated as public-domain.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

# ══ SYNTHESIS — the spoken ceiling over the browser floor ════════════════════════════════════════════
_API = "https://api.elevenlabs.io/v1"
_MODEL = "eleven_multilingual_v2"   # matches the 1.0 render pipeline
_MAX_CHARS = 1200                   # a guard: never ship an essay to the paid API in one call
_TIMEOUT = 60


def _key() -> str:
    return (os.environ.get("ELEVENLABS_API_KEY") or "").strip()


def _voice_id() -> str:
    return (os.environ.get("ELEVENLABS_VOICE_ID") or "").strip()


def configured() -> bool:
    """True when the operator's voice is wired (key + voice_id both present)."""
    return bool(_key() and _voice_id())


def _cache_dir() -> Path:
    base = os.environ.get("CONCORDANCE_AUDIO_DIR") or (
        (os.environ.get("CONCORDANCE_DATA_DIR") or "data") + "/audio")
    d = Path(base)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _digest(text: str) -> str:
    """Content address of the utterance — voice + model + text, so a re-voicing or a text change yields a
    fresh file and the cache never serves the wrong audio."""
    h = hashlib.sha256()
    h.update((_voice_id() + "|" + _MODEL + "|" + text).encode("utf-8"))
    return h.hexdigest()


def speak(text: str):
    """Return (mp3_bytes, "hit"|"miss") in the operator's voice, or None.

    None means 'ceiling unavailable — use the browser floor': unconfigured env, empty text, or a failed
    upstream call. Never raises. Caches the audio content-addressed so the paid API is touched at most
    once per distinct utterance.
    """
    text = (text or "").strip()
    if not text or not configured():
        return None
    if len(text) > _MAX_CHARS:
        text = text[:_MAX_CHARS]
    cache = _cache_dir() / (_digest(text) + ".mp3")
    if cache.is_file():
        try:
            return cache.read_bytes(), "hit"
        except OSError:
            pass  # fall through and re-synthesize
    payload = {
        "text": text,
        "model_id": _MODEL,
        "voice_settings": {
            "stability": 0.5, "similarity_boost": 0.85, "style": 0.0, "use_speaker_boost": True,
        },
    }
    req = urllib.request.Request(
        f"{_API}/text-to-speech/{_voice_id()}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"xi-api-key": _key(), "Content-Type": "application/json", "accept": "audio/mpeg"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            audio = r.read()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return None
    if not audio:
        return None
    try:
        cache.write_bytes(audio)
    except OSError:
        pass  # transient audio still served this call; cache is best-effort
    return audio, "miss"


# ══ SELECTION — whose words (the house shepherd: Matt's own, verbatim, fit) ═══════════════════════════
_STOP = frozenset((
    "the a an of to and but in on for is are was were be am his her my your their our its it he she they "
    "we you i do does did not no as at by or if with from about into over under out up down this that these "
    "those his who what when where why how so all any can could would should will me us him them not").split())

_CACHE: Dict[str, Any] = {"rows": None, "mtime": 0.0}
_BOOK_CACHE: Dict[str, Any] = {"rows": None, "mtime": 0.0}
_REFKEY = re.compile(r"^\s*(\d?\s?[A-Za-z][A-Za-z ]*?)\s+(\d+)\s*:")


def _path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "voice_lines.jsonl"


def _book_path() -> Path:
    base = os.environ.get("CONCORDANCE_DATA_DIR", "").strip() or "data"
    return Path(base) / "voice_book_lines.jsonl"


def _tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(w) > 2 and w not in _STOP}


def _ref_key(ref: str) -> str:
    """'Matthew 6:25-34' -> 'matthew 6' — the book+chapter, so a shared Scripture theme reads as fit."""
    m = _REFKEY.match(ref or "")
    return (m.group(1).strip().lower() + " " + m.group(2)) if m else ""


def _load(path: Path, cache: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        mt = path.stat().st_mtime
    except OSError:
        return []
    if cache["rows"] is not None and cache["mtime"] == mt:
        return cache["rows"]
    rows: List[Dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if str(r.get("text") or "").strip():
                    rows.append(r)
    except Exception:  # noqa: BLE001 — no corpus is an honest silence, never a crash
        rows = []
    cache["rows"], cache["mtime"] = rows, mt
    return rows


def _rows() -> List[Dict[str, Any]]:
    return _load(_path(), _CACHE)


def _book_rows() -> List[Dict[str, Any]]:
    return _load(_book_path(), _BOOK_CACHE)


def see(text: str, *, ref: str = "", k: int = 1) -> Dict[str, Any]:
    """Matt's own words that most fit this moment — his verbatim unit, attributed, or honestly empty where
    his writing does not reach it. `ref` is the anchor the Word landed on; a unit that sits on the same
    Scripture (book+chapter) is a strong fit. Ranked by shared subject words; a candidate must share the
    theme (>=2), so a stray word cannot pull an off-key reflection. Proposes; never confirms."""
    q = _tokens(text) | _tokens(ref)
    anchor = _ref_key(ref)
    rows = _rows()
    scored = []
    for i, r in enumerate(rows):
        ut = _tokens((r.get("text") or "") + " " + (r.get("ref") or ""))
        overlap = len(q & ut)
        if anchor and _ref_key(r.get("ref") or "") == anchor:   # same Scripture theme — a strong fit
            overlap += 3
        if overlap >= 2:
            scored.append((overlap, -i, r))
    scored.sort(key=lambda x: (-x[0], x[1]))
    seeing = [{"text": r.get("text"), "source": r.get("source"), "ref": r.get("ref"), "by": r.get("by")}
              for _o, _i, r in scored[:max(1, int(k))]]
    return {"seeing": seeing, "gathered": len(rows), "proposes": True, "confirms": False,
            "note": ("his own words, fit to this and spoken in his voice" if seeing else
                     "his writing does not reach this one yet")}


# A second safety at serve-time for the NARRATIVE tier — a line that slipped the extractor's filter still
# never surfaces. The story surface tolerates atmosphere, never the graphic (same stoplist as the seed).
_DARK = re.compile(r"\b(kill(ed|ing|s)?|murder|blood(y|ied)?|corpse|rape|slaughter|gun|knife|stab|"
                   r"damn(ed|it)?|bastard|whore|bitch|fuck|shit|naked|sex|breast|thigh|drunk|whiskey|"
                   r"vomit|piss|rot(ting|ted)?|maggot|scream(ed|ing)?|torture)\b", re.I)


def illustrate(theme: str, *, k: int = 1, min_fit: int = 2) -> Dict[str, Any]:
    """Matt's NARRATIVE (the books) that echoes a theme — for a STORY surface, where his narrative voice
    belongs (beneath a parable, never as counsel to the hurting). `theme` is the parable's shape-words.
    Ranked by shared subject words; a candidate must share >= min_fit of them AND pass the dark gate, so
    an atmospheric line that merely grazed a word, or a grim line that slipped the extractor, is dropped.
    Verbatim, attributed, fit — honestly empty where no passage reaches it. Proposes; never confirms."""
    q = _tokens(theme)
    if not q:
        return {"seeing": [], "gathered": 0, "proposes": True, "confirms": False, "note": "no theme"}
    rows = _book_rows()
    scored = []
    for i, r in enumerate(rows):
        body = str(r.get("text") or "")
        if _DARK.search(body):
            continue
        overlap = len(q & _tokens(body))
        if overlap >= min_fit:
            scored.append((overlap, -i, r))
    scored.sort(key=lambda x: (-x[0], x[1]))
    seeing = [{"text": r.get("text"), "source": r.get("source"), "by": r.get("by")}
              for _o, _i, r in scored[:max(1, int(k))]]
    return {"seeing": seeing, "gathered": len(rows), "proposes": True, "confirms": False,
            "note": ("his narrative, fit to the story and spoken in his voice" if seeing else
                     "his narrative does not reach this theme yet")}


__all__ = ["speak", "configured", "see", "illustrate"]
