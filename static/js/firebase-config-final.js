/**
 * Configuración Firebase para HuertoRentable
 * Version limpia y profesional
 */

// Fallback estático mínimo (se reemplaza por /config/firebase en producción)
const firebaseConfigFallback = {
  apiKey: "AIzaSyANFRY9_m3KL_Riiiep9V0t5EbY0UBu-zo",
  authDomain: "huerto-rentable.firebaseapp.com",
  projectId: "huerto-rentable",
  storageBucket: "huerto-rentable.firebasestorage.app",
  messagingSenderId: "887320361443",
  appId: "1:887320361443:web:61da1fbb63380e7b2e88d6",
};

// Objeto global para acceso desde toda la aplicación
window.HuertoFirebase = {
  config: null,
  app: null,
  auth: null,

  /**
   * Inicializa Firebase de forma segura
   */
  initialize: async function () {
    try {
      console.log("HuertoFirebase: Iniciando configuración...");

      // Verificar que Firebase SDK esté disponible
      if (typeof firebase === "undefined") {
        console.error("HuertoFirebase: Firebase SDK no está cargado");
        return false;
      }

      // Cargar configuración dinámica del backend si no está aún
      if (!this.config) {
        try {
          const res = await fetch("/config/firebase", { cache: "no-store" });
          if (res.ok) {
            const cfg = await res.json();
            // Validar apiKey básica
            if (cfg && cfg.apiKey && cfg.apiKey.startsWith("AIza")) {
              this.config = cfg;
              console.log("HuertoFirebase: Config cargada desde backend");
            } else {
              console.warn(
                "HuertoFirebase: Config inválida desde backend, usando fallback"
              );
              this.config = firebaseConfigFallback;
            }
          } else {
            console.warn(
              "HuertoFirebase: No se pudo obtener /config/firebase, usando fallback"
            );
            this.config = firebaseConfigFallback;
          }
        } catch (e) {
          console.warn(
            "HuertoFirebase: Error cargando /config/firebase, usando fallback",
            e
          );
          this.config = firebaseConfigFallback;
        }
      }

      // Inicializar app si no existe
      if (!this.app) {
        this.app = firebase.initializeApp(this.config);
        console.log("HuertoFirebase: App inicializada exitosamente");
      }

      // Inicializar Auth si no existe
      if (!this.auth) {
        this.auth = firebase.auth();
        console.log("HuertoFirebase: Auth inicializado exitosamente");
      }

      console.log("HuertoFirebase: Configuración completada");
      return true;
    } catch (error) {
      console.error("HuertoFirebase: Error en inicialización:", error);
      return false;
    }
  },

  /**
   * Verifica el estado de la configuración
   */
  getStatus: function () {
    return {
      sdkLoaded: typeof firebase !== "undefined",
      appInitialized: !!this.app,
      authInitialized: !!this.auth,
      config: !!this.config,
    };
  },
};

// Auto-inicialización cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", function () {
  console.log("HuertoFirebase: DOM listo, iniciando Firebase...");
  window.HuertoFirebase.initialize();
});

console.log("HuertoFirebase: Configuración cargada");
