"""
Punto de entrada compatible con Render.com
""" 
import os
from run import app

if __name__ == "__main__":
    # Configuración para producción (Render)
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'  # Necesario para Render
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"🚀 Iniciando servidor en {host}:{port}")
    print(f"🌍 Modo: {'PRODUCTION' if not debug else 'DEVELOPMENT'}")
    
    app.run(host=host, port=port, debug=debug)
