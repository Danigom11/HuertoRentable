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
        # Detectar entorno de producción de varias maneras
        if (os.environ.get('FLASK_ENV') == 'production' or 
            os.environ.get('PORT') or  # Google Cloud Run siempre configura PORT
            os.environ.get('GAE_ENV') or  # Google App Engine
            os.environ.get('RAILWAY_ENVIRONMENT') or  # Railway
            os.environ.get('HEROKU_APP_NAME')):  # Heroku
            config_name = 'production'
        else:
            config_name = 'development'
    
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
    print(f"🔍 ENVIRONMENT: {config_name}")
    print(f"🔍 SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
    
    # Solo sobrescribir configuración de cookies en desarrollo
    if config_name == 'development':
        # Configurar Flask para desarrollo (sin HTTPS)
        app.config['SESSION_COOKIE_HTTPONLY'] = False  # Permitir acceso desde JS para debug
        app.config['SESSION_COOKIE_SECURE'] = False    # No HTTPS en desarrollo
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Envío en navegación same-site
    
    @app.before_request
    def before_request():
        """Preparar cada request para manejar sesiones correctamente"""
        # LOG TODAS LAS PETICIONES (reducido en producción)
        if config_name == 'development':
            print(f"🌐 [{request.method}] {request.url} - IP: {request.remote_addr}")
            print(f"   Headers: {dict(request.headers)}")
            print(f"   Session antes: {dict(session)}")
        else:
            # Solo log básico en producción
            print(f"🌐 [{request.method}] {request.path} - Session: {bool(session.get('is_authenticated'))}")
        
        # Forzar inicialización de sesión
        session.permanent = True
        # Crear una clave dummy para forzar creación de cookie
        if '_init' not in session:
            session['_init'] = True

        # Reconstrucción GLOBAL temprana: si no hay sesión válida pero sí cookies/URL con UID,
        # establecer una sesión mínima antes de que actúe @require_auth.
        try:
            has_valid_session = bool(session.get('is_authenticated') and session.get('user_uid'))
            if not has_valid_session:
                from_uid = request.args.get('uid') or request.args.get('user_uid')
                cookie_uid = request.cookies.get('huerto_user_uid')
                cookie_data = request.cookies.get('huerto_user_data')
                chosen_uid = from_uid or cookie_uid
                if chosen_uid:
                    import json as _json
                    base = None
                    if cookie_data:
                        try:
                            base = _json.loads(cookie_data)
                        except Exception:
                            base = None
                    session['user_uid'] = chosen_uid
                    session['is_authenticated'] = True
                    # Refrescar/inicializar timestamp
                    try:
                        import time as _t
                        session['login_timestamp'] = int(_t.time())
                    except Exception:
                        pass
                    session['user'] = {
                        'uid': chosen_uid,
                        'email': (base or {}).get('email'),
                        'name': (base or {}).get('name') or ((base or {}).get('email') or 'Usuario'),
                        'plan': (base or {}).get('plan', 'gratuito')
                    }
                    session.modified = True
                    if config_name == 'development':
                        try:
                            print(f"[GLOBAL RECONSTRUCT] Sesión creada desde {'param' if from_uid else 'cookie'} para UID={chosen_uid}")
                        except Exception:
                            pass
        except Exception as _e:
            try:
                print(f"[GLOBAL RECONSTRUCT] Error: {_e}")
            except Exception:
                pass

        # Guardia GLOBAL anti-bucles para rutas protegidas principales
        # Importante: no redirigir si hay indicios de autenticación que el middleware
        # @require_auth pueda usar para reconstruir sesión (cookies/headers/parámetros).
        try:
            path = request.path or ''
            # Tratar config/firebase como público para no contaminar diagnóstico
            if path.startswith('/config/firebase'):
                return None
            is_protected = path.startswith('/crops') or (path.startswith('/analytics') and not path.startswith('/analytics/api'))
            if is_protected:
                # Solo registrar señales; no redirigir desde la guardia global
                dev_token = request.args.get('dev_token')
                has_session = bool(session.get('is_authenticated') and session.get('user_uid'))
                has_auth_header = bool(request.headers.get('Authorization'))
                has_firebase_cookie = 'firebase_id_token' in request.cookies
                has_user_cookie = 'huerto_user_uid' in request.cookies or 'huerto_user_data' in request.cookies
                has_uid_param = bool(request.args.get('uid') or request.args.get('user_uid'))
                came_from_auth = request.args.get('from') in ("login", "register")
                has_session_cookie = app.config.get('SESSION_COOKIE_NAME', 'session') in request.cookies
                wants_json = 'application/json' in (request.headers.get('Accept', '') or '').lower()
                print(f"[GLOBAL GUARD] path={path} endpoint={request.endpoint} dev_token={dev_token} has_session={has_session} auth_header={has_auth_header} firebase_cookie={has_firebase_cookie} user_cookie={has_user_cookie} uid_param={has_uid_param} from_auth={came_from_auth} session_cookie={has_session_cookie} wants_json={wants_json}")
                # Dejar que @require_auth gestione cualquier decisión de auth/redirect
                return None
        except Exception as _e:
            # No bloquear la request por errores en esta guarda
            print(f"[GLOBAL GUARD] Error evaluando guardia: {_e}")
    
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
        
        # FORZAR envío de cookie de sesión en TODAS las respuestas y refrescar timestamp
        session.permanent = True
        if session.get('is_authenticated'):
            try:
                import time as _t
                session['login_timestamp'] = int(_t.time())
            except Exception:
                pass
        session.modified = True
        # Escribir cookies de respaldo con el UID/datos del usuario para reconstrucción en API calls
        try:
            user_uid = session.get('user_uid')
            if user_uid:
                # Cookie con UID del usuario (no HttpOnly para que el frontend pueda leer si fuera necesario)
                response.set_cookie(
                    'huerto_user_uid',
                    value=user_uid,
                    secure=app.config.get('SESSION_COOKIE_SECURE', False),
                    httponly=False,
                    samesite=app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
                    path=app.config.get('SESSION_COOKIE_PATH', '/'),
                    domain=app.config.get('SESSION_COOKIE_DOMAIN')
                )
                # Cookie compacta con datos básicos (para mejorar UX)
                import json as _json
                basic = session.get('user') or {
                    'uid': user_uid,
                    'email': session.get('user_email'),
                    'name': session.get('user_email') or 'Usuario',
                    'plan': session.get('user', {}).get('plan', 'gratuito') if isinstance(session.get('user'), dict) else 'gratuito'
                }
                try:
                    basic_json = _json.dumps({
                        'uid': basic.get('uid') or user_uid,
                        'email': basic.get('email'),
                        'name': basic.get('name'),
                        'plan': basic.get('plan', 'gratuito')
                    }, ensure_ascii=False)
                except Exception:
                    basic_json = _json.dumps({'uid': user_uid})
                response.set_cookie(
                    'huerto_user_data',
                    value=basic_json,
                    secure=app.config.get('SESSION_COOKIE_SECURE', False),
                    httponly=False,
                    samesite=app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
                    path=app.config.get('SESSION_COOKIE_PATH', '/'),
                    domain=app.config.get('SESSION_COOKIE_DOMAIN')
                )
        except Exception as _e:
            try:
                print(f"[AFTER_REQUEST] No se pudieron establecer cookies de respaldo: {_e}")
            except Exception:
                pass

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
    import datetime as _dt
    from flask import request
    
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

    @app.template_filter('format_date')
    def format_date(value, fmt='%d/%m/%Y'):
        """
        Formatea fechas de forma segura para plantillas.
        - Acepta datetime, date, strings ISO y Timestamps de Firestore (con to_datetime()).
        - Si no puede formatear, devuelve el valor original.
        """
        try:
            if value is None or value == '':
                return ''
            # Firestore Timestamp
            if hasattr(value, 'to_datetime') and callable(getattr(value, 'to_datetime')):
                value = value.to_datetime()
            # Strings ISO
            if isinstance(value, str):
                try:
                    value = _dt.datetime.fromisoformat(value)
                except Exception:
                    # No es ISO, devolver tal cual
                    return value
            # date o datetime
            if isinstance(value, (_dt.datetime, _dt.date)):
                # date también soporta strftime
                return value.strftime(fmt)
            # Último recurso: intentar acceder a strftime si existe
            if hasattr(value, 'strftime'):
                return value.strftime(fmt)
        except Exception:
            pass
        return value
    
    @app.context_processor
    def inject_config():
        return {
            'PLAN_GRATUITO': app.config['PLAN_GRATUITO'], 
            'PLAN_PREMIUM': app.config['PLAN_PREMIUM'],
            'timestamp': int(time.time())  # Para versionado de assets
        }

    @app.context_processor
    def inject_user_context():
        """
        Inyecta `user`, `is_authenticated` y `user_display_name` en todas las plantillas.
        - Usa el usuario del middleware/sesión si existe
        - Si no, intenta reconstruir desde la cookie `huerto_user_data`
        """
        # 1) Orígenes posibles del usuario
        try:
            from app.middleware.auth_middleware import get_current_user as _get_user
            user_from_g = _get_user()
        except Exception:
            user_from_g = None
        user_from_session = session.get('user') if 'user' in session else None

        # 2) Leer cookie compacta si existe
        cookie_dict = {}
        try:
            import json as _json
            raw = request.cookies.get('huerto_user_data')
            if raw:
                data = _json.loads(raw)
                if isinstance(data, dict):
                    cookie_dict = data
        except Exception:
            cookie_dict = {}

        # 3) Seleccionar base de usuario (prioridad: sesión → g → cookie)
        u = user_from_session or user_from_g or (
            {
                'uid': cookie_dict.get('uid'),
                'email': cookie_dict.get('email'),
                'name': cookie_dict.get('name'),
                'plan': cookie_dict.get('plan', 'gratuito')
            } if cookie_dict else None
        )

        # 4) Enriquecer campos faltantes (nombre/email) desde sesión/cookie
        if u:
            if not u.get('name'):
                u['name'] = (
                    (user_from_session or {}).get('name')
                    or cookie_dict.get('name')
                    or (user_from_session or {}).get('email')
                    or cookie_dict.get('email')
                    or None
                )
            if not u.get('email'):
                u['email'] = (
                    (user_from_session or {}).get('email')
                    or cookie_dict.get('email')
                    or None
                )

        # 5) Construir nombre a mostrar con prioridad clara (no "Usuario" si hay email)
        display_name = (
            (user_from_session or {}).get('name')
            or (user_from_session or {}).get('email')
            or cookie_dict.get('name')
            or cookie_dict.get('email')
            or ((u or {}).get('name'))
            or ((u or {}).get('email'))
            or 'Usuario'
        )

        return {
            'user': u,
            'is_authenticated': bool(u),
            'user_display_name': display_name,
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
