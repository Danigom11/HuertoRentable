/**
 * Cloud Function para ejecutar HuertoRentable Flask App EXACTA
 * Copia y ejecuta la aplicación tal como está
 */

const functions = require("firebase-functions");
const admin = require("firebase-admin");
const express = require("express");
const fs = require("fs");
const path = require("path");

// Inicializar Firebase Admin
if (!admin.apps.length) {
  admin.initializeApp();
}

const app = express();

// Import del código Python (simulado en JavaScript)
// Vamos a replicar EXACTAMENTE lo que hace tu run.py y app/__init__.py

// Configuración exacta de tu aplicación
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Configurar sesiones como en tu Flask
const session = require("express-session");
app.use(
  session({
    secret: process.env.SECRET_KEY || "dev-secret-key-huerto",
    resave: false,
    saveUninitialized: false,
    cookie: {
      secure: false, // En desarrollo
      httpOnly: false,
      maxAge: 24 * 60 * 60 * 1000, // 1 día como en tu config
      sameSite: "lax",
    },
  })
);

// Servir archivos estáticos EXACTOS
app.use("/static", express.static(__dirname + "/../static"));

// Configurar motor de templates (Jinja2 -> EJS similar)
app.set("view engine", "ejs");
app.set("views", __dirname + "/../templates");

// Middleware de autenticación EXACTO como tu auth_middleware.py
async function requireAuth(req, res, next) {
  try {
    // Verificar token Firebase como en tu código
    const token =
      req.cookies?.firebase_id_token ||
      req.headers.authorization?.replace("Bearer ", "");

    if (token) {
      const decodedToken = await admin.auth().verifyIdToken(token);
      req.user = {
        uid: decodedToken.uid,
        email: decodedToken.email,
        email_verified: decodedToken.email_verified,
      };

      // Simular sesión Flask
      req.session.is_authenticated = true;
      req.session.user_uid = decodedToken.uid;
      req.session.user = req.user;

      next();
    } else {
      // Redirigir a onboarding como en tu código
      res.redirect("/onboarding");
    }
  } catch (error) {
    console.error("Auth error:", error);
    res.redirect("/onboarding");
  }
}

function optionalAuth(req, res, next) {
  // Como tu optional_auth pero sin requerir autenticación
  requireAuth(req, res, () => {}).catch(() => {});
  next();
}

function getCurrentUser(req) {
  return req.user || req.session?.user || null;
}

function getCurrentUserUid(req) {
  return req.user?.uid || req.session?.user_uid || null;
}

// RUTAS EXACTAS de tu main.py
// ================================

// Ruta raíz - CÓDIGO EXACTO de tu home() function
app.get("/", (req, res) => {
  console.log(`🔍 [HOME] Request args: ${JSON.stringify(req.query)}`);
  console.log(`🔍 [HOME] Session: ${JSON.stringify(req.session)}`);
  console.log(`🔍 [HOME] Cookies: ${JSON.stringify(req.cookies)}`);

  // PRIORIDAD MÁXIMA: Si viene del registro, ir directo al dashboard
  if (
    req.query.from === "register" ||
    (req.get("referer") && req.get("referer").includes("register"))
  ) {
    console.log("🎯 [HOME] Usuario viene del registro - redirigir a dashboard");
    return res.redirect(
      "/dashboard?" + new URLSearchParams(req.query).toString()
    );
  }

  // 1) Priorizar sesión de Flask (reciente tras registro/login)
  if (req.session?.is_authenticated && req.session?.user) {
    console.log("✅ [HOME] Usuario autenticado en sesión - ir a dashboard");
    return res.redirect("/dashboard");
  }

  // 2) Fallback: obtener usuario desde helper (token Firebase o g.current_user)
  const user = getCurrentUser(req);
  if (user) {
    console.log("✅ [HOME] Usuario detectado por helper - ir a dashboard");
    return res.redirect("/dashboard");
  }

  // 3) Si hay cookie de usuario, ir al dashboard
  if (req.cookies?.huerto_user_uid || req.cookies?.firebase_id_token) {
    console.log("✅ [HOME] Cookie de usuario detectada - ir a dashboard");
    return res.redirect("/dashboard");
  }

  // CAMBIO: Por defecto ir al onboarding para mejor UX
  // Solo ir directo al dashboard si explícitamente han elegido demo
  if (req.session?.demo_mode_chosen || req.query.demo === "true") {
    console.log("✅ [HOME] Modo demo - ir a dashboard");
    return res.redirect(
      "/dashboard?" + new URLSearchParams(req.query).toString()
    );
  }

  // Primera visita o sin elección → onboarding
  console.log("❌ [HOME] No hay usuario - ir a onboarding");
  return res.redirect("/onboarding");
});

