"""
API endpoints para la aplicación
Endpoints RESTful para interacción con frontend
"""
from flask import Blueprint, request, jsonify
from app.auth.auth_service import login_required, get_current_user
from app.services.crop_service import CropService

api_bp = Blueprint('api', __name__)

@api_bp.route('/status')
def status():
    """Estado de la API y la aplicación"""
    return jsonify({
        'status': 'online',
        'version': '2.0',
        'features': {
            'authentication': True,
            'plans': True,
            'firebase': True,
            'analytics': True
        }
    })

@api_bp.route('/crops', methods=['GET'])
@login_required
def get_crops():
    """Obtener cultivos del usuario"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    cultivos = crop_service.get_user_crops(user['uid'])
    
    return jsonify({
        'success': True,
        'crops': cultivos,
        'count': len(cultivos)
    })

@api_bp.route('/crops', methods=['POST'])
@login_required
def create_crop():
    """Crear nuevo cultivo via API"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    data = request.get_json()
    
    if not data or not data.get('nombre'):
        return jsonify({'error': 'Nombre requerido'}), 400
    
    crop_data = {
        'nombre': data['nombre'].strip(),
        'precio': float(data.get('precio', 0))
    }
    
    if crop_service.create_crop(user['uid'], crop_data):
        return jsonify({'success': True, 'message': 'Cultivo creado'})
    else:
        return jsonify({'error': 'Error creando cultivo'}), 400

@api_bp.route('/crops/<crop_id>/production', methods=['POST'])
@login_required
def update_production(crop_id):
    """Actualizar producción via API"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    data = request.get_json()
    kilos = float(data.get('kilos', 0))
    
    if kilos <= 0:
        return jsonify({'error': 'Kilos debe ser positivo'}), 400
    
    if crop_service.update_production(user['uid'], crop_id, kilos):
        return jsonify({'success': True, 'message': 'Producción actualizada'})
    else:
        return jsonify({'error': 'Error actualizando producción'}), 400

@api_bp.route('/user/totals')
@login_required
def user_totals():
    """Obtener totales del usuario"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
    
    return jsonify({
        'total_kilos': total_kilos,
        'total_beneficios': total_beneficios
    })
