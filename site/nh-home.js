/* A clear way home, identical on every page.
 *
 * Pages grew their own headers over time — some had a brand link, some had it buried in a nav,
 * two had none at all. Rather than hand-edit thirty files into agreement, one control is
 * injected here so "home" looks and behaves the same everywhere, and can never drift again.
 *
 * Skipped on the home page itself. Never covers page content: it sits in the top-left gutter
 * and is keyboard-reachable.
 */
(function () {
  var path = location.pathname.replace(/\/+$/, '');
  if (path === '' || path === '/index.html') return;        // already home
  if (document.getElementById('nh-home')) return;

  function inject() {
    if (document.getElementById('nh-home')) return;
    var a = document.createElement('a');
    a.id = 'nh-home';
    a.href = '/';
    a.setAttribute('aria-label', 'Back to Narrow Highway');
    a.innerHTML = '<span aria-hidden="true">←</span> Home';

    var css = document.createElement('style');
    css.textContent =
      '#nh-home{position:fixed;top:.75rem;left:.85rem;z-index:2147483000;' +
      'display:inline-flex;align-items:center;gap:.4rem;' +
      'font:500 .82rem/1 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif;' +
      'letter-spacing:.04em;text-decoration:none;padding:.44rem .8rem;border-radius:999px;' +
      'color:#6b5b45;background:rgba(252,249,242,.92);border:1px solid #d5c8ad;' +
      'box-shadow:0 2px 10px -4px rgba(60,44,20,.3);backdrop-filter:saturate(1.2) blur(6px);' +
      'transition:color .16s ease,border-color .16s ease,transform .16s ease}' +
      '#nh-home:hover,#nh-home:focus{color:#241d15;border-color:#a9822b;transform:translateY(-1px);outline:none}' +
      '#nh-home:focus-visible{box-shadow:0 0 0 3px rgba(169,130,43,.35)}' +
      '@media (prefers-color-scheme:dark){#nh-home{color:#a5947a;background:rgba(27,24,19,.92);' +
      'border-color:#3a3025}#nh-home:hover,#nh-home:focus{color:#ece0c8;border-color:#d8ad4e}}' +
      '@media print{#nh-home{display:none}}';
    document.head.appendChild(css);
    document.body.appendChild(a);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', inject);
  else inject();
})();

/* Arrive where the link pointed.
 *
 * A URL carrying ?q= / ?search= / ?ref= / ?shelf= is a reader — or a citation — asking for one
 * specific thing. Every page here has a search control and NOT ONE of them read the URL, so such
 * a link silently produced the unfiltered page instead. That is the same failure that makes 2,124
 * card citations to /canon.html?ref=… land on a generic Bible page with the reference thrown
 * away: the reader arrives somewhere plausible and wrong, and nothing reports it.
 *
 * One adopter on the shared shell fixes every page at once and cannot drift back. A page that
 * knows better takes over by defining window.NHDeepLink(value) / window.NHDeepLinkShelf(shelf) —
 * then it owns the waiting, and this stops after one call.
 *
 * Fails silent: no matching control -> nothing happens, and the page is exactly what it was.
 */
(function () {
  var P;
  try { P = new URLSearchParams(location.search); } catch (e) { return; }
  var term = '';
  var KEYS = ['q', 'search', 'ref', 'term', 'name'];
  for (var i = 0; i < KEYS.length && !term; i++) term = P.get(KEYS[i]) || '';
  var shelf = P.get('shelf') || '';
  if (!term && !shelf) return;

  // Ordered, not a comma-selector: querySelector with a list returns the first match in DOCUMENT
  // order, which on some pages is the wrong box entirely.
  var INPUTS = ['[data-deeplink]', '#q', '#search', 'input[type=search]'];
  function firstOf(sels) {
    for (var i = 0; i < sels.length; i++) {
      var el = document.querySelector(sels[i]);
      if (el) return el;
    }
    return null;
  }

  var tries = 0;
  function apply() {
    var settled = true;

    if (term) {
      if (typeof window.NHDeepLink === 'function') {
        window.NHDeepLink(term); term = '';
      } else {
        var input = firstOf(INPUTS);
        if (input) {
          input.value = term; term = '';
          var go = document.getElementById('go');
          if (go) go.click();
          else {
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
          }
        } else settled = false;
      }
    }

    if (shelf) {
      if (typeof window.NHDeepLinkShelf === 'function') {
        window.NHDeepLinkShelf(shelf); shelf = '';
      } else {
        // the dropdown is filled from /cards/stats AFTER load — wait for OUR option, not just
        // for the <select>, or the value is set on an empty list and silently discarded
        var sel = firstOf(['[data-deeplink-shelf]', 'select#shelf']);
        var has = sel && Array.prototype.some.call(sel.options, function (o) { return o.value === shelf; });
        if (has) {
          sel.value = shelf; shelf = '';
          sel.dispatchEvent(new Event('change', { bubbles: true }));
        } else settled = false;
      }
    }

    if (settled || ++tries > 40) return;   // ~4s of waiting, then give up quietly
    setTimeout(apply, 100);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply);
  else apply();
})();
