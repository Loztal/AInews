var CACHE_VERSION = 'claude-daily-v3';

var APP_SHELL = [
    './',
    './index.html',
    './css/style.css',
    './js/app.js',
    './js/briefing.js',
    './manifest.webmanifest',
    './icons/icon-192.png'
];

// Install: cache app shell
self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(CACHE_VERSION).then(function (cache) {
            return cache.addAll(APP_SHELL);
        })
    );
    self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(
                keys.filter(function (key) { return key !== CACHE_VERSION; })
                    .map(function (key) { return caches.delete(key); })
            );
        })
    );
    self.clients.claim();
});

// Fetch: network-first for data, cache-first for app shell
self.addEventListener('fetch', function (event) {
    var url = new URL(event.request.url);

    // Network-first for briefing data
    if (url.pathname.endsWith('briefing.json')) {
        event.respondWith(
            fetch(event.request)
                .then(function (response) {
                    var clone = response.clone();
                    caches.open(CACHE_VERSION).then(function (cache) {
                        cache.put(event.request, clone);
                    });
                    // Signal online to clients
                    notifyClients({ type: 'data-source', source: 'network' });
                    return response;
                })
                .catch(function () {
                    // Signal offline/cached to clients
                    notifyClients({ type: 'data-source', source: 'cache' });
                    return caches.match(event.request);
                })
        );
        return;
    }

    // Stale-while-revalidate for app shell
    event.respondWith(
        caches.open(CACHE_VERSION).then(function (cache) {
            return cache.match(event.request).then(function (cached) {
                var fetched = fetch(event.request).then(function (response) {
                    cache.put(event.request, response.clone());
                    return response;
                });
                return cached || fetched;
            });
        })
    );
});

function notifyClients(msg) {
    self.clients.matchAll().then(function (clients) {
        clients.forEach(function (client) {
            client.postMessage(msg);
        });
    });
}
