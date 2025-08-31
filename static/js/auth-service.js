/**
 * Servicio de Autenticación Frontend para HuertoRentable
 * Maneja Firebase Authentication y fallback a modo local
 */

class AuthService {
  constructor() {
    this.isFirebaseReady = false;
    this.currentUser = null;
  }

  /**
   * Inicializar el servicio de autenticación
   */
  async initialize() {
    try {
      console.log("🚀 Inicializando AuthService...");

      // Verificar que HuertoFirebase esté disponible
      if (!window.HuertoFirebase) {
        console.error("❌ HuertoFirebase no está disponible");
        this.isFirebaseReady = false;
        return;
      }

      console.log("📊 Estado de Firebase:", window.HuertoFirebase.getStatus());

      // Intentar inicializar Firebase
      const initialized = window.HuertoFirebase.initialize();

      if (initialized) {
        this.isFirebaseReady = true;
        console.log("✅ Firebase Authentication listo");

        // Escuchar cambios de estado de autenticación
        firebase.auth().onAuthStateChanged((user) => {
          this.currentUser = user;
          console.log(
            "👤 Estado de autenticación cambió:",
            user ? `Usuario: ${user.email}` : "No autenticado"
          );
          this.onAuthStateChanged(user);
        });
      } else {
        console.log(
          "⚠️ Firebase no se pudo inicializar, usando autenticación local"
        );
        this.isFirebaseReady = false;
      }
    } catch (error) {
      console.error("❌ Error inicializando autenticación:", error);
      this.isFirebaseReady = false;
    }
  }

