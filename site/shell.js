/* shell.js — the one spine for every Narrow Highway surface.
 *
 * Include once, high in <head>, WITHOUT defer, so the theme is stamped before
 * first paint and the bar is built on DOMContentLoaded:
 *     <script src="/shell.js"></script>
 *
 * It renders a single consistent header (wordmark, canonical nav, the three-faces
 * switcher, a light/dark toggle) so all ~45 pages read as one building instead of
 * one-off rooms. It is self-contained: its own scoped styles (prefix .nhs-), its own
 * brand fonts, no dependency on any page's CSS variables. A page opts a section into
 * the "active" state with  <html data-nh-section="atlas">  (else it is inferred from
 * the path). Numbers marked  data-nh-count="verifiers.distinct_modules_total"  are
 * filled live from /capabilities so a count can never silently drift from the engine.
 *
 * Owning the spine in one file means the nav, the faces, and the theme are changed
 * once, here — not edited across 45 hand-authored files.
 */
(function () {
  "use strict";
  var THEME_KEY = "nh_theme"; // reuse the landing's existing key so a saved choice carries over

  /* --- 1. anti-FOUC: stamp a saved theme at parse time, before the body paints --- */
  try {
    var saved = localStorage.getItem(THEME_KEY);
    if (saved === "light" || saved === "dark") {
      document.documentElement.setAttribute("data-theme", saved);
    }
  } catch (e) {}

  /* --- the canonical spine. Links are absolute so they work from any surface. --- */
  var NAV = [
    { k: "verify",    label: "Verify",    href: "/#verify" },
    { k: "atlas",     label: "Atlas",     href: "/explore.html" },
    { k: "domains",   label: "Domains",   href: "/domains.html" },
    { k: "mechanism", label: "Mechanism", href: "/#mechanism" },
    { k: "api",       label: "API",       href: "/#api" },
    { k: "map",       label: "Map",       href: "/map.html" }
  ];
  var FACES = [
    { k: "reach",   label: "reach",   href: "https://narrowhighway.com" },
    { k: "witness", label: "witness", href: "https://narrowhighway.org" },
    { k: "museum",  label: "museum",  href: "https://narrowhighway.tv" }
  ];

  function activeSection() {
    var override = document.documentElement.getAttribute("data-nh-section");
    if (override) return override;
    var p = location.pathname.replace(/\/+$/, "") || "/";
    if (p === "/" || p === "/index.html" || p === "/com.html") return "home";
    var map = {
      "/explore.html": "atlas", "/atlas.html": "atlas",
      "/domains.html": "domains", "/map.html": "map"
    };
    return map[p] || "";
  }
  function activeFace() {
    var h = location.hostname;
    if (/(^|\.)narrowhighway\.org$/.test(h)) return "witness";
    if (/(^|\.)narrowhighway\.tv$/.test(h))  return "museum";
    return "reach";
  }

  /* effective light/dark for the BAR itself — a page may be hard-coded to one theme
   * with no data-theme (e.g. the dark Map), so fall back to reading its body colour. */
  function effectiveDark() {
    var dt = document.documentElement.getAttribute("data-theme");
    if (dt === "dark") return true;
    if (dt === "light") return false;
    // a page whose frame and reading surface differ in tone can pin the bar explicitly
    var pin = document.documentElement.getAttribute("data-nh-bar");
    if (pin === "dark") return true;
    if (pin === "light") return false;
    try {
      var bg = getComputedStyle(document.body).backgroundColor || "";
      var m = bg.match(/rgba?\(([^)]+)\)/);
      if (m) {
        var p = m[1].split(",").map(parseFloat);
        var lum = 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2];
        if (!isNaN(lum)) return lum < 128;
      }
    } catch (e) {}
    return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
  }

  var STYLE =
  '@font-face{font-family:"NHSpectral";font-weight:600;font-display:swap;src:url(/fonts/spectral-600.woff2) format("woff2")}' +
  '@font-face{font-family:"NHPlex";font-weight:400;font-display:swap;src:url(/fonts/plexsans-400.woff2) format("woff2")}' +
  '@font-face{font-family:"NHPlex";font-weight:500;font-display:swap;src:url(/fonts/plexsans-500.woff2) format("woff2")}' +
  '@font-face{font-family:"NHMono";font-weight:500;font-display:swap;src:url(/fonts/plexmono-500.woff2) format("woff2")}' +
  /* the spine supersedes the old shared home button and the per-page wordmark; a page's
     section sub-nav (e.g. the scripture cluster) stays, but its duplicate brand is hidden */
  '#nh-home{display:none!important}' +
  'header.site .brand,header.bar .brand{display:none!important}' +
  '.nhs{position:sticky;top:0;z-index:9990;width:100%;-webkit-backdrop-filter:blur(9px);backdrop-filter:blur(9px);' +
    'background:var(--b-bg);border-bottom:1px solid var(--b-line);' +
    'font-family:"NHPlex",system-ui,-apple-system,"Segoe UI",sans-serif}' +
  '.nhs[data-mode="dark"]{--b-bg:rgba(11,14,19,.82);--b-solid:#0d1218;--b-ink:#aeb9c4;--b-brand:#eef2f6;--b-line:rgba(255,255,255,.09);--b-accent:#3bb6a3;--b-chip:rgba(255,255,255,.05)}' +
  '.nhs[data-mode="light"]{--b-bg:rgba(247,249,251,.88);--b-solid:#f4f6f9;--b-ink:#4c5763;--b-brand:#12161c;--b-line:rgba(16,22,28,.11);--b-accent:#0c6b5f;--b-chip:rgba(16,22,28,.03)}' +
  '.nhs-in{max-width:1180px;margin:0 auto;height:54px;display:flex;align-items:center;gap:1rem;' +
    'padding:0 clamp(1rem,3.5vw,2.4rem)}' +
  '.nhs-brand{display:flex;align-items:center;gap:.5rem;text-decoration:none;color:var(--b-brand);' +
    'font-family:"NHSpectral",Georgia,serif;font-weight:600;font-size:1.04rem;letter-spacing:-.01em;white-space:nowrap}' +
  '.nhs-mk{width:12px;height:12px;border:2px solid var(--b-accent);border-radius:50%;flex:0 0 auto}' +
  '.nhs-nav{display:flex;align-items:center;gap:1.2rem;margin-left:1.4rem;font-size:.88rem}' +
  '.nhs-link{color:var(--b-ink);text-decoration:none;white-space:nowrap;padding:.15rem 0;' +
    'border-bottom:2px solid transparent;transition:color .12s}' +
  '.nhs-link:hover{color:var(--b-accent)}' +
  '.nhs-link[aria-current]{color:var(--b-brand);border-bottom-color:var(--b-accent)}' +
  '.nhs-right{margin-left:auto;display:flex;align-items:center;gap:.7rem}' +
  '.nhs-faces{display:flex;gap:.15rem;padding:.18rem;border:1px solid var(--b-line);border-radius:999px;' +
    'font-family:"NHMono",ui-monospace,Menlo,monospace;font-size:.66rem;letter-spacing:.02em}' +
  '.nhs-face{color:var(--b-ink);text-decoration:none;padding:.2rem .55rem;border-radius:999px;line-height:1;transition:color .12s,background .12s}' +
  '.nhs-face:hover{color:var(--b-brand)}' +
  '.nhs-face[data-f="reach"][aria-current]{color:#fff;background:#3bb6a3}' +
  '.nhs-face[data-f="witness"][aria-current]{color:#12161c;background:#c9a24a}' +
  '.nhs-face[data-f="museum"][aria-current]{color:#fff;background:#8a7fd6}' +
  '.nhs-btn{font:inherit;color:var(--b-ink);background:var(--b-chip);border:1px solid var(--b-line);' +
    'border-radius:8px;width:32px;height:30px;display:grid;place-items:center;cursor:pointer;padding:0;transition:color .12s,border-color .12s}' +
  '.nhs-btn:hover{color:var(--b-accent);border-color:var(--b-accent)}' +
  '.nhs-menu{display:none}' +
  '.nhs-panel{display:none}' +
  /* collapse well before the full bar (~800px of content) can overflow a narrow viewport */
  '@media(max-width:900px){' +
    '.nhs-nav,.nhs-faces{display:none}' +
    '.nhs-menu{display:grid}' +
    '.nhs.open .nhs-panel{display:block;position:absolute;left:0;right:0;top:54px;' +
      'background:var(--b-solid);border-bottom:1px solid var(--b-line);' +
      'box-shadow:0 18px 30px -20px rgba(0,0,0,.5);padding:.6rem clamp(1rem,3.5vw,2.4rem) 1rem}' +
    '.nhs-panel a{display:block;padding:.55rem 0;color:var(--b-ink);text-decoration:none;' +
      'border-bottom:1px solid var(--b-line);font-size:.95rem}' +
    '.nhs-panel a[aria-current]{color:var(--b-brand)}' +
    '.nhs-panel .nhs-plabel{font-family:"NHMono",monospace;font-size:.6rem;letter-spacing:.22em;' +
      'text-transform:uppercase;color:var(--b-accent);margin:.7rem 0 .1rem}' +
  '}';

  function el(tag, cls, attrs) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (attrs) for (var a in attrs) n.setAttribute(a, attrs[a]);
    return n;
  }

  function build() {
    if (document.getElementById("nhs-root")) return; // idempotent
    var sec = activeSection(), face = activeFace();

    var style = el("style", null, { id: "nhs-style" });
    style.textContent = STYLE;
    document.head.appendChild(style);

    var bar = el("header", "nhs", { id: "nhs-root", role: "banner" });
    var inner = el("div", "nhs-in");

    var brand = el("a", "nhs-brand", { href: "/", "aria-label": "Narrow Highway — home" });
    brand.appendChild(el("span", "nhs-mk"));
    brand.appendChild(document.createTextNode("Narrow Highway"));
    inner.appendChild(brand);

    var nav = el("nav", "nhs-nav", { "aria-label": "Primary" });
    NAV.forEach(function (item) {
      var a = el("a", "nhs-link", { href: item.href });
      if (item.k === sec) a.setAttribute("aria-current", "page");
      a.textContent = item.label;
      nav.appendChild(a);
    });
    inner.appendChild(nav);

    var right = el("div", "nhs-right");
    var faces = el("div", "nhs-faces", { "aria-label": "Three faces, one engine" });
    FACES.forEach(function (f) {
      var a = el("a", "nhs-face", { href: f.href, "data-f": f.k, title: f.href.replace("https://", "") });
      if (f.k === face) a.setAttribute("aria-current", "true");
      a.textContent = f.label;
      faces.appendChild(a);
    });
    right.appendChild(faces);

    var toggle = el("button", "nhs-btn", { type: "button", "aria-label": "Toggle light or dark" });
    toggle.innerHTML = "&#9680;";
    toggle.addEventListener("click", function () {
      var root = document.documentElement, cur = root.getAttribute("data-theme");
      var next = cur === "dark" ? "light" : cur === "light" ? "dark"
        : (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "light" : "dark");
      root.setAttribute("data-theme", next);
      try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
      syncMode();
    });
    right.appendChild(toggle);

    var menu = el("button", "nhs-btn nhs-menu", { type: "button", "aria-label": "Menu", "aria-expanded": "false" });
    menu.innerHTML = "&#9776;";
    menu.addEventListener("click", function () {
      var open = bar.classList.toggle("open");
      menu.setAttribute("aria-expanded", open ? "true" : "false");
    });
    right.appendChild(menu);
    inner.appendChild(right);
    bar.appendChild(inner);

    /* mobile panel — same links, stacked */
    var panel = el("div", "nhs-panel");
    NAV.forEach(function (item) {
      var a = el("a", null, { href: item.href });
      if (item.k === sec) a.setAttribute("aria-current", "page");
      a.textContent = item.label;
      panel.appendChild(a);
    });
    var pl = el("div", "nhs-plabel"); pl.textContent = "three faces"; panel.appendChild(pl);
    FACES.forEach(function (f) {
      var a = el("a", null, { href: f.href, "data-f": f.k });
      if (f.k === face) a.setAttribute("aria-current", "true");
      a.textContent = f.label + "  —  " + f.href.replace("https://", "");
      panel.appendChild(a);
    });
    bar.appendChild(panel);

    document.body.insertBefore(bar, document.body.firstChild);

    function syncMode() { bar.setAttribute("data-mode", effectiveDark() ? "dark" : "light"); }
    syncMode();
    if (window.matchMedia) {
      try { window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", syncMode); } catch (e) {}
    }
    fillCounts();
  }

  /* live counts from /capabilities — only fires if a page actually asks for one */
  function fillCounts() {
    var nodes = document.querySelectorAll("[data-nh-count]");
    if (!nodes.length) return;
    fetch("/capabilities").then(function (r) { return r.json(); }).then(function (c) {
      nodes.forEach(function (n) {
        var v = n.getAttribute("data-nh-count").split(".").reduce(function (o, k) {
          return (o && o[k] != null) ? o[k] : null;
        }, c);
        if (v != null) n.textContent = (typeof v === "number") ? v.toLocaleString("en-US") : String(v);
      });
    }).catch(function () {});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
