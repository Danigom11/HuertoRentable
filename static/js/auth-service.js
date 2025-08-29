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
      // Intentar inicializar Firebase
      if (window.HuertoFirebase && window.HuertoFirebase.initialize()) {
        this.isFirebaseReady = true;
        console.log("✅ Firebase Authentication listo");

        // Escuchar cambios de estado de autenticación
        firebase.auth().onAuthStateChanged((user) => {
          this.currentUser = user;
          this.onAuthStateChanged(user);
        });
      } else {
        console.log("⚠️ Firebase no disponible, usando autenticación local");
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
      if (this.isFirebaseReady) {
        // Registro con Firebase
        console.log("🔥 Registrando usuario con Firebase");

        const userCredential = await firebase
          .auth()
          .createUserWithEmailAndPassword(email, password);
        const user = userCredential.user;

        // Actualizar perfil con nombre si se proporcionó
        if (displayName.trim()) {
          await user.updateProfile({ displayName: displayName.trim() });
          await user.reload(); // Recargar para obtener los datos actualizados
        }

        // Enviar token al backend para crear usuario en Firestore con plan
        const idToken = await user.getIdToken();
        const response = await fetch("/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            idToken: idToken,
            plan: plan,
          }),
        });

        if (!response.ok) {
          throw new Error("Error creando perfil de usuario");
        }

        const result = await response.json();

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
      console.error("❌ Error en registro:", error);

      // Manejar errores específicos de Firebase
      let errorMessage = "Error al crear la cuenta";

      if (error.code) {
        switch (error.code) {
          case "auth/email-already-in-use":
            errorMessage = "Este email ya está registrado";
            break;
          case "auth/weak-password":
            errorMessage = "La contraseña es demasiado débil";
            break;
          case "auth/invalid-email":
            errorMessage = "Email inválido";
            break;
          case "auth/operation-not-allowed":
            errorMessage = "Registro no habilitado. Contacta al administrador";
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
        });

        if (!response.ok) {
          throw new Error("Error en autenticación del servidor");
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
}

// Crear instancia global del servicio
window.authService = new AuthService();

// Inicializar cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", function () {
  window.authService.initialize();
});

console.log("🔐 Servicio de autenticación cargado");
