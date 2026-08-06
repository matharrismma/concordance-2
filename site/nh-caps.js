/* nh-caps.js — every public NUMBER comes from the live engine, never a stranded literal.
 *
 * Matt, 2026-08-06: "make sure every statement is factual, and we have a mechanism to update as we
 * add more." This is that mechanism. Any element carrying data-cap="<dotted path into the JSON of
 * GET /capabilities>" has its text replaced, on load, with the live count — so as the corpus and the
 * verifier fleet grow, the page's numbers move with them and cannot drift.
 *
 * The literal written in the HTML is a FALLBACK, shown only if JS is off or the fetch fails (a blip
 * must never blank a number). A gate test (tests/test_caps_fresh.py) asserts every fallback still
 * matches the live value, so the static text can never quietly go stale either — belt and suspenders.
 *
 * Paths address the capability statement built by capabilities.statement(): a leaf is normally
 * {count, means, ...}, so "verifiers.distinct_modules_total" resolves to that node's .count. A path
 * that already points at a bare number (e.g. "tools.count") is used as-is.
 */
(function () {
  function resolve(obj, path) {
    var node = obj, parts = path.split('.');
    for (var i = 0; i < parts.length; i++) {
      if (node == null || typeof node !== 'object') return undefined;
      node = node[parts[i]];
    }
    if (node && typeof node === 'object' && 'count' in node) node = node.count;  // {count, means} leaf
    return node;
  }
  function fmt(v) {
    return (typeof v === 'number') ? v.toLocaleString('en-US') : v;
  }
  function apply(d) {
    var els = document.querySelectorAll('[data-cap]');
    for (var i = 0; i < els.length; i++) {
      var v = resolve(d, els[i].getAttribute('data-cap'));
      if (v !== undefined && v !== null) els[i].textContent = fmt(v);  // else keep the fallback text
    }
  }
  function pull() {
    // freshness in the URL — a browser will not honour no-store on its own (the stale-read lesson)
    fetch('/capabilities?t=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(apply)
      .catch(function () { /* keep the server-rendered fallback — a blip must not blank a number */ });
  }
  if (document.readyState !== 'loading') pull();
  else document.addEventListener('DOMContentLoaded', pull);
})();
