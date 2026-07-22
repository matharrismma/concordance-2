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
