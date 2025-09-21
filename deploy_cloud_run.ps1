# Deploy a Cloud Run del backend Flask HuertoRentable
Param(
    [string]$Project = "huerto-rentable",
    [string]$Region = "us-central1",
    [string]$Service = "huertorentable",
    [string]$Image = "gcr.io/huerto-rentable/huertorentable:latest"
)

Write-Host "🚀 Despliegue Cloud Run - HuertoRentable" -ForegroundColor Green

# 1) Verificar gcloud
try {
    $gver = gcloud --version
    Write-Host "✅ gcloud disponible" -ForegroundColor Green
}
catch {
    Write-Host "❌ gcloud CLI no encontrado. Instálalo y autentícate: https://cloud.google.com/sdk" -ForegroundColor Red
    exit 1
}

# 2) Configurar proyecto y región
& gcloud config set project $Project | Out-Null
& gcloud config set run/region $Region | Out-Null

# 3) Construir imagen (Cloud Build) usando Dockerfile
Write-Host "📦 Construyendo imagen con Cloud Build..." -ForegroundColor Yellow
$build = gcloud builds submit --tag $Image .
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Error al construir imagen" -ForegroundColor Red; exit 1 }

# 4) Desplegar servicio a Cloud Run
Write-Host "🚢 Desplegando a Cloud Run ($Service)..." -ForegroundColor Yellow
$deploy = gcloud run deploy $Service `
    --image $Image `
    --platform managed `
    --allow-unauthenticated `
    --port 8080 `
    --cpu 1 `
    --memory 512Mi `
    --max-instances 10 `
    --set-env-vars FLASK_ENV=production `
    --region $Region

if ($LASTEXITCODE -ne 0) { Write-Host "❌ Error en el despliegue" -ForegroundColor Red; exit 1 }

Write-Host "🎉 Despliegue completado" -ForegroundColor Green

# 5) Mostrar URL del servicio
$svcUrl = gcloud run services describe $Service --region $Region --format="value(status.url)"
Write-Host "🌐 URL Cloud Run: $svcUrl" -ForegroundColor Cyan

# 6) Sugerencias post-deploy
Write-Host "\nSiguientes pasos:" -ForegroundColor Magenta
Write-Host " - Verifica salud: $svcUrl/api/health" -ForegroundColor White
Write-Host " - Asegura que firebase.json apunta a serviceId '$Service' en región '$Region'" -ForegroundColor White
Write-Host " - Si cambiaste service/region, ejecuta: firebase deploy --only hosting" -ForegroundColor White
