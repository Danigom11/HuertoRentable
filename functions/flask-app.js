/**
 * Cloud Function para servir HuertoRentable Flask App
 * Esta función servirá como proxy para la aplicación Flask
 */

const functions = require("firebase-functions");
const admin = require("firebase-admin");
const express = require("express");
const cors = require("cors");
const path = require("path");

// Inicializar Firebase Admin si no está inicializado
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

// Middleware para parsear JSON
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Servir archivos estáticos
app.use("/static", express.static(path.join(__dirname, "../dist/static")));

// Función para verificar autenticación
async function verifyAuth(req, res, next) {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res.redirect("/login");
    }

    const idToken = authHeader.split("Bearer ")[1];
    const decodedToken = await admin.auth().verifyIdToken(idToken);

    req.user = {
      uid: decodedToken.uid,
      email: decodedToken.email,
    };

    next();
  } catch (error) {
    console.error("Error de autenticación:", error);
    res.redirect("/login");
  }
}

// ============================================
// RUTAS PRINCIPALES
// ============================================

// Ruta de inicio - Dashboard
app.get(["/", "/dashboard"], verifyAuth, async (req, res) => {
  try {
    const db = admin.firestore();

    // Obtener resumen de cultivos del usuario
    const cultivosRef = db
      .collection("cultivos")
      .where("usuario_id", "==", req.user.uid);
    const cultivosSnapshot = await cultivosRef.get();

    const cultivos = [];
    let totalBeneficios = 0;
    let totalKilos = 0;

    cultivosSnapshot.forEach((doc) => {
      const cultivo = { id: doc.id, ...doc.data() };
      cultivos.push(cultivo);

      // Calcular totales
      if (cultivo.produccion_diaria) {
        const kilosCultivo = cultivo.produccion_diaria.reduce(
          (total, prod) => total + (prod.kilos || 0),
          0
        );
        totalKilos += kilosCultivo;
        totalBeneficios += kilosCultivo * (cultivo.precio_por_kilo || 0);
      }
    });

    // Generar HTML del dashboard
    const dashboardHTML = generateDashboardHTML({
      user: req.user,
      cultivos,
      totalBeneficios,
      totalKilos,
      cultivosActivos: cultivos.filter((c) => c.activo).length,
    });

    res.send(dashboardHTML);
  } catch (error) {
    console.error("Error en dashboard:", error);
    res.status(500).send(generateErrorHTML("Error al cargar el dashboard"));
  }
});

// Ruta de login
app.get("/login", (req, res) => {
  const loginHTML = generateLoginHTML();
  res.send(loginHTML);
});

// Ruta de cultivos
app.get("/crops", verifyAuth, async (req, res) => {
  try {
    const db = admin.firestore();
    const cultivosRef = db
      .collection("cultivos")
      .where("usuario_id", "==", req.user.uid);
    const cultivosSnapshot = await cultivosRef.get();

    const cultivos = [];
    cultivosSnapshot.forEach((doc) => {
      cultivos.push({ id: doc.id, ...doc.data() });
    });

    const cropsHTML = generateCropsHTML({ cultivos, user: req.user });
    res.send(cropsHTML);
  } catch (error) {
    console.error("Error en cultivos:", error);
    res.status(500).send(generateErrorHTML("Error al cargar cultivos"));
  }
});

// Ruta de analytics
app.get("/analytics", verifyAuth, async (req, res) => {
  try {
    const db = admin.firestore();
    const cultivosRef = db
      .collection("cultivos")
      .where("usuario_id", "==", req.user.uid);
    const cultivosSnapshot = await cultivosRef.get();

    const cultivos = [];
    cultivosSnapshot.forEach((doc) => {
      cultivos.push({ id: doc.id, ...doc.data() });
    });

    const analyticsHTML = generateAnalyticsHTML({ cultivos, user: req.user });
    res.send(analyticsHTML);
  } catch (error) {
    console.error("Error en analytics:", error);
    res.status(500).send(generateErrorHTML("Error al cargar analytics"));
  }
});

