/*
 * HuertoRentable - PWA con Firebase
 * JavaScript principal para Firebase Hosting
 */

// ================================
// CONFIGURACIÓN DE FIREBASE
// ================================

const firebaseConfig = {
  apiKey: "AIzaSyANFRY9_m3KL_Riiiep9V0t5EbY0UBu-zo",
  authDomain: "huerto-rentable.firebaseapp.com",
  projectId: "huerto-rentable",
  storageBucket: "huerto-rentable.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef123456789012",
};

// Inicializar Firebase
let app, auth, db;

// ================================
// ESTADO GLOBAL DE LA APP
// ================================

const HuertoApp = {
  version: "2.0.0",
  currentUser: null,
  cultivos: [],
  currentSection: "dashboard",
  modals: {},
  charts: {},
};

// ================================
// INICIALIZACIÓN
// ================================

document.addEventListener("DOMContentLoaded", function () {
  console.log("🌱 HuertoRentable v" + HuertoApp.version + " iniciando...");

  initializeFirebase();
  initializeApp();
  setupEventListeners();

  console.log("✅ HuertoRentable cargado correctamente");
});

function initializeFirebase() {
  try {
    // Inicializar Firebase v8
    app = firebase.initializeApp(firebaseConfig);
    auth = firebase.auth();
    db = firebase.firestore();

    console.log("🔥 Firebase inicializado correctamente");

    // Configurar observador de autenticación
    auth.onAuthStateChanged((user) => {
      if (user) {
        HuertoApp.currentUser = user;
        updateUIForAuthenticatedUser(user);
        loadUserData();
      } else {
        HuertoApp.currentUser = null;
        updateUIForGuestUser();
      }
    });
  } catch (error) {
    console.error("Error inicializando Firebase:", error);
  }
}

function initializeApp() {
  // Inicializar modales de Bootstrap
  try {
    HuertoApp.modals.login = new bootstrap.Modal(
      document.getElementById("loginModal")
    );
    HuertoApp.modals.register = new bootstrap.Modal(
      document.getElementById("registerModal")
    );
    HuertoApp.modals.nuevoCultivo = new bootstrap.Modal(
      document.getElementById("nuevoCultivoModal")
    );
  } catch (error) {
    console.error("Error inicializando modales:", error);
  }

  // Configurar fecha por defecto
  const today = new Date().toISOString().split("T")[0];
  const fechaInput = document.getElementById("cultivoFechaSiembra");
  if (fechaInput) {
    fechaInput.value = today;
  }
}

function setupEventListeners() {
  // Formularios
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const nuevoCultivoForm = document.getElementById("nuevoCultivoForm");

  if (loginForm) loginForm.addEventListener("submit", handleLogin);
  if (registerForm) registerForm.addEventListener("submit", handleRegister);
  if (nuevoCultivoForm)
    nuevoCultivoForm.addEventListener("submit", handleNuevoCultivo);
}

// ================================
// AUTENTICACIÓN
// ================================

async function handleLogin(e) {
  e.preventDefault();

  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;

  try {
    await auth.signInWithEmailAndPassword(email, password);
    HuertoApp.modals.login.hide();
    showAlert("¡Bienvenido de nuevo!", "success");
  } catch (error) {
    console.error("Error de login:", error);
    showAlert("Error al iniciar sesión: " + error.message, "danger");
  }
}

async function handleRegister(e) {
  e.preventDefault();

  const email = document.getElementById("registerEmail").value;
  const password = document.getElementById("registerPassword").value;
  const name = document.getElementById("registerName").value;

  try {
    const userCredential = await auth.createUserWithEmailAndPassword(
      email,
      password
    );

    // Guardar datos adicionales del usuario
    await db.collection("users").add({
      uid: userCredential.user.uid,
      name: name,
      email: email,
      createdAt: new Date(),
      plan: "gratuito",
    });

    HuertoApp.modals.register.hide();
    showAlert("¡Cuenta creada exitosamente!", "success");
  } catch (error) {
    console.error("Error de registro:", error);
    showAlert("Error al registrarse: " + error.message, "danger");
  }
}

