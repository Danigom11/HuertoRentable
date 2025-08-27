/*
 * JavaScript principal para HuertoRentable PWA
 * Funcionalidades comunes, PWA y utilidades
 */

// ================================
// CONFIGURACIÓN GLOBAL
// ================================

const HuertoApp = {
  version: "1.0.0",
  isOnline: navigator.onLine,
  user: null,
  config: {
    apiBaseUrl: window.location.origin,
    enableNotifications: true,
    enableGeolocation: false,
    cacheDuration: 5 * 60 * 1000, // 5 minutos
  },
};

// ================================
// INICIALIZACIÓN DE LA APP
// ================================

document.addEventListener("DOMContentLoaded", function () {
  console.log("🌱 HuertoRentable v" + HuertoApp.version + " iniciando...");

  // Inicializar funcionalidades principales
  initializeApp();
  setupEventListeners();
  checkAuthentication();
  setupPWAFeatures();

  console.log("✅ HuertoRentable cargado correctamente");
});

function initializeApp() {
  // Configurar usuario si está autenticado
  const userData = localStorage.getItem("huerto_user");
  if (userData) {
    try {
      HuertoApp.user = JSON.parse(userData);
      updateUIForUser();
    } catch (error) {
      console.error("Error parsing user data:", error);
      localStorage.removeItem("huerto_user");
    }
  }

  // Configurar estado inicial de conexión
  updateConnectionStatus();

  // Inicializar tooltips de Bootstrap
  initializeTooltips();
}

function setupEventListeners() {
  // Eventos de conexión
  window.addEventListener("online", handleOnline);
  window.addEventListener("offline", handleOffline);

  // Eventos de visibilidad (para optimización)
  document.addEventListener("visibilitychange", handleVisibilityChange);

  // Eventos de instalación PWA
  window.addEventListener("beforeinstallprompt", handleInstallPrompt);
  window.addEventListener("appinstalled", handleAppInstalled);

  // Eventos globales de error
  window.addEventListener("error", handleGlobalError);
  window.addEventListener("unhandledrejection", handleUnhandledRejection);
}

// ================================
// GESTIÓN DE AUTENTICACIÓN
// ================================

function checkAuthentication() {
  const authStatus = localStorage.getItem("huerto_auth");
  const currentPath = window.location.pathname;

  // Si no está autenticado y no está en login, redirigir
  if (!authStatus && currentPath !== "/login" && currentPath !== "/") {
    // En desarrollo, permitir acceso directo para testing
    if (HuertoApp.config.isDevelopment) {
      console.log("🔧 Modo desarrollo: saltando autenticación");
      return;
    }

    console.log("🔐 Redirigiendo a login...");
    window.location.href = "/login";
    return;
  }

  // Si está autenticado y está en login, redirigir a dashboard
  if (authStatus && currentPath === "/login") {
    window.location.href = "/";
    return;
  }
}

function updateUIForUser() {
  if (!HuertoApp.user) return;

  // Actualizar elementos de UI que muestren info del usuario
  const userElements = document.querySelectorAll("[data-user-info]");
  userElements.forEach((element) => {
    const field = element.getAttribute("data-user-info");
    if (HuertoApp.user[field]) {
      element.textContent = HuertoApp.user[field];
    }
  });

  // Mostrar badge de demo si corresponde
  if (HuertoApp.user.esDemo) {
    showDemoBadge();
  }
}

function showDemoBadge() {
  const navbar = document.querySelector(".navbar-nav");
  if (navbar && !document.querySelector(".demo-badge")) {
    const demoBadge = document.createElement("span");
    demoBadge.className = "badge bg-warning demo-badge ms-2";
    demoBadge.textContent = "DEMO";
    navbar.appendChild(demoBadge);
  }
}

// ================================
// GESTIÓN DE CONEXIÓN
// ================================

function handleOnline() {
  console.log("🟢 Conexión restaurada");
  HuertoApp.isOnline = true;
  updateConnectionStatus();

  // Mostrar notificación
  showNotification("Conexión restaurada", "success");

  // Sincronizar datos pendientes
  syncPendingData();
}

function handleOffline() {
  console.log("🔴 Conexión perdida");
  HuertoApp.isOnline = false;
  updateConnectionStatus();

  // Mostrar notificación
  showNotification(
    "Sin conexión - Los datos se guardarán localmente",
    "warning"
  );
}