// ============================================
// GENERADORES DE HTML
// ============================================

function generateBaseHTML(title, content, additionalHead = "") {
  return `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title} - HuertoRentable</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" href="/static/img/icon.png">
    ${additionalHead}
    <style>
        body { background-color: #f8f9fa; }
        .navbar-brand { font-weight: bold; }
        .card { border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .btn-success { background-color: #28a745; border-color: #28a745; }
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
            </div>
        </div>
    </nav>
    <main class="container mt-4">
        ${content}
    </main>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js');
        }
    </script>
</body>
</html>`;
}

function generateDashboardHTML(data) {
  const content = `
    <div class="row">
        <div class="col-12">
            <h1>Dashboard</h1>
            <p class="text-muted">Bienvenido, ${data.user.email}</p>
        </div>
    </div>
    
    <div class="row mb-4">
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="card-title">Cultivos Activos</h5>
                    <h2 class="text-success">${data.cultivosActivos}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="card-title">Total Kilos</h5>
                    <h2 class="text-info">${data.totalKilos.toFixed(2)}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="card-title">Beneficios</h5>
                    <h2 class="text-warning">€${data.totalBeneficios.toFixed(
                      2
                    )}</h2>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5>Cultivos Recientes</h5>
                </div>
                <div class="card-body">
                    ${
                      data.cultivos.length > 0
                        ? data.cultivos
                            .slice(0, 5)
                            .map(
                              (cultivo) => `
                            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                                <div>
                                    <strong>${cultivo.nombre}</strong>
                                    <br><small class="text-muted">Precio: €${
                                      cultivo.precio_por_kilo
                                    }/kg</small>
                                </div>
                                <span class="badge ${
                                  cultivo.activo ? "bg-success" : "bg-secondary"
                                }">
                                    ${cultivo.activo ? "Activo" : "Finalizado"}
                                </span>
                            </div>
                        `
                            )
                            .join("")
                        : '<p class="text-muted">No hay cultivos registrados aún.</p>'
                    }
                    <div class="mt-3">
                        <a href="/crops" class="btn btn-success">Ver todos los cultivos</a>
                    </div>
                </div>
            </div>
        </div>
    </div>`;

  return generateBaseHTML("Dashboard", content);
}

function generateLoginHTML() {
  const content = `
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header text-center">
                    <h3>🌱 HuertoRentable</h3>
                    <p class="text-muted">Inicia sesión para continuar</p>
                </div>
                <div class="card-body">
                    <div id="firebaseui-auth-container"></div>
                </div>
            </div>
        </div>
    </div>`;

  const firebaseScript = `
    <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/ui/6.0.1/firebase-ui-auth.js"></script>
    <link type="text/css" rel="stylesheet" href="https://www.gstatic.com/firebasejs/ui/6.0.1/firebase-ui-auth.css" />
    <script>
        // Configurar Firebase
        const firebaseConfig = {
            // Configuración de Firebase aquí
        };
        firebase.initializeApp(firebaseConfig);
        
        // Configurar FirebaseUI
        const ui = new firebaseui.auth.AuthUI(firebase.auth());
        const uiConfig = {
            callbacks: {
                signInSuccessWithAuthResult: function(authResult, redirectUrl) {
                    window.location.href = '/dashboard';
                    return false;
                }
            },
            signInOptions: [
                firebase.auth.EmailAuthProvider.PROVIDER_ID,
                firebase.auth.GoogleAuthProvider.PROVIDER_ID
            ]
        };
        ui.start('#firebaseui-auth-container', uiConfig);
    </script>`;

  return generateBaseHTML("Iniciar Sesión", content, firebaseScript);
}

