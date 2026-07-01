"""Voice — the spoken floor and the spoken ceiling.

FLOOR (always, sovereign, offline, free): the browser's own speech (site/speak.js →
NHSpeak). No key, no network, no dependency — a word can always be spoken.

CEILING (optional): when ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are present in the
environment, `/speak` returns audio in the operator's own cloned voice. If the key is
absent or the upstream call fails, `speak()` returns None and the caller falls back to the
floor — the ceiling never becomes a single point of failure.

Content-addressed cache (save-once-use-forever): the audio for a given (voice, model, text)
is synthesized once and reused, so the paid API is called at most once per distinct
utterance. The cache lives under data/audio/ (gitignored, like the rest of the runtime).

Conduit, not source: the engine SPEAKS found and verified words — Scripture, a lexicon
entry, a cited take. It does not generate the words it speaks; it only gives them a voice.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

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
    """Content address of the utterance — voice + model + text, so a re-voicing or a text
    change yields a fresh file and the cache never serves the wrong audio."""
    h = hashlib.sha256()
    h.update((_voice_id() + "|" + _MODEL + "|" + text).encode("utf-8"))
    return h.hexdigest()


def speak(text: str):
    """Return (mp3_bytes, "hit"|"miss") in the operator's voice, or None.

    None means 'ceiling unavailable — use the browser floor': unconfigured env, empty text,
    or a failed upstream call. Never raises. Caches the audio content-addressed so the paid
    API is touched at most once per distinct utterance.
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
