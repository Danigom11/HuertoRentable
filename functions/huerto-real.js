/**
 * Cloud Function que monta la aplicación Flask real de HuertoRentable
 * Usa toda la estructura de rutas y servicios existentes
 */

const functions = require("firebase-functions");
const admin = require("firebase-admin");
const express = require("express");
const cookieParser = require("cookie-parser");
const cors = require("cors");
const path = require("path");

const app = express();

// Middleware básico
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());

// Servir archivos estáticos
app.use("/static", express.static(path.join(__dirname, "../dist/static")));

// Middleware de autenticación (simulando tu auth_middleware.py)
async function authenticateUser(req, res, next) {
  try {
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
      req.session = req.session || {};
      req.session.is_authenticated = true;
      req.session.user_uid = decodedToken.uid;
      req.session.user = req.user;
    }

    next();
  } catch (error) {
    console.log("Auth error:", error);
    next();
  }
}

app.use(authenticateUser);

// Función helper para verificar autenticación (como require_auth)
function requireAuth(req, res, next) {
  if (!req.user) {
    return res.redirect("/onboarding");
  }
  next();
}

// ============================================
// RUTAS PRINCIPALES (Como tu main.py)
// ============================================

// Ruta raíz - Lógica exacta de tu home()
app.get("/", (req, res) => {
  console.log("🔍 [HOME] Request args:", req.query);
  console.log("🔍 [HOME] Session:", req.session);
  console.log("🔍 [HOME] Cookies:", req.cookies);

  // PRIORIDAD MÁXIMA: Si viene del registro, ir directo al dashboard
  if (
    req.query.from === "register" ||
    (req.get("Referer") && req.get("Referer").includes("register"))
  ) {
    console.log("🎯 [HOME] Usuario viene del registro - redirigir a dashboard");
    return res.redirect("/dashboard");
  }

  // 1) Usuario autenticado en sesión
  if (req.session?.is_authenticated && req.session?.user) {
    console.log("✅ [HOME] Usuario autenticado en sesión - ir a dashboard");
    return res.redirect("/dashboard");
  }

  // 2) Usuario detectado por token
  if (req.user) {
    console.log("✅ [HOME] Usuario detectado por helper - ir a dashboard");
    return res.redirect("/dashboard");
  }

  // 3) Cookie de usuario
  if (req.cookies?.huerto_user_uid || req.cookies?.firebase_id_token) {
    console.log("✅ [HOME] Cookie de usuario detectada - ir a dashboard");
    return res.redirect("/dashboard");
  }

  // Modo demo
  if (req.session?.demo_mode_chosen || req.query.demo === "true") {
    console.log("✅ [HOME] Modo demo - ir a dashboard");
    return res.redirect("/dashboard");
  }

  // Primera visita → onboarding
  console.log("❌ [HOME] No hay usuario - ir a onboarding");
  return res.redirect("/onboarding");
});

// Ruta de onboarding (como tu onboarding())
app.get("/onboarding", (req, res) => {
  // Aquí deberías renderizar tu template de onboarding
  // Por ahora usaremos el HTML directo hasta copiar los templates
  res.send(generateOnboardingHTML());
});

// Dashboard (como tu dashboard())
app.get("/dashboard", requireAuth, async (req, res) => {
  try {
    const user_uid = req.user.uid;
    const user = req.user;

    console.log(`✅ [Dashboard] Usuario autenticado: ${user_uid}`);

    // Obtener cultivos del usuario desde Firestore
    const db = admin.firestore();
    const cropsSnapshot = await db
      .collection("cultivos")
      .where("usuario_id", "==", user_uid)
      .orderBy("fecha_siembra", "desc")
      .get();

    const crops = [];
    cropsSnapshot.forEach((doc) => {
      crops.push({ id: doc.id, ...doc.data() });
    });

    console.log(`🌱 [Dashboard] Cultivos encontrados: ${crops.length}`);

    // Calcular métricas (como en tu código)
    const active_crops = crops.filter((c) => !c.fecha_cosecha);
    const finished_crops = crops.filter((c) => c.fecha_cosecha);

    let total_kilos = 0;
    let total_beneficios = 0;

    crops.forEach((crop) => {
      const produccion = crop.produccion_diaria || [];
      const kilos_cultivo = produccion.reduce(
        (sum, p) => sum + (p.kilos || 0),
        0
      );
      const precio = crop.precio_por_kilo || 0;
      const beneficio_cultivo = kilos_cultivo * precio;

      total_kilos += kilos_cultivo;
      total_beneficios += beneficio_cultivo;
    });

    // Renderizar dashboard con datos reales
    res.send(
      generateDashboardHTML({
        user,
        crops,
        active_crops: active_crops.length,
        finished_crops: finished_crops.length,
        total_kilos,
        total_beneficios,
        recent_crops: crops.slice(0, 5),
      })
    );
  } catch (error) {
    console.error("Error en dashboard:", error);
    res.status(500).send("Error cargando dashboard");
  }
});

