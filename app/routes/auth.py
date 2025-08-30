"""
Rutas de autenticación
Login, logout, registro con Firebase Auth y selección de planes
"""
import datetime
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash, send_from_directory
from app.auth.auth_service import AuthService, UserService
from app.services.plan_service import PlanService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/debug')
def debug_register():
    """Página de debug para registro"""
    try:
        from flask import current_app, send_file
        import os
        
        debug_file = os.path.join(current_app.root_path, '..', 'debug_register.html')
        if os.path.exists(debug_file):
            return send_file(debug_file)
        else:
            return "Archivo de debug no encontrado", 404
    except Exception as e:
        return f"Error cargando debug: {e}", 500

@auth_bp.route('/test-completo')
def test_completo():
    """Página de test completo para registro"""
    try:
        from flask import current_app, send_file
        import os
        
        test_file = os.path.join(current_app.root_path, '..', 'test_registro_completo.html')
        if os.path.exists(test_file):
            return send_file(test_file)
        else:
            return "Archivo de test no encontrado", 404
    except Exception as e:
        return f"Error cargando test: {e}", 500

@auth_bp.route('/test-backend')
def test_backend():
    """Endpoint para probar el backend de Firebase"""
    try:
        from flask import current_app
        import firebase_admin
        from app.auth.auth_service import AuthService
        
        # Test básico
        results = {
            'firebase_apps': len(firebase_admin._apps),
            'firebase_initialized': len(firebase_admin._apps) > 0,
            'timestamp': str(datetime.datetime.now())
        }
        
        # Test de token verification
        try:
            result = AuthService.verify_firebase_token("invalid-token")
            results['token_verification'] = f"Success (result: {result})"
        except Exception as e:
            results['token_verification'] = f"Error: {str(e)}"
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register-simple', methods=['GET'])
def register_simple():
    """Página de registro simplificada para debugging"""
    return render_template('auth/register_simple.html')

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
        session['user'] = {
            'uid': user_data['uid'],
            'email': user_data['email'],
            'name': user_data['name'],
        }
        session['is_authenticated'] = True

        # Limpiar flags de modos especiales para evitar entrar en demo/invitado
        session.pop('demo_mode_chosen', None)
        session.pop('guest_mode_active', None)
        
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
        print("📝 [/auth/register] Solicitud recibida")
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
        session['is_authenticated'] = True

        # Limpiar flags de modos especiales para evitar entrar en demo/invitado
        session.pop('demo_mode_chosen', None)
        session.pop('guest_mode_active', None)

        print("✅ [/auth/register] Registro procesado correctamente")
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
        import traceback
        print(f"❌ [/auth/register] Error en registro: {e}")
        traceback.print_exc()
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
