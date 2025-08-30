"""
Rutas principales de la aplicación
Dashboard, onboarding y páginas principales
"""
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, make_response
from app.auth.auth_service import get_current_user, UserService
from app.services.crop_service import CropService
from app.utils.helpers import get_plan_limits
import time

main_bp = Blueprint('main', __name__)

# @main_bp.route('/login')
# def login_redirect():
#     """Redireccionar desde /login a /auth/login para compatibilidad"""
#     return redirect(url_for('auth.login'))

# @main_bp.route('/register')
# def register_redirect():
#     """Redireccionar desde /register a /auth/register para compatibilidad"""
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
    user = get_current_user()
    
    # Si está autenticado, ir al dashboard
    if user:
        return redirect(url_for('main.dashboard'))
    
    # CAMBIO: Por defecto ir al onboarding para mejor UX
    # Solo ir directo al dashboard si explícitamente han elegido demo
    if session.get('demo_mode_chosen'):
        return redirect(url_for('main.dashboard'))
    
    # Primera visita o sin elección → onboarding
    return redirect(url_for('main.onboarding'))

@main_bp.route('/onboarding')
def onboarding():
    """Pantallas de onboarding para nuevos usuarios"""
    return render_template('onboarding/welcome.html')

@main_bp.route('/dashboard')
def dashboard():
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
    plan_limits = get_plan_limits(plan)
    
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
            'limits': get_plan_limits(plan)
        })
    else:
        return jsonify({
            'authenticated': False,
            'plan': 'invitado',
            'limits': get_plan_limits('invitado')
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
