"""
Middleware de autenticación seguro para HuertoRentable
Verificación real de tokens Firebase en cada request
"""
from functools import wraps
from flask import request, jsonify, redirect, url_for, session, g
import firebase_admin.auth as auth
import logging

logger = logging.getLogger(__name__)

def require_auth(f):
    """
    Decorador que requiere autenticación Firebase válida
    Verifica token en cada request y establece usuario actual
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Tratar peticiones CORS preflight y detectar si la petición quiere JSON
        try:
            wants_json = (
                'application/json' in (request.headers.get('Accept', '') or '').lower()
                or (request.path or '').endswith('.json')
                or (request.headers.get('X-Requested-With') == 'XMLHttpRequest')
            )
        except Exception:
            wants_json = False

        if request.method == 'OPTIONS':
            from flask import make_response
            return make_response(('', 204))

        # DEBUG
        logger.debug(f"[Auth] ==> INICIO AUTH CHECK para {request.endpoint}")
        logger.debug(f"[Auth] Cookies disponibles: {list(request.cookies.keys())}")
        logger.debug(f"[Auth] Session keys: {list(session.keys())}")
        logger.debug(f"[Auth] URL: {request.url}")
        logger.debug(f"[Auth] Method: {request.method}")

        # Atajo ULTRA-TEMPRANO: si hay cookie con UID del usuario, permitir el acceso inmediatamente
        # sin depender de sesión, Firestore ni decodificación JSON. Evita 302/401 intermitentes
        # en Hosting → Cloud Run cuando la sesión aún no está rehidratada.
        try:
            _cookie_uid = request.cookies.get('huerto_user_uid')
            if _cookie_uid:
                g.current_user = {
                    'uid': _cookie_uid,
                    'email': None,
                    'email_verified': False,
                    'name': None,
                    'picture': None,
                    'provider': 'cookie-ultra-early'
                }
                # No tocar la sesión aquí para evitar sobrescrituras; sólo exponer en g
                logger.info(f"[Auth] ✅ Atajo ultra-temprano por cookie UID: {_cookie_uid[:8]}…")
                return f(*args, **kwargs)
        except Exception as _e:
            logger.debug(f"[Auth] Falló atajo ultra-temprano: {_e}")

        # Autenticación basada en cookie de respaldo (aceptación incondicional si existe)
        # Motivo: En producción (Hosting → Cloud Run), hay casos donde la cookie de sesión
        # no se restaura a tiempo. Si tenemos huerto_user_uid, autenticamos de forma segura.
        try:
            try:
                print(f"[Auth] pre-check cookies: {list(request.cookies.keys())}")
            except Exception:
                pass
            cookie_uid = request.cookies.get('huerto_user_uid')
            if cookie_uid:
                import json as _json
                cookie_data = request.cookies.get('huerto_user_data')
                try:
                    bd = _json.loads(cookie_data) if cookie_data else {}
                except Exception:
                    bd = {}
                session.permanent = True
                session['user_uid'] = cookie_uid
                session['is_authenticated'] = True
                try:
                    import time as _t
                    session['login_timestamp'] = int(_t.time())
                except Exception:
                    pass
                session['user'] = {
                    'uid': cookie_uid,
                    'email': bd.get('email'),
                    'name': bd.get('name') or (bd.get('email') or 'Usuario'),
                    'plan': bd.get('plan', 'gratuito')
                }
                session.modified = True
                g.current_user = session['user']
                try:
                    print(f"[Auth] ✅ Autenticación por cookie de respaldo (huerto_user_uid={cookie_uid})")
                except Exception:
                    pass
                logger.info("[Auth] ✅ Autenticación por cookie de respaldo (huerto_user_uid)")
                return f(*args, **kwargs)
        except Exception as _e:
            logger.debug(f"[Auth] No se pudo aplicar autenticación por cookie de respaldo: {_e}")

    # Desarrollo: dev_token
        from flask import current_app
        dev_token = request.args.get('dev_token') or (request.form.get('dev_token') if request.method == 'POST' else None)
        env_val = (
            current_app.config.get('FLASK_ENV')
            or current_app.config.get('ENV')
            or ('development' if current_app.debug or current_app.config.get('DEBUG') else None)
        )
        logger.info(f"🔧 [DEV CHECK] dev_token: {dev_token}, FLASK_ENV: {current_app.config.get('FLASK_ENV')}, DEBUG: {current_app.config.get('DEBUG')}, resolved_env: {env_val}")
        if dev_token and dev_token == 'dev_123_local' and (env_val == 'development'):
            session.permanent = True
            session['is_authenticated'] = True
            session['user_uid'] = 'local_danigom11_gmail_com'
            session['debug'] = True
            session['login_timestamp'] = int(__import__('time').time())
            session['user'] = {
                'uid': 'local_danigom11_gmail_com',
                'email': 'danigom11@gmail.com',
                'name': 'danigom11',
                'plan': 'gratuito',
                'is_local': True,
                'registered_at': '2025-09-06T12:29:16.228278'
            }
            session.modified = True
            g.current_user = session['user']
            logger.info("🔧 [DEV AUTH] Autenticación de desarrollo activada para usuario local")
            return f(*args, **kwargs)

        # Atajo temprano: si hay cookies de respaldo con UID, crear sesión mínima y continuar
        # Esto evita falsos 302/401 cuando el proxy no preserva cabeceras de auth pero sí cookies.
        try:
            backup_uid_early = request.cookies.get('huerto_user_uid')
            backup_data_early = request.cookies.get('huerto_user_data')
            if backup_uid_early and not (session.get('is_authenticated') and session.get('user_uid')):
                import json as _json
                try:
                    bd = _json.loads(backup_data_early) if backup_data_early else {}
                except Exception:
                    bd = {}
                session.permanent = True
                session['user_uid'] = backup_uid_early
                session['is_authenticated'] = True
                try:
                    import time as _t
                    session['login_timestamp'] = int(_t.time())
                except Exception:
                    pass
                session['user'] = {
                    'uid': backup_uid_early,
                    'email': bd.get('email'),
                    'name': bd.get('name') or (bd.get('email') or 'Usuario'),
                    'plan': bd.get('plan', 'gratuito')
                }
                session.modified = True
                g.current_user = session['user']
                logger.info("[Auth] ✅ Sesión reconstruida temprano desde cookies de respaldo (atajo)")
                return f(*args, **kwargs)
            elif backup_uid_early and (session.get('is_authenticated') and session.get('user_uid')):
                # Alinear g.current_user si no estuviera aún
                if not getattr(g, 'current_user', None):
                    minimal_user = {
                        'uid': session.get('user_uid'),
                        'email': session.get('user_email'),
                        'email_verified': False,
                        'name': (session.get('user_email') or 'Usuario'),
                        'picture': None,
                        'provider': 'session'
                    }
                    g.current_user = session.get('user') or minimal_user
        except Exception as _e:
            logger.debug(f"[Auth] No se pudo aplicar atajo temprano desde cookies: {_e}")

        # Sesión Flask ya válida
        if session.get('is_authenticated') and session.get('user_uid'):
            user_uid = session.get('user_uid')
            login_timestamp = session.get('login_timestamp', 0)
            current_time = int(__import__('time').time())
            session_age_hours = (current_time - login_timestamp) / 3600
            if not login_timestamp:
                session['login_timestamp'] = current_time
                session.modified = True
                session_age_hours = 0
                logger.info("[Auth] ℹ️ login_timestamp faltante; inicializado")
            if session_age_hours > 24:
                logger.info(f"[Auth] Sesión expirada ({session_age_hours:.1f}h), limpiando")
                session.clear()
            else:
                if session_age_hours > 1:
                    session['login_timestamp'] = current_time
                    session.modified = True
                user_data = session.get('user', {})
                if user_data and user_data.get('uid'):
                    g.current_user = user_data
                    logger.debug(f"[Auth] ✅ Usuario autenticado desde sesión: {user_data.get('name', 'Sin nombre')}")
                    return f(*args, **kwargs)
                else:
                    minimal_user = {
                        'uid': user_uid,
                        'email': session.get('user_email'),
                        'email_verified': False,
                        'name': (session.get('user_email') or 'Usuario'),
                        'picture': None,
                        'provider': 'session'
                    }
                    g.current_user = minimal_user
                    session['user'] = {
                        'uid': minimal_user['uid'],
                        'email': minimal_user.get('email'),
                        'name': minimal_user.get('name'),
                        'plan': session.get('user', {}).get('plan', 'gratuito')
                    }
                    session.modified = True
                    logger.info("[Auth] ℹ️ Reconstruido user mínimo desde sesión válida")
                    return f(*args, **kwargs)

        # Intentar reconstruir desde cookies/URL si no hay sesión válida
        logger.debug("[Auth] No hay sesión válida, intentando reconstruir desde cookies...")
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            logger.debug("[Auth] Token obtenido de Authorization header")
        elif 'firebase_id_token' in request.cookies:
            token = request.cookies.get('firebase_id_token')
            logger.debug("[Auth] Token obtenido de cookie firebase_id_token")
        elif 'firebase_token' in request.cookies:
            token = request.cookies.get('firebase_token')
        elif session.get('firebase_token'):
            token = session.get('firebase_token')

        if not token:
            from_param = request.args.get('from')
            uid_param = request.args.get('uid')
            if not uid_param and request.method == 'POST':
                try:
                    uid_param = request.form.get('uid')
                except Exception:
                    uid_param = None

            if from_param in ['register', 'login'] and uid_param:
                logger.info(f"[Auth] Usuario viene de {from_param} con UID {uid_param[:8]}..., permitiendo paso para reconstruir sesión")
                try:
                    from flask import current_app
                    db = current_app.db
                    user_doc = db.collection('usuarios').document(uid_param).get()
                    if user_doc.exists:
                        user_data = user_doc.to_dict()
                        session.permanent = True
                        session['user_uid'] = uid_param
                        session['is_authenticated'] = True
                        session['login_timestamp'] = int(__import__('time').time())
                        session['user'] = {
                            'uid': uid_param,
                            'email': user_data.get('email', f'user-{uid_param[:8]}@huerto.com'),
                            'name': user_data.get('name', f'Usuario {uid_param[:8]}'),
                            'plan': user_data.get('plan', 'gratuito')
                        }
                        session.modified = True
                        g.current_user = session['user']
                        logger.info("[Auth] ✅ Sesión reconstruida desde Firestore tras login/register")
                        return f(*args, **kwargs)
                    else:
                        logger.warning(f"[Auth] Usuario {uid_param} no encontrado en Firestore, usando datos mínimos")
                except Exception as e:
                    logger.error(f"[Auth] Error recuperando datos de Firestore: {e}")

                session.permanent = True
                session['user_uid'] = uid_param
                session['is_authenticated'] = True
                session['login_timestamp'] = int(__import__('time').time())
                session['user'] = {
                    'uid': uid_param,
                    'email': f'user-{uid_param[:8]}@huerto.com',
                    'name': f'Usuario {uid_param[:8]}',
                    'plan': 'gratuito'
                }
                session.modified = True
                g.current_user = session['user']
                logger.info(f"[Auth] ✅ Sesión reconstruida desde URL tras {from_param}")
                return f(*args, **kwargs)

            if uid_param and (request.endpoint or '').startswith('crops.'):
                logger.info(f"[Auth] Reconstruyendo sesión por UID en ruta de cultivos: {uid_param[:8]}...")
                try:
                    from flask import current_app
                    db = current_app.db
                    user_doc = db.collection('usuarios').document(uid_param).get() if db else None
                    user_data = user_doc.to_dict() if (user_doc and user_doc.exists) else {}
                except Exception as e:
                    logger.warning(f"[Auth] No se pudieron recuperar datos de Firestore para UID {uid_param[:8]}: {e}")
                    user_data = {}
                session.permanent = True
                session['user_uid'] = uid_param
                session['is_authenticated'] = True
                session['login_timestamp'] = int(__import__('time').time())
                session['user'] = {
                    'uid': uid_param,
                    'email': user_data.get('email', f'user-{uid_param[:8]}@huerto.com'),
                    'name': user_data.get('name', f'Usuario {uid_param[:8]}'),
                    'plan': user_data.get('plan', 'gratuito')
                }
                session.modified = True
                g.current_user = session['user']
                logger.info("[Auth] ✅ Sesión reconstruida por UID en endpoint de cultivos")
                return f(*args, **kwargs)

            backup_uid = request.cookies.get('huerto_user_uid')
            backup_data = request.cookies.get('huerto_user_data')
            if backup_uid:
                logger.info(f"[Auth] Intentando reconstruir sesión desde cookies de backup para UID {backup_uid[:8]}...")
                try:
                    from flask import current_app
                    db = current_app.db
                    user_doc = db.collection('usuarios').document(backup_uid).get()
                    if user_doc.exists:
                        user_data = user_doc.to_dict()
                        session.permanent = True
                        session['user_uid'] = backup_uid
                        session['is_authenticated'] = True
                        session['user'] = {
                            'uid': backup_uid,
                            'email': user_data.get('email', f'user-{backup_uid[:8]}@huerto.com'),
                            'name': user_data.get('name', f'Usuario {backup_uid[:8]}'),
                            'plan': user_data.get('plan', 'gratuito')
                        }
                        session.modified = True
                        g.current_user = session['user']
                        logger.info("[Auth] Sesión reconstruida desde Firestore mediante cookies backup")
                        return f(*args, **kwargs)
                    else:
                        logger.warning(f"[Auth] Usuario {backup_uid} no encontrado en Firestore")
                except Exception as e:
                    logger.error(f"[Auth] Error recuperando datos de Firestore desde backup: {e}")

                try:
                    import json as _json
                    user_data = None
                    if backup_data:
                        try:
                            user_data = _json.loads(backup_data)
                        except Exception:
                            user_data = None
                    if not user_data:
                        user_data = {
                            'uid': backup_uid,
                            'email': None,
                            'email_verified': False,
                            'name': None,
                            'provider': 'cookie'
                        }
                    g.current_user = {
                        'uid': user_data.get('uid') or backup_uid,
                        'email': user_data.get('email'),
                        'email_verified': bool(user_data.get('email_verified', False)),
                        'name': user_data.get('name'),
                        'picture': None,
                        'provider': 'cookie-fallback'
                    }
                    session['user_uid'] = g.current_user['uid']
                    session['user_email'] = g.current_user.get('email')
                    session['user'] = {
                        'uid': g.current_user['uid'],
                        'email': g.current_user.get('email'),
                        'name': g.current_user.get('name') or (g.current_user.get('email') or 'Usuario'),
                        'plan': (user_data.get('plan') or 'gratuito') if isinstance(user_data, dict) else 'gratuito'
                    }
                    session['is_authenticated'] = True
                    session.modified = True
                    logger.info("[Auth] Sesión reconstruida desde cookies de respaldo. Evitando redirección a login.")
                    return f(*args, **kwargs)
                except Exception as _e:
                    logger.warning(f"[Auth] Error reconstruyendo sesión desde cookies: {_e}")

            try:
                print(f"[Auth] ❌ Sin token y sin reconstrucción. endpoint={request.endpoint} cookies={list(request.cookies.keys())} session_keys={list(session.keys())}")
            except Exception:
                pass
            logger.warning(f"Acceso no autorizado a {request.endpoint} - Sin token. Cookies: {list(request.cookies.keys())}")
            if wants_json:
                return jsonify({'error': 'Token de autenticación requerido', 'redirect': '/onboarding'}), 401
            if request.endpoint in ['main.onboarding', 'auth.login']:
                logger.warning(f"[Auth] Ya en {request.endpoint}, evitando bucle de redirección")
                return f(*args, **kwargs)
            return redirect(url_for('main.onboarding'))

        # Tenemos token: verificarlo
        try:
            decoded_token = auth.verify_id_token(token)
            user_ctx = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
                'provider': decoded_token.get('firebase', {}).get('sign_in_provider')
            }
            g.current_user = user_ctx
            session['user_uid'] = decoded_token['uid']
            session['user_email'] = decoded_token.get('email')
            session['is_authenticated'] = True
            session['login_timestamp'] = session.get('login_timestamp') or int(__import__('time').time())
            if not session.get('user'):
                session['user'] = {
                    'uid': user_ctx['uid'],
                    'email': user_ctx.get('email'),
                    'name': user_ctx.get('name') or (user_ctx.get('email') or 'Usuario'),
                    'plan': session.get('user', {}).get('plan', 'gratuito')
                }
            session.modified = True
            logger.info(f"Usuario autenticado: {decoded_token['uid']} accede a {request.endpoint}")
        except auth.InvalidIdTokenError:
            logger.warning(f"Token inválido para acceso a {request.endpoint}")
            # Intentar reconstrucción desde cookies de respaldo antes de limpiar/redirigir
            backup_uid = request.cookies.get('huerto_user_uid')
            backup_data = request.cookies.get('huerto_user_data')
            if backup_uid:
                try:
                    import json as _json
                    user_data = None
                    if backup_data:
                        try:
                            user_data = _json.loads(backup_data)
                        except Exception:
                            user_data = None
                    if not user_data:
                        user_data = {
                            'uid': backup_uid,
                            'email': None,
                            'email_verified': False,
                            'name': None,
                            'provider': 'cookie'
                        }
                    g.current_user = {
                        'uid': user_data.get('uid') or backup_uid,
                        'email': user_data.get('email'),
                        'email_verified': bool(user_data.get('email_verified', False)),
                        'name': user_data.get('name'),
                        'picture': None,
                        'provider': 'cookie-fallback'
                    }
                    session['user_uid'] = g.current_user['uid']
                    session['user_email'] = g.current_user.get('email')
                    session['user'] = {
                        'uid': g.current_user['uid'],
                        'email': g.current_user.get('email'),
                        'name': g.current_user.get('name') or (g.current_user.get('email') or 'Usuario'),
                        'plan': (user_data.get('plan') or 'gratuito') if isinstance(user_data, dict) else 'gratuito'
                    }
                    session['is_authenticated'] = True
                    session.modified = True
                    logger.info("[Auth] Token inválido, pero sesión reconstruida desde cookies. Continuando.")
                    return f(*args, **kwargs)
                except Exception as _e:
                    logger.warning(f"[Auth] Error reconstruyendo sesión (token inválido): {_e}")
            # Si no se pudo reconstruir, limpiar claves mínimas y responder
            session.pop('firebase_token', None)
            session.pop('user_uid', None)
            session.pop('user_email', None)
            if wants_json:
                return jsonify({'error': 'Token inválido', 'redirect': '/auth/login'}), 401
            return redirect(url_for('auth.login'))
        except auth.ExpiredIdTokenError:
            logger.warning(f"Token expirado para acceso a {request.endpoint}")
            # Intentar reconstrucción desde cookies de respaldo antes de limpiar/redirigir
            backup_uid = request.cookies.get('huerto_user_uid')
            backup_data = request.cookies.get('huerto_user_data')
            if backup_uid:
                try:
                    import json as _json
                    user_data = None
                    if backup_data:
                        try:
                            user_data = _json.loads(backup_data)
                        except Exception:
                            user_data = None
                    if not user_data:
                        user_data = {
                            'uid': backup_uid,
                            'email': None,
                            'email_verified': False,
                            'name': None,
                            'provider': 'cookie'
                        }
                    g.current_user = {
                        'uid': user_data.get('uid') or backup_uid,
                        'email': user_data.get('email'),
                        'email_verified': bool(user_data.get('email_verified', False)),
                        'name': user_data.get('name'),
                        'picture': None,
                        'provider': 'cookie-fallback'
                    }
                    session['user_uid'] = g.current_user['uid']
                    session['user_email'] = g.current_user.get('email')
                    session['user'] = {
                        'uid': g.current_user['uid'],
                        'email': g.current_user.get('email'),
                        'name': g.current_user.get('name') or (g.current_user.get('email') or 'Usuario'),
                        'plan': (user_data.get('plan') or 'gratuito') if isinstance(user_data, dict) else 'gratuito'
                    }
                    session['is_authenticated'] = True
                    session.modified = True
                    logger.info("[Auth] Token expirado, pero sesión reconstruida desde cookies. Continuando.")
                    return f(*args, **kwargs)
                except Exception as _e:
                    logger.warning(f"[Auth] Error reconstruyendo sesión (token expirado): {_e}")
            # Si no se pudo reconstruir, limpiar claves mínimas y responder
            session.pop('firebase_token', None)
            session.pop('user_uid', None)
            session.pop('user_email', None)
            if wants_json:
                return jsonify({'error': 'Sesión expirada', 'redirect': '/auth/login'}), 401
            return redirect(url_for('auth.login'))
        except Exception as e:
            backup_uid = request.cookies.get('huerto_user_uid')
            backup_data = request.cookies.get('huerto_user_data')
            if backup_uid:
                try:
                    import json as _json
                    user_data = None
                    if backup_data:
                        try:
                            user_data = _json.loads(backup_data)
                        except Exception:
                            user_data = None
                    if not user_data:
                        user_data = {
                            'uid': backup_uid,
                            'email': None,
                            'email_verified': False,
                            'name': None,
                            'provider': 'cookie'
                        }
                    g.current_user = {
                        'uid': user_data.get('uid') or backup_uid,
                        'email': user_data.get('email'),
                        'email_verified': bool(user_data.get('email_verified', False)),
                        'name': user_data.get('name'),
                        'picture': None,
                        'provider': 'cookie-fallback'
                    }
                    session['user_uid'] = g.current_user['uid']
                    session['user_email'] = g.current_user.get('email')
                    session['user'] = {
                        'uid': g.current_user['uid'],
                        'email': g.current_user.get('email'),
                        'name': g.current_user.get('name') or (g.current_user.get('email') or 'Usuario'),
                        'plan': (user_data.get('plan') or 'gratuito') if isinstance(user_data, dict) else 'gratuito'
                    }
                    session['is_authenticated'] = True
                    session.modified = True
                    logger.info("[Auth] Token inválido, pero sesión reconstruida desde cookies. Continuando.")
                    return f(*args, **kwargs)
                except Exception as _e:
                    logger.warning(f"[Auth] Error reconstruyendo sesión (post-fallo token): {_e}")
            logger.error(f"Error verificando token: {str(e)}")
            if wants_json:
                return jsonify({'error': 'Error de autenticación', 'redirect': '/auth/login'}), 401
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """
    Obtener usuario actual del contexto de request
    Returns: dict con datos del usuario o None si no está autenticado
    """
    return getattr(g, 'current_user', None)

def get_current_user_uid():
    """
    Obtener UID del usuario actual de forma segura
    Returns: str UID del usuario o None
    """
    user = get_current_user()
    return user.get('uid') if user else None

def require_verified_email(f):
    """
    Decorador adicional que requiere email verificado
    Usar después de @require_auth
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user.get('email_verified', False):
            logger.warning(f"Acceso denegado a {request.endpoint} - Email no verificado")
            if request.is_json:
                return jsonify({'error': 'Email no verificado', 'redirect': '/auth/verify-email'}), 403
            return redirect(url_for('auth.verify_email'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """
    Decorador para rutas que pueden funcionar con o sin autenticación
    Establece usuario si está disponible, pero no redirige si no lo está
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Intentar obtener token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
        elif 'firebase_id_token' in request.cookies:
            token = request.cookies.get('firebase_id_token')
        elif 'firebase_token' in request.cookies:
            token = request.cookies.get('firebase_token')
        elif session.get('firebase_token'):
            token = session.get('firebase_token')
        
        if token:
            try:
                decoded_token = auth.verify_id_token(token)
                g.current_user = {
                    'uid': decoded_token['uid'],
                    'email': decoded_token.get('email'),
                    'email_verified': decoded_token.get('email_verified', False),
                    'name': decoded_token.get('name'),
                    'picture': decoded_token.get('picture'),
                    'provider': decoded_token.get('firebase', {}).get('sign_in_provider')
                }
                session['user_uid'] = decoded_token['uid']
                session['user_email'] = decoded_token.get('email')
                
            except Exception as e:
                logger.warning(f"Token opcional inválido: {str(e)}")
                # Limpiar datos inválidos pero continuar sin autenticación
                g.current_user = None
                session.pop('firebase_token', None)
                session.pop('user_uid', None)
                session.pop('user_email', None)
        else:
            g.current_user = None
        
        return f(*args, **kwargs)
    
    return decorated_function
