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

@main_bp.route('/login')
def login_redirect():
    """Redireccionar desde /login a /auth/login para compatibilidad"""
    return redirect(url_for('auth.login'))

@main_bp.route('/register')
def register_redirect():
    """Redireccionar desde /register a /auth/register para compatibilidad"""
    return redirect(url_for('auth.register'))

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

@main_bp.route('/')
def home():
    """Página principal - redirecciona según estado del usuario"""
    user = get_current_user()
    
    # Si está autenticado, ir al dashboard
    if user:
        return redirect(url_for('main.dashboard'))
    
    # Si es primera visita, mostrar onboarding
    if not session.get('visited_before'):
        return redirect(url_for('main.onboarding'))
    
    # Usuario conocido sin autenticar, ir al dashboard
    return redirect(url_for('main.dashboard'))

@main_bp.route('/onboarding')
def onboarding():
    """Pantallas de onboarding para nuevos usuarios"""
    return render_template('onboarding/welcome.html')

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard principal con resumen de cultivos"""
    from flask import current_app
    
    user = get_current_user()
    
    # Determinar tipo de usuario y plan
    if user:
        user_service = UserService(current_app.db)
        plan = user_service.get_user_plan(user['uid'])
        is_authenticated = True
    else:
        plan = 'invitado'
        is_authenticated = False
    
    # Obtener límites del plan
    plan_limits = get_plan_limits(plan)
    
    # Obtener cultivos según el usuario
    crop_service = CropService(current_app.db)
    
    if is_authenticated:
        # Usuario autenticado: datos de Firebase
        cultivos = crop_service.get_user_crops(user['uid'])
        total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
    else:
        # Usuario invitado: datos locales o demo
        cultivos = crop_service.get_demo_crops()
        total_kilos, total_beneficios = crop_service.get_demo_totals()
    
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
        'show_upgrade_banner': should_show_upgrade_banner(plan, len(cultivos)),
        'demo_mode': not is_authenticated  # Para mostrar banner demo
    }
    
    return render_template('dashboard.html', **context)

@main_bp.route('/profile')
def profile():
    """Perfil de usuario y configuración"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth_bp.login'))
    
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
    """Determinar si mostrar banner de upgrade"""
    if plan == 'invitado' and num_cultivos >= 2:
        return True
    elif plan == 'gratuito' and num_cultivos >= 5:
        return True
    return False