async function logout() {
  try {
    await auth.signOut();
    showAlert("Sesión cerrada correctamente", "info");
  } catch (error) {
    console.error("Error al cerrar sesión:", error);
    showAlert("Error al cerrar sesión", "danger");
  }
}

function updateUIForAuthenticatedUser(user) {
  // Ocultar enlaces de login/register
  const loginLink = document.getElementById("loginLink");
  const registerLink = document.getElementById("registerLink");
  const userDropdown = document.getElementById("userDropdown");
  const userName = document.getElementById("userName");
  const guestBanner = document.getElementById("guestBanner");

  if (loginLink) loginLink.classList.add("d-none");
  if (registerLink) registerLink.classList.add("d-none");
  if (userDropdown) userDropdown.classList.remove("d-none");
  if (userName) userName.textContent = user.displayName || user.email;
  if (guestBanner) guestBanner.style.display = "none";
}

function updateUIForGuestUser() {
  // Mostrar enlaces de login/register
  const loginLink = document.getElementById("loginLink");
  const registerLink = document.getElementById("registerLink");
  const userDropdown = document.getElementById("userDropdown");
  const guestBanner = document.getElementById("guestBanner");

  if (loginLink) loginLink.classList.remove("d-none");
  if (registerLink) registerLink.classList.remove("d-none");
  if (userDropdown) userDropdown.classList.add("d-none");
  if (guestBanner) guestBanner.style.display = "block";
}

// ================================
// GESTIÓN DE CULTIVOS
// ================================

async function handleNuevoCultivo(e) {
  e.preventDefault();

  const cultivo = {
    nombre: document.getElementById("cultivoNombre").value,
    variedad: document.getElementById("cultivoVariedad").value,
    fechaSiembra: new Date(
      document.getElementById("cultivoFechaSiembra").value
    ),
    precio: parseFloat(document.getElementById("cultivoPrecio").value),
    fechaCreacion: new Date(),
    activo: true,
    cosechas: [],
    gastos: [],
  };

  try {
    if (HuertoApp.currentUser && db) {
      // Usuario autenticado - guardar en Firebase
      cultivo.userId = HuertoApp.currentUser.uid;
      await db.collection("cultivos").add(cultivo);
    } else {
      // Usuario invitado - guardar en localStorage
      const localCultivos = JSON.parse(
        localStorage.getItem("huerto_cultivos") || "[]"
      );
      cultivo.id = "local_" + Date.now();
      localCultivos.push(cultivo);
      localStorage.setItem("huerto_cultivos", JSON.stringify(localCultivos));
    }

    HuertoApp.modals.nuevoCultivo.hide();
    document.getElementById("nuevoCultivoForm").reset();

    // Recargar datos
    await loadUserData();

    showAlert("¡Cultivo creado exitosamente!", "success");
  } catch (error) {
    console.error("Error al crear cultivo:", error);
    showAlert("Error al crear cultivo: " + error.message, "danger");
  }
}

async function loadUserData() {
  try {
    if (HuertoApp.currentUser && db) {
      // Cargar desde Firebase
      const q = db
        .collection("cultivos")
        .where("userId", "==", HuertoApp.currentUser.uid)
        .orderBy("fechaCreacion", "desc");

      const querySnapshot = await q.get();

      HuertoApp.cultivos = [];
      querySnapshot.forEach((doc) => {
        HuertoApp.cultivos.push({
          id: doc.id,
          ...doc.data(),
        });
      });
    } else {
      // Cargar desde localStorage
      HuertoApp.cultivos = JSON.parse(
        localStorage.getItem("huerto_cultivos") || "[]"
      );
    }

    updateDashboard();
    updateCultivosSection();
    updateAnalytics();
  } catch (error) {
    console.error("Error al cargar datos:", error);
    showAlert("Error al cargar datos", "danger");
  }
}

// Modo demo eliminado: no cargar datos simulados

// ================================
// ACTUALIZACIÓN DE INTERFAZ
// ================================

