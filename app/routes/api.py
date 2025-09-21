"""
API endpoints para la aplicación - SEGUROS
Endpoints RESTful para interacción con frontend con autenticación Firebase
"""
from flask import Blueprint, request, jsonify
from app.middleware.auth_middleware import require_auth, get_current_user, get_current_user_uid, optional_auth
from app.services.crop_service import CropService

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'HuertoRentable',
        'version': '2.0'
    })

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
@require_auth
def get_crops():
    """Obtener cultivos del usuario (requiere autenticación)."""
    from flask import current_app
    
    user_uid = get_current_user_uid()
    crop_service = CropService(current_app.db)
    
    cultivos = crop_service.get_user_crops(user_uid)
    
    return jsonify({
        'success': True,
        'crops': cultivos,
        'count': len(cultivos)
    })

@api_bp.route('/crops', methods=['POST'])
@require_auth
def create_crop():
    """Crear nuevo cultivo via API - REQUIERE AUTENTICACIÓN SEGURA"""
    from flask import current_app
    
    user_uid = get_current_user_uid()
    crop_service = CropService(current_app.db)
    
    data = request.get_json()
    
    if not data or not data.get('nombre'):
        return jsonify({'error': 'Nombre requerido'}), 400
    
    crop_data = {
        'nombre': data['nombre'].strip(),
        'precio': float(data.get('precio', 0))
    }
    
    if crop_service.create_crop(user_uid, crop_data):
        return jsonify({'success': True, 'message': 'Cultivo creado'})
    else:
        return jsonify({'error': 'Error creando cultivo'}), 400

@api_bp.route('/crops/<crop_id>/production', methods=['POST'])
@require_auth
def update_production(crop_id):
    """Actualizar producción via API - REQUIERE AUTENTICACIÓN SEGURA"""
    from flask import current_app
    
    user_uid = get_current_user_uid()
    crop_service = CropService(current_app.db)
    
    data = request.get_json()
    kilos = float(data.get('kilos', 0))
    
    if kilos <= 0:
        return jsonify({'error': 'Kilos debe ser positivo'}), 400
    
    if crop_service.update_production(user_uid, crop_id, kilos):
        return jsonify({'success': True, 'message': 'Producción actualizada'})
    else:
        return jsonify({'error': 'Error actualizando producción'}), 400

@api_bp.route('/crops/update-color', methods=['POST'])
@require_auth
def update_crop_color():
    """Actualizar color de cultivo via API - REQUIERE AUTENTICACIÓN SEGURA"""
    from flask import current_app
    
    user = get_current_user()
    user_uid = get_current_user_uid()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
            
        cultivo_id = data.get('cultivo_id')
        color = data.get('color')
        
        if not cultivo_id or not color:
            return jsonify({'success': False, 'error': 'cultivo_id y color requeridos'}), 400
        
        if current_app.db:
            crop_ref = current_app.db.collection('usuarios').document(user_uid).collection('cultivos').document(cultivo_id)
            crop_ref.update({
                'color_cultivo': color,
                'actualizado_en': __import__('datetime').datetime.utcnow()
            })
            return jsonify({'success': True, 'color': color})
        else:
            return jsonify({'success': False, 'error': 'Base de datos no disponible'}), 500
    except Exception as e:
        print('Error actualizando color:', e)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/totals')
@require_auth
def user_totals():
    """Obtener totales del usuario (requiere autenticación)."""
    from flask import current_app
    
    user_uid = get_current_user_uid()
    crop_service = CropService(current_app.db)
    
    total_kilos, total_beneficios = crop_service.get_user_totals(user_uid)
    
    return jsonify({
        'total_kilos': total_kilos,
        'total_beneficios': total_beneficios
    })
