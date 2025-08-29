/**
 * Configur// CONFIGURACIÓN FIREBASE - DATOS REALES COMPLETOS ✅
const firebaseConfig = {
  apiKey: "AIzaSyANFRY9_m3KL_Riiiep9V0t5EbY0UBu-zo",
  authDomain: "huerto-rentable.firebaseapp.com",
  projectId: "huerto-rentable",
  storageBucket: "huerto-rentable.firebasestorage.app",
  messagingSenderId: "887320361443",
  appId: "1:887320361443:web:61da1fbb63380e7b2e88d6"
};irebase para HuertoRentable
 *
 * INSTRUCCIONES PARA CONFIGURAR FIREBASE REAL:
 *
 * 1. Ve a https://console.firebase.google.com/
 * 2. Crea un nuevo proyecto (ej: "huerto-rentable")
 * 3. Ve a Project Settings > General > Your apps
 * 4. Haz clic en "Web" (</>)
 * 5. Registra tu app y copia la configuración
 * 6. Reemplaza firebaseConfig abajo con tus datos reales
 * 7. Habilita Authentication > Sign-in method > Email/Password
 * 8. Crea Firestore Database en modo test
 * 9. Descarga serviceAccountKey.json para el backend
 */

// CONFIGURACIÓN FIREBASE - DATOS REALES DE TU PROYECTO
const firebaseConfig = {
  // ✅ Configuración real del proyecto "huerto-rentable"
  apiKey: "AIzaSyANFRY9_m3KL_Riiiep9V0t5EbY0UBu-zo",
  authDomain: "huerto-rentable.firebaseapp.com",
  projectId: "huerto-rentable",
  storageBucket: "huerto-rentable.appspot.com",
  messagingSenderId: "887320361443",
  appId: "1:887320361443:web:huerto-rentable-app",
};

// PARA DESARROLLO/DEMO: Configuración temporal
// Esta configuración es para testing local, no funcionará en producción
const DEV_CONFIG = {
  apiKey: "demo-api-key",
  authDomain: "demo-project.firebaseapp.com",
  projectId: "demo-project",
  storageBucket: "demo-project.appspot.com",
  messagingSenderId: "000000000000",
  appId: "demo-app-id",
};

// Función para inicializar Firebase
function initializeFirebase() {
  try {
    // En desarrollo, intentar con configuración real si está disponible
    if (firebaseConfig.apiKey !== "AIzaSyC...") {
      console.log("🔥 Inicializando Firebase con configuración real");
      firebase.initializeApp(firebaseConfig);
    } else {
      console.log("⚠️ Usando modo demo - Firebase no configurado");
      // En modo demo, no inicializar Firebase real
      return false;
    }
    return true;
  } catch (error) {
    console.error("❌ Error inicializando Firebase:", error);
    return false;
  }
}

// Función para verificar si Firebase está disponible
function isFirebaseAvailable() {
  return typeof firebase !== "undefined" && firebase.apps.length > 0;
}

// Exportar configuración para uso en otros archivos
window.HuertoFirebase = {
  config: firebaseConfig,
  initialize: initializeFirebase,
  isAvailable: isFirebaseAvailable,
};
