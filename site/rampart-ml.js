// rampart-ml.js — OPT-IN contextual layer: the full Rampart guard (deterministic + an ML
// model that also catches NAMES, organizations, and phone numbers), loaded only on demand.
//
// The sovereign deterministic baseline (redact.js, window.Rampart) is ALWAYS on and runs
// same-origin/offline. This optional layer adds the National Design Studio's Rampart model
// (CC BY 4.0, ~15 MB int8 ONNX) — proven to turn "Dr. Sarah Johnson … 415-555-0142" into
// "[GIVEN_NAME_1] [SURNAME_1] … [PHONE_1]". It runs ON-DEVICE once loaded and is cached in
// the browser (IndexedDB) after first use.
//
// SOVEREIGNTY NOTE (honest): the deterministic layer is fully sovereign. THIS layer loads the
// Rampart library from a pinned CDN and the model from Hugging Face on first use, then runs +
// caches entirely on your device. Fully self-hosting both (no CDN) is a documented follow-up.
(function (global) {
  var RAMPART_ESM = "https://cdn.jsdelivr.net/npm/@nationaldesignstudio/rampart@0.1.3/+esm";
  var guardPromise = null;

  // Returns a Promise<ChatGuard>. Reused after the first load. onStatus(msg) for UI feedback.
  function load(onStatus) {
    if (!guardPromise) {
      guardPromise = (async function () {
        if (onStatus) onStatus("loading Rampart library…");
        var mod = await import(RAMPART_ESM);
        if (onStatus) onStatus("loading model (~15 MB, first time only)…");
        var guard = await mod.createGuard();        // downloads + caches the model on-device
        if (onStatus) onStatus("ready");
        return guard;
      })().catch(function (e) { guardPromise = null; throw e; });  // allow retry on failure
    }
    return guardPromise;
  }

  global.RampartML = { load: load };
})(window);
