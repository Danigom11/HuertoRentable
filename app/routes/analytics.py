"""
Rutas de analytics y reportes
Gráficas y estadísticas avanzadas
"""
from flask import Blueprint, render_template, jsonify
from app.auth.auth_service import login_required, get_current_user, premium_required
from app.services.crop_service import CropService

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
@login_required
def dashboard():
    """Dashboard de analytics básico"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    # Obtener datos básicos
    cultivos = crop_service.get_user_crops(user['uid'])
    total_kilos, total_beneficios = crop_service.get_user_totals(user['uid'])
    
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
    
    return render_template('analytics/dashboard.html',
                         datos_cultivos=datos_cultivos,
                         total_kilos=total_kilos,
                         total_beneficios=total_beneficios)

@analytics_bp.route('/advanced')
@premium_required
def advanced():
    """Analytics avanzados (solo premium)"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    # Obtener datos más detallados
    cultivos = crop_service.get_user_crops(user['uid'])
    
    # Análisis temporal, predicciones, comparativas, etc.
    # TODO: Implementar analytics avanzados
    
    return render_template('analytics/advanced.html', cultivos=cultivos)

@analytics_bp.route('/api/chart-data')
@login_required
def api_chart_data():
    """API para datos de gráficas"""
    from flask import current_app
    
    user = get_current_user()
    crop_service = CropService(current_app.db)
    
    cultivos = crop_service.get_user_crops(user['uid'])
    
    # Preparar datos para Chart.js
    labels = []
    kilos_data = []
    beneficios_data = []
    
    for cultivo in cultivos:
        labels.append(cultivo['nombre'].title())
        
        kilos_total = sum(p.get('kilos', 0) for p in cultivo.get('produccion_diaria', []))
        precio_kilo = cultivo.get('precio_por_kilo', 0)
        
        kilos_data.append(kilos_total)
        beneficios_data.append(kilos_total * precio_kilo)
    
    return jsonify({
        'labels': labels,
        'datasets': [
            {
                'label': 'Kilogramos producidos',
                'data': kilos_data,
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 2
            },
            {
                'label': 'Beneficios (€)',
                'data': beneficios_data,
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 2
            }
        ]
    })
