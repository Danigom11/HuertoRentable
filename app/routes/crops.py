"""
Rutas de gestión de cultivos
CRUD de cultivos con verificación de planes
"""
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.auth.auth_service import login_required, get_current_user
from app.services.crop_service import CropService
from app.utils.helpers import get_plan_limits

crops_bp = Blueprint('crops', __name__)

@crops_bp.route('/')
def list_crops():
    """Listar cultivos del usuario (modo demo disponible)"""
    from flask import current_app, session
    
    # Detectar modo invitado desde la sesión o parámetros URL
    guest_mode = request.args.get('mode') == 'guest' or session.get('guest_mode_active', False)
    demo_mode = request.args.get('demo') == 'true' or session.get('demo_mode_chosen', False)
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    if demo_mode:
        # Modo demo: cultivos de ejemplo
        cultivos = crop_service.get_demo_crops()
        return render_template('crops.html', cultivos=cultivos, demo_mode=True, guest_mode=False)
    elif guest_mode or (user and user.get('isGuest')):
        # Modo invitado: datos desde localStorage (se manejan en frontend)
        session['guest_mode_active'] = True
        return render_template('crops.html', cultivos=[], demo_mode=False, guest_mode=True)
    elif user:
        # Usuario autenticado: verificar si es local o Firebase
        if user.get('is_local'):
            cultivos = crop_service.get_local_user_crops(user['uid'])
        else:
            cultivos = crop_service.get_user_crops(user['uid'])
        return render_template('crops.html', cultivos=cultivos, demo_mode=False, guest_mode=False)
    else:
        # Sin usuario ni modo específico: mostrar demo
        cultivos = crop_service.get_demo_crops()
        return render_template('crops.html', cultivos=cultivos, demo_mode=True, guest_mode=False)

@crops_bp.route('/create', methods=['GET', 'POST'])
def create_crop():
    """Crear nuevo cultivo (requiere autenticación o modo invitado)"""
    from flask import current_app, session
    
    # Detectar modo invitado
    guest_mode = request.args.get('mode') == 'guest' or session.get('guest_mode_active', False)
    
    user = get_current_user()
    
    if not user and not guest_mode:
        if request.method == 'POST':
            # En modo demo, mostrar mensaje informativo y redirigir
            flash('🌱 Modo Demo: Para crear cultivos reales, regístrate gratis. ¡Los datos demo son solo para explorar!', 'info')
            return redirect(url_for('crops.list_crops'))
        else:
            # GET request, redirigir directamente
            return redirect(url_for('crops.list_crops'))
    
    if request.method == 'GET':
        if guest_mode:
            return render_template('crops.html', guest_mode=True, demo_mode=False)
        else:
            return render_template('crops.html', guest_mode=False, demo_mode=False)
    
    # POST request - crear cultivo
    crop_service = CropService(current_app.db)
    
    # Obtener datos del formulario
    crop_data = {
        'nombre': request.form.get('nombre', '').strip(),
        'precio': request.form.get('precio', 0)
    }
    
    # Validaciones
    if not crop_data['nombre']:
        flash('El nombre del cultivo es obligatorio', 'error')
        if guest_mode:
            return redirect(url_for('crops.list_crops', mode='guest'))
        else:
            return redirect(url_for('crops.create_crop'))
    
    try:
        crop_data['precio'] = float(crop_data['precio'])
        if crop_data['precio'] < 0:
            flash('El precio debe ser positivo', 'error')
            if guest_mode:
                return redirect(url_for('crops.list_crops', mode='guest'))
            else:
                return redirect(url_for('crops.create_crop'))
    except ValueError:
        flash('Precio inválido', 'error')
        if guest_mode:
            return redirect(url_for('crops.list_crops', mode='guest'))
        else:
            return redirect(url_for('crops.create_crop'))
    
    # Crear cultivo
    if guest_mode:
        # Modo invitado: los datos se manejan con localStorage en el frontend
        # Solo devolvemos un JSON con los datos para que JavaScript los procese
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': True,
                'cultivo': {
                    'id': f'guest_{int(time.time())}',
                    'nombre': crop_data['nombre'],
                    'precio': crop_data['precio'],
                    'fecha_siembra': datetime.now().isoformat(),
                    'activo': True,
                    'produccion_total': 0,
                    'beneficio_total': 0
                }
            })
        else:
            # Formulario HTML normal: mostrar mensaje y redirigir
            flash(f'Cultivo "{crop_data["nombre"]}" creado en modo invitado (datos locales)', 'success')
            return redirect(url_for('crops.list_crops', mode='guest'))
    elif user.get('is_local'):
        # Usuario local: guardar en sesión
        success = crop_service.create_local_crop(user['uid'], crop_data)
    else:
        # Usuario Firebase: guardar en Firestore
        success = crop_service.create_crop(user['uid'], crop_data)
    
    if success:
        flash(f'Cultivo "{crop_data["nombre"]}" creado exitosamente', 'success')
        return redirect(url_for('crops.list_crops'))
    else:
        flash('Error al crear cultivo. Verifica los límites de tu plan.', 'error')
        return redirect(url_for('crops.create_crop'))

@crops_bp.route('/<crop_id>/production', methods=['POST'])
def update_production(crop_id):
    """Actualizar producción de un cultivo (requiere autenticación)"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Modo demo: regístrate para actualizar cultivos reales'}), 403
        
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    try:
        kilos = float(request.form.get('kilos', 0))
        if kilos <= 0:
            flash('Los kilos deben ser positivos', 'error')
            return redirect(url_for('main.dashboard'))
        
        if crop_service.update_production(user['uid'], crop_id, kilos):
            flash(f'Producción actualizada: {kilos}kg', 'success')
        else:
            flash('Error actualizando producción', 'error')
        
        return redirect(url_for('main.dashboard'))
        
    except ValueError:
        flash('Cantidad inválida', 'error')
        return redirect(url_for('main.dashboard'))

@crops_bp.route('/api/user-crops')
def api_user_crops():
    """API para obtener cultivos del usuario (modo demo disponible)"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    if user:
        cultivos = crop_service.get_user_crops(user['uid'])
    else:
        cultivos = crop_service.get_demo_crops()
    
    # Serializar cultivos para JSON
    cultivos_json = []
    for cultivo in cultivos:
        cultivo_data = {
            'id': cultivo['id'],
            'nombre': cultivo['nombre'],
            'precio_por_kilo': cultivo['precio_por_kilo'],
            'activo': cultivo['activo'],
            'total_kilos': sum(p.get('kilos', 0) for p in cultivo.get('produccion_diaria', []))
        }
        cultivos_json.append(cultivo_data)
    
    return jsonify(cultivos_json)