  /**
   * Registrar nuevo usuario
   */
  async register(email, password, displayName = "", plan = "gratuito") {
    try {
      console.log(`🔥 Iniciando registro: ${email}, plan: ${plan}`);
      console.log(`📊 Firebase disponible: ${this.isFirebaseReady}`);

      if (this.isFirebaseReady) {
        // Registro con Firebase
        console.log("🔥 Registrando usuario con Firebase");

        // Verificar que Firebase Auth esté disponible
        if (typeof firebase === "undefined" || !firebase.auth) {
          throw new Error("Firebase Auth no está disponible");
        }

        console.log("📧 Creando usuario con email y contraseña...");
        const userCredential = await firebase
          .auth()
          .createUserWithEmailAndPassword(email, password);
        const user = userCredential.user;
        console.log(`✅ Usuario creado en Firebase: ${user.uid}`);

        // Actualizar perfil con nombre si se proporcionó
        if (displayName.trim()) {
          console.log(`📝 Actualizando perfil con nombre: ${displayName}`);
          await user.updateProfile({ displayName: displayName.trim() });
          await user.reload(); // Recargar para obtener los datos actualizados
          console.log("✅ Perfil actualizado");
        }

        // Enviar token al backend para crear usuario en Firestore con plan
        console.log("🎫 Obteniendo token ID...");
        const idToken = await user.getIdToken();
        console.log(`✅ Token obtenido: ${idToken.substring(0, 20)}...`);

        console.log("📤 Enviando datos al backend...");
        // Añadir timeout explícito al fetch para evitar cuelgues
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s
        const response = await fetch("/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            idToken: idToken,
            plan: plan,
          }),
          credentials: "include",
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        console.log(`📥 Respuesta del backend: ${response.status}`);

        if (!response.ok) {
          const errorData = await response.text();
          console.error("❌ Error en respuesta del backend:", errorData);
          throw new Error(
            `Error del servidor: ${response.status} - ${errorData}`
          );
        }

        const result = await response.json();
        console.log("✅ Registro exitoso en backend:", result);

        // Cookies de respaldo para navegadores con problemas de sesión
        try {
          const uid = user.uid;
          const userCookie = {
            uid,
            email: user.email,
            name: user.displayName || displayName || email.split("@")[0],
            plan,
            authenticated: true,
          };
          this._setCookie("huerto_user_uid", uid, 86400);
          this._setCookie(
            "huerto_user_data",
            JSON.stringify(userCookie),
            86400
          );
          // Guardar también el idToken por 1h
          this._setCookie("firebase_id_token", idToken, 3600);
          console.log("🍪 Cookies de respaldo establecidas tras registro");
        } catch (e) {
          console.warn("No se pudieron establecer cookies de respaldo:", e);
        }

        return {
          success: true,
          user: {
            uid: user.uid,
            email: user.email,
            name: user.displayName || displayName || email.split("@")[0],
            emailVerified: user.emailVerified,
            plan: plan,
          },
          message: result.message,
        };
      } else {
        // Registro local (fallback)
        console.log("🏠 Registrando usuario localmente");

        const response = await fetch("/auth/register-local", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: email,
            name: displayName || email.split("@")[0],
          }),
          credentials: "include",
        });

        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.error || "Error en registro local");
        }

        return {
          success: true,
          user: result.user,
          isLocal: true,
        };
      }
    } catch (error) {
      console.error("❌ Error completo en registro:", error);
      console.error("❌ Stack trace:", error.stack);

      // Manejar errores específicos de Firebase
      let errorMessage = "Ha ocurrido un error inesperado";

      if (error.code) {
        console.error(`❌ Código de error Firebase: ${error.code}`);
        switch (error.code) {
          case "auth/email-already-in-use":
            errorMessage = "Este email ya está registrado";
            break;
          case "auth/weak-password":
            errorMessage = "La contraseña debe tener al menos 6 caracteres";
            break;
          case "auth/invalid-email":
            errorMessage = "El formato del email no es válido";
            break;
          case "auth/operation-not-allowed":
            errorMessage =
              "El registro con email/contraseña no está habilitado en Firebase";
            break;
          case "auth/network-request-failed":
            errorMessage =
              "Error de conexión. Verifica tu internet y vuelve a intentar";
            break;
          default:
            errorMessage = `Error Firebase (${error.code}): ${error.message}`;
        }
      } else if (error.message) {
        // Errores más específicos basados en el mensaje
        if (error.message.includes("Firebase Auth no está disponible")) {
          errorMessage = "Error de configuración: Firebase no está disponible";
        } else if (error.message.includes("Error del servidor")) {
          errorMessage = error.message;
        } else {
          errorMessage = error.message;
        }
      }

      console.error(`❌ Mensaje final de error: ${errorMessage}`);

      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Iniciar sesión
   */
  async login(email, password) {
    try {
      if (this.isFirebaseReady) {
        // Login con Firebase
        console.log("🔥 Iniciando sesión con Firebase");

        const userCredential = await firebase
          .auth()
          .signInWithEmailAndPassword(email, password);
        const user = userCredential.user;

        // Enviar token al backend
        const idToken = await user.getIdToken();
        const response = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ idToken: idToken }),
          credentials: "include",
        });

        if (!response.ok) {
          throw new Error("Error en autenticación del servidor");
        }

        // Cookies de respaldo
        try {
          const uid = user.uid;
          const userCookie = {
            uid,
            email: user.email,
            name: user.displayName || email.split("@")[0],
            plan: "gratuito",
            authenticated: true,
          };
          this._setCookie("huerto_user_uid", uid, 86400);
          this._setCookie(
            "huerto_user_data",
            JSON.stringify(userCookie),
            86400
          );
          this._setCookie("firebase_id_token", idToken, 3600);
          console.log("🍪 Cookies de respaldo establecidas tras login");
        } catch (e) {
          console.warn("No se pudieron establecer cookies de respaldo:", e);
        }

        return {
          success: true,
          user: {
            uid: user.uid,
            email: user.email,
            name: user.displayName || email.split("@")[0],
            emailVerified: user.emailVerified,
          },
        };
      } else {
        // Login local (fallback)
        console.log("🏠 Iniciando sesión localmente");

        const response = await fetch("/auth/register-local", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: email,
            name: email.split("@")[0],
          }),
        });

        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.error || "Error en login local");
        }

        return {
          success: true,
          user: result.user,
          isLocal: true,
        };
      }
    } catch (error) {
      console.error("❌ Error en login:", error);

      // Manejar errores específicos de Firebase
      let errorMessage = "Error al iniciar sesión";

      if (error.code) {
        switch (error.code) {
          case "auth/user-not-found":
            errorMessage = "Usuario no encontrado";
            break;
          case "auth/wrong-password":
            errorMessage = "Contraseña incorrecta";
            break;
          case "auth/invalid-email":
            errorMessage = "Email inválido";
            break;
          case "auth/user-disabled":
            errorMessage = "Cuenta deshabilitada";
            break;
          case "auth/too-many-requests":
            errorMessage = "Demasiados intentos. Intenta más tarde";
            break;
          default:
            errorMessage = error.message;
        }
      } else {
        errorMessage = error.message;
      }

      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Cerrar sesión
   */
  async logout() {
    try {
      if (this.isFirebaseReady && firebase.auth().currentUser) {
        await firebase.auth().signOut();
      }

      // Limpiar sesión local
      const response = await fetch("/auth/logout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });

      this.currentUser = null;

      return { success: true };
    } catch (error) {
      console.error("❌ Error cerrando sesión:", error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Obtener usuario actual
   */
  getCurrentUser() {
    if (this.isFirebaseReady) {
      return firebase.auth().currentUser;
    }
    return this.currentUser;
  }

  /**
   * Callback para cambios de estado de autenticación
   */
  onAuthStateChanged(user) {
    console.log(
      "🔄 Estado de autenticación cambió:",
      user ? "autenticado" : "no autenticado"
    );

    // Emitir evento personalizado para que otros componentes puedan reaccionar
    const event = new CustomEvent("authStateChanged", {
      detail: { user: user },
    });
    window.dispatchEvent(event);
  }

  /**
   * Verificar si el usuario está autenticado
   */
  isAuthenticated() {
    return !!this.getCurrentUser();
  }

  _setCookie(name, value, maxAgeSeconds) {
    try {
      document.cookie = `${name}=${encodeURIComponent(
        value
      )}; path=/; max-age=${maxAgeSeconds}; SameSite=Lax`;
    } catch (e) {
      console.warn("No se pudo escribir cookie", name, e);
    }
  }
}

// Crear instancia global del servicio
window.authService = new AuthService();

// Inicializar cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", function () {
  window.authService.initialize();
});

console.log("🔐 Servicio de autenticación cargado");
