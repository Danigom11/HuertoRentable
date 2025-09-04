"""
Factory de la aplicación Flask
Inicialización modular y profesional de HuertoRentable
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, session, request
from config.settings import config

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

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
    
    # Debug: Verificar configuración de sesiones
    print(f"🔍 SECRET_KEY configurado: {bool(app.config.get('SECRET_KEY'))}")
    print(f"🔍 SESSION_PERMANENT: {app.config.get('SESSION_PERMANENT')}")
    print(f"🔍 PERMANENT_SESSION_LIFETIME: {app.config.get('PERMANENT_SESSION_LIFETIME')}")
    
    # Configurar Flask para que siempre envíe cookies de sesión
    # Nota: SameSite=None requiere Secure en navegadores modernos; en dev usamos 'Lax' para evitar rechazo
    app.config['SESSION_COOKIE_HTTPONLY'] = False  # Permitir acceso desde JS para debug
    app.config['SESSION_COOKIE_SECURE'] = False    # No HTTPS en desarrollo
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Envío en navegación same-site (formularios POST)
    
    @app.before_request
    def before_request():
        """Preparar cada request para manejar sesiones correctamente"""
        # LOG TODAS LAS PETICIONES
        print(f"🌐 [{request.method}] {request.url} - IP: {request.remote_addr}")
        print(f"   Headers: {dict(request.headers)}")
        print(f"   Session antes: {dict(session)}")
        
        # Forzar inicialización de sesión
        session.permanent = True
        # Crear una clave dummy para forzar creación de cookie
        if '_init' not in session:
            session['_init'] = True
    
    @app.after_request
    def after_request(response):
        """Middleware para forzar envío de cookies de sesión"""
        # CORS sólo si hay Origin explícito; evitar '*'+credentials que algunos navegadores rechazan
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Vary'] = 'Origin'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        # FORZAR envío de cookie de sesión en TODAS las respuestas
        session.permanent = True
        session.modified = True
        
        # Debug mejorado
        has_session_data = len([k for k in session.keys() if not k.startswith('_')]) > 0
        print(f"🍪 Session data: {has_session_data}, Response: {response.status_code}")
        
        return response
    
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
        import os
        # 1) Si ya está inicializado, solo intenta crear el cliente Firestore
        if firebase_admin._apps:
            try:
                db = firestore.client()
                print("✅ Firebase ya inicializado (reutilizado)")
                return db
            except Exception as e:
                print(f"⚠️ Firebase inicializado pero error creando Firestore client: {e}")
                return None

        # 2) Inicialización por variables de entorno explícitas (producción gestionada)
        if config.get('FIREBASE_TYPE'):
            print("✅ Cargando credenciales Firebase desde variables de entorno")
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
            firebase_admin.initialize_app(cred)
        else:
            # 3) Si estamos en Cloud Run/GCP, usar ADC (sin credenciales explícitas)
            if os.environ.get('K_SERVICE') or os.environ.get('GOOGLE_CLOUD_PROJECT'):
                print("✅ Detectado entorno GCP (Cloud Run) - usando Application Default Credentials")
                firebase_admin.initialize_app()
            else:
                # 4) Desarrollo: buscar serviceAccountKey.json de forma robusta
                print("⚠️ Buscando serviceAccountKey.json localmente")
                possible_paths = [
                    'serviceAccountKey.json',
                    os.path.join(os.getcwd(), 'serviceAccountKey.json'),
                    os.path.join(os.path.dirname(__file__), '..', 'serviceAccountKey.json'),
                    os.path.join(os.path.dirname(__file__), '..', '..', 'serviceAccountKey.json'),
                ]
                sa_path = next((p for p in possible_paths if os.path.exists(p)), None)
                if not sa_path:
                    print("❌ serviceAccountKey.json no encontrado. Intentando ADC por defecto.")
                    firebase_admin.initialize_app()
                else:
                    print(f"✅ Usando credenciales locales: {sa_path}")
                    cred = credentials.Certificate(sa_path)
                    firebase_admin.initialize_app(cred)

        # Intentar crear cliente Firestore (opcional para autenticación)
        try:
            db = firestore.client()
            print("✅ Firebase inicializado correctamente (Firestore OK)")
            return db
        except Exception as e:
            print(f"⚠️ Firebase inicializado, pero Firestore no disponible: {e}")
            return None

    except Exception as error:
        print(f"❌ Error inicializando Firebase (fase crítica): {error}")
        # En este caso, la verificación de tokens podría fallar. No forzamos salida, pero dejamos rastro.
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
    
    # Registrar filtro personalizado para formato español de números
    @app.template_filter('spanish_format')
    def spanish_format(value, decimals=2):
        """
        Filtro para formatear números con el formato español (coma como separador decimal)
        """
        try:
            if value is None:
                return "0"
            
            # Formatear el número con el número de decimales especificado
            formatted = f"{float(value):.{decimals}f}"
            
            # Convertir punto a coma (formato español)
            formatted = formatted.replace('.', ',')
            
            return formatted
        except (ValueError, TypeError):
            return str(value)
    
    @app.context_processor
    def inject_config():
        return {
            'PLAN_GRATUITO': app.config['PLAN_GRATUITO'], 
            'PLAN_PREMIUM': app.config['PLAN_PREMIUM'],
            'timestamp': int(time.time())  # Para versionado de assets
        }
    
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

def setup_auth_middleware(app):
    """Configurar middleware de autenticación automática"""
    from app.middleware.auth_middleware import auto_auth_middleware
    auto_auth_middleware(app)
