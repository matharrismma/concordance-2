/* Every tool, one keystroke away — on every page.
 *
 * The rail is the visible way in; this is the fast way in. Ctrl-K (Cmd-K on a Mac) opens a
 * plain list, you type a few letters, Enter goes. No dependency, no build step, no network:
 * the whole index is the array below, so it works offline exactly as it works online.
 *
 * Injected on every page by the same rule as nh-home.js — a tool you cannot reach from where
 * you are standing is not really available.
 */
(function () {
  if (window.__nhTools) return;
  window.__nhTools = true;

  // Deliberately absent: keep.html is the operator's own surface and carries noindex — a
  // public list is not the place for it. ask.html is the landing's predecessor, and
  // encyclopedia.html is a redirect stub onto characters.html; both would be a second door
  // onto a room already listed here.
  var TOOLS = [
    { h: '/',                n: 'Write',            k: 'ask new page home chat conversation start' },
    { h: '/bible.html',      n: 'Scripture',        k: 'bible verse passage read canon testament word' },
    { h: '/read.html',       n: 'Study for a test', k: 'learn school lesson coach tutor curriculum practice' },
    { h: '/characters.html', n: 'Dictionary',       k: 'define meaning people names who character lexicon' },
    { h: '/library.html',    n: 'The keeping',      k: 'library cards corpus browse search everything' },
    { h: '/almanac.html',    n: 'Almanac',          k: 'facts figures reference tables data' },
    { h: '/map.html',        n: 'The map',          k: 'connections graph atlas structure links' },
    { h: '/brain.html',      n: 'The brain',        k: 'graph visual network nodes force' },
    { h: '/journal.html',    n: 'Journal',          k: 'writing entries past dates diary notes wrote' },
    { h: '/days.html',       n: 'Your days',        k: 'time concentration history activity what i did map' },
    { h: '/steward.html',    n: 'Steward',          k: 'money budget spend save cost debt finance' },
    { h: '/seal.html',       n: 'Seals',            k: 'receipts proof verified cite citation' },
    { h: '/audit.html',      n: 'Audit a document', k: 'check claims paste text verify article' },
    { h: '/reason.html',     n: 'Check an argument', k: 'reasoning chain logic function code derivation steps' },
    { h: '/collapse.html',   n: 'A worked proof',    k: 'derivation maxwell sealed example chain show me' },
    { h: '/connect.html',    n: 'Connect an agent',  k: 'api mcp developer integrate build llm tool' },
    { h: '/corrected.html',  n: 'What we got wrong', k: 'corrections honest record demoted overclaiming mistakes' },
    { h: '/seeds.html',      n: 'Seeds of the Word', k: 'areopagus athens nations fragments paul philosophy' },
    { h: '/check.html',      n: 'Check a claim',    k: 'verify true false math fact' },
    { h: '/teachings.html',  n: 'Teachings',        k: 'jesus christ words sayings gospel' },
    { h: '/prophecy.html',   n: 'Prophecy',         k: 'traces fulfilment signposts' },
    { h: '/codex.html',      n: 'The Codex',        k: 'manuscript compiled book document' },
    { h: '/community.html',  n: 'Community',        k: 'groups study together share people' },
    { h: '/proof.html',      n: 'What it proves',   k: 'refusals limits catalog guarantees honest' },
    { h: '/boundary.html',   n: 'The boundary',     k: 'limits cannot mappable edge' },
    { h: '/guarantees.html', n: 'Guarantees',       k: 'promises honest what it will not do' },
    { h: '/companion.html',  n: 'The Companion',    k: 'plan body specialists router scribe carry' },
    { h: '/tv.html',         n: 'Watch & listen',   k: 'tv video channels audio' }
  ];

  var css = document.createElement('style');
  css.textContent =
    '#nh-pal{position:fixed;inset:0;z-index:2147482000;display:none;align-items:flex-start;' +
      'justify-content:center;background:rgba(20,13,7,.55);padding:14vh 1rem 1rem}' +
    '#nh-pal[data-open="1"]{display:flex}' +
    '#nh-pal .box{width:min(34rem,100%);background:linear-gradient(180deg,#f5f1e6,#e9e3d3);' +
      'border-radius:3px;box-shadow:0 30px 70px -20px #000;overflow:hidden;' +
      'font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;color:#241f18}' +
    '#nh-pal input{width:100%;border:0;border-bottom:1px solid rgba(138,106,47,.35);outline:0;' +
      'background:transparent;font:inherit;font-size:1.05rem;padding:.9rem 1rem;color:inherit}' +
    '#nh-pal ul{list-style:none;margin:0;padding:.3rem 0;max-height:46vh;overflow-y:auto}' +
    '#nh-pal li{padding:.5rem 1rem;cursor:pointer;display:flex;justify-content:space-between;gap:1rem}' +
    '#nh-pal li[aria-selected="true"]{background:rgba(198,154,74,.24)}' +
    '#nh-pal li span{color:#9b8a6d;font-size:.78rem}' +
    '#nh-pal .hint{padding:.45rem 1rem;font-size:.72rem;color:#9b8a6d;' +
      'border-top:1px solid rgba(138,106,47,.2)}';
  document.head.appendChild(css);

  var wrap = document.createElement('div');
  wrap.id = 'nh-pal';
  wrap.setAttribute('role', 'dialog');
  wrap.setAttribute('aria-modal', 'true');
  wrap.setAttribute('aria-label', 'Go to a tool');
  wrap.innerHTML =
    '<div class="box"><input type="text" placeholder="Go to…" aria-label="Go to a tool" ' +
    'autocomplete="off" spellcheck="false"><ul role="listbox"></ul>' +
    '<div class="hint">Enter to go · Esc to close</div></div>';

  var input, list, shown = [], sel = 0, opener = null;

  function match(q) {
    q = q.trim().toLowerCase();
    if (!q) return TOOLS.slice();
    return TOOLS.filter(function (t) {
      var hay = (t.n + ' ' + t.k).toLowerCase();
      return q.split(/\s+/).every(function (w) { return hay.indexOf(w) >= 0; });
    });
  }

  function draw() {
    list.innerHTML = shown.map(function (t, i) {
      return '<li role="option" data-i="' + i + '" aria-selected="' + (i === sel) + '">' +
             t.n + '<span>' + t.h.replace('.html', '').replace(/^\//, '') + '</span></li>';
    }).join('') || '<li aria-selected="false"><span>Nothing by that name.</span></li>';
    var on = list.querySelector('[aria-selected="true"]');
    if (on && on.scrollIntoView) on.scrollIntoView({ block: 'nearest' });
  }

  function open() {
    opener = document.activeElement;
    shown = match(''); sel = 0;
    wrap.dataset.open = '1';
    input.value = '';
    draw();
    input.focus();
  }

  function close() {
    wrap.dataset.open = '0';
    if (opener && opener.focus) opener.focus();
  }

  function go() {
    var t = shown[sel];
    if (t) window.location.href = t.h;
  }

  function ready() {
    if (document.getElementById('nh-pal')) return;
    document.body.appendChild(wrap);
    input = wrap.querySelector('input');
    list = wrap.querySelector('ul');

    input.addEventListener('input', function () { shown = match(input.value); sel = 0; draw(); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); sel = Math.min(sel + 1, shown.length - 1); draw(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(sel - 1, 0); draw(); }
      else if (e.key === 'Enter') { e.preventDefault(); go(); }
      else if (e.key === 'Escape') { e.preventDefault(); close(); }
    });
    list.addEventListener('click', function (e) {
      var li = e.target.closest('li[data-i]');
      if (li) { sel = +li.dataset.i; go(); }
    });
    wrap.addEventListener('mousedown', function (e) { if (e.target === wrap) close(); });

    document.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        if (wrap.dataset.open === '1') close(); else open();
      }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();
