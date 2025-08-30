/**
 * Servicio de Registro Simplificado para HuertoRentable
 * Versión específica para solucionar el problema de "ha ocurrido un error inesperado"
 */

class SimpleRegistrationService {
  constructor() {
    this.isReady = false;
    this.firebase = null;
    this.auth = null;
  }

  // Inicialización paso a paso con logging detallado
  async initialize() {
    console.log("🔧 SimpleRegistrationService: Iniciando...");

    try {
      // Step 1: Verificar Firebase SDK
      if (typeof firebase === "undefined") {
        throw new Error("Firebase SDK no está cargado");
      }
      console.log("✅ Firebase SDK disponible");

      // Step 2: Verificar configuración
      if (!window.HuertoFirebase) {
        throw new Error("Configuración Firebase no disponible");
      }
      console.log("✅ Configuración Firebase disponible");

      // Step 3: Inicializar Firebase usando HuertoFirebase
      const initialized = window.HuertoFirebase.initialize();
      if (!initialized) {
        throw new Error("No se pudo inicializar Firebase");
      }
      console.log("✅ Firebase inicializado");

      // Step 4: Obtener Auth service
      this.auth = firebase.auth();
      console.log("✅ Firebase Auth obtenido");

      // Step 5: Verificar conectividad
      this.auth.useDeviceLanguage();
      console.log("✅ Firebase Auth configurado");

      this.isReady = true;
      console.log("🎉 SimpleRegistrationService listo");
      return true;
    } catch (error) {
      console.error("❌ Error inicializando SimpleRegistrationService:", error);
      this.isReady = false;
      return false;
    }
  }

  // Registro paso a paso con manejo específico de errores
  async register(email, password, displayName = "", plan = "gratuito") {
    console.log(`🚀 Registro iniciado: ${email}, plan: ${plan}`);

    try {
      // Verificar que el servicio esté listo
      if (!this.isReady) {
        console.log("⚠️ Servicio no listo, intentando inicializar...");
        const initialized = await this.initialize();
        if (!initialized) {
          throw new Error("No se pudo inicializar el servicio de Firebase");
        }
      }

      // Step 1: Crear usuario en Firebase
      console.log("📧 Creando usuario en Firebase Auth...");
      const userCredential = await this.auth.createUserWithEmailAndPassword(
        email,
        password
      );
      const user = userCredential.user;
      console.log(`✅ Usuario creado en Firebase: ${user.uid}`);

      // Step 2: Actualizar perfil si se proporcionó nombre
      if (displayName && displayName.trim()) {
        console.log(`📝 Actualizando perfil: ${displayName}`);
        await user.updateProfile({ displayName: displayName.trim() });
        await user.reload();
        console.log("✅ Perfil actualizado");
      }

      // Step 3: Obtener token ID
      console.log("🎫 Obteniendo token ID...");
      const idToken = await user.getIdToken();
      console.log(`✅ Token obtenido (longitud: ${idToken.length})`);

      // Step 4: Enviar al backend
      console.log("📤 Enviando datos al backend...");
      // Añadir timeout explícito al fetch para evitar cuelgues
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s
      const response = await fetch("/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          idToken: idToken,
          plan: plan,
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      console.log(`📥 Respuesta del backend: ${response.status}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("❌ Error del backend:", errorText);
        throw new Error(
          `Error del servidor (${response.status}): ${errorText}`
        );
      }

      const result = await response.json();
      console.log("✅ Respuesta del backend exitosa:", result);

      // Step 5: Retornar resultado exitoso
      const finalResult = {
        success: true,
        user: {
          uid: user.uid,
          email: user.email,
          name: user.displayName || displayName || email.split("@")[0],
          emailVerified: user.emailVerified,
          plan: plan,
        },
        message: result.message || "Usuario registrado exitosamente",
      };

      console.log("🎉 Registro completado exitosamente:", finalResult);
      return finalResult;
    } catch (error) {
      console.error("❌ Error completo en registro:", error);

      // Manejo específico de errores de Firebase
      let errorMessage = "Ha ocurrido un error inesperado durante el registro";

      if (error.code) {
        console.error(`🔥 Error Firebase: ${error.code}`);
        switch (error.code) {
          case "auth/email-already-in-use":
            errorMessage =
              "Este email ya está registrado. Intenta iniciar sesión.";
            break;
          case "auth/weak-password":
            errorMessage = "La contraseña debe tener al menos 6 caracteres.";
            break;
          case "auth/invalid-email":
            errorMessage = "El formato del email no es válido.";
            break;
          case "auth/operation-not-allowed":
            errorMessage =
              "El registro no está habilitado. Contacta al administrador.";
            break;
          case "auth/network-request-failed":
            errorMessage =
              "Error de conexión. Verifica tu internet y vuelve a intentar.";
            break;
          default:
            errorMessage = `Error de autenticación: ${error.message}`;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      console.error(`❌ Mensaje de error final: ${errorMessage}`);

      return {
        success: false,
        error: errorMessage,
      };
    }
  }
}

// Crear instancia global
window.simpleRegistrationService = new SimpleRegistrationService();

// Función helper para usar desde formularios
window.registerUser = async function (email, password, displayName, plan) {
  return await window.simpleRegistrationService.register(
    email,
    password,
    displayName,
    plan
  );
};

console.log("🔧 SimpleRegistrationService cargado y disponible");
