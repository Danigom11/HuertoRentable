"""
Rutas de autenticación
Login, logout, registro con Firebase Auth y selección de planes
"""
import datetime
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash
from app.auth.auth_service import AuthService, UserService
from app.services.plan_service import PlanService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/plans')
def plan_selection():
    """Página de selección de planes"""
    try:
        from flask import current_app
        plan_service = PlanService(current_app.db)
        plans = plan_service.get_available_plans()
        
        return render_template('auth/plan_selection.html', plans=plans)
        
    except Exception as e:
        print(f"Error cargando selección de planes: {e}")
        return redirect(url_for('main.onboarding'))

@auth_bp.route('/guest')
def activate_guest_mode():
    """Activar modo invitado directamente (enlace directo)"""
    try:
        from flask import current_app
        plan_service = PlanService(current_app.db)
        
        # Crear ID de sesión de invitado
        guest_id = plan_service.create_guest_session()
        
        # Configurar sesión local
        session['user'] = {
            'uid': guest_id,
            'email': 'invitado@local',
            'name': 'Usuario Invitado', 
            'plan': 'invitado',
            'isGuest': True,
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        
        # Marcar modo invitado activo
        session['guest_mode_active'] = True
        
        flash('¡Modo invitado activado! Tus datos se guardan localmente en este navegador.', 'info')
        return redirect(url_for('main.dashboard', mode='guest'))
        
    except Exception as e:
        print(f"Error activando modo invitado: {e}")
        flash('Error al activar modo invitado. Inténtalo de nuevo.', 'error')
        return redirect(url_for('auth.plan_selection'))

@auth_bp.route('/guest-mode', methods=['POST'])
def create_guest_mode():
    """Crear sesión de modo invitado"""
    try:
        from flask import current_app
        plan_service = PlanService(current_app.db)
        
        # Crear ID de sesión de invitado
        guest_id = plan_service.create_guest_session()
        
        # Configurar sesión local
        session['user'] = {
            'uid': guest_id,
            'email': 'invitado@local',
            'name': 'Usuario Invitado',
            'plan': 'invitado',
            'isGuest': True,
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': 'Sesión de invitado creada',
            'redirect': url_for('main.dashboard')
        })
        
    except Exception as e:
        print(f"Error creando sesión de invitado: {e}")
        return jsonify({'error': 'Error creando sesión'}), 500

@auth_bp.route('/sync-user', methods=['POST'])
def sync_user():
    """Sincronizar usuario de Firebase con Firestore"""
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
            print(f"🆕 Creando nuevo usuario en Firestore: {user_data['uid']}")
            user_service.create_user(user_data['uid'], user_data)
        else:
            # Usuario ya existe
            print(f"✅ Usuario ya existe en Firestore: {user_data['uid']}")
        
        return jsonify({
            'success': True,
            'user': user_data,
            'created': not existing_user
        })
        
    except Exception as e:
        print(f"Error sincronizando usuario: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

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

@auth_bp.route('/upgrade-plan', methods=['POST'])
def upgrade_plan():
    """Actualizar plan de usuario"""
    try:
        if 'user' not in session:
            return jsonify({'error': 'Usuario no autenticado'}), 401
        
        data = request.get_json()
        new_plan = data.get('plan')
        
        if new_plan not in ['gratuito', 'premium']:
            return jsonify({'error': 'Plan inválido'}), 400
        
        user_uid = session['user']['uid']
        
        # Si es usuario invitado, no puede cambiar plan
        if session['user'].get('isGuest'):
            return jsonify({'error': 'Los usuarios invitados no pueden cambiar de plan'}), 400
        
        # Actualizar plan
        from flask import current_app
        plan_service = PlanService(current_app.db)
        
        if plan_service.upgrade_user_plan(user_uid, new_plan):
            # Actualizar sesión
            session['user']['plan'] = new_plan
            
            return jsonify({
                'success': True,
                'message': f'Plan actualizado a {new_plan}',
                'new_plan': new_plan
            })
        else:
            return jsonify({'error': 'Error actualizando plan'}), 500
            
    except Exception as e:
        print(f"Error actualizando plan: {e}")
        return jsonify({'error': 'Error interno'}), 500

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página e endpoint de registro con selección de plan"""
    if request.method == 'GET':
        # Obtener plan seleccionado de la URL
        selected_plan = request.args.get('plan', 'gratuito')
        
        # Validar plan
        if selected_plan not in ['gratuito', 'premium']:
            selected_plan = 'gratuito'
        
        return render_template('auth/register.html', selected_plan=selected_plan)
    
    # POST: Procesar registro
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        selected_plan = data.get('plan', 'gratuito')
        
        if not id_token:
            return jsonify({'error': 'Token requerido'}), 400
        
        # Validar plan seleccionado
        if selected_plan not in ['gratuito', 'premium']:
            selected_plan = 'gratuito'
        
        # Verificar token de Firebase
        user_data = AuthService.verify_firebase_token(id_token)
        if not user_data:
            return jsonify({'error': 'Token inválido'}), 401
        
        # Añadir plan seleccionado a los datos del usuario
        user_data['plan'] = selected_plan
        
        # Crear usuario en Firestore con el plan seleccionado
        from flask import current_app
        user_service = UserService(current_app.db)
        
        existing_user = user_service.get_user_by_uid(user_data['uid'])
        if not existing_user:
            # Crear nuevo usuario con plan seleccionado
            print(f"🆕 Creando usuario con plan '{selected_plan}': {user_data['uid']}")
            user_service.create_user(user_data['uid'], user_data)
        
        # Crear token de sesión
        session_token = AuthService.create_custom_token(user_data)
        
        # Guardar en sesión
        session['token'] = session_token
        session['user_uid'] = user_data['uid']
        session['user'] = {
            'uid': user_data['uid'],
            'email': user_data['email'],
            'name': user_data['name'],
            'plan': selected_plan
        }
        
        return jsonify({
            'success': True,
            'token': session_token,
            'user': {
                'uid': user_data['uid'],
                'email': user_data['email'],
                'name': user_data['name'],
                'plan': selected_plan
            },
            'message': f'Cuenta creada con plan {selected_plan}'
        })
        
    except Exception as e:
        print(f"Error en registro: {e}")
        return jsonify({'error': f'Error en registro: {str(e)}'}), 500

@auth_bp.route('/register-local', methods=['POST'])
def register_local():
    """Registro local sin Firebase para modo demo mejorado"""
    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name', email.split('@')[0] if email else 'Usuario')
        
        if not email:
            return jsonify({'error': 'Email requerido'}), 400
        
        # Crear usuario local en sesión
        user_data = {
            'uid': f"local_{email.replace('@', '_').replace('.', '_')}",
            'email': email,
            'name': name,
            'plan': 'gratuito',
            'registered_at': datetime.datetime.now().isoformat(),
            'is_local': True
        }
        
        # Guardar en sesión
        session['user'] = user_data
        session['user_uid'] = user_data['uid']
        session['is_authenticated'] = True
        
        return jsonify({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Error en registro: {str(e)}'}), 500

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
