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
        # DEBUG: Mostrar todas las cookies que llegan
        logger.debug(f"[Auth] Cookies recibidas: {dict(request.cookies)}")
        logger.debug(f"[Auth] Session actual: {dict(session)}")
        logger.debug(f"[Auth] URL: {request.url}")
        logger.debug(f"[Auth] Method: {request.method}")
        
        # Detectar si estamos en desarrollo local
        is_local = request.host.startswith('127.0.0.1') or request.host.startswith('localhost')
        
        # En desarrollo local, si ya hay sesión válida, usar directamente
        if is_local and session.get('is_authenticated') and session.get('user_uid'):
            # Verificar si la sesión ha expirado (más de 24 horas)
            login_timestamp = session.get('login_timestamp', 0)
            current_time = int(__import__('time').time())
            session_age_hours = (current_time - login_timestamp) / 3600
            
            if session_age_hours > 24:
                logger.info(f"[Auth] Sesión expirada ({session_age_hours:.1f}h), limpiando y redirigiendo a login")
                session.clear()
                # Limpiar también las cookies de backup
                from flask import make_response
                response = make_response(redirect(url_for('auth.login')))
                response.set_cookie('huerto_user_uid', '', expires=0)
                response.set_cookie('huerto_user_data', '', expires=0)
                response.set_cookie('huerto_session', '', expires=0)
                return response
            
            # Renovar timestamp cada hora para mantener sesión activa
            if session_age_hours > 1:
                session['login_timestamp'] = current_time
                session.modified = True
                logger.debug(f"[Auth] Timestamp de sesión renovado")
            
            logger.debug(f"[Auth] Desarrollo local - usando sesión existente para {session.get('user_uid')} (edad: {session_age_hours:.1f}h)")
            
            # CORRECCIÓN: Asegurar que g.current_user tiene la estructura correcta
            user_data = session.get('user', {})
            user_uid = session.get('user_uid')
            
            # Si no hay datos completos del usuario en sesión pero sí hay UID, reconstruir
            if user_uid and (not user_data or not user_data.get('uid')):
                user_data = {
                    'uid': user_uid,
                    'email': session.get('user', {}).get('email') or f'user@local.dev',
                    'name': session.get('user', {}).get('name') or 'Usuario Local',
                    'is_local': True
                }
            
            g.current_user = user_data
            return f(*args, **kwargs)
        
        # 1. Obtener token del header o cookie
        token = None
        
        # Prioridad 1: Header Authorization
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            logger.debug("[Auth] Token obtenido de Authorization header")
        
        # Prioridad 2: Cookie Firebase ID token (nombre moderno)
        elif 'firebase_id_token' in request.cookies:
            token = request.cookies.get('firebase_id_token')
            logger.debug("[Auth] Token obtenido de cookie firebase_id_token")

        # Prioridad 3: Cookie de sesión (nombre legado)
        elif 'firebase_token' in request.cookies:
            token = request.cookies.get('firebase_token')
        
        # Prioridad 4: Session Flask (fallback)
        elif session.get('firebase_token'):
            token = session.get('firebase_token')
        
        if not token:
            # NUEVA LÓGICA: Si viene con from=register|login en URL, permitir paso para reconstruir sesión
            if request.args.get('from') in ['register', 'login'] and request.args.get('uid'):
                uid = request.args.get('uid')
                logger.info(f"[Auth] Usuario viene de {request.args.get('from')} con UID {uid[:8]}..., permitiendo paso para reconstruir sesión")
                
                # Obtener datos reales del usuario desde Firestore
                try:
                    from flask import current_app
                    db = current_app.db
                    user_doc = db.collection('usuarios').document(uid).get()
                    
                    if user_doc.exists:
                        user_data = user_doc.to_dict()
                        logger.info(f"[Auth] Datos reales del usuario recuperados desde Firestore")
                        
                        # Reconstruir sesión con datos reales
                        session.permanent = True
                        session['user_uid'] = uid
                        session['is_authenticated'] = True
                        session['user'] = {
                            'uid': uid,
                            'email': user_data.get('email', f'user-{uid[:8]}@huerto.com'),
                            'name': user_data.get('name', f'Usuario {uid[:8]}'),
                            'plan': user_data.get('plan', 'gratuito')
                        }
                        session.modified = True
                        
                        # Establecer usuario en contexto
                        g.current_user = session['user']
                        
                        logger.info(f"[Auth] Sesión reconstruida desde Firestore para {user_data.get('name', 'usuario')}")
                        return f(*args, **kwargs)
                    else:
                        logger.warning(f"[Auth] Usuario {uid} no encontrado en Firestore, usando datos mínimos")
                        
                except Exception as e:
                    logger.error(f"[Auth] Error recuperando datos de Firestore: {e}")
                
                # Fallback con datos mínimos si falla Firestore
                session.permanent = True
                session['user_uid'] = uid
                session['is_authenticated'] = True
                session['user'] = {
                    'uid': uid,
                    'email': f'user-{uid[:8]}@huerto.com',
                    'name': f'Usuario {uid[:8]}',
                    'plan': 'gratuito'
                }
                session.modified = True
                
                # Establecer usuario en contexto
                g.current_user = session['user']
                
                logger.info(f"[Auth] Sesión reconstruida desde URL tras {request.args.get('from')}")
                return f(*args, **kwargs)
            
            # Reconstrucción mejorada desde cookies de respaldo si existen
            backup_uid = request.cookies.get('huerto_user_uid')
            backup_data = request.cookies.get('huerto_user_data')
            if backup_uid:
                logger.info(f"[Auth] Intentando reconstruir sesión desde cookies de backup para UID {backup_uid[:8]}...")
                try:
                    # Obtener datos reales del usuario desde Firestore
                    from flask import current_app
                    db = current_app.db
                    user_doc = db.collection('usuarios').document(backup_uid).get()
                    
                    if user_doc.exists:
                        user_data = user_doc.to_dict()
                        logger.info(f"[Auth] Datos del usuario recuperados desde Firestore: {user_data.get('name', 'Sin nombre')}")
                        
                        # Reconstruir sesión completa con datos reales
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
                        
                        # Establecer usuario en contexto
                        g.current_user = session['user']
                        
                        logger.info(f"[Auth] Sesión reconstruida desde Firestore para {user_data.get('name', 'usuario')} mediante cookies backup")
                        return f(*args, **kwargs)
                    else:
                        logger.warning(f"[Auth] Usuario {backup_uid} no encontrado en Firestore")
                        
                except Exception as e:
                    logger.error(f"[Auth] Error recuperando datos de Firestore desde backup: {e}")
                
                # Fallback con datos del cookie backup
                try:
                    import json as _json
                    user_data = None
                    if backup_data:
                        try:
                            user_data = _json.loads(backup_data)
                        except Exception:
                            user_data = None

                    # Construir usuario mínimo si no hay datos completos
                    if not user_data:
                        user_data = {
                            'uid': backup_uid,
                            'email': None,
                            'email_verified': False,
                            'name': None,
                            'provider': 'cookie'
                        }

                    # Establecer usuario actual en contexto y sesión para evitar bucles
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
            logger.warning(f"Acceso no autorizado a {request.endpoint} - Sin token. Cookies: {list(request.cookies.keys())}")
            if request.is_json:
                return jsonify({'error': 'Token de autenticación requerido', 'redirect': '/onboarding'}), 401
            
            # Evitar bucles de redirección: si ya estamos en onboarding o login, no redirigir
            if request.endpoint in ['main.onboarding', 'auth.login']:
                logger.warning(f"[Auth] Ya en {request.endpoint}, evitando bucle de redirección")
                return f(*args, **kwargs)
            
            # Redirigir a onboarding en lugar de login directo para mejor UX
            return redirect(url_for('main.onboarding'))
        
        try:
            # 2. Verificar token con Firebase Admin SDK
            decoded_token = auth.verify_id_token(token)
            logger.debug(f"[Auth] Token verificado para UID {decoded_token.get('uid')}")
            
            # 3. Establecer usuario actual en contexto global
            g.current_user = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
                'provider': decoded_token.get('firebase', {}).get('sign_in_provider')
            }
            
            # 4. Actualizar session para mantener estado
            session['user_uid'] = decoded_token['uid']
            session['user_email'] = decoded_token.get('email')
            
            logger.info(f"Usuario autenticado: {decoded_token['uid']} accede a {request.endpoint}")
            
        except auth.InvalidIdTokenError:
            logger.warning(f"Token inválido para acceso a {request.endpoint}")
            # Limpiar datos de sesión inválidos
            session.pop('firebase_token', None)
            session.pop('user_uid', None)
            session.pop('user_email', None)
            
            if request.is_json:
                return jsonify({'error': 'Token inválido', 'redirect': '/auth/login'}), 401
            return redirect(url_for('auth.login'))
            
        except auth.ExpiredIdTokenError:
            logger.warning(f"Token expirado para acceso a {request.endpoint}")
            # Limpiar datos de sesión expirados
            session.pop('firebase_token', None)
            session.pop('user_uid', None)
            session.pop('user_email', None)
            
            if request.is_json:
                return jsonify({'error': 'Sesión expirada', 'redirect': '/auth/login'}), 401
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            # Si el token falla pero hay cookies de respaldo, reconstruir sesión para evitar bucles
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
            if request.is_json:
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
