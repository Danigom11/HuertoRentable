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
            logger.warning(f"Acceso no autorizado a {request.endpoint} - Sin token. Cookies: {list(request.cookies.keys())}")
            if request.is_json:
                return jsonify({'error': 'Token de autenticación requerido', 'redirect': '/auth/login'}), 401
            return redirect(url_for('auth.login'))
        
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
    return user['uid'] if user else None

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
