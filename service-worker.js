// Service Worker para HuertoRentable PWA
// Proporciona funcionalidad offline y cacheo de recursos

// Versión fija - solo cambiar cuando hay actualizaciones reales
const CACHE_VERSION = "v2.4";
const CACHE_NAME = "huertorentable-" + CACHE_VERSION;
const STATIC_CACHE = "huertorentable-static-" + CACHE_VERSION;
const DYNAMIC_CACHE = "huertorentable-dynamic-" + CACHE_VERSION;

// Recursos estáticos para cachear inmediatamente
const STATIC_ASSETS = [
  "/",
  "/static/css/styles.css",
  "/static/js/app.js",
  "/static/img/icon.png",
  "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
  "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css",
  "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
  "https://cdn.jsdelivr.net/npm/chart.js",
  "/manifest.json",
];

// URLs que siempre deben intentar la red primero
const NETWORK_FIRST_URLS = ["/crops", "/analytics", "/api/"];

// Página offline de respaldo
const OFFLINE_PAGE = "/offline.html";

// ================================
// EVENTOS DEL SERVICE WORKER
// ================================

// Evento de instalación - cachear recursos estáticos
self.addEventListener("install", (event) => {
  console.log("🔧 Service Worker: Instalando...");

  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => {
        console.log("📦 Service Worker: Cacheando recursos estáticos");
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log("✅ Service Worker: Recursos estáticos cacheados");
        // Forzar activación inmediata
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error("❌ Error cacheando recursos estáticos:", error);
      })
  );
});

// Evento de activación - limpiar caches antiguos y notificar actualización
self.addEventListener("activate", (event) => {
  console.log("🚀 Service Worker: Activando versión", CACHE_VERSION);

  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        // Eliminar TODOS los caches antiguos de HuertoRentable
        const deletePromises = cacheNames
          .map((cacheName) => {
            if (
              cacheName !== STATIC_CACHE &&
              cacheName !== DYNAMIC_CACHE &&
              (cacheName.startsWith("huertorentable-") ||
                cacheName.includes("huertorentable"))
            ) {
              console.log(
                "🗑️ Service Worker: Eliminando cache antiguo:",
                cacheName
              );
              return caches.delete(cacheName);
            }
          })
          .filter(Boolean);

        return Promise.all(deletePromises);
      })
      .then(() => {
        console.log("✅ Service Worker: Activado y limpieza completada");
        // Tomar control de todas las páginas inmediatamente
        return self.clients.claim();
      })
      .then(() => {
        // Notificar a todos los clientes sobre la actualización
        return self.clients.matchAll().then((clients) => {
          clients.forEach((client) => {
            client.postMessage({
              type: "SW_UPDATED",
              version: CACHE_VERSION,
              message: "Nueva versión disponible",
            });
          });
        });
      })
  );
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

// Evento de fetch - interceptar requests y aplicar estrategias de cache
self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Solo manejar requests GET
  if (request.method !== "GET") {
    return;
  }

  // Ignorar requests de Chrome extensions y dev tools
  if (
    url.protocol === "chrome-extension:" ||
    url.protocol === "moz-extension:" ||
    (url.hostname === "localhost" && url.port === "3000")
  ) {
    return;
  }

  const path = url.pathname || "";

  // Solo interceptar assets estáticos (css/js/img/icon/manifest) dentro de /static o raíz conocida
  const isStaticAsset =
    path.startsWith("/static/") ||
    path.endsWith(".css") ||
    path.endsWith(".js") ||
    path.endsWith(".png") ||
    path.endsWith(".jpg") ||
    path.endsWith(".jpeg") ||
    path.endsWith(".svg") ||
    path.endsWith(".ico") ||
    path.endsWith(".webmanifest") ||
    path === "/manifest.json";

  // Bypass todo lo que no sea estático (HTML, APIs, auth, analytics, crops, etc.)
  if (!isStaticAsset) {
    return; // No interceptar; dejar pasar al navegador/red
  }

  event.respondWith(handleRequest(request));
});

// ================================
// ESTRATEGIAS DE CACHING
// ================================

async function handleRequest(request) {
  const url = new URL(request.url);

  try {
    // 1. Para APIs y páginas dinámicas: Network First
    if (shouldUseNetworkFirst(url.pathname)) {
      return await networkFirstStrategy(request);
    }

    // 2. Para recursos estáticos: Cache First
    if (shouldUseCacheFirst(url.pathname)) {
      return await cacheFirstStrategy(request);
    }

    // 3. Para navegación (HTML): Network First con fallback offline
    if (request.mode === "navigate") {
      return await navigationStrategy(request);
    }

    // 4. Para todo lo demás: Stale While Revalidate
    return await staleWhileRevalidateStrategy(request);
  } catch (error) {
    console.error("❌ Error en handleRequest:", error);
    return await getOfflineResponse(request);
  }
}

