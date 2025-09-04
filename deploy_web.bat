@echo off
echo ========================================
echo    HuertoRentable - Deploy Web
echo ========================================
echo.

echo 📦 Paso 1: Preparando archivos...
python build.py
if errorlevel 1 (
    echo ❌ Error en build
    pause
    exit /b 1
)
echo.

echo 📦 Paso 2: Instalando dependencias de Cloud Functions...
cd functions
call npm install
if errorlevel 1 (
    echo ❌ Error instalando dependencias
    cd ..
    pause
    exit /b 1
)
cd ..
echo.

echo 📦 Paso 3: Verificando Firebase CLI...
firebase --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Firebase CLI no encontrado, instalando...
    npm install -g firebase-tools
    if errorlevel 1 (
        echo ❌ Error instalando Firebase CLI
        pause
        exit /b 1
    )
)
echo.

echo 🚀 Paso 4: Iniciando deploy...
echo.
echo Opciones de deploy:
echo [1] Solo Hosting (recomendado para primera vez)
echo [2] Solo Cloud Functions
echo [3] Deploy completo (Hosting + Functions)
echo [4] Solo Firestore Rules
echo.
set /p opcion="Selecciona una opción (1-4): "

if "%opcion%"=="1" (
    echo 🌐 Desplegando solo Firebase Hosting...
    firebase deploy --only hosting
) else if "%opcion%"=="2" (
    echo ⚡ Desplegando solo Cloud Functions...
    firebase deploy --only functions
) else if "%opcion%"=="3" (
    echo 🚀 Deploy completo...
    firebase deploy
) else if "%opcion%"=="4" (
    echo 🔒 Desplegando Firestore Rules...
    firebase deploy --only firestore:rules
) else (
    echo ❌ Opción no válida
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo ❌ Error en el deploy
    echo.
    echo 💡 Soluciones posibles:
    echo    - Verificar conexión a internet
    echo    - Hacer login: firebase login
    echo    - Verificar permisos del proyecto
    pause
    exit /b 1
)

echo.
echo ✅ Deploy completado exitosamente!
echo.
echo 📱 Tu aplicación está disponible en:
echo    https://huerto-rentable.web.app
echo    https://huerto-rentable.firebaseapp.com
echo.
pause
