/* NHSearch — find the whole keeping with NO server, on the device.
 *
 * The offline finding layer. It lazily loads /search-index.json (every public seed as a tiny row),
 * caches it (the service worker keeps it), and searches it locally — so when there is no network,
 * you can still FIND anything in the keeping by name or word. The full card body loads from the
 * cached /card endpoint when opened; this layer is the finding.
 *
 * Conduit, not source: it only surfaces and ranks what the keeping already holds — it generates
 * nothing. Fails silent: no index (never downloaded) -> returns empty, the caller stays honest.
 */
window.NHSearch = (function () {
  var idx = null, loading = null;

  function load() {
    if (idx) return Promise.resolve(idx);
    if (loading) return loading;
    loading = fetch('/search-index.json')
      .then(function (r) { if (!r.ok) throw new Error('no index'); return r.json(); })
      .then(function (d) { idx = (d && d.rows) || []; return idx; })
      .catch(function () { loading = null; return []; });
    return loading;
  }

  function toks(s) { return (String(s || '').toLowerCase().match(/[a-z0-9]{2,}/g)) || []; }

  function find(q, limit) {
    limit = limit || 8;
    var ql = String(q || '').trim().toLowerCase();
    return load().then(function (rows) {
      var qt = toks(ql); if (!qt.length || !rows.length) return [];
      var scored = [];
      for (var i = 0; i < rows.length; i++) {
        var r = rows[i], hay = (r.t + ' ' + (r.x || '')).toLowerCase(), sc = 0;
        for (var j = 0; j < qt.length; j++) if (hay.indexOf(qt[j]) >= 0) sc++;
        if (!sc) continue;
        var tl = r.t.toLowerCase();
        if (tl === ql) sc += 12; else if (tl.indexOf(ql) === 0) sc += 5;   // exact / prefix title wins
        else if (tl.indexOf(ql) >= 0) sc += 2;
        scored.push([sc, r]);
      }
      scored.sort(function (a, b) { return b[0] - a[0]; });
      return scored.slice(0, limit).map(function (x) {
        return { id: x[1].i, title: x[1].t, shelf: x[1].s, snippet: x[1].x };
      });
    });
  }

  // ensure the index is on the device (a deliberate "carry the keeping" download)
  function download() { return load().then(function (rows) { return rows.length; }); }

  return { load: load, find: find, download: download,
           ready: function () { return load().then(function (r) { return r.length > 0; }); } };
})();
