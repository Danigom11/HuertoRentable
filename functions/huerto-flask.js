/**
 * Cloud Function para HuertoRentable - Aplicación Flask completa
 * Sirve la aplicación Flask real con todas sus funcionalidades
 */

const functions = require("firebase-functions");
const admin = require("firebase-admin");

// Inicializar Firebase Admin si no está inicializado
if (!admin.apps.length) {
  admin.initializeApp();
}

// Función para servir la aplicación Flask completa
const { spawn } = require("child_process");
const express = require("express");
const httpProxy = require("http-proxy-middleware");

const app = express();

// Configurar proxy para la aplicación Flask
const flaskProxy = httpProxy.createProxyMiddleware({
  target: "http://localhost:5000", // Donde correrá Flask
  changeOrigin: true,
  ws: true, // Habilitar WebSocket si es necesario
  pathRewrite: {
    "^/": "/", // Mantener todas las rutas
  },
  onError: (err, req, res) => {
    console.error("Error en proxy Flask:", err);
    res.status(500).send("Error interno del servidor");
  },
});

// Usar el proxy para todas las rutas
app.use("/", flaskProxy);

// Exportar la función
exports.huertoRentableApp = functions
  .runWith({
    timeoutSeconds: 300,
    memory: "512MB",
  })
  .https.onRequest(app);
