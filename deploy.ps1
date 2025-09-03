# HuertoRentable Cloud Functions Deploy Script
Write-Host "============================================" -ForegroundColor Green
Write-Host "   DEPLOYING HUERTORENTABLE CLOUD FUNCTIONS" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Verificar Firebase CLI
Write-Host "1. Verificando Firebase CLI..." -ForegroundColor Yellow
try {
    $firebaseVersion = firebase --version
    Write-Host "✅ Firebase CLI: $firebaseVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Firebase CLI no encontrado" -ForegroundColor Red
    exit 1
}

# Verificar proyecto
Write-Host ""
Write-Host "2. Verificando proyecto configurado..." -ForegroundColor Yellow
try {
    $currentProject = firebase use
    Write-Host "✅ Proyecto: $currentProject" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: No hay proyecto configurado" -ForegroundColor Red
    exit 1
}

# Verificar funciones
Write-Host ""
Write-Host "3. Verificando sintaxis de funciones..." -ForegroundColor Yellow
Set-Location "functions"
try {
    node -c index.js
    Write-Host "✅ Sintaxis correcta" -ForegroundColor Green
} catch {
    Write-Host "❌ Error de sintaxis en las funciones" -ForegroundColor Red
    exit 1
}
Set-Location ".."

# Deploy
Write-Host ""
Write-Host "4. Iniciando deploy..." -ForegroundColor Yellow
Write-Host "   Esto puede tardar 2-5 minutos..." -ForegroundColor Cyan
Write-Host ""

try {
    firebase deploy --only functions --project huerto-rentable
    Write-Host ""
    Write-Host "🎉 ¡DEPLOY COMPLETADO EXITOSAMENTE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "URLs finales para Android:" -ForegroundColor Cyan
    Write-Host "Base: https://us-central1-huerto-rentable.cloudfunctions.net/" -ForegroundColor White
    Write-Host "Health: https://us-central1-huerto-rentable.cloudfunctions.net/health" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "❌ Error en el deploy" -ForegroundColor Red
    Write-Host "Intenta: firebase login" -ForegroundColor Yellow
    exit 1
}

Write-Host "============================================" -ForegroundColor Green
Write-Host "   BACKEND LISTO PARA ANDROID" -ForegroundColor Green  
Write-Host "============================================" -ForegroundColor Green
