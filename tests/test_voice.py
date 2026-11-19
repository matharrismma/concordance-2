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


def _stub_upstream():
    """Stand in for the paid API: returns audio, counts calls. Returns (restore, calls)."""
    calls = {"n": 0}
    orig = voice.urllib.request.urlopen

    def fake(req, timeout=0):
        calls["n"] += 1
        return _FakeResp(b"ID3-fake-mp3-bytes")
    voice.urllib.request.urlopen = fake

    def restore():
        voice.urllib.request.urlopen = orig
    return restore, calls


def test_cached_knows_whether_an_utterance_is_already_paid_for():
    d = tempfile.mkdtemp(prefix="nh-voice-")
    _env(monkey_ok=True, audio_dir=d)
    line = "The LORD is my shepherd"
    assert voice.cached(line) is False          # nothing paid for yet
    restore, _ = _stub_upstream()
    try:
        assert voice.speak(line)[1] == "miss"
    finally:
        restore()
    assert voice.cached(line) is True           # now it costs nothing to serve


def test_cached_is_false_when_the_ceiling_is_unwired():
    _env(monkey_ok=False)
    assert voice.cached("anything") is False


def test_the_predicate_and_the_synthesizer_agree_about_a_long_line():
    """If cached() and speak() normalized differently, a caller could be told a line is free and
    then be billed for it. Both go through _normalized, so the truncated form is the utterance."""
    d = tempfile.mkdtemp(prefix="nh-voice-")
    _env(monkey_ok=True, audio_dir=d)
    long_line = "x" * (voice._MAX_CHARS + 50)
    restore, calls = _stub_upstream()
    try:
        voice.speak(long_line)
    finally:
        restore()
    assert voice.cached(long_line) is True
    assert voice.cached("x" * voice._MAX_CHARS) is True   # the same utterance by another spelling
    assert calls["n"] == 1


def test_a_stranger_cannot_spend_but_may_replay_what_was_already_bought():
    """The paid door: a MISS is the operator's alone; a HIT belongs to everyone."""
    d = tempfile.mkdtemp(prefix="nh-voice-")
    _env(monkey_ok=True, audio_dir=d)
    line = "Come unto me, all ye that labour"
    assert voice.may_synthesize(line, is_operator=False) is False   # money, and not theirs to spend
    assert voice.may_synthesize(line, is_operator=True) is True     # the operator may
    restore, _ = _stub_upstream()
    try:
        voice.speak(line)
    finally:
        restore()
    assert voice.may_synthesize(line, is_operator=False) is True    # paid for once, free ever after


def test_the_gate_asks_about_money_not_about_whether_the_ceiling_is_up():
    """With no key the operator still passes the gate — and speak() still returns None, so the door
    falls to the floor exactly as it did before the gate existed. The two questions stay separate."""
    _env(monkey_ok=False)
    assert voice.may_synthesize("anything", is_operator=True) is True   # the gate is about spending
    assert voice.speak("anything") is None                              # the ceiling is still down


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} voice tests passed — ceiling over floor; synthesized once, cached, never a hard dependency.")
