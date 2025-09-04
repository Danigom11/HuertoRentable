/**
 * Cloud Functions para HuertoRentable
 * Sistema seguro con Firebase Authentication para app Android
 */

const functions = require("firebase-functions");
const admin = require("firebase-admin");
const express = require("express");
const cors = require("cors");

// Inicializar Firebase Admin
admin.initializeApp();
const db = admin.firestore();

// Configurar CORS para permitir requests desde la app Android
const corsOptions = {
  origin: true, // Permitir todos los orígenes por ahora, restringir en producción
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"],
};

// ============================================
// MIDDLEWARE DE AUTENTICACIÓN
// ============================================

/**
 * Middleware para verificar token de Firebase
 * Equivalente a @require_auth en Flask
 */
async function verifyAuth(req, res, next) {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res.status(401).json({
        error: "Token de autorización requerido",
        code: "NO_TOKEN",
      });
    }

    const idToken = authHeader.split("Bearer ")[1];

    // Verificar token con Firebase Admin
    const decodedToken = await admin.auth().verifyIdToken(idToken);

    // Agregar información del usuario al request
    req.user = {
      uid: decodedToken.uid,
      email: decodedToken.email || null,
      emailVerified: decodedToken.email_verified || false,
    };

    console.log(`✅ Usuario autenticado: ${req.user.uid}`);
    next();
  } catch (error) {
    console.error("❌ Error de autenticación:", error);
    return res.status(401).json({
      error: "Token inválido o expirado",
      code: "INVALID_TOKEN",
    });
  }
}

// ============================================
// FUNCIONES DE UTILIDAD
// ============================================

/**
 * Respuesta estándar para errores
 */
function errorResponse(res, message, code = "ERROR", statusCode = 400) {
  return res.status(statusCode).json({
    error: message,
    code: code,
    timestamp: new Date().toISOString(),
  });
}

/**
 * Respuesta estándar para éxito
 */
function successResponse(res, data = null, message = "Operación exitosa") {
  return res.status(200).json({
    success: true,
    message: message,
    data: data,
    timestamp: new Date().toISOString(),
  });
}

// ============================================
// IMPORTAR MÓDULOS DE FUNCIONES
// ============================================

const cropsModule = require("./crops");
const analyticsModule = require("./analytics");
const authModule = require("./auth");

// Importar la aplicación Flask SIMPLE
const { flaskApp } = require("./flask-simple");

// ============================================
// CONFIGURAR EXPRESS APPS
// ============================================

// App principal para gestión de cultivos
const cropsApp = express();
cropsApp.use(cors(corsOptions));
cropsApp.use(express.json());
cropsApp.use(verifyAuth); // Aplicar autenticación a todas las rutas
cropsModule.setupRoutes(cropsApp, db);

// App para analytics
const analyticsApp = express();
analyticsApp.use(cors(corsOptions));
analyticsApp.use(express.json());
analyticsApp.use(verifyAuth);
analyticsModule.setupRoutes(analyticsApp, db);

// App para autenticación adicional
const authApp = express();
authApp.use(cors(corsOptions));
authApp.use(express.json());
authModule.setupRoutes(authApp, db, admin);

// ============================================
// EXPORTAR CLOUD FUNCTIONS
// ============================================

// Función principal de la aplicación Flask - NUEVA
exports.flaskApp = flaskApp;

// Función principal para gestión de cultivos
exports.crops = functions.https.onRequest(cropsApp);

// Función para analytics y reportes
exports.analytics = functions.https.onRequest(analyticsApp);

// Función para autenticación y gestión de usuarios
exports.auth = functions.https.onRequest(authApp);

// Función de salud del sistema
exports.health = functions.https.onRequest((req, res) => {
  res.set("Access-Control-Allow-Origin", "*");
  res.set("Access-Control-Allow-Methods", "GET");

  return res.status(200).json({
    status: "healthy",
    service: "HuertoRentable Cloud Functions",
    version: "1.0.0",
    timestamp: new Date().toISOString(),
    firebase: "connected",
  });
});

// Función para información del usuario autenticado
exports.user = functions.https.onRequest(async (req, res) => {
  res.set("Access-Control-Allow-Origin", "*");
  res.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.set("Access-Control-Allow-Headers", "Content-Type, Authorization");

  if (req.method === "OPTIONS") {
    return res.status(200).send();
  }

  try {
    await verifyAuth(req, res, async () => {
      // Si llegamos aquí, el usuario está autenticado
      const userInfo = {
        uid: req.user.uid,
        email: req.user.email,
        emailVerified: req.user.emailVerified,
        lastLogin: new Date().toISOString(),
      };

      return successResponse(res, userInfo, "Información de usuario obtenida");
    });
  } catch (error) {
    console.error("Error en función user:", error);
    return errorResponse(
      res,
      "Error interno del servidor",
      "INTERNAL_ERROR",
      500
    );
  }
});
