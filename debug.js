// Debug simple para verificar Firebase y AuthService
console.log("🔬 INICIANDO DEBUG FIREBASE Y AUTHSERVICE");

// Test 1: Firebase SDK disponible
console.log(
  "1. Firebase SDK:",
  typeof firebase !== "undefined" ? "✅ DISPONIBLE" : "❌ NO DISPONIBLE"
);

// Test 2: HuertoFirebase config
console.log(
  "2. HuertoFirebase:",
  typeof window.HuertoFirebase !== "undefined"
    ? "✅ DISPONIBLE"
    : "❌ NO DISPONIBLE"
);

// Test 3: AuthService disponible
console.log(
  "3. AuthService:",
  typeof window.authService !== "undefined"
    ? "✅ DISPONIBLE"
    : "❌ NO DISPONIBLE"
);

// Test 4: Estado de inicialización
if (window.authService) {
  console.log(
    "4. Firebase Ready:",
    window.authService.isFirebaseReady ? "✅ SÍ" : "❌ NO"
  );
}

// Test 5: Inicialización Firebase
if (window.HuertoFirebase) {
  const status = window.HuertoFirebase.getStatus();
  console.log("5. Estado Firebase:", status);
}

// Test 6: Simular registro rápido
setTimeout(async () => {
  console.log("🧪 INICIANDO TEST DE REGISTRO RÁPIDO...");

  if (window.authService && window.authService.isFirebaseReady) {
    try {
      const timestamp = Date.now();
      const testEmail = `debug${timestamp}@test.com`;
      const testPassword = "123456789";

      console.log(`📧 Probando registro con: ${testEmail}`);

      const result = await window.authService.register(
        testEmail,
        testPassword,
        "Usuario Debug",
        "gratuito"
      );

      if (result.success) {
        console.log("✅ REGISTRO EXITOSO:", result);
      } else {
        console.log("❌ REGISTRO FALLÓ:", result.error);
      }
    } catch (error) {
      console.log("❌ ERROR EN REGISTRO:", error.message);
    }
  } else {
    console.log("❌ AuthService no está listo para Firebase");
  }
}, 3000); // Esperar 3 segundos para que todo se inicialice

console.log("🔬 DEBUG SCRIPT CARGADO - Resultados aparecerán en 3 segundos");
