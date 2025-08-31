"""
Rutas principales de la aplicación
Dashboard, onboarding y páginas principales
"""
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, make_response
from app.auth.auth_service import get_current_user, UserService
from app.services.crop_service import CropService
from app.utils.helpers import get_plan_limits as get_plan_config
import time

main_bp = Blueprint('main', __name__)

@main_bp.route('/diagnostico-firebase')
def diagnostico_firebase():
    """Página de diagnóstico para Firebase"""
    return render_template('diagnostico_firebase.html')

@main_bp.route('/firebase-test-clean')
def firebase_test_clean():
    """Página de test limpia para Firebase"""
    return render_template('firebase_test_clean.html')

@main_bp.route('/test-completo')
def test_completo():
    """Página de test completo del sistema"""
    return render_template('test_completo.html')

@main_bp.route('/test-session')
def test_session():
    """Test de sesión para debug"""
    from flask import session, request
    from app.auth.auth_service import get_current_user
    
    user = get_current_user()
    
    return jsonify({
        'session': dict(session),
        'cookies': dict(request.cookies),
        'current_user': user,
        'is_authenticated': session.get('is_authenticated', False),
        'user_uid': session.get('user_uid'),
        'has_token': 'token' in session
    })

@main_bp.route('/ping')
def ping():
    """Endpoint simple para verificar conectividad"""
    return "PONG - Servidor funcionando correctamente"

@main_bp.route('/debug/session')
def debug_session():
    """Debug detallado de sesión"""
    import time
    
    data = {
        'timestamp': time.time(),
        'session_data': dict(session),
        'cookies': dict(request.cookies),
        'is_authenticated': session.get('is_authenticated', False),
        'user_uid': session.get('user_uid'),
        'user_data': session.get('user'),
        'headers': dict(request.headers),
        'method': request.method,
        'url': request.url,
        'has_firebase_token': 'firebase_id_token' in request.cookies,
        'has_user_cookie': 'huerto_user_uid' in request.cookies
    }
    
    return jsonify(data)

@main_bp.route('/debug/force-session')
def force_session():
    """Forzar creación de sesión para debug"""
    session.permanent = True
    session['debug'] = True
    session['test_user'] = {
        'uid': 'test123',
        'email': 'test@test.com',
        'name': 'Test User'
    }
    session['is_authenticated'] = True
    session.modified = True
    
    return jsonify({
        'message': 'Sesión forzada creada',
        'session': dict(session)
    })

