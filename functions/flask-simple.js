/**
 * Cloud Function SIMPLE para HuertoRentable
 * Sin redirecciones complejas - Solo servir contenido directo
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

// Configuración básica
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Nota: Los estáticos los sirve Firebase Hosting desde dist/static
// app.use("/static", express.static(path.join(__dirname, "static")));

// Helper para leer templates
function readTemplate(templatePath, baseTemplate = true) {
  try {
    let content = fs.readFileSync(
      path.join(__dirname, "templates", templatePath),
      "utf8"
    );

    if (baseTemplate) {
      // Leer base.html
      const baseHtml = fs.readFileSync(
        path.join(__dirname, "templates/base.html"),
        "utf8"
      );

      // Extraer contenido del bloque content
      const contentMatch = content.match(
        /{% block content %}([\s\S]*?){% endblock %}/
      );
      const blockContent = contentMatch ? contentMatch[1] : content;

      // Insertar en base
      content = baseHtml
        .replace(/{% block title %}.*?{% endblock %}/, "HuertoRentable")
        .replace(/{% block content %}.*?{% endblock %}/, blockContent)
        .replace(/{{ url_for\('static', filename='([^']+)'\) }}/g, "/static/$1")
        .replace(/{{ url_for\('([^']+)'\) }}/g, "/$1")
        .replace(/{{ url_for\('([^']+)\.([^']+)'\) }}/g, "/$2");
    }

    return content;
  } catch (error) {
    console.error("Error reading template:", error);
    return `<html><body><h1>Error cargando página</h1><p>${error.message}</p></body></html>`;
  }
}

// RUTA PRINCIPAL - SIN REDIRECCIONES
app.get("/", (req, res) => {
  console.log("🏠 Acceso a ruta principal");

  // Servir directamente la página de onboarding sin redirecciones
  const html = readTemplate("onboarding/welcome.html");
  res.send(html);
});

// ONBOARDING
app.get("/onboarding", (req, res) => {
  console.log("🎯 Acceso a onboarding");
  const html = readTemplate("onboarding/welcome.html");
  res.send(html);
});

// DASHBOARD
app.get("/dashboard", (req, res) => {
  console.log("📊 Acceso a dashboard");
  const html = readTemplate("dashboard.html");
  res.send(html);
});

// LOGIN
app.get("/auth/login", (req, res) => {
  console.log("🔐 Acceso a login");
  const html = readTemplate("auth/login.html");
  res.send(html);
});

// CULTIVOS
app.get("/crops", (req, res) => {
  console.log("🌾 Acceso a cultivos");
  const html = readTemplate("crops.html");
  res.send(html);
});

// ANALYTICS
app.get("/analytics", (req, res) => {
  console.log("📈 Acceso a analytics");
  const html = readTemplate("analytics.html");
  res.send(html);
});

// CAPTURAR TODAS LAS RUTAS NO DEFINIDAS
app.get("*", (req, res) => {
  console.log(`❓ Ruta no encontrada: ${req.path}`);
  // Ir al onboarding por defecto
  const html = readTemplate("onboarding/welcome.html");
  res.send(html);
});

// Exportar función
exports.flaskApp = functions.https.onRequest(app);
