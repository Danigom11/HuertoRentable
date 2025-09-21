#!/usr/bin/env python3
"""
Despliegue unificado de HuertoRentable
- Construye assets (dist)
- Construye imagen y despliega a Cloud Run
- Despliega Firebase Hosting apuntando a Cloud Run

Uso:
  python deploy.py [--project huerto-rentable] [--region us-central1] [--service huertorentable]

Requisitos:
- gcloud CLI autenticado y con permisos (roles/run.admin, storage.admin)
- Firebase CLI autenticado y proyecto activo
- Dockerfile en la raíz
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def run(cmd: str, desc: str) -> None:
    print(f"\n➡️  {desc}")
    print(f"   $ {cmd}")
    proc = subprocess.run(cmd, shell=True)
    if proc.returncode != 0:
        print(f"❌ Error en: {desc}")
        sys.exit(proc.returncode)
    print(f"✅ {desc}")


def which(bin_name: str) -> bool:
    from shutil import which as _which
    return _which(bin_name) is not None


def main():
    parser = argparse.ArgumentParser(description="Deploy HuertoRentable (Cloud Run + Hosting)")
    parser.add_argument("--project", default="huerto-rentable")
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--service", default="huertorentable")
    args = parser.parse_args()

    root = Path(__file__).parent
    image = f"gcr.io/{args.project}/{args.service}:latest"

    # Verificaciones rápidas
    if not which("gcloud"):
        print("❌ gcloud CLI no encontrado. Instálalo: https://cloud.google.com/sdk")
        sys.exit(1)
    if not which("firebase"):
        print("❌ Firebase CLI no encontrado. Instálalo: npm i -g firebase-tools")
        sys.exit(1)

    # 1) Build de assets
    if not (root / "build.py").exists():
        print("❌ build.py no encontrado en la raíz")
        sys.exit(1)
    # Usar llamada con argumentos para evitar problemas de quoting en Windows
    print("\n➡️  Construyendo assets (dist)")
    print(f"   $ {sys.executable} build.py")
    proc = subprocess.run([sys.executable, "build.py"])  # shell=False por defecto
    if proc.returncode != 0:
        print("❌ Error en: Construyendo assets (dist)")
        sys.exit(proc.returncode)
    print("✅ Construyendo assets (dist)")

    # 2) Cloud Run
    run(f"gcloud config set project {args.project}", "Seleccionando proyecto GCP")
    run(f"gcloud config set run/region {args.region}", "Seleccionando región Cloud Run")
    run(f"gcloud builds submit --tag {image} .", "Construyendo imagen con Cloud Build")
    deploy_cmd = (
    f"gcloud run deploy {args.service} "
    f"--image {image} --platform managed --allow-unauthenticated "
        f"--port 8080 --cpu 1 --memory 512Mi --max-instances 10 --set-env-vars FLASK_ENV=production "
    f"--region {args.region}"
    )
    run(deploy_cmd, "Desplegando servicio a Cloud Run")

    # 3) Firebase Hosting
    run("firebase use", "Verificando proyecto Firebase activo")
    # Nos aseguramos de tener dist listo según firebase.json
    if not (root / "dist").exists():
        print("❌ Directorio dist no encontrado tras el build")
        sys.exit(1)
    run("firebase deploy --only hosting --project huerto-rentable", "Desplegando Firebase Hosting")

    # 4) Mostrar URLs finales
    print("\n🎉 Deploy completado correctamente")
    try:
        url = subprocess.check_output(
            [
                "gcloud",
                "run",
                "services",
                "describe",
                args.service,
                "--region",
                args.region,
                "--format=value(status.url)",
            ],
            text=True,
        ).strip()
    except Exception:
        url = "(no disponible)"
    print(f"🌐 Cloud Run: {url}")
    print("🌐 Hosting: https://huerto-rentable.web.app/")


if __name__ == "__main__":
    main()