function generateCropsHTML(data) {
  const content = `
    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>Gestión de Cultivos</h1>
                <button class="btn btn-success" data-bs-toggle="modal" data-bs-target="#nuevoCultivoModal">
                    + Nuevo Cultivo
                </button>
            </div>
        </div>
    </div>
    
    <div class="row">
        ${
          data.cultivos.length > 0
            ? data.cultivos
                .map(
                  (cultivo) => `
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between">
                            <h5>${cultivo.nombre}</h5>
                            <span class="badge ${
                              cultivo.activo ? "bg-success" : "bg-secondary"
                            }">
                                ${cultivo.activo ? "Activo" : "Finalizado"}
                            </span>
                        </div>
                        <div class="card-body">
                            <p><strong>Precio por kilo:</strong> €${
                              cultivo.precio_por_kilo
                            }</p>
                            <p><strong>Fecha siembra:</strong> ${new Date(
                              cultivo.fecha_siembra._seconds * 1000
                            ).toLocaleDateString()}</p>
                            <p><strong>Producción total:</strong> ${
                              cultivo.produccion_diaria
                                ? cultivo.produccion_diaria
                                    .reduce(
                                      (total, prod) =>
                                        total + (prod.kilos || 0),
                                      0
                                    )
                                    .toFixed(2)
                                : 0
                            } kg</p>
                            <div class="btn-group">
                                <button class="btn btn-outline-primary btn-sm">Ver detalles</button>
                                <button class="btn btn-outline-warning btn-sm">Editar</button>
                            </div>
                        </div>
                    </div>
                </div>
            `
                )
                .join("")
            : '<div class="col-12"><p class="text-muted text-center">No hay cultivos registrados.</p></div>'
        }
    </div>`;

  return generateBaseHTML("Cultivos", content);
}

function generateAnalyticsHTML(data) {
  const content = `
    <div class="row">
        <div class="col-12">
            <h1>Analytics</h1>
            <p class="text-muted">Análisis de rendimiento de tus cultivos</p>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5>Producción por Cultivo</h5>
                </div>
                <div class="card-body">
                    <canvas id="produccionChart"></canvas>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5>Beneficios Mensuales</h5>
                </div>
                <div class="card-body">
                    <canvas id="beneficiosChart"></canvas>
                </div>
            </div>
        </div>
    </div>`;

  const chartScript = `
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Gráfica de producción
        const ctxProduccion = document.getElementById('produccionChart').getContext('2d');
        new Chart(ctxProduccion, {
            type: 'bar',
            data: {
                labels: ${JSON.stringify(data.cultivos.map((c) => c.nombre))},
                datasets: [{
                    label: 'Kilos producidos',
                    data: ${JSON.stringify(
                      data.cultivos.map((c) =>
                        c.produccion_diaria
                          ? c.produccion_diaria.reduce(
                              (total, prod) => total + (prod.kilos || 0),
                              0
                            )
                          : 0
                      )
                    )},
                    backgroundColor: 'rgba(40, 167, 69, 0.8)'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        // Gráfica de beneficios
        const ctxBeneficios = document.getElementById('beneficiosChart').getContext('2d');
        new Chart(ctxBeneficios, {
            type: 'line',
            data: {
                labels: ${JSON.stringify(data.cultivos.map((c) => c.nombre))},
                datasets: [{
                    label: 'Beneficios (€)',
                    data: ${JSON.stringify(
                      data.cultivos.map((c) => {
                        const kilos = c.produccion_diaria
                          ? c.produccion_diaria.reduce(
                              (total, prod) => total + (prod.kilos || 0),
                              0
                            )
                          : 0;
                        return kilos * (c.precio_por_kilo || 0);
                      })
                    )},
                    borderColor: 'rgba(255, 193, 7, 1)',
                    backgroundColor: 'rgba(255, 193, 7, 0.2)',
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>`;

  return generateBaseHTML("Analytics", content, chartScript);
}

function generateErrorHTML(message) {
  const content = `
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="alert alert-danger text-center">
                <h4>Error</h4>
                <p>${message}</p>
                <a href="/" class="btn btn-success">Volver al inicio</a>
            </div>
        </div>
    </div>`;

  return generateBaseHTML("Error", content);
}

// Exportar la función
exports.flaskApp = functions.https.onRequest(app);