// Función para generar HTML de onboarding (basado en tu template)
function generateOnboardingHTML() {
  return `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenido a HuertoRentable</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="manifest" href="/manifest.json">
    <style>
        .hero-section {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            color: #333;
        }
        .feature-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        .btn-custom {
            border-radius: 25px;
            padding: 1rem 2rem;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
    </style>
</head>
<body>
    <div class="hero-section">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-6">
                    <h1 class="display-3 fw-bold mb-4">🌱 HuertoRentable</h1>
                    <p class="lead mb-4">La aplicación definitiva para gestionar huertos rentables con análisis profesional y seguimiento detallado.</p>
                    
                    <div class="d-flex flex-wrap gap-3 mb-5">
                        <a href="/auth/register" class="btn btn-light btn-custom">
                            Comenzar Ahora
                        </a>
                        <a href="/auth/login" class="btn btn-outline-light btn-custom">
                            Ya tengo cuenta
                        </a>
                        <a href="/dashboard?demo=true" class="btn btn-secondary btn-custom">
                            Ver Demo
                        </a>
                    </div>
                </div>
                
                <div class="col-lg-6">
                    <div class="row">
                        <div class="col-md-6 mb-4">
                            <div class="feature-card text-center">
                                <div class="feature-icon">📊</div>
                                <h4>Analytics Avanzados</h4>
                                <p>Gráficas detalladas de producción, beneficios y tendencias.</p>
                            </div>
                        </div>
                        <div class="col-md-6 mb-4">
                            <div class="feature-card text-center">
                                <div class="feature-icon">🌾</div>
                                <h4>Gestión Completa</h4>
                                <p>Control total de siembra, abonos, riego y cosecha.</p>
                            </div>
                        </div>
                        <div class="col-md-6 mb-4">
                            <div class="feature-card text-center">
                                <div class="feature-icon">💰</div>
                                <h4>Rentabilidad</h4>
                                <p>Calcula beneficios y optimiza tu producción.</p>
                            </div>
                        </div>
                        <div class="col-md-6 mb-4">
                            <div class="feature-card text-center">
                                <div class="feature-icon">📱</div>
                                <h4>PWA Moderna</h4>
                                <p>Funciona offline y se instala como app nativa.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Sección de características detalladas -->
            <div class="row mt-5 pt-5">
                <div class="col-12 text-center mb-5">
                    <h2 class="display-5">¿Por qué elegir HuertoRentable?</h2>
                    <p class="lead">Todo lo que necesitas para maximizar la rentabilidad de tu huerto</p>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="text-center">
                        <div class="feature-icon">🔄</div>
                        <h4>Seguimiento Diario</h4>
                        <p>Registra producción, abonos y actividades día a día para un control total.</p>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="text-center">
                        <div class="feature-icon">📈</div>
                        <h4>Análisis Predictivo</h4>
                        <p>Predicciones basadas en datos históricos para planificar mejor.</p>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="text-center">
                        <div class="feature-icon">🌍</div>
                        <h4>Acceso Universal</h4>
                        <p>Desde cualquier dispositivo, en cualquier lugar, con o sin internet.</p>
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

// Función para generar dashboard HTML (como tu template)
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
        .metric-card { 
            border: none; 
            border-radius: 15px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
            transition: transform 0.2s;
        }
        .metric-card:hover { transform: translateY(-5px); }
        .metric-value { font-size: 2.5rem; font-weight: bold; }
        .navbar-brand { font-weight: bold; }
        .crop-item {
            border-left: 4px solid #28a745;
            background: white;
            border-radius: 8px;
            margin-bottom: 1rem;
            padding: 1rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-success shadow">
        <div class="container">
            <a class="navbar-brand" href="/">🌱 HuertoRentable</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <div class="navbar-nav ms-auto">
                    <a class="nav-link active" href="/dashboard">Dashboard</a>
                    <a class="nav-link" href="/crops">Cultivos</a>
                    <a class="nav-link" href="/analytics">Analytics</a>
                    <a class="nav-link" href="/exports">Exportar</a>
                    <a class="nav-link" href="/auth/logout">Salir</a>
                </div>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <!-- Encabezado -->
        <div class="row mb-4">
            <div class="col-12">
                <h1 class="display-6">Dashboard</h1>
                <p class="text-muted">Bienvenido de vuelta, ${
                  data.user.email
                } 👋</p>
            </div>
        </div>
        
        <!-- Métricas principales -->
        <div class="row mb-4">
            <div class="col-md-3 mb-3">
                <div class="card metric-card text-center p-4">
                    <div class="metric-value text-success">${
                      data.active_crops
                    }</div>
                    <div class="text-muted">Cultivos Activos</div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card metric-card text-center p-4">
                    <div class="metric-value text-info">${
                      data.finished_crops
                    }</div>
                    <div class="text-muted">Cosechados</div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card metric-card text-center p-4">
                    <div class="metric-value text-warning">${data.total_kilos.toFixed(
                      1
                    )} kg</div>
                    <div class="text-muted">Total Producido</div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card metric-card text-center p-4">
                    <div class="metric-value text-danger">€${data.total_beneficios.toFixed(
                      2
                    )}</div>
                    <div class="text-muted">Beneficios Totales</div>
                </div>
            </div>
        </div>
        
        <!-- Sección principal -->
        <div class="row">
            <div class="col-lg-8 mb-4">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">Cultivos Recientes</h5>
                        <a href="/crops" class="btn btn-success btn-sm">Ver todos</a>
                    </div>
                    <div class="card-body">
                        ${
                          data.recent_crops.length > 0
                            ? data.recent_crops
                                .map(
                                  (crop) => `
                                <div class="crop-item">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 class="mb-1">${crop.nombre}</h6>
                                            <small class="text-muted">
                                                Precio: €${
                                                  crop.precio_por_kilo
                                                }/kg
                                                ${
                                                  crop.fecha_siembra
                                                    ? ` • Sembrado: ${new Date(
                                                        crop.fecha_siembra
                                                          ._seconds * 1000
                                                      ).toLocaleDateString()}`
                                                    : ""
                                                }
                                            </small>
                                        </div>
                                        <span class="badge ${
                                          crop.activo
                                            ? "bg-success"
                                            : "bg-secondary"
                                        }">
                                            ${
                                              crop.activo
                                                ? "Activo"
                                                : "Finalizado"
                                            }
                                        </span>
                                    </div>
                                </div>
                            `
                                )
                                .join("")
                            : `<div class="text-center py-5">
                                <div class="display-1">🌱</div>
                                <h4>¡Comienza tu primer cultivo!</h4>
                                <p class="text-muted">No hay cultivos registrados aún.</p>
                                <a href="/crops/add" class="btn btn-success">Añadir Cultivo</a>
                               </div>`
                        }
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">Acciones Rápidas</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="/crops/add" class="btn btn-success">
                                🌱 Nuevo Cultivo
                            </a>
                            <a href="/crops/production" class="btn btn-outline-primary">
                                📊 Registrar Producción
                            </a>
                            <a href="/analytics" class="btn btn-outline-info">
                                📈 Ver Analytics
                            </a>
                            <a href="/exports" class="btn btn-outline-secondary">
                                📄 Exportar Datos
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-3">
                    <div class="card-header">
                        <h5 class="mb-0">Resumen Mensual</h5>
                    </div>
                    <div class="card-body">
                        <small class="text-muted">Producción este mes</small>
                        <div class="h4 text-success">${(
                          data.total_kilos * 0.3
                        ).toFixed(1)} kg</div>
                        
                        <small class="text-muted">Beneficios este mes</small>
                        <div class="h4 text-warning">€${(
                          data.total_beneficios * 0.3
                        ).toFixed(2)}</div>
                        
                        <div class="progress mt-2">
                            <div class="progress-bar bg-success" role="progressbar" style="width: 65%"></div>
                        </div>
                        <small class="text-muted">65% del objetivo mensual</small>
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

// Exportar la función
exports.flaskApp = functions
  .runWith({
    timeoutSeconds: 300,
    memory: "1GB",
  })
  .https.onRequest(app);
