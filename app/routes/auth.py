"""
Rutas de autenticación
Login, logout, registro con Firebase Auth
"""
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from app.auth.auth_service import AuthService, UserService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página e endpoint de login"""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # POST: Procesar login
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        
        if not id_token:
            return jsonify({'error': 'Token requerido'}), 400
        
        # Verificar token de Firebase
        user_data = AuthService.verify_firebase_token(id_token)
        if not user_data:
            return jsonify({'error': 'Token inválido'}), 401
        
        # Crear o actualizar usuario en Firestore
        from flask import current_app
        user_service = UserService(current_app.db)
        
        existing_user = user_service.get_user_by_uid(user_data['uid'])
        if not existing_user:
            # Crear nuevo usuario
            user_service.create_user(user_data['uid'], user_data)
        else:
            # Actualizar último acceso
            user_service.update_last_access(user_data['uid'])
        
        # Crear token de sesión personalizado
        session_token = AuthService.create_custom_token(user_data)
        
        # Guardar en sesión
        session['token'] = session_token
        session['user_uid'] = user_data['uid']
        
        return jsonify({
            'success': True,
            'token': session_token,
            'user': {
                'uid': user_data['uid'],
                'email': user_data['email'],
                'name': user_data['name']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error en login: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Cerrar sesión"""
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página e endpoint de registro"""
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    # El registro se maneja igual que login
    # Firebase Auth maneja la creación de cuentas
    return login()

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verificar si un token es válido"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'valid': False}), 400
        
        user_data = AuthService.verify_custom_token(token)
        if user_data:
            return jsonify({'valid': True, 'user': user_data})
        else:
            return jsonify({'valid': False}), 401
            
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500
