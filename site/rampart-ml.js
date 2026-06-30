// rampart-ml.js — OPT-IN contextual layer: the full Rampart guard (deterministic + an ML model
// that also catches NAMES, organizations, and phone numbers), loaded only on demand.
//
// The sovereign deterministic baseline (redact.js, window.Rampart) is ALWAYS on, same-origin,
// offline. This layer adds the National Design Studio's Rampart model (CC BY 4.0, ~15 MB int8
// ONNX). It tries the FULLY SELF-HOSTED path first (model + transformers.js runtime + ONNX
// WASM all served from this origin — no CDN, no Hugging Face), and only falls back to a pinned
// CDN if that fails, so this can improve sovereignty but never regress the feature. The guard
// runs entirely on-device either way. `RampartML.path()` reports which path loaded.
//
// Self-hosting requires an import map in the page resolving "@huggingface/transformers" to the
// vendored runtime (see index.html). Assets are produced by tools/vendor_rampart.sh.
(function (global) {
  var CDN = "https://cdn.jsdelivr.net/npm/@nationaldesignstudio/rampart@0.1.3/+esm";
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

  async function viaCdn(onStatus) {
    if (onStatus) onStatus("loading Rampart (CDN fallback)…");
    var mod = await import(CDN);
    var guard = await mod.createGuard();
    loadedPath = "cdn";
    return guard;
  }

  function load(onStatus) {
    if (!guardPromise) {
      guardPromise = (async function () {
        try {
          return await selfHosted(onStatus);
        } catch (e) {
          console.warn("Rampart self-hosted load failed; falling back to CDN:", e);
          return await viaCdn(onStatus);
        }
      })().catch(function (e) { guardPromise = null; throw e; });  // allow retry
    }
    return guardPromise;
  }

  global.RampartML = { load: load, path: function () { return loadedPath; } };
})(window);
