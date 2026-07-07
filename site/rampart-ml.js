// rampart-ml.js — OPT-IN contextual layer: the full Rampart guard (deterministic + an ML model
// that also catches NAMES, organizations, and phone numbers), loaded only on demand.
//
// The sovereign deterministic baseline (redact.js, window.Rampart) is ALWAYS on, same-origin,
// offline. This layer adds the National Design Studio's Rampart model (CC BY 4.0, ~15 MB int8
// ONNX), served FULLY SELF-HOSTED (model + transformers.js runtime + ONNX WASM all from this
// origin — no CDN, no Hugging Face). If the vendored assets are absent, this layer simply fails
// and the UI stays on the always-on deterministic baseline — it NEVER reaches out to a CDN.
// The guard runs entirely on-device. `RampartML.path()` reports which path loaded.
//
// Self-hosting requires an import map in the page resolving "@huggingface/transformers" to the
// vendored runtime (see index.html). Assets are produced by tools/vendor_rampart.sh.
(function (global) {
  var guardPromise = null;
  var loadedPath = null;

  async function selfHosted(onStatus) {
    if (onStatus) onStatus("loading Rampart (self-hosted)…");
    var t = await import("/vendor/transformers/transformers.web.min.js");
    t.env.allowRemoteModels = false;            // never reach out to Hugging Face
    t.env.allowLocalModels = true;
    t.env.localModelPath = "/models/";          // served from this origin
    t.env.backends.onnx.wasm.wasmPaths = "/vendor/ort/";  // self-hosted ONNX runtime
    var r = await import("/vendor/rampart/index.js");      // its bare transformers import -> importmap
    if (onStatus) onStatus("loading model (self-hosted, ~15 MB)…");
    var guard = await r.createGuard({ model: "nationaldesignstudio/rampart" });
    loadedPath = "self-hosted";
    return guard;
  }

  function load(onStatus) {
    // Self-hosted ONLY. On failure we reject so the caller degrades to the deterministic
    // baseline (always on) — we NEVER fall back to a CDN. Nulling the promise allows retry.
    if (!guardPromise) {
      guardPromise = selfHosted(onStatus).catch(function (e) { guardPromise = null; throw e; });
    }
    return guardPromise;
  }

  global.RampartML = { load: load, path: function () { return loadedPath; } };
})(window);