// Modo demo eliminado: implementar updateDashboard real
function updateDashboard() {
  const recentCropsContainer = document.getElementById("recentCrops");
  if (!recentCropsContainer) return;

  const hasCultivos =
    Array.isArray(HuertoApp.cultivos) && HuertoApp.cultivos.length > 0;
  if (!hasCultivos) {
    recentCropsContainer.innerHTML = `
      <div class="text-center text-muted py-5">
        <i class="bi bi-plus-circle-dotted fs-1"></i>
        <p class="mt-2">No hay cultivos registrados</p>
        <button class="btn btn-outline-success" onclick="showNuevoCultivo()">
          Añadir primer cultivo
        </button>
      </div>
    `;
    return;
  }

  const recentCrops = HuertoApp.cultivos.slice(0, 3);
  recentCropsContainer.innerHTML = recentCrops
    .map((cultivo) => {
      const totalCosecha =
        cultivo.cosechas?.reduce(
          (sum, cosecha) => sum + (cosecha.cantidad || 0),
          0
        ) || 0;
      const beneficio =
        totalCosecha * (cultivo.precio || 0) -
        (cultivo.gastos?.reduce(
          (sum, gasto) => sum + (gasto.cantidad || 0),
          0
        ) || 0);

      return `
        <div class="row align-items-center py-2 border-bottom">
          <div class="col-md-4">
            <h6 class="mb-1">${cultivo.nombre}</h6>
            <small class="text-muted">${
              cultivo.variedad || "Sin variedad"
            }</small>
          </div>
          <div class="col-md-3">
            <small class="text-muted">Cosecha</small>
            <div>${totalCosecha.toFixed(1)} kg</div>
          </div>
          <div class="col-md-3">
            <small class="text-muted">Beneficio</small>
            <div class="${
              beneficio >= 0 ? "text-success" : "text-danger"
            }">€${beneficio.toFixed(2)}</div>
          </div>
          <div class="col-md-2 text-end">
            <span class="badge bg-success">Activo</span>
          </div>
        </div>
      `;
    })
    .join("");
}

function updateCultivosSection() {
  const cultivosContainer = document.getElementById("cultivosList");
  if (!cultivosContainer) return;

  if (HuertoApp.cultivos.length === 0) {
    cultivosContainer.innerHTML = `
      <div class="text-center text-muted py-5">
        <i class="bi bi-tree fs-1"></i>
        <h4 class="mt-3">No tienes cultivos</h4>
        <p>Comienza añadiendo tu primer cultivo</p>
        <button class="btn btn-success" onclick="showNuevoCultivo()">
          <i class="bi bi-plus-circle me-1"></i>
          Crear primer cultivo
        </button>
      </div>
    `;
  } else {
    cultivosContainer.innerHTML = HuertoApp.cultivos
      .map((cultivo) => {
        const totalCosecha =
          cultivo.cosechas?.reduce(
            (sum, cosecha) => sum + cosecha.cantidad,
            0
          ) || 0;
        const totalGastos =
          cultivo.gastos?.reduce((sum, gasto) => sum + gasto.cantidad, 0) || 0;
        const beneficio = totalCosecha * cultivo.precio - totalGastos;
        const fechaSiembra = new Date(
          cultivo.fechaSiembra
        ).toLocaleDateString();

        return `
        <div class="card mb-3">
          <div class="card-body">
            <div class="row align-items-center">
              <div class="col-md-3">
                <h5 class="card-title mb-1">${cultivo.nombre}</h5>
                <p class="text-muted mb-0">${
                  cultivo.variedad || "Sin variedad"
                }</p>
                <small class="text-muted">Sembrado: ${fechaSiembra}</small>
              </div>
              <div class="col-md-2 text-center">
                <div class="text-muted small">Precio/kg</div>
                <div class="fw-bold">€${cultivo.precio.toFixed(2)}</div>
              </div>
              <div class="col-md-2 text-center">
                <div class="text-muted small">Cosechado</div>
                <div class="fw-bold">${totalCosecha.toFixed(1)} kg</div>
              </div>
              <div class="col-md-2 text-center">
                <div class="text-muted small">Gastos</div>
                <div class="fw-bold text-danger">€${totalGastos.toFixed(
                  2
                )}</div>
              </div>
              <div class="col-md-2 text-center">
                <div class="text-muted small">Beneficio</div>
                <div class="fw-bold ${
                  beneficio >= 0 ? "text-success" : "text-danger"
                }">€${beneficio.toFixed(2)}</div>
              </div>
              <div class="col-md-1 text-end">
                <span class="badge bg-success">Activo</span>
              </div>
            </div>
          </div>
        </div>
      `;
      })
      .join("");
  }
}

