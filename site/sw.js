/* Narrow Highway — offline service worker.
 *
 * Tier 1 of the offline plan (docs/THE_COMPANION.md §6b): the surfaces keep working with no
 * network, with no install. The engine itself is already network-free; this closes the gap
 * for the *browser* surface.
 *
 * Strategy is deliberately conservative, because a bad service worker is worse than none:
 *   - navigations + data  -> NETWORK FIRST, cache as fallback.  Online users always get
 *     fresh content; offline users get the last good copy. No sticky staleness.
 *   - static assets       -> stale-while-revalidate (fast, self-healing).
 *   - GET + same-origin only. Never caches errors, opaque responses, or the seal/verify path.
 * Bump CACHE to purge every old cache on activate.
 */
const CACHE = 'nh-offline-v6';  // v6: precache coach.html + situations.html (the audio front door + urgent-need triage, offline-ready)

/* The floor: what must be there with no network at all — precached on install so the whole flagship
   experience (the door, the Floor of Discovery, the Coach, the Apothecary, Scripture, the journal)
   is CARRIED with you, ready before you ever go offline. We take the internet when it is there and
   fall back to this when it is not. Best-effort — a miss never fails the install (a failed install
   would leave the site with no worker at all). Paramless knowledge endpoints are precached too, so
   the pages have their data offline; per-item data (a passage, a lesson) caches as it is visited. */
const CORE = [
  '/', '/index.html', '/read.html', '/bible.html', // one entry for the Corpus, not one per section: the sections are views of a single document,
  // so `?section=` would precache the same bytes three times under three cache keys
  '/kinds.js', '/nh-tools.js', '/nh-home.js', '/speak.js', '/gate.js', '/redact.js', '/nh-search.js',
  '/manifest.webmanifest', '/icon.svg',
  '/coach.html', '/situations.html', // the audio-native front door + the urgent-need triage — offline-ready, with the static crisis floor
  '/floor', '/coach/journey', '/coach/subjects', '/apothecary', '/almanac'
];

/* Never cache: anything that must be live-verified or is per-request. */
const NEVER = [/^\/verify/, /^\/seal/, /^\/s\//, /^\/audit/, /^\/speak/];

/* THE SHELL — the scripts that decide what a page DOES, network-first like the pages themselves.
 *
 * Measured 2026-07-31, in a browser, right after deploying the deep-link adopter into nh-home.js:
 * /hymns.html redirected correctly, the page loaded, and the adopter did not run. The service
 * worker had served YESTERDAY's nh-home.js from stale-while-revalidate; the fix arrived in the
 * cache in the background and worked on the NEXT load. One-load-behind — the same shape as the
 * shelf bug in July, which was one WRITE behind.
 *
 * Stale-while-revalidate is right for bytes that only have to look the same. It is wrong for the
 * bytes that decide whether a citation resolves: the reader gets the old behaviour once, sees the
 * wrong page, and never knows a newer answer existed. These files are 2–12 KB, so the cost of
 * asking the network first is small, and the cached copy still answers when there is no network —
 * offline loses nothing. The cache is NOT bumped for this: purging would take the keeping off the
 * device of someone who carried it deliberately, which is a worse harm than one stale load.
 */
const SHELL = ['/nh-home.js', '/nh-tools.js', '/nh-search.js', '/kinds.js', '/gate.js', '/sw.js'];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.allSettled(CORE.map((u) => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function cacheable(req, res) {
  return res && res.ok && res.type === 'basic' && req.method === 'GET';
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;          // never touch third parties
  if (NEVER.some((re) => re.test(url.pathname))) return;    // always live

  const isDoc = req.mode === 'navigate' ||
                (req.headers.get('accept') || '').includes('text/html');
  // the read-only KEEPING — network-first (fresh when there is a network, the last good copy when
  // there is not). The whole keeping travels with you: the floor, the coach, the apothecary, the
  // almanac, Scripture and its helps, the dictionary, the map, the codex.
  const isData = ['/graph', '/search', '/card', '/threads', '/floor', '/coach', '/apothecary',
                  '/passage', '/commentary', '/cross_refs', '/original', '/canon', '/almanac',
                  '/character', '/prophecy', '/seeds', '/codex', '/works', '/locate', '/library/health',
                  '/daily', '/resolve', '/word_study'].some((p) => url.pathname.startsWith(p));

  const isShell = SHELL.includes(url.pathname);

  if (isDoc || isData || isShell) {
    // NETWORK FIRST — fresh whenever there is a network; cached copy when there is not.
    e.respondWith(
      fetch(req)
        .then((res) => {
          if (cacheable(req, res)) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
        // A document with no network falls back to the companion page. A SCRIPT must not — handing
        // HTML to a <script> tag is a syntax error, and the page would lose the shell entirely.
        .catch(() => caches.match(req)
          .then((hit) => hit || (isShell ? Response.error() : caches.match())))
    );
    return;
  }

  // STATIC — stale-while-revalidate.
  e.respondWith(
    caches.match(req).then((hit) => {
      const live = fetch(req)
        .then((res) => {
          if (cacheable(req, res)) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => hit);
      return hit || live;
    })
  );
});

/* Web Push — a word on your door becomes a notification. The browser decrypts the aes128gcm payload
   (RFC 8291); we read {title, body, url} and show it. A servant signal, never bait. */
self.addEventListener('push', (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) { d = { body: (e.data && e.data.text()) || '' }; }
  const opts = {
    body: d.body || '', icon: '/icon.svg', badge: '/icon.svg',
    tag: d.tag || 'nh-mesh', data: { url: d.url || '/mesh.html#way' }
  };
  e.waitUntil(self.registration.showNotification(d.title || 'Narrow Highway', opts));
});

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || '/mesh.html#way';
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((wins) => {
      for (const w of wins) { if (w.url.includes() && 'focus' in w) return w.focus(); }
      return clients.openWindow(url);
    })
  );
});
