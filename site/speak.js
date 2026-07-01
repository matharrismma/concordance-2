/* NHSpeak — the sovereign browser-speech floor for pronunciation / reading aloud.
   Uses the built-in Web Speech API (no network, no dependency). The ElevenLabs voice
   (Matt's own) is the optional ceiling, wired separately; pages prefer that when present
   and fall back to this so a word can always be spoken, offline. */
(function () {
  function say(text, opts) {
    opts = opts || {};
    try {
      if (!('speechSynthesis' in window) || !text) return false;
      var u = new SpeechSynthesisUtterance(String(text));
      if (opts.lang) u.lang = opts.lang;
      u.rate = opts.rate || 0.95;
      u.pitch = opts.pitch || 1.0;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
      return true;
    } catch (e) { return false; }
  }
  window.NHSpeak = { say: say, available: ('speechSynthesis' in window) };
})();
