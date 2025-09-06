"""
Rutas de autenticación
Login, logout, registro con Firebase Auth y selección de planes
"""
import datetime
import time
import json
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash, send_from_directory, make_response
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

@auth_bp.route('/debug-cultivos-page')
def debug_cultivos_page():
    """Página de debug para cultivos"""
    try:
        from flask import current_app, send_file
        import os
        
        debug_file = os.path.join(current_app.root_path, '..', 'debug_cultivos.html')
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

@auth_bp.route('/test-crear-cultivo', methods=['POST'])
def test_crear_cultivo():
    """Endpoint para probar la creación de cultivos directamente"""
    try:
        from flask import current_app
        from app.services.crop_service import CropService
        from app.auth.auth_service import UserService
        
        # Simular usuario autenticado
        test_uid = "test_user_real"
        
        # Datos del cultivo
        crop_data = {
            'nombre': request.form.get('nombre', 'tomates test'),
            'precio': float(request.form.get('precio', 3.5)),
            'numero_plantas': int(request.form.get('numero_plantas', 10))
        }
        
        print(f"🧪 Test crear cultivo para UID: {test_uid}")
        print(f"🌱 Datos: {crop_data}")
        
        # Asegurar que el usuario existe
        user_service = UserService(current_app.db)
        user = user_service.get_user_by_uid(test_uid)
        
        if not user:
            print("📝 Creando usuario de prueba...")
            user_data = {
                'uid': test_uid,
                'email': 'test@real.com',
                'name': 'Test User Real',
                'plan': 'gratuito'
            }
            created = user_service.create_user(test_uid, user_data)
            print(f"Usuario creado: {created}")
        
        # Crear cultivo
        crop_service = CropService(current_app.db)
        success = crop_service.create_crop(test_uid, crop_data)
        
        return jsonify({
            'success': success,
            'message': 'Cultivo creado exitosamente' if success else 'Error al crear cultivo',
            'uid': test_uid,
            'crop_data': crop_data
        })
        
    except Exception as e:
        import traceback
        print(f"Error en test crear cultivo: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@auth_bp.route('/debug-cultivo')
def debug_cultivo():
    """Endpoint para diagnosticar problemas de creación de cultivos"""
    try:
        from flask import current_app
        from app.services.crop_service import CropService
        from app.auth.auth_service import UserService
        from app.services.plan_service import PlanService
        
        results = {}
        
        # Estado básico
        results['firebase_connected'] = current_app.db is not None
        results['timestamp'] = str(datetime.datetime.now())
        
        if not current_app.db:
            results['error'] = 'No hay conexión a Firebase'
            return jsonify(results)
        
        # Datos de prueba
        test_uid = "debug_user_123"
        crop_data = {
            'nombre': 'tomates debug',
            'precio': 3.50,
            'numero_plantas': 10
        }
        
        # Servicios
        user_service = UserService(current_app.db)
        crop_service = CropService(current_app.db)
        plan_service = PlanService(current_app.db)
        
        # Test 1: Verificar usuario
        user = user_service.get_user_by_uid(test_uid)
        results['user_exists'] = user is not None
        
        if not user:
            # Crear usuario de prueba
            user_data = {
                'uid': test_uid,
                'email': 'debug@test.com',
                'name': 'Debug User',
                'plan': 'gratuito'
            }
            created = user_service.create_user(test_uid, user_data)
            results['user_created'] = created
        
        # Test 2: Verificar plan
        plan = user_service.get_user_plan(test_uid)
        results['user_plan'] = plan
        
        # Test 3: Verificar límites
        can_create = plan_service.check_plan_limits(test_uid, 'crops')
        results['can_create_crops'] = can_create
        
        # Test 4: Obtener cultivos existentes
        existing_crops = crop_service.get_user_crops(test_uid)
        results['existing_crops_count'] = len(existing_crops)
        
        # Test 5: Intentar crear cultivo
        try:
            success = crop_service.create_crop(test_uid, crop_data)
            results['crop_creation_success'] = success
            
            if success:
                updated_crops = crop_service.get_user_crops(test_uid)
                results['crops_after_creation'] = len(updated_crops)
            
        except Exception as e:
            results['crop_creation_error'] = str(e)
            import traceback
            results['crop_creation_traceback'] = traceback.format_exc()
        
        return jsonify(results)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
    """Endpoint para diagnosticar problemas de creación de cultivos"""
    try:
        from flask import current_app
        from app.services.crop_service import CropService
        from app.auth.auth_service import UserService
        from app.services.plan_service import PlanService
        
        results = {}
        
        # Estado básico
        results['firebase_connected'] = current_app.db is not None
        results['timestamp'] = str(datetime.datetime.now())
        
        if not current_app.db:
            results['error'] = 'No hay conexión a Firebase'
            return jsonify(results)
        
        # Datos de prueba
        test_uid = "debug_user_123"
        crop_data = {
            'nombre': 'tomates debug',
            'precio': 3.50,
            'numero_plantas': 10
        }
        
        # Servicios
        user_service = UserService(current_app.db)
        crop_service = CropService(current_app.db)
        plan_service = PlanService(current_app.db)
        
        # Test 1: Verificar usuario
        user = user_service.get_user_by_uid(test_uid)
        results['user_exists'] = user is not None
        
        if not user:
            # Crear usuario de prueba
            user_data = {
                'uid': test_uid,
                'email': 'debug@test.com',
                'name': 'Debug User',
                'plan': 'gratuito'
            }
            created = user_service.create_user(test_uid, user_data)
            results['user_created'] = created
        
        # Test 2: Verificar plan
        plan = user_service.get_user_plan(test_uid)
        results['user_plan'] = plan
        
        # Test 3: Verificar límites
        can_create = plan_service.check_plan_limits(test_uid, 'crops')
        results['can_create_crops'] = can_create
        
        # Test 4: Obtener cultivos existentes
        existing_crops = crop_service.get_user_crops(test_uid)
        results['existing_crops_count'] = len(existing_crops)
        
        # Test 5: Intentar crear cultivo
        try:
            success = crop_service.create_crop(test_uid, crop_data)
            results['crop_creation_success'] = success
            
            if success:
                updated_crops = crop_service.get_user_crops(test_uid)
                results['crops_after_creation'] = len(updated_crops)
            
        except Exception as e:
            results['crop_creation_error'] = str(e)
            import traceback
            results['crop_creation_traceback'] = traceback.format_exc()
        
        return jsonify(results)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

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
    """Sincronizar usuario de Firebase con Firestore y crear sesión persistente"""
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
        
        # FORZAR CREACIÓN DE SESIÓN AGRESIVA
        session.permanent = True
        session.clear()  # Limpiar sesión anterior
        
        # Crear datos de usuario completos
        user_session_data = {
            'uid': user_data['uid'],
            'email': user_data['email'],
            'name': user_data.get('name', user_data['email'].split('@')[0]),
            'plan': user_data.get('plan', 'gratuito'),
            'created_at': user_data.get('created_at'),
            'last_login': user_data.get('last_login')
        }
        
        # Establecer múltiples formas de identificación
        session['user'] = user_session_data
        session['is_authenticated'] = True
        session['user_uid'] = user_data['uid']
        session['firebase_uid'] = user_data['uid']
        session['auth_method'] = 'firebase'
        session['login_timestamp'] = int(time.time())
        session.permanent = True  # Asegurar que la sesión es permanente
        
        # Forzar modificación de sesión
        session.modified = True
        
        print(f"✅ [sync-user] Sesión creada para {user_data['uid']}")
        print(f"🔍 [sync-user] Session data: {dict(session)}")
        
        # Crear respuesta con cookie adicional como backup
        response = make_response(jsonify({
            'success': True,
            'user': user_data,
            'created': not existing_user,
            'session_created': True,
            'redirect_url': f'/dashboard?from=register&welcome=true&uid={user_data["uid"]}'
        }))
        
        # FORZAR cookies de sesión manualmente
        import uuid
        session_id = str(uuid.uuid4())
        
        # Cookie de sesión Flask (forzar escritura)
        response.set_cookie(
            'huerto_session',
            session_id,
            max_age=86400,  # 24 horas
            secure=False,   # False para desarrollo
            httponly=False, # Permitir JS
            samesite='Lax',
            path='/'
        )
        
        # Cookie adicional como backup
        response.set_cookie(
            'huerto_user_uid',
            user_data['uid'],
            max_age=86400,  # 24 horas
            secure=False,   # False para desarrollo
            httponly=False, # Permitir JS
            samesite='Lax',
            path='/'
        )
        
        # Cookie con datos completos del usuario
        import json
        user_cookie_data = json.dumps({
            'uid': user_data['uid'],
            'email': user_data['email'],
            'name': user_data.get('name', user_data['email'].split('@')[0]),
            'plan': user_data.get('plan', 'gratuito'),
            'authenticated': True
        })
        
        response.set_cookie(
            'huerto_user_data',
            user_cookie_data,
            max_age=86400,  # 24 horas
            secure=False,   # False para desarrollo
            httponly=False, # Permitir JS
            samesite='Lax',
            path='/'
        )
        
        # También soportar flujo tradicional: si el cliente no espera JSON, redirigir
        if request.headers.get('Accept', '').startswith('text/html'):
            return redirect(f"/dashboard?from=register&welcome=true&uid={user_data['uid']}")
        return response
        
    except Exception as e:
        print(f"❌ Error sincronizando usuario: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error interno del servidor'}), 500

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página e endpoint de login"""
    if request.method == 'GET':
        # Verificar si viene del registro sin sesión
        message = request.args.get('message')
        if message == 'complete_auth':
            flash('Por favor, inicia sesión para completar el proceso de registro.', 'info')
        
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
        
        # Guardar en sesión y hacer permanente
        session.permanent = True
        session['token'] = session_token
        session['user_uid'] = user_data['uid']
        session['user'] = {
            'uid': user_data['uid'],
            'email': user_data['email'],
            'name': user_data.get('name', user_data['email'].split('@')[0]),
        }
        session['is_authenticated'] = True
        # IMPORTANTE: Añadir timestamp para el middleware de autenticación
        session['login_timestamp'] = int(time.time())

        # Debug: Verificar que la sesión se guardó
        print(f"🔍 [Login] Sesión creada: {dict(session)}")

        # Limpiar flags de modos especiales para evitar entrar en demo/invitado
        session.pop('demo_mode_chosen', None)
        session.pop('guest_mode_active', None)
        
        # Preparar respuesta JSON y setear cookies de respaldo
        response = make_response(jsonify({
            'success': True,
            'token': session_token,
            'user': {
                'uid': user_data['uid'],
                'email': user_data['email'],
                'name': user_data.get('name', user_data['email'].split('@')[0])
            }
        }))

        import uuid, json as _json
        from flask import request as _req
        
        # Detectar si estamos en HTTPS (producción) o HTTP (desarrollo)
        is_production = (request.is_secure or 
                        request.headers.get('X-Forwarded-Proto') == 'https' or
                        'run.app' in request.host or
                        not request.host.startswith(('localhost', '127.0.0.1')))
        
        print(f"🔍 [Login] Entorno detectado: {'PRODUCCIÓN (HTTPS)' if is_production else 'DESARROLLO (HTTP)'}")
        
        session_id = str(uuid.uuid4())
        
        # Configurar cookies con parámetros correctos según entorno
        cookie_secure = is_production
        cookie_samesite = 'Lax'  # Funciona tanto en HTTP como HTTPS
        
        response.set_cookie('huerto_session', session_id, 
                          max_age=86400, secure=cookie_secure, 
                          httponly=True, samesite=cookie_samesite, path='/')
        response.set_cookie('huerto_user_uid', user_data['uid'], 
                          max_age=86400, secure=cookie_secure, 
                          httponly=True, samesite=cookie_samesite, path='/')
        response.set_cookie('huerto_user_data', _json.dumps({
            'uid': user_data['uid'],
            'email': user_data['email'],
            'name': user_data.get('name', user_data['email'].split('@')[0]),
            'plan': 'gratuito',
            'authenticated': True
        }), max_age=86400, secure=cookie_secure, 
           httponly=True, samesite=cookie_samesite, path='/')
        
        # Token Firebase
        try:
            id_token_val = data.get('idToken')
            if id_token_val:
                response.set_cookie('firebase_id_token', id_token_val,
                                  max_age=3600, secure=cookie_secure,
                                  httponly=True, samesite=cookie_samesite, path='/')
                print(f"✅ [Login] Token Firebase guardado en cookie")
        except Exception as e:
            print(f"⚠️ [Login] Error guardando token Firebase: {e}")

        session.permanent = True
        session.modified = True

        # SOLUCIÓN ANTI-BUCLE: Las cookies no viajan por el proxy Hosting→Cloud Run
        # Hacer redirect directo del servidor tras establecer sesión
        print(f"✅ [login] Sesión creada exitosamente en servidor, redirigiendo a dashboard")
        
        # Si es request AJAX/JSON, devolver JSON con redirect_url
        if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
            return jsonify({
                'success': True,
                'token': session_token,
                'user': {
                    'uid': user_data['uid'],
                    'email': user_data['email'],
                    'name': user_data.get('name', user_data['email'].split('@')[0])
                },
                'redirect_url': f"/dashboard?from=login&uid={user_data['uid']}"
            })
        
        # Si es request HTML normal, hacer redirect DIRECTO del servidor
        return redirect(f"/dashboard?from=login&uid={user_data['uid']}")

        if request.headers.get('Accept', '').startswith('text/html'):
            return redirect(f"/dashboard?from=login&uid={user_data['uid']}")
        return response
        
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

@auth_bp.route('/test-cookie-simple', methods=['POST'])
def test_cookie_simple():
    """Test ultra simple para verificar cookies desde Hosting→Cloud Run"""
    try:
        # Crear una respuesta que establezca cookies básicas
        response = make_response(jsonify({
            'message': 'Test cookie establecida',
            'timestamp': str(datetime.datetime.now()),
            'received_cookies': dict(request.cookies),
            'host': request.host
        }))
        
        # Establecer cookies con diferentes configuraciones
        response.set_cookie('test_basic', 'valor1', max_age=3600, path='/')
        response.set_cookie('test_lax', 'valor2', max_age=3600, path='/', samesite='Lax')
        response.set_cookie('test_none_secure', 'valor3', max_age=3600, path='/', 
                           samesite='None', secure=True)
        
        # También establecer la sesión Flask agresivamente
        session.permanent = True
        session['test_cookie_time'] = str(datetime.datetime.now())
        session.modified = True
        
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página e endpoint de registro con selección de plan"""
    if request.method == 'GET':
        # Obtener plan seleccionado de la URL
        selected_plan = request.args.get('plan', 'gratuito')
        
        # Validar plan
        if selected_plan not in ['gratuito', 'premium']:
            selected_plan = 'gratuito'
        
        print(f"DEBUG: Pasando 'plan={selected_plan}' a register.html")
        return render_template('auth/register.html', plan=selected_plan)
    
    # POST: Procesar registro
    try:
        print("📝 [/auth/register] Solicitud recibida")
        data = request.get_json()
        print(f"🔍 [Debug] Datos recibidos: {data}")
        id_token = data.get('idToken')
        selected_plan = data.get('plan', 'gratuito')
        display_name = data.get('displayName', '')  # ✅ Capturar displayName del frontend
        
        print(f"🔍 [Debug] displayName extraído: '{display_name}'")
        
        if not id_token:
            return jsonify({'error': 'Token requerido'}), 400
        
        # Validar plan seleccionado
        if selected_plan not in ['gratuito', 'premium']:
            selected_plan = 'gratuito'
        
        # Verificar token de Firebase
        user_data = AuthService.verify_firebase_token(id_token)
        if not user_data:
            return jsonify({'error': 'Token inválido'}), 401
        
        # Sobrescribir con el nombre del formulario si se proporcionó
        if display_name.strip():
            user_data['name'] = display_name.strip()
            print(f"✅ Usando nombre del formulario: {display_name.strip()}")
        else:
            print(f"⚠️ No se proporcionó displayName, usando: {user_data.get('name', 'Sin nombre')}")
        
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

        # Guardar en sesión y hacer permanente
        session.permanent = True
        session['token'] = session_token
        session['user_uid'] = user_data['uid']
        session['user'] = {
            'uid': user_data['uid'],
            'email': user_data['email'],
            'name': user_data.get('name', user_data['email'].split('@')[0]),
            'plan': selected_plan
        }
        session['is_authenticated'] = True

        # Debug: Verificar que la sesión se guardó
        print(f"🔍 [Register] Sesión creada: {dict(session)}")

        # Limpiar flags de modos especiales para evitar entrar en demo/invitado
        session.pop('demo_mode_chosen', None)
        session.pop('guest_mode_active', None)

        print("✅ [/auth/register] Registro procesado correctamente")
        # Preparar respuesta JSON
        response = make_response(jsonify({
            'success': True,
            'token': session_token,
            'user': {
                'uid': user_data['uid'],
                'email': user_data['email'],
                'name': user_data.get('name', user_data['email'].split('@')[0]),
                'plan': selected_plan
            },
            'message': f'Cuenta creada con plan {selected_plan}',
            'redirect_url': f"/dashboard?from=register&welcome=true&uid={user_data['uid']}"
        }))

    # Establecer cookies de respaldo para navegadores con problemas de sesión
        import uuid, json as _json
        session_id = str(uuid.uuid4())
        response.set_cookie('huerto_session', session_id, max_age=86400, secure=False, httponly=False, samesite='Lax', path='/')
        response.set_cookie('huerto_user_uid', user_data['uid'], max_age=86400, secure=False, httponly=False, samesite='Lax', path='/')
        response.set_cookie('huerto_user_data', _json.dumps({
                'uid': user_data['uid'],
                'email': user_data['email'],
                'name': user_data.get('name', user_data['email'].split('@')[0]),
                'plan': selected_plan,
                'authenticated': True
        }), max_age=86400, secure=False, httponly=False, samesite='Lax', path='/')
        # Si el frontend nos envió id_token, guardarlo también para reconstrucción
        try:
            id_token_val = data.get('idToken')
            if id_token_val:
                from flask import request as _req
                host = _req.host.split(':')[0]
                is_local = host in ('localhost', '127.0.0.1') or host.endswith('.local')
                response.set_cookie(
                    'firebase_id_token',
                    id_token_val,
                    max_age=3600,
                    secure=not is_local,
                    httponly=False,
                    samesite='Lax' if is_local else 'None',
                    path='/'
                )
        except Exception:
            pass
        session.permanent = True
        session.modified = True

        # SOLUCIÓN ANTI-BUCLE: Las cookies no viajan por el proxy Hosting→Cloud Run
        # En lugar de depender de cookies, hacer redirect directo del servidor
        print(f"✅ [register] Sesión creada exitosamente en servidor, redirigiendo a dashboard")
        
        # Si es request AJAX/JSON, devolver JSON con redirect_url
        if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
            return jsonify({
                'success': True,
                'token': session_token,
                'user': {
                    'uid': user_data['uid'],
                    'email': user_data['email'],
                    'name': user_data.get('name', user_data['email'].split('@')[0]),
                    'plan': selected_plan
                },
                'message': f'Cuenta creada con plan {selected_plan}',
                'redirect_url': f"/dashboard?from=register&welcome=true&uid={user_data['uid']}"
            })
        
        # Si es request HTML normal, hacer redirect DIRECTO del servidor (sin depender del frontend)
        return redirect(f"/dashboard?from=register&welcome=true&uid={user_data['uid']}")

        return response

    except Exception as e:
        import traceback
        print(f"❌ [/auth/register] Error en registro: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Error en registro: {str(e)}'}), 500

@auth_bp.route('/test-simple-session', methods=['GET', 'POST'])
def test_simple_session():
    """
    Test ultra simple de sesión con formulario HTML normal
    Para debuggear si el problema es con AJAX o con las sesiones en general
    """
    if request.method == 'GET':
        # Mostrar formulario simple
        return '''
        <html>
        <head><title>Test Sesión</title></head>
        <body>
            <h1>Test de Sesión Simple</h1>
            <form method="POST">
                <input type="text" name="test_value" placeholder="Escribe algo" required>
                <button type="submit">Crear Sesión</button>
            </form>
            <hr>
            <a href="/auth/test-check-session">Ver Sesión Actual</a>
        </body>
        </html>
        '''
    
    # POST: Crear sesión
    test_value = request.form.get('test_value', 'valor por defecto')
    
    # Crear sesión de test
    session.permanent = True
    session['test_data'] = test_value
    session['timestamp'] = str(datetime.datetime.now())
    session['is_test'] = True
    session.modified = True
    
    print(f"🧪 [TEST-SIMPLE] Sesión creada: {dict(session)}")
    
    return f'''
    <html>
    <head><title>Sesión Creada</title></head>
    <body>
        <h1>✅ Sesión Creada</h1>
        <p>Valor guardado: {test_value}</p>
        <p>Timestamp: {session.get('timestamp')}</p>
        <hr>
        <a href="/auth/test-check-session">Ver Sesión Actual</a><br>
        <a href="/dashboard">Ir al Dashboard</a>
    </body>
    </html>
    '''

@auth_bp.route('/test-check-session')
def test_check_session():
    """Verificar el estado actual de la sesión"""
    session_data = dict(session)
    
    print(f"🔍 [CHECK-SESSION] Sesión actual: {session_data}")
    
    return f'''
    <html>
    <head><title>Estado de Sesión</title></head>
    <body>
        <h1>Estado Actual de la Sesión</h1>
        <pre>{json.dumps(session_data, indent=2, default=str)}</pre>
        <hr>
        <a href="/auth/test-simple-session">Crear Nueva Sesión</a><br>
        <a href="/dashboard">Ir al Dashboard</a>
    </body>
    </html>
    '''

@auth_bp.route('/test-session-flow', methods=['POST'])
def test_session_flow():
    """
    Endpoint para probar el flujo completo de sesión sin Firebase real
    Simula el registro completo y verifica la persistencia de sesión
    """
    try:
        print("🧪 [TEST-SESSION-FLOW] Iniciando test de sesión completa")
        
        # Simular datos de usuario como si vinieran de Firebase
        fake_user_data = {
            'uid': 'test-user-123',
            'email': 'test@huertorentable.com',
            'name': 'Usuario Test',
            'email_verified': True
        }
        
        selected_plan = 'premium'
        
        # Simular token de sesión
        session_token = f"session-token-{int(time.time())}"
        
        # Crear sesión exactamente como en el registro real
        session.permanent = True
        session['token'] = session_token
        session['user_uid'] = fake_user_data['uid']
        session['user'] = {
            'uid': fake_user_data['uid'],
            'email': fake_user_data['email'],
            'name': fake_user_data.get('name', fake_user_data['email'].split('@')[0]),
            'plan': selected_plan
        }
        session['is_authenticated'] = True
        
        # Limpiar flags de modo especial
        session.pop('demo_mode_chosen', None)
        session.pop('guest_mode_active', None)
        
        # Forzar modificación de sesión
        session.modified = True
        
        print(f"🔍 [TEST] Sesión creada: {dict(session)}")
        
        # Crear respuesta con middleware
        response_data = {
            'success': True,
            'test_mode': True,
            'message': 'Sesión de test creada exitosamente',
            'session_created': dict(session),
            'next_step': 'Hacer GET a /dashboard para verificar persistencia'
        }
        
        response = jsonify(response_data)
        response = make_response(response)
        
        print(f"✅ [TEST] Respuesta de test preparada")
        
        return response
        
    except Exception as e:
        import traceback
        print(f"❌ [TEST] Error en test de sesión: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Error en test: {str(e)}'}), 500

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
        session.permanent = True
        session['user'] = user_data
        session['user_uid'] = user_data['uid']
        session['is_authenticated'] = True
        # IMPORTANTE: Añadir timestamp para el middleware de autenticación
        session['login_timestamp'] = int(time.time())
        session.modified = True
        
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
