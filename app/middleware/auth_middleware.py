"""
Middleware de autenticación automática
Verifica tokens Firebase en cada request para mantener sesiones consistentes
"""
from flask import request, session, g
from app.auth.auth_service import AuthService

def auto_auth_middleware(app):
    """
    Middleware que automáticamente verifica tokens Firebase en requests
    """
    @app.before_request
    def verify_firebase_auth():
        """Verificar autenticación Firebase en cada request"""
        
        # Saltar verificación para rutas estáticas y de autenticación
        if (request.endpoint and 
            (request.endpoint.startswith('static') or 
             request.endpoint in ['auth.register', 'auth.login'] or
             request.path.startswith('/static/') or
             request.path.startswith('/service-worker'))):
            return
        
        # Si ya hay usuario en la sesión, no hacer nada
        if session.get('is_authenticated') and session.get('user'):
            return
        
        # Buscar token Firebase en headers o cookies
        auth_header = request.headers.get('Authorization')
        firebase_token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            firebase_token = auth_header.replace('Bearer ', '')
        else:
            # Buscar en cookies de Firebase
            firebase_token = request.cookies.get('firebase_id_token')
        
        if firebase_token:
            try:
                # Verificar token de Firebase
                user_data = AuthService.verify_firebase_token(firebase_token)
                if user_data:
                    # Crear sesión automáticamente
                    session['token'] = AuthService.create_custom_token(user_data)
                    session['user_uid'] = user_data['uid']
                    session['user'] = {
                        'uid': user_data['uid'],
                        'email': user_data['email'],
                        'name': user_data.get('name', user_data['email'].split('@')[0])
                    }
                    session['is_authenticated'] = True
                    
                    print(f"✅ [Auto-Auth] Sesión creada automáticamente para: {user_data['uid']}")
                    
            except Exception as e:
                print(f"❌ [Auto-Auth] Error verificando token: {e}")
                pass  # Continuar sin autenticación
