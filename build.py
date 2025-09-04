#!/usr/bin/env python3
"""
Script de build para HuertoRentable
Prepara los archivos para deploy en Firebase Hosting
"""
import os
import shutil
import json
from pathlib import Path

def crear_directorio_dist():
    """Crear directorio dist limpio"""
    dist_path = Path('dist')
    if dist_path.exists():
        shutil.rmtree(dist_path)
    dist_path.mkdir()
    return dist_path

def copiar_archivos_estaticos(dist_path):
    """Copiar archivos estáticos (CSS, JS, imágenes)"""
    static_src = Path('static')
    static_dest = dist_path / 'static'
    
    if static_src.exists():
        shutil.copytree(static_src, static_dest)
        print("✓ Archivos estáticos copiados")

def copiar_templates(dist_path):
    """Copiar templates HTML"""
    templates_src = Path('templates')
    templates_dest = dist_path / 'templates'
    
    if templates_src.exists():
        shutil.copytree(templates_src, templates_dest)
        print("✓ Templates copiados")

def copiar_manifest_y_sw(dist_path):
    """Copiar manifest.json y service-worker.js"""
    archivos_pwa = ['manifest.json', 'service-worker.js']
    
    for archivo in archivos_pwa:
        if Path(archivo).exists():
            shutil.copy2(archivo, dist_path / archivo)
            print(f"✓ {archivo} copiado")

def crear_index_html(dist_path):
    """Crear un index.html básico que redirija a la app Flask"""
    index_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HuertoRentable - Cargando...</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            padding-top: 50px;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            min-height: 100vh;
            margin: 0;
        }
        .loader {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #ffffff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 2s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <h1>🌱 HuertoRentable</h1>
    <div class="loader"></div>
    <p>Cargando aplicación...</p>
    <script>
        // Redireccionar a la Cloud Function
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 2000);
    </script>
    <script>
        // Registrar Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js');
        }
    </script>
</body>
</html>"""
    
    with open(dist_path / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_content)
    print("✓ index.html creado")

def crear_404_html(dist_path):
    """Crear página 404 personalizada"""
    html_404 = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Página no encontrada - HuertoRentable</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            padding-top: 50px;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            min-height: 100vh;
            margin: 0;
        }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .btn { 
            display: inline-block; 
            padding: 10px 20px; 
            background: white; 
            color: #28a745; 
            text-decoration: none; 
            border-radius: 5px; 
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌱 HuertoRentable</h1>
        <h2>Página no encontrada</h2>
        <p>La página que buscas no existe o ha sido movida.</p>
        <a href="/" class="btn">Volver al inicio</a>
    </div>
</body>
</html>"""
    
    with open(dist_path / '404.html', 'w', encoding='utf-8') as f:
        f.write(html_404)
    print("✓ 404.html creado")

def main():
    """Función principal del build"""
    print("🔨 Iniciando build de HuertoRentable...")
    
    # Crear directorio dist
    dist_path = crear_directorio_dist()
    
    # Copiar archivos necesarios
    copiar_archivos_estaticos(dist_path)
    copiar_templates(dist_path)
    copiar_manifest_y_sw(dist_path)
    
    # Crear archivos HTML
    crear_index_html(dist_path)
    crear_404_html(dist_path)
    
    print("\n✅ Build completado exitosamente!")
    print(f"📦 Archivos preparados en: {dist_path.absolute()}")
    print("\n🚀 Listo para deploy con: firebase deploy --only hosting")

if __name__ == "__main__":
    main()
