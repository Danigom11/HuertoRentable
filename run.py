"""
HuertoRentable - Aplicación Flask PWA Profesional
Sistema de gestión de huertos rentables con autenticación y monetización
"""
import os
from app import create_app

# Crear aplicación usando factory pattern
app, db = create_app()

# Inyectar db en el contexto de la aplicación
app.db = db

def main():
    """Función principal de la aplicación"""
    # Configurar host y puerto
    port = int(os.environ.get('PORT', 5001))
    host = '0.0.0.0' if os.environ.get('FLASK_ENV') == 'production' else '127.0.0.1'
    
    # Información de inicio
    print(f"🌱 HuertoRentable v2.0 iniciando en {host}:{port}")
    print(f"📊 Estado Firebase: {'✅ Conectado' if db else '⚠️ Modo Demo'}")
    print(f"🚀 Modo: {os.environ.get('FLASK_ENV', 'development').upper()}")
    
    # Iniciar aplicación
    app.run(host=host, port=port, debug=app.config['DEBUG'])

if __name__ == '__main__':
    main()
