/* NHKind — the result-kind badge, shown on every surface.

   Conduit-not-source made visible: every result on Narrow Highway wears its KIND, so a visitor can
   tell at a glance what weight it carries. Five kinds (see /guarantees.html):
     verified  ✓  a sealed, re-checkable check (the moat)
     cited     ⌖  found + attributed — real material, NOT "verified true"
     scripture ✶  Scripture, found & cited (public-domain text)
     signpost  →  points toward Christ — never a proof
     yours     ✎  your own words, kept verbatim — never graded, never verified
   Each badge links to /guarantees.html so the boundary is one click from being fully explained.
   Self-styling (injects its CSS once); uses the page's austere theme vars with safe fallbacks. */
(function () {
  if (window.NHKind) return;
  var css =
    '.nhk{display:inline-flex;align-items:center;gap:.3rem;font-size:.6rem;letter-spacing:.13em;' +
    'text-transform:uppercase;border:1px solid var(--line,rgba(201,162,74,.16));border-radius:2px;' +
    'padding:.12rem .5rem;text-decoration:none;line-height:1.5;white-space:nowrap}' +
    '.nhk:hover{text-decoration:none;border-color:var(--gold,#c9a24a)}' +
    '.nhk-v{color:var(--pass,#8bbf8f)} .nhk-c{color:var(--goldsoft,#a98a3f)}' +
    '.nhk-s{color:var(--mid,#c9b06a)} .nhk-y{color:var(--dim,#8f8a7c)}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  var K = {
    verified:  { s: '✓', l: 'Verified · sealed', c: 'v' },
    cited:     { s: '⌖', l: 'Found & cited', c: 'c' },
    scripture: { s: '✦', l: 'Scripture · found & cited', c: 'c' },
    signpost:  { s: '→', l: 'Signpost — not a proof', c: 's' },
    yours:     { s: '✎', l: 'Your own — kept, not verified', c: 'y' },
  };
  function esc(x){ var d=document.createElement('div'); d.textContent=String(x==null?'':x); return d.innerHTML; }
  // badge(kind[, note]) -> HTML string. `note` appends a source/context, e.g. "World English Bible (PD)".
  function badge(kind, note) {
    var k = K[kind] || K.cited;
    var lbl = k.l + (note ? (' · ' + note) : '');
    return '<a class="nhk nhk-' + k.c + '" href="/guarantees.html" ' +
      'title="What this means — what we prove, and what we don\'t">' + k.s + ' ' + esc(lbl) + '</a>';
  }
  // Declarative use: drop <span data-nhkind="cited" data-nhnote="the keeping"></span> anywhere and it fills
  // itself on load. Keeps the labels in one place; static pages need no inline script, only the include.
  function fill(root) {
    var els = (root || document).querySelectorAll('[data-nhkind]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (el.getAttribute('data-nhk-done')) continue;
      el.innerHTML = badge(el.getAttribute('data-nhkind'), el.getAttribute('data-nhnote') || undefined);
      el.setAttribute('data-nhk-done', '1');
    }
  }
  if (document.readyState !== 'loading') fill();
  else document.addEventListener('DOMContentLoaded', function () { fill(); });
  window.NHKind = { badge: badge, fill: fill };
})();
