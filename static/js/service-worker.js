/* ============================================================
    SERVICE WORKER — DUNIA PWA
    Version 2.0.1 — Backend Web Push + safe offline shell
   ============================================================ */

const CACHE_NAME = 'dunia-shell-v2.0.1';
const RUNTIME_CACHE = 'dunia-runtime-v2.0.1';
const IMAGE_CACHE = 'dunia-images-v2.0.1';

const swPath = (typeof self !== 'undefined' && self.location && self.location.pathname) ? self.location.pathname : '/';
let BASE = swPath.replace(/\/service-worker\.js$/, '');
if (!BASE) BASE = '/';

function joinPath(p) {
    if (!p) return BASE;
    const cleanBase = BASE === '/' ? '/' : BASE.replace(/\/+$/, '');
    const cleanP = p.replace(/^\/+/, '');
    return cleanBase === '/' ? '/' + cleanP : cleanBase + '/' + cleanP;
}

const PRECACHE_URLS = [
    joinPath('static/documents/manifest.json'),
    joinPath('static/images/logo-dunia.png'),
    joinPath('static/icons/icon-192x192.png'),
    joinPath('static/documents/offline.html')
];

/* ============ INSTALLATION ============ */
self.addEventListener('install', (event) => {
    console.log('[SW] Installation en cours...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Pré-cache des fichiers essentiels...');

                return Promise.all(PRECACHE_URLS.map((url) => cache.add(url).catch(() => undefined)));
            })
            .then(() => {
                console.log('[SW] Pré-cache terminé — activation immédiate');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[SW] Erreur critique pré-cache:', error);
                return self.skipWaiting();
            })
    );
});

/* ============ ACTIVATION ============ */
self.addEventListener('activate', (event) => {
    console.log('[SW] Activation...');
    const currentCaches = [CACHE_NAME, RUNTIME_CACHE, IMAGE_CACHE];

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName.startsWith('dunia-') && !currentCaches.includes(cacheName)) {
                            console.log('[SW] Suppression ancien cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => self.clients.claim())
    );
});

/* ============ FETCH ============ */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (request.method !== 'GET') return;
    if (!url.protocol.startsWith('http')) return;
    if (url.origin !== self.location.origin) return;

    // Ignore les réseaux sociaux
    if (url.hostname.includes('wa.me') ||
        url.hostname.includes('facebook.com') ||
        url.hostname.includes('instagram.com') ||
        url.hostname.includes('linkedin.com')) {
        return;
    }

    // Polices Google
    if (url.hostname.includes('fonts.googleapis.com') ||
        url.hostname.includes('fonts.gstatic.com')) {
        event.respondWith(
            caches.open(RUNTIME_CACHE).then((cache) => {
                return cache.match(request).then((cachedResponse) => {
                    const fetchPromise = fetch(request).then((networkResponse) => {
                        cache.put(request, networkResponse.clone());
                        return networkResponse;
                    });
                    return cachedResponse || fetchPromise;
                });
            })
        );
        return;
    }

    // Images
    if (url.pathname.startsWith(joinPath('static/')) && (
        request.destination === 'image' || url.pathname.match(/\.(png|jpg|jpeg|gif|webp|svg|ico)$/)
    )) {
        event.respondWith(
            caches.open(IMAGE_CACHE).then((cache) => {
                return cache.match(request).then((cachedResponse) => {
                    if (cachedResponse) {
                        fetch(request).then((networkResponse) => {
                            if (networkResponse && networkResponse.status === 200) {
                                cache.put(request, networkResponse.clone());
                            }
                        }).catch(() => { });
                        return cachedResponse;
                    }
                    return fetch(request).then((networkResponse) => {
                        if (networkResponse && networkResponse.status === 200) {
                            cache.put(request, networkResponse.clone());
                        }
                        return networkResponse;
                    }).catch(() => caches.match(joinPath('static/images/logo-dunia.png')));
                });
            })
        );
        return;
    }

    // Ne jamais mettre en cache le HTML dynamique : pages de compte et données privées.
    if (request.mode === 'navigate' ||
        request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(
            fetch(request)
                .catch(() => {
                    return caches.match(joinPath('static/documents/offline.html'));
                })
        );
        return;
    }

    // CSS / JS : Cache First
    if (request.destination === 'style' ||
        request.destination === 'script' ||
        url.pathname.match(/\.(css|js)$/)) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) return cachedResponse;
                return fetch(request).then((networkResponse) => {
                    const responseClone = networkResponse.clone();
                    caches.open(RUNTIME_CACHE).then((cache) => {
                        cache.put(request, responseClone);
                    });
                    return networkResponse;
                });
            })
        );
        return;
    }

    // API, documents et médias privés restent toujours réseau uniquement.
    event.respondWith(fetch(request));
});

/* ============ MESSAGE ============ */
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

/* ============ PUSH NOTIFICATIONS ============ */

/**
 * Réception d'une notification Web Push chiffrée envoyée par Django.
 */
self.addEventListener('push', (event) => {
    let data = {
        title: 'DUNIA',
        body: 'Une nouvelle actualité est disponible sur notre site.',
        icon: joinPath('static/icons/icon-192x192.png'),
        badge: joinPath('static/icons/icon-96x96.png'),
        url: joinPath(''),
        tag: 'dunia-push'
    };

    // Tentative de lecture du payload JSON
    if (event.data) {
        try {
            const payload = event.data.json();
            if (payload.title) data.title = payload.title;
            if (payload.body) data.body = payload.body;
            if (payload.icon) data.icon = payload.icon;
            if (payload.badge) data.badge = payload.badge;
            if (payload.url) data.url = payload.url;
            if (payload.tag) data.tag = payload.tag;
        } catch (e) {
            // Payload non-JSON — on conserve les valeurs par défaut
            const text = event.data.text();
            if (text) data.body = text;
        }
    }

    const options = {
        body: data.body,
        icon: data.icon,
        badge: data.badge,
        tag: data.tag,
        renotify: true,
        vibrate: [200, 100, 200],
        data: { url: data.url },
        actions: [
            { action: 'open', title: 'Ouvrir Dunia' },
            { action: 'dismiss', title: '✕ Fermer' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

/**
 * Clic sur la notification — ouvre la page cible ou focus l'onglet existant.
 */
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'dismiss') return;

    const requestedUrl = event.notification.data && event.notification.data.url
        ? event.notification.data.url
        : joinPath('');
    const target = new URL(requestedUrl, self.location.origin);
    const targetUrl = target.origin === self.location.origin ? target.href : self.location.origin + joinPath('');

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((windowClients) => {
                // Chercher un onglet existant avec la même URL
                for (const client of windowClients) {
                    if (new URL(client.url).origin === self.location.origin && 'focus' in client) {
                        return client.navigate(targetUrl).then((windowClient) => windowClient.focus());
                    }
                }
                // Sinon ouvrir un nouvel onglet
                if (clients.openWindow) {
                    return clients.openWindow(targetUrl);
                }
            })
    );
});