// Network First - para datos dinámicos
async function networkFirstStrategy(request) {
  try {
    // Intentar red primero
    const networkResponse = await fetch(request);

    // Si es exitoso, cachear y devolver
    if (
      networkResponse &&
      networkResponse.ok &&
      networkResponse.type !== "opaqueredirect"
    ) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    // Si falla la red, buscar en cache
    console.log("🔄 Network failed, trying cache for:", request.url);
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
      return cachedResponse;
    }

    // Si no hay cache, devolver respuesta offline
    return await getOfflineResponse(request);
  }
}

// Cache First - para recursos estáticos
async function cacheFirstStrategy(request) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  // Si no está en cache, buscar en red y cachear
  try {
    const networkResponse = await fetch(request);

    if (
      networkResponse &&
      networkResponse.ok &&
      networkResponse.type !== "opaqueredirect"
    ) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    return await getOfflineResponse(request);
  }
}

// Navigation Strategy - para páginas HTML
async function navigationStrategy(request) {
  try {
    // Intentar red primero
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    // Si falla, buscar página en cache
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
      return cachedResponse;
    }

    // Si no hay cache, mostrar página offline
    return (
      (await caches.match("/")) ||
      (await caches.match("/offline.html")) ||
      new Response("Offline - HuertoRentable no disponible", {
        status: 200,
        headers: { "Content-Type": "text/html" },
      })
    );
  }
}

// Stale While Revalidate - para recursos que pueden estar desactualizados
async function staleWhileRevalidateStrategy(request) {
  const cachedResponse = await caches.match(request);

  // Fetch en paralelo para actualizar cache
  const fetchPromise = fetch(request)
    .then((networkResponse) => {
      try {
        if (
          networkResponse &&
          networkResponse.ok &&
          networkResponse.type !== "opaqueredirect"
        ) {
          const cache = caches.open(DYNAMIC_CACHE);
          cache.then((c) => c.put(request, networkResponse.clone()));
        }
      } catch (e) {
        // Evitar "Response body is already used" y problemas con redirecciones opacas
        console.warn("[SW] No se cachea respuesta por tipo/estado:", e);
      }
      return networkResponse;
    })
    .catch(() => {
      console.log("🔄 Network failed for stale-while-revalidate:", request.url);
    });

  // Devolver cache inmediatamente si existe, sino esperar red
  return cachedResponse || (await fetchPromise);
}

// ================================
// FUNCIONES AUXILIARES
// ================================

function shouldUseNetworkFirst(pathname) {
  // Con la nueva política, no usamos Network First salvo que en el futuro lo reactivemos
  return false;
}

function shouldUseCacheFirst(pathname) {
  return (
    pathname.startsWith("/static/") ||
    pathname.endsWith(".css") ||
    pathname.endsWith(".js") ||
    pathname.endsWith(".png") ||
    pathname.endsWith(".jpg") ||
    pathname.endsWith(".ico")
  );
}

async function getOfflineResponse(request) {
  // Para navegación u otros, no respondemos (dejamos a la red/navegador) porque no interceptamos no-estáticos

  // Para otros recursos, respuesta básica
  return new Response("Recurso no disponible offline", {
    status: 503,
    statusText: "Service Unavailable",
  });
}

// ================================
// EVENTOS DE SINCRONIZACIÓN
// ================================

// Background Sync para sincronizar datos cuando vuelva la conexión
self.addEventListener("sync", (event) => {
  console.log("🔄 Background Sync:", event.tag);

  if (event.tag === "sync-cultivos") {
    event.waitUntil(syncCultivos());
  }
});

async function syncCultivos() {
  try {
    // Obtener datos pendientes de sincronización del IndexedDB
    // Esto se implementaría con la lógica de la app
    console.log("🔄 Sincronizando cultivos...");

    // Simular sincronización exitosa
    console.log("✅ Cultivos sincronizados");
  } catch (error) {
    console.error("❌ Error sincronizando cultivos:", error);
    throw error;
  }
}

// ================================
// NOTIFICACIONES PUSH (FUTURO)
// ================================

self.addEventListener("push", (event) => {
  console.log("📱 Push notification recibida");

  const options = {
    body: event.data ? event.data.text() : "Nueva actualización en tu huerto",
    icon: "/static/img/icon.png",
    badge: "/static/img/icon.png",
    vibrate: [200, 100, 200],
    tag: "huerto-notification",
    actions: [
      {
        action: "view",
        title: "Ver Huerto",
      },
    ],
  };

  event.waitUntil(
    self.registration.showNotification("HuertoRentable", options)
  );
});

// Manejar clicks en notificaciones
self.addEventListener("notificationclick", (event) => {
  console.log("🔔 Notification clicked:", event.action);

  event.notification.close();

  event.waitUntil(clients.openWindow("/"));
});

console.log("✅ Service Worker cargado correctamente");