@main_bp.route('/test-registro-manual')
def test_registro_manual():
    """Página de test para registro manual simplificado"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Registro Manual</title>
        <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .log { background: #f0f0f0; padding: 10px; margin: 10px 0; border-left: 3px solid #007bff; }
            .success { border-color: #28a745; background: #d4edda; }
            .error { border-color: #dc3545; background: #f8d7da; }
            input, button { padding: 8px; margin: 5px; }
            button { background: #007bff; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>🧪 Test de Registro Manual</h1>
        
        <div>
            <h3>1. Datos del Usuario</h3>
            <input type="email" id="email" placeholder="Email" value="test@huerto.com">
            <input type="password" id="password" placeholder="Password" value="password123">
            <input type="text" id="name" placeholder="Nombre" value="Usuario Test">
            <br>
            <button onclick="testRegister()">Registrar Usuario</button>
            <button onclick="checkSession()">Ver Sesión</button>
            <button onclick="goToDashboard()">Ir al Dashboard</button>
        </div>
        
        <div id="logs"></div>
        
        <script>
            // Configuración Firebase - Cargar desde el backend
            let firebaseConfig = {};
            
            // Cargar configuración Firebase desde el servidor
            fetch('/config/firebase')
                .then(response => response.json())
                .then(config => {
                    firebaseConfig = config;
                    log(`✅ Configuración Firebase cargada: ${config.projectId}`, 'success');
                    firebase.initializeApp(firebaseConfig);
                })
                .catch(error => {
                    log(`❌ Error cargando configuración Firebase: ${error.message}`, 'error');
                });
            
            function log(message, type = 'log') {
                const logs = document.getElementById('logs');
                const div = document.createElement('div');
                div.className = `log ${type}`;
                div.innerHTML = `[${new Date().toLocaleTimeString()}] ${message}`;
                logs.appendChild(div);
                console.log(message);
            }
            
            async function testRegister() {
                try {
                    // Verificar que Firebase esté inicializado
                    if (!firebase.apps.length) {
                        log('⏳ Esperando inicialización de Firebase...', 'error');
                        setTimeout(testRegister, 1000);
                        return;
                    }
                    
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const name = document.getElementById('name').value;
                    
                    log(`🚀 Iniciando registro para: ${email}`);
                    
                    // 1. Registrar en Firebase Auth
                    const userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);
                    const user = userCredential.user;
                    log(`✅ Usuario creado en Firebase: ${user.uid}`, 'success');
                    
                    // 2. Actualizar perfil
                    await user.updateProfile({ displayName: name });
                    log(`✅ Perfil actualizado: ${name}`, 'success');
                    
                    // 3. Obtener token
                    const idToken = await user.getIdToken();
                    log(`✅ Token obtenido: ${idToken.substring(0, 20)}...`, 'success');
                    
                    // 4. Guardar token como cookie
                    document.cookie = `firebase_id_token=${idToken}; path=/; max-age=3600; SameSite=Lax`;
                    log(`✅ Token guardado como cookie`, 'success');
                    
                    // 5. Sincronizar con backend
                    const syncResponse = await fetch('/auth/sync-user', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({ idToken })
                    });
                    
                    const syncResult = await syncResponse.json();
                    log(`✅ Sincronización: ${JSON.stringify(syncResult)}`, 'success');
                    
                    if (syncResult.session_created) {
                        log(`🎉 Sesión creada en el servidor`, 'success');
                    }
                    
                    // 6. Verificar sesión inmediatamente después
                    await checkSession();
                    
                    // 7. REDIRECCIÓN DIRECTA al dashboard (sin pasar por /)
                    const redirectUrl = `/dashboard?from=register&welcome=true&uid=${user.uid}`;
                    log(`🎯 Redirigiendo DIRECTAMENTE a: ${redirectUrl}`, 'success');
                    
                    // Delay más corto para mantener el contexto
                    setTimeout(() => {
                        window.location.href = redirectUrl;
                    }, 500);
                    
                } catch (error) {
                    log(`❌ Error: ${error.message}`, 'error');
                    console.error(error);
                }
            }
            
            async function checkSession() {
                try {
                    const response = await fetch('/debug/session', { credentials: 'include' });
                    const data = await response.json();
                    log(`📊 Sesión: ${JSON.stringify(data, null, 2)}`);
                } catch (error) {
                    log(`❌ Error verificando sesión: ${error.message}`, 'error');
                }
            }
            
            function goToDashboard() {
                window.location.href = '/dashboard';
            }
        </script>
    </body>
    </html>
    '''

@main_bp.route('/test-firebase-config')
def test_firebase_config():
    """Página de test detallado para Firebase Config"""
    return render_template('test_firebase_config.html')

@main_bp.route('/login')
def login_redirect():
    """Redireccionar desde /login a /auth/login para compatibilidad"""
    return redirect(url_for('auth.login'))

@main_bp.route('/register')
def register_redirect():
    """Redireccionar desde /register a /auth/register para compatibilidad"""
    return redirect(url_for('auth.register'))
#     return redirect(url_for('auth.register'))

@main_bp.route('/clear-session')
def clear_session():
    """Limpiar sesión problemática - útil para resolver loops de login"""
    session.clear()
    return redirect(url_for('main.dashboard'))

@main_bp.route('/manifest.json')
def manifest():
    """Servir el manifest de PWA"""
    from flask import send_from_directory, current_app
    import os
    
    # Buscar manifest.json en el directorio raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return send_from_directory(project_root, 'manifest.json', mimetype='application/json')

@main_bp.route('/service-worker.js')
def service_worker():
    """Servir el service worker para PWA"""
    from flask import send_from_directory, current_app
    import os
    
    # Buscar service-worker.js en el directorio raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return send_from_directory(project_root, 'service-worker.js', mimetype='application/javascript')

@main_bp.route('/version')
def check_version():
    """Endpoint para verificar versión actual - solo para información"""
    current_version = "v2.2"  # Versión fija, cambiar solo en actualizaciones reales
    response = make_response(jsonify({
        'version': current_version,
        'timestamp': int(time.time()),
        'force_reload': False  # No forzar reload automático
    }))
    
    # Headers para evitar cache
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache' 
    response.headers['Expires'] = '0'
    
    return response

@main_bp.route('/config/firebase')
def firebase_web_config():
    """Devolver configuración Firebase Web para el frontend"""
    from flask import current_app
    cfg = current_app.config
    return jsonify({
        'apiKey': cfg.get('FIREBASE_WEB_API_KEY'),
        'authDomain': cfg.get('FIREBASE_AUTH_DOMAIN'),
        'projectId': cfg.get('FIREBASE_PROJECT_ID'),
        'storageBucket': cfg.get('FIREBASE_STORAGE_BUCKET'),
        'messagingSenderId': cfg.get('FIREBASE_MESSAGING_SENDER_ID'),
        'appId': cfg.get('FIREBASE_APP_ID'),
    })

@main_bp.route('/')
def home():
    """Página principal - redirecciona según estado del usuario"""
    
    # DEBUG: Log de la petición
    print(f"🔍 [HOME] Request args: {dict(request.args)}")
    print(f"🔍 [HOME] Session: {dict(session)}")
    print(f"🔍 [HOME] Cookies: {dict(request.cookies)}")
    
    # PRIORIDAD MÁXIMA: Si viene del registro, ir directo al dashboard
    if (request.args.get('from') == 'register' or 
        request.referrer and 'register' in request.referrer):
        print("🎯 [HOME] Usuario viene del registro - redirigir a dashboard")
        return redirect(url_for('main.dashboard', **request.args))
    
    # 1) Priorizar sesión de Flask (reciente tras registro/login)
    if session.get('is_authenticated') and session.get('user'):
        print("✅ [HOME] Usuario autenticado en sesión - ir a dashboard")
        return redirect(url_for('main.dashboard'))

    # 2) Fallback: obtener usuario desde helper (token Firebase o g.current_user)
    user = get_current_user()
    if user:
        print("✅ [HOME] Usuario detectado por helper - ir a dashboard")
        return redirect(url_for('main.dashboard'))
    
    # 3) Si hay cookie de usuario, ir al dashboard
    if request.cookies.get('huerto_user_uid') or request.cookies.get('firebase_id_token'):
        print("✅ [HOME] Cookie de usuario detectada - ir a dashboard")
        return redirect(url_for('main.dashboard'))
    
    # CAMBIO: Por defecto ir al onboarding para mejor UX
    # Solo ir directo al dashboard si explícitamente han elegido demo
    if session.get('demo_mode_chosen') or request.args.get('demo') == 'true':
        print("✅ [HOME] Modo demo - ir a dashboard")
        return redirect(url_for('main.dashboard', **request.args))
    
    # Primera visita o sin elección → onboarding
    print("❌ [HOME] No hay usuario - ir a onboarding")
    return redirect(url_for('main.onboarding'))

@main_bp.route('/onboarding')
def onboarding():
    """Pantallas de onboarding para nuevos usuarios"""
    return render_template('onboarding/welcome.html')

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard principal - funciona para usuarios autenticados y modo demo"""
    from flask import current_app, session
    from app.services.crop_service import CropService
    
    # Debug: Verificar estado de la sesión
    print(f"🔍 [Dashboard] Session: {dict(session)}")
    print(f"🔍 [Dashboard] Request args: {dict(request.args)}")
    print(f"🔍 [Dashboard] Cookies: {dict(request.cookies)}")
    
    user = None
    
    # 1) MÁXIMA PRIORIDAD: Viene del registro - esto tiene precedencia sobre todo
    if request.args.get('from') == 'register' and request.args.get('uid'):
        uid = request.args.get('uid')
        print(f"🔍 [Dashboard] Viene del registro con UID: {uid}")
        
        # EN LUGAR DE BUSCAR COOKIES, USAR EL UID DIRECTAMENTE
        # Si viene del registro, asumir que es válido (acabamos de crearlo)
        try:
            # Crear usuario básico desde UID
            user = {
                'uid': uid,
                'email': f'user-{uid[:8]}@huerto.com',  # Email temporal
                'name': f'Usuario {uid[:8]}',           # Nombre temporal
                'plan': 'gratuito'
            }
            
            # Crear sesión básica
            session.permanent = True
            session['user'] = user
            session['is_authenticated'] = True
            session['user_uid'] = uid
            session['from_register'] = True  # Marcar como recién registrado
            # Limpiar cualquier flag de demo/invitado
            session.pop('demo_mode_chosen', None)
            session.pop('guest_mode_active', None)
            session.modified = True
            
            print(f"✅ [Dashboard] Usuario creado desde registro: {user['uid']}")
            
        except Exception as e:
            print(f"❌ [Dashboard] Error creando usuario desde registro: {e}")
    
    # 2) ALTA PRIORIDAD: Usuario de sesión Flask (si no viene del registro)
    elif session.get('is_authenticated') and session.get('user'):
        # Usuario autenticado en sesión Flask
        user = session.get('user')
        print(f"✅ [Dashboard] Usuario desde sesión Flask: {user['uid']}")
        # Asegurar flags limpios
        session.pop('demo_mode_chosen', None)
        session.pop('guest_mode_active', None)
        session.modified = True
    
    # 3) BACKUP: Cookie de usuario como fallback
    elif request.cookies.get('huerto_user_data'):
        try:
            import json
            user_cookie_data = json.loads(request.cookies.get('huerto_user_data'))
            if user_cookie_data.get('authenticated'):
                user = {
                    'uid': user_cookie_data['uid'],
                    'email': user_cookie_data['email'],
                    'name': user_cookie_data['name'],
                    'plan': user_cookie_data['plan']
                }
                
                # Recrear sesión desde cookie
                session.permanent = True
                session['user'] = user
                session['is_authenticated'] = True
                session['user_uid'] = user['uid']
                session.modified = True
                
                print(f"✅ [Dashboard] Usuario recuperado desde cookie de datos: {user['uid']}")
        except Exception as e:
            print(f"❌ [Dashboard] Error parseando cookie de datos: {e}")
    
    # 4) BACKUP: Cookie simple de UID
    elif request.cookies.get('huerto_user_uid'):
        user_uid = request.cookies.get('huerto_user_uid')
        print(f"🔍 [Dashboard] Intentando recuperar desde cookie: {user_uid}")
        
        # Intentar obtener token Firebase de cookies
        firebase_token = request.cookies.get('firebase_id_token')
        if firebase_token:
            try:
                from app.auth.auth_service import AuthService
                user_data = AuthService.verify_firebase_token(firebase_token)
                if user_data and user_data['uid'] == user_uid:
                    user = {
                        'uid': user_data['uid'],
                        'email': user_data['email'],
                        'name': user_data.get('name', user_data['email'].split('@')[0]),
                        'plan': user_data.get('plan', 'gratuito')
                    }
                    
                    # Recrear sesión
                    session.permanent = True
                    session['user'] = user
                    session['is_authenticated'] = True
                    session['user_uid'] = user_data['uid']
                    session.modified = True
                    
                    print(f"✅ [Dashboard] Sesión recreada desde cookie: {user['uid']}")
            except Exception as e:
                print(f"❌ [Dashboard] Error recuperando de cookie: {e}")
    
    # 5) ÚLTIMO RECURSO: Si viene del registro pero no tenemos UID en URL
    elif request.args.get('from') == 'register':
        print(f"🔍 [Dashboard] Viene del registro sin UID - modo demo temporal")
        # Crear usuario demo temporal
        user = {
            'uid': 'demo-user-temp',
            'email': 'demo@huerto.com',
            'name': 'Usuario Demo',
            'plan': 'gratuito'
        }
        
        session.permanent = True
        session['user'] = user
        session['is_authenticated'] = True
        session['user_uid'] = 'demo-user-temp'
        session['demo_user'] = True
        session.modified = True
        
        print(f"✅ [Dashboard] Usuario demo creado temporalmente")
    
    # 4) FALLBACK FINAL: Helper tradicional
    if not user:
        user = get_current_user()
        if user:
            print(f"✅ [Dashboard] Usuario desde helper: {user.get('uid', 'N/A')}")
    
    print(f"🎯 [Dashboard] Usuario final: {user}")
    
    # Detectar modo demo ANTES de verificar usuario
    demo_mode = request.args.get('demo') == 'true' or session.get('demo_mode_chosen', False)
    
    # Si no hay usuario y no es modo demo, redirigir
    if not user and not demo_mode:
        print("❌ [Dashboard] No hay usuario y no es modo demo - redirigiendo a onboarding")
        print(f"🔍 [Dashboard] Resumen del diagnóstico:")
        print(f"  - Session authenticated: {session.get('is_authenticated', False)}")
        print(f"  - Session user: {bool(session.get('user'))}")
        print(f"  - Cookie firebase_id_token: {'firebase_id_token' in request.cookies}")
        print(f"  - Cookie huerto_user_uid: {'huerto_user_uid' in request.cookies}")
        print(f"  - Cookie huerto_user_data: {'huerto_user_data' in request.cookies}")
        print(f"  - Cookie huerto_session: {'huerto_session' in request.cookies}")
        print(f"  - URL args: {dict(request.args)}")
        print(f"  - Viene del registro: {request.args.get('from') == 'register'}")
        print(f"  - Todas las cookies: {list(request.cookies.keys())}")
        return redirect(url_for('main.onboarding'))
    
    # Verificar si es bienvenida desde registro
    welcome = request.args.get('welcome')
    if welcome == 'true':
        print("🎉 [Dashboard] Usuario recién registrado - bienvenida")
    
    # Continuar con el resto del dashboard...
    try:
        crop_service = CropService(current_app.db)
        
        # Determinar UID robusto (sesión -> URL -> cookie)
        robust_uid = (
            (user or {}).get('uid') or
            request.args.get('uid') or
            request.cookies.get('huerto_user_uid')
        )
        
        # Obtener cultivos del usuario (si hay UID)
        user_crops = crop_service.get_user_crops(robust_uid) if robust_uid else []
        
    # Enriquecer datos para UI
        for c in user_crops:
            try:
                kilos = sum(float(p.get('kilos', 0)) for p in c.get('produccion_diaria', []))
            except Exception:
                kilos = 0.0
            c['kilos_totales'] = kilos
            try:
                precio = float(c.get('precio_por_kilo', 0))
            except Exception:
                precio = 0.0
            c['beneficio_total'] = kilos * precio
            # Mapear número de plantas al nombre usado en el template
            try:
                c['plantas_sembradas'] = int(c.get('numero_plantas', c.get('plantas_sembradas', 0)) or 0)
            except Exception:
                c['plantas_sembradas'] = 0
            # Calcular unidades recolectadas sumando 'unidades' si existe; si no, contar registros como 1 unidad
            try:
                producciones = c.get('produccion_diaria', []) or []
                unidades_sum = 0
                for p in producciones:
                    if 'unidades' in p and p['unidades'] is not None:
                        try:
                            unidades_sum += int(p['unidades'])
                        except Exception:
                            unidades_sum += 0
                    else:
                        # Compatibilidad: cada registro cuenta como 1 unidad si no hay campo específico
                        unidades_sum += 1
                c['unidades_recolectadas'] = int(unidades_sum)
            except Exception:
                c['unidades_recolectadas'] = 0
        
        total_crops = len(user_crops)
        
        # Calcular estadísticas básicas con clave correcta 'activo'
        active_crops = [c for c in user_crops if c.get('activo', True)]
        completed_crops = [c for c in user_crops if not c.get('activo', True)]
        
        # Totales globales (alias para el template)
        try:
            total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
        except Exception:
            total_kilos, total_beneficios = 0, 0
        
        # Plan y límites
        plan = user.get('plan', 'gratuito')
        plan_limits = get_plan_config(plan)
        
        return render_template(
            'dashboard.html',
            # Identidad y sesión
            user=user,
            is_authenticated=True,
            is_demo_mode=False,
            is_guest_mode=False,
            # Métricas
            total_crops=total_crops,
            active_crops=len(active_crops),
            completed_crops=len(completed_crops),
            recent_crops=user_crops[:5],
            cultivos=user_crops,
            total_production=total_kilos,
            total_revenue=total_beneficios,
            # Plan
            plan=plan,
            plan_limits=plan_limits,
            show_upgrade_banner=should_show_upgrade_banner(plan, len(user_crops)),
            # Otros
            welcome=welcome == 'true'
        )
                             
    except Exception as e:
        print(f"❌ Error en dashboard: {e}")
        # En caso de error, mostrar dashboard básico
        return render_template(
            'dashboard.html',
            # Identidad y sesión
            user=user,
            is_authenticated=True,
            is_demo_mode=False,
            is_guest_mode=False,
            # Métricas vacías
            total_crops=0,
            active_crops=0,
            completed_crops=0,
            recent_crops=[],
            cultivos=[],
            total_production=0,
            total_revenue=0,
            # Plan por defecto
            plan=user.get('plan', 'gratuito') if isinstance(user, dict) else 'gratuito',
            plan_limits=get_plan_config(user.get('plan', 'gratuito') if isinstance(user, dict) else 'gratuito'),
            show_upgrade_banner=False,
            # Otros
            welcome=welcome == 'true'
        )
        
        # Verificar si hay token de ID de Firebase en las cookies/headers
        firebase_token = request.headers.get('Authorization')
        if firebase_token and firebase_token.startswith('Bearer '):
            from app.auth.auth_service import AuthService
            firebase_token = firebase_token.replace('Bearer ', '')
            user_data = AuthService.verify_firebase_token(firebase_token)
            if user_data:
                print(f"🔍 [Dashboard] Usuario recuperado de token Firebase: {user_data['uid']}")
                user = user_data
    
    crop_service = CropService(current_app.db)
    
    # Obtener datos según el modo (demo_mode ya se detectó arriba)
    if demo_mode:
        # Modo demo - mostrar datos de demostración
        cultivos = crop_service.get_demo_crops()
        total_kilos, total_beneficios = crop_service.get_demo_totals()
        plan = 'demo'
    elif user:
        # Usuario autenticado
        if user.get('is_local'):
            cultivos = crop_service.get_local_user_crops(user['uid'])
            total_kilos, total_beneficios = crop_service.get_local_user_totals(user['uid'])
        else:
            cultivos = crop_service.get_user_crops(user['uid'])
            total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
        
        # Obtener plan del usuario
        if not user.get('is_local'):
            from app.auth.auth_service import UserService
            user_service = UserService(current_app.db)
            plan = user_service.get_user_plan(user['uid'])
        else:
            plan = user.get('plan', 'gratuito')
        demo_mode = False
    else:
        # Sin usuario ni modo demo: mostrar página de espera o ir a login, pero NO al onboarding
        if request.args.get('from') == 'register':
            print("🔍 [Dashboard] Usuario registrado pero sin sesión - mostrar waiting")
            return render_template('auth/waiting.html', 
                                   message="Finalizando configuración...",
                                   redirect_url="/dashboard")
        # En cualquier otro caso, ir a login con next al dashboard
        return redirect(url_for('auth.login', next=url_for('main.dashboard')))
    
    # Preparar datos para gráficas
    datos_cultivos = {}
    for cultivo in cultivos:
        nombre = cultivo['nombre']
        precio_kilo = cultivo.get('precio_por_kilo', 0)
        kilos_total = sum(p.get('kilos', 0) for p in cultivo.get('produccion_diaria', []))
        
        datos_cultivos[nombre] = {
            'kilos': kilos_total,
            'beneficio': kilos_total * precio_kilo
        }
    
    # Obtener límites del plan
    plan_limits = get_plan_config(plan)
    
    return render_template('dashboard.html',
                         datos_cultivos=datos_cultivos,
                         total_kilos=total_kilos,
                         total_beneficios=total_beneficios,
                         demo_mode=demo_mode,
                         plan=plan,
                         plan_limits=plan_limits,
                         cultivos=cultivos)

