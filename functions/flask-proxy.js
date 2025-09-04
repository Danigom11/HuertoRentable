/**
 * Cloud Function que ejecuta la aplicación Flask de HuertoRentable TAL CUAL ESTÁ
 * Sin modificar NADA del código original
 */

const functions = require("firebase-functions");
const { spawn } = require("child_process");
const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");

// Esta función simplemente ejecuta tu Flask app y hace proxy
const app = express();

// Configurar proxy a tu aplicación Flask
const proxyOptions = {
  target: "http://localhost:5000", // Tu Flask app
  changeOrigin: true,
  ws: true,
  pathRewrite: {
    "^/": "/", // Mantener todas las rutas exactas
  },
  router: {
    // Todas las rutas van a tu Flask
  },
  onError: (err, req, res) => {
    console.error("Proxy error:", err);
    res.status(500).send(`
      <h1>Iniciando HuertoRentable...</h1>
      <p>La aplicación se está cargando. Intenta de nuevo en unos segundos.</p>
      <script>setTimeout(() => location.reload(), 3000);</script>
    `);
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log("Proxy request:", req.method, req.url);
  },
};

// Función para iniciar tu aplicación Flask en la Cloud Function
let flaskProcess = null;

async function startFlaskApp() {
  if (flaskProcess) {
    return; // Ya está corriendo
  }

  console.log("🚀 Iniciando aplicación Flask original...");

  // Ejecutar tu run.py exacto
  flaskProcess = spawn("python", ["run.py"], {
    cwd: __dirname + "/../",
    env: {
      ...process.env,
      FLASK_ENV: "production",
      PORT: "5000",
      PYTHONPATH: __dirname + "/../",
    },
    stdio: "pipe",
  });

  flaskProcess.stdout.on("data", (data) => {
    console.log("Flask:", data.toString());
  });

  flaskProcess.stderr.on("data", (data) => {
    console.error("Flask error:", data.toString());
  });

  // Esperar a que Flask esté listo
  await new Promise((resolve) => {
    setTimeout(resolve, 5000); // Dar tiempo a Flask para iniciar
  });
}

// Middleware para iniciar Flask si no está corriendo
app.use(async (req, res, next) => {
  try {
    await startFlaskApp();
    next();
  } catch (error) {
    console.error("Error starting Flask:", error);
    res.status(500).send("Error starting application");
  }
});

// Proxy TODAS las rutas a tu aplicación Flask
app.use("/", createProxyMiddleware(proxyOptions));

// Exportar la función
exports.flaskApp = functions
  .runWith({
    timeoutSeconds: 540, // Máximo tiempo
    memory: "2GB", // Más memoria para Flask
  })
  .https.onRequest(app);