function updateConnectionStatus() {
  const wifiIcon = document.getElementById("wifi-icon");
  const lastSync = document.getElementById("last-sync");

  if (wifiIcon) {
    if (HuertoApp.isOnline) {
      wifiIcon.className = "bi bi-wifi text-light";
    } else {
      wifiIcon.className = "bi bi-wifi-off text-warning";
    }
  }

  if (lastSync) {
    if (HuertoApp.isOnline) {
      lastSync.textContent = "Conectado";
    } else {
      lastSync.textContent = "Sin conexión";
    }
  }
}

// ================================
// PWA FUNCIONALIDADES
// ================================

function setupPWAFeatures() {
  // Configurar actualizaciones del Service Worker
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      console.log("🔄 Service Worker actualizado");
      showNotification("Aplicación actualizada", "info");
    });
  }

  // Configurar notificaciones push si están disponibles
  if ("Notification" in window && HuertoApp.config.enableNotifications) {
    setupNotifications();
  }
}

let deferredPrompt = null;

function handleInstallPrompt(e) {
  console.log("💾 App se puede instalar");

  // Prevenir el prompt automático
  e.preventDefault();
  deferredPrompt = e;

  // Mostrar botón de instalación personalizado
  showInstallButton();
}

function handleAppInstalled() {
  console.log("✅ App instalada correctamente");
  deferredPrompt = null;
  hideInstallButton();
  showNotification("¡HuertoRentable instalado correctamente!", "success");
}

function showInstallButton() {
  // Crear botón de instalación si no existe
  let installButton = document.getElementById("install-button");
  if (!installButton && deferredPrompt) {
    installButton = document.createElement("button");
    installButton.id = "install-button";
    installButton.className = "btn btn-outline-light btn-sm ms-2";
    installButton.innerHTML = '<i class="bi bi-download me-1"></i>Instalar';
    installButton.onclick = installApp;

    const navbar = document.querySelector(".navbar-nav");
    if (navbar) {
      navbar.appendChild(installButton);
    }
  }
}

function hideInstallButton() {
  const installButton = document.getElementById("install-button");
  if (installButton) {
    installButton.remove();
  }
}

async function installApp() {
  if (!deferredPrompt) return;

  try {
    // Mostrar prompt de instalación
    deferredPrompt.prompt();

    // Esperar respuesta del usuario
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === "accepted") {
      console.log("✅ Usuario aceptó instalación");
    } else {
      console.log("❌ Usuario rechazó instalación");
    }

    deferredPrompt = null;
    hideInstallButton();
  } catch (error) {
    console.error("Error durante instalación:", error);
  }
}

// ================================
// NOTIFICACIONES
// ================================

async function setupNotifications() {
  if (Notification.permission === "default") {
    const permission = await Notification.requestPermission();
    console.log("🔔 Permisos de notificación:", permission);
  }
}

function showNotification(message, type = "info", duration = 4000) {
  // Crear notificación en pantalla
  const notification = document.createElement("div");
  notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  notification.style.cssText = `
    top: 20px;
    right: 20px;
    z-index: 9999;
    max-width: 300px;
    box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
  `;

  notification.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(notification);

  // Auto-remover después del duration
  setTimeout(() => {
    if (notification.parentNode) {
      notification.remove();
    }
  }, duration);

  // También crear notificación push si está disponible
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification("HuertoRentable", {
      body: message,
      icon: "/static/img/icon.png",
      tag: "huerto-notification",
    });
  }
}

// ================================
// UTILIDADES Y HELPERS
// ================================