@main_bp.route('/test-cultivo-simple')
def test_cultivo_simple():
    """Test simple para crear cultivo sin autenticación"""
    try:
        from flask import current_app
        from app.services.crop_service import CropService
        from app.auth.auth_service import UserService
        import traceback
        
        html = "<h1>🧪 Test Cultivo Simple</h1>"
        
        if not current_app.db:
            return html + "<p style='color: red'>❌ No hay conexión a Firebase</p>"
        
        html += "<p style='color: green'>✅ Firebase conectado</p>"
        
        # Test de conectividad básica
        html += "<p>🔍 Probando conectividad a Firestore...</p>"
        try:
            # Intentar listar colecciones (esto falla si la DB no existe)
            collections = list(current_app.db.collections())
            html += f"<p style='color: green'>✅ Base de datos Firestore existe - Colecciones: {len(collections)}</p>"
        except Exception as e:
            html += f"<p style='color: red'>❌ Error accediendo a Firestore: {e}</p>"
            html += "<p style='color: orange'>💡 Probable causa: Base de datos Firestore no creada en Firebase Console</p>"
            html += "<p>🔧 Solución: Ve a Firebase Console → Firestore Database → Create database</p>"
        
        # Usuario de prueba
        test_uid = "simple_test_user"
        user_service = UserService(current_app.db)
        crop_service = CropService(current_app.db)
        
        html += f"<p>👤 UID de prueba: {test_uid}</p>"
        
        # Verificar/crear usuario
        user = user_service.get_user_by_uid(test_uid)
        if not user:
            html += "<p>📝 Creando usuario de prueba...</p>"
            user_data = {
                'uid': test_uid,
                'email': 'simple@test.com',
                'name': 'Simple Test',
                'plan': 'gratuito'
            }
            
            try:
                created = user_service.create_user(test_uid, user_data)
                html += f"<p>Usuario creado: {'✅' if created else '❌'}</p>"
                
                if not created:
                    # Intentar diagnóstico más detallado
                    html += "<p>🔍 Diagnóstico detallado del error de usuario:</p>"
                    try:
                        # Intentar una operación simple de prueba
                        test_doc = current_app.db.collection('test').document('connectivity')
                        test_doc.set({'test': True, 'timestamp': 'now'})
                        html += "<p style='color: green'>✅ Escritura de prueba exitosa</p>"
                        
                        # Limpiar
                        test_doc.delete()
                        html += "<p style='color: green'>✅ Eliminación de prueba exitosa</p>"
                        
                    except Exception as e:
                        html += f"<p style='color: red'>❌ Error en escritura de prueba: {e}</p>"
                        html += f"<p style='color: red'>📋 Traceback: {traceback.format_exc()}</p>"
                        
            except Exception as e:
                html += f"<p style='color: red'>❌ Error creando usuario: {e}</p>"
                html += f"<p style='color: red'>📋 Traceback: {traceback.format_exc()}</p>"
        else:
            html += f"<p>✅ Usuario existe con plan: {user.get('plan', 'N/A')}</p>"
        
        # Solo intentar crear cultivo si el usuario existe o se creó
        user_exists_now = user_service.get_user_by_uid(test_uid) is not None
        
        if user_exists_now:
            # Intentar crear cultivo
            crop_data = {
                'nombre': 'tomates simples',
                'precio': 2.5,
                'numero_plantas': 5
            }
            
            html += f"<p>🌱 Intentando crear cultivo: {crop_data}</p>"
            
            try:
                success = crop_service.create_crop(test_uid, crop_data)
                html += f"<p>Resultado: {'✅ Éxito' if success else '❌ Falló'}</p>"
                
                if success:
                    # Esperar un momento para que se propague
                    import time
                    time.sleep(0.5)
                    
                    crops = crop_service.get_user_crops(test_uid)
                    html += f"<p>📊 Cultivos totales: {len(crops)}</p>"
                    
                    # Mostrar detalles del cultivo si existe
                    if crops:
                        ultimo_cultivo = crops[0]
                        html += f"<p>🌱 Último cultivo: {ultimo_cultivo.get('nombre', 'N/A')}</p>"
                        html += f"<p>💰 Precio: €{ultimo_cultivo.get('precio_por_kilo', 0)}/kg</p>"
                    else:
                        html += "<p style='color: orange'>⚠️ No se encontraron cultivos después de crear</p>"
                        
                        # Debug: intentar obtener todos los cultivos sin filtro
                        try:
                            all_crops_ref = current_app.db.collection('usuarios').document(test_uid).collection('cultivos')
                            all_docs = list(all_crops_ref.stream())
                            html += f"<p>🔍 Debug: Total documentos en la colección: {len(all_docs)}</p>"
                            
                            for doc in all_docs:
                                data = doc.to_dict()
                                html += f"<p>📄 Documento: {doc.id} - activo: {data.get('activo', 'N/A')}</p>"
                        except Exception as e:
                            html += f"<p style='color: red'>❌ Error en debug: {e}</p>"
                else:
                    html += "<p style='color: red'>❌ El cultivo no se pudo crear</p>"
            except Exception as e:
                html += f"<p style='color: red'>❌ Error creando cultivo: {e}</p>"
                html += f"<p style='color: red'>📋 Traceback: {traceback.format_exc()}</p>"
        else:
            html += "<p style='color: orange'>⚠️ No se puede crear cultivo porque el usuario no existe</p>"
        
        return html
        
    except Exception as e:
        import traceback
        return f"<h1>❌ Error general</h1><p>{e}</p><pre>{traceback.format_exc()}</pre>"
    """Dashboard principal con resumen de cultivos"""
    from flask import current_app
    
    # Obtener parámetros de URL para determinar el modo
    demo_mode = request.args.get('demo') == 'true'
    guest_mode = request.args.get('mode') == 'guest'
    from_register = request.args.get('from') == 'register'
    
    # También verificar si hay sesión activa de modo invitado
    guest_session_active = session.get('guest_mode_active', False)
    demo_session_active = session.get('demo_mode_chosen', False)
    
    user = get_current_user()
    
    # Si viene de registro pero no hay usuario, mostrar página de espera
    if from_register and not user:
        return render_template('auth/waiting.html', 
                             message="Configurando tu cuenta...",
                             redirect_url="/dashboard")
    
    # Determinar el tipo de sesión y plan (priorizar usuario autenticado)
    if user:
        # Usuario autenticado (Firebase o local)
        if user.get('is_local'):
            plan = user.get('plan', 'gratuito')
            user_type = 'local'
        else:
            # Preferir el plan del token/sesión si está presente (más fiable justo tras registro)
            token_plan = user.get('plan')
            if token_plan:
                plan = token_plan
            else:
                user_service = UserService(current_app.db)
                plan = user_service.get_user_plan(user['uid'])
            user_type = 'firebase'
        is_authenticated = True
        use_demo_data = False
    
    elif demo_mode or demo_session_active:
        # Modo demo con datos de ejemplo
        plan = 'invitado'
        is_authenticated = False
        use_demo_data = True
        user_type = 'demo'
        session['demo_mode_chosen'] = True
        
    elif guest_mode or guest_session_active or (user and user.get('isGuest')):
        # Modo invitado sin datos (vacío)
        plan = 'invitado'
        is_authenticated = False
        use_demo_data = False
        user_type = 'guest'
        session['guest_mode_active'] = True
        
    else:
        # Sin usuario ni modo específico -> redirección al onboarding
        return redirect(url_for('main.onboarding'))
    
    # Obtener límites del plan
    plan_limits = plan_limit_helper(plan)
    
    # Obtener cultivos según el tipo de usuario
    crop_service = CropService(current_app.db)
    
    if use_demo_data:
        # Datos demo con ejemplos
        cultivos = crop_service.get_demo_crops()
        total_kilos, total_beneficios = crop_service.get_demo_totals()
        
    elif user_type == 'guest':
        # Modo invitado vacío (datos desde localStorage en frontend)
        cultivos = []
        total_kilos, total_beneficios = 0, 0
        
    elif user_type == 'local':
        # Usuario local registrado
        cultivos = crop_service.get_local_user_crops(user['uid'])
        total_kilos, total_beneficios = crop_service.get_local_user_totals(user['uid'])
        
    elif user_type == 'firebase':
        # Usuario Firebase
        cultivos = crop_service.get_user_crops(user['uid'])
        total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
        
    else:
        # Fallback
        cultivos = []
        total_kilos, total_beneficios = 0, 0
    
    # Marcar como visitado
    session['visited_before'] = True
    
    # Calcular estadísticas adicionales
    total_crops = len(cultivos)
    active_crops = len([c for c in cultivos if c.get('activo', True)])
    
    context = {
        'cultivos': cultivos,
        'total_kilos': total_kilos,
        'total_beneficios': total_beneficios,
        'total_production': total_kilos,  # Alias para compatibilidad con template
        'total_revenue': total_beneficios,  # Alias para compatibilidad con template
        'total_crops': total_crops,
        'active_crops': active_crops,
        'plan': plan,
        'plan_limits': plan_limits,
        'is_authenticated': is_authenticated,
        'user_type': user_type,  # Añadir tipo de usuario
        'is_demo_mode': use_demo_data,  # Para banners específicos
        'is_guest_mode': user_type == 'guest',  # Para funcionalidad local
        'show_upgrade_banner': should_show_upgrade_banner(plan, len(cultivos)),
        'demo_mode': use_demo_data  # Para mostrar banner demo
    }
    
    return render_template('dashboard.html', **context)