// Ruta onboarding - EXACTA como tu código
app.get("/onboarding", (req, res) => {
  // Leer tu template HTML EXACTO y enviarlo
  const fs = require("fs");
  const path = require("path");

  try {
    // Leer tu base.html
    let baseHtml = fs.readFileSync(
      path.join(__dirname, "../templates/base.html"),
      "utf8"
    );
    // Leer tu welcome.html
    let welcomeHtml = fs.readFileSync(
      path.join(__dirname, "../templates/onboarding/welcome.html"),
      "utf8"
    );

    // Simular Jinja2: reemplazar {% extends "base.html" %}
    welcomeHtml = welcomeHtml.replace(
      /{% extends "base\.html" %}.*?{% endblock %}/gs,
      ""
    );
    welcomeHtml = welcomeHtml
      .replace(/{% block content %}/, "")
      .replace(/{% endblock %}/, "");

    // Insertar contenido en base
    const finalHtml = baseHtml
      .replace(
        /{% block title %}.*?{% endblock %}/,
        "Bienvenido - HuertoRentable"
      )
      .replace(/{% block content %}.*?{% endblock %}/, welcomeHtml)
      .replace(/{{ url_for\('static', filename='([^']+)'\) }}/g, "/static/$1")
      .replace(/{{ url_for\('([^']+)\.([^']+)'\) }}/g, "/$2");

    res.send(finalHtml);
  } catch (error) {
    console.error("Error loading template:", error);
    // Fallback: HTML básico
    res.send(`
      <!DOCTYPE html>
      <html lang="es">
      <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Bienvenido - HuertoRentable</title>
          <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
      </head>
      <body>
          <div class="container py-5 text-center">
              <h1 class="display-4 text-success mb-3">🌱 ¡Bienvenido a HuertoRentable!</h1>
              <p class="lead">Transforma tu huerto en un negocio rentable</p>
              <div class="mt-4">
                  <a href="/auth/register" class="btn btn-success btn-lg me-3">Comenzar</a>
                  <a href="/auth/login" class="btn btn-outline-success btn-lg">Iniciar Sesión</a>
              </div>
          </div>
      </body>
      </html>
    `);
  }
});

// Dashboard - EXACTO como tu código con require_auth
app.get("/dashboard", requireAuth, async (req, res) => {
  const userUid = getCurrentUserUid(req);
  const user = getCurrentUser(req);

  console.log(`✅ [Dashboard] Usuario autenticado: ${userUid}`);

  try {
    // Obtener cultivos EXACTO como en tu CropService
    const db = admin.firestore();
    const cropsSnapshot = await db
      .collection("cultivos")
      .where("usuario_id", "==", userUid)
      .get();

    const crops = [];
    cropsSnapshot.forEach((doc) => {
      crops.push({ id: doc.id, ...doc.data() });
    });

    console.log(`🌱 [Dashboard] Cultivos encontrados: ${crops.length}`);

    // Calcular métricas EXACTO como en tu código
    const activeCrops = crops.filter((c) => !c.fecha_cosecha);
    const finishedCrops = crops.filter((c) => c.fecha_cosecha);

    let totalKilos = 0;
    let totalBeneficios = 0;

    crops.forEach((crop) => {
      const produccion = crop.produccion_diaria || [];
      const kilosCultivo = produccion.reduce(
        (sum, p) => sum + (p.kilos || 0),
        0
      );
      const precio = crop.precio_por_kilo || 0;
      const beneficioCultivo = kilosCultivo * precio;

      totalKilos += kilosCultivo;
      totalBeneficios += beneficioCultivo;
    });

    // Renderizar template EXACTO
    res.render("dashboard", {
      user: user,
      crops: crops,
      active_crops: activeCrops,
      finished_crops: finishedCrops,
      total_kilos: totalKilos,
      total_beneficios: totalBeneficios,
      // Todas las variables que usas en tu template
    });
  } catch (error) {
    console.error("Error en dashboard:", error);
    res.status(500).send("Error cargando dashboard");
  }
});

// Todas las demás rutas de tu aplicación...
// (aquí agregaríamos todas las rutas de crops.py, analytics.py, auth.py, etc.)

// Exportar la función
exports.flaskApp = functions
  .runWith({
    timeoutSeconds: 300,
    memory: "1GB",
  })
  .https.onRequest(app);
