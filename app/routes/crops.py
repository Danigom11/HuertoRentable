"""
Rutas de gestión de cultivos
CRUD de cultivos con verificación de planes
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.auth.auth_service import login_required, get_current_user
from app.services.crop_service import CropService
from app.utils.helpers import get_plan_limits

crops_bp = Blueprint('crops', __name__)

@crops_bp.route('/')
@login_required
def list_crops():
    """Listar cultivos del usuario"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    cultivos = crop_service.get_user_crops(user['uid'])
    
    return render_template('crops/list.html', cultivos=cultivos)

@crops_bp.route('/create', methods=['GET', 'POST'])
@login_required  
def create_crop():
    """Crear nuevo cultivo"""
    from flask import current_app
    
    if request.method == 'GET':
        return render_template('crops/create.html')
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    # Obtener datos del formulario
    crop_data = {
        'nombre': request.form.get('nombre', '').strip(),
        'precio': request.form.get('precio', 0)
    }
    
    # Validaciones
    if not crop_data['nombre']:
        flash('El nombre del cultivo es obligatorio', 'error')
        return redirect(url_for('crops.create_crop'))
    
    try:
        crop_data['precio'] = float(crop_data['precio'])
        if crop_data['precio'] < 0:
            flash('El precio debe ser positivo', 'error')
            return redirect(url_for('crops.create_crop'))
    except ValueError:
        flash('Precio inválido', 'error')
        return redirect(url_for('crops.create_crop'))
    
    # Crear cultivo
    if crop_service.create_crop(user['uid'], crop_data):
        flash(f'Cultivo "{crop_data["nombre"]}" creado exitosamente', 'success')
        return redirect(url_for('crops.list_crops'))
    else:
        flash('Error al crear cultivo. Verifica los límites de tu plan.', 'error')
        return redirect(url_for('crops.create_crop'))

@crops_bp.route('/<crop_id>/production', methods=['POST'])
@login_required
def update_production(crop_id):
    """Actualizar producción de un cultivo"""
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
@login_required
def api_user_crops():
    """API para obtener cultivos del usuario"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    cultivos = crop_service.get_user_crops(user['uid'])
    
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