@main_bp.route('/profile')
def profile():
    """Perfil de usuario y configuración"""
    user = get_current_user()
    if not user:
        # return redirect(url_for('auth.login'))  # Comentado para evitar loops
        return redirect(url_for('main.dashboard'))
    
    from flask import current_app
    user_service = UserService(current_app.db)
    user_data = user_service.get_user_by_uid(user['uid'])
    
    return render_template('profile/main.html', user=user_data)

@main_bp.route('/pricing')
def pricing():
    """Página de precios y planes"""
    user = get_current_user()
    current_plan = 'invitado'
    
    if user:
        from flask import current_app
        user_service = UserService(current_app.db)
        current_plan = user_service.get_user_plan(user['uid'])
    
    return render_template('pricing/plans.html', current_plan=current_plan)

@main_bp.route('/api/user-status')
def api_user_status():
    """API para obtener estado del usuario actual"""
    user = get_current_user()
    
    if user:
        from flask import current_app
        user_service = UserService(current_app.db)
        plan = user_service.get_user_plan(user['uid'])
        
        return jsonify({
            'authenticated': True,
            'uid': user['uid'],
            'email': user['email'],
            'plan': plan,
            'limits': get_plan_config(plan)
        })
    else:
        return jsonify({
            'authenticated': False,
            'plan': 'invitado',
            'limits': get_plan_config('invitado')
        })

def should_show_upgrade_banner(plan, num_cultivos):
    """Determinar si mostrar banner de upgrade - NO mostrar en modo demo"""
    # En modo demo (plan='invitado') no mostrar banners de upgrade
    # porque es una demostración de funcionalidades premium
    if plan == 'invitado':
        return False
    elif plan == 'gratuito' and num_cultivos >= 5:
        return True
    return False
