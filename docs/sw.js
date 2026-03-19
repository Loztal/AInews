var CACHE_VERSION = 'claude-daily-v1';

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
                    return response;
                })
                .catch(function () {
                    return caches.match(event.request);
                })
        );
        return;
    }

    // Cache-first for everything else
    event.respondWith(
        caches.match(event.request).then(function (cached) {
            return cached || fetch(event.request);
        })
    );
});
