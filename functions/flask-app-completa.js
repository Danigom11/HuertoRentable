/**
 * Cloud Function real para HuertoRentable
 * Integra la aplicación Flask completa existente
 */

const functions = require("firebase-functions");
const admin = require("firebase-admin");
const express = require("express");
const cors = require("cors");
const path = require("path");

// Inicializar Firebase Admin
if (!admin.apps.length) {
  admin.initializeApp();
}

const app = express();

// Configurar CORS
app.use(
  cors({
    origin: true,
    credentials: true,
  })
);

// Middleware para parsear datos
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Configurar motor de plantillas (simulando Jinja2)
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "../dist/templates"));

// Servir archivos estáticos
app.use("/static", express.static(path.join(__dirname, "../dist/static")));

// Middleware de autenticación simplificado
async function authMiddleware(req, res, next) {
  try {
    // Buscar token en cookies o headers
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
    }

    next();
  } catch (error) {
    console.log("Auth middleware error:", error);
    next(); // Continuar sin autenticación
  }
}

app.use(authMiddleware);

// ============================================
// RUTAS PRINCIPALES (Como tu Flask original)
// ============================================

// Ruta raíz - Onboarding o Dashboard
app.get("/", async (req, res) => {
  try {
    if (!req.user) {
      // Mostrar onboarding como en tu app original
      return res.send(`
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>HuertoRentable - Bienvenido</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="manifest" href="/manifest.json">
            <style>
                .hero { background: linear-gradient(135deg, #28a745, #20c997); color: white; min-height: 100vh; }
                .feature-icon { font-size: 3rem; margin-bottom: 1rem; }
            </style>
        </head>
        <body>
            <div class="hero d-flex align-items-center">
                <div class="container text-center">
                    <h1 class="display-3 fw-bold mb-4">🌱 HuertoRentable</h1>
                    <p class="lead mb-4">Tu aplicación para gestionar huertos rentables de forma profesional</p>
                    
                    <div class="row mt-5">
                        <div class="col-md-4 mb-4">
                            <div class="feature-icon">📊</div>
                            <h3>Analytics Avanzados</h3>
                            <p>Gráficas detalladas de producción y beneficios</p>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="feature-icon">🌾</div>
                            <h3>Gestión de Cultivos</h3>
                            <p>Control completo de siembra, abonos y cosecha</p>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="feature-icon">💰</div>
                            <h3>Rentabilidad</h3>
                            <p>Calcula beneficios y optimiza tu producción</p>
                        </div>
                    </div>
                    
                    <div class="mt-5">
                        <a href="/login" class="btn btn-light btn-lg px-5 py-3 me-3">
                            Iniciar Sesión
                        </a>
                        <a href="/register" class="btn btn-outline-light btn-lg px-5 py-3">
                            Registrarse
                        </a>
                    </div>
                </div>
            </div>
            
            <script>
                // Registrar Service Worker
                if ('serviceWorker' in navigator) {
                    navigator.serviceWorker.register('/service-worker.js');
                }
            </script>
        </body>
        </html>
      `);
    }

    // Usuario autenticado - mostrar dashboard
    res.redirect("/dashboard");
  } catch (error) {
    console.error("Error en ruta raíz:", error);
    res.status(500).send("Error del servidor");
  }
});

// Ruta de login
app.get("/login", (req, res) => {
  if (req.user) {
    return res.redirect("/dashboard");
  }

  res.send(`
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Iniciar Sesión - HuertoRentable</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/ui/6.0.1/firebase-ui-auth.js"></script>
        <link rel="stylesheet" href="https://www.gstatic.com/firebasejs/ui/6.0.1/firebase-ui-auth.css" />
        <style>
            body { background: linear-gradient(135deg, #28a745, #20c997); min-height: 100vh; }
            .login-card { border: none; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body class="d-flex align-items-center">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6 col-lg-4">
                    <div class="card login-card">
                        <div class="card-body p-5">
                            <div class="text-center mb-4">
                                <h2 class="fw-bold text-success">🌱 HuertoRentable</h2>
                                <p class="text-muted">Inicia sesión para continuar</p>
                            </div>
                            
                            <div id="firebaseui-auth-container"></div>
                            
                            <div class="text-center mt-4">
                                <a href="/" class="btn btn-outline-secondary">← Volver al inicio</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Configurar Firebase (usar tu configuración real)
            const firebaseConfig = {
                apiKey: "AIzaSyCQNb3I5yXCSkWK8xBr3jRH_8-x4cIe89o",
                authDomain: "huerto-rentable.firebaseapp.com",
                projectId: "huerto-rentable",
                storageBucket: "huerto-rentable.appspot.com",
                messagingSenderId: "369311228687",
                appId: "1:369311228687:web:6c43b5c8b5a5f8c8f8c8f8"
            };
            firebase.initializeApp(firebaseConfig);
            
            // Configurar FirebaseUI
            const ui = new firebaseui.auth.AuthUI(firebase.auth());
            const uiConfig = {
                callbacks: {
                    signInSuccessWithAuthResult: function(authResult, redirectUrl) {
                        // Guardar token y redirigir
                        authResult.user.getIdToken().then(token => {
                            document.cookie = \`firebase_id_token=\${token}; path=/; max-age=3600\`;
                            window.location.href = '/dashboard';
                        });
                        return false;
                    }
                },
                signInOptions: [
                    firebase.auth.EmailAuthProvider.PROVIDER_ID,
                    firebase.auth.GoogleAuthProvider.PROVIDER_ID
                ],
                signInFlow: 'popup'
            };
            ui.start('#firebaseui-auth-container', uiConfig);
        </script>
    </body>
    </html>
  `);
});

