/* NHSpeak — speaking, floor first with an optional ceiling.

   FLOOR: say() uses the built-in Web Speech API (no network, no dependency, offline).
   CEILING: play() tries the server /speak endpoint first — the operator's own cloned voice
   (ElevenLabs) when it's wired — and falls back to the floor if that isn't available. So a
   word or a verse can always be spoken, and it's read in Matt's voice wherever possible. */
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

  var _current = null;   // the currently-playing ceiling audio, so a new play() stops the old

  // play(text): prefer the operator's voice (server /speak); fall back to the browser floor.
  // Returns a promise that resolves to 'ceiling' | 'floor' | false.
  function play(text, opts) {
    opts = opts || {};
    text = String(text == null ? '' : text).trim();
    if (!text) return Promise.resolve(false);
    var api = (window.API != null ? window.API : (opts.api || ''));
    return fetch(api + '/speak', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ text: text })
    }).then(function (r) {
      if (!r.ok) throw new Error('no ceiling');   // 503 when the voice isn't wired
      var ct = r.headers.get('content-type') || '';
      if (ct.indexOf('audio') === -1) throw new Error('not audio');
      return r.blob();
    }).then(function (blob) {
      try { if (_current) { _current.pause(); } } catch (e) {}
      try { window.speechSynthesis && window.speechSynthesis.cancel(); } catch (e) {}
      var url = URL.createObjectURL(blob);
      var a = new Audio(url);
      _current = a;
      a.onended = a.onerror = function () { try { URL.revokeObjectURL(url); } catch (e) {} };
      a.play();
      return 'ceiling';
    }).catch(function () {
      return say(text, opts) ? 'floor' : false;   // ceiling absent -> sovereign browser voice
    });
  }

  window.NHSpeak = { say: say, play: play, available: ('speechSynthesis' in window) };
})();