function initializeTooltips() {
  // Inicializar tooltips de Bootstrap
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

// Formatear números para mostrar
function formatNumber(number, decimals = 2) {
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(number);
}

// Formatear fechas
function formatDate(date, options = {}) {
  const defaultOptions = {
    year: "numeric",
    month: "long",
    day: "numeric",
  };

  return new Intl.DateTimeFormat("es-ES", {
    ...defaultOptions,
    ...options,
  }).format(new Date(date));
}

// Debounce para optimizar búsquedas
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ================================
// GESTIÓN DE ERRORES
// ================================

function handleGlobalError(error) {
  console.error("❌ Error global:", error);

  // En desarrollo, mostrar error detallado
  if (window.location.hostname === "localhost") {
    showNotification(`Error: ${error.message}`, "danger", 8000);
  } else {
    showNotification("Ha ocurrido un error inesperado", "danger");
  }
}

function handleUnhandledRejection(event) {
  console.error("❌ Promise rejection no manejada:", event.reason);

  // Prevenir que aparezca en consola
  event.preventDefault();

  showNotification("Error de conexión o procesamiento", "warning");
}

// ================================
// FUNCIONES DE API
// ================================

async function apiRequest(endpoint, options = {}) {
  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  };

  try {
    const response = await fetch(
      `${HuertoApp.config.apiBaseUrl}${endpoint}`,
      defaultOptions
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error en API ${endpoint}:`, error);

    if (!HuertoApp.isOnline) {
      showNotification(
        "Sin conexión - Los datos se guardarán localmente",
        "warning"
      );
      // Aquí se podría guardar en IndexedDB para sincronizar después
    } else {
      showNotification("Error de conexión con el servidor", "danger");
    }

    throw error;
  }
}

// ================================
// SINCRONIZACIÓN DE DATOS
// ================================

async function syncPendingData() {
  console.log("🔄 Sincronizando datos pendientes...");

  try {
    // Obtener datos pendientes del almacenamiento local
    const pendingData = localStorage.getItem("huerto_pending_sync");
    if (!pendingData) {
      console.log("✅ No hay datos pendientes de sincronización");
      return;
    }

    const data = JSON.parse(pendingData);
    console.log("📦 Datos a sincronizar:", data.length, "elementos");

    // Procesar cada elemento pendiente
    for (const item of data) {
      try {
        await apiRequest(item.endpoint, item.options);
        console.log("✅ Sincronizado:", item.id);
      } catch (error) {
        console.error("❌ Error sincronizando:", item.id, error);
      }
    }

    // Limpiar datos sincronizados
    localStorage.removeItem("huerto_pending_sync");
    showNotification("Datos sincronizados correctamente", "success");
  } catch (error) {
    console.error("❌ Error en sincronización:", error);
  }
}

// ================================
// EVENTOS DE CICLO DE VIDA
// ================================

function handleVisibilityChange() {
  if (document.hidden) {
    console.log("👁️ App en background");
  } else {
    console.log("👁️ App en foreground");
    // Verificar conexión y sincronizar si es necesario
    if (navigator.onLine && HuertoApp.isOnline !== navigator.onLine) {
      handleOnline();
    }
  }
}

// ================================
// EXPORTAR FUNCIONES GLOBALES
// ================================

// Hacer disponibles algunas funciones globalmente
window.HuertoApp = HuertoApp;
window.showNotification = showNotification;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.apiRequest = apiRequest;

// ================================
// SISTEMA DE ACTUALIZACIONES PWA
// ================================

// Función para verificar actualizaciones desde el servidor
function checkForUpdates() {
  fetch("/version", {
    cache: "no-cache",
    headers: {
      "Cache-Control": "no-cache, no-store, must-revalidate",
      Pragma: "no-cache",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.force_reload) {
        console.log("🔄 Actualización forzada detectada desde servidor");
        // Limpiar todos los caches
        if ("caches" in window) {
          caches.keys().then((names) => {
            names.forEach((name) => {
              if (name.includes("huertorentable")) {
                caches.delete(name);
              }
            });
          });
        }

        // Mostrar notificación y recargar
        showUpdateNotification();
      }
    })
    .catch((error) => {
      console.log("No se pudo verificar actualizaciones:", error);
    });
}

// Mostrar notificación de actualización
function showUpdateNotification() {
  const updateNotification = document.createElement("div");
  updateNotification.className =
    "alert alert-success alert-dismissible position-fixed top-0 start-50 translate-middle-x mt-3";
  updateNotification.style.zIndex = "9999";
  updateNotification.innerHTML = `
    <div class="d-flex align-items-center">
      <i class="bi bi-arrow-clockwise me-2"></i>
      <span class="me-auto"><strong>¡Nueva versión disponible!</strong></span>
      <button type="button" class="btn btn-sm btn-success me-2" onclick="window.location.reload(true)">
        Actualizar Ahora
      </button>
      <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
    </div>
  `;

  document.body.appendChild(updateNotification);

  // Auto-recargar después de 3 segundos
  setTimeout(() => {
    console.log("🔄 Recargando automáticamente...");
    window.location.reload(true);
  }, 3000);
}

// Detectar actualizaciones del Service Worker
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.addEventListener("message", (event) => {
    if (event.data && event.data.type === "SW_UPDATED") {
      console.log("🔄 Nueva versión detectada:", event.data.version);
      showUpdateNotification();
    }
  });

  // TEMPORALMENTE DESACTIVADO - verificar actualizaciones del servidor
  // setInterval(checkForUpdates, 10000); // Cada 10 segundos
  // setTimeout(checkForUpdates, 2000);

  // Service Worker update check - solo cuando sea necesario
  navigator.serviceWorker.ready.then((registration) => {
    // Verificar actualizaciones menos frecuentemente
    setInterval(() => {
      registration.update();
    }, 60000); // Cada minuto en lugar de 15 segundos
  });
}

console.log("✅ JavaScript principal de HuertoRentable cargado");
