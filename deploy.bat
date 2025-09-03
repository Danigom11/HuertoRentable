@echo off
echo ===========================================
echo   DEPLOYING HUERTORENTABLE CLOUD FUNCTIONS
echo ===========================================
echo.

echo 1. Verificando configuracion...
firebase --version
firebase use

echo.
echo 2. Listando proyectos disponibles...
firebase projects:list

echo.
echo 3. Iniciando deploy...
firebase deploy --only functions

echo.
echo 4. Verificando funciones desplegadas...
firebase functions:list

echo.
echo ===========================================
echo   DEPLOY COMPLETADO
echo ===========================================
echo.
echo URLs base para Android:
echo https://us-central1-huerto-rentable.cloudfunctions.net/
echo.
echo Health Check:
echo https://us-central1-huerto-rentable.cloudfunctions.net/health
echo.
pause