function updateAnalytics() {
  // Actualizar gráficas si están en la sección analytics
  if (HuertoApp.currentSection === "analytics") {
    createProductionChart();
    createBenefitsChart();
  }
}

// ================================
// GRÁFICAS CON CHART.JS
// ================================

function createProductionChart() {
  const ctx = document.getElementById("productionChart");
  if (!ctx) return;

  if (HuertoApp.charts.production) {
    HuertoApp.charts.production.destroy();
  }

  const data = HuertoApp.cultivos.map((cultivo) => ({
    label: cultivo.nombre,
    data:
      cultivo.cosechas?.reduce((sum, cosecha) => sum + cosecha.cantidad, 0) ||
      0,
  }));

  HuertoApp.charts.production = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: data.map((d) => d.label),
      datasets: [
        {
          data: data.map((d) => d.data),
          backgroundColor: [
            "#198754",
            "#20c997",
            "#6f42c1",
            "#fd7e14",
            "#dc3545",
          ],
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom",
        },
      },
    },
  });
}

function createBenefitsChart() {
  const ctx = document.getElementById("benefitsChart");
  if (!ctx) return;

  if (HuertoApp.charts.benefits) {
    HuertoApp.charts.benefits.destroy();
  }

  const data = HuertoApp.cultivos.map((cultivo) => {
    const totalCosecha =
      cultivo.cosechas?.reduce((sum, cosecha) => sum + cosecha.cantidad, 0) ||
      0;
    const totalGastos =
      cultivo.gastos?.reduce((sum, gasto) => sum + gasto.cantidad, 0) || 0;
    return {
      label: cultivo.nombre,
      beneficio: totalCosecha * cultivo.precio - totalGastos,
    };
  });

  HuertoApp.charts.benefits = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.map((d) => d.label),
      datasets: [
        {
          label: "Beneficio (€)",
          data: data.map((d) => d.beneficio),
          backgroundColor: data.map((d) =>
            d.beneficio >= 0 ? "#198754" : "#dc3545"
          ),
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

// ================================
// NAVEGACIÓN Y UTILIDADES
// ================================

function showSection(sectionName) {
  // Ocultar todas las secciones
  const sections = ["dashboardSection", "cultivosSection", "analyticsSection"];
  sections.forEach((section) => {
    const element = document.getElementById(section);
    if (element) element.classList.add("d-none");
  });

  // Mostrar la sección seleccionada
  const targetSection = document.getElementById(sectionName + "Section");
  if (targetSection) {
    targetSection.classList.remove("d-none");
  }

  // Actualizar navegación activa
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.remove("active");
  });

  HuertoApp.currentSection = sectionName;

  // Si es analytics, crear gráficas
  if (sectionName === "analytics") {
    setTimeout(() => {
      createProductionChart();
      createBenefitsChart();
    }, 100);
  }
}

function showLogin() {
  if (HuertoApp.modals.login) {
    HuertoApp.modals.login.show();
  }
}

function showRegister() {
  if (HuertoApp.modals.register) {
    HuertoApp.modals.register.show();
  }
}

function showNuevoCultivo() {
  if (HuertoApp.modals.nuevoCultivo) {
    HuertoApp.modals.nuevoCultivo.show();
  }
}

function showProfile() {
  showAlert("Función de perfil próximamente", "info");
}

function showAlert(message, type = "info") {
  const alertContainer = document.getElementById("alertContainer");
  if (!alertContainer) return;

  const alertId = "alert_" + Date.now();

  const alertHtml = `
    <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
  `;

  alertContainer.insertAdjacentHTML("beforeend", alertHtml);

  // Auto-remover después de 5 segundos
  setTimeout(() => {
    const alertElement = document.getElementById(alertId);
    if (alertElement) {
      alertElement.remove();
    }
  }, 5000);
}

// ================================
// FUNCIONES GLOBALES
// ================================

window.showSection = showSection;
window.showLogin = showLogin;
window.showRegister = showRegister;
window.showNuevoCultivo = showNuevoCultivo;
window.showProfile = showProfile;
window.logout = logout;

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
  // TEMPORAL: Limpiar localStorage problemático
  localStorage.removeItem("huerto_auth");
  localStorage.removeItem("huerto_user");

  // Modo demo eliminado
  return;

  // Código original comentado
  /*
  const authStatus = localStorage.getItem("huerto_auth");
  const currentPath = window.location.pathname;

  // Si no está autenticado y no está en login, redirigir
  if (!authStatus && currentPath !== "/auth/login" && currentPath !== "/") {
    // En desarrollo, permitir acceso directo para testing
    if (HuertoApp.config.isDevelopment) {
      console.log("🔧 Modo desarrollo: saltando autenticación");
      return;
    }

    console.log("🔐 Redirigiendo a login...");
    window.location.href = "/auth/login";
    return;
  }

  // Si está autenticado y está en login, redirigir a dashboard
  if (authStatus && currentPath === "/auth/login") {
    window.location.href = "/";
    return;
  }
  */
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

  // Modo demo eliminado: sin badge
}

