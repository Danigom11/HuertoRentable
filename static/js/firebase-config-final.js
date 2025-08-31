/**
 * Configuración Firebase para HuertoRentable
 * Version limpia y profesional
 */

// Configuración Firebase obtenida del console
const firebaseConfig = {
  apiKey: "AIzaSyANFRY9_m3KL_Riiiep9V0t5EbY0UBu-zo",
  authDomain: "huerto-rentable.firebaseapp.com",
  projectId: "huerto-rentable",
  storageBucket: "huerto-rentable.appspot.com",
  messagingSenderId: "814068450380",
  appId: "1:814068450380:web:df8f5d7e2c42e7e5b23456",
  measurementId: "G-XXXXXXXXXX",
};

// Objeto global para acceso desde toda la aplicación
window.HuertoFirebase = {
  config: firebaseConfig,
  app: null,
  auth: null,

  /**
   * Inicializa Firebase de forma segura
   */
  initialize: function () {
    try {
      console.log("HuertoFirebase: Iniciando configuración...");

      // Verificar que Firebase SDK esté disponible
      if (typeof firebase === "undefined") {
        console.error("HuertoFirebase: Firebase SDK no está cargado");
        return false;
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
