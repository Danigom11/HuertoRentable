"""
Sistema de autenticación con Firebase Auth y JWT
Manejo de usuarios, sesiones y planes de suscripción
"""
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, session, current_app, g
from firebase_admin import auth as firebase_auth

class AuthService:
    """Servicio de autenticación centralizado"""
    
    @staticmethod
    def verify_firebase_token(id_token):
        """
        Verificar token de Firebase Authentication
        
        Args:
            id_token (str): Token ID de Firebase
            
        Returns:
            dict: Información del usuario o None si es inválido
        """
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            return {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture')
            }
        except Exception as e:
            print(f"Error verificando token Firebase: {e}")
            return None
    
    @staticmethod
    def create_custom_token(user_data):
        """
        Crear token JWT personalizado para sesiones
        
        Args:
            user_data (dict): Datos del usuario
            
        Returns:
            str: Token JWT
        """
        payload = {
            'uid': user_data['uid'],
            'email': user_data['email'],
            'plan': user_data.get('plan', 'gratuito'),
            'exp': datetime.datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'iat': datetime.datetime.utcnow()
        }
        
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_custom_token(token):
        """
        Verificar token JWT personalizado
        
        Args:
            token (str): Token JWT
            
        Returns:
            dict: Datos del usuario o None si es inválido
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

class UserService:
    """Servicio de gestión de usuarios"""
    
    def __init__(self, db):
        self.db = db
    
    def get_user_by_uid(self, uid):
        """
        Obtener usuario por UID de Firebase
        
        Args:
            uid (str): UID del usuario
            
        Returns:
            dict: Datos del usuario o None
        """
        try:
            if not self.db:
                return None
                
            doc_ref = self.db.collection('usuarios').document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            print(f"Error obteniendo usuario: {e}")
            return None
    
    def create_user(self, uid, user_data):
        """
        Crear nuevo usuario en Firestore
        
        Args:
            uid (str): UID del usuario
            user_data (dict): Datos del usuario
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            if not self.db:
                return False
                
            user_doc = {
                'uid': uid,
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'picture': user_data.get('picture'),
                'plan': 'gratuito',
                'fecha_registro': datetime.datetime.utcnow(),
                'ultimo_acceso': datetime.datetime.utcnow(),
                'configuracion': {
                    'notificaciones': True,
                    'analytics': True,
                    'backup_automatico': True
                }
            }
            
            self.db.collection('usuarios').document(uid).set(user_doc)
            return True
            
        except Exception as e:
            print(f"Error creando usuario: {e}")
            return False
    
    def update_last_access(self, uid):
        """Actualizar último acceso del usuario"""
        try:
            if not self.db:
                return
                
            self.db.collection('usuarios').document(uid).update({
                'ultimo_acceso': datetime.datetime.utcnow()
            })
            
        except Exception as e:
            print(f"Error actualizando último acceso: {e}")
    
    def get_user_plan(self, uid):
        """
        Obtener plan de suscripción del usuario
        
        Args:
            uid (str): UID del usuario
            
        Returns:
            str: Nombre del plan ('invitado', 'gratuito', 'premium')
        """
        user = self.get_user_by_uid(uid)
        if user:
            return user.get('plan', 'gratuito')
        return 'invitado'
    
    def upgrade_to_premium(self, uid):
        """Actualizar usuario a plan premium"""
        try:
            if not self.db:
                return False
                
            self.db.collection('usuarios').document(uid).update({
                'plan': 'premium',
                'fecha_upgrade': datetime.datetime.utcnow()
            })
            return True
            
        except Exception as e:
            print(f"Error actualizando a premium: {e}")
            return False

# Decoradores de autenticación
def login_required(f):
    """Decorador para rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Buscar token en headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Token malformado'}), 401
        
        # Buscar token en session
        elif 'token' in session:
            token = session['token']
        
        if not token:
            return jsonify({'error': 'Token requerido'}), 401
        
        # Verificar token
        user_data = AuthService.verify_custom_token(token)
        if not user_data:
            return jsonify({'error': 'Token inválido'}), 401
        
        # Añadir usuario al contexto global
        g.current_user = user_data
        
        return f(*args, **kwargs)
    
    return decorated_function

def premium_required(f):
    """Decorador para rutas que requieren plan premium"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user'):
            return jsonify({'error': 'Autenticación requerida'}), 401
        
        # Verificar plan del usuario en base de datos
        from flask import current_app
        user_service = UserService(current_app.db)
        plan = user_service.get_user_plan(g.current_user['uid'])
        
        if plan != 'premium':
            return jsonify({'error': 'Suscripción premium requerida'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Obtener usuario actual del contexto"""
    return getattr(g, 'current_user', None)
