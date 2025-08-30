/**
 * Configuración Firebase para HuertoRentable
 */

// CONFIGURACIÓN FIREBASE - DATOS REALES COMPLETOS ✅
const firebaseConfig = {
  apiKey: "AIzaSyANFRY9_m3KL_Riiiep9V0t5EbY0UBu-zo",
  authDomain: "huerto-rentable.firebaseapp.com",
  projectId: "huerto-rentable",
  storageBucket: "huerto-rentable.firebasestorage.app",
  messagingSenderId: "887320361443",
  appId: "1:887320361443:web:61da1fbb63380e7b2e88d6",
};

// Función para inicializar Firebase
function initializeFirebase() {
  try {
    console.log("🔥 Inicializando Firebase...");
    console.log("📝 Configuración:", {
      apiKey: firebaseConfig.apiKey ? "✅ Presente" : "❌ Falta",
      authDomain: firebaseConfig.authDomain,
      projectId: firebaseConfig.projectId,
    });

    // Verificar que Firebase SDK esté disponible
    if (typeof firebase === "undefined") {
      throw new Error("Firebase SDK no está cargado");
    }

    console.log(
      "📦 Firebase SDK disponible, versión:",
      firebase.SDK_VERSION || "desconocida"
    );

    // Verificar si ya está inicializado
    if (firebase.apps.length > 0) {
      console.log("✅ Firebase ya estaba inicializado");
      return true;
    }

    // Inicializar Firebase
    const app = firebase.initializeApp(firebaseConfig);
    console.log("✅ Firebase inicializado correctamente");
    console.log("🔗 App name:", app.name);

    // Verificar servicios disponibles
    try {
      const auth = firebase.auth();
      console.log("✅ Firebase Auth disponible");
    } catch (authError) {
      console.error("❌ Firebase Auth no disponible:", authError);
    }

    try {
      const firestore = firebase.firestore();
      console.log("✅ Firebase Firestore disponible");
    } catch (firestoreError) {
      console.error("❌ Firebase Firestore no disponible:", firestoreError);
    }

    return true;
  } catch (error) {
    console.error("❌ Error inicializando Firebase:", error);
    console.error("❌ Detalles del error:", error.message);
    return false;
  }
}

// Función para verificar si Firebase está disponible
function isFirebaseAvailable() {
  return typeof firebase !== "undefined" && firebase.apps.length > 0;
}

// Función para obtener estadísticas de Firebase
function getFirebaseStatus() {
  return {
    sdkLoaded: typeof firebase !== "undefined",
    appsInitialized: typeof firebase !== "undefined" ? firebase.apps.length : 0,
    authAvailable: false,
    firestoreAvailable: false,
  };
}

// Exportar configuración para uso en otros archivos
window.HuertoFirebase = {
  config: firebaseConfig,
  initialize: initializeFirebase,
  isAvailable: isFirebaseAvailable,
  getStatus: getFirebaseStatus,
};
