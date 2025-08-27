"""
Factory de la aplicación Flask
Inicialización modular y profesional de HuertoRentable
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask
from config.settings import config

def create_app(config_name=None):
    """
    Factory function para crear la aplicación Flask
    
    Args:
        config_name (str): Nombre de la configuración a usar
        
    Returns:
        tuple: (app, db) - Instancia de Flask y cliente Firestore
    """
    # Determinar configuración
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    # Crear aplicación Flask
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar Firebase
    db = init_firebase(app.config)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Registrar error handlers
    register_error_handlers(app)
    
    # Configurar contexto de plantillas
    setup_template_context(app)
    
    return app, db

def init_firebase(config):
    """
    Inicializar Firebase con manejo de errores robusto
    
    Args:
        config: Configuración de la aplicación
        
    Returns:
        firestore.Client: Cliente de Firestore inicializado
    """
    try:
        # Verificar si Firebase ya está inicializado
        if firebase_admin._apps:
            app_firebase = firebase_admin.get_app()
        else:
            # Configuración desde variables de entorno
            if config.get('FIREBASE_TYPE'):
                print("✅ Cargando credenciales Firebase desde variables de entorno")
                
                # Reconstruir private_key con saltos de línea
                private_key = config.get('FIREBASE_PRIVATE_KEY')
                if private_key:
                    private_key = private_key.replace('\\n', '\n')
                
                cred_dict = {
                    "type": config.get('FIREBASE_TYPE'),
                    "project_id": config.get('FIREBASE_PROJECT_ID'),
                    "private_key_id": config.get('FIREBASE_PRIVATE_KEY_ID'),
                    "private_key": private_key,
                    "client_email": config.get('FIREBASE_CLIENT_EMAIL'),
                    "client_id": config.get('FIREBASE_CLIENT_ID'),
                    "auth_uri": config.get('FIREBASE_AUTH_URI'),
                    "token_uri": config.get('FIREBASE_TOKEN_URI'),
                    "auth_provider_x509_cert_url": config.get('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
                    "client_x509_cert_url": config.get('FIREBASE_CLIENT_X509_CERT_URL'),
                    "universe_domain": config.get('FIREBASE_UNIVERSE_DOMAIN')
                }
                
                cred = credentials.Certificate(cred_dict)
                
            else:
                # Fallback: usar archivo local en desarrollo
                print("⚠️ Usando credenciales locales de desarrollo")
                cred = credentials.Certificate('serviceAccountKey.json')
            
            # Inicializar Firebase
            app_firebase = firebase_admin.initialize_app(cred)
        
        # Crear cliente Firestore
        db = firestore.client()
        print("✅ Firebase inicializado correctamente")
        return db
        
    except Exception as error:
        print(f"❌ Error inicializando Firebase: {error}")
        print("⚠️ Modo demo activado - los datos no se guardarán")
        return None

def register_blueprints(app):
    """Registrar todos los blueprints de la aplicación"""
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.crops import crops_bp
    from app.routes.analytics import analytics_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(crops_bp, url_prefix='/crops')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(api_bp, url_prefix='/api')

def register_error_handlers(app):
    """Registrar manejadores de errores personalizados"""
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        return render_template('errors/500.html'), 500

def setup_template_context(app):
    """Configurar variables globales para plantillas"""
    import time
    
    @app.context_processor
    def inject_config():
        return {
            'PLAN_INVITADO': app.config['PLAN_INVITADO'],
            'PLAN_GRATUITO': app.config['PLAN_GRATUITO'], 
            'PLAN_PREMIUM': app.config['PLAN_PREMIUM'],
            'timestamp': int(time.time())  # Para versionado de assets
        }
    
    @app.template_global()
    def moment():
        """Función global para obtener timestamp actual"""
        return type('moment', (), {'timestamp': int(time.time())})()
    
    @app.after_request
    def add_cache_headers(response):
        """Añadir headers para controlar cache en producción"""
        if app.config.get('ENV') == 'production':
            # No cachear HTML, CSS y JS en producción para forzar actualizaciones
            if (response.mimetype.startswith('text/html') or 
                response.mimetype.startswith('text/css') or 
                response.mimetype.startswith('application/javascript')):
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
        return response
