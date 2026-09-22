/* NH LISTEN — the one voice-input standard: PUSH-TO-TALK.
 *
 * A button, held. The microphone opens only WHILE the key is pressed (press to speak, release to
 * send), so nothing is ever heard unless the person chooses it — sovereign, low-power, no wake word,
 * no always-on ear. The same press/release maps to a physical button on a pair of glasses. Mirrors
 * speak.js (the voice-OUTPUT standard): one implementation, attached wherever voice is taken.
 *
 *   NHListen.attach(button, {
 *     onFinal(text),    // command mode: the whole utterance, once, on release
 *     onInterim(text),  // dictation mode: the transcript so far, live while held (fills a box)
 *     onStart(),        // fires when the key is pressed (e.g. to capture what's already in the box)
 *     idle, live,       // optional button labels for the two states
 *     lang              // default 'en-US'
 *   })  -> true if wired (browser supports it), false otherwise (fall back to the written line).
 *
 * On-device: the browser's own SpeechRecognition; no audio leaves the machine through us.
 */
(function () {
  "use strict";
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;

  window.NHListen = {
    supported: !!SR,

    attach: function (btn, opts) {
      if (!SR || !btn) return false;
      opts = opts || {};
      var rec = new SR();
      rec.lang = opts.lang || "en-US";
      rec.interimResults = !!opts.onInterim;     // stream only when a live target wants it
      rec.continuous = false;                     // one held turn, never an open mic
      var listening = false, finalText = "";

      function label(t) { if (t != null && "textContent" in btn) btn.textContent = t; }

      rec.onresult = function (ev) {
        var interim = "", fin = "";
        for (var i = ev.resultIndex; i < ev.results.length; i++) {
          var r = ev.results[i];
          if (r.isFinal) fin += r[0].transcript; else interim += r[0].transcript;
        }
        if (fin) finalText += fin;
        if (opts.onInterim) opts.onInterim((finalText + " " + interim).trim());
      };
      rec.onend = function () {
        listening = false; btn.setAttribute("aria-pressed", "false"); label(opts.idle);
        var t = finalText.trim(); finalText = "";
        if (t && opts.onFinal) opts.onFinal(t);
      };
      rec.onerror = function () {
        listening = false; btn.setAttribute("aria-pressed", "false"); label(opts.idle);
      };

      function start() {
        if (listening) return;
        finalText = "";
        try { rec.start(); listening = true; btn.setAttribute("aria-pressed", "true"); label(opts.live);
              if (opts.onStart) opts.onStart(); } catch (e) {}
      }
      function stop() { if (listening) { try { rec.stop(); } catch (e) {} } }

      // press-and-hold — pointer covers mouse, touch and pen; a glasses/hardware button is the same
      btn.addEventListener("pointerdown", function (e) { e.preventDefault(); start(); });
      btn.addEventListener("pointerup", function (e) { e.preventDefault(); stop(); });
      btn.addEventListener("pointerleave", stop);
      btn.addEventListener("pointercancel", stop);
      // keyboard parity: hold Space or Enter to talk, release to send
      btn.addEventListener("keydown", function (e) {
        if ((e.key === " " || e.key === "Enter") && !e.repeat) { e.preventDefault(); start(); }
      });
      btn.addEventListener("keyup", function (e) {
        if (e.key === " " || e.key === "Enter") { e.preventDefault(); stop(); }
      });

      if (opts.idle != null) label(opts.idle);
      return true;
    }
  };
})();