// Modo demo eliminado: función showDemoBadge removida

// ================================
// GESTIÓN DE CONEXIÓN
// ================================

function handleOnline() {
  console.log("🟢 Conexión restaurada");
  HuertoApp.isOnline = true;

  // Mostrar notificación
  showNotification("Conexión restaurada", "success");

  // Sincronizar datos pendientes
  syncPendingData();
}

function handleOffline() {
  console.log("🔴 Conexión perdida");
  HuertoApp.isOnline = false;

  // Mostrar notificación
  showNotification(
    "Sin conexión - Los datos se guardarán localmente",
    "warning"
  );
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

// Escuchar evento personalizado desde base.html
window.addEventListener("appInstallable", (e) => {
  handleInstallPrompt(e.detail);
});

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
  const defaultHeaders = {
    "Content-Type": "application/json",
  };

  // Agregar token de Firebase si está disponible
  try {
    if (
      window.firebase &&
      window.firebase.auth &&
      window.firebase.auth().currentUser
    ) {
      const token = await window.firebase.auth().currentUser.getIdToken();
      defaultHeaders["Authorization"] = `Bearer ${token}`;
      console.log("🔑 Token de Firebase agregado a la petición");
    }
  } catch (error) {
    console.warn("⚠️ No se pudo obtener token de Firebase:", error);
  }

  const defaultOptions = {
    headers: defaultHeaders,
    ...options,
  };

  // Combinar headers si se pasan opciones adicionales
  if (options.headers) {
    defaultOptions.headers = { ...defaultHeaders, ...options.headers };
  }

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

// ================================
// FUNCIONES GLOBALES DE AUTENTICACIÓN
// ================================

/**
 * Función global para cerrar sesión
 * Utiliza AuthService si está disponible
 */
async function logout() {
  try {
    if (typeof AuthService !== "undefined") {
      // Usar AuthService si está disponible
      await AuthService.logout();
    } else {
      // Fallback directo
      const response = await fetch("/auth/logout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      if (response.ok) {
        // Limpiar datos locales
        localStorage.removeItem("huerto_user");
        localStorage.removeItem("firebase_token");

        // Redirigir al onboarding
        window.location.href = "/";
      } else {
        throw new Error("Error al cerrar sesión");
      }
    }
  } catch (error) {
    console.error("Error durante logout:", error);
    // En caso de error, forzar limpieza local y redirección
    localStorage.clear();
    window.location.href = "/";
  }
}

console.log("✅ JavaScript principal de HuertoRentable cargado");
