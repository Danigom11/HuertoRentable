/**
 * Cloud Function que ejecuta DIRECTAMENTE tu aplicación Flask
 * Usando functions-framework para Python
 */

const functions = require("firebase-functions");
const express = require("express");
const { exec } = require("child_process");
const path = require("path");

const app = express();

// Servir archivos estáticos
app.use("/static", express.static(path.join(__dirname, "../static")));

// Proxy directo a Flask
app.use("*", (req, res) => {
  // Ejecutar tu Flask app directamente
  const pythonPath = process.env.PYTHON_PATH || "python";
  const appPath = path.join(__dirname, "../");

  // Configurar variables de entorno para Flask
  const env = {
    ...process.env,
    FLASK_ENV: "production",
    FLASK_APP: "run.py",
    PYTHONPATH: appPath,
    PORT: "8080",
  };

  // Ejecutar Flask
  const flaskProcess = exec(`${pythonPath} run.py`, {
    cwd: appPath,
    env: env,
  });

  // Redirigir la respuesta
  flaskProcess.stdout.on("data", (data) => {
    console.log("Flask output:", data);
  });

  flaskProcess.stderr.on("data", (data) => {
    console.error("Flask error:", data);
  });

  // Por ahora, devolver un mensaje mientras arranca
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
        <title>HuertoRentable - Iniciando</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #28a745, #20c997); color: white;">
        <h1>🌱 HuertoRentable</h1>
        <p>Tu aplicación se está iniciando...</p>
        <p>Esto puede tomar unos segundos la primera vez.</p>
        <script>
            setTimeout(() => {
                location.reload();
            }, 5000);
        </script>
    </body>
    </html>
  `);
});

exports.flaskApp = functions
  .runWith({
    timeoutSeconds: 540,
    memory: "2GB",
  })
  .https.onRequest(app);