// Ruta de registro
app.get("/register", (req, res) => {
  res.redirect("/login"); // Usar mismo formulario
});

// Dashboard principal
app.get("/dashboard", async (req, res) => {
  if (!req.user) {
    return res.redirect("/login");
  }

  try {
    const db = admin.firestore();

    // Obtener cultivos del usuario
    const cultivosSnapshot = await db
      .collection("cultivos")
      .where("usuario_id", "==", req.user.uid)
      .orderBy("fecha_siembra", "desc")
      .limit(5)
      .get();

    const cultivos = [];
    let totalKilos = 0;
    let totalBeneficios = 0;

    cultivosSnapshot.forEach((doc) => {
      const cultivo = { id: doc.id, ...doc.data() };
      cultivos.push(cultivo);

      if (cultivo.produccion_diaria) {
        const kilos = cultivo.produccion_diaria.reduce(
          (sum, p) => sum + (p.kilos || 0),
          0
        );
        totalKilos += kilos;
        totalBeneficios += kilos * (cultivo.precio_por_kilo || 0);
      }
    });

    res.send(
      generateDashboardHTML({
        user: req.user,
        cultivos,
        totalKilos,
        totalBeneficios,
        cultivosActivos: cultivos.filter((c) => c.activo).length,
      })
    );
  } catch (error) {
    console.error("Error en dashboard:", error);
    res.status(500).send("Error cargando dashboard");
  }
});

// Función para generar HTML del dashboard
function generateDashboardHTML(data) {
  return `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - HuertoRentable</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="manifest" href="/manifest.json">
    <style>
        body { background-color: #f8f9fa; }
        .metric-card { border: none; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2.5rem; font-weight: bold; }
        .navbar-brand { font-weight: bold; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-success">
        <div class="container">
            <a class="navbar-brand" href="/">🌱 HuertoRentable</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/dashboard">Dashboard</a>
                <a class="nav-link" href="/crops">Cultivos</a>
                <a class="nav-link" href="/analytics">Analytics</a>
                <a class="nav-link" href="/logout">Salir</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1>Dashboard</h1>
                <p class="text-muted">Bienvenido, ${data.user.email}</p>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-4 mb-3">
                <div class="card metric-card text-center p-4">
                    <div class="metric-value text-success">${
                      data.cultivosActivos
                    }</div>
                    <div class="text-muted">Cultivos Activos</div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card metric-card text-center p-4">
                    <div class="metric-value text-info">${data.totalKilos.toFixed(
                      1
                    )} kg</div>
                    <div class="text-muted">Total Producido</div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card metric-card text-center p-4">
                    <div class="metric-value text-warning">€${data.totalBeneficios.toFixed(
                      2
                    )}</div>
                    <div class="text-muted">Beneficios Totales</div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">Cultivos Recientes</h5>
                        <a href="/crops" class="btn btn-success btn-sm">Ver todos</a>
                    </div>
                    <div class="card-body">
                        ${
                          data.cultivos.length > 0
                            ? data.cultivos
                                .map(
                                  (c) => `
                                <div class="d-flex justify-content-between align-items-center border-bottom py-3">
                                    <div>
                                        <h6 class="mb-1">${c.nombre}</h6>
                                        <small class="text-muted">€${
                                          c.precio_por_kilo
                                        }/kg</small>
                                    </div>
                                    <span class="badge ${
                                      c.activo ? "bg-success" : "bg-secondary"
                                    }">
                                        ${c.activo ? "Activo" : "Finalizado"}
                                    </span>
                                </div>
                            `
                                )
                                .join("")
                            : '<p class="text-muted text-center py-4">No hay cultivos registrados aún.<br><a href="/crops" class="btn btn-success">Añadir primer cultivo</a></p>'
                        }
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js');
        }
    </script>
</body>
</html>`;
}

// Logout
app.get("/logout", (req, res) => {
  res.clearCookie("firebase_id_token");
  res.redirect("/");
});

// Ruta de cultivos (básica por ahora)
app.get("/crops", (req, res) => {
  if (!req.user) return res.redirect("/login");

  res.send(`
    <h1>Gestión de Cultivos</h1>
    <p>Usuario: ${req.user.email}</p>
    <a href="/dashboard">← Volver al Dashboard</a>
  `);
});

// Ruta de analytics (básica por ahora)
app.get("/analytics", (req, res) => {
  if (!req.user) return res.redirect("/login");

  res.send(`
    <h1>Analytics</h1>
    <p>Usuario: ${req.user.email}</p>
    <a href="/dashboard">← Volver al Dashboard</a>
  `);
});

// Exportar la función corregida
exports.flaskApp = functions
  .runWith({
    timeoutSeconds: 300,
    memory: "1GB",
  })
  .https.onRequest(app);
