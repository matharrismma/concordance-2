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
const CACHE = 'nh-offline-v1';

/* The floor: what must be there with no network at all. Best-effort — a miss never
   fails the install (a failed install would leave the site with no worker at all). */
const CORE = [
  '/', '/index.html', '/companion.html', '/ask.html',
  '/kinds.js', '/speak.js', '/gate.js'
];

/* Never cache: anything that must be live-verified or is per-request. */
const NEVER = [/^\/verify/, /^\/seal/, /^\/s\//, /^\/audit/, /^\/speak/];

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
  const isData = url.pathname.startsWith('/graph') || url.pathname.startsWith('/search') ||
                 url.pathname.startsWith('/card') || url.pathname.startsWith('/threads');

  if (isDoc || isData) {
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
        .catch(() => caches.match(req).then((hit) => hit || caches.match('/companion.html')))
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
