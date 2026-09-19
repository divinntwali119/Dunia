/* ============================================================
   SERVICE WORKER — DUNIA PWA (GitHub Pages /Dunia/)
   Version 1.2.0 — Installation tolérante aux erreurs
   ============================================================ */

const CACHE_NAME = 'dunia-v1.2.0';
const RUNTIME_CACHE = 'dunia-runtime-v1.2.0';
const IMAGE_CACHE = 'dunia-images-v1.2.0';

/* Détecte dynamiquement la base du site selon l'emplacement du service worker */
const swPath = (typeof self !== 'undefined' && self.location && self.location.pathname) ? self.location.pathname : '/';
let BASE = swPath.replace(/\/service-worker\.js$/, '');
if (!BASE) BASE = '/';

function joinPath(p) {
  if (!p) return BASE;
  const cleanBase = BASE === '/' ? '/' : BASE.replace(/\/+$/, '');
  const cleanP = p.replace(/^\/+/, '');
  return cleanBase === '/' ? '/' + cleanP : cleanBase + '/' + cleanP;
}

/* Fichiers essentiels — leur absence ne bloque PAS l'installation */
const PRECACHE_URLS = [
  joinPath(''),
  joinPath('index.html'),
  joinPath('formations.html'),
  joinPath('offline.html'),
  joinPath('manifest.json'),
  joinPath('images/logo-dunia.png')
];

/* Fichiers optionnels — ignorés silencieusement si manquants */
const OPTIONAL_URLS = [
  joinPath('icons/icon-32x32.png'),
  joinPath('icons/icon-96x96.png'),
  joinPath('icons/icon-128x128.png'),
  joinPath('icons/icon-144x144.png'),
  joinPath('icons/icon-152x152.png'),
  joinPath('icons/icon-180x180.png'),
  joinPath('icons/icon-192x192.png'),
  joinPath('icons/icon-384x384.png'),
  joinPath('icons/icon-512x512.png'),
  joinPath('icons/icon-192x192-maskable.png'),
  joinPath('icons/icon-512x512-maskable.png')
];

/* ============ INSTALLATION ============ */
self.addEventListener('install', (event) => {
  console.log('[SW] Installation en cours...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Pré-cache des fichiers essentiels...');

        const essentialPromises = PRECACHE_URLS.map((url) => {
          return cache.add(url).catch((err) => {
            console.warn('[SW] Fichier essentiel manquant:', url, err.message);
          });
        });

        const optionalPromises = OPTIONAL_URLS.map((url) => {
          return cache.add(url).catch(() => {
            /* Silencieux */
          });
        });

        return Promise.all([...essentialPromises, ...optionalPromises]);
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
            if (!currentCaches.includes(cacheName)) {
              console.log('[SW] Suppression ancien cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Activation terminée — prise de contrôle');
        return self.clients.claim();
      })
  );
});

/* ============ FETCH ============ */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET') return;
  if (!url.protocol.startsWith('http')) return;

  /* Ignorer réseaux sociaux et domaines externes */
  if (url.hostname.includes('wa.me') ||
      url.hostname.includes('whatsapp.com') ||
      url.hostname.includes('facebook.com') ||
      url.hostname.includes('instagram.com') ||
      url.hostname.includes('linkedin.com') ||
      url.hostname.includes('youtube.com') ||
      url.hostname.includes('tiktok.com') ||
      url.hostname.includes('pinimg.com') ||
      url.hostname.includes('unsplash.com') ||
      url.hostname.includes('fbcdn.net') ||
      url.hostname.includes('fna.fbcdn.net')) {
    return;
  }

  /* Polices Google */
  if (url.hostname.includes('fonts.googleapis.com') ||
      url.hostname.includes('fonts.gstatic.com')) {
    event.respondWith(
      caches.open(RUNTIME_CACHE).then((cache) => {
        return cache.match(request).then((cachedResponse) => {
          const fetchPromise = fetch(request).then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              cache.put(request, networkResponse.clone());
            }
            return networkResponse;
          }).catch(() => cachedResponse);
          return cachedResponse || fetchPromise;
        });
      })
    );
    return;
  }

  /* CDN externes */
  if (url.hostname.includes('cdn.tailwindcss.com') ||
      url.hostname.includes('cdnjs.cloudflare.com')) {
    event.respondWith(
      caches.open(RUNTIME_CACHE).then((cache) => {
        return cache.match(request).then((cachedResponse) => {
          const fetchPromise = fetch(request).then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              cache.put(request, networkResponse.clone());
            }
            return networkResponse;
          }).catch(() => cachedResponse);
          return cachedResponse || fetchPromise;
        });
      })
    );
    return;
  }

  /* Images */
  if (request.destination === 'image' ||
      url.pathname.match(/\.(png|jpg|jpeg|gif|webp|svg|ico)$/i)) {
    event.respondWith(
      caches.open(IMAGE_CACHE).then((cache) => {
        return cache.match(request).then((cachedResponse) => {
          if (cachedResponse) {
            fetch(request).then((networkResponse) => {
              if (networkResponse && networkResponse.status === 200) {
                cache.put(request, networkResponse.clone());
              }
            }).catch(() => {});
            return cachedResponse;
          }
          return fetch(request).then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              cache.put(request, networkResponse.clone());
            }
            return networkResponse;
          }).catch(() => {
            return caches.match(BASE + '/images/logo-dunia.png');
          });
        });
      })
    );
    return;
  }

  /* Vidéos — Network First */
  if (request.destination === 'video' ||
      url.pathname.match(/\.(mp4|webm|ogg)$/i)) {
    event.respondWith(
      fetch(request).catch(() => caches.match(request))
    );
    return;
  }

  /* HTML — Network First */
  if (request.mode === 'navigate' ||
      (request.headers.get('accept') && request.headers.get('accept').includes('text/html'))) {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
          return networkResponse;
        })
        .catch(() => {
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) return cachedResponse;
            return caches.match(BASE + '/offline.html');
          });
        })
    );
    return;
  }

  /* CSS / JS — Cache First */
  if (request.destination === 'style' ||
      request.destination === 'script' ||
      url.pathname.match(/\.(css|js)$/i)) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) return cachedResponse;
        return fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return networkResponse;
        }).catch(() => {
          return new Response('', { status: 408, statusText: 'Offline' });
        });
      })
    );
    return;
  }

  /* Par défaut */
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) return cachedResponse;
      return fetch(request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseClone = networkResponse.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return networkResponse;
      });
    }).catch(() => {
      if (request.mode === 'navigate') {
        return caches.match(BASE + '/offline.html');
      }
      return new Response('', { status: 408, statusText: 'Offline' });
    })
  );
});

/* ============ MESSAGE ============ */
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (event.data && event.data.type === 'CHECK_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});