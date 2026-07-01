"""Voice — the ElevenLabs ceiling over the browser floor.

Proves: unconfigured env => None (caller falls back to the floor); configured => synthesizes
once, caches content-addressed (miss then hit), never re-calls the paid API for the same
utterance; the digest is bound to voice + text; empty text => None; a failed upstream call
=> None (never raises). Hermetic — the upstream call is stubbed, no network. Runs under
pytest OR directly.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from concordance import voice  # noqa: E402


class _FakeResp:
    def __init__(self, data): self._d = data
    def read(self): return self._d
    def __enter__(self): return self
    def __exit__(self, *a): return False


def _env(monkey_ok=True, audio_dir=None):
    import os
    if monkey_ok:
        os.environ["ELEVENLABS_API_KEY"] = "sk_test_key"
        os.environ["ELEVENLABS_VOICE_ID"] = "K3Ptest"
    else:
        os.environ.pop("ELEVENLABS_API_KEY", None)
        os.environ.pop("ELEVENLABS_VOICE_ID", None)
    if audio_dir:
        os.environ["CONCORDANCE_AUDIO_DIR"] = audio_dir


def test_unconfigured_returns_none():
    _env(monkey_ok=False)
    assert voice.configured() is False
    assert voice.speak("For God so loved the world") is None


def test_empty_text_returns_none():
    _env(monkey_ok=True, audio_dir=tempfile.mkdtemp(prefix="nh-voice-"))
    assert voice.speak("") is None
    assert voice.speak("   ") is None


def test_synthesize_then_cache_hit():
    d = tempfile.mkdtemp(prefix="nh-voice-")
    _env(monkey_ok=True, audio_dir=d)
    calls = {"n": 0}
    orig = voice.urllib.request.urlopen

    def fake(req, timeout=0):
        calls["n"] += 1
        return _FakeResp(b"ID3-fake-mp3-bytes")
    voice.urllib.request.urlopen = fake
    try:
        r1 = voice.speak("In the beginning was the Word")
        assert r1 == (b"ID3-fake-mp3-bytes", "miss")
        r2 = voice.speak("In the beginning was the Word")
        assert r2 == (b"ID3-fake-mp3-bytes", "hit")   # served from cache, no second call
        assert calls["n"] == 1                          # the paid API touched exactly once
        assert list(Path(d).glob("*.mp3"))              # cached on disk
    finally:
        voice.urllib.request.urlopen = orig


def test_digest_binds_voice_and_text():
    import os
    _env(monkey_ok=True)
    os.environ["ELEVENLABS_VOICE_ID"] = "voiceA"
    a1 = voice._digest("hello")
    a2 = voice._digest("hello world")
    os.environ["ELEVENLABS_VOICE_ID"] = "voiceB"
    b1 = voice._digest("hello")
    assert a1 != a2 and a1 != b1   # text change and voice change both change the address


def test_upstream_failure_returns_none():
    d = tempfile.mkdtemp(prefix="nh-voice-")
    _env(monkey_ok=True, audio_dir=d)
    orig = voice.urllib.request.urlopen

    def boom(req, timeout=0):
        raise voice.urllib.error.URLError("down")
    voice.urllib.request.urlopen = boom
    try:
        assert voice.speak("anything") is None   # never raises; caller uses the floor
    finally:
        voice.urllib.request.urlopen = orig


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} voice tests passed — ceiling over floor; synthesized once, cached, never a hard dependency.")